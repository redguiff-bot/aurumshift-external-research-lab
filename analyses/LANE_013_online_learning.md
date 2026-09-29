# Analyse approfondie — Lane 013 : Apprentissage en ligne pour marchés non stationnaires (PR #14 ; run 2 sans PR)

Auteur : Claude (analyste de recherche), 2026-09-29. Lecteur visé : Jean-François, qui ne connaît ni GitHub ni le trading quantitatif. Chaque terme technique est expliqué à sa première occurrence.

Conventions de lecture :
- « Le rapport affirme » = écrit dans les rapports du dépôt. « J'ai vérifié » = relu ou recalculé par moi dans les fichiers bruts. Marques : ✔ vérifié, ✘ écart, ? non vérifiable.
- Labels du dépôt (voir §1) : PROVEN, OBSERVED, DOCUMENTED_CLAIM, INFERENCE, UNKNOWN. Mes jugements sont marqués « (mon analyse) ». Les chiffres que j'ai recalculés moi-même à partir des fichiers bruts sont marqués « (recalcul) ».
- Les branches ont été lues avec `git show origin/<branche>:<chemin>`, sans rien checkout ni modifier. Pour vérifier le rejeu, j'ai copié le code dans mon dossier temporaire (hors dépôt) et je l'y ai exécuté.
- Le seul fichier écrit dans le dépôt est celui-ci.

---

## 0. Fiche d'identité

| Élément | Run 1 (complet) | Run 2 (incomplet) |
|---|---|---|
| Branche | `origin/claude/online-learning-v1` | `origin/claude/online-learning-v1-b` |
| PR | n° 14, « 013 online learning / continual adaptation (external, synthetic) », **ouverte, en brouillon (draft), non fusionnée**, `mergeable_state: clean`, créée 2026-09-29 18:12:09 UTC, 5 commits, 33 fichiers modifiés, 3 372 lignes ajoutées (lu via l'API GitHub) | **aucune PR** (confirmé par `SYNTHESE_LANES.md` l. 43 et 183) |
| Base commune | `1a449df` (merge de la PR #6) | `1a449df` (idem) |
| Commits propres | `0f9aa60` (17:50:25 UTC, harnais + protocole), `1bed702` (17:51:29, brouillons de rapports), `3a6f100` (17:53:27, résultats de tuning), `6caada0` (18:08:49, résultats held-out bruts), `363ec81` (18:11:59, rapports + analyse) | `29f65a2` (18:33:23, harnais + scripts), `92eb7af` (18:45:21, résultats de tuning) |
| Auteur des commits | « Claude » | « Claude » |
| Fichiers de la lane | 33 (22 dans `bench/online_learning_v1/`, 11 rapports `reports/013_online_learning/00…10`) | 20 (tous dans `bench/online_learning_v1/`) ; aucun rapport |
| Taille | 2 481 788 octets (dont 60 171 de rapports ; `main.json` 1 804 378 ; `tuning_rows.json` 191 890) | 94 591 octets (dont `tune.json` 45 615) |
| Type de données | 100 % synthétiques (générateur avec vérité connue), aucune donnée de marché | idem |
| Verdict final | `FINAL_VERDICT=LIMITED_ONLINE_METHODS_SUPPORTED` | **aucun** (pas d'évaluation held-out, pas de verdict) |
| Force du verdict (mon analyse) | Modérée sur le **classement** (bien étayé par 15 graines held-out, rejeu reproduit par moi) ; **faible** sur la portée : seuil de 10 % franchi de justesse par deux méthodes différentes, une par piste, monde purement synthétique, plusieurs réglages en bord de grille (voir §7). | Sans objet |

Explication des termes :
- **Branche** : une « ligne de travail » parallèle dans Git (l'outil qui garde l'historique du code). **PR (pull request)** : une demande de fusion d'une branche dans la branche officielle `main`. « Brouillon » = pas encore prête à être fusionnée.
- **Commit** : un instantané enregistré, avec auteur, date, message. **Held-out** : jeu de test tenu à l'écart pendant le réglage, utilisé une seule fois pour juger honnêtement.
- **Synthétique** : les données sont fabriquées par un programme dont on connaît la vérité, ce qui permet de mesurer l'erreur exacte, mais ne dit rien des vrais marchés.

Note de datation : les horodatages des commits sont ceux du dépôt ; le run 1 s'étale sur ~22 minutes, le run 2 sur ~12 minutes entre ses deux commits (plus la durée du tuning, voir §8).

---

## 1. Mission et question posée

### 1.1 Reformulation simple
Sur un marché, les « règles cachées » qui relient ce que tu observes à ce qui va se passer changent avec le temps (on parle de **non-stationnarité** ou de **dérive**, en anglais *drift*). Un modèle appris une fois et jamais mis à jour devient faux. La question de la lane : **parmi les méthodes d'apprentissage « en ligne » légères** (qui se mettent à jour au fil de l'eau, une observation à la fois, avec un état borné et rejouable), **lesquelles méritent leur complexité face à la solution simple** qui consiste à réentraîner régulièrement un modèle sur une fenêtre glissante récente (« refit glissant borné », *rolling refit*) ? Et ces méthodes oublient-elles, s'adaptent-elles vite, se rejouent-elles à l'identique (déterminisme), sans triche sur le futur (fuite, *lookahead*) ?

Termes :
- **Apprentissage en ligne** : le modèle apprend échantillon par échantillon, sans retraiter tout l'historique.
- **Prequentiel** (predict-then-learn) : à chaque pas on prédit d'abord, puis on apprend la réponse quand elle arrive. C'est la seule façon honnête de simuler un usage réel.
- **Regret** : ici, l'écart entre la prédiction du modèle et la **vérité connue** du générateur (pas le bruit). Plus bas = mieux.
- **RLS (Recursive Least Squares)** : régression linéaire mise à jour récursivement, avec un « facteur d'oubli » lambda (λ) qui pondère moins les vieilles données. **Kalman** : variante où les coefficients suivent une marche aléatoire. **SGD** : descente de gradient stochastique (mise à jour par petits pas). **PA (Passive-Aggressive)** : mise à jour par marge. **Arbre de Hoeffding / ARF** : arbres de décision qui poussent au fil du flux ; ARF = forêt adaptative. **ADWIN** : détecteur de changement dans un flux.
- **SNR (signal-to-noise ratio)** : rapport signal/bruit ; SNR faible = signal noyé dans le bruit, comme sur les marchés réels.

### 1.2 Contraintes de la doctrine (`claude.md`)
Priorité : **REUSE → ADAPT → WRAP → COMPOSE → CUSTOM en dernier** (réutiliser un composant existant, l'adapter, l'envelopper, composer plusieurs composants, n'écrire du code maison qu'en dernier recours). Labels de preuve : **PROVEN** (exécuté/inspecté), **OBSERVED** (mesuré), **DOCUMENTED_CLAIM** (affirmé par une doc/un article, non revérifié), **INFERENCE** (déduit), **UNKNOWN**. Verdicts possibles d'une candidate : ADOPT / ADAPT / PARK / REJECT. Contraintes AurumShift rappelées : recherche seule/papier (aucun capital réel), PostgreSQL d'abord, PIT/provenance/no-lookahead critiques, événementiel/intraday (pas de HFT), une source faisant autorité par sujet, coûts de marché réalistes, peu de relais opérateur, reproductibilité scientifique, complexité justifiée. **Frontière** : ne jamais affirmer qu'un candidat est compatible avec AurumShift à partir de ce dépôt ; l'adjudication finale se fait plus tard contre le vrai dépôt local.

### 1.3 Ce que la lane a reconnu elle-même
Le rapport 10 (`reports/013_online_learning/10_LIMITATIONS.md`) déclare : synthétique seulement, gain d'adaptation « haut de fourchette », grilles minuscules, aucune connaissance d'AurumShift.

---

## 2. Méthode

### 2.1 Run 1 (le seul avec protocole complet)

**Données/univers** : deux « pistes » partageant le même chemin de concept latent `w_t` (vecteur unitaire, D = 8 dimensions, T = 4 000 pas, rodage N0 = 500 pas exclus des métriques) (`bench/online_learning_v1/py/scenarios.py`) :
- **Piste C (classification)** : `P(y=1|x) = sigmoïde(3·w_t·x)` (KAPPA = 3). Métrique = *KL en excès* (divergence de Kullback-Leibler entre la vraie probabilité et celle du modèle, en nats par pas ; « nat » = unité d'information avec log naturel).
- **Piste R (régression)** : `y = w_t·x + N(0, 0,5²)` (NOISE_SD = 0,5). Métrique = *MSE en excès* `(prédiction − w_t·x)²`.
- Concepts A et B **orthogonaux** (le modèle périmé est maximalement faux) : borne haute délibérément dure sur le coût d'ignorer la dérive.

**10 scénarios** (`03_DRIFT_SCENARIOS.md`, code vérifié) : `stationary` (témoin), `abrupt` (A→B à t=2000), `gradual` (rotation A→B de t=1500 à 2500), `recurring` (A/B/A/B, changements à 1000/2000/3000), `shock` (B pendant 100 pas puis retour), `false_drift` (traits ×3 et bruit ×3 sur t=2000–2400, concept inchangé), `random_walk` (diffusion σ=0,01/pas/coordonnée), `abrupt_missing` (70 % des étiquettes jamais reçues après t=2000), `abrupt_delayed` (étiquettes en retard de 100 pas sur tout le run), `abrupt_nonlinear` (concept d'interaction `1.5·x0·x1 + 0.5·x2` → `−1.5·x0·x1 + 0.5·x3`).

**Protocole d'arrivée des étiquettes** : à l'instant `now`, l'étiquette de l'échantillon τ n'est livrée que si `τ+1+delay ≤ now`, avec `assert` à chaque livraison (`harness.py`). Le modèle reçoit `now` comme horodatage de mise à jour.

**Candidats** (`models.py`) : River 0.26.1 (LogisticRegression SGD, LinearRegression SGD, PAClassifier/PARegressor, BayesianLinearRegression, HoeffdingTree, HoeffdingAdaptiveTree, ARF, ADWINBagging, drift.ADWIN) + code maison numpy (RLS, Kalman à marche aléatoire, Platt en ligne, `DriftReset`, `Bank`). Baselines : `frozen` (ajusté une fois sur les 500 premières étiquettes), `batch` (refit à fenêtre expansive tous les P ∈ {250, 500, 1000} pas), `rolling` (fenêtre W ∈ {150, 300, 600}, refit tous les 25 pas). 25 entrées (modèle × piste) : 19 candidats + 6 baselines (3 × 2).

**Splits et graines** : tuning sur graines **100–102**, held-out sur graines **1–15** (sensibilité SNR bas : graines 1–8). Une seule configuration par (modèle, piste), choisie sur la **moyenne arithmétique** du regret sur **tous** les scénarios (jamais par scénario) (`run_tuning.py`, 56 configurations × 10 scénarios × 3 graines = 1 680 lignes ✔ `tuning_rows.json`).

**Pré-enregistrement** : `02_PROTOCOL.md` a été commité en `0f9aa60` à 17:50:25, **avant** les résultats de tuning (17:53:27) et le held-out (18:08:49) ; le fichier n'a jamais été modifié depuis (`git log` : un seul commit). Les scripts `models.py`, `scenarios.py`, `harness.py`, `analyze.py`, `run_*.py` sont **identiques** entre `0f9aa60` et la fin (seuls `run_determinism.py` — correction du contrôle négatif — et `analyze_lowsnr.py` — nouveau — changent) (`git diff --stat`). **Réserve** : les hypothèses de `01_LANDSCAPE.md` (« attentes écrites avant de lancer ») et le journal `08_FALSIFICATION.md` n'entrent dans le dépôt qu'au commit final `363ec81`, après les résultats : leur antériorité n'est pas prouvable par Git (mon analyse).

**Gel des paramètres** : `results/tuned_config.json` (commit `3a6f100`, avant `main.json`) ; `run_main.py` relit ce fichier.

**Critères de décision** (`02_PROTOCOL.md` §6, codés dans `analyze.py`) — une méthode « MÉRITE SA PLACE » sur une piste si les quatre portes sont franchies sur held-out :
- **(a) Gain** : moyenne géométrique sur les 8 scénarios de dérive du ratio `regret_M / regret_référence` **≤ 0,90** ET borne haute de l'IC à 95 % (bootstrap apparié sur graines, 4 000 rééchantillonnages) **< 1,0**.
- **(b) Pas d'explosion** : ratio moyen par scénario **≤ 1,25** vs la meilleure référence simple sur **chacun des 10 scénarios** (témoins inclus).
- **(c) État borné** : taille d'état (octets pickle de l'objet entier) médiane à t=4000 **≤ 1,5 ×** celle à t=1000 dans tous les scénarios.
- **(d) Rejeu** : prédictions bit-à-bit identiques (i) même processus, (ii) deux interpréteurs frais avec `PYTHONHASHSEED` différents, (iii) checkpoint pickle à t=2000 → restauration → reprise, (iv) prédictions à t ≤ 1500 inchangées si toutes les étiquettes d'indice ≥ 1500 sont corrompues (pas de fuite du futur) ; un « tricheur » de contrôle négatif doit être détecté par (iv).

**Correspondance verdict** (`02_PROTOCOL.md` §7) : `ONLINE_ADAPTATION_REFERENCE_SUPPORTED` (≥1 méthode passe sur **les deux** pistes, même famille, et Spearman tuning/held-out ≥ 0,5) ; `LIMITED_ONLINE_METHODS_SUPPORTED` (≥1 méthode passe sur une seule piste, ou passe (a),(c),(d) en échouant (b) sur un sous-ensemble nommé) ; `BATCH_RETRAIN_REMAINS_SUFFICIENT` (aucune ne passe (a) et le refit est à moins de 10 % du meilleur en ligne) ; `NO_ROBUST_ADAPTATION_METHOD` ; `STUDY_INCONCLUSIVE` (Spearman < 0,5 sur une piste, ou IC à cheval sur le seuil).

**Mesures complémentaires** (§8 du protocole) : vitesse d'adaptation (pas jusqu'à ce que le regret glissant sur 50 pas retombe à ≤ 1,5 × son niveau d'avant + 0,01, censuré à 600), oubli (300 points-sondes évalués sans apprentissage à t = 999/1999/2999/3999 contre A et B), ratio de coût de retour, variance (CV = écart-type/moyenne entre graines), croissance de l'état, temps de calcul (µs/étiquette, conteneur partagé 4 cœurs : indicatif).

### 2.2 Run 2 (banc écrit, tuning fait, évaluation jamais terminée)
Code sous `bench/online_learning_v1/` de la branche `-b` (structure différente : `src/` + scripts racine). Différences de conception notables (détail §8) : D = 5, sorties probit (étiquette = `(z > 0)` avec `z = s + σ·ε`, σ = 2,0), 11 scénarios, 28 modèles (13 régression, 15 classification, dont un modèle nul de contrôle par piste), tuning sur graines **1000–1007** (8), évaluation prévue sur 20 graines (`run_eval.py`), critère de tuning = moyenne arithmétique des scénarios de l'excès « overall » post-rodage (500). **Aucun protocole ni critère de décision n'est écrit** dans cette branche (voir §8.3).

---

## 3. Résultats détaillés (run 1 ; le run 2 est traité en §8)

Tous les chiffres viennent de `results/main.json` (3 750 lignes ✔ : 25 entrées × 10 scénarios × 15 graines) via `analyze.py`. « Ratio » = par rapport au refit glissant (`rolling`), la référence simple retenue sur les graines de tuning. Regret bas = mieux.

### 3.1 Résultats de tête (rapport 04 §4.1 ; vérifiés)
- Gel et batch expansif coûtent, en moyenne géométrique sur les 8 scénarios de dérive, **5,4× (C) / 7,9× (R)** et **3,1× (C) / 5,2× (R)** le regret du refit glissant. ✔ recalculé : frozen C 5,404 [5,26 ; 5,54], R 7,935 [7,74 ; 8,15] ; batch C 3,066 [3,02 ; 3,11], R 5,155 [5,08 ; 5,25].
- Le refit glissant borné est une base dure : 8 méthodes sur 12 (C) et 9 sur 11 (R) sont pires sur l'agrégat de dérive. ✔ (compté à la main dans `summary.json`).
- Deux méthodes franchissent les quatre portes : **`bank_sgd_log` (piste C)** ratio 0,88 [0,87 ; 0,90], pire scénario 1,14 (`gradual`), croissance d'état 1,03 ; **`rls` (piste R)** ratio 0,85 [0,84 ; 0,85], pire scénario 0,98 (`abrupt_nonlinear`), croissance 1,00. ✔ (recalcul : 0,884 [0,874 ; 0,896] et 0,847 [0,841 ; 0,852] ; pires scénarios 1,141 et 0,977).
- Presque-réussites qui échouent (b) : `blr` R (0,78 mais 1,58× sur `false_drift`), `sgd_log` C (0,90 mais 2,39× sur `false_drift`), `reset_sgd_log` C (0,93 ; échoue (a) car le gain est < 10 %). ✔ (recalcul : blr 0,778 / 1,578 ; sgd_log 0,902 / 2,391 ; reset_sgd_log 0,929).
- Concordance tuning/held-out (corrélation de rang de Spearman) : **0,97 (C), 0,72 (R)**, tous deux ≥ 0,5 → étude non « inconclusive ». ✔ (0,9725 et 0,7203 dans `summary.json`).

**Lecture en langage simple** : ne pas mettre à jour son modèle coûte très cher (5 à 8 fois plus d'erreur) ; mais une méthode de réentraînement glissant très simple est déjà presque aussi bonne que les méthodes en ligne sophistiquées : la meilleure ne fait que 12–15 % mieux.

### 3.2 Tableau des portes par méthode (rapport 04 §4.2, reproduit)

| piste | méthode | (a) ratio [IC] | (b) pire scénario | (c) croissance d'état max | (d) rejeu | mérite sa place |
|---|---|---|---|---|---|---|
| C | adwin_bag | 2,61 [2,53 ; 2,70] ✗ | 7,13 (gradual) ✗ | 3,89 ✗ | ✓ | non |
| C | arf | 3,32 [3,26 ; 3,38] ✗ | 10,78 (false_drift) ✗ | 5,10 ✗ | ✓ | non |
| C | bank_sgd_log | 0,88 [0,87 ; 0,90] ✓ | 1,14 (gradual) ✓ | 1,03 ✓ | ✓ | **OUI** |
| C | batch | 3,07 [3,02 ; 3,11] ✗ | 9,87 (gradual) ✗ | 4,33 ✗ | ✓ | non |
| C | frozen | 5,40 [5,26 ; 5,54] ✗ | 23,95 (gradual) ✗ | 1,00 ✓ | ✓ | non |
| C | hat | 2,99 [2,90 ; 3,08] ✗ | 8,91 (false_drift) ✗ | 4,72 ✗ | ✓ | non |
| C | ht | 3,04 [2,97 ; 3,12] ✗ | 8,31 (false_drift) ✗ | 3,96 ✗ | ✓ | non |
| C | pa_platt | 1,20 [1,18 ; 1,21] ✗ | 1,53 (gradual) ✗ | 1,00 ✓ | ✓ | non |
| C | pa_raw | 1,21 [1,19 ; 1,23] ✗ | 3,42 (stationary) ✗ | 1,00 ✓ | ✓ | non |
| C | reset_sgd_log | 0,93 [0,92 ; 0,94] ✗ | 1,20 (false_drift) ✓ | 1,04 ✓ | ✓ | non |
| C | sgd_log | 0,90 [0,89 ; 0,91] ✗ | 2,39 (false_drift) ✗ | 1,00 ✓ | ✓ | non |
| C | sgd_log_platt | 0,96 [0,96 ; 0,97] ✗ | 1,16 (gradual) ✓ | 1,00 ✓ | ✓ | non |
| R | arf | 5,16 [5,07 ; 5,26] ✗ | 22,49 (false_drift) ✗ | 4,70 ✗ | ✓ | non |
| R | bank_rls | 1,23 [1,21 ; 1,25] ✗ | 2,81 (gradual) ✗ | 1,11 ✓ | ✓ | non |
| R | batch | 5,15 [5,07 ; 5,25] ✗ | 28,90 (gradual) ✗ | 4,33 ✗ | ✓ | non |
| R | blr | 0,78 [0,77 ; 0,78] ✓ | 1,58 (false_drift) ✗ | 1,00 ✓ | ✓ | non |
| R | frozen | 7,93 [7,74 ; 8,16] ✗ | 58,45 (gradual) ✗ | 1,00 ✓ | ✓ | non |
| R | hat | 1,73 [1,67 ; 1,82] ✗ | 28,79 (false_drift) ✗ | 5,87 ✗ | ✓ | non |
| R | kalman | 1,05 [1,04 ; 1,06] ✗ | 1,37 (abrupt_missing) ✗ | 1,00 ✓ | ✓ | non |
| R | par_reg | 1,18 [1,17 ; 1,19] ✗ | 3,62 (false_drift) ✗ | 1,00 ✓ | ✓ | non |
| R | reset_rls | 1,25 [1,22 ; 1,28] ✗ | 2,32 (gradual) ✗ | 1,03 ✓ | ✓ | non |
| R | rls | 0,85 [0,84 ; 0,85] ✓ | 0,98 (abrupt_nonlinear) ✓ | 1,00 ✓ | ✓ | **OUI** |
| R | sgd_lin | 1,07 [1,06 ; 1,08] ✗ | 2,67 (false_drift) ✗ | 1,00 ✓ | ✓ | non |

(`rolling` = référence, ratio 1,00 par construction.) Source : `reports/013_online_learning/04_RESULTS.md` §4.2 et `results/summary.json`. Vérification : les cases (a), (c) des deux gagnants et plusieurs (b) recalculés ✔ ; les autres lignes, `?` non recalculées une à une mais issues du même `summary.json` produit par `analyze.py`.

**Précision importante** (mon analyse) : les IC ne couvrent que le **hasard des graines** (15 flux indépendants d'un même générateur), pas l'erreur de spécification du générateur, ni le choix de configuration (voir §7).

### 3.3 Regret par scénario — piste C (excès KL en nats/pas, moyenne ± écart-type sur 15 graines)

| modèle | abrupt | gradual | recurring | shock | random_walk | abrupt_missing | abrupt_delayed | abrupt_nonlinear | stationary | false_drift |
|---|---|---|---|---|---|---|---|---|---|---|
| adwin_bag | 0,172±0,026 | 0,160±0,035 | 0,190±0,009 | 0,073±0,011 | 0,146±0,032 | 0,273±0,045 | 0,187±0,027 | 0,339±0,008 | 0,058±0,007 | 0,098±0,013 |
| arf | 0,196±0,016 | 0,208±0,014 | 0,253±0,011 | 0,161±0,020 | 0,214±0,011 | 0,251±0,015 | 0,217±0,016 | 0,309±0,018 | 0,154±0,016 | 0,168±0,016 |
| bank_sgd_log | 0,038±0,004 | 0,026±0,002 | 0,052±0,010 | 0,031±0,003 | 0,048±0,004 | 0,098±0,014 | 0,066±0,004 | 0,319±0,005 | 0,009±0,001 | 0,012±0,002 |
| batch | 0,256±0,007 | 0,222±0,009 | 0,270±0,008 | 0,032±0,003 | 0,170±0,034 | 0,401±0,018 | 0,280±0,009 | 0,341±0,005 | 0,003±0,001 | 0,004±0,001 |
| frozen | 0,556±0,058 | 0,538±0,054 | 0,557±0,049 | 0,036±0,004 | 0,388±0,125 | 0,620±0,050 | 0,569±0,046 | 0,383±0,018 | 0,009±0,002 | 0,013±0,006 |
| hat | 0,163±0,019 | 0,162±0,043 | 0,244±0,014 | 0,105±0,020 | 0,173±0,026 | 0,315±0,050 | 0,202±0,028 | 0,369±0,016 | 0,076±0,018 | 0,138±0,032 |
| ht | 0,205±0,031 | 0,181±0,038 | 0,230±0,022 | 0,090±0,008 | 0,165±0,035 | 0,303±0,026 | 0,228±0,026 | 0,365±0,015 | 0,072±0,006 | 0,129±0,025 |
| pa_platt | 0,054±0,005 | 0,034±0,003 | 0,124±0,006 | 0,032±0,003 | 0,057±0,006 | 0,148±0,015 | 0,087±0,006 | 0,316±0,005 | 0,010±0,001 | 0,012±0,002 |
| pa_raw | 0,059±0,004 | 0,051±0,003 | 0,073±0,004 | 0,062±0,003 | 0,061±0,003 | 0,073±0,009 | 0,081±0,004 | 0,385±0,007 | 0,049±0,005 | 0,053±0,003 |
| reset_sgd_log | 0,036±0,003 | 0,026±0,002 | 0,078±0,004 | 0,039±0,004 | 0,048±0,004 | 0,087±0,014 | 0,062±0,004 | 0,319±0,005 | 0,010±0,002 | 0,019±0,005 |
| **rolling (réf.)** | 0,042±0,003 | 0,022±0,002 | 0,097±0,007 | 0,039±0,002 | 0,053±0,006 | 0,097±0,013 | 0,070±0,004 | 0,321±0,006 | 0,014±0,002 | 0,016±0,002 |
| sgd_log | 0,038±0,003 | 0,027±0,002 | 0,063±0,004 | 0,041±0,003 | 0,041±0,003 | 0,068±0,014 | 0,069±0,005 | 0,355±0,006 | 0,024±0,002 | 0,037±0,003 |
| sgd_log_platt | 0,039±0,003 | 0,026±0,002 | 0,092±0,004 | 0,028±0,002 | 0,049±0,004 | 0,103±0,014 | 0,070±0,005 | 0,318±0,005 | 0,010±0,001 | 0,012±0,002 |

Vérifications ponctuelles ✔ : rolling C abrupt 0,0416±0,0031 ; bank_sgd_log C abrupt 0,0382±0,0040 ; batch C stationary 0,0031±0,0009 ; sgd_log C false_drift 0,0371±0,0035 ; arf C abrupt_nonlinear 0,3085±0,0179 ; frozen C abrupt 0,5565±0,0577.

### 3.4 Regret par scénario — piste R (excès MSE, moyenne ± écart-type sur 15 graines)

| modèle | abrupt | gradual | recurring | shock | random_walk | abrupt_missing | abrupt_delayed | abrupt_nonlinear | stationary | false_drift |
|---|---|---|---|---|---|---|---|---|---|---|
| arf | 0,460±0,017 | 0,383±0,031 | 0,599±0,028 | 0,231±0,018 | 0,394±0,058 | 0,699±0,037 | 0,516±0,016 | 2,170±0,157 | 0,175±0,010 | 0,688±0,055 |
| bank_rls | 0,058±0,006 | 0,052±0,005 | 0,090±0,007 | 0,041±0,004 | 0,147±0,020 | 0,182±0,029 | 0,114±0,009 | 2,356±0,094 | 0,001±0,000 | 0,014±0,005 |
| batch | 0,622±0,024 | 0,532±0,016 | 0,658±0,017 | 0,059±0,007 | 0,391±0,103 | 0,921±0,034 | 0,672±0,019 | 2,446±0,098 | 0,001±0,001 | 0,003±0,001 |
| blr | 0,038±0,002 | 0,022±0,002 | 0,069±0,005 | 0,049±0,003 | 0,040±0,003 | 0,075±0,014 | 0,095±0,010 | 2,544±0,102 | 0,021±0,001 | 0,048±0,006 |
| frozen | 1,133±0,054 | 1,077±0,034 | 1,140±0,031 | 0,061±0,007 | 0,802±0,255 | 1,155±0,050 | 1,186±0,044 | 2,624±0,091 | 0,004±0,002 | 0,010±0,004 |
| hat | 0,089±0,035 | 0,100±0,032 | 0,185±0,057 | 0,092±0,010 | 0,210±0,026 | 0,156±0,036 | 0,145±0,021 | 1,991±0,382 | 0,048±0,003 | 0,880±0,132 |
| kalman | 0,055±0,004 | 0,021±0,002 | 0,147±0,005 | 0,050±0,004 | 0,061±0,008 | 0,163±0,021 | 0,111±0,008 | 2,368±0,093 | 0,007±0,001 | 0,028±0,005 |
| par_reg | 0,070±0,007 | 0,030±0,003 | 0,153±0,011 | 0,067±0,005 | 0,054±0,005 | 0,170±0,026 | 0,126±0,011 | 2,340±0,089 | 0,027±0,001 | 0,111±0,008 |
| reset_rls | 0,052±0,007 | 0,043±0,011 | 0,148±0,009 | 0,052±0,010 | 0,129±0,016 | 0,170±0,029 | 0,109±0,009 | 2,350±0,093 | 0,002±0,001 | 0,017±0,006 |
| rls | 0,042±0,003 | 0,016±0,001 | 0,101±0,006 | 0,048±0,004 | 0,046±0,005 | 0,112±0,017 | 0,098±0,009 | 2,416±0,095 | 0,011±0,001 | 0,027±0,006 |
| **rolling (réf.)** | 0,051±0,006 | 0,018±0,002 | 0,123±0,007 | 0,072±0,006 | 0,058±0,006 | 0,119±0,019 | 0,106±0,009 | 2,473±0,106 | 0,015±0,001 | 0,031±0,006 |
| sgd_lin | 0,056±0,003 | 0,021±0,002 | 0,151±0,003 | 0,050±0,004 | 0,063±0,008 | 0,166±0,023 | 0,113±0,006 | 2,369±0,094 | 0,006±0,001 | 0,082±0,008 |

Vérifications ✔ : rls R gradual 0,0161±0,0015 ; rolling R shock 0,0721±0,0061 ; blr R false_drift 0,0482±0,0061 ; frozen R gradual 1,077±0,034.

**Observation cruciale sur `abrupt_nonlinear` (mon analyse)** : en piste R, tous les modèles linéaires y font ≈ 2,3–2,6, car l'écart-type du signal vrai vaut environ 1,5 (l'interaction `1.5·x0·x1` n'est pas représentable linéairement : variance ≈ 1,5² + 0,25 ≈ 2,5). Ce scénario ajoute donc ≈ 2,4 à toute moyenne **arithmétique** de la piste R, et un ratio ≈ 1,0 à toute moyenne **géométrique** (où il dilue légèrement les gains). Il domine le choix des hyperparamètres (voir §7.2).

### 3.5 Précision réalisée (piste C, accuracy / log-loss, held-out)
Rapport 04 §4.3. Exemples : `bank_sgd_log` stationary 0,832 / 0,368, rolling 0,828 / 0,373, frozen 0,833 / 0,367 ; sur `abrupt`, frozen 0,643 / 0,918 contre rolling 0,811 / 0,407 et bank_sgd_log 0,819 / 0,402. Sur `abrupt_nonlinear`, tout le monde est à 0,55–0,63 de précision : personne n'apprend le concept d'interaction. `?` non recalculé (issu de la même exécution ; `metric` et `logloss` sont dans `main.json`).

### 3.6 Vitesse d'adaptation (rapport 04 §4.3 / 05 §5.4)
Nombre de pas jusqu'à retour à ≤ 1,5 × niveau d'avant + 0,01, médiane sur graines, [% censuré à 600] :

| piste | modèle | abrupt : pas médians [% censurés] | regret 600 pas après | retour (recurring, t=2000) |
|---|---|---|---|---|
| C | pa_raw | 74 [0 %] | 0,097 | 68 [0 %] |
| C | sgd_log | 144 [0 %] | 0,106 | 133 [0 %] |
| C | rolling | 266 [0 %] | 0,173 | 263 [0 %] |
| C | bank_sgd_log | 600 [60 %] | 0,162 | 39 [7 %] |
| C | reset_sgd_log | 600 [60 %] | 0,144 | 415 [13 %] |
| C | pa_platt / batch / frozen | 600 [100 %] | 0,252 / 0,750 / 0,953 | 550 [33 %] / 0 / 0 |
| R | blr | 93 [0 %] | 0,119 | 96 [0 %] |
| R | hat | 128 [7 %] | 0,279 | 127 [0 %] |
| R | rolling | 134 [0 %] | 0,230 | 141 [0 %] |
| R | rls | 219 [0 %] | 0,193 | 204 [0 %] |
| R | kalman | 402 [0 %] | 0,288 | 342 [0 %] |
| R | bank_rls | 401 [7 %] | 0,326 | 40 [0 %] |

Le rapport note que `kalman` (q = 1e-5) et `sgd_lin` (lr = 0,003) sont en **bord de grille** donc lents par artefact de réglage ; que « gradual = 0 pas » est un artefact de métrique (le regret reste sous le seuil au point de changement) ; que `pa_platt`, `reset_sgd_log`, `sgd_log_platt` récupèrent lentement parce que le réglage moyen a favorisé des configurations calmes. ✔ cohérent avec `tuned_config.json`.

Chose à noter (mon analyse) : `bank_sgd_log` est **censuré à 600 dans 60 % des cas sur `abrupt`** alors qu'il gagne en regret moyen : son regret cumulé est bas parce qu'il est précis avant et après, pas parce qu'il se remet vite du choc. Le seuil de 1,5 × niveau d'avant est exigeant quand le niveau d'avant est très bas.

### 3.7 Oubli et états récurrents (rapport 05 §5.2)
Scénario `recurring` ; ratio de coût de retour = regret 600 pas après le retour en A ÷ regret 600 pas après le premier basculement (nouveau) :

| piste | modèle | sonde A en fin de B1 (« oubli ») | sonde B en fin de B1 (plasticité) | ratio de coût de retour | pas d'adaptation retour vs nouveau |
|---|---|---|---|---|---|
| C | bank_sgd_log | 0,838 | 0,012 | **0,42** | 39 vs 431 |
| C | rolling | 1,012 | 0,015 | 1,02 | 263 vs 260 |
| C | sgd_log | 1,105 | 0,021 | 1,00 | 133 vs 124 |
| C | arf / ht / hat | 0,408 / 0,297 / 0,420 | 0,200 / 0,212 / 0,240 | 0,99 / 0,57 / 0,73 | — |
| C | batch / frozen | 0,155 / 0,010 | 0,254 / 0,994 | 0,26 / 0,01 (artefacts) | 0 vs 600 |
| R | bank_rls | 2,040 | 0,003 | **0,34** | 40 vs 373 |
| R | rls | 2,017 | 0,009 | 1,02 | 204 vs 212 |
| R | rolling | 2,027 | 0,012 | 1,04 | 141 vs 140 |

Vérifications ✔ : return-cost bank_sgd_log C 0,4165 (pas 39 vs 431), bank_rls R 0,3357 (40 vs 373), rolling C 1,023 (263 vs 260).

**Interprétation** : « oublier » A quand on apprend B est normal pour un modèle linéaire à un seul état, car A et B sont orthogonaux (un modèle parfait de B a une perte de sonde A ≈ 2,0 en R et ≈ 1,0 nat en C, §5.1 du rapport). Seul un mécanisme de mémoire explicite (la banque de photographies de modèles) rend le retour à A peu coûteux. Les faibles ratios de `batch`/`frozen` sont des **artefacts** : ils ne se sont jamais vraiment adaptés à B, donc ils n'ont rien à réapprendre (rapport 05 l'explique correctement ✔).

### 3.8 Choc temporaire (rapport 05 §5.3)
Regret 600 pas après le retour : C — batch 0,004, frozen 0,009, bank_sgd_log 0,029, sgd_log_platt 0,037, rolling 0,057, reset_sgd_log 0,075, arf 0,155. R — batch/frozen 0,004, bank_rls 0,037, rls 0,079, rolling 0,154. ✔ cohérent avec les tableaux. Message : **réagir vite est un coût quand le changement est transitoire** ; les détecteurs à remise à zéro font pire que le modèle nu.

### 3.9 Variance, état, calcul (rapport 04 §4.3)
| modèle (piste) | état à t=4000 (octets, médiane) | croissance ×(1000→4000) | µs/étiquette (apprentissage) |
|---|---|---|---|
| rls (R) | 841 ✔ | 1,00 | 11 |
| kalman (R) | 838 | 1,00 | 13 |
| sgd_log (C) | 788 | 1,00 | 7 |
| bank_sgd_log (C) | 20 401 ✔ (20 145 à t=1000) | 1,03 | 20 |
| bank_rls (R) | 21 962 | 1,11 | 19 |
| rolling (C / R) | 35 169 / 17 755 ✔ (R) | 1,00 | 88 / 3 |
| batch (C / R) | 464 326 / 464 313 | 4,33 | 13 / 2 |
| ht (C) | 125 620 | 3,96 | 42 |
| hat (C / R) | 165 306 / 275 844 | 4,72 / 5,87 | 83 / 320 |
| adwin_bag (C) | 821 538 | 3,89 | 377 |
| arf (C / R) | 8 084 329 ✔ / 2 126 360 | 5,10 / 4,70 | 510 / 1 135 |

Le CV médian du regret entre graines va de 0,04 à 0,17 ; pire graine / graine médiane ≤ 2,7 (HAT, R). Les temps viennent d'un conteneur partagé : indicatifs.

### 3.10 Sensibilité à faible SNR (rapport 04 §4.4, **non re-tuné**)
Configuration : κ = 1, σ = 1,5 (≈ 3 × moins de signal), 8 graines, trois scénarios (abrupt, recurring, random_walk) ; 600 lignes ✔. Ratio géométrique vs rolling (recalcul ✔ intégralement) :

| piste | modèle | ratio | | piste | modèle | ratio |
|---|---|---|---|---|---|---|
| C | bank_sgd_log | 0,79 | | R | kalman | 0,72 |
| C | reset_sgd_log | 0,79 | | R | sgd_lin | 0,72 |
| C | sgd_log_platt | 0,81 | | R | bank_rls | 0,73 |
| C | pa_platt | 0,87 | | R | rls | 0,77 |
| C | **sgd_log** | **1,82** | | R | reset_rls | 0,83 |
| C | **pa_raw** | **2,71** | | R | par_reg | 0,99 |
| C | adwin_bag / ht / hat / arf | 1,82 / 2,47 / 2,71 / 2,98 | | R | blr | 1,16 |
| C | batch / frozen | 2,05 / 3,93 | | R | batch / frozen / hat / arf | 2,91 / 5,34 / 3,95 / 4,13 |

Le rapport dit : « les apprenants récursifs linéaires avec oubli (RLS, Kalman, SGD, bank_*) gagnent 20–28 % ». **✘ écart partiel** : c'est exact pour R (`rls` 0,77, `kalman`/`sgd_lin` 0,72, `bank_rls` 0,73) et pour `bank_sgd_log` C (0,79), mais **`sgd_log` en piste C est à 1,82 × (pire que rolling)** et `blr` R à 1,16 ; le résumé exécutif ne dit d'ailleurs que « ≈ 20–28 % » sans cette réserve. Le rapport reconnaît que le test mesure en partie la robustesse du réglage : le rolling tuné à SNR normal a une fenêtre trop courte à SNR bas (INFERENCE du rapport ✔ plausible, cf. run 2 où la fenêtre optimale est 400).

### 3.11 Ce que le rapport 04 §4.5 met en avant
- Sur `stationary` et `false_drift`, le batch expansif est meilleur (0,003) ; les adaptatifs paient une « taxe de variance » (rolling 0,014, sgd_log 0,024, rls 0,011). ✔ (batch C stationary 0,0031).
- `false_drift` casse SGD sans garde-fou (C 0,037 vs 0,016 ; R 0,082) et ARF/HAT (R 0,69–0,88 vs 0,03) : « s'adapter à l'échelle n'est pas s'adapter au concept ».
- Les arbres ne gagnent presque pas même sur le concept non linéaire : ARF 0,309 vs rolling 0,321 (≈ −4 %). ✔ (0,3085 vs 0,321).

---

## 4. Candidats évalués un par un (rapport 09 + mon analyse)

Rappel : l'adjudication est de la recherche externe, pas une décision d'intégration.

| candidat | appel du rapport | justification chiffrée (vérifiée) | conditions de changement de verdict (mon analyse) |
|---|---|---|---|
| **Refit glissant borné** (fenêtre 150–300, refit tous les 25 pas) | ADOPT comme référence | 3 à 8 × mieux que frozen/batch sous dérive ; état 18–35 Ko ; rejouable ; 12–15 % derrière les meilleurs en ligne | La fenêtre optimale dépend du SNR (150 à SNR normal en R, 400 dans le run 2 à SNR bas) : à re-tuner sur données réelles |
| **RLS avec oubli (λ ≈ 0,99)** — régression | ADOPT comme référence incrémentale (R) | 0,85 × rolling [0,84 ; 0,85] ; 841 octets ; 11 µs/mise à jour ; 4/4 portes ; ~10 lignes maison | Bord de grille λ = 0,98 meilleur si on ignore la piste non linéaire (§7.2) ; pas de garde-fou d'échelle (pire scénario 0,98 ici, mais non testé au-delà de `false_drift` ×3) |
| **SGD logistique + banque de dérive (`bank_sgd_log`)** — classification | ADAPT (avec garde-fous) | 0,88 [0,87 ; 0,90] ; pire 1,14 (gradual) ; seule méthode exploitant la récurrence (coût de retour 0,42) ; **non tunée** (une seule config lr = 0,03, δ = 0,002) | Utile seulement si des régimes récurrents existent dans le réel (UNKNOWN) ; `sgd_log`/`sgd_log_platt` sont à 2–8 % sans la machinerie |
| `sgd_log_platt`, `sgd_log`, `reset_sgd_log`, `pa_*` | PARK | ≤ 10 % de gain ou échec de (b) (`sgd_log` 2,39 × sur false_drift) | Si gain > 10 % avec un garde-fou d'échelle |
| `blr` (BayesianLinearRegression, lissage 0,98) | PARK | meilleur regret brut R (0,78) mais 1,58 × sur false_drift | Passerait (b) avec un garde-fou d'échelle |
| `kalman`, `sgd_lin`, `par_reg`, `reset_rls`, `bank_rls` | PARK | 1,05 à 1,25 × | Kalman sous-exploré (q = 1e-5 en bord de grille) ; dans le run 2, Kalman est à 0,91 en tuning avec q = 1e-4 (§8) |
| HT / HAT / ARF / ADWIN-bagging | REJECT pour cet usage | 2,6–5,2 × pires que rolling ; état ×4–6 ; 0,4–1,1 ms/étiquette | Concept non linéaire à beaucoup plus de données (T > 4 000 : UNKNOWN) ; bornage `max_size`/`max_depth` non testé |
| Frozen / batch expansif | REJECT comme réponse adaptative, GARDÉS comme témoins | meilleurs seulement sans mouvement (batch 0,003 en stationary) | — |

**Verdict formel** : aucune méthode ne passe sur les deux pistes → `LIMITED_ONLINE_METHODS_SUPPORTED`. Le rapport 09 admet (« Honest reading ») que la décision repose sur le seuil de 10 % : avec un seuil de 15 %, `rls` (0,85) passerait tout juste et `bank_sgd_log` (0,88) non.

---

## 5. Bloc final complet (reproduit tel quel, `00_EXECUTIVE_SUMMARY.md`)

```
ALGORITHMS_DISCOVERED=12 families (+ 5 named but not executed: AdaBoost/ADWINBoosting/SRP/LeveragingBagging, VW/MOA)
ALGORITHMS_EXECUTED=15 candidate algorithms (19 model×track entries) + 3 baselines

FROZEN_BASELINE=executed; 5.4x (C) / 7.9x (R) rolling-refit regret under drift; best only when stationary/shock
BATCH_RETRAIN_BASELINE=executed (expanding, period 250); 3.1x (C) / 5.2x (R) rolling-refit regret under drift; best on stationary/false-drift controls

ONLINE_ADAPTATION_BENEFIT=12% (C, bank_sgd_log 0.88 [0.87,0.90]) to 15% (R, rls 0.85 [0.84,0.85]) below a tuned rolling refit; ~20-28% at 3x lower SNR (untuned); synthetic only
RECURRING_STATE_RECOVERY=only with explicit memory bank (return-cost 0.42 C / 0.34 R; 39-40 vs 373-431 steps); all single-state learners ~1.0
DETERMINISTIC_REPLAY_SUPPORTED=YES (25/25 entries: replay, cross-process, checkpoint, no-leak; negative control detected; single platform)

BEST_SIMPLE_REFERENCE=bounded rolling-window refit (window 150-300, refit every 25)
BEST_INCREMENTAL_REFERENCE=rls (RLS, lambda=0.99) for regression; bank_sgd_log (SGD logistic + drift bank) for classification

FINAL_VERDICT=LIMITED_ONLINE_METHODS_SUPPORTED
```

### Explication ligne par ligne
- `ALGORITHMS_DISCOVERED=12 families (+5 nommées non exécutées)` : 12 familles répertoriées dans `01_LANDSCAPE.md` (River, SGD, PA, arbres de Hoeffding, arbres adaptatifs, ARF, bagging/boosting en ligne, RLS, Kalman, calibration Platt, reset piloté par ADWIN, refit glissant) ; 5 citées mais non lancées (AdaBoost, ADWINBoosting, SRP, LeveragingBagging, VW/MOA).
- `ALGORITHMS_EXECUTED=15 (19 entrées modèle×piste) + 3 baselines` : ✔ 19 entrées candidates comptées (10 en C, 9 en R) + 6 entrées baselines = 25 entrées ; le chiffre « 15 algorithmes » est un regroupement du rapport (`?` non défini précisément).
- `FROZEN_BASELINE` : modèle figé ; 5,4 × / 7,9 × le regret du rolling sous dérive ✔ ; « meilleur seulement quand stationnaire ou choc ».
- `BATCH_RETRAIN_BASELINE` : refit à fenêtre expansive, période 250 (bord de grille) ; 3,1 × / 5,2 × ✔ ; meilleur sur les témoins.
- `ONLINE_ADAPTATION_BENEFIT` : gain 12 % (C) à 15 % (R) sous un refit glissant tuné ✔ (0,884 et 0,847) ; « ~20-28 % à SNR 3 × plus bas (non re-tuné) » : ✔ pour 5 des 7 méthodes linéaires récursives, ✘ pour `sgd_log` C (1,82 ×), voir §3.10.
- `RECURRING_STATE_RECOVERY` : seule la banque explicite récupère (0,42 C / 0,34 R ; 39–40 pas contre 373–431) ✔ ; les apprenants à un état sont ~1,0.
- `DETERMINISTIC_REPLAY_SUPPORTED=YES` : 25/25 entrées sur quatre tests ✔ (`determinism.json` : 25 lignes, toutes vraies) ; contrôle négatif détecté ✔ ; **une seule plateforme**.
- `BEST_SIMPLE_REFERENCE` : refit glissant fenêtre 150–300, refit tous les 25 pas ✔ (150 en R, 300 en C).
- `BEST_INCREMENTAL_REFERENCE` : `rls` (λ = 0,99) en régression ; `bank_sgd_log` en classification. **Nuance (mon analyse)** : `analyze.py` calcule aussi un « meilleur incrémental » par tuning et par held-out ; ils valent **`hat` (tuning) et `blr` (held-out) en piste R** (`summary.json`). Le choix de `rls` est fondé sur « qui franchit les quatre portes », pas sur ce calcul. Aucun rapport ne le dit.
- `FINAL_VERDICT` : calculé par les règles pré-enregistrées.

---

## 6. Contrôles de validité

### 6.1 Rejeu, déterminisme, fuite (rapport 06 ; `determinism.json`)
Exécution sur `abrupt_delayed`, graine 1, configs tunées, 25 entrées :
- **Rejeu même processus** : deux runs → même SHA-256 des prédictions : 25/25 ✔ (recalculé sur `determinism.json`).
- **Rejeu inter-processus** : deux interpréteurs frais avec `PYTHONHASHSEED` = 1 et 12345, égaux entre eux et au run en processus : 25/25 ✔.
- **Checkpoint/restauration** : arrêt à t=2000, `pickle.dumps` → `loads` → reprise : identique : 25/25 ✔ (tailles : 313 octets pour frozen R, 220 669 pour batch R, 17 755 pour rolling R, 841 pour rls…).
- **Pas de fuite du futur** : corruption de toutes les étiquettes d'indice ≥ 1500 ; les prédictions à t ≤ 1500 doivent être inchangées : 25/25 ✔.
- **Contrôle négatif** : un `Cheater` qui lit l'étiquette courante est bien détecté : `cheater_detected = True` ✔.
- **Assertion d'arrivée** `τ+1+delay ≤ now` : exécutée à chaque livraison, 3 750 runs sans arrêt ; `?` (l'assertion est dans le code, `harness.py` ✔ lu ; l'absence d'abandon est déduite de l'existence des 3 750 lignes).
- Sources de déterminisme : graines explicites pour HAT/ARF/ADWIN-bagging (`seed=1`), RNG numpy `default_rng([seed, somme(ord(nom))])` (pas de `hash()`), threads BLAS fixés à 1.

**Mon rejeu indépendant (recalcul)** : j'ai extrait le code de la branche (versions figées : river 0.26.1, scikit-learn 1.9.1, Python 3.11.15, numpy 2.4.6 installé sur cette machine — la version numpy de l'auteur n'est pas notée dans le run 1, `?`). Sur 7 runs choisis (C rolling abrupt s1 ; C bank_sgd_log recurring s2 ; R rls gradual s3 ; R blr false_drift s1 ; C sgd_log false_drift s4 ; R kalman shock s5 ; C frozen abrupt s1), le **regret et le hash de prédictions sont strictement identiques** à ceux de `main.json` (égalité à 1e-12 et hash égal) ✔. J'ai aussi lancé une passe complète de `run_main.py` (3 750 runs) ; je l'ai **interrompue au bout d'environ 28 minutes** sans résultat (le conteneur était saturé : charge moyenne ≈ 20 sur 4 cœurs, processus à ~30 % de CPU ; `Pool.map` n'écrit rien avant la fin). Cette passe complète n'est donc **pas vérifiée** (`?`) ; seule l'égalité sur les 7 runs témoins l'est.

### 6.2 Erreurs corrigées / écarts au protocole
- `run_determinism.py` a été **corrigé après le tuning** (commit `6caada0`) : le contrôle négatif `Cheater` consommait son compteur aussi lors des appels de sondes du harnais (l'ancienne version comptait les appels de sondes comme des pas de flux) ; la correction ignore les appels dont l'entrée n'est pas la prochaine ligne du flux. Ce changement n'est **mentionné dans aucun rapport** ; le message de commit dit seulement « determinism runner fix ». Impact : il concerne le contrôle négatif, pas les résultats de régret. (mon analyse)
- Aucun écart déclaré au protocole dans les rapports 00–10. Écarts que je constate : (i) l'IC bootstrap utilise `default_rng(0)` fixé dans `analyze.py` : reproductible ✔ ; (ii) la « meilleure référence simple » est choisie sur la **moyenne arithmétique** du regret de tuning sur les 8 scénarios de dérive (`tuning_agg` de `analyze.py`), alors que la porte (a) utilise la moyenne **géométrique** : incohérence mineure, sans effet ici (rolling l'emporte partout).

### 6.3 Ce que les tests de validité ne couvrent pas
Une seule graine et un seul scénario (`abrupt_delayed`) pour le rejeu ; une seule plateforme ; pas de test multi-thread BLAS ; le test de fuite ne teste qu'une coupure (t=1500) et ne corrompt que les étiquettes, pas les features (rapport 06 §Caveats l'admet en partie).

---

## 7. Critique indépendante

### 7.1 Points forts (pour être juste)
Protocole et code figés avant le held-out, vérifié par l'historique Git ; critères chiffrés codés (pas de verdict « à l'œil ») ; tableaux complets avec écarts-types ; contrôles négatifs ; rejeu que j'ai reproduit bit à bit ; auto-critique honnête (`09` « Honest reading », `10`). Les runs individuels se rejouent en une fraction de seconde (§6.1), ce qui rend l'étude vérifiable (la passe complète n'a pas pu être bouclée par moi, §9.1).

### 7.2 Points faibles et hypothèses fragiles
1. **Le choix des hyperparamètres en piste R est dominé par un scénario où aucun modèle linéaire ne peut rien** (recalcul sur `tuning_rows.json`). Avec la moyenne arithmétique sur 10 scénarios, `abrupt_nonlinear` pèse ≈ 2,4 sur un total ≈ 0,30. Excluant ce scénario, les scores de tuning changent de classement : `rls` λ = 0,98 (bord de grille) donnerait 0,0527 contre 0,0581 pour λ = 0,99 (choisi) ; `blr` smoothing 0,98 (bord) 0,0527 ; `kalman` q = 1e-4 (0,0562) au lieu de q = 1e-5 (0,0747, choisi). Le rolling R resterait à W = 150 (0,0687, bord de grille aussi). Autrement dit les réglages retenus en R dépendent d'un scénario non discriminant, et plusieurs optimums sont **au bord de grille** (donc non encadrés).
2. **Bords de grille** (déclarés dans `08`, `10`, vérifiés dans `tuned_config.json`) : `kalman` q = 1e-5, `sgd_lin` lr = 0,003, `sgd_log` lr = 0,1, `rolling|R` W = 150, `batch` P = 250, `par_reg` C = 0,01, `pa_platt` C = 0,01, `reset_*` δ = 0,05, `blr` smoothing = 0,98. Une grille plus large pourrait déplacer les gains dans un sens ou dans l'autre (INFERENCE).
3. **Asymétrie de réglage** : `bank_sgd_log` et `bank_rls` n'ont **qu'une configuration** (pas de réglage), et `bank_sgd_log` utilise lr = 0,03 alors que `sgd_log` seul a été réglé à lr = 0,1. Le rapport 10 §3 le présente comme un « léger avantage à la baseline » ; mais la banque hérite d'un lr différent, ce qui rend la comparaison bank vs sgd_log moins nette (mon analyse).
4. **Gain marginal contre un seuil arbitraire** : 0,88 et 0,85 contre un seuil de 0,90. Le rapport 09 reconnaît que 15 % ferait échouer `bank_sgd_log`. Le seuil de 10 % n'est pas justifié par un coût économique.
5. **Le verdict tient sur deux méthodes différentes, une par piste** ; le rapport 10 §10 note qu'aucune référence transversale n'est établie. Ce n'est pas un défaut du procédé, mais l'énoncé « LIMITED… SUPPORTED » peut être lu à tort comme un feu vert pour une méthode unique. Or il manquait au run 1 un classifieur de la famille « moindres carrés récursifs » (EKF logistique / logistique bayésienne avec oubli) — présent seulement dans le run 2 (§8). C'est possiblement la cause de l'absence de méthode commune (INFERENCE, à valider).
6. **Le monde simulé est très gentil** : gaussien i.i.d., bruit stationnaire, concepts orthogonaux (limite haute pour le coût de l'immobilisme), SNR élevé (κ = 3 ; bruit 0,5). Les marchés réels ont queues épaisses, autocorrélation, hétéroscédasticité, SNR minuscule (rapport 10 §1). Le rapport le dit ; ce que les chiffres **ne prouvent pas** : qu'un gain de 12–15 % existe, ou même ait le même signe, sur des données de marché.
7. **`false_drift` n'est qu'un seul type de choc d'échelle** (×3 sur traits et bruit pendant 400 pas). Les échecs de SGD/BLR/ARF/HAT « avec garde-fou d'échelle nécessaire » ne sont pas testés avec un garde-fou ; la conclusion « il faut un garde-fou » est INFERENCE.
8. **Multiplicité** (rapport 10 §9) : 19 entrées × 10 scénarios × 2 pistes examinées ; les IC serrés reflètent 15 flux indépendants d'un générateur, pas la robustesse au générateur.
9. **Métrique d'adaptation** dégénérée pour `gradual` (0 pas) ; `censuré à 600` pour beaucoup de méthodes ; l'ordre des méthodes sur la vitesse dépend surtout de leur taux d'apprentissage réglé.
10. **Formulations à nuancer** : « ~20–28 % à SNR bas » (voir §3.10 ✘) ; « BEST_INCREMENTAL_REFERENCE » incohérent avec le calcul de `analyze.py` en R (§5) ; « attentes écrites avant » non prouvables (§2.1).
11. **Pré-enregistrement partiel** : le protocole et les scripts sont figés avant, mais le protocole autorise la sélection de la référence simple *après* tuning sur les 8 scénarios de dérive avec l'agrégat arithmétique : c'est un degré de liberté pré-déclaré, donc acceptable, mais qui n'est pas neutre pour la piste R (point 1).
12. **Compute et état** : les µs proviennent d'un conteneur partagé ; les octets sont ceux de `pickle`, format non versionnable (voir §6 et §8.5).

### 7.3 Écarts rapports vs résultats bruts (bilan des vérifications)
Voir le tableau de vérification ci-dessous : aucun écart numérique sur les 30+ chiffres clés recalculés ; deux écarts d'énoncé (`SNR bas` généralisé à SGD ; `BEST_INCREMENTAL_REFERENCE` en R) ; une omission (correction du contrôle négatif).

| # | Chiffre / affirmation | Source du rapport | Résultat de ma vérification | Marque |
|---|---|---|---|---|
| 1 | 3 750 runs held-out | 00, 02 | 3 750 lignes ; graines 1–15 ; 25 entrées | ✔ |
| 2 | frozen 5,4 × (C) / 7,9 × (R) | 00, 04 | 5,404 / 7,935 | ✔ |
| 3 | batch 3,1 × / 5,2 × | 00, 04 | 3,066 / 5,155 | ✔ |
| 4 | bank_sgd_log 0,88 [0,87 ; 0,90] | 04 | 0,884 [0,874 ; 0,896] | ✔ |
| 5 | rls 0,85 [0,84 ; 0,85] | 04 | 0,847 [0,841 ; 0,852] | ✔ |
| 6 | blr 0,78 et 1,58 × sur false_drift | 04 | 0,778 ; 1,578 | ✔ |
| 7 | sgd_log 0,90 et 2,39 × false_drift | 04 | 0,902 ; 2,391 | ✔ |
| 8 | Pire scénario bank_sgd_log 1,14 (gradual) ; rls 0,98 | 04 | 1,141 ; 0,977 (abrupt_nonlinear) | ✔ |
| 9 | Spearman 0,97 / 0,72 | 04, 09 | 0,9725 / 0,7203 | ✔ |
| 10 | Coût de retour bank 0,42 C / 0,34 R ; 39/431 et 40/373 pas | 05 | 0,4165 ; 0,3357 ; 39 vs 431 ; 40 vs 373 | ✔ |
| 11 | État rls 841 octets ; arf C 2 341 288 → 8 084 329 | 04 | 841 → 841 ; 2 341 287,5 → 8 084 329 | ✔ |
| 12 | Tableaux par scénario (échantillon de 10 cellules) | 04 | égalité à l'arrondi | ✔ |
| 13 | Tableau bas SNR (26 lignes) | 04 §4.4 | égalité intégrale | ✔ |
| 14 | 25/25 rejeu, cheater détecté | 06 | 25 lignes vraies ; cheater_detected true | ✔ |
| 15 | 1 680 lignes de tuning | (déduit) | 56 configs × 10 scénarios × 3 graines | ✔ |
| 16 | Réglages en bord de grille cités | 05, 08 | conformes à `tuned_config.json` | ✔ |
| 17 | « SNR bas : RLS, Kalman, **SGD**, bank_* gagnent 20–28 % » | 04 §4.4, 08 H12 | vrai sauf sgd_log C (1,82) ; blr R 1,16 | ✘ partiel |
| 18 | BEST_INCREMENTAL_REFERENCE=rls (R) | 00 | `summary.json` : tuning=hat, held-out=blr | ✘ énoncé |
| 19 | Protocole antérieur au held-out | 02 | commit 17:50:25 vs 18:08:49 ; fichier inchangé | ✔ |
| 20 | Hypothèses de 01 « écrites avant » | 01, 08 | commit final seulement | ? |
| 21 | Temps (µs) et « conteneur partagé 4 cœurs » | 04, 10 | non rejouables à l'identique | ? |
| 22 | 15 algorithmes candidats (regroupement) | 00 | 19 entrées comptées ; regroupement non défini | ? |

---

## 8. Comparaison run 1 / run 2

**Mise en garde initiale** : le run 2 n'a **aucun résultat held-out**. La seule comparaison chiffrée possible est celle des **résultats de tuning** (sur graines de tuning, donc optimistes pour toute méthode réglée dessus) et celle des **choix de conception**. Le run 1 a aussi des résultats de tuning (`tuning_rows.json`), ce qui permet une comparaison à armes égales : « tuning vs tuning ». Tous les ratios de cette section sont mes recalculs (sauf mention contraire) à partir de `tune.json` (run 2) et `tuning_rows.json` / `tuned_config.json` (run 1) ; le run 2 se rejoue à l'identique : j'ai recalculé le score de tuning de `rls`, `rolling_ridge`, `ekf_logit`, `rolling_logit` (8 graines × 11 scénarios) et obtenu **exactement** les valeurs stockées, écart 0 par scénario ✔.

### 8.1 Le banc : mêmes questions ?

| Aspect | Run 1 | Run 2 |
|---|---|---|
| Dimension D | 8 | 5 |
| Horizon T / rodage | 4 000 / 500 | 4 000 / 500 |
| Modèle classification | P = sigmoïde(3·w·x) (logistique, forte) | étiquette = 1[z > 0], z = s + σε, P = Φ(s/σ) (probit), σ = 2,0 |
| Bruit régression | 0,5 | 2,0 |
| SNR | élevé (κ = 3 ; σ = 0,5) ; le run « SNR bas » a κ = 1, σ = 1,5 | bas (σ = 2,0) : plus proche du run « SNR bas » du run 1 |
| Concepts | A ⟂ B (orthogonaux) | A, B, C tirés au hasard, non orthogonalisés (`_unit(rw)` ×3) |
| Scénarios | 10 : stationary, abrupt, gradual, recurring, shock, false_drift, random_walk, abrupt_missing, abrupt_delayed, abrupt_nonlinear | 11 : stationary, abrupt, gradual, recurring, shock, false_drift, missing_random, missing_blackout, delayed_50, delayed_200, nonlinear_abrupt ; **pas de random_walk** |
| false_drift | traits ×3 **et** bruit ×3 simultanés, t=2000–2400 | bruit ×3 sur 1800–2000 puis traits ×2 sur 2600–2800 (deux chocs distincts) |
| Étiquettes manquantes | 70 % perdues **après** t=2000 | `missing_random` : 70 % perdues **sur tout le run** (`avail = keep_u < 0,3`) ; `missing_blackout` : plus aucune étiquette de 1900 à 2500 |
| Retards | 100 pas (un cas) | 50 et 200 pas |
| Non-linéaire | interaction ±1,5·x0·x1 (+ terme linéaire) | interaction ±0,8·x0·x1 avec poids 0,8·w |
| Graines | tuning 100–102 (3) ; held-out 1–15 (15) ; SNR bas 1–8 | tuning 1000–1007 (8) ; eval prévue 0–19 (20) ; « lowsnr » 10 graines (bruit 4,0) ; « default » 10 graines (non tunées) |
| Nombre de modèles | 25 entrées (19 candidates + 6 baselines) | 28 (dont 2 modèles nuls) |
| Nombre de configurations testées | 56 | 76 |
| Séparation tuning/eval | oui (graines disjointes) | oui (1000–1007 vs 0–19) |
| Sorties | `summary.json`, tableaux, 11 rapports | `tune.json` seulement |
| Critères de décision | 4 portes (a)–(d) pré-enregistrées | **aucun** |
| Aléas communs | non explicité (RNG par scénario) | oui : « common random numbers » : mêmes vecteurs, features, bruits entre scénarios d'une même graine |
| Métrique de régret | KL / MSE contre la vérité, post-rodage | idem (exact, sans bruit d'étiquette) : `excess` |

### 8.2 Le tuning : mêmes algorithmes ? mêmes grilles ? mêmes optimums ?

**Algorithmes.** Communs aux deux runs : refit glissant, batch/périodique, gelé, RLS, Kalman à marche aléatoire, SGD linéaire/logistique River, PA régression/classification, arbre de Hoeffding (HAT adaptatif dans le run 1 ; Hoeffding non adaptatif dans le run 2), ARF, reset piloté par ADWIN, banque de modèles maison, Platt en ligne. **Propres au run 1** : `blr` (BayesianLinearRegression River), `adwin_bag`, PA + Platt, HAT. **Propres au run 2** : **`ekf_logit`** (logistique bayésienne récursive/EKF avec oubli), `river_adaboost_clf`, `rolling_*_drift` (refit glissant à fenêtre tronquée par ADWIN), `hoeffding_platt`, deux modèles nuls (`null_reg`/`null_clf`, témoin de « skill »). Différences d'implémentation (lues dans le code) :
- **Reset** : run 1 = nouvelle instance **réchauffée** sur les 150 derniers échantillons, base RLS λ = 0,999 ; run 2 = nouvelle instance **sans réchauffement** (elle n'apprend que l'échantillon courant), base RLS **λ = 1,0** (sans oubli). Le `reset` du run 2 est donc structurellement désavantagé.
- **Banque** : run 1 = K = 3, instantanés « retardés » tous les 100 pas, comparaison par perte EWMA active vs banque, seuil 0,85, **non réglée** ; run 2 = K = 4, mémoire des 50 dernières étiquettes, rappel de l'instantané qui ajuste le mieux les 50 derniers points si sa perte < 0,8 × celle de l'actif, δ d'ADWIN **réglé**.
- **Kalman** : run 1 = bruit de mesure fixe R = 0,25 ; run 2 = bruit de mesure estimé par EWMA de l'erreur (adaptatif). Cela suffit à expliquer une partie de la différence de performance (INFERENCE).
- **RLS** : initialisation P0 = 10·I (run 1) vs 100·I (run 2).
- **SGD linéaire** : run 1 `intercept_lr=0` ; run 2 réglages par défaut de River.
- **PA reg** : run 1 `learn_intercept=False` ; run 2 `mode=1`.

**Grilles et optimums retenus**

| Modèle | Run 1 : grille → choix | Run 2 : grille → choix | Même grille ? Même optimum ? |
|---|---|---|---|
| refit glissant, régression | W ∈ {150, 300, 600} → **150** (bord bas) | W ∈ {100, 200, 400, 800} → **400** (intérieur) | non ; non — mais tendance cohérente avec le SNR (fenêtre plus longue à SNR bas) |
| refit glissant, classification | W ∈ {150, 300, 600} → **300** | W ∈ {200, 400, 800, 1600} → **400** | non ; voisins |
| RLS | λ ∈ {0,98 ; 0,99 ; 0,995 ; 0,999} → **0,99** | λ ∈ {0,99 ; 0,995 ; 0,998 ; 0,9995} → **0,995** | non (grilles décalées) ; horizon effectif 1/(1−λ) = 100 vs 200 |
| Kalman | q ∈ {1e-5, 1e-4, 1e-3, 1e-2} → **1e-5** (bord) | même grille → **1e-4** (intérieur) | **même grille** ; optimum différent (bord vs intérieur) |
| SGD linéaire | lr ∈ {0,003 ; 0,01 ; 0,03} → **0,003** (bord) | {0,005 ; 0,02 ; 0,05} → **0,005** (bord) | non ; **les deux au bord bas** (lr = 0,05 diverge dans le run 2 : score 2,3e11 ; lr = 0,03 dans le run 1 : 1,2e22) |
| PA régression | C ∈ {0,01 ; 0,1 ; 1} → **0,01** (bord) | même grille → **0,01** (bord) | **même grille, même optimum (bord bas)** |
| SGD logistique | lr ∈ {0,01 ; 0,03 ; 0,1} → **0,1** (bord haut) | {0,005 ; 0,02 ; 0,05} → **0,02** (intérieur) | non ; **optima opposés** |
| PA classification | C ∈ {0,01 ; 0,1 ; 1} → raw 0,1 ; platt 0,01 | même grille → **0,01** | même grille |
| Arbre de Hoeffding | grace ∈ {50, 200} → 200 (ht C ; HAT C) ; HAT R 50 | {50, 200} → **200** (reg et clf) | même grille ; optimum au bord haut presque partout |
| ARF | 1 config (grace 50, non réglé) | grace ∈ {50, 200} → **200** | non réglé vs réglé |
| Reset ADWIN | δ ∈ {0,002 ; 0,05} → **0,05** | δ ∈ {0,1 ; 0,02 ; 0,002} → **0,1** | partiellement ; **les deux au bord permissif** |
| Banque | 1 config (non réglée) | δ ∈ {0,1 ; 0,02 ; 0,002} → **0,1** | non réglée vs réglée ; run 2 au bord |
| Batch / périodique | P ∈ {250, 500, 1000} → 250 (bord) | R ∈ {100, 250, 500} → **100** (bord) | non ; **les deux au bord bas** |
| Gelé | n0 = 500 fixe | n0 ∈ {250, 1000} → **250** (bord) | non |
| BLR | smoothing ∈ {None, 0,995, 0,98} → 0,98 (bord) | absent | — |
| EKF logistique | absent | λ ∈ {0,99 ; 0,995 ; 0,998 ; 0,9995} → **0,995** | — |

**Comment le run 2 choisit** : `run_tune.py` retient, par modèle, la configuration de plus petit score, score = moyenne arithmétique sur les 11 scénarios de la moyenne sur 8 graines de l'excès « overall ». C'est la même logique que le run 1 (moyenne arithmétique sur tous les scénarios), donc **mêmes défauts** (domination par les scénarios où le regret est gros, notamment nonlinear). ✔ vérifié dans le code. 76 configurations × 11 × 8 = 6 688 tâches ✔ (log : « 6688 jobs », 1 111,5 s).

### 8.3 Résultats de tuning côte à côte (ratio au refit glissant tuné, sur graines de tuning)

Attention : ratios du run 1 = 10 scénarios ; du run 2 = 11 scénarios ; graines de tuning de chaque run ; **pas des held-out**. « Arith » = ratio des scores moyens arithmétiques ; « Géo » = moyenne géométrique des ratios par scénario ; « pire » = ratio maximal sur un scénario.

**Piste régression** (référence = refit glissant ; tuning du run 1 : rolling W = 150, score 0,3107 ; tuning du run 2 : W = 400, score 0,2551)

| méthode | Run 1 arith | Run 1 géo | Run 1 pire scénario | Run 2 arith | Run 2 géo | Run 2 pire scénario |
|---|---|---|---|---|---|---|
| RLS | 0,952 | 0,832 | 0,98 (nonlinear) | **0,890** | 0,893 | 1,03 (stationary) |
| Kalman | 0,985 | 0,937 | 1,36 (abrupt_missing) | 0,909 | 0,898 | 1,02 (stationary) |
| SGD linéaire | 1,01 | 1,065 | 2,52 (false_drift) | 1,166 | 1,401 | 3,35 (false_drift) |
| PA régression | 1,029 | 1,342 | 3,13 (false_drift) | 1,124 | 1,208 | 1,56 (gradual) |
| Banque RLS | 0,993 | 0,846 | 2,78 (gradual) | 1,136 | 1,088 | 2,98 (gradual) |
| Reset RLS | 0,996 | 0,843 | 2,37 (random_walk) | 1,73 | 1,594 | 13,8 (false_drift) |
| Arbre adaptatif (HAT) / Hoeffding | 1,225 (HAT) | 2,42 | 26,9 (false_drift) | 2,066 (Hoeffding) | 2,79 | 7,03 (false_drift) |
| ARF | 2,024 | 6,34 | 21,0 (gradual) | 2,628 | 3,50 | 8,32 (gradual) |
| Batch / périodique | 2,057 | 2,27 | 28,8 (gradual) | 2,311 | 1,70 | 8,49 (gradual) |
| Gelé | 2,993 | 3,98 | 56,1 (gradual) | 4,284 | 4,00 | 19,2 (gradual) |
| BLR | 0,979 | 0,886 | 1,49 (stationary) | — | — | — |

**Piste classification** (référence : run 1 rolling W = 300, 0,0788 ; run 2 rolling W = 400, 0,0193)

| méthode | Run 1 arith | Run 1 géo | Run 1 pire | Run 2 arith | Run 2 géo | Run 2 pire |
|---|---|---|---|---|---|---|
| SGD logistique | 0,990 | 1,048 | 2,30 (false_drift) | **0,935** | 0,938 | 1,03 (gradual) |
| SGD logistique + banque | **0,895** | 0,833 | 1,18 (gradual) | — | — | — |
| EKF logistique + banque | — | — | — | 0,925 | 0,810 | 1,13 (gradual) |
| **EKF logistique (RLS-like)** | — | — | — | **0,863** | 0,867 | 1,02 (stationary) |
| SGD logistique + reset | 0,930 | 0,915 | 1,18 (gradual) | — | — | — |
| EKF + reset | — | — | — | 1,066 | 0,935 | 1,67 (gradual) |
| SGD logistique + Platt | 0,968 | 0,917 | 1,21 (gradual) | 0,958 | 0,977 | 1,11 (gradual) |
| PA classification | 1,212 (raw) / 1,136 (platt) | 1,45 / 1,09 | 3,38 / 1,54 | 1,168 | 1,186 | 1,50 (gradual) |
| Hoeffding / HT | 2,529 | 3,52 | 7,45 | 2,72 | 3,09 | 7,44 (gradual) |
| ARF | 2,636 | 3,97 | 10,3 | 2,422 | 2,89 | 5,74 (gradual) |
| AdaBoost en ligne | — | — | — | 1,935 | 2,29 | 4,34 (gradual) |
| Batch / périodique | 2,562 | 1,80 | 8,79 | 2,082 | 1,57 | 5,75 (gradual) |
| Gelé | 4,736 | 3,53 | 20,8 | 4,098 | 3,56 | 13,9 (gradual) |

**Scores bruts de tuning du run 2 (excès moyen sur 11 scénarios, 8 graines)** — tous relus dans `results/tune.json` et `logs/tune.log` (identiques ✔) :

| Régression | score | | Classification | score |
|---|---|---|---|---|
| null_reg | 1,0362 | | null_clf | 0,0689 |
| frozen_ridge (n0=250) | 1,0929 | | frozen_logit (n0=250) | 0,0792 |
| periodic_ridge (R=100) | 0,5894 | | periodic_logit (R=100) | 0,0402 |
| rolling_ridge (W=400) | 0,2551 | | rolling_logit (W=400) | 0,0193 |
| rolling_ridge_drift (δ=0,1) | 0,2910 | | rolling_logit_drift (δ=0,1) | 0,0195 |
| **rls (λ=0,995)** | **0,2270** | | **ekf_logit (λ=0,995)** | **0,0167** |
| kalman_rw (q=1e-4) | 0,2319 | | river_sgd_logit (lr=0,02) | 0,0181 |
| river_sgd_lin (lr=0,005) | 0,2975 | | ekf_bank_custom (δ=0,1) | 0,0179 |
| river_pa_reg (C=0,01) | 0,2866 | | sgd_logit_platt (lr=0,005) | 0,0185 |
| river_hoeffding_reg (gp=200) | 0,5271 | | river_pa_clf (C=0,01) | 0,0226 |
| river_arf_reg (gp=200) | 0,6703 | | ekf_reset_adwin (δ=0,1) | 0,0206 |
| rls_reset_adwin (δ=0,1) | 0,4413 | | river_hoeffding_clf (gp=200) | 0,0526 |
| rls_bank_custom (δ=0,1) | 0,2899 | | river_arf_clf (gp=200) | 0,0468 |
| | | | river_adaboost_clf (gp=200) | 0,0374 |
| | | | hoeffding_platt (lr=0,02) | 0,0408 |

Le modèle nul (ne rien apprendre) vaut ≈ 1,04 (R) et 0,069 (C) ; `rls` R le ramène à 0,227 : « compétence » (skill = 1 − excès/nul) ≈ 0,78 ; en C, `ekf_logit` ≈ 0,76.

### 8.4 Où ils s'accordent, où ils divergent, et pourquoi (probable)

**Accords (qualitatifs, robustes aux différences de banc)**
1. Le **refit glissant est dur à battre** : le meilleur en ligne n'est que 10–14 % mieux en tuning dans le run 2 (RLS 0,89 ; EKF 0,86) contre 12–15 % en held-out dans le run 1 (0,85 ; 0,88). Ordre de grandeur cohérent malgré des mondes différents.
2. **Les récursifs linéaires avec oubli (RLS, Kalman ; EKF logistique)** forment le peloton de tête.
3. **Arbres et forêts très en retrait** : 2,1–2,7 × (run 2) contre 2,5–5,2 × (run 1) ; l'état de ces modèles explose (run 1 : ×4–6 ; run 2 : voir §8.5).
4. **Gelé et batch/périodique** : 3–4,7 × pires que le rolling en tuning des deux runs.
5. **La banque de modèles coûte cher en suivi progressif** : `gradual` ≈ 2,8× (run 1) / 3,0× (run 2) en régression ; elle aide en classification (0,895 ; 0,925 en arith.).
6. **Le reset piloté par ADWIN n'aide pas** ; il est pire que le modèle nu (run 1 : 1,25 en held-out ; run 2 : 1,73 en tuning, 13,8 × sur false_drift).
7. **Optima souvent en bord de grille** dans les deux runs (SGD lin lr bas ; PA C bas ; batch/périodique période basse ; reset δ permissif ; arbres grace élevé).

**Divergences et causes probables**
- **Kalman** : 1,05 en held-out (run 1, q en bord de grille, bruit fixe) contre 0,91 en tuning (run 2, q intérieur, bruit adaptatif). Cause probable : q et estimation du bruit de mesure ; le run 1 le dit lui-même (« sous-exploré »).
- **SGD logistique** : plein d'ennuis sur `false_drift` dans le run 1 (2,39 ×, lr = 0,1 avec traits ×3) mais pas dans le run 2 (pire ratio 1,03 ; lr = 0,02, chocs plus doux, pas simultanés). Cause probable : learning rate et intensité du choc (INFERENCE ; non testée en croisant les deux réglages).
- **Reset** : très différent (1,25 vs 1,73) : dans le run 2 la nouvelle instance n'est pas réchauffée et le RLS de base n'a pas d'oubli.
- **Banque en classification** : le run 1 la teste sur SGD, le run 2 sur EKF : ratios arithmétiques 0,895 vs 0,925 ; en géométrique 0,833 vs 0,810. Pas de contradiction visible.
- **Méthode « transversale »** : le run 1 n'a pas trouvé de méthode commune aux deux pistes. Le run 2, dans son seul tuning, met **la famille moindres carrés récursifs / EKF** en tête sur les deux pistes (RLS 0,89 en R, EKF 0,86 en C, le meilleur des deux) : signal que l'absence de méthode commune dans le run 1 peut venir de l'absence d'un classifieur de type RLS. **Cette conclusion reste une hypothèse : elle n'est fondée que sur des graines de tuning, sans held-out, sans IC**, et le run 2 n'a pas franchi les portes du run 1 puisqu'il n'a pas de portes.
- **Fenêtre optimale du refit** : 150 (R) / 300 (C) dans le run 1 (SNR élevé) contre 400 dans les deux pistes du run 2 (SNR bas). Accord avec l'explication du rapport 04 §4.4.
- **Ampleur des gains** : 0,89 / 0,86 (run 2) sont des gains **de tuning** (biaisés à la baisse, car la sélection se fait sur ces graines) ; les ratios de tuning du run 1 (0,95 / 0,90 en arith.) sont plus modestes que ses ratios held-out en géométrique sur 8 scénarios (0,85 / 0,88) parce que la moyenne et le jeu de scénarios diffèrent. Ne pas comparer à la légère.
- **Les optimums ne sont « les mêmes » nulle part**, essentiellement parce que les grilles ne se recoupent pas et que le SNR diffère. Seule la grille de Kalman et celle de PA sont identiques dans les deux runs (Kalman : 1e-5 vs 1e-4 ; PA reg : même optimum 0,01).

### 8.5 Preuves supplémentaires apportées seulement par le run 2 (logs)
Trois logs de compatibilité de `pickle` (commit `29f65a2`, avant le tuning) — je les lis comme suit, les scripts qui ont *créé* les checkpoints n'étant pas dans la branche (donc la direction exacte est INFERENCE) :
- `pickle_compat_river026.log` (River 0.26.1) : `ekf_logit`, `river_arf_clf`, `river_hoeffding_clf`, `river_hoeffding_reg`, `river_sgd_lin`, `river_sgd_logit` : **tous LOAD_OK** (valeurs 0,1965 ; 0,4307 ; 0,2381 ; −3,041 ; −1,3816 ; 0,1944).
- `pickle_compat_river022.log` (River 0.22.0) : `ekf_logit` LOAD_OK (0,1965, **même valeur**) et `river_hoeffding_clf` LOAD_OK (0,2381) ; mais `river_arf_clf`, `river_hoeffding_reg`, `river_sgd_lin`, `river_sgd_logit` **LOAD_FAIL** (« No module named 'river._river_rust' »).
- `pickle_compat_old_to_new.log` : des checkpoints d'une ancienne version chargés sous 0.26.1 : `ht_clf` OK, mais `arf_clf` échoue (« No module named 'river.drift.adwin_c' »), `sgd_lin` et `sgd_logit` échouent (« Can't get attribute '__pyx_unpickle_VectorDict' »).
Conséquence (OBSERVED dans le log, sous réserve de la lecture ci-dessus) : **les checkpoints pickle de modèles River ne sont pas portables entre versions de River** ; les modèles numpy maison (`ekf_logit`) le sont. C'est précisément le point que le run 1 avait laissé en INFERENCE/UNKNOWN (rapport 06 : « une mise à jour de River peut silencieusement changer la mise en page »). Ce fait plaide pour un état sérialisé **explicite et versionné** pour les modèles retenus.
Le run 2 a aussi prévu (code écrit, non exécuté) : métadonnées de mise à jour *dans* l'état pickle (`state_version="olv1"`, `n_updates`, `last_label_t`, `last_update_t`), un contrôle positif de fuite `Leaky`, un test de sensibilité à l'ordre d'arrivée des étiquettes (par blocs de 10, mélangés), des expériences d'oubli F1–F4 (rétention d'instantanés, économies au réapprentissage, croissance d'état jusqu'à 20 000 pas, variance liée à la graine du modèle).

### 8.6 Ce qui manque au run 2 pour être exploitable
Liste précise, fichier par fichier (constaté par `git ls-tree` de la branche `-b`) :
1. **Résultats d'évaluation held-out absents.** `run_eval.py` prévoit 3 campagnes : `main` (28 modèles × 11 scénarios × 20 graines = 6 160 runs, configs tunées), `lowsnr` (10 graines, bruit 4,0), `default` (10 graines, configs par défaut non tunées). Le seul artefact est `logs/eval.log`, qui contient **une ligne** : « main 6160 ». Il n'y a ni `results/eval_main.json`, ni `eval_main.blocks.npy`, ni `eval_lowsnr*`, ni `eval_default*` : l'exécution a été lancée puis interrompue ou non commitée (INFERENCE ; le commit final est celui du tuning, 18:45:21).
2. **Résultats des autres expériences absents** : `results/replay.json` (écrit par `run_replay.py`, tests R1–R5), `results/forgetting.json` (écrit par `run_forgetting.py`, F1–F4), `results/summary_main.json` et `results/tables/*.md` (produits par `analyze.py`). Aucun n'existe.
3. **Aucun rapport** : pas de dossier `reports/013_online_learning/` sur cette branche ; pas de synthèse, pas de verdict, pas de bloc final.
4. **Aucun protocole ni critère de décision** : `analyze.py` calcule des « skills » (1 − excès/nul), des différences appariées avec IC bootstrap contre gelé/périodique/rolling, des tableaux d'adaptation et de récurrence (RRI), etc., mais **ne contient aucune porte de décision ni aucun seuil**. Rien n'est pré-enregistré (pas de `02_PROTOCOL` équivalent). Donc, même avec les résultats, le verdict n'aurait pas de règle antérieure aux données.
5. **Pas de README ni d'instructions** : seules `requirements.txt` (numpy 2.4.6, scipy 1.17.1, scikit-learn 1.9.1, river 0.26.1) et l'ordre implicite des scripts.
6. **Tuning non validé** : les scores sont sur les graines de tuning uniquement (biaisés vers le bas pour la config choisie), avec optimums en bord de grille pour au moins 10 modèles (SGD lin, PA reg, PA clf, hoeffding, ARF, reset, banque, périodique, gelé, sgd_logit_platt).
7. **Le scénario `missing_random` est plus dur que celui du run 1** (70 % perdues sur tout le run) et le SNR est très différent : les nombres du run 2 ne sont pas transposables tels quels au run 1.
8. **Des constats à corriger avant exécution complète** (mon analyse, non testés par exécution) : `Reset` sans réchauffement et base RLS λ = 1,0 (pénalise le reset) ; grilles de plusieurs modèles atteignant leur bord ; écart d'implémentation Kalman/RLS/PA avec le run 1 ; aucune graine de modèle variée dans l'évaluation (sauf F4).
9. **Ce qui existe et est utile** : un banc propre et rejouable (mon rejeu du tuning : écart exact 0), une liste de modèles plus large (EKF logistique, AdaBoost), des scénarios complémentaires (blackout, retards 50/200), les logs de compatibilité pickle.
Estimation de l'effort restant (mon analyse) : les 6 160 runs de la campagne `main` sont surtout coûteux à cause des ARF (environ 4 à 9 secondes par run d'ARF lors de mon test de fumée `run_smoke.py`, quelques dixièmes de seconde pour les modèles linéaires) ; l'ordre de grandeur est d'une vingtaine de minutes à une heure sur 4 cœurs (`?` non exécuté par moi, extrapolation). Le tuning a demandé 1 111,5 s (log).

### 8.7 Conclusion de la comparaison
Le run 2 **ne peut pas** corroborer ni infirmer le verdict du run 1 : il n'a pas de held-out. Son tuning suggère une **structure qualitative identique** (récursifs linéaires ≥ refit glissant ≫ arbres/gel/batch ; reset inutile ; banque utile seulement en classification) et une **hypothèse nouvelle** à tester : un classifieur EKF/logistique-bayésien avec oubli pourrait fournir la méthode « de même famille » sur les deux pistes.

---

## 9. Reproductibilité

### 9.1 Run 1
- **Dépendances** : Python 3.11.15 ; River 0.26.1 ; scikit-learn 1.9.1 ; numpy/scipy (versions exactes non notées dans les rapports du run 1 : `?`) ; j'ai utilisé numpy 2.4.6 (celle imposée par le run 2) et obtenu des sorties identiques sur 7 runs.
- **Commandes** (depuis `bench/online_learning_v1/py/`, avec `OMP_NUM_THREADS=1`) : `python run_tuning.py` (→ `../results/tuning_rows.json`, `tuned_config.json`) ; `python run_main.py` (→ `main.json`, 3 750 lignes) ; `LOWSNR=1 python run_main.py` (→ `main_lowsnr.json`, 600 lignes) ; `python run_determinism.py` (→ `determinism.json`) ; `python analyze.py` (→ `summary.json`, `tables.md`) ; `python analyze_lowsnr.py`.
- **Durée** : commits espacés de 15 minutes entre tuning et held-out (17:53 → 18:08 avec le run SNR bas) ; mes 7 runs témoins ont pris 3,2 s en tout (0,0 à 0,7 s chacun). Ma passe complète n'a pas terminé en 28 minutes sur un conteneur saturé : la durée totale du run 1 sur une machine libre n'est donc pas confirmée par moi (les horodatages de commits suggèrent ≈ 15 minutes, `?`).
- **Fourni** : code, configs gelées, résultats bruts, tables, journaux. **Manque** : fichier `requirements` ou README pour le run 1 ; versions numpy/scipy ; cible de lancement unique (pas de Makefile) ; les chemins de sortie sont relatifs (`../results/`), donc il faut lancer depuis `py/`.

### 9.2 Run 2
- **Dépendances** : `requirements.txt` (numpy 2.4.6, scipy 1.17.1, scikit-learn 1.9.1, river 0.26.1).
- **Commandes** (depuis `bench/online_learning_v1/`) : `python run_smoke.py` (test de fumée : je l'ai exécuté, 28 modèles, dernier ARF ~9 s) ; `python run_tune.py` (~1 111 s) ; `python run_eval.py [main|lowsnr|default]` ; `python run_replay.py` ; `python run_forgetting.py` ; `python analyze.py main` (la fonction `main(tag)` ne produit les tables détaillées que pour `tag == "main"`).
- **Fourni** : code, `results/tune.json`, `logs/tune.log`, logs pickle. **Manque** : tout le reste (voir §8.6).

---

## 10. Implications pratiques pour AurumShift (pistes « à adjuger plus tard », aucune compatibilité affirmée)

1. **Référence « simple d'abord »** : un refit glissant borné (fenêtre de l'ordre de 150–400 échantillons, selon le SNR) est une base solide, peu coûteuse, rejouable. À évaluer plus tard sur les données PIT réelles avec la même discipline d'arrivée des étiquettes.
2. **Défi incrémental candidat** : RLS avec oubli (état ≈ 841 octets, pur numpy) pour la régression ; à adjuger contre le vrai flux d'AurumShift. Piste de classification : SGD logistique + banque (run 1) ou EKF logistique (run 2), à départager sur données réelles.
3. **Ne pas investir dans arbres/forêts/ADWIN-bagging pour cet usage** à l'échelle testée (T = 4 000) : coût 2,6–5,2 ×, état non borné, latence plus haute.
4. **Garde-fou d'échelle** (détection de choc de variance ou de volatilité) avant tout apprenant SGD/BLR : piste de conception, non testée avec un garde-fou.
5. **Sérialisation d'état explicite et versionnée** pour les petits modèles (dictionnaire `{schéma, λ, P, w, dernière mise à jour}`) plutôt que `pickle` : plaide le run 2 (incompatibilités River observées) et le rapport 06 du run 1. Lien possible avec l'exigence PIT/provenance (mise à jour horodatée avec `last_label_t`, `last_update_t` comme dans le run 2) — à adjuger contre le stockage PostgreSQL réel.
6. **Banque de régimes** : seulement si une récurrence de régimes est démontrée sur données réelles (UNKNOWN).
7. **Coût de transaction et signal réel** : non traités ; les gains synthétiques ne se convertissent pas en performance de trading (mon analyse).

---

## 11. Questions ouvertes et suites recommandées (classées par valeur)

1. **Terminer le run 2** (valeur haute, coût faible) : lancer `run_eval.py main`, `run_replay.py`, `run_forgetting.py`, `analyze.py main` ; **écrire un protocole et des critères de décision avant** de regarder le held-out (par exemple en reprenant les portes (a)–(d) du run 1 : c'est ce qui manque le plus). Livrer des rapports.
2. **Tester l'hypothèse « famille commune RLS/EKF »** : ajouter un EKF logistique au banc du run 1 (mêmes 10 scénarios, mêmes portes) ou porter les portes du run 1 sur le banc du run 2. Vérifier si une seule méthode passe alors sur les deux pistes (changerait le verdict en `ONLINE_ADAPTATION_REFERENCE_SUPPORTED`).
3. **Re-tuner sans dépendre du scénario non linéaire** et élargir les grilles pour lever les bords (RLS λ = 0,98 et en dessous ; fenêtre de rolling en dessous de 150 ; Kalman avec bruit adaptatif ; SGD avec lr plus élevé/plus bas) ; mesurer si les 12–15 % de gain survivent.
4. **Croiser SNR et types de chocs** dans un seul banc (κ, σ, intensité du choc d'échelle) pour séparer « robustesse du réglage » et « capacité intrinsèque » (le rapport 04 §4.4 le note).
5. **Tester un garde-fou d'échelle** sur SGD/BLR/EKF avec `false_drift` de plusieurs intensités.
6. **Données réelles PIT** avec le même harnais (suite proposée par le rapport 09), en re-tunant le rolling par fenêtre.
7. **Heavy tails et autocorrélation** dans le générateur ; concepts partiellement corrélés (non orthogonaux) pour un ordre de grandeur plus réaliste du coût de l'immobilisme (le run 2 a des concepts non orthogonalisés : un début).
8. **Durcir le rejeu** : plusieurs graines et scénarios, multi-threads BLAS, autre plateforme/OS, sérialisation versionnée testée entre versions.
9. **Corriger les énoncés** : « 20–28 % à SNR bas » (préciser les exceptions) ; clarifier `BEST_INCREMENTAL_REFERENCE` ; documenter la correction du contrôle négatif.

---

## 12. Index des fichiers lus

### Run 1 — branche `origin/claude/online-learning-v1`
Rapports (`reports/013_online_learning/`) — tous lus intégralement :
- `00_EXECUTIVE_SUMMARY.md` — résumé, verdict, bloc final.
- `01_LANDSCAPE.md` — 12 familles, sources, attentes avant lancement.
- `02_PROTOCOL.md` — protocole pré-enregistré, portes (a)–(d), mapping des verdicts.
- `03_DRIFT_SCENARIOS.md` — définition des 10 scénarios.
- `04_RESULTS.md` — résultats held-out, portes par méthode, tableaux, SNR bas.
- `05_FORGETTING.md` — oubli, récurrence, adaptation, variance, état.
- `06_REPLAY_DETERMINISM.md` — rejeu, checkpoint, fuite, contrôle négatif.
- `07_OSS_COMPONENTS.md` — composants River, licences, versions.
- `08_FALSIFICATION.md` — 12 hypothèses et leur sort.
- `09_ADJUDICATION.md` — ADOPT/ADAPT/PARK/REJECT.
- `10_LIMITATIONS.md` — limites.
Code et résultats (`bench/online_learning_v1/`) :
- `py/scenarios.py` (lu en entier) — générateur des 10 scénarios ; `py/harness.py` (entier) — boucle prequentielle, régret, sondes ; `py/models.py` (entier) — modèles, grilles (`GRID`) ; `py/run_tuning.py`, `py/run_main.py`, `py/run_smoke.py`, `py/analyze.py`, `py/analyze_lowsnr.py`, `py/run_determinism.py` (tous entiers).
- `results/tuned_config.json` — configs gelées et scores de tuning ; `results/tuning.log`, `main.log`, `main_lowsnr.log`, `determinism.log` — journaux courts ; `results/tuning_rows.json` (1 680 lignes, analysé par script) ; `results/main.json` (3 750 lignes, analysé par script) ; `results/main_lowsnr.json` (600 lignes, analysé) ; `results/summary.json` (critères par méthode, analysé) ; `results/determinism.json` (25 lignes, analysé) ; `results/tables.md`, `tables_lowsnr.md`, `analyze.log` — tables (lus en partie, contenu identique à 04/05 ; `analyze.log` : début seulement).
Autres : `claude.md`, `SYNTHESE_LANES.md` (lignes 43, 55, 175–190, 241, 286–288), `analyses/LANE_004_pit_safe_evidence_replay.md` (début, pour le format), PR #14 via API GitHub (métadonnées).

### Run 2 — branche `origin/claude/online-learning-v1-b`
- `bench/online_learning_v1/requirements.txt` — versions figées ; `run_smoke.py`, `run_tune.py`, `run_eval.py`, `run_replay.py`, `run_forgetting.py`, `replay_child.py`, `pickle_compat_child.py`, `analyze.py` — scripts (tous lus en entier).
- `src/streams.py`, `src/harness.py`, `src/models.py`, `src/registry.py`, `src/runner.py` — banc (tous lus en entier).
- `results/tune.json` — 76 configurations, meilleurs paramètres, scores par scénario (analysé par script).
- `logs/tune.log`, `logs/eval.log` (une ligne), `logs/pickle_compat_old_to_new.log`, `pickle_compat_river022.log`, `pickle_compat_river026.log` — journaux.
- **Non lu / inexistant** : aucun rapport `.md`, aucun README, aucun résultat d'évaluation, `replay.json`, `forgetting.json` (n'existent pas dans la branche).

### Ce que j'ai exécuté moi-même (hors dépôt, dans le dossier temporaire de session)
- Rejeu de 7 runs du run 1 (égalité bit à bit avec `main.json`) ; tentative de passe complète de `run_main.py` du run 1, interrompue (voir §6.1) ; test de fumée du run 2 ; recalcul de 4 scores de tuning du run 2 (égalité exacte) ; recalculs statistiques ponctuels (ratios, bootstrap, comparaisons de tuning).
