"""Q1 static calibration. Synthetic (20 seeds, chronological train/cal/val/held-out) + public: ELEC2 (chronological), breast cancer (random)."""
import json, sys, numpy as np, pandas as pd, warnings; warnings.filterwarnings('ignore')
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import GaussianNB
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import train_test_split
from ulib import *

def base_models():
    return dict(LR=lambda: LogisticRegression(max_iter=1000), GNB=lambda: GaussianNB(),
                HGB=lambda: HistGradientBoostingClassifier(max_iter=300, learning_rate=0.1, max_depth=None, early_stopping=False, random_state=0))
def score_row(p, y, tau=0.6):
    d = dec_metrics(p, y, tau=tau)
    return dict(brier=brier(p, y), logloss=logloss(p, y), ece=ece_top(p, y), ece_pos=ece_pos(p, y),
                fcr=d['false_conf_rate'], fcc=d['false_conf_cond'])

def eval_split(Xtr, ytr, Xc, yc, Xv, yv, Xh, yh, out, tag):
    for bn, mk in base_models().items():
        m = mk().fit(Xtr, ytr); pc, pv, ph = [m.predict_proba(a)[:, 1] for a in (Xc, Xv, Xh)]
        for cn, C in CALIBRATORS.items():
            cal = C().fit(pc, yc)
            for part, (pp, yy) in dict(val=(pv, yv), held=(ph, yh)).items():
                r = score_row(cal(pp), yy); r.update(tag=tag, base=bn, cal=cn, part=part); out.append(r)

def synthetic(seeds=20, ntr=4000, nc=3000, nv=3000, nh=6000):
    out = []
    for s in range(seeds):
        rng = np.random.default_rng(1000 + s); W = make_world(rng); n = ntr + nc + nv + nh
        x = gen_x(rng, n); p = true_p(x, W); y = sample_y(rng, p); a, b, c = ntr, ntr + nc, ntr + nc + nv
        eval_split(x[:a], y[:a], x[a:b], y[a:b], x[b:c], y[b:c], x[c:], y[c:], out, 'synthetic')
        # oracle reference: true probability on held-out
        r = score_row(p[c:], y[c:]); r.update(tag='synthetic', base='ORACLE', cal='true_p', part='held'); out.append(r)
    return out

def elec2():
    df = pd.read_csv('../data/elec2.csv'); price = df['nswprice']
    df['pm48'] = price.shift(1).rolling(48).mean(); df['dm48'] = df['nswdemand'].shift(1).rolling(48).mean()
    df['p_rel'] = price - df['pm48']; df['d_rel'] = df['nswdemand'] - df['dm48']; df['day'] = df['day'].astype(int)
    df = df.iloc[48:].reset_index(drop=True)
    feats = ['nswprice', 'nswdemand', 'vicprice', 'vicdemand', 'transfer', 'period', 'day', 'p_rel', 'd_rel']
    # forecasting task: features at t (past-only) -> label at t+1 (label y_t is itself a function of price up to t; predicting y_t from p_rel would leak the label definition)
    X = df[feats].values[:-1]; y = df['y'].values[1:]; n = len(y)
    a, b, c = 9000, 13500, 18000; out = []
    # chronological: train | cal | val | held-out chunks (held-out = everything after val, in 6 chunks)
    edges = np.linspace(c, n, 7).astype(int)
    for bn, mk in base_models().items():
        m = mk().fit(X[:a], y[:a]); pc = m.predict_proba(X[a:b])[:, 1]; pv = m.predict_proba(X[b:c])[:, 1]
        for cn, C in CALIBRATORS.items():
            cal = C().fit(pc, y[a:b])
            r = score_row(cal(pv), y[b:c]); r.update(tag='elec2', base=bn, cal=cn, part='val', chunk=-1); out.append(r)
            for k in range(6):
                lo, hi = edges[k], edges[k + 1]; ph = m.predict_proba(X[lo:hi])[:, 1]
                r = score_row(cal(ph), y[lo:hi]); r.update(tag='elec2', base=bn, cal=cn, part='held', chunk=k); out.append(r)
    return out

def bcancer(seeds=20):
    X, y = load_breast_cancer(return_X_y=True); out = []
    for s in range(seeds):
        Xa, Xh, ya, yh = train_test_split(X, y, test_size=0.35, stratify=y, random_state=s)
        Xtr, Xr, ytr, yr = train_test_split(Xa, ya, test_size=0.6, stratify=ya, random_state=s)   # 40% train
        Xc, Xv, yc, yv = train_test_split(Xr, yr, test_size=0.5, stratify=yr, random_state=s)
        eval_split(Xtr, ytr, Xc, yc, Xv, yv, Xh, yh, out, 'breast_cancer')
    return out

if __name__ == '__main__':
    res = synthetic() + elec2() + bcancer()
    pd.DataFrame(res).to_csv('../results/static_raw.csv', index=False)
    df = pd.DataFrame(res); h = df[df.part == 'held']
    for tag in ['synthetic', 'breast_cancer']:
        t = h[h.tag == tag].groupby(['base', 'cal'])[['brier', 'logloss', 'ece', 'ece_pos', 'fcr']].agg(['mean']).round(4); print(tag); print(t.to_string())
    e = h[h.tag == 'elec2'].groupby(['base', 'cal'])[['brier', 'logloss', 'ece', 'fcr']].mean().round(4); print('elec2'); print(e.to_string())
