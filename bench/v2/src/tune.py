"""Hyper-parameter selection for policies B, C, C2, D on TRAIN then VALIDATION scenarios ONLY.

Policy A is FIXED (operator contract) and is never tuned.  This file imports only the dev generators.
Usage: python tune.py <B|C|C2|D> [--workers 4]
Writes results/tuning/<policy>_{train,validation}.json and configs/selected_<policy>.json
(C2 requires configs/selected_C.json's train ranking, produced by the C run.)
"""
import os, json, itertools, time, argparse
from multiprocessing import Pool
import numpy as np
from scenarios_dev import make_dev_scenario, DEV_SPECS
from runner import run_one, make_policy

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROT = json.load(open(os.path.join(ROOT, "configs", "protocol.json")))
SEEDS = {k: list(range(*PROT["seeds"][k])) for k in ("train", "validation")}
KEEP = ["info_ratio", "starvation_rate", "stale_rate", "silent_excess", "lowinfo_excess", "coverage_W",
        "adapt_delay", "max_starvation_duration", "turnover", "policy_seconds"]


def J(m):
    return (m["info_ratio"] - 1.0 * m["starvation_rate"] - 0.5 * m["stale_rate"]
            - 0.5 * max(m["silent_excess"], 0.0) - 0.25 * max(m["lowinfo_excess"], 0.0))


def _job(a):
    label, spec, split, scen, seed = a
    try:
        r = run_one(make_dev_scenario(split, scen, seed), make_policy(spec, seed))
        out = {k: float(r[k]) for k in KEEP}
        out["J"] = J(r)
        return label, scen, seed, out, None
    except Exception:
        import traceback
        return label, scen, seed, None, traceback.format_exc()


def grid_B():
    s = PROT["search_spaces"]["B"]
    return {f"B|g{g}|S{S}|M{M}": dict(kind="B", gamma=g, S=S, M=M)
            for g, S, M in itertools.product(s["gamma"], s["S"], s["M"])}


def grid_C():
    s, out = PROT["search_spaces"]["C"], {}
    for f, e in itertools.product(s["eps_ew"]["fading"], s["eps_ew"]["eps"]):
        out[f"C|eps_ew|f{f}|e{e}"] = dict(kind="C", algo="eps_ew", fading=f, eps=e)
    for f, d in itertools.product(s["ucb_ew"]["fading"], s["ucb_ew"]["delta"]):
        out[f"C|ucb_ew|f{f}|d{d}"] = dict(kind="C", algo="ucb_ew", fading=f, delta=d)
    for d in s["ucb_mean"]["delta"]:
        out[f"C|ucb_mean|d{d}"] = dict(kind="C", algo="ucb_mean", delta=d)
    return out


def grid_C2(top3):
    s, out = PROT["search_spaces"]["C2_guard_on_top3_C"], {}
    for lab, spec in top3.items():
        for S, M in itertools.product(s["S"], s["M"]):
            sp = dict(spec, kind="C2", guard=[S, M])
            out[f"C2|{lab[2:]}|S{S}|M{M}"] = sp
    return out


def grid_D():
    s, out = PROT["search_spaces"]["D"], {}
    for g, lr, ug in itertools.product(s["squarecb"]["gamma_scale"], s["squarecb"]["lr"], s["squarecb"]["use_group"]):
        out[f"D|sq|g{g}|lr{lr}|grp{int(ug)}"] = dict(kind="D", algo="squarecb", expl=g, lr=lr, use_group=ug)
    for e, lr, ug in itertools.product(s["eps"]["eps"], s["eps"]["lr"], s["eps"]["use_group"]):
        out[f"D|eps|e{e}|lr{lr}|grp{int(ug)}"] = dict(kind="D", algo="eps", expl=e, lr=lr, use_group=ug)
    return out


def evaluate(cfgs, split, pool):
    jobs = [(lab, spec, split, sc, sd) for lab, spec in cfgs.items() for sc in DEV_SPECS[split] for sd in SEEDS[split]]
    res, errs = {}, []
    for lab, scen, seed, out, err in pool.imap_unordered(_job, jobs, chunksize=2):
        if err:
            errs.append(dict(label=lab, scenario=scen, seed=seed, error=err)); continue
        res.setdefault(lab, []).append(dict(scenario=scen, seed=seed, **out))
    full = len(DEV_SPECS[split]) * len(SEEDS[split])
    summ = {lab: float(np.mean([r["J"] for r in rs])) for lab, rs in res.items() if len(rs) == full}
    return res, summ, errs


def select(summ_train, summ_val_fn, cfgs, pool):
    top3 = sorted(summ_train, key=lambda k: -summ_train[k])[:3]
    val_res, val_summ, val_err = summ_val_fn({k: cfgs[k] for k in top3})
    best = sorted(top3, key=lambda k: -val_summ.get(k, -9))
    # ties (|dJ|<0.005) keep the train-ranking order among the tied leaders
    lead = [k for k in best if val_summ.get(k, -9) >= val_summ[best[0]] - 0.005]
    chosen = sorted(lead, key=lambda k: top3.index(k))[0]
    return top3, val_res, val_summ, val_err, chosen


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("policy"); ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args()
    outd = os.path.join(ROOT, "results", "tuning"); os.makedirs(outd, exist_ok=True)
    t0 = time.time()
    with Pool(a.workers) as pool:
        if a.policy == "C2":
            base = json.load(open(os.path.join(ROOT, "configs", "selected_C.json")))
            top3 = {k: base["all_specs"][k] for k in base["top3_train"]}
            cfgs = grid_C2(top3)
        else:
            cfgs = {"B": grid_B, "C": grid_C, "D": grid_D}[a.policy]()
        tr_res, tr_summ, tr_err = evaluate(cfgs, "train", pool)
        top3, va_res, va_summ, va_err, chosen = select(
            tr_summ, lambda c: evaluate(c, "validation", pool), cfgs, pool)
        # reference baselines on the same objective (context only)
        ref_cfgs = {"REF|A": dict(kind="A"), "REF|R": dict(kind="R")}
        rt, rts, _ = evaluate(ref_cfgs, "train", pool)
        rv, rvs, _ = evaluate(ref_cfgs, "validation", pool)
    json.dump(dict(train=tr_res, validation=va_res, errors=tr_err + va_err, refs=dict(train=rt, validation=rv)),
              open(os.path.join(outd, f"{a.policy}_raw.json"), "w"))
    sel = dict(policy=a.policy, chosen=chosen, spec=cfgs[chosen], train_J=tr_summ[chosen], validation_J=va_summ[chosen],
               top3_train=top3, top3_train_J={k: tr_summ[k] for k in top3}, top3_validation_J=va_summ,
               train_J_all=tr_summ, all_specs=cfgs, n_configs=len(cfgs), n_errors=len(tr_err) + len(va_err),
               ref_train_J=rts, ref_validation_J=rvs, wall_seconds=time.time() - t0)
    json.dump(sel, open(os.path.join(ROOT, "configs", f"selected_{a.policy}.json"), "w"), indent=1)
    print(a.policy, "chosen", chosen, "trainJ %.4f valJ %.4f" % (tr_summ[chosen], va_summ[chosen]),
          "errors", sel["n_errors"], "wall %.0fs" % sel["wall_seconds"])
