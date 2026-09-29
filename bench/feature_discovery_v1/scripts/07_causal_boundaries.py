"""Where do predictive association, invariance and ICP-lite stop short of causation? Structural simulations with known DAGs.
A causal X->Y | B confounded (U->X, U->Y) | C reverse (Y->X, X proxies past Y) | D non-invariant spurious (loading flips by environment)."""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import numpy as np
from scipy import stats
from fd import invariance, causal
from fd.metrics import spearman

RES = os.path.join(os.path.dirname(__file__), "..", "results")


def ar(rng, n, phi):
    e = rng.standard_normal(n); x = np.zeros(n)
    for t in range(1, n):
        x[t] = phi * x[t - 1] + np.sqrt(1 - phi ** 2) * e[t]
    return x


def gen(case, rng, n=6000, env=0, do_x=None, shift=True):
    """X_t (feature at t) and Y_{t+1} (label). shift=True: environments change the scale of X's idiosyncratic noise
    (an intervention on X, the kind of heterogeneity ICP needs); shift=False: environments are exchangeable replications."""
    s = [1.0, 1.6, 0.6, 1.3][env % 4] if shift else 1.0
    U = ar(rng, n, 0.9)
    b = 0.3
    if case == "A":      # X -> Y
        X = s * ar(rng, n, 0.8) if do_x is None else do_x
        Y = b * np.roll(X, 1) + rng.standard_normal(n)
    elif case == "B":    # U -> X, U -> Y ; X has NO effect on Y
        X = 0.7 * U + 0.7 * s * rng.standard_normal(n) if do_x is None else do_x
        Y = b * np.roll(U, 1) + rng.standard_normal(n)
    elif case == "C":    # Y -> X (X is a lagged proxy of an autocorrelated Y)
        Yl = ar(rng, n, 0.9)
        X = 0.8 * np.roll(Yl, 1) + 0.5 * s * rng.standard_normal(n) if do_x is None else do_x
        return X[2:-1], Yl[3:]
    elif case == "D":    # confounder loading flips sign between environments
        sign = 1.0 if env % 2 == 0 else -1.0
        X = 0.7 * U + 0.7 * rng.standard_normal(n) if do_x is None else do_x
        Y = sign * b * np.roll(U, 1) + rng.standard_normal(n)
    return X[1:-1], Y[2:]


CASES = {"A_causal_shifted_envs": ("A", True), "B_confounded_shifted_envs": ("B", True), "B_confounded_exchangeable_envs": ("B", False),
         "C_reverse_exchangeable_envs": ("C", False), "D_flipping_confounder": ("D", True)}
TRUE = {"A": True, "B": False, "C": False, "D": False}
out = {}
for name, (case, shift) in CASES.items():
    envs = {f"e{i}": gen(case, np.random.default_rng(100 * ord(case) + i + (0 if shift else 50)), env=i, shift=shift) for i in range(8)}
    Xe = {e: v[0] for e, v in envs.items()}; ye = {e: v[1] for e, v in envs.items()}
    ic = float(np.mean([spearman(Xe[e], ye[e]) for e in envs]))
    q = invariance.cochran_q(Xe, ye)
    XX = {e: Xe[e][:, None] for e in envs}
    icp = invariance.icp_lite(XX, ye, ["X"], ["X"], max_size=1, thin=6)
    bs, ses = [], []
    for i in range(8):     # randomised intervention: X assigned independently of everything, HAC SE
        Xdo = np.random.default_rng(5000 + i).standard_normal(6000)
        X_, Y_ = gen(case, np.random.default_rng(100 * ord(case) + i + (0 if shift else 50)), env=i, do_x=Xdo, shift=shift)
        b_, se_ = invariance.hac_slope(X_, Y_); bs.append(b_); ses.append(se_)
    bs, ses = np.array(bs), np.array(ses)
    b = float(bs.mean()); z = b / (np.sqrt((ses ** 2).sum()) / len(ses)); pdo = float(2 * (1 - stats.norm.cdf(abs(z))))
    stable = abs(ic) > 0.02
    inc = icp["intersection"] is not None and "X" in icp["intersection"]
    out[name] = dict(pooled_ic=ic, cochran_Q_p=q["p"], sign_agree=q["sign_agree"], icp_n_accepted=icp["n_accepted"],
                     icp_intersection=icp["intersection"], do_effect=b, do_effect_p=pdo,
                     class_observational_even_if_mechanism_claimed=causal.classify(stable, q["p"], q["sign_agree"], inc, True),
                     class_with_randomised_design=causal.classify(stable, q["p"], q["sign_agree"], inc, True, design=dict(kind="randomised_intervention", effect_p=pdo, checks_passed=True, replicated=bool(np.mean(np.sign(bs) == np.sign(b)) >= 0.875))),
                     truth_X_causes_Y=TRUE[case])
    print(name, {k: (round(v, 4) if isinstance(v, float) else v) for k, v in out[name].items()})
json.dump(out, open(os.path.join(RES, "causal_boundaries.json"), "w"), indent=1)
