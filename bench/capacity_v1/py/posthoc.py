"""POST-HOC exploratory diagnostics (NOT pre-registered, NOT part of any verdict, run on VALIDATION worlds only
so that the held-out set stays untouched).  Purpose: attribute effects the pre-registered comparison cannot separate.
  LIFO_NETPOS     freshest-first with the net>0 filter  -> separates 'freshness' from 'quality' ranking (FIFO takes the stalest first)
  MARGINAL_DIAG   RANK_NET minus own-variance term only (no correlation) -> is the MARGINAL_RISK gain about correlation or just vol/duration?
  MARGINAL_CORR   RANK_NET minus cross-covariance term only            (= CORR_PENALTY at the tuned-for-MARGINAL scale)
Writes results/posthoc_validation.csv.gz and results/tables/posthoc.md"""
import sys, os, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd
from policies import Policy, Engine, default_configs, FifoNetPos, isnan
import runner as R
import scenarios as SCN
from report_tables import md, ci


class LifoNetPos(FifoNetPos):
    name = "LIFO_NETPOS"
    def decide(self, t, pend, openp, free, cap):
        for v in pend:
            if v.cid in self.seen: continue
            self.seen.add(v.cid)
            if not isnan(v.score): self.s_sum += v.score; self.s_n += 1
            if not isnan(v.cost): self.c_sum += v.cost; self.c_n += 1
        sm = self.s_sum / self.s_n if self.s_n else 0.0
        cm = self.c_sum / self.c_n if self.c_n else 0.0
        ok = [v for v in pend if (sm if isnan(v.score) else v.score) - (cm if isnan(v.cost) else v.cost) > 0]
        order = sorted(ok, key=lambda v: (v.age, v.cid))
        return [v.cid for v in order[:max(free, 0)]], []


class MarginalDiag(Engine):
    def __init__(self, name, g, mode):
        super().__init__(name, "diversification"); self.g, self.mode = g, mode
    def est(self, v):
        e = Engine.est(self, v)
        if e is None or self.cov_n < 60: return e
        net, dur, x = e
        S, _ = self.corr_hat(); sbar = float(np.sqrt(np.mean(np.diag(S))))
        if self.mode == "diag":
            net = net - self.g * dur * S[v.inst, v.inst] / (2 * sbar)
        return net, dur, x


def cell_ph(job):
    P, seed, caps, meta = job
    from env import make_world, run
    W = make_world(P, seed); rows = []
    tuned = json.load(open(f"{R.RES}/tuned_params.json"))
    reg = default_configs()
    pol = {"FIFO": lambda: reg["FIFO"]({}), "FIFO_NETPOS": lambda: reg["FIFO_NETPOS"]({}), "RANK_NET": lambda: reg["RANK_NET"]({}),
           "LIFO_NETPOS": lambda: LifoNetPos(), "MARGINAL_RISK": lambda: reg["MARGINAL_RISK"](tuned["MARGINAL_RISK"]),
           "MARGINAL_DIAG": lambda: MarginalDiag("MARGINAL_DIAG", tuned["MARGINAL_RISK"]["g"], "diag"),
           "CORR_PENALTY": lambda: reg["CORR_PENALTY"](tuned["CORR_PENALTY"])}
    for cap in caps:
        for name, f in pol.items():
            m = run(W, f(), cap, seed=seed)
            rows.append(dict(meta, seed=seed, cap=cap, policy=name, **{k: m[k] for k in ("lat_per_slot_hour", "dens0_rms", "ret_to_risk", "pnl_day_sd", "max_drawdown", "hhi_cluster", "mean_hold")}))
    return rows


if __name__ == "__main__":
    from multiprocessing import Pool
    jobs = []
    for fam in SCN.families("VALIDATION"):
        for P in SCN.variants(fam, "VALIDATION", 3):
            Pc = {k: v for k, v in P.items() if not k.startswith("_")}
            for s in range(4):
                jobs.append((Pc, 2000 + s, (4, 6), dict(family=fam, variant=P["_variant"])))
    with Pool(4) as p: rows = [r for x in p.imap_unordered(cell_ph, jobs) for r in x]
    df = pd.DataFrame(rows); df.to_csv(f"{R.RES}/posthoc_validation.csv.gz", index=False)
    key = ["family", "variant", "seed", "cap"]
    def d(a, b, m, scale=True):
        W = df.pivot_table(index=key, columns="policy", values=m); x = W[a] - W[b]
        if scale: x = x / W["FIFO"].index.to_frame().join(df[df.policy == "FIFO"].set_index(key).dens0_rms).dens0_rms
        return x.reset_index(name="d")
    out = []
    for a, b in (("FIFO", "LIFO_NETPOS"), ("FIFO_NETPOS", "LIFO_NETPOS"), ("RANK_NET", "LIFO_NETPOS")):
        x = d(a, b, "lat_per_slot_hour"); blk = x.groupby(["family", "variant", "seed"]).d.mean().values
        lo, hi = ci(blk); out.append(dict(comparison=f"{a} - {b} (lat, dz)", pooled=f"{blk.mean():+.3f} [{lo:+.3f},{hi:+.3f}]"))
    for a in ("MARGINAL_RISK", "MARGINAL_DIAG", "CORR_PENALTY"):
        for m, sc in (("lat_per_slot_hour", True), ("ret_to_risk", False), ("pnl_day_sd", False), ("max_drawdown", False)):
            x = d(a, "RANK_NET", m, sc); blk = x.groupby(["family", "variant", "seed"]).d.mean().values
            lo, hi = ci(blk); out.append(dict(comparison=f"{a} - RANK_NET ({m})", pooled=f"{blk.mean():+.4f} [{lo:+.4f},{hi:+.4f}]"))
    open(f"{R.RES}/tables/posthoc.md", "w").write(md(pd.DataFrame(out)))
    print(md(pd.DataFrame(out)))
