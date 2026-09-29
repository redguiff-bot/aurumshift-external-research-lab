"""Analysis of held-out runs against the pre-registered gates. Writes ../results/{gates.json,tables.md}."""
import json, gzip, sys
import numpy as np
import scenarios as S, registry as G

OUT = "../results/"
rng = np.random.default_rng(12345)
rec = {}
for line in gzip.open(OUT + "heldout_runs.jsonl.gz", "rt"):
    m = json.loads(line)
    rec[(m["method"], m["mode"], m["tag"], m["scenario"], m["seed"])] = m
HELD = list(range(1000, 1040)); SS = list(range(2000, 2020))
CORE = S.CORE
METHODS = list(G.REG)
FAM = {"A": ["SleepHedge", "SleepEG", "FixedShare", "DiscFreeze", "DiscAmnesty", "SH_bounded", "CtxOracle",
             "CtxLag", "CtxNoisy", "DivSH"],
       "B": ["EWMA", "EWMA_bounded", "WTA", "BMA", "DivEWMA", "Static", "Equal"],
       "C": ["SleepEXP3", "DUCB", "HedgePlain"]}
fam_of = {m: f for f, ms in FAM.items() for m in ms}


def arr(meth, scen, key="regret", mode="correct", tag="heldout", seeds=HELD):
    return np.array([rec[(meth, mode, tag, scen, s)][key] for s in seeds])


def pr_seed(meth, mode="correct", tag="heldout", seeds=HELD, scen=CORE):
    return np.mean([arr(meth, sc, "regret", mode, tag, seeds) for sc in scen], axis=0)   # per seed


def boot_ci(d, n=2000):
    idx = rng.integers(0, len(d), (n, len(d)))
    b = d[idx].mean(1)
    return float(np.percentile(b, 2.5)), float(np.percentile(b, 97.5))


PR = {m: pr_seed(m) for m in METHODS}
PRm = {m: float(PR[m].mean()) for m in METHODS}
bb = min(G.BASELINES, key=lambda m: PRm[m])
res = {"best_baseline": bb, "PR": PRm}
gates = {}
for m in METHODS:
    g = {}
    d = PR[bb] - PR[m]
    lo, hi = boot_ci(d)
    g["G1"] = bool(PRm[m] <= 0.9 * PRm[bb] and lo > 0) if m != bb else False
    g["G1_detail"] = dict(ratio=PRm[m] / PRm[bb], ci_diff=[lo, hi])
    s0 = arr(m, "S0_base").mean()
    ratios = {sc: float(arr(m, sc).mean() / s0) for sc in ("S6a_gap_mcar", "S6b_gap_burst", "S6d_abstain_informative")}
    g["G2a"] = all(v <= 1.5 for v in ratios.values()); g["G2a_detail"] = ratios
    if m in G.NAIVE_SUBSET:
        dn = pr_seed(m, "naive_zero") - PR[m]
        lo2, hi2 = boot_ci(dn)
        g["G2b"] = bool(lo2 > 0); g["G2b_detail"] = dict(naive_minus_correct=float(dn.mean()), ci=[lo2, hi2])
    else:
        g["G2b"] = True; g["G2b_detail"] = "n/a (not in NAIVE_SUBSET)"
    tts = arr(m, "S3_new_expert", "ev", ) if False else np.array([rec[(m, "correct", "heldout", "S3_new_expert", s)]["ev"]["tts_new"] for s in HELD])
    g["G3a"] = bool(np.median(tts) <= 150 and (tts < 400).mean() >= 0.8)
    g["G3a_detail"] = dict(median=float(np.median(tts)), frac_reached=float((tts < 400).mean()))
    rf = np.array([rec[(m, "correct", "heldout", "S2_dormancy", s)]["ev"]["rare_first25"][1] for s in HELD])
    g["G3b"] = bool(np.nanmean(rf) >= 0.35); g["G3b_detail"] = float(np.nanmean(rf))
    lr = np.array([rec[(m, "correct", "heldout", "S7_temp_underperf", s)]["ev"]["late_recovery"] for s in HELD])
    g["G3c"] = bool(np.median(lr) <= 100); g["G3c_detail"] = dict(median=float(np.median(lr)), mean=float(lr.mean()))
    g["G3"] = g["G3a"] and g["G3b"] and g["G3c"]
    gates[m] = g
# G4a
non_bandit = [m for m in METHODS if m not in G.BANDITS]
worst = {}
for m in METHODS:
    w = 0.0; wsc = None
    for sc in CORE:
        best = min(arr(x, sc).mean() for x in non_bandit)
        r = arr(m, sc).mean() / max(best, 1e-9)
        if r > w: w, wsc = r, sc
    gates[m]["G4a"] = bool(w <= 1.5); gates[m]["G4a_detail"] = dict(worst_ratio=w, scenario=wsc)
# G4b
stress = {}
for tag in ("lowsnr", "highnoise"):
    prs = {m: float(pr_seed(m, "correct", tag, SS).mean()) for m in METHODS}
    bbs = min(prs[b] for b in G.BASELINES)
    stress[tag] = dict(PR=prs, best_baseline=bbs)
for m in METHODS:
    ok = all(stress[t]["PR"][m] <= stress[t]["best_baseline"] + 1e-12 for t in stress)
    gates[m]["G4b"] = bool(ok)
    gates[m]["G4b_detail"] = {t: stress[t]["PR"][m] / stress[t]["best_baseline"] for t in stress}
    gates[m]["G4"] = gates[m]["G4a"] and gates[m]["G4b"]
    gates[m]["G234"] = gates[m]["G2a"] and gates[m]["G2b"] and gates[m]["G3"] and gates[m]["G4"]
    gates[m]["G1234"] = gates[m]["G1"] and gates[m]["G234"]
res["gates"] = gates; res["stress"] = stress

# --- verdict logic
elig = [m for m in METHODS if m not in G.BANDITS and m != "Equal"]
g234 = [m for m in elig if gates[m]["G234"]]
minpr = min(PRm[m] for m in elig)
reason = []
if not g234:
    verdict = "NO_ROBUST_ENSEMBLE_METHOD"; reason.append("no method satisfies G2-G4")
else:
    suff = [b for b in ("Static", "EWMA") if b in g234 and PRm[b] <= 1.10 * minpr]
    passing = [m for m in elig if gates[m]["G1234"] and m != "CtxOracle"]
    famsp = sorted({fam_of[m] for m in passing if fam_of[m] in "AB"})
    if suff:
        verdict = "STATIC_OR_EWMA_SUFFICIENT"; reason.append(f"{suff} pass G2-G4 and within 10% of best PR")
    elif len(famsp) >= 2:
        verdict = "MULTIPLE_ENSEMBLE_METHODS_SUPPORTED"; reason.append(f"families {famsp} pass: {passing}")
    elif passing and len([m for m in passing if fam_of[m] == "A"]) >= 2:
        top = sorted(passing, key=lambda m: PRm[m])
        close = [m for m in top if PRm[m] <= 1.10 * PRm[top[0]]]
        verdict = "MULTIPLE_ENSEMBLE_METHODS_SUPPORTED" if len(close) >= 2 else "SLEEPING_EXPERT_REFERENCE_SUPPORTED"
        reason.append(f"family A passing {top}; within 10% of best: {close}")
    elif passing and fam_of[passing[0]] == "A":
        verdict = "SLEEPING_EXPERT_REFERENCE_SUPPORTED"; reason.append(f"only {passing}")
    else:
        verdict = "STUDY_INCONCLUSIVE"; reason.append(f"passing={passing} g234={g234}")
res["preliminary_verdict"] = verdict; res["verdict_reason"] = reason
res["passing_G1234"] = [m for m in METHODS if gates[m]["G1234"]]
res["passing_G234"] = g234
json.dump(res, open(OUT + "gates.json", "w"), indent=1)

# --- tables
L = []
L.append("| method | fam | PR x1e3 | vs best baseline | CI(bb-m) x1e3 | reward | best_mass | starved | G1 | G2a | G2b | G3a | G3b | G3c | G4a | G4b |")
L.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
for m in sorted(METHODS, key=lambda x: PRm[x]):
    g = gates[m]; d = g["G1_detail"]
    rw = np.mean([arr(m, sc, "reward").mean() for sc in CORE]); bm = np.mean([arr(m, sc, "best_mass").mean() for sc in CORE])
    sv = np.mean([arr(m, sc, "starved").mean() for sc in CORE])
    ck = lambda b: "✔" if b else "✘"
    L.append(f"| {m} | {fam_of[m]} | {PRm[m]*1e3:.2f} | {d['ratio']:.2f}x | [{d['ci_diff'][0]*1e3:.2f},{d['ci_diff'][1]*1e3:.2f}] | {rw:.4f} | {bm:.3f} | {sv:.3f} | {ck(g['G1'])} | {ck(g['G2a'])} | {ck(g['G2b'])} | {ck(g['G3a'])} | {ck(g['G3b'])} | {ck(g['G3c'])} | {ck(g['G4a'])} | {ck(g['G4b'])} |")
L.append("")
L.append("## Regret x1e3 per scenario (held-out mean)\n")
L.append("| method | " + " | ".join(CORE + S.STRESS) + " |")
L.append("|---|" + "---|" * (len(CORE) + len(S.STRESS)))
for m in sorted(METHODS, key=lambda x: PRm[x]):
    L.append(f"| {m} | " + " | ".join(f"{arr(m, sc).mean()*1e3:.1f}" for sc in CORE + S.STRESS) + " |")
L.append("\n## Semantics: naive_zero vs correct (PR x1e3, paired mean diff and 95% CI)\n")
L.append("| method | correct | naive_zero | diff | CI |")
L.append("|---|---|---|---|---|")
for m in G.NAIVE_SUBSET:
    d = pr_seed(m, "naive_zero") - PR[m]; lo, hi = boot_ci(d)
    L.append(f"| {m} | {PRm[m]*1e3:.2f} | {pr_seed(m,'naive_zero').mean()*1e3:.2f} | {d.mean()*1e3:+.2f} | [{lo*1e3:.2f},{hi*1e3:.2f}] |")
L.append("\n## Starvation probes (held-out)\n")
L.append("| method | new-expert tts median (cap400) | reached<400 | rare 1st ep w25 | rare 2nd ep w25 (after dormancy) | rare 3rd... | LATE recovery median (cap 300) |")
L.append("|---|---|---|---|---|---|---|")
for m in sorted(METHODS, key=lambda x: PRm[x]):
    g = gates[m]
    e2 = np.array([rec[(m, "correct", "heldout", "S2_dormancy", s)]["ev"]["rare_first25"] for s in HELD])
    L.append(f"| {m} | {g['G3a_detail']['median']:.0f} | {g['G3a_detail']['frac_reached']:.2f} | {np.nanmean(e2[:,0]):.3f} | {np.nanmean(e2[:,1]):.3f} | – | {g['G3c_detail']['median']:.0f} |")
L.append("\n## Stress sets: PR ratio vs best baseline of that set\n")
L.append("| method | lowsnr(0.5x edges) | highnoise(1.6x) |")
L.append("|---|---|---|")
for m in sorted(METHODS, key=lambda x: PRm[x]):
    L.append(f"| {m} | {gates[m]['G4b_detail']['lowsnr']:.2f} | {gates[m]['G4b_detail']['highnoise']:.2f} |")
open(OUT + "tables.md", "w").write("\n".join(L))
print("best baseline:", bb); print("verdict(prelim):", verdict, reason)
print("G1234:", res["passing_G1234"]); print("G234:", g234)
print("\n".join(L))
