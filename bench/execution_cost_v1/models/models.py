"""Reference implementations (minimal, from published formulas) of the cost / fill / spread models under test.
All cost models return an expected cost in bps vs ARRIVAL MID for a BUY, EXCLUDING fees (fees are a separate,
measured line in the accounting contract).  ctx is a dict; a model that lacks a required field returns nan
(=> MODEL_NOT_APPLICABLE for that data regime, never a silent zero).
"""
import numpy as np
from scipy.stats import norm

STEP = 0.25


# ------------------------------------------------------------------ cost models (single market order)
def m_mid_fill(ctx, p):            # E1 fantasy
    return 0.0

def m_fixed(ctx, p):               # p['c']
    return p["c"]

def m_half_spread(ctx, p):         # requires L1
    return ctx["spread"] / 2 if ctx.get("spread") is not None else np.nan

def m_spread_prop(ctx, p):         # k * half-spread   (k calibrated: absorbs slippage as a spread multiple)
    return p["k"] * ctx["spread"] / 2 if ctx.get("spread") is not None else np.nan

def m_vol_scaled(ctx, p):          # half-spread + a * sigma*sqrt(1s)   (sigma bps/sqrt(s))
    if ctx.get("spread") is None: return np.nan
    return ctx["spread"] / 2 + p["a"] * ctx["sigma"]

def m_size_depth(ctx, p):          # half-spread + b * N / D_1bp   (L1 size + depth-within-1bp proxy)
    if ctx.get("spread") is None or ctx.get("D1") is None: return np.nan
    return ctx["spread"] / 2 + p["b"] * ctx["N"] / ctx["D1"]

def m_sqrt(ctx, p):                # half-spread + Y * sigma_day * sqrt(N / V_day)   (Bouchaud/Toth style)
    hs = ctx["spread"] / 2 if ctx.get("spread") is not None else p.get("hs_fallback", np.nan)
    sd = ctx["sigma"] * np.sqrt(86400.0)
    return hs + p["Y"] * sd * np.sqrt(ctx["N"] / ctx["V_day"])

def m_sqrt_no_spread(ctx, p):      # OHLCV-only variant: spread unknown -> constant fallback proxy
    sd = ctx["sigma"] * np.sqrt(86400.0)
    return p["hs_fallback"] + p["Y"] * sd * np.sqrt(ctx["N"] / ctx["V_day"])

def book_walk(q, x, N):
    d = x + STEP / 2
    cum = np.cumsum(q)
    filled = min(N, cum[-1])
    k = min(int(np.searchsorted(cum, filled)), len(q) - 1)
    prev = cum[k - 1] if k > 0 else 0.0
    return ((q[:k] * d[:k]).sum() + (filled - prev) * d[k]) / filled, filled / N

def m_walk(ctx, p):                # exact walk of the OBSERVED snapshot (L2)
    if ctx.get("q") is None: return np.nan
    avg, ff = book_walk(ctx["q"], ctx["x"], ctx["N"])
    return ctx["spread"] / 2 + avg

def m_walk_fallback(ctx, p):       # L2 walk; if order exceeds visible depth -> sqrt fallback (documented degrade path)
    if ctx.get("q") is None: return np.nan
    avg, ff = book_walk(ctx["q"], ctx["x"], ctx["N"])
    if ff < 0.999:
        return m_sqrt(ctx, p)
    return ctx["spread"] / 2 + avg

def m_walk_latency(ctx, p):        # walk + expected adverse drift over latency (drift_hat * lat)
    w = m_walk(ctx, p)
    return w + ctx.get("drift_hat", 0.0) * ctx["lat"]


# ------------------------------------------------------------------ sliced execution
def kernel(tau, lam, phi, tau0, gamma):
    return lam * (phi + (1 - phi) * (1 + tau / tau0) ** (-gamma))

def m_sliced_independent(ctx, p):  # each child walks the same snapshot (no impact memory, no depletion)
    n = ctx["slices"]
    return m_walk(dict(ctx, N=ctx["N"] / n), p)

def m_sliced_propagator(ctx, p):   # walk per child + propagator memory of previous children
    n, T = ctx["slices"], ctx["horizon"]
    base = m_walk(dict(ctx, N=ctx["N"] / n), p)
    child = ctx["N"] / n
    ts = np.linspace(0, T, n, endpoint=False) if n > 1 else np.array([0.0])
    imp = 0.0
    for j in range(n):
        imp += sum(kernel(ts[j] - ts[i], p["lam"], p["phi"], p["tau0"], p["gamma"]) * child / 1e6 for i in range(j))
    return base + imp / n

def m_sliced_ac(ctx, p):           # Almgren-Chriss-style expected cost: eps + 0.5*g*N + eta*rate  (all linear)
    n, T = ctx["slices"], max(ctx["horizon"], 1.0)
    rate = ctx["N"] / T if n > 1 else ctx["N"] / max(ctx["lat"], 1.0)
    hs = ctx["spread"] / 2
    return hs + 0.5 * p["g"] * ctx["N"] / 1e6 + p["eta"] * rate / 1e6

def m_sliced_sqrt(ctx, p):
    return m_sqrt(ctx, p)


# ------------------------------------------------------------------ passive fills
def f_always(ctx, p):              # E1-maker fantasy
    return 1.0

def f_const(ctx, p):
    return p["p"]

def f_price_through(ctx, p):       # needs only sigma + tick : first passage of a BM one tick below in H
    H = ctx["H"]; tick = ctx["tick"]
    return 2 * norm.sf(tick / (ctx["sigma"] * np.sqrt(H)))

def f_queue_volume(ctx, p):        # displayed queue ahead vs cumulative sell volume ~ lognormal-ish (needs L1 size + trade rate)
    need = ctx["queue_ahead"] + ctx["order_n"]
    mu = ctx["sell_rate"] * ctx["H"]
    cv = p.get("cv", 0.5)
    s = np.sqrt(np.log(1 + cv ** 2)); m = np.log(mu) - s * s / 2
    return norm.sf((np.log(need) - m) / s)

def f_hybrid(ctx, p):              # price-through OR queue consumption (independence approx)
    a = f_price_through(ctx, p); b = f_queue_volume(ctx, p)
    return a + (1 - a) * b


# ------------------------------------------------------------------ spread estimators (OHLC / close only)
def roll(C):
    """Roll (1984): 2*sqrt(-cov(dp_t, dp_{t-1})) in the units of C; 0 when covariance positive."""
    d = np.diff(C)
    c = np.cov(d[1:], d[:-1])[0, 1]
    return 2 * np.sqrt(-c) if c < 0 else 0.0

def corwin_schultz(H, L, floor_zero=True):
    """Corwin & Schultz (2012) two-day high-low estimator on prices (need strictly positive prices, use price levels).
    Returns mean over pairs of S = 2(e^a - 1)/(1+e^a) in FRACTIONAL units."""
    H = np.asarray(H, float); L = np.asarray(L, float)
    b = (np.log(H[:-1] / L[:-1])) ** 2 + (np.log(H[1:] / L[1:])) ** 2
    Hh = np.maximum(H[:-1], H[1:]); Ll = np.minimum(L[:-1], L[1:])
    g = (np.log(Hh / Ll)) ** 2
    k = 3 - 2 * np.sqrt(2)
    a = (np.sqrt(2 * b) - np.sqrt(b)) / k - np.sqrt(g / k)
    S = 2 * (np.exp(a) - 1) / (1 + np.exp(a))
    if floor_zero:
        S = np.maximum(S, 0)
    return float(np.nanmean(S)), float(np.mean(np.asarray(a) < 0))

def abdi_ranaldo(C, H, L):
    """Abdi & Ranaldo (2017) close-high-low estimator (fractional)."""
    c = np.log(np.asarray(C, float)); h = np.log(np.asarray(H, float)); l = np.log(np.asarray(L, float))
    eta = (h + l) / 2
    v = (c[:-1] - eta[:-1]) * (c[:-1] - eta[1:])
    return float(2 * np.sqrt(max(np.mean(v), 0)))

def hl_range_proxy(H, L, c=0.5):
    """Naive: c * median(H/L-1) (a volatility proxy mistaken for a spread)."""
    return float(c * np.median(np.asarray(H, float) / np.asarray(L, float) - 1))
