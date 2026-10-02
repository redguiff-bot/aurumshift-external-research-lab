"""Aggregate held-out (+tuning) results into markdown tables: results/tables/*.md and results/key_numbers.json."""
import glob, json, numpy as np, pandas as pd
from scipy import stats
from sklearn.metrics import f1_score, confusion_matrix, precision_recall_fscore_support
import os
os.makedirs("results/tables", exist_ok=True)
KN = {}


def rd(pat): return pd.concat([pd.read_csv(f) for f in sorted(glob.glob(pat))], ignore_index=True)
def md(df, fn, floatfmt=3):
    df = df.copy(); s = df.round(floatfmt).to_markdown(); open(f"results/tables/{fn}.md", "w").write(s + "\n"); return s
def ci(x):
    x = np.asarray(x, float); x = x[~np.isnan(x)]; n = len(x)
    return f"{x.mean():.3f} ± {stats.t.ppf(.975, n - 1) * x.std(ddof=1) / np.sqrt(n):.3f}" if n > 1 else f"{x.mean():.3f}"


# ---------------- static
S = rd("results/static_hold_*_metrics.csv"); S = S[S.phase != "val"]
KN["n_heldout_seeds"] = int(S.seed.nunique())
indist = S[(S.scenario == "none")].groupby(["base", "method"])[["brier", "logloss", "ece", "fcr", "cwm"]].mean()
md(indist, "static_indist")
# paired difference vs raw over seeds (in-dist = pre phase of every scenario is identical -> use scenario none, both phases pooled per seed)
rows = []
for base in ["lr", "gbm"]:
    for m in ["temperature", "platt", "beta", "isotonic", "bayes_bin"]:
        a = S[(S.base == base) & (S.scenario == "none") & (S.method == m)].groupby("seed")[["brier", "logloss", "ece", "cwm"]].mean()
        r = S[(S.base == base) & (S.scenario == "none") & (S.method == "raw")].groupby("seed")[["brier", "logloss", "ece", "cwm"]].mean()
        d = a - r
        rows.append(dict(base=base, method=m, **{f"d_{k}": ci(d[k]) for k in d.columns}))
md(pd.DataFrame(rows), "static_paired_vs_raw")
for base in ["lr", "gbm"]:
    t = S[(S.base == base) & (S.phase == "post")].groupby(["scenario", "method"])["ece"].mean().unstack("method")
    md(t, f"static_shift_ece_{base}")
    t = S[(S.base == base) & (S.phase == "post")].groupby(["scenario", "method"])["cwm"].mean().unstack("method")
    md(t, f"static_shift_cwm_{base}")
# ECE drift = post - pre
dr = S.pivot_table(index=["base", "scenario", "method", "seed"], columns="phase", values="ece").reset_index(); dr["drift"] = dr.post - dr.pre
md(dr.groupby(["base", "scenario", "method"]).drift.mean().unstack("method"), "static_ece_drift")
KN["static_ece_drift_temp_gbm"] = dr[(dr.base == "gbm") & (dr.method == "temperature")].groupby("scenario").drift.mean().round(3).to_dict()
KN["static_ece_drift_temp_lr"] = dr[(dr.base == "lr") & (dr.method == "temperature")].groupby("scenario").drift.mean().round(3).to_dict()
# tuning-seed ranking (selection evidence)
T = rd("results/static_tune_*_metrics.csv"); T = T[T.phase != "val"]
md(T.groupby(["base", "method"])[["brier", "logloss", "ece", "cwm"]].mean(), "static_tuning_ranking")
# risk coverage
K = rd("results/static_hold_*_riskcov.csv")
md(K[K.method == "platt"].groupby(["base", "phase", "score"])[["aurc", "risk_at_50", "risk_at_25"]].mean(), "selective_scores_aurc")
md(K[K.score == "msp"].groupby(["base", "phase", "method"])[["aurc", "risk_at_50", "risk_at_25"]].mean(), "selective_msp_by_calibrator")
md(K[(K.method == "platt") & (K.base == "gbm")].groupby(["scenario", "phase", "score"]).aurc.mean().unstack("score"), "selective_aurc_by_scenario_gbm")

# ---------------- online
O = rd("results/hold_*_online.csv")
o = O[O.phase == "post"]
for base in ["lr", "gbm"]:
    t = o[(o.base == base) & (o.cal == "temperature")].groupby(["scenario", "variant"])[["ece", "brier", "cwm", "turnover", "abstain"]].mean()
    md(t.unstack("variant")["ece"], f"online_ece_{base}"); md(t.unstack("variant")["cwm"], f"online_cwm_{base}")
    md(t.unstack("variant")["turnover"], f"online_turnover_{base}"); md(t.unstack("variant")["abstain"], f"online_abstain_{base}")
    md(t.unstack("variant")["brier"], f"online_brier_{base}")
agg = o.groupby(["base", "cal", "variant"])[["ece", "brier", "logloss", "cwm", "turnover", "abstain", "utility"]].mean()
md(agg, "online_all_variants")
sh = o[o.scenario != "none"]
md(sh.groupby(["base", "cal", "variant"])[["ece", "brier", "cwm", "turnover"]].mean(), "online_shift_only")
KN["online_shift_only_temp"] = sh[sh.cal == "temperature"].groupby(["base", "variant"])[["ece", "brier", "cwm", "turnover"]].mean().round(4).to_dict("index").__repr__()
# stationary cost of online recal
stat = O[(O.scenario == "none")].groupby(["base", "cal", "variant", "phase"])[["ece", "brier", "logloss", "turnover"]].mean()
md(stat, "online_stationary_cost")
# turnover added by recal, paired vs static
pv = o.pivot_table(index=["base", "cal", "scenario", "seed"], columns="variant", values="turnover").reset_index()
pv["d_window"] = pv.window - pv.static; pv["d_decay"] = pv.decay - pv.static
md(pv.groupby(["base", "cal", "scenario"])[["d_window", "d_decay"]].mean(), "online_turnover_delta_vs_static")
# rolling ece trajectories
RL = rd("results/hold_*_rolling.csv")
md(RL[(RL.cal == "temperature") & (RL.base == "gbm")].groupby(["scenario", "variant", "win"]).ece.mean().unstack("win"), "rolling_ece_gbm_temp")
# lookahead inflation
lk = sh[(sh.cal == "beta")].pivot_table(index=["base", "scenario", "seed"], columns="variant", values="ece").reset_index()
KN["lookahead_ece_beta"] = dict(window=float(lk.window.mean()), leak_h0=float(lk.leak_h0.mean()), leak_peek=float(lk.leak_peek.mean()), static=float(lk.static.mean()))
lkb = sh[(sh.cal == "beta")].groupby("variant")[["ece", "brier", "logloss", "cwm"]].mean(); md(lkb, "online_lookahead_beta")

# ---------------- abstention
A = rd("results/hold_*_abstain.csv")
A["rule_base"] = A.rule.str.split("@").str[0]; A["budget"] = A.rule.str.extract(r"@([\d.]+)")[0].astype(float)
a1 = A[A.budget.isna()]
md(a1.groupby(["base", "phase", "rule"])[["abstain_on_trades", "good_retained", "bad_removed", "util_total_before", "util_total_after", "util_total_random", "conf_wrong_trade_mass_before", "conf_wrong_trade_mass_after", "turnover_after"]].mean(), "abstention_val_tau")
b1 = A[A.budget.notna()]
tb = b1.groupby(["base", "phase", "budget", "rule_base"])[["abstain_on_trades", "good_retained", "bad_removed", "util_total_before", "util_total_after", "util_total_random", "conf_wrong_trade_mass_before", "conf_wrong_trade_mass_after"]].mean()
md(tb, "abstention_budgets")
sc = b1[(b1.phase == "post")].groupby(["base", "scenario", "budget", "rule_base"])[["abstain_on_trades", "good_retained", "bad_removed", "util_total_after", "util_total_before", "util_total_random"]].mean()
md(sc, "abstention_budget_by_scenario")

# ---------------- conformal
R = rd("results/hold_*_conf_reg.csv"); Kc = rd("results/hold_*_conf_clf.csv")
p = R[R.phase == "post"]
md(p.groupby(["scenario", "method"]).coverage.mean().unstack("method"), "conf_reg_post_coverage")
md(p.groupby(["scenario", "method"]).worst_win_cov.mean().unstack("method"), "conf_reg_post_worstwin")
md(p.groupby(["scenario", "method"]).width.median().unstack("method"), "conf_reg_post_width")
md(p.groupby(["method"])[["coverage", "worst_win_cov", "cov_gap_abs", "width", "inf_rate"]].mean(), "conf_reg_post_overall_shift")
md(p[~p.scenario.isin(["none", "iid_control"])].groupby(["method"])[["coverage", "worst_win_cov", "cov_gap_abs", "width", "inf_rate"]].mean(), "conf_reg_post_shift_only")
pre = R[R.phase == "pre"]
md(pre[pre.scenario.isin(["iid_control", "none"])].groupby(["scenario", "method"])[["coverage", "cov_lowvol", "cov_highvol", "width"]].mean(), "conf_reg_conditional_vol")
# seed-level ci for split coverage under iid_control and none
KN["split_cov_iid_control"] = ci(pre[(pre.scenario == "iid_control") & (pre.method == "split")].coverage)
KN["split_cov_none_pre"] = ci(pre[(pre.scenario == "none") & (pre.method == "split")].coverage)
KN["gaussian_cov_none_pre"] = ci(pre[(pre.scenario == "none") & (pre.method == "gaussian")].coverage)
for base in ["lr", "gbm"]:
    k = Kc[(Kc.base == base) & (Kc.phase == "post")]
    md(k.groupby(["scenario", "method"])[["coverage", "set_size", "abstain", "utility"]].mean().unstack("method")["coverage"], f"conf_clf_post_coverage_{base}")
    md(k.groupby(["method"])[["coverage", "set_size", "singleton_rate", "abstain", "acc_singleton", "utility", "acc_all"]].mean(), f"conf_clf_post_overall_{base}")
    md(k[~k.scenario.isin(["none", "iid_control"])].groupby(["method"])[["coverage", "set_size", "abstain", "acc_singleton", "utility"]].mean(), f"conf_clf_post_shift_only_{base}")

# ---------------- shift detection + diagnosis
D = rd("results/diag_detection_*.csv")
det = D.groupby(["scenario", "detector"]).agg(detect_rate=("detected", "mean"), median_delay=("delay", "median"), far_pre=("far_pre", "mean"), post_alarm_rate=("post_alarm_rate", "mean"))
md(det.unstack("detector")["detect_rate"], "detect_rate"); md(det.unstack("detector")["median_delay"], "detect_delay"); md(det.unstack("detector")["post_alarm_rate"], "detect_post_alarm_rate")
md(D[D.scenario == "none"].groupby("detector")[["far_pre", "post_alarm_rate"]].mean(), "detect_false_alarm")
DR = pd.concat([pd.read_csv(f) for f in sorted(glob.glob("results/diag_diagrows_hold_*.csv.gz"))])
import sys; sys.path.insert(0, "py"); import shift as SH
cfg_all = json.load(open("frozen_config.json"))["diagnosis"]
cfg = dict(q_ood=cfg_all["q_ood_mahalanobis_percentile_of_cal"], q_mi=cfg_all["q_mi_ensemble_MI_percentile_of_cal"], tau_ns=cfg_all["tau_no_signal_conf"])
d4 = DR[DR.scenario.isin(SH.CAUSAL_SCEN)]
variants = {"full_cascade": cfg, "no_gap_flags": {**cfg, "use_gap_flags": False}, "no_ood": {**cfg, "use_ood": False}, "no_mi": {**cfg, "use_mi": False},
            "only_conf(NO_SIGNAL vs rest)": {**cfg, "use_gap_flags": False, "use_ood": False, "use_mi": False}}
rows = []
for vn, c in variants.items():
    pr = SH.classify(d4, c)
    pcs, rcs, fcs, ns = precision_recall_fscore_support(d4.truth.values, pr, labels=SH.CAUSE4, zero_division=0)
    for lab, a, b, cc in zip(SH.CAUSE4, pcs, rcs, fcs): rows.append(dict(variant=vn, cause=lab, precision=a, recall=b, f1=cc))
    rows.append(dict(variant=vn, cause="MACRO", precision=pcs.mean(), recall=rcs.mean(), f1=fcs.mean()))
    if vn == "full_cascade":
        cm = pd.DataFrame(confusion_matrix(d4.truth.values, pr, labels=SH.CAUSE4), index=[f"true_{c_}" for c_ in SH.CAUSE4], columns=[f"pred_{c_}" for c_ in SH.CAUSE4]); md(cm, "diag_confusion", 0)
        KN["diag_macro_f1_full"] = float(fcs.mean())
md(pd.DataFrame(rows).pivot_table(index="cause", columns="variant", values=["precision", "recall", "f1"]), "diag_prf")
# per-seed macro-F1 CI
pf = [f1_score(g.truth.values, SH.classify(g, cfg), labels=SH.CAUSE4, average="macro", zero_division=0) for _, g in d4.groupby("seed")]; KN["diag_macro_f1_seed_ci"] = ci(pf)
# blind spot: concept-type shifts
bs = DR[DR.scenario.isin(["vol_jump", "regime_transition"])].copy(); bs["pred"] = SH.classify(bs, cfg)
md(bs.groupby("scenario").apply(lambda g: pd.Series(dict(error_rate=g.wrong.mean(), mean_conf=g.conf.mean(), flagged_non_normal=(g.pred.isin(["DATA_GAP", "MODEL_UNCERTAINTY", "OUT_OF_DISTRIBUTION"])).mean(), flagged_NO_SIGNAL=(g.pred == "NO_SIGNAL").mean()))), "diag_concept_blindspot")
base_none = DR[(DR.scenario == "none")].copy(); base_none["pred"] = SH.classify(base_none, cfg)
KN["diag_false_flag_rate_in_dist"] = float(base_none.pred.isin(["DATA_GAP", "MODEL_UNCERTAINTY", "OUT_OF_DISTRIBUTION"]).mean())
# wrong-rate by predicted cause on all shift pool
allp = DR.copy(); allp["pred"] = SH.classify(allp, cfg)
md(allp.groupby("pred").agg(n=("wrong", "size"), error_rate=("wrong", "mean"), mean_conf=("conf", "mean")), "diag_error_by_predicted_cause")

# ---------------- public data
E_ = pd.read_csv("results/public_elec_metrics.csv"); EB = pd.read_csv("results/public_elec_blocks.csv"); EC = pd.read_csv("results/public_elec_conformal.csv")
md(E_.set_index(["base", "cal", "variant"])[["acc", "brier", "logloss", "ece", "fcr", "cwm", "chosen_W", "chosen_HL"]], "public_elec_overall")
md(EB[(EB.cal == "temperature")].groupby(["base", "variant", "block"]).ece.mean().unstack("block"), "public_elec_blocks_ece_temp")
md(EC.groupby(["base", "method", "block"]).coverage.mean().unstack("block"), "public_elec_conformal_cov_blocks")
md(EC.groupby(["base", "method"])[["coverage", "set_size", "singleton_rate"]].mean(), "public_elec_conformal_overall")
I_ = pd.read_csv("results/public_iid_metrics.csv"); md(I_.groupby(["task", "base", "cal"])[["acc", "brier", "logloss", "ece", "fcr", "cwm"]].mean(), "public_iid_calibration")
IC = pd.read_csv("results/public_iid_conformal.csv"); md(IC.groupby(["task", "base"])[["coverage", "set_size"]].agg(["mean", "std"]), "public_iid_conformal")
IK = pd.read_csv("results/public_iid_riskcov.csv"); md(IK.groupby(["task", "base", "cal"])[["aurc", "risk_full", "risk_at_50"]].mean(), "public_iid_riskcov")
CA = pd.read_csv("results/public_california.csv"); md(CA.groupby(["split", "method"])[["coverage", "width"]].agg(["mean", "std"]), "public_california")
json.dump(KN, open("results/key_numbers.json", "w"), indent=1, default=str)
