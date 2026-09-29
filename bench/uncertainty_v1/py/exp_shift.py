"""Q2 abstention, Q3 calibration under shift, Q4 taxonomy. Synthetic worlds, 20 seeds.
Splits (chronological, one AR stream/seed): train[0:4000] cal[4000:7000] val[7000:10000] held-out[10000:16000]."""
import os; os.environ['OMP_NUM_THREADS']='1'
import json, sys, numpy as np, pandas as pd, warnings; warnings.filterwarnings('ignore')
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import HistGradientBoostingClassifier as HGB
from ulib import *
SEEDS = 20; TAU = 0.6; COST = 0.2; NE = 8
SHIFTS = ['iid', 'vol_jump', 'regime_transition', 'feature_shift', 'missing_features', 'stale_features', 'venue_change']

def apply_shift(kind, x, W, rng):
    n = len(x); xo = x.copy(); flags = dict(missing=np.zeros(n, bool), stale=np.zeros(n, bool)); p = true_p(x, W)
    if kind == 'vol_jump': xo = 1.5 * x; p = true_p(x, W, snr=0.35)
    elif kind == 'regime_transition':
        w2 = W['w'].copy(); w2[:2] *= -1; p = true_p(x, W, w_override=w2)
    elif kind == 'feature_shift': xo = x.copy(); xo[:, :4] += 1.5; p = true_p(xo, W)
    elif kind == 'missing_features':
        m = rng.random(x.shape) < 0.3; xo = np.where(m, np.nan, x); flags['missing'] = m.any(1)
    elif kind == 'stale_features':
        t = 0
        while t < n:
            L = rng.integers(10, 40)
            if rng.random() < 0.4 and t > 0: xo[t:t + L, :4] = xo[t - 1, :4]
            t += L
        d = np.r_[False, np.all(xo[1:, :4] == xo[:-1, :4], 1)]; flags['stale'] = d
    elif kind == 'venue_change': xo = 0.7 * x + 0.5 + 0.5 * rng.normal(size=x.shape)
    y = sample_y(rng, p); return xo, y, flags

def prep(xo, mu_tr): return np.where(np.isnan(xo), mu_tr, xo)

def fit_all(xtr, ytr, seed):
    base = HGB(max_iter=300, early_stopping=False, random_state=0).fit(xtr, ytr)
    lr = LogisticRegression(max_iter=1000).fit(xtr, ytr)
    rng = np.random.default_rng(seed); ens = []
    for k in range(NE):
        i = rng.integers(0, len(xtr), len(xtr)); ens.append(HGB(max_iter=80, max_depth=3, early_stopping=False, random_state=k).fit(xtr[i], ytr[i]))
    return base, lr, ens

def ens_stats(ens, X):
    P = np.stack([m.predict_proba(X)[:, 1] for m in ens]); return P.mean(0), P.std(0)

def calib_monitor(p, y, tau=TAU, win=300, z=-3.0, h=10):
    """label-based: rolling binomial z-test of accuracy vs claimed confidence on acted rows; labels delayed h. returns first alarm index or None."""
    conf = np.maximum(p, 1 - p); corr = ((p >= .5) == y).astype(float); a = conf >= tau
    idx = np.where(a)[0]; 
    if len(idx) < win: return None
    cc, cr = conf[idx], corr[idx]
    for k in range(win, len(idx) + 1):
        c, r = cc[k - win:k], cr[k - win:k]; var = (c * (1 - c)).sum()
        zz = (r.sum() - c.sum()) / np.sqrt(var + 1e-9)
        if zz < z: return int(idx[k - 1] + h)
    return None

def run_seed(s):
    rng = np.random.default_rng(2000 + s); W = make_world(rng); x = gen_x(rng, 16000); p0 = true_p(x, W); y = sample_y(rng, p0)
    tr, ca, va, te = slice(0, 4000), slice(4000, 7000), slice(7000, 10000), slice(10000, 16000)
    mu_tr = x[tr].mean(0); base, lr, ens = fit_all(x[tr], y[tr], s)
    mu, Si = maha_fit(x[ca]); mc = maha(x[ca], mu, Si); m99 = np.quantile(mc, .99)
    _, sc = ens_stats(ens, x[ca]); s90 = np.quantile(sc, .90)
    cal = {}
    for bn, m in dict(HGB=base, LR=lr).items():
        pc = m.predict_proba(x[ca])[:, 1]
        cal[bn] = {cn: C().fit(pc, y[ca]) for cn, C in CALIBRATORS.items() if cn in ('raw', 'platt', 'isotonic', 'bayes_bin')}
    rows, drows, prow, mrows, rc = [], [], [], [], []
    for k in SHIFTS:
        r2 = np.random.default_rng(3000 + s * 10 + SHIFTS.index(k))
        xo, yt, fl = apply_shift(k, x[te], W, r2); xi = prep(xo, mu_tr)
        for bn, m in dict(HGB=base, LR=lr).items():
            ph_raw = m.predict_proba(xi)[:, 1]
            for cn, c in cal[bn].items():
                q = c(ph_raw); r = dict(seed=s, shift=k, base=bn, cal=cn, brier=brier(q, yt), logloss=logloss(q, yt), ece=ece_top(q, yt), ece_pos=ece_pos(q, yt))
                r.update({kk: v for kk, v in dec_metrics(q, yt, tau=TAU, cost=COST).items()}); rows.append(r)
        # ---- risk-coverage: ranking by raw confidence, calibrated confidence, calibrated confidence minus 2*ensemble std
        praw = base.predict_proba(xi)[:, 1]; qq = cal['HGB']['platt'](praw); _, sd0 = ens_stats(ens, xi); wrong = ((qq >= .5) != yt)
        for rn, sc_ in dict(raw_conf=np.maximum(praw, 1 - praw), cal_conf=np.maximum(qq, 1 - qq), cal_conf_minus_2ens=np.maximum(qq, 1 - qq) - 2 * sd0, random=np.random.default_rng(s).random(len(qq))).items():
            cum = risk_coverage(sc_, wrong); n_ = len(cum)
            rc.append(dict(seed=s, shift=k, ranking=rn, aurc=float(cum.mean()), **{f'risk@{c}': float(cum[int(c * n_) - 1]) for c in (0.9, 0.7, 0.5, 0.3)}))
        # ---- abstention policies on HGB + platt (chosen a-priori simple reference), thresholds from cal
        q = cal['HGB']['platt'](base.predict_proba(xi)[:, 1]); _, sd = ens_stats(ens, xi); mm = maha(xi, mu, Si)
        dflag = fl['missing'] | fl['stale']
        ok_ens = sd <= s90; ok_ood = (mm <= m99) & ~dflag
        pols = dict(P0_none=np.ones(len(q), bool), P1_conf=np.ones(len(q), bool), P2_conf_ens=ok_ens, P3_conf_ood_gap=ok_ood, P4_all=ok_ens & ok_ood)
        for pn, act in pols.items():
            tau = 0.5 if pn == 'P0_none' else TAU
            d = dec_metrics(q, yt, act=act, tau=tau, cost=COST); d.update(seed=s, shift=k, policy=pn)
            # confidence-only ranking at matched coverage (oracle-matched comparator) + random expectation
            conf = np.maximum(q, 1 - q); nk = int(round(d['coverage'] * len(q)))
            if nk > 0:
                sel = np.argsort(-conf)[:nk]; wrong = ((q >= .5) != yt); d['matched_conf_risk'] = float(wrong[sel].mean())
            else: d['matched_conf_risk'] = float('nan')
            d['random_risk'] = d['full_risk']; prow.append(d)
        # ---- detection
        iid_rows = k == 'iid'
        drows.append(dict(seed=s, shift=k, maha_mean=float(mm.mean()), ens_std_mean=float(sd.mean()), conf_mean=float(np.maximum(q, 1 - q).mean()),
                          flag_missing=float(fl['missing'].mean()), flag_stale=float(fl['stale'].mean()), maha_alarm=float((mm > m99).mean()), ens_alarm=float((sd > s90).mean()),
                          _maha=mm if iid_rows else None, _sd=sd if iid_rows else None))
        al = calib_monitor(q, yt); mrows.append(dict(seed=s, shift=k, alarm=al is not None, delay=al))
        if k == 'iid': iid_cache = (mm, sd, q)
    # row-level AUROC vs iid rows
    aur = []
    mm0, sd0, q0 = iid_cache
    for k in SHIFTS[1:]:
        r2 = np.random.default_rng(3000 + s * 10 + SHIFTS.index(k)); xo, yt, fl = apply_shift(k, x[te], W, r2); xi = prep(xo, mu_tr)
        mmk = maha(xi, mu, Si); _, sdk = ens_stats(ens, xi); qk = cal['HGB']['platt'](base.predict_proba(xi)[:, 1])
        lab = np.r_[np.zeros(len(mm0)), np.ones(len(mmk))]
        aur.append(dict(seed=s, shift=k, auc_maha=auroc(np.r_[mm0, mmk], lab), auc_ens=auroc(np.r_[sd0, sdk], lab),
                        auc_lowconf=auroc(-np.r_[np.maximum(q0, 1 - q0), np.maximum(qk, 1 - qk)], lab),
                        auc_flag=auroc(np.r_[np.zeros(len(mm0)), (fl['missing'] | fl['stale']).astype(float)], lab)))
    return rows, prow, drows, mrows, aur, rc

if __name__ == '__main__':
    R, P, D, M, A, RC = [], [], [], [], [], []
    for s in range(SEEDS):
        r, p, d, m, a, rcs = run_seed(s); RC += rcs; R += r; P += p; D += [{k: v for k, v in z.items() if not k.startswith('_')} for z in d]; M += m; A += a; print('seed', s, flush=True)
    for n, v in dict(shift_cal=R, shift_policy=P, shift_detect=D, shift_monitor=M, shift_auroc=A, shift_riskcov=RC).items(): pd.DataFrame(v).to_csv(f'../results/{n}.csv', index=False)
