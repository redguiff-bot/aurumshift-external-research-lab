"""Falsification battery on the PRE-DECLARED primary spec of every primitive (full sample unless stated). Outputs results/falsification.json."""
import warnings; warnings.filterwarnings("ignore")
import json, os, sys, numpy as np, pandas as pd, lib, primitives as pr
assets = [a for a in lib.CORE if os.path.exists(f"{lib.D}/{a}_metrics5m.parquet")]
P = lib.load_panel(assets); R = {}
PRICE_ONLY = ["P01_TSMOM","P02_XS_RS7D","P03_REV4H","P04_VOLCOMP_BRK","P05_BRK_PERSIST","P11_LIQ_SHOCK","P12_LEADLAG_BTC","P13_SEASON_HOD"]
def spec(n): fn, fam, mode, H, sH, note, needs = pr.REG[n]; return mode, H
def run(n, Pf, truth, k=1.0, delay=0, mask=None, cost_mult=1.0, split="FULL", cols=None):
    mode, H = spec(n); S = pr.signal(n, Pf, k=k, H=H)
    if cols is not None: S = S[cols]
    if mask is not None: S = S.where(~mask.reindex(columns=S.columns))
    if S.notna().sum().sum() == 0: return None
    if mode == "CS" and S.notna().sum(1).max() < 4: return None
    T = {kk: (v[S.columns] if hasattr(v, "columns") else v) for kk, v in truth.items()}
    sim = lib.simulate(T, S, mode, H, delay=delay, cost_mult=cost_mult)
    s = lib.summarize(sim, H, split)
    return dict(gross_sharpe=s["gross"]["sharpe"], net_sharpe=s["net"]["sharpe"], net_t=s["net"]["t_nw"], gross_t=s["gross"]["t_nw"], net_ret=s["net"]["ann_ret"], gross_ret=s["gross"]["ann_ret"])
def corrupt(Pc, p, kind, seed):
    rng = np.random.default_rng(seed); n, m = Pc["o"].shape
    if kind == "missing": mask = pd.DataFrame(rng.random((n, m)) < p, index=Pc["o"].index, columns=Pc["o"].columns)
    else:   # stale: runs of 3 frozen bars
        st = rng.random((n, m)) < p / 3; mask = pd.DataFrame(st, index=Pc["o"].index, columns=Pc["o"].columns)
        mask = mask | mask.shift(1, fill_value=False) | mask.shift(2, fill_value=False)
    F = {}
    for k, v in Pc.items():
        F[k] = v.mask(mask).ffill(limit=None) if kind == "missing" else v.mask(mask).ffill()
    return F, (mask if kind == "missing" else None)

for n in pr.REG:
    mode, H = spec(n); r = {}
    r["base"] = run(n, P, P)
    if r["base"] is None: continue
    r["delay1"] = run(n, P, P, delay=1); r["delay2"] = run(n, P, P, delay=2)
    for cm in (2, 3, 5): r[f"cost_x{cm}"] = run(n, P, P, cost_mult=cm)
    r["cost_x0.5_optimistic"] = run(n, P, P, cost_mult=0.5)
    for k in (0.5, 0.75, 1.5, 2.0): r[f"param_k{k}"] = run(n, P, P, k=k)
    for kind in ("missing", "stale"):
        for p in (0.10, 0.25):
            rs = []
            for seed in (1, 2, 3):
                F, mask = corrupt(P, p, kind, seed); x = run(n, F, P, mask=mask)
                if x: rs.append(x)
            if rs: r[f"{kind}_{int(p*100)}pct"] = {k: float(np.mean([q[k] for q in rs])) for k in rs[0]}
    for sp in ("DEV", "TEST"): r[f"split_{sp}"] = run(n, P, P, split=sp)
    # different assets (holdout universe, BTC used only as a leader for P12 and dropped from the book)
    if n not in ("P14_VRP_DVOL", "P15_FUND_DIV"):
        Ph = lib.load_panel(["BTC"] + lib.HOLD); r["holdout_assets"] = run(n, Ph, Ph, cols=[c for c in Ph["o"].columns if c != "BTC"])
    else: r["holdout_assets"] = "N/A_inputs_only_for_core_assets"
    # wrong venue: signal from Coinbase spot bars (9 assets, no BNB), P&L on Binance perp; baseline = same assets/window with Binance-derived signal
    if n in PRICE_ONLY:
        Pc = lib.load_panel([a for a in lib.CORE if a != "BNB"], venue="cb"); cols = list(Pc["o"].columns)
        Pb = {k: v[cols] for k, v in P.items()}
        r["venue_baseline_TEST"] = run(n, Pb, Pb, split="TEST", cols=cols); r["venue_coinbase_signal_TEST"] = run(n, Pc, Pb, split="TEST", cols=cols)
    else: r["venue_coinbase_signal_TEST"] = "N/A_not_price_only_input"
    R[n] = r; print(n, "net S base %.2f | d1 %.2f | x3 %.2f | miss25 %.2f | stale25 %.2f" % tuple((r[k]["net_sharpe"] if r.get(k) else float('nan')) for k in ("base","delay1","cost_x3","missing_25pct","stale_25pct")), flush=True)
# placebo: autocorrelated random signals through the identical pipeline (null distribution of net/gross t at H=24, TS)
rng = np.random.default_rng(11); pl = []
for i in range(150):
    S = pd.DataFrame(rng.standard_normal(P["c"].shape), index=P["c"].index, columns=P["c"].columns).ewm(span=24).mean()
    sim = lib.simulate(P, S, "TS", 24); s = lib.summarize(sim, 24, "FULL"); pl.append((s["gross"]["t_nw"], s["net"]["t_nw"], s["gross"]["sharpe"]))
pl = np.array(pl); R["_placebo"] = dict(n=len(pl), gross_t_sd=float(pl[:, 0].std()), gross_t_p95=float(np.percentile(pl[:, 0], 95)), gross_t_p99=float(np.percentile(pl[:, 0], 99)), net_t_p95=float(np.percentile(pl[:, 1], 95)), sharpe_sd=float(pl[:, 2].std()))
print(R["_placebo"])
# controls: (i) planted-future signal must be detected (validates timing alignment of the simulator), (ii) same signal 3H-misaligned must be ~0
ctl = {}
for H in (4, 24):
    F0 = lib.fwd_ret(P, H); sd = F0.std()
    noise = pd.DataFrame(rng.standard_normal(F0.shape), index=F0.index, columns=F0.columns)
    for lab, S in ((f"planted_future_H{H}", F0 + 3 * sd * noise), (f"misaligned_3H_H{H}", (F0 + 3 * sd * noise).shift(3 * H))):
        for dl in (0, 1):
            sim = lib.simulate(P, S, "TS", H, delay=dl); s = lib.summarize(sim, H, "FULL"); ctl[f"{lab}_delay{dl}"] = dict(gross_sharpe=s["gross"]["sharpe"], gross_t=s["gross"]["t_nw"], net_sharpe=s["net"]["sharpe"])
R["_controls"] = ctl; print(json.dumps(ctl, indent=1))
json.dump(R, open("../results/falsification.json", "w"), indent=1, default=float)
