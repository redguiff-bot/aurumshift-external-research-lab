import warnings, os, hashlib, time, json, tempfile; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd, duckdb, polars as pl, pyarrow as pa, pyarrow.parquet as pq
from common import save
res = {"versions": {"duckdb": duckdb.__version__, "polars": pl.__version__, "pyarrow": pa.__version__, "pandas": pd.__version__}}
rng = np.random.default_rng(9)
n = 200_000
qt = pd.Series(np.sort(rng.integers(0, 10**12, n))).drop_duplicates().values
quotes = pd.DataFrame({"ts": pd.to_datetime(qt, unit="ns", utc=True), "bid": 100 + rng.normal(0, 1, len(qt)).cumsum() * .01})
tt = np.sort(rng.integers(0, 10**12, 50_000))
trades = pd.DataFrame({"ts": pd.to_datetime(tt, unit="ns", utc=True), "px": rng.normal(100, 1, len(tt))})
# force some exact ts ties to expose inclusive/strict semantics
trades["ts"] = trades["ts"].astype(object); trades.loc[:99, "ts"] = list(quotes.ts.iloc[1000:1100]); trades["ts"] = pd.to_datetime(trades["ts"], utc=True); trades = trades.sort_values("ts").reset_index(drop=True)
for c in ("quotes", "trades"): globals()[c]["ts"] = globals()[c]["ts"].astype("datetime64[us, UTC]")
# strict (<) = "quote strictly known before the trade" ; inclusive (<=)
def pd_asof(strict): return pd.merge_asof(trades, quotes, on="ts", allow_exact_matches=not strict).bid.values
def pl_asof(strict):
    t, q = pl.from_pandas(trades), pl.from_pandas(quotes)
    if strict: q = q.with_columns((pl.col("ts") + pl.duration(microseconds=1)).alias("ts"))   # emulate strict via +1us shift
    return t.join_asof(q, on="ts", strategy="backward").get_column("bid").to_numpy()
def dk_asof(strict):
    con = duckdb.connect(); con.register("t", trades); con.register("q", quotes)
    op = ">" if strict else ">="
    return con.execute(f"SELECT q.bid FROM t ASOF LEFT JOIN q ON t.ts {op} q.ts ORDER BY t.ts").fetchnumpy()["bid"]
out = {}
for strict in (False, True):
    a, b, c = pd_asof(strict), pl_asof(strict), dk_asof(strict)
    out["strict" if strict else "inclusive"] = {"pandas_vs_polars_equal": bool(np.array_equal(a, b, equal_nan=True)), "pandas_vs_duckdb_equal": bool(np.array_equal(a, np.asarray(c, float), equal_nan=True)), "polars_vs_duckdb_equal": bool(np.array_equal(b, np.asarray(c, float), equal_nan=True))}
# lookahead invariant using duckdb: joined quote ts <= trade ts (inclusive) / < (strict)
con = duckdb.connect(); con.register("t", trades); con.register("q", quotes)
out["duckdb_asof_invariant_violations_inclusive"] = int(con.execute("SELECT count(*) FROM (SELECT t.ts tts, q.ts qts FROM t ASOF LEFT JOIN q ON t.ts >= q.ts) WHERE qts > tts").fetchone()[0])
out["duckdb_asof_invariant_violations_strict"] = int(con.execute("SELECT count(*) FROM (SELECT t.ts tts, q.ts qts FROM t ASOF LEFT JOIN q ON t.ts > q.ts) WHERE qts >= tts").fetchone()[0])
res["asof_join_50k_trades_x_200k_quotes"] = out
tm = {}
for name, f in (("pandas", pd_asof), ("polars", pl_asof), ("duckdb", dk_asof)):
    t0 = time.perf_counter(); f(False); tm[name] = round(time.perf_counter() - t0, 3)
res["asof_seconds"] = tm
# parquet determinism
d = tempfile.mkdtemp(); hs = []
for i in range(2):
    p = f"{d}/q{i}.parquet"; pq.write_table(pa.Table.from_pandas(quotes, preserve_index=False), p, compression="zstd", use_dictionary=False); hs.append(hashlib.sha256(open(p, "rb").read()).hexdigest()[:12])
res["parquet_pyarrow_bytes_identical_2_writes"] = hs[0] == hs[1]
res["parquet_size_MB"] = round(os.path.getsize(f"{d}/q0.parquet") / 1e6, 2)
# duckdb query directly over parquet (zero-copy, no load)
t0 = time.perf_counter(); r = duckdb.sql(f"SELECT count(*), avg(bid) FROM '{d}/q0.parquet'").fetchone(); res["duckdb_over_parquet"] = {"rows": r[0], "seconds": round(time.perf_counter() - t0, 4)}
# duckdb extension: attach a live Postgres (authoritative store stays Postgres)
try:
    con = duckdb.connect(); t0 = time.perf_counter(); con.execute("INSTALL postgres; LOAD postgres;")
    con.execute("ATTACH 'host=/tmp/pgts port=55432 user=postgres dbname=postgres' AS pg (TYPE postgres, READ_ONLY)")
    n1 = con.execute("SELECT count(*) FROM pg.t.ticks_plain").fetchone()[0]
    b = con.execute("SELECT count(*) FROM (SELECT date_trunc('minute',ts) b, sym, max(px) FROM pg.t.ticks_plain GROUP BY 1,2)").fetchone()[0]
    res["duckdb_postgres_scanner"] = {"attached_read_only": True, "rows_seen": n1, "minute_groups": b, "seconds": round(time.perf_counter() - t0, 2)}
except Exception as e: res["duckdb_postgres_scanner"] = {"error": f"{type(e).__name__}: {str(e)[:250]}"}
# ArcticDB versioned store: PIT read by version and by timestamp
try:
    import arcticdb as adb
    tmp = tempfile.mkdtemp(); ac = adb.Arctic(f"lmdb://{tmp}"); lib = ac.get_library("l", create_if_missing=True)
    df1 = pd.DataFrame({"px": [1.0, 2.0]}, index=pd.to_datetime(["2024-01-01", "2024-01-02"]))
    lib.write("bars", df1); t_mid = pd.Timestamp.now(); time.sleep(1.1)
    df2 = pd.DataFrame({"px": [1.0, 2.5]}, index=df1.index)  # a restatement
    lib.write("bars", df2)
    v0 = lib.read("bars", as_of=0).data; v1 = lib.read("bars", as_of=1).data; vt = lib.read("bars", as_of=t_mid).data
    res["arcticdb"] = {"version": adb.__version__, "read_as_of_v0_px": v0.px.tolist(), "read_as_of_v1_px": v1.px.tolist(), "read_as_of_timestamp_before_restatement_px": vt.px.tolist(), "versions": [(k, str(v.get('date') if isinstance(v, dict) else '')) for k, v in list(lib.list_versions("bars").items())[:2]] if False else len(lib.list_versions("bars")),
       "storage": "LMDB local dir (or S3/Azure); a separate datastore"}
except Exception as e: res["arcticdb"] = {"error": f"{type(e).__name__}: {str(e)[:300]}"}
print(json.dumps(res, indent=1, default=str)); save("store_microtest.json", res)
