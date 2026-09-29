"""Aggregate eval results into markdown tables + a machine-readable summary."""
import sys, json, os, collections
import numpy as np
sys.path.insert(0, 'src')
import registry as REG
from streams import SCENARIOS

OUT = "results/tables"; os.makedirs(OUT, exist_ok=True)
rng = np.random.default_rng(0)


def load(tag):
    return json.load(open(f"results/eval_{tag}.json"))


def idx(rows):
    d = collections.defaultdict(dict)   # (model, scen) -> seed -> row
    for r in rows:
        d[(r["model"], r["scenario"])][r["seed"]] = r
    return d


def boot_ci(x, n=4000):
    x = np.asarray(x, float)
    m = rng.choice(x, size=(n, len(x)), replace=True).mean(1)
    return float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))


def ov(d, m, s):
    seeds = sorted(d[(m, s)])
    return np.array([d[(m, s)][k]["overall"] for k in seeds])


def skill_table(d, models, task, tag):
    null = "null_" + task
    hdr = "| model | family | " + " | ".join(SCENARIOS) + " | mean | worst |\n|---|---|" + "---|" * (len(SCENARIOS) + 2) + "\n"
    lines, summ = [], {}
    for m in models:
        sk = [1 - ov(d, m, s).mean() / ov(d, null, s).mean() for s in SCENARIOS]
        summ[m] = dict(mean=float(np.mean(sk)), worst=float(np.min(sk)), per=dict(zip(SCENARIOS, map(float, sk))))
        lines.append((np.mean(sk), f"| {m} | {REG.R[m]['family']} | " + " | ".join(f"{v:.2f}" for v in sk) + f" | **{np.mean(sk):.2f}** | {np.min(sk):.2f} |"))
    lines.sort(key=lambda t: -t[0])
    open(f"{OUT}/skill_{tag}_{task}.md", "w").write(hdr + "\n".join(l for _, l in lines) + "\n")
    return summ


def paired(d, a, b, scens):
    """positive => a better (lower excess) than b."""
    diffs = np.stack([ov(d, b, s) - ov(d, a, s) for s in scens])   # scen x seed
    agg = diffs.mean(0)
    lo, hi = boot_ci(agg)
    return dict(mean=float(agg.mean()), lo=lo, hi=hi, wins=float((agg > 0).mean()),
                per=dict(zip(scens, map(float, diffs.mean(1)))))


def main(tag="main"):
    d = idx(load(tag))
    tune = json.load(open("results/tune.json"))
    summary = {}
    for task in ("reg", "clf"):
        models = [m for m, v in REG.R.items() if v["task"] == task]
        summary[task] = dict(skill=skill_table(d, models, task, tag))
        if tag != "main":
            continue
        best = tune["best"]
        fam = lambda f: [m for m in models if REG.R[m]["family"] in f]
        simple = min(fam(["baseline"]), key=lambda m: best[m]["score"])
        rolling = [m for m in models if m.startswith("rolling") and REG.R[m]["family"] == "baseline"][0]
        incr = min(fam(["incremental", "tree", "drift_composite", "custom", "calibration"]), key=lambda m: best[m]["score"])
        incr_lin = min(fam(["incremental"]), key=lambda m: best[m]["score"])
        summary[task].update(best_simple=simple, best_incremental=incr, best_incremental_plain=incr_lin)
        ns = [s for s in SCENARIOS if s != "stationary"]
        frozen = [m for m in models if m.startswith("frozen")][0]
        periodic = [m for m in models if m.startswith("periodic")][0]
        lines = [f"| model | vs {frozen} | vs {periodic} | vs {rolling} |", "|---|---|---|---|"]
        cmp = {}
        for m in models:
            if REG.R[m]["family"] == "control":
                continue
            cells = []
            for b in (frozen, periodic, rolling):
                if m == b:
                    cells.append("—"); continue
                p = paired(d, m, b, ns)
                cmp[f"{m}|{b}"] = p
                cells.append(f"{p['mean']:+.4f} [{p['lo']:+.4f},{p['hi']:+.4f}] w={p['wins']:.0%}")
            lines.append(f"| {m} | " + " | ".join(cells) + " |")
        open(f"{OUT}/paired_{task}.md", "w").write(
            "Positive = row model has LOWER excess loss than the column baseline (mean over the 10 non-stationary scenarios, 20 seeds; 95% bootstrap CI over seeds; w = fraction of seeds won).\n\n"
            + "\n".join(lines) + "\n")
        summary[task]["paired"] = cmp
        st = ["| model | stationary excess | null excess | stationary skill |", "|---|---|---|---|"]
        for m in models:
            v = ov(d, m, "stationary"); n = ov(d, "null_" + task, "stationary")
            st.append(f"| {m} | {v.mean():.4f} | {n.mean():.4f} | {1 - v.mean() / n.mean():.2f} |")
        open(f"{OUT}/stationary_{task}.md", "w").write("\n".join(st) + "\n")
        ad = []
        for sc in ["abrupt", "delayed_50", "delayed_200", "missing_random", "missing_blackout", "nonlinear_abrupt", "shock"]:
            ad.append(f"\n**{sc}** (first change point c={d[(models[0], sc)][0]['cps'][0]['c']})\n")
            ad.append("| model | pre-change excess | first 100 | next 300 | median recovery (steps, cap 1000) | % recovered |\n|---|---|---|---|---|---|")
            for m in models:
                cp = [d[(m, sc)][k]["cps"][0] for k in sorted(d[(m, sc)])]
                ad.append(f"| {m} | {np.mean([c['pre'] for c in cp]):.3f} | {np.mean([c['first100'] for c in cp]):.3f} | {np.mean([c['next300'] for c in cp]):.3f} | {np.median([c['rec'] for c in cp]):.0f} | {np.mean([c['recovered'] for c in cp]):.0%} |")
        open(f"{OUT}/adapt_{task}.md", "w").write("\n".join(ad) + "\n")
        rr = ["| model | novel B onset (t=1000) first-100 | return B (t=3000) first-100 | return A (t=2000) first-100 | RRI = novel/return (>1: recall helps) |", "|---|---|---|---|---|"]
        rri = {}
        for m in models:
            nov, ret, reta = [], [], []
            for k in sorted(d[(m, "recurring")]):
                c = d[(m, "recurring")][k]["cps"]
                nov.append(c[0]["first100"]); reta.append(c[1]["first100"]); ret.append(c[2]["first100"])
            rri[m] = float(np.mean(nov) / np.mean(ret))
            rr.append(f"| {m} | {np.mean(nov):.3f} | {np.mean(ret):.3f} | {np.mean(reta):.3f} | {rri[m]:.2f} |")
        open(f"{OUT}/recurring_{task}.md", "w").write("\n".join(rr) + "\n")
        summary[task]["rri"] = rri
        fd = ["| model | resets: false_drift | resets: stationary | resets: abrupt |", "|---|---|---|---|"]
        for m in models:
            if REG.R[m]["family"] in ("drift_composite", "custom"):
                g = lambda sc: np.mean([d[(m, sc)][k]["meta"]["n_resets"] for k in d[(m, sc)]])
                fd.append(f"| {m} | {g('false_drift'):.2f} | {g('stationary'):.2f} | {g('abrupt'):.2f} |")
        open(f"{OUT}/falsedrift_{task}.md", "w").write("\n".join(fd) + "\n")
        cs = ["| model | complexity(0-4) | sec/run (4000 steps) | state@1000 | state@4000 | refits (mean) |", "|---|---|---|---|---|---|"]
        for m in models:
            rr_ = [r for s in SCENARIOS for r in d[(m, s)].values()]
            cs.append(f"| {m} | {REG.R[m]['complexity']} | {np.mean([r['seconds'] for r in rr_]):.2f} | {int(np.mean([r['state']['999'] for r in rr_])):,} B | {int(np.mean([r['state']['3999'] for r in rr_])):,} B | {np.mean([r['meta']['n_refits'] for r in rr_]):.0f} |")
        open(f"{OUT}/cost_{task}.md", "w").write("\n".join(cs) + "\n")
        vr = ["| model | mean std across seeds (overall excess) | mean CV |", "|---|---|---|"]
        for m in models:
            sd = np.mean([ov(d, m, s).std(ddof=1) for s in SCENARIOS])
            cv = np.mean([ov(d, m, s).std(ddof=1) / max(ov(d, m, s).mean(), 1e-9) for s in SCENARIOS])
            vr.append(f"| {m} | {sd:.4f} | {cv:.2f} |")
        open(f"{OUT}/variance_{task}.md", "w").write("\n".join(vr) + "\n")
        ts = ["| model | #configs | best | median | worst | worst/best |", "|---|---|---|---|---|---|"]
        for m in models:
            sc = sorted(f["score"] for f in tune["full"] if f["model"] == m)
            ts.append(f"| {m} | {len(sc)} | {sc[0]:.4f} | {np.median(sc):.4f} | {sc[-1]:.4f} | {sc[-1] / max(sc[0], 1e-9):.2f}x |")
        open(f"{OUT}/tuning_{task}.md", "w").write("\n".join(ts) + "\n")
        ch = ["| model | chosen params (tuning seeds 1000-1007) | tuning score |", "|---|---|---|"]
        for m in models:
            ch.append(f"| {m} | `{json.dumps(best[m]['params'])}` | {best[m]['score']:.4f} |")
        open(f"{OUT}/chosen_{task}.md", "w").write("\n".join(ch) + "\n")
    json.dump(summary, open(f"results/summary_{tag}.json", "w"), indent=1, default=float)
    return summary


if __name__ == "__main__":
    for tag in sys.argv[1:] or ["main"]:
        main(tag)
