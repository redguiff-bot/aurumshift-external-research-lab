"""DuckDB/Polars fleet-wide as-of sur 1,1M lignes vs pit.asof (axe STRICT ingested_at)."""
import time, json, datetime as dt, duckdb, polars as pl
from common import *
c = connect("pitlab")
T = c.execute("SELECT percentile_disc(0.6) WITHIN GROUP (ORDER BY ingested_at) FROM pit.obs").fetchone()[0]
t0 = time.time(); ref = {r[0] for r in c.execute("SELECT obs_id FROM pit.asof(%s)", (T,)).fetchall()}; t_sql = time.time() - t0
cols = "obs_id,source,instrument,timeframe,event_time,revision,ingested_at"
rows = c.execute(f"SELECT {cols} FROM pit.obs").fetchall()
df = pl.DataFrame(rows, schema=cols.split(","), orient="row")
out = {"T": str(T), "rows": df.height, "pg_pit_asof_s": round(t_sql, 2), "ref_size": len(ref)}
t0 = time.time()
p = (df.filter(pl.col("ingested_at") <= T)
       .sort(["source","instrument","timeframe","event_time","revision","ingested_at","obs_id"],
             descending=[False]*4 + [True]*3, nulls_last=True)
       .group_by(["source","instrument","timeframe","event_time"], maintain_order=True).first())
out["polars_s"] = round(time.time() - t0, 2); out["polars_equal"] = set(p["obs_id"].to_list()) == ref
d = duckdb.connect(); d.register("o", df.to_arrow()); t0 = time.time()
q = d.execute("""SELECT obs_id FROM o WHERE ingested_at <= ? QUALIFY row_number() OVER (
   PARTITION BY source,instrument,timeframe,event_time
   ORDER BY revision DESC NULLS LAST, ingested_at DESC, obs_id DESC)=1""", [T]).fetchall()
out["duckdb_s"] = round(time.time() - t0, 2); out["duckdb_equal"] = {r[0] for r in q} == ref
save("fleet_offline.json", out); print(json.dumps(out, indent=1))
