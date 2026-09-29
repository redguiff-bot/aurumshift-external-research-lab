"""Turns results/main.json (+tuning_rows.json, determinism.json) into markdown tables and a machine-checked verdict.
The criteria below are the PRE-REGISTERED ones from reports/013_online_learning/02_PROTOCOL.md (written before main.json existed)."""
import json, os, numpy as np
from collections import defaultdict
R = os.path.join(os.path.dirname(__file__), "../results")
rows = json.load(open(f"{R}/main.json")); tun = json.load(open(f"{R}/tuning_rows.json")); det = json.load(open(f"{R}/determinism.json"))
tuned = json.load(open(f"{R}/tuned_config.json"))
DRIFT = ["abrupt", "gradual", "recurring", "shock", "random_walk", "abrupt_missing", "abrupt_delayed", "abrupt_nonlinear"]
CONTROL = ["stationary", "false_drift"]; ALL = DRIFT + CONTROL
SIMPLE = ["frozen", "batch", "rolling"]
rng = np.random.default_rng(0)

def key(r): return (r["kind"], r["model"], r["scenario"])
by = defaultdict(dict)
for r in rows: by[key(r)][r["seed"]] = r
seeds = sorted({r["seed"] for r in rows})
models = {k: sorted({m for (kk, m, _) in by if kk == k}) for k in "CR"}
def reg(k, m, sc): return np.array([by[(k, m, sc)][s]["regret"] for s in seeds])

# ---- best simple reference: chosen on TUNING seeds (drift scenarios), never on held-out ---------------------------
def tuning_agg(kind, m):
    v = [np.mean([r["regret"] for r in tun if r["kind"] == kind and r["model"] == m and r["scenario"] == sc and r["cfg"] == tuned[f"{m}|{kind}"]["cfg_index"]]) for sc in DRIFT]
    return float(np.mean(v))
best_simple = {k: min(SIMPLE, key=lambda m: tuning_agg(k, m)) for k in "CR"}
INCR = {k: [m for m in models[k] if m not in SIMPLE] for k in "CR"}
best_incr_tuning = {k: min(INCR[k], key=lambda m: tuning_agg(k, m)) for k in "CR"}

def boot_ci(x, n=4000):
    x = np.asarray(x); b = [x[rng.integers(0, len(x), len(x))].mean() for _ in range(n)]; return float(np.percentile(b, 2.5)), float(np.percentile(b, 97.5))

out = dict(seeds=seeds, best_simple_by_tuning=best_simple, best_incremental_by_tuning=best_incr_tuning, criteria={}, per_model={})
md = []
# ---- table 1: regret by scenario -------------------------------------------------------------------------------------
for k, unit in (("C", "excess KL (nats/step) vs generating probability"), ("R", "excess MSE vs true conditional mean")):
    md.append(f"\n### Track {k} — mean {unit}, held-out seeds n={len(seeds)}, mean ± sd\n")
    md.append("| model | " + " | ".join(ALL) + " | drift-geomean ratio vs " + best_simple[k] + " |")
    md.append("|---|" + "---|" * (len(ALL) + 1))
    base = {sc: reg(k, best_simple[k], sc) for sc in ALL}
    for m in models[k]:
        cells = []
        for sc in ALL: v = reg(k, m, sc); cells.append(f"{v.mean():.3f}±{v.std(ddof=1):.3f}")
        per_seed = np.exp(np.mean([np.log((reg(k, m, sc) + 1e-6) / (base[sc] + 1e-6)) for sc in DRIFT], axis=0))
        lo, hi = boot_ci(per_seed); gm = float(np.exp(np.mean(np.log(per_seed))))
        md.append(f"| {m}{' **(ref)**' if m == best_simple[k] else ''} | " + " | ".join(cells) + f" | {gm:.2f} [{lo:.2f},{hi:.2f}] |")
        # ---- criteria --------------------------------------------------------------------------------------------------
        ratio_sc = {sc: float(reg(k, m, sc).mean() / (base[sc].mean() + 1e-9)) for sc in ALL}
        sz = [(by[(k, m, sc)][s]["size4000"] / by[(k, m, sc)][s]["size1000"]) for sc in ALL for s in seeds]
        d = det["rows"]; dm = [x for x in d if x["model"] == m and x["kind"] == k][0]
        crit = dict(
            a_gain=dict(ratio=gm, ci=[lo, hi], passed=bool(gm <= 0.90 and hi < 1.0)),
            b_no_blowup=dict(max_ratio_scenario=max(ratio_sc, key=ratio_sc.get), max_ratio=max(ratio_sc.values()), passed=bool(max(ratio_sc.values()) <= 1.25)),
            c_bounded_state=dict(max_growth_1000_to_4000=float(max(sz)), size4000_median=float(np.median([by[(k, m, sc)][s]["size4000"] for sc in ALL for s in seeds])),
                                 passed=bool(max(sz) <= 1.5)),
            d_replay=dict(replay=dm["replay_same_process"], cross_process=dm["replay_cross_process"], checkpoint=dm["checkpoint_resume_identical"],
                          no_leak=dm["no_future_leakage"], passed=bool(all(dm[z] for z in ("replay_same_process", "replay_cross_process", "checkpoint_resume_identical", "no_future_leakage")))))
        crit["earns_place"] = bool(all(crit[z]["passed"] for z in ("a_gain", "b_no_blowup", "c_bounded_state", "d_replay")))
        crit["ratio_by_scenario"] = ratio_sc; out["per_model"][f"{m}|{k}"] = crit
    out["criteria"][k] = {m: out["per_model"][f"{m}|{k}"]["earns_place"] for m in INCR[k]}

# ---- table 2: adaptation --------------------------------------------------------------------------------------------
md.append("\n### Adaptation speed — steps to rolling-50 regret <= 1.5x own pre-change level + 0.01 (censored at 600), pooled over seeds; and 600-step post-change regret\n")
for k in "CR":
    md.append(f"\n**Track {k}**\n\n| model | abrupt median steps [%censored] | abrupt post-600 regret | gradual median [%cens] | recurring return(t=2000) median [%cens] | shock post-return regret (t=2100) |\n|---|---|---|---|---|---|")
    for m in models[k]:
        def ad(sc, i): a = np.array([by[(k, m, sc)][s]["adapt_steps"][i] for s in seeds]); return f"{np.median(a):.0f} [{100*np.mean(a>=600):.0f}%]"
        pr = lambda sc, i: np.mean([by[(k, m, sc)][s]["post_regret"][i] for s in seeds])
        md.append(f"| {m} | {ad('abrupt',0)} | {pr('abrupt',0):.3f} | {ad('gradual',0)} | {ad('recurring',1)} | {pr('shock',1):.3f} |")

# ---- table 3: forgetting / recurring ---------------------------------------------------------------------------------
md.append("\n### Forgetting and recurring-state recovery (scenario `recurring`; probes at t=999 end-A1, 1999 end-B1, 2999 end-A2, 3999 end-B2)\n")
ign = dict(C=None, R=1.0)
for k in "CR":
    md.append(f"\n**Track {k}** (probe loss on fixed probe set; C: KL(p_true||p_model), R: MSE vs true mean; ignorance level R=1.0, C≈{'see 05'} )\n\n"
              "| model | probeA end-A1 | probeA end-B1 (forgetting) | probeB end-B1 (plasticity) | probeA end-A2 (re-learned A) | return-cost ratio post600(t=2000)/post600(t=1000) | adapt steps t=2000 vs t=1000 |\n|---|---|---|---|---|---|---|")
    for m in models[k]:
        P = lambda t, j: np.mean([by[(k, m, "recurring")][s]["probes"][str(t)][j] for s in seeds])
        cr = np.mean([by[(k, m, "recurring")][s]["post_regret"][1] / (by[(k, m, "recurring")][s]["post_regret"][0] + 1e-9) for s in seeds])
        a = [np.median([by[(k, m, "recurring")][s]["adapt_steps"][i] for s in seeds]) for i in (0, 1)]
        md.append(f"| {m} | {P(999,0):.3f} | {P(1999,0):.3f} | {P(1999,1):.3f} | {P(2999,0):.3f} | {cr:.2f} | {a[1]:.0f} vs {a[0]:.0f} |")
        out["per_model"][f"{m}|{k}"]["recur"] = dict(return_cost_ratio=float(cr), adapt_return=a[1], adapt_novel=a[0])

# ---- table 4: variance, state, compute -------------------------------------------------------------------------------
md.append("\n### Variance, state growth, compute (all scenarios pooled)\n")
for k in "CR":
    md.append(f"\n**Track {k}**\n\n| model | median CV of regret across seeds | worst-seed / median-seed regret (max over scenarios) | state bytes @1000 (median) | @4000 (median) | max growth ratio | learn µs/label | predict µs |\n|---|---|---|---|---|---|---|---|")
    for m in models[k]:
        cvs, worst = [], []
        for sc in ALL:
            v = reg(k, m, sc); cvs.append(v.std(ddof=1) / (v.mean() + 1e-9)); worst.append(v.max() / (np.median(v) + 1e-9))
        s1 = np.median([by[(k, m, sc)][s]["size1000"] for sc in ALL for s in seeds]); s4 = np.median([by[(k, m, sc)][s]["size4000"] for sc in ALL for s in seeds])
        g = out["per_model"][f"{m}|{k}"]["c_bounded_state"]["max_growth_1000_to_4000"]
        tl = np.median([by[(k, m, sc)][s]["t_learn_us"] for sc in ALL for s in seeds]); tp = np.median([by[(k, m, sc)][s]["t_pred_us"] for sc in ALL for s in seeds])
        md.append(f"| {m} | {np.median(cvs):.2f} | {max(worst):.1f} | {s1:,.0f} | {s4:,.0f} | {g:.2f} | {tl:.0f} | {tp:.0f} |")

# ---- accuracy / logloss context (C) -----------------------------------------------------------------------------------
md.append("\n### Track C realised accuracy and log-loss (held-out, post burn-in) — context for the KL numbers\n\n| model | " + " | ".join(ALL) + " |\n|---|" + "---|" * len(ALL))
for m in models["C"]:
    md.append(f"| {m} | " + " | ".join(f"{np.mean([by[('C',m,sc)][s]['metric'] for s in seeds]):.3f} / {np.mean([by[('C',m,sc)][s]['logloss'] for s in seeds]):.3f}" for sc in ALL) + " |")

# ---- best references on held-out --------------------------------------------------------------------------------------
def agg(k, m): return float(np.exp(np.mean([np.log(reg(k, m, sc).mean() + 1e-6) for sc in DRIFT])))
out["heldout_geomean_regret_drift"] = {k: {m: agg(k, m) for m in models[k]} for k in "CR"}
out["best_simple_heldout"] = {k: min(SIMPLE, key=lambda m: agg(k, m)) for k in "CR"}
out["best_incremental_heldout"] = {k: min(INCR[k], key=lambda m: agg(k, m)) for k in "CR"}
tun_rank = [tuning_agg("C", m) for m in models["C"]]; held_rank = [agg("C", m) for m in models["C"]]
from scipy.stats import spearmanr
out["tuning_vs_heldout_spearman"] = {k: float(spearmanr([tuning_agg(k, m) for m in models[k]], [agg(k, m) for m in models[k]])[0]) for k in "CR"}
out["negative_control_cheater_detected"] = det["negative_control"]["cheater_detected"]
json.dump(out, open(f"{R}/summary.json", "w"), indent=1)
open(f"{R}/tables.md", "w").write("\n".join(md)); print("\n".join(md)); print(json.dumps({k: out[k] for k in out if k != "per_model"}, indent=1))
