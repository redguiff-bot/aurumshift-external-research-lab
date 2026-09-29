"""Held-out analysis: per-scenario summaries, paired hierarchical bootstrap, effect sizes, dominance check.
Reads results/heldout/S*.json (immutable).  Writes results/heldout_analysis/*.md|json.  No p-values."""
import json, os, glob, itertools, sys
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROT = json.load(open(os.path.join(ROOT, "configs", "protocol.json")))
THR = PROT["practical_thresholds"]
NB = PROT["statistics"]["bootstrap_resamples"]
HIGHER = {"info_ratio", "coverage_W", "rare_discovery_rate", "hit_rate_post", "target_share_post", "info_ratio_first40"}
NEUTRAL = {"turnover", "gini_attention_rate", "top10pct_share"}
POLS = ["A", "B", "C", "D", "C2", "R"]
CONTENDERS = ["A", "B", "C", "D"]
ALL = ["S1_MASSIVE_COLD_START", "S2_ABRUPT_REGIME_CHANGE", "S3_SLOW_DRIFT", "S4_TEMPORARY_SILENCE", "S5_PROVIDER_DATA_GAP",
       "S6_STALE_BUT_VALID", "S7_GENUINELY_LOW_INFORMATION", "S8_RARE_HIGH_INFORMATION", "S9_LONG_DORMANCY_RETURN",
       "S10_DYNAMIC_POPULATION"]
CORE = {  # metric -> scenarios where it is a meaningful core metric
    "info_ratio": ALL, "starvation_rate": ALL, "stale_rate": ALL, "coverage_W": ALL, "max_starvation_duration": ALL,
    "silent_excess": [ALL[3], ALL[4], ALL[8]], "adapt_delay": [ALL[1], ALL[2], ALL[8]],
    "degraded_excess_post": [ALL[1], ALL[2]], "new_ttfa_median": [ALL[0], ALL[9]], "new_never_attempted": [ALL[0], ALL[9]],
    "lowinfo_excess": [ALL[6]], "rare_discovery_rate": [ALL[7]],
}
KEY = ["info_ratio", "coverage_W", "starvation_rate", "max_starvation_duration", "stale_rate", "silent_excess",
       "lowinfo_excess", "adapt_delay", "new_ttfa_median", "rare_discovery_rate", "gini_attention_rate", "turnover"]


def load(dirn, names=ALL):
    data = {}
    for s in names:
        p = os.path.join(dirn, f"{s}.json")
        if not os.path.exists(p):
            continue
        for r in json.load(open(p))["runs"]:
            if "error" in r:
                raise SystemExit(f"ERROR RUN present: {r['label']} {r['scenario']} {r['seed']}")
            data.setdefault((s, r["label"]), {})[r["seed"]] = r
    return data


def vec(data, s, pol, m):
    d = data[(s, pol)]
    return np.array([d[k][m] for k in sorted(d)], float)


def summ(x):
    x = x[~np.isnan(x)]
    if len(x) == 0:
        return None
    return dict(mean=float(x.mean()), median=float(np.median(x)), sd=float(x.std(ddof=1)) if len(x) > 1 else 0.0,
                q10=float(np.quantile(x, .1)), q90=float(np.quantile(x, .9)), min=float(x.min()), max=float(x.max()), n=int(len(x)))


def worst(x, m):
    x = x[~np.isnan(x)]
    if len(x) == 0: return np.nan
    return float(x.min()) if m in HIGHER else (float(x.max()) if m not in NEUTRAL else float(x.max()))


def pooled_boot(diffs_by_scen, rng):
    """diffs_by_scen: list of 1-D arrays (paired per-seed diffs).  Returns (point, lo, hi)."""
    pt = np.mean([d.mean() for d in diffs_by_scen])
    bs = np.mean([d[rng.integers(0, len(d), (NB, len(d)))].mean(1) for d in diffs_by_scen], axis=0)
    return float(pt), float(np.quantile(bs, .025)), float(np.quantile(bs, .975))


def cliffs(x, y):
    x, y = np.asarray(x), np.asarray(y)
    return float(((x > y).sum() - (x < y).sum()) / len(x))


def category(pt, lo, hi, m):
    dist = (lo > 0) or (hi < 0)
    meaningful = abs(pt) >= THR.get(m, np.inf)
    if dist and meaningful: return "DISTINGUISHABLE+MEANINGFUL"
    if dist: return "STATISTICALLY_DISTINGUISHABLE"
    if meaningful: return "PRACTICALLY_MEANINGFUL(CI includes 0)"
    return "INCONCLUSIVE"


def better(pt, m):
    """sign: +1 if X better than Y for diff pt = X - Y"""
    if m in NEUTRAL: return 0
    return (1 if pt > 0 else -1) if m in HIGHER else (1 if pt < 0 else -1)


def main(dirn, out):
    os.makedirs(out, exist_ok=True)
    data = load(dirn)
    scens = [s for s in ALL if (s, "A") in data]
    rng = np.random.default_rng(20260929)
    res = dict(summary={}, pooled={}, pairs={}, dominance={})
    md = []
    # ---- per-scenario summary --------------------------------------------------------------
    for s in scens:
        md.append(f"\n#### {s}  (n={len(data[(s,'A')])} seeds)\n")
        md.append("| metric | " + " | ".join(POLS) + " |\n|---|" + "---|" * len(POLS))
        for m in KEY:
            row = []
            ok = False
            for p in POLS:
                x = vec(data, s, p, m); z = summ(x)
                res["summary"].setdefault(s, {}).setdefault(p, {})[m] = z
                if z is None: row.append("n/a")
                else:
                    ok = True
                    row.append(f"{z['mean']:.3f} ± {z['sd']:.3f} (med {z['median']:.3f}; worst {worst(x, m):.3f})")
            if ok: md.append(f"| {m} | " + " | ".join(row) + " |")
    open(os.path.join(out, "per_scenario_tables.md"), "w").write("\n".join(md))
    # ---- pooled means with hierarchical bootstrap CI -------------------------------------------
    md = ["| metric (scenarios pooled) | " + " | ".join(POLS) + " |\n|---|" + "---|" * len(POLS)]
    for m in KEY:
        sc_ok = [s for s in scens if not np.isnan(vec(data, s, "A", m)).all()]
        if not sc_ok: continue
        row = []
        for p in POLS:
            per = [vec(data, s, p, m) for s in sc_ok]
            pt, lo, hi = pooled_boot([x for x in per], rng)
            res["pooled"].setdefault(m, {})[p] = dict(mean=pt, lo=lo, hi=hi, scenarios=len(sc_ok))
            row.append(f"{pt:.3f} [{lo:.3f},{hi:.3f}]")
        md.append(f"| {m} (n_scen={len(sc_ok)}) | " + " | ".join(row) + " |")
    open(os.path.join(out, "pooled_table.md"), "w").write("\n".join(md))
    # ---- pairwise paired comparisons --------------------------------------------------------------
    md = ["| metric | pair X vs Y | Δ=X−Y pooled [95% CI] | d_z | Cliff δ | category | better |\n|---|---|---|---|---|---|---|"]
    hm = ["metric", ]
    for m in [k for k in KEY if k not in NEUTRAL]:
        sc_ok = [s for s in scens if not np.isnan(vec(data, s, "A", m)).all()]
        if not sc_ok: continue
        for X, Y in itertools.combinations(POLS, 2):
            dif = [vec(data, s, X, m) - vec(data, s, Y, m) for s in sc_ok]
            pt, lo, hi = pooled_boot(dif, rng)
            allv = np.concatenate(dif); sd = allv.std(ddof=1)
            dz = float(allv.mean() / sd) if sd > 0 else float("nan")
            cx = np.concatenate([vec(data, s, X, m) for s in sc_ok]); cy = np.concatenate([vec(data, s, Y, m) for s in sc_ok])
            cd = cliffs(cx, cy)
            cat = category(pt, lo, hi, m); bt = better(pt, m)
            res["pairs"].setdefault(m, {})[f"{X}-{Y}"] = dict(diff=pt, lo=lo, hi=hi, dz=dz, cliff=cd, category=cat, better=("X" if bt > 0 else "Y" if bt < 0 else "-"), n_scen=len(sc_ok))
            md.append(f"| {m} | {X} vs {Y} | {pt:+.3f} [{lo:+.3f},{hi:+.3f}] | {dz:+.2f} | {cd:+.2f} | {cat} | {'X' if bt>0 else 'Y' if bt<0 else '-'} |")
    open(os.path.join(out, "pairwise_table.md"), "w").write("\n".join(md))
    # ---- dominance check per scenario x core metric (practical thresholds, per-scenario mean diffs) -------------
    dom = {}
    for X, Y in itertools.permutations(POLS, 2):
        b = w = e = 0; worse_cells = []
        for m, sl in CORE.items():
            for s in sl:
                if s not in scens: continue
                d = float(np.nanmean(vec(data, s, X, m) - vec(data, s, Y, m)))
                if np.isnan(d): continue
                if abs(d) < THR[m]: e += 1
                elif better(d, m) > 0: b += 1
                else:
                    w += 1; worse_cells.append(f"{m}@{s.split('_')[0]}")
        dom[f"{X}>{Y}"] = dict(better=b, worse=w, equal=e, worse_cells=worse_cells)
    res["dominance"] = dom
    md = ["| X vs Y | X practically better | X practically worse | equal | X worse on |\n|---|---|---|---|---|"]
    for k, v in dom.items():
        md.append(f"| {k} | {v['better']} | {v['worse']} | {v['equal']} | {', '.join(v['worse_cells'][:10])}{'…' if len(v['worse_cells'])>10 else ''} |")
    open(os.path.join(out, "dominance_table.md"), "w").write("\n".join(md))
    json.dump(res, open(os.path.join(out, "analysis.json"), "w"), indent=1, default=float)
    return res


if __name__ == "__main__":
    dirn = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "results", "heldout")
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, "results", "heldout_analysis")
    main(dirn, out)
    print("analysis written to", out)
