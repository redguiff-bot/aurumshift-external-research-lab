"""T09 — data-quality frameworks on 1-minute bars: clean frame must pass, each of 12 single-defect variants must fail.
Shared derived columns (dts, absret, flat_run, stale_run) are computed once outside the frameworks (needed by all of them)."""
import sys, json, time, os, warnings, tempfile; warnings.filterwarnings("ignore")
sys.path.insert(0, __file__.rsplit("/", 1)[0])
import numpy as np, pandas as pd
import dq_data as q
fw = sys.argv[1]; LO = 946684800000; HI = q.ASOF_MS
def derive(d):
    d = d.copy(); d["dts"] = d.ts.diff().fillna(60000); d["absret"] = np.log(d.close).diff().abs().fillna(0)
    z = (d.volume == 0).astype(int); d["flat_run"] = z.groupby((z != z.shift()).cumsum()).cumsum()
    same = (d.close == d.close.shift()) & (d.volume == d.volume.shift()); d["stale_run"] = same.astype(int).groupby((~same).cumsum()).cumsum()
    return d
V = {k: derive(v) for k, v in q.variants().items()}
native = {}
if fw == "pandera":
    import pandera.pandas as pa
    C, K = pa.Column, pa.Check
    schema = pa.DataFrameSchema({
        "ts": C(int, [K.in_range(LO, HI)], unique=True), "open": C(float, K.gt(0)), "high": C(float, K.gt(0)), "low": C(float, K.gt(0)), "close": C(float, K.gt(0)),
        "volume": C(float, K.ge(0)), "dts": C(float, K.eq(60000)), "absret": C(float, K.lt(0.2)), "flat_run": C(int, K.lt(10)), "stale_run": C(int, K.lt(10))},
        checks=[K(lambda d: d.ts.is_monotonic_increasing, name="monotonic"), K(lambda d: d.high >= d[["open", "close", "low"]].max(axis=1), name="high_ge_all"), K(lambda d: d.low <= d[["open", "close", "high"]].min(axis=1), name="low_le_all")], coerce=False)
    def check(d):
        try: schema.validate(d, lazy=True); return True
        except pa.errors.SchemaErrors as e: return False
    native = dict(null="native(nullable default False)", unique="native", range="native", monotonic="custom lambda", cross_column="custom lambda", gaps="derived col + native eq", flat_run="derived + native", spike="derived + native")
elif fw == "great_expectations":
    import great_expectations as gx, great_expectations.expectations as E
    ctx = gx.get_context(mode="ephemeral"); ds = ctx.data_sources.add_pandas("p"); asset = ds.add_dataframe_asset("a"); bd = asset.add_batch_definition_whole_dataframe("b")
    exps = [E.ExpectColumnValuesToNotBeNull(column=c) for c in ("ts", "open", "high", "low", "close", "volume")]
    exps += [E.ExpectColumnValuesToBeUnique(column="ts"), E.ExpectColumnValuesToBeIncreasing(column="ts", strictly=True), E.ExpectColumnValuesToBeBetween(column="ts", min_value=LO, max_value=HI),
             E.ExpectColumnValuesToBeBetween(column="volume", min_value=0), E.ExpectColumnValuesToBeBetween(column="dts", min_value=60000, max_value=60000),
             E.ExpectColumnValuesToBeBetween(column="absret", max_value=0.2, strict_max=True), E.ExpectColumnValuesToBeBetween(column="flat_run", max_value=10, strict_max=True),
             E.ExpectColumnValuesToBeBetween(column="stale_run", max_value=10, strict_max=True)]
    for a, b in (("high", "low"), ("high", "open"), ("high", "close"), ("open", "low"), ("close", "low")):
        exps.append(E.ExpectColumnPairValuesAToBeGreaterThanB(column_A=a, column_B=b, or_equal=True))
    suite = gx.ExpectationSuite(name="s", expectations=exps)
    def check(d):
        r = bd.get_batch(batch_parameters={"dataframe": d}).validate(suite); return bool(r.success)
    native = dict(null="native", unique="native", range="native", monotonic="native (strictly increasing)", cross_column="native (pair A>=B)", gaps="derived col + native", flat_run="derived + native", spike="derived + native")
elif fw == "pointblank":
    import pointblank as pb
    def check(d):
        v = (pb.Validate(data=d, thresholds=pb.Thresholds(warning=1, error=1, critical=1)).col_vals_not_null(columns=["ts", "open", "high", "low", "close", "volume"])
             .rows_distinct(columns_subset=["ts"]).col_vals_between("ts", LO, HI).col_vals_ge("volume", 0).col_vals_eq("dts", 60000)
             .col_vals_lt("absret", 0.2).col_vals_lt("flat_run", 10).col_vals_lt("stale_run", 10)
             .col_vals_ge("high", pb.col("low")).col_vals_ge("high", pb.col("open")).col_vals_ge("high", pb.col("close")).col_vals_le("low", pb.col("open")).col_vals_le("low", pb.col("close"))
             .interrogate())
        return bool(v.all_passed())
    native = dict(null="native", unique="native rows_distinct", range="native", monotonic="NOT native (would need dts>0 derived)", cross_column="native col(...)", gaps="derived + native", flat_run="derived + native", spike="derived + native")
elif fw == "frictionless":
    from frictionless import Resource, Schema, fields, validate
    sch = Schema(fields=[fields.IntegerField(name="ts", constraints=dict(required=True, unique=True, minimum=LO, maximum=HI)),
        *[fields.NumberField(name=c, constraints=dict(required=True, minimum=(0 if c == "volume" else 1e-9))) for c in ("open", "high", "low", "close", "volume")]])
    tmp = tempfile.mkdtemp()
    def check(d):
        p = os.path.join(tmp, "b.csv"); d[["ts", "open", "high", "low", "close", "volume"]].to_csv(p, index=False)
        return bool(validate(Resource(path="b.csv", basepath=tmp, schema=sch)).valid)
    native = dict(null="native (required)", unique="native", range="native", monotonic="NOT native", cross_column="NOT native", gaps="NOT native", flat_run="NOT native", spike="NOT native")
res = dict(framework=fw, native_support=native, per_variant={})
t = time.perf_counter(); ok = check(V["clean"]); res["clean_pass"] = ok; res["clean_seconds_200k_rows"] = round(time.perf_counter()-t, 2)
for k in q.DEFECTS:
    try: res["per_variant"][k] = "DETECTED" if not check(V[k]) else "MISSED"
    except Exception as e: res["per_variant"][k] = "ERROR " + repr(e)[:120]
res["detected"] = sum(v == "DETECTED" for v in res["per_variant"].values()); res["n_defects"] = len(q.DEFECTS)
print(json.dumps(res))
