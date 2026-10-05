"""laneBJKL — pgvector L1/L2 smoke sur PG16 jetable (port 55433) : HNSW build + recall@10 vs scan exact.
Données aléatoires (pas de sémantique) : mesure uniquement la mécanique, pas la qualité de retrieval."""
import json, time, numpy as np, psycopg
N, D, Q = 50_000, 128, 100
rng = np.random.default_rng(18)
X = rng.normal(size=(N, D)).astype(np.float32)
qs = rng.normal(size=(Q, D)).astype(np.float32)
con = psycopg.connect("host=localhost port=55433 user=postgres dbname=postgres", autocommit=True)
c = con.cursor()
c.execute("DROP TABLE IF EXISTS mem_item; CREATE TABLE mem_item(id bigint primary key, emb vector(%s))" % D)
t = time.perf_counter()
with c.copy("COPY mem_item(id, emb) FROM STDIN") as cp:
    for i, v in enumerate(X):
        cp.write_row((i, "[" + ",".join(f"{x:.6f}" for x in v) + "]"))
res = {"pgvector": c.execute("select extversion from pg_extension where extname='vector'").fetchone()[0],
       "n": N, "dim": D, "t_copy_s": round(time.perf_counter() - t, 2)}
def topk(q, k=10):
    return [r[0] for r in c.execute("SELECT id FROM mem_item ORDER BY emb <-> %s::vector LIMIT %s",
                                    ("[" + ",".join(map(str, q)) + "]", k)).fetchall()]
c.execute("SET enable_indexscan=off"); exact = [topk(q) for q in qs]; c.execute("RESET enable_indexscan")
t = time.perf_counter(); c.execute("SET maintenance_work_mem='512MB'")
c.execute("CREATE INDEX ON mem_item USING hnsw (emb vector_l2_ops) WITH (m=16, ef_construction=64)")
res["t_hnsw_build_s"] = round(time.perf_counter() - t, 2)
for ef in (40, 200):
    c.execute(f"SET hnsw.ef_search={ef}")
    t = time.perf_counter(); approx = [topk(q) for q in qs]; dt = time.perf_counter() - t
    res[f"recall10_ef{ef}"] = round(float(np.mean([len(set(a) & set(e)) / 10 for a, e in zip(approx, exact)])), 3)
    res[f"ms_per_query_ef{ef}"] = round(dt / Q * 1000, 2)
res["plan_uses_hnsw"] = "mem_item_emb_idx" in str(c.execute("EXPLAIN SELECT id FROM mem_item ORDER BY emb <-> %s::vector LIMIT 10",
                                                             ("[" + ",".join(map(str, qs[0])) + "]",)).fetchall())
res["table_plus_index_mb"] = round(c.execute("select pg_total_relation_size('mem_item')").fetchone()[0] / 2**20, 1)
print(json.dumps(res, indent=1))
