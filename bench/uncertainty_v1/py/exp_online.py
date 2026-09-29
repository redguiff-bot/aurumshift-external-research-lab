"""Q3/§6: static vs incremental (PIT-safe, delayed-label) recalibration; lookahead audit via deliberately leaky variants.
Base model frozen after training on [0:4000]; initial calibration block [4000:7000]; stream = [7000:21000]."""
import os; os.environ['OMP_NUM_THREADS']='1'
from multiprocessing import Pool
import numpy as np, pandas as pd, warnings; warnings.filterwarnings('ignore')
from sklearn.ensemble import HistGradientBoostingClassifier as HGB
from sklearn.linear_model import LogisticRegression
from ulib import *
H = 10; T0 = 7000; N = 21000; TAU = 0.6; SEEDS = 8
KINDS = ['static_platt', 'static_iso', 'expand_platt', 'window_platt', 'window_iso', 'sgd', 'leak_block', 'leak_global']
PIT_SAFE = {'static_platt', 'static_iso', 'expand_platt', 'window_platt', 'window_iso', 'sgd'}
def scenario(kind, x, W, rng):
    n = len(x); t = np.arange(n); xo = x.copy(); on = T0 + 5000
    if kind == 'stationary': p = true_p(x, W)
    elif kind == 'abrupt_regime':
        w2 = W['w'].copy(); w2[:2] *= -1; p = np.where(t < on, true_p(x, W), true_p(x, W, w_override=w2))
    elif kind == 'gradual_drift':
        lam = np.clip((t - T0) / 8000, 0, 1); w1 = W['w']; s0 = true_p(x, W)
        w2 = W['w'].copy(); w2[:2] *= -1; s1 = true_p(x, W, w_override=w2); p = (1 - lam) * s0 + lam * s1
    elif kind == 'vol_jump':
        xo[t >= on] *= 1.5; p = np.where(t < on, true_p(x, W), true_p(x, W, snr=0.35))
    return xo, sample_y(rng, p)
def metrics(q, y, p_raw, slope, chunks=1000):
    ec = [ece_top(q[i:i + chunks], y[i:i + chunks], bins=8) for i in range(0, len(q) - chunks + 1, chunks)]
    d = dec_metrics(q, y, tau=TAU); dq = decisions(q, TAU); dr = decisions(p_raw, TAU)
    return dict(ece=ece_top(q, y), brier=brier(q, y), logloss=logloss(q, y), fcr=d['false_conf_rate'], coverage=d['coverage'], sel_risk=d['selective_risk'],
                ece_chunk_mean=float(np.mean(ec)), ece_chunk_worst=float(np.max(ec)), turnover=turnover(dq), turnover_raw=turnover(dr),
                slope_sd=float(np.nanstd(slope)) if np.isfinite(slope).any() else float('nan'), utility=d['utility'])
def one(s, sc):
    rng = np.random.default_rng(7000 + s); W = make_world(rng); x = gen_x(rng, N); xo, y = scenario(sc, x, W, rng)
    base = HGB(max_iter=300, early_stopping=False, random_state=0).fit(xo[:4000], y[:4000]); p = base.predict_proba(xo)[:, 1]
    out = []
    for k in KINDS:
        q, sl, ok = run_online(p, y, k, T0, h=H)
        r = metrics(q, y[T0:], p[T0:], sl); r.update(seed=s, scenario=sc, method=k, pit_ok=bool(ok), pit_safe=k in PIT_SAFE); out.append(r)
    return out
def elec(h):
    df = pd.read_csv('../data/elec2.csv'); price = df['nswprice']
    df['pm48'] = price.shift(1).rolling(48).mean(); df['dm48'] = df['nswdemand'].shift(1).rolling(48).mean()
    df['p_rel'] = price - df['pm48']; df['d_rel'] = df['nswdemand'] - df['dm48']; df['day'] = df['day'].astype(int); df = df.iloc[48:].reset_index(drop=True)
    F = ['nswprice', 'nswdemand', 'vicprice', 'vicdemand', 'transfer', 'period', 'day', 'p_rel', 'd_rel']
    X = df[F].values[:-1]; y = df['y'].values[1:]; out = []
    for bn, mk in dict(HGB=lambda: HGB(max_iter=300, early_stopping=False, random_state=0), LR=lambda: LogisticRegression(max_iter=1000)).items():
        p = mk().fit(X[:9000], y[:9000]).predict_proba(X)[:, 1]; t0 = 13500
        for k in KINDS:
            q, sl, ok = run_online(p, y, k, t0, h=h, refit=250, W=2000)
            r = metrics(q, y[t0:], p[t0:], sl, chunks=3000); r.update(scenario=f'ELEC2_{bn}_h{h}', method=k, pit_ok=bool(ok), pit_safe=k in PIT_SAFE, seed=0); out.append(r)
    return out
if __name__ == '__main__':
    R = []
    with Pool(4) as P:
        for o in P.starmap(one, [(s, sc) for sc in ['stationary', 'abrupt_regime', 'gradual_drift', 'vol_jump'] for s in range(SEEDS)]): R += o
        for o in P.map(elec, [1, 48]): R += o
    d = pd.DataFrame(R); d.to_csv('../results/online_raw.csv', index=False)
    pd.set_option('display.width', 250)
    print(d.groupby(['scenario', 'method'])[['ece', 'brier', 'ece_chunk_worst', 'fcr', 'turnover', 'turnover_raw', 'slope_sd']].mean().round(3).to_string())
    print('pit_ok all safe methods:', d[d.pit_safe].pit_ok.all())
