"""Main execution: 15 primitives x {TS,CS} x H{4,24} x {DEV,TEST,FULL}; gross & net separately (net = gross - trading cost - funding).
Outputs results/main_results.json, results/pnl_primary.parquet, results/signals_daily.parquet."""
import warnings; warnings.filterwarnings("ignore")
import json, sys, numpy as np, pandas as pd, lib, primitives as pr
assets = [a for a in lib.CORE if __import__("os").path.exists(f"{lib.D}/{a}_metrics5m.parquet")] if len(sys.argv) < 2 else sys.argv[1].split(",")
P = lib.load_panel(assets)
out = {}; pnl = {}; sigs = {}; persist = {}
for n, (fn, fam, pmode, pH, sH, note, needs) in pr.REG.items():
    for H in (4, 24):
        S = pr.signal(n, P, H=H)
        if H == pH:
            z = (S / lib.rstd(S, 720)).clip(-3, 3); sigs[n] = z.iloc[::24]
            persist[n] = {str(l): float(np.nanmean([z[a].corr(z[a].shift(l)) for a in z.columns if z[a].notna().sum() > 500])) for l in (1, 4, 24, 72)}
        for mode in ("TS", "CS"):
            if S.notna().sum().sum() == 0 or (mode == "CS" and S.notna().sum(1).max() < 4): continue
            sim = lib.simulate(P, S, mode, H)
            rec = {sp: lib.summarize(sim, H, sp) for sp in ("DEV", "TEST", "FULL")}
            F = lib.fwd_ret(P, H)
            ic, ict, nic = lib.cs_ic(S, F, H); rec["cs_ic"] = dict(ic=ic, t=ict, n=nic)
            rec["meta"] = dict(family=fam, primary=(mode == pmode and H == pH), pre_sign=note)
            out[f"{n}|{mode}|H{H}"] = rec
            if mode == pmode and H == pH: pnl[n] = sim[["gross", "net", "cost", "fund", "turn", "gexp"]]
            f = rec["FULL"]; print(f"{n:16s} {mode} H{H:<2d} gross S={f['gross']['sharpe']:+.2f} t={f['gross']['t_nw']:+.2f} | net S={f['net']['sharpe']:+.2f} t={f['net']['t_nw']:+.2f} | turn/d={f['turn_per_day']:.2f} ic={ic:+.4f}", flush=True)
json.dump(dict(assets=assets, persistence=persist, results=out), open("../results/main_results.json", "w"), indent=1, default=float)
pd.concat(pnl, axis=1).to_parquet("../results/pnl_primary.parquet")
pd.concat({k: v.stack() for k, v in sigs.items()}, axis=1).to_parquet("../results/signals_daily.parquet")
