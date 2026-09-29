"""Comparaison des jointures PIT « dernier fait connu à T » : SQL de référence vs Feast (algorithme extrait) vs DuckDB/Polars/pandas.
Verdict mécanique par moteur : LOOKAHEAD_DETECTED si un résultat utilise une ligne dont ingested_at > T."""
import os; os.environ["PITDB"] = "pitx"; os.environ["PITNOSAVE"] = "1"
import json, datetime as dt
import duckdb, polars as pl, pandas as pd
from common import *
import scenarios

assert scenarios.run(), "batterie de référence en échec"
ctx = scenarios.run.ctx; rows = ctx["rows"]; lab = ctx["lab"]
UTC = dt.timezone.utc
pairs = sorted({(c[2], c[3]) for c in ctx["checks"]}, key=lambda x: (x[0], x[1]))
conn = connect()
byid = {r["obs_id"]: r for r in rows}
A = [r for r in rows if r["source"] == "A"]
df = pd.DataFrame([{k: r[k] for k in ("obs_id","instrument","event_time","revision","ingested_at")} for r in A])
for c in ("event_time","ingested_at"): df[c] = pd.to_datetime(df[c], utc=True).dt.tz_convert(None)
df["rev"] = df["revision"].astype("float64").fillna(-1e9)
q = pd.DataFrame([{"instrument": i, "T": pd.Timestamp(T).tz_convert("UTC").tz_localize(None)} for i, T in pairs])

def ref(i, T):
    r = conn.execute("SELECT obs_id FROM pit.latest_known(%s,'A',%s,'5m')", (T, i)).fetchall()
    return r[0][0] if r else None

def feast(created_filter):
    out = {}
    for i, T in pairs:
        cand = [r for r in A if r["instrument"] == i and r["event_time"] <= T and (not created_filter or r["ingested_at"] <= T)]
        if cand:
            m = max(cand, key=lambda r: (r["event_time"], r["ingested_at"], r["obs_id"]))  # ORDER BY event_timestamp DESC, created_timestamp DESC
            out[(i, T)] = m["obs_id"]
        else: out[(i, T)] = None
    return out

def duck(sql):
    con = duckdb.connect(); con.register("o", df); con.register("q", q)
    res = con.execute(sql).df()
    return {(r.instrument, pairs[j][1]): (None if pd.isna(r.obs_id) else int(r.obs_id)) for j, r in enumerate(res.itertuples())} if False else res
def by_pair(res):
    m = {}
    for r in res.itertuples():
        key = next(p for p in pairs if p[0] == r.instrument and pd.Timestamp(p[1]).tz_convert("UTC").tz_localize(None) == r.T)
        m[key] = None if pd.isna(r.obs_id) else int(r.obs_id)
    return m

engines = {}
engines["feast_default(event_timestamp<=T)"] = feast(False)
engines["feast_filter_by_created_timestamp"] = feast(True)
engines["duckdb_ASOF_on_event_time"] = by_pair(duck("SELECT q.instrument, q.T, o.obs_id FROM q ASOF LEFT JOIN o ON q.instrument=o.instrument AND q.T >= o.event_time"))
engines["duckdb_ASOF_on_ingested_at"] = by_pair(duck("SELECT q.instrument, q.T, o.obs_id FROM q ASOF LEFT JOIN o ON q.instrument=o.instrument AND q.T >= o.ingested_at"))
engines["duckdb_range_join_QUALIFY"] = by_pair(duck("""SELECT instrument, T, obs_id FROM (
   SELECT q.instrument, q.T, o.obs_id, row_number() OVER (PARTITION BY q.instrument, q.T ORDER BY o.event_time DESC, o.rev DESC, o.ingested_at DESC, o.obs_id DESC) rn
   FROM q LEFT JOIN o ON q.instrument=o.instrument AND o.ingested_at <= q.T) WHERE rn=1"""))
# Polars
pdf = pl.from_pandas(df); pq = pl.from_pandas(q)
def pol_asof(on):
    r = pq.sort("T").join_asof(pdf.sort(on), left_on="T", right_on=on, by="instrument", strategy="backward")
    return {(x["instrument"], next(p[1] for p in pairs if p[0]==x["instrument"] and pd.Timestamp(p[1]).tz_convert("UTC").tz_localize(None)==x["T"])): x["obs_id"] for x in r.to_dicts()}
engines["polars_join_asof_on_event_time"] = pol_asof("event_time")
def pol_correct():
    r = (pq.join_where(pdf, pl.col("instrument") == pl.col("instrument_right"), pl.col("ingested_at") <= pl.col("T")) if False else
         pq.join(pdf, on="instrument", how="left").filter(pl.col("ingested_at").is_null() | (pl.col("ingested_at") <= pl.col("T")))
         .sort(["instrument","T","event_time","rev","ingested_at","obs_id"], descending=[False,False,True,True,True,True])
         .group_by(["instrument","T"], maintain_order=True).first())
    return {(x["instrument"], next(p[1] for p in pairs if p[0]==x["instrument"] and pd.Timestamp(p[1]).tz_convert("UTC").tz_localize(None)==x["T"])): x["obs_id"] for x in r.to_dicts()}
engines["polars_filter_then_group_first"] = pol_correct()
# pandas merge_asof
r = pd.merge_asof(q.sort_values("T"), df.sort_values("event_time"), left_on="T", right_on="event_time", by="instrument")
engines["pandas_merge_asof_on_event_time"] = {next(p for p in pairs if p[0]==x.instrument and pd.Timestamp(p[1]).tz_convert("UTC").tz_localize(None)==x.T): (None if pd.isna(x.obs_id) else int(x.obs_id)) for x in r.itertuples()}

report = {}
for name, res in engines.items():
    leaks, wrong = [], []
    for (i, T) in pairs:
        got = res.get((i, T)); exp = ref(i, T)
        if got is not None and not pd.isna(got): got = int(got)
        else: got = None
        if got is not None and byid[got]["ingested_at"] > T: leaks.append({"instrument": i, "T": T, "leaked": lab[got]})
        elif got != exp: wrong.append({"instrument": i, "T": T, "got": lab.get(got), "expected": lab.get(exp)})
    report[name] = {"pairs": len(pairs), "leaks": len(leaks), "wrong_no_leak": len(wrong),
                    "verdict": "LOOKAHEAD_DETECTED" if leaks else ("WRONG_RESULT_NO_LEAK" if wrong else "LOOKAHEAD_PREVENTED_AND_EQUAL_TO_REFERENCE"),
                    "leak_examples": leaks[:4], "wrong_examples": wrong[:4]}
save("joins.json", report)
for k, v in report.items(): print(f"{k:42s} {v['verdict']:45s} leaks={v['leaks']} wrong={v['wrong_no_leak']}")
