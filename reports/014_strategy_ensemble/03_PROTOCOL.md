# 03 — Protocole (pré-enregistré avant le run held-out)

Mode : EXTERNAL_RESEARCH_ONLY · aucun code privé AurumShift · aucune intégration. Données **synthétiques uniquement** (aucune donnée de marché réelle).
Labels : PROVEN · OBSERVED · DOCUMENTED_CLAIM · INFERENCE · UNKNOWN.

## Tâche
Chaque tour t : K = 10 experts émettent (ou non) une prévision de probabilité `p_i,t` d'un événement binaire `y_t`. Le combineur choisit des poids sur les experts **éveillés** et prédit `ŷ_t = Σ w_i p_i`. Les combineurs apprennent de `y_t` et des seuls scores **observés**. Métrique de réalisation : erreur au vrai `q_t` (`(ŷ−q)²`, espérance du Brier moins le bruit de Bayes → variance faible, appariée par graine).

## Processus générateur
Logit latent `a_t` AR(1). Prévision d'un expert : `logit p_i = a_t + sd_i(régime)·bruit`, avec corrélation intra-cluster ρ (clones). Régimes A/B/C (dwell moyen ~80) + régime R rare (bouffées ~25 tours). `sd = ∞` ⇒ expert structurellement invalide dans ce régime.

## Sémantique des statuts (par expert et par tour)
| Statut | Prévoit ? | Dans le mélange ? | Feedback ? | Mise à jour du combineur |
|---|---|---|---|---|
| ACTIVE | oui | oui | oui | oui (perte observée) |
| INACTIVE (régime / pas né / retiré) | non | non | non | **aucune** |
| ABSTAIN | non | non | non | **aucune** |
| DATA_GAP | non | non | non | **aucune** |
| NO_EVIDENCE | oui | oui | **non** | **aucune** |
| perte élevée observée | (ACTIVE) | oui | oui | oui — c'est la seule source de « négatif » |

Ablations (contrôles de sémantique, pénalité 0,5 sur le Brier) : `*_INACTIVE_NEG`, `*_MISSING_NEG`; contrôles de mise à jour : `EG_UNCENTRED`, `SLEEP_UNCENTRED`.

## Scénarios (11)
S0 base propre · S1 lacunes/abstentions/preuve manquante (12 % gap, 30 % sans feedback, 8 % abstention) · S2 changements de leadership (permutation trend/meanrev, puis généraliste) · S3 récurrence de régimes (cycle A→B→C, spécialistes dormants 2/3 du temps) · S4a nouvel expert excellent à T/2 · S4b nouvel expert mauvais à T/2 · S5 expert retiré puis revenu dégradé · S6 clones corrélés (4 clones ρ=0,95, bons puis mauvais) · S7 sous-performance temporaire (fenêtre 2000–3000) · S8 spécialiste de régime rare · S9 longue lacune de données (1250 tours) d'une étoile.
T = 5000. Contexte observable = étiquette de régime corrompue à 10 %.

## Splits
Tuning : graines 100–109. Held-out : graines 1000–1029 (30). Les hyperparamètres sont choisis **une fois par méthode, tous scénarios confondus** (moyenne du nrm sur scénarios) sur le tuning uniquement, puis gelés. Deux tours de grille (le tour 1 a montré des optimums en bord de grille → tour 2 avec grilles étendues, toujours tuning seul).
`nrm = (mse_m − mse_ORACLE)/(mse_EQUAL − mse_ORACLE)` : 0 = oracle (poids à variance inverse connue, référence non candidate), 1 = poids égaux.

## Règles d'adjudication (fixées avant le held-out ; implémentées dans `bench/ensemble_v1/py/adjudicate.py`)
Marges : δ = 0,05 (écart de moyenne nrm), δ_R = 0,15 (écart pire-cas au meilleur par scénario).
Une méthode est **ROBUSTE** si toutes les portes passent :
- `gap_ok` : max_s [nrm_m,s − min_m' nrm_m',s] ≤ δ_R (m' parmi baselines + candidats non bandit).
- `G_noworse` : jamais significativement pire que EQUAL (nrm>1 et IC 95 % apparié > 0) dans un scénario.
- `G_new` : part de poids du nouvel expert (S4a, tours T/2+200..300) ≥ 50 % de la part oracle, et nrm(S4b) ≤ 1.
- `G_rare` : sur les occurrences ≥3 du régime rare (S8), nrm ≤ 0,5 et part du spécialiste ≥ 50 % de la part oracle.
- `G_under` : après la fenêtre de sous-performance (S7), nrm(blocs 60–66) − nrm(avant, blocs 30–40) ≤ 0,15.
- `G_dorm` : après la lacune (S9) même critère ≤ 0,15 ET nrm de ré-entrée de régime (S3, 50 premiers tours) ≤ 0,6.

Arbre de décision :
1. Spearman(nrm tuning, nrm held-out) entre méthodes < 0,6 ⇒ STUDY_INCONCLUSIVE.
2. Aucune méthode robuste ⇒ NO_ROBUST_ENSEMBLE_METHOD.
3. Aucun candidat robuste, ou meilleure baseline robuste à ≤ δ du meilleur candidat robuste (moyenne nrm) ⇒ STATIC_OR_EWMA_SUFFICIENT.
4. Sinon m* = meilleur candidat robuste (moyenne nrm). Si un membre du cœur sleeping (SLEEP_HEDGE, EG, BMA, SLEEP_FLOOR) robuste est à ≤ δ de m* et (écart pire-cas de m* ≤ δ ou < 2 familles « nécessaires ») ⇒ SLEEPING_EXPERT_REFERENCE_SUPPORTED.
5. Sinon, ≥ 2 familles (cœur, tracking, contexte, diversité) chacune « nécessaire » (bat toutes les autres familles et baselines de > δ, IC 95 % apparié, dans ≥ 1 scénario) ⇒ MULTIPLE_ENSEMBLE_METHODS_SUPPORTED ; sinon SLEEPING_EXPERT_REFERENCE_SUPPORTED.
Toute déviation ultérieure à ces règles sera étiquetée **post-hoc** dans 09.

Les bandits (EXP3, ε-greedy) sont des comparaisons uniquement et n'entrent pas dans la décision.
