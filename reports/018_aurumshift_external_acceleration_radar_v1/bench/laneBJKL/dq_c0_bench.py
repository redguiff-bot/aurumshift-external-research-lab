"""laneBJKL — Qualité de données « observation C0 » : Pandera (backend polars et pandas) vs Polars écrit à la main.
Frame synthétique seedé (venue, symbol, event_time, ingested_at, bid, ask, depth) + fautes injectées à compte connu.
Usage : python dq_c0_bench.py [N]"""
import json, sys, time
import numpy as np, polars as pl, pandas as pd
import pandera.polars as pap
import pandera.pandas as pa
from pandera.api.polars.types import PolarsData

N = int(sys.argv[1]) if len(sys.argv) > 1 else 1_000_000
MAX_LAG_MS, MAX_GAP_MS = 5_000, 60_000
rng = np.random.default_rng(18)
venues, syms = ["binance", "okx", "bybit"], [f"S{i:02d}" for i in range(22)]
K = len(venues) * len(syms); per = N // K
rows = []
for vi, v in enumerate(venues):
    for si, s in enumerate(syms):
        et = 1_790_000_000_000 + np.cumsum(rng.integers(500, 1500, per))
        rows.append(pl.DataFrame({"venue": [v] * per, "symbol": [s] * per, "event_time": et,
                                  "ingested_at": et + rng.integers(5, 300, per),
                                  "bid": 100 + rng.normal(0, 1, per).cumsum() * 0.01}))
df = pl.concat(rows).with_columns(ask=pl.col("bid") + 0.01 + pl.lit(rng.exponential(0.02, N - N % K if False else per * K)),
                                  depth=pl.lit(rng.exponential(5, per * K)))
n = df.height
inj = {}
def pick(k): return rng.choice(np.arange(1, n - 1), k, replace=False)
ev, ing, bid, ask, dep = (df[c].to_numpy().copy() for c in ("event_time", "ingested_at", "bid", "ask", "depth"))
i = pick(37); ask[i] = bid[i] - 0.05; inj["crossed_bid_ge_ask"] = 37
i = pick(23); ing[i] = ev[i] - 50; inj["ingested_before_event"] = 23
i = pick(41); ing[i] = ev[i] + 20_000; inj["stale_lag_gt_5s"] = 41
i = pick(11); dep[i] = -1.0; inj["negative_depth"] = 11
# 9 sauts temporels > 60 s (décalage de toute la suite du flux) -> 9 gaps
for j in rng.choice(np.arange(K), 9, replace=False):
    a = j * per + per // 2; ev[a:(j + 1) * per] += 120_000; ing[a:(j + 1) * per] += 120_000
inj["gaps_gt_60s"] = 9
# 7 inversions locales d'ordre (non monotone) loin des gaps
nm = rng.choice(np.arange(K), 7, replace=False)
for j in nm:
    a = j * per + per // 4; ev[a], ev[a + 1] = ev[a + 1], ev[a]
inj["non_monotonic_pairs"] = 7
df = df.with_columns(event_time=pl.Series(ev), ingested_at=pl.Series(ing), bid=pl.Series(bid), ask=pl.Series(ask), depth=pl.Series(dep))
# 5 doublons exacts
dups = df[pick(5).tolist()]; df = pl.concat([df, dups]); inj["duplicate_rows"] = 5
# 6 bids nuls
nb = df["bid"].to_numpy().copy(); nb = nb.astype(object); idx = pick(6); nb[idx] = None
df = df.with_columns(bid=pl.Series(nb.tolist(), dtype=pl.Float64)); inj["null_bid"] = 6
df = df.sort(["venue", "symbol"], maintain_order=True)  # garde l'ordre d'arrivée intra-flux

# ---------------- écrit à la main (Polars) ----------------
# HAND_BEGIN
def hand(d: pl.DataFrame) -> dict:
    g = ["venue", "symbol"]
    d = d.with_columns(dt=pl.col("event_time").diff().over(g))
    return d.select(
        crossed=(pl.col("bid") >= pl.col("ask")).sum(),
        ing_before_ev=(pl.col("ingested_at") < pl.col("event_time")).sum(),
        stale=((pl.col("ingested_at") - pl.col("event_time")) > MAX_LAG_MS).sum(),
        neg_depth=(pl.col("depth") < 0).sum(),
        null_bid=pl.col("bid").is_null().sum(),
        non_monotonic=(pl.col("dt") < 0).sum(),
        gaps=(pl.col("dt") > MAX_GAP_MS).sum(),
        dup_keys=pl.struct(*g, "event_time").is_duplicated().sum(),
    ).row(0, named=True)
# HAND_END

# ---------------- Pandera polars ----------------
# PAP_BEGIN
G = ["venue", "symbol"]
class C0Obs(pap.DataFrameModel):
    venue: str = pap.Field(isin=venues)
    symbol: str
    event_time: int
    ingested_at: int
    bid: float = pap.Field(gt=0, nullable=False)
    ask: float = pap.Field(gt=0)
    depth: float = pap.Field(ge=0)

    class Config:
        unique = ["venue", "symbol", "event_time"]

    @pap.dataframe_check
    def bid_lt_ask(cls, d: PolarsData) -> pl.LazyFrame:
        return d.lazyframe.select(pl.col("bid") < pl.col("ask"))

    @pap.dataframe_check
    def ingested_after_event(cls, d: PolarsData) -> pl.LazyFrame:
        return d.lazyframe.select(pl.col("ingested_at") >= pl.col("event_time"))

    @pap.dataframe_check
    def fresh(cls, d: PolarsData) -> pl.LazyFrame:
        return d.lazyframe.select((pl.col("ingested_at") - pl.col("event_time")) <= MAX_LAG_MS)

    @pap.dataframe_check
    def monotonic_per_stream(cls, d: PolarsData) -> pl.LazyFrame:
        return d.lazyframe.select((pl.col("event_time").diff().over(G) >= 0).fill_null(True))

    @pap.dataframe_check
    def no_gap(cls, d: PolarsData) -> pl.LazyFrame:
        return d.lazyframe.select((pl.col("event_time").diff().over(G) <= MAX_GAP_MS).fill_null(True))
# PAP_END

# ---------------- Pandera pandas ----------------
# PA_BEGIN
def _dt(df): return df.groupby(["venue", "symbol"], sort=False)["event_time"].diff()
c0_pd = pa.DataFrameSchema({
    "venue": pa.Column(str, pa.Check.isin(venues)), "symbol": pa.Column(str),
    "event_time": pa.Column("int64"), "ingested_at": pa.Column("int64"),
    "bid": pa.Column(float, pa.Check.gt(0), nullable=False), "ask": pa.Column(float, pa.Check.gt(0)),
    "depth": pa.Column(float, pa.Check.ge(0))},
    checks=[pa.Check(lambda d: d["bid"] < d["ask"], name="bid_lt_ask"),
            pa.Check(lambda d: d["ingested_at"] >= d["event_time"], name="ingested_after_event"),
            pa.Check(lambda d: (d["ingested_at"] - d["event_time"]) <= MAX_LAG_MS, name="fresh"),
            pa.Check(lambda d: _dt(d).fillna(0) >= 0, name="monotonic_per_stream"),
            pa.Check(lambda d: _dt(d).fillna(0) <= MAX_GAP_MS, name="no_gap")],
    unique=["venue", "symbol", "event_time"])
# PA_END

def loc(tag):
    src = open(__file__).read().split(f"# {tag}_BEGIN")[1].split(f"# {tag}_END")[0]
    return sum(1 for l in src.splitlines() if l.strip() and not l.strip().startswith("#"))

res = {"n_rows": df.height, "injected": inj, "versions": {"pandera": __import__("pandera").__version__, "polars": pl.__version__, "pandas": pd.__version__},
       "loc": {"hand_polars": loc("HAND"), "pandera_polars": loc("PAP"), "pandera_pandas": loc("PA")}}
t = time.perf_counter(); h = hand(df); res["t_hand_polars_s"] = round(time.perf_counter() - t, 3); res["hand_counts"] = h

t = time.perf_counter()
try:
    C0Obs.validate(df, lazy=True); res["pandera_polars"] = "PASSED?!"
except pap.errors.SchemaErrors as e:
    fc = e.failure_cases
    res["t_pandera_polars_s"] = round(time.perf_counter() - t, 3)
    res["pandera_polars_failures_by_check"] = {str(k): int(v) for k, v in
        fc.group_by("check").len().sort("check").iter_rows()}
pdf = df.to_pandas()
t = time.perf_counter()
try:
    c0_pd.validate(pdf, lazy=True); res["pandera_pandas"] = "PASSED?!"
except pa.errors.SchemaErrors as e:
    res["t_pandera_pandas_s"] = round(time.perf_counter() - t, 3)
    res["pandera_pandas_failures_by_check"] = {str(k): int(v) for k, v in e.failure_cases.groupby("check").size().items()}
    res["pandera_pandas_unique_rows_by_check"] = {str(k): int(v) for k, v in e.failure_cases.groupby("check")["index"].nunique().items()}
print(json.dumps(res, indent=1, default=str))
