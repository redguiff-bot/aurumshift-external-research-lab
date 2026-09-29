#### y_ret / C01 — `(ret_24h * wknd)` (signe -1)

- **Formule (préfixe)** : `mul(ret_24h, wknd)` ; nœuds 3, constantes 0
- **Variables** : `ret_24h` = ln(C_t/C_{t-24}) [log-return]; `wknd` = 1[day_of_week in {Sat,Sun}] [dimensionless {0,1}]
- **Unités** : entrées dimensionless rolling z-scores (720-bar window, clipped +-5) of the listed primitives (calendar features unscaled) ; sortie dimensionless, standardised by train mean/sd; monotone rank-signal, not a calibrated forecast ; cible : forward 4h log-return divided by (168h hourly vol x sqrt 4): dimensionless, in units of forward volatility
- **Entrées requises** : champs ['close', 'timestamp'] ; lookback primitif max 24 barres + fenêtre de standardisation 720 → historique minimal 744 barres 1h fermées
- **Monotonie attendue** : `ret_24h` decreasing; `wknd` non-monotone/interaction-dependent (49% of rows increase)
- **Ablation (Δ IC validation en neutralisant la variable)** : `ret_24h` +0.0296; `wknd` +0.0296
- **Modes de défaillance** :
  - uses calendar features: fragile to changes in market-hours structure / DST-free UTC assumption
  - inputs clipped at +-5 sd: saturates in extreme moves (crashes/squeezes), where the relation is unverified
  - relationship estimated on 2021-2024 crypto spot only; regime change (e.g. market-structure or fee change) can invalidate it
  - data gaps (exchange maintenance) make 'N bars' lookbacks span more than N hours
- **Forward-safety** : n'utilise que des barres ≤ t (vérifié : tests/test_forward_safety.py (prefix-invariance + future-scramble)) ; horizon de label 4 barres ; any downstream CV must embargo >= label horizon between train and test rows

#### y_vol / C01 — `(ret_72h * sgn(mag_168))` (signe -1)

- **Formule (préfixe)** : `mul(ret_72h, sgn(mag_168))` ; nœuds 4, constantes 0
- **Variables** : `mag_168` = ln C_t - ln mean_{i<168} C_{t-i} [log-distance]; `ret_72h` = ln(C_t/C_{t-72}) [log-return]
- **Unités** : entrées dimensionless rolling z-scores (720-bar window, clipped +-5) of the listed primitives (calendar features unscaled) ; sortie dimensionless, standardised by train mean/sd; monotone rank-signal, not a calibrated forecast ; cible : log(forward 24h realised vol / trailing 24h realised vol): dimensionless log-ratio
- **Entrées requises** : champs ['close'] ; lookback primitif max 168 barres + fenêtre de standardisation 720 → historique minimal 888 barres 1h fermées
- **Monotonie attendue** : `mag_168` non-monotone/interaction-dependent (62% of rows increase); `ret_72h` non-monotone/interaction-dependent (49% of rows increase)
- **Ablation (Δ IC validation en neutralisant la variable)** : `mag_168` +0.1222; `ret_72h` +0.1222
- **Modes de défaillance** :
  - inputs clipped at +-5 sd: saturates in extreme moves (crashes/squeezes), where the relation is unverified
  - relationship estimated on 2021-2024 crypto spot only; regime change (e.g. market-structure or fee change) can invalidate it
  - data gaps (exchange maintenance) make 'N bars' lookbacks span more than N hours
- **Forward-safety** : n'utilise que des barres ≤ t (vérifié : tests/test_forward_safety.py (prefix-invariance + future-scramble)) ; horizon de label 24 barres ; any downstream CV must embargo >= label horizon between train and test rows

