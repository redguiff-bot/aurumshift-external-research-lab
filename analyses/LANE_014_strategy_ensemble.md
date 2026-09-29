# Analyse approfondie — Lane 014 : ensemble de stratégies, experts endormis (sleeping experts)

Deux runs indépendants : PR #15 (`STUDY_INCONCLUSIVE`) et PR #21 (`NO_ROBUST_ENSEMBLE_METHOD`).
Rédigé pour Jean-François. Je tutoie et j'explique chaque terme technique à sa première occurrence.

Conventions de lecture :
- « R1 » = run 1 = branche `origin/claude/strategy-ensemble-experts-v1` (rapports en anglais, PR #15).
- « R2 » = run 2 = branche `origin/claude/strategy-ensemble-experts-v1-b` (rapports en français, PR #21).
- ✔ vérifié (j'ai recalculé ou relu le chiffre dans les fichiers de résultats bruts), ✘ écart, ? non vérifiable.
- « DÉRIVÉ » = calcul que j'ai fait moi-même à partir des fichiers bruts (pas écrit dans les rapports).
- Les labels du dépôt (`claude.md`) : PROVEN (prouvé par un test reproductible), OBSERVED (vu dans du code/des données inspectés), DOCUMENTED_CLAIM (affirmé par une source, non revérifié), INFERENCE (déduction), UNKNOWN (inconnu).

Glossaire minimal (repris plus bas quand il sert) :
- **Expert** : ici, une « stratégie » ou un modèle qui donne un signal/une prévision. Un « ensemble » les combine avec des **poids** (des pourcentages qui somment à 100 %).
- **Expert endormi (sleeping expert)** : un expert qui, à certains moments, n'est pas disponible ou pas valide (ex. une stratégie qui n'a de sens que dans un marché très volatil). Le combineur doit décider quoi faire de lui quand il « dort ».
- **Regret** : écart moyen entre ce que le combineur gagne et ce que gagnerait un « oracle » (un tricheur qui connaît la vérité). Plus bas = mieux.
- **Held-out** : jeu de test mis de côté, jamais utilisé pour régler les méthodes. **Tuning** : phase où on règle les paramètres (hyperparamètres) de chaque méthode. **Graine (seed)** : nombre qui fixe le hasard d'une simulation ; une graine = une « histoire » simulée reproductible.
- **Pré-enregistrement** : écrire à l'avance les règles de décision et les seuils, avant de voir les résultats, pour ne pas les ajuster après coup.
- **Bootstrap / IC 95 %** : technique de rééchantillonnage pour donner une fourchette (intervalle de confiance) autour d'une moyenne ; si la fourchette d'une différence ne contient pas 0, la différence est jugée « significative ».
- **Baseline** : méthode simple de référence à battre.
- **Bandit** : famille d'algorithmes qui choisissent une seule option à chaque tour et n'observent que le résultat de cette option (« machine à sous »).

---

## 0. Fiche d'identité

| | Run 1 (R1) | Run 2 (R2) |
|---|---|---|
| Branche | `claude/strategy-ensemble-experts-v1` | `claude/strategy-ensemble-experts-v1-b` |
| PR | #15, titre « Report 014 … (verdict: STUDY_INCONCLUSIVE) », état ouvert, brouillon (draft), non fusionnée, créée 2026-09-29 18:17 UTC | #21, titre « report 014 … (V1, independent run) — NO_ROBUST_ENSEMBLE_METHOD », ouverte, brouillon, non fusionnée, créée 2026-09-29 19:00 UTC |
| Commits propres à la branche (base commune `1a449df`) | 4 : `e1b345a` (générateur + préenregistrement, 17:47), `f19cd75` (tuning, 17:58), `d9d3f6c` (held-out, portes, analyses, 18:15), `054be04` (rapports, 18:17) | 3 : `d21ccc7` (environnement, apprenants, runner, adjudication « WIP », 18:30), `cfa5565` (protocole 03 + tuning round 1, 18:37), `36905d2` (held-out + rapports, 19:00) |
| Fichiers sous `reports/014_strategy_ensemble` + `bench/ensemble_v1` | 42 fichiers, 5 854 110 octets (≈5,6 Mo) | 50 fichiers, 15 335 585 octets (≈14,6 Mo) |
| Diff de la PR (GitHub) | +33 380 lignes, 42 fichiers | +4 250 lignes, 50 fichiers |
| Langue des rapports | anglais | français |
| Simulateur | 12 scénarios cœur + 1 stress, K=12 experts, T=1200 tours, récompense bornée [0,1] | 11 scénarios, K=10 experts, T=5000 tours, prévisions de probabilité, perte de Brier |
| Méthodes exécutées | 20 lignes (19 réglées + Equal), dont 6 rejouées en sémantique « naïve » | 17 méthodes + 6 ablations + 1 sonde river + une référence ORACLE |
| Runs held-out | 22 880 (fichier `heldout.log`) ✔ | 8 580 lignes de `heldout_raw.csv.gz` (11 scénarios × 30 graines × 26 configurations) ✔ |
| Verdict final | `STUDY_INCONCLUSIVE` | `NO_ROBUST_ENSEMBLE_METHOD` |
| Force du verdict | **Faible** : reconnue comme sensible aux seuils ; deux portes mal définies par l'auteur ; deux routes de calcul (littérale et « post-hoc ») aboutissent au même label ; plusieurs seuils passent ou échouent à quelques millièmes près (voir §7) | **Moyenne** : règle appliquée mécaniquement, aucun seuil changé après le held-out ; mais la porte « spécialiste rare » est quasi infranchissable par construction, et un bug de calcul (§7) touche des chiffres secondaires |

Dates : tout est daté du 2026-09-29 (une seule journée, deux sessions différentes, d'après les métadonnées des commits). Auteur des commits : « Claude ».

Source des faits de PR : lecture GitHub des PR #15 et #21 (titres, états, nombre de commits/fichiers/lignes). Les « rapports » ne mentionnent pas ces numéros.

---

## 1. Mission et question posée

### 1.1 Reformulation simple
Imagine que AurumShift possède plusieurs « stratégies » de trading de natures différentes (suivi de tendance, retour à la moyenne, portage/« carry », spécialistes de volatilité, un spécialiste d'événement rare…). À un instant donné, seules certaines sont *valides*. La question : **quelle règle en ligne (qui apprend au fil de l'eau) permet de transformer les stratégies actuellement valides en poids, à partir des résultats réalisés, sans oracle de régime, et sans supposer qu'un « bandit » soit la bonne réponse ?**

Sous-questions imposées par le cahier des charges du lane (repris dans les blocs finaux) :
1. Poids statiques suffisants ? EWMA (moyenne mobile exponentielle des performances récentes) suffisant ? Le « Hedge endormi » (sleeping experts) est-il une bonne référence ?
2. Comment traiter la **preuve manquante** (donnée absente) : ne pas la confondre avec une mauvaise performance.
3. **Famine** : un nouvel expert, un spécialiste rare, un expert en sous-performance temporaire sont-ils privés de poids indéfiniment ?
4. Non-stationnarité : changement de leader, récurrence de régimes, arrivée/départ d'experts, experts corrélés (clones).
5. La complexité (contexte, diversité, bornes) est-elle justifiée ?

### 1.2 Contraintes du dépôt (`claude.md`)
- Ordre de préférence : **REUSE → ADAPT → WRAP → COMPOSE → CUSTOM en dernier**. Les deux runs ont inspecté `river` (ensemble EWA), `mabwiser`, `contextualbandits` (R1) / `river` (R2) pour appliquer REUSE d'abord, et concluent qu'aucun n'a de masque de disponibilité, donc ADAPT/CUSTOM-petit.
- Labels PROVEN / OBSERVED / DOCUMENTED_CLAIM / INFERENCE / UNKNOWN utilisés dans les deux jeux de rapports.
- Ne pas fabriquer de résultats de benchmark ; ne pas classer sur les étoiles GitHub ; rejeter ou mettre en PARK ce qui exige trop de réglages sauf gain exceptionnel.
- Contraintes AurumShift à ne pas contredire : recherche seule/papier, pas de capital réel, PIT (point-in-time, c'est-à-dire n'utiliser que ce qui était connu à la date), pas de « lookahead » (regarder le futur), « l'absence de preuve n'est pas une preuve négative », coûts de marché réalistes.
- Mode : `EXTERNAL_RESEARCH_ONLY` (aucun code privé d'AurumShift lu). Les deux runs le disent explicitement.

---

## 2. Méthode

### 2.1 R1 — Simulateur « récompenses » (bench/ensemble_v1, R1)
Source : `reports/014_strategy_ensemble/03_PROTOCOL.md`, `bench/ensemble_v1/py/scenarios.py`, `runner.py`, `PREREGISTRATION.md`.

- **Univers** : K=12 emplacements : TREND, MREV, CARRY, DUD (mauvais), VOLSPEC (spécialiste régime R2), RARE (spécialiste régime R3), BRK (régimes R0 et R2), LATE (fort, peut être introduit tard), CLN0-2 (clones), SPARE. Récompense r∈[0,1], moyenne vraie = 0,5 + « edge » du régime. Bruit = facteur commun (écart-type 0,10) + idiosyncratique (0,10), tronqué.
- **Régimes** : 4, chaîne de Markov ; chaque régime 0-2 reste avec proba 0,97 (durée moyenne ≈33 tours) ; le régime 3 (rare, ~5 %) n'est valide que pour RARE.
- **Sémantique à 5 états** par (tour, expert) : NOT_EXIST, INACTIVE (régime invalide), ABSTAIN, GAP (alloué, résultat réalisé mais non observé), OBS (observé). Contrat : seul OBS met l'état de l'apprenant à jour.
- **Information complète** parmi les experts observés (« shadow returns » : on connaît aussi le rendement de ceux qu'on n'a pas choisis). Les bandits (SleepEXP3, DUCB) n'utilisent que l'expert échantillonné.
- **Métrique principale PR** = moyenne, sur les 12 scénarios cœur à poids égaux, du regret attendu sans bruit : `max_i μ_it − Σ_i w_it μ_it`, i parmi les experts alloués. L'oracle est donc « le meilleur expert vraiment valide » (choix dur d'un seul expert). Pas de coûts, pas de capacité, objectif **linéaire et neutre au risque**.
- **Scénarios (12 cœur + 1 stress)** : S0 base ; S1 rotation du leadership à T/4, T/2, 3T/4 ; S2 spécialiste rare dormant ~840 tours ; S3 nouvel expert à T/3 ; S4 expert retiré à T/2 ; S5a 3 clones du mauvais ; S5b 3 clones du meilleur ; S6a lacunes MCAR 30 % (MCAR = manquant complètement au hasard) ; S6b lacune en rafale de 350 tours sur TREND ; S6d abstention informative (les généralistes s'abstiennent quand ils perdraient) ; S7 sous-performance temporaire (LATE 150 tours, RARE malchanceux 15 premières obs) ; S8 composite ; S6c lacunes MNAR (les mauvais résultats disparaissent ; stress uniquement, non jugé).
- **Splits** : tuning graines 0-5 ; held-out graines 1000-1039 (40) ; stress 2000-2019 × {snr 0,5 ; bruit ×1,6} ; sensibilité graines 3000-3007 ; label-noise graines 1000-1019. Aucun chevauchement ✔ (lu dans `heldout.py`, `tune.py`, `sensitivity.py`).
- **Réglage** : grille par méthode, objectif = PR moyen sur les 12 scénarios. Round 1 → beaucoup d'optima au bord de la grille → **une seule extension pré-déclarée** (`tune2.py`) → figé (`tuned_params.json`). Résultat : plusieurs optima restent au bord (§7).
- **Graines/déterminisme** : `rng = default_rng(1_000_003*seed + crc32(name) % 9973)` pour le scénario ; `default_rng(777+rseed)` pour l'apprenant. Déterministe ✔ (code lu ; je n'ai pas relancé la totalité, voir §9).
- **Pré-enregistrement** : `PREREGISTRATION.md`, committé en `e1b345a` avant le tuning et le held-out. Le fichier n'a pas changé ensuite ✔ (git diff vide sur ce fichier). En revanche `learners.py` a reçu 4 lignes après ce commit (règle « evidence-time » : oubli/partage n'avancent que s'il y a au moins une observation), commit `f19cd75` (tuning, avant le held-out). Ce changement n'est pas dans les écarts déclarés du rapport 08.

**Portes (gates) et seuils exacts pré-enregistrés (R1)** :
- **G1 précision** : PR(m) ≤ 0,90 × PR(meilleure baseline) ET IC bootstrap 95 % (2000 rééchantillonnages, sur les graines) de PR(meilleure baseline) − PR(m) exclut 0. Baselines : Equal, Static, WTA, EWMA.
- **G2a** : regret en S6a, S6b, S6d chacun ≤ 1,5 × son regret en S0. **G2b** : pour les méthodes du sous-ensemble NAIVE (EWMA, HedgePlain, SleepHedge, FixedShare, BMA, DiscFreeze), la sémantique naïve doit être pire que la correcte avec IC excluant 0.
- **G3 famine** : (a) nouvel expert (S3) : médiane des tours alloués avant que la moyenne des 25 derniers poids ≥ 0,25 soit ≤ 150 et ≥ 80 % des graines l'atteignent en 400 ; (b) spécialiste rare après dormance (S2, 2ᵉ épisode, 25 premiers tours alloués) : poids moyen ≥ 0,35 ; (c) sous-performance temporaire (S7) : médiane de tours pour récupérer 50 % du poids d'avant ≤ 100.
- **G4 robustesse** : (a) dans aucun scénario cœur le regret > 1,5 × celui de la meilleure méthode non-bandit de ce scénario ; (b) PR sous chaque jeu de stress ≤ PR de la meilleure baseline de ce jeu.
- **Familles** : A = lignée « endormie » (SleepHedge, SleepEG, FixedShare, DiscFreeze, DiscAmnesty, SH_bounded, CtxOracle/Lag/Noisy, DivSH) ; B = lignée « scores/EWMA » (EWMA, EWMA_bounded, WTA, BMA, DivEWMA, Static, Equal) ; C = bandits + HedgePlain.
- **Règles de verdict (dans l'ordre)** : 1 `NO_ROBUST_ENSEMBLE_METHOD` si aucune méthode (baselines incluses) ne satisfait G2-G4 ; 2 `STATIC_OR_EWMA_SUFFICIENT` si Static ou EWMA satisfait G2-G4 et PR ≤ 1,10 × min ; 3 `MULTIPLE_ENSEMBLE_METHODS_SUPPORTED` si ≥ 2 familles passent G1-G4 (ou ≥ 2 de la famille A proches) ; 4 `SLEEPING_EXPERT_REFERENCE_SUPPORTED` si l'ensemble passant est exactement la famille A avec un seul meilleur ; 5 `STUDY_INCONCLUSIVE` si le verdict des règles 1-4 change quand la méthode de tête est remplacée par son voisin de grille ou quand on remplace le held-out par le stress. Les bandits ne peuvent pas être le verdict. `CtxOracle` (utilise la vraie étiquette de régime) est déclaré « optimiste, non éligible comme seule base d'un verdict » ; `CtxLag`/`CtxNoisy` sont éligibles.

### 2.2 R2 — Simulateur « prévisions de probabilité »
Source : `03_PROTOCOL.md` (R2), `env.py`, `learners.py`, `runner.py`, `adjudicate.py`.

- **Tâche** : à chaque tour t, K=10 experts émettent (ou non) une prévision de probabilité `p_i,t` d'un événement binaire `y_t`. Le combineur choisit des poids sur les experts éveillés et prédit `ŷ_t = Σ w_i p_i`. Métrique : erreur au vrai `q_t` : `(ŷ − q)²` (Brier moins le bruit irréductible ; le « Brier » est l'erreur quadratique d'une prévision de probabilité).
- **Générateur** : logit latent `a_t` AR(1) (autorégressif d'ordre 1, coefficient 0,9) ; `logit p_i = a_t + sd_i(régime)·bruit` ; corrélation intra-cluster ρ (clones 0,9 ou 0,95). Régimes A/B/C (durée moyenne ≈80) + régime R rare (rafales ≈25 tours). `sd=∞` = expert structurellement invalide. Contexte observable = étiquette de régime corrompue à 10 %.
- **Statuts** : ACTIVE, INACTIVE, ABSTAIN, DATA_GAP, NO_EVIDENCE (l'expert prévoit donc pèse, mais son score n'est pas observé). Le seul « négatif » légitime est une perte élevée observée sur un tour ACTIVE.
- **T=5000**, **11 scénarios** : S0 base propre ; S1 lacunes (12 % gap, 30 % sans feedback, 8 % abstention) ; S2 changements de leadership ; S3 récurrence de régimes ; S4a nouvel expert excellent à T/2 ; S4b nouvel expert mauvais ; S5 expert retiré puis revenu dégradé ; S6 4 clones ρ=0,95 bons puis mauvais ; S7 sous-performance temporaire (fenêtre 2000-3000) ; S8 spécialiste de régime rare ; S9 longue lacune (1250 tours) d'une étoile.
- **Splits** : tuning graines 100-109 (10) ; held-out 1000-1029 (30). Attention : la « graine » d'un scénario est en fait `seed0 + sum(ord(nom))` et les 10 ou 30 « graines » sont des trajectoires vectorisées tirées d'un même flux aléatoire. J'ai vérifié qu'aucun germe de tuning n'égale un germe de held-out ✔ (DÉRIVÉ : ensembles {950…1480} et {1850…2380} disjoints).
- **Réglage** : un jeu d'hyperparamètres **par méthode, tous scénarios confondus**, critère = moyenne du `nrm` sur scénarios (tuning seul). Deux tours de grille (le 1er a montré des optima au bord).
- **Métrique `nrm`** = `(mse_m − mse_ORACLE) / (mse_EQUAL − mse_ORACLE)` : 0 = oracle (poids à variance inverse connue, non candidat), 1 = poids égaux, >1 = pire qu'égal, <0 = bat l'oracle (possible car l'oracle ignore les corrélations).
- **Portes (seuils exacts, R2)** : marges δ = 0,05 (écart de moyenne nrm) et δ_R = 0,15 (écart pire-cas au meilleur par scénario). Une méthode est ROBUSTE si toutes passent :
  - `gap_ok` : max_s [nrm_m,s − min_m' nrm_m',s] ≤ 0,15 (m' parmi baselines + candidats non bandit).
  - `G_noworse` : jamais significativement pire qu'EQUAL (nrm > 1 et IC 95 % apparié > 0) dans un scénario.
  - `G_new` : part de poids du nouvel expert (S4a, tours T/2+200..300) ≥ 50 % de la part de l'oracle ET nrm(S4b) ≤ 1.
  - `G_rare` : sur les occurrences ≥ 3 du régime rare (S8), nrm ≤ 0,5 ET part du spécialiste ≥ 50 % de la part de l'oracle.
  - `G_under` : après la fenêtre de sous-performance (S7), nrm(blocs 60-66) − nrm(avant, blocs 30-40) ≤ 0,15.
  - `G_dorm` : après la lacune (S9) même critère ≤ 0,15 ET nrm de ré-entrée de régime (S3, 50 premiers tours) ≤ 0,6.
- **Arbre de décision** : 1 Spearman (corrélation de rangs) entre nrm tuning et held-out < 0,6 ⇒ `STUDY_INCONCLUSIVE` ; 2 aucune méthode robuste ⇒ `NO_ROBUST_ENSEMBLE_METHOD` ; 3 aucun candidat robuste, ou meilleure baseline robuste à ≤ δ du meilleur candidat ⇒ `STATIC_OR_EWMA_SUFFICIENT` ; 4/5 sinon `SLEEPING_EXPERT_REFERENCE_SUPPORTED` ou `MULTIPLE_ENSEMBLE_METHODS_SUPPORTED` selon les « familles nécessaires ». Toute déviation ultérieure serait étiquetée post-hoc.
- **Pré-enregistrement** : le protocole 03 est committé en `cfa5565`, en même temps que les sorties du tuning round 1 ; donc il n'a pas précédé *tout* le tuning, seulement le held-out. Les règles d'adjudication codées existent depuis `d21ccc7` (commit « WIP »). Le held-out d'un premier run bugué a été vu avant correction (§6).

---

## 3. Résultats détaillés

### 3.1 R1 — Tableau d'adjudication (held-out, 40 graines, PR = regret ×10⁻³, plus bas = mieux)
Source : `bench/ensemble_v1/results/tables.md`, `gates.json` ; recalculé depuis `heldout_runs.jsonl.gz` ✔ (PR de 14 méthodes retrouvés à 0,01 près).

| méthode | fam. | PR ×10³ | vs meilleure baseline (WTA) | IC(bb−m) ×10³ | G1 | G2a | G2b | G3a | G3b | G3c | G4a | G4b |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CtxOracle | A | 8,36 | 0,71× | [3,15 ; 3,53] | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ |
| CtxLag | A | 10,52 | 0,90× | [1,01 ; 1,35] | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✘ | ✔ |
| DiscFreeze | A | 10,59 | 0,91× | [0,92 ; 1,31] | ✘ | ✘ | ✔ | ✔ | ✔ | ✔ | ✘ | ✔ |
| BMA | B | 10,97 | 0,94× | [0,68 ; 0,77] | ✘ | ✘ | ✔ | ✔ | ✔ | ✔ | ✘ | ✔ |
| DiscAmnesty | A | 11,35 | 0,97× | [0,14 ; 0,55] | ✘ | ✘ | ✔ | ✔ | ✔ | ✘ | ✘ | ✔ |
| WTA | B | 11,69 | 1,00× | [0 ; 0] | ✘ | ✘ | ✔ | ✔ | ✔ | ✔ | ✘ | ✔ |
| DivEWMA | B | 11,74 | 1,00× | [−0,06 ; −0,03] | ✘ | ✘ | ✔ | ✔ | ✔ | ✔ | ✘ | ✘ |
| EWMA | B | 11,83 | 1,01× | [−0,15 ; −0,12] | ✘ | ✘ | ✔ | ✔ | ✔ | ✔ | ✘ | ✘ |
| SleepEG | A | 12,64 | 1,08× | [−1,29 ; −0,61] | ✘ | ✔ | ✔ | ✔ | ✔ | ✔ | ✘ | ✘ |
| DivSH | A | 13,16 | 1,13× | [−1,68 ; −1,23] | ✘ | ✔ | ✔ | ✔ | ✔ | ✔ | ✘ | ✔ |
| SleepHedge | A | 13,16 | 1,13× | [−1,68 ; −1,24] | ✘ | ✔ | ✔ | ✔ | ✔ | ✔ | ✘ | ✔ |
| FixedShare | A | 13,33 | 1,14× | [−1,78 ; −1,49] | ✘ | ✔ | ✔ | ✔ | ✔ | ✔ | ✘ | ✘ |
| CtxNoisy | A | 14,40 | 1,23× | [−2,87 ; −2,53] | ✘ | ✔ | ✔ | ✔ | ✔ | ✔ | ✘ | ✘ |
| HedgePlain | C | 17,58 | 1,50× | [−6,26 ; −5,49] | ✘ | ✘ | ✔ | ✔ | ✔ | ✔ | ✘ | ✘ |
| DUCB | C | 17,94 | 1,53× | [−6,55 ; −5,96] | ✘ | ✔ | ✔ | ✔ | ✔ | ✔ | ✘ | ✘ |
| EWMA_bounded | B | 23,21 | 1,98× | [−11,67 ; −11,36] | ✘ | ✔ | ✔ | ✔ | ✔ | ✔ | ✘ | ✘ |
| Static | B | 24,92 | 2,13× | [−13,89 ; −12,54] | ✘ | ✔ | ✔ | ✔ | ✔ | ✔ | ✘ | ✘ |
| SH_bounded | A | 25,29 | 2,16× | [−13,78 ; −13,39] | ✘ | ✔ | ✔ | ✔ | ✔ | ✔ | ✘ | ✘ |
| SleepEXP3 | C | 59,35 | 5,07× | [−48,24 ; −47,06] | ✘ | ✔ | ✔ | ✔ | ✘ | ✔ | ✘ | ✘ |
| Equal | B | 63,34 | 5,42× | [−51,97 ; −51,30] | ✘ | ✔ | ✔ | ✘ | ✘ | ✔ | ✘ | ✘ |

(`tables.md` donne aussi la récompense réalisée moyenne, entre 0,5242 pour Equal et 0,5790 pour CtxOracle.)

Lecture en langage simple :
- Un regret de 11,7 signifie qu'en moyenne WTA perd 0,0117 de « récompense attendue » par tour par rapport au choix parfait. Equal (poids égaux) perd 0,0633, soit 5,4× plus.
- « IC(bb−m) » est l'intervalle de la différence « meilleure baseline moins la méthode » : positif = la méthode est meilleure. Seuls CtxOracle, CtxLag, DiscFreeze, BMA et DiscAmnesty ont un intervalle strictement positif, mais G1 exige *aussi* un gain de 10 %.
- **Précision sur le caractère limite** (DÉRIVÉ, vérifié) : CtxLag = 10,5255/11,6949 = **0,89987×**, donc G1 « passe » avec une marge relative de 0,00013 ; DiscFreeze = 0,9055× échoue de 0,0055. Voir §7.
- **Écart-type entre graines du PR** (DÉRIVÉ) : WTA 0,66 ; EWMA 0,65 ; DiscFreeze 0,66 ; BMA 0,62 ; SleepHedge 0,80 ; FixedShare 0,51 ; SleepEG 1,05 ; CtxLag 0,40 ; CtxOracle 0,29 ; Static 2,25 (×10⁻³, sur 40 graines, erreur-type ≈ 0,1). Les rapports ne donnent pas ces écarts-types, seulement les IC.
- Différence par graine (DÉRIVÉ) : DiscFreeze bat WTA sur 97,5 % des graines (gain moyen 1,11×10⁻³) ; CtxLag sur 100 % (1,17) ; EWMA bat WTA sur 0 % des graines (−0,14). Les différences sont donc petites mais très régulières : c'est la définition du seuil de 10 % qui tranche, pas le bruit.

### 3.2 R1 — Rapport 04 : sémantique des absences
Sortie de `tables.md` (recalcul ✔ pour EWMA 34,94 / SleepHedge 40,47 / FixedShare 26,61 / BMA 34,85 / DiscFreeze 34,73 / HedgePlain 42,55) :

| méthode | correct | naive_zero | diff | IC bootstrap |
|---|---|---|---|---|
| EWMA | 11,83 | 34,94 | +23,11 | [22,69 ; 23,52] |
| HedgePlain | 17,58 | 42,55 | +24,96 | [24,08 ; 25,90] |
| SleepHedge | 13,16 | 40,47 | +27,31 | [26,52 ; 28,10] |
| FixedShare | 13,33 | 26,61 | +13,28 | [12,98 ; 13,59] |
| BMA | 10,97 | 34,85 | +23,88 | [23,44 ; 24,31] |
| DiscFreeze | 10,59 | 34,73 | +24,14 | [23,69 ; 24,58] |

`naive_zero` = on donne au combineur la pire récompense (0) pour tout expert existant qui n'a pas été observé (inactif, abstention, lacune). Ratio recalculé (DÉRIVÉ) : EWMA 2,95× ; SleepHedge 3,08× ; FixedShare 2,00× ; BMA 3,18× ; DiscFreeze 3,28× ; HedgePlain 2,42×. Le rapport écrit « 2,0–3,3× » ✔. Sous cette erreur, le poids d'un spécialiste s'effondre à 0,000 et ne revient jamais (EWMA, BMA, SleepHedge, DiscFreeze, HedgePlain) ; FixedShare garde ≈0,6 car il réinjecte de la masse (`starvation_extra.md` ✔).

Sleeping vs scores absolus (rapport 04 ; regret ×10³, recalculé ✔ pour WTA/EWMA/SleepHedge/DiscFreeze/BMA) :

| scénario | mécanisme | WTA | EWMA | SleepHedge | DiscFreeze | BMA |
|---|---|---|---|---|---|---|
| S6a | 30 % de lacunes MCAR | 13,6 | 13,7 | 11,0 | 11,8 | 12,4 |
| S6b | rafale de 350 tours | 12,3 | 12,4 | 11,1 | 17,7 | 11,5 |
| S6d | abstention informative | 16,2 | 16,2 | 10,6 | 9,3 | 15,3 |
| S6c (stress) | MNAR | 13,0 | 13,2 | 11,4 | 10,5 | 12,4 |

Explication simple : en S6d, un généraliste s'abstient quand il aurait perdu, donc ses résultats *observés* sont flatteurs. Un rang basé sur la moyenne absolue (WTA/EWMA/BMA) est alors trompé (+53 % de regret vs S0). La règle « spécialiste » compare chaque expert seulement avec ceux qui étaient présents en même temps, donc résiste. Mécanisme : INFERENCE ; effet : PROVEN dans le générateur. DiscFreeze en S6b (17,7 vs 9,3 en S0 = 1,9×) : l'oubli exponentiel rapproche les experts observés de la moyenne alors que l'expert non observé garde une preuve périmée ; non isolé par ablation (INFERENCE).

### 3.3 R1 — Rapport 05 : famine
Reproduction du tableau (`starvation_extra.md`, recalculé ✔ pour S7 EWMA/WTA/BMA/SleepHedge/DiscFreeze/DivSH/CtxLag/FixedShare). « w25 » = poids moyen du spécialiste sur ses 25 premiers tours alloués d'un épisode (part équitable ≈ 0,2 parmi 4-5 experts valides).

| méthode | S2 rare w25 ép.1 | ép.2 (après ~840 dormants) | S3 nouvel expert : médiane tours | atteint <400 | S7 rare w25 ép.1 (départ malchanceux) | ép.2 | ép.3 | S7 LATE récup. médiane |
|---|---|---|---|---|---|---|---|---|
| BMA | 0,880 | 1,000 | 25 | 1,00 | 0,026 | 0,999 | 1,000 | 56 |
| CtxLag | 0,853 | 0,960 | 42 | 0,97 | 0,112 | 0,963 | 0,966 | 38 |
| CtxNoisy | 0,790 | 0,911 | 25 | 1,00 | 0,121 | 0,919 | 0,942 | 39 |
| CtxOracle | 0,862 | 0,979 | 58 | 0,97 | 0,111 | 0,984 | 0,983 | 34 |
| DUCB | 1,000 | 1,000 | 25 | 1,00 | 0,177 | 0,783 | 0,905 | 77 |
| DiscAmnesty | 0,992 | 0,994 | 25 | 1,00 | 0,211 | 0,996 | 0,997 | 110 |
| DiscFreeze | 1,000 | 1,000 | 25 | 1,00 | 0,712 | 1,000 | 1,000 | 57 |
| DivEWMA | 0,690 | 0,999 | 36 | 1,00 | 0,017 | 0,999 | 1,000 | 55 |
| DivSH | 0,996 | 1,000 | 25 | 1,00 | 0,465 | 1,000 | 1,000 | 22 |
| EWMA | 0,672 | 0,999 | 38 | 1,00 | 0,014 | 0,999 | 1,000 | 56 |
| EWMA_bounded | 0,523 | 0,699 | 32 | 1,00 | 0,052 | 0,700 | 0,700 | 43 |
| Equal | 0,173 | 0,172 | 400 | 0,00 | 0,173 | 0,174 | 0,174 | 10 |
| FixedShare | 0,961 | 0,977 | 25 | 1,00 | 0,181 | 0,986 | 0,988 | 21 |
| HedgePlain | 1,000 | 1,000 | 28 | 1,00 | 1,000 | 1,000 | 1,000 | 10 |
| SH_bounded | 0,695 | 0,698 | 25 | 1,00 | 0,207 | 0,700 | 0,699 | 12 |
| SleepEG | 0,998 | 1,000 | 25 | 1,00 | 0,214 | 0,950 | 0,950 | 80 |
| SleepEXP3 | 0,090 | 0,068 | 25 | 1,00 | 0,056 | 0,089 | 0,062 | 38 |
| SleepHedge | 0,995 | 1,000 | 25 | 1,00 | 0,463 | 1,000 | 1,000 | 22 |
| Static | 0,862 | 0,866 | 25 | 1,00 | 0,173 | 0,691 | 0,690 | 10 |
| WTA | 0,672 | 1,000 | 38 | 1,00 | 0,014 | 0,999 | 1,000 | 55 |

Lectures :
1. **Nouvel expert (S3)** : pas de famine pour les méthodes qui n'apprennent que sur observation. La médiane 25 est le plancher de mesure (fenêtre glissante de 25). Le rapport dit lui-même que cela vient surtout de la règle d'initialisation « au niveau moyen de la cohorte » et que le nouvel expert est fort (edge 0,06) : il y a peu à affamer (INFERENCE).
2. **Spécialiste rare après dormance (S2)** : contrôlé. Tous les méthodes adaptatives ≥ 0,87. Les variantes bornées plafonnent à 0,70 par construction (plafond 0,7). EXP3 ne le trouve jamais (0,07). Static tient 0,87 car les poids figés favorisaient par hasard le spécialiste (INFERENCE).
3. **Spécialiste rare avec départ malchanceux (S7)** : vraie famine des règles à score. WTA/EWMA/BMA/DivEWMA ne lui donnent que 0,014–0,026 sur tout le premier épisode de 80 tours, et il revient ensuite (0,999). SleepHedge/DiscFreeze/DivSH lui donnent 0,46–0,71. HedgePlain 1,000, mais pour une mauvaise raison (courte exposition = perte cumulée faible).
4. **Sous-performance de LATE (S7 patch)** : récupération rapide pour la plupart (21 à 57 tours) ; DiscAmnesty 110, SleepEG 80, DUCB 77.
5. Les variantes « bornées » ont été réglées vers zéro borne (plancher 0-0,02, B au maximum de la grille) : l'assurance n'est jamais rentabilisée ici (PR 23–25 contre 12–13).

Nuance que le rapport ne souligne pas assez : dans S7 l'« infortune » du spécialiste est codée en **changeant la moyenne vraie** de ses 15 premières observations à 0,5−0,10 (`scenarios.py`, `MU[idx,k] = 0.5 + e`), pas seulement le tirage. Le poids très bas de WTA/EWMA sur cette période est donc en partie une réaction correcte à un expert réellement mauvais à ce moment-là (§7).

### 3.4 R1 — Rapport 06 : non-stationnarité (regret ×10³ par scénario)
Extrait recalculé ✔ pour 6 colonnes × 5 méthodes ; le tableau complet est dans `tables.md` (S0, S1 leadership, S2 dormance, S3 nouvel expert, S4 disparition, S5a/S5b clones, S6a/b/d, S7, S8, S6c).

Points clés (chiffres exacts) : en S1 (rotation du leadership) SleepHedge 21,0 et DivSH 21,0, SleepEG 17,9, Static 36,6, HedgePlain 23,0, contre DiscFreeze 10,2, BMA 10,8, WTA 11,5, EWMA 11,7, FixedShare 13,1. En S8 (composite) SleepHedge 23,5, Static 44,8, HedgePlain 27,9, contre DiscFreeze 10,1. En S4 (disparition) tout le monde s'améliore par rapport à S0 (SleepHedge 7,3 vs EWMA 8,8). Contextes : CtxOracle 7,2 en S0 (recurrence exploitée). Conclusion du rapport : « aucune règle n'est meilleure partout ; l'ordre des familles change selon le mécanisme dominant » — c'est le contenu de fond du verdict.

Explication : SleepHedge est réglé sur un η énorme (400), presque « le gagnant prend tout » ; comme il n'oublie jamais, l'avantage cumulé d'un ancien leader met longtemps à s'effondrer après un changement de leadership.

### 3.5 R1 — Rapport 07 : diversité
| méthode | S0 | S5a clones du mauvais | S5b clones du meilleur |
|---|---|---|---|
| Equal | 61,6 | 79,9 | 49,4 |
| EWMA | 10,6 | 11,5 | 11,2 |
| DivEWMA | 10,5 | 11,4 | 11,0 |
| SleepHedge | 10,7 | 10,7 | 10,3 |
| DivSH | 10,7 | 10,7 | 10,3 |
| WTA | 10,4 | 11,4 | 11,0 |

Les clones ne font mal qu'à Equal (+18 en S5a). Les enveloppes « diversité » n'apportent rien mesurable (DivSH identique à SleepHedge à 2 décimales ; DivEWMA 0,8 % mieux, dans le bruit). Raison (INFERENCE, importante) : l'objectif est l'espérance de récompense d'un agrégateur linéaire, donc se concentrer sur le meilleur expert est optimal et la diversification n'a rien à acheter. La diversité vaut pour la variance/le drawdown, non modélisés → `NOT_TESTED_FOR_RISK`. Le paramètre τ a été réglé au minimum de la grille (0,1) sur un objectif plat.

### 3.6 R1 — Rapport 08 : falsification, label-noise, sensibilité
Hypothèses (résumé exact) : H1 (sleeping bat la meilleure baseline de ≥10 % sans étiquette de régime) **falsifiée** (DiscFreeze 0,91×, BMA 0,94×, SleepHedge 1,13×, FixedShare 1,14×) ✔ ; H2 (traiter manquant/inactif comme négatif coûte cher) **soutenue fortement** ✔ ; H3 (EWMA suffit) **partiellement falsifiée** (+53 % en S6d ✔ 1,530 ; +25 % en S6a vs sleeping ✔ 13,7/11,0 ; famine 0,014 ✔ ; brittle 11,9…51,1 ✔) ; H4 (Static suffit) **falsifiée** (2,1× ✔ ; 3,2–4,0× en leadership/composite : S1 36,6/11,5=3,2 ✔ ; S8 44,8/11,3=4,0 ✔) ; H5 (bornes) falsifiée ici ; H6 (bandit) falsifiée (SleepEXP3 5,07×, DUCB 1,53×) ✔ ; H7 (diversité) non soutenue ; H8 (contexte) soutenue sous condition ; H9 (famine) partiellement.

**Label-noise du mélange contextuel** (`label_noise.csv`, graines 1000-1019, CtxOracle réglé, l'étiquette est remplacée par un régime tiré au hasard avec probabilité p ; précision = 1 − 0,75 p) ✔ recalculé depuis le CSV :

| p | PR ×10³ | ÷ WTA | ÷ EWMA |
|---|---|---|---|
| 0,00 | 8,32 | 0,72 | 0,71 |
| 0,05 | 10,18 | 0,87 | 0,86 |
| 0,10 | 11,88 | 1,02 | 1,01 |
| 0,20 | 14,42 | 1,24 | 1,22 |
| 0,30 | 16,31 | 1,40 | 1,39 |
| 0,50 | 18,95 | 1,63 | 1,61 |

Le rapport dit « bat de ≥10 % pour p ≲ 0,066 (précision ≳95 %) ». ✘ écart léger : l'interpolation linéaire entre p=0,05 (0,8745) et p=0,10 (1,0210) donne un croisement de 0,90 à **p ≈ 0,059** (précision ≈ 95,6 %) (DÉRIVÉ ; vs EWMA : p ≈ 0,062). La conclusion (« ≈95 % de précision ») ne change pas. Point d'équilibre ~ p = 0,10 (précision 92,5 %) ✔.

**Sensibilité aux hyperparamètres** (graines 3000-3007 ; `sensitivity.csv`, ✔ recalculé) : DiscFreeze 12 points 10,8/11,0/12,4 ✔ (10,821 ; 10,968 ; 12,376) ; SleepHedge 6 points 13,4/13,4/14,3 ✔ ; WTA 3 points 11,8/13,2/13,9 ✔ ; CtxLag 19 pts 10,5/12,6/22,2 ✔ ; EWMA 17 pts 11,9/15,0/51,1 ✔ ; BMA 38 pts 11,0/12,9/47,1 ✔ ; FixedShare 17 pts 13,4/16,4/36,5 ✔ ; CtxNoisy 19 pts 14,4/15,4/23,3 ✔. Remarque : le « meilleur » de cette table est le meilleur sur les graines de sensibilité, donc légèrement optimiste (c'est un rapport, pas une sélection).

**Déviations déclarées** : G4a mal définie (la référence « meilleure méthode non-bandit » incluait CtxOracle, déclaré inéligible) ; G4b mal définie (exigeait PR ≤ meilleure baseline exactement, donc toute baseline autre que la meilleure échoue par construction : EWMA échoue de 1 %). Amendement post-hoc : référence G4a sans CtxOracle ; G4b avec tolérance 5 %. Aucun seuil de G1, G2, G3 changé.

### 3.7 R1 — Rapport 09 : application des règles
- **Route littérale** : seul CtxOracle satisfait G1-G4 (`gates.json` : `passing_G234 = ['CtxOracle']` ✔, `passing_G1234 = ['CtxOracle']`). CtxOracle est inéligible comme base de verdict. Règle 1 ne se déclenche pas (car CtxOracle satisfait G2-G4). Règles 2-4 ne se déclenchent pas. L'arbre est « non résolu » ⇒ `STUDY_INCONCLUSIVE`. Attention : dans `analyze.py`, ce label sort du `else` final du code (aucune méthode éligible ne passe G1234) et non de la règle 5 telle qu'écrite en pré-enregistrement (§7).
- **Route post-hoc** (`gates_amended.json`) : seul candidat réaliste passant G1-G4 amendées : **CtxLag** (0,90×, pire scénario 1,243 en S4 ✔ recalculé). Règle 4 donnerait `SLEEPING_EXPERT_REFERENCE_SUPPORTED`, mais règle 5 se déclenche : son jumeau CtxNoisy (20 % d'étiquettes fausses) échoue G1 (1,23×) ; le point d'équilibre est à ≈92,5 % de précision ; la grille de CtxLag est brittle (10,5–22,2) ; les autres méthodes sleeping (SleepHedge, FixedShare, DiscFreeze) échouent G1 (0,91–1,14×). ⇒ `STUDY_INCONCLUSIVE`. La règle 5 est appliquée « à la main » dans le rapport, pas par le code.
- **Jeux de stress** (ratio PR vs meilleure baseline du jeu) : recalculé ✔ CtxLag 0,91/0,99 ; DiscFreeze 0,82/0,82 ; SleepHedge 0,77/0,85 ; SleepEG 0,84/1,85 ; FixedShare 1,08/1,26 ; EWMA 1,01/1,01 ; Static 1,49/1,60 ; SleepEXP3 3,05/3,44 ; Equal 3,08/3,66 (tableau complet dans le rapport 09).

### 3.8 R1 — Rapport 10 : limites (résumé)
11 limites listées : synthétique ; objectif linéaire neutre au risque (« plus grande raison de l'inconclusif ») ; évaluation fantôme supposée ; étiquette de régime donnée gratuitement ; plateau de tuning aux bords ; seuils arbitraires ; générateur commun tuning/held-out ; ablations manquantes ; littérature citée de mémoire (aucun papier re-téléchargé) ; regret espéré vs réalisé ; aucune connaissance d'AurumShift.

### 3.9 R2 — Tableau principal `nrm` par scénario (held-out, 30 graines)
Source : `results/summary_tables.md`, `adjudication.json` (recalcul ✔ : les 15 colonnes de moyennes et les cellules citées sont identiques au rapport 04).

| Scénario | STATIC | EWMA | HEDGE_CUM | SLEEP_HEDGE | EG | BMA | FIXED_SHARE | DISC_AWAKE | MPP | CONTEXT | DIVERS. |
|---|---|---|---|---|---|---|---|---|---|---|---|
| S0 base | 0,93 | 0,74 | 0,65 | 0,92 | 0,68 | 0,98 | 0,71 | 0,65 | 0,73 | 0,58 | 0,77 |
| S1 lacunes | 0,91 | 0,98 | 0,99 | 0,87 | 0,74 | 0,88 | 0,79 | 0,74 | 0,83 | 0,67 | 0,82 |
| S2 leadership | 0,94 | 0,35 | 0,43 | 0,40 | 0,41 | 0,39 | 0,33 | 0,38 | 0,39 | 0,66 | 0,64 |
| S3 récurrence | 0,72 | 0,27 | 0,31 | 0,30 | 0,24 | 0,33 | 0,15 | 0,45 | 0,32 | 0,26 | 0,72 |
| S4a nouveau bon | 0,90 | 0,53 | 0,53 | 0,71 | 0,57 | 0,76 | 0,42 | 0,61 | 0,58 | 0,46 | 0,75 |
| S4b nouveau mauvais | 0,94 | 0,76 | 0,76 | 0,92 | 0,71 | 0,99 | 0,72 | 0,63 | 0,74 | 0,61 | 0,82 |
| S5 retrait/retour | 0,90 | 0,71 | 1,68 | 0,84 | 0,62 | 0,91 | 0,66 | 0,64 | 0,75 | 0,90 | 0,78 |
| S6 corrélés | 1,24 | 0,02 | 0,86 | 0,85 | −0,27 | 0,64 | 0,11 | 0,25 | 0,29 | 1,73 | −0,02 |
| S7 sous-perf. | 0,92 | 0,57 | 0,56 | 0,85 | 0,57 | 0,94 | 0,57 | 0,54 | 0,61 | 0,83 | 0,68 |
| S8 rare | 0,90 | 0,73 | 0,66 | 0,89 | 0,68 | 0,94 | 0,68 | 0,66 | 0,70 | 0,58 | 0,76 |
| S9 longue lacune | 0,85 | 0,38 | 0,47 | 0,43 | 0,40 | 0,44 | 0,28 | 0,58 | 0,39 | 0,30 | 0,75 |
| **moyenne** | 0,92 | 0,55 | 0,72 | 0,73 | **0,49** | 0,74 | **0,49** | 0,56 | 0,58 | 0,69 | 0,68 |

Autres lignes (recalculées ✔) : moyenne WTA 2,416 ; EXP3 3,836 ; EPS_GREEDY 3,357 ; DISC_CLOCK 0,653 ; SLEEP_FLOOR 0,682 ; EQUAL 1,000.

Ordre de grandeur pour la lecture : `nrm=0,49` signifie que EG comble ≈51 % de l'écart entre « poids égaux » et « oracle ». Dans DÉRIVÉ : la différence EG − EWMA moyennée sur les 11 scénarios est −0,060 (IC 95 % approx. [−0,069 ; −0,052], en combinant les erreurs-types par scénario) ; FIXED_SHARE − EWMA −0,054 [−0,060 ; −0,047] ; EG − FIXED_SHARE −0,007 [−0,014 ; 0,000], donc EG et Fixed-share sont indistinguables. Cette dernière ligne est dans la même logique que le rapport (« ≈ marge δ = 0,05 »), mais l'écart EG−EWMA est statistiquement non nul et proche de δ, non « à peine » en dessous du bruit.

Écart d'échelle utile (DÉRIVÉ) : l'écart EQUAL–ORACLE (dénominateur de nrm) vaut en MSE : S0 0,00498 ; S1 0,00516 ; S2 0,00838 ; S3 0,00509 ; S4a 0,00509 ; S4b 0,00488 ; S5 0,00475 ; S6 0,00559 ; S7 0,00600 ; S8 0,00482 ; S9 0,00482. Tous du même ordre, donc le nrm n'est pas dégénéré (pas de division par presque zéro au niveau scénario).

### 3.10 R2 — Rapport 04 : mécanisme endormi
- **SLEEP_HEDGE** : meilleur qu'égal partout (−0,275 en moyenne, « mieux dans les 11 scénarios » ✔ extras.json) mais η optimal = 0,03 (proche d'égal). Significativement pire qu'EWMA dans 10 scénarios sur 11 (meilleur seulement en S1) ✔.
- **EG et Fixed-share** : −0,238 et −0,231 vs SLEEP_HEDGE, mieux dans 10-11 scénarios ✔. Vs EWMA : EG mieux dans 7 scénarios, pire dans 3 (S2, S4a, S9) ✔ ; Fixed-share mieux dans 9, pire en S6 ✔ (0,11 vs 0,02).
- **S1** : EG 0,74 et Fixed-share 0,79 tiennent ; EWMA 0,98 (presque égal) car son état se périme sans détection.
- **BMA** (perte logarithmique, sans oubli) : κ optimal 0,01 = quasi-poids égaux (INFERENCE non isolée).
- **Portes** (`summary_tables.md` ✔ les colonnes G_*) :

| Méthode | écart pire-cas | nouvel expert | rare | sous-perf. | dormance | robuste |
|---|---|---|---|---|---|---|
| EG | 0,149 ✔ | ✘ (0,306) | ✘ | ✔ | ✔ | non |
| FIXED_SHARE | 0,387 ✘ | ✔ (0,643) | ✘ | ✔ | ✘ | non |
| EWMA | 0,304 ✘ | ✘ (0,493) | ✘ | ✔ | ✔ | non |
| MPP | 0,566 ✘ | ✔ (0,576) | ✘ | ✔ | ✔ | non |
| DISC_AWAKE | 0,519 ✘ | ✘ | ✘ | ✔ | ✔ | non |
| CONTEXT_MIX | 1,999 ✘ | ✘ | ✔ | ✘ | ✔ | non (pire qu'égal en S6) |

Recalculé (DÉRIVÉ) : le pire écart d'EG est 0,149 **en S4a** (nouveau bon expert), le même scénario où EG échoue G_new ; EWMA pire écart 0,304 en S1 ; Fixed-share pire écart 0,387 en S6.

### 3.11 R2 — Rapport 05 : famine
- **Nouvel expert (S4a)**, part de poids à T/2+250 et T/2+450 (✔ tous recalculés depuis `extras.json`) : ORACLE 0,56/0,55 ; WTA 0,76/0,84 ; FIXED_SHARE 0,36/0,49 ; MPP 0,32/0,34 ; EWMA 0,28/0,40 ; DISC_AWAKE 0,23/0,23 ; CONTEXT 0,17/0,23 ; EG 0,17/0,20 ; SLEEP_HEDGE 0,15/0,18 ; EQUAL 0,14/0,14. Seuls FIXED_SHARE et MPP passent (WTA aussi mais échoue partout). Le rapport écrit EWMA 0,28 mais la porte l'échoue avec un ratio de 0,4928, à 0,007 du seuil de 0,5.
- **Coût du faux départ (S4b)** : FIXED_SHARE 0,72, EG 0,71, EWMA 0,76 ; WTA 3,26 ✔.
- **Spécialiste rare (S8)** : part du spécialiste / mse (✔) : ORACLE 0,92 / 0,0009 ; WTA 0,94 / 0,0028 ; CONTEXT_MIX 0,63 / 0,0036 ; DISC_AWAKE 0,32 / 0,0075 ; FIXED_SHARE 0,27 / 0,0100 ; MPP 0,24 / 0,0130 ; EG 0,21 / 0,0084 ; SLEEP_HEDGE 0,20 / 0,0097 ; EWMA 0,16 / 0,0135 ; EQUAL 0,14 / 0,0111. EWMA fait pire qu'égal dans ce régime (0,0135 vs 0,0111). ✘ Le rapport dit « Porte échouée par tous sauf CONTEXT_MIX et WTA » ; le fichier montre que **HEDGE_CUM passe aussi G_rare** (rare_nrm 0,077 ; ratio de part 0,954). Il est éliminé ailleurs (G_noworse : pire qu'égal en S5, nrm 1,68).
- **Sous-performance (S7)** : le rapport écrit que « toutes les candidates récupèrent … G_under ✔ sauf BMA et CONTEXT_MIX » ✔ (colonnes). Il déclare non informative la métrique de temps de récupération (médiane 0) et ne la cite pas ✔ (`extras.json` : 0 pour toutes).
- **Dormance (S9 puis S3)** : nrm post-lacune moins pré-lacune : EG 0,33 → 0,21 ; EWMA 0,58 → 0,63 ; DISC_AWAKE 0,53 → 0,59 ; FIXED_SHARE 0,09 → 0,43 (le rapport explique par la dilution uniforme après un long sommeil) ; MPP 0,23 → 0,36 ✔ dans le tableau brut. **Mais voir §7 : ces chiffres pour EWMA et SLEEP_HEDGE proviennent d'une mauvaise configuration.** DISC_CLOCK vs DISC_AWAKE : « oublie les dormants » non démontré (H11), UNKNOWN. Ré-entrée de régime S3 : FIXED_SHARE 0,15 ✔ (0,309 en `reentry_nrm` 50 premiers tours ?) — attention, la valeur 0,15 est le nrm global S3, la porte utilise `reentry_nrm` (FIXED_SHARE 0,309, EG 0,255, CONTEXT 0,304, EWMA 0,565, DIVERSITY 0,798). Le rapport 05 cite « FIXED_SHARE 0,15, EG 0,25, CONTEXT_MIX 0,26, EWMA 0,27 ✔ ; DIVERSITY 0,72 et STATIC 0,72 ✘ » : ce sont les nrm globaux de S3 (0,15 ; 0,24 ; 0,26 ; 0,27 ; 0,72 ; 0,72), pas la métrique de ré-entrée de la porte. ✘ étiquetage confus, la conclusion qualitative (DIVERSITY et STATIC échouent) reste vraie car leurs `reentry_nrm` sont 0,80 et 0,71 > 0,6.
- **Verdict famine** : `STARVATION_CONTROLLED=FALSE`.

### 3.12 R2 — Rapports 06 à 08
- **Non-stationnarité (06)** : S2 leadership : EWMA 0,35, Fixed-share 0,33, DISC_AWAKE 0,38, SLEEP_HEDGE 0,40, EG 0,41, CONTEXT 0,66, DIVERSITY 0,64, STATIC 0,94 ✔. S3 récurrence : Fixed-share 0,15, EG 0,25, CONTEXT 0,26 ; DISC_* 0,45–0,51 (« oublient ») ✔ ; WTA 0,47 ✔ ; STATIC 0,72 ✔. S5 : HEDGE_CUM 1,68 (significativement pire qu'égal) parce que la perte cumulée d'un expert retiré reste figée basse : il revient avec un avantage indu. **Stabilité tuning → held-out** : Spearman 0,9714 ✔ (calculé sur les 15 méthodes hors bandits ; règle ≥ 0,6).
- **Diversité (07, S6)** : part du cluster corrélé / n effectif (✔) : EQUAL 0,57 / 7,0 ; SLEEP_HEDGE 0,58 / 6,0 ; CONTEXT_MIX 0,58 / 3,9 ; FIXED_SHARE 0,46 / 4,7 ; EWMA 0,44 / 4,9 ; **DIVERSITY 0,30 (fichier : 0,296) / 4,8** ; **EG 0,33 (0,326) / 5,2** ; ORACLE 0,51 / 5,7. Le rabais de redondance réduit le cluster et gagne face à Fixed-share en S6, mais coûte +0,186 en moyenne ailleurs et est significativement pire dans 9 des 10 autres scénarios ✔ (extras.json : mieux seulement en S6, pire dans 9). EG seul bat même le rabais dédié (−0,27 en S6) : sa mise à jour centrée pénalise les clones d'un bloc.
- **Falsification (08)** : 12 hypothèses ; H1 statique réfutée ; H2 EWMA « partiellement réfutée » ; H3 Hedge endormi comme référence gagnante réfutée ; H4 « inactif = mauvais » réfutée (EWMA 0,55 → 1,16 ✔ 1,155 ; SLEEP 0,73 → 1,35 ✔ 1,346) ; H5 « preuve manquante = mauvais » réfutée en S1 seulement (+1,55 ✔ ; +1,21 ✔) ; H6 conservation de masse confirmée (SLEEP_NOMASS +2,03 en S5 ✔, +1,11 en S1 ✔, +0,60 en S4b ✔ ; EG_NOMASS +0,25 en S1 ✔ ; mais SLEEP_NOMASS meilleur de 0,05–0,24 dans S0, S2, S4a, S7, S8 ✔ : −0,15 ; −0,05 ; −0,24 ; −0,14 ; −0,12) ; H7 bandit (EXP3 3,84 ✔ ; ε-greedy 3,36 ✔) ; H8 WTA 2,42 ✔, pire qu'égal dans 9 scénarios ✔ ; H9 diversité ; H10 contexte confirmé pour S8 seulement ; H11 décote horloge non démontrée ; H12 OSS `river EWARegressor` réfutée.
- **Sonde river** (`oss_probe.json`, 4 trajectoires de 2500 tours, seed 66) : en S0 le mse de river avec remplissage 0,5 = 0,0309, remplissage par la moyenne des éveillés = 0,0226, contre EQUAL 0,0080, SLEEP_HEDGE réglé 0,0077, ORACLE 0,0037 ; en S1 0,0354 / 0,0195 vs EQUAL 0,0094 ; en S3 0,0292 / 0,0129 vs EQUAL 0,0086. Ratios river/EQUAL : S0 3,84 et 2,81 ; S1 3,76 et 2,07 ; S3 3,40 et 1,50. Le rapport dit « 1,5–4× pire qu'égal » ✔. La lr choisie est 0,3 (bas de grille, [0,3 ; 1 ; 3 ; 10]) : le rapport le reconnaît (limite 8) ; la tendance lr→0 tend vers EQUAL, ce que la grille ne teste pas.

### 3.13 R2 — Rapport 09 : adjudication
1. Stabilité Spearman 0,9714 ≥ 0,6 ✔ (pas d'INCONCLUSIVE).
2. Ensemble robuste vide (`robust_set: []` ✔). Plus proche : EG (écart 0,149 ≤ 0,15 de justesse ; échoue nouvel expert + rare). Fixed-share : meilleure moyenne ex æquo mais écart 0,387 (S6) et dormance dégradée. EWMA : 0,304, échoue nouvel expert et rare.
3. `NO_ROBUST_ENSEMBLE_METHOD`.
4. Familles « nécessaires » : cœur (S6, via EG), tracking (S3, via Fixed-share) ; contexte et diversité : aucune ✔ (`families_needed`).
5. **Sensibilité post-hoc** (ne change pas le verdict) : avec un écart toléré de 0,40, EG et Fixed-share passent cette porte mais EG échoue toujours nouvel expert et rare ; Fixed-share échoue rare et dormance ✔ (G_dorm de Fixed-share ✘). Ordre par moyenne (extras.json) : EG, FIXED_SHARE, EWMA, DISC_AWAKE, MPP, DISC_CLOCK, DIVERSITY, SLEEP_FLOOR, CONTEXT_MIX, HEDGE_CUM, SLEEP_HEDGE, BMA, STATIC, EQUAL, WTA.

### 3.14 R2 — Rapport 10 : limites (résumé)
Synthétique ; perte de prévision et non de décision ; portes exigeantes et en partie arbitraires (fixées avant le held-out mais après un smoke test) ; un jeu d'hyperparamètres pour tous scénarios, certains optima proches du bas de grille (MPP, FIXED_SHARE α, SLEEP_HEDGE η) ; oracle non borné ; implémentations simplifiées (MPP = moyenne uniforme des postérieurs passés, pas le schéma Bousquet-Warmuth complet ; pas de coin-betting ni ML-Poly/BOA) ; bandits minimaux ; sonde river limitée ; un bug corrigé et held-out du run bugué vu ; un seul T=5000, K=10 ; 4 références vérifiées par recherche web, le reste de mémoire.

---

## 4. Candidats / méthodes évalués un par un

Rappel des labels : **ADOPT** = à retenir comme principe ; **ADAPT** = à modifier/tester ; **PARK** = mettre de côté avec condition de reprise ; **REJECT** = écarter. Ce sont des candidats externes, jamais des décisions.

### 4.1 Verdicts publiés par chaque run

| Candidat | Verdict R1 (rapport 09) | Verdict R2 (rapport 09) |
|---|---|---|
| Contrat de sémantique (dormant/manquant ≠ mauvais) | ADOPT (contrat) | ADOPT (principe) |
| Conservation de masse du bloc mis à jour (normalisation « spécialiste ») | (implicite dans SleepHedge ; non ablatée) | ADOPT (principe) |
| Hedge endormi simple | PARK (plain/fixed-share) | non recommandé comme référence ; le mécanisme oui |
| Hedge endormi avec oubli (DiscFreeze) | ADAPT (référence) | DISC_AWAKE : PARK |
| Fixed-share endormi | PARK | ADAPT (α≈0,003–0,01) |
| EG endormi | (SleepEG, non mentionné dans le tableau de candidats) | ADAPT (η≈0,1) |
| EWMA / WTA | garder comme baseline à battre | EWMA : ADAPT (baseline/repli) ; WTA : REJECT |
| Mélange contextuel | PARK en attendant la qualité de l'étiquette (≳95 %) | PARK |
| Pondération sensible à la diversité | PARK | REJECT en l'état |
| Poids bornés (plancher/plafond) | PARK | (SLEEP_FLOOR non retenu) |
| Bandits | REJECT comme cadre principal | REJECT |
| Bibliothèques (`river`, `mabwiser`, `contextualbandits`) | REJECT pour ce besoin | river EWARegressor : REJECT pour ce cas |
| MPP | non exécuté | PARK |
| BMA sans oubli, HEDGE_CUM, EXP3, ε-greedy | — | REJECT |

### 4.2 Justification chiffrée et conditions de changement de verdict

**Sémantique (freeze + prior neutre).** R1 : naive_zero coûte 2,0–3,3× (+13,3 à +27,3 en PR×10³, IC loin de 0). R2 : `INACTIVE_NEG` EWMA 0,55 → 1,16, SLEEP 0,73 → 1,35 ; `MISSING_NEG` +1,55 / +1,21 en S1. *Deux tailles d'effet différentes, même sens.* Changerait si des données réelles montraient que « donnée manquante » est corrélée à la performance (MNAR) : R1 S6c dit qu'aucune règle testée ne peut le réparer (dégradation 6-25 % vs S0).

**EWMA.** R1 : 11,83 (1,01× WTA), brittle (11,9…51,1 sur 17 points de grille) ; échoue G2a (S6d 1,530 > 1,5) et famine S7 (0,014). R2 : 0,548, meilleure baseline, échoue nouvel expert (0,4928) et rare (0,177 ; nrm 1,24). Reprise du rôle « suffisant » si un jeu réel montre pas d'abstention informative et pas de spécialiste rare.

**WTA.** R1 : 11,69, *meilleure baseline*, famine S7 0,014. R2 : 2,416, *pire qu'égal dans 9 scénarios*. Le renversement est causé par la nature de l'objectif (§8).

**Hedge endormi / Fixed-share / EG.** R1 : SleepHedge 13,16 (η=400) ; FixedShare 13,33 (α=0,0005, η=10) ; SleepEG 12,64 (η=60, mais 1,85× sous forte bruit). R2 : SLEEP_HEDGE 0,725 (η=0,03), EG 0,487 (η=0,1), FIXED_SHARE 0,494 (α=0,003, η=0,3). Reprise en « référence supportée » si un critère de précision de 10 % était atteint avec IC (jamais dans R1 sans étiquette de régime) ou si les portes de famine étaient assouplies (R2 §09 post-hoc).

**Oubli (DiscFreeze / DISC_AWAKE).** R1 : 10,59 (0,906× la baseline, IC positif, 39/40 graines) mais 1,9× en rafale de lacune (S6b) et ratio G2a 1,895 ; hyperparamètres robustes (10,8–12,4). R2 : DISC_AWAKE 0,558, oublie en récurrence (S3 0,45), échoue nouvel expert/rare. Reprise si le seuil G1 était à 9 % ou si S6b n'est pas une menace.

**Mélange contextuel.** R1 : CtxLag 10,52 (0,8999×) bat la barre de 10 % de 0,00013, pire scénario amendé 1,243, mais CtxNoisy (85 % de précision) 14,40 (1,23×) ; CtxOracle 8,36. R2 : CONTEXT_MIX 0,689, seul remède du spécialiste rare (part 0,63) mais 1,73 en S6, 0,90 en S5, 0,83 en S7. Reprise si la qualité d'étiquette de régime ≥ ~95 % est démontrée sur des données réelles.

**Diversité.** R1 : rien de mesurable. R2 : réduit le cluster (0,296) mais +0,186 partout ailleurs. Reprise avec un objectif de risque (variance/drawdown) qui n'existe dans aucun run.

**Bornes.** R1 : PR 23–25 vs 12–13 (assurance non rentabilisée, réglées vers zéro borne). R2 : SLEEP_FLOOR 0,682 (plancher 0,2) ; pas de gain de famine. Reprise avec objectif de risque.

**Bandits.** R1 : DUCB 17,94 (1,53×), SleepEXP3 59,35 (5,07×). R2 : EXP3 3,836, ε-greedy 3,357 (3-4× pire qu'égal). Reprise si l'observation devient partielle (seuls les stratégies exécutées visibles).

**Bibliothèques OSS.** `river` 0.26.1 `EWARegressor` : Hedge simple sans masque (OBSERVED par lecture de source, R1 ; OBSERVED + exécuté, R2 : 1,5–3,8× pire qu'égal). `mabwiser`, `contextualbandits` : aucune mention de sleeping/fixed-share/hedge (grep, R1). Reprise si une bibliothèque avec masque de disponibilité apparaît (recherche non exhaustive : UNKNOWN).

---

## 5. Blocs finaux complets et explication ligne par ligne

### 5.1 Bloc final R1 (reproduit tel quel, `00_EXECUTIVE_SUMMARY.md` R1)
```
METHODS_DISCOVERED=13 (families; 4 of them baselines/variants counted inside)
METHODS_EXECUTED=20 (19 tuned + Equal; + 6 re-run under naive_zero semantics)

STATIC_WEIGHTS_RESULT=Static PR 24.9 (2.1x best baseline; 3.2-4.0x in leadership/composite); insufficient
EWMA_RESULT=EWMA PR 11.8 / WTA 11.7 = best baselines; hard to beat by 10%; but +53% on informative abstention, +25% on MCAR gaps vs sleeping update, starves unlucky-start specialist (w25=0.014), brittle grid (11.9-51.1)
SLEEPING_EXPERTS_RESULT=SleepHedge 13.2 / FixedShare 13.3 / SleepEG 12.6 / DiscFreeze 10.6: robust to gaps, selection and unlucky starts; slow on leadership change unless forgetting/share added; no 10%-margin win without a regime label

MISSING_EVIDENCE_HANDLED=YES with freeze + neutral-prior contract (unit-tested); violating it costs 2.0-3.3x regret; MNAR censoring not fixable
STARVATION_CONTROLLED=PARTIAL (new expert and 840-round-dormant specialist: yes; early-bad-luck specialist under absolute-score rules: no; floors control it at ~2x regret)
RECURRING_SPECIALIST_RECOVERY=YES under freeze semantics (>=0.87 weight in first 25 rounds after 840 dormant rounds for all gated rules; 0.000 under naive semantics)

COMPLEXITY_JUSTIFIED=NOT_DEMONSTRATED (no non-oracle-context method clears a 10% margin over EWMA/WTA; context needs >=~95% label accuracy; diversity/bounding/bandits unjustified under this risk-neutral synthetic objective)

FINAL_VERDICT=STUDY_INCONCLUSIVE
```
Explication ligne par ligne :
- `METHODS_DISCOVERED=13` : 13 familles de la littérature (weighted majority/Hedge, EG, specialists, sleeping experts, fixed-share, regret adaptatif, sans paramètre, expert-set croissant, BMA/DMA, mélange contextuel, bandits endormis, diversité, follow-the-leader). Les 4 baselines comptent dedans.
- `METHODS_EXECUTED=20` : lignes du registre (Equal, Static, WTA, EWMA, HedgePlain, SleepHedge, SleepEG, FixedShare, DiscFreeze, DiscAmnesty, SH_bounded, EWMA_bounded, BMA, CtxOracle, CtxLag, CtxNoisy, DivEWMA, DivSH, SleepEXP3, DUCB) ✔ compté dans `registry.py` ; 6 rejouées en `naive_zero` (`NAIVE_SUBSET`) ✔.
- `STATIC_WEIGHTS_RESULT` : Static 24,9, soit 2,13× la meilleure baseline, et 3,2–4,0× en leadership/composite ; insuffisant.
- `EWMA_RESULT` : EWMA/WTA sont les meilleures baselines, difficiles à battre de 10 % ; mais +53 % en abstention informative, +25 % en lacunes MCAR contre la mise à jour sleeping, départ malchanceux (0,014), grille brittle.
- `SLEEPING_EXPERTS_RESULT` : les quatre méthodes citées sont robustes aux lacunes, à la sélection différentielle et aux départs malchanceux ; lentes au changement de leadership sauf oubli/partage ; aucune ne bat de 10 % sans étiquette de régime.
- `MISSING_EVIDENCE_HANDLED=YES` : contrat testé unitairement ; le violer coûte 2,0–3,3× ; le MNAR n'est pas réparable.
- `STARVATION_CONTROLLED=PARTIAL` : contrôlée pour nouvel expert et spécialiste dormant ; non contrôlée pour un spécialiste à mauvais départ sous règles à score ; les planchers contrôlent mais coûtent ≈2× le regret.
- `RECURRING_SPECIALIST_RECOVERY=YES` : ≥0,87 de poids dans les 25 premiers tours après 840 tours dormants (pour les règles passant la porte) ; 0,000 en sémantique naïve.
- `COMPLEXITY_JUSTIFIED=NOT_DEMONSTRATED` : aucune méthode sans oracle de contexte ne dépasse la marge de 10 % ; le contexte exige ≥~95 % de précision d'étiquette ; diversité/bornes/bandits non justifiés sous cet objectif neutre au risque.
- `FINAL_VERDICT=STUDY_INCONCLUSIVE`.

### 5.2 Bloc final R2 (reproduit tel quel, `00_EXECUTIVE_SUMMARY.md` R2)
```
METHODS_DISCOVERED=22 (voir 02)
METHODS_EXECUTED=17 méthodes + 6 ablations + 1 sonde OSS (river) + référence ORACLE

STATIC_WEIGHTS_RESULT=nrm 0,92 (≈ poids égaux) ; pire qu'égal en S6 ; échoue toutes les portes de famine
EWMA_RESULT=nrm 0,55, meilleure baseline ; échoue nouvel expert et spécialiste rare (écart pire-cas 0,30)
SLEEPING_EXPERTS_RESULT=Hedge endormi simple 0,73 (faible) ; EG endormi 0,49 et Fixed-share endormi 0,49 (meilleures moyennes) mais aucun robuste

MISSING_EVIDENCE_HANDLED=TRUE (sémantique « ni mise à jour ni pénalité » PROVEN ; les ablations négatives nuisent significativement)
STARVATION_CONTROLLED=FALSE
RECURRING_SPECIALIST_RECOVERY=PARTIAL (ré-entrée de régime OK pour EG/Fixed-share ; spécialiste de régime rare affamé pour toutes les méthodes sauf le mélange contextuel)

COMPLEXITY_JUSTIFIED=FALSE (contexte, diversité, MPP, décote : non justifiés ; EG/Fixed-share : gain sur EWMA ≈ marge δ, non robuste)

FINAL_VERDICT=NO_ROBUST_ENSEMBLE_METHOD
```
Explication ligne par ligne :
- `METHODS_DISCOVERED=22` : tableau du rapport 02 (22 lignes, dont 4 vérifiées par recherche web : specialists, Putting Bayes to sleep, growing experts, MPP).
- `METHODS_EXECUTED` : 17 du registre ✔ + 6 ablations ✔ + sonde river + ORACLE.
- `STATIC_WEIGHTS_RESULT` : nrm 0,923 ✔ ; pire qu'égal en S6 (1,24, IC>0) ✔ ; échoue les portes de famine.
- `EWMA_RESULT` : nrm 0,548 ✔ ; écart pire-cas 0,304 ✔ ; échoue nouvel expert et rare ✔.
- `SLEEPING_EXPERTS_RESULT` : SLEEP_HEDGE 0,725 ✔ ; EG 0,487 ✔ ; FIXED_SHARE 0,494 ✔.
- `MISSING_EVIDENCE_HANDLED=TRUE` : ablations négatives significativement nuisibles (tableau du §3.12).
- `STARVATION_CONTROLLED=FALSE` : aucune méthode ne réussit les quatre tests à la fois.
- `RECURRING_SPECIALIST_RECOVERY=PARTIAL`.
- `COMPLEXITY_JUSTIFIED=FALSE`.
- `FINAL_VERDICT=NO_ROBUST_ENSEMBLE_METHOD`.

Différence de format : les deux blocs ont les mêmes clés (imposées par le brief), sauf que R1 utilise `YES/PARTIAL/NOT_DEMONSTRATED` et R2 `TRUE/FALSE/PARTIAL`. Dans R1 `STARVATION_CONTROLLED=PARTIAL` alors que dans R2 `=FALSE`, sur des scénarios comparables : c'est un vrai désaccord de fond (§8).

---

## 6. Contrôles de validité

### 6.1 R1
- **Tests unitaires** (`unit_tests.json`, ✔ relu : 20 méthodes, toutes `simplex`, `frozen_on_missing`, `no_lookahead` = true ; DiscAmnesty marqué « non gelé par conception » ; SleepEXP3 déclaré gelé par exception). Trois propriétés : (1) simplexe valide et support dans l'allocation ; (2) une mise à jour sans observation laisse tout l'état identique (test sur un instantané de l'état) ; (3) **absence de lookahead testée empiriquement** : on remplace toutes les récompenses à partir de t0=500 par du bruit aléatoire et on vérifie que les poids ≤ t0 sont identiques ✔ (code lu, `test_semantics.py`).
- **Contrôle négatif** : `naive_zero` (mauvaise sémantique volontaire) sur 6 méthodes → dégradation 2,0–3,3× ✔.
- **Contrôles positifs/de plausibilité** : Equal et bandits très mauvais ; le regret à l'oracle CtxOracle est le plus bas ; cohérence tuning vs held-out (Equal 63,31 vs 63,34 ; WTA 11,51 vs 11,69 ; EWMA 11,66 vs 11,83 ; DiscFreeze 10,49 vs 10,59) ✔ lus dans `tuned_params.json`.
- **Déterminisme** : graines fixes ; non relancé ici.
- **Erreurs corrigées** : aucune correction d'implémentation déclarée. Deux portes mal définies (G4a, G4b) déclarées.
- **Écarts au protocole** : G4a/G4b amendées (post-hoc, étiquetées). Non déclaré : ajout de la règle « evidence-time » dans `learners.py` après le commit de pré-enregistrement (avant le held-out).
- **Analyse du statut d'`CtxOracle` dans la règle 1** : voir §7 et §8, c'est le point qui explique la différence d'étiquette.

### 6.2 R2
- **Tests unitaires** (`unit_tests.json`, ✔ toutes true) : η→0 ≡ EQUAL ; centrage sans effet quand la masse est conservée ; poids relatifs des experts au repos gelés ; masse du bloc conservée ; poids ≥ 0, nuls sur endormis, somme 1 ; ORACLE meilleur qu'EQUAL ; **`no_lookahead_by_construction: true` est une constante écrite en dur** dans `unit_tests.py` (`res["no_lookahead_by_construction"] = True`), pas un test. L'argument (y_t n'est lu qu'après `weights()`) est plausible d'après `simulate()` mais n'est pas vérifié par une expérience (contrairement à R1).
- **Ablations** (contrôles négatifs) : `INACTIVE_NEG`, `MISSING_NEG`, `NOMASS` ✔.
- **Bug corrigé en cours d'étude** : conservation de masse approchée dans la première version ; découvert parce que l'ablation `SLEEP_UNCENTRED` (censée être mathématiquement identique) donnait −0,18 vs SLEEP_HEDGE en S0. Correction exacte `e^c = m0(1−m1)/((1−m0)m1)` + test d'invariance. Run bugué archivé (`results/buggy_mass_fix/`) : même verdict, moyennes proches : EG 0,497 (fichier) vs 0,487 ; FIXED_SHARE 0,515 vs 0,494 (le rapport écrit 0,498 et 0,516 ; ✘ écart de 0,001 sur EG et 0,001 sur Fixed-share, sans conséquence) ✔ `buggy_mass_fix/adjudication.json`. Le held-out du run bugué a été *vu* avant la correction (déclaré).
- **Écarts au protocole déclarés** : tuning en deux tours ; métrique de temps de récupération écartée ; « aucun seuil de porte modifié après le held-out ».
- **Écart de documentation non déclaré** : le protocole 03 cite les ablations `EG_UNCENTRED`/`SLEEP_UNCENTRED` ; le code final utilise `EG_NOMASS`/`SLEEP_NOMASS` (le protocole 03 n'a pas été mis à jour) ✘ mineur.
- **Bug non détecté (trouvé ici)** : voir §7.2 point 1 (défaut d'écrasement des blocs).

---

## 7. Critique indépendante

### 7.1 R1
1. **Verdict fragile par construction.** Le seuil G1 de 10 % est arbitraire (l'auteur le dit). CtxLag « passe » avec un ratio de 0,89987 (PR 10,5255 contre seuil 10,5254 ; DÉRIVÉ, vérifié) ; DiscFreeze échoue avec 0,9055. Dans la route littérale, CtxLag échoue G4a à 1,50009 (seuil 1,5, en S2), soit un écart de 0,00009. Le même état de « juste au-dessus/juste en dessous » se retrouve en G2a d'EWMA en S6d (1,5300 vs 1,5). Un changement de 0,1 % sur un paramètre flipperait ces portes. Le rapport le reconnaît en partie mais ne donne pas ces marges.
2. **Le label `STUDY_INCONCLUSIVE` vient d'un cas non prévu.** La règle 1 dit « si aucune méthode (baselines incluses) ne satisfait G2-G4 ⇒ NO_ROBUST ». `CtxOracle` la satisfait, mais il est déclaré inéligible comme base de verdict, seulement dans la phrase « ne peut être l'unique base d'un verdict ». Si CtxOracle avait été exclu de la règle 1 (lecture raisonnable, puisqu'il triche), aucune méthode réaliste ne passe G2-G4 littérales (`passing_G234` = CtxOracle seul) et la règle 1 aurait donné **`NO_ROBUST_ENSEMBLE_METHOD`**, l'étiquette de R2. Le code (`analyze.py`) route ce cas vers le `else` final `STUDY_INCONCLUSIVE`. La règle 5 (voisin de grille/stress) est appliquée à la main sur la route post-hoc, sans code.
3. **Optima en bord de grille après extension** (`_grid_edge_flags`) : Static κ=400 (max), EWMA β=400 (max), HedgePlain η=300 (max), SleepHedge η=400 (max), FixedShare α=0,0005 (min), DiscFreeze η=100 (max) et γ=0,95 (min), DiscAmnesty η=100 (max), SH_bounded B=10 (max) et floor=0,0 (min), EWMA_bounded floor=0,02 (min), BMA κ=600 (max) et opt=0,1 (max), Ctx* n0=10 (min), DivEWMA/DivSH τ=0,1 (min). Le rapport le dit (« plateau vers le winner-take-all »), mais cela veut dire que les η choisis (400, β=400) sont **des durcissements extrêmes** : avec des récompenses dans [0,1] et des écarts de 0,06, β=400 revient à un argmax. Les réglages ne sont donc pas des optima identifiés mais des butées.
4. **Objectif qui favorise le choix dur.** Le regret est mesuré contre « le meilleur expert unique », avec un agrégateur linéaire et sans coût de turnover. Dans ce cadre le mélange n'a aucun intérêt intrinsèque et le winner-take-all est optimal. Beaucoup de conclusions (bornes inutiles, diversité inutile, WTA meilleur) sont donc des artefacts de l'objectif. C'est l'auteur qui le dit (limite 2) ; il faut le lire comme « ne prouve pas ».
5. **Départ malchanceux de S7 = vraie dégradation.** La moyenne vraie du spécialiste est abaissée à 0,4 pendant ses 15 premières observations : un poids ≈0 pendant ce temps est en partie rationnel. Le rapport présente la « famine » comme un défaut de WTA/EWMA/BMA.
6. **`CtxLag` est trop optimiste.** L'« étiquette retardée » est la *vraie* étiquette du tour précédent ; avec des durées de ~33 tours (probabilité de rester 0,97), elle est correcte ≈97 % du temps sans aucun travail de détection. Le seuil « 95 % » du rapport correspond donc presque exactement à ce que CtxLag reçoit gratuitement. Aucun détecteur de régime réel n'est simulé.
7. **Aucun écart-type/IC pour les comparaisons de scénario ni pour les seuils de famine** : les IC sont donnés seulement pour le PR global. Les valeurs de famine sont des moyennes de 40 graines sans dispersion.
8. **Métrique de famine plafonnée.** Le temps « 25 » est le plancher de la fenêtre ; « atteint <400 » vaut 1,00 pour presque toutes les méthodes, donc la porte G3a ne discrimine presque rien (seuls Equal et SleepEXP3 échouent).
9. **`naive_zero` est une erreur extrême.** Il donne la pire récompense à *tous* les experts existants non observés, y compris ceux structurellement inactifs 95 % du temps (RARE). Le facteur 2–3,3× est donc l'ordre de grandeur d'un cas volontairement mal conçu, pas une estimation d'une erreur réaliste.
10. **Littérature de mémoire** (limite 9) : citations non revérifiées. Les résultats d'exécution, eux, sont vérifiables.
11. **Ce que les chiffres ne prouvent pas** : rien sur des rendements réels (queues lourdes, coûts, capacité) ; rien sur le risque ; rien sur la qualité d'un détecteur de régime.

Écarts rapport vs résultats bruts (R1) : (a) le seuil de précision d'étiquette « p ≲ 0,066 » est en réalité ≈0,059 (§3.6), sans conséquence qualitative ; (b) tous les autres chiffres vérifiés (≥ 40 valeurs) concordent. Aucune contradiction interne grave (le rapport 09 distingue bien route littérale et post-hoc).

### 7.2 R2
1. **Bug d'écrasement des blocs (trouvé pendant cette analyse, non détecté par l'auteur).** Dans `runner.heldout`, la liste de configurations contient deux fois `SLEEP_HEDGE` (tuned, `default_eta1`) et deux fois `EWMA` (tuned, `default`). `run_scenario` range les blocs dans `B[f"{meth}"]` : la dernière configuration écrase la première. Vérification chiffrée (DÉRIVÉ) : la moyenne des blocs `SLEEP_HEDGE` en S7 = 0,018363 = le mse de `default_eta1` (le mse « tuned » vaut 0,009122) ; idem S0 (0,018097 vs 0,008301) et S9 (0,006673 vs 0,004313) ; pour EWMA S9 0,005208 (défaut) vs 0,004032 (tuned). Conséquence : les portes calculées par blocs (`G_under`, la partie S9 de `G_dorm`, et donc les chiffres « avant/après lacune » du rapport 05 pour EWMA et SLEEP_HEDGE) utilisent **η=1 et α=0,03/β=20** au lieu des paramètres réglés (η=0,03 ; α=0,005/β=60). Preuve visible dans `summary_tables.md` : SLEEP_HEDGE `under_pre` = 3,11 et `under_post` = 3,21 alors que son nrm S7 global est 0,85. Impact sur le verdict : aucun, car ni EWMA ni SLEEP_HEDGE ne passent d'autres portes (G_new, G_rare, gap_ok). Mais le tableau de dormance/sous-performance pour ces deux méthodes du rapport 05 (« EWMA 0,58 → 0,63 ») décrit un EWMA non réglé. Les autres méthodes ne sont pas concernées (EG bloc = EG tuned ✔).
2. **Porte `G_rare` presque infranchissable pour des poids lisses.** Elle exige une part ≥ 50 % de celle de l'oracle (0,92) donc ≥ 0,46 pour un spécialiste éveillé ~2 % du temps, avec nrm ≤ 0,5. Seuls WTA (choix dur), HEDGE_CUM (défaut d'exposition) et CONTEXT_MIX (étiquette) la passent. C'est une porte qui sélectionne le comportement « hard-max » que d'autres portes (nrm moyen, pire qu'égal) sanctionnent. L'auteur admet que les portes de famine sont « très exigeantes » (rapport 09).
3. **Le pire écart d'EG (0,149) passe à 0,001 près** (seuil 0,15) et tombe sur S4a, où EG échoue G_new ; EWMA rate G_new de 0,007 (0,4928 vs 0,5). Les verdicts « robuste/non robuste » dépendent de ces marges.
4. **Un jeu d'hyperparamètres pour 11 scénarios** : compromis. Un tuning par scénario n'a pas été testé. Optima proches du bas de grille (MPP `mpp`=0,005, FIXED_SHARE α=0,003, SLEEP_HEDGE η=0,03, BMA κ=0,01 ; grille BMA [0,003…1]) : le « Hedge endormi » optimal est quasi égal, donc une conclusion « le Hedge endormi n'est pas le gagnant » est partiellement un effet de l'échelle de η.
5. **Implémentations simplifiées qui pèsent sur des conclusions :** BMA = SleepHedge à perte logarithmique avec tempérage (pas de postérieur bayésien avec oubli, et différent du BMA de R1) ; MPP = moyenne uniforme des postérieurs passés ; `CONTEXT_MIX` n'a pas la conservation de masse spécialiste (`ContextMix.update` met à jour le poids global et par contexte sans `_keep_mass`), donc son échec en S5/S6/S7 peut relever de l'implémentation, non du concept de mélange contextuel ; `DIVERSITY` utilise un socle Fixed-share avec α=0,05 fixe et non le α réglé de FIXED_SHARE, donc la comparaison « DIVERSITY − FIXED_SHARE » (+0,186) mélange l'effet diversité et l'écart de socle.
6. **Hypothèse de bruit** : erreurs gaussiennes indépendantes sur le logit, régime à 90 % observable, clones parfaits. Aucun test de structure d'erreur réaliste.
7. **Le run bugué a été vu** : le held-out de la première version a été regardé avant de corriger ; le protocole a un rôle de garde, mais un œil informé (l'auteur le note).
8. **Protocole partiellement postérieur au tuning** : `03_PROTOCOL.md` est committé en même temps que les sorties du tuning round 1.
9. **`no_lookahead` non testé** (§6.2).
10. **Un seul (T=5000, K=10)** ; pas de stress de bruit ni de SNR comme dans R1.
11. **Ce que les chiffres ne prouvent pas** : la conclusion « aucune méthode robuste » veut dire « aucune ne passe ces portes ». Le rapport le dit (« pas aucune n'est utile »). Aucun résultat sur données réelles, coûts, P&L.

Écarts rapport vs bruts (R2) : (a) `G_rare` : HEDGE_CUM passe aussi, omis par le rapport 05 ; (b) chiffres EWMA et SLEEP_HEDGE de dormance/sous-performance issus d'une mauvaise configuration (bug §7.2.1) ; (c) protocole 03 cite des ablations `*_UNCENTRED` absentes du run final ; (d) chiffres du run bugué EG 0,498 / FS 0,516 dans le rapport contre 0,497 / 0,515 dans le fichier ; (e) les chiffres de ré-entrée S3 du rapport 05 sont les nrm globaux S3, non la métrique de la porte. Tous les autres chiffres vérifiés (≥ 60 cellules) concordent.

---

## 8. Comparaison point par point des deux runs (section obligatoire)

### 8.1 Pourquoi les deux étiquettes diffèrent : la réponse courte
1. **Les deux runs ne mesurent pas la même chose.** R1 = combinaison de *récompenses* avec regret face au meilleur expert unique (objectif linéaire, neutre au risque, le choix dur est optimal). R2 = combinaison de *prévisions de probabilité* avec erreur quadratique face à une vérité latente et référence « oracle à variance inverse » (mélanger moyenne les erreurs, le choix dur est catastrophique). Les résultats bruts en sont la preuve : **WTA est la meilleure baseline dans R1 (PR 11,69, 1,00×) et la pire méthode non bandit dans R2 (nrm 2,416, pire qu'égal dans 9 scénarios sur 11).**
2. **Les portes sont différentes** : R1 a une porte d'*exactitude* G1 (gain ≥10 % vs meilleure baseline, IC) et des portes de famine avec seuils bas (poids ≥ 0,35 pour le spécialiste rare ; 25 tours) ; R2 n'a pas de porte d'exactitude autonome mais une porte d'écart pire-cas δ_R=0,15 et des portes de famine sur la *part de l'oracle* (≥ 50 %, soit ≥ 0,46 pour le spécialiste rare).
3. **Les règles de verdict traitent différemment le cas « seul un tricheur passe »** : R1 possède une méthode-oracle (CtxOracle, vraie étiquette) qui passe toutes les portes ; comme la règle 1 dit « aucune méthode », elle ne se déclenche pas et l'arbre tombe dans un `else` → `STUDY_INCONCLUSIVE`. R2 n'a pas de méthode oracle candidate (son `ORACLE` est une référence hors candidats, son CONTEXT_MIX reçoit une étiquette bruitée à 10 %), donc la règle 2 « aucun robuste ⇒ NO_ROBUST » se déclenche directement.
4. **Si l'on écarte le tricheur, les deux runs disent la même chose** : dans R1 littéral, *aucune méthode réaliste* ne passe G2-G4 (`passing_G234 = ['CtxOracle']`). C'est exactement la condition de `NO_ROBUST_ENSEMBLE_METHOD`. Les deux étiquettes reflètent donc en grande partie **un choix de rédaction de règle** (éligibilité de l'oracle dans la règle 1) plus que deux conclusions scientifiques opposées. Le vrai désaccord scientifique est ailleurs (famine, WTA, contexte), voir ci-dessous.
5. **Sens des mots** : R1 `STUDY_INCONCLUSIVE` = « le verdict change avec le voisin de grille / les seuils / l'oracle » ; R2 `NO_ROBUST_ENSEMBLE_METHOD` = « aucune méthode ne franchit toutes les portes ». Les deux impliquent « pas de gagnant net à adopter ».

### 8.2 Tableau des différences de conception

| Dimension | R1 | R2 |
|---|---|---|
| Type de tâche | récompense d'un expert ∈[0,1], agrégation linéaire | prévision de probabilité, agrégation linéaire des probabilités, perte quadratique |
| Oracle de référence | meilleur expert alloué réellement valide (choix dur) | poids à variance inverse (mélange), ignore les corrélations |
| Métrique | PR = regret moyen ×10³ (12 scénarios à poids égaux) | nrm = (mse−oracle)/(égal−oracle), 0=oracle, 1=égal |
| K, T | 12, 1200 | 10, 5000 |
| Régimes | 4, dwell ≈33, rare ≈5 % | 3+1 rare, dwell ≈80, rare ≈25 tours |
| Scénarios | 12 cœur + S6c stress + 2 jeux de stress (SNR ×0,5, bruit ×1,6) | 11, pas de jeu de stress |
| Graines tuning / held-out | 0–5 / 1000–1039 (40) | 100–109 / 1000–1029 (30) |
| Méthodes candidates | 20 lignes (dont CtxOracle/Lag/Noisy, DivEWMA, DivSH, EWMA_bounded, DiscAmnesty) | 17 + 6 ablations (dont MPP, DISC_CLOCK, SLEEP_FLOOR, EG_NOMASS) |
| Erreur de sémantique testée | `naive_zero` global (tout non observé = pire) | ablations séparées `INACTIVE_NEG`, `MISSING_NEG`, `NOMASS` |
| Portes | G1 exactitude ≥10 % ; G2 lacunes/abstention ; G3 famine (150/0,35/100) ; G4 robustesse (1,5× meilleur non bandit, stress) | gap_ok (0,15) ; noworse ; new (≥50 % oracle) ; rare (≥50 % oracle + nrm≤0,5) ; under ; dorm |
| Règle de stabilité | règle 5 : voisin de grille / stress | Spearman tuning–held-out ≥ 0,6 (0,9714) |
| Oracle-candidat | CtxOracle inclus (vraie étiquette) | non |
| Bugs corrigés | aucun (portes G4a/G4b mal écrites) | conservation de masse (run bugué archivé) ; bug d'écrasement non détecté |
| Langage | anglais | français |

### 8.3 Chiffres côte à côte pour les mêmes questions

| Question | R1 | R2 | Accord ? |
|---|---|---|---|
| Poids égaux | PR 63,34 (5,42× la meilleure baseline) | nrm 1,000 (par définition) | qualitatif : très mauvais dans R1, référence dans R2 |
| Poids statiques | 24,92 (2,13×) ; 36,6/44,8 en S1/S8 | 0,923 (≈égal) ; 1,24 en S6 | Oui : insuffisant |
| EWMA | 11,83 (1,01× WTA) ; brittle 11,9…51,1 | 0,548 ; meilleure baseline ; écart pire-cas 0,304 | Oui : baseline forte |
| WTA | 11,69, **meilleure baseline** | 2,416, **pire qu'égal** dans 9 scénarios | **Non : opposé** |
| Hedge endormi simple | 13,16 (1,13×), η=400 (quasi hard-max) | 0,725, η=0,03 (quasi égal) | Non comparable : optima opposés (voir plus bas) |
| Fixed-share | 13,33 (1,14×), α=0,0005 | 0,494 (meilleure moyenne avec EG), α=0,003 | R2 le favorise, R1 non |
| EG endormi | SleepEG 12,64 (1,08×), mais 1,85× en fort bruit | 0,487 (meilleure moyenne) | Divergent en classement |
| Oubli exponentiel | DiscFreeze 10,59 (0,91×), mais 1,9× en S6b | DISC_AWAKE 0,558 ; oublie en récurrence | Divergent |
| BMA | 10,97 (0,94×) DMA-style Gaussien | 0,744 (quasi égal, κ=0,01), log-loss sans oubli | Objets différents sous le même nom |
| Mélange contextuel | CtxLag 10,52 (0,90×), CtxNoisy 14,40 (1,23×) | 0,689 ; 1,73 en S6 ; seul remède du rare | Divergent |
| Diversité | aucun effet (identique) | réduit le cluster mais +0,186 ailleurs | Accord : pas de gain net ; mécanisme différent |
| Bornes / plancher | PR 23–25 (2× pire) | SLEEP_FLOOR 0,682 (pas de gain) | Accord : pas rentable |
| Bandits | DUCB 17,94 (1,53×) ; SleepEXP3 59,35 (5,07×) | EXP3 3,836 ; ε-greedy 3,357 | Accord : rejetés |
| Manquant = négatif | 2,0–3,3× | EWMA 0,55→1,16 ; SLEEP 0,73→1,35 (S1 : +1,55/+1,21) | Accord (même sens ; tailles non comparables) |
| Nouvel expert | non affamé (médiane 25 tours) | affamé sauf Fixed-share et MPP (EWMA 0,49 de la part oracle) | **Divergent** |
| Spécialiste rare après dormance | ≥0,87 pour tous (contrôlé) | 0,16–0,32 de part (oracle 0,92), sauf contexte 0,63 et WTA | **Divergent** |
| Départ malchanceux | famine des règles à score (0,014) | non testé | R1 seul |
| Clones | seul Equal en souffre | EG bat même l'oracle en S6 (−0,27) | Partiel |
| OSS | inspection de code `river`, `mabwiser`, `contextualbandits` | `river` exécuté (1,5–3,8× pire qu'égal) | Accord : pas de masque de sommeil |
| Sensibilité aux hyperparamètres | grille EWMA 11,9–51,1 ; BMA 11,0–47,1 | non chiffrée (un jeu pour tout) ; Spearman 0,9714 | R1 plus détaillé |

### 8.4 Où ils s'accordent
- Contrat de sémantique (dormant/manquant ≠ mauvais) : résultat le plus fort des deux études.
- Poids statiques insuffisants ; poids égaux dépassés ; bandits inadaptés ; bornes/diversité sans gain net sous un objectif de précision.
- EWMA est une baseline forte et difficile à battre nettement ; aucune méthode ne domine dans tous les scénarios.
- Aucune bibliothèque OSS inspectée ne gère la disponibilité.
- Verdict pratique : pas de vainqueur robuste ; le contrat de disponibilité est à adopter comme principe.

### 8.5 Où ils divergent et pourquoi (causes probables)
1. **WTA (opposé)** : dans R1 le choix dur est optimal (regret face au meilleur expert unique, agrégateur linéaire) ; dans R2 la moyenne d'erreurs indépendantes réduit le bruit, donc concentrer sur un seul expert est très coûteux. C'est l'écart de conception numéro un.
2. **Échelle des hyperparamètres** : R1 choisit η=400, β=400 (durcissement extrême, bord de grille) alors que R2 choisit η=0,03 pour SLEEP_HEDGE (quasi égal, bas de grille). Un même algorithme « SleepHedge » y est donc en pratique un argmax dans R1 et une moyenne quasi uniforme dans R2. Les classements de méthodes à mise à jour multiplicative ne sont pas comparables.
3. **Famine** : R1 initialise un nouvel expert à la moyenne des scores de la cohorte, avec un nouvel expert fort ; le critère de la porte est un poids ≥0,25 (fenêtre 25) ; R2 exige ≥50 % de la part de l'oracle. R1 mesure aussi un spécialiste ré-entrant dans son propre régime où il est le seul valide ou presque ; R2 mesure sa part quand il n'est éveillé que ~2 % du temps et que l'oracle lui donne 0,92. Les seuils, non les algorithmes, expliquent une grande partie du désaccord (`STARVATION_CONTROLLED=PARTIAL` vs `FALSE`).
4. **Contexte** : R1 CtxLag reçoit la vraie étiquette avec un tour de retard (≈97 % de précision gratuite) ; R2 reçoit une étiquette corrompue à 10 % (≈92,5 % de précision équivalente à 10 % de remplacement uniforme par 4 régimes : 1−0,75×0,10 = 92,5 %), avec une implémentation sans conservation de masse. Le point d'équilibre de R1 (≈92,5 %) est précisément le niveau de bruit de R2 : les deux sont cohérents (CtxLag de R1 à 92,5 % ≈ égale la baseline ; CONTEXT_MIX de R2 est mitigé).
5. **Diversité** : R1 (objectif linéaire, choix dur) : concentrer est optimal, ignorer les clones suffit ; R2 (moyenne d'erreurs corrélées) : les clones sont surpondérés et l'on peut battre l'oracle qui les ignore ; EG y parvient.
6. **Spécialistes rares** : R1 a un régime rare dont RARE est le seul expert valide (donc pratiquement pas de concurrence) ; R2 met le spécialiste en concurrence avec les généralistes éveillés.

### 8.6 Les mesures sont-elles convertibles d'un run à l'autre ?
**Réponse : non, pas au sens quantitatif ; seules quelques comparaisons qualitatives ou de rang tiennent.**
- **Unités** : PR de R1 = différence d'espérance de récompense (unités de récompense) au meilleur expert unique ; nrm de R2 = fraction de l'écart d'erreur quadratique entre poids égaux et oracle à variance inverse. Ce ne sont ni la même perte, ni le même oracle, ni la même normalisation.
- **Conversion formelle possible mais trompeuse** (DÉRIVÉ) : puisque le regret de l'oracle R1 vaut 0 par définition, on peut définir un « pseudo-nrm » R1 = PR/PR(Equal) : WTA 0,185 ; EWMA 0,187 ; DiscFreeze 0,167 ; BMA 0,173 ; SleepHedge 0,208 ; FixedShare 0,210 ; SleepEG 0,200 ; CtxLag 0,166 ; Static 0,393 ; HedgePlain 0,278 ; DUCB 0,283 ; SleepEXP3 0,937. Ces valeurs sont sur une échelle « 0 = choix parfait, 1 = poids égaux » comme le nrm R2, mais l'oracle R1 est un choix dur et l'oracle R2 un mélange ; côté R2 WTA vaut 2,416 tandis que côté R1 il vaut ≈0,185. Cela montre qu'une conversion numérique ne préserve ni les rangs ni les ordres de grandeur. Je la donne uniquement pour démontrer l'impossibilité.
- **Ce qui se compare** : (i) la *direction* d'un effet (ex. semantique naïve dégrade, bandit dégrade, statique dégrade) ; (ii) les *rangs* dans des situations où les objectifs sont d'accord (EWMA vs Static vs Equal) ; (iii) la *présence d'un phénomène* (famine, brittleness).
- **Ce qui ne se compare pas** : les facteurs multiplicatifs (2,0–3,3× vs +0,6 nrm), les valeurs de η/β, les seuils de portes, et tout classement impliquant WTA, Hedge endormi ou contexte.
- **Portes** : non transférables (seuils absolus 0,35/25/150 vs relatifs 50 % de l'oracle).
- **Vérification de cohérence indirecte** (DÉRIVÉ) : si l'on relâche G_rare à 25 % de l'oracle, R2 fait passer la part pour DISC_AWAKE (0,35), FIXED_SHARE (0,29), DISC_CLOCK (0,28), MPP (0,26) mais leur nrm rare est de 0,645–1,18, encore > 0,5, donc le désaccord avec R1 ne se réduit pas en changeant un seul seuil.

### 8.7 Ce que je retiendrais des deux runs pris ensemble
- Robuste aux deux conceptions : contrat de sémantique ; statique et bandit à écarter ; EWMA comme baseline ; pas d'usage de bibliothèques sans masque.
- Dépend de l'objectif (donc à décider par l'objectif réel d'AurumShift, à adjuger plus tard) : choix dur vs mélange (WTA), taille de η, utilité de la diversité, utilité de bornes.
- Aucun des deux ne modélise le risque, les coûts, ni la détection de régime réelle.

---

## 9. Reproductibilité

### 9.1 R1
Commandes (README R1) : `cd bench/ensemble_v1/py; python3 test_semantics.py; python3 tune.py; python3 tune2.py; python3 heldout.py; python3 analyze.py; python3 analyze_amended.py; python3 sensitivity.py; python3 label_noise.py; python3 starvation_extra.py`.
Dépendances : `numpy` uniquement (numpy 2.4.6, Python 3.11 déclarés). Durées : tuning ≈9 min, held-out ≈9 min sur 4 cœurs (`tune_round1.log` 177 s ; `tune_round2.log` 374 s ; `heldout.log` 521 s ✔).
Fichiers fournis : scripts, `tuned_params*.json`, `heldout_runs.jsonl.gz` (22 880 lignes, 2,7 Mo), `tuning_raw*.csv`, `gates*.json`, `tables.md`, `sensitivity.csv`, `label_noise.csv`, `starvation_extra.md`, `unit_tests.json`. Manque : aucune configuration d'environnement figée (pas de `requirements.txt`) ; `analyze_amended.py` exécute une partie de `analyze.py` via `exec` (fragile) ; les 4 lignes de `learners.py` ajoutées après le préenregistrement sont dans l'historique git. Ce que j'ai fait : recalculé PR, gates et statistiques à partir de `heldout_runs.jsonl.gz` ; je n'ai pas relancé les simulations complètes (non lu/non exécuté : `tune.py`, `heldout.py`).

### 9.2 R2
Commandes (README R2) : `pip install numpy pandas scipy tabulate river; cd py; python unit_tests.py; python runner.py tune  # ~7 min; python runner.py heldout  # ~1-2 min; python adjudicate.py; python extras.py; python oss_probe.py`.
Dépendances : numpy, pandas, scipy, tabulate, river 0.26.1. Durées déclarées : tuning ≈7 min (logs : 444 s round 1 et 294 s round 2), held-out 70 s (`heldout.log` ✔ « heldout done 70 s »).
Fichiers fournis : scripts, `tuning_raw.csv.gz` (2,6 Mo), `heldout_raw.csv.gz`, `blocks_*.npz` (~1 Mo chacun), `adjudication.json`, `summary_tables.md`, `extras.json`, `oss_probe.json`, `tuned_params*.json`, `buggy_mass_fix/`. Manque : version de numpy/Python non indiquée ; `no_lookahead` non testé ; le bug d'écrasement (§7.2) fait que `blocks_*.npz` de `SLEEP_HEDGE` et `EWMA` ne sont pas les configurations réglées ; l'ORACLE `Oracle` réutilise l'objet `sdt` ; le générateur utilise `sum(map(ord, scen))` pour les graines (non standard mais déterministe).

---

## 10. Implications pratiques pour AurumShift (pistes « à adjuger plus tard », jamais une compatibilité)

Aucune de ces pistes ne suppose la connaissance du code d'AurumShift.
1. **Piste « contrat d'états »** : demander, lors d'une revue locale, si le système distingue déjà « inactif », « abstention », « donnée manquante », « preuve manquante » et « mauvaise performance réalisée », et si une preuve manquante peut aujourd'hui se traduire en pénalité. C'est l'effet le plus solide (PROVEN, synthétique) dans les deux runs. Compatibilité : UNKNOWN.
2. **Piste « baseline EWMA + tests »** : conserver EWMA comme repli, à mettre à l'épreuve contre une mise à jour « spécialiste » sur des données réelles, avec les deux tests où EWMA est le plus fragile (abstention informative, spécialiste rare à mauvais départ). Compatibilité : UNKNOWN.
3. **Piste « Fixed-share ou EG endormi »** : candidats d'essai (ADAPT) si l'on veut une règle plus robuste que EWMA aux lacunes ; les gains sur EWMA sont de l'ordre de la marge δ (R2) ou négatifs (R1). Le choix dépend de l'objectif réel (choix dur ou mélange) : à décider plus tard.
4. **Piste « objectif d'abord »** : les deux runs montrent que la conclusion dépend du critère (regret contre le meilleur expert vs erreur du mélange). Définir l'objectif réel (P&L net de coûts, risque, capacité) avant tout choix. UNKNOWN.
5. **Piste « détecteur de régime »** : le mélange contextuel n'a de valeur que si l'étiquette est fiable (~95 % dans R1). Cela dépend d'un composant qui, d'après ces deux runs, n'existe qu'en simulation. UNKNOWN.
6. **Piste « données PIT »** : ces études n'ont pas testé les restatements ou la disponibilité point-in-time ; à croiser avec les autres lanes (ex. rapport 004 mentionné par R1).
7. **Ne pas** retenir en l'état les bibliothèques `river`/`mabwiser`/`contextualbandits` pour ce besoin (OBSERVED).

---

## 11. Questions ouvertes et suites recommandées (classées par valeur)

1. **Relancer R2 avec correction du bug d'écrasement des blocs** (clé `meth+cfg`) et recalculer `G_under`/`G_dorm` : faible coût, rend les tableaux 05 corrects. (Le verdict ne devrait pas changer, mais à confirmer.)
2. **Réconcilier les deux bancs sous un même objectif** : exécuter les mêmes algorithmes (mêmes noms, mêmes hyperparamètres bornés) sur les deux générateurs, avec les deux métriques, pour séparer « effet de l'algorithme » et « effet de l'objectif ». Valeur maximale pour interpréter les divergences.
3. **Ajouter un objectif sensible au risque** (variance, drawdown, coûts de turnover) : c'est ce qui manque pour juger diversité et bornes (R1 limite 2).
4. **Détecteur de régime simulé** (avec retard, faux positifs) au lieu d'une étiquette vraie/lagguée/corrompue uniformément ; mesurer le point d'équilibre réel.
5. **Rendre les règles de verdict non ambiguës** : dans R1, dire si un oracle est éligible pour la règle 1 ; dans R2, remplacer des seuils d'absolu de part d'oracle par des seuils atteignables ; publier la sensibilité systématique des verdicts aux seuils (grille de seuils).
6. **Tester `no_lookahead` empiriquement dans R2** (comme dans R1).
7. **Ablations manquantes** : DiscFreeze en burst-gap (R1, S6b) ; MPP schéma complet ; AdaNormalHedge/Squint ; BMA textbook ; tuning par scénario.
8. **Stress supplémentaires pour R2** (bruit, SNR, T, K, corruption de contexte) et un stress de type « queues lourdes » pour R1.
9. **Vérification bibliographique** : re-télécharger les articles cités de mémoire.
10. **Données réelles** (anonymisées, point-in-time) pour vérifier si l'abstention est informative et si les données manquantes sont MNAR.

---

## 12. Index des fichiers lus

### Dépôt / méta
- `claude.md` — doctrine du dépôt (REUSE→ADAPT→…, labels, contraintes) : lu (en-tête et règles).
- PR GitHub #15 et #21 — métadonnées lues via l'API GitHub (titres, corps, états, tailles).

### Branche R1 `origin/claude/strategy-ensemble-experts-v1`
- `reports/014_strategy_ensemble/00_EXECUTIVE_SUMMARY.md` — synthèse, tableau des résultats, bloc final.
- `.../01_PROBLEM.md` — question, tableau des sémantiques, limites de périmètre.
- `.../02_METHODS.md` — 13 familles de la littérature, inspection OSS, table des 20 lignes exécutées.
- `.../03_PROTOCOL.md` — simulateur, scénarios, splits, tests unitaires, reproduction.
- `.../04_SLEEPING_EXPERTS.md` — contrat des états, coût de naive_zero, sleeping vs scores absolus.
- `.../05_STARVATION.md` — tableau de famine et lectures.
- `.../06_NONSTATIONARITY.md` — tableau du regret par scénario.
- `.../07_DIVERSITY.md` — S5a/S5b et enveloppes de diversité.
- `.../08_FALSIFICATION.md` — hypothèses H1-H9, label-noise, sensibilité, déviations.
- `.../09_ADJUDICATION.md` — tableau d'adjudication, stress, application des règles, candidats.
- `.../10_LIMITATIONS.md` — 11 limites.
- `bench/ensemble_v1/PREREGISTRATION.md` — données/split, métrique, portes G1-G4, règles de verdict 1-5.
- `bench/ensemble_v1/README.md` — carte des fichiers et ordre d'exécution.
- `py/scenarios.py` — générateur (12+1 scénarios, états, étiquettes) : lu en entier.
- `py/learners.py` — Equal, EWMA, WTA, Static, HedgePlain, SleepHedge, SleepEG, BMA, CtxMix, Div, SleepEXP3, DUCB : lu en entier.
- `py/registry.py`, `py/runner.py`, `py/heldout.py`, `py/tune.py`, `py/tune2.py` — registre/grilles, boucle et métriques, held-out, tuning : lus.
- `py/analyze.py`, `py/analyze_amended.py` — portes, verdict, tables, amendements post-hoc : lus.
- `py/sensitivity.py`, `py/label_noise.py`, `py/starvation_extra.py`, `py/test_semantics.py` — lus.
- `results/tables.md`, `gates.json`, `gates_amended.json`, `label_noise.csv`, `starvation_extra.md`, `sensitivity.csv`, `unit_tests.json`, `tuned_params.json`, `tune_round1.log`, `tune_round2.log`, `heldout.log`, `heldout_runs.jsonl.gz` (22 880 lignes, recalculé) — lus/recalculés.
- `results/tuning_raw.csv`, `tuning_raw_round2.csv`, `tuned_params_round1.json`, `sensitivity.log` — non lus en détail (tailles vues seulement).

### Branche R2 `origin/claude/strategy-ensemble-experts-v1-b`
- `reports/014_strategy_ensemble/00 à 10` (11 fichiers, français) — lus en entier : synthèse et bloc final, problème, méthodes (22), protocole pré-enregistré, experts endormis, famine, non-stationnarité, diversité, falsification, adjudication, limites.
- `bench/ensemble_v1/README.md` — commandes et carte.
- `py/env.py` (générateur), `py/learners.py` (apprenants), `py/runner.py` (registre/boucle/tuning/held-out), `py/adjudicate.py` (portes et verdict), `py/extras.py`, `py/oss_probe.py`, `py/unit_tests.py` — lus en entier.
- `results/adjudication.json`, `summary_tables.md`, `extras.json`, `oss_probe.json`, `unit_tests.json`, `tuned_params.json`, `tune.log`, `tune_round1.log`, `heldout.log`, `adjudicate.log`, `heldout_raw.csv.gz` (8 580 lignes), `blocks_S7_TEMP_UNDERPERF.npz`, `blocks_S9_LONG_GAP.npz`, `blocks_S0_BASE_CLEAN.npz` (contrôle de l'écrasement) — lus/recalculés.
- `results/buggy_mass_fix/adjudication.json` et `tuned_params.json` — lus (comparaison des moyennes).
- `results/tuning_raw.csv.gz`, `tuning_table.csv` (lu en partie), `tuning_table_round1.csv`, `oss_probe.log`, autres `blocks_*.npz` (S1-S6, S8, S4a/b) — non lus en détail.

### Synthèse des vérifications (≥ 10 demandées)
✔ vérifiés R1 : PR de 14 méthodes ; ratios 0,9 de CtxLag et DiscFreeze ; 6 différences naive_zero et ratios ; 5 méthodes × 6 scénarios (S6, S1, S8) ; poids S7 de 8 méthodes ; 8 lignes de sensibilité ; 6 lignes label-noise ; ratios de stress ; 20 unit tests ; comptage 22 880 runs ; G4a/G2a du détail des gates.
✘ écarts R1 : seuil « p ≲ 0,066 » vs ≈0,059 calculé (sans effet qualitatif).
✔ vérifiés R2 : 15 moyennes nrm et ~50 cellules du tableau 04 ; parts S4a et S8 ; S6 (cluster/eff. n) ; 6 ablations et leurs deltas appariés ; Spearman 0,9714 ; robust_set vide ; 17 méthodes ; run bugué.
✘ écarts R2 : G_rare (HEDGE_CUM passe, omis) ; chiffres dormance/sous-perf. de EWMA et SLEEP_HEDGE issus d'une mauvaise configuration ; ablations `*_UNCENTRED` citées dans le protocole absentes du run final ; valeurs du run bugué à 0,001 près ; métriques de ré-entrée S3 mal libellées.
? non vérifiable : citations bibliographiques des deux runs (de mémoire ou par recherche web non rejouable) ; durées exactes de calcul en dehors des logs.
