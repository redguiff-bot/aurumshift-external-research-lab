# Analyse approfondie — Lane 008 (étude A) : capacité de risque et turnover

Analyste : Claude (analyse indépendante, lecture seule du dépôt).
Lecteur visé : Jean-François (pas de connaissance de GitHub ni du trading quantitatif : chaque terme technique est expliqué à sa première occurrence).

Conventions de ce document :
- **Le rapport affirme** = ce qui est écrit dans les rapports 00 à 13 de la branche.
- **Vérifié** = j'ai recalculé le chiffre moi-même à partir des fichiers de résultats bruts (ou j'ai relancé le code). Symboles : ✔ vérifié / ✘ écart / ? non vérifiable.
- Les chemins entre parenthèses sont relatifs à la racine du dépôt, sur la branche `origin/claude/risk-capacity-turnover-v1` (sauf mention contraire). Pour lire un fichier sans checkout : `git show origin/claude/risk-capacity-turnover-v1:<chemin>`.
- Mes propres recalculs ont été faits dans un dossier temporaire (extraction de la branche via `git archive`) : aucune branche du dépôt n'a été modifiée, rien n'a été poussé. Seul ce fichier a été écrit.
- Étiquettes de preuve du dépôt (`claude.md`) : PROVEN, OBSERVED, DOCUMENTED_CLAIM, INFERENCE, UNKNOWN. Je les réutilise. Les étiquettes « ✔/✘/? » sont les miennes.

---

## 0. Fiche d'identité

| Élément | Valeur |
|---|---|
| Lane | 008 (étude A) — « Risk capacity & turnover allocation V1 » (mission `AURUMSHIFT_EXTERNAL_RISK_CAPACITY_AND_TURNOVER_ALLOCATION_V1`) |
| Branche complète | `origin/claude/risk-capacity-turnover-v1` (tête = commit `ea3fc74`) |
| PR #10 | « 008 risk-capacity & turnover allocation study: pre-registered held-out results and reports » — **ouverte, en brouillon (draft)**, créée le 2026-09-29 16:02:20 UTC, 9 commits, 91 fichiers modifiés, +9 664 / −95 lignes, mergeable_state « clean » (lu via l'API GitHub). |
| PR #6 | **Mergée** dans `main` (merge `1a449df`, 2026-09-29 15:59 +0200). Elle n'a capturé que l'état partiel (WIP) : commits `1d676ff` (13:46 UTC, simulateur + politiques + tests de fuite), `588dc4b` (log de tuning), `da2f7c4` (13:51 UTC, résultats de tuning tour 1 + grilles étendues). Rien du held-out (l'évaluation finale) ni des rapports. |
| Commits propres à la PR #10 (ordre chronologique, UTC) | `0c8c6ac` 13:59 (log tuning tour 2) ; `6f03b85` 14:12 (résultats tuning tour 2) ; `23f603f` 14:14 (log validation) ; `3bbc451` 15:11 (validation + PRÉ-ENREGISTREMENT v1) ; `7c991af` 15:13 (run 1 déclaré « superseded », remplacé) ; `c4d0b86` 15:29:02 (re-tuning + validation + PRÉ-ENREGISTREMENT v2) ; `cb13041` 15:29:35 (held-out lancé) ; `db7e45a` 15:49 (résultats held-out + verdict) ; `ea3fc74` 16:02 (rapports 00–13). |
| Durée mesurée du held-out | 1 014 s (~17 min) pour 450 « jobs » (`bench/capacity_v1/results/heldout.log`). |
| Fichiers de la lane | 94 fichiers dans `reports/008_risk_capacity_turnover/` (14 rapports .md) + `bench/capacity_v1/` (80 fichiers : 11 scripts Python, 1 README, 1 pré-enregistrement JSON, résultats, tables, `superseded_run1/`). Taille cumulée ≈ 36,3 Mo (`git ls-tree -l`), dont ≈ 12,3 Mo pour `heldout_raw.csv.gz`. |
| Nature | Étude **purement synthétique** (simulateur écrit par l'analyste). Aucun code privé AurumShift lu, aucune donnée de marché réelle. |
| Verdict final (machine) | `FINAL_VERDICT=CAPACITY_ALLOCATION_REFERENCE_SUPPORTED`, méthode de référence `COMPOSED` (`bench/capacity_v1/results/heldout_verdict.json`). |
| Force du verdict | **Faible à modérée, et fragile** : (i) la marge de `COMPOSED` sur le simple classement par valeur nette est +0,023 pour une barre à 0,02 (marge 0,003) ; (ii) avec une marge d'équivalence à 0,03 le même jeu de données donne `MULTIPLE_CAPACITY_METHODS_SUPPORTED` ; (iii) **mon propre test** montre que le verdict dépend d'une seule famille de scénarios « spam » (§7). Ce que le verdict établit solidement : « FIFO seul n'est pas suffisant dans le simulateur » ; ce qu'il n'établit pas : que `COMPOSED` soit *la* référence. |

Petit lexique immédiat (utilisé partout ensuite) :
- **Slot (emplacement)** : une « case » de capacité. Ici, une position ouverte occupe un slot. `C` = nombre de slots. Le rapport dit explicitement que `max_open_positions` (paramètre AurumShift) n'est *pas* recommandé de changer.
- **Opportunité (« opp »)** : un candidat de trade qui se présente et attend au plus 3 heures avant de disparaître.
- **FIFO** (first in, first out) : servir le plus ancien candidat d'abord. C'est la référence « naïve » à battre.
- **bps** (basis points) : 1 bps = 0,01 %. L'unité de gain du simulateur.
- **dz** : différence de gain par slot-heure entre deux politiques, divisée par une échelle typique de valeur des opportunités du monde simulé (voir §2). Sert à comparer des scénarios d'échelles différentes. C'est une unité normalisée, pas des bps.
- **Held-out** : jeu de test final, jamais utilisé pour régler quoi que ce soit.
- **Pré-enregistrement** : règles de décision écrites et figées *avant* de regarder les résultats du test final.
- **IC 95 % (intervalle de confiance)** : fourchette dans laquelle la vraie valeur se situe plausiblement ; ici obtenue par *bootstrap* (rééchantillonnage aléatoire des mondes simulés).

---

## 1. Mission et question posée

### 1.1 Reformulation simple
AurumShift (en mode recherche/paper : pas de capital réel) ne peut avoir qu'un nombre limité de positions ouvertes en même temps. Quand plus de candidats se présentent qu'il n'y a de places, **comment choisir lesquels méritent une place rare**, sans tricher avec le futur (« lookahead »), sans sur-régler sur les données (« overfitting ») et sans supposer un capital caché ?

Le rapport 01 formule : `C` slots identiques (3, 4, 6, 10 en « sensibilité synthétique seulement »), temps discret d'une heure, opportunités qui attendent au plus `ttl = 3` heures, durée de détention aléatoire, 12 instruments répartis en 2 à 4 groupes corrélés, score d'entrée bruité/manquant/périmé, coût potentiellement INCONNU. `UNKNOWN_COST ≠ ZERO_COST` : un coût inconnu est observé comme `NaN`, jamais 0.

Sous-questions de la mission (reprises dans les rapports 03 à 10) :
1. FIFO est-il une référence suffisante ? (si non : dans quels scénarios)
2. Vaut-il mieux classer par « valeur nette attendue » que par score brut ?
3. La valeur **par slot-heure** (diviser par la durée attendue) bat-elle la valeur brute ? (« économie de slot »)
4. Les pénalités de corrélation / plafonds par groupe améliorent-elles le portefeuille ou ne font-elles que rejeter de bonnes occasions ?
5. Le **turnover** (fermer de force une position pour en ouvrir une meilleure) aide-t-il ?
6. Les bandits (algorithmes d'apprentissage par essais), « sleeping experts », règle du secrétaire : sont-ils appropriés ?
7. Comment se comporte la valeur en fonction du nombre de slots (sans en déduire un plafond réel) ?
8. Modes de défaillance : spam de candidats, triche de score, famine d'instruments, changement de régime, bruit.
9. Existe-t-il une bibliothèque « prête à l'emploi » ? (réponse du rapport : non, `ANY_DROP_IN_ALLOCATOR=NO`)

### 1.2 Contraintes de la doctrine (`claude.md`)
- Priorité **REUSE → ADAPT → WRAP → COMPOSE → CUSTOM en dernier** ; sources primaires, ne pas croire les README, exécuter les candidats, ne pas fabriquer de résultats de benchmark.
- Étiquettes : PROVEN / OBSERVED / DOCUMENTED_CLAIM / INFERENCE / UNKNOWN.
- Contraintes AurumShift : recherche/paper seulement, pas de capital réel, PIT (point-in-time) / provenance / pas de lookahead critiques, événementiel/intraday (pas HFT), « l'absence de preuve n'est pas une preuve négative », coûts de marché réalistes, faible charge opérateur.
- Frontière : ne jamais affirmer qu'un candidat est compatible avec AurumShift à partir de ce dépôt seul ; sorties = ADOPT/ADAPT/PARK/REJECT.

Respect observé dans l'étude : bonne discipline d'étiquetage dans les rapports (chaque rapport rappelle « OBSERVED sur simulateur synthétique »). Point où la doctrine est moins bien suivie : les références bibliographiques (rapport 02) sont **DOCUMENTED_CLAIM rappelées de mémoire, non re-vérifiées** (le rapport l'avoue) ; VW, Riskfolio-Lib, Open Bandit Pipeline **non exécutés** (avoué en 11 et 13). Le principe « exécuter les candidats » est respecté pour SciPy/HiGHS, OR-Tools, SimPy, MABWiser, River, PyPortfolioOpt, scikit-learn, CVXPY (`oss_probe.json`).

---

## 2. Méthode

### 2.1 Données et univers
Aucune donnée réelle. Tout est généré par `bench/capacity_v1/py/env.py` (`make_world(P, seed)`).
- 12 instruments (`N_INST = 12`), 4 groupes de corrélation par défaut (2 dans les scénarios corrélés), horizon `T = 1000` heures, `ttl = 3`.
- Rendements horaires `r_i = β·F_groupe + σ_i·ε` (facteur de groupe → corrélation). Chaque position a un côté ±1 ; deux positions du même groupe et du même côté sont corrélées.
- Bord de gain (« edge ») latent par opportunité : moyenne d'instrument + bruit ; **décroît avec l'attente** `edge·exp(−âge/τ)` avec `τ = 8 h`.
- Durée : log-normale (ou Pareto dans les sondes), tronquée à 1–96 h.
- Coût vrai = frais (4–8 bps) + glissement (1–3 bps) par instrument, toujours > 0 ; observé comme `NaN` avec probabilité `p_cost_unk` (10 % par défaut).
- Score observé = `a + b·edge_actuel + biais persistant + bruit iid` (bruit propre à l'instrument) ; peut manquer (`p_miss`). `dur_hat` : estimation bruitée de la durée (mélange instrument/vraie durée, ρ_d = 0,3).
- Résultat net d'une position : `net = edge_à_l'admission × (tenue/durée) + côté × Σ rendements − coût − extra_éviction`. Métrique primaire : **`lat_per_slot_hour`** = résultat net **latent** (espérance sans le bruit de marché) par slot-heure disponible, en bps ; `real_per_slot_hour` = version avec le chemin de marché réalisé.
- Cinq flux aléatoires indépendants (`SeedSequence`) : structure, arrivées, latent, observables, marché → les politiques ne peuvent pas modifier le monde ; toutes voient les **mêmes mondes** (« common random numbers », comparaisons appariées).

### 2.2 Scénarios (rapport 04)
12 familles obligatoires S1–S12 + 3 familles held-out seulement H1–H3 :

| ID | Construction |
|---|---|
| S1 sparse | charge offerte 0,15 |
| S2 modéré | charge 1,0 |
| S3 saturation chronique | charge 4,0 |
| S4 qualité tardive | durées longues, alternance phase longue de faible qualité / courte de haute qualité |
| S5 corrélé | 2 clusters de 6 instruments, facteur de cluster élevé, cluster « encombré » à meilleur edge |
| S6 court-faible vs long-fort | instruments rapides (2 h) vs lents (36 h), ratio de densité varié |
| S7 changement de régime | à mi-horizon : permutation des edges, pente de calibration inversée pour 2 clusters, volatilité ×2 |
| S8 classement bruité | bruit de score ×2,8 |
| S9 qualité manquante | 40 % de scores manquants, 35 % de coûts inconnus, 30 % de durées manquantes |
| S10 spam répété | un instrument émet 1,2 opps/h quasi-dupliquées, faible valeur, score gonflé (+12) |
| S11 rafale | débit ×12 pendant 3 h tous les 100 h |
| S12 tous presque égaux | dispersion inter-instruments nulle |
| H1 (held-out only) | chronique + corrélé + changement de régime |
| H2 (held-out only) | rafale + très bruité + manquant |
| H3 (held-out only) | spam + rapide/lent |

### 2.3 Découpage tuning / validation / held-out (`scenarios.py`)
| Split | Familles | Variantes | Graines | Slots | Usage |
|---|---|---|---|---|---|
| TUNING | S1–S12 | 3 (jitter ×0,80–1,25 sur charge, bruit score, durée, vol. cluster, dispersion edge) | 1000–1002 | 4, 6 | choisir les hyper-paramètres (108 jobs) |
| VALIDATION | S1–S12 | 3 (jitter 0,75–1,30) | 2000–2003 | 3, 4, 6, 10 | mesurer l'optimisme du tuning, choisir la short-list (144 jobs, 16 704 lignes) |
| ROBUST | 1 famille de référence + perturbations une à une | — | 3000–3004 | 3, 4, 6, 10 | 9 axes, 180 jobs |
| FAILURE | idem, sondes de défaillance | — | 4000–4005 | 4, 6 | 114 jobs |
| **HELDOUT** | S1–S12 + H1–H3 | 3 (jitter 0,65–1,50, plus large ; ratios S6 = 1,8 / 0,9 / 3,0 jamais vus) | **9000–9009** | 3, 4, 6, 10 | comparaison finale, jamais réglée dessus |

Taille du held-out : 15 familles × 3 variantes × 10 graines = 450 mondes × 4 capacités × 29 politiques = **52 200 runs** (✔ vérifié : `heldout_raw.csv.gz` a 52 200 lignes, 29 politiques, 450 blocs famille×variante×graine, graines 9000–9009 ; somme des `n_opps` = 46 459 856 ≈ « ~46,5 M opportunités simulées »).

### 2.4 Tuning (réglage des paramètres)
- Objectif : moyenne sur les cellules de tuning de `(lat_per_slot_hour − FIFO)/dens0_rms`.
- 17 politiques réglables, **92 configurations** (✔ 92 lignes dans `results/tuning_table.csv`), 3 graines, capacités 4 et 6 seulement.
- Grilles : `policies.GRIDS`. Un tour 2 a étendu les grilles qui finissaient au bord (tuning seul).
- Paramètres gelés : `bench/capacity_v1/results/tuned_params.json` (SHA-256 `d95c9910…ba814`, ✔ recalculé, identique à la valeur écrite dans le pré-enregistrement).

### 2.5 Pré-enregistrement v2 (`bench/capacity_v1/prereg/PREREGISTRATION.json`)
Seuils exacts :
- `delta_material = 0,10` (un gain « matériel »),
- `delta_equivalence = 0,02` (sous cette différence, deux méthodes sont dites équivalentes ; sert aussi de barre pour « bat le classement simple »),
- `fifo_equiv_upper = 0,04` (FIFO déclaré équivalent si la borne haute de l'IC du meilleur gain < 0,04).
- Short-list (choisie mécaniquement sur la validation) : `COMPOSED` (0,179), `SHADOW_PRICE` (0,174), `ONLINE_KNAPSACK_PSI` (0,171) ; `RANK_NET` toujours évalué comme référence simple. (`FLUID_QUANTILE`, 0,171, a manqué la short-list « de moins de 0,001 » selon le fichier.)
- Critères « cœur » (a)–(c) : (a) dz poolé vs FIFO ≥ 0,10 avec borne basse de l'IC > 0 ; (b) ≥ 60 % des cellules (famille, capacité) avec IC bas > 0 ; (c) ≤ 15 % des cellules matériellement pires que FIFO.
- Critères « bat le simple » (d)–(f) : (d) dz poolé vs `RANK_NET` ≥ 0,02 avec IC bas > 0 ; (e) positif à ≥ 3 capacités sur 4 ; (f) tests de fuite passés.
- Règles de verdict : `STUDY_INCONCLUSIVE` si fuite ou demi-largeur d'IC > 0,10 ; sinon, si ≥ 1 méthode short-list passe cœur + « bat le simple » : `MULTIPLE_CAPACITY_METHODS_SUPPORTED` si ≥ 2 sont à moins de `delta_equivalence` du meilleur, sinon `CAPACITY_ALLOCATION_REFERENCE_SUPPORTED` ; autres branches vers `RANK_NET` puis `FIFO_REMAINS_SUFFICIENT` / `NO_CAPACITY_METHOD_SUPPORTED`.
- Bootstrap : 4 000 rééchantillonnages, graine 20260929, sur les 450 blocs (famille, variante, graine) après moyenne sur les capacités.
- SHA-256 gelés : paramètres tunés, script de verdict, `policies.py`, `env.py`. **✔ Les quatre hachages ont été recalculés sur la branche et correspondent** (`d95c9910…`, `e844d35b…`, `0fcb4129…`, `e98f3d97…`). Le script `runner.py heldout` refuse de tourner si les paramètres ont changé (assertion).

### 2.6 Critères de décision FIFO
« FIFO_FAIL » par famille : le meilleur de {RANK_NET + short-list} a dz vs FIFO ≥ 0,10 avec IC bas > 0 (capacités 4 et 6 poolées). « FIFO_EQUIV » si IC haut < 0,04. Biais reconnu : le « meilleur de quatre » gonfle FIFO_FAIL.

### 2.7 Simulateur : validation
Erlang-B (formule de blocage d'un système à pertes) : erreur absolue maximale **0,0197** sur 9 points (C, charge) (`results/validation.json`, ✔ ; 0,020 arrondi). SimPy (bibliothèque de simulation à événements discrets) indépendant : 0,250/0,525/0,325 vs formule 0,254/0,517/0,319 (✔ `oss_probe.json`).

---

## 3. Résultats détaillés

Toutes les valeurs « held-out » sont des moyennes sur 15 familles × 3 variantes × 10 graines × 4 capacités, en bps par slot-heure (latent) sauf mention. Les vérifications sont faites sur `heldout_raw.csv.gz`.

### 3.1 Rapport 03 — Références et contrôles
Politiques de base : `FIFO` (plus ancien d'abord), `ROUND_ROBIN` (tourner entre instruments), `RANDOM_SEEDED` (tirage au hasard à graine fixe), `EQUAL_QUOTA` (instrument le moins servi d'abord), `OLDEST_SLOT` (FIFO ; quand plein, ferme de force la position la plus ancienne si tenue ≥ 12 h). Contrôles ajoutés : `FIFO_NETPOS` (FIFO mais seulement sur candidats dont score − coût estimé > 0), `RANK_SCORE_RAW`, `RANK_NET`, ablations `RANK_NET_UNKCOST_ZERO` (coût inconnu traité comme 0) et `RANK_NET_MISSING_REJECT` (rejette si score manquant).

| politique | lat/slot-h | real/slot-h | utilisation | hq_missed | hhi_cluster | n_evict | tenue moy. (h) | ret/risque |
|---|---|---|---|---|---|---|---|---|
| EQUAL_QUOTA | 0,250 | 0,251 | 0,861 | 0,469 | 0,496 | 0 | 14,42 | 0,291 |
| FIFO | 0,162 | 0,158 | 0,863 | 0,474 | 0,511 | 0 | 14,22 | 0,190 |
| FIFO_NETPOS | 0,422 | 0,421 | 0,802 | 0,413 | 0,543 | 0 | 14,52 | 0,494 |
| OLDEST_SLOT | −0,019 | −0,020 | 0,853 | 0,314 | 0,512 | 154,7 | 10,01 | −0,000 |
| RANDOM_SEEDED | 0,190 | 0,185 | 0,860 | 0,479 | 0,518 | 0 | 14,05 | 0,218 |
| ROUND_ROBIN | 0,241 | 0,243 | 0,859 | 0,471 | 0,497 | 0 | 14,29 | 0,278 |

✔ Toutes ces moyennes recalculées à l'identique (`hq_missed_frac` = part des opportunités « haute qualité » — quartile supérieur de densité de valeur et valeur positive — expirées sans avoir été admises ; `hhi_cluster` = indice de concentration par cluster, 1 = tout dans un cluster).

Différences appariées (dz, IC 95 % bootstrap) :

| politique | vs FIFO | vs FIFO_NETPOS | vs RANK_NET |
|---|---|---|---|
| FIFO_NETPOS | +0,090 [+0,085 ; +0,096] | — | −0,058 [−0,065 ; −0,051] |
| EQUAL_QUOTA | +0,029 [+0,025 ; +0,033] | −0,061 | −0,119 |
| ROUND_ROBIN | +0,029 [+0,025 ; +0,033] | −0,061 | −0,119 |
| RANDOM_SEEDED | +0,021 [+0,016 ; +0,026] | −0,070 | −0,127 |
| FIFO | — | −0,090 | −0,148 |
| OLDEST_SLOT | −0,070 [−0,076 ; −0,064] | −0,161 | −0,218 [−0,230 ; −0,207] |

✔ Recalculés : FIFO_NETPOS−FIFO = +0,0904 [0,085 ; 0,096] ; OLDEST_SLOT−RANK_NET = −0,2183 [−0,2297 ; −0,2065].

Lecture simple : forcer l'« équité » entre instruments (`ROUND_ROBIN`, `EQUAL_QUOTA`) n'apporte que +0,03 ; **la moitié du gain de FIFO vers les bonnes méthodes vient simplement de refuser les opportunités à valeur négative** (`FIFO_NETPOS`), ce qui est banal. `OLDEST_SLOT` (fermer les anciennes positions pour faire tourner) est nettement pire : ≈ 155 fermetures forcées par run.

Diagnostic **post-hoc** (non pré-enregistré, sur mondes de *validation*, `tables/posthoc.md`) : `LIFO_NETPOS` (le plus récent d'abord avec filtre) fait mieux que FIFO de 0,153 dz (IC [0,139 ; 0,168]) et que `FIFO_NETPOS` de 0,050, et n'est qu'à 0,008 dz sous `RANK_NET` (✔ le fichier `posthoc.md` contient exactement ces trois chiffres). Conséquence : une grande part de ce que « le classement » gagne sur FIFO est la fraîcheur (FIFO sert le plus périmé d'abord alors que l'edge décroît) plus le filtre, pas la vraie discrimination de qualité. Cette conclusion dépend de l'hypothèse `edge·exp(−âge/8 h)` (UNKNOWN dans le réel).

### 3.2 Rapport 05 — Économie de slot
Tableau complet (29 politiques) : voir rapport 05. Valeurs clés recalculées (✔) :

| politique | lat/slot-h | utilisation | tenue moy. | hq_missed | dont « refusée avec slot libre » |
|---|---|---|---|---|---|
| ORACLE_DENSITY (non implémentable) | 0,874 | 0,734 | 14,08 | 0,222 | 0,001 |
| COMPOSED | 0,644 | 0,725 | 13,72 | 0,357 | 0,133 |
| SHADOW_PRICE | 0,598 | 0,734 | 13,25 | 0,340 | 0,109 |
| ONLINE_KNAPSACK_PSI | 0,596 | 0,696 | 12,79 | 0,332 | 0,130 |
| RANK_NET | 0,569 | 0,798 | 14,89 | 0,388 | 0,041 |
| FIFO | 0,162 | 0,863 | 14,22 | 0,474 | 0,000 |

(Valeurs lat/utilisation/tenue ✔ ; les colonnes « refusée avec slot libre » reprises du rapport, ? non recalculées une par une.)

Constats :
1. **Ce qu'on mesure est le gain par slot-heure disponible**, pas par trade. L'utilisation n'est pas l'objectif : les gagnants (`SHADOW_PRICE`, `ONLINE_KNAPSACK_PSI`, `FLUID_QUANTILE`, `COMPOSED`, `TRUNK_RESERVATION`) laissent des slots inoccupés **de 6,0 à 10,3 points** de plus que `RANK_NET` et tiennent leurs positions 1,2 à 2,1 h de moins (✔ : écarts utilisation 0,073 / 0,064 / 0,103 / 0,060 / 0,066 ; tenue 1,17 / 1,64 / 2,10 / 1,81 / 2,01 h). **✘ Écart mineur** : le résumé exécutif (rapport 00) écrit « 6–14 points » ; le maximum mesuré est 10,3. Le rapport 07 écrit correctement « 6–10 points ».
2. `evals_per_opp` ≈ 3,0 : chaque opportunité est « réévaluée » ~3 fois (ttl = 3). ✔ Moyenne 3,04 ; 1,01 en S1 ; 3,66 en S3 ; 3,80 en S10. Donc compter des rejets par évaluation gonflerait ×3 le nombre d'occasions réellement distinctes (le rapport a raison de compter par opportunité unique).
3. **Regret contre la borne LP** (LP = programme linéaire de « planification rétrospective » : le meilleur ordonnancement possible connaissant tout, borne supérieure sans early-exit) : COMPOSED 0,654 / 0,552 / 0,403 / 0,242 (capacités 3/4/6/10), FIFO 1,287 / 1,099 / 0,844 / 0,547, RANK_NET 0,786 / 0,640 / 0,454 / 0,271 (✔). `ORACLE_DENSITY` capture 71,3 % / 76,3 % / 83,8 % / 92,7 % de la borne LP (✔).
4. Vue par famille aux capacités 4/6 (FIFO / RANK_NET / COMPOSED en lat/slot-h) : S3 0,016 / 0,848 / 0,977 ; S10 −0,479 / 0,289 / 0,622 ; S6 1,225 / 1,608 / 1,663 ; S1 0,032 / 0,065 / 0,065 (rapport 05, tableau ; ? non recalculé cellule par cellule, mais les moyennes globales le sont).
5. Dans S6, `RANK_NET` rate *plus* d'opportunités haute qualité que FIFO (0,70 vs 0,66) parce qu'il préfère les positions longues qui bloquent des slots (tenue 27 h vs 19 h), tout en gagnant plus par slot-heure (rapport 05, ? non recalculé).

### 3.3 Rapport 06 — Diversification
Idée : les pénalités de corrélation améliorent-elles le portefeuille ou rejettent-elles seulement des bonnes occasions ?
Implémentations (au-dessus de `RANK_NET`) : `CLUSTER_CAP` (max ⌈0,75·C⌉ positions par cluster), `CORR_PENALTY` (valeur − γ·covariance croisée avec les positions ouvertes, γ = 0,02), `MARGINAL_RISK` (contribution marginale à la variance, incluant la variance propre, γ = 0,05), `CORR_HARD_REJECT` (rejet si corrélation ≥ 0,95 avec une position ouverte). Corrélation estimée causalement (EWMA — moyenne mobile exponentielle — corrigée du biais, rétrécissement 0,05, utilisée après 60 observations). Les clusters sont **donnés** aux politiques (connaissance a priori de la structure).

Différences appariées vs `RANK_NET` (dz ; mesures de risque en bps de PnL quotidien). Mes recalculs (IC bootstrap avec ma propre graine, écarts ≤ 0,003 avec le rapport) :

| politique | familles | d_lat_dz | d_ret/risque | d_PnL_jour_sd | d_max_drawdown |
|---|---|---|---|---|---|
| CLUSTER_CAP | toutes | +0,0002 | +0,0002 | +0,16 | −3,8 |
| CLUSTER_CAP | S5/H1 | −0,0060 | −0,0142 | +0,91 | +0,5 |
| CORR_PENALTY | toutes | +0,0005 [−0,0001 ; +0,0010] | +0,0263 | −7,02 | −42,1 |
| CORR_PENALTY | S5/H1 | +0,0020 | +0,0507 | −25,5 | −141,7 |
| MARGINAL_RISK | toutes | +0,0060 | +0,0947 | −16,5 | −112,4 |
| MARGINAL_RISK | S5/H1 | +0,0079 | +0,1651 | −53,0 | −351,6 |
| CORR_HARD_REJECT | toutes | −0,0070 | +0,0517 | −14,7 | −87,8 |
| CORR_HARD_REJECT | S5/H1 | −0,0157 | +0,0217 | −24,7 | −100,4 |
| COMPOSED | toutes | +0,0231 | +0,0849 | −3,8 | −61,3 |

✔ Tous ces chiffres du rapport 06 sont reproduits (à la 3e–4e décimale) à partir des données brutes. (S5/H1 = les deux familles corrélées ; ret/risque = rendement quotidien moyen / écart-type quotidien.)

Lecture :
- `CORR_PENALTY` (pénalité douce, corrélation seule) baisse la volatilité et le drawdown (creux maximal de la courbe de PnL) sans perte d'espérance mesurable.
- Rejet dur et plafond par cluster « rejettent surtout de bonnes occasions » (dz négatif sur les familles corrélées).
- `MARGINAL_RISK` gagne le plus en risque, mais le post-hoc (validation) montre qu'une variante **sans aucune corrélation** (`MARGINAL_DIAG`, pénalité de variance propre seule) obtient un gain d'espérance plus grand (+0,0123 vs +0,0052 dz) : l'effet vient surtout d'une pénalité « volatilité/durée », c'est de l'économie de slot, pas de la diversification (✔ `posthoc.md`).

**Test de stress « effondrement de corrélation »** (volatilité des facteurs de cluster ×1/×2/×4/×8 à mi-parcours, capacité 4, 6 graines de sondes séparées) — ✔ chiffres du rapport reproduits pour `RANK_NET` (écart-type quotidien 105 → 149 → 258 → 493 ; drawdown 346 → 589 → 1274 → 2860), `MARGINAL_RISK` (91 → 116 → 162 → 259 ; 1516 à ×8) et `CLUSTER_CAP` (486 à ×8).
**✘ Écart d'interprétation important** : le résumé exécutif (rapport 00, point 4) écrit « sous un stress d'effondrement de corrélation le **soft penalty (`CORR_PENALTY`)** divise le risque de queue par deux ». Le chiffre « moitié » est celui de **`MARGINAL_RISK`**. Pour `CORR_PENALTY` (la méthode désignée `BEST_DIVERSIFICATION_REFERENCE`), mon calcul sur `failure_raw.csv.gz` donne à ×8 (capacité 4) : écart-type quotidien **329** (vs 493, −33 %), drawdown **2 147** (vs 2 860, −25 %). C'est utile mais ce n'est pas « la moitié ». La partie « moitié » est justement celle dont le rapport dit qu'elle n'est pas principalement de la corrélation.

### 3.4 Rapport 07 — Turnover et économie de slot-heure
Différences vs `RANK_NET` (dz ; effet sur utilisation etc.) :

| politique | d_lat_dz [IC] | d_n_evict | d_tenue (h) | d_utilisation |
|---|---|---|---|---|
| SLOTHOUR_DENSITY | +0,0018 [+0,0006 ; +0,0028] | 0 | −0,67 | −0,002 |
| SLOTHOUR_HAZARD | −0,0017 [−0,0039 ; +0,0004] | 0 | −1,13 | −0,004 |
| SHADOW_PRICE | +0,0156 [+0,0120 ; +0,0190] | 0 | −1,64 | −0,065 |
| FLUID_QUANTILE | +0,0129 | 0 | −1,81 | −0,060 |
| ONLINE_KNAPSACK_PSI | +0,0146 [+0,0100 ; +0,0187] | 0 | −2,10 | −0,103 |
| TRUNK_RESERVATION | +0,0100 | 0 | −2,01 | −0,066 |
| EVICT_SWAP | +0,0048 [+0,0010 ; +0,0084] | +35,3 | −2,73 | −0,010 |
| OLDEST_SLOT | −0,2183 | +154,7 | −4,88 | +0,055 |

✔ recalculés : SLOTHOUR_DENSITY +0,0018, SHADOW +0,0156, KNAPSACK +0,0146, EVICT_SWAP +0,0048, OLDEST −0,2183.

Constats du rapport :
1. « Valeur par heure de détention attendue » seule (`SLOTHOUR_DENSITY`) ≈ classement net (+0,002) : l'idée évidente ne survit pas seule.
2. Ce qui aide = le **seuil de coût d'opportunité** (laisser un slot vide quand le meilleur candidat est marginal) : `SHADOW_PRICE` (+0,016), `ONLINE_KNAPSACK_PSI` (+0,015), `FLUID_QUANTILE` (+0,013), `TRUNK_RESERVATION` (+0,010).
3. `EVICT_SWAP` (échange avec durée minimale 12 h, marge ×1,5) : +0,005 pour ≈ 35 sorties forcées par run ; `OLDEST_SLOT` falsifié.
4. Table S6 : SLOTHOUR_DENSITY bat RANK_NET dans 3/3 variantes (+0,002, +0,060, +0,010 bps/slot-h) ; ✔ recalculé (1,295−1,293 ; 2,838−2,778 ; 0,756−0,746). `SHADOW_PRICE` (0,822) dépasse `ORACLE_DENSITY` (0,813) dans la variante 2 : preuve que le « oracle glouton » n'est pas une borne supérieure (seule la LP l'est) ✔.

**✘ Découverte importante (non signalée par le rapport) : le mécanisme « hazard » (décote par péremption du score) est inerte dans toute l'étude.**
Dans `policies.py`, la décote est `s = s·exp(−score_age/τ)`. Or `score_age` vaut toujours 0 quand `refresh=True` (`env.py` ligne 334 : `a if not P["refresh"] else 0`) et `refresh=True` est la valeur par défaut de `BASE` **sans qu'aucun scénario ne la change** (recherche de « refresh » dans tous les `.py` : trois occurrences, toutes dans `env.py`). Preuves :
1. `tuning_table.csv` : les cinq valeurs de τ de `SLOTHOUR_HAZARD` (1, 2, 3, 6, 12) donnent **exactement le même objectif 0,138354** — égal à celui de `SLOTHOUR_DENSITY` avec `h0 = 2` (0,138354). ✔ constaté.
2. J'ai relancé le code (tirage held-out variante 0, graine 9000, capacité 4) : `COMPOSED` avec τ = 6 et avec τ = 0,1 ont des `lat_net` **identiques** (5174,78 sur S3 ; 2016,69 sur S8 ; 3518,27 sur S10) et des listes d'admissions identiques ; `SLOTHOUR_HAZARD` (tuné) est identique à `SLOTHOUR_DENSITY(h0=2)` (4709,31 ; 1707,91 ; 1797,67). Les chiffres `COMPOSED` de mon rejeu coïncident *exactement* avec la ligne correspondante de `heldout_raw.csv.gz` (5174,7844502 pour S3) : déterminisme confirmé.
Conséquences : (a) `SLOTHOUR_HAZARD` n'est pas une idée distincte : c'est la densité avec `h0 = 2` (d'où son écart de −0,0034 dz vs `SLOTHOUR_DENSITY` `h0 = 12`, ✔ calculé) ; (b) `COMPOSED`, décrit comme « LCB calibrée + hazard de péremption + densité + quantile fluide », est **en réalité LCB calibrée + densité(h0=2) + quantile fluide** ; le composant « hazard » n'y fait rien ; (c) le rapport 04 interprète « SLOTHOUR_HAZARD τ = 1 en bord de grille » comme « le bouton veut être éteint » : c'est un artefact de départage d'égalité (toutes les valeurs de τ sont ex æquo, le premier est retenu) ; (d) la conclusion « le hazard-ajusté est indistinguable » (rapport 07) est vraie mais trivialement, la fonctionnalité n'ayant jamais été testée. La *fraîcheur* est néanmoins prise en compte indirectement, car le score simulé est recalculé à chaque âge à partir de l'edge décru (`refresh=True`) ; ce que l'étude ne teste pas, c'est un score **figé** (périmé).

### 3.5 Rapport 08 — Sensibilité à la capacité (synthétique seulement)
Valeurs recalculées (✔) en lat/slot-h et utilisation (capacités 3 / 4 / 6 / 10) :

| politique | lat/slot-h | utilisation |
|---|---|---|
| FIFO | 0,158 / 0,161 / 0,162 / 0,168 | 0,909 / 0,894 / 0,862 / 0,788 |
| FIFO_NETPOS | 0,457 / 0,441 / 0,418 / 0,371 | 0,867 / 0,846 / 0,800 / 0,695 |
| RANK_NET | 0,660 / 0,619 / 0,552 / 0,443 | 0,865 / 0,843 / 0,795 / 0,690 |
| COMPOSED | 0,791 / 0,708 / 0,602 / 0,473 | 0,763 / 0,766 / 0,739 / 0,633 |
| SHADOW_PRICE | 0,724 / 0,660 / 0,566 / 0,440 | 0,785 / 0,767 / 0,730 / 0,653 |
| ONLINE_KNAPSACK_PSI | 0,707 / 0,666 / 0,575 / 0,438 | 0,802 / 0,755 / 0,675 / 0,551 |
| ORACLE_DENSITY | 1,030 / 0,961 / 0,843 / 0,663 | 0,827 / 0,795 / 0,727 / 0,588 |
| Borne LP | 1,445 / 1,260 / 1,006 / 0,714 | — |

Gain apparié `COMPOSED` vs FIFO : +0,224 / +0,195 / +0,157 / +0,107 dz ✔ ; vs `RANK_NET` : +0,042 / +0,028 / +0,015 / +0,008 ✔. Le gain d'une politique intelligente diminue de façon monotone quand la capacité augmente (concavité de la valeur de capacité), et le rapport insiste : rien n'est déductible d'un plafond réel, car l'intensité d'arrivée est ancrée à `C_ref = 4`.
Détail à noter : `ONLINE_KNAPSACK_PSI` est en dessous de `RANK_NET` à la capacité 10 (−0,005) ✔ ; `SHADOW_PRICE` est à 0,000 ✔.

### 3.6 Rapport 09 — Résultats held-out (pré-enregistrés)
**Tableau des 29 politiques (dz poolé)** — extraits (chiffres du rapport ; tous ✔ recalculés pour les 16 lignes que j'ai vérifiées) :

| politique | vs FIFO | vs FIFO_NETPOS | vs RANK_NET |
|---|---|---|---|
| ORACLE_DENSITY (borne non implémentable) | +0,260 | +0,170 | +0,112 |
| ORACLE_SCORE (idem) | +0,248 | +0,157 | +0,100 |
| **COMPOSED** | **+0,171 [0,160 ; 0,182]** | +0,081 | **+0,023 [0,019 ; 0,027]** |
| SHADOW_PRICE | +0,164 | +0,073 | +0,016 [0,012 ; 0,019] |
| ONLINE_KNAPSACK_PSI | +0,163 | +0,072 | +0,015 [0,010 ; 0,019] |
| FLUID_QUANTILE | +0,161 | +0,070 | +0,013 |
| UNCERTAINTY_LCB | +0,155 | +0,065 | +0,007 |
| MARGINAL_RISK | +0,154 | +0,064 | +0,006 |
| TRUNK_RESERVATION | +0,158 | +0,068 | +0,010 |
| SLEEPING_HEDGE | +0,151 | +0,061 | +0,003 |
| CORR_PENALTY / CLUSTER_CAP / RANK_NET_MISSING_REJECT | +0,148 | +0,058 | 0,000 |
| RANK_NET | +0,148 | +0,058 | — |
| SLOTHOUR_DENSITY | +0,150 | +0,059 | +0,002 |
| EVICT_SWAP | +0,153 | +0,062 | +0,005 |
| RANK_NET_UNKCOST_ZERO | +0,144 | +0,054 | −0,004 |
| SLOTHOUR_HAZARD | +0,146 | +0,056 | −0,002 |
| CORR_HARD_REJECT | +0,141 | +0,051 | −0,007 |
| LIN_TS | +0,128 | +0,038 | −0,020 |
| RANK_SCORE_RAW | +0,131 | +0,041 | −0,017 |
| LINUCB | +0,125 | +0,035 | −0,023 |
| FIFO_NETPOS | +0,090 | — | −0,058 |
| EQUAL_QUOTA / ROUND_ROBIN | +0,029 | −0,061 | −0,119 |
| SECRETARY_1_OVER_E | +0,014 | −0,077 | −0,134 |
| RANDOM_SEEDED | +0,021 | −0,070 | −0,127 |
| FIFO | — | −0,090 | −0,148 |
| OLDEST_SLOT | −0,070 | −0,161 | −0,218 |

**Critères pré-enregistrés appliqués** (✔ vérifiés dans `heldout_verdict.json`) :

| Critère | COMPOSED | SHADOW_PRICE | ONLINE_KNAPSACK_PSI | RANK_NET |
|---|---|---|---|---|
| (a) dz vs FIFO ≥ 0,10, IC bas > 0 | passe (0,1711 ; IC [0,1605 ; 0,1817]) | passe (0,1636) | passe (0,1626) | passe (0,148) |
| (b) ≥ 60 % cellules IC bas > 0 | 100 % | 100 % | 100 % | 100 % |
| (c) ≤ 15 % cellules matériellement pires | 0 % | 0 % | 0 % | 0 % |
| (d) dz vs RANK_NET ≥ 0,02, IC bas > 0 | **passe (0,0231 ; [0,0196 ; 0,0268])** | échoue (0,0156) | échoue (0,0146) | — |
| (e) positif à ≥ 3 capacités sur 4 | 4/4 | 3/4 (cap. 10 = 0,000) | 3/4 (cap. 10 = −0,005) | — |
| (f) fuite | passe | passe | passe | passe |

Demi-largeur maximale d'IC vs FIFO : 0,0108 (≪ 0,10) → étude non sous-puissante pour ses propres seuils ✔. La part de cellules (famille×capacité) où `COMPOSED` bat `RANK_NET` avec IC > 0 est seulement **65 %** ; 11 cellules sur 60 ont un dz moyen négatif (✔ calculé).

**FIFO échoue-t-il, par famille ?** (capacités 4 et 6 ; meilleur de RANK_NET + short-list) — ✔ recalculé à partir de `heldout_verdict.json` :

| famille | meilleure méthode | dz vs FIFO | dz vs FIFO_NETPOS | FIFO_FAIL | FIFO_EQUIV |
|---|---|---|---|---|---|
| H1 chronique/corrélé/régime | ONLINE_KNAPSACK_PSI | +0,238 | +0,107 | oui | non |
| H2 rafale/bruité/manquant | ONLINE_KNAPSACK_PSI | +0,104 | +0,046 | oui | non |
| H3 spam + rapide/lent | COMPOSED | +0,173 | +0,124 | oui | non |
| S10 spam | COMPOSED | +0,363 | +0,238 | oui | non |
| S11 rafale | ONLINE_KNAPSACK_PSI | +0,151 | +0,030 | oui | non |
| S12 tous égaux | RANK_NET | +0,341 | +0,292 | oui | non |
| S1 sparse | ONLINE_KNAPSACK_PSI | +0,010 | +0,000 | non | **oui** |
| S2 modéré | ONLINE_KNAPSACK_PSI | +0,100 | +0,011 | oui (limite : 0,100) | non |
| S3 chronique | SHADOW_PRICE | +0,364 | +0,164 | oui | non |
| S4 qualité tardive | ONLINE_KNAPSACK_PSI | +0,127 | +0,074 | oui | non |
| S5 corrélé | ONLINE_KNAPSACK_PSI | +0,235 | +0,088 | oui | non |
| S6 court vs long | SHADOW_PRICE | +0,086 | +0,054 | non | non |
| S7 régime | ONLINE_KNAPSACK_PSI | +0,237 | +0,094 | oui | non |
| S8 bruité | ONLINE_KNAPSACK_PSI | +0,164 | +0,060 | oui | non |
| S9 manquant | ONLINE_KNAPSACK_PSI | +0,189 | +0,095 | oui | non |

13 échecs de FIFO, 1 équivalence (S1), 1 « ni l'un ni l'autre » (S6). Deux familles sont proches du seuil : **S2 (0,100, et même 0,1004 selon l'arrondi) et H2 (0,104)** — la classification « échec » y est un franchissement de seuil, pas une différence nette. Face à `FIFO_NETPOS` (filtre inclus), seules 5 familles dépassent 0,10 (H1, H3, S10, S12, S3) ✔.

**Stabilité validation → held-out** (dz vs FIFO) : COMPOSED 0,179 → 0,171 ; SHADOW 0,174 → 0,164 ; KNAPSACK 0,171 → 0,163 ; RANK_NET 0,154 → 0,148 ; FIFO_NETPOS 0,100 → 0,090 ; LINUCB 0,125 → 0,125. ✔ Recalculé sur `validation_raw.csv.gz` (COMPOSED 0,1789 ; SHADOW 0,1736 ; KNAPSACK 0,1712 ; RANK_NET 0,1539 ; FIFO_NETPOS 0,0997 ; LINUCB 0,1251). L'optimisme du tuning (≈ 0,006–0,01) est donc plus petit que la marge de 0,023.

**Sensibilité de FIFO aux axes de robustesse** (graines 3000–3004, famille de référence : charge 3, 2 clusters, etc., capacités poolées) : cf. tableau du rapport 09 §4/§6. Points vérifiés (✔) : coût ×4 (niveau 3) : FIFO −1,741, FIFO_NETPOS −0,110, RANK_NET −0,106, COMPOSED −0,098, SHADOW −0,104 ; coût ×2 : FIFO −0,545, RANK_NET 0,280, SHADOW 0,320 ; pente de calibration −0,3 : FIFO 0,053, RANK_NET −0,246, COMPOSED −0,207, LINUCB 0,252, LIN_TS 0,277 (**✘ mineur** : le texte écrit « LinTS est la seule méthode qui récupère, +0,25 » alors que LinUCB atteint aussi 0,252 et LinTS 0,277 — les deux bandits récupèrent) ; charge 0,5 : toutes les méthodes sensées à 0,219 ; charge 6 : COMPOSED 1,204, SHADOW 1,200, RANK_NET 0,996, FIFO −0,004.
Conclusion du rapport : l'ordre FIFO ≪ FIFO_NETPOS < RANK_NET < {COMPOSED, SHADOW, KNAPSACK} tient sur arrivées, bruit ×0,5–×4, durées, corrélation, timing de régime, coût inconnu 0–70 %, charge ; il **casse** à pente nulle ou négative, à coût ×4, et à charge 0,5.

### 3.7 Rapport 10 — Modes de défaillance (graines 4000–4005, capacités 4 et 6)
- **Spam de candidats** (taux 0 / 0,5 / 1,2 / 3,0 par heure ; les opps de spam pèsent 0/39/61/79 % des arrivées). Capacité 4, lat/slot-h — ✔ tous reproduits :

| politique | 0 | 0,5 | 1,2 | 3,0 | part de spam dans les admissions à 3,0 |
|---|---|---|---|---|---|
| FIFO | 0,115 | −0,143 | −0,247 | −0,317 | 0,50 (0,498) |
| EQUAL_QUOTA | 0,188 | 0,065 | 0,020 | 0,044 | 0,11 |
| RANK_NET | 0,763 | 0,411 | 0,302 | 0,216 | 0,67 |
| SHADOW_PRICE | 0,883 | 0,640 | 0,521 | 0,362 | 0,57 |
| LINUCB | 0,596 | 0,487 | 0,346 | 0,260 | 0,53 |
| COMPOSED | 0,824 | 0,711 | 0,661 | 0,638 | 0,26 |

Pertes relatives entre sans spam et 3,0/h : RANK_NET −71,7 % (rapport −72 %), SHADOW −59 % (✔), COMPOSED −22,6 % (**rapport : −22 %, arrondi par défaut**, écart cosmétique). Mécanisme : le score de l'instrument spammeur est gonflé, donc le classement brut est attiré ; la calibration par instrument de COMPOSED/UNCERTAINTY_LCB apprend que ce score ne prédit rien.
Notez que **sans spam, SHADOW_PRICE (0,883) bat COMPOSED (0,824)** : la calibration de COMPOSED coûte de la valeur quand il n'y a pas d'attaque.
- **Triche de score** (biais du spammeur 0 → 12 → 30 → 60) : ✔ `RANK_NET` 0,585 → 0,325 → −0,069 → −0,371 ; `SHADOW` 0,810 → 0,540 → 0,006 → −0,441 ; `COMPOSED` 0,767 → 0,678 → 0,644 → 0,606 ; FIFO −0,201 plat ; instruments positifs affamés (`starved_pos_inst`) par RANK_NET : 0 → 0,17 → 0,83 → 3,83 (rapport « 3,8 sur 12 ») ; COMPOSED : 0. Le modèle d'attaque est un **biais constant sur un seul instrument**; un adversaire adaptatif n'est pas testé.
- **Famine** (capacités 4/6, toutes familles) : ✔ `starved_pos_inst` — RANK_NET 0,008, COMPOSED 0,002, SECRETARY 1,147 (rapport 1,15), LIN_TS 0,277 (0,28), LINUCB 0,069 (0,07).
- **Capture de slots longs** : positions longues = 65–68 % des slot-heures dans S6 sous RANK_NET et SLOTHOUR_DENSITY ; en durées Pareto avec corrélation edge–durée : 0,54–0,58. Propriété du mélange d'opportunités, non corrigée par ces allocateurs.
- **Régime** : ✔ (capacité 4, par quart) RANK_NET 0,81/0,88/0,20/0,20, COMPOSED 0,88/0,93/0,20/0,19, SHADOW 0,91/0,96/0,21/0,21, LINUCB 0,66/0,79/0,18/0,19, FIFO 0,14/0,23/0,15/0,07. Held-out S7+H1 (capacités 4/6) : RANK_NET 0,848/0,859/0,362/0,344, COMPOSED 0,939/0,973/0,402/0,347 : chute de ~60 %, aucune méthode ne s'adapte en 500 h ; l'oracle reste ≈ 1,05–1,08.
- **Bruit du score** (sd 10 → 30 → 60, forte hétérogénéité) : ✔ RANK_NET 0,709 → 0,484 → 0,354 ; SHADOW 0,812 → 0,502 → 0,387 ; COMPOSED 0,792 → 0,374 → 0,306 : **COMPOSED passe sous RANK_NET** (−0,11 et −0,05). Son coefficient de variation du seuil est 4–5 (rapport, ? non recalculé).
- **Oscillation** (bascule de l'état « tous les slots pleins », variabilité de seuil) : constaté sans perte de valeur mesurée (rapport, ?).
- Autres : `UNKNOWN_COST` traité comme 0 : −0,004 dz [−0,005 ; −0,003] à 10 % d'inconnus (✔ −0,004 dz vs RANK_NET), perte de valeur −12 % à 70 % inconnus (0,643 → 0,566, ✔ dans la table de robustesse 0,647/0,644/0,643/0,643→0,587/0,566 pour la variante zéro : ✔ ordre de grandeur). `RANK_NET_MISSING_REJECT` ≡ RANK_NET (0,000).

### 3.8 Rapport 11 — Composants OSS exécutés
Voir §4.2 pour les verdicts. Chiffres vérifiés (✔ `oss_probe.json`) : versions SciPy 1.17.1, OR-Tools 9.15.6755, MABWiser 2.7.4, SimPy 4.1.2, River 0.26.1, CVXPY 1.9.3, PyPortfolioOpt 1.6.0, PuLP 3.3.2, scikit-learn 1.9.1 ; OR-Tools CP-SAT = glouton 100/100 (2,83 ms/instance) ; greedy = MILP 200/200 et affectation hongroise = top-k 200/200 ; MABWiser vs LinUCB propre sur 9 mondes : latent moyen 0,2775 vs 0,3631 vs FIFO −0,0588 (rapport 0,277/0,363/−0,059 ✔ ; en réalité MABWiser n'est meilleur que LinUCB propre que dans 2 des 9 mondes) ; erreur de Frobenius sur la matrice de corrélation (n = 100/200/400) : échantillon 0,50/0,31/0,20, Ledoit–Wolf 0,63/0,33/0,20, EWMA propre 0,62/0,43/0,46 ✔.
Remarque : `oss_probe.log` contient une erreur d'import du solveur HiGHS dans CVXPY (`undefined symbol …Highs…releaseMemory`) ; le QP a tout de même été résolu (statut `optimal`, autre solveur). Sans conséquence pour le verdict.

### 3.9 Rapport 12 — Décomposition du gain
Sur les 0,171 dz de COMPOSED vs FIFO : filtrage des valeurs négatives 0,090 (≈ 53 %) ; classement par valeur nette 0,148−0,090 = 0,058 (≈ 34 %) ; seuils de coût d'opportunité +0,013 à 0,016 ; composition complète +0,023 sur RANK_NET (≈ 13,5 % du total, « un huitième ») — arithmétique ✔.

---

## 4. Candidats et méthodes évalués, un par un

Vocabulaire des verdicts du rapport : ADOPT_REFERENCE (référence de recherche, rien n'est intégré), ADAPT_CANDIDATE, PARK (mis de côté), REJECT. Les verdicts « ADOPT » ne veulent pas dire « à intégrer » : la doctrine interdit d'affirmer la compatibilité AurumShift.

### 4.1 Politiques d'allocation (29 exécutées en held-out)
Pour chacune : ce que c'est, gain vs RANK_NET (dz, ✔ recalculé sauf mention), verdict (le rapport ne donne pas ADOPT/REJECT à chaque politique ; j'écris le verdict implicite du rapport puis le mien).

1. **FIFO** — servir par ordre d'arrivée. −0,148 vs RANK_NET. Verdict : référence à battre ; insuffisante dans 13/15 familles ; équivalente seulement en demande éparse (S1). Change si : demande éparse, score non informatif (pente ≤ 0,2).
2. **FIFO_NETPOS** — FIFO avec filtre valeur estimée > 0. +0,090 vs FIFO. Verdict : **contrôle indispensable** ; fournit la moitié du gain. Le rapport aurait dû l'imposer comme référence « naïve » principale (il le fait en partie dans le verdict, règle 5 de la pré-inscription).
3. **ROUND_ROBIN / EQUAL_QUOTA / RANDOM_SEEDED** — +0,021 à +0,029 vs FIFO. REJECT comme méthode (l'équité ne rapporte rien).
4. **OLDEST_SLOT** — −0,218 vs RANK_NET, 155 sorties forcées/run. REJECT (falsifié). Change si : coût de sortie forcée quasi nul et edge qui s'épuise vite (non testé).
5. **RANK_SCORE_RAW** — −0,017 vs RANK_NET. REJECT (ignore le coût).
6. **RANK_NET** — classement par (score − coût), coût inconnu imputé par la moyenne courante, refus si ≤ 0. +0,148 vs FIFO. Verdict : **référence simple solide** ; c'est le vrai « point de comparaison » des méthodes plus complexes.
7. **RANK_NET_UNKCOST_ZERO** — −0,004. REJECT (le coût inconnu ne vaut pas 0) — confirmé, petit effet.
8. **RANK_NET_MISSING_REJECT** — 0,000. Indistinguable ; « absence de preuve n'est pas preuve négative » non départageable ici.
9. **UNCERTAINTY_LCB** (calibration bayésienne hiérarchique par instrument + borne inférieure de confiance) — +0,007. Verdict implicite : utile *contre le spam*, coûteux sinon. ADAPT_CANDIDATE conditionnel.
10. **SLOTHOUR_DENSITY** (valeur / (durée + h0)) — +0,002. Non supporté seul.
11. **SLOTHOUR_HAZARD** — −0,002. **Inerte** (§3.4) : doublon de la densité `h0 = 2`.
12. **SHADOW_PRICE** (prix fictif d'un slot, montée duale sur l'utilisation cible 0,8) — +0,016 [0,012 ; 0,019]. Meilleure référence « slot-heure » (`BEST_SLOT_HOUR_REFERENCE`) ; échoue la barre 0,02 de 0,004. ADAPT_CANDIDATE (idée), pas de bibliothèque.
13. **ONLINE_KNAPSACK_PSI** (seuil Ψ(remplissage) des sacs à dos en ligne) — +0,015 ; négatif à capacité 10 (−0,005), 5 % des cellules matériellement pires que RANK_NET (✔ 0,05). ADAPT_CANDIDATE.
14. **FLUID_QUANTILE** (seuil quantile « fluide ») — +0,013. ADAPT_CANDIDATE.
15. **TRUNK_RESERVATION** — +0,010. ADAPT_CANDIDATE marginal.
16. **CLUSTER_CAP** — 0,000 globalement, −0,006 sur familles corrélées. REJECT (falsifié).
17. **CORR_PENALTY** — 0,000 en valeur, meilleur profil risque « propre » (−7 bps de volatilité, −42 de drawdown). `BEST_DIVERSIFICATION_REFERENCE`. ADAPT_CANDIDATE.
18. **MARGINAL_RISK** — +0,006, meilleur en risque, mais gain d'espérance surtout via variance propre/durée. ADAPT_CANDIDATE avec réserve.
19. **CORR_HARD_REJECT** — −0,007 (−0,016 corrélé). REJECT.
20. **EVICT_SWAP** — +0,005 [0,001 ; 0,008] pour 35 sorties/run. PARK (gain d'un ordre de grandeur sous les seuils, coût opérationnel de sorties forcées) ; négatif à capacité 10 (−0,005, ✔).
21. **LINUCB / LIN_TS** — −0,023 / −0,020. REJECT sauf pente négative (seuls à récupérer).
22. **SLEEPING_HEDGE** — +0,003. Essentiellement égal au classement simple. « REJECT en tant que bibliothèque » (aucune trouvée), algorithme gardé comme référence de recherche.
23. **SECRETARY_1_OVER_E** — dz vs FIFO +0,014 ; utilisation 13 % ; 1,15 instrument positif affamé. REJECT.
24. **COMPOSED** — LCB calibrée (k = 0,5, κ = 25) + densité h0 = 2 + quantile fluide (s = 1,2) ; corrélation désactivée (g = 0) ; hazard **inerte**. +0,171 vs FIFO, +0,023 vs RANK_NET. Verdict machine : référence. **Mon avis : PARK-comme-référence unique ; ADAPT_CANDIDATE comme brique « calibration anti-spam »** (voir §7).
25. **ORACLE_SCORE / ORACLE_DENSITY** — bornes de référence non implémentables ; le rapport reconnaît qu'elles ne sont pas de vraies bornes supérieures (méthodes à seuil les battent).
26. Diagnostics post-hoc : `LIFO_NETPOS`, `MARGINAL_DIAG` ; canari de fuite `LEAKY_CANARY_NOT_IMPLEMENTABLE`.

Conditions de changement de verdict qui reviennent : (i) score non informatif ou de pente négative → tout classement par score ≈ FIFO ; (ii) coûts ×4 → toutes les méthodes perdent de l'argent ; (iii) demande éparse → tout se vaut ; (iv) spam/triche → seule la calibration par instrument protège.

### 4.2 Composants externes (rapport 11)
| Composant | Exécuté ? | Verdict rapport | Mon commentaire |
|---|---|---|---|
| SciPy (`milp`, `linprog`/HiGHS, `linear_sum_assignment`) | oui | ADOPT_REFERENCE (borne LP, vérification) | ✔ cohérent : 1 800 LP résolus (450 mondes × 4 caps), ~1,4 s chacun (durée : ? non recalculée) |
| OR-Tools CP-SAT | oui | ADAPT_CANDIDATE si contraintes non laminaires | ✔ 100/100 ≡ glouton |
| SimPy | oui | ADOPT_REFERENCE (contre-vérif simulateur) | ✔ |
| MABWiser | oui (9 mondes) | PARK | échantillon très petit, mixte |
| River (bandit) | smoke test | PARK | |
| Vowpal Wabbit, Open Bandit Pipeline, Riskfolio-Lib | **non exécutés** | PARK | métadonnées PyPI seulement (DOCUMENTED_CLAIM) |
| PyPortfolioOpt | HRP exécuté | PARK admission ; ADAPT estimateurs de covariance | |
| scikit-learn LedoitWolf | oui | ADAPT_CANDIDATE (meilleur à fenêtre longue) | non testé *dans* une politique (INFERENCE) |
| CVXPY | QP exécuté | PARK (dimensionnement, pas sélection) | |
| PuLP | installé seulement | PARK | |
| Bibliothèque « sleeping experts » | recherche limitée aux index de paquets | REJECT (résultat de recherche) | recherche faible |
| Sac à dos en ligne / secrétaire / bid-price / trunk reservation | aucune bibliothèque, codés à partir des articles | ADAPT (idées) / PARK (lib) | |
| `ANY_DROP_IN_ALLOCATOR` | — | NO | cohérent |

---

## 5. Bloc final complet (reproduit tel quel, `12_ADJUDICATION.md` §6)

```
ALGORITHMS_DISCOVERED=36
ALGORITHMS_EXECUTED=29 policies in the held-out grid (27 implementable + 2 upper-bound oracles); + 2 post-hoc diagnostics, 1 leakage canary, 1 library bandit (MABWiser), solver/simulator cross-checks (SciPy HiGHS/LSA, OR-Tools CP-SAT, SimPy)

HELDOUT_SCENARIOS=15 families (S1–S12 + H1–H3) x 3 variants = 45 scenario instances x 4 capacity levels; 52,200 runs
SEEDS=10 per scenario instance (9000–9009) => 450 held-out worlds; tuning 3 (1000–1002), validation 4 (2000–2003), robustness 5 (3000–3004), failure 6 (4000–4005)

FIFO_FAILURE_SCENARIOS=13: H1_chronic_corr_regime, H2_burst_noisy_missing, H3_spam_fastslow, S2_moderate, S3_chronic, S4_late_quality, S5_correlated, S7_regime_shift, S8_noisy_ranking, S9_missing_quality, S10_spam, S11_burst, S12_all_equal  (mostly filter+freshness; see 09)
FIFO_EQUIVALENT_SCENARIOS=1: S1_sparse   (S6_short_vs_long is between: +0.086, below the 0.10 bar)

BEST_SLOT_HOUR_REFERENCE=SHADOW_PRICE (opportunity-cost/bid-price threshold; statistically tied with ONLINE_KNAPSACK_PSI and FLUID_QUANTILE; SLOTHOUR_DENSITY alone is not distinguishable from RANK_NET)
BEST_DIVERSIFICATION_REFERENCE=CORR_PENALTY (correlation-only soft penalty; MARGINAL_RISK scores higher but part of its gain is an own-variance/duration effect)
BEST_TURNOVER_REFERENCE=SHADOW_PRICE (no forced exits); EVICT_SWAP is the only explicit-turnover rule with a positive sign (+0.005) and OLDEST_SLOT is falsified

CAP3_SYNTHETIC_RESULT=FIFO 0.158 / RANK_NET 0.660 / COMPOSED 0.791 bps per slot-hour (LP bound 1.445); COMPOSED +0.224 dz vs FIFO
CAP4_SYNTHETIC_RESULT=FIFO 0.161 / RANK_NET 0.619 / COMPOSED 0.708 (LP bound 1.260); +0.195 dz
CAP6_SYNTHETIC_RESULT=FIFO 0.162 / RANK_NET 0.552 / COMPOSED 0.602 (LP bound 1.006); +0.157 dz   [synthetic sensitivity only; no production cap recommended; max_open_positions is not to be raised on this basis]

NO_LOOKAHEAD_PROVEN=YES within tested scope (27 implementable policies x 5 scenario cases: counterfactual-latent and future-truncation tests, 0 failures; leaky canary detected 5/5; static audit clean)
CANDIDATE_SPAM_HANDLED=PARTIAL — handled by calibrated methods (COMPOSED −22% under 3 spam opps/h; UNCERTAINTY_LCB); plain ranking and shadow-price rules are not (−72% / −59%); no identity/dedup rule was tested
STARVATION_MEASURED=YES — zero for simple EV ranking; non-zero for bandits/secretary and for other instruments under a gamed instrument

ANY_DROP_IN_ALLOCATOR=NO
ANY_SCIENTIFIC_INVALIDATION=NO for the final verdict (run 1 invalidated pre-held-out and superseded; disclosed in 04, 12, 13)

FINAL_VERDICT=CAPACITY_ALLOCATION_REFERENCE_SUPPORTED
```

### Explication ligne par ligne
- `ALGORITHMS_DISCOVERED=36` : nombre d'idées répertoriées au rapport 02 (la ligne 22 regroupe les cinq baselines). ✔ 36 lignes numérotées.
- `ALGORITHMS_EXECUTED=29 …` : 29 politiques dans la grille held-out (27 utilisables + 2 « oracles » qui voient le futur). ✔ 29. S'y ajoutent hors grille : 2 diagnostics post-hoc, 1 canari, MABWiser, et les contrôles de solveurs.
- `HELDOUT_SCENARIOS=15 … 52,200 runs` : 15 familles × 3 variantes × 4 capacités × (10 graines) × 29 politiques ; 45 instances de scénario. ✔.
- `SEEDS=…` : les graines des sous-jeux (tuning 3, validation 4, robustesse 5, défaillance 6). ✔.
- `FIFO_FAILURE_SCENARIOS=13` : familles où FIFO est nettement dominé (règle du §2.6). ✔ liste identique à `heldout_verdict.json`.
- `FIFO_EQUIVALENT_SCENARIOS=1` : S1 (demande éparse). S6 est « entre deux » (0,086).
- `BEST_SLOT_HOUR_REFERENCE=SHADOW_PRICE` : meilleure méthode d'économie de slot ; **c'est un choix descriptif, pas une décision de la règle de verdict** (qui a désigné COMPOSED). Nuance : dans le classement pré-enregistré des méthodes à seuil, KNAPSACK/FLUID/SHADOW sont statistiquement à égalité.
- `BEST_DIVERSIFICATION_REFERENCE=CORR_PENALTY` : la pénalité douce de corrélation, propre mais de faible effet ; `MARGINAL_RISK` fait mieux en chiffres mais partiellement pour une autre raison.
- `BEST_TURNOVER_REFERENCE=SHADOW_PRICE` : la meilleure « gestion du turnover » est de ne pas forcer de sorties, mais de laisser des slots vides.
- `CAP3/4/6_SYNTHETIC_RESULT` : lat/slot-h de FIFO, RANK_NET, COMPOSED et borne LP ; ✔ tous exacts. À lire comme forme de courbe, pas comme recommandation de plafond.
- `NO_LOOKAHEAD_PROVEN=YES within tested scope` : 0 échec sur 135 runs de test (27 × 5) ; le canari (politique volontairement tricheuse) est détecté 5/5 ; audit statique sans occurrence des champs latents. « Proven » signifie « dans le périmètre testé », voir §6.
- `CANDIDATE_SPAM_HANDLED=PARTIAL` : seule la calibration par instrument encaisse le spam.
- `STARVATION_MEASURED=YES` : la famine d'instruments a été mesurée (nulle pour les classements simples, non nulle pour bandits/secrétaire ou sous triche).
- `ANY_DROP_IN_ALLOCATOR=NO` : aucune bibliothèque prête à l'emploi.
- `ANY_SCIENTIFIC_INVALIDATION=NO for the final verdict` : le run 1 a été invalidé avant tout held-out ; le verdict final n'est pas invalidé **d'après le rapport**. Voir §7 : je ne trouve pas d'invalidation formelle mais des faiblesses substantielles.
- `FINAL_VERDICT=CAPACITY_ALLOCATION_REFERENCE_SUPPORTED` : « une méthode de référence est soutenue » (COMPOSED) ; les autres valeurs possibles sont `MULTIPLE_CAPACITY_METHODS_SUPPORTED`, `FIFO_REMAINS_SUFFICIENT`, `NO_CAPACITY_METHOD_SUPPORTED`, `STUDY_INCONCLUSIVE`.

---

## 6. Contrôles de validité

### 6.1 Tests de fuite (lookahead)
Code : `bench/capacity_v1/py/validate_and_leakage.py`. Résultat : `results/validation.json` → `leakage.NO_LOOKAHEAD_PROVEN_within_tested_scope = true` (✔), 135 runs (27 politiques × 5 cas : S3, S5, S9, S7, S10), échecs `[]`.
- **T1 contrefactuel** : on brouille les champs latents (edge, durée, coût vrai) de toutes les opportunités *jamais admises* ; le journal complet des décisions doit rester identique.
- **T2 troncature du futur** : on brouille tout ce qui n'est connaissable qu'après t0 = 400 (arrivées après t0, leurs observables, rendements futurs) ; les décisions jusqu'à t0 doivent être identiques.
- **T3 canari** : une politique volontairement tricheuse doit être détectée : 5/5 par les deux tests (✔ `leakage.log`).
- **T4 audit statique** : 0 occurrence de `W.edge`, `W.dur`, `cost_true`, `.CR`, `needs_world`, `attach(`, `world` dans le code des politiques implémentables ; les champs de `View` ne contiennent pas de champ latent ✔.
- Erreur corrigée en route (avouée) : 28 fausses alarmes dues à un test qui brouillait les opportunités arrivant *à* t0 (légitimement visibles) ; corrigé (`arrival > t0`) → 0 échec.
- **Limites que je constate en lisant le code** : (i) les tests utilisent `GRIDS[name][0]` (première configuration de grille, **pas les paramètres tunés**) ; (ii) un seul monde par cas (graine 4242), capacité 4 seulement, variante de TUNING ; (iii) l'audit statique est une recherche de mots-clés ; (iv) `cluster` est fourni à la politique (structure de corrélation connue d'avance, `policy.reset(cap, seed, N, W.cl)`), donc les clusters ne sont pas estimés ; (v) le tirage de la graine du hasard de politique est dérivé de la graine du monde (`12345 + seed`), sans effet de fuite. Le rapport 13 (point 12) reconnaît les limites (i)-partielle, (ii), (iii).

### 6.2 Déterminisme
✔ J'ai relancé `make_world` + `run` sur trois mondes held-out (S3/S8/S10, variante 0, graine 9000, capacité 4) : les `lat_net` de `COMPOSED` coïncident au chiffre près avec `heldout_raw.csv.gz` (5174,7844502 pour S3 ; 2016,69354442 pour S8 ; 3518,26651979 pour S10) et le nombre d'admissions aussi (529, 398, 520). Reproductibilité numérique confirmée dans mon environnement (Python 3.11.15, NumPy 2.4.6, SciPy 1.17.1).

### 6.3 Contrôles négatifs / positifs
- Positif : canari détecté ; Erlang-B (erreur max 0,0197) ; glouton ≡ MILP (200/200) ; affectation ≡ top-k (200/200) ; CP-SAT ≡ glouton (100/100).
- Négatifs / falsifications : `OLDEST_SLOT` (churn) fortement négatif ; `CORR_HARD_REJECT`, `CLUSTER_CAP` ; pente de calibration négative → tous les classements par score perdent contre FIFO ; coût ×4 → tous perdent de l'argent.

### 6.4 Erreurs corrigées / écarts au protocole déclarés
1. **Run 1 remplacé** (avant tout held-out) : biais d'échauffement de l'estimateur de covariance (prior `eye·40` qui décroît lentement), rétrécissement 0,2 trop fort, normalisateur `dens0_sd` qui explose sur des scénarios presque identiques (S12) ; corrigé en EWMA corrigée du biais + δ = 0,05 + normalisateur `dens0_rms`. Diff vérifié dans `git diff origin/main..branche` (mes lectures de `policies.py`/`env.py`/`runner.py` confirment ces trois changements). Les artefacts v1 sont conservés dans `results/superseded_run1/`.
2. **Chronologie serrée** : pré-enregistrement v1 à 15:11 UTC, run 1 déclaré remplacé à 15:13, pré-enregistrement v2 à 15:29, held-out lancé 15:29:35, terminé environ 15:46. La correction a été décidée en deux minutes. Rien dans les données ne permet de dire que le held-out a été regardé avant (la log de lancement est bien après le v2), mais on ne peut pas le prouver non plus : ? non vérifiable, on n'a que les horodatages de commit.
3. **Seuils modifiés après vue de la validation** (avoué en 04 et 13) : `delta_material` 0,15 → 0,10 et `delta_equivalence` 0,03 → 0,02 (v1 : `superseded_run1/PREREGISTRATION_v1.json`). C'est précisément `delta_equivalence` qui bascule le verdict (0,03 → `MULTIPLE_CAPACITY_METHODS_SUPPORTED`). Voir §7.
4. **Robustesse et défaillances** (graines 3000+/4000+) ont été exécutées et commitées **après** le held-out (les logs sont dans `db7e45a` et `ea3fc74`) ; elles ne changent pas le verdict, mais leur conception n'est pas pré-enregistrée.
5. **Divergences internes mineures** entre l'outil d'analyse et le verdict : `analyze.py` utilise un seuil « matériel » de 0,15 pour ses colonnes `frac_cells_material_*` alors que le verdict utilise 0,10 (le verdict est produit par `heldout_verdict.py`, donc le calcul de référence est cohérent) ; les IC de `report_tables.py` (graine 7) diffèrent de ceux de `heldout_verdict.json` (graine 20260929) de ±0,001 (ex. COMPOSED vs FIFO [0,160 ; 0,182] dans les rapports vs [0,1605 ; 0,1817] en JSON).
6. **Process** : la PR #6 a été fusionnée par quelqu'un d'autre pendant l'étude ; le travail continue sur une branche recréée à partir de `main`. Le contenu fusionné (simulateur, politiques, tuning partiel) est un sous-ensemble ; les paramètres tunés y sont **différents** des paramètres finaux (ex. `ONLINE_KNAPSACK_PSI.U` 4,0 → 1,5 ; `SHADOW_PRICE` (η, cible) (0,1 ; 0,95) → (0,02 ; 0,8) ; `CORR_HARD_REJECT.ρ` 0,6 → 0,95 ; `FLUID_QUANTILE.s` 1,3 → 1,0). Attention : **`main` contient donc un état de tuning périmé** (ancien estimateur de covariance, ancien normalisateur) qui ne correspond pas aux résultats finaux.

---

## 7. Critique indépendante

### 7.1 Ce que je considère solide
- Conception propre : mondes déterministes, comparaisons appariées, grand nombre de graines, split disjoint, hachages figés vérifiés, script de verdict versionné, code lisible, échec avoué (run 1, fausses alarmes).
- Les résultats bruts reproduisent les rapports à l'arrondi près sur ~50 chiffres vérifiés (§ index de vérification ci-dessous). Peu d'écarts, tous mineurs — sauf les deux ci-dessous.
- Conclusion robuste dans le simulateur : FIFO est nettement dominé quand la demande dépasse la capacité, mais surtout parce qu'il admet des valeurs négatives et sert le plus périmé d'abord.

### 7.2 Points faibles majeurs
1. **Le verdict « COMPOSED = référence » dépend des familles de spam (mon test, ✔).**
   Le gain de `COMPOSED` sur `RANK_NET` est +0,0231 (IC [0,0193 ; 0,0268] avec ma graine) sur 15 familles. Par famille : S10 +0,129, H3 +0,037, S3 +0,049, H1 +0,034 ; S12 −0,019 ; S1 0,000. Si on retire **S10 seule**, `COMPOSED` tombe à **+0,0155** (< barre 0,02) et `SHADOW_PRICE` à +0,0127, `KNAPSACK` +0,0130 ; l'écart COMPOSED−SHADOW devient +0,0028 [−0,0005 ; +0,0062]. Si on retire **les deux familles de spam** (S10, H3), l'ordre s'inverse : `ONLINE_KNAPSACK_PSI` +0,0213 et `SHADOW_PRICE` +0,0197 contre `COMPOSED` +0,0138 ; COMPOSED−SHADOW = **−0,0059 [−0,0072 ; −0,0046]** (COMPOSED significativement pire). Dans 10 familles sur 15, COMPOSED est en dessous de SHADOW_PRICE (S1 −0,000, S2 −0,000, S3 −0,014, S4 −0,007, S5 −0,010, S6 −0,007, S7 −0,011, S8 −0,002, S9 −0,016, H1 −0,004, H2 −0,009, S11 −0,001 : douze valeurs ≤ 0 dont deux à zéro arrondi). La règle pré-enregistrée pondère les 15 familles également ; le rapport le sait en partie (« fragilité »), mais il ne dit pas que **le gain moyen est porté par une famille (S10) conçue pour être favorable à la calibration par instrument** (biais constant +12 sur un instrument, sur lequel une calibration par instrument est presque optimale par construction).
2. **Barre à 0,02 et marge de 0,003, fixées après avoir vu la validation.** La v1 avait 0,03 ; avec 0,03 le même jeu donne `MULTIPLE_CAPACITY_METHODS_SUPPORTED` (✔ : aucun des trois n'atteint 0,03). Le rapport publie cette sensibilité, ce qui est honnête ; mais la « pré-enregistrement » est moins contraignante qu'elle en a l'air.
3. **Le composant « staleness hazard » est inerte** (§3.4, ✔ prouvé par rejeu). Le rapport présente `COMPOSED` comme contenant une mécanique de péremption qui n'a jamais fonctionné ; l'interprétation « τ = 1 en bord de grille = bouton éteint » est un artefact de départage.
4. **Intervalles de confiance trop étroits pour la variance de conception.** L'IC bootstrap est calculé sur 450 blocs (famille × variante × graine), mais seulement 45 tirages de paramètres de scénario existent (3 variantes par famille) et 15 familles. Mon bootstrap en grappes (✔) donne pour COMPOSED−RANK_NET : IC par (famille, variante) [0,0137 ; 0,0345] (45 unités) et par famille [0,0088 ; 0,0413] (15 unités) ; et pour COMPOSED−SHADOW_PRICE : [−0,0025 ; +0,0197] et [−0,007 ; +0,0276]. La barre 0,02 est à l'intérieur de ces IC : impossible de trancher statistiquement entre COMPOSED, SHADOW_PRICE et KNAPSACK. Le rapport 13 (point 4) reconnaît que les IC ne couvrent pas la conception ; il ne chiffre pas l'effet.
5. **Tout dépend de la forme du simulateur** (rédigé par l'auteur) : décroissance exponentielle de l'edge (τ = 8 h) ; score = fonction linéaire de l'edge courant recalculée à chaque heure (`refresh`) ; durée connue via un a priori de mauvaise qualité ; coût fixe. Chaque conclusion « FIFO perd » est relative à ces choix. FIFO est de plus pénalisé mécaniquement (il sert le plus périmé d'abord alors que l'edge décroît de 30 % en 3 heures : exp(−3/8) ≈ 0,69, calcul de ma part ; le score, lui, est déjà recalculé à chaque âge).
6. **Grille de tuning : optima au bord, plus nombreux que ne l'annonce le rapport.** Le rapport 04/13 cite comme optima au bord : `SLOTHOUR_HAZARD τ`, `ONLINE_KNAPSACK_PSI U`, `CORR_PENALTY g`, `CORR_HARD_REJECT ρ` (04), et en 13 : `EVICT_SWAP`, `SLOTHOUR_DENSITY h0`, `LINUCB α`. Je constate (par comparaison `tuned_params.json` × `policies.GRIDS`) :
   - **Bord confirmé** : `ONLINE_KNAPSACK_PSI` U = 1,5 (minimum) **et L = 0,25 (minimum, non cité)** ; `CORR_HARD_REJECT` ρ = 0,95 (maximum) ; `EVICT_SWAP` mh = 12 (max) et M = 1,5 (max) ; `SHADOW_PRICE` η = 0,02 et cible = 0,8 (**les deux au minimum de la grille, non cités**) ; `COMPOSED` k = 0,5 et s = 1,2 (**les deux au maximum d'une grille de 2 points, non cités**) ; `TRUNK_RESERVATION` q = 0,75 (max), r = 1 (min) ; `SLEEPING_HEDGE` ζ = 8 (max), η = 0,05 (min) ; `UNCERTAINTY_LCB` κ = 25 (min) ; `OLDEST_SLOT` min_hold = 12 (max).
   - **Cité à tort comme bord** : `CORR_PENALTY` g = 0,02 (intérieur de 0,005…1,0) ; `LINUCB` α = 0,6 (intérieur de 0,05…3,0) ; `SLOTHOUR_DENSITY` h0 = 12 (24 est dans la grille ; les objectifs 6/12/24 sont 0,1405/0,1408/0,1408 : plat). ✘
   - **`COMPOSED` n'a été réglé que sur 8 configurations** (k ∈ {0 ; 0,5}, g ∈ {0 ; 0,15}, s ∈ {0,8 ; 1,2}), avec `h0 = 2` et `τ = 6` fixés à la main et non explorés ; les méthodes à seuil concurrentes ont 4 à 10 configurations. Le rapport 13 note que bandits et experts ont reçu moins de recherche.
   - Rapport 07 écrit « grid 0/3/6/12 h » pour `OLDEST_SLOT` ; la grille du code est (3, 6, 12) ✘ mineur.
7. **Les oracles glouton ne sont pas des bornes** (avoué) : `ORACLE_SCORE` < plusieurs méthodes implémentables ; la seule vraie borne est la LP (hors early exit). Les « % de la borne LP capturés » ne mesurent donc pas la marge d'amélioration atteignable.
8. **Le seuil « FIFO_FAIL » est une sélection du maximum de quatre méthodes par famille**, à seuil 0,10 : optimiste par construction (avoué). S2 (0,100) et H2 (0,104) sont à la limite.
9. **Pas d'effet de taille de position, pas d'impact de marché, pas de remplissages partiels, pas de niveaux de frais** (avoué en 13). Les positions ont une taille unitaire ; le « gain » est en bps d'une position.
10. **Le risque est mesuré sur des PnL quotidiens à taille fixe**, 41 jours par monde (T = 1000 h) : les mesures de drawdown/volatilité reposent sur peu de jours.
11. **Diversification : les clusters sont connus des politiques** (donnée a priori). Le plafond par cluster (`CLUSTER_CAP`) et la pénalité utilisent donc une information de structure parfaite ; dans le réel, cette structure est estimée (`CORR_PENALTY` estime les corrélations, mais `CLUSTER_CAP` reçoit les vrais clusters).
12. **Le bandit n'a pas reçu la même chance** : fonctionnalités à 6 dimensions, récompense normalisée « réalisé/tenue/5 » écrêtée à ±3, aucune exploration forcée ; le rapport le concède partiellement (13.5).
13. **Résultats de régime** : changement permanent unique ; aucun estimateur à fenêtre courte ou détecteur de rupture testé (avoué).
14. **Statistique multiple** : 29 politiques, verdict sur une short-list choisie mécaniquement en validation ; sélection par le maximum (« meilleur de » par famille). Le rapport le note.

### 7.3 Ce que les chiffres ne prouvent PAS
- Ils ne prouvent rien sur AurumShift ni sur des marchés réels (UNKNOWN).
- Ils ne prouvent pas que `COMPOSED` soit meilleur que `SHADOW_PRICE` ou `ONLINE_KNAPSACK_PSI` hors situations de spam.
- Ils ne prouvent pas que la valeur d'un slot supplémentaire suive la courbe concave observée (la forme est produite par la distribution de qualité simulée).
- Ils ne prouvent pas l'absence de fuite d'une politique modifiée (tests limités au périmètre testé).
- « FIFO perd de 0,171 dz » n'est pas « les stratégies AurumShift perdent » : une part est due à l'hypothèse de décroissance et à l'admission de valeurs négatives.

### 7.4 Écarts rapports ↔ résultats bruts (récapitulatif)
| # | Écart | Gravité |
|---|---|---|
| 1 | « Staleness hazard » décrit comme composant actif de COMPOSED et de SLOTHOUR_HAZARD ; en fait inerte (score_age ≡ 0) ; « τ=1 en bord de grille » est un artefact d'égalité | Élevée (description erronée d'un composant) |
| 2 | Résumé exécutif : « le soft penalty (CORR_PENALTY) divise le risque de queue par deux » — c'est vrai pour MARGINAL_RISK ; CORR_PENALTY : −33 % (vol.), −25 % (drawdown) à ×8 | Moyenne |
| 3 | Résumé exécutif : « 6–14 points de slot-heures inactifs » ; mesuré 6,0–10,3 | Faible |
| 4 | Optima au bord : liste incomplète (SHADOW_PRICE η & cible, COMPOSED k & s, ONLINE_KNAPSACK L, etc.) et trois entrées à tort (CORR_PENALTY g, LINUCB α, SLOTHOUR_DENSITY h0) | Moyenne |
| 5 | « LinTS est la seule méthode qui récupère » à pente −0,3 : LinUCB récupère aussi (0,252 vs LinTS 0,277) | Faible |
| 6 | COMPOSED −22 % (mesuré −22,6 %) | Cosmétique |
| 7 | Grille OLDEST_SLOT « 0/3/6/12 » vs code (3,6,12) | Cosmétique |
| 8 | IC de `report_tables.py` (graine 7) vs `heldout_verdict.json` (graine 20260929) : ±0,001 | Cosmétique |
| 9 | `analyze.py` seuil matériel 0,15 vs verdict 0,10 | Cosmétique (colonnes auxiliaires) |
| 10 | Le rapport dit que les probes « robust/failure » ont utilisé des « graines séparées » ✔ ; elles ont été exécutées après le held-out | Information |

### 7.5 Contradictions internes
- Le rapport 12 §2 affirme que `COMPOSED` est « la seule méthode qui gère le spam et la plus fragile sous bruit » : cohérent avec mes constats, mais alors qualifier `COMPOSED` de « référence » sans condition contredit cet énoncé : la référence dépend de l'hypothèse « le score est gameable ». Le rapport le dit lui-même (« c'est le compromis qui est le vrai résultat »).
- Le point 2 du rapport 00 (« FIFO n'est pas une référence suffisante dans 13 familles sur 15 ») coexiste avec le fait que 5 seulement dépassent 0,10 face à FIFO_NETPOS ; le rapport le précise, mais le titre de la conclusion reste FIFO-centrique.

---

## 8. Points de comparaison à vérifier contre l'étude B

(L'étude B est réalisée par un autre analyste ; voici ce qu'il faudra confronter, sans que j'aie lu B.)

1. **Verdict** : B rend-il `CAPACITY_ALLOCATION_REFERENCE_SUPPORTED`, `MULTIPLE_…` ou `FIFO_REMAINS_SUFFICIENT` ? Quelle marge sur le classement simple ?
2. **FIFO vs FIFO avec filtre valeur > 0** : B sépare-t-il « filtrer » de « classer » ? (chez A : 0,090 sur 0,171.)
3. **Fraîcheur** : B modélise-t-il une décroissance de l'edge avec l'attente ? FIFO y est-il pénalisé de la même façon ?
4. **Nombre de familles de scénarios où FIFO échoue** (A : 13/15) et seuil utilisé (A : 0,10 dz).
5. **Méthode gagnante** : seuils de coût d'opportunité (SHADOW_PRICE / KNAPSACK / FLUID) ? Calibration par instrument ? Le gain dépend-il du spam ?
6. **Valeur par slot-heure** : B trouve-t-il, comme A, que diviser par la durée seule n'apporte rien (+0,002) ?
7. **Diversification** : pénalité douce vs plafond/rejet dur (A : douce OK, dure mauvaise) ; effet sur volatilité/drawdown.
8. **Turnover forcé** : B teste-t-il des sorties forcées ? (A : churn −0,218 dz, échange à marge haute +0,005.)
9. **Bandits / secrétaire / sleeping experts** : sous le classement simple chez A ; B ?
10. **Sensibilité à la capacité** : courbe A (COMPOSED vs FIFO +0,224 → +0,107 de 3 à 10 slots) ; B a-t-il la même forme ? Aucun plafond ne doit être déduit.
11. **Coût inconnu ≠ 0** et signal manquant : mêmes effets (A : −0,004 dz, −12 % à 70 % inconnu).
12. **Fuite** : B teste-t-il aussi de façon contrefactuelle ? Avec les paramètres tunés ?
13. **Protocole** : pré-enregistrement daté avant held-out ? seuils modifiés après validation ? Nombre de graines et d'unités de conception indépendantes (A : 450 blocs mais 45 tirages de scénario).
14. **Modes de défaillance** : changement de régime (A : aucune méthode ne s'adapte en 500 h), effondrement de corrélation, bruit extrême.
15. **Bibliothèques** : mêmes verdicts (SciPy/HiGHS pour bornes, OR-Tools, SimPy) ? Aucune bibliothèque drop-in ?
16. Vérifier, chez B, que les composants « inertes » ou dupliqués n'existent pas (piège de A : hazard inerte).

Divergences attendues (INFERENCE) : différences de modèle d'arrivée, de décroissance et de score ; toute différence de verdict sur COMPOSED vs seuils est plausiblement liée au poids donné au spam.

---

## 9. Reproductibilité

- **Dépendances** : Python 3.11 ; NumPy, SciPy, pandas ; pour la sonde OSS : ortools, mabwiser, simpy, river, cvxpy, pyportfolioopt, scikit-learn (README). Versions utilisées par l'auteur dans `oss_probe.json`.
- **Commandes** (README, depuis `bench/capacity_v1/py/`) : `python3 validate_and_leakage.py ; python3 runner.py tune ; python3 runner.py validate ; <pré-enregistrer> ; python3 runner.py heldout ; python3 heldout_verdict.py`. Puis `analyze.py`, `report_tables.py heldout|robust|failure`, `posthoc.py`, `build_reports.py`, `oss_probe.py`.
- **Durées observées** (logs) : tuning ≈ 500–530 s (108 jobs, 4 processus) ; validation ≈ 311 s ; held-out 1 014 s ; robustesse 388 s ; défaillances 112 s.
- **Fournis** : code complet, résultats bruts compressés (tuning, validation, held-out, robustesse, défaillances), paramètres gelés, pré-enregistrement, verdict JSON, tables, run 1 archivé, logs. Suffisant pour recalculer tous les chiffres sans relancer le simulateur.
- **Manque / points d'attention** : pas de fichier de dépendances verrouillé (`requirements.txt`) ; pas de script unique « tout relancer » (la ligne du README contient `<pre-register>` comme étape manuelle) ; le pré-enregistrement est fait à la main ; `robust`/`failure` ne sont pas listés dans la ligne de commande du README ; les bibliothèques externes VW/OBP/Riskfolio ne sont pas exécutées.
- **Ce que j'ai vérifié moi-même** : lecture de tous les scripts ; rechargement des CSV bruts avec pandas ; rejeu de 3 mondes held-out (résultats identiques à 10 décimales) ; recalcul des hachages ; recalculs de l'ensemble des tableaux clés (§3) et des analyses supplémentaires (§7). Je n'ai pas relancé le held-out complet (~17 min sur 4 cœurs) ni les LP.

---

## 10. Implications pratiques pour AurumShift (pistes « à adjuger plus tard », aucune affirmation de compatibilité)

Toutes ces pistes sont des hypothèses issues d'un simulateur ; rien n'est établi pour AurumShift, dont le code n'a pas été lu.

1. **Piste « filtre + fraîcheur avant sophistication »** : à adjuger : le mécanisme actuel d'AurumShift (inconnu ici) admet-il des candidats à valeur nette estimée ≤ 0 ou sert-il les plus anciens d'abord ? Dans le simulateur, ces deux points expliquent plus de la moitié du gain.
2. **Piste « coût d'opportunité par slot »** : laisser volontairement un slot vide lorsque le meilleur candidat est marginal (prix fictif / seuil). À adjuger : existence d'un mécanisme équivalent, mesure du gain sur des données PIT réelles.
3. **Piste « calibration causale par instrument »** contre le spam/la triche de score : à adjuger si AurumShift reçoit des scores générés par des modèles ou des sources potentiellement biaisées ou redondantes. Attention : coût quand il n'y a pas d'attaque (SHADOW_PRICE 0,883 vs COMPOSED 0,824 sans spam) et fragilité sous bruit fort.
4. **Piste « pénalité douce de corrélation »** (et non plafond dur) pour réduire volatilité/drawdown : à adjuger avec les vrais clusters estimés (ici donnés) et éventuellement un estimateur type Ledoit–Wolf (plus précis à fenêtre longue dans la sonde).
5. **Piste « ne pas forcer de sorties »** : le turnover forcé est négatif dans le simulateur.
6. **Piste « compter les rejets par opportunité unique »** : l'observation des `evals_per_opp` (~3) rappelle que des rejets répétés d'un même candidat ne sont pas des occasions indépendantes.
7. **Piste « coût inconnu ≠ 0 »** : déjà conforme à la doctrine ; chiffrage de l'effet à adjuger.
8. **À NE PAS déduire** : aucune valeur de `max_open_positions` ; aucun gain en bps réels ; aucun choix entre COMPOSED, SHADOW_PRICE, KNAPSACK.

---

## 11. Questions ouvertes et suites recommandées (classées par valeur)

1. **Corriger et rejouer le composant hazard** (mettre `refresh=False` dans au moins une famille, ou supprimer le composant) et **ré-évaluer COMPOSED**. Valeur : élevée, coût faible. Change potentiellement la description de la « référence ».
2. **Tester la sensibilité du verdict à la composition des familles** (leave-one-family-out, bootstrap en grappes famille/variante) et publier une barre d'équivalence justifiée a priori. Valeur : élevée ; les calculs de §7 montrent que le verdict n'est pas robuste à S10/H3.
3. **Élargir les variantes de scénario** (> 3 par famille, pour que l'incertitude de conception soit estimée) et tuner COMPOSED de façon aussi large que ses concurrents (h0, τ, k, s, κ).
4. **Attaquant adaptatif et dé-duplication d'identité** (le rapport le propose) : biais variable dans le temps, spam corrélé sur plusieurs instruments, règle de dédoublonnage. Valeur : élevée si les scores d'AurumShift peuvent être redondants.
5. **Adaptation au changement de régime** (fenêtres courtes, détecteurs de rupture, apprentissage à oubli) — aucune méthode testée ne s'adapte en 500 h.
6. **Intégrer Ledoit–Wolf dans `CORR_PENALTY`/`MARGINAL_RISK`** et clusters estimés (non donnés).
7. **Sensibilité au modèle de décroissance de l'edge** (τ, absence de décroissance) : mesurer combien du gain de FIFO→RANK_NET est de la fraîcheur.
8. **Étude sur données réelles PIT** (hors de ce dépôt externe) pour au moins un paramètre clé : pente de calibration du score, décroissance de l'edge, distribution des durées.
9. **Exécuter VW / OBP / Riskfolio** si la piste bandits ou l'allocation de portefeuille reste d'actualité (actuellement PARK sans exécution).
10. **Ménage du dépôt** : `main` contient l'état de tuning périmé de la PR #6 ; à synchroniser avec la PR #10 (une fois relue) pour éviter la confusion.

---

## 12. Index des fichiers lus

Rapports (`reports/008_risk_capacity_turnover/`, tous lus intégralement) :
- `00_EXECUTIVE_SUMMARY.md` — résumé, 8 constats, bloc final.
- `01_PROBLEM_FORMULATION.md` — problème de décision, abstraction de résultat net, économie de slot.
- `02_ALGORITHM_LANDSCAPE.md` — 36 idées, statut EXEC/EXEC-OSS/REF.
- `03_BASELINES.md` — baselines, contrôles, différences appariées, diagnostic LIFO.
- `04_SYNTHETIC_PROTOCOL.md` — environnement, scénarios, splits, prééenregistrement, tests de fuite, validation du simulateur.
- `05_SLOT_ECONOMICS.md` — tableau des 29 politiques, regret LP, vue par famille.
- `06_DIVERSIFICATION.md` — pénalités de corrélation, stress d'effondrement.
- `07_TURNOVER.md` — seuils de coût d'opportunité, échanges, S6.
- `08_CAPACITY_SENSITIVITY.md` — courbes selon 3/4/6/10 slots.
- `09_HELDOUT_RESULTS.md` — 29 politiques, critères, FIFO par famille, robustesse.
- `10_FAILURE_MODES.md` — spam, triche, famine, régime, bruit, oscillation.
- `11_OSS_COMPONENTS.md` — bibliothèques exécutées et verdicts.
- `12_ADJUDICATION.md` — verdict, décomposition, ledger de falsification, bloc final.
- `13_LIMITATIONS.md` — 15 limites.

Code et configuration (`bench/capacity_v1/`) :
- `README.md` — carte des fichiers, commande de reproduction.
- `prereg/PREREGISTRATION.json` — pré-enregistrement v2.
- `py/env.py` (508 lignes) — simulateur, métriques, borne LP, perturbations de fuite.
- `py/policies.py` (604) — 29 politiques, calibration, grilles.
- `py/scenarios.py` (83) — familles, variantes, splits.
- `py/runner.py` (168) — tune/validate/robust/failure/heldout.
- `py/heldout_verdict.py` (117) — règles de verdict pré-enregistrées.
- `py/validate_and_leakage.py` (125) — Erlang-B, glouton = MILP, tests T1–T4.
- `py/posthoc.py` (85) — LIFO_NETPOS, MARGINAL_DIAG.
- `py/analyze.py` (76), `py/report_tables.py` (207), `py/build_reports.py` (15) — génération de tables. `py/oss_probe.py` (148) : en-tête et sortie lus (`oss_probe.json`/`.log`), corps non lu en détail.

Résultats (`bench/capacity_v1/results/`) :
- `heldout_raw.csv.gz` (52 200 lignes), `validation_raw.csv.gz` (16 704), `robustness_raw.csv.gz` (19 440), `failure_raw.csv.gz` (6 156) — chargés avec pandas et exploités.
- `tuning_table.csv` (92 configurations), `tuned_params.json` — lus. `tuning_raw.csv.gz` — non ouvert.
- `heldout_verdict.json`, `validation_verdict_dryrun.json`, `validation.json` — lus.
- `posthoc_validation.csv.gz` — non ouvert ; `tables/posthoc.md` — lu.
- Logs `tune.log`, `validate.log`, `heldout.log`, `robust.log`, `failure.log`, `leakage.log`, `oss_probe.log`, `oss_probe.json` — lus.
- `tables/*.md`, `heldout_cells_vs_FIFO.csv`, `heldout_summary_vs_*.csv`, `heldout_main_table.csv` — non lus un par un (les rapports en reprennent les contenus, que j'ai recalculés à partir des données brutes).
- `superseded_run1/` : `PREREGISTRATION_v1.json` (seuils et statut), `tuned_params.json`, `tune.log`, `validation_verdict_dryrun.json` lus ; le reste non lu.

PR #6 sur `origin/main` : liste des fichiers et diffs des commits `1d676ff`, `588dc4b`, `da2f7c4` ; `tuned_params.json` et `tune.log` de main lus ; `git diff origin/main..branche` sur `policies.py`, `env.py`, `runner.py`, `analyze.py` lus. PR #10 : métadonnées lues via l'API GitHub.

### Index des vérifications chiffrées (✔/✘/?)
| # | Chiffre du rapport | Résultat |
|---|---|---|
| 1 | 52 200 runs / 29 politiques / 450 mondes / graines 9000–9009 | ✔ |
| 2 | lat/slot-h moyens des 29 politiques (FIFO 0,162 … COMPOSED 0,644 …) | ✔ |
| 3 | COMPOSED vs FIFO +0,171 [0,160 ; 0,182] | ✔ (0,1711 [0,1605 ; 0,1817]) |
| 4 | COMPOSED vs RANK_NET +0,023 [0,020 ; 0,027] | ✔ (0,0231 [0,0196 ; 0,0268]) |
| 5 | dz par capacité (COMPOSED 0,224/0,195/0,157/0,107) | ✔ |
| 6 | Borne LP 1,445/1,260/1,006/0,714 ; capture oracle 71–93 % | ✔ |
| 7 | OLDEST_SLOT 155 sorties/run, −0,218 | ✔ (154,7 ; −0,2183) |
| 8 | Utilisation : « 6–14 points » | ✘ (6,0–10,3) |
| 9 | evals_per_opp ≈ 3,0 | ✔ (3,04) |
| 10 | Spam : −72 % / −59 % / −22 % | ✔ (−71,7 / −59 / −22,6) |
| 11 | Triche de score, bruit, régime (séries de valeurs) | ✔ |
| 12 | Diversification : 9 lignes × 4 métriques | ✔ |
| 13 | Stress corrélation (RANK_NET 105→493, MARGINAL_RISK 91→259) | ✔ ; « soft penalty divise par deux » ✘ pour CORR_PENALTY (−33 % / −25 %) |
| 14 | Table S6 par variante | ✔ |
| 15 | Erlang-B 0,0197 ; SimPy | ✔ |
| 16 | MABWiser 0,277 / LinUCB 0,363 / FIFO −0,059 | ✔ |
| 17 | Hachages du prééenregistrement (4) | ✔ |
| 18 | Stabilité validation → held-out (0,179→0,171 …) | ✔ |
| 19 | Table FIFO_FAIL par famille (15 lignes) | ✔ |
| 20 | Post-hoc LIFO/MARGINAL_DIAG | ✔ |
| 21 | « SLOTHOUR_HAZARD τ = 1 en bord de grille / bouton éteint » | ✘ (égalité exacte des 5 τ) |
| 22 | Optima au bord (liste) | ✘ (incomplète et 3 erreurs) |
| 23 | « LinTS seule à récupérer » (pente −0,3) | ✘ mineur |
| 24 | CV de seuil 4–5 ; oscillation ; regret LP par famille (rapport 05) ; durée « ~1,4 s par LP » | ? |
| 25 | Nombre de fichiers 91 (PR) / 94 (moi, rapports + bench) | ✔ (différence : 91 = fichiers modifiés vs `main`, dont certains déjà présents) |
