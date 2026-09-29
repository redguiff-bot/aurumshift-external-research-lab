"""Environment-invariance diagnostics: per-env slopes + Cochran Q (HAC SEs) and ICP-lite (Peters et al. 2016).
Passing these is evidence of *invariant association*, never identification of a causal effect."""
import itertools
import numpy as np
from scipy import stats


def hac_slope(f, y, lag=48):
    f = f - f.mean(); yc = y - y.mean()
    b = (f @ yc) / (f @ f)
    u = (yc - b * f) * f
    n = len(f)
    s = u @ u + 2 * sum((1 - k / (lag + 1)) * (u[k:] @ u[:-k]) for k in range(1, lag + 1))
    se = np.sqrt(max(s, 1e-30)) / (f @ f)
    return float(b), float(se)


def cochran_q(f_by_env, y_by_env):
    bs, ses = [], []
    for e in f_by_env:
        b, se = hac_slope(f_by_env[e], y_by_env[e]); bs.append(b); ses.append(se)
    bs, ses = np.array(bs), np.array(ses)
    w = 1 / ses ** 2; bbar = (w * bs).sum() / w.sum()
    Q = float((w * (bs - bbar) ** 2).sum()); df = len(bs) - 1
    return dict(betas=bs.tolist(), ses=ses.tolist(), Q=Q, df=df, p=float(1 - stats.chi2.cdf(Q, df)),
                sign_agree=float(np.mean(np.sign(bs) == np.sign(bbar))), z_min=float(np.min(np.abs(bs / ses))))


def icp_lite(X_by_env, y_by_env, names, cand_names, max_size=3, alpha=0.05, thin=12):
    """Accept subset S if residuals of pooled OLS y~S have equal mean (F) and variance (Levene) across envs."""
    envs = list(X_by_env)
    X = np.vstack([X_by_env[e][::thin] for e in envs]); y = np.concatenate([y_by_env[e][::thin] for e in envs])
    lab = np.concatenate([[i] * len(X_by_env[e][::thin]) for i, e in enumerate(envs)])
    ix = {n: names.index(n) for n in cand_names}
    accepted, pv = [], {}
    for k in range(0, max_size + 1):
        for S in itertools.combinations(cand_names, k):
            A = np.column_stack([np.ones(len(y))] + [X[:, ix[s]] for s in S])
            r = y - A @ np.linalg.lstsq(A, y, rcond=None)[0]
            groups = [r[lab == i] for i in range(len(envs))]
            p1 = stats.f_oneway(*groups)[1]; p2 = stats.levene(*groups)[1]
            p = min(1.0, 2 * min(p1, p2)); pv[S] = p
            if p > alpha:
                accepted.append(S)
    inter = set(cand_names)
    for S in accepted:
        inter &= set(S)
    return dict(n_subsets=len(pv), n_accepted=len(accepted), accepted=[list(s) for s in accepted[:20]],
                intersection=sorted(inter) if accepted else None,
                assumptions_violated=(len(accepted) == 0), min_p=float(min(pv.values())))
