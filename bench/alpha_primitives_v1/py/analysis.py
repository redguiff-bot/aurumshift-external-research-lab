"""Post-processing: results tables (markdown fragments in results/tables) + adjudication json. Deterministic; reads only results/*.json|parquet."""
import warnings; warnings.filterwarnings("ignore")
import json, os, numpy as np, pandas as pd, lib, primitives as pr
from scipy import stats as st
from scipy.cluster.hierarchy import linkage, fcluster
from scipy.spatial.distance import squareform
R = "../results/"; T = R + "tables/"; os.makedirs(T, exist_ok=True)
M = json.load(open(R + "main_results.json")); res = M["results"]; F = json.load(open(R + "falsification.json")); LA = json.load(open(R + "lookahead_test.json"))
pnl = pd.read_parquet(R + "pnl_primary.parquet"); sig = pd.read_parquet(R + "signals_daily.parquet")
names = list(pr.REG.keys())
def primary(n): fn, fam, mode, H, sH, note, needs = pr.REG[n]; return res.get(f"{n}|{mode}|H{H}")
def md(df, fmt="{:+.2f}"): 
    cols = list(df.columns); out = "| " + df.index.name + " | " + " | ".join(cols) + " |\n|" + "---|" * (len(cols) + 1) + "\n"
    for i, r in df.iterrows(): out += f"| {i} | " + " | ".join(fmt.format(v) if isinstance(v, (int, float, np.floating)) and v == v else str(v) for v in r) + " |\n"
    return out
def w(fn, s): open(T + fn, "w").write(s)
def p1(t): return 1 - st.norm.cdf(t)
# ---- 05 results
rows = []
for n in names:
    r = primary(n)
    if r is None: continue
    fn, fam, mode, H, sH, note, needs = pr.REG[n]
    rows.append(dict(id=n, mode=mode, H=H, gross_S_DEV=r["DEV"]["gross"]["sharpe"], gross_S_TEST=r["TEST"]["gross"]["sharpe"], gross_S_FULL=r["FULL"]["gross"]["sharpe"], gross_t=r["FULL"]["gross"]["t_nw"],
                     net_S_DEV=r["DEV"]["net"]["sharpe"], net_S_TEST=r["TEST"]["net"]["sharpe"], net_S_FULL=r["FULL"]["net"]["sharpe"], net_t=r["FULL"]["net"]["t_nw"],
                     gross_ann_pct=100 * r["FULL"]["gross"]["ann_ret"], net_ann_pct=100 * r["FULL"]["net"]["ann_ret"], turn_day=r["FULL"]["turn_per_day"], cost_ann_pct=100 * r["FULL"]["cost_ann"], fund_ann_pct=100 * r["FULL"]["fund_ann"], cs_ic=r["cs_ic"]["ic"], cs_ic_t=r["cs_ic"]["t"]))
A = pd.DataFrame(rows).set_index("id"); A.index.name = "primitive"
pv = A.net_t.apply(p1); order = pv.sort_values().index; m = len(pv)
bh = pd.Series(index=order, dtype=float); prev = 1.0
for i, k in reversed(list(enumerate(order, 1))): prev = min(prev, pv[k] * m / i); bh[k] = prev
A["p_net_1sided"] = pv; A["BH_q"] = bh
A.to_json(R + "primary_table.json", indent=1)
w("05_primary.md", md(A[["mode","H","gross_S_DEV","gross_S_TEST","gross_S_FULL","gross_t","net_S_DEV","net_S_TEST","net_S_FULL","net_t","BH_q"]].assign(H=A.H.astype(str)), "{:+.2f}"))
w("05_econ.md", md(A[["gross_ann_pct","net_ann_pct","cost_ann_pct","fund_ann_pct","turn_day","cs_ic","cs_ic_t"]], "{:+.2f}"))
alt = []
for k, r in res.items():
    n, mode, h = k.split("|"); fn, fam, pm, pH, sH, note, needs = pr.REG[n]
    if r["meta"]["primary"]: continue
    alt.append(dict(spec=k, gross_S=r["FULL"]["gross"]["sharpe"], gross_t=r["FULL"]["gross"]["t_nw"], net_S=r["FULL"]["net"]["sharpe"], net_t=r["FULL"]["net"]["t_nw"], turn_day=r["FULL"]["turn_per_day"]))
alt = pd.DataFrame(alt).set_index("spec"); alt.index.name = "spec (non-primary)"; w("05_alt.md", md(alt))
# ---- 06 orthogonality
sp = sig.copy(); sp.columns = [c for c in sp.columns]
rk = sp.rank(); C_sig = rk.corr()
G = pnl.xs("gross", axis=1, level=1) if isinstance(pnl.columns, pd.MultiIndex) else None
Ng = pnl.xs("net", axis=1, level=1)
Gd = G.resample("1D").sum(); Nd = Ng.resample("1D").sum()
C_g = Gd.corr(); C_n = Nd.corr()
def tri(C): return C.where(np.triu(np.ones(C.shape), 1).astype(bool)).stack().abs().sort_values(ascending=False)
ev = np.linalg.eigvalsh(C_g.fillna(0).values)[::-1]; effN = float(ev.sum() ** 2 / (ev ** 2).sum())
ev_s = np.linalg.eigvalsh(C_sig.fillna(0).values)[::-1]; effN_s = float(ev_s.sum() ** 2 / (ev_s ** 2).sum())
D = 1 - C_sig.abs().fillna(0).values; np.fill_diagonal(D, 0); Z = linkage(squareform(D, checks=False), "average"); cl = fcluster(Z, 0.7, criterion="distance")   # |rho|>0.3 avg link
clusters = pd.Series(cl, index=C_sig.index)
inc = {}
Y = Nd.dropna(how="all").fillna(0)
for n in Y.columns:
    X = Y.drop(columns=n); X = np.c_[np.ones(len(X)), X.values]; yv = Y[n].values
    beta, *_ = np.linalg.lstsq(X, yv, rcond=None); e = yv - X @ beta; s2 = e @ e / (len(yv) - X.shape[1]); se = np.sqrt(s2 * np.linalg.inv(X.T @ X)[0, 0])
    inc[n] = dict(alpha_t=float(beta[0] / se), R2=float(1 - e.var() / yv.var()))
inc = pd.DataFrame(inc).T; inc.index.name = "primitive"
persist = pd.DataFrame(M["persistence"]).T; persist.columns = [f"acf_lag{c}h" for c in persist.columns]; persist.index.name = "primitive"
w("06_sigcorr.md", md(C_sig.round(2), "{:+.2f}")); w("06_pnlcorr.md", md(C_g.round(2), "{:+.2f}")); w("06_incremental.md", md(inc, "{:+.2f}")); w("06_persistence.md", md(persist.join(A[["turn_day"]]), "{:+.2f}"))
w("06_clusters.md", "\n".join(f"- cluster {c}: {', '.join(clusters[clusters == c].index)}" for c in sorted(set(cl))) + f"\n\nEffective number of independent bets (participation ratio): signals {effN_s:.2f}, gross P&L {effN:.2f} (of {len(names)}).\n\nTop |corr| pairs (signal rank / gross daily P&L):\n" + "\n".join(f"- {a} ~ {b}: sig {C_sig.loc[a,b]:+.2f}, pnl {C_g.loc[a,b]:+.2f}" for (a, b) in list(tri(C_sig).index[:8])) + "\n")
# ---- 07 regimes
P = lib.load_panel(["BTC"]); vol, trend = lib.regimes(P); vol = vol.shift(1).reindex(pnl.index); trend = trend.shift(1).reindex(pnl.index)
rg = {}
for n in names:
    if n not in Ng.columns: continue
    H = pr.REG[n][3]; rr = {}
    for lab, ser in (("vol", vol), ("trend", trend)):
        for g in sorted(ser.dropna().unique()):
            for kind, X in (("gross", G), ("net", Ng)):
                x = X[n][ser == g].dropna()
                rr[f"{g}_{kind}_S"] = float(x.mean() * 8760 / (x.std() * np.sqrt(8760))) if len(x) > 500 else np.nan
                rr[f"{g}_{kind}_t"] = float(lib.nw_t(x.values, max(2 * H, 24))) if len(x) > 500 else np.nan
            rr[f"{g}_share"] = float((ser == g).mean())
    rg[n] = rr
RG = pd.DataFrame(rg).T; RG.index.name = "primitive"; RG.to_json(R + "regime_table.json", indent=1)
regs = ["LOWVOL","MIDVOL","HIGHVOL","UPTREND","DOWNTREND"]
w("07_regime_net_S.md", md(RG[[f"{g}_net_S" for g in regs]].rename(columns=lambda c: c.replace("_net_S", "")))); w("07_regime_net_t.md", md(RG[[f"{g}_net_t" for g in regs]].rename(columns=lambda c: c.replace("_net_t", ""))))
w("07_regime_gross_S.md", md(RG[[f"{g}_gross_S" for g in regs]].rename(columns=lambda c: c.replace("_gross_S", ""))))
# ---- 08 costs
cost = {}
for n in names:
    if n not in Ng.columns: continue
    g = G[n]; c = pnl[n]["cost"]; f = pnl[n]["fund"]; sd = g.std() * np.sqrt(8760); r = {}
    r["gross_S"] = g.mean() * 8760 / sd; 
    for mlt in (0.5, 1, 2, 3, 5): r[f"net_S_x{mlt}"] = ((g - mlt * c - f).mean() * 8760) / ((g - mlt * c - f).std() * np.sqrt(8760))
    r["breakeven_x"] = float((g - f).mean() / c.mean()) if c.mean() > 0 else np.nan
    r["fund_ann_pct"] = 100 * f.mean() * 8760; cost[n] = r
CT = pd.DataFrame(cost).T; CT.index.name = "primitive"; CT.to_json(R + "cost_table.json", indent=1); w("08_cost.md", md(CT.rename(columns=lambda c: c.replace("net_S_", "net Sharpe ")), "{:+.2f}"))
# ---- 09 falsification tables
frows = {}; verdicts = {}
for n in names:
    r = F.get(n)
    if not r or r.get("base") is None: continue
    def g(k, f="net_sharpe"): x = r.get(k); return x[f] if isinstance(x, dict) else np.nan
    row = dict(base_net=g("base"), delay1=g("delay1"), delay2=g("delay2"), cost_x2=g("cost_x2"), cost_x3=g("cost_x3"), cost_x5=g("cost_x5"),
               miss10=g("missing_10pct"), miss25=g("missing_25pct"), stale10=g("stale_10pct"), stale25=g("stale_25pct"),
               k_min=np.nanmin([g(f"param_k{k}") for k in (0.5, 0.75, 1.5, 2.0)]), k_max=np.nanmax([g(f"param_k{k}") for k in (0.5, 0.75, 1.5, 2.0)]),
               hold_gross=g("holdout_assets", "gross_sharpe"), hold_net=g("holdout_assets"), venue_base_gross=g("venue_baseline_TEST", "gross_sharpe"), venue_cb_gross=g("venue_coinbase_signal_TEST", "gross_sharpe"))
    frows[n] = row
FT = pd.DataFrame(frows).T; FT.index.name = "primitive"; w("09_falsification.md", md(FT)); FT.to_json(R + "falsification_table.json", indent=1)
# ---- 10 adjudication (criteria pre-declared in 02_PRIMITIVE_CONTRACTS.md)
adj = {}
for n in names:
    if n not in A.index: continue
    a = A.loc[n]; f = FT.loc[n] if n in FT.index else None
    c1 = LA.get(n, {}).get("verdict") == "PASS"
    c2 = a.net_S_DEV > 0 and a.net_S_TEST > 0
    c3 = a.net_t >= 2.0 and a.BH_q < 0.10
    c5 = f is not None and f.cost_x2 > 0
    checks = []
    if f is not None:
        checks = [f.delay1 > 0, f.k_min > 0, f.miss25 > 0, f.stale25 > 0]
        if f.hold_gross == f.hold_gross: checks.append(f.hold_gross > 0)
        if f.venue_cb_gross == f.venue_cb_gross: checks.append(f.venue_cb_gross > 0)
    c6 = len(checks) > 0 and np.mean(checks) >= 0.7
    tier = "NOT_SUPPORTED"
    if c1 and c2 and c3: tier = "SUPPORTED_ROBUST" if (c5 and c6) else "SUPPORTED_FRAGILE"
    elif c1 and a.gross_t >= 2.0: tier = "GROSS_ONLY"
    r = RG.loc[n] if n in RG.index else None
    regdep = False
    if r is not None:
        vt = [r[f"{g}_net_t"] for g in ("LOWVOL","HIGHVOL") if r[f"{g}_net_t"] == r[f"{g}_net_t"]]; tt = [r[f"{g}_net_t"] for g in ("UPTREND","DOWNTREND") if r[f"{g}_net_t"] == r[f"{g}_net_t"]]
        for tl in (vt, tt):
            if len(tl) == 2 and ((min(tl) <= -1.5 and max(tl) >= 1.5) or (max(tl) >= 2.5 and a.net_t < 2.0)): regdep = True
    adj[n] = dict(C1_forward_safe=bool(c1), C2_net_pos_both_halves=bool(c2), C3_net_t2_BH=bool(c3), C5_survives_cost_x2=bool(c5), C6_falsification_pass_rate=float(np.mean(checks)) if checks else None, C6=bool(c6), tier=tier, regime_dependent=bool(regdep), net_t=float(a.net_t), gross_t=float(a.gross_t))
J = pd.DataFrame(adj).T; J.index.name = "primitive"
sup = [n for n in J.index if J.loc[n, "tier"].startswith("SUPPORTED")]
nonred = []
for n in sorted(sup, key=lambda k: -J.loc[k, "net_t"]):
    if all(abs(C_sig.loc[n, m]) < 0.5 and abs(C_g.loc[n, m]) < 0.5 for m in nonred): nonred.append(n)
final = dict(PRIMITIVES_EXECUTED=len(J), FORWARD_SAFE_COUNT=int(J.C1_forward_safe.sum()), SUPPORTED=sup, ROBUST=[n for n in sup if J.loc[n, "tier"] == "SUPPORTED_ROBUST"], NONREDUNDANT=nonred, REGIME_DEPENDENT=[n for n in J.index if J.loc[n, "regime_dependent"]],
             GROSS_ONLY=[n for n in J.index if J.loc[n, "tier"] == "GROSS_ONLY"], effN_signals=effN_s, effN_pnl=effN, placebo=F.get("_placebo"))
json.dump(dict(table=adj, final=final), open(R + "adjudication.json", "w"), indent=1, default=float)
w("10_adjudication.md", md(J[["C1_forward_safe","C2_net_pos_both_halves","C3_net_t2_BH","C5_survives_cost_x2","C6_falsification_pass_rate","tier","regime_dependent","net_t","gross_t"]], "{:.2f}"))
print(json.dumps(final, indent=1, default=float))
