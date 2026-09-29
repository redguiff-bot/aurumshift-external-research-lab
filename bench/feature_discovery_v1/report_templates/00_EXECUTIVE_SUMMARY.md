# 00 — Résumé exécutif

Mission `AURUMSHIFT_EXTERNAL_FEATURE_DISCOVERY_SYMBOLIC_CAUSAL_V1` — EXTERNAL_RESEARCH_ONLY / NO_PRIVATE_AURUMSHIFT_CODE / NO_INTEGRATION.
Étiquettes : PROVEN / OBSERVED / DOCUMENTED_CLAIM / INFERENCE / UNKNOWN.

## Question

Peut-on découvrir automatiquement des features de marché compactes, interprétables, non redondantes, sans que la
fouille ne surajuste silencieusement ? Méthodes testées : MI/CMI, stability selection, lasso, interactions, régression symbolique (GP),
orthogonalisation, invariance/ICP-lite. Baselines : primitives brutes, lasso, importance d'arbre, importance par permutation.

## Ce qui a été fait (OBSERVED)

- 9 marchés crypto spot 1h réels (Binance, 2021-01 → 2026-08) : 4 pour la découverte, **5 jamais vus** (XRP, ADA, DOGE, LINK, PAXG) évalués une seule fois.
- Splits temporels stricts avec embargo 7 j, protocole pré-enregistré commité avant les runs, **formules gelées puis held-out lu une seule fois** (verrou de fichier + digest).
- 26 primitives PIT, 2 cibles : `y_ret` (rendement 4 h, très difficile) et `y_vol` (log-ratio de volatilité future 24 h / passée, cible « facile »).
- 5 seeds par cible, 4 marchés de découverte × 2 périodes (train/val), gates de validation avec pénalités de complexité et de paramètres.
- **Arène de falsification synthétique** (vérité connue, 40 + 40 réplications, graines jamais utilisées en développement) exécutant le *même* pipeline.

## Résultat

| | valeur |
|---|---|
| FEATURES_DISCOVERED | {{FEATURES_DISCOVERED}} |
| FEATURES_HELDOUT_STABLE | {{FEATURES_HELDOUT_STABLE}} |
| SYMBOLIC_EXPRESSIONS_STABLE | {{SYMBOLIC_EXPRESSIONS_STABLE}} |
| NONREDUNDANT_FEATURES | {{NONREDUNDANT_FEATURES}} |
| CAUSAL_IDENTIFIED_COUNT | {{CAUSAL_IDENTIFIED_COUNT}} |
| COMPLEXITY_JUSTIFIED | {{COMPLEXITY_JUSTIFIED}} |
| **FINAL_VERDICT** | **{{FINAL_VERDICT}}** |

### Lecture honnête (INFERENCE)

1. Le verdict est **mécanique** (règle du protocole §10) : une formule est stable au held-out → `LIMITED_STABLE_FEATURES_SUPPORTED`. Ce verdict est **faible** : la formule stable (`mul(ret_72h, sgn(mag_168))` sur `y_vol`, IC held-out +0.104, positif sur 9/9 marchés) est un proxy de magnitude de mouvement récent, **déjà couvert par les baselines** : sa corrélation partielle avec la cible, en contrôlant le ridge sur les 26 primitives brutes, est **négative** (−0.035) → **0 feature non redondante**.
2. **La complexité n'est pas justifiée** : sur les deux cibles, le modèle « découvert » ne bat aucune baseline non-plafond (sur `y_vol` il est *moins bon* que le ridge brut : −0.021 d'IC, q10 −0.028). Le plafond GBM (non parcimonieux) fait mieux de +0.010 d'IC sur `y_vol` : il reste un peu de non-linéarité, non capturée en forme compacte.
3. **`y_ret`** : aucune feature stable. Les 26 primitives brutes n'ont pas d'IC held-out distinguable de 0 (0.006, IC 90 % [−0.012, +0.023]) ; l'unique candidat (`ret_24h × week-end`, IC +0.012 sur 9/9 marchés) a un p_Holm de 0.107.
4. **Aucune expression symbolique (GP) n'est gelée** : les programmes GP trouvés sur `y_vol` (IC val jusqu'à 0.50) sont des combinaisons linéaires déguisées (ex. `−wknd − lrv_24`) instables d'une seed à l'autre, donc rejetées à la consolidation. Les deux formules gelées viennent de la recherche d'interactions exhaustive, pas du GP.
5. **Causalité** : `CAUSAL_IDENTIFIED_COUNT = 0` (aucun design identifié n'existe dans des klines observationnelles). La formule stable est classée `PREDICTIVE` ; ICP-lite n'accepte aucun sous-ensemble (hypothèses violées : la volatilité varie trop entre environnements).
6. **La procédure elle-même est valide** (arène) : sous H0 aucun faux positif stable sur 40 réplications (FWER 0/40) ; la composante linéaire plantée est retrouvée à 100 %, l'interaction pure à 100 %, la non-linéarité pure à seulement 27.5 %, les effets spécifiques à un marché ou décroissants ne passent jamais.

### Ce que ça veut dire pour AurumShift (INFERENCE, sans intégration)

La fouille automatique de features **sait se retenir** (bon contrôle du faux positif) mais, sur des barres 1h crypto avec ces primitives, **n'apporte pas de valeur au-delà d'un ridge/lasso sur primitives brutes**. Recommandation externe : voir 09 (ADAPT stability selection + shift-null + protocole gelé/verrouillé ; PARK la régression symbolique ; REJECT toute affirmation causale sans design). Aucune compatibilité avec le code AurumShift privé n'est affirmée.

## Fichiers

`01_METHODS` `02_PROTOCOL` `03_SYMBOLIC` `04_SPARSE` `05_INTERACTIONS` `06_STABILITY` `07_CAUSAL_BOUNDARIES` `08_FALSIFICATION` `09_ADJUDICATION` `10_LIMITATIONS` ; code/données/résultats : `bench/feature_discovery_v1/`.

```
FEATURES_DISCOVERED={{FEATURES_DISCOVERED}}
FEATURES_HELDOUT_STABLE={{FEATURES_HELDOUT_STABLE}}
SYMBOLIC_EXPRESSIONS_STABLE={{SYMBOLIC_EXPRESSIONS_STABLE}}
NONREDUNDANT_FEATURES={{NONREDUNDANT_FEATURES}}

CAUSAL_IDENTIFIED_COUNT={{CAUSAL_IDENTIFIED_COUNT}}

COMPLEXITY_JUSTIFIED={{COMPLEXITY_JUSTIFIED}}

FINAL_VERDICT={{FINAL_VERDICT}}
```
