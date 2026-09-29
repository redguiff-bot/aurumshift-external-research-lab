"""Read-only adjudication probes for report 009. Does not modify either corpus.

Usage (extract both corpora to scratch first, never run inside the study directories):
  git archive origin/claude/risk-capacity-turnover-v1 bench/capacity_v1 | tar -x -C $S/Abranch   # Study A, unmerged run 2
  git archive origin/main bench/capacity_v1                              | tar -x -C $S/Amain     # Study A, as merged (run 1)
  git archive origin/claude/festive-archimedes-c3fso6 bench/capacity_v1  | tar -x -C $S/B         # Study B (PR #8 head 0ff4f71)
  S=$S python3 adjudication_probe.py
Requires numpy, pandas, scipy.
"""
import os, sys, json
import numpy as np, pandas as pd
S = os.environ["S"]
rng = np.random.default_rng(1)
def boot(x, n=4000):
    m = np.array([x[rng.integers(0, len(x), len(x))].mean() for _ in range(n)])
    return round(x.mean(), 3), round(np.percentile(m, 2.5), 3), round(np.percentile(m, 97.5), 3)

print("== [1] Study A run 2 (UNMERGED branch cb13041) validation split, dz units, block bootstrap over (family,variant,seed), caps pooled")
a = pd.read_csv(f"{S}/Abranch/bench/capacity_v1/results/validation_raw.csv.gz")
a["dz"] = a.lat_per_slot_hour / a["dens0_rms"]
piv = a.pivot_table(index=["family", "variant", "seed", "cap"], columns="policy", values="dz")
for p, q in [("RANK_NET","FIFO"),("FIFO_NETPOS","FIFO"),("RANK_SCORE_RAW","FIFO"),("RANK_NET","RANK_SCORE_RAW"),
             ("RANK_NET","FIFO_NETPOS"),("SLOTHOUR_DENSITY","RANK_NET"),("CORR_PENALTY","RANK_NET"),
             ("MARGINAL_RISK","RANK_NET"),("CLUSTER_CAP","RANK_NET"),("LIN_TS","RANK_NET"),("LINUCB","RANK_NET"),
             ("UNCERTAINTY_LCB","RANK_NET"),("COMPOSED","RANK_NET"),("RANDOM_SEEDED","FIFO"),("ROUND_ROBIN","FIFO"),
             ("EQUAL_QUOTA","FIFO"),("OLDEST_SLOT","FIFO")]:
    d = (piv[p] - piv[q]).dropna().groupby(level=[0, 1, 2]).mean().values
    print(f"  {p} - {q}: mean, lo, hi = {boot(d)}")
for c in (3, 4, 6, 10):
    sub = piv.xs(c, level=3)
    print(f"  cap {c}: RANK_NET-FIFO {(sub.RANK_NET-sub.FIFO).mean():.3f}  NETPOS-FIFO {(sub.FIFO_NETPOS-sub.FIFO).mean():.3f}")
print("  FIFO utilisation by cap:", a[a.policy == "FIFO"].groupby("cap").utilisation.mean().round(3).to_dict())

print("\n== [2] Study A as merged (main, run 1) tuning split: tuned method minus FIFO in dens0_sd units, per family (S12 normaliser blow-up)")
t = pd.read_csv(f"{S}/Amain/bench/capacity_v1/results/tuning_raw.csv.gz")
tp = json.load(open(f"{S}/Amain/bench/capacity_v1/results/tuned_params.json"))
sel = t[(t.policy == "FIFO") | t.apply(lambda r: r.base in tp and json.loads(r.params) == tp[r.base], axis=1)].copy()
sel["z"] = sel.lat_per_slot_hour / sel.dens0_sd
pv = sel.pivot_table(index=["family", "variant", "seed", "cap"], columns="base", values="z")
d = (pv["SLOTHOUR_DENSITY"] - pv["FIFO"]).groupby(level=0).mean()
print("  SLOTHOUR_DENSITY - FIFO by family:", d.round(3).to_dict())
print("  share of pooled mean contributed by S12:", round(d["S12_all_equal"] / d.sum(), 3))

print("\n== [3] Study B heldout H1 (PR #8 head), M1 = net per available slot-hour, paired by (scenario, seed), macro over 13 scenarios")
h = pd.read_csv(f"{S}/B/bench/capacity_v1/results/heldout/H1_primary.csv")
m = "net_per_avail_slot_hour"
pb = h.pivot_table(index=["scen", "seed"], columns="policy", values=m)
for p, q in [("FIFO_SCREEN","FIFO"),("SCORE_RANK","FIFO"),("SLOTHOUR","FIFO"),("SCORE_RANK","FIFO_SCREEN"),
             ("SLOTHOUR","SCORE_RANK"),("UNCERTAINTY_LCB","SLOTHOUR"),("CORR_AWARE","SLOTHOUR"),("LINTS","SLOTHOUR"),
             ("SLOTHOUR_SHADOW","SLOTHOUR"),("OLDEST_SLOT","FIFO"),("RANDOM","FIFO"),("ROUND_ROBIN","FIFO"),("EQUAL_QUOTA","FIFO")]:
    dd = (pb[p] - pb[q]).unstack(0); n = len(dd)
    bs = [dd.iloc[rng.integers(0, n, n)].mean().mean() for _ in range(2000)]
    print(f"  {p} - {q}: {dd.mean().mean():.3f} [{np.percentile(bs,2.5):.3f}, {np.percentile(bs,97.5):.3f}] wins {(dd.mean()>0).sum()}/13")
h2 = pd.read_csv(f"{S}/B/bench/capacity_v1/results/heldout/H2_ingest_matrix.csv")
print("  ingest confound check (macro M1, seeds 3000-3009):")
print(h2.groupby(["policy","ingest","scen"])[m].mean().groupby(["policy","ingest"]).mean().unstack().round(3).loc[["FIFO","SCORE_RANK","SLOTHOUR"]].to_string())

print("\n== [4] Probes: run Study A run-2 simulator (scratch copy) under altered assumptions; 20 seeds x cap 4, family S3_chronic; latent bps per slot-hour")
sys.path.insert(0, f"{S}/Abranch/bench/capacity_v1/py")
import warnings; warnings.filterwarnings("ignore")
from env import make_world, run, BASE
from policies import default_configs
import scenarios as SCN
reg = default_configs()
def go(over, label, pols, fam="S3_chronic", ref="FIFO"):
    P = dict(BASE); P.update(SCN.SC[fam]); P.update(over)
    out = {k: [] for k in pols}
    for s in range(20):
        W = make_world(P, 5000 + s)
        for k, (name, params) in pols.items():
            out[k].append(run(W, reg[name](params), 4, seed=s)["lat_per_slot_hour"])
    f = np.array(out[ref])
    print(f"  {label:38s}", {k: round(float(np.mean(v)), 3) for k, v in out.items()},
          "| diff vs", ref, {k: f"{np.mean(np.array(v)-f):+.3f}" for k, v in out.items() if k != ref})
P1 = {"FIFO": ("FIFO", {}), "RANDOM": ("RANDOM_SEEDED", {}), "NETPOS": ("FIFO_NETPOS", {}), "RANK_NET": ("RANK_NET", {})}
go({}, "A default (waiting decay tau=8)", P1)
go({"tau": 1e9}, "A, no waiting-age decay", P1)
BL = {"mu_mean": 22.0, "fee_lo": 2, "fee_hi": 6, "slip_lo": .5, "slip_hi": 1.5, "dur_base": 7.0, "tau": 1e9, "evict_extra": 0.0}
go(BL, "A transplanted to B-like edge/cost", P1)
P2 = {"FIFO": ("FIFO", {}), "OLD4": ("OLDEST_SLOT", {"min_hold": 4}), "OLD12": ("OLDEST_SLOT", {"min_hold": 12})}
go({}, "A default (evict penalty 3)", P2)
go(BL, "A transplanted to B-like", P2)
go({**BL, "fee_lo": 6, "fee_hi": 18, "slip_lo": 1.5, "slip_hi": 4.5}, "A transplanted, cost x3", P2)
