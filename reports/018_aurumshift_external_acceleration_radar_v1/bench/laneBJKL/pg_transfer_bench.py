"""laneBJKL — L1/L2 : transfert Arrow/Parquet <-> PostgreSQL (fichier C0 -> table) : ADBC adbc_ingest vs psycopg COPY,
et lecture PG -> Arrow : ADBC fetch_arrow vs psycopg + DuckDB postgres_scanner (si extension téléchargeable).
Égalité vérifiée par sha256 d'un tri canonique. Instance PG16 jetable port 55433."""
import hashlib, json, time, numpy as np, pyarrow as pa, pyarrow.parquet as pq, psycopg
import adbc_driver_postgresql.dbapi as adbc, duckdb
N = 1_000_000
rng = np.random.default_rng(18)
t = pa.table({"venue": pa.array(rng.choice(["binance", "okx", "bybit"], N)), "symbol": pa.array(rng.choice([f"S{i:02d}" for i in range(22)], N)),
              "event_time": pa.array(1_790_000_000_000 + np.arange(N, dtype=np.int64)), "ingested_at": pa.array(1_790_000_000_100 + np.arange(N, dtype=np.int64)),
              "bid": pa.array(rng.normal(100, 1, N)), "ask": pa.array(rng.normal(100.1, 1, N)), "depth": pa.array(rng.exponential(5, N))})
pq.write_table(t, "/tmp/laneBJKL_pg/c0.parquet")
URI = "postgresql://postgres@localhost:55433/postgres"
res = {"n": N, "adbc_driver_postgresql": __import__("adbc_driver_postgresql").__version__, "duckdb": duckdb.__version__}
def digest(tbl):
    tbl = tbl.sort_by([("event_time", "ascending")])
    return hashlib.sha256(b"".join(c.to_numpy(zero_copy_only=False).tobytes() if c.type != pa.string() else "\x00".join(c.to_pylist()).encode()
                                   for c in [tbl.column(n).combine_chunks() for n in t.column_names])).hexdigest()
h0 = digest(t)
with adbc.connect(URI) as con, con.cursor() as cur:
    cur.execute("DROP TABLE IF EXISTS c0_adbc"); con.commit()
    s = time.perf_counter(); cur.adbc_ingest("c0_adbc", pq.read_table("/tmp/laneBJKL_pg/c0.parquet"), mode="create"); con.commit()
    res["t_adbc_ingest_s"] = round(time.perf_counter() - s, 2)
    s = time.perf_counter(); cur.execute("SELECT * FROM c0_adbc"); back = cur.fetch_arrow_table()
    res["t_adbc_fetch_arrow_s"] = round(time.perf_counter() - s, 2); res["adbc_roundtrip_equal"] = digest(back.select(t.column_names)) == h0
with psycopg.connect(URI, autocommit=True) as pc:
    pc.execute("DROP TABLE IF EXISTS c0_copy; CREATE TABLE c0_copy (venue text, symbol text, event_time bigint, ingested_at bigint, bid float8, ask float8, depth float8)")
    s = time.perf_counter(); tt = pq.read_table("/tmp/laneBJKL_pg/c0.parquet")
    cols = [tt.column(n).to_pylist() for n in tt.column_names]
    with pc.cursor().copy("COPY c0_copy FROM STDIN (FORMAT BINARY)") as cp:
        cp.set_types(["text", "text", "int8", "int8", "float8", "float8", "float8"])
        for row in zip(*cols): cp.write_row(row)
    res["t_psycopg_copy_binary_s"] = round(time.perf_counter() - s, 2)
    s = time.perf_counter(); rows = pc.execute("SELECT * FROM c0_copy").fetchall(); res["t_psycopg_fetchall_s"] = round(time.perf_counter() - s, 2)
try:
    d = duckdb.connect(); d.execute("INSTALL postgres; LOAD postgres")
    d.execute(f"ATTACH 'host=localhost port=55433 user=postgres dbname=postgres' AS pg (TYPE postgres, READ_ONLY)")
    s = time.perf_counter(); dt = d.execute("SELECT * FROM pg.public.c0_adbc").arrow()
    if hasattr(dt, "read_all"): dt = dt.read_all()  # DuckDB 1.5 : .arrow() renvoie un reader paresseux
    res["t_duckdb_pgscan_arrow_s"] = round(time.perf_counter() - s, 2)
    res["duckdb_roundtrip_equal"] = digest(dt.select(t.column_names)) == h0
except Exception as e:
    res["duckdb_postgres_ext"] = f"FAILED: {type(e).__name__}: {str(e)[:160]}"
print(json.dumps(res, indent=1))
