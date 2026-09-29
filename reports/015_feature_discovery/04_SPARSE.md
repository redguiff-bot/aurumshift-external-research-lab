# 04 — Régression parcimonieuse, screening MI/CMI, stability selection

## Stability selection (lasso randomisé, blocs de 336 barres, π = 0.7, q̄ ≤ 6 ; borne E[V] ≈ 3.46 — peu informative avec p = 26 et π = 0.7)

| target | primitive | mean stability-selection freq (5 seeds, pooled) | #markets (of 4) freq>=0.7 alone | both train halves >=0.7 | retained as stable main |
|---|---|---|---|---|---|
| y_ret | mag_24 | 0.63 | 0 | no | no |
| y_ret | lrv_24 | 0.51 | 0 | no | yes |
| y_ret | lrng_1 | 0.42 | 0 | no | no |
| y_ret | ret_168h | 0.42 | 0 | no | no |
| y_ret | mag_168 | 0.40 | 0 | no | no |
| y_ret | lpk_24 | 0.37 | 0 | no | no |
| y_ret | ret_24h | 0.31 | 0 | no | no |
| y_ret | tbr_24 | 0.24 | 0 | no | no |
| y_vol | lrv_24 | 1.00 | 4 | yes | yes |
| y_vol | lrv_168 | 1.00 | 4 | yes | yes |
| y_vol | lvol_1 | 0.76 | 1 | no | yes |
| y_vol | dhi_72 | 0.44 | 1 | no | no |
| y_vol | ret_168h | 0.40 | 0 | no | no |
| y_vol | lnt_1 | 0.38 | 0 | no | no |
| y_vol | lrng_1 | 0.36 | 0 | no | no |
| y_vol | mag_168 | 0.34 | 0 | no | no |


Constats (OBSERVED) :
- `y_vol` : `lrv_24` et `lrv_168` sont sélectionnés à fréquence 1.00 dans les 4 marchés pris séparément et dans les deux moitiés du train ; `lvol_1` (0.76) est retenu au pool mais pas marché par marché → **feature stable = volatilité passée** (persistance / retour à la moyenne, connue).
- `y_ret` : seul `lrv_24` passe (via CMI, pas via stabilité : fréquence 0.51) ; `mag_24` (0.63) est proche du seuil. **Pas de feature à fréquence ≥ 0.7** : aucun signal de rendement sparse et stable.
- La CMI gaussienne conditionnelle ne sélectionne que `lrv_24` (et `lrv_168` sur `y_vol`), cohérent avec le lasso.
- Le screening MI kNN (rapport dans `discovery_train_val.json`) n'a pas servi de décision : estimateur bruité à IC ≈ 0.01.

## Baselines held-out (une seule lecture, protocole §8)

| target | model | params | pooled IC held-out | IC 90% CI | OOS R² (mean over markets) | discovered − this (mean, q10) |
|---|---|---|---|---|---|---|
| y_ret | raw_ridge | 26 | +0.0058 | [-0.0115, +0.0227] | -0.281% | +0.0014 (q10 -0.0149) |
| y_ret | lasso | 20 | +0.0061 | [-0.0113, +0.0233] | -0.161% | +0.0011 (q10 -0.0150) |
| y_ret | tree_top8_ridge | 8 | -0.0019 | [-0.0199, +0.0148] | -0.109% | +0.0092 (q10 -0.0065) |
| y_ret | perm_top8_ridge | 8 | +0.0005 | [-0.0170, +0.0177] | -0.255% | +0.0067 (q10 -0.0095) |
| y_ret | gbm_full_ceiling | 1200 | -0.0022 | [-0.0165, +0.0117] | -0.219% | +0.0095 (q10 -0.0051) |
| y_ret | discovered | 6 | +0.0068 | [-0.0111, +0.0257] | -0.074% |  |
| y_vol | raw_ridge | 26 | +0.5848 | [+0.5584, +0.6105] | +34.405% | -0.0208 (q10 -0.0282) |
| y_vol | lasso | 24 | +0.5851 | [+0.5586, +0.6111] | +34.444% | -0.0210 (q10 -0.0279) |
| y_vol | tree_top8_ridge | 8 | +0.5752 | [+0.5479, +0.6019] | +33.695% | -0.0112 (q10 -0.0159) |
| y_vol | perm_top8_ridge | 8 | +0.5784 | [+0.5514, +0.6048] | +33.834% | -0.0143 (q10 -0.0203) |
| y_vol | gbm_full_ceiling | 1200 | +0.5948 | [+0.5680, +0.6202] | +35.963% | -0.0306 (q10 -0.0369) |
| y_vol | discovered | 11 | +0.5642 | [+0.5361, +0.5914] | +32.136% |  |


Lecture (OBSERVED) :
- `y_ret` : toutes les baselines ont un IC held-out indistinguable de 0 (IC 90 % contient 0), R² OOS négatif. **Le plafond GBM (1200 paramètres) n'apporte rien** (−0.002).
- `y_vol` : ridge brut = lasso = 0.585 ; sélection par importance d'arbre ou permutation (8 variables) perd 0.007–0.010 ; le GBM plafond gagne +0.010. **Le lasso à 24/26 coefficients non nuls montre que « sparse » n'aide pas ici : presque tout est utilisé.**
- Les **importances d'arbre et de permutation** listent des variables qui ne sont pas toutes des mains stables : p. ex. pour `y_ret` elles retiennent `ret_72h`, `mag_168`, `ret_1h`, `hod_cos`, `dlo_72` (voir `heldout_results.json › baseline_features`), alors que la stabilité n'en retient aucune → les importances **classent du bruit** quand il n'y a pas de signal (INFERENCE).
