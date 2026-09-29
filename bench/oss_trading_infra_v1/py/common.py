import numpy as np, pandas as pd
def make_bars(n=600, seed=3, start="2023-01-02"):
    rng = np.random.default_rng(seed)
    r = rng.normal(0, 0.01, n); close = 100*np.exp(np.cumsum(r))
    opn = np.r_[100.0, close[:-1]] * (1 + rng.normal(0, 0.002, n))   # gap vs prev close
    hi = np.maximum(opn, close)*(1+np.abs(rng.normal(0, 0.003, n))); lo = np.minimum(opn, close)*(1-np.abs(rng.normal(0, 0.003, n)))
    idx = pd.bdate_range(start, periods=n, tz=None)
    return pd.DataFrame(dict(Open=opn, High=hi, Low=lo, Close=close, Volume=rng.integers(1_000, 5_000, n).astype(float)), index=idx)
FEE = 0.001; SLIP = 0.0005; QTY = 100
BUY_BAR, SELL_BAR = 100, 200   # decision index (signal known at close of this bar)
def analytic(df):
    """PnL under both timing conventions, fee on notional per side, adverse slippage on price."""
    out = {}
    for name, (ib, isl) in dict(same_bar_close=(BUY_BAR, SELL_BAR), next_bar_open=(BUY_BAR+1, SELL_BAR+1)).items():
        col = "Close" if name == "same_bar_close" else "Open"
        pb = df[col].iloc[ib]*(1+SLIP); ps = df[col].iloc[isl]*(1-SLIP)
        out[name] = dict(buy_px=pb, sell_px=ps, pnl=(ps-pb)*QTY - FEE*QTY*(pb+ps))
    return out
