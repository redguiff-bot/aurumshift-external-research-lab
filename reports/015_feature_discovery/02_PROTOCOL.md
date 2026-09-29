# 02 — Protocole (pré-enregistré avant tout run sur données réelles)

> Ce fichier a été commité **avant** `scripts/02_discovery.py` et **avant** `scripts/05_heldout_once.py`.
> Le SHA du commit fait foi de l'ordre. Toute déviation est listée en §11.
> Étiquettes de preuve du dépôt : PROVEN / OBSERVED / DOCUMENTED_CLAIM / INFERENCE / UNKNOWN.

## 1. Mode et périmètre

EXTERNAL_RESEARCH_ONLY, NO_PRIVATE_AURUMSHIFT_CODE, NO_INTEGRATION. Aucun code ni schéma AurumShift
privé n'est connu ni supposé. Rien ici ne dit qu'une méthode est compatible avec AurumShift.

## 2. Données (OBSERVED)

- Source : klines spot 1h Binance via `data-api.binance.vision`, fenêtre figée
  2021-01-01T00:00Z → 2026-09-01T00:00Z (exclu). Hash SHA-256 par fichier dans `bench/feature_discovery_v1/data/MANIFEST.json`.
- **Marchés de découverte** : BTCUSDT, ETHUSDT, BNBUSDT, SOLUSDT.
- **Marchés jamais vus** : XRPUSDT, ADAUSDT, DOGEUSDT, LINKUSDT, PAXGUSDT (or tokenisé). Ils n'entrent
  *qu'à l'évaluation held-out* (aucune ligne d'entraînement/validation, aucune statistique).
- Splits temporels stricts par marché sur une grille commune :

| split | plage | usage |
|---|---|---|
| train | début (après 800 barres de warm-up) → 2023-06-30 | screening, sparse, stabilité, GP, fit des baselines |
| embargo | 7 jours | ≥ 7× l'horizon de label max (24 h) |
| validation | 2023-07-08 → 2024-12-31 | sélection : signe, gate, pénalité complexité, α des baselines |
| embargo | 7 jours | |
| held-out | 2025-01-08 → 2026-08-31 | **une seule évaluation**, sur formules gelées |

- `fd.panel.panels(target, split)` est la seule porte d'accès ; `02_discovery.py` n'appelle que `train`/`val`.
  `05_heldout_once.py` écrit `results/heldout_lock.json` et refuse de se relancer.

## 3. Primitives (26) et cibles

Primitives : rendements (1/4/24/72/168 h), log-vol réalisée (6/24/168 h), Parkinson 24 h, range 1 barre,
CLV, log-volume (1, 24), ratio taker-buy (1, 24), log-nb de trades (1, 24), taille moyenne de trade,
distance au plus haut/bas 72 h, écarts aux moyennes 24/168 h, Amihud-like 24 h, heure (sin/cos), week-end.
Toutes calculées avec des barres ≤ t, standardisées sur fenêtre glissante passée de 720 barres, clip ±5.
Détail unité/formule/lookback : `fd/features.py::REGISTRY`.

Cibles (analysées séparément, jamais moyennées) :
- `y_ret` : rendement futur 4 h / (vol 168 h × √4). Difficile (attendu : quasi non prédictible).
- `y_vol` : log(vol réalisée future 24 h / vol réalisée passée 24 h). Cible « facile » : contrôle de puissance.

## 4. Méthodes (toutes sur train, 5 seeds {11,23,37,41,59}, chaque seed voit 70 % des blocs de 336 barres)

1. MI kNN (rapport seulement), 2. CMI gaussienne avec sélection avant conditionnelle (nulle par décalage circulaire, q95),
3. lasso randomisé + stability selection (bloc, π=0.7, borne E[V]),
4. interactions : *toutes* les paires × 3 formes (`a·b`, `a·sgn b`, `b·sgn a`), corrélation partielle
   après effets principaux, nulle du max par décalage circulaire, même signe sur les 4 marchés,
5. régression symbolique (gplearn, 5 seeds, pop 300, 10 générations, parcimonie 0.004) + simplification gloutonne
   par score pénalisé, 6. orthogonalisation / non-redondance (|ρ|<0.80),
7. invariance : Cochran-Q par environnement (marché) et ICP-lite (diagnostic, jamais identifiant).

## 5. Pénalités

Score de validation = IC_val moyen − 0.0005 × (nœuds) − 0.001 × (constantes ajustées). Nœuds ≤ 15.
Ridge/lasso : α choisi sur validation. Le signe d'une feature est fixé sur **train**, jamais sur validation/held-out.

## 6. Gates de découverte (validation)

Une expression est « découverte » si : IC_val > 0 (signe train) sur ≥ 75 % des marchés de découverte,
p bootstrap par blocs (48 barres) < 0.10 sur l'IC poolé, score pénalisé > 0, et si elle survit à la
consolidation : famille (corrélation de rang ≥ 0.85 sur validation) retrouvée dans ≥ 60 % des seeds,
non redondante (|ρ| < 0.80) avec les familles déjà retenues. **FEATURES_DISCOVERED** = nombre de familles gelées (les deux cibles).

## 7. Critères held-out (pré-enregistrés)

Pour chaque formule gelée, sur les 9 marchés (4 découverte + 5 jamais vus), grille temporelle commune :

- **STABLE** ⇔ p_holm < 0.05 (bootstrap circulaire par blocs de 48 barres, B=2000, temps partagé entre marchés,
  Holm sur *toute* la famille gelée des deux cibles) **et** IC>0 sur ≥ 75 % des marchés **et** IC>0 sur une majorité des 5 marchés jamais vus.
- **NON-REDONDANTE** ⇔ STABLE **et** corrélation partielle avec y (contrôlant la prédiction du ridge sur les 26 primitives brutes,
  ajusté train+val) significative (Holm 0.05) **et** |ρ| < 0.80 avec les autres formules stables.
- **SYMBOLIC_EXPRESSIONS_STABLE** = formules STABLE de type `symbolic`.

## 8. Baselines (mêmes splits ; hyper-paramètres sur validation ; refit train+val)

`raw_ridge` (26 primitives), `lasso` (sparse linéaire), `tree_top8_ridge` (importance RF → top-8 → ridge),
`perm_top8_ridge` (importance par permutation d'un GBM → top-8 → ridge), `gbm_full_ceiling` (plafond non parcimonieux, non éligible comme « baseline à battre »).
Modèle découvert = ridge sur [features principales stables + formules gelées].

**COMPLEXITY_JUSTIFIED** (par cible, puis agrégé) : `YES` si le modèle découvert bat *toutes* les baselines non-plafond
en IC held-out poolé avec IC 90 % (bootstrap apparié) > 0 de la différence **et** ≥ 1 formule NON-REDONDANTE ;
`PARTIAL` si non-inférieur (borne basse de la différence > −0.005) avec ≤ moitié des paramètres de la meilleure baseline ;
sinon `NO`. Agrégat : YES si YES sur au moins une cible ; sinon PARTIAL si PARTIAL sur une cible ; sinon NO.

## 9. Arène de falsification (synthétique, vérité connue) — condition de validité de la procédure

`scripts/03_synthetic_arena.py` exécute **le même pipeline** sur panels synthétiques : NULL (aucun signal) et
MIXED (5 composantes plantées : linéaire, interaction pure, non-linéaire pure, spécifique à des marchés, décroissante ; + doublon quasi identique).
Graines de développement 0–9 ; chiffres finaux sur graines ≥ 1000. La procédure est **valide** si :
FWER (≥ 1 formule stable sous NULL) ≤ 0.10 (40 réplications), et puissance sur composante linéaire ≥ 0.80.
Sinon le verdict est STUDY_INCONCLUSIVE quelle que soit la sortie réelle.

## 10. Verdict (règle mécanique)

- arène invalide → `STUDY_INCONCLUSIVE`
- sinon NON-REDONDANTES ≥ 3 sur ≥ 2 familles de méthode/cibles et COMPLEXITY_JUSTIFIED = YES → `FEATURE_DISCOVERY_REFERENCE_SUPPORTED`
- sinon ≥ 1 formule STABLE → `LIMITED_STABLE_FEATURES_SUPPORTED`
- sinon → `NO_STABLE_NEW_FEATURES`

## 11. Classification causale

`PREDICTIVE` (stable held-out) → `INVARIANT_ASSOCIATION` (+ Cochran-Q non rejeté sur environnements marché × période,
signe identique partout, y compris marchés jamais vus) → `CAUSAL_HYPOTHESIS` (+ variables incluses dans l'intersection ICP-lite
*et* mécanisme plausible écrit) → `CAUSAL_IDENTIFIED` **uniquement** avec un design identifié (intervention, expérience naturelle,
instrument valide). Aucune donnée réelle de ce dépôt n'offre un tel design : le compte attendu est 0.

## 12. Déviations

(aucune à la date de rédaction — les déviations éventuelles sont ajoutées ci-dessous avec le commit fautif)
