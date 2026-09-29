"""Experiment runner.  Usage: python3 runner.py <phase>   phase in tune|validate|robust|failure|heldout"""
import sys, json, os, time, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd
from multiprocessing import Pool
from env import make_world, run, offline_lp_bound, BASE
from policies import default_configs, GRIDS
import scenarios as SCN

RES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results")
reg = default_configs()
ORACLES = ["ORACLE_SCORE_NOT_IMPLEMENTABLE", "ORACLE_DENSITY_NOT_IMPLEMENTABLE"]
FIXED = ["FIFO", "ROUND_ROBIN", "RANDOM_SEEDED", "EQUAL_QUOTA", "FIFO_NETPOS", "RANK_SCORE_RAW", "RANK_NET",
         "RANK_NET_UNKCOST_ZERO", "RANK_NET_MISSING_REJECT", "SECRETARY_1_OVER_E"]
KEEP = ["n_opps", "n_admit", "n_evict", "evals_per_opp", "real_net", "lat_net", "real_per_slot_hour", "lat_per_slot_hour",
        "lat_per_used_hour", "utilisation", "idle", "mean_hold", "admit_per_slot_hour", "v0_admitted_mean", "v0_rejected_mean",
        "v0_all_mean", "v0_sd", "dens0_sd", "dens0_rms", "n_hq", "hq_missed_frac", "hq_missed_capacity", "hq_declined_with_free_slot",
        "opp_cost_missed_value_per_slot_hour", "hhi_cluster", "eff_clusters", "max_cluster_share", "pnl_day_sd", "pnl_day_mean",
        "ret_to_risk", "max_drawdown", "starved_inst", "starved_pos_inst", "min_admit_ratio", "inst_admit_share_max",
        "spam_admit_share", "spam_opp_share", "long_slot_hour_share", "long_admit_share", "short_admit_share",
        "full_toggle_rate", "occ_abs_change", "diag_thr_cv", "diag_thr_flip", "lat_q0", "lat_q1", "lat_q2", "lat_q3"]


def cell(job):
    P, seed, caps, specs, lp_caps, meta = job
    W = make_world(P, seed)
    rows = []
    for cap in caps:
        lp = offline_lp_bound(W, cap) if cap in lp_caps else np.nan
        for label, name, params in specs:
            m = run(W, reg[name](params), cap, seed=seed)
            r = dict(meta, seed=seed, cap=cap, policy=label, base=name, params=json.dumps(params, sort_keys=True), lp_bound=lp)
            for k in KEEP:
                r[k] = m.get(k, np.nan)
            rows.append(r)
    return rows


def pool_run(jobs, procs=4):
    t = time.time(); out = []
    with Pool(procs) as p:
        for i, r in enumerate(p.imap_unordered(cell, jobs, chunksize=1)):
            out.extend(r)
            if (i + 1) % max(1, len(jobs) // 10) == 0:
                print(f"  {i+1}/{len(jobs)} jobs  {time.time()-t:.0f}s", flush=True)
    return pd.DataFrame(out)


def specs_from(tuned):
    s = [(n, n, {}) for n in FIXED]
    for n in GRIDS:
        s.append((n, n, tuned[n]))
    return s


def jobs_for(split, nseed, caps, specs, lp_caps=(), fams=None, nvar=3):
    jobs = []
    for fam in (fams or list(SCN.families(split))):
        for P in SCN.variants(fam, split, nvar):
            meta = dict(family=fam, variant=P["_variant"], split=split)
            Pc = {k: v for k, v in P.items() if not k.startswith("_")}
            for s in range(nseed):
                jobs.append((Pc, SCN.SPLIT_SEED0[split] + s, caps, specs, lp_caps, meta))
    return jobs


def tune():
    specs = [(n, n, {}) for n in FIXED if n in ("FIFO",)]
    for n, grid in GRIDS.items():
        for i, p in enumerate(grid):
            specs.append((f"{n}#{i}", n, p))
    jobs = jobs_for("TUNING", 3, (4, 6), specs)
    print("tuning jobs", len(jobs), "specs", len(specs))
    df = pool_run(jobs)
    df.to_csv(f"{RES}/tuning_raw.csv.gz", index=False)
    key = ["family", "variant", "seed", "cap"]
    fifo = df[df.policy == "FIFO"].set_index(key)
    df = df[df.policy != "FIFO"].join(fifo[["lat_per_slot_hour"]].rename(columns={"lat_per_slot_hour": "fifo"}), on=key)
    df["z"] = (df.lat_per_slot_hour - df.fifo) / df.dens0_rms
    # objective = mean over cells of z (equal weight per cell; cells are family x variant x seed x cap)
    obj = df.groupby(["base", "policy", "params"]).z.mean().reset_index()
    tuned, table = {}, []
    for n in GRIDS:
        o = obj[obj.base == n].sort_values("z", ascending=False)
        tuned[n] = json.loads(o.iloc[0].params)
        for _, r in o.iterrows():
            table.append(dict(policy=n, params=r.params, tuning_objective_z=r.z, chosen=(r.params == o.iloc[0].params)))
    json.dump(tuned, open(f"{RES}/tuned_params.json", "w"), indent=1)
    pd.DataFrame(table).to_csv(f"{RES}/tuning_table.csv", index=False)
    print(json.dumps(tuned, indent=1))


def validate():
    tuned = json.load(open(f"{RES}/tuned_params.json"))
    specs = specs_from(tuned) + [(o, o, {}) for o in ORACLES]
    jobs = jobs_for("VALIDATION", 4, (3, 4, 6, 10), specs, lp_caps=(4,))
    print("validation jobs", len(jobs))
    df = pool_run(jobs)
    df.to_csv(f"{RES}/validation_raw.csv.gz", index=False)


def heldout():
    pre = json.load(open(f"{RES}/../prereg/PREREGISTRATION.json"))
    h = hashlib.sha256(open(f"{RES}/tuned_params.json", "rb").read()).hexdigest()
    assert pre["frozen_tuned_params_sha256"] == h, "tuned params changed after preregistration"
    tuned = json.load(open(f"{RES}/tuned_params.json"))
    specs = specs_from(tuned) + [(o, o, {}) for o in ORACLES]
    jobs = jobs_for("HELDOUT", 10, (3, 4, 6, 10), specs, lp_caps=(3, 4, 6, 10))
    print("heldout jobs", len(jobs))
    df = pool_run(jobs)
    df.to_csv(f"{RES}/heldout_raw.csv.gz", index=False)


REF = dict(load=3.0, NCL=2, cl_bonus=[6.0, -2.0], sig_c=8.0)


def robust():
    """One-at-a-time robustness axes on a reference scenario, on separate seeds (3000+); never the held-out seeds."""
    tuned = json.load(open(f"{RES}/tuned_params.json"))
    specs = specs_from(tuned)
    axes = {
        "arrival": [dict(arrival="poisson"), dict(arrival="mmpp"), dict(arrival="periodic"), dict(burst=(60, 4, 8.0))],
        "score_noise_x": [dict(score_sd=5.0), dict(score_sd=10.0), dict(score_sd=20.0), dict(score_sd=40.0)],
        "score_calib_slope": [dict(score_b=1.0), dict(score_b=0.5), dict(score_b=0.2), dict(score_b=-0.3)],
        "duration_dist": [dict(dur_dist="lognorm", dur_sd=0.3), dict(dur_dist="lognorm", dur_sd=0.55), dict(dur_dist="lognorm", dur_sd=1.0), dict(dur_dist="pareto")],
        "corr_scale": [dict(corr_scale=0.3), dict(corr_scale=1.0), dict(corr_scale=2.0), dict(corr_scale=3.5)],
        "regime": [dict(regime=None), dict(regime=dict(t_frac=0.25, perm_mu=True, b_after=[1, -0.5], sig_c_mult=2.0)),
                   dict(regime=dict(t_frac=0.5, perm_mu=True, b_after=[1, -0.5], sig_c_mult=2.0)),
                   dict(regime=dict(t_frac=0.75, perm_mu=True, b_after=[1, -0.5], sig_c_mult=2.0))],
        "cost_x": [dict(fee_lo=2, fee_hi=4, slip_lo=.5, slip_hi=1.5), dict(), dict(fee_lo=8, fee_hi=16, slip_lo=2, slip_hi=6), dict(fee_lo=16, fee_hi=32, slip_lo=4, slip_hi=12)],
        "cost_unknown": [dict(p_cost_unk=0.0), dict(p_cost_unk=0.1), dict(p_cost_unk=0.4), dict(p_cost_unk=0.7)],
        "load": [dict(load=0.5), dict(load=1.5), dict(load=3.0), dict(load=6.0)],
    }
    jobs = []
    for ax, lst in axes.items():
        for j, over in enumerate(lst):
            P = dict(BASE); P.update(REF); P.update(over)
            for s in range(5):
                jobs.append((P, 3000 + s, (3, 4, 6, 10), specs, (), dict(family="REF", axis=ax, level=j, split="ROBUST", variant=0)))
    print("robust jobs", len(jobs))
    df = pool_run(jobs)
    df.to_csv(f"{RES}/robustness_raw.csv.gz", index=False)


def failure():
    tuned = json.load(open(f"{RES}/tuned_params.json"))
    specs = specs_from(tuned)
    tests = {
        "candidate_spam_rate": [dict(spam=dict(rate=r, mu=-2.0, bias=12.0, inst=0)) for r in (0.0, 0.5, 1.2, 3.0)],
        "score_gaming_bias": [dict(spam=dict(rate=1.0, mu=-2.0, bias=b, inst=0)) for b in (0.0, 12.0, 30.0, 60.0)],
        "corr_collapse": [dict(regime=dict(t_frac=0.5, perm_mu=False, b_after=None, sig_c_mult=m)) for m in (1.0, 2.0, 4.0, 8.0)],
        "regime_lag": [dict(regime=dict(t_frac=0.5, perm_mu=True, b_after=[1, -1.0], sig_c_mult=1.0, mu_shift=0.0), mu_sd=10.0)],
        "noisy_score": [dict(score_sd=s, score_het=0.8) for s in (10.0, 30.0, 60.0)],
        "long_slot_capture": [dict(dur_dist="pareto", dur_sd=1.2, edge_dur_k=k) for k in (0.0, 8.0, 16.0)],
    }
    jobs = []
    for ax, lst in tests.items():
        for j, over in enumerate(lst):
            P = dict(BASE); P.update(REF); P.update(over)
            for s in range(6):
                jobs.append((P, 4000 + s, (4, 6), specs, (), dict(family="FAIL", axis=ax, level=j, split="FAILURE", variant=0)))
    print("failure jobs", len(jobs))
    df = pool_run(jobs)
    df.to_csv(f"{RES}/failure_raw.csv.gz", index=False)


if __name__ == "__main__":
    globals()[sys.argv[1]]()
