# Lane 008 (étude B) — Capacité de risque et turnover : analyse approfondie

Analyste : Claude (session de relecture indépendante). Date de l'analyse : 2026-09-29.
Lecteur visé : Jean-François, qui ne connaît ni GitHub ni le trading quantitatif. Chaque terme technique est expliqué à sa première occurrence.

Conventions de citation dans ce document :
- `R/` = `reports/008_risk_capacity_turnover/` ; `B/` = `bench/capacity_v1/` (tous deux sur la branche `origin/claude/festive-archimedes-c3fso6`).
- Marqueurs de vérification : **✔ vérifié** (j'ai recalculé le chiffre depuis les fichiers de résultats bruts), **✘ écart**, **? non vérifiable**.
- Les labels du dépôt (claude.md) sont repris : PROVEN (prouvé), OBSERVED (mesuré), DOCUMENTED_CLAIM (affirmé par une source, non re-vérifié), INFERENCE (déduction), UNKNOWN (inconnu).
- « Le rapport affirme » = ce que disent les fichiers `R/`. « J'ai vérifié » = ce que j'ai recalculé moi-même. Les deux sont toujours distingués.
- Tout ce qui est marqué **[MA VÉRIF.]** est une expérience ou un calcul que j'ai exécuté moi-même dans un dossier temporaire (rien n'a été écrit sur une branche du dépôt, rien n'a été poussé).

---

## 0. Fiche d'identité

| Élément | Valeur |
|---|---|
| Lane | 008 (étude B) — « Capacité de risque et turnover » (allocation de créneaux de positions rares) |
| Nom d'étude dans les fichiers | `AURUMSHIFT_EXTERNAL_RISK_CAPACITY_AND_TURNOVER_ALLOCATION_V1` (`R/00_EXECUTIVE_SUMMARY.md`) |
| Branche | `origin/claude/festive-archimedes-c3fso6` |
| Pull request | PR n°8 « research(008): risk-capacity & turnover allocation V1 — MULTIPLE_CAPACITY_METHODS_SUPPORTED », ouverte (`state=open`, non fusionnée, `mergeable_state=clean`), créée 2026-09-29 14:06:15 UTC, dernière mise à jour 15:23:18 UTC (lue via l'API GitHub) |
| Base de la PR | `main` (sha 1a449df…) ; tête de branche `0ff4f71efe7fd2a3e3014407553f0c3665617d2f` |
| Commits de la lane | 3 : `ad2adda` (13:51:49 UTC : simulateur, politiques, tests, tuning + validation, paramètres gelés, PRÉ-ENREGISTREMENT) ; `c64cbb4` (14:05:18 : exécution held-out H1/H2/H3) ; `0ff4f71` (14:05:19 : diagnostics, analyses, sonde OSS, rapports 00–14) |
| Fichiers de la lane | 75 (15 rapports dans `R/` + 60 dans `B/`), cohérent avec « changed_files: 75 » de la PR |
| Volume | +49 515 lignes ajoutées (PR) ; ≈ 25 Mo extraits pour `R/` + `B/` (dont ≈ 5,7 Mo `tuning_runs.csv`, 3,9 Mo `H2`, 3,8 Mo `H3`, 1,9 Mo `H1`) |
| Auteur des commits | « Claude » (agent), compte `redguiff-bot` |
| Verdict final | `FINAL_VERDICT=MULTIPLE_CAPACITY_METHODS_SUPPORTED` (`R/00_EXECUTIVE_SUMMARY.md`, `R/13_ADJUDICATION.md`) |
| Force du verdict (mon jugement) | **Modérée pour la partie « ne pas allouer par ordre d'arrivée » ; faible à fragile pour le libellé exact « plusieurs méthodes »** (voir §7 : il dépend d'un seuil δ choisi par les auteurs, et le rapport se trompe sur ce qui se passe à δ=0,5). Tout est synthétique (données inventées par un générateur), donc aucune force empirique sur le monde réel. |
| Note de contexte importante | La PR signale elle-même qu'une **autre implémentation indépendante** de la même mission existe (branche `claude/risk-capacity-turnover-v1`, fichiers `bench/capacity_v1/py/*` déjà fusionnés dans `main` via la PR n°6) : c'est très probablement « l'étude A », faite par un autre analyste. Je ne l'ai pas lue (voir §8). |

Ce que « verdict » veut dire ici, en clair : l'étude a comparé plusieurs façons de décider **quelles opportunités méritent une place quand les places sont rares** (par exemple « combien de positions ouvertes en même temps »), sur des marchés simulés. Le verdict `MULTIPLE_CAPACITY_METHODS_SUPPORTED` signifie : « plusieurs méthodes basées sur un score battent nettement la méthode naïve du premier arrivé, premier servi, et elles sont trop proches les unes des autres pour en désigner une seule ».

---

## 1. Mission et question posée

### 1.1 Question reformulée simplement

Imagine un système qui dispose de **K places** (ici K=4 « slots », des emplacements de position ouverte). Des **opportunités arrivent** (des signaux « ce titre semble intéressant »), souvent plus nombreuses que les places libres. À chaque instant, il faut décider **lesquelles prendre**. Question : comment répartir ces places rares **sans regarder le futur** (« lookahead » : utiliser par erreur une information qu'on n'aurait pas eue au moment de la décision), **sans surapprendre** (« overfitting » : régler la méthode tellement finement sur un jeu de données qu'elle ne marche plus ailleurs) et **sans hypothèse cachée sur le capital**.

Le rapport le formule ainsi (`R/00`) : « When incoming opportunities exceed available position slots, how should scarce slots be allocated without lookahead, overfitting or hidden capital assumptions? ». Et dans `R/13` : « how should a research/PAPER engine decide which opportunities deserve scarce slots… ».

Sous-questions traitées :
1. Le « premier arrivé, premier servi » (FIFO) suffit-il, ou échoue-t-il, et dans quels scénarios ?
2. Classer par valeur nette attendue par **heure de place occupée** (« slot-hour ») aide-t-il ?
3. Un « prix fantôme » (seuil de coût d'opportunité) aide-t-il ? (= n'occuper une place que si le gain par heure dépasse une fraction du gain moyen des positions déjà prises.)
4. Une pénalité de corrélation (éviter d'entasser des positions dans le même groupe) aide-t-elle ?
5. Un bandit contextuel (algorithme d'apprentissage qui explore/exploite) est-il justifié ?
6. Le « spam » de candidats (le même instrument émet 20 fois plus de signaux), la « famine » (un instrument n'a jamais de place), l'effet de la capacité K (3, 4, 6, 10).
7. Y a-t-il une méthode « prête à l'emploi » (drop-in) ? (Réponse du rapport : non.)

### 1.2 Contraintes du dépôt (claude.md)

Doctrine de recherche du dépôt (`claude.md`, lu) : ordre de priorité **REUSE → ADAPT → WRAP → COMPOSE → CUSTOM LAST** (réutiliser un composant existant, sinon l'adapter, l'envelopper, en composer plusieurs, et ne fabriquer soi-même qu'en dernier recours). Labels obligatoires PROVEN / OBSERVED / DOCUMENTED_CLAIM / INFERENCE / UNKNOWN. Interdictions : ne pas fabriquer de résultats, ne pas juger sur les étoiles GitHub, ne jamais prétendre qu'un candidat est compatible avec AurumShift sur la seule base de ce dépôt (l'adjudication finale se fait plus tard contre le vrai dépôt local privé). Contraintes AurumShift rappelées : recherche seule / « paper » (sans capital réel), PostgreSQL d'abord, PIT (« point-in-time » : n'utiliser que les données connues à la date de la décision) / provenance / pas de lookahead, événementiel intraday (pas de haute fréquence), une seule source d'autorité par sujet, « l'absence de preuve n'est pas une preuve d'absence », coûts de marché réalistes.

Respect par l'étude (mon jugement) :
- **Étiquetage** : très bien respecté (chaque rapport marque OBSERVED/INFERENCE/UNKNOWN). Littérature marquée DOCUMENTED_CLAIM et papiers « non re-téléchargés » (`R/02`).
- **CUSTOM LAST** : l'étude écrit son propre simulateur (~600 lignes) en justifiant qu'aucune bibliothèque ne modélise « un slot, un instrument, retour censuré et retardé, séparation public/caché » (`R/12`). Justification plausible mais non testée (aucune bibliothèque de simulation n'a été essayée : SimPy/ciw classés PARK sans essai).
- **REUSE/ADAPT** : la sonde OSS (`R/12`, `B/src/oss_probe.py`) n'interroge que les métadonnées PyPI (version, licence, date) ; **aucune source n'a été lue, aucun paquet installé ni exécuté** sauf `scipy.optimize.linear_sum_assignment` (500/500 essais). Donc la partie « inspecter le vrai code » de claude.md n'est pas remplie pour les bibliothèques.
- **Frontière** : le rapport répète partout qu'il ne conclut rien sur `max_open_positions`, l'allocateur actuel, ni un plafond de production (`R/00`, `R/09`, `R/13`, `R/14` point 18). Respecté.

---

## 2. Méthode

### 2.1 Vue d'ensemble

Étude **entièrement synthétique** : aucune donnée de marché réelle. Un générateur (`B/src/world.py`) fabrique des « mondes » déterministes. Un simulateur (`B/src/engine.py`) fait tourner des politiques d'allocation (`B/src/policies.py`) dans ces mondes. On compare les politiques sur des métriques. Les résultats bruts sont des CSV (une ligne par politique × scénario × graine).

Vocabulaire :
- **bps** (basis points) : 1 bps = 0,01 %. Ici c'est une unité générique de gain/coût, sans lien avec une monnaie précise.
- **M1** = `net_per_avail_slot_hour` = gain net total divisé par (K × W), avec W=600 heures. C'est le gain net par heure de place *disponible* (occupée ou non). C'est la métrique principale déclarée dans `B/configs/prereg.json`.
- **Graine (« seed »)** : nombre qui fixe le hasard ; deux exécutions avec la même graine donnent le même monde. Comparer deux politiques sur la même graine s'appelle un **appariement** (les deux voient exactement le même monde : les écarts viennent de la politique, pas de la chance).
- **Bootstrap apparié (2000 rééchantillonnages)** : on tire au hasard, avec remise, des graines pour recalculer l'écart moyen 2000 fois ; les 2,5 % et 97,5 % des écarts donnent un **intervalle de confiance à 95 % (IC)**. Si l'IC ne contient pas 0, l'écart est jugé « détectable ».
- **Macro-moyenne** : moyenne simple des 13 moyennes par scénario (chaque scénario pèse pareil).

### 2.2 Monde simulé (`R/04`, `B/src/world.py`)

- Pas de temps = 1 heure ; W = 600 pas d'admission + 48 h de marge de règlement (`PAD=48`).
- N instruments (10 en tuning, 12 en validation, 15 en held-out) répartis en G groupes publics (5, 4, 5). K=4 places par défaut.
- Chaque instrument a : un gain moyen (edge) μ, une volatilité σ, une durée moyenne de position, un coût par entrée (bps). L'« edge » réel varie dans le temps (processus AR(1) de persistance φ=0,9 + régimes de Markov + facteurs de groupe et de marché).
- Gain brut d'un trade : `(E/D)·h + σ·(ρ_g·ΔC_g + ρ_m·ΔC_m + √(1−ρ_g²−ρ_m²)·√h·Z)` ; net = brut − coût, coût prélevé **une fois** par admission. **L'edge s'accumule linéairement avec le temps de détention (hypothèse A3)**, ce qui rend la sortie anticipée peu coûteuse.
- Hypothèses dures : une seule position par instrument (A1) ; un candidat expire après TTL = 4 pas (A2) ; durées lognormales ou Pareto écrêtées à [1, 48] h.
- **Arrivées** : Poisson par instrument, charge offerte `load` fixée en valeur absolue (pour K=10 le système est donc sous-chargé).
- **Score observé** : `s = a_i + b·E + τ·bruit` (estimation bruitée de l'edge brut). Il peut être périmé (réutilise l'ancien score), manquant (NaN) ou inversé/mal calibré (scénarios de diagnostic).
- Séparation information publique / cachée : les politiques reçoivent une `View` (candidats, positions ouvertes) et un `Pub` (groupes, volatilité publique bruitée, estimation de coût). Les tableaux cachés (edge réel, durée réelle, aléa idiosyncratique, chemins de facteurs) restent dans `World` et ne servent qu'au règlement après admission (`B/src/world.py` docstring, `B/src/engine.py`). Retour d'information aux politiques : uniquement à la fermeture d'un trade, et seulement pour les trades admis (retour « censuré »).

### 2.3 Les 13 scénarios (`R/04`, `B/src/world.py::SCENARIOS`)

| id | ce qu'il stresse | paramètres clés |
|---|---|---|
| S1 sparse | demande < capacité | load=0,4 |
| S2 moderate | saturation occasionnelle | load=1,2 |
| S3 chronic | saturation permanente | load=3,5 |
| S4 late high-quality | les bons candidats arrivent tard, après qu'une rafale de mauvais a rempli les places avec des trades longs (14 h) | load=3,5, profil de phase |
| S5 correlated (crise) | le groupe au meilleur edge subit une dérive négative cachée entre 30 % et 60 % de la fenêtre ; ρ_g=0,8 | diversification utile |
| S5b correlated (bénin) | même monde sans crise | diversification peut nuire |
| S6 short vs long | trades courts (2 h, edge 14) contre longs (16 h, edge 45) | le classement par trade préfère le long, le classement par heure préfère le court |
| S7 regime shift | le classement des edges s'inverse à W/2 | flip dur |
| S8 noisy rank | bruit de score ×2,5 | τ×2,5 |
| S9 missing quality | 50 % des scores absents (NaN) | p_miss=0,5 |
| S10 spam | 2 instruments médiocres émettent ×20 | sémantiques d'ingestion |
| S11 burst | arrivées ×15 pendant 4 pas toutes les 60 | load=2,5 |
| S12 nearly equal | tout est quasi égal ; le choix ≈ bruit | edges/durées/coûts ≈ égaux |

Scénarios de diagnostic seulement (split validation, jamais held-out) : F_score_gaming, F_corr_collapse, F_inversion, F_poor_cal, F_stale, F_starve_skew, F_short_churn_cost.

### 2.4 Politiques (12 implémentables + 1 oracle) (`B/src/policies.py`)

| id | rôle | règle en langage simple | paramètre gelé |
|---|---|---|---|
| FIFO | baseline A | premier émis, premier servi | — (ingestion RAW) |
| ROUND_ROBIN | baseline B | tour de rôle entre instruments | — |
| RANDOM | baseline C | tirage aléatoire (graine dédiée `seed+424242`) | — |
| EQUAL_QUOTA | baseline D | l'instrument le moins servi passe d'abord | — |
| OLDEST_SLOT | baseline E | comme FIFO, mais si tout est plein et qu'un candidat attend, on **évince** la position la plus ancienne (âge ≥ min_hold) ; le coût est payé en entier, le gain est tronqué | min_hold=4 |
| FIFO_SCREEN | contrôle ajouté | FIFO, mais seulement si (score − coût) > 0 | — (SCORE_UPDATE) |
| SCORE_RANK | candidat | classe par valeur nette (score − coût), refuse le négatif | — |
| SLOTHOUR | candidat | classe par valeur nette **divisée par la durée de détention estimée** (EWMA des durées réalisées de l'instrument ; a priori 6 h) | — |
| SLOTHOUR_SHADOW | candidat | comme SLOTHOUR mais n'admet que si le taux ≥ θ × (moyenne mobile du taux des positions admises) | θ=0,25 |
| UNCERTAINTY_LCB | candidat | « rétrécit » le score vers l'historique de l'instrument (poids ω), puis borne inférieure (κ × écart-type) ; manquant → variance supplémentaire | ω=0,6 ; κ=0 |
| CORR_AWARE | candidat | SLOTHOUR − pénalité proportionnelle à l'exposition déjà prise dans le même groupe (ρ̂=0,6 fixé exprès à tort) | γ=0,1 |
| LINTS | candidat | Thompson sampling linéaire (bandit contextuel : tire un modèle plausible de la récompense et classe avec) sur récompense retardée = net par heure de détention | α=0,1 |
| ORACLE_GREEDY_UB | **non implémentable** | choisit avec la connaissance parfaite du gain réel ; sert de plafond de référence et de « canari » du test de fuite | — |

Note : « Complexe » (pré-enregistré) = {SLOTHOUR_SHADOW, UNCERTAINTY_LCB, CORR_AWARE, LINTS} ; « Simple » = {FIFO_SCREEN, SCORE_RANK, SLOTHOUR, ROUND_ROBIN} (`B/configs/prereg.json`).

### 2.5 Sémantiques d'ingestion (« spam ») (`R/01`, `B/src/engine.py`)

| mode | règle |
|---|---|
| RAW | chaque émission est un candidat indépendant |
| DEDUP_LATEST | un seul candidat par instrument, le dernier remplace l'ancien (l'âge repart à zéro) |
| COOLDOWN | émission ignorée si l'instrument a été accepté il y a < 3 pas |
| SCORE_UPDATE | un candidat par instrument, garde sa position d'arrivée, score remplacé par le dernier non manquant, expiration rafraîchie |

Les politiques baselines A–E sont évaluées en RAW (« implémentation naïve »), les autres avec leur mode ajusté (SCORE_UPDATE pour toutes les candidates).

### 2.6 Découpage tuning / validation / held-out et pré-enregistrement (`R/05`)

1. **TUNING** (graines 1000–1005, monde N=10, G=5, τ=8, CV=0,6) : toutes les configurations (politique × paramètre × mode d'ingestion = 128 configurations) sur 13 scénarios ; objectif = macro-moyenne de M1 (`B/results/tuning/tuning_objective.csv`, 9984 lignes brutes ✔ = 128×13×6).
2. **VALIDATION** (graines 2000–2007, monde différent N=12, G=4, τ=9, CV=0,8) : les 3 meilleures configurations de chaque politique sont rejouées (36 configurations × 13 × 8 = 3744 lignes ✔). La meilleure en validation est gelée dans `B/configs/frozen_params.json`.
3. **PRÉ-ENREGISTREMENT** `B/configs/prereg.json` (commit `ad2adda`) : métriques, marge d'équivalence δ = 0,25 bps/slot-heure, règles d'échec/équivalence de FIFO, règle de justification de la complexité, règle de verdict, sha256 du code (`952d5c02…d12` ) et des paramètres gelés (`ebcd46c4…1383`).
4. **HELD-OUT** (`B/src/run_heldout.py`, refuse d'écraser) : H1 primaire (13 scénarios × 20 graines 3000–3019 × 13 politiques, K=4) ; H2 matrice d'ingestion (10 graines, 4 modes) ; H3 balayage de capacité K∈{3,4,6,10} (10 graines, paramètres non ré-ajustés).
5. **Diagnostics hors held-out** (D1–D6, split validation, graines 6000–8019) : robustesse, qualité du score, coût, modes de défaillance, sensibilité aux paramètres, stress diversification. Le rapport les présente comme diagnostics, pas comme preuve principale.
6. Le code d'analyse a été écrit **après** l'existence des résultats H1 mais n'implémente que les règles pré-enregistrées ; les « paires ciblées », D6 et la sonde OSS sont déclarées post-hoc/diagnostiques (`R/05`, `R/14` point 10).

### 2.7 Vérification du gel — **[MA VÉRIF.]**

- ✔ `sha256(frozen_params.json du commit ad2adda)` = `ebcd46c4668407ad00e3248d0b92948d30d3605b3fefce093d4d8b4a0c7b1383` = valeur de `prereg.json`.
- ✔ Concaténation triée des 5 fichiers `src/*.py` du commit `ad2adda` (common, engine, policies, run_tuning, world) : sha256 = `952d5c02e31a5f67546c83895d4f83f152eb57ad0ecca50d61a759f96b12d43d` = valeur de `prereg.json`.
- ✔ `git diff ad2adda origin/…c3fso6 -- world.py engine.py policies.py common.py run_tuning.py` : **0 ligne** (le simulateur n'a pas bougé depuis le gel). Les fichiers ajoutés ensuite sont `run_heldout.py`, `analysis*.py`, `run_diag.py`, `run_div_stress.py`, `verify_repro.py`, `oss_probe.py`, `make_reports.py`.
- Limite : ce « pré-enregistrement » est un fichier dans le même dépôt, écrit par le même agent, sans horodatage externe (ni tag signé, ni dépôt tiers). L'ordre des commits (13:51 puis 14:05) est la seule preuve ; les commits `c64cbb4` (héld-out) et `0ff4f71` (rapports) ont **une seconde d'écart** (14:05:18 et 14:05:19) : ils ont clairement été créés ensemble après coup. Ça ne prouve rien de mal, mais le pré-enregistrement est *déclaratif*, pas *vérifiable de l'extérieur*.

### 2.8 Critères de décision pré-enregistrés (seuils exacts) (`B/configs/prereg.json`)

- Métrique primaire : `net_per_avail_slot_hour` (M1). Métriques secondaires rapportées séparément, sans score composite.
- **δ = 0,25** bps/slot-heure (justifié comme ≈ 10 % du M1 typique de FIFO, marqué INFERENCE ; sensibilité déclarée δ ∈ {0,1 ; 0,5}).
- FIFO_FAILURE_SCENARIO (vs FIFO RAW) : scénario où **au moins une** des 6 candidates {SCORE_RANK, SLOTHOUR, SLOTHOUR_SHADOW, UNCERTAINTY_LCB, CORR_AWARE, LINTS} a une **borne basse de l'IC** de (M1 − M1_FIFO) **> δ**. Idem contre FIFO_SCREEN.
- FIFO_EQUIVALENT : aucune des 6 n'a IC_bas > δ.
- COMPLEXITY_JUSTIFIED = VRAI si une méthode « complexe » a un écart macro > δ **et** IC_bas > 0 **et** gagne (estimation ponctuelle) dans ≥ 8/13 scénarios contre la meilleure « simple ».
- Verdict : B = méthodes battant FIFO@RAW de plus de δ avec IC_bas > 0. **B vide → FIFO_REMAINS_SUFFICIENT_REFERENCE.** T = méthodes à moins de δ de la meilleure implémentable, gagnant ≥ 8/13 contre FIFO. |T| = 1 → CAPACITY_ALLOCATION_REFERENCE_SUPPORTED ; |T| ≥ 2 → MULTIPLE_CAPACITY_METHODS_SUPPORTED. Aucune méthode (FIFO incluse) ne bat RANDOM de plus de δ → NO_CAPACITY_METHOD_SUPPORTED. Invalidation scientifique → STUDY_INCONCLUSIVE.
- BEST_SLOT_HOUR = argmax macro M1 sur {SLOTHOUR, SLOTHOUR_SHADOW, SCORE_RANK}.

---

## 3. Résultats détaillés

### 3.1 Sélection tuning → validation → gel (`B/results/tuning`, `B/results/validation`) — ✔ recalculé

Paramètres gelés (`B/configs/frozen_params.json`) et M1 de validation :

| politique | paramètres | ingestion primaire | M1 validation |
|---|---|---|---|
| CORR_AWARE | γ=0,1 | SCORE_UPDATE | 2,447 |
| EQUAL_QUOTA | — | RAW (tuned: SCORE_UPDATE) | 2,006 |
| FIFO | — | RAW | 2,052 |
| FIFO_SCREEN | — | SCORE_UPDATE | 2,206 |
| LINTS | α=0,1 | SCORE_UPDATE | 2,472 |
| OLDEST_SLOT | min_hold=4 | RAW | 2,387 |
| RANDOM | — | RAW (tuned: SCORE_UPDATE) | 2,037 |
| ROUND_ROBIN | — | RAW (tuned: DEDUP_LATEST) | 2,004 |
| SCORE_RANK | — | SCORE_UPDATE | 2,399 |
| SLOTHOUR | — | SCORE_UPDATE | 2,449 |
| SLOTHOUR_SHADOW | θ=0,25 | SCORE_UPDATE | 2,451 |
| UNCERTAINTY_LCB | ω=0,6 ; κ=0 | SCORE_UPDATE | 2,505 |

Remarques que j'ai relevées dans les CSV (non dans les rapports) :
- Les meilleures configurations du tuning sont parfois très proches de celles retenues en validation : LINTS top-1 du tuning = α=0,6 en RAW (2,410) mais le gel est α=0,1 en SCORE_UPDATE (validation 2,472 contre 2,471 pour α=0,6 RAW) : différence de 0,001, donc choix arbitraire sans conséquence.
- OLDEST_SLOT : le top-3 du tuning contenait min_hold=8 (deux ingestions) et min_hold=4 en RAW ; la validation donne 2,387 pour (4, RAW) contre 2,310 (8, SCORE_UPDATE). `run_tuning.py` force en plus l'ingestion primaire RAW pour les baselines A–E (règle décidée à la conception). Cohérent avec le rapport.
- Valeurs de validation du tuning-objective : CORR_AWARE meilleur tuning γ=0,05 (2,462) mais validation gèle γ=0,1 (2,447 contre 2,445) : différence négligeable.

### 3.2 Held-out H1 : résultat principal (K=4, 13 scénarios × 20 graines) — `R/10`, `B/results/heldout/H1_primary.csv`

Structure du fichier ✔ : 3380 lignes = 13 politiques × 13 scénarios × 20 graines (3000–3019), K=4 partout.

**Tableau principal (macro-moyenne, écarts appariés contre FIFO RAW).** Toutes les valeurs M1, écarts et IC ci-dessous sont ✔ vérifiés (M1 recalculé depuis le CSV brut ; écarts/IC lus dans `B/results/analysis/H1_paired_macro.csv`, et **recalculés par mon propre bootstrap** pour SLOTHOUR, LCB, SHADOW, LINTS, FIFO_SCREEN, OLDEST_SLOT avec écart < 0,005).

| politique | M1 (bps/slot-h) | net total moyen | écart vs FIFO [IC 95 %] | scénarios gagnés /13 | écart vs FIFO_SCREEN [IC] |
|---|---|---|---|---|---|
| FIFO | 1,781 | 4273,5 | — | — | — |
| ROUND_ROBIN | 1,775 | 4259,5 | −0,006 [−0,050 ; 0,035] | 8 | −0,170 [−0,216 ; −0,127] |
| RANDOM | 1,739 | 4173,0 | −0,042 [−0,087 ; 0,001] | 6 | −0,206 [−0,249 ; −0,158] |
| EQUAL_QUOTA | 1,740 | 4175,6 | −0,041 [−0,082 ; 0,002] | 5 | −0,205 [−0,247 ; −0,161] |
| OLDEST_SLOT | 1,966 | 4717,7 | +0,185 [0,140 ; 0,229] | 10 | +0,021 [−0,022 ; 0,066] |
| FIFO_SCREEN | 1,944 | 4666,7 | +0,164 [0,124 ; 0,205] | 11 | — |
| SCORE_RANK | 2,145 | 5149,2 | +0,365 [0,319 ; 0,413] | 12 | +0,201 [0,156 ; 0,246] |
| SLOTHOUR | 2,216 | 5317,9 | +0,435 [0,388 ; 0,479] | 13 | +0,271 [0,229 ; 0,315] |
| SLOTHOUR_SHADOW | 2,225 | 5339,5 | +0,444 [0,395 ; 0,495] | 12 | +0,280 [0,235 ; 0,324] |
| UNCERTAINTY_LCB | 2,278 | 5466,5 | +0,497 [0,449 ; 0,545] | 13 | +0,333 [0,289 ; 0,379] |
| CORR_AWARE | 2,194 | 5265,9 | +0,413 [0,366 ; 0,462] | 13 | +0,250 [0,205 ; 0,294] |
| LINTS | 2,196 | 5271,0 | +0,416 [0,365 ; 0,464] | 13 | +0,252 [0,207 ; 0,300] |
| ORACLE_GREEDY_UB (non implémentable) | 5,719 | 13725,7 | — | — | — |

Lecture en langage simple :
- FIFO, tour de rôle, aléatoire et quotas égaux forment un même paquet (écarts dans [−0,04 ; +0,00], IC contenant ou frôlant 0). **L'ordre d'arrivée n'a aucune information sur la qualité** dans ce monde (le rapport le dit : « by construction candidates are exchangeable in time » — `R/03`).
- Tous les classements par score gagnent de +0,37 à +0,50 bps par slot-heure, soit environ +21 % à +28 % (0,365/1,781 = 20,5 % ; 0,497/1,781 = 27,9 %), avec 12 à 13 scénarios gagnés sur 13.
- Le plafond « oracle » vaut 5,72, mais il est **non atteignable** (il connaît le futur). La meilleure méthode implémentable comble (2,278−1,781)/(5,719−1,781) ≈ 12,6 % de l'écart FIFO→oracle, soit le « ≈13 % » du rapport (`R/06`) ✔.

**Écarts-types entre graines (FIFO, ✔ recalculés)** : par scénario, l'écart-type de M1 sur 20 graines va de 0,25 (S1) à 0,77 (S10). Les IC par scénario sont donc de l'ordre de ±0,1 à ±0,3, comme le dit `R/14` point 8.

**Comparaison au meilleur « simple » (SLOTHOUR)** (`B/results/analysis/H1_vs_best_simple.csv`, ✔ recalculé) :

| politique | écart vs SLOTHOUR [IC] | scénarios gagnés |
|---|---|---|
| FIFO | −0,435 [−0,481 ; −0,389] | 0 |
| ROUND_ROBIN | −0,441 [−0,488 ; −0,394] | 0 |
| RANDOM | −0,477 [−0,527 ; −0,425] | 0 |
| EQUAL_QUOTA | −0,476 [−0,528 ; −0,429] | 1 |
| OLDEST_SLOT | −0,250 [−0,296 ; −0,205] | 3 |
| FIFO_SCREEN | −0,271 [−0,310 ; −0,229] | 0 |
| SCORE_RANK | −0,070 [−0,109 ; −0,031] | 2 |
| SLOTHOUR_SHADOW | +0,009 [−0,026 ; +0,044] | 5 |
| **UNCERTAINTY_LCB** | **+0,062 [+0,026 ; +0,099]** | 10 |
| CORR_AWARE | −0,022 [−0,051 ; +0,009] | 5 |
| LINTS | −0,020 [−0,054 ; +0,017] | 5 |

Contre RANDOM (`H1_vs_random.csv`) : SLOTHOUR +0,477 [0,424 ; 0,529], LCB +0,539 [0,493 ; 0,587], FIFO +0,042 [−0,001 ; 0,087].

**Per-scénario, M1 moyen sur 20 graines (`R/03`, ✔ vérifié en entier pour FIFO, SLOTHOUR, LCB, ORACLE ; les autres colonnes ✔ par échantillonnage de la macro-moyenne)** :

| scénario | FIFO | RR | RANDOM | EQ_Q | OLDEST | F_SCREEN | S_RANK | SLOTHOUR | SHADOW | LCB | CORR | LINTS | ORACLE |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| S10_spam | 2,003 | 2,087 | 2,019 | 1,907 | 2,156 | 2,156 | 2,220 | 2,262 | 2,230 | 2,275 | 2,279 | 2,242 | 4,883 |
| S11_burst | 0,960 | 0,960 | 0,909 | 0,924 | 0,923 | 0,979 | 1,152 | 1,199 | 1,175 | 1,212 | 1,193 | 1,183 | 3,015 |
| S12_near_equal | 2,646 | 2,592 | 2,543 | 2,678 | 2,881 | 2,814 | 2,934 | 2,965 | 2,914 | 3,109 | 3,010 | 2,886 | 7,758 |
| S1_sparse | 0,828 | 0,833 | 0,831 | 0,837 | 0,843 | 0,825 | 0,835 | 0,836 | 0,789 | 0,832 | 0,836 | 0,836 | 1,825 |
| S2_moderate | 1,469 | 1,458 | 1,478 | 1,419 | 1,533 | 1,579 | 1,653 | 1,663 | 1,516 | 1,604 | 1,647 | 1,622 | 3,988 |
| S3_chronic | 2,123 | 2,231 | 2,079 | 2,021 | 2,398 | 2,353 | 3,024 | 3,213 | 3,304 | 3,256 | 3,083 | 3,153 | 7,880 |
| S4_late_hq | 1,558 | 1,434 | 1,509 | 1,438 | 2,105 | 1,665 | 1,837 | 1,885 | 2,143 | 1,952 | 1,847 | 1,887 | 4,772 |
| S5_correlated | 0,967 | 1,029 | 0,873 | 0,997 | 0,892 | 1,186 | 1,297 | 1,345 | 1,363 | 1,392 | 1,346 | 1,345 | 5,498 |
| S5b_corr_benign | 1,767 | 1,496 | 1,510 | 1,607 | 1,678 | 1,920 | 2,165 | 2,314 | 2,427 | 2,284 | 2,268 | 2,209 | 6,017 |
| S6_short_vs_long | 3,187 | 3,220 | 3,253 | 3,202 | 3,888 | 3,109 | 3,082 | 3,441 | 3,412 | 3,492 | 3,334 | 3,538 | 7,985 |
| S7_regime_shift | 1,866 | 1,821 | 1,960 | 1,808 | 2,154 | 2,264 | 2,765 | 2,727 | 2,779 | 2,819 | 2,731 | 2,746 | 6,911 |
| S8_noisy_rank | 1,783 | 1,805 | 1,785 | 1,709 | 1,934 | 2,103 | 2,293 | 2,262 | 2,212 | 2,523 | 2,301 | 2,369 | 6,699 |
| S9_missing | 1,993 | 2,107 | 1,853 | 2,070 | 2,170 | 2,325 | 2,634 | 2,694 | 2,659 | 2,859 | 2,650 | 2,536 | 7,116 |

Observations à moi : (a) dans S1 (peu de demande), tout le monde vaut ≈0,83 : normal, quand il y a plus de places que de candidats il n'y a rien à choisir ; (b) dans S10, l'égalité exacte de OLDEST_SLOT et FIFO_SCREEN à 2,156 est une coïncidence numérique constatée dans le CSV, pas une erreur de copie (les valeurs viennent du même tableau) ; (c) dans S6, SCORE_RANK (3,082) est **plus bas** que FIFO (3,187) en estimation ponctuelle ; le rapport le note (« significance not tested », `R/08`) — la paire SCORE_RANK−FIFO existe dans `H1_paired_perscenario.csv` avec valeur −0,10 (`R/10` tableau des `*`), non significative.

**Différences appariées par scénario contre FIFO** (`R/10` ; `*` = IC exclut 0 vers le haut). J'ai vérifié les chiffres de plusieurs lignes dans `H1_paired_perscenario.csv` / `targeted_pairs.csv` ✔. Points saillants :
- S3_chronic : +0,90 (SCORE_RANK) à +1,18 (SHADOW), tous significatifs : c'est le scénario où l'allocation compte le plus.
- S7_regime_shift : +0,86 à +0,95, tous significatifs.
- S1_sparse : +0,00 à +0,01 (SHADOW −0,04) : aucune différence.
- S6_short_vs_long : OLDEST_SLOT +0,70 (le plus fort), SLOTHOUR +0,25, SCORE_RANK −0,10 (non signif.).
- S4_late_hq : SHADOW +0,59 et OLDEST_SLOT +0,55 sont les plus forts ; les autres +0,28 à +0,39.

### 3.3 Règles pré-enregistrées : échec / équivalence de FIFO — `R/10`, `R/13`, `H1_rules_and_verdict_machinery.json` — ✔ recalculé

Avec δ = 0,25 et l'ensemble candidat de 6 méthodes :
- **Échec de FIFO** (au moins une candidate a IC_bas > 0,25 contre FIFO) : S12, S3, S4, S5, S5b, S7, S8, S9 (8 scénarios).
- **Équivalence** : S10, S11, S1, S2, S6 (5 scénarios).
- Contre le contrôle plus fort FIFO_SCREEN : échec = S3, S4, S5b, S7, S8, S9 (6) ; équivalence = S10, S11, S12, S1, S2, S5, S6 (7).

Sensibilité à δ (`R/10`, JSON ✔) :

| δ | nb d'échecs vs FIFO | scénarios | nb d'équivalents | nb d'échecs vs FIFO_SCREEN |
|---|---|---|---|---|
| 0,1 | 11 | S10, S11, S12, S3, S4, S5, S5b, S6, S7, S8, S9 | 2 | 9 |
| 0,25 | 8 | S12, S3, S4, S5, S5b, S7, S8, S9 | 5 | 6 |
| 0,5 | 4 | S3, S7, S8, S9 | 9 | 1 (S3) |

Deux réserves du rapport (`R/10` « Two flags ») : S6 est « équivalent » pour les 6 candidates, mais OLDEST_SLOT (baseline E) bat FIFO de +0,70 [0,53 ; 0,87] dans S6 (aussi +0,55 en S4, +0,27 en S3, +0,29 en S7, +0,23 en S12) ; la faiblesse de FIFO sur la capture des places longues est réparée par la préemption, pas par le classement. Et en S1/S2 tout coïncide (normal).

Interprétation : plus la marge δ exigée est grande, moins on trouve de scénarios où FIFO échoue. Le choix δ=0,25 est **une décision des auteurs** (INFERENCE), non tirée d'une quantité mesurée.

### 3.4 Machinerie de verdict — ✔ recalculé

Sortie de `B/results/analysis/H1_rules_and_verdict_machinery.json` : meilleure implémentable = UNCERTAINTY_LCB ; B = T = [SCORE_RANK, SLOTHOUR, SLOTHOUR_SHADOW, UNCERTAINTY_LCB, CORR_AWARE, LINTS] ; meilleure simple = SLOTHOUR ; meilleure complexe = UNCERTAINTY_LCB ; |T| = 6 ≥ 2 ⇒ MULTIPLE_CAPACITY_METHODS_SUPPORTED. Complexité (vs SLOTHOUR) :

| méthode | écart macro | IC | scénarios gagnés | justifiée ? |
|---|---|---|---|---|
| SLOTHOUR_SHADOW | +0,009 | [−0,028 ; +0,046] | 5 | non |
| UNCERTAINTY_LCB | +0,062 | [+0,027 ; +0,097] | 10 | non (0,062 < 0,25) |
| CORR_AWARE | −0,022 | [−0,051 ; +0,010] | 5 | non |
| LINTS | −0,020 | [−0,057 ; +0,016] | 5 | non |

**Sensibilité du verdict à δ — [MA VÉRIF.] et ✘ écart avec le rapport.** `R/13` écrit : « δ=0.1 ⇒ T = {LCB, SHADOW, SLOTHOUR, LINTS, CORR_AWARE} … still multiple ; δ=0.5 ⇒ T also contains FIFO_SCREEN/OLDEST_SLOT: still multiple. A single-method verdict would need δ<0.05 ». J'applique la règle pré-enregistrée telle qu'elle est écrite (`prereg.json`, « B empty → FIFO_REMAINS_SUFFICIENT_REFERENCE ») aux écarts publiés (`H1_paired_macro.csv`) :
- δ=0,1 : B = {OLDEST_SLOT, FIFO_SCREEN, SCORE_RANK, SLOTHOUR, SHADOW, LCB, CORR_AWARE, LINTS} ; T (à moins de 0,1 de 2,278) = {LCB, SHADOW, SLOTHOUR, LINTS, CORR_AWARE} : « plusieurs », d'accord avec le rapport.
- **δ=0,5 : B = ∅**, car la meilleure méthode (LCB) bat FIFO de seulement +0,497 < 0,5. La règle dit alors **FIFO_REMAINS_SUFFICIENT_REFERENCE**, et non « still multiple ». De plus, à δ=0,5 FIFO (1,781 ≥ 2,278−0,5 = 1,778) est lui-même dans T. Le rapport a raisonné sur T seul et a oublié la règle de B qui passe avant.
- Autrement dit : **le verdict final n'est pas robuste à δ** : il change de nature entre δ=0,25 et δ=0,5, et l'écart de 0,003 (0,497 vs 0,5) est minuscule. Cela n'invalide pas le verdict au δ pré-enregistré, mais l'affirmation « conclusion robuste aux marges 0,1 et 0,5 » (implicite dans `R/13`) est **fausse**.

### 3.5 Rapport 06 — Économie des slots, spam, famine

Table macro H1 complète (`R/06`, ✔ vérifiée sur `H1_macro_all_metrics.csv`) : M1, net par slot-heure occupé, regret vs oracle, slot-heures inactives, inactives avec candidats en attente, rotation, ré-entrée, durée moyenne, HHI (concentration) instrument/groupe, qualité des rejetés, qualité des admis, capture de haute qualité. Extraits ✔ :

| politique | M1 | net/slot-h occupé | slot-h inactives | inactives avec candidats en attente | rotation (adm./slot-h) | durée moyenne (h) | HHI instr. | HHI groupe | hq_capture |
|---|---|---|---|---|---|---|---|---|---|
| FIFO | 1,781 | 2,028 | 292,7 | 0 | 0,104 | 8,75 | 0,094 | 0,231 | 0,638 |
| OLDEST_SLOT | 1,966 | 2,256 | 320,3 | 0 | 0,196 | 5,04 | 0,087 | 0,226 | 0,934 |
| FIFO_SCREEN | 1,944 | 2,304 | 371,3 | 51,8 | 0,100 | 8,74 | 0,097 | 0,232 | 0,698 |
| SLOTHOUR | 2,216 | 2,628 | 382,9 | 57,8 | 0,104 | 8,38 | 0,092 | 0,228 | 0,742 |
| SLOTHOUR_SHADOW | 2,225 | 2,845 | 510,4 | 158,5 | 0,100 | 8,16 | 0,095 | 0,232 | 0,729 |
| UNCERTAINTY_LCB | 2,278 | 2,657 | 359,4 | 39,3 | 0,106 | 8,36 | 0,095 | 0,231 | 0,752 |
| ORACLE_GREEDY_UB | 5,719 | 6,660 | 376,5 | 58,5 | 0,121 | 7,36 | 0,088 | 0,223 | 0,889 |

Ce que ça signifie :
- Les méthodes de classement laissent **plus** de places vides que FIFO (SLOTHOUR 383 slot-heures vides contre 293) mais gagnent plus : refuser un candidat au gain net négatif est une décision, pas un défaut (« idleness is a decision », `R/06`). Le rapport présente cela comme un choix économique correct ; il l'est *dans ce monde*, où le coût est connu et le score est calibré.
- OLDEST_SLOT double la rotation (0,196 contre 0,104) et évince 52 % de ses trades (`evict_frac` 0,523 ✔). Sa « capture de haute qualité » 0,934 est un artefact de son nombre d'admissions (le rapport le dit, `R/03`, `R/14` point 14).
- La qualité par heure de détention des candidats **admis** passe de 3,44 (FIFO) à 4,42 (SLOTHOUR) et celle des **rejetés** de 3,46 à 2,71 (oracle : 9,26 et 1,53) ✔ (`adm_rate`, `rej_rate_instw`).

**Famine (starvation)** (`R/06`, ✔ recalculé) :

| politique | famine dure | famine douce | jours max de refus (heures) | part max d'un instrument |
|---|---|---|---|---|
| FIFO | 0,000 | 0,016 | 214,8 | 0,144 |
| ROUND_ROBIN | 0,000 | 0,008 | 193,4 | 0,130 |
| EQUAL_QUOTA | 0,000 | 0,000 | 132,7 | 0,095 |
| OLDEST_SLOT | 0,000 | 0,007 | 105,0 | 0,134 |
| SCORE_RANK | 0,003 | 0,039 | 289,9 | 0,155 |
| SLOTHOUR | 0,002 | 0,031 | 272,7 | 0,160 |
| SLOTHOUR_SHADOW | 0,002 | 0,058 | 325,0 | 0,170 |
| UNCERTAINTY_LCB | 0,005 | 0,059 | 330,5 | 0,168 |
| CORR_AWARE | 0,002 | 0,029 | 272,4 | 0,161 |
| LINTS | 0,002 | 0,027 | 260,8 | 0,161 |

Définitions du rapport : famine dure = part des instruments ayant ≥5 émissions mais zéro admission ; douce = admissions < 25 % de la moyenne ; « max denial hours » = plus longue période de refus (borne haute : un refus justifié économiquement compte aussi).
Lecture : la famine dure est ≈0 partout ; la famine douce est 2 à 7 fois plus élevée pour les méthodes de classement (0,059/0,008 ≈ 7). Les garde-fous EQUAL_QUOTA / ROUND_ROBIN suppriment la famine mais **rendent tout le gain** du classement (−0,44 et −0,48 vs SLOTHOUR ✔ −0,441/−0,476) : « le prix d'une garantie d'équité ≈ 0,45 bps/slot-heure » dans ce monde. Aucun garde-fou plus léger (bonus d'ancienneté, part minimale) n'a été testé.

**Spam (S10, H2, D4)** — ✔ vérifié dans `H2_ingest_matrix.csv` et `D4_spam_paired_vs_RAW.csv`.
Part d'admissions prise par l'instrument le plus admis, S10 : FIFO 0,326 (RAW), 0,293 (DEDUP), 0,303 (COOLDOWN), 0,328 (SCORE_UPDATE) ; SLOTHOUR 0,348/0,335/0,314/0,335 ; contre ≈0,14–0,17 hors spam. RR / EQUAL_QUOTA : 0,287 / 0,236 (RAW). M1 en S10 par sémantique (✔) : FIFO 2,163 (RAW) 2,272 (DEDUP) 2,227 (COOL) 2,220 (SU) ; SLOTHOUR 2,297 / 2,389 / 2,240 / 2,389 ; LCB 2,416 / 2,361 / 2,403 / 2,361.
Effet apparié vs RAW (validation, S10, graines 7000–7009, 10 graines) : COOLDOWN coûte −0,252 [−0,370 ; −0,118] à SLOTHOUR, −0,221 [−0,288 ; −0,155] à SCORE_RANK, −0,271 [−0,409 ; −0,125] à FIFO_SCREEN ✔ ; DEDUP/SCORE_UPDATE : effets M1 dans le bruit (tous les IC contiennent 0), réduction de concentration de −0,007 à −0,034. Conclusion du rapport, que j'approuve : spam distord **qui** reçoit les places plus que **combien** on gagne ; COOLDOWN n'est pas un filtre gratuit. Réserve : les instruments spam ont un edge « médiocre mais pas mauvais » : le cas dangereux (edge négatif) n'a pas été simulé (`R/06`).

**Effet de l'ingestion sur la baseline FIFO — [MA VÉRIF.]** Comme les baselines sont en RAW et les candidates en SCORE_UPDATE, on pourrait craindre une comparaison biaisée. `H2_ingest_matrix.csv` (macro 13 scénarios, 10 graines) : FIFO RAW 1,814 ; SCORE_UPDATE 1,810 ; DEDUP_LATEST 1,845 ; COOLDOWN 1,853. L'écart d'ingestion pour FIFO est ≤ 0,04 : **le biais est négligeable** devant les +0,4 à +0,5 des méthodes de classement.

### 3.6 Rapport 07 — Diversification (CORR_AWARE)

Principe : CORR_AWARE = SLOTHOUR − γ·ρ̂·σ̂·(exposition déjà ouverte dans le même groupe), avec ρ̂=0,6 fixé volontairement faux (les vraies corrélations valent 0,35 / 0,8 / 0,9 / 0,3).
Différences appariées CORR_AWARE(γ=0,1) − SLOTHOUR (`R/07`) :

| scénario | M1 | pnl_std | pire 24 h | drawdown max | HHI groupe |
|---|---|---|---|---|---|
| S5_correlated (20 graines) | +0,00 [−0,08 ; +0,09] | −0,12 [−0,54 ; +0,28] | +12,86 [−27 ; +53] | −47,9 [−154 ; +54] | 0,00 |
| S5b_corr_benign | −0,05 [−0,14 ; +0,05] | −0,20 | +13,56 | −19,4 | 0,00 |
| F_corr_collapse (validation, 10 graines) | −0,16 [−0,33 ; −0,02] | −0,15 | −5,01 | +26,2 | 0,00 |

Aucun effet significatif au γ gelé (0,1) : la pénalité est trop faible pour changer les allocations (HHI de groupe bouge < 0,005).
**Test de stress D6** (validation, 20 graines 8000–8019, γ ∈ {0,1 ; 0,4 ; 1 ; 2 ; 4 ; 8}), ✔ table `D6_diversification_stress_table.csv` et `D6_paired_vs_SLOTHOUR.csv` :
- S5 (crise) γ=1 : M1 +0,04 [−0,09 ; +0,16] (non signif.), pire 24 h +40,7 [5,9 ; 79,1] (significatif), drawdown −37,9 [−139,9 ; +49,0] (non signif.). À ρ_g=0,9 : drawdown −86 à −100 avec IC excluant surtout 0. Bénéfice de risque à coût moyen nul.
- S5b (bénin) γ=1 : M1 −0,13 [−0,28 ; +0,02] ; γ=4 : −0,29 [−0,43 ; −0,15] (significatif).
- F_corr_collapse γ=4 : M1 −0,34 [−0,50 ; −0,19] ; la pénalité de groupe ne protège pas d'un facteur de marché.
- Sensibilité macro (D5) : γ ∈ {0,02…0,4} donne 2,312–2,328 (plat).
Verdict du rapport : la diversification par pénalité **ne s'améliore pas de façon fiable** ; γ≈0,4–1 est au mieux une « couverture bon marché du risque de queue » si le contrôle du drawdown est un objectif.
Mes remarques : (i) plusieurs de ces comparaisons portent sur 20 graines et des dizaines de métriques sans correction de comparaisons multiples ; le seul effet clairement positif (« pire 24 h » en S5) est un parmi ≈ 54 IC lus, donc à prendre comme piste, pas comme preuve ; (ii) l'en-tête de `B/src/run_div_stress.py` annonce « incl. a single-group-heavy world (G=2 groups) », mais **ce cas n'est pas exécuté** dans le script (seules 5 configurations S5/S5b/F_corr_collapse avec ρ=0,9 en option) ; le rapport ne prétend d'ailleurs pas l'avoir fait (il liste ce cas en UNKNOWN). Petit décalage de commentaire, sans effet sur les résultats.

### 3.7 Rapport 08 — Turnover et économie du slot-heure

1. **SLOTHOUR vs SCORE_RANK** : +0,070 [+0,031 ; +0,109] ✔ (macro) ; significatif seulement en S5b (+0,148 [0,028 ; 0,300]) et S6 (+0,358 [0,164 ; 0,564]) ✔ ; aucune valeur où SCORE_RANK gagne significativement ✔. Test de réfutation (validation, échelle de qualité de score D2) : avec un score parfait (τ=0), SCORE_RANK 3,150 > SLOTHOUR 2,980 ✔ : diviser par une durée *estimée* ajoute du bruit quand la durée varie plus à l'intérieur d'un instrument qu'entre instruments (INFERENCE du rapport).
2. **Prix fantôme (SHADOW)** : θ=0,25 gelé (bas de grille ; θ=0 = SLOTHOUR). Sensibilité (validation, 13 scénarios, ✔ `D5`) : θ=0,25 → 2,344 ; 0,5 → 2,053 ; 0,75 → 1,068 ; 1,0 → 0,399 ; 1,25 → 0,189 : effondrement. Held-out vs SLOTHOUR : +0,009 [−0,026 ; +0,044] ✔ ; seulement significatif en S4 (+0,258 [0,101 ; 0,404]) ✔ et significativement **pire** en S1 (−0,047 [−0,089 ; −0,013]) et S2 (−0,147 [−0,251 ; −0,049]) ✔. Le communiqué de synthèse dit « θ≥0,5 collapses » : c'est vrai à partir de 0,75 ; à 0,5 la perte est de −0,29 (2,05 contre 2,34), forte mais pas un « effondrement » (léger surdire).
3. **Détention minimale (OLDEST_SLOT)** : validation macro min_hold 2 → 2,093 ; 4 → 2,271 ; 8 → 2,193 ✔ (D5). Held-out : +0,185 vs FIFO, mais seulement +0,021 [−0,022 ; +0,066] vs FIFO_SCREEN. **Sensibilité au coût** (D3, S3, ✔) : à coûts ×3 OLDEST_SLOT rapporte −1,163 alors que toutes les autres politiques restent positives (FIFO 0,224 ; FIFO_SCREEN 1,222 ; SLOTHOUR 1,534). Tout repose sur l'hypothèse A3 (gain linéaire dans le temps), non testée localement.
4. **Ajustement de hasard (hazard) / pénalité de rotation** : *non exécutés* (justification : nécessiterait un modèle de sortie ; une pénalité de rotation est algébriquement un surcoût). Statut : UNKNOWN.
5. **Incertitude de coût** (D3, validation, paramètres gelés, ✔ tableau reproduit à l'identique : S3 « known » ×1 : FIFO 1,894 ; FIFO_SCREEN 2,364 ; SCORE_RANK 3,002 ; SLOTHOUR 3,141 ; LCB 3,153 ; OLDEST 2,161 ; et à ×3 : 0,224 ; 1,222 ; 1,439 ; 1,534 ; 1,599 ; −1,163). Croyance de coût « zéro » alors que le vrai coût est ×3 : FIFO_SCREEN passe de 1,222 à 0,552 ✔, SLOTHOUR de 1,534 à 1,240 ✔. Conclusion du rapport : *classer* est moins sensible à l'erreur de coût que *seuiller* (écran). Ce que le rapport ne relève pas, et que j'ai vu dans `D3_cost_table.csv` : à coûts ×0,5 et croyance « unknown_conservative » (coût présumé 10 bps), FIFO_SCREEN fait **mieux** (2,807) qu'avec la vraie croyance « known » (2,679) — une croyance fausse fait mieux que la vérité, ce qui suggère que le seuil « score − coût > 0 » n'est pas optimal quand le score est bruité (malédiction du gagnant : les scores les plus élevés sont en partie du bruit). Piste, pas démonstration.
6. **Échelle de qualité du score** (D2, S3, validation, 8 graines 6000–6007, ✔ tableau complet reproduit) : pour SLOTHOUR, M1 = 3,141 (calibré bruité) ; 2,551 (inversé) ; 3,134 (50 % manquants) ; 2,639 (bruit ×2) ; 2,980 (parfait, borne haute) ; 2,558 (mal calibré) ; 3,135 (périmé à 60 %). FIFO reste à 1,894 (il n'utilise pas le score). L'avantage de SLOTHOUR sur FIFO passe de +1,247 (calibré) à +0,657 (inversé) et +0,664 (mal calibré) : baisse de 47 % ; pour SCORE_RANK, inversé : 2,240−1,894 = +0,346, baisse de 72 % ✔ « 45–70 % » du résumé exécutif est correct au sens large (45 à 72 %).

### 3.8 Rapport 09 — Sensibilité à la capacité K (H3, 10 graines, paramètres non ré-ajustés) — ✔

| politique | K=3 | K=4 | K=6 | K=10 |
|---|---|---|---|---|
| FIFO | 1,834 | 1,814 | 1,720 | 1,312 |
| OLDEST_SLOT | 2,080 | 2,005 | 1,876 | 1,315 |
| FIFO_SCREEN | 2,019 | 1,955 | 1,799 | 1,268 |
| SCORE_RANK | 2,411 | 2,211 | 1,870 | 1,271 |
| SLOTHOUR | 2,513 | 2,290 | 1,876 | 1,270 |
| SLOTHOUR_SHADOW | 2,512 | 2,263 | 1,862 | 1,210 |
| UNCERTAINTY_LCB | 2,579 | 2,340 | 1,933 | 1,310 |
| ORACLE | 6,508 | 5,754 | 4,506 | 2,847 |

Écarts appariés vs FIFO (`H3_paired_vs_FIFO.csv`) : K=3 : SLOTHOUR +0,679 [0,607 ; 0,756], LCB +0,745 [0,647 ; 0,842] ; K=4 : +0,476 / +0,526 ; K=6 : +0,156 / +0,213 ; K=10 : SLOTHOUR −0,041 [−0,059 ; −0,024], LCB −0,002 [−0,017 ; +0,014], FIFO_SCREEN −0,043 [−0,060 ; −0,027]. Taux de « tous les slots pleins » (`full_frac`) : FIFO 0,839 / 0,784 / 0,646 / 0,123 ; SLOTHOUR 0,794 / 0,716 / 0,500 / 0,054 ✔.
Lecture : plus les places sont abondantes (charge offerte fixée), moins l'intelligence d'allocation rapporte ; à K=10, plus aucune méthode ne bat FIFO. **Aucune recommandation de plafond** n'est ou ne doit être tirée : M1 est divisé par K×W et la demande est fixée, donc K plus grand est sous-chargé par construction. Robustesse OFAT (S3, validation) : meilleure implémentable − FIFO = +1,675 (K=3), +1,297 (K=4), +0,599 (K=6), +0,048 (K=10) ✔ (`D1_robustness_table.csv`), même ordre monotone.

Petit point : dans le bloc final, « CAP3 : FIFO 1,83 vs meilleure implémentable 2,58 (LCB−FIFO +0,75) » compare des moyennes (2,579−1,834 = 0,745 ✔) ; `H3_gaps_by_K.csv` donne un autre nombre « FIFO_to_best_impl_gap » (0,878 pour K=3) parce qu'il prend le max **par scénario** avant de moyenner : il est biaisé vers le haut (sélection du maximum). Le rapport cite bien la version non biaisée (0,75).

### 3.9 Rapport 10 — Robustesse (D1, D2, D5) — reprises et vérifications

- **Bruit de score** (D1, S3, 8 graines, ✔ `D1_score_noise_curve.csv`) : à τ×4 LCB garde 2,805 contre SLOTHOUR 2,351 (FIFO 1,894) ; pente de perte (de ×0,5 à ×4) : SCORE_RANK 0,74 ; SLOTHOUR 0,82 ; LCB 0,21 ; LINTS 0,51 — LCB est le moins sensible ✔.
- **Autres axes OFAT** (✔ table) : la charge (load 1,0 → tout est dans ±0,25 ; 6,0 → best−FIFO 1,611), la corrélation (0,1 → 0,85 : best−FIFO 1,300 → 1,201), la distribution des durées (lognormale CV 0,3/0,6/1,2 et Pareto), la persistance de régime. Résultat : l'ordre FIFO < FIFO_SCREEN < famille de classement est stable partout sauf load=1,0.
- **Sensibilité aux paramètres** (D5, 13 scénarios × 8 graines, ingestion gelée, ✔ 25 lignes reproduites) : LCB ω=0 → 2,349, 0,3 → 2,370, 0,6 → 2,418 ; κ n'aide pas (κ=0,3 & ω=0 → 2,307). CORR_AWARE γ plat (2,312–2,328) ; LINTS α plat (2,317–2,331).
- **Compute** (`compute_cost_serial.csv`, ✔) : LINTS 42,78 ms de sélection par run contre SLOTHOUR 1,78 ms (≈ 24×) ; LCB 3,11 ms.

### 3.10 Rapport 11 — Modes de défaillance (D4, validation, 10 graines 7000–7009)

Tableau du rapport et ce que j'ai vérifié :

| # | mode | résultat du rapport | vérification |
|---|---|---|---|
| 1 | score gaming (20 % d'instruments à score +30 bps gonflé, edge ≤10) | tous les classements sur-admettent les tricheurs (part max 0,15 FIFO → 0,20 SLOTHOUR) mais battent FIFO (2,68 vs 2,28) ; aucune politique ne détecte le trucage | ✔ 0,148 → 0,198 ; M1 2,68 / 2,28 ; SLOTHOUR−FIFO +0,403 [0,023 ; 0,761], SCORE_RANK−FIFO +0,359 [0,129 ; 0,588] ; LCB hérite du biais car il met en commun l'historique gonflé. OUVERT. |
| 2 | spam | concentration ↑, M1 dans le bruit, COOLDOWN nuit | ✔ (§3.5) |
| 3 | famine | dure ≈0 ; douce/refus plus élevés pour les classements ; garde-fous ≈0,45 | ✔ ; F_starve_skew soft 0,075 (SLOTHOUR) contre 0,000 (RR) — le rapport écrit « 0,07 » (0,075 arrondi vers le bas) |
| 4 | capture de places longues | S6 : SCORE_RANK durée moyenne 12,0 h contre 7,8 h (SLOTHOUR) | ✔ 12,02 / 7,77 |
| 5 | rotation courte | OLDEST_SLOT rotation ×2, ré-entrée 0,61 ; à coûts ×3 négatif | ✔ ré-entrée 0,607 (F_short_churn_cost) ; −1,163 |
| 6 | corrélation qui s'effondre | CORR_AWARE −0,16 [−0,33 ; −0,02] | ✔ (§3.6) |
| 7 | retard de régime | S7 : les scores courants s'adaptent instantanément ; LCB +0,09 [−0,02 ; +0,20] | ✔ +0,092 [−0,019 ; 0,199]. Non observé à cette vitesse de régime ; mémoire EWMA de 5 pas (0,8/0,2) |
| 8 | instabilité par bruit | occupation écart-type 0,05 (FIFO) → 0,13/0,19 (SLOTHOUR/SHADOW) en S8 ; LCB meilleur (+0,26 [0,12 ; 0,41]) | ✔ 0,046 → 0,128 / 0,194 ; +0,261 [0,122 ; 0,406] |
| 9 | oscillation de capacité | S11 : pleins 0,18–0,22, écart-type 0,34 pour tous ; inactivité 1499 h (SHADOW) contre 1222 (FIFO) | ✔ |
| 10 | un instrument monopolise les rafraîchissements | part 0,30–0,33, RR/EQ 0,23–0,28 | ✔ |
| 11 | bonne opportunité tardive | S4 : capture HQ FIFO 0,53 → SLOTHOUR 0,73 → SHADOW 0,77 ; SHADOW +0,26 ; OLDEST +0,44 vs FIFO_SCREEN | ✔ 0,535 / 0,729 / 0,767 |
| 12 | inversion de l'estimation de qualité | F_inversion : SCORE_RANK 2,43 < FIFO 2,62 ; SLOTHOUR 2,73, LINTS 2,83 ; OLDEST_SLOT 2,88 « au moins aussi bon que toute politique à score » ; OUVERT | ✔ pour les moyennes ; **mais voir §7 : non significatif** |

Points de vérification sur le #12 — **[MA VÉRIF.]** Dans `D4_failure_modes.csv` (10 graines), paires appariées F_inversion : SCORE_RANK − FIFO = **−0,191 [−0,509 ; +0,144]**, SLOTHOUR − FIFO = +0,106 [−0,198 ; +0,433], LINTS − FIFO = +0,205 [−0,104 ; +0,560], OLDEST_SLOT − FIFO = +0,256 [−0,017 ; +0,511], OLDEST_SLOT − SLOTHOUR = +0,150 [−0,205 ; +0,489]. **Tous les IC contiennent 0.** La phrase du résumé exécutif « in the separate inversion battery (D4) SCORE_RANK falls *below* FIFO » est donc une estimation ponctuelle non distinguable du bruit. Et l'échelle D2 (même mécanisme d'inversion, S3, 8 graines) donne l'inverse : SCORE_RANK 2,240 **>** FIFO 1,894 (+0,346).

### 3.11 Rapport 12 — Composants OSS (`B/results/analysis/oss_probe.json`, `R/12`)

Méthode : métadonnées de l'API JSON de PyPI, **sans inspection de source, sans installation, sans benchmark** (sauf le test scipy). Résultats (extrait, lus dans le JSON) : scipy 1.18.1 (≥ Python 3.12), OR-Tools 9.15.6755 (Apache 2.0), PuLP 4.0.0 (MIT, 2026-09-25), highspy 1.15.1 (MIT), cvxpy 1.9.3 (Apache-2.0, ≥3.11), MABWiser 2.7.4 (dernier envoi 2024-08-30, champ licence vide), etc. Classification du rapport : scipy ADOPT_REFERENCE ; OR-Tools, PuLP/HiGHS, cvxpy, contextualbandits, Open Bandit Pipeline, river, SimPy/ciw PARK ; PyPortfolioOpt / Riskfolio / skfolio REJECT pour l'admission de slots ; MABWiser ADAPT_CANDIDATE conditionnel ; Vowpal Wabbit REJECT. ✔ Test de réduction : assignation optimale à poids indépendants du slot = top-f par poids (500/500 essais) — un résultat élémentaire (PROVEN par réduction et OBSERVED), sans surprise. Limites : le classement OSS est fondé sur la date de mise en ligne uniquement (pas d'issues, pas de code), et Python 3.11 installé < ≥3.12 requis par scipy récent (`R/14` point 17).

### 3.12 Rapport 02 — Paysage algorithmique (24 familles)

24 familles : 1–12 exécutées (les 5 baselines, FIFO_SCREEN, SCORE_RANK, SLOTHOUR, SHADOW, LCB, CORR_AWARE, LINTS) ; 10 en PARK (LinUCB, bandits avec sacs à dos, sleeping bandits, assignation/min-cost-flow, ILP, secrétaire, optimisation en ligne primal-dual, Whittle, contrôle d'admission par file d'attente, Lyapunov) ; 2 REJECT (Exp3/Exp4, portefeuille HRP/moyenne-variance). Toutes les références de littérature sont DOCUMENTED_CLAIM « from prior knowledge, not re-fetched » (aucune vérification de théorème). Cohérent, mais le tableau est un catalogue, pas une revue systématique.

---

## 4. Candidats / méthodes évalués un par un

Notation : ADOPT / ADAPT / PARK / REJECT — celle du dépôt. Le rapport lui-même ne met pas ces mots sur chaque politique (il parle de « deserves local evaluation »). **La colonne « verdict » ci-dessous est ma traduction**, à confronter au tableau `R/13` « Which methods deserve local evaluation ».

| Méthode | Ce que dit le rapport | Ma traduction du verdict | Justification chiffrée (H1 sauf mention) | Conditions de changement de verdict |
|---|---|---|---|---|
| FIFO | insuffisant seul quand les places sont rares | REJECT comme allocateur ; conserver comme référence | 1,781 ; échec dans 8/13 scénarios (δ=0,25) ; équivalent si demande ≤ capacité (S1, S2, K=10) | si dans le système réel l'ordre d'arrivée corrèle avec la qualité (UNKNOWN) |
| ROUND_ROBIN, RANDOM, EQUAL_QUOTA | indistinguables de FIFO | REJECT comme allocateurs ; garde-fous = seulement métriques de suivi | 1,775 / 1,739 / 1,740 ; coût de l'équité ≈ 0,45 vs SLOTHOUR | si l'équité entre instruments est une exigence dure, mesurer localement un garde-fou plus léger (non testé) |
| OLDEST_SLOT (préemption) | diagnostic seulement | PARK (diagnostic) | +0,185 vs FIFO mais +0,021 [−0,022 ; +0,066] vs FIFO_SCREEN ; meilleur en S4 (+0,44 vs écran) et S6 ; pire en S5/S5b ; −1,163 à coûts ×3 | modèle défendable d'accumulation partielle du gain (hypothèse A3) et coûts d'échange bas |
| FIFO_SCREEN (écran net > 0) | contrôle à évaluer | ADAPT comme contrôle minimal | +0,164 [0,124 ; 0,205], 11/13 ; dégrade vers FIFO si la croyance de coût est 0 (1,222 → 0,552 à coûts ×3) | une croyance de coût locale défendable (l'inconnu ne doit pas valoir zéro) |
| SCORE_RANK | inférieur à SLOTHOUR | PARK (dominé) | +0,365 ; −0,070 vs SLOTHOUR ; capture des places longues en S6 (12,0 h) ; inversion : voir §7 | si la durée varie plus dans un même instrument qu'entre instruments, il redevient préférable (score parfait : 3,150 vs 2,980) |
| **SLOTHOUR** (net / durée estimée) | **référence primaire, sans paramètre** | **ADAPT (référence à évaluer localement)** | +0,435 [0,388 ; 0,479] vs FIFO, 13/13 ; +0,271 vs écran ; significatif contre SCORE_RANK seulement en S5b et S6 | il faut une estimation locale de la durée de détention ; si elle est inconnue/instable, préférer SCORE_RANK |
| UNCERTAINTY_LCB (mise en commun du score, ω=0,6) | référence complexe secondaire | ADAPT conditionnel | 2,278 ; +0,062 [0,026 ; 0,099] vs SLOTHOUR, 10/13 ; nettement meilleur en S8 (+0,261) et S12 (+0,144) ; le gain vient du rétrécissement (κ=0), pas de la pénalité de risque | utile seulement si un instrument émet des scores répétés/bruités ; sous marge δ=0,05 il deviendrait « justifié en taille d'effet » (`R/13`) |
| SLOTHOUR_SHADOW | situationnel | PARK (conditionnel) | +0,009 [−0,026 ; +0,044] ; S4 +0,258 ; S1 −0,047, S2 −0,147 ; θ ≥ 0,5 dégrade fortement | qualité qui arrive par vagues tardives (type S4) ; sinon laisse des places vides |
| CORR_AWARE | conditionnel | PARK | −0,022 [−0,051 ; +0,009] ; aucun gain de M1 significatif ; gain de risque limité au cas « crise dans le meilleur groupe » (γ≈0,4–1) | drawdown = objectif déclaré et peu de gros groupes ; à tester avec un monde à K ≫ G et groupes larges (non testé) |
| LINTS (bandit Thompson) | non maintenant | REJECT (pour l'instant) | −0,020 [−0,057 ; +0,016] ; ≈ 24× le temps de décision ; un seul design de features | un bandit mieux conçu pourrait combler l'écart (UNKNOWN) |
| Autres bandits (LinUCB, Exp3…), ILP/assignation | non maintenant | PARK ou REJECT | assignation à poids indépendants du slot = top-f (PROVEN) ; aucun test empirique | seulement si apparaissent des poids par slot ou des termes par paires |
| ORACLE_GREEDY_UB | plafond de référence | non candidat | 5,719 | — |
| Bibliothèques OSS | scipy ADOPT_REFERENCE, le reste PARK/REJECT | voir §3.11 | métadonnées PyPI seulement | inspection réelle du code requise avant tout ADOPT |

---

## 5. Bloc final complet (reproduit tel quel) et explication ligne par ligne

Bloc (identique dans `R/00_EXECUTIVE_SUMMARY.md` et `R/13_ADJUDICATION.md` ; j'ai comparé visuellement les deux) :

```
ALGORITHMS_DISCOVERED=24 (families/variants catalogued in 02_ALGORITHM_LANDSCAPE.md)
ALGORITHMS_EXECUTED=12 implementable (5 mandatory baselines + FIFO_SCREEN control + 6 candidates) + 1 non-implementable ORACLE_GREEDY_UB upper reference (not counted)

TUNING_SCENARIOS=13 scenarios (S1-S12 + S5b) x 6 seeds, split=tuning
VALIDATION_SCENARIOS=13 x 8 seeds, split=validation (selection among tuning top-3)
HELDOUT_SCENARIOS=13 (S1-S12 + S5b) x 20 seeds, split=heldout (structurally different world parameters)
SEEDS=tuning 1000-1005 | validation 2000-2007 | heldout H1 3000-3019 (H2/H3 3000-3009) | diagnostics 6000-8019

FIFO_FAILURE_SCENARIOS=S12, S3, S4, S5, S5b, S7, S8, S9   (delta=0.25 bps/avail-slot-hour, vs raw FIFO, pre-registered candidate set)
FIFO_EQUIVALENT_SCENARIOS=S10, S11, S1, S2, S6
  (vs the stronger FIFO_SCREEN control: failure=S3, S4, S5b, S7, S8, S9; equivalent=S10, S11, S12, S1, S2, S5, S6)

BEST_SLOT_HOUR_REFERENCE=SLOTHOUR_SHADOW@theta=0.25 by the pre-registered argmax rule; STATISTICALLY TIED with parameter-free SLOTHOUR (diff +0.009, CI [-0.026,+0.044]) -> SLOTHOUR is the practical reference
BEST_DIVERSIFICATION_REFERENCE=CORR_AWARE@gamma~0.4-1.0 (WEAK/CONDITIONAL: no significant M1 gain in any scenario; modest drawdown reduction only in the crisis-in-best-group case; costs M1 when gamma>=1 in benign/collapse worlds); default remains SLOTHOUR
BEST_TURNOVER_REFERENCE=SLOTHOUR (pre-registered argmax SLOTHOUR_SHADOW@0.25 is a tie; shadow-price threshold >=0.5 degrades sharply; OLDEST_SLOT preemption helps only in S4/S6-type worlds under a favourable linear-accrual assumption)

CAP3_SYNTHETIC_RESULT=FIFO 1.83 vs best implementable 2.58 bps/avail-slot-hour (LCB-FIFO +0.75, CI [0.65,0.84])
CAP4_SYNTHETIC_RESULT=FIFO 1.81 vs 2.34 (LCB-FIFO +0.53, CI [0.46,0.59])
CAP6_SYNTHETIC_RESULT=FIFO 1.72 vs 1.93 (LCB-FIFO +0.21, CI [0.16,0.26])
CAP10_SYNTHETIC_RESULT=FIFO 1.31 vs 1.31: no ranking method beats FIFO (LCB-FIFO -0.002, CI [-0.017,+0.014]); SLOTHOUR is slightly WORSE (-0.041)
  (descriptive only, offered load held fixed in absolute terms; NO production cap is recommended)

NO_LOOKAHEAD_PROVEN=TRUE_WITHIN_HARNESS (OBSERVED: prefix-invariance metamorphic test passes for all 12 implementable policies x 4 ingest modes x 5 scenarios x 2 cut points; leaky oracle is flagged; NOT a formal proof about any real system)
CANDIDATE_SPAM_HANDLED=TRUE (scope: modelled, 4 semantics compared, distortion quantified; spam inflates top-instrument admission share ~0.30 vs ~0.14 without spam, semantics reduce it by only 0.01-0.03; economic effect within noise; COOLDOWN hurts ranking policies)
STARVATION_MEASURED=TRUE (hard starvation ~0 for every policy; soft starvation and max denial higher for ranking methods; see 06)

BEST_SIMPLE_REFERENCE=SLOTHOUR
BEST_COMPLEX_REFERENCE=UNCERTAINTY_LCB (omega=0.6, kappa=0: the gain comes from shrinkage/pooling of repeated scores, not from the risk penalty)

COMPLEXITY_JUSTIFIED=FALSE (best complex vs best simple: +0.062 bps/avail-slot-hour, CI [0.027,0.097]: detectable but below the pre-registered practical margin 0.25)

ANY_DROP_IN_ALLOCATOR=FALSE
ANY_SCIENTIFIC_INVALIDATION=FALSE (limitations, not invalidations, are listed in 14)

FINAL_VERDICT=MULTIPLE_CAPACITY_METHODS_SUPPORTED
```

Explication ligne par ligne, avec statut de vérification :

- **ALGORITHMS_DISCOVERED=24** : nombre de familles cataloguées dans `R/02`. ✔ (24 lignes comptées).
- **ALGORITHMS_EXECUTED=12 … + 1 oracle** : 5 baselines + FIFO_SCREEN + 6 candidates = 12 implémentables ; l'oracle est un plafond non compté. ✔ (13 politiques dans H1).
- **TUNING_SCENARIOS** : 13 scénarios × 6 graines (1000–1005) pour ajuster les paramètres. ✔ (9984 lignes).
- **VALIDATION_SCENARIOS** : 13 × 8 graines (2000–2007) pour choisir parmi les 3 meilleures configurations du tuning. ✔ (3744 lignes).
- **HELDOUT_SCENARIOS** : 13 × 20 graines dans des mondes aux paramètres structurels différents (N=15, G=5…). ✔ (3380 lignes). Précision : « structurellement différents » = paramètres différents dans la *même famille de générateur* (`R/14` point 8).
- **SEEDS** : plages de graines. ✔ (min/max relevés dans les CSV : 1000–1005, 2000–2007, 3000–3019 ; H2 3000–3009 ✔). Les diagnostics 6000–8019 : plages déclarées dans `run_diag.py` (6000–6007 ; 7000–7009) et `run_div_stress.py` (8000–8019) ✔ ; le README écrit « 6000–7009 » (formulation légèrement différente, sans conséquence).
- **FIFO_FAILURE_SCENARIOS / FIFO_EQUIVALENT_SCENARIOS** : scénarios où au moins une candidate bat FIFO de plus de 0,25 avec IC_bas > 0.25 (échec) ou aucun (équivalent). ✔ recalculé (§3.3). Deuxième ligne : même chose contre FIFO_SCREEN. ✔.
- **BEST_SLOT_HOUR_REFERENCE** : la règle argmax pré-enregistrée désigne SLOTHOUR_SHADOW@0,25 (2,225 contre 2,216), mais c'est une égalité statistique (+0,009 [−0,026 ; +0,044]) ; on retient SLOTHOUR car sans paramètre. ✔ (2,225 > 2,216 ; IC ✔).
- **BEST_DIVERSIFICATION_REFERENCE** : CORR_AWARE à γ≈0,4–1 mais « faible / conditionnel » : aucun gain de M1 significatif, léger gain de risque seulement dans le cas « crise dans le meilleur groupe », coût de M1 si γ ≥ 1 en monde bénin/effondrement ; par défaut, SLOTHOUR. ✔ pour les chiffres (D6). Réserve : γ≈0,4–1 est **hors du γ gelé (0,1)** ; c'est donc une valeur issue du test de stress *post hoc*, pas de la procédure de tuning.
- **BEST_TURNOVER_REFERENCE** : SLOTHOUR ; SHADOW est à égalité, θ ≥ 0,5 dégrade, OLDEST_SLOT n'aide que dans des mondes de type S4/S6 et sous l'hypothèse de gain linéaire. ✔.
- **CAP3/4/6/10_SYNTHETIC_RESULT** : M1 de FIFO contre la meilleure implémentable (LCB) à chaque capacité, avec l'écart apparié et son IC. ✔ (H3 : 2,579 − 1,834 = 0,745 ; 2,340 − 1,814 = 0,526 ; 1,933 − 1,720 = 0,213 ; 1,310 − 1,312 = −0,002). Précision utile : « best implementable » pour K=10 est LCB (1,310) ou OLDEST_SLOT (1,315) : le rapport écrit « 1,31 vs 1,31 ».
- **NO_LOOKAHEAD_PROVEN=TRUE_WITHIN_HARNESS** : le test métamorphique (on redessine tout l'état futur caché à partir d'un instant t0, les décisions jusqu'à t0 doivent être identiques) passe pour 12 politiques × 4 ingestions × 5 scénarios × 2 coupures (150 et 300). L'oracle échoue au test (≥ 4 scénarios sur 5), donc le test est sensible. ✔ **[MA VÉRIF.]** j'ai relancé la suite : `77 passed`. Ce n'est PAS une preuve formelle et ne dit rien d'un système réel.
- **CANDIDATE_SPAM_HANDLED=TRUE** : le spam est modélisé, 4 sémantiques comparées, distorsion chiffrée ; la part max d'un instrument monte à ≈0,30 contre ≈0,14 ; les sémantiques la réduisent de 0,01 à 0,03 ; effet économique dans le bruit ; COOLDOWN nuit. ✔. Attention : « HANDLED=TRUE » veut dire « mesuré », pas « neutralisé » (le rapport le précise).
- **STARVATION_MEASURED=TRUE** : la famine a été mesurée avec quatre indicateurs. ✔.
- **BEST_SIMPLE_REFERENCE=SLOTHOUR** ; **BEST_COMPLEX_REFERENCE=UNCERTAINTY_LCB (ω=0,6, κ=0)** : le gain vient de la mise en commun des scores répétés (shrinkage), pas de la pénalité de risque. ✔ (D5 : κ n'aide pas). **[MA VÉRIF.]** ω>0,6 n'améliore pas (voir §7).
- **COMPLEXITY_JUSTIFIED=FALSE** : +0,062 < 0,25. ✔.
- **ANY_DROP_IN_ALLOCATOR=FALSE** : aucun composant externe n'est prêt à l'emploi. ? Non vérifiable au-delà des métadonnées PyPI (recherche limitée, aucune recherche GitHub/awesome-list documentée).
- **ANY_SCIENTIFIC_INVALIDATION=FALSE** : ni fuite, ni non-déterminisme. ✔ tests, ✔ hachages (300/300 du rapport ; 60/60 supplémentaires chez moi).
- **FINAL_VERDICT=MULTIPLE_CAPACITY_METHODS_SUPPORTED** : |T| = 6. ✔ au δ pré-enregistré ; **fragile** face à δ (voir §3.4 et §7).

Aucune clé du bloc n'est trompeuse au sens fort ; les deux points à corriger sont : la robustesse implicite du verdict à δ et le sens de « HANDLED ».

---

## 6. Contrôles de validité

### 6.1 Fuite / lookahead
- Séparation structurelle : les tableaux cachés ne sont jamais passés aux politiques (`B/src/engine.py` : `View`, `Pub` ne contiennent que l'observable ; `policy.on_close` reçoit `hold, net, gross` seulement à la fermeture). Lu dans le code ✔.
- Test métamorphique (`B/tests/test_capacity.py::test_prefix_decisions_invariant_to_future_hidden`) : 12 politiques × 4 modes = 48 cas, chacun sur 5 scénarios × 2 coupures ; jumeau du monde avec `resample_hidden_after` (E, D, Z et chemins de facteurs redessinés pour l'indice ≥ t0, événements/scores/infos publiques identiques). Canari : l'oracle doit échouer (`test_oracle_canary_is_detected_as_leaking`, seuil ≥ 4 sur 5). **[MA VÉRIF.] 77 tests passent en 19 s** (48 + 1 + 12 déterminisme + 1 monde + 12 capacité + 1 coût inconnu + 1 manquant + 1 éviction = 77 ✔).
- Limites du test (mon analyse) : (i) il ne couvre que 5 scénarios sur 13 et 2 coupures ; (ii) il redessine seulement les variables cachées, il ne teste pas de fuite via le générateur des scores (les scores contiennent l'edge réel E de l'instant t, bruité — c'est voulu) ni via l'indexation (par ex. `w.E[i,t]` lu au moment t) ; (iii) le pool de candidats expirés est réglé avec la durée cachée **pour le reporting seulement** (`rejected` : `w.hold(c.inst, c.t_last)` dans `engine.run`) : ce calcul n'influence pas les décisions (relu dans le code). ✔ conclusion : pas de fuite visible dans le harnais, mais cela ne prouve rien pour un pipeline réel.
- Ce que l'agent appelle « lookahead » côté politique : `on_emit` met à jour l'EWMA `m_i` **avant** la sélection, en incluant l'émission courante avec poids 0,2 : c'est de l'information disponible à l'instant t, donc légitime.

### 6.2 Déterminisme
- Tests unitaires (12 politiques rejouées deux fois : hash identique) ✔.
- `B/results/analysis/determinism_check.json` : `{"hash_mismatches": 0, "sampled": 300}` ✔ (script `verify_repro.py`).
- **[MA VÉRIF.]** 60 cellules H1 tirées au hasard (graine 123) relancées : 0 hash différent, écart maximal de M1 = 8,9 × 10⁻¹⁶ (bruit numérique flottant).

### 6.3 Contrôles négatifs / positifs
- Contrôle positif : l'oracle échoue au test de fuite (le test détecte bien une fuite) ✔.
- Contrôles négatifs : RANDOM, ROUND_ROBIN, EQUAL_QUOTA sont des « nuls » ; S12 (tout égal) et S1 (demande faible) doivent ne pas montrer de différences majeures : c'est le cas pour S1 (toutes ≈ 0,83). Pour S12, les candidates gagnent tout de même de +0,24 à +0,46 : voir §7 (réserve).
- `UNKNOWN_COST ≠ ZERO_COST` : test unitaire (croyance zéro admet ≥ autant que connue ; conservative ≤ zéro) ✔ ; plus démonstration D3.
- Score manquant ≠ score négatif : test (`sc()` renvoie la moyenne globale, `PRIOR_SCORE`=15 quand rien n'est encore vu) ✔.
- Éviction : test qu'elle est appliquée, avec coût intégral (`evict_frac>0`) ✔ (mais le test ne vérifie pas la valeur des gains tronqués).

### 6.4 Erreurs corrigées en cours de route, écarts au protocole déclarés
- `R/13` : « two mis-statements about OLDEST_SLOT and heavy-tail durations in draft text were corrected against the tables before commit; no result data changed » — non vérifiable (les brouillons n'existent pas dans le dépôt) ? .
- Écarts déclarés (`R/05`, `R/14`) : analyses (paires ciblées, D6, OSS) post-hoc ; hash de code du pré-enregistrement couvre seulement les 5 fichiers de base ; wall-time H1 mesuré sous charge 4 processus (référence : `compute_cost_serial.csv`).
- Écart à mon avis **non déclaré** : `R/13` affirme (indirectement) la robustesse du verdict à δ (§3.4).
- Écart mineur : la note du README « diagnostics 6000-7009, div-stress 8000-8019 » contre le bloc final « diagnostics 6000-8019 » (fusion des plages) ; sans conséquence.

---

## 7. Critique indépendante

### 7.1 Points faibles et choix fragiles

1. **Le verdict « plusieurs méthodes » repose sur δ=0,25, choisi par les auteurs (INFERENCE).** Recalcul : à δ=0,5 la règle pré-enregistrée donne B = ∅ ⇒ `FIFO_REMAINS_SUFFICIENT_REFERENCE` (LCB bat FIFO de 0,497, à 0,003 du seuil). Le rapport dit « still multiple ». Au sens des règles écrites d'avance, le verdict change avec un seuil raisonnable. La conclusion défendable est : « dans ce générateur, le classement par score bat FIFO de ≈ 0,4–0,5 ; qu'on appelle cela “nettement mieux” dépend de la marge exigée ». (✘ écart rapport vs résultats bruts, ma vérification.)
2. **Le monde est calibré en faveur des méthodes à score.** Le score contient l'edge réel de l'instant + bruit indépendant (`s = a + b·E + τ·ξ`), et l'ordre d'arrivée est indépendant de la qualité par construction (`R/14` points 1–2). Dans un tel monde FIFO ne peut pas gagner : la conclusion « FIFO est mauvais » est **en grande partie construite**. Le seul vrai test de robustesse est le diagnostic D2/D4 (score inversé/mal calibré), non le held-out.
3. **Held-out = même famille de générateur** (N, G, τ, CV, plages différents) : une généralisation hors famille (autre structure d'edge, non-stationnarité différente) n'est pas testée. 20 graines par scénario : IC par scénario de ±0,1 à ±0,3 ; les indicateurs `*` par scénario ne sont pas corrigés des comparaisons multiples (13 scénarios × 6 méthodes × … ).
4. **Macro-moyenne à poids égaux sur 13 scénarios choisis par les auteurs.** 5 scénarios (S1, S2 quasi triviaux ; S10, S11, S12) sont peu informatifs ; 5 sont de saturation forte. La proportion « +21 % à +28 % » dépend de ce mélange. Une pondération différente change le chiffre.
5. **Les coûts sont connus par défaut en H1** (`belief="known"`) : les politiques voient le vrai coût. Optimiste. D3 montre une robustesse au mauvais coût, mais seulement sur S3 et S6, validation, 8 graines.
6. **Grille en bord.** ω du LCB gelé sur la valeur la plus haute testée (0,6) ; θ du SHADOW à la plus basse (0,25, mais θ=0 = SLOTHOUR donc couvert). **[MA VÉRIF.]** j'ai relancé UNCERTAINTY_LCB (κ=0, SCORE_UPDATE) sur la validation (13 scénarios, graines 6000–6007, mêmes que D5) : ω=0,6 → 2,418 (identique à D5 ✔), ω=0,8 → 2,407, ω=0,9 → 2,390, ω=1,0 → 2,409. Donc **pas d'amélioration au-delà de 0,6** : la crainte de bord de grille est écartée pour ce cadre. **Constat en plus, à ne pas sur-interpréter** : ω=1,0 (le score de l'émission courante est ignoré, seul l'historique EWMA compte — mais l'EWMA inclut déjà l'émission courante avec poids 0,2) donne presque autant (2,409) : dans ce générateur, l'information utile est surtout la moyenne persistante par instrument (μ_i + régimes + AR(1), φ=0,9). L'avantage de LCB tient donc à cette structure : dans un monde où l'edge de chaque événement serait indépendant, la mise en commun ne servirait pas. (Mon calcul, non présent dans le dépôt, 8 graines, split validation.)
7. **Ce qui n'est pas dans le score composite** : la conception refuse un score composite (bien) ; mais le verdict, lui, s'appuie uniquement sur M1. Les métriques de risque/équité qui se dégradent (famine douce ×2–7, occupation plus volatile : écart-type d'occupation FIFO 0,046 → SLOTHOUR 0,128 en S8, SHADOW 0,194 ✔) ne pèsent pas dans la règle de verdict.
8. **La baseline OLDEST_SLOT** : forte estimation (+0,185) mais très dépendante de A3 (accumulation linéaire du gain avec le temps de détention) ; dans le monde simulé, une sortie anticipée « ne perd que le gain non encore acquis », ce qui est optimiste pour la préemption. Le rapport le signale ; je le souligne car il est central pour toute discussion de « turnover ».
9. **Un unique coût constant par admission** ; pas de glissement/impact dépendant de la rotation ou de la taille ; pas d'exécution partielle (`R/14` point 5). Or la question « turnover » est justement là où l'impact de coût se joue.
10. **Le plafond oracle est un glouton**, non l'optimum hors-ligne (`R/01`, `R/14` point 13). « Regret vs oracle » mélange perte d'allocation et bruit inévitable ; ne pas lire 12,6 % comme une marge de progrès atteignable.
11. **Sonde OSS légère.** Classer des paquets sans lire le code ni les tickets ouverts n'est pas ce que demande `claude.md`. Le rapport le reconnaît.
12. **Pré-enregistrement auto-attesté** (§2.7).

### 7.2 Ce que les chiffres ne prouvent PAS
- Que SLOTHOUR ou LCB fonctionnerait sur des données réelles : les scores y sont peut-être peu informatifs, l'ordre d'arrivée peut porter de l'information, et la calibration n'est pas garantie.
- Aucune information sur `max_open_positions`, sur la « bonne » capacité ni sur AurumShift (le rapport le dit).
- Que « la diversification ne sert à rien » : elle est testée dans un monde où l'exposition de groupe est déjà plafonnée par la structure (≤ 3 instruments par groupe, une position par instrument, K=4, G=5 : HHI de groupe 0,22–0,23 contre 0,20 idéal).
- Que les bandits sont inutiles : un seul design de features, 3 valeurs d'α.
- Que COOLDOWN est mauvais en général : il l'est parce qu'il jette des scores frais dans ce simulateur.
- Que le score-gaming et l'inversion sont « ouverts » : ils sont non atténués, mais leur ampleur n'est pas résolue (IC larges, 10 graines).

### 7.3 Écarts rapports vs résultats bruts et contradictions internes

| # | constat | type | référence |
|---|---|---|---|
| 1 | Sensibilité du verdict à δ=0,5 : rapport « still multiple » ; règle pré-enregistrée appliquée aux écarts publiés → B vide → FIFO suffisant | ✘ écart (mon jugement, vérifié par recalcul) | `R/13` « Sensitivity of the verdict to δ » vs `prereg.json` VERDICT + `H1_paired_macro.csv` |
| 2 | « SCORE_RANK falls *below* FIFO » en inversion (résumé exécutif #9 ; `R/11` #12) : IC [−0,509 ; +0,144] contient 0 ; l'échelle D2 (même mécanisme) donne l'inverse (+0,346) | affirmation non soutenue statistiquement / contradiction interne apparente | `D4_failure_modes.csv`, `D2_score_quality_table.csv` |
| 3 | « OLDEST_SLOT (2,88) est au moins aussi bon que toute politique à score » en inversion : +0,15 vs SLOTHOUR, IC [−0,205 ; +0,489] | non significatif | idem |
| 4 | Le résumé dit « θ≥0,5 collapses » ; l'effondrement net commence à 0,75 (2,344 → 2,053 → 1,068) | léger sur-énoncé | `D5_param_sensitivity_table.csv` |
| 5 | IC de la même quantité qui varient légèrement selon la source (LINTS−SLOTHOUR : [−0,05 ; +0,02] dans `R/02` ; [−0,054 ; +0,017] dans `H1_vs_best_simple.csv` ; [−0,057 ; +0,016] dans le JSON de verdict) | bruit de bootstrap (graines de rééchantillonnage différentes) ; sans conséquence | `R/02`, `R/13`, CSV |
| 6 | `H3_gaps_by_K.csv` « FIFO_to_best_impl_gap » (0,878 en K=3) est biaisé par la sélection du maximum par scénario ; le bloc final utilise l'écart non biaisé (0,745) | présentation à surveiller | `H3_gaps_by_K.csv` |
| 7 | `run_div_stress.py` docstring annonce un monde à G=2 groupes non exécuté | commentaire trompeur, pas un résultat | `B/src/run_div_stress.py` |
| 8 | `F_starve_skew` : « 0,07 » dans le rapport, 0,075 dans le CSV | arrondi | `D4_failure_modes_all_metrics.csv` |

Points où le rapport est **exact** sur tout ce que j'ai testé : macro M1 de 13 politiques (13/13 égaux à 3 décimales), écarts appariés et IC (à ±0,005), tables de coût D3, échelle D2, robustesse D1, sensibilité D5, table H3, hash du gel, tests et déterminisme.

### 7.4 Vérifications numériques (≥ 10 chiffres clés)

| # | chiffre du rapport | source contrôlée | statut |
|---|---|---|---|
| 1 | M1 held-out : FIFO 1,781 ; SLOTHOUR 2,216 ; LCB 2,278 ; oracle 5,719 (13 politiques) | `H1_primary.csv` recalculé | ✔ |
| 2 | 3380 lignes H1 = 13×13×20 ; 6760 lignes H2/H3 | comptage | ✔ |
| 3 | SLOTHOUR − FIFO = +0,435 [0,388 ; 0,479], 13/13 | H1 + mon bootstrap (0,435 [0,389 ; 0,481], 13) | ✔ |
| 4 | LCB − SLOTHOUR = +0,062 [0,026 ; 0,099], 10/13 | H1 + mon bootstrap (0,062 [0,026 ; 0,096], 10) | ✔ |
| 5 | SHADOW − SLOTHOUR = +0,009 [−0,026 ; +0,044] ; significatif en S4 (+0,258) | idem + `targeted_pairs.csv` | ✔ |
| 6 | Échecs de FIFO à δ=0,25 : S12, S3, S4, S5, S5b, S7, S8, S9 | JSON de règles | ✔ |
| 7 | Hash gel `frozen_params.json` et hash `src` | `git show` + sha256 | ✔ |
| 8 | 77 tests passent | `pytest` | ✔ |
| 9 | 300/300 hash identiques ; 60/60 chez moi | `determinism_check.json` + mon échantillon | ✔ |
| 10 | Capacité : K=3 +0,75 ; K=4 +0,53 ; K=6 +0,21 ; K=10 ≈0 (−0,002) | `H3_capacity_sweep.csv` / `H3_paired_vs_FIFO.csv` | ✔ |
| 11 | Famine douce 0,059 (LCB) vs 0,008 (RR) ; dure max 0,005 | `H1_macro_all_metrics.csv` | ✔ |
| 12 | COOLDOWN coûte −0,252 à SLOTHOUR en S10 | `D4_spam_paired_vs_RAW.csv` | ✔ |
| 13 | Coût ×3 + croyance zéro : FIFO_SCREEN 1,222 → 0,552 ; OLDEST −1,163 | `D3_cost_table.csv` | ✔ |
| 14 | Compute LINTS ≈ 24× SLOTHOUR (42,78 vs 1,78 ms) | `compute_cost_serial.csv` | ✔ |
| 15 | S4 capture HQ : 0,535 / 0,729 / 0,767 | `H1_primary.csv` | ✔ |
| 16 | S6 durée moyenne SCORE_RANK 12,0 h contre 7,8 h SLOTHOUR | `H1_primary.csv` | ✔ |
| 17 | Sensibilité verdict à δ=0,5 (« multiple ») | recalcul de B | ✘ |
| 18 | « SCORE_RANK < FIFO en inversion (D4) » | paires appariées D4 | ? non significatif (IC contient 0) |
| 19 | ω>0,6 non testé (limite) | mon extension | ✔ comblé (aucun gain) |
| 20 | Littérature (Agrawal–Goyal, KPP, etc.) | non re-vérifiée par l'étude | ? non vérifiable |
| 21 | « Deux mis-statements corrigés avant commit » | brouillons absents | ? non vérifiable |
| 22 | Versions PyPI (scipy 1.18.1, etc.) | `oss_probe.json` lu, PyPI non ré-interrogé | ? (valeurs cohérentes avec le JSON) |

---

## 8. Points de comparaison à vérifier contre l'étude A (non lue)

L'étude A (branche `claude/risk-capacity-turnover-v1`, fichiers `bench/capacity_v1/py/*` déjà dans `main`) est réalisée par un autre analyste ; je n'y ai pas touché. Points à contrôler point par point :

1. **Verdict final** et règle qui le produit : est-ce aussi `MULTIPLE_CAPACITY_METHODS_SUPPORTED` ? Quelle marge d'équivalence (δ) et quelle règle de robustesse ? Le verdict change-t-il avec δ ? (ici : oui entre 0,25 et 0,5).
2. **FIFO** : suffit-il ? Dans quels scénarios échoue-t-il ? L'étude A trouve-t-elle aussi que FIFO ≈ round-robin ≈ aléatoire ? (ici : indistinguables, ~1,74–1,78.)
3. **Ordre des méthodes** : classement par valeur nette par heure de slot vs classement par valeur nette ; écart mesuré ; y a-t-il un cas où le classement par heure perd ? (ici : +0,070 [0,031 ; 0,109] ; perd en score parfait ; gagne en S6, S5b.)
4. **Prix fantôme / seuil d'opportunité** : θ optimal, effondrement à quel seuil ? (ici : θ=0,25 ok, 0,5 dégrade, ≥0,75 s'effondre.)
5. **Corrélation / diversification** : effet sur M1 et sur le drawdown ; le gain de risque n'existe-t-il que dans le scénario « crise dans le meilleur groupe » ? (ici : oui, +40,7 sur le pire 24 h, M1 inchangé.)
6. **Bandits** : ont-ils été codés, avec quel résultat et quel coût de calcul ? (ici : LinTS ≈ SLOTHOUR, 24× le calcul.)
7. **Mise en commun des scores (shrinkage)** : présent ? (ici : c'est ce qui distingue LCB, +0,062.)
8. **Préemption / rotation** : politique équivalente à OLDEST_SLOT ? hypothèse d'accumulation du gain ? sensibilité au coût ? (ici : +0,185 vs FIFO ; −1,163 à coûts ×3.)
9. **Capacité K** : quelle grille, charge offerte fixée ou proportionnelle ? Résultat monotone en rareté ? (ici : gain +0,75 → +0,53 → +0,21 → ≈0 pour K=3/4/6/10, charge fixée.) Toute recommandation de plafond dans A serait à examiner à part : ici, aucune.
10. **Spam, famine** : sémantiques d'ingestion comparées ; COOLDOWN nuisible ? famine douce chez les méthodes de classement ? coût de l'équité ?
11. **Séparation des jeux** : tuning / validation / held-out réellement distincts, pré-enregistrement daté avant le held-out, graines, gel des paramètres (hash) ; nombre de graines par scénario (ici : 6 / 8 / 20).
12. **Test de fuite** : équivalent métamorphique ? canari oracle ?
13. **Métrique primaire** : même définition (gain net par slot-heure disponible) ? Les chiffres ne sont comparables que si le générateur, l'unité et la charge sont alignés ; sinon comparer seulement les **directions** et les **rangs**.
14. **Hypothèses de générateur** : score calibré, ordre d'arrivée sans information, accumulation linéaire, une position par instrument, TTL=4, coût constant : lesquelles diffèrent chez A ? Les divergences éventuelles sont probablement dues à ces choix, plus qu'aux algorithmes.
15. **Sonde OSS** : mêmes bibliothèques ? lecture du code ou métadonnées seulement ?
16. **Reconnaissance des limites** : l'étude A signale-t-elle aussi que le résultat est purement synthétique et ne dit rien sur `max_open_positions` ?

Remarque de structure : la PR n°8 indique que les deux implémentations coexistent avec des chemins de fichiers différents (`py/*` pour A, `src/`, `tests/`, `configs/`, `results/{tuning,validation,heldout,diagnostics,analysis}/` pour B) ; la fusion des deux dans `bench/capacity_v1/` est à trancher par un humain.

---

## 9. Reproductibilité

### 9.1 Comment relancer (README de la lane, `B/README.md`)
Dépendances : numpy, pandas, scipy, pytest, Python 3.11 (les 4 premiers sont installables par pip ; **aucun fichier de dépendances (requirements) n'est fourni**).
```
PYTHONPATH=src pytest -q tests           # 77 tests, ≈ 19 s (mesuré chez moi)
python3 src/run_tuning.py                # ~1,5 min sur 4 cœurs (déclaré) ; écrit tuning/, validation/, configs/frozen_params.json
python3 src/run_heldout.py               # ~2 min (déclaré) ; refuse d'écraser un résultat existant
python3 src/run_diag.py && python3 src/run_div_stress.py
python3 src/analysis.py && python3 src/analysis_diag.py && python3 src/analysis_extra.py && python3 src/verify_repro.py && python3 src/oss_probe.py   # oss_probe : accès réseau PyPI
python3 src/make_reports.py              # régénère les tableaux des rapports
```
Temps mesurés chez moi : 60 cellules H1 en 2,3 s (≈ 0,04 s par cellule) ; l'extension LCB de 13 scénarios × 8 graines × 4 valeurs de ω + 2 références en 19 s. Le held-out entier (≈ 20 000 cellules) doit donc tenir en quelques minutes sur quelques cœurs, en accord avec « ~2 min » déclarés.

### 9.2 Ce qui est fourni
Code du simulateur, du générateur, des politiques, des tests, des analyses ; paramètres gelés et pré-enregistrement ; **tous les résultats bruts** (tuning, validation, held-out H1/H2/H3, diagnostics D1–D6) et les tables agrégées ; le journal `logs/diag.log` (5 lignes : « D1 2600 », « D2 728 », « D3 2496 », « D4 2210 », « D5 2600 ») ; les rapports 00–14.

### 9.3 Ce qui manque
- Pas de fichier de dépendances ni d'environnement figé (versions numpy/pandas non indiquées).
- Pas de journal de l'exécution du tuning ni du held-out (seul `diag.log`).
- Le pré-enregistrement n'a pas d'horodatage externe.
- La régénération complète du held-out ne réécrit pas de fichiers si `heldout/H1_primary.csv` existe (par conception) ; pour reproduire il faut travailler dans un dossier vide.
- `make_reports.py` (74 Ko) génère les tables des rapports à partir des CSV : je ne l'ai pas relancé (`R/` ↔ CSV vérifiés à la main sur les chiffres clés, §7.4).
- `oss_probe.py` dépend du réseau et de l'état de PyPI à la date d'exécution ; le JSON fourni est un instantané non rejouable exactement.

---

## 10. Implications pratiques pour AurumShift — pistes « à adjuger plus tard »

Rien ici n'affirme une compatibilité avec le code privé d'AurumShift, que je ne connais pas et que ce dépôt ne contient pas. Ce sont des idées à confronter plus tard aux vraies données et au vrai dépôt local.

1. **Piste « mesurer d'abord la rareté »** : le gain du classement dépend de la rareté des places (le résultat de la lane tombe à ≈0 quand les places sont abondantes). À adjuger : dans les journaux locaux, à quelle fréquence les places sont-elles toutes prises alors que des candidats attendent ? Si rarement, aucune sophistication n'est utile.
2. **Piste « comparer trois règles seulement »** : arrivée-ordre (FIFO), écran net > 0, classement par net attendu / durée attendue. Les autres méthodes n'ont pas justifié leur complexité dans la simulation. À adjuger : rejouer ces trois sur un historique local (« replay » : rejouer des décisions passées).
3. **Piste « le coût inconnu n'est pas zéro »** : les écrans (seuil sur le net) sont plus sensibles à une mauvaise croyance de coût que le classement. À adjuger : si les coûts locaux sont incertains, préférer un classement.
4. **Piste « estimer la durée de détention »** : le classement par heure suppose une durée attendue apprenable par instrument. À adjuger : est-ce le cas localement ?
5. **Piste « mesurer la calibration des scores »** : la simulation montre que tout se dégrade quand les scores sont inversés ou mal calibrés, et qu'aucune politique ne le détecte en ligne. À adjuger : un contrôle de calibration (prédit vs réalisé par tranche de score) est un prérequis à toute allocation par score.
6. **Piste « suivre la famine sans l'imposer »** : indicateurs de famine à surveiller, pas garde-fous (coût simulé de l'équité forcée ≈ 0,45 bps/slot-heure). À adjuger : l'équité entre instruments est-elle une exigence métier ?
7. **Piste « spam »** : DEDUP_LATEST ou SCORE_UPDATE sont inoffensifs dans la simulation, COOLDOWN nuit. À adjuger : les vrais flux répètent-ils des candidats ?
8. **Piste « préemption »** : à ne considérer que si un modèle défendable de l'accumulation du gain existe localement, et avec des coûts d'échange connus (simulation : négatif à coûts ×3).
9. **Piste « diversification »** : n'a servi que comme couverture de queue à coût nul dans un cas précis (crise dans le meilleur groupe). À adjuger seulement si le drawdown est un objectif explicite.
10. **Piste « composants »** : `scipy` comme référence de test d'assignation ; aucun autre composant n'est prêt (métadonnées seules). Aucune adoption sans lecture du code (doctrine claude.md).
11. **Piste « aucune conclusion sur un plafond de positions »** : la courbe de capacité est descriptive ; elle ne doit pas alimenter un choix de `max_open_positions`.

---

## 11. Questions ouvertes et suites recommandées (classées par valeur)

1. **Valeur maximale — Tester hors de la famille du générateur** : un second générateur structurellement différent (edge événementiel non persistant, ordre d'arrivée corrélé à la qualité, gain non linéaire dans le temps) pour voir si le classement par score résiste. Sans cela l'écart FIFO-classement reste partiellement construit.
2. **Rejouer sur des données réelles locales (replay)**, avec vraies durées de détention, vrais coûts et vrais scores : c'est la seule voie pour transformer le verdict en décision (étape prévue par claude.md).
3. **Repréciser le verdict selon δ** : publier le verdict pour δ ∈ {0,05 ; 0,1 ; 0,25 ; 0,5} avec la règle complète, y compris la règle B vide. Corriger l'énoncé de `R/13` (§3.4).
4. **Corriger ou nuancer l'énoncé « SCORE_RANK < FIFO en inversion »** ; refaire D4 avec plus de graines (≥ 50) et mêmes scénarios que D2.
5. **Détection en ligne d'un score inversé/gonflé** (suivi de calibration, bonus/malus par instrument selon prédit vs réalisé) : mode de défaillance ouvert (#1, #12).
6. **Modèle de coût dépendant de la rotation/taille** (glissement, impact) : nécessaire pour juger la préemption et tout « turnover ».
7. **Monde avec groupes larges et K ≫ G, et cas spam à edge négatif** : les deux cas où la diversification et le filtrage de spam auraient le plus de levier ; non testés.
8. **Garde-fous d'équité légers** (bonus d'ancienneté, part minimale) : le seul garde-fou testé coûte tout le gain.
9. **Bandit mieux conçu / LinUCB / bandits avec sacs à dos** si (et seulement si) des données de retour sont disponibles ; sinon PARK.
10. **Lecture réelle du code des bibliothèques OSS retenues** (MABWiser, scipy.optimize.milp/HiGHS) avant tout ADOPT.
11. **Correction de comparaisons multiples** (ou test global) pour les indicateurs par scénario.
12. **Pré-enregistrement à horodatage externe** (tag signé, dépôt séparé) pour les prochaines lanes.

---

## 12. Index des fichiers lus

Rapports (`reports/008_risk_capacity_turnover/`, lus intégralement) :
- `00_EXECUTIVE_SUMMARY.md` — question, ce qui a été fait, 9 constats, bloc final, frontières.
- `01_PROBLEM_FORMULATION.md` — cadre (K places, information visible/cachée, sémantiques d'ingestion, métriques, coût inconnu).
- `02_ALGORITHM_LANDSCAPE.md` — 24 familles et statut EXEC/PARK/REJECT, liens avec la liste « turnover » de la mission.
- `03_BASELINES.md` — 5 baselines + FIFO_SCREEN ; table macro et table par scénario (13 politiques).
- `04_SYNTHETIC_PROTOCOL.md` — monde, scénarios, tests de fuite, splits.
- `05_HELDOUT_PROTOCOL.md` — ordre des étapes, paramètres gelés, règles pré-enregistrées.
- `06_SLOT_ECONOMICS.md` — métriques macro, famine, spam (ingestions).
- `07_DIVERSIFICATION.md` — CORR_AWARE, stress D6.
- `08_TURNOVER.md` — SLOTHOUR, SHADOW, OLDEST_SLOT, coût, échelle de qualité de score.
- `09_CAPACITY_SENSITIVITY.md` — H3 (K=3,4,6,10).
- `10_HELDOUT_RESULTS.md` — H1 complet, robustesse, sensibilité aux paramètres, règles FIFO.
- `11_FAILURE_MODES.md` — 12 modes de défaillance.
- `12_OSS_COMPONENTS.md` — sonde PyPI, classifications.
- `13_ADJUDICATION.md` — adjudication, simple vs complexe, machinerie de verdict, candidats à évaluer localement, bloc final.
- `14_LIMITATIONS.md` — 18 limites.

Code et configuration (`bench/capacity_v1/`) :
- `README.md` — structure, commandes de reproduction, graines.
- `.gitignore` — non lu en détail (39 octets, fichier trivial).
- `configs/prereg.json` — pré-enregistrement (règles, seuils, hash).
- `configs/frozen_params.json` — paramètres gelés par politique.
- `src/common.py` — exécution parallèle, écriture/lecture CSV.
- `src/engine.py` — simulateur, ingestion, éviction, métriques (lu en entier).
- `src/policies.py` — 12 politiques + oracle + grilles (lu en entier).
- `src/world.py` — générateur, scénarios, jumeau de test de fuite (lu en entier).
- `src/run_tuning.py`, `run_heldout.py`, `run_diag.py`, `run_div_stress.py`, `verify_repro.py`, `oss_probe.py` — pilotes d'exécution (lus en entier).
- `src/analysis.py`, `analysis_diag.py`, `analysis_extra.py` — analyses (lus en entier).
- `src/make_reports.py` (74 Ko) — générateur des rapports : **non lu** (générateur de texte ; les tables des rapports ont été vérifiées contre les CSV).
- `tests/test_capacity.py` — 77 tests (lu en entier, exécuté).
- `logs/diag.log` — 5 lignes de comptage des lignes de diagnostics.

Résultats (`bench/capacity_v1/results/`) :
- `tuning/tuning_objective.csv` (128 configs), `tuning/tuning_runs.csv` (9984 lignes) — lus et agrégés.
- `validation/validation_objective.csv` (36 configs), `validation/validation_runs.csv` (3744 lignes) — idem.
- `heldout/H1_primary.csv` (3380), `H2_ingest_matrix.csv` (6760), `H3_capacity_sweep.csv` (6760) — recalculés.
- `diagnostics/D1_robustness.csv`, `D2_score_quality.csv`, `D3_cost.csv`, `D4_failure_modes.csv`, `D5_param_sensitivity.csv`, `D6_diversification_stress.csv` — D2, D3, D4 et D5 agrégés via les tables d'analyse et recalculés en partie (D4 : paires appariées) ; D1 et D6 lus via tables agrégées.
- `analysis/` : `H1_macro_all_metrics.csv`, `H1_paired_macro.csv`, `H1_paired_perscenario.csv` (échantillonné), `H1_perscenario_all_metrics.csv` (échantillonné), `H1_vs_best_simple.csv`, `H1_vs_random.csv`, `H1_fifo_dims.csv` (non lu en détail), `H1_rules_and_verdict_machinery.json`, `H2_macro_by_ingest.csv`, `H2_S10_by_ingest.csv` (recalculés depuis le brut), `H3_macro_by_K.csv`, `H3_gaps_by_K.csv`, `H3_paired_vs_FIFO.csv`, `D1_robustness_table.csv`, `D1_score_noise_curve.csv`, `D2_score_quality_table.csv`, `D3_cost_table.csv`, `D4_failure_modes_all_metrics.csv`, `D4_spam_ingest_S10.csv` (non lu en détail), `D4_spam_paired_vs_RAW.csv`, `D5_param_sensitivity_table.csv`, `D6_diversification_stress_table.csv`, `D6_paired_vs_SLOTHOUR.csv`, `targeted_pairs.csv` (échantillonné), `compute_cost_serial.csv`, `determinism_check.json`, `oss_probe.json` (début lu).

Autres sources : `claude.md` (doctrine du dépôt, lu) ; PR n°8 via l'API GitHub (titre, corps, dates, état) ; historique git (`git log`, `git show`, `git diff`) pour les commits `ad2adda`, `c64cbb4`, `0ff4f71`. **Non lus** : la branche `claude/risk-capacity-turnover-v1` et les fichiers `bench/capacity_v1/py/*` de `main` (étude A, autre analyste) ; le journal de discussion éventuel de la PR (commentaires) : non consulté.

Expériences propres exécutées dans un dossier temporaire (rien de poussé, aucune branche modifiée) : suite de tests (77 passés) ; 60 cellules H1 rejouées (0 divergence) ; bootstrap apparié (6 comparaisons) ; règle B pour δ ∈ {0,1 ; 0,25 ; 0,5} ; extension de UNCERTAINTY_LCB à ω ∈ {0,8 ; 0,9 ; 1,0} ; paires D4 de F_inversion et F_score_gaming.
