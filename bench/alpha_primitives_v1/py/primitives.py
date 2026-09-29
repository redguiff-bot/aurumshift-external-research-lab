"""15 executed primitives. Each: fn(P, k=1.0, H=None) -> signal DataFrame (rows=decision bars, cols=assets).
Only data with index <= t is used at row t (verified by lookahead_test.py). `k` scales look-backs (parameter-perturbation test).
Signs/horizons/modes are PRE-DECLARED in 02_PRIMITIVE_CONTRACTS.md before any result was produced."""
import numpy as np, pandas as pd
from lib import rstd

def _n(x, k): return max(2, int(round(x * k)))
def _lr(P): return np.log(P["c"]).diff()
def _sig1(P): return rstd(_lr(P), 720)
def _ret(P, n): return np.log(P["c"] / P["c"].shift(n))

def p01_tsmom(P, k=1.0, H=None):
    s1 = _sig1(P); a, b = _n(24, k), _n(72, k)
    return 0.5 * (_ret(P, a) / (s1 * np.sqrt(a)) + _ret(P, b) / (s1 * np.sqrt(b)))
def p02_xsrs(P, k=1.0, H=None):
    n = _n(168, k); return _ret(P, n) / (_sig1(P) * np.sqrt(n))
def p03_rev(P, k=1.0, H=None):
    n = _n(4, k); return -_ret(P, n) / (_sig1(P) * np.sqrt(n))
def p04_volcomp_brk(P, k=1.0, H=None):
    pk = (np.log(P["h"] / P["l"]) ** 2) / (4 * np.log(2))
    comp = (pk.rolling(_n(24, k)).mean() / pk.rolling(720).mean()).shift(1) < 0.7
    up = P["c"] > P["h"].rolling(_n(48, k)).max().shift(1); dn = P["c"] < P["l"].rolling(_n(48, k)).min().shift(1)
    return (up.astype(float) - dn.astype(float)).where(comp, 0.0).where(P["c"].notna())
def p05_brk_persist(P, k=1.0, H=None):
    n = _n(48, k); hi, lo = P["h"].rolling(n).max(), P["l"].rolling(n).min()
    return (P["c"] - lo) / (hi - lo).replace(0, np.nan) - 0.5
def p06_fund_carry(P, k=1.0, H=None):
    return -P["fund_ph"].rolling(_n(72, k), min_periods=24).mean()
def p07_premium(P, k=1.0, H=None):
    p = P["prem"].rolling(_n(4, k), min_periods=2).mean()
    return -(p - p.rolling(720, min_periods=168).mean())
def p08_oi_price(P, k=1.0, H=None):
    n = _n(24, k); d = np.log(P["oi"]).diff(n); s1 = np.log(P["oi"]).diff().rolling(720, min_periods=168).std()
    return np.sign(_ret(P, n)) * d / (s1 * np.sqrt(n))
def p09_oi_flush(P, k=1.0, H=None):
    n = _n(6, k); lo = np.log(P["oi"]); z = lo.diff(n) / (lo.diff().rolling(720, min_periods=168).std() * np.sqrt(n))
    r = _ret(P, n); big = (r.abs() / (_sig1(P) * np.sqrt(n))) > 1.5
    return (-np.sign(r) * (-z - 1).clip(lower=0)).where(big, 0.0).where(z.notna())
def p10_taker_imb(P, k=1.0, H=None):
    n = _n(4, k); num = (2 * P["tbq"] - P["qv"]).rolling(n).sum(); return num / P["qv"].rolling(n).sum()
def p11_liq_shock(P, k=1.0, H=None):
    lv = np.log(P["qv"].replace(0, np.nan)); n = _n(168, k)
    z = (lv - lv.rolling(n, min_periods=n // 2).mean()) / lv.rolling(n, min_periods=n // 2).std()
    return (-_lr(P) / _sig1(P)).where(z > 1.5, 0.0).where(z.notna())
def p12_leadlag_btc(P, k=1.0, H=None):
    lr = _lr(P); b = lr["BTC"]; n = _n(2, k)
    beta = lr.rolling(720, min_periods=168).cov(b).div(b.rolling(720, min_periods=168).var(), axis=0)
    rb = _ret(P, n)["BTC"]; ra = _ret(P, n)
    s = (beta.mul(rb, axis=0) - ra) / (_sig1(P) * np.sqrt(n)); s["BTC"] = np.nan; return s
def p13_season_hod(P, k=1.0, H=4):
    """sum over predicted bars t+j (j=1..H<=24) of the mean of the same-hour returns of the previous J days: mean_i lr[t+j-24i], i=1..J (all indices <= t)."""
    lr = _lr(P); J = _n(60, k)
    return sum(lr.shift(24 * i - j) for j in range(1, H + 1) for i in range(1, J + 1)) / J

def p14_vrp_dvol(P, k=1.0, H=None):
    rv = _lr(P).rolling(_n(168, k), min_periods=100).std() * np.sqrt(8760) * 100
    s = P["dvol"] - rv; return s - s.rolling(2160, min_periods=500).mean()
def p15_fund_div(P, k=1.0, H=None):
    n = _n(24, k); bn = P["fund_ph"].rolling(n, min_periods=8).mean(); hl = P["hlf"].rolling(n, min_periods=8).mean()
    return -(bn - hl)

# id: (fn, family, primary_mode, primary_H, secondary_H, expected_sign_note, needs)
REG = {
 "P01_TSMOM":        (p01_tsmom,        "momentum/trend",                    "TS", 24, 4,  "+ continuation",                       ["c"]),
 "P02_XS_RS7D":      (p02_xsrs,         "cross-sectional relative strength", "CS", 24, 4,  "+ winners keep winning",               ["c"]),
 "P03_REV4H":        (p03_rev,          "mean reversion",                    "TS", 4,  24, "- fade 4h move",                       ["c"]),
 "P04_VOLCOMP_BRK":  (p04_volcomp_brk,  "vol compression -> expansion + breakout", "TS", 24, 4, "+ breakout direction after compression", ["c","h","l"]),
 "P05_BRK_PERSIST":  (p05_brk_persist,  "breakout persistence (baseline)",   "TS", 24, 4,  "+ position in 48h Donchian range",     ["c","h","l"]),
 "P06_FUND_CARRY":   (p06_fund_carry,   "carry / funding",                   "CS", 24, 4,  "- short high-funding, long low-funding (receive carry)", ["fund_ph"]),
 "P07_PREMIUM":      (p07_premium,      "basis (perp premium index)",        "TS", 4,  24, "- fade premium deviation",             ["prem"]),
 "P08_OI_PRICE":     (p08_oi_price,     "open-interest / price divergence",  "TS", 24, 4,  "+ OI rising with move confirms it",    ["oi","c"]),
 "P09_OI_FLUSH":     (p09_oi_flush,     "liquidation pressure (OI-flush proxy)", "TS", 4, 24, "- fade price move accompanied by OI collapse", ["oi","c"]),
 "P10_TAKER_IMB":    (p10_taker_imb,    "volume imbalance (taker flow)",     "TS", 4,  24, "+ flow persistence",                   ["tbq","qv"]),
 "P11_LIQ_SHOCK":    (p11_liq_shock,    "liquidity shock (volume z>1.5)",    "TS", 4,  24, "- fade 1h move on volume shock",       ["qv","c"]),
 "P12_LEADLAG_BTC":  (p12_leadlag_btc,  "cross-asset lead/lag",              "CS", 4,  24, "+ alt catches up to beta*BTC 2h move", ["c"]),
 "P13_SEASON_HOD":   (p13_season_hod,   "intraday seasonality",              "TS", 4,  24, "+ trailing same-hour mean return",     ["c"]),
 "P14_VRP_DVOL":     (p14_vrp_dvol,     "realized vs implied vol",           "TS", 24, 4,  "+ VRP above own mean -> positive return (BTC/ETH only)", ["dvol","c"]),
 "P15_FUND_DIV":     (p15_fund_div,     "funding divergence (Binance vs Hyperliquid)", "CS", 24, 4, "- Binance funding above HL -> crowded", ["fund_ph","hlf"]),
}
def signal(name, P, k=1.0, H=None):
    fn = REG[name][0]; return fn(P, k, H or REG[name][3]) if name == "P13_SEASON_HOD" else fn(P, k)
