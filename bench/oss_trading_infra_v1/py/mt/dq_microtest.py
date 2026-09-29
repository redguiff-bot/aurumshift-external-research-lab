"""Data-quality frameworks vs injected faults in a 1-min OHLCV frame (ground truth known).
Faults: F1 high<low (5 rows), F2 negative price (3), F3 duplicate timestamps (4), F4 non-monotonic ts (1 swap), F5 time gaps (10 missing minutes),
F6 zero-volume flat bars (20), F7 price spike >20% (2), F8 NaN close (3). Each framework is asked to express the checks it natively can."""
import warnings, os; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd, json, time, importlib.metadata as md, io
from common import *
base = synth(3000, seed=5).reset_index().rename(columns={"index": "ts"})
df = base.copy()
rng = np.random.default_rng(0)
idx = {}
def pick(k, n): idx[k] = sorted(rng.choice(np.arange(100, 2900), n, replace=False)); return idx[k]
for i in pick("F1", 5): df.loc[i, "high"], df.loc[i, "low"] = df.loc[i, "low"] - .5, df.loc[i, "high"] + .5
for i in pick("F2", 3): df.loc[i, "close"] = -1.0
for i in pick("F6", 20): df.loc[i, ["open", "high", "low", "close", "volume"]] = [df.loc[i-1, "close"]] * 4 + [0.0]
for i in pick("F7", 2): df.loc[i, "close"] = df.loc[i-1, "close"] * 1.3
for i in pick("F8", 3): df.loc[i, "close"] = np.nan
truth = {"F1_high_lt_low": 5, "F2_negative": 3, "F6_zero_vol": 20, "F7_spike": 2, "F8_nan": 3}
# F5 gaps: drop 10 rows ; F3 dup: append 4 dup rows ; F4: swap two rows
gap_rows = sorted(rng.choice(np.arange(200, 2800), 10, replace=False)); df = df.drop(index=gap_rows)
df = pd.concat([df, df.iloc[[300, 400, 500, 600]]]).reset_index(drop=True)
df.loc[[1000, 1001], :] = df.loc[[1001, 1000], :].values
truth.update({"F5_gap_minutes": 10, "F3_dup_rows": 4, "F4_non_monotonic_pairs": 1})
res = {"truth": truth}
# --- pandera
import pandera.pandas as pa
t0 = time.perf_counter()
schema = pa.DataFrameSchema({
  "ts": pa.Column(pa.DateTime, nullable=False, unique=True, checks=pa.Check(lambda s: s.is_monotonic_increasing, name="monotonic", element_wise=False)),
  "open": pa.Column(float, pa.Check.gt(0)), "high": pa.Column(float, pa.Check.gt(0)), "low": pa.Column(float, pa.Check.gt(0)),
  "close": pa.Column(float, [pa.Check.gt(0)], nullable=False), "volume": pa.Column(float, pa.Check.ge(0)),
}, checks=[pa.Check(lambda d: d["high"] >= d[["open", "close", "low"]].max(axis=1), name="high_is_max"),
           pa.Check(lambda d: d["low"] <= d[["open", "close", "high"]].min(axis=1), name="low_is_min")], coerce=True)
try:
    schema.validate(df.assign(ts=df.ts.dt.tz_localize(None)), lazy=True)
    res["pandera"] = {"raised": False}
except pa.errors.SchemaErrors as e:
    fc = e.failure_cases
    res["pandera"] = {"raised": True, "n_failure_cases": len(fc), "by_check": fc.groupby("check").size().to_dict(), "seconds": round(time.perf_counter() - t0, 3), "version": md.version("pandera")}
# --- great_expectations (v1 API, ephemeral in-memory context, pandas datasource)
try:
    import great_expectations as gx, great_expectations.expectations as gxe
    t0 = time.perf_counter()
    ctx = gx.get_context(mode="ephemeral")
    src = ctx.data_sources.add_pandas("p"); asset = src.add_dataframe_asset("a"); bd = asset.add_batch_definition_whole_dataframe("b")
    batch = bd.get_batch(batch_parameters={"dataframe": df.assign(ts=df.ts.dt.tz_localize(None))})
    exps = [gxe.ExpectColumnValuesToBeUnique(column="ts"), gxe.ExpectColumnValuesToBeBetween(column="close", min_value=0, strict_min=True),
            gxe.ExpectColumnValuesToNotBeNull(column="close"), gxe.ExpectColumnValuesToBeIncreasing(column="ts"),
            gxe.ExpectColumnPairValuesAToBeGreaterThanB(column_A="high", column_B="low", or_equal=True),
            gxe.ExpectColumnValuesToBeBetween(column="volume", min_value=0)]
    out = {}
    for e in exps:
        r = batch.validate(e); out[f"{type(e).__name__}({getattr(e,'column',getattr(e,'column_A',''))})"] = {"success": r.success, "unexpected_count": r.result.get("unexpected_count")}
    res["great_expectations"] = {"results": out, "seconds": round(time.perf_counter() - t0, 3), "version": md.version("great_expectations")}
except Exception as e: res["great_expectations"] = {"error": f"{type(e).__name__}: {str(e)[:300]}"}
# --- frictionless
try:
    from frictionless import Resource, Checklist, checks
    t0 = time.perf_counter()
    d2 = df.assign(ts=df.ts.astype(str)); csv = d2.to_csv(index=False)
    r = Resource(path="x.csv", data=None) if False else None
    import tempfile; os.chdir(tempfile.mkdtemp()); open("dq.csv", "w").write(csv)
    from frictionless import validate
    rep = validate("dq.csv", checklist=Checklist(checks=[checks.duplicate_row(), checks.deviated_value(field_name="close", average="mean", interval=3)]))
    res["frictionless"] = {"valid": rep.valid, "error_types": pd.Series([e.type for t in rep.tasks for e in t.errors]).value_counts().to_dict(), "seconds": round(time.perf_counter() - t0, 3), "version": md.version("frictionless")}
except Exception as e: res["frictionless"] = {"error": f"{type(e).__name__}: {str(e)[:300]}"}
# --- reference: what does plain pandas need for the same 8 checks? (LOC counted from this file, no framework)
def plain(d):
    return {"high_lt_low": int((d.high < d.low).sum()), "nonpos": int((d.close <= 0).sum()), "dups": int(d.ts.duplicated().sum()), "nonmono": int((d.ts.diff().dt.total_seconds() < 0).sum()),
            "nan": int(d.close.isna().sum()), "zero_vol": int((d.volume == 0).sum()), "gap_minutes_missing": int(((d.ts.drop_duplicates().sort_values().diff().dt.total_seconds().fillna(60) // 60 - 1).clip(lower=0)).sum())}
res["plain_pandas_reference"] = plain(df)
# install footprint
import subprocess, os
def size(pkg):
    try:
        dist = md.distribution(pkg); return round(sum(os.path.getsize(dist.locate_file(f)) for f in dist.files if os.path.exists(dist.locate_file(f))) / 1e6, 1)
    except Exception: return None
res["own_size_MB"] = {p: size(p) for p in ("pandera", "great-expectations", "frictionless")}
print(json.dumps(res, indent=1, default=str)); save("dq_microtest.json", res)
