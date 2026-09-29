"""Prequential harness with explicit label-availability control.

At step t the model may only see labels whose availability step
    avail_step(t') = t' + 1 + delay   <=   t
and only if the feedback was delivered (S.avail[t']). x_t is shown at predict
time; y_t is never visible at or before t.
"""
import hashlib
import pickle
import numpy as np
from scipy.special import xlogy

from streams import WARMUP


def target(S, task):
    return S.z if task == "reg" else S.lab


def run(model, S, task, t0=0, t1=None, preds=None, y=None, on_step=None):
    y = target(S, task) if y is None else y
    t1 = S.T if t1 is None else t1
    preds = np.zeros(S.T) if preds is None else preds
    for t in range(t0, t1):
        tp = t - 1 - S.delay
        if tp >= 0 and S.avail[tp]:
            model.observe(S.X[tp], y[tp], tp, t)
        preds[t] = model.predict(S.X[t])
        if on_step is not None:
            on_step(t, model)
    return preds


def excess(S, task, preds):
    """Exact excess risk vs. the oracle at each step (noise-free)."""
    if task == "reg":
        return (preds - S.s) ** 2
    p, q = S.p_true, np.clip(preds, 1e-4, 1 - 1e-4)
    return xlogy(p, p / q) + xlogy(1 - p, (1 - p) / (1 - q))


def state_bytes(model):
    return len(pickle.dumps(model, protocol=4))


def phash(preds):
    return hashlib.sha256(np.ascontiguousarray(preds, dtype="<f8").tobytes()).hexdigest()[:16]


def cp_metrics(e, c, nxt, T):
    """Metrics around change point c (segment ends at nxt)."""
    end = min(nxt, c + 1000, T)
    pre_a = max(c - 300, 0)
    pre = float(e[pre_a:c].mean()) if c > pre_a else float("nan")
    tau = 1.5 * pre + 0.02
    cs = np.cumsum(np.insert(e, 0, 0.0))
    rec, ok = end - c, False
    for t in range(c + 29, end):
        if (cs[t + 1] - cs[t - 29]) / 30.0 <= tau:
            rec, ok = t - c, True
            break
    return dict(c=int(c), pre=pre, first100=float(e[c:c + 100].mean()),
                next300=float(e[c + 100:min(c + 400, T)].mean()),
                rec=int(rec), recovered=bool(ok))


def summarize(S, task, preds, model, cks):
    e = excess(S, task, preds)
    ch = sorted(S.changes)
    cps = [cp_metrics(e, c, ch[i + 1] if i + 1 < len(ch) else S.T, S.T)
           for i, c in enumerate(ch)]
    blocks = e[: S.T // 25 * 25].reshape(-1, 25).mean(1)
    return dict(overall=float(e[WARMUP:].mean()), cps=cps,
                blocks=blocks.astype("float32"), state=cks, meta=model.meta(),
                phash=phash(preds))
