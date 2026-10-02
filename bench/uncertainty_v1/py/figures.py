import glob, numpy as np, pandas as pd, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
def rd(p):
    out = []
    for f in sorted(glob.glob(p)):
        try: out.append(pd.read_csv(f))
        except pd.errors.EmptyDataError: pass
    return pd.concat(out, ignore_index=True)
C = {"raw": "#c0392b", "temperature": "#1f77b4", "beta": "#2ca02c", "isotonic": "#9467bd"}
# 1 reliability (gbm, seeds 0-2 pooled)
Rl = rd("results/static_hold_*_reliability.csv"); Rl = Rl[Rl.base == "gbm"]
fig, ax = plt.subplots(1, 3, figsize=(13, 4), sharex=True, sharey=True)
for a, (sc, ph, ttl) in zip(ax, [("none", "pre", "in-distribution"), ("feature_shift", "post", "feature shift (post-onset)"), ("regime_transition", "post", "regime transition (post-onset)")]):
    a.plot([0, 1], [0, 1], "k--", lw=1)
    for m, c in C.items():
        g = Rl[(Rl.scenario == sc) & (Rl.phase == ph) & (Rl.method == m)]
        if g.empty: continue
        g = g.groupby("bin").apply(lambda x: pd.Series(dict(conf=np.average(x.conf, weights=x.n), acc=np.average(x.acc, weights=x.n), n=x.n.sum())))
        a.plot(g.conf, g.acc, "o-", color=c, label=m, ms=4)
    a.set_title(ttl); a.set_xlabel("confidence (top label)"); a.grid(alpha=.3)
ax[0].set_ylabel("empirical accuracy"); ax[0].legend(); fig.suptitle("Reliability, over-confident GBM base, static calibrators fit on calibration split (seeds 0-2)")
fig.tight_layout(); fig.savefig("results/figures/reliability_gbm.png", dpi=130); plt.close(fig)
# 2 rolling ECE static vs online
RL = rd("results/hold_*_rolling.csv"); RL = RL[(RL.cal == "temperature") & (RL.base == "gbm")]
fig, ax = plt.subplots(1, 4, figsize=(15, 3.6), sharey=True)
for a, sc in zip(ax, ["none", "vol_jump", "regime_transition", "feature_shift"]):
    for v, c, ls in [("static", "#c0392b", "-"), ("window", "#1f77b4", "-"), ("decay", "#2ca02c", "--"), ("leak_peek", "#7f7f7f", ":")]:
        g = RL[(RL.scenario == sc) & (RL.variant == v)].groupby("win").ece.mean(); a.plot((g.index + .5) * 500, g.values, ls, color=c, label=v)
    a.axvline(1500, color="k", lw=.8); a.set_title(sc); a.set_xlabel("held-out step (onset=1500)"); a.grid(alpha=.3)
ax[0].set_ylabel("ECE (500-step windows)"); ax[0].legend(); fig.suptitle("Static vs online temperature scaling (GBM, 12 seeds)"); fig.tight_layout(); fig.savefig("results/figures/rolling_ece.png", dpi=130); plt.close(fig)
# 3 electricity
EB = pd.read_csv("results/public_elec_blocks.csv"); EB = EB[(EB.cal == "temperature")]
EC = pd.read_csv("results/public_elec_conformal.csv")
fig, ax = plt.subplots(1, 2, figsize=(11, 3.8))
for v, c in [("static", "#c0392b"), ("window", "#1f77b4"), ("decay", "#2ca02c")]:
    g = EB[(EB.base == "gbm") & (EB.variant == v)].groupby("block").ece.mean(); ax[0].plot(g.index, g.values, "o-", color=c, label=v)
ax[0].set_title("ELEC2: ECE per 2000-row block (GBM, temperature)"); ax[0].set_xlabel("block"); ax[0].legend(); ax[0].grid(alpha=.3)
for m, c in [("split", "#c0392b"), ("rolling", "#1f77b4"), ("aci_rolling", "#2ca02c")]:
    g = EC[(EC.base == "gbm") & (EC.method == m)].groupby("block").coverage.mean(); ax[1].plot(g.index, g.values, "o-", color=c, label=m)
ax[1].axhline(.8, color="k", lw=.8); ax[1].set_title("ELEC2: conformal set coverage per block (target 0.80)"); ax[1].set_xlabel("block"); ax[1].legend(); ax[1].grid(alpha=.3)
fig.tight_layout(); fig.savefig("results/figures/elec2.png", dpi=130); plt.close(fig)
