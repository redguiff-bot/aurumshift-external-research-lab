# 04 — Régression parcimonieuse, screening MI/CMI, stability selection

## Stability selection (lasso randomisé, blocs de 336 barres, π = 0.7, q̄ ≤ 6 ; borne E[V] ≈ 3.46 — peu informative avec p = 26 et π = 0.7)

{{sparse}}

Constats (OBSERVED) :
- `y_vol` : `lrv_24` et `lrv_168` sont sélectionnés à fréquence 1.00 dans les 4 marchés pris séparément et dans les deux moitiés du train ; `lvol_1` (0.76) est retenu au pool mais pas marché par marché → **feature stable = volatilité passée** (persistance / retour à la moyenne, connue).
- `y_ret` : seul `lrv_24` passe (via CMI, pas via stabilité : fréquence 0.51) ; `mag_24` (0.63) est proche du seuil. **Pas de feature à fréquence ≥ 0.7** : aucun signal de rendement sparse et stable.
- La CMI gaussienne conditionnelle ne sélectionne que `lrv_24` (et `lrv_168` sur `y_vol`), cohérent avec le lasso.
- Le screening MI kNN (rapport dans `discovery_train_val.json`) n'a pas servi de décision : estimateur bruité à IC ≈ 0.01.

## Baselines held-out (une seule lecture, protocole §8)

{{heldout_models}}

Lecture (OBSERVED) :
- `y_ret` : toutes les baselines ont un IC held-out indistinguable de 0 (IC 90 % contient 0), R² OOS négatif. **Le plafond GBM (1200 paramètres) n'apporte rien** (−0.002).
- `y_vol` : ridge brut = lasso = 0.585 ; sélection par importance d'arbre ou permutation (8 variables) perd 0.007–0.010 ; le GBM plafond gagne +0.010. **Le lasso à 24/26 coefficients non nuls montre que « sparse » n'aide pas ici : presque tout est utilisé.**
- Les **importances d'arbre et de permutation** listent des variables qui ne sont pas toutes des mains stables : p. ex. pour `y_ret` elles retiennent `ret_72h`, `mag_168`, `ret_1h`, `hod_cos`, `dlo_72` (voir `heldout_results.json › baseline_features`), alors que la stabilité n'en retient aucune → les importances **classent du bruit** quand il n'y a pas de signal (INFERENCE).
