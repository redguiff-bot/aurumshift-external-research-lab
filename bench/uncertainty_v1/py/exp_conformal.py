"""§7 conformal validity: classification sets (LAC on Platt-calibrated probs) + regression intervals, under exchangeable / AR / drift / real ELEC2 data,
plus California-housing covariate shift. Coverage is judged marginally AND in rolling windows; singleton (=act) conditional accuracy is reported because
marginal coverage does not imply decision-level reliability."""
import os; os.environ['OMP_NUM_THREADS']='1'
import numpy as np, pandas as pd, warnings; warnings.filterwarnings('ignore')
from multiprocessing import Pool
from sklearn.ensemble import HistGradientBoostingClassifier as HGBC, HistGradientBoostingRegressor as HGBR
from sklearn.datasets import fetch_california_housing
from ulib import *
H = 10; T0 = 7000; N = 21000; SEEDS = 8
METHODS = ['split', 'rolling', 'weighted', 'aci', 'aci_h0']
def scen(kind, rng):
    W = make_world(rng); x = gen_x(rng, N, phi=0.0 if kind == 'iid_control' else 0.7); t = np.arange(N); on = T0 + 5000
    if kind in ('iid_control', 'ar_stationary'): p = true_p(x, W)
    elif kind == 'abrupt_regime':
        w2 = W['w'].copy(); w2[:2] *= -1; p = np.where(t < on, true_p(x, W), true_p(x, W, w_override=w2))
    elif kind == 'gradual_drift':
        lam = np.clip((t - T0) / 8000, 0, 1); w2 = W['w'].copy(); w2[:2] *= -1; p = (1 - lam) * true_p(x, W) + lam * true_p(x, W, w_override=w2)
    elif kind == 'vol_jump':
        p = np.where(t < on, true_p(x, W), true_p(x, W, snr=0.35)); x = x.copy(); x[t >= on] *= 1.5
    return x, sample_y(rng, p)
def cls_job(a):
    kind, s, alphas = a; rng = np.random.default_rng(9000 + s); x, y = scen(kind, rng)
    m = HGBC(max_iter=300, early_stopping=False, random_state=0).fit(x[:4000], y[:4000]); p = m.predict_proba(x)[:, 1]
    q = Platt().fit(p[4000:5500], y[4000:5500])(p); out = []
    for al in alphas:
        for me in METHODS:
            i0, i1, cov = conformal_stream(q, y, T0, alpha=al, method=me, h=H, ncal0=1500)
            r = set_stats(i0, i1, y[T0:], cov, al); r.update(kind=kind, seed=s, alpha=al, method=me); out.append(r)
    return out
def elec_job(al):
    df = pd.read_csv('../data/elec2.csv'); price = df['nswprice']; df['pm48'] = price.shift(1).rolling(48).mean(); df['dm48'] = df['nswdemand'].shift(1).rolling(48).mean()
    df['p_rel'] = price - df['pm48']; df['d_rel'] = df['nswdemand'] - df['dm48']; df['day'] = df['day'].astype(int); df = df.iloc[48:].reset_index(drop=True)
    F = ['nswprice', 'nswdemand', 'vicprice', 'vicdemand', 'transfer', 'period', 'day', 'p_rel', 'd_rel']; X = df[F].values[:-1]; y = df['y'].values[1:]
    p = HGBC(max_iter=300, early_stopping=False, random_state=0).fit(X[:9000], y[:9000]).predict_proba(X)[:, 1]
    q = Platt().fit(p[9000:11500], y[9000:11500])(p); t0 = 13500; out = []
    for me in METHODS:
        i0, i1, cov = conformal_stream(q, y, t0, alpha=al, method=me, h=1, W=2000, ncal0=2000); r = set_stats(i0, i1, y[t0:], cov, al, win=1000); r.update(kind='ELEC2', seed=0, alpha=al, method=me); out.append(r)
    return out
def reg_job(a):
    kind, s = a; rng = np.random.default_rng(9500 + s); W = make_world(rng); x = gen_x(rng, N); t = np.arange(N); on = T0 + 5000
    mu = x[:, :4] @ W['w'] + W['g'] * x[:, 0] * x[:, 1]; sig = np.where((t >= on) & (kind == 'vol_jump'), 3.0, 1.0)
    if kind == 'vol_ramp': sig = 1 + 2 * np.clip((t - T0) / 8000, 0, 1)
    y = mu + sig * rng.normal(size=N); m = HGBR(max_iter=200, early_stopping=False, random_state=0).fit(x[:4000], y[:4000]); pred = m.predict(x); out = []
    for me in ['split', 'rolling', 'aci']:
        half, cov = conformal_reg_stream(pred, y, T0, alpha=0.2, method=me, h=H, ncal0=1500); roll = np.convolve(cov.astype(float), np.ones(500) / 500, 'valid')
        out.append(dict(kind='reg_' + kind, seed=s, method=me, coverage=float(cov.mean()), min_roll_cov=float(roll.min()), width=float(np.mean(half)), frac_win_below=float((roll < .75).mean())))
    return out
def housing():
    d = fetch_california_housing(); X, y = d.data, d.target; rng = np.random.default_rng(0); out = []
    for mode in ['random_split(exchangeable)', 'covariate_shift(train/cal MedInc<=P60, test MedInc>P60)']:
        for rep in range(10):
            r = np.random.default_rng(rep); idx = r.permutation(len(y))
            if mode.startswith('random'): a, b, c = idx[:8000], idx[8000:12000], idx[12000:]
            else:
                lo = idx[X[idx, 0] <= np.quantile(X[:, 0], .6)]; hi = idx[X[idx, 0] > np.quantile(X[:, 0], .6)]; a, b, c = lo[:6000], lo[6000:9000], hi
            m = HGBR(max_iter=200, random_state=0).fit(X[a], y[a]); rc = np.abs(y[b] - m.predict(X[b])); n = len(rc); k = int(np.ceil((n + 1) * .8)); qh = np.sort(rc)[min(k, n) - 1]
            cov = np.abs(y[c] - m.predict(X[c])) <= qh
            out.append(dict(kind='housing', mode=mode, rep=rep, coverage=float(cov.mean()), target=0.8, width=float(2 * qh)))
    return out
if __name__ == '__main__':
    jobs = [(k, s, [0.2, 0.1] if k in ('ar_stationary', 'abrupt_regime') else [0.2]) for k in ['iid_control', 'ar_stationary', 'abrupt_regime', 'gradual_drift', 'vol_jump'] for s in range(SEEDS)]
    with Pool(4) as P:
        C = [r for o in P.map(cls_job, jobs) for r in o]; E = [r for al in (0.2, 0.1) for r in elec_job(al)]
        Rg = [r for o in P.map(reg_job, [(k, s) for k in ['stationary', 'vol_jump', 'vol_ramp'] for s in range(SEEDS)]) for r in o]
    pd.DataFrame(C + E).to_csv('../results/conformal_cls.csv', index=False); pd.DataFrame(Rg).to_csv('../results/conformal_reg.csv', index=False); pd.DataFrame(housing()).to_csv('../results/conformal_housing.csv', index=False)
    pd.set_option('display.width', 250); d = pd.DataFrame(C + E)
    print(d.groupby(['kind', 'alpha', 'method'])[['coverage', 'min_roll_cov', 'frac_win_below', 'singleton', 'both', 'empty', 'singleton_acc']].mean().round(3).to_string())
    print(pd.DataFrame(Rg).groupby(['kind', 'method'])[['coverage', 'min_roll_cov', 'frac_win_below', 'width']].mean().round(3))
    print(pd.DataFrame(housing()).groupby('mode')[['coverage', 'width']].mean().round(3))
