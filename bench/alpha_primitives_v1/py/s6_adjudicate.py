"""Rule-based adjudication (rules fixed in code, reported in 10_ADJUDICATION.md)."""
from common import *
s1 = json.load(open(os.path.join(RES, "s1_main.json"))); s2 = json.load(open(os.path.join(RES, "s2_ortho.json")))
s3 = json.load(open(os.path.join(RES, "s3_regime.json"))); s4 = json.load(open(os.path.join(RES, "s4_cost.json"))); s5 = json.load(open(os.path.join(RES, "s5_falsify.json")))["prims"]
NAMES = list(X.PRIMS); adj = {}
def nz(x): return x is not None and x == x
# Holm adjustment over raw one-sided holdout-net bootstrap p-values (15 tests)
ps = {k: s1["primitives"][k]["holdout"]["boot"]["p_one_sided"] if s1["primitives"][k]["holdout"].get("boot") else 1.0 for k in NAMES}
order = sorted(NAMES, key=lambda k: ps[k]); holm = {}; run = 0.0
for i, k in enumerate(order): run = max(run, min(1.0, ps[k] * (len(NAMES) - i))); holm[k] = run
for k in NAMES:
    a = s1["primitives"][k]; f, d, h = a["full"], a["dev"], a["holdout"]; c = s4[k]; z = s5[k]
    fl = {}
    fl["F1_gross_info"] = bool(nz(f["gross_sharpe"]) and f["gross_sharpe"] > 0 and a["boot_gross_full"]["p_one_sided"] <= 0.10)
    fl["F2_gross_pos_dev_and_holdout"] = bool(nz(d["gross_sharpe"]) and nz(h["gross_sharpe"]) and d["gross_sharpe"] > 0 and h["gross_sharpe"] > 0)
    fl["F3_net_pos_full_dev_holdout"] = bool(all(nz(x["net_sharpe"]) and x["net_sharpe"] > 0 for x in (f, d, h)))
    fl["F4_net_pos_at_1.5x_cost"] = bool(nz(c["mult"]["1.5"]["full"]["net_sharpe"]) and c["mult"]["1.5"]["full"]["net_sharpe"] > 0)
    fl["F5_perturb_ge70pct_net_pos"] = bool(z["perturbation"]["frac_net_pos"] is not None and z["perturbation"]["frac_net_pos"] >= 0.7)
    fl["F6_latency1_net_pos"] = bool(nz(z["latency"]["1"]["net_sharpe"]) and z["latency"]["1"]["net_sharpe"] > 0)
    fl["F7_placebo_p_gross_le_0.10"] = bool(z["placebo"]["p_gross"] <= 0.10)
    fl["F8_majors_and_minors_gross_pos"] = bool(z["assets"]["majors"] and z["assets"]["minors"] and z["assets"]["majors"]["gross_sharpe"] > 0 and z["assets"]["minors"]["gross_sharpe"] > 0) if k != "P15_RV_IV_VRP" else None
    v = z.get("venues")
    if v:
        vals = []
        for vn, x in v.items():
            if "venue" in x: vals.append(x["venue"]["gross_sharpe"] > 0)
            elif "okx_exec" in x: vals.append(x["okx_exec"]["gross_sharpe"] > 0)
            elif "hl_signal_okx_prices" in x: vals.append(x["hl_signal_okx_prices"]["gross_sharpe"] > 0)
        fl["F9_venue_transfer_gross_pos"] = bool(vals and all(vals))
    else: fl["F9_venue_transfer_gross_pos"] = None
    ms = z["missing"]["obs_0.2"]["stale"]["net_sharpe"]; fl["F10_missing20_stale_net_pos"] = bool(nz(ms) and ms > 0)
    fl["holdout_boot_p_raw"] = ps[k]; fl["holdout_boot_p_holm15"] = holm[k]
    core = ["F3_net_pos_full_dev_holdout", "F4_net_pos_at_1.5x_cost", "F5_perturb_ge70pct_net_pos", "F6_latency1_net_pos", "F7_placebo_p_gross_le_0.10"]
    net_ok = all(fl[x] for x in core)
    if net_ok and fl["holdout_boot_p_raw"] <= 0.10: tier = "NET_POSITIVE_EXTERNAL_CANDIDATE"
    elif net_ok: tier = "NET_POSITIVE_UNPROVEN (passes core rules, holdout p>0.10)"
    elif fl["F1_gross_info"] or (fl["F2_gross_pos_dev_and_holdout"] and z["placebo"]["p_gross"] <= 0.10): tier = "GROSS_INFORMATION_ONLY (not net-monetisable at generic taker costs)"
    elif f["gross_sharpe"] is not None and nz(f["gross_sharpe"]) and f["gross_sharpe"] > 0: tier = "WEAK_GROSS_NOT_SIGNIFICANT"
    else: tier = "REJECTED"
    fl["tier"] = tier
    # redundancy
    r = s2["redundancy"].get(k); fl["max_abs_corr"] = r["max_abs_corr"] if r else None; fl["R2_vs_others"] = r["R2_vs_others"] if r else None
    fl["nonredundant"] = bool(r is None or (r["max_abs_corr"] < 0.5 and r["R2_vs_others"] < 0.35))
    rp = s3["prims"][k]; sig = {n: rp[n]["perm_p_range"] for n in rp}
    fl["regime_perm_p"] = sig; fl["regime_dependent_raw"] = bool(any(p <= 0.05 for p in sig.values()))
    fl["regime_dependent"] = bool(any(rp[n]["perm_p_range"] <= 0.05 and rp[n]["sign_consistent_dev_holdout"] == rp[n]["n_states_cmp"] and rp[n]["n_states_cmp"] >= 2 for n in rp))
    adj[k] = fl
jd(adj, "s6_adjudication.json")
for k, fl in adj.items():
    print(f"{k:22s} {fl['tier'][:34]:34s} F1{int(fl['F1_gross_info'])} F2{int(fl['F2_gross_pos_dev_and_holdout'])} F3{int(fl['F3_net_pos_full_dev_holdout'])} F4{int(fl['F4_net_pos_at_1.5x_cost'])} F5{int(fl['F5_perturb_ge70pct_net_pos'])} F6{int(fl['F6_latency1_net_pos'])} F7{int(fl['F7_placebo_p_gross_le_0.10'])} F9{fl['F9_venue_transfer_gross_pos']} nonred {fl['nonredundant']} regdep {fl['regime_dependent']} hoP {fl['holdout_boot_p_raw']:.2f}")
