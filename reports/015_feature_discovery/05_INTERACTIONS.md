# 05 — Interactions et cartes d'interprétabilité des formules gelées

Recherche exhaustive : 26 primitives → 325 paires × 3 formes (`a·b`, `a·sgn b`, `b·sgn a`) = 975 candidats par seed ; corrélation partielle
après effets principaux (espace gaussien), seuil = quantile 95 % du max sous décalage circulaire (50 nulles), même signe sur les 4 marchés de découverte.

## Modèle vs additif (validation, train seul)

| target | GBM depth (1 = additive) | validation IC | validation R² |
|---|---|---|---|
| y_ret | depth1 | +0.0116 | +0.082% |
| y_ret | depth3 | +0.0173 | -0.223% |
| y_vol | depth1 | +0.5145 | +24.393% |
| y_vol | depth3 | +0.5710 | +32.352% |


`y_vol` : passer d'un GBM additif (profondeur 1) à profondeur 3 fait gagner +0.057 d'IC et +8 points de R² en validation → **il y a de la structure non additive** sur `y_vol`. `y_ret` : IC ≈ 0.01–0.02, R² < 0 → rien d'exploitable.

## Formules gelées (après consolidation ≥ 60 % des seeds, |ρ| < 0.80)

| target | id | expression | kind | nodes | constants | seed freq | IC train | IC val (mean 4 mkts) | val boot p | val partial IC vs mains-ridge | sign fixed on train | family |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| y_ret | C01 | `mul(ret_24h, wknd)` | interaction | 3 | 0 | 0.6 | -0.0422 | +0.0301 | 0.003 | +0.0158 | -1.0 | 3 members |
| y_vol | C01 | `mul(ret_72h, sgn(mag_168))` | interaction | 4 | 0 | 1.0 | -0.0777 | +0.1227 | 0.003 | -0.0665 | -1.0 | 5 members |


Note : « IC train » est mesuré sur l'expression brute avant application du signe (fixé sur train) ; c'est pourquoi il est négatif alors que l'IC val (signé) est positif.

## Résultats held-out (lecture unique)

| target | id | expression | kind | nodes | seed freq | IC val | IC held-out | IC 90% CI | markets IC>0 | unseen IC>0 | p_Holm | STABLE | partial IC vs raw-ridge | p_Holm partial | NON-REDUNDANT | evidence class |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| y_ret | C01 | `mul(ret_24h, wknd)` | interaction | 3 | 0.6 | +0.0301 | +0.0120 | [-0.0038, +0.0277] | 1.00 | 5/5 | 0.107 | no | +0.0079 | 0.431 | no | NONE |
| y_vol | C01 | `mul(ret_72h, sgn(mag_168))` | interaction | 4 | 1.0 | +0.1227 | +0.1043 | [+0.0729, +0.1364] | 1.00 | 5/5 | 0.001 | yes | -0.0349 | 0.959 | no | PREDICTIVE |


IC par marché (tous positifs pour les deux formules) :

| target | id | BTCUSDT | ETHUSDT | BNBUSDT | SOLUSDT | XRPUSDT | ADAUSDT | DOGEUSDT | LINKUSDT | PAXGUSDT |
|---|---|---|---|---|---|---|---|---|---|---|
| y_ret | C01 | +0.014 | +0.016 | +0.001 | +0.002 | +0.017 | +0.022 | +0.018 | +0.013 | +0.004 |
| y_vol | C01 | +0.082 | +0.118 | +0.118 | +0.112 | +0.097 | +0.130 | +0.081 | +0.104 | +0.097 |


- `y_vol / C01` : **stable** (p_Holm 0.001, 9/9 marchés, 5/5 jamais vus), IC 0.104 (val 0.123 : légère érosion).
- Mais **non redondante : non** — corrélation partielle après le ridge sur 26 primitives = −0.035 (p_Holm 0.96) ; à la validation elle était déjà de −0.067 (le protocole n'avait pas de gate là-dessus, voir 02 §12.5). La formule (`ret_72h` × signe de l'écart à la moyenne 168 h) est en pratique une **magnitude de mouvement directionnel récent** ; l'information de volatilité récente est déjà dans les baselines.
- `y_ret / C01` : IC +0.012 positif sur 9/9 marchés mais **non significatif** après Holm (p 0.107) et sans valeur incrémentale (partiel +0.008, p_Holm 0.43). Statut : **non stable** — on ne le compte pas.

## Cartes d'interprétabilité (formule, unités, entrées, monotonie, défaillances, forward-safety)

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



**Hitchhikers** : l'ablation d'une variable détruit tout l'IC (Δ ≈ IC entier) : aucune variable superflue (INFERENCE : normal pour un produit de deux termes, où neutraliser l'un annule la formule ; l'ablation ne dit pas laquelle est « utile »).
