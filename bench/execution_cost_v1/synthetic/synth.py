"""Deterministic synthetic microstructure bench (ground-truth generator).

Units: prices in bps relative to arrival mid (m0 = 0), notional in USD, time in seconds.
NOTHING here is claimed to transfer to production; it is a controlled truth for falsifying models.

Truth world (documented so nobody mistakes it for reality):
  * mid: arithmetic random walk in bps (sigma*sqrt(dt)) + drift + optional OU pull + optional jump
  * book: cumulative notional depth to distance x bps from the touch  C(x) = A * x^beta  (beta=1 flat density,
    beta=2 density growing linearly -> square-root-like walk cost), discretised on a grid, lognormal level noise,
    optional liquidity shock (depth multiplier, spread multiplier), optional 'wall' (sparse book then big level)
  * own impact: transient+permanent propagator on mid  G(tau)=lam*(phi+(1-phi)*(1+tau/tau0)^-gamma) per $M
    and depletion of consumed levels that recovers exponentially (rho)
  * limit orders: tick-snapped quotes, queue ahead consumed by sell aggressor flow, price-through fills,
    flow-price coupling (net signed flow moves mid) => adverse selection is ENDOGENOUS.
"""
from dataclasses import dataclass, replace, asdict
import numpy as np

STEP = 0.25          # bps grid of book levels
NLEV = 2400          # up to 600 bps deep


@dataclass(frozen=True)
class Scenario:
    name: str = "base"
    sigma: float = 0.9            # bps / sqrt(s)  (~BTC 50% annual)
    drift: float = 0.0            # bps / s, applied in favour of the price move ADVERSE to buyer if >0 (trend continuation)
    ou_kappa: float = 0.0         # mean reversion 1/s toward arrival mid (m0)
    jump_bps: float = 0.0         # signed jump (adverse if >0 for buyer) inserted at random time in [0, latency]
    spread: float = 1.0           # full spread, bps
    A: float = 4.0e5              # notional per bps^beta of cumulative depth
    beta: float = 1.5
    lat: float = 0.5              # seconds decision -> arrival at venue (deterministic mean, jitter +-50%)
    obs_age: float = 0.0          # extra staleness of the observed snapshot (s)
    noise: float = 0.35           # lognormal sd of per-level size
    noise_corr: float = 0.7       # persistence of level noise between observed and executed books
    shock_mult: float = 1.0       # depth multiplier at execution time (liquidity withdrawal <1)
    shock_spread_mult: float = 1.0
    wall_at: float = 0.0          # bps distance where depth becomes sparse (0 = none)
    wall_thin: float = 0.05
    lam: float = 0.4              # own-impact bps per $1M (peak, at tau=0)
    phi: float = 0.4              # permanent fraction of own impact
    tau0: float = 30.0
    gamma: float = 0.5
    rho: float = 0.05             # depletion recovery per second
    V_day: float = 2.0e9          # daily traded notional (for sqrt models)
    fee_taker_bps: float = 5.0
    fee_maker_bps: float = 2.0
    n_venues: int = 1             # fragmentation: depth split equally across venues


def _level_arrays(sc: Scenario, mult=1.0, wall=True):
    x = STEP * (np.arange(NLEV) + 1.0)                      # distance from touch, upper edge of each level
    C = sc.A * mult / sc.n_venues * x ** sc.beta
    q = np.diff(np.concatenate([[0.0], C]))
    if wall and sc.wall_at > 0:
        thin = x < sc.wall_at
        q = np.where(thin, q * sc.wall_thin, q)
        # mass hidden behind the wall sits on the wall level
        extra = (np.diff(np.concatenate([[0.0], C]))[thin].sum()) * (1 - sc.wall_thin)
        q[np.argmax(~thin)] += extra
    return x, q


def make_book(sc: Scenario, rng, noise_state=None, mult=1.0, corr=0.0):
    """Returns (dist_from_mid array, q array, noise_state)."""
    x, q0 = _level_arrays(sc, mult)
    z = rng.standard_normal(NLEV)
    if noise_state is not None and corr > 0:
        z = corr * noise_state + np.sqrt(1 - corr ** 2) * z
    q = q0 * np.exp(sc.noise * z - 0.5 * sc.noise ** 2)
    return x - STEP + 0.0, q, z   # x-STEP = distance to touch of level lower edge; caller adds half spread


def walk(dist_from_touch, q, notional):
    """Buy walk. Returns (avg distance from TOUCH in bps, filled_fraction). Levels priced at their mean distance."""
    d = dist_from_touch + STEP / 2   # level mid-distance
    cum = np.cumsum(q)
    filled = min(notional, cum[-1])
    if filled <= 0:
        return 0.0, 0.0
    k = int(np.searchsorted(cum, filled))
    k = min(k, len(q) - 1)
    prev = cum[k - 1] if k > 0 else 0.0
    tot = (q[:k] * d[:k]).sum() + (filled - prev) * d[k]
    return tot / filled, filled / notional


def sqrt_kernel(tau, sc):
    return sc.lam * (sc.phi + (1 - sc.phi) * (1 + tau / sc.tau0) ** (-sc.gamma))


def simulate_market(sc: Scenario, notional: float, n_trials: int, seed: int, slices: int = 1,
                    horizon: float = 0.0, obs_levels: int = 400, side: int = +1):
    """Execute a BUY parent order (side=+1) as `slices` equal child market orders spread evenly over `horizon` s.
    Returns dict of arrays (per trial), incl. ground-truth decomposition and the OBSERVED snapshot at decision time
    for models (mid=0, spread, top-`obs_levels` levels, sigma_hat inputs)."""
    rng = np.random.default_rng(seed)
    sc_t = replace(sc, n_venues=1)   # truth routes across ALL venues; observed snapshot is ONE venue's book
    out = {k: np.zeros(n_trials) for k in
           ["IS", "drift", "half_spread", "walk", "impact", "filled", "fee", "IS_fee"]}
    obs = []
    dts = np.linspace(0, horizon, slices, endpoint=False) if slices > 1 else np.array([0.0])
    child = notional / slices
    for i in range(n_trials):
        # ---------------- observed snapshot at decision time (before latency) ----------------
        xo, qo, zo = make_book(sc, rng, mult=1.0)
        obs.append((qo[:obs_levels].copy(), xo[:obs_levels].copy()))
        # ---------------- path of mid up to and through execution ----------------
        t_prev = -sc.obs_age
        m = 0.0
        dep = np.zeros(NLEV)          # depletion of consumed notional per level
        own = []                      # (time, notional) of own executions for propagator
        fills_cost = 0.0; fills_n = 0.0
        dr = hs = wk = im = 0.0
        last_t = 0.0; prev_ex = 0.0
        jump_done = sc.jump_bps == 0
        jt = rng.uniform(0, max(sc.lat, 1e-9))
        for j, t_dec in enumerate(dts):
            lat = sc.lat * rng.uniform(0.5, 1.5)
            t_ex = t_dec + lat
            # advance exogenous mid from last_t to t_ex
            dt = max(t_ex - last_t, 1e-9)
            step = sc.sigma * np.sqrt(dt) * rng.standard_normal() + sc.drift * dt
            if sc.ou_kappa > 0:
                step += -sc.ou_kappa * m * dt
            m_exo = m + step
            if (not jump_done) and t_ex >= jt:
                m_exo += sc.jump_bps; jump_done = True
            # own-impact contribution (propagator over past own fills)
            imp_prev = sum(sqrt_kernel(t_ex - ts, sc) * n / 1e6 for ts, n in own)
            mid_ex = m_exo + imp_prev      # exogenous path is kept separate from impact
            m = m_exo; last_t = t_ex
            s_ex = sc.spread * sc.shock_spread_mult if sc.shock_mult < 1 else sc.spread
            # executed book: correlated noise with observed, depletion recovery, shock
            xe, qe, _ = make_book(sc_t, rng, noise_state=zo, mult=sc.shock_mult, corr=sc.noise_corr * np.exp(-sc.obs_age / 20.0))
            dep *= np.exp(-sc.rho * max(t_ex - prev_ex, 0.0))
            prev_ex = t_ex
            qe = np.maximum(qe - dep, 0.0)
            avg_d, ff = walk(xe, qe, child)
            # consume
            cum = np.cumsum(qe); take = min(child, cum[-1])
            k = int(np.searchsorted(cum, take)); k = min(k, NLEV - 1)
            used = np.zeros(NLEV); used[:k] = qe[:k]
            prev = cum[k - 1] if k > 0 else 0.0
            used[k] = max(take - prev, 0.0)
            dep += used
            fills_n += take
            hs += take * s_ex / 2; wk += take * avg_d; dr += take * m_exo; im += take * imp_prev
            own.append((t_ex, take))
        if fills_n > 0:
            out["drift"][i] = dr / fills_n; out["half_spread"][i] = hs / fills_n
            out["walk"][i] = wk / fills_n; out["impact"][i] = im / fills_n
        out["filled"][i] = fills_n / notional
        out["IS"][i] = out["drift"][i] + out["half_spread"][i] + out["walk"][i] + out["impact"][i]
        out["fee"][i] = sc.fee_taker_bps
        out["IS_fee"][i] = out["IS"][i] + sc.fee_taker_bps
    out["obs"] = obs
    return out


def simulate_limit(sc: Scenario, n_trials: int, seed: int, order_n: float = 2.0e4, queue_frac: float = 0.5,
                   H: int = 60, M: int = 30, tick: float = 0.5, V: float = 2.0e4, flow_sd: float = 1.0,
                   imb_sd: float = 0.5, lam_flow: float = 0.05, cancel: float = 0.01, top_depth: float = 2.0e5, info: float = 0.0):
    """Passive BUY at the touch bid for horizon H seconds; unfilled remainder is chased with a market order.
    V = mean aggressor notional per side per second; lam_flow = bps mid move per $1M net signed flow.
    drift in `sc.drift` acts as alpha-aligned trend (price rising = adverse for a passive buyer who does not fill).
    Returns per-trial arrays: filled_frac, fill_time, IS_total(bps, incl fee), adverse_markout (bps), path info for models."""
    rng = np.random.default_rng(seed)
    T = H + M
    n = n_trials
    eps = rng.standard_normal((n, T))
    u = np.zeros((n, T)); u_prev = rng.standard_normal(n) * imb_sd
    for t in range(T):
        u_prev = 0.9 * u_prev + np.sqrt(1 - 0.81) * imb_sd * rng.standard_normal(n); u[:, t] = u_prev
    noise_b = np.exp(flow_sd * rng.standard_normal((n, T)) - 0.5 * flow_sd ** 2)
    noise_s = np.exp(flow_sd * rng.standard_normal((n, T)) - 0.5 * flow_sd ** 2)
    vb = V * np.clip(1 + u, 0.05, None) * noise_b
    vs = V * np.clip(1 - u, 0.05, None) * noise_s
    dm = sc.sigma * eps + sc.drift + lam_flow * (vb - vs) / 1e6 + info * u   # info: flow-imbalance persistence predicts drift
    if sc.ou_kappa > 0:
        pass  # (mean reversion handled sequentially below)
    m = np.zeros((n, T + 1))
    for t in range(T):
        m[:, t + 1] = m[:, t] + dm[:, t] - sc.ou_kappa * m[:, t]
    half = sc.spread / 2
    bid0 = np.floor(-half / tick) * tick
    bid = np.floor((m[:, 1:] - half) / tick) * tick
    q = queue_frac * top_depth * np.ones(n)
    rem = order_n * np.ones(n)
    filled = np.zeros(n); fill_t = np.full(n, np.nan); fill_w = np.zeros(n)   # value-weighted time
    for t in range(H):
        same = bid[:, t] == bid0
        through = bid[:, t] < bid0
        q = np.where(same, q - vs[:, t] - cancel * q, q - cancel * q)
        # fill amount: queue exhausted part
        avail = np.where(through, rem, np.where(same, np.clip(-q, 0, None), 0.0))
        got = np.minimum(avail, rem)
        first = (got > 0) & np.isnan(fill_t)
        fill_t[first] = t
        rem -= got; filled += got
        q = np.where(got > 0, np.maximum(q, 0.0), q)
        q = np.where(through, -1e18, q)
    ff = filled / order_n
    # adverse markout (buyer): mid falls after fill => positive adverse
    idx = np.where(np.isnan(fill_t), 0, fill_t).astype(int)
    m_fill = m[np.arange(n), idx + 1]
    m_after = m[np.arange(n), np.minimum(idx + 1 + M, T)]
    adverse = -(m_after - m_fill)          # bps lost after fill (positive = adverse)
    # chase remainder at end of H
    xe, qe, _ = make_book(sc, rng)
    chase_walk, _ = walk(xe, qe, max(order_n, 1.0))
    chase = m[:, H] + half + chase_walk
    passive_cost = bid0 + sc.fee_maker_bps
    IS = ff * passive_cost + (1 - ff) * (chase + sc.fee_taker_bps)
    # taker benchmark: immediate market order (latency 0 here) at arrival
    taker = half + chase_walk + sc.fee_taker_bps
    return dict(ff=ff, fill_t=fill_t, IS=IS, adverse=adverse, taker=np.full(n, taker),
                m=m, vb=vb, vs=vs, bid=bid, bid0=bid0, half=half, chase=chase)


# ------------------------------------------------------------------------------------------------
# OHLCV synthesis for spread-proxy falsification
# ------------------------------------------------------------------------------------------------
def simulate_ohlc(spread_bps: float, sigma: float, n_bars: int, bar_s: int, seed: int, trades_per_s: float = 0.5,
                  tick_bps: float = 0.0):
    """Efficient-price random walk + trades printed at bid/ask (random aggressor side).
    Returns dict of OHLC (of trade prices, in bps of mid0=0), close-to-close, plus truth spread and effective spread."""
    rng = np.random.default_rng(seed)
    total = n_bars * bar_s
    mid = np.cumsum(sigma * rng.standard_normal(total))
    n_tr = rng.poisson(trades_per_s, total)
    O = np.full(n_bars, np.nan); H = O.copy(); L = O.copy(); Cl = O.copy()
    eff = []
    last = 0.0
    for b in range(n_bars):
        px = []
        for s in range(bar_s):
            t = b * bar_s + s
            for _ in range(n_tr[t]):
                sgn = 1 if rng.random() < 0.5 else -1
                p = mid[t] + sgn * spread_bps / 2
                if tick_bps > 0:
                    p = np.round(p / tick_bps) * tick_bps
                px.append(p); eff.append(2 * abs(p - mid[t]))
        if px:
            O[b], H[b], L[b], Cl[b] = px[0], max(px), min(px), px[-1]
            last = Cl[b]
        else:
            O[b] = H[b] = L[b] = Cl[b] = last
    return dict(O=O, H=H, L=L, C=Cl, spread=spread_bps, eff_spread=float(np.mean(eff)) if eff else np.nan, sigma=sigma)
