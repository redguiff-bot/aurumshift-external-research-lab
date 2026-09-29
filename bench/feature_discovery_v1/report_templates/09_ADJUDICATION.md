# 09 — Adjudication

## Bloc final

```
FEATURES_DISCOVERED={{FEATURES_DISCOVERED}}
FEATURES_HELDOUT_STABLE={{FEATURES_HELDOUT_STABLE}}
SYMBOLIC_EXPRESSIONS_STABLE={{SYMBOLIC_EXPRESSIONS_STABLE}}
NONREDUNDANT_FEATURES={{NONREDUNDANT_FEATURES}}

CAUSAL_IDENTIFIED_COUNT={{CAUSAL_IDENTIFIED_COUNT}}

COMPLEXITY_JUSTIFIED={{COMPLEXITY_JUSTIFIED}}

FINAL_VERDICT={{FINAL_VERDICT}}
```

Règle mécanique (protocole §10, `scripts/06_adjudicate.py`) : arène valide ✔ ; NON-REDONDANTES = 0 < 3 → pas `REFERENCE_SUPPORTED` ; ≥ 1 formule stable (1) → `LIMITED_STABLE_FEATURES_SUPPORTED`.

**Réserve d'adjudication (INFERENCE)** : le label `LIMITED_STABLE_FEATURES_SUPPORTED` couvre ici une seule formule stable *mais redondante* et *sans bénéfice de complexité*. Une lecture stricte de « feature nouvelle utile » donnerait `NO_STABLE_NEW_FEATURES`. Le verdict rapporté est celui de la règle pré-enregistrée ; la lecture pratique est : **rien à ajouter au jeu de primitives brutes**.

## Détail COMPLEXITY_JUSTIFIED
Par cible : `y_ret` = NO, `y_vol` = NO (protocole §8). Tableau en 04.

## Méthodes : ADOPT / ADAPT / PARK / REJECT (externes, sans compatibilité AurumShift affirmée)

| Méthode | Décision | Raison (preuve) |
|---|---|---|
| Protocole gelé + verrou held-out + marchés jamais vus + Holm sur famille | **ADOPT** | seul dispositif qui rende le faux positif mesurable (arène FWER 0/40) |
| Nulle par décalage circulaire du max (interactions, CMI) | **ADOPT** | contrôle de la multiplicité sans hypothèse i.i.d. |
| Stability selection (blocs) + lasso | **ADAPT** | trouve les mains stables (`lrv_24/168`) ; borne E[V] non fiable sous dépendance |
| CMI gaussienne / orthogonalisation | **ADAPT** | cohérent avec lasso ; ajouter un **gate de nouveauté** vs baseline (manque révélé par C01/y_vol) |
| Recherche exhaustive d'interactions | **ADAPT** | 100 % de puissance dans l'arène ; ne pas juger sans test partiel vs baseline |
| Régression symbolique GP | **PARK** | 27.5 % de puissance sur non-linéarité pure ; 0 expression stable ; combinaisons linéaires déguisées |
| Importance d'arbre / permutation pour la sélection | **PARK** | classe du bruit quand il n'y a pas de signal |
| Cochran-Q inter-marchés | **ADAPT** | diagnostic de robustesse utile, pas d'identification |
| ICP-lite | **PARK** | 0 sous-ensemble accepté en réel ; hypothèses violées |
| Affirmations causales sans design | **REJECT** | 07 : B échangeable et C imitent A |

## Suite recommandée (hors périmètre de cette mission)
1. Ajouter le gate de nouveauté (corrélation partielle > 0 vs ridge de mains) *avant* gel ; refaire l'arène.
2. Élargir les primitives (order-book, funding/OI, macro) — le jeu OHLCV+taker 1h semble épuisé pour `y_ret`.
3. Cibles plus proches d'un usage : coûts, exécution, horizons plus longs.
4. Toute décision d'intégration : adjudication ultérieure contre le vrai dépôt local AurumShift.
