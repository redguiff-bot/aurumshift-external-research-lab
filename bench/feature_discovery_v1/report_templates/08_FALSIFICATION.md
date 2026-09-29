# 08 — Falsification

## 8.1 Arène synthétique (vérité connue) — le même pipeline, 40 + 40 réplications, graines 1000–1039 (jamais vues en développement)

Scénarios : `NULL` (y sans signal) et `MIXED` (5 composantes plantées de R² ≈ 0.6 % chacune : linéaire, interaction pure, non-linéaire pure, spécifique à 2 marchés de découverte sur 3, décroissante vers 0 avant le held-out ; + quasi-doublon de la composante linéaire). 3 marchés de découverte + 3 jamais vus, mêmes règles STABLE que le réel.

{{arena}}

- **FWER sous H0 = 0/40** (IC 95 % de Clopper-Pearson unilatéral ≈ [0, 0.07]) : aucune formule stable sur du bruit. Des candidats *gelés* sous H0 : 0/40 (le filtre validation+consolidation suffit ici). **Des « mains » faux positifs** (variable de bruit sélectionnée par stability selection) apparaissent dans 15 % des réplications NULL (INFERENCE : la borne E[V] du protocole n'est pas garantie sous la dépendance temporelle ; les mains ne comptent pas comme features découvertes).
- **Puissance** : linéaire 100 %, interaction pure 100 %, non-linéaire pure 27.5 % (limite du GP).
- **Composantes non persistantes** (spécifique à des marchés, décroissante) : jamais déclarées stables → les exigences « marchés jamais vus » et « held-out temporel » filtrent effectivement le surajustement au régime.
- **Non-redondance** : le doublon quasi identique est sélectionné avec son jumeau dans 2.5 % des réplications seulement.
- Condition de validité du protocole (§9) : FWER ≤ 0.10 **et** puissance linéaire ≥ 0.80 → **satisfaite** ; le verdict n'est pas `STUDY_INCONCLUSIVE`.

## 8.2 Forward-safety (PROVEN par tests)
`tests/test_forward_safety.py` (5 tests, passés) : invariance au préfixe (features à t identiques calculées sur les données ≤ t ou sur toute la série), invariance à la manipulation du futur, absence de fuite de la cible dans les features (|corr| < 0.1), évaluateur d'expressions, ordre/embargo des splits.

## 8.3 Absence de sélection sur held-out
Pré-enregistrement commité avant runs ; `FROZEN.json` haché (`digest` recalculé et comparé avant le held-out) ; `heldout_lock.json` empêche toute seconde lecture ; les marchés jamais vus n'apparaissent dans aucun fit. Déviations listées : `02_PROTOCOL.md §12`.

## 8.4 Placebo sur données réelles
Voir 06 (0/20 et 1/20 au niveau 5 %).

## 8.5 Ce qui n'a pas pu être falsifié
Les coûts de transaction et l'exécution ne sont pas modélisés : un IC de 0.01 (`y_ret`) ne dit rien sur un PnL net (UNKNOWN).
