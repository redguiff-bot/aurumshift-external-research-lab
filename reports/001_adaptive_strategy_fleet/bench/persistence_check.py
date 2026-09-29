"""Pickle round-trip check: does a restored policy continue identically to the uninterrupted one?"""
import pickle, random, warnings; warnings.filterwarnings("ignore")
from river import bandit, stats, proba
def drive(p, n, rng, arms=list(range(30))):
    out = []
    for _ in range(n):
        a = p.pull(arms); out.append(a); p.update(a, float(rng.random() < 0.3 + 0.02 * a))
    return out
for name, mk in [("river_ucb_mean", lambda: bandit.UCB(delta=0.5, seed=1)),
                 ("river_ts_beta", lambda: bandit.ThompsonSampling(reward_obj=proba.Beta(), seed=1)),
                 ("river_ucb_ew", lambda: bandit.UCB(delta=0.5, reward_obj=stats.EWMean(0.9), seed=1))]:
    p = mk(); drive(p, 300, random.Random(5))
    blob = pickle.dumps(p); q = pickle.loads(blob)
    print(name, "identical continuation:", drive(p, 200, random.Random(9)) == drive(q, 200, random.Random(9)), "blob bytes", len(blob))
