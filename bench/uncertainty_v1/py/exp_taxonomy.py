"""Q4: can uncertainty signals separate NO_SIGNAL / DATA_GAP / MODEL_UNCERTAINTY / OUT_OF_DISTRIBUTION (+ SIGNAL)?
Cause labels are constructed by the generator (so this is a controlled test, not proof for real markets). 20 seeds."""
import numpy as np, pandas as pd, warnings; warnings.filterwarnings('ignore')
from sklearn.ensemble import HistGradientBoostingClassifier as HGB
from ulib import *
CL = ['SIGNAL', 'NO_SIGNAL', 'DATA_GAP', 'MODEL_UNCERTAINTY', 'OOD']
N = 1200
def run(s):
    rng = np.random.default_rng(5000 + s); W = make_world(rng); x = gen_x(rng, 24000); p0 = true_p(x, W); y = sample_y(rng, p0)
    sparse = (x[:, 0] > 1) & (x[:, 1] > 1) & (x[:, 7] <= 1)
    tr = np.arange(0, 6000); keep = ~sparse[tr] | (rng.random(len(tr)) < 0.08); tr = tr[keep]        # thin the sparse region in TRAIN only
    ca = slice(6000, 10000); te = np.arange(10000, 24000); mu_tr = x[tr].mean(0)
    base = HGB(max_iter=200, early_stopping=False, random_state=0).fit(x[tr], y[tr])
    ens = [HGB(max_iter=80, max_depth=3, early_stopping=False, random_state=k).fit(x[tr][i], y[tr][i]) for k, i in enumerate([rng.integers(0, len(tr), len(tr)) for _ in range(8)])]
    cal = Platt().fit(base.predict_proba(x[ca])[:, 1], y[ca]); mu, Si = maha_fit(x[ca])
    cs = np.stack([m.predict_proba(x[ca])[:, 1] for m in ens]).std(0); m99 = np.quantile(maha(x[ca], mu, Si), .99); s90 = np.quantile(cs, .90)
    # pools from the test stream
    gate = x[te, 7] > 1; sp = sparse[te]; sig = te[~gate & ~sp]; nos = te[gate]; mun = te[sp]
    pick = lambda a: rng.choice(a, min(N, len(a)), replace=False)
    pools = {'SIGNAL': (pick(sig), 'none'), 'NO_SIGNAL': (pick(nos), 'none'), 'MODEL_UNCERTAINTY': (pick(mun), 'none'),
             'DATA_GAP': (pick(sig), 'gap'), 'OOD': (pick(sig), 'ood')}
    rows = []
    for c, (idx, mode) in pools.items():
        xo = x[idx].copy(); miss = np.zeros(len(idx), bool); stale = np.zeros(len(idx), bool)
        if mode == 'gap':
            h = len(idx) // 2; m = rng.random((h, x.shape[1])) < 0.3; xo[:h][m] = np.nan; miss[:h] = m.any(1)
            xo[h:, :4] = x[idx[h], :4]        # stalled feed: frozen values
        if mode == 'ood': xo = 1.5 * xo; xo[:, :4] += 3.0
        stale = np.r_[False, np.all(xo[1:, :4] == xo[:-1, :4], 1)]    # data-derived exact-repeat flag
        xi = np.where(np.isnan(xo), mu_tr, xo); q = cal(base.predict_proba(xi)[:, 1]); P = np.stack([m.predict_proba(xi)[:, 1] for m in ens]); sd = P.std(0)
        mm = maha(xi, mu, Si)
        # rule cascade (thresholds from calibration data only)
        pred = np.full(len(idx), 'SIGNAL', object)
        pred[np.abs(q - .5) < 0.08] = 'NO_SIGNAL'
        pred[sd > s90] = 'MODEL_UNCERTAINTY'; pred[mm > m99] = 'OOD'
        pred[miss | stale] = 'DATA_GAP'
        for pp in pred: rows.append(dict(seed=s, truth=c, pred=pp))
    return rows
if __name__ == '__main__':
    R = []
    for s in range(20): R += run(s)
    d = pd.DataFrame(R); d.to_csv('../results/taxonomy_raw.csv', index=False)
    cm = pd.crosstab(d.truth, d.pred, normalize='index').reindex(index=CL, columns=CL).fillna(0).round(3); print(cm)
    cm.to_csv('../results/taxonomy_confusion.csv')
