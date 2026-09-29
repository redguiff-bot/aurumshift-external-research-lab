"""Builds markdown tables from results/*.csv into results/tables/*.md (single source for the reports)."""
import os, numpy as np, pandas as pd
R = '../results/'; O = R + 'tables/'; os.makedirs(O, exist_ok=True)
def ms(x):
    x = np.asarray(x, float); x = x[~np.isnan(x)]
    return f"{x.mean():.3f}±{1.96*x.std(ddof=1)/np.sqrt(len(x)):.3f}" if len(x) > 1 else (f"{x.mean():.3f}" if len(x) else 'n/a')
def md(df): 
    df = df.reset_index(); return '| ' + ' | '.join(map(str, df.columns)) + ' |\n|' + '---|' * len(df.columns) + '\n' + '\n'.join('| ' + ' | '.join(map(str, r)) + ' |' for r in df.values)
def w(name, s): open(O + name + '.md', 'w').write(s + '\n')

# ---- static
s = pd.read_csv(R + 'static_raw.csv'); h = s[s.part == 'held']
for tag in ['synthetic', 'breast_cancer']:
    t = h[h.tag == tag].groupby(['base', 'cal']).agg(brier=('brier', ms), logloss=('logloss', ms), ece=('ece', ms), ece_pos=('ece_pos', ms), fcr=('fcr', ms)); w('static_' + tag, md(t))
e = h[h.tag == 'elec2']; w('static_elec2_mean', md(e.groupby(['base', 'cal'])[['brier', 'logloss', 'ece', 'fcr']].mean().round(3)))
ch = e[e.cal.isin(['raw', 'platt', 'temperature', 'isotonic'])].pivot_table(index=['base', 'cal'], columns='chunk', values='ece').round(3); ch.columns = [f'chunk{int(c)}' for c in ch.columns]; w('static_elec2_chunks', md(ch))
v = e[(e.base == 'HGB')]; w('static_elec2_val_vs_held', md(pd.concat([s[(s.tag == 'elec2') & (s.part == 'val')].groupby(['base', 'cal']).ece.mean().rename('ece_val'), e.groupby(['base', 'cal']).ece.mean().rename('ece_held_mean')], axis=1).round(3)))
# paired: calibrated minus raw on synthetic HGB
sy = h[h.tag == 'synthetic'].pivot_table(index=['seed'] if 'seed' in h else h[h.tag == 'synthetic'].index // 1, columns=['base', 'cal'], values='ece') if False else None

# ---- shift
c = pd.read_csv(R + 'shift_cal.csv'); H = c[(c.base == 'HGB') & c.cal.isin(['raw', 'platt', 'isotonic', 'bayes_bin'])]
order = ['iid', 'vol_jump', 'regime_transition', 'feature_shift', 'missing_features', 'stale_features', 'venue_change']
for m in ['ece', 'false_conf_rate', 'brier']:
    t = H.pivot_table(index='shift', columns='cal', values=m, aggfunc=ms) if False else H.groupby(['shift', 'cal'])[m].apply(ms).unstack('cal').reindex(order); w('shift_' + m + '_HGB', md(t))
L = c[(c.base == 'LR') & c.cal.isin(['raw', 'platt'])]; w('shift_ece_fcr_LR', md(L.groupby(['shift', 'cal'])[['ece', 'false_conf_rate']].mean().round(3).unstack('cal').reindex(order)))
# survival verdict (HGB+platt), per seed then aggregated
P = c[(c.base == 'HGB') & (c.cal == 'platt')].pivot_table(index='seed', columns='shift', values=['ece', 'false_conf_rate'])
rows = []
for k in order[1:]:
    ece = P['ece'][k]; fcr = P['false_conf_rate'][k]; f0 = P['false_conf_rate']['iid']
    ok = (ece <= 0.05) & (fcr <= 1.5 * f0 + 0.01)
    rows.append(dict(shift=k, ece_shift=ms(ece), ece_iid=ms(P['ece']['iid']), fcr_shift=ms(fcr), fcr_iid=ms(f0), seeds_surviving=f"{int(ok.sum())}/{len(ok)}", survives='YES' if ok.mean() >= .5 and ece.mean() <= .05 else 'NO'))
sv = pd.DataFrame(rows).set_index('shift'); w('shift_survival', md(sv)); sv.to_csv(R + 'shift_survival.csv')
p = pd.read_csv(R + 'shift_policy.csv')
t = p.groupby(['shift', 'policy'])[['coverage', 'selective_risk', 'random_risk', 'matched_conf_risk', 'bad_avoided', 'good_retained', 'conf_wrong_penalty', 'utility']].mean().round(3).reset_index()
t['shift'] = pd.Categorical(t['shift'], order); t = t.sort_values(['shift', 'policy']).set_index(['shift', 'policy']); w('shift_policy', md(t))
d = pd.read_csv(R + 'shift_auroc.csv').groupby('shift')[['auc_maha', 'auc_ens', 'auc_lowconf', 'auc_flag']].mean().round(3); w('shift_auroc', md(d))
m = pd.read_csv(R + 'shift_monitor.csv').groupby('shift').agg(alarm_rate=('alarm', 'mean'), median_delay_steps=('delay', 'median')).round(2).reindex(order); w('shift_monitor', md(m))
tx = pd.read_csv(R + 'taxonomy_confusion.csv', index_col=0); w('taxonomy', md(tx))
rec = {c_: float(tx.loc[c_, c_]) for c_ in tx.index}; w('taxonomy_recall', ', '.join(f'{k}={v:.2f}' for k, v in rec.items()))
# ---- online
o = pd.read_csv(R + 'online_raw.csv'); scs = ['stationary', 'abrupt_regime', 'gradual_drift', 'vol_jump', 'ELEC2_HGB_h1', 'ELEC2_HGB_h48', 'ELEC2_LR_h1', 'ELEC2_LR_h48']
for sc in scs:
    t = o[o.scenario == sc].groupby('method').agg(ece=('ece', ms), brier=('brier', ms), ece_chunk_worst=('ece_chunk_worst', ms), fcr=('fcr', ms), turnover=('turnover', 'mean'), turnover_raw=('turnover_raw', 'mean'), slope_sd=('slope_sd', 'mean')).round(3); w('online_' + sc, md(t))
w('online_pit_audit', f"pit_ok (all label indices used satisfy j+h<=t) for every PIT-safe method/run: **{bool(o[o.pit_safe].pit_ok.all())}** ({int(o.pit_safe.sum())} runs)")
# online criterion check
rows = []
for sc in ['abrupt_regime', 'gradual_drift', 'vol_jump']:
    a = o[(o.scenario == sc)]; st = a[a.method == 'static_platt'].set_index('seed'); 
    for me in ['window_platt', 'window_iso', 'sgd', 'expand_platt']:
        b = a[a.method == me].set_index('seed'); dlt = st.ece_chunk_worst - b.ece_chunk_worst; lo = dlt.mean() - 1.96 * dlt.std(ddof=1) / np.sqrt(len(dlt))
        rows.append(dict(scenario=sc, method=me, worst_chunk_ece_gain_vs_static=ms(dlt), ci_lower_ge_0_02='YES' if lo >= .02 else 'NO', turnover_ratio_vs_raw=round(float(b.turnover.mean() / b.turnover_raw.mean()), 2)))
w('online_criterion', md(pd.DataFrame(rows).set_index(['scenario', 'method'])))
# ---- conformal
k = pd.read_csv(R + 'conformal_cls.csv'); order_k = ['iid_control', 'ar_stationary', 'gradual_drift', 'abrupt_regime', 'vol_jump', 'ELEC2']
for al in [0.2, 0.1]:
    t = k[k.alpha == al].groupby(['kind', 'method']).agg(coverage=('coverage', ms), min_roll_cov=('min_roll_cov', 'mean'), frac_win_below=('frac_win_below', 'mean'), singleton=('singleton', 'mean'), both_abstain=('both', 'mean'), singleton_acc=('singleton_acc', 'mean')).round(3).reset_index()
    t['kind'] = pd.Categorical(t['kind'], order_k); t = t.sort_values(['kind', 'method']).set_index(['kind', 'method']); w(f'conformal_cls_a{int(al*100)}', md(t))
rg = pd.read_csv(R + 'conformal_reg.csv'); w('conformal_reg', md(rg.groupby(['kind', 'method']).agg(coverage=('coverage', ms), min_roll_cov=('min_roll_cov', 'mean'), frac_win_below=('frac_win_below', 'mean'), width=('width', 'mean')).round(3)))
hs = pd.read_csv(R + 'conformal_housing.csv'); w('conformal_housing', md(hs.groupby('mode').agg(coverage=('coverage', ms), target=('target', 'mean'), width=('width', 'mean')).round(3)))
# conformal criterion: |cov-(1-a)|<=.03 and frac_win_below<=.10 (mean over seeds)
rows = []
for (kd, me, al), g in k.groupby(['kind', 'method', 'alpha']):
    ok = abs(g.coverage.mean() - (1 - al)) <= .03 and g.frac_win_below.mean() <= .10; rows.append(dict(kind=kd, alpha=al, method=me, supported='YES' if ok else 'NO'))
cr = pd.DataFrame(rows).pivot_table(index=['kind', 'alpha'], columns='method', values='supported', aggfunc='first'); w('conformal_criterion', md(cr))
print(open(O + 'shift_survival.md').read()); print(open(O + 'online_criterion.md').read()); print(open(O + 'conformal_criterion.md').read()); print(open(O + 'taxonomy_recall.md').read())
rc = pd.read_csv(R + 'shift_riskcov.csv'); t = rc.groupby(['shift', 'ranking'])[['aurc', 'risk@0.9', 'risk@0.7', 'risk@0.5', 'risk@0.3']].mean().round(3).reset_index()
t['shift'] = pd.Categorical(t['shift'], order); w('riskcov', md(t.sort_values(['shift', 'ranking']).set_index(['shift', 'ranking'])))
