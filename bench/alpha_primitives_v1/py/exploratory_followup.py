"""EXPLORATORY (not used for adjudication): follow-up of the non-primary specs with the highest gross t. Purpose: characterise 'gross-only, cost-dominated' leads."""
import warnings; warnings.filterwarnings("ignore")
import json, numpy as np, pandas as pd, lib, primitives as pr
AL = pd.read_json("../results/all_specs_table.json").T if False else None
res = json.load(open("../results/main_results.json"))["results"]
specs = sorted([(v["FULL"]["gross"]["t_nw"], k) for k, v in res.items() if not v["meta"]["primary"]], reverse=True)[:6]
P = lib.load_panel(lib.CORE); Ph = lib.load_panel(["BTC"] + lib.HOLD); cb_assets = [a for a in lib.CORE if a != "BNB"]; Pc = lib.load_panel(cb_assets, venue="cb"); Pb = {k: v[cb_assets] for k, v in P.items()}
out = {}
def g(sim, H, sp="FULL"): s = lib.summarize(sim, H, sp); return dict(gross_S=s["gross"]["sharpe"], gross_t=s["gross"]["t_nw"], net_S=s["net"]["sharpe"], turn=s["turn_per_day"], cost_ann=s["cost_ann"], gross_ann=s["gross"]["ann_ret"])
for t, k in specs:
    n, mode, h = k.split("|"); H = int(h[1:]); r = {}
    S = pr.signal(n, P, H=H); base = lib.simulate(P, S, mode, H); r["full"] = g(base, H); r["dev"] = g(base, H, "DEV"); r["test"] = g(base, H, "TEST")
    for d in (1, 2): r[f"delay{d}"] = g(lib.simulate(P, S, mode, H, delay=d), H)
    for cm in (0.25, 0.5): r[f"cost_x{cm}"] = dict(net_S=lib.summarize(lib.simulate(P, S, mode, H, cost_mult=cm), H, "FULL")["net"]["sharpe"])
    if n not in ("P14_VRP_DVOL", "P15_FUND_DIV"):
        Sh = pr.signal(n, Ph, H=H); Sh = Sh[[c for c in Sh.columns if c != "BTC"]]; Th = {kk: v[Sh.columns] for kk, v in Ph.items()}
        r["holdout_assets"] = g(lib.simulate(Th, Sh, mode, H), H)
    if n in ("P01_TSMOM","P02_XS_RS7D","P03_REV4H","P04_VOLCOMP_BRK","P05_BRK_PERSIST","P11_LIQ_SHOCK","P12_LEADLAG_BTC","P13_SEASON_HOD"):
        Sc = pr.signal(n, Pc, H=H)[cb_assets]; r["coinbase_signal_TEST"] = g(lib.simulate(Pb, Sc, mode, H), H, "TEST"); r["binance_signal_same_assets_TEST"] = g(lib.simulate(Pb, pr.signal(n, Pb, H=H), mode, H), H, "TEST")
    out[k] = r; print(k, {a: (round(b.get("gross_S", b.get("net_S", 0)), 2)) for a, b in r.items()}, flush=True)
json.dump(out, open("../results/exploratory_followup.json", "w"), indent=1, default=float)
