# 01 — Méthodes

Les références sont citées de mémoire (DOCUMENTED_CLAIM, non re-vérifiées en ligne dans cette session). Le comportement réel de chaque
méthode ci-dessous est OBSERVED via le code exécuté dans `bench/feature_discovery_v1/fd/`.

| Méthode | Référence (DOCUMENTED_CLAIM) | Implémentation ici | Rôle |
|---|---|---|---|
| Screening MI kNN | Kraskov-Stögbauer-Grassberger 2004 (via `sklearn.mutual_info_regression`) | `screening.knn_mi` | rapport seulement (bruyant, pas de décision) |
| Information mutuelle conditionnelle | Fleuret 2004 (CMIM), Frenzel-Pompe 2007 | CMI **gaussienne** (copule) = −½ln(1−ρ²_partiel), sélection avant, nulle par décalage circulaire du max | sélection de mains non redondants |
| Orthogonalisation | Gram-Schmidt / résidualisation | `screening.orthogonalise`, corrélation partielle vs baseline | non-redondance |
| Régression parcimonieuse | lasso, Tibshirani 1996 | `sparse.py` (chemin lasso) | baseline linéaire sparse + stability selection |
| Stability selection | Meinshausen-Bühlmann 2010 (lasso randomisé, sous-échantillons) | sous-échantillons **par blocs de 336 barres**, π = 0.7, borne E[V] | stabilité des mains |
| Découverte d'interactions | Lim-Hastie 2015 (glinternet), Bien et al. 2013 (hierNet), Friedman-Popescu 2008 (H) | **toutes** les paires × 3 formes ; corrélation partielle après effets principaux ; nulle du max par décalage circulaire ; même signe sur les 4 marchés | interactions purs sans effet principal inclus |
| Régression symbolique / GP | Koza 1992 ; gplearn 0.4.3 (code lu et exécuté) ; PySR (Cranmer 2023) *non exécuté* (Julia) | `symbolic.py` (gplearn) + simplification gloutonne par score pénalisé | construction de features composites |
| Prédiction invariante | Peters-Bühlmann-Meinshausen 2016 (ICP) ; Arjovsky et al. 2019 (IRM, non implémenté) | Cochran-Q par environnement (HAC) + ICP-lite (F sur moyennes, Levene sur variances) | *diagnostic* d'association invariante |
| Dépistage causal | Pearl ; ordre temporel (les features précèdent la cible par construction) | classe d'évidence `fd/causal.py` | limite les affirmations |
| Multiplicité / surapprentissage de recherche | Harvey-Liu-Zhu 2016 ; White 2000 ; Bailey-López de Prado (PBO/DSR) | Holm sur toute la famille gelée, held-out unique verrouillé, placebo décalé, arène NULL | contrôle du faux positif |
| Baselines | — | ridge (26 primitives), lasso, RF-importance top-8→ridge, permutation-importance (GBM) top-8→ridge, GBM plafond | comparaison |

## Choix de conception (INFERENCE)

- **Décalage circulaire** comme nulle : préserve l'autocorrélation de la cible et des features, détruit seulement l'alignement ; plus honnête qu'une permutation i.i.d. sur des séries financières.
- **Bootstrap circulaire par blocs de 48 barres, temps partagé entre marchés** : conserve la corrélation contemporaine entre cryptos (sinon 9 marchés seraient comptés comme 9 preuves indépendantes).
- **Pénalités** : −0.0005 d'IC par nœud, −0.001 par constante ajustée (pénalité de paramètres), nœuds ≤ 15 ; simplification gloutonne pour éliminer les « hitchhikers » du GP.
- **Le signe est fixé sur train**, jamais sur validation ni held-out.

Verdict par méthode (sans intégration) : voir `09_ADJUDICATION.md`.
