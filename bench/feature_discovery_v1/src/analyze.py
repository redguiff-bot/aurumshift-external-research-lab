"""Aggregate results -> results/summary.json + results/summary.md (tables used by the reports)."""
import json, glob, os, re, sys
import numpy as np
R = os.path.join(os.path.dirname(__file__), "..", "results")
P = json.load(open(os.path.join(os.path.dirname(__file__), "..", "configs", "protocol.json")))
L = lambda m: [json.load(open(f)) for f in sorted(glob.glob(f"{R}/{m}/run_*.json"))]

def synth_validity(runs):
    rec, fp, trap, n = [], [], [], len(runs)
    rows = []
    for r in runs:
        got = r["planted_recovered"]; rec.append(np.mean(list(got.values())))
        # false discoveries: held-out-stable nonredundant NEW features that are not a planted composite
        bad = [h["key"] for h in r["heldout"] if h["stable"] and h["nonredundant"] and h["new_incremental"]
               and not any(h["key"].replace(" ", "") in (f"prod:(f1*f2)", "prod:(f2*f1)", "gate:(f3*|f4|)") for _ in [0])]
        fp.append(len(bad))
        t = [h for h in r["heldout"] if "f5" in h["key"]]
        trap.append(dict(retained=len(t), flagged_noninvariant=sum(1 for h in t if not h["invariant"])))
        rows.append(dict(seed=r["run_seed"], recovered=got, false_disc=bad, final=[h["key"] for h in r["heldout"]], f5_trap=trap[-1],
                         planted_inv=[(h["key"], h["invariant"], round(h["Q_p"], 3)) for h in r["heldout"] if h["stable"]],
                         raw_r2=r["perf"]["B1_raw_ridge"]["r2"], disc_r2=r["perf"].get("DISC_raw_plus_final", {}).get("r2"),
                         gbm_r2=r["perf"]["B5_gbm_full"]["r2"], lasso_r2=r["perf"]["B2_lasso"]["r2"]))
    pv = P["synthetic_validity"]
    ok = (np.mean(rec) >= pv["min_recall_planted"]) and (np.mean(fp) <= pv["max_false_discovery_per_run"])
    return dict(n_runs=n, mean_recall=float(np.mean(rec)), mean_false_disc=float(np.mean(fp)), pass_=bool(ok), runs=rows)

def null_validity(runs):
    c = [r["counts"] for r in runs]
    st = [x["heldout_stable"] for x in c]; nw = [x["new_stable_nonredundant"] for x in c]
    ok = np.mean(st) <= P["null_validity"]["max_mean_heldout_stable_under_null"]
    return dict(n_runs=len(runs), heldout_stable_per_run=st, new_nonredundant_per_run=nw, discovered=[x["discovered"] for x in c],
                passed_validation=[x["passed_validation"] for x in c], final=[x["final"] for x in c],
                mean_stable=float(np.mean(st)), mean_new=float(np.mean(nw)), pass_=bool(ok),
                null_delta_r2=[r["complexity"].get("DISC_raw_plus_final_vs_B1", {}).get("delta") for r in runs])

def consensus(runs, seed_min=3):
    """cluster the final lists of all seeds by |corr| of validation vectors (>0.9); key-equal features merge automatically"""
    items = []
    for r in runs:
        for h in r["heldout"]: items.append((r["run_seed"], h))
    n = len(items); par = list(range(n))
    def f(a):
        while par[a] != a: par[a] = par[par[a]]; a = par[a]
        return a
    V = [np.array(h["val_vec"]) for _, h in items]
    for i in range(n):
        for j in range(i + 1, n):
            if items[i][1]["key"] == items[j][1]["key"] or (len(V[i]) == len(V[j]) and abs(np.corrcoef(V[i], V[j])[0, 1]) > 0.9): par[f(i)] = f(j)
    g = {}
    for i in range(n): g.setdefault(f(i), []).append(i)
    out = []
    for m in g.values():
        seeds = sorted({items[i][0] for i in m}); hs = [items[i][1] for i in m]
        rep = min(m, key=lambda i: (items[i][1]["nodes"], items[i][1]["key"]))
        frac = lambda k: float(np.mean([h[k] for h in hs]))
        out.append(dict(key=items[rep][1]["key"], formula=items[rep][1]["formula"], kind=items[rep][1]["kind"], nodes=items[rep][1]["nodes"],
                        n_seeds_selected=len(seeds), seeds=seeds, stable_frac=frac("stable"), nonred_frac=frac("nonredundant"),
                        new_frac=frac("new_incremental"), invariant_frac=frac("invariant"),
                        ic_val=float(np.mean([h["ic_val"] for h in hs])), ic_test=float(np.mean([h["ic_test"] for h in hs])),
                        ic_test_unseen=float(np.mean([h["ic_test_unseen"] for h in hs if h["ic_test_unseen"] is not None] or [np.nan])),
                        partial_ic=float(np.mean([h["partial_ic_vs_raw"] for h in hs])), p_test=float(np.median([h["p_test"] for h in hs])),
                        sign_agree=float(np.mean([h["sign_agree_all"] for h in hs])), Q_p=float(np.median([h["Q_p"] for h in hs])),
                        half1=float(np.mean([h["half1"] for h in hs])), half2=float(np.mean([h["half2"] for h in hs])),
                        dec_val=np.mean([h["dec_val"] for h in hs], 0).tolist() if "dec_val" in hs[0] else None,
                        dec_test=np.mean([h["dec_test"] for h in hs], 0).tolist() if "dec_test" in hs[0] else None,
                        why=sorted({w for h in hs for w in h["why"]}), per_market=np.mean([h["per_market"] for h in hs], 0).tolist()))
    for o in out:
        o["seed_stable"] = o["n_seeds_selected"] >= seed_min
        o["heldout_stable"] = bool(o["seed_stable"] and o["stable_frac"] > 0.5)
        o["nonredundant"] = bool(o["heldout_stable"] and o["nonred_frac"] > 0.5)
        o["new"] = bool(o["nonredundant"] and o["new_frac"] > 0.5 and o["kind"] != "prim")
        o["invariant"] = bool(o["heldout_stable"] and o["invariant_frac"] > 0.5)
        o["class"] = ("CAUSAL_HYPOTHESIS" if (o["invariant"] and o["new"] and o["n_seeds_selected"] >= len(runs) - 1 and False) else
                      "INVARIANT_ASSOCIATION" if o["invariant"] else "PREDICTIVE" if o["heldout_stable"] else "NOT_STABLE")
    return sorted(out, key=lambda o: -o["n_seeds_selected"])

def real_summary(runs):
    c = [r["counts"] for r in runs]; cons = consensus(runs)
    # redundancy between consensus stable features (validation vectors of representatives are not stored across clusters -> use per-run flag)
    perf = {}
    for k in runs[0]["perf"]:
        v = [r["perf"][k] for r in runs if k in r["perf"]]
        perf[k] = dict(r2_mean=float(np.mean([x["r2"] for x in v])), r2_min=float(np.min([x["r2"] for x in v])), r2_max=float(np.max([x["r2"] for x in v])),
                       ic_mean=float(np.mean([x["ic"] for x in v])), r2_disc_mk=float(np.mean([x["r2_disc_mk"] for x in v])),
                       r2_unseen_mk=float(np.mean([x["r2_unseen_mk"] for x in v])), n=len(v))
    comp = {}
    for k in ("DISC_raw_plus_final_vs_B1", "DISC_raw_plus_stable_nonredundant_vs_B1"):
        v = [r["complexity"][k] for r in runs if k in r["complexity"]]
        if v: comp[k] = dict(n=len(v), delta_mean=float(np.mean([x["delta"] for x in v])), lo_min=float(np.min([x["lo"] for x in v])),
                             lo_mean=float(np.mean([x["lo"] for x in v])), hi_mean=float(np.mean([x["hi"] for x in v])),
                             markets_improve_mean=float(np.mean([x["markets_improve"] for x in v])))
    return dict(per_seed_counts=c, consensus=cons, perf=perf, complexity=comp, lock_sha=[r["lock"]["sha256"] for r in runs],
                baseline_meta=[r["baseline_meta"] for r in runs], runtime=[r["runtime_s"] for r in runs])

def verdict(real, syn, nul):
    cons = real["consensus"]
    n_stable = sum(o["heldout_stable"] for o in cons); n_nonred = sum(o["nonredundant"] for o in cons); n_new = sum(o["new"] for o in cons)
    just = False
    for k, v in real["complexity"].items():
        if v["lo_mean"] > 0 and v["markets_improve_mean"] > 0.5: just = True
    valid = syn["pass_"] and nul["pass_"]
    if not valid: v = "STUDY_INCONCLUSIVE"
    elif n_new >= 3 and just: v = "FEATURE_DISCOVERY_REFERENCE_SUPPORTED"
    elif n_nonred >= 1: v = "LIMITED_STABLE_FEATURES_SUPPORTED"
    else: v = "NO_STABLE_NEW_FEATURES"
    return dict(n_stable=n_stable, n_nonred=n_nonred, n_new=n_new, complexity_justified=just, valid=valid, verdict=v)

if __name__ == "__main__":
    out = {}
    s, n, r = L("synth"), L("null"), L("real")
    if s: out["synth"] = synth_validity(s)
    if n: out["null"] = null_validity(n)
    if r: out["real"] = real_summary(r)
    if s and n and r: out["verdict"] = verdict(out["real"], out["synth"], out["null"])
    json.dump(out, open(f"{R}/summary.json", "w"), indent=1, default=lambda x: x.item() if hasattr(x, "item") else str(x))
    print(json.dumps({k: (v if k == "verdict" else {kk: vv for kk, vv in v.items() if kk in ("n_runs", "mean_recall", "mean_false_disc", "pass_", "mean_stable", "mean_new", "heldout_stable_per_run")}) for k, v in out.items()}, indent=1, default=str))
