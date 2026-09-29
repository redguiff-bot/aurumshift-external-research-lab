# 05 — Interactions et cartes d'interprétabilité des formules gelées

Recherche exhaustive : 26 primitives → 325 paires × 3 formes (`a·b`, `a·sgn b`, `b·sgn a`) = 975 candidats par seed ; corrélation partielle
après effets principaux (espace gaussien), seuil = quantile 95 % du max sous décalage circulaire (50 nulles), même signe sur les 4 marchés de découverte.

## Modèle vs additif (validation, train seul)

{{gbm_val}}

`y_vol` : passer d'un GBM additif (profondeur 1) à profondeur 3 fait gagner +0.057 d'IC et +8 points de R² en validation → **il y a de la structure non additive** sur `y_vol`. `y_ret` : IC ≈ 0.01–0.02, R² < 0 → rien d'exploitable.

## Formules gelées (après consolidation ≥ 60 % des seeds, |ρ| < 0.80)

{{frozen}}

Note : « IC train » est mesuré sur l'expression brute avant application du signe (fixé sur train) ; c'est pourquoi il est négatif alors que l'IC val (signé) est positif.

## Résultats held-out (lecture unique)

{{heldout_candidates}}

IC par marché (tous positifs pour les deux formules) :

{{heldout_by_market}}

- `y_vol / C01` : **stable** (p_Holm 0.001, 9/9 marchés, 5/5 jamais vus), IC 0.104 (val 0.123 : légère érosion).
- Mais **non redondante : non** — corrélation partielle après le ridge sur 26 primitives = −0.035 (p_Holm 0.96) ; à la validation elle était déjà de −0.067 (le protocole n'avait pas de gate là-dessus, voir 02 §12.5). La formule (`ret_72h` × signe de l'écart à la moyenne 168 h) est en pratique une **magnitude de mouvement directionnel récent** ; l'information de volatilité récente est déjà dans les baselines.
- `y_ret / C01` : IC +0.012 positif sur 9/9 marchés mais **non significatif** après Holm (p 0.107) et sans valeur incrémentale (partiel +0.008, p_Holm 0.43). Statut : **non stable** — on ne le compte pas.

## Cartes d'interprétabilité (formule, unités, entrées, monotonie, défaillances, forward-safety)

{{cards}}

**Hitchhikers** : l'ablation d'une variable détruit tout l'IC (Δ ≈ IC entier) : aucune variable superflue (INFERENCE : normal pour un produit de deux termes, où neutraliser l'un annule la formule ; l'ablation ne dit pas laquelle est « utile »).
