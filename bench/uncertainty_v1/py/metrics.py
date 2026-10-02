import numpy as np

TAU_FC = 0.6      # "confident" threshold for false-confidence (chance = 1/3)
# utility of action given true class: rows=action(SELL,HOLD,BUY) cols=true(DOWN,FLAT,UP)
UTIL = np.array([[1., -.3, -1.], [0., 0., 0.], [-1., -.3, 1.]])


def brier(P, y):
    Y = np.eye(P.shape[1])[y]; return ((P - Y) ** 2).sum(1).mean()


def logloss(P, y): return -np.log(np.clip(P[np.arange(len(y)), y], 1e-9, 1)).mean()


def reliability(P, y, bins=10):
    c = P.max(1); ok = P.argmax(1) == y
    e = np.linspace(0, 1, bins + 1); i = np.clip(np.digitize(c, e) - 1, 0, bins - 1)
    rows = []
    for b in range(bins):
        m = i == b
        if m.sum(): rows.append((b, m.sum(), c[m].mean(), ok[m].mean()))
    return rows


def ece(P, y, bins=10, equal_mass=False):
    c = P.max(1); ok = (P.argmax(1) == y).astype(float)
    if equal_mass:
        e = np.unique(np.quantile(c, np.linspace(0, 1, bins + 1))); e[-1] += 1e-9
    else:
        e = np.linspace(0, 1, bins + 1); e[-1] += 1e-9
    i = np.clip(np.digitize(c, e) - 1, 0, len(e) - 2)
    return sum((i == b).mean() * abs(c[i == b].mean() - ok[i == b].mean()) for b in range(len(e) - 1) if (i == b).any())


def false_conf(P, y, tau=TAU_FC):
    """FCR = P(wrong | conf>=tau); CWM = P(conf>=tau & wrong) (confident-wrong mass)."""
    c = P.max(1); wrong = P.argmax(1) != y; m = c >= tau
    return (wrong[m].mean() if m.any() else np.nan), (m & wrong).mean(), m.mean()


def actions(P, accept=None):
    a = P.argmax(1)      # class index == action index (0 SELL,1 HOLD,2 BUY)
    if accept is not None: a = np.where(accept, a, 1)
    return a


def utility(a, y): return UTIL[a, y]


def turnover(a):
    return float((a[1:] != a[:-1]).mean()) if len(a) > 1 else np.nan


def risk_coverage(score, err):
    """selective error vs coverage, accepting highest score first. returns (coverage, risk), AURC."""
    o = np.argsort(-score, kind="stable"); e = err[o].astype(float)
    cov = np.arange(1, len(e) + 1) / len(e); risk = np.cumsum(e) / np.arange(1, len(e) + 1)
    return cov, risk, float(risk.mean())


def summary(P, y, prefix=""):
    f, cw, hi = false_conf(P, y)
    return {prefix + "n": len(y), prefix + "acc": float((P.argmax(1) == y).mean()), prefix + "brier": brier(P, y),
            prefix + "logloss": logloss(P, y), prefix + "ece": ece(P, y), prefix + "ece_eq": ece(P, y, equal_mass=True),
            prefix + "fcr": f, prefix + "cwm": cw, prefix + "hi_conf_rate": hi}
