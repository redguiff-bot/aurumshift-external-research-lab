"""ONE-SHOT held-out evaluation of the frozen formulas. Refuses to run twice (lock file).
--dryrun: smoke-test the code path on validation data only (no held-out access), writes nothing."""
import sys, os, json, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import numpy as np
from fd import panel, features, pipeline as P, baselines as B, data, invariance
from fd.metrics import boot_ic, spearman

RES = os.path.join(os.path.dirname(__file__), "..", "results")
N = features.NAMES
DRY = "--dryrun" in sys.argv
LOCK = os.path.join(RES, "heldout_lock.json")


def main():
    fro = json.load(open(os.path.join(RES, "FROZEN.json")))
    dg = fro.pop("digest")
    assert dg == P.digest(fro), "FROZEN.json modified after freezing"
    if not DRY:
        assert not os.path.exists(LOCK), "held-out already evaluated: refusing to re-run (no selection on held-out)"
    disc = json.load(open(os.path.join(RES, "discovery_train_val.json")))
    unseen = set(data.UNSEEN_MARKETS)
    all_recs, per_target = [], {}
    for target in ("y_ret", "y_vol"):
        tr, _ = panel.panels(target, "train"); va, _ = panel.panels(target, "val")
        if DRY:
            ho, hoi = va, None; un = set(list(va)[:2])
        else:
            ho, hoi = panel.panels(target, "heldout"); un = unseen
        frozen = fro[target]; mains = fro["mains"][target]
        # full candidate info (for cand_value need sign/mu/sd/expr) - present in FROZEN.json
        bl = B.fit_baselines(tr, va, N, seed=0)
        disc_m = B.fit_discovered(tr, va, N, mains, frozen, P.cand_value)
        base_pred = {m: B.predict(bl["raw_ridge"], ho[m][0]) for m in ho}
        recs = P.evaluate_heldout(frozen, ho, un, N, base_pred, B=2000 if not DRY else 200)
        for r in recs:
            r["target"] = target
        # placebo: same circular shift of y in every market; rate at which frozen candidates would be 'stable'
        rng = np.random.default_rng(99); pl = []
        nH = len(next(iter(ho.values()))[1])
        for _ in range(20 if not DRY else 3):
            s = int(rng.integers(500, nH - 500))
            hop = {m: (ho[m][0], np.roll(ho[m][1], s)) for m in ho}
            rr = P.evaluate_heldout(frozen, hop, un, N, base_pred, B=300, seed=3)
            pl.append([x["p_raw"] for x in rr])
        pl = np.array(pl) if pl else np.zeros((0, 0))
        # model comparison (pooled mean IC, paired block bootstrap)
        y = {m: ho[m][1] for m in ho}
        preds = {k: {m: B.predict(v, ho[m][0]) for m in ho} for k, v in bl.items()}
        if disc_m is not None:
            preds["discovered"] = {m: disc_m["model"].predict(disc_m["feats"](ho[m][0])) for m in ho}
        params = {k: v["params"] for k, v in bl.items()}
        if disc_m is not None:
            params["discovered"] = disc_m["params"]
        draws, ics, r2 = {}, {}, {}
        for k, pm in preds.items():
            ms, ic, bt = boot_ic(pm, y, B=2000 if not DRY else 200, seed=11)
            draws[k] = bt.mean(1); ics[k] = dict(zip(ms, map(float, ic)))
            base = np.mean(np.concatenate([np.concatenate([tr[m][1], va[m][1]]) for m in tr]))
            r2[k] = float(np.mean([1 - ((y[m] - pm[m]) ** 2).sum() / ((y[m] - base) ** 2).sum() for m in ms]))
        cmp = {}
        for k in draws:
            cmp[k] = dict(ic_mean=float(np.mean(list(ics[k].values()))), ic_by_market=ics[k], r2_oos_mean=r2[k], params=params[k],
                          ic_ci90=[float(np.quantile(draws[k], .05)), float(np.quantile(draws[k], .95))])
        if "discovered" in draws:
            for k in draws:
                if k != "discovered":
                    d = draws["discovered"] - draws[k]
                    cmp[k]["disc_minus_this"] = dict(mean=float(d.mean()), q10=float(np.quantile(d, .10)), q90=float(np.quantile(d, .90)))
        # invariance on held-out environments
        inv = {}
        for c in frozen:
            f = {m: P.cand_value(c, ho[m][0], N) for m in ho}
            inv[c["id"]] = invariance.cochran_q(f, {m: ho[m][1] for m in ho})
        per_target[target] = dict(comparison=cmp, params=params, baseline_features={k: v.get("features") for k, v in bl.items()},
                                  placebo_p_raw=pl.tolist(), invariance_heldout=inv, n_rows={m: len(ho[m][1]) for m in ho},
                                  span=None if hoi is None else [str(hoi[0]), str(hoi[-1])], candidates=[r["id"] for r in recs])
        all_recs += recs
        print(target, {k: round(v["ic_mean"], 4) for k, v in cmp.items()}, flush=True)
    K = len(all_recs)
    all_recs = P.decide(all_recs, family_size=max(K, 1))
    # COMPLEXITY_JUSTIFIED
    cj = {}
    for target, d in per_target.items():
        cmp = d["comparison"]
        nonred = [r for r in all_recs if r["target"] == target and r["novel_vs_baseline"]]
        if "discovered" not in cmp:
            cj[target] = "NO"; continue
        bases = [k for k in cmp if k not in ("discovered", "gbm_full_ceiling")]
        yes = all(cmp[k]["disc_minus_this"]["q10"] > 0 for k in bases) and len(nonred) >= 1
        best = max(bases, key=lambda k: cmp[k]["ic_mean"])
        part = cmp[best]["disc_minus_this"]["q10"] > -0.005 and cmp["discovered"]["params"] <= 0.5 * cmp[best]["params"]
        cj[target] = "YES" if yes else "PARTIAL" if part else "NO"
    agg = "YES" if "YES" in cj.values() else "PARTIAL" if "PARTIAL" in cj.values() else "NO"
    res = dict(digest=dg, dryrun=DRY, family_size=K, records=all_recs, per_target=per_target, complexity_justified=dict(per_target=cj, aggregate=agg),
               forward_safety_tests="tests/test_forward_safety.py")
    if DRY:
        print("DRYRUN OK", cj, [(r["id"], round(r["ic_mean"], 3), r["stable"]) for r in all_recs]); return
    json.dump(res, open(os.path.join(RES, "heldout_results.json"), "w"), indent=1, default=float)
    json.dump(dict(digest=dg, time=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())), open(LOCK, "w"))
    print("DONE", cj, agg)


main()
