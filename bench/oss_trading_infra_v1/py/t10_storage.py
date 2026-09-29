"""T10 — time-series storage utilities: versioning / as-of semantics / immutability / throughput / footprint.
ArcticDB (embedded, LMDB) vs DuckDB+Parquet (embedded). Question: can either serve as append-only, PIT-safe evidence store, and what does it cost?"""
import sys, json, time, os, tempfile, shutil, warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
which = sys.argv[1]; res = dict(candidate=which)
N = 1_000_000; rng = np.random.default_rng(0)
df = pd.DataFrame(dict(a=rng.normal(size=N), b=rng.normal(size=N), c=rng.integers(0, 1000, N), d=rng.normal(size=N), e=rng.normal(size=N)),
                  index=pd.date_range("2024-01-01", periods=N, freq="s"))
tmp = tempfile.mkdtemp()
if which == "arcticdb":
    import arcticdb as adb
    ac = adb.Arctic(f"lmdb://{tmp}/db?map_size=5GB"); lib = ac.get_library("l", create_if_missing=True)
    t = time.perf_counter(); lib.write("bars", df); res["write_1M_rows_s"] = round(time.perf_counter()-t, 3)
    t = time.perf_counter(); back = lib.read("bars").data; res["read_1M_rows_s"] = round(time.perf_counter()-t, 3)
    res["roundtrip_equal_strict"] = bool(back.equals(df))
    try: pd.testing.assert_frame_equal(back, df, check_freq=False); res["roundtrip_equal_ignoring_index_freq"] = True
    except AssertionError as e: res["roundtrip_equal_ignoring_index_freq"] = False; res["roundtrip_diff"] = str(e)[:200]
    res["disk_mb"] = round(sum(os.path.getsize(os.path.join(dp, f)) for dp, _, fs in os.walk(tmp) for f in fs)/1e6, 1)
    # versioning / as-of
    t_before = pd.Timestamp.now(); time.sleep(1.1)
    corr = df.iloc[:5].copy(); corr["a"] = 999.0
    t0 = pd.Timestamp.now(); lib.update("bars", corr); time.sleep(1.1); t1 = pd.Timestamp.now()
    vers = lib.list_versions("bars"); res["n_versions_after_update"] = len(vers)
    v0 = lib.read("bars", as_of=0).data.iloc[0].a; vlatest = lib.read("bars").data.iloc[0].a
    res["as_of_version0_first_a_equals_original"] = bool(v0 == df.iloc[0].a); res["latest_first_a"] = float(vlatest)
    r_ts = lib.read("bars", as_of=t0 - pd.Timedelta(seconds=0.5)).data.iloc[0].a
    res["as_of_timestamp_before_update_returns_original"] = bool(r_ts == df.iloc[0].a)
    r_ts2 = lib.read("bars", as_of=t1).data.iloc[0].a; res["as_of_timestamp_after_update_returns_correction"] = bool(r_ts2 == 999.0)
    res["version_timestamp_source"] = "INFERENCE: stamped by the writing process (embedded library, no server clock); write() exposes no timestamp argument"
    # can a caller forge / backdate? check write() kwargs
    import inspect; res["write_has_timestamp_param"] = "timestamp" in inspect.signature(lib.write).parameters or "date" in inspect.signature(lib.write).parameters
    # destructive operations: prune / delete
    lib.prune_previous_versions("bars"); 
    try: lib.read("bars", as_of=0); res["prune_previous_versions_removes_history"] = False
    except Exception as e: res["prune_previous_versions_removes_history"] = True
    lib.write("snap_sym", df.iloc[:10]); lib.snapshot("s1"); lib.delete("snap_sym")
    try: r = lib.read("snap_sym", as_of="s1").data; res["snapshot_survives_delete"] = len(r) == 10
    except Exception as e: res["snapshot_survives_delete"] = False
    res["delete_is_available_to_any_writer"] = True
    # append-only enforcement?
    lib.write("ev", df.iloc[:100]); 
    try: lib.append("ev", df.iloc[:50]); res["append_out_of_order_rejected"] = False
    except Exception as e: res["append_out_of_order_rejected"] = True; res["append_error"] = repr(e)[:160]
    # concurrent-writer / multi-process: LMDB single-writer
    res["multi_process_writers"] = "LMDB backend: single writer (documented); S3/Azure/Mongo backends needed for distributed writes"
elif which == "duckdb_parquet":
    import duckdb
    con = duckdb.connect(); pq = f"{tmp}/bars.parquet"
    t = time.perf_counter(); con.register("df", df.reset_index(names="ts")); con.execute(f"COPY df TO '{pq}' (FORMAT PARQUET, COMPRESSION ZSTD)"); res["write_1M_rows_s"] = round(time.perf_counter()-t, 3)
    t = time.perf_counter(); back = con.execute(f"SELECT * FROM '{pq}'").df(); res["read_1M_rows_s"] = round(time.perf_counter()-t, 3)
    res["roundtrip_equal_values"] = bool(np.allclose(back[["a", "b", "d", "e"]].values, df[["a", "b", "d", "e"]].values)); res["disk_mb"] = round(os.path.getsize(pq)/1e6, 1)
    # append-only files + known_at column => PIT by filtering; DuckDB gives no versioning of its own
    res["native_versioning"] = False; res["pit_pattern"] = "immutable parquet parts + explicit known_at column; as-of = WHERE known_at <= T then arg_max (see report 004)"
    con.execute("CREATE TABLE t AS SELECT * FROM df"); t = time.perf_counter(); r = con.execute("SELECT count(*), avg(a) FROM t WHERE ts BETWEEN '2024-01-05' AND '2024-01-06'").fetchall(); res["range_query_1day_s"] = round(time.perf_counter()-t, 4)
    res["asof_join_available"] = True; res["asof_join_pit_hazard"] = "ASOF JOIN ignores known_at unless pre-filtered (report 004)"
res["site_packages_mb"] = None
shutil.rmtree(tmp, ignore_errors=True)
print(json.dumps(res, default=str))
