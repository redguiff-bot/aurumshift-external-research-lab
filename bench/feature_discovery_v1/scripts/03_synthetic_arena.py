"""Falsification arena: run the FULL pipeline on synthetic panels with known truth.
NULL  : y has no signal -> measures false-discovery rate (family-wise) of the whole procedure.
MIXED : 5 planted components (linear, interaction, pure-nonlinear, market-specific, decaying) + near-duplicate feature.
Dev seeds 0..9 were used while debugging; final numbers use seeds >= 1000 never touched during tuning."""
import sys, os, json, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import numpy as np
from joblib import Parallel, delayed
from sklearn.linear_model import Ridge
from fd import synth, pipeline as P, expr as E
from fd.metrics import spearman

CFG = P.Cfg(gp_rows=8000)
COMPS = ["c1_linear", "c2_interaction", "c3_square", "c4_market_specific", "c5_decaying"]


def run_rep(scn, seed):
    tr, va, ho, truth, un = synth.make_panel(scn, seed)
    N = synth.NAMES
    sr = [P.discover_seed(tr, va, N, s + seed * 7, CFG) for s in CFG.seeds]
    fin, info = P.consolidate(sr, tr, va, N, CFG)
    frozen = P.freeze(fin, tr, N)
    Xp = np.vstack([np.vstack([tr[m][0], va[m][0]]) for m in tr]); yp = np.concatenate([np.concatenate([tr[m][1], va[m][1]]) for m in tr])
    rb = Ridge(alpha=100).fit(Xp, yp)
    bp = {m: rb.predict(ho[m][0]) for m in ho}
    recs = P.evaluate_heldout(frozen, ho, set(un), N, bp, B=500, seed=seed)
    recs = P.decide(recs, family_size=max(len(recs), 1))
    mains = info.get("mains", [])
    out = dict(scn=scn, seed=seed, mains=mains, c1_main_recovered=bool({"f00", "f06"} & set(mains)),
               false_mains=sorted(set(mains) - {"f00", "f06", "f01", "f02", "f03", "f04", "f05"}),
               both_duplicates_selected=bool({"f00", "f06"} <= set(mains)), n_val_pass_any_seed=int(sum(len(s["selected"]) for s in sr)), n_frozen=len(frozen), n_stable=0, n_novel=0,
               recovered=[], false_stable=0, nonpersistent_stable=[], stable=[])
    for c, r in zip(frozen, recs):
        if not r["stable"]:
            continue
        out["n_stable"] += 1; out["n_novel"] += int(r["novel_vs_baseline"])
        v = np.concatenate([P.cand_value(c, ho[m][0], N) for m in ho])
        cor = {k: abs(spearman(v, np.concatenate([truth[m][k] for m in ho]))) for k in COMPS}
        best = max(cor, key=cor.get)
        rec = dict(expr=c["expr"], corr=cor, best=best)
        if cor[best] >= 0.5:
            (out["recovered"] if best in COMPS[:3] else out["nonpersistent_stable"]).append(best)
        else:
            out["false_stable"] += 1
        out["stable"].append(rec)
    out["recovered"] = sorted(set(out["recovered"]))
    return out


if __name__ == "__main__":
    reps = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    base = int(sys.argv[2]) if len(sys.argv) > 2 else 1000
    tag = sys.argv[3] if len(sys.argv) > 3 else "final"
    t = time.time()
    jobs = [(scn, base + i) for scn in ("NULL", "MIXED") for i in range(reps)]
    res = Parallel(n_jobs=4)(delayed(run_rep)(s, i) for s, i in jobs)
    json.dump(res, open(os.path.join(os.path.dirname(__file__), "..", "results", f"synthetic_arena_{tag}.json"), "w"), indent=1)
    for scn in ("NULL", "MIXED"):
        R = [r for r in res if r["scn"] == scn]
        print(scn, "reps", len(R), "any_frozen", np.mean([r["n_frozen"] > 0 for r in R]), "FWER(any stable)", np.mean([r["n_stable"] > 0 for r in R]),
              "mean stable", np.mean([r["n_stable"] for r in R]), "false_stable_mean", np.mean([r["false_stable"] for r in R]))
    R = [r for r in res if r["scn"] == "MIXED"]
    print("power c1_linear (via stable mains f00/f06)", np.mean([r["c1_main_recovered"] for r in R]), "both duplicates selected", np.mean([r["both_duplicates_selected"] for r in R]))
    print("false mains: NULL", np.mean([len(r["false_mains"]) > 0 for r in res if r["scn"] == "NULL"]), "MIXED", np.mean([len(r["false_mains"]) > 0 for r in R]))
    for k in COMPS[1:3]:
        print("power", k, np.mean([k in r["recovered"] for r in R]))
    for k in COMPS[3:]:
        print("nonpersistent stable", k, np.mean([k in r["nonpersistent_stable"] for r in R]))
    print("time", time.time() - t)
