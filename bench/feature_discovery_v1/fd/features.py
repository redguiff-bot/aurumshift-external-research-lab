"""Primitive feature set + targets. Every primitive at row t uses bars <= t only (bar t closed).

All primitives are rolling-standardised (720-bar past window, inclusive of t) and clipped to +-5,
except calendar features. Units column documents the raw unit before standardisation.
"""
import numpy as np, pandas as pd

WARMUP = 800
H_RET = 4      # forward return horizon (bars)
H_VOL = 24     # forward realised-vol horizon (bars)

REGISTRY = [  # name, formula, raw unit, fields, lookback(bars)
    ("ret_1h", "ln(C_t/C_{t-1})", "log-return", "close", 1),
    ("ret_4h", "ln(C_t/C_{t-4})", "log-return", "close", 4),
    ("ret_24h", "ln(C_t/C_{t-24})", "log-return", "close", 24),
    ("ret_72h", "ln(C_t/C_{t-72})", "log-return", "close", 72),
    ("ret_168h", "ln(C_t/C_{t-168})", "log-return", "close", 168),
    ("lrv_6", "ln sqrt(sum_{i<6} r_{t-i}^2)", "ln(log-return)", "close", 7),
    ("lrv_24", "ln sqrt(sum_{i<24} r_{t-i}^2)", "ln(log-return)", "close", 25),
    ("lrv_168", "ln sqrt(sum_{i<168} r_{t-i}^2)", "ln(log-return)", "close", 169),
    ("lpk_24", "ln sqrt(mean_{i<24} ln(H/L)^2/(4 ln2))", "ln(log-return)", "high,low", 24),
    ("lrng_1", "ln ln(H_t/L_t)", "ln(log-return)", "high,low", 1),
    ("clv_1", "(2C-H-L)/(H-L) at t", "dimensionless in [-1,1]", "high,low,close", 1),
    ("lvol_1", "ln(1+V_t)", "ln(base units)", "volume", 1),
    ("lvol_24", "mean_{i<24} ln(1+V_{t-i})", "ln(base units)", "volume", 24),
    ("tbr_1", "taker_buy_base_t / V_t", "fraction [0,1]", "taker_buy_base,volume", 1),
    ("tbr_24", "sum taker_buy_base / sum V over 24", "fraction [0,1]", "taker_buy_base,volume", 24),
    ("lnt_1", "ln(1+trades_t)", "ln(count)", "trades", 1),
    ("lnt_24", "mean_{i<24} ln(1+trades_{t-i})", "ln(count)", "trades", 24),
    ("lsz_1", "ln(1+V_t/(1+trades_t))", "ln(base units/trade)", "volume,trades", 1),
    ("dhi_72", "ln C_t - max_{i<72} ln H_{t-i}", "log-distance <=0", "high,close", 72),
    ("dlo_72", "ln C_t - min_{i<72} ln L_{t-i}", "log-distance >=0", "low,close", 72),
    ("mag_24", "ln C_t - ln mean_{i<24} C_{t-i}", "log-distance", "close", 24),
    ("mag_168", "ln C_t - ln mean_{i<168} C_{t-i}", "log-distance", "close", 168),
    ("lami_24", "ln(mean|r| / mean quote_vol) over 24", "ln(1/quote currency)", "close,quote_volume", 24),
    ("hod_sin", "sin(2pi*hour_utc/24)", "dimensionless", "timestamp", 0),
    ("hod_cos", "cos(2pi*hour_utc/24)", "dimensionless", "timestamp", 0),
    ("wknd", "1[day_of_week in {Sat,Sun}]", "dimensionless {0,1}", "timestamp", 0),
]
NAMES = [r[0] for r in REGISTRY]
META = {r[0]: dict(formula=r[1], unit=r[2], fields=r[3], lookback=r[4]) for r in REGISTRY}
_NOZ = {"hod_sin", "hod_cos", "wknd"}


def raw_primitives(d: pd.DataFrame) -> pd.DataFrame:
    lc = np.log(d.close)
    r1 = lc.diff()
    eps = 1e-9
    f = pd.DataFrame(index=d.index)
    f["ret_1h"] = r1
    for n in (4, 24, 72, 168):
        f[f"ret_{n}h"] = lc.diff(n)
    for n in (6, 24, 168):
        f[f"lrv_{n}"] = np.log(np.sqrt((r1 ** 2).rolling(n).sum()) + eps)
    hl = np.log(d.high / d.low)
    f["lpk_24"] = np.log(np.sqrt((hl ** 2).rolling(24).mean() / (4 * np.log(2))) + eps)
    f["lrng_1"] = np.log(hl + eps)
    rng = (d.high - d.low)
    f["clv_1"] = ((2 * d.close - d.high - d.low) / rng.where(rng > 0)).fillna(0.0)
    lv = np.log1p(d.volume)
    f["lvol_1"] = lv
    f["lvol_24"] = lv.rolling(24).mean()
    f["tbr_1"] = (d.taker_buy_base / d.volume.where(d.volume > 0)).fillna(0.5)
    f["tbr_24"] = (d.taker_buy_base.rolling(24).sum() / d.volume.rolling(24).sum().where(lambda s: s > 0)).fillna(0.5)
    lt = np.log1p(d.trades)
    f["lnt_1"] = lt
    f["lnt_24"] = lt.rolling(24).mean()
    f["lsz_1"] = np.log1p(d.volume / (1 + d.trades))
    f["dhi_72"] = lc - np.log(d.high).rolling(72).max()
    f["dlo_72"] = lc - np.log(d.low).rolling(72).min()
    f["mag_24"] = lc - np.log(d.close.rolling(24).mean())
    f["mag_168"] = lc - np.log(d.close.rolling(168).mean())
    f["lami_24"] = np.log(r1.abs().rolling(24).mean() / d.quote_volume.rolling(24).mean().where(lambda s: s > 0) + 1e-20)
    hr = d.index.hour.values
    f["hod_sin"] = np.sin(2 * np.pi * hr / 24)
    f["hod_cos"] = np.cos(2 * np.pi * hr / 24)
    f["wknd"] = (d.index.dayofweek.values >= 5).astype(float)
    return f[NAMES]


def standardise(f: pd.DataFrame, win=720) -> pd.DataFrame:
    z = f.copy()
    for c in NAMES:
        if c in _NOZ:
            continue
        x = f[c].replace([np.inf, -np.inf], np.nan)
        mu = x.rolling(win, min_periods=240).mean()
        sd = x.rolling(win, min_periods=240).std().clip(lower=1e-9)
        z[c] = ((x - mu) / sd).clip(-5, 5)
    return z


def targets(d: pd.DataFrame) -> pd.DataFrame:
    lc = np.log(d.close)
    r1 = lc.diff()
    sig_h = np.sqrt((r1 ** 2).rolling(168).mean())
    fwd = lc.shift(-H_RET) - lc
    y_ret = (fwd / (sig_h * np.sqrt(H_RET))).clip(-5, 5)
    rv_past = np.sqrt((r1 ** 2).rolling(H_VOL).sum())
    rv_fwd = np.sqrt((r1 ** 2).rolling(H_VOL).sum().shift(-H_VOL))
    y_vol = (np.log(rv_fwd + 1e-9) - np.log(rv_past + 1e-9)).clip(-3, 3)
    return pd.DataFrame({"y_ret": y_ret, "y_vol": y_vol})


def build(d: pd.DataFrame) -> pd.DataFrame:
    """features (standardised) + targets, warm-up dropped; NaN features -> 0 (neutral), NaN targets kept."""
    z = standardise(raw_primitives(d))
    out = pd.concat([z, targets(d)], axis=1).iloc[WARMUP:]
    out[NAMES] = out[NAMES].fillna(0.0)
    return out
