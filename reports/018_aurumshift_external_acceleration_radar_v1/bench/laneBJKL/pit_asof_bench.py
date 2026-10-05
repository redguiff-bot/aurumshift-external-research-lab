"""laneBJKL — PIT join avec révisions : ASOF naïf vs ASOF sur « timeline de connaissance » vs référence range+QUALIFY.

Sémantique de référence (LAB_PRIOR 004, Q3) pour une décision (symbol, T) :
  lignes connues = symbol égal, ingested_at <= T ET event_time <= T ;
  fait retenu = event_time max ; version = revision max parmi les lignes connues de ce fait.
Données synthétiques seedées : révisions (rev0..2), révisions inférieures arrivant en retard (S4b),
lignes à horloge biaisée (ingested_at < event_time), ex aequo d'ingestion.
Usage : python pit_asof_bench.py N_ROWS N_DECISIONS N_REF [SKEW_FRAC]
"""
import json, sys, time
import numpy as np, polars as pl, duckdb

N = int(sys.argv[1]) if len(sys.argv) > 1 else 1_000_000
M = int(sys.argv[2]) if len(sys.argv) > 2 else 200_000
NREF = int(sys.argv[3]) if len(sys.argv) > 3 else 2_000
SKEW = float(sys.argv[4]) if len(sys.argv) > 4 else 0.001
S = 50
rng = np.random.default_rng(18)

# ---- génération ----
nfacts = int(N / 1.25)
sym = rng.integers(0, S, nfacts)
order = np.argsort(sym, kind="stable"); sym = sym[order]
gaps = rng.integers(1, 2000, nfacts)  # ms
et = np.zeros(nfacts, dtype=np.int64)
for s in range(S):  # event_time croissant par symbole
    m = sym == s
    et[m] = 1_700_000_000_000 + np.cumsum(gaps[m])
nrev = 1 + (rng.random(nfacts) < 0.20) + (rng.random(nfacts) < 0.05)
fi = np.repeat(np.arange(nfacts), nrev)
rev = np.concatenate([np.arange(k) for k in nrev])
lag0 = rng.exponential(80, nfacts).astype(np.int64)  # ms
ing = et[fi] + lag0[fi] + rev * rng.integers(1_000, 300_000, len(fi))
# S4b : 2 % des faits révisés -> rev0 arrive APRÈS rev1
multi = np.where(nrev >= 2)[0]
swap = rng.choice(multi, int(0.02 * len(multi)), replace=False)
start = np.concatenate([[0], np.cumsum(nrev)[:-1]])
i0, i1 = start[swap], start[swap] + 1
ing[i0], ing[i1] = ing[i1].copy(), ing[i0].copy()
# biais d'horloge : ingested_at < event_time
sk = rng.random(len(fi)) < SKEW
ing[sk] = et[fi][sk] - rng.integers(1, 200, sk.sum())
# ex aequo d'ingestion : arrondi à 10 ms
ing = (ing // 10) * 10
obs = pl.DataFrame({"symbol": sym[fi].astype(np.int32), "event_time": et[fi], "revision": rev.astype(np.int32),
                    "ingested_at": ing, "value": rng.normal(100, 1, len(fi))})
lo, hi = obs["ingested_at"].quantile(0.05), obs["ingested_at"].max()
dec = pl.DataFrame({"did": np.arange(M), "symbol": rng.integers(0, S, M).astype(np.int32),
                    "T": rng.integers(int(lo), int(hi), M)})
res = {"n_rows": obs.height, "n_facts": nfacts, "n_decisions": M, "n_ref": NREF, "skew_frac": SKEW,
       "late_lower_rev_facts": int(len(swap)), "skew_rows": int(sk.sum()),
       "versions": {"polars": pl.__version__, "duckdb": duckdb.__version__}}

def tm(f):
    t = time.perf_counter(); r = f(); return r, round(time.perf_counter() - t, 3)

con = duckdb.connect(); con.execute("SET threads=4")
con.register("obs_df", obs.to_arrow()); con.register("dec_df", dec.to_arrow())
con.execute("CREATE TABLE obs AS SELECT * FROM obs_df"); con.execute("CREATE TABLE dec AS SELECT * FROM dec_df")

# ---- référence : range join + QUALIFY (forme 004) sur un sous-échantillon ----
ref, t_ref = tm(lambda: pl.from_arrow(con.execute(f"""
  SELECT d.did, o.event_time, o.revision, o.value FROM (SELECT * FROM dec WHERE did < {NREF}) d
  JOIN obs o ON o.symbol=d.symbol AND o.ingested_at<=d.T AND o.event_time<=d.T
  QUALIFY row_number() OVER (PARTITION BY d.did ORDER BY o.event_time DESC, o.revision DESC)=1
""").arrow()).sort("did"))
res["t_ref_range_qualify_s"] = t_ref

# ---- timeline de connaissance : available_at = greatest(ingested_at, event_time),
#      état = cummax lexicographique (event_time, revision) par symbole ----
def build_timeline(df):
    k = (df.with_columns(avail=pl.max_horizontal("ingested_at", "event_time"),
                         key=pl.col("event_time") * 4 + pl.col("revision"))
         .sort(["symbol", "avail", "key"]))
    k = k.with_columns(best=pl.col("key").cum_max().over("symbol"))
    k = k.group_by(["symbol", "avail"], maintain_order=True).agg(pl.col("best").last())
    vals = df.select("symbol", key=pl.col("event_time") * 4 + pl.col("revision"), v="value", et="event_time", rv="revision")
    return k.join(vals, left_on=["symbol", "best"], right_on=["symbol", "key"], how="left").sort(["symbol", "avail"])

def pl_timeline_asof():
    tl = build_timeline(obs)
    return dec.sort("T").join_asof(tl, left_on="T", right_on="avail", by="symbol", strategy="backward") \
              .select("did", event_time="et", revision="rv", value="v").sort("did")
pl_tl, t_pl_tl = tm(pl_timeline_asof); res["t_polars_timeline_asof_s"] = t_pl_tl

def duck_timeline_asof():
    return pl.from_arrow(con.execute("""
      WITH k AS (SELECT symbol, greatest(ingested_at, event_time) AS avail, event_time*4+revision AS key FROM obs),
      c AS (SELECT symbol, avail, max(key) OVER (PARTITION BY symbol ORDER BY avail, key ROWS UNBOUNDED PRECEDING) AS best,
                   row_number() OVER (PARTITION BY symbol, avail ORDER BY key DESC) AS rn FROM k),
      tl AS (SELECT c.symbol, c.avail, o.event_time, o.revision, o.value FROM c
             JOIN obs o ON o.symbol=c.symbol AND o.event_time*4+o.revision=c.best WHERE c.rn=1)
      SELECT d.did, tl.event_time, tl.revision, tl.value FROM dec d ASOF LEFT JOIN tl
        ON d.symbol=tl.symbol AND d.T >= tl.avail ORDER BY d.did""").arrow())
du_tl, t_du_tl = tm(duck_timeline_asof); res["t_duckdb_timeline_asof_s"] = t_du_tl
# NB : rn=1 + cummax : dernier état à un instant avail = cummax de toutes les lignes avail' <= avail (ORDER BY avail,key) ;
#      la ligne rn=1 (key max à cet avail) est la dernière de la fenêtre pour cet avail -> état final correct.

# ---- naïfs ----
def pl_naive(on):
    o = obs.sort(["symbol", on])
    return dec.sort("T").join_asof(o, left_on="T", right_on=on, by="symbol", strategy="backward") \
              .select("did", "event_time", "revision", "value", ing="ingested_at").sort("did")
pl_et, t1 = tm(lambda: pl_naive("event_time")); pl_ing, t2 = tm(lambda: pl_naive("ingested_at"))
res["t_polars_naive_asof_event_time_s"] = t1; res["t_polars_naive_asof_ingested_s"] = t2
du_ing, t3 = tm(lambda: pl.from_arrow(con.execute(
    "SELECT d.did, o.event_time, o.revision, o.value, o.ingested_at AS ing FROM dec d ASOF LEFT JOIN obs o "
    "ON d.symbol=o.symbol AND d.T >= o.ingested_at ORDER BY d.did").arrow()))
res["t_duckdb_naive_asof_ingested_s"] = t3

def cmp(a, name):
    a = a.filter(pl.col("did") < NREF)
    base = pl.DataFrame({"did": np.arange(NREF)})
    j = base.join(ref, on="did", how="left").join(a, on="did", how="left", suffix="_x")
    bad = j.filter(pl.col("event_time").ne_missing(pl.col("event_time_x")) |
                   pl.col("revision").ne_missing(pl.col("revision_x")) |
                   pl.col("value").ne_missing(pl.col("value_x")))
    res[f"diff_vs_ref_{name}"] = int(bad.height)
    return bad

for n, a in [("polars_timeline", pl_tl), ("duckdb_timeline", du_tl), ("polars_naive_event_time", pl_et),
             ("polars_naive_ingested", pl_ing), ("duckdb_naive_ingested", du_ing)]:
    cmp(a.select("did", "event_time", "revision", "value"), n)
res["ref_rows_with_match"] = ref.height
# lookahead sur l'ensemble des décisions (pas seulement l'échantillon)
def lookahead(a, name):
    j = a.join(dec, on="did").join(obs.select("symbol", "event_time", "revision", "ingested_at"),
                                   on=["symbol", "event_time", "revision"], how="left")
    res[f"lookahead_{name}"] = int(j.filter((pl.col("ingested_at") > pl.col("T")) | (pl.col("event_time") > pl.col("T"))).height)
for n, a in [("polars_timeline", pl_tl), ("duckdb_timeline", du_tl), ("polars_naive_event_time", pl_et),
             ("polars_naive_ingested", pl_ing), ("duckdb_naive_ingested", du_ing)]:
    lookahead(a.select("did", "event_time", "revision", "value"), n)
res["polars_vs_duckdb_timeline_full_equal"] = bool(pl_tl.select("did", "event_time", "revision", "value").equals(
    du_tl.cast({"did": pl.Int64}).select("did", "event_time", "revision", "value").cast(pl_tl.select("did","event_time","revision","value").schema)))

# ---- snapshot de flotte à un T (gel d'un DecisionInput) : forme 004 ----
T0 = int(obs["ingested_at"].quantile(0.6))
snap_pl, t4 = tm(lambda: obs.filter((pl.col("ingested_at") <= T0) & (pl.col("event_time") <= T0))
                 .sort(["symbol", "event_time", "revision"], descending=[False, True, True])
                 .group_by("symbol", maintain_order=True).first().sort("symbol"))
snap_du, t5 = tm(lambda: pl.from_arrow(con.execute(f"""SELECT * FROM obs WHERE ingested_at<={T0} AND event_time<={T0}
   QUALIFY row_number() OVER (PARTITION BY symbol ORDER BY event_time DESC, revision DESC)=1 ORDER BY symbol""").arrow()))
res["t_snapshot_polars_s"] = t4; res["t_snapshot_duckdb_s"] = t5
res["snapshot_equal"] = bool(snap_pl.select("symbol", "event_time", "revision", "value").equals(
    snap_du.select("symbol", "event_time", "revision", "value")))
print(json.dumps(res, indent=1))
