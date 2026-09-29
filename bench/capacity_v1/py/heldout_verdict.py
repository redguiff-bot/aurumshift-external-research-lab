"""Pre-registered held-out adjudication.  The rules below were fixed BEFORE the held-out run
(see ../prereg/PREREGISTRATION.json, which stores this file's sha256).
Usage: python3 heldout_verdict.py   -> results/heldout_verdict.json"""
import json, os, sys
import numpy as np, pandas as pd

RES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results")
PRE = json.load(open(os.path.join(RES, "..", "prereg", "PREREGISTRATION.json")))
D_MAT, D_EQ = PRE["thresholds"]["delta_material"], PRE["thresholds"]["delta_equivalence"]
SHORT = PRE["shortlist"]
CAPS = PRE["caps"]
rng = np.random.default_rng(PRE["bootstrap_seed"])


def ci(x, n=4000):
    x = np.asarray(x, float); x = x[np.isfinite(x)]
    m = x[rng.integers(0, len(x), (n, len(x)))].mean(1)
    return float(np.quantile(m, .025)), float(np.quantile(m, .975))


def pair(df, pol, ref, metric="lat_per_slot_hour"):
    key = ["family", "variant", "seed", "cap"]
    a = df[df.policy == pol].set_index(key)
    b = df[df.policy == ref].set_index(key)
    d = pd.DataFrame({"dz": (a[metric] - b[metric]) / b["dens0_sd"]}).reset_index()
    return d


def stats(df, pol, ref):
    d = pair(df, pol, ref)
    blk = d.groupby(["family", "variant", "seed"]).dz.mean().values          # pooled over caps
    lo, hi = ci(blk)
    cells = d.groupby(["family", "cap"]).dz.apply(list)
    cl = {k: ci(v, 800) for k, v in cells.items()}
    cm = d.groupby(["family", "cap"]).dz.mean()
    n = len(cm)
    percap = {int(c): d[d.cap == c].dz.mean() for c in CAPS}
    percap_ci = {int(c): ci(d[d.cap == c].groupby(["family", "variant", "seed"]).dz.mean().values, 1000) for c in CAPS}
    return dict(pooled=float(blk.mean()), lo=lo, hi=hi,
                frac_cells_pos=float(np.mean([cl[k][0] > 0 for k in cm.index])),
                frac_cells_mat_neg=float(np.mean([(cm[k] <= -D_MAT) and (cl[k][1] < 0) for k in cm.index])),
                frac_cells_mat_pos=float(np.mean([(cm[k] >= D_MAT) and (cl[k][0] > 0) for k in cm.index])),
                percap=percap, percap_ci=percap_ci, n_cells=int(n))


def main():
    RAW = os.environ.get("RAW", "heldout_raw.csv.gz")
    df = pd.read_csv(f"{RES}/{RAW}")
    val = json.load(open(f"{RES}/validation.json"))
    leak_ok = bool(val["leakage"]["NO_LOOKAHEAD_PROVEN_within_tested_scope"])
    out = dict(leak_ok=leak_ok)
    methods = ["RANK_NET"] + SHORT
    S = {m: dict(vs_FIFO=stats(df, m, "FIFO"), vs_FIFO_NETPOS=stats(df, m, "FIFO_NETPOS")) for m in methods}
    S["FIFO_NETPOS"] = dict(vs_FIFO=stats(df, "FIFO_NETPOS", "FIFO"))
    for m in SHORT:
        S[m]["vs_RANK_NET"] = stats(df, m, "RANK_NET")
    out["stats"] = S

    def core(m):
        s = S[m]["vs_FIFO"]
        return s["pooled"] >= D_MAT and s["lo"] > 0 and s["frac_cells_pos"] >= 0.60 and s["frac_cells_mat_neg"] <= 0.15

    sup_adv = {}
    for m in SHORT:
        r = S[m]["vs_RANK_NET"]
        beats = r["pooled"] >= D_EQ and r["lo"] > 0 and sum(r["percap"][c] > 0 for c in CAPS) >= 3
        sup_adv[m] = bool(core(m) and beats and leak_ok)
    rn = S["RANK_NET"]
    simple_ok = bool(core("RANK_NET") and rn["vs_FIFO_NETPOS"]["pooled"] >= D_EQ and rn["vs_FIFO_NETPOS"]["lo"] > 0 and leak_ok)
    equiv_to_simple = [m for m in SHORT if core(m) and abs(S[m]["vs_RANK_NET"]["pooled"]) < D_EQ]
    width = max(S[m]["vs_FIFO"]["hi"] - S[m]["vs_FIFO"]["lo"] for m in methods) / 2
    out.update(sup_adv=sup_adv, simple_ok=simple_ok, equiv_to_simple=equiv_to_simple, max_ci_halfwidth=float(width))

    winners = [m for m, v in sup_adv.items() if v]
    if (not leak_ok) or width > D_MAT:
        verdict = "STUDY_INCONCLUSIVE"
    elif winners:
        # separable? a winner dominates another if its paired advantage over it is >= D_EQ with CI>0
        top = max(winners, key=lambda m: S[m]["vs_RANK_NET"]["pooled"])
        others = [m for m in winners if m != top]
        indist = [m for m in others if S[top]["vs_RANK_NET"]["pooled"] - S[m]["vs_RANK_NET"]["pooled"] < D_EQ]
        verdict = "MULTIPLE_CAPACITY_METHODS_SUPPORTED" if indist else "CAPACITY_ALLOCATION_REFERENCE_SUPPORTED"
        out["reference_method"] = top; out["indistinguishable_from_top"] = indist
    elif simple_ok:
        verdict = "MULTIPLE_CAPACITY_METHODS_SUPPORTED" if len(equiv_to_simple) >= 2 else "CAPACITY_ALLOCATION_REFERENCE_SUPPORTED"
        out["reference_method"] = "RANK_NET"; out["equivalent_to_RANK_NET"] = equiv_to_simple
    else:
        # nothing beats FIFO_NETPOS materially: is FIFO(+admissibility filter) enough?
        fn = S["FIFO_NETPOS"]["vs_FIFO"]
        verdict = "FIFO_REMAINS_SUFFICIENT" if not core("RANK_NET") or rn["vs_FIFO_NETPOS"]["hi"] < D_EQ else "NO_CAPACITY_METHOD_SUPPORTED"
    out["FINAL_VERDICT"] = verdict

    # FIFO failure / equivalence per family (pre-registered: max over {RANK_NET}+SHORT of family-level dz, caps 4 and 6 pooled)
    fam_rows = []
    for fam in sorted(df.family.unique()):
        best = None
        for m in methods:
            d = pair(df[df.family == fam], m, "FIFO"); d = d[d.cap.isin([4, 6])]
            blk = d.groupby(["variant", "seed"]).dz.mean().values
            lo, hi = ci(blk, 1500)
            row = dict(method=m, dz=float(blk.mean()), lo=lo, hi=hi)
            if best is None or row["dz"] > best["dz"]: best = row
        # same versus FIFO_NETPOS (filtering removed)
        d = pair(df[df.family == fam], best["method"], "FIFO_NETPOS"); d = d[d.cap.isin([4, 6])]
        b2 = d.groupby(["variant", "seed"]).dz.mean().values; l2, h2 = ci(b2, 1500)
        fam_rows.append(dict(family=fam, best_method=best["method"], dz_vs_FIFO=best["dz"], lo=best["lo"], hi=best["hi"],
                             dz_vs_FIFO_NETPOS=float(b2.mean()), lo_np=l2, hi_np=h2,
                             FIFO_FAIL=bool(best["dz"] >= D_MAT and best["lo"] > 0), FIFO_EQUIV=bool(best["hi"] < D_EQ + 0.02)))
    out["family_fifo_table"] = fam_rows
    out["FIFO_FAILURE_SCENARIOS"] = [r["family"] for r in fam_rows if r["FIFO_FAIL"]]
    out["FIFO_EQUIVALENT_SCENARIOS"] = [r["family"] for r in fam_rows if r["FIFO_EQUIV"]]
    json.dump(out, open(os.environ.get("OUTF", f"{RES}/heldout_verdict.json"), "w"), indent=1, default=float)
    print(json.dumps({k: v for k, v in out.items() if k not in ("stats", "family_fifo_table")}, indent=1, default=float))


if __name__ == "__main__":
    main()
