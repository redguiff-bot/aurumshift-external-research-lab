# LANE 012 — Calibration d'incertitude et abstention : analyse approfondie des deux runs (PR #19 et PR #24)

> Document d'analyse écrit pour Jean-François. Recherche externe uniquement : aucun code privé AurumShift n'a été lu, aucune compatibilité avec AurumShift n'est affirmée.
> Convention de lecture : « le rapport dit » = affirmation lue dans un rapport `.md` de la lane ; « vérifié » = recalculé par moi à partir des CSV bruts (ou par relecture du code) ; les marques **✔ vérifié / ✘ écart / ? non vérifiable** sont utilisées dans les tableaux de vérification (sections 6 et 7).
> Les termes techniques sont expliqués à leur première apparition (et récapitulés dans le petit glossaire ci-dessous, pour que tu n'aies pas à chercher).

## Glossaire express (à lire d'abord)

| Terme | Explication simple |
|---|---|
| **Branche / PR (pull request)** | Une branche est une « copie de travail » du dépôt où une personne (ici, un agent Claude) ajoute des fichiers sans toucher à la version principale. Une PR est la demande officielle de fusionner cette copie dans la version principale ; on peut la lire et la discuter avant. Ici : PR #19 = run 1, PR #24 = run 2. |
| **Run** | Une exécution complète de l'étude. Ici, la même consigne a été exécutée deux fois, indépendamment, par deux sessions différentes. |
| **Modèle de classification / probabilité** | Un programme qui, pour chaque situation, annonce « probabilité que le prix monte = 0,8 ». C'est sa *confiance*. |
| **Calibration** | Une confiance est *calibrée* si, parmi tous les cas où le modèle dit « 80 % », il a raison environ 80 % du temps. Un modèle « sûr de lui à tort » est mal calibré (sur-confiant). |
| **ECE (Expected Calibration Error)** | Mesure de mauvaise calibration : l'écart moyen entre la confiance annoncée et le taux de réussite réel. 0 = parfait ; 0,02 = très bon ; 0,10 et plus = franchement mauvais. Attention : les deux runs ne calculent pas l'ECE de la même façon (voir section 8). |
| **Brier / log-loss** | Deux scores de qualité des probabilités (plus bas = mieux). Le Brier est l'erreur quadratique moyenne ; la log-loss punit très fort les erreurs faites avec beaucoup d'assurance. |
| **Platt, température, bêta, isotonique, binning bayésien** | Cinq « recettes de recalibrage » qui transforment la confiance brute d'un modèle en une confiance plus honnête. Platt = une droite sur le logit (2 paramètres) ; température = un seul paramètre qui « adoucit » la confiance ; bêta = variante à 3 paramètres ; isotonique = courbe en escalier libre (beaucoup de paramètres) ; binning bayésien = moyennes par tranches. |
| **Fausse confiance (FCR / CWM)** | Part des décisions où le modèle est à la fois très sûr de lui *et* faux. Les deux runs la définissent différemment (voir section 8). |
| **Abstention / HOLD** | Ne pas agir quand on n'est pas assez sûr. En trading : rester à plat (HOLD) au lieu d'acheter/vendre. |
| **Risque sélectif / couverture** | Couverture = part des cas où on agit. Risque sélectif = taux d'erreur *sur ces cas seulement*. Une bonne abstention fait baisser le risque sélectif. |
| **Prédiction conforme (conformal prediction)** | Méthode qui, au lieu d'une seule réponse, fournit un intervalle (ou un ensemble de réponses possibles) avec une garantie du type « contient la vérité 80 % du temps ». La garantie n'est valable que si les données sont « échangeables » (l'ordre ne compte pas). |
| **Split conformal / rolling / pondéré / ACI** | Variantes : *split* = calibrée une fois ; *rolling* = sur une fenêtre glissante récente ; *pondéré* = les données récentes pèsent plus ; *ACI (Adaptive Conformal Inference)* = ajuste le niveau visé en continu selon les erreurs constatées. |
| **Couverture marginale vs conditionnelle** | Marginale = moyenne sur l'ensemble du temps. Conditionnelle = dans chaque sous-situation (par exemple, périodes de forte volatilité). La garantie éventuelle est marginale seulement. |
| **Dérive / choc de distribution (shift)** | Le monde change après l'entraînement du modèle (volatilité qui saute, régime de marché qui bascule, capteur qui se fige...). |
| **Lookahead / fuite / PIT (point-in-time)** | Utiliser sans le vouloir une information qui n'était pas encore disponible à l'instant de la décision. « PIT-safe » = on n'utilise que ce qui était connu à l'heure dite. |
| **Délai de maturité des étiquettes (H)** | Le résultat d'une décision n'est connu que H pas de temps plus tard. Un recalibrage « en ligne » ne peut donc utiliser que les résultats *déjà mûrs*. |
| **Graine (seed)** | Nombre qui fixe le hasard d'une simulation. 20 graines = 20 mondes simulés différents ; on moyenne. |
| **Held-out** | Données mises de côté, non utilisées pour choisir quoi que ce soit, servant au score final. |
| **ELEC2** | Jeu de données public réel : prix de l'électricité en Nouvelle-Galles du Sud (Australie), 45 312 demi-heures, connu pour dériver dans le temps. Ce n'est PAS un problème financier d'achat/vente d'actif. |
| **AUROC** | Mesure (0,5 = hasard, 1 = parfait) de la capacité d'un signal à séparer deux groupes. |
| **ADOPT / ADAPT / PARK / REJECT** | Verdicts du laboratoire : ADOPT = à retenir tel quel comme référence ; ADAPT = utile mais à adapter/tester ; PARK = mis de côté, pas assez de preuves ; REJECT = écarté. |
| **PROVEN / OBSERVED / DOCUMENTED_CLAIM / INFERENCE / UNKNOWN** | Étiquettes de preuve du dépôt : démontré / mesuré ici / affirmé par la littérature sans vérification / déduction / inconnu. |

---

## 0. Fiche d'identité

| Élément | Run 1 (PR #19) | Run 2 (PR #24) |
|---|---|---|
| Branche | `origin/claude/uncertainty-calibration-v1` | `origin/claude/uncertainty-calibration-v1-b` |
| Commit de tête de la PR | `40a97212e800c778d360120e570c6cd4284f86fe` (`refs/pull/19/head`, vérifié par `git ls-remote`) | `23eacc27ed3c4ad642ae6eebac5de7099321fdc0` (`refs/pull/24/head`, vérifié) |
| Commits propres à la branche | 2 : `73a1650` « WIP 012 … library, static/shift/taxonomy experiments, methods+protocol » (2026-09-29 18:47:55 UTC) puis `40a9721` « Report 012 … (final) » (2026-09-29 18:56:49 UTC) | 1 seul : `23eacc2` « 012: uncertainty calibration and abstention study (external research) » (2026-09-29 19:24:40 UTC) |
| Base commune | `1a449df` (fusion de la PR #6 « risk-capacity-turnover ») — vérifié par `git merge-base` | idem |
| Nombre de fichiers (rapports + `bench/uncertainty_v1/`) | 69 (11 rapports + 1 README + 1 données + 7 scripts + 49 fichiers de résultats) | 169 (11 rapports + README + `frozen_config.json` + 13 scripts/`.sh` + 1 test + ~140 fichiers de résultats, dont tables, figures, journaux) |
| Taille des fichiers de ces dossiers | 5 992 964 octets (dont 2 998 235 pour `data/elec2.csv`, une copie du jeu ELEC2 embarquée dans le dépôt) | 23 325 766 octets (le run 2 ne redistribue aucune donnée publique : elles sont téléchargées à l'exécution) |
| Lignes ajoutées vs base | +154 216 (69 fichiers) | +82 947 (169 fichiers) |
| Durée d'exécution annoncée / observée | README : « ~10 min sur 4 cœurs » (non vérifié en entier ; mes re-exécutions partielles ci-dessous prennent ~30 s chacune pour la partie statique et la taxonomie) | journaux : ~73 s par graine pour la partie statique (`results/logs/static_hold_0-6.log`) ; ~115 s/graine pour l'en ligne ; ~437 s pour 6 graines de conformal |
| Tests automatisés | aucun test unitaire ; un `assert` interne (`pit_ok`) | `tests/test_no_lookahead.py` : 4 tests ; **je les ai exécutés : 4 PASS en 6 s** |
| **Verdict final** | `LIMITED_UNCERTAINTY_METHODS_SUPPORTED` | `LIMITED_UNCERTAINTY_METHODS_SUPPORTED` |
| Force du verdict | Moyenne à modérée : preuves synthétiques nombreuses (20 graines pour statique/choc/taxonomie, 8 pour en ligne/conformal) + un seul jeu réel dérivant (ELEC2, 1 réalisation, sans intervalle de confiance) | Moyenne à modérée : 12 graines de test + 4 graines de réglage, ELEC2 (33 312 lignes de test) + 3 jeux publics « iid » ; verdict identique mais nuances différentes (section 8) |
| Rapports lus | 00 à 10 (11 fichiers) intégralement | 00 à 10 (11 fichiers) intégralement |

Ce qu'il faut retenir : **deux runs indépendants, deux fois le même verdict « limité »**. Les grands constats convergent ; les écarts sont dus à des conceptions de simulateur différentes, pas à des contradictions de fond (détail en section 8).

**Correspondance des noms de fichiers.** Les deux branches utilisent la même numérotation de rapports (00 à 10 : synthèse, méthodes, protocole, calibration statique, calibration en ligne, abstention, conformal, chocs, modes de défaillance, adjudication, limites) et le même dossier `bench/uncertainty_v1/`, mais **le contenu des scripts est différent** (run 1 : `ulib.py` + 5 scripts `exp_*` ; run 2 : 12 modules Python séparés). Ce sont donc bien deux implémentations indépendantes.

---

## 1. Mission et question posée

### 1.1 La question, reformulée simplement

Un système de trading automatique (AurumShift) produit des « confiances » (« je pense à 70 % que ça monte »). Trois problèmes concrets se posent :

1. **Ces confiances sont-elles honnêtes ?** Si le système dit 70 %, a-t-il raison 7 fois sur 10 ? (Q1 : calibration.)
2. **Quand la confiance est faible, vaut-il mieux s'abstenir ?** Et cela évite-t-il des mauvaises décisions sans se priver de trop de bonnes ? (Q2 : abstention.)
3. **Quand le marché change (volatilité qui explose, régime qui bascule, données manquantes ou figées, autre place de marché), la confiance reste-t-elle honnête ?** Et peut-on le détecter ? (Q3 : robustesse au choc.)
4. **Peut-on distinguer *pourquoi* on est incertain** : pas de signal du tout (NO_SIGNAL), trou de données (DATA_GAP), modèle qui manque d'exemples (MODEL_UNCERTAINTY), ou situation inconnue (OOD = out-of-distribution, « hors du domaine d'entraînement ») ? (Q4 : taxonomie des causes.)

S'y ajoutent deux sujets transverses : la **recalibration en ligne** (peut-on remettre la confiance à niveau au fil du temps, sans tricher avec le futur ?) et la **prédiction conforme** (les intervalles « garantis » le sont-ils vraiment sur des séries temporelles qui dérivent ?).

Le rapport de run 2 (02_PROTOCOL / 09_ADJUDICATION) désigne ces questions Q1 à Q4 ; le run 1 fait de même (09_ADJUDICATION « Answers to the four questions »). Le texte exact de la consigne d'origine n'est pas dans les fichiers lus : je le reconstitue à partir des deux rapports (**consigne non lue directement**, `?`).

### 1.2 Contraintes du dépôt (`claude.md`, lu intégralement pour les parties citées)

* **Doctrine REUSE → ADAPT → WRAP → COMPOSE → CUSTOM LAST** : préférer réutiliser un composant externe existant ; n'écrire du code sur mesure qu'en dernier recours. Points d'attention pour cette lane : les deux runs ont **réimplémenté** les méthodes (« CUSTOM ») au lieu d'utiliser MAPIE, netcal, crepes, etc. Run 1 le dit explicitement (`01_METHODS.md` : « re-implemented in ~350 lines of numpy/scikit-learn so label-delay handling and lookahead are auditable » ; MAPIE seulement listé via `pip index`, version 1.5.0, OBSERVED ; **aucune comparaison croisée avec MAPIE/netcal**). Run 2 n'utilise pas non plus de bibliothèque spécialisée. La doctrine de réutilisation est donc **respectée en intention (les méthodes sont des recettes standard) mais pas en pratique (aucune bibliothèque testée)**.
* **Étiquettes de preuve** : PROVEN / OBSERVED / DOCUMENTED_CLAIM / INFERENCE / UNKNOWN. Les deux runs les emploient. Point important : **toutes les citations de littérature sont DOCUMENTED_CLAIM non relues** (run 1 : « no paper was opened in this run » ; run 2 : « for arXiv items the *title* was confirmed through the arXiv API… the papers themselves were not read in full »).
* **Ne pas fabriquer de résultats de benchmark** ; **ne pas se fier aux README** ; **cloner/exécuter quand c'est possible** (fait : les deux runs exécutent leurs propres expériences).
* **Contraintes AurumShift à respecter dans la lecture** : recherche seule / papier seul (pas de capital réel), PIT / provenance / no-lookahead critiques, événementiel/intraday (pas HFT), « une source faisant autorité par sujet », **« l'absence de preuve n'est pas une preuve négative »**, coûts de marché réalistes, faible charge pour l'opérateur, reproductibilité, complexité d'infrastructure à justifier.
* **Frontière** : ne jamais affirmer qu'un candidat est compatible avec AurumShift à partir de ce dépôt ; le résultat est un verdict ADOPT/ADAPT/PARK/REJECT *externe*. L'adjudication finale se fait plus tard contre le vrai dépôt privé. **Je respecte cette frontière dans toute la section 10.**

---

## 2. Méthode

### 2.1 Run 1 (PR #19)

**Données et univers (protocole `02_PROTOCOL.md`).**

| Jeu | Contenu | Rôle |
|---|---|---|
| **S — synthétique** | 8 variables AR(1) (φ = 0,7 ; φ = 0 pour le témoin « échangeable »), étiquette binaire ~ Bernoulli(σ(w·x[:4] + 0,7·x0·x1)), précision de Bayes ≈ 0,71 ; la région `x7 > 1` est du **bruit pur** (vraie probabilité 0,5). 20 graines (8 pour l'en ligne et le conformal ; 20 pour choc et taxonomie), chaque graine = un monde neuf. | Vérité de probabilité connue → on peut mesurer l'écart à la vérité |
| **E — ELEC2** | OpenML `electricity` v1, 45 312 demi-heures, 1996-98, **reformulé en prévision** (features passées à t → étiquette à t+1) | contrôle réel non stationnaire |
| **B — breast cancer** (sklearn) | 569 lignes, échangeable | petit échantillon |
| **H — California housing** (sklearn) | régression, iid vs décalage volontaire sur le revenu médian | validité des intervalles conformal |

**Découpages (jamais mélangés).**

* Synthétique : entraînement [0:4000] | calibration [4000:7000] | validation [7000:10000] | test (held-out) [10000:16000], chronologique. Les chocs sont appliqués **au bloc test uniquement**.
* ELEC2 (après 48 lignes d'échauffement) : entraînement 0–9000 | calibration 9000–13500 | validation 13500–18000 | test 18000–fin en 6 tronçons.
* Breast cancer : découpage extérieur 65/35 stratifié ; intérieur 40 % entraînement / 30 % calibration / 30 % validation ; 20 graines.
* En ligne : le modèle de base est figé après entraînement ; seuls les calibrateurs évoluent dans le flux.

**Protocole et gel.** `02_PROTOCOL.md` est intitulé « declared before looking at the final numbers » (« déclaré avant de regarder les chiffres finaux »). **Ce que j'ai vérifié : le fichier de protocole du commit WIP `73a1650` est identique au fichier final (aucune différence dans `git diff 73a1650 40a9721 -- 02_PROTOCOL.md`), MAIS ce même commit WIP contient déjà les CSV de résultats des expériences statique, choc et taxonomie** (`static_raw.csv`, `shift_cal.csv`, `taxonomy_raw.csv`…, tous **inchangés** dans le commit final). Autrement dit, **rien dans l'historique Git ne permet de prouver que les critères ont été écrits avant les chiffres** ; le protocole et les résultats arrivent dans le même commit. Le texte de protocole peut très bien avoir été rédigé d'abord, mais c'est `?` (non vérifiable). Seule l'expérience en ligne a été refaite après une correction de bug (voir section 6).

**Réglage des hyper-paramètres.** Presque rien n'est réglé : τ = 0,6 est *dérivé* d'un modèle de coût (pas réglé) ; les fenêtres (W = 1000, 2000 pour ELEC2 ; refit toutes les 250 étapes ; SGD lr = 0,02 ; ACI γ = 0,005 ; poids λ = 0,998) sont **fixées à l'avance sans tuning** (`01_METHODS.md` : « fixed ad-hoc weights, no TV-distance tuning »). Il n'y a pas de séparation « réglage / test » à proprement parler pour ces valeurs — d'où l'absence de risque de sur-réglage, mais aussi l'absence de garantie qu'elles soient bonnes.

**Graines.** Chaque expérience utilise des graines fixes (`default_rng(1000+s)`, `2000+s`, `5000+s`, `7000+s`, `9000+s`…). **Vérifié : re-exécuter `exp_static.py` et `exp_taxonomy.py` sur cette machine redonne des fichiers CSV octet pour octet identiques** (voir section 9).

**Simulateurs de chocs (exp_shift.py, lu en entier).**

| Choc | Définition exacte dans le code |
|---|---|
| `vol_jump` | features ×1,5 **et** rapport signal/bruit ×0,35 (`true_p(x, W, snr=0.35)`) |
| `regime_transition` | signes de deux coefficients inversés (P(y\|x) change, les features paraissent identiques) — appliqué sur **tout** le bloc test (pas de transition progressive) |
| `feature_shift` | +1,5 sur 4 features **et l'étiquette est recalculée à partir des features décalées** (`p = true_p(xo, W)`) : c'est un vrai décalage de covariables, la relation P(y\|x observé) est inchangée |
| `missing_features` | chaque feature NaN avec probabilité 0,3 (remplacée par la moyenne d'entraînement) ; la vérité vient des features complètes |
| `stale_features` | 40 % du temps, les 4 premières features sont figées à leur dernière valeur (arrêts de 10 à 40 pas) |
| `venue_change` | entrées = 0,7·x + 0,5 + bruit N(0, 0,5²) ; vérité issue du vrai x |

**Modèles de base.** Régression logistique (LR), Bayes naïf gaussien (GNB), HistGradientBoosting (HGB : 300 itérations, pas d'arrêt précoce — **volontairement sur-confiant**). Ensemble d'incertitude : 8 HGB peu profonds (80 itérations, profondeur 3) sur rééchantillonnages bootstrap.

**Règles de décision.** `BUY si p ≥ τ, SELL si p ≤ 1−τ, sinon HOLD`. Gain +1 si juste, −1 si faux, coût c = 0,2 par transaction ⇒ τ* = (1+c)/2 = **0,6** (dérivation : espérance d'un trade à confiance c = c − (1−c) − 0,2 = 2c − 1,2 ≥ 0 ⇔ c ≥ 0,6 ; je l'ai revérifiée, elle est exacte **si les probabilités sont calibrées**).

**Critères de décision pré-déclarés (seuils exacts, `02_PROTOCOL.md`).**

| Critère | Seuil exact |
|---|---|
| Calibré | ECE top-label ≤ 0,03 sur le test synthétique (n = 6000) **et** meilleur que le brut sur ECE ou log-loss (ou brut déjà ≤ 0,03 : « pas de dégât ») |
| La calibration survit à un choc | ECE_choc ≤ 0,05 **et** FCR ≤ 1,5 × FCR_iid (+ plancher 0,01) |
| Fausse confiance (FCR) | P(faux ∧ confiance ≥ 0,8) sur toutes les lignes ; aussi P(faux \| conf ≥ 0,8) et une « pénalité de faux confiant » moyenne(1[agit ∧ faux]·(2·conf−1)) |
| L'abstention aide | risque sélectif < risque de l'abstention au hasard **et** utilité (±1, coût 0,2) ≥ utilité « tout trader » **et** ≥ 50 % des bonnes décisions conservées au point de fonctionnement |
| Recalibration en ligne supportée | sous dérive, la variante PIT-safe bat le statique sur l'ECE du pire tronçon d'au moins 0,02 (moyenne sur les graines, borne basse de l'IC ≥ 0,02) **sans** que le turnover de décision dépasse de plus de 20 % (relatif) celui du modèle brut ; résultats éloignés des variantes qui trichent |
| Conformal supporté dans un cadre | couverture moyenne à ±0,03 de 1−α **et** ≤ 10 % des fenêtres de 500 pas sous 1−α−0,05 |
| Q4 | rappel par classe ≥ 0,7 pour chacune des 4 causes (labels définis par le générateur : borne haute) |
| Barème de verdict | `UNCERTAINTY_ABSTENTION_REFERENCE_SUPPORTED` : statique + en ligne + abstention + conformal (au moins une méthode valide hors iid) supportés **et** calibration survivant à la plupart des chocs ; `LIMITED_...` : certains supportés avec limites nommées ; `NO_ROBUST_...` : aucun ; `STUDY_INCONCLUSIVE` |

**Statistiques.** Moyenne sur les graines ± 1,96·écart-type/√n (intervalle « de type t » approximé par la loi normale). Avec 8 graines, l'IC est un peu optimiste (le vrai multiplicateur t à 7 degrés de liberté est ≈ 2,36, non 1,96 — **INFERENCE** de ma part ; le rapport reconnaît « approximate »). ELEC2 : une seule réalisation, donc **aucun IC**.

**Contre-mesures contre la fuite.** `run_online` impose que les calibrateurs n'utilisent que des étiquettes `y_j` avec `j + h ≤ t`, avec h = 10 pas (synthétique), 1 ou 48 demi-heures (ELEC2). Deux variantes **délibérément tricheuses** (`leak_block` : calibrée sur le bloc même qu'elle prédit ; `leak_global` : calibrée sur tout le futur) servent d'audit. J'ai relu le code : le booléen `pit_ok` est calculé par `audit_ok &= (hi - 1 + h <= s)` à partir des **mêmes variables** que celles qui servent à découper les données — c'est une vérification arithmétique de cohérence interne, pas un test de perturbation indépendant (voir critique, section 7).

### 2.2 Run 2 (PR #24)

**Monde synthétique (`worlds.py`, lu en entier).**

* Classes : 0 = DOWN (SELL), 1 = FLAT (HOLD), 2 = UP (BUY) — **trois classes**, ce qui rapproche du vrai problème BUY/SELL/HOLD (le run 1 est binaire).
* Rendement latent r = w·x + σ_t·ε ; y = UP si r > 0,6, DOWN si r < −0,6, sinon FLAT. Taux de base ≈ 27/46/27 %.
* Features x ∈ R⁶ en AR(1) avec ρ = 0,7 ; volatilité σ_t pilotée par une chaîne de Markov cachée à 2 états (0,9 / 1,6, persistance 0,985) → **volatilité en grappes (non échangeable)** ; 1 % de lignes « cluster rare » avec une relation inversée et des features décalées (~40 exemples vus à l'entraînement).
* Postérieure oracle exacte (permet de savoir quelles lignes sont vraiment « sans signal »).
* Chronologie par graine : train 4000 → calibration 3000 → validation 3000 → test 4500 (début du choc à l'étape 1500 du test ; avant = référence dans-la-distribution, après = 3000 étapes).
* Utilité : trade juste +1, trade dans le mauvais sens −1, trade quand le marché est FLAT −0,3, HOLD 0. « Ce gain est un jouet ; les conclusions sur l'abstention en dépendent » (`02_PROTOCOL.md`).
* 8 scénarios : `none`, `vol_jump` (σ × (1+1,5·m)), `regime_transition` (rotation de 120°·m de la relation sur 1000 pas), `feature_shift` (features observées +1,5·m sur 4 dims et × (1+0,3·m) **alors que les étiquettes viennent des features d'origine** : P(y|x vrai) inchangée mais le modèle voit des entrées corrompues), `missing_features` (40 %·m de NaN sur 3 features, imputation par la moyenne), `stale_features` (3 features figées par séquences de 10·m pas), `venue_change` (x observé = (1−0,3m)x + 0,5m + 0,8m·bruit), `rare_cluster` (fréquence 1 % → 1+7m %) ; plus un témoin `iid_control` (conformal seulement).

**Modèles.** `lr` : régression logistique multinomiale sur [x, x²] (bien spécifiée, bien calibrée d'origine) ; `gbm` : HistGradientBoosting 100 itérations, taux 0,3, pas d'arrêt précoce (sur-confiant à dessein). Ensemble bootstrap de 8 membres (5 pour statique/abstention, 2 pour en ligne) pour l'information mutuelle « épistémique ».

**Découpages et gel.**

| Découpage | Graines | Ampleur du choc | Usage |
|---|---|---|---|
| train | toutes, 4000 premières lignes | — | modèle de base |
| calibration | 3000 suivantes | — | calibrateurs, scores conformal de calibration |
| validation | 3000 suivantes | — | τ d'abstention / budgets ; historique pour l'en ligne |
| réglage (tuning) | graines 100–103 | 0,6 | W, demi-vie, paramètres conformal, seuils de diagnostic, choix du meilleur calibrateur |
| test (held-out) | graines 0–11 | 1,0 | chiffres rapportés, une exécution par composante |

`frozen_config.json` (lu) : `H_label_maturity = 10`, `R_refit_period = 50`, `window_W = 600`, `decay_halflife = 400`, `best_simple_static = temperature`, `conformal: alpha_reg 0.1, alpha_clf 0.2, window_W 300, decay_halflife 150, aci_gamma 0.01`, `diagnosis: q_ood 0.99, q_mi 0.95, tau_no_signal 0.5`. Le rapport dit que ce fichier a été écrit avant les exécutions test de l'en ligne, du conformal et du diagnostic. **Je ne peux pas le confirmer par l'historique** : la branche ne compte qu'un seul commit (`23eacc2`) qui contient tout. Les journaux (`results/logs/*.log`) ne portent pas d'horodatage. → `?`.

**Divulgations de processus reconnues dans `02_PROTOCOL.md`** : (i) un bug d'indexation de masque dans `regime_transition` corrigé avant toute sortie test ; (ii) taille du GBM réduite (150 → 100 itérations) et ensembles statiques à 5 membres pour le temps de calcul, avant tout run test ; (iii) **le banc d'abstention (budgets 10/25/40 %) a été conçu après avoir regardé les tables test statique et en ligne**, puis exécuté une fois sur les mêmes graines test sans réglage ; (iv) 4 graines de réglage, 12 de test, IC de type t optimistes car les scénarios partagent les mêmes mondes.

**Maturité des étiquettes et anti-fuite.** La ligne s a son étiquette disponible à s + H (H = 10). À l'instant absolu t, un recalibrateur en ligne n'utilise que les lignes s ≤ t − H, refit toutes les R = 50 étapes. **Test anti-fuite** (`tests/test_no_lookahead.py`, lu et **exécuté : 4 PASS**) : il corrompt toutes les étiquettes non mûres à un instant de coupe et vérifie que les probabilités **déjà servies avant** sont bit-à-bit identiques ; il vérifie aussi que les variantes tricheuses (`leak_h0` : H = 1 ; `leak_peek` : voit le bloc suivant) sont bien détectées comme fuyantes ; même test pour les flux conformal. C'est un test de **perturbation empirique**, beaucoup plus probant que l'`assert` arithmétique du run 1.

**Métriques.** Brier multiclasse (somme des carrés sur les 3 classes, donc ≈ 2 × le Brier binaire — **à ne pas comparer directement** aux Brier du run 1), log-loss, **ECE à 10 classes de largeur égale** (variante à masse égale stockée), tables de fiabilité, couverture, risque sélectif / AURC, **FCR = P(faux | conf ≥ 0,6)** et **CWM (confident-wrong mass) = P(conf ≥ 0,6 ∧ faux)** (le hasard vaut 1/3, donc 0,6 = « clairement confiant »), dérive de calibration = ECE(après le choc) − ECE(avant), ECE glissant par fenêtres de 500 pas, turnover de décision. Plancher d'ECE : ≈ 0,04 à n = 500 avec 10 classes ; les différences < 0,01 ne sont pas interprétées.

**Données publiques (`run_public.py`, lu).** ELEC2 (OpenML `electricity` v1) en **nowcast** de la ligne courante (X de la ligne t → étiquette UP/DOWN de la même ligne t ; **pas de reformulation en prévision** comme dans le run 1) ; lignes 0–6000 entraînement, 6000–9000 calibration, 9000–12000 validation, 12000–fin test (33 312 lignes, 16 blocs de 2000 pour les tableaux par bloc) ; W et demi-vie choisis sur validation parmi {500, 1000, 2000} / {250, 500, 1000} (choix : W = 2000 et demi-vie 1000, **au bord de la grille**). credit-g et breast-cancer : 20 re-découpages aléatoires 40/20/20/20. California housing : HGB régresseur, découpage iid vs découpage de décalage de covariables (entraînement/calibration sur les 80 % de revenu médian les plus bas, test sur le quintile supérieur).

**Critères de décision** : le run 2 **ne déclare pas de seuils numériques de succès** du type « ECE ≤ 0,03 » avant les résultats ; il présente des résultats et des verdicts par candidat (ADOPT/ADAPT/PARK/REJECT) fondés sur des comparaisons et la lecture des tableaux. C'est une différence importante avec le run 1 (section 8, point « critères »). Les seuils utilisés en pratique : intervalle de confiance apparié excluant zéro pour les gains de calibration ; écarts < 0,01 d'ECE considérés comme du bruit ; étiquetage de la recalibration en ligne comme « recouvre ≈ 80–100 % de l'excès d'ECE » (non défini plus précisément).

**Sélection sur graines de réglage** (ce que j'ai recalculé à partir de `static_tune_*` et `tune_*_online.csv`) : voir section 6 ; en résumé la température est bien le meilleur calibrateur sur les graines de réglage (GBM : ECE 0,046, Brier 0,596 contre Platt 0,155/0,671, brut 0,276/0,728), mais le choix W = 600 / demi-vie 400 **n'est pas** le meilleur sur les graines de réglage pour l'ECE (W = 300 : 0,0174 ; demi-vie 150 : 0,0165 ; contre 0,0179 et 0,0196 pour les valeurs retenues, GBM, température, scénarios avec choc).

---

## 3. Résultats détaillés

Tous les chiffres ci-dessous viennent des rapports lus ; je signale (✔) quand je les ai recalculés à partir des CSV bruts. Le chemin entre parenthèses est le fichier source du chiffre. « ± » = demi-largeur d'un intervalle de confiance à 95 % sur les graines, tel que le rapport le calcule.

### 3.A — RUN 1 (PR #19)

#### 3.A.0 Synthèse exécutive du run 1 (`reports/012_uncertainty_calibration/00_EXECUTIVE_SUMMARY.md`)

Sept constats numérotés : (1) la calibration marche en régime stationnaire (GBM sur-confiant : ECE 0,118, fausse confiance 0,119 → Platt/température/bêta ≈ 0,022 ; oracle 0,017) ; (2) elle ne survit pas au choc (2 chocs sur 6 seulement) ; sur ELEC2 un calibrateur ajusté sur la fenêtre de calibration a *empiré* l'ECE de la régression logistique (0,103 → 0,15–0,17) ; (3) un modèle peut rester confiant en ayant tort (AUROC de la « faible confiance » 0,39 / 0,43 ; fausse confiance × 2 à × 4,5) ; (4) l'abstention aide dans certaines limites (τ = 0,6 : 69 % des lignes tradées, risque sélectif 0,318 → 0,256, 45 % des mauvaises décisions évitées, 75 % des bonnes conservées ; pas d'aide sous choc de régime : 0,486 → 0,482) ; (5) la recalibration en ligne aide si et seulement si elle est PIT-safe (ECE régime abrupt 0,100 → 0,017 ; pire tronçon 0,182 → 0,104) ; (6) le conformal *split* est invalide sous dérive (0,72–0,73 au lieu de 0,80), ACI et pondéré tiennent la couverture marginale mais **couverture marginale ≠ fiabilité de la décision** (précision des cas « singleton » 0,65–0,73) ; (7) séparation des causes à moitié réussie (DATA_GAP 0,97 et OOD 0,98 ; NO_SIGNAL 0,36 ; MODEL_UNCERTAINTY 0,15).

**Vérification.** Les valeurs 1, 2, 4, 5, 6, 7 sont confirmées par recalcul (voir tableaux ci-dessous). **Un écart de formulation (✘ mineur) sur le constat 3** : le résumé écrit « under feature shift and vol jump … false-confidence rate rises 2–4.5× over iid (0.024 → 0.054–0.107) ». Or, dans le tableau `07_SHIFT_TESTS.md` (recalculé ✔), la fausse confiance calibrée (HGB+Platt) vaut : feature_shift **0,037** (×1,5 seulement), vol_jump **0,107** (×4,5), stale_features **0,054** (×2,3), regime_transition 0,096 (×4,0). La plage « 0,054–0,107 » est correcte mais la valeur basse 0,054 correspond aux *données figées* (stale), pas au feature_shift. L'AUROC 0,39 (feature shift) et 0,43 (vol jump) est bien correct (✔).

#### 3.A.1 Calibration statique (`03_STATIC_CALIBRATION.md`) — Q1

*Ce qui est testé.* Le modèle de base est entraîné, un calibrateur est ajusté sur le bloc de calibration (3000 points), on mesure sur le test (6000 points). 20 graines. « ORACLE » = la vraie probabilité du générateur (plafond inatteignable).

**Monde synthétique, HGB (le modèle sur-confiant) — ✔ tous recalculés** (`bench/uncertainty_v1/results/static_raw.csv`) :

| Calibrateur | Brier | Log-loss | ECE | Fausse confiance (FCR) |
|---|---|---|---|---|
| brut (raw) | 0,218 ± 0,001 | 0,660 ± 0,004 | **0,118 ± 0,003** | **0,119 ± 0,002** |
| Platt | 0,201 ± 0,001 | 0,586 ± 0,002 | 0,022 ± 0,002 | 0,028 ± 0,002 |
| température | 0,201 ± 0,001 | 0,586 ± 0,002 | 0,022 ± 0,002 | 0,028 ± 0,002 |
| bêta | 0,201 ± 0,001 | 0,585 ± 0,002 | 0,022 ± 0,002 | 0,027 ± 0,002 |
| isotonique | 0,202 ± 0,001 | 0,588 ± 0,002 | 0,023 ± 0,002 | 0,031 ± 0,003 |
| binning bayésien | 0,203 ± 0,001 | 0,589 ± 0,002 | 0,028 ± 0,003 | 0,032 ± 0,004 |
| ORACLE (vraie proba) | 0,182 ± 0,001 | 0,536 ± 0,002 | 0,017 ± 0,002 | 0,035 ± 0,001 |

*Lecture simple.* Le GBM brut dit « 80 % » mais n'a raison qu'environ 68 % du temps (ECE 0,118). Une simple droite (Platt) ou un seul paramètre (température) suffit à le corriger (0,022), tout près du plafond 0,017 (le plafond n'est pas zéro parce que l'ECE mesuré sur 6000 points contient toujours du bruit d'estimation). La log-loss baisse de 0,660 à 0,586 (oracle 0,536). Le ratio gain/complexité favorise nettement les recettes à 1–2 paramètres ; isotonique et binning bayésien n'apportent rien à n = 3000.

*Curiosité à noter.* La fausse confiance de l'oracle (0,035) est *plus élevée* que celle du HGB recalibré (0,028) : un modèle parfaitement calibré reste faux quand il annonce 80 %, 20 % du temps ; la FCR n'est donc pas un indicateur à faire tendre vers 0, mais à comparer (le run 2 le dit explicitement).

**LR et GNB** (bases déjà quasi calibrées dans ce monde « logistique ») : LR brut ECE 0,022 → Platt 0,023, température 0,023, bêta 0,022 — **aucun gain ni dégât** ✔. Le rapport précise que le monde « favorise LR ».

**Petit échantillon — breast cancer (calibration n ≈ 170 ; 20 découpages) — ✔ vérifiés en partie :**

| base | calibrateur | Brier | log-loss | ECE |
|---|---|---|---|---|
| GNB | brut | 0,060 | 0,493 | 0,058 |
| GNB | binning bayésien | 0,053 | 0,226 | **0,031** |
| GNB | Platt | 0,049 | 0,189 | 0,049 |
| HGB | brut | 0,042 | 0,253 | 0,038 |
| HGB | Platt | 0,037 | 0,147 | 0,028 |
| HGB | température | 0,037 | 0,137 | 0,029 |
| LR | brut | 0,040 | 0,152 | 0,025 |
| LR | Platt | 0,039 | 0,135 | 0,024 |
| LR | isotonique | 0,043 | 0,159 | 0,039 |

(les autres lignes du tableau complet figurent dans `03_STATIC_CALIBRATION.md`, non reproduites ici ; les 5 lignes ✔ recalculées : GNB brut 0,058/0,060/0,493, GNB bayes_bin 0,031/0,053/0,226, LR isotonique 0,039/0,043/0,159, LR Platt 0,024/0,039/0,135, HGB Platt 0,028/0,037/0,147.)

*Lecture.* Avec ~170 points de calibration, les écarts d'ECE entre méthodes sont de l'ordre des intervalles de confiance : le rapport conclut honnêtement qu'« aucune méthode n'est distinguable du brut, sauf les gains de log-loss pour les GNB/HGB sur-confiants ». L'isotonique (courbe libre) est pire que Platt/température pour LR (0,039 contre 0,024) : la variance d'une courbe libre coûte cher sur peu de données.

**Données réelles dérivantes — ELEC2 (prévision de y_{t+1} ; calibration 9000–13500 ; 6 tronçons de test ; une seule réalisation) — ✔ vérifiés en partie :**

| base | calibrateur | Brier | log-loss | ECE moyen | FCR |
|---|---|---|---|---|---|
| GNB | brut | 0,181 | 0,611 | 0,101 | 0,093 |
| GNB | isotonique | 0,163 | 0,500 | 0,056 | 0,032 |
| HGB | brut | 0,170 | 0,595 | 0,107 ✔ | 0,124 |
| HGB | **température** | 0,160 | 0,508 | **0,068** ✔ | 0,091 |
| HGB | Platt | 0,166 | 0,530 | 0,080 | 0,099 |
| LR | **brut** | 0,178 | 0,532 | **0,103** ✔ | 0,013 |
| LR | Platt | 0,200 | 0,619 | 0,153 ✔ | 0,159 |
| LR | température | 0,209 | 0,647 | 0,168 ✔ | 0,173 |
| LR | isotonique | 0,205 | 0,604 | 0,159 ✔ | 0,208 |

ECE par tronçon (`06`/`03`, extraits) — HGB température : 0,048 / 0,082 / 0,104 / 0,125 / 0,025 / 0,024 (✔ recalculé) ; HGB brut : 0,096 / 0,129 / 0,148 / 0,170 / 0,059 / 0,042 ; LR Platt : 0,173 / 0,168 / 0,212 / 0,232 / 0,078 / 0,054 ; LR brut : 0,100 / 0,132 / 0,124 / 0,120 / 0,049 / 0,092.

*Lecture simple.* **Le recalibrage fait sur la fenêtre de calibration n'a pas survécu au temps.** Pour LR, le calibrateur a *empiré* l'ECE (0,103 → 0,15–0,17). Pour HGB/GNB, c'est mieux que brut mais bien au-dessus de 0,03 et instable (0,025 à 0,125 selon le tronçon). **Un détail que le rapport ne souligne pas et que j'ai trouvé dans les CSV (✔)** : sur la *fenêtre de validation adjacente* (13500–18000), le même calibrateur Platt de LR donne un ECE de **0,015** (brut : 0,128) — il fonctionne très bien juste après la fenêtre de calibration, puis se dégrade en s'éloignant. Cela illustre le vieillissement d'un calibrateur figé (`static_raw.csv`, lignes `part = val`).

**Réponse à Q1 (rapport)** : oui en régime stationnaire avec ≥ ~3000 points de calibration (Platt ou température fait l'affaire) ; non à travers le temps sur ELEC2.

#### 3.A.2 Calibration en ligne (`04_ONLINE_CALIBRATION.md`)

*Ce qui est testé.* Le modèle de base est figé (entraîné sur 0–4000). Bloc de calibration 4000–7000. Flux à partir de 7000 (14 000 pas en synthétique ; ELEC2 à partir de 13 500). L'étiquette du pas j n'est révélée qu'à j + h ; un calibrateur utilisé à l'instant t ne peut utiliser que les étiquettes avec j + h ≤ t (h = 10 en synthétique ; 1 ou 48 demi-heures en ELEC2). Méthodes : Platt statique / isotonique statique ; Platt à fenêtre extensible (expanding) ; Platt à fenêtre glissante (W = 1000 ; 2000 pour ELEC2 ; refit toutes les 250 pas) ; isotonique glissant ; Platt SGD (descente de gradient en ligne, lr 0,02) ; et deux variantes **volontairement tricheuses** servant d'audit. 8 graines par scénario. Scénarios : stationnaire ; régime abrupt (deux coefficients changent de signe à l'étape 12 000) ; dérive graduelle (même inversion, étalée sur 8000 pas) ; saut de volatilité (features ×1,5, rapport signal/bruit ×0,35).

**Audit anti-fuite** : `pit_ok` vaut True pour les 216 exécutions PIT-safe (✔ recalculé : 216 lignes, toutes True).

**Tableaux complets (✔ tous recalculés ; extrait « régime abrupt » et « stationnaire »)** (`bench/uncertainty_v1/results/online_raw.csv`) :

Stationnaire :

| méthode | ECE | Brier | ECE pire tronçon | FCR | turnover | turnover brut | écart-type de la pente |
|---|---|---|---|---|---|---|---|
| Platt extensible | 0,012 ± 0,002 | 0,201 | 0,047 | 0,027 | 0,498 | 0,449 | 0,006 |
| Platt SGD | 0,012 ± 0,001 | 0,202 | 0,045 | 0,031 | 0,489 | 0,449 | 0,106 |
| Platt statique | 0,013 ± 0,002 | 0,201 | 0,049 | 0,026 | 0,498 | 0,449 | 0 |
| Platt glissant | 0,013 ± 0,002 | 0,201 | 0,048 | 0,027 | 0,496 | 0,449 | 0,039 |
| isotonique statique | 0,020 ± 0,003 | 0,202 | 0,052 | 0,031 | 0,494 | 0,449 | — |
| isotonique glissant | 0,020 ± 0,002 | 0,203 | 0,052 | 0,035 | 0,485 | 0,449 | — |

Régime abrupt :

| méthode | ECE | Brier | ECE pire tronçon | FCR | turnover | pente sd |
|---|---|---|---|---|---|---|
| Platt statique | 0,100 ± 0,042 | 0,252 | 0,182 ± 0,067 | 0,065 | 0,498 | 0 |
| isotonique statique | 0,102 ± 0,040 | 0,253 | 0,187 | 0,073 | 0,494 | — |
| Platt extensible | 0,067 ± 0,026 | 0,237 | 0,152 ± 0,062 | 0,028 | 0,466 | 0,085 |
| **Platt glissant** | **0,017 ± 0,004** | 0,225 | **0,104 ± 0,031** | 0,015 | 0,401 | 0,188 |
| isotonique glissant | 0,026 ± 0,003 | 0,229 | 0,117 ± 0,040 | 0,021 | 0,343 | — |
| Platt SGD | 0,025 ± 0,006 | 0,227 | 0,064 ± 0,011 | 0,018 | 0,395 | 0,223 |
| *triche : bloc lui-même* | 0,013 | 0,221 | 0,048 | 0,013 | 0,391 | 0,203 |
| *triche : futur global* | 0,013 | 0,233 | 0,119 | 0,006 | 0,319 | 0 |

Dérive graduelle (rapport, non reproduit en entier) : ECE statique Platt 0,110 → glissant 0,016, SGD 0,026, extensible 0,063. Saut de volatilité : statique 0,092 → glissant 0,016 ; SGD 0,024 ; extensible 0,057.

*Lecture simple.* Sans dérive, « en ligne » n'apporte rien (tout ≈ 0,012–0,020). Sous dérive, le calibrateur figé s'effondre (ECE 0,10) et le calibrateur à fenêtre glissante le rattrape presque entièrement (0,017) — **mais avec retard** : le pire tronçon (celui qui contient la cassure) reste à 0,104. Le Platt extensible (qui garde toute l'histoire) est le plus faible : l'ancien régime dilue le nouveau.

**Critère pré-déclaré (gain du pire tronçon vs statique ≥ 0,02 avec borne basse de l'IC ≥ 0,02 ; turnover ≤ 1,2 × brut) — ✔ recalculé pour Platt glissant / extensible / SGD** :

| scénario | méthode | gain pire tronçon | borne basse ≥ 0,02 ? | ratio turnover vs brut |
|---|---|---|---|---|
| régime abrupt | Platt glissant | 0,079 ± 0,040 | OUI | 0,89 |
| régime abrupt | SGD | 0,119 ± 0,064 | OUI | 0,88 |
| régime abrupt | Platt extensible | 0,031 ± 0,016 | **NON** | 1,04 |
| dérive graduelle | Platt glissant | 0,125 ± 0,063 | OUI | 0,85 |
| dérive graduelle | extensible | 0,066 ± 0,028 | OUI | 0,99 |
| saut de volatilité | Platt glissant | 0,073 ± 0,014 | OUI | 0,98 |
| saut de volatilité | SGD | 0,097 ± 0,009 | OUI | 0,90 |
| saut de volatilité | extensible | 0,026 ± 0,010 | **NON** | 1,13 |

**ELEC2 réel (une réalisation ; ✔ recalculé)** :

| base | méthode | ECE | ECE pire tronçon | écart-type de pente |
|---|---|---|---|---|
| HGB | Platt statique | 0,057 | 0,177 | 0 |
| HGB | Platt glissant | 0,017 | 0,044 | 0,130 |
| HGB | Platt extensible | 0,016 | 0,090 | 0,075 |
| LR | Platt statique | 0,130 | 0,283 | 0 |
| LR | Platt glissant | 0,024 | 0,057 | **0,782** |
| LR | isotonique glissant | 0,014 | 0,044 | — |

*Point d'attention.* L'instabilité du paramètre de pente sur ELEC2-LR (écart-type 0,56 à 0,78) est signalée par le rapport comme un « vrai risque » (« worth capping / smoothing before any use »). Ce n'est pas mesuré comme un coût de décision ; c'est une alerte.

**Fuite mesurée** : le triche « bloc lui-même » atteint un pire tronçon de 0,048 (abrupt) contre 0,104 pour le glissant honnête ; le triche « futur global » fait *pire* (0,119) car une seule carte globale ne suit pas le changement — le rapport en conclut (à juste titre) que « la fuite ne flatte pas toujours » et que l'audit ne fait que borner l'effet.

**Verdict du rapport pour l'en ligne** : supporté avec fenêtre glissante et étiquettes retardées (Platt glissant, isotonique glissant, SGD : 3 scénarios de dérive sur 3 ; extensible : non).

#### 3.A.3 Abstention (`05_ABSTENTION.md`) — Q2

Politiques testées (base HGB + Platt ; seuils fixés sur le bloc de *calibration*) : P0 tout trader (τ = 0,5) ; P1 confiance calibrée ≥ 0,6 ; P2 = P1 + écart-type d'ensemble ≤ 90ᵉ percentile de calibration ; P3 = P1 + pas de drapeau manquant/figé + Mahalanobis ≤ 99ᵉ percentile de calibration ; P4 = P1 ∧ P2 ∧ P3. `matched_conf_risk` est un comparateur « à même couverture, classer par la confiance seule », utilisé pour tester si P2–P4 apportent quelque chose au-delà de la confiance.

**Tableau complet** (extraits ; tout le tableau `05_ABSTENTION.md` a été recalculé pour iid et régime : ✔) :

| choc | politique | couverture | risque sélectif | risque de l'abstention au hasard | risque « confiance seule, même couverture » | mauvaises évitées | bonnes conservées | utilité |
|---|---|---|---|---|---|---|---|---|
| iid | P0 tout trader | 1,000 | 0,318 | 0,318 | 0,318 | 0 | 1,000 | 0,163 |
| iid | **P1 conf ≥ 0,6** | **0,686** | **0,256** | 0,318 | 0,256 | **0,449** | **0,750** | **0,198** |
| iid | P2 conf+ensemble | 0,632 | 0,243 | 0,318 | 0,242 | 0,519 | 0,702 | 0,199 |
| iid | P3 conf+drapeaux | 0,677 | 0,256 | 0,318 | 0,254 | 0,455 | 0,739 | 0,195 |
| iid | P4 tout | 0,625 | 0,243 | 0,318 | 0,240 | 0,522 | 0,694 | 0,196 |
| vol_jump | P0 | 1,000 | 0,420 | — | — | 0 | 1,000 | −0,040 |
| vol_jump | P1 | 0,753 | 0,397 | — | 0,397 | 0,288 | 0,783 | 0,004 |
| vol_jump | P4 | 0,394 | 0,393 | — | 0,348 | 0,631 | 0,412 | 0,005 |
| regime_transition | P0 | 1,000 | 0,486 | — | — | 0 | 1,000 | **−0,171** |
| regime_transition | P1 | 0,686 | 0,482 | — | 0,482 | 0,328 | 0,682 | −0,112 |
| regime_transition | P4 | 0,625 | 0,482 | — | 0,481 | 0,390 | 0,620 | −0,102 |
| feature_shift | P0 | 1,000 | 0,266 | — | — | 0 | 1,000 | 0,267 |
| feature_shift | P1 | 0,782 | 0,220 | — | 0,220 | 0,368 | 0,831 | 0,291 |
| feature_shift | P4 | 0,416 | 0,188 | — | 0,138 | 0,715 | 0,460 | 0,188 |
| missing_features | P0 | 1,000 | 0,365 | — | — | 0 | 1,000 | 0,070 |
| missing_features | P1 | 0,619 | 0,303 | — | 0,303 | 0,487 | 0,679 | 0,120 |
| missing_features | P3 | **0,039** | 0,266 | — | 0,096 | 0,972 | 0,045 | 0,010 |
| stale_features | P0 | 1,000 | 0,391 | — | — | 0 | 1,000 | 0,018 |
| stale_features | P1 | 0,685 | 0,352 | — | 0,352 | 0,384 | 0,729 | 0,066 |
| stale_features | P3 | 0,401 | **0,258** | — | 0,303 | 0,735 | 0,488 | 0,114 |
| venue_change | P0 | 1,000 | 0,396 | — | — | 0 | 1,000 | 0,007 |
| venue_change | P1 | 0,652 | 0,353 | — | 0,353 | 0,419 | 0,698 | 0,060 |

(Le rapport contient aussi P2/P3/P4 pour chaque choc ; non tous reproduits ; recalcul ✔ pour iid et régime : coïncidence parfaite.)

**Courbes risque-couverture** (`05_ABSTENTION.md`, extraits) : AURC iid — confiance calibrée 0,198 ; confiance brute 0,198 ; confiance − 2×écart-type ensemble **0,191** ; hasard 0,316. Régime : 0,471 / 0,471 / 0,471 / 0,486. *Les lignes « brute » et « calibrée » sont identiques* : Platt est une transformation croissante, elle ne change pas le classement, donc pas la courbe risque-couverture.

*Lecture simple.* **Dans la distribution** : en n'agissant que si la confiance est ≥ 0,6, le système agit sur 69 % des lignes, son taux d'erreur sur ces lignes tombe de 31,8 % à 25,6 %, il évite 45 % des mauvaises décisions et garde 75 % des bonnes. L'utilité (gain moyen par occasion) passe de 0,163 à 0,198. **Sous choc de régime** (la relation entre features et résultat a changé), la confiance ne dit plus rien : 48,6 % d'erreur avant, 48,2 % après, l'utilité reste négative — s'abstenir ne peut pas réparer un modèle faux. Les « vetos » d'ensemble et de distance n'apportent pas plus que de relever le seuil de confiance (P2 : 0,243 contre 0,242 pour la confiance seule au même volume) ; **seuls les drapeaux de défaut de données aident vraiment** (stale P3 : 0,258 de risque contre 0,303). Sous 30 % de valeurs manquantes par feature, P3 s'abstient sur ~96 % des lignes : correct mais c'est un arrêt total, pas une dégradation gracieuse.

**Réponse à Q2 (rapport)** : oui dans la distribution et sous chocs de type covariables (feature shift, venue, données figées/manquantes) ; non sous chocs de concept.

**Réserve de fond** (rapport `05` dernier paragraphe) : le gain ±1/coût 0,2 est un « proxy stylisé, pas du P&L ». Autre remarque de ma part : le seuil τ = 0,6 est *exactement* le seuil de rentabilité nulle du modèle de gain ; « l'abstention améliore l'utilité » est donc en partie une conséquence mathématique de la définition du gain (ne pas trader quand l'espérance est négative), pas une découverte empirique. L'apport empirique réside dans le fait que la calibration rend ce seuil *utilisable sans réglage*.

#### 3.A.4 Prédiction conforme (`06_CONFORMAL.md`)

*Statut théorique (DOCUMENTED_CLAIM, non relu)* : split conformal = couverture marginale ≥ 1−α *seulement si* échangeabilité ; conformal non échangeable/pondéré (Barber et al. 2023) = borne d'écart dépendant des poids et d'un terme de distance de distribution, pas de garantie sans distribution pour des poids fixes ad hoc (ici λ = 0,998) ; ACI (Gibbs & Candès 2021) = la moyenne de long terme du taux de non-couverture converge vers α *avec retour immédiat de l'étiquette*, sans hypothèse de distribution, mais c'est une moyenne temporelle, pas une couverture conditionnelle ; **avec étiquettes retardées, aucune garantie prouvée dans ce run** (UNKNOWN).

*Conception.* Score LAC (1 − probabilité calibrée de la vraie classe) sur HGB+Platt (Platt ajusté sur les lignes 4000–5500, scores de calibration conformal sur 5500–7000, lignes disjointes). Ensembles possibles : {haut}, {bas}, {les deux} (= s'abstenir), ∅. Le score du pas j n'est utilisable qu'à j + h. Méthodes : `split` (figé), `rolling` (W = 1000), `weighted` (λ = 0,998), `aci` (γ = 0,005, retard h = 10), `aci_h0` (version manuel, irréaliste). Scénarios : `iid_control` (φ = 0), AR(1) stationnaire, régime abrupt, dérive graduelle, saut de volatilité ; ELEC2 (h = 1). 8 graines. Couverture jugée en marginal et en fenêtres de 500 pas (`min_roll_cov`, `frac_win_below`). *Détail de code repéré (✘ mineur par rapport au rapport)* : pour ELEC2, `set_stats(..., win=1000)` : les fenêtres glissantes sont de **1000 pas** et non 500 comme le protocole l'annonce.

**Classification, α = 0,2 (cible 0,80) — ✔ recalculé pour les lignes reproduites :**

| type | méthode | couverture | pire fenêtre | part de fenêtres sous 0,75 | singleton | « les deux » | précision des singletons |
|---|---|---|---|---|---|---|---|
| iid_control | split | 0,796 ± 0,011 | 0,746 | 0,021 | 0,757 | 0,243 | 0,731 |
| iid_control | ACI | 0,800 | 0,765 | 0 | 0,746 | 0,254 | 0,732 |
| régime abrupt | **split** | **0,733 ± 0,013** | 0,638 | **0,600** | 0,740 | 0,260 | 0,638 |
| régime abrupt | rolling | 0,796 | 0,711 | 0,033 | 0,606 | 0,394 | 0,662 |
| régime abrupt | pondéré | 0,798 | 0,728 | 0,022 | 0,602 | 0,398 | 0,663 |
| régime abrupt | ACI | 0,800 | 0,756 | 0 | 0,597 | 0,403 | 0,663 |
| saut de vol. | **split** | **0,723 ± 0,005** | 0,630 | **0,653** | 0,779 | 0,221 | 0,645 |
| saut de vol. | ACI | 0,800 | 0,755 | 0,001 | 0,614 | 0,386 | 0,674 |
| dérive graduelle | split | 0,726 ± 0,014 | 0,645 | 0,69 | 0,740 | 0,260 | 0,629 |
| ELEC2 | split | 0,764 | 0,589 | 0,386 | 0,975 | 0 | 0,783 |
| ELEC2 | rolling | 0,796 | 0,692 | **0,106** | 0,908 | 0,068 | 0,802 |
| ELEC2 | pondéré | 0,800 | 0,732 | 0,011 | 0,902 | 0,074 | 0,805 |
| ELEC2 | ACI | 0,800 | 0,755 | 0 | 0,886 | 0,082 | 0,811 |

Classification α = 0,1 (cible 0,90), ELEC2 : split 0,849 (fenêtres en défaut 0,445), ACI 0,900, pondéré 0,902, rolling 0,898 (0,024) — ✔.

**Critère pré-déclaré (|couverture − (1−α)| ≤ 0,03 et ≤ 10 % de fenêtres basses)** : ACI et pondéré OUI dans les 9 cadres ; rolling OUI dans 8/9 (ELEC2 α = 0,2 : NON, 10,6 % de fenêtres basses, « de justesse ») ; split NON sous toute dérive.

**Régression (α = 0,2) — ✔ :**

| type | méthode | couverture | pire fenêtre | largeur |
|---|---|---|---|---|
| stationnaire | split | 0,798 | 0,751 | 1,379 |
| vol. ×3 | **split** | **0,512 ± 0,009** | 0,301 | 1,379 |
| vol. ×3 | rolling | 0,793 | 0,581 | 2,950 |
| vol. ×3 | ACI | 0,800 | 0,732 | 3,010 |
| rampe de vol. | **split** | **0,452 ± 0,010** | 0,307 | 1,379 |
| rampe de vol. | ACI | 0,800 | 0,765 | 3,171 |

**California housing, intervalle split, α = 0,2 (10 répétitions) — ✔** : décalage de covariables (entraînement/calibration revenu médian ≤ P60, test > P60) **0,498 ± 0,006** contre cible 0,80, largeur 0,817 ; découpage aléatoire échangeable **0,799 ± 0,004**, largeur 0,95.

*Lecture simple.* Quand les données sont « échangeables », tout marche (0,796–0,802). Dès que le monde change, le conformal figé (split) ne couvre plus que 72–73 % au lieu de 80 % (dans 60–69 % des fenêtres) et, sur le décalage de revenus de California housing, à peine la moitié (0,498). Les méthodes adaptatives rétablissent la couverture *moyenne*, mais (i) juste après une cassure la couverture locale reste sous la cible (pire fenêtre 0,70–0,76), (ii) **et surtout la couverture marginale n'est pas la précision de la décision** : quand l'ensemble prédit est un singleton (donc quand on agirait), la précision réelle n'est que de 0,65–0,73 dans les mondes synthétiques, très loin des « 80 % » de couverture. La raison : la couverture compte comme « correcte » toutes les lignes où l'ensemble est {les deux classes}, qui contiennent trivialement la vérité. Le choix de α *est* le taux d'abstention (α = 0,1 → 51–64 % de lignes {les deux} ; α = 0,2 → 26–42 %).

*Effet du retard* : `aci` (h = 10) et `aci_h0` (h = 0, irréaliste) diffèrent d'au plus 0,001 de couverture — pas une preuve (γ petit, h petit devant T).

**Tableau « ce qui est supporté »** du rapport : exchangeable → split OK (théorie + témoin) ; AR stationnaire → split OK *empiriquement* (0,801 ; « la théorie ne le couvre pas ») ; dérive/vol/ELEC2 → ACI (retardé) et pondéré tiennent la couverture marginale, rolling tient sur le synthétique mais est limite sur ELEC2 α = 0,2 ; décalage de covariables (housing) split **non valide** (0,498) ; fiabilité au niveau de la décision (singleton) : **aucune méthode supportée**.

#### 3.A.5 Tests de choc (`07_SHIFT_TESTS.md`) — Q3 et Q4

Bloc test synthétique [10000:16000], les **mêmes lignes** avec et sans transformation (comparaison appariée). Calibrateurs ajustés sur le bloc de calibration *non décalé*. 20 graines.

**ECE par choc (HGB) — ✔ recalculé :**

| choc | binning bayésien | isotonique | Platt | brut |
|---|---|---|---|---|
| iid | 0,026 | 0,022 | 0,021 | 0,116 |
| vol_jump | 0,144 | 0,142 | 0,141 | 0,251 |
| regime_transition | 0,177 | 0,170 | 0,172 | 0,283 |
| feature_shift | 0,054 | 0,052 | 0,036 | 0,113 |
| missing_features | 0,040 | 0,033 | 0,030 | 0,133 |
| stale_features | 0,080 | 0,076 | 0,076 | 0,186 |
| venue_change | 0,076 | 0,071 | 0,068 | 0,177 |

**Fausse confiance calibrée (HGB+Platt) : ✔** iid 0,024 ; vol_jump 0,107 ; regime 0,096 ; feature_shift 0,037 ; missing 0,023 ; stale 0,054 ; venue 0,040. Brut : 0,115 / 0,239 / 0,254 / 0,123 / 0,118 / 0,172 / 0,157.

**Q3 — la calibration survit-elle ? (critère : ECE ≤ 0,05 ET FCR ≤ 1,5 × iid + 0,01 ; HGB+Platt) — ✔ toutes les valeurs, y compris « graines survivantes » recalculées** :

| choc | ECE choc | ECE iid | FCR choc | FCR iid | graines survivantes | survit |
|---|---|---|---|---|---|---|
| vol_jump | 0,141 ± 0,004 | 0,021 | 0,107 ± 0,005 | 0,024 | 0/20 | NON |
| regime_transition | 0,172 ± 0,042 | 0,021 | 0,096 ± 0,020 | 0,024 | 1/20 | NON |
| feature_shift | 0,036 ± 0,008 | 0,021 | 0,037 ± 0,011 | 0,024 | 17/20 | OUI |
| missing_features | 0,030 ± 0,004 | 0,021 | 0,023 ± 0,002 | 0,024 | 19/20 | OUI |
| stale_features | 0,076 ± 0,004 | 0,021 | 0,054 ± 0,004 | 0,024 | 0/20 | NON |
| venue_change | 0,068 ± 0,012 | 0,021 | 0,040 ± 0,008 | 0,024 | 7/20 | NON |

**2 chocs sur 6.** Pour LR (déjà calibré), brut ≈ Platt à chaque choc (ECE 0,158–0,187 sur vol/régime).

**Détection de choc sans étiquettes (AUROC ligne par ligne, choc vs iid) — ✔ tous recalculés :**

| choc | Mahalanobis | écart-type ensemble | faible confiance | drapeaux manquant/figé |
|---|---|---|---|---|
| feature_shift | 0,877 | 0,629 | **0,391** | 0,5 |
| missing_features | **0,313** | 0,470 | 0,558 | 0,971 |
| regime_transition | 0,500 | 0,500 | 0,500 | 0,500 |
| stale_features | 0,500 | 0,506 | 0,502 | 0,704 |
| venue_change | 0,495 | 0,535 | 0,534 | 0,500 |
| vol_jump | 0,864 | 0,615 | **0,425** | 0,500 |

*Lecture.* Un AUROC de 0,5 = aucune information. Un AUROC **inférieur à 0,5** pour la « faible confiance » (0,39 ; 0,43) signifie que le modèle devient *plus* confiant quand le monde change : c'est la définition de la fausse confiance. Le Mahalanobis (distance statistique aux features d'entraînement) attrape les chocs de features (0,86–0,88) mais est aveugle aux changements de relation (0,50) et *à l'envers* pour les données manquantes (0,31, car l'imputation par la moyenne rapproche les lignes du centre). Le choc de régime est **invisible pour tout détecteur sans étiquettes**.

**Moniteur de calibration fondé sur les étiquettes (z binomial glissant < −3 sur les lignes traitées ; étiquettes retardées de 10 pas ; fenêtre 300) — ✔ recalculé** :

| choc | part des graines alarmées | délai médian (pas) |
|---|---|---|
| iid | **0,15** | 5232 |
| vol_jump | 1,00 | 411 |
| regime_transition | 1,00 | 454,5 |
| feature_shift | 0,50 | 1203,5 |
| missing_features | 0,90 | 1592 |
| stale_features | 1,00 | 505 |
| venue_change | 1,00 | 488,5 |

*Lecture.* C'est le seul signal qui détecte le choc de régime (toutes les graines, ≈ 450 pas après), mais au prix de 15 % de fausses alarmes par 6000 pas en données iid (surveillance continue sans correction de tests multiples) et de plusieurs centaines de pas de retard.

**Q4 — séparer les causes (matrice de confusion, lignes = vérité, colonnes = prédiction ; ✔ recalculée depuis `taxonomy_confusion.csv`)** :

| vérité \ prédiction | SIGNAL | NO_SIGNAL | DATA_GAP | MODEL_UNCERTAINTY | OOD |
|---|---|---|---|---|---|
| SIGNAL | 0,734 | 0,185 | 0 | 0,070 | 0,011 |
| NO_SIGNAL | 0,396 | **0,360** | 0 | 0,222 | 0,021 |
| DATA_GAP | 0,023 | 0,006 | **0,968** | 0,003 | 0 |
| MODEL_UNCERTAINTY | 0,720 | 0,098 | 0 | **0,149** | 0,033 |
| OOD | 0,014 | 0,001 | 0 | 0,006 | **0,979** |

Cascade de règles (seuils issus des seules données de calibration) : DATA_GAP (drapeau manquant ou répétition exacte) → OOD (Mahalanobis > p99 de calibration) → MODEL_UNCERTAINTY (écart-type d'ensemble > p90) → NO_SIGNAL (|p − 0,5| < 0,08) → SIGNAL. Pools de 1200 lignes par graine et par cause (20 graines ; le pool MODEL_UNCERTAINTY est plus petit : 5 883 lignes au total ✔ soit ≈ 294 par graine, parce que la région éparse est rare).

**Critère (rappel ≥ 0,7 pour chacune des 4 causes) : NON atteint, 2 sur 4.** Réserve du rapport : les causes sont définies par le générateur (circulaire ; borne haute).

#### 3.A.6 Modes de défaillance, adjudication, limites (`08`, `09`, `10`)

* `08_FAILURE_MODES.md` : 14 modes de défaillance mesurés (F1 à F14) et 4 défaillances de processus (voir section 6).
* `09_ADJUDICATION.md` : tableau critère par critère (voir section 4) : calibré MET (stationnaire) / NOT MET (ELEC2) ; survit au choc NOT MET ; abstention MET sauf sous concept shift ; en ligne MET pour glissant/SGD ; conformal MET pour la couverture marginale ACI/pondéré ; Q4 NOT MET (2/4).
* `10_LIMITATIONS.md` : 11 limites (monde synthétique défini par le générateur ; monde qui favorise les modèles simples ; données réelles minces ; proxy de gain ; puissance statistique ; réimplémentations non croisées avec MAPIE/netcal ; littérature citée de mémoire ; méthodes non testées dont AgACI, SAOCP, conformal PID, CQR, 3 classes BUY/SELL/HOLD, étiquettes à horizon chevauchant ; délai d'étiquette fixe et connu ; seuils choisis par l'auteur ; aucune revendication d'intégration).

---

### 3.B — RUN 2 (PR #24) — lu intégralement (11 rapports), puis recalculé sur les CSV

#### 3.B.0 Synthèse exécutive du run 2 (`00_EXECUTIVE_SUMMARY.md`)

Ce que le rapport dit (en résumé fidèle) :

* **Q1** : oui en régime stationnaire. Pour un apprenant sur-confiant, la température fait passer l'ECE de 0,249 à 0,027 et la masse « confiant et faux » (CWM, conf ≥ 0,6 et faux) de 0,336 à 0,073 (IC appariés excluant 0). Pour un modèle déjà bien spécifié, la calibration n'ajoute rien. La température (1 paramètre) est aussi bonne ou meilleure que bêta/isotonique/BBQ-lite ; **Platt échoue sur les confiances saturées (ECE 0,119)**.
* **Q2** : « seulement faiblement ». À 25 % d'abstention sur les trades, le classement par confiance retire 36 % des trades perdants en gardant 83 % des gagnants (hasard : 25 % / 75 %), soit un gain modeste (~1,4×). Mais avec ce gain-jouet, même les trades peu confiants ont une espérance positive : l'abstention optimale n'est que ~5 % et des budgets plus grands *réduisent* l'utilité totale (−3 % à 25 %, −13 % à 40 %). L'abstention devient clairement utile seulement quand les trades deviennent négatifs sous choc *et* que la confiance est recalibrée en ligne (régime : utilité totale −151 → −36 ; données figées +122 → +146). L'ensemble n'est pas un meilleur score d'abstention que la probabilité maximale. Le conformal « singleton » (α = 0,2) écarte 58–76 % des décisions.
* **Q3** : la calibration statique ne survit pas (dérive d'ECE après−avant du GBM recalibré par température : feature shift +0,126, régime +0,150, figé +0,108, venue +0,066, vol +0,053). La recalibration en ligne avec étiquettes mûres la restaure largement (ECE moyen des chocs 0,107 → 0,025 ; CWM 0,127 → 0,025) après un transitoire de ≈ 500–1000 pas, sans coût mesurable en stationnaire. Idem sur ELEC2 (ECE 0,16 → 0,02–0,04).
* **Q4** : partiellement. DATA_GAP séparable *uniquement* via les drapeaux manquant/répétition (précision = rappel = 1,0 **par construction** ; sans ces drapeaux le rappel est 0). NO_SIGNAL vs NORMAL séparable par la confiance calibrée (F1 0,71). OOD détecté avec haute précision (0,97) mais faible rappel (0,39). **MODEL_UNCERTAINTY non séparable (F1 0,07).** Sauts de volatilité et transitions de régime invisibles pour les détecteurs d'espace d'entrée (taux de drapeau 5,9 % = niveau de fausse alarme alors que le taux d'erreur est 49–64 %) ; seul un moniteur de perte réalisée sur étiquettes mûres les détecte (100 % des graines, délai 150–500 pas).
* **Conformal** : split valide dans le témoin iid (0,902 ± 0,006), s'effondre sous choc (0,766 en moyenne pour cible 0,90 ; 0,54 pour un saut de vol. ; ELEC2 0,59–0,85 par bloc vs 0,80 ; California décalage 0,59). ACI/rolling/pondéré restaurent la couverture marginale de long terme (0,89–0,90) mais pas la conditionnelle (0,96–0,98 en basse vol. vs 0,82–0,84 en haute vol.), peuvent produire des intervalles infinis (ACI sur scores split : 9 % des pas), sous-couvrent transitoirement (pire fenêtre de 300 pas 0,82–0,88).

Bloc final (repris en section 5). **Tout ce résumé a été recoupé avec les CSV (sections ci-dessous) ; les seuls écarts trouvés sont signalés.**

#### 3.B.1 Calibration statique (`03_STATIC_CALIBRATION.md`)

**Dans la distribution (scénario `none`, 12 graines de test ; ✔ tout recalculé depuis `static_hold_*_metrics.csv`) :**

| base | méthode | Brier | log-loss | ECE (10 classes) | FCR@0,6 | CWM |
|---|---|---|---|---|---|---|
| lr | brut | 0,528 | 0,892 | 0,022 | 0,248 | 0,101 |
| lr | température | 0,528 | 0,893 | 0,022 | 0,248 | 0,101 |
| lr | Platt | 0,528 | 0,893 | 0,021 | 0,251 | 0,104 |
| lr | bêta | 0,528 | 0,893 | 0,023 | 0,251 | 0,104 |
| lr | isotonique | 0,528 | 0,894 | 0,024 | 0,245 | 0,099 |
| lr | BBQ-lite | 0,529 | 0,894 | 0,024 | 0,256 | 0,111 |
| gbm | **brut** | 0,684 | 1,339 | **0,249** | 0,432 | **0,336** |
| gbm | **température** | **0,575** | **0,964** | **0,027** | 0,272 | 0,073 |
| gbm | bêta | 0,595 | 1,052 | 0,029 | 0,281 | 0,076 |
| gbm | isotonique | 0,596 | 1,053 | 0,030 | 0,280 | 0,074 |
| gbm | BBQ-lite | 0,596 | 1,053 | 0,028 | 0,272 | 0,067 |
| gbm | **Platt** | 0,634 | 1,279 | **0,119** | 0,342 | 0,153 |

Différences appariées vs brut (moyenne ± IC t sur 12 graines, ✔) : GBM température ΔBrier −0,109 ± 0,003, ΔECE −0,222 ± 0,003, ΔCWM −0,263 ± 0,008.

*Lecture simple.* Sur le modèle sur-confiant, la température divise l'ECE par 9 et la masse « sûr et faux » par 4,6. Sur le modèle bien spécifié, rien ne change. **Le point piquant est Platt** : ECE 0,119, très au-dessus de la température (0,027). Le rapport l'explique par « les confiances saturent (logit ≈ ±14) donc une sigmoïde à deux paramètres ne représente pas la courbe » et l'étiquette *INFERENCE (non diagnostiqué séparément)*. **J'ai diagnostiqué ce point (voir sections 6 et 7) : c'est très probablement un défaut du solveur maison, pas une limite de la méthode de Platt.** En ajustant la même régression logistique avec scikit-learn sur les mêmes confiances, on obtient (pente 0,33 ; ordonnée −0,45), contre (1,60 ; −2,64) pour le solveur maison, et un ECE de 0,014–0,021 (comparable à la température : 0,012–0,015) au lieu de ~0,10–0,14.

**Stabilité stationnaire.** Dérive d'ECE (après − avant) dans le scénario `none` : −0,003 (GBM) / −0,005 (LR) ✔.

**Sous choc — dérive d'ECE statique (température) ✔ recalculée** :

| scénario | GBM | LR |
|---|---|---|
| feature_shift | +0,126 | +0,179 |
| regime_transition | +0,150 | +0,188 |
| stale_features | +0,108 | +0,124 |
| venue_change | +0,066 | +0,089 |
| vol_jump | +0,053 | +0,051 |
| missing_features | +0,040 | +0,001 |
| rare_cluster | +0,005 | +0,011 |

Masse « confiant et faux » après le choc, GBM température (✔) : feature 0,174 ; régime 0,169 ; figé 0,138 ; venue 0,127 ; vol 0,107 (contre 0,073 dans la distribution). GBM brut : ECE 0,42 (régime), CWM 0,34–0,50 selon le scénario (✔ 0,336–0,499).

*Lecture.* Le choix du calibrateur n'a pas d'importance sous choc : toutes les cartes statiques dérivent du même montant, parce que l'échec vient d'un changement de P(y|x) ou de la distribution d'entrée, pas de la forme de la carte confiance→précision. Le cas LR `missing_features` (+0,001) est anecdotique : l'imputation par la moyenne ramène les probabilités vers le taux de base, donc le modèle est *par accident* sous-confiant là où l'information manque.

**Données publiques (✔ recalculées depuis `public_*.csv`)** :

* iid, 20 découpages : credit-g GBM ECE brut **0,210** (Brier 0,457) → température **0,054** (Brier 0,358) ; credit-g LR 0,092 → 0,060 ; breast-cancer LR : le brut est déjà meilleur (ECE 0,028 contre 0,033 après température ; log-loss 0,097 contre 0,135) ; breast-cancer GBM 0,042 → 0,037. Ensembles de test de 114–200 lignes : bruités ; les découpages se recouvrent, donc l'écart-type est sous-estimé.
* ELEC2 (nowcast, 33 312 lignes de test) : **la température statique est pire que le brut pour LR** (Brier 0,456 → 0,478 ; log-loss 0,744 → 0,879 ; ECE 0,157 → 0,189) et n'aide que le GBM (Brier 0,530 → 0,471 ; ECE 0,240 → 0,164). Précision de test : 0,711 (LR), 0,697 (GBM).

#### 3.B.2 Calibration en ligne (`04_ONLINE_CALIBRATION.md`)

*Conception.* Recalibrage toutes les R = 50 pas avec uniquement les étiquettes mûres à t − H (H = 10). Variantes : `static` (ajusté une fois), `window` (dernières W = 600 lignes mûres, y compris l'historique de validation), `expanding` (toutes les lignes mûres), `decay` (poids exponentiels, demi-vie 400), plus les contrôles tricheurs `leak_h0` (H = 1) et `leak_peek` (voit le bloc suivant).

**ECE après le choc, température, GBM ✔ recalculé** (`hold_*_online.csv`) :

| scénario | statique | extensible | decay | **fenêtre** |
|---|---|---|---|---|
| feature_shift | 0,154 | 0,112 | 0,033 | 0,026 |
| regime_transition | 0,178 | 0,139 | 0,061 | 0,055 |
| stale_features | 0,136 | 0,101 | 0,025 | 0,018 |
| venue_change | 0,094 | 0,069 | 0,019 | 0,014 |
| vol_jump | 0,082 | 0,056 | 0,020 | 0,024 |
| missing_features | 0,069 | 0,055 | 0,025 | 0,020 |
| rare_cluster | 0,033 | 0,027 | 0,020 | 0,018 |
| none | 0,025 | 0,025 | 0,022 | 0,020 |

Moyennes sur les 7 chocs (GBM ✔) : ECE 0,107 → 0,025 (fenêtre) / 0,029 (decay) / 0,080 (extensible) ; CWM 0,127 → 0,025 / 0,028 / 0,085 ; Brier 0,670 → 0,641. LR : ECE 0,117 → 0,035, CWM 0,185 → 0,053 (✔). Avec bêta ou isotonique : ECE moyen sous choc (fenêtre, GBM) 0,060 et 0,064 contre 0,025 pour la température (✔).

*Lecture simple.* Après un choc, la calibration figée se dégrade de 0,03–0,18 ; refaire le calibrage sur les ~600 dernières lignes dont l'issue est connue ramène l'ECE à ≈ 0,02–0,06, avec un transitoire de 500–1000 pas. « Incrémental » veut dire **oublier** : garder toute l'histoire (extensible) n'améliore qu'à moitié.

**Limite forte, écrite par le rapport lui-même** : le régime de transition (rotation progressive de la relation) ne revient jamais au niveau dans-la-distribution (ECE ≈ 0,055 contre 0,02–0,04) et le Brier reste à 0,665 (contre 0,576 dans la distribution ; ✔ 0,665 / 0,576) : la recalibration suit un changement de *niveau* de confiance, mais si le modèle est simplement faux, la confiance calibrée devient basse et le Brier reste mauvais. **Elle ne crée pas d'information.**

**ELEC2 (33 312 lignes de test) — ✔ recalculé** :

| base | statique | fenêtre | decay |
|---|---|---|---|
| GBM/température : ECE | 0,164 | 0,021 | 0,021 |
| GBM/température : Brier | 0,471 | 0,386 | 0,386 |
| LR/température : ECE | 0,189 | 0,043 | 0,042 |
| LR/température : Brier | 0,478 | 0,372 | 0,371 |

ECE par bloc de 2000 lignes, GBM température (✔) : statique 0,03 / 0,08 / 0,03 / 0,14 / 0,25 / 0,32 / 0,20 / 0,25 / 0,34 / 0,34 / 0,37 / 0,24 / 0,13 / 0,01 / 0,02 / 0,04 ; fenêtre 0,02 → 0,13 max. Le rapport dit « statique 0,20–0,37 aux blocs 4–11, revient à 0,01–0,04 à la fin » ✔. **Réserve du rapport : W = 2000 et demi-vie 1000 (choisis sur validation) sont au bord de la grille** (« a longer window might do better »).

**Coût en régime stationnaire (✔)** : ECE 0,020 (fenêtre) contre 0,025 (statique), Brier 0,577 contre 0,576 ; turnover 0,487 contre 0,487 (GBM). Le recalibrage ne change jamais l'argmax (température et cartes top-label préservent l'argmax) ; il déplace seulement la frontière accepter/s'abstenir. **✘ mineur** : le rapport écrit « largest *added* turnover vs static is +0.023 (beta, feature shift) » ; le fichier `online_turnover_delta_vs_static.md` confirme +0,023 pour **GBM** bêta, mais pour **LR** température/feature_shift j'obtiens **+0,039** (fenêtre) et, à l'inverse, une baisse de **−0,192** pour LR température en transition de régime (le rapport cite « up to −0,10 », valable pour GBM : −0,101 ✔). Les bornes du rapport sont donc celles du GBM seulement.

**Fuite (lookahead) ✔ recalculé** : avec H = 1 ou une vue d'un bloc en avant, les calibrateurs à faible capacité sont à peine flattés (GBM température, ECE sous choc : honnête 0,0249, `leak_h0` 0,0246, `leak_peek` 0,0255). Le calibrateur **flexible isotonique** l'est : Brier GBM honnête 0,694 contre 0,686 (peek) ; LR 0,634 contre 0,622 ✔. L'inflation croît avec la capacité du calibrateur et l'ECE seul la sous-estime : il faut contrôler Brier/log-loss. Le rapport note que dans la vraie vie la fuite est pire car les étiquettes de rendements futurs se chevauchent dans le temps.

**Non mesuré** (rapport) : jitter des paramètres du calibrateur (trajectoire de la température ajustée), sensibilité à R. (UNKNOWN.)

**Verdict du rapport pour §6** : `ONLINE_CALIBRATION_SUPPORTED` : la température glissante/à décroissance avec étiquettes mûres est stable, bon marché et récupère l'essentiel de la calibration ; elle ne crée pas d'information ; elle **nécessite un flux d'étiquettes à délai de maturité connu** que le système privé peut fournir ou non (UNKNOWN).

#### 3.B.3 Abstention (`05_ABSTENTION.md`)

*Conception.* Abstain ≡ HOLD. Règles fondées sur : probabilité maximale du modèle recalibré par température statique (`conf_static_temp`), la même après recalibration glissante (`conf_online_temp`), probabilité maximale brute, entropie, information mutuelle d'ensemble. τ (ou seuil de budget) fixé sur la **validation** puis appliqué tel quel au test. « Good retained » = part des trades qui auraient rapporté > 0 encore pris ; « bad removed » = part des trades perdants évités ; référence : abstention au hasard au même taux.

**Classement risque-couverture (AURC, plus bas = mieux ; ✔ recalculé)** :

| score | GBM avant choc | LR avant choc | GBM après | LR après |
|---|---|---|---|---|
| probabilité max | 0,342 | 0,273 | 0,476 | 0,407 |
| entropie | 0,342 | 0,272 | 0,477 | 0,407 |
| MI d'ensemble | 0,339 | 0,410 | 0,474 | 0,503 |
| Mahalanobis | 0,518 | 0,479 | 0,590 | 0,553 |

Probabilité max ≈ entropie ; l'MI d'ensemble n'est pas meilleure pour GBM (0,339 contre 0,342 : écart de 0,003, non significatif) et clairement pire pour LR ; le Mahalanobis est *anti-informatif* pour les erreurs. Le choix du calibrateur change l'AURC de moins de 0,005 (✔ : 0,338–0,346 avant, GBM ; la carte est croissante, le classement est conservé).

**Budgets fixes d'abstention dans la distribution (avant choc ; GBM ; utilité totale sans abstention = 405,3 ; ✔ recalculé)** :

| abstention sur les trades | mauvais trades retirés | bons trades conservés | utilité totale | abstention au hasard, même taux |
|---|---|---|---|---|
| 10 % | 0,151 (LR 0,169) | 0,935 | 406,3 | 364,5 |
| 25 % | 0,362 (LR 0,383) | 0,826 (LR 0,831) | 392,1 | 303,3 |
| 40 % | 0,539 (LR 0,570) | 0,696 (LR 0,702) | 352,2 | 242,6 |

LR à 25 % : utilité 497,6 contre 514,1 sans abstention ✔. τ optimal sur validation : abstient ≈ 5 % (GBM ; ✔ 4,9 %) / 8 % (LR) des trades, utilité 407,4 contre 405,3 (+0,5 % ; hasard 386,2 ✔).

*Lecture simple.* Classer par confiance vaut ~1,4 × le hasard (à 25 % d'abstention : 36 % des mauvais trades retirés au lieu de 25 %, 83 % des bons gardés au lieu de 75 %). **Mais** dans ce gain-jouet, un trade peu confiant a quand même une espérance positive ; donc chaque abstention supplémentaire *retire de la valeur* : l'utilité totale baisse quand le budget grandit. Le seul intérêt de l'abstention apparaît quand le marché change.

**Sous choc avec τ gelé sur validation (après choc ; GBM ; ✔ recalculé)** :

| scénario | règle | abstention sur trades | mauvais retirés | bons conservés | utilité totale (sans abstention → règle ; hasard) |
|---|---|---|---|---|---|
| regime_transition | confiance statique | 0,048 | 0,049 | 0,954 | −151,3 → −141,7 (hasard −144,3) |
| regime_transition | **confiance en ligne** | **0,395** | 0,417 | 0,642 | −151,3 → **−35,7** (hasard −95,9) |
| stale_features | confiance statique | 0,049 | 0,055 | 0,959 | 121,9 → 130,6 |
| stale_features | **confiance en ligne** | 0,306 | 0,331 | 0,727 | 121,9 → **146,1** (hasard 85,3) |
| feature_shift | confiance statique | 0,026 | 0,030 | 0,979 | 119,9 → 126,0 |
| feature_shift | **confiance en ligne** | 0,220 | 0,239 | 0,806 | 119,9 → **146,8** (hasard 99,0) |
| vol_jump | confiance statique | 0,048 | 0,060 | 0,962 | 413,8 → 417,8 |
| vol_jump | confiance en ligne | 0,155 | 0,183 | 0,868 | 413,8 → **402,7** (hasard 346,9) |
| none | statique / en ligne | 0,048 / 0,049 | 0,076 / 0,077 | 0,972 / 0,971 | 803,2 → 809,4 / 808,1 |

Tous les 7 chocs + `none` poolés (GBM, ✔) : confiance statique s'abstient sur 4,6 % des trades, utilité 350,4 → 357,1 (+6,8) ; confiance en ligne : 17,9 % des trades, 350,4 → 372,5 (+22,1 ; hasard au même taux 319,0).

*Lecture.* Un seuil fixe sur une confiance *statique* ne réagit presque pas au choc (3–5 % d'abstention partout), car la sur-confiance est justement ce que la calibration statique ne voit pas. Un seuil fixe sur une confiance *recalibrée en ligne* s'ajuste tout seul : il s'abstient à 22–40 % là où les trades deviennent perdants. Et il **détruit de la valeur là où le marché reste rentable** (`vol_jump` : 413,8 → 402,7). L'abstention est un dispositif de **contrôle du risque, pas une source d'alpha**.

**Abstention conformal singleton** (renvoi à `06`) : sets LAC α = 0,2 (LR) : ≈ 38–42 % de décisions singleton en distribution (58–62 % d'abstention) ; sous choc 76 % d'abstention (ACI-rolling) pour une précision singleton de 0,63. Le contrôle de couverture consomme l'essentiel du nombre d'occasions parce que le signal à 3 classes est faible.

**Verdict Q2 (rapport)** : partiellement supporté. Gain régulier mais modeste sur le hasard (≈ 1,4×) ; peut éviter de grosses pertes **combiné à la recalibration en ligne dans un choc qui rend le trading non rentable** ; n'augmente pas l'utilité en monde stationnaire rentable ; la désaccord d'ensemble n'ajoute rien.

**Chronologie de conception à retenir** : le protocole (iii) reconnaît que le banc d'abstention a été conçu après avoir vu les tables test statique/en ligne. Ce n'est pas du sur-réglage (rien n'a été ajusté sur le test), mais c'est un degré de liberté du chercheur (choix des budgets 10/25/40 %).

#### 3.B.4 Prédiction conforme (`06_CONFORMAL.md`)

*Paramètres gelés.* Régression α = 0,10 sur le rendement latent futur ; classification LAC 3 classes α = 0,20 ; W = 300, demi-vie 150, ACI γ = 0,01 (choisis sur les graines de réglage : γ = 0,02 réduit légèrement l'écart de couverture mais fait passer le taux d'intervalle infini de 4 % à 9 % pour ACI sur scores split — **mes chiffres sur les graines de réglage : 4,7 % (γ = 0,01) contre 10,3 % (γ = 0,02) et 2,5 % (γ = 0,005)**, même ordre de grandeur, pas identiques). Tous les indicateurs en ligne n'utilisent que des scores mûrs (H = 10) ; le retour d'erreur d'ACI est retardé de H aussi.

**Tableau théorie/observation du rapport** : split : garantie de couverture marginale ≥ 1−α sous échangeabilité — témoin iid **0,902 ± 0,006 ✔**, monde stationnaire non échangeable 0,904 ± 0,015 ✔ (« marginalement correct, mais aucune garantie n'en découle » — ergodicité, pas échangeabilité, INFERENCE) ; conditionnel : cassé même dans le témoin iid : **0,981 (basse vol.) vs 0,823 (haute vol.)** ✔ pour cible 0,90 (l'hétéroscédasticité, pas le choc, en est la cause) ; Gaussien : **0,751 ± 0,028** dès le monde stationnaire ✔ ; ACI : 0,897–0,899 malgré le retard H = 10, mais « la borne publiée ne s'applique pas telle quelle avec retard » (littérature non vérifiée) ; ACI sur scores split : **intervalles infinis 9,3 %** des pas après choc (0,3 % sur scores rolling) ✔.

**Régression sous choc (post-début, moyenne des 7 chocs, α = 0,10 ; ✔ recalculé)** :

| méthode | couverture marginale | pire fenêtre de 300 pas | largeur médiane | taux d'intervalles infinis |
|---|---|---|---|---|
| Gaussien | 0,578 | 0,499 | 2,84 | 0 |
| split conformal | **0,766** | 0,696 | 4,37 | 0 |
| rolling | 0,890 | 0,817 | 6,35 | 0 |
| pondéré | 0,894 | 0,828 | 6,39 | 0 |
| ACI (scores split) | 0,897 | 0,865 | (moyenne 41, plafonnée) | **0,093** |
| ACI (scores rolling) | **0,899** | 0,869 | 6,47 | 0,003 |
| normalisé split | 0,907 | 0,877 | 6,63 | 0 |
| normalisé + ACI | 0,900 | 0,881 | 6,61 | 0 |

Saut de volatilité (✔) : split **0,538**, Gaussien **0,368**, rolling 0,879 (pire fenêtre 0,733), ACI-rolling 0,900 (0,864). Transition de régime : split 0,729 ✔. Le prix de la validité est la largeur : +45–50 % par rapport à split après un choc. La normalisation locale ne réduit que partiellement l'écart conditionnel (hors choc : basse vol. 0,931 / haute 0,871 pour normalisé+ACI, contre 0,981 / 0,824 pour split simple ✔).

**Classification, ensembles LAC (α = 0,2, LR, moyennes des 7 chocs après début ; ✔ recalculé)** :

| méthode | couverture | taille d'ensemble | taux de singletons | abstention | précision des singletons |
|---|---|---|---|---|---|
| split | **0,668** (cible 0,80) | 1,64 | 0,450 | 0,550 | 0,565 |
| rolling | 0,793 | 2,05 | 0,245 | 0,755 | 0,626 |
| pondéré | 0,793 | 2,05 | 0,245 | 0,755 | 0,626 |
| ACI (scores split) | 0,796 | 2,07 | 0,243 | 0,757 | 0,623 |
| ACI (scores rolling) | 0,800 | 2,08 | 0,237 | 0,763 | 0,625 |

En monde stationnaire (`none`, avant) : 0,412–0,420 de singletons (58 % d'abstention) et précision des singletons 0,73–0,74 ✔. « Le guarantee contrôle la couverture, pas la qualité de la décision — avec un signal faible, il achète la validité en s'abstenant sur la plupart des lignes. »

**ELEC2 (α = 0,2, 16 blocs de 2000 ; ✔)** : couverture split par bloc entre **0,588 et 0,866** (moyenne 0,720 LR / 0,734 GBM) ; rolling 0,676–0,886 ; ACI-rolling 0,785–0,812 (moyenne 0,800). **iid** (credit-g, breast-cancer, 20 découpages) : couverture split 0,800–0,812, écart-type 0,028–0,056 ✔ (valide en moyenne, forte variance). **California** : iid **0,901 ± 0,005** ; décalage de covariables **0,589** (Gaussien 0,546) ; conformal *pondéré* avec rapport de densités **estimé** par un classifieur de domaine entraîné sur les X de test non étiquetés : **0,651** contre 0,589 pour split et 0,90 nominal (✔). Le rapport note honnêtement que la correction « aide mais est loin d'être valide, parce que le rapport est estimé dans des régions extrêmes mal supportées ». (Le nom de la méthode dans le CSV est `weighted_cp_oracle_domain_clf`, alors que le rapport parle de rapport « estimé » : un « oracle » au sens de « utilise les X de test » — ce n'est pas un oracle au sens de rapport vrai.)

**Adjudication §7 (rapport)** : `CONFORMAL_SUPPORTED = PARTIAL` : valide seulement pour données échangeables ; sous série temporelle + dérive, seules défendables : (a) les méthodes de type ACI donnent *empiriquement* une couverture marginale de long terme proche du nominal ; (b) aucune couverture conditionnelle ou par régime ; (c) les méthodes de récence sont des heuristiques qui sous-couvrent pendant les transitions ; (d) avec étiquettes retardées toute garantie en ligne est plus faible que dans les théorèmes à retour immédiat.

#### 3.B.5 Tests de choc, détection et attribution de cause (`07_SHIFT_TESTS.md`)

*Détecteurs.* Fenêtres de 200 lignes évaluées toutes les 100 lignes sur le flux test ; seuil d'alarme = maximum de la statistique sur le flux de validation dans la distribution (pas de p-valeurs car les features autocorrélées invalident les p-valeurs iid). « Délai » = temps entre le début du choc et la *fin* de la première fenêtre en alarme (≈ 100 = minimum).

**Taux de détection sur 12 graines / délai médian (✔ recalculé depuis `diag_detection_*.csv`)** :

| scénario | classifieur de domaine (AUC) | KS max | Mahalanobis | taux de manquants | taux de répétitions | fenêtre de perte (étiquettes mûres) |
|---|---|---|---|---|---|---|
| feature_shift | 1,00 / 200 | 1,00 / 100 | 1,00 / 100 | 0 | 0 | 1,00 / 100 |
| venue_change | 1,00 / 200 | 1,00 / 200 | 1,00 / 100 | 0 | 0 | 1,00 / 150 |
| missing_features | 1,00 / 200 | 0,75 / 1500 | 0,00 | **1,00 / 100** | 0 | 1,00 / 250 |
| stale_features | 0,83 / 1500 | 1,00 / 300 | 0,83 / 1250 | 0 | **1,00 / 100** | 1,00 / 100 |
| rare_cluster | 0,42 / 1000 | 0,58 / 1400 | 0,92 / 700 | 0 | 0 | 1,00 / 300 |
| vol_jump | 0,42 / 1300 | 0,58 / 1400 | 0,67 / 1600 | 0 | 0 | **1,00 / 150** |
| regime_transition | 0,42 / 1300 | 0,58 / 1400 | 0,67 / 1600 | 0 | 0 | **1,00 / 500** |
| none (fausses alarmes) | 0,42 | 0,58 | 0,67 | 0 | 0 | **0,58** |

Fausses alarmes avant le début du choc (par bloc ; ✔) : classifieur de domaine 2,4 %, fenêtre de perte 4,8 %, KS 5,4 %, Mahalanobis 7,7 %. Dans le monde `none`, la « détection » est la part de graines avec *une* alarme quelconque sur 3000 pas = probabilité de fausse alarme par graine. **Donc 0,42–0,67 pour vol_jump / regime_transition / rare_cluster par les détecteurs d'entrée sont indiscernables des fausses alarmes** (le rapport le dit ; d'ailleurs ces scénarios ne changent pas les entrées observées — les valeurs sont *identiques* à celles de `none`, ce que j'ai constaté dans le CSV).

**Point que le rapport atténue (voir critique)** : la ligne `none` montre que la **fenêtre de perte** (le détecteur à étiquettes mûres, désigné « ADOPT comme alarme de choc ») déclenche au moins une alarme dans **58 % des graines** sur 3000 pas d'un monde *sans aucun choc* (délai médian 700 pas). Le rapport signale « persistence rule needed » pour les détecteurs d'entrée, mais la conclusion « seul détecteur du choc de concept, 100 % des graines » n'est pas accompagnée d'un taux de fausses alarmes par graine comparable pour le moniteur de perte dans la synthèse.

**Q4 — attribution de cause (règles gelées sur les graines de réglage ; ✔ recalculé, ≈ 198 000 lignes = 198 000 ✔)** : cascade, première règle qui correspond : DATA_GAP (NaN ou valeur répétée) → OOD (Mahalanobis > p99 de calibration) → MODEL_UNCERTAINTY (MI d'ensemble > p95) → NO_SIGNAL (confiance calibrée < 0,5) → NORMAL. Seuils maximisant le F1 macro sur les graines de réglage (0,516).

| cause vraie | précision | rappel | F1 |
|---|---|---|---|
| NORMAL | 0,545 | 0,902 | 0,679 |
| NO_SIGNAL | 0,602 | 0,873 | 0,713 |
| DATA_GAP | 1,000 | 1,000 | 1,000 (**par construction**) |
| MODEL_UNCERTAINTY | 0,047 | 0,168 | **0,073** |
| OUT_OF_DISTRIBUTION | 0,966 | 0,389 | 0,555 |
| macro | 0,632 | 0,666 | **0,604** (± 0,003 entre graines) |

Ablations (F1 macro ; ✔ recalculées : 0,325 / 0,479 / 0,585 / 0,181) : sans drapeaux de lacune DATA_GAP → 0 et macro 0,325 ; sans règle OOD → OOD 0 (macro 0,479) ; sans règle MI → MODEL_UNCERTAINTY 0 (macro 0,585) ; confiance seule (NO_SIGNAL contre le reste) macro 0,181. Des lignes dans la distribution reçoivent à tort une étiquette de défaut 5,9 % du temps (✔ 0,0588).

**Zone aveugle (✔ recalculé)** : vol_jump : taux d'erreur 0,492, confiance moyenne 0,575, marquées défaut 5,9 %, marquées NO_SIGNAL 38,5 % ; regime_transition : erreur **0,640**, confiance 0,575, marquées 5,9 %, NO_SIGNAL 38,5 %. **Erreur par cause prédite (toutes lignes poolées ; ✔)** : NORMAL 0,441 (conf 0,697) ; NO_SIGNAL 0,613 (0,409) ; DATA_GAP 0,560 (0,537) ; MODEL_UNCERTAINTY 0,564 (0,546) ; **OOD 0,479 (conf 0,726)** — les lignes étiquetées OOD conservent une confiance moyenne de 0,73 en étant fausses 48 % du temps : la fausse confiance classique que seule une porte OOD explicite peut traiter.

#### 3.B.6 Modes de défaillance, adjudication, limites (`08`, `09`, `10`)

* `08_FAILURE_MODES.md` : 20 modes (F1 à F20) dont F19 (INFERENCE : sensibilité à la longueur de fenêtre, grille trop étroite pour ELEC2) et F20 (UNKNOWN : instabilité des paramètres du calibrateur en ligne, sensibilité à R, interaction avec chevauchement réel des étiquettes de rendement futur).
* `09_ADJUDICATION.md` : 17 décisions candidates (section 4) et bloc final (section 5).
* `10_LIMITATIONS.md` : réalisme des données (monde auteur-défini ; ELEC2 n'est pas un rendement financier ; pas de données de venue/microstructure ; 3 classes, un horizon, un délai H = 10 fixe ; gain jouet), statistique (12 + 4 graines ; IC en t partageant du code générateur ; pas de correction de comparaisons multiples ; réglage sur seulement 4 graines à 0,6× ; seuils de détecteurs ad hoc), couverture des méthodes (Bayésien seulement en BBQ-lite ; **19 méthodes sur 52 non exécutées** ; pas de réseaux de neurones ; l'ensemble est un bootstrap du même apprenant ; DATA_GAP tautologique ; ACI retardé sans théorème), et périmètre (aucune donnée AurumShift).

#### 3.B.7 Quelques chiffres complémentaires du run 2 que j'ai extraits

* Méthodes : 52 découvertes (calibration 10, incertitude 8, sélectif 7, conformal 12, choc 9, en ligne 6), 33 exécutées, 19 découvertes non exécutées (`methods_counts.json` ✔ ; ✔ le comptage du tableau `01_METHODS.md` donne bien 33 « EXECUTED » et 19 « DISCOVERED_NOT_EXECUTED »).
* `key_numbers.json` (fichier) : `n_heldout_seeds = 12`, `split_cov_iid_control = 0.902 ± 0.006`, `split_cov_none_pre = 0.904 ± 0.015`, `gaussian_cov_none_pre = 0.751 ± 0.028`, `diag_macro_f1_full = 0.6039663…`, `diag_macro_f1_seed_ci = 0.604 ± 0.003`, `diag_false_flag_rate_in_dist = 0.058833…`.

---

## 4. Candidats et méthodes évalués, un par un

Rappel : ADOPT = à retenir comme référence externe ; ADAPT = utile mais à adapter, régler ou re-tester ; PARK = mis de côté faute de preuve ; REJECT = écarté. **Ces verdicts sont externes à AurumShift** ; ils ne disent rien de la compatibilité avec le vrai système.

Le run 1 n'utilise pas exactement les quatre mots pour chaque méthode : son `09_ADJUDICATION.md` donne des verdicts « critère par critère » (MET/NOT MET) puis une liste de références (ADOPT-as-reference / ADAPT / REJECT/PARK). Je les rapproche du barème à quatre mots en le disant. Le run 2 donne un tableau de 17 décisions.

### 4.1 Run 1 (PR #19)

| Candidat | Verdict (mots du rapport) | Justification chiffrée | Condition de changement de verdict (ma lecture) |
|---|---|---|---|
| **Platt fitté sur un bloc de calibration mis de côté + τ dérivé du coût + drapeaux manquant/figé** (`BEST_SIMPLE_REFERENCE`) | « ADOPT-as-reference / ADAPT (needs its own PIT-safe calibration block) » | GBM sur-confiant : ECE 0,118 → 0,022, FCR 0,119 → 0,028 ; LR/GNB : aucun dégât (0,022 → 0,023) ; abstention à τ = 0,6 : risque 0,318 → 0,256 ✔ | Devient inadapté dès que le marché change (2 chocs sur 6 seulement survivent) ; sur ELEC2, calibrer sur la fenêtre de calibration a *empiré* LR (0,103 → 0,153) : la référence ne vaut que dans un cadre stationnaire ou re-calibré régulièrement |
| **Température** | traitée comme « ≈ Platt » | ECE 0,022 identique à Platt (HGB, LR) ; ELEC2 HGB : meilleure que Platt (0,068 contre 0,080) mais LR pire (0,168 contre 0,153) | — |
| **Bêta** | pas de verdict propre | ECE 0,022 (HGB) ; version non contrainte (« sign not enforced ») | tester la version contrainte |
| **Isotonique / binning bayésien** | « REJECT/PARK : no gain at n≲3000 » | ECE 0,023 / 0,028 contre 0,022 pour Platt (HGB) ; à n ≈ 170 (LR) 0,039 contre 0,024 ; isotonique en ligne 0,020 contre 0,013 en stationnaire ✔ | à n bien plus grand, l'isotonique rattrape (littérature, **non testé**, UNKNOWN) |
| **Platt à fenêtre glissante, étiquettes retardées, PIT-assertée, refit ≈ 250 pas, W ≈ 1000** (`BEST_ONLINE_REFERENCE`) | « ADAPT (tune W/refit ; smooth the slope) » | régime abrupt : ECE 0,100 → 0,017 ; pire tronçon 0,182 → 0,104 ; critère MET (gain 0,079 ± 0,040 ≥ 0,02) ; turnover 0,89 × brut ✔ ; mais pente instable (sd 0,78 sur ELEC2-LR) | lissage/plafonnement de la pente non testés ; sensibilité à W et au refit non mesurée |
| **Platt SGD (lr 0,02)** | supporté sur les 3 scénarios de dérive | gain pire tronçon 0,119 ± 0,064 (abrupt), 0,114 (graduel), 0,097 (vol.) ✔ ; pente sd 0,106 en stationnaire | idem |
| **Isotonique glissant** | supporté sur les 3 scénarios | gain 0,066 / 0,117 / 0,067 ; ELEC2-LR ECE 0,014 | plus exposé à la fuite (constat du run 2) |
| **Platt à fenêtre extensible** | **non supporté** | gain 0,031 ± 0,016 (abrupt) et 0,026 ± 0,010 (vol.) : borne basse < 0,02 → NON ✔ | — |
| **Conformal split sur séries non stationnaires** | « REJECT/PARK : invalid » | couverture 0,72–0,73 (cible 0,80) ; regression vol. ×3 : 0,512 ; housing : 0,498 ✔ | valable seulement échangeable |
| **ACI (retardé) et conformal pondéré** | « MET for marginal coverage » | couverture 0,798–0,800 dans les 9 cadres ; pire fenêtre 0,72–0,76 ; **aucune fiabilité au niveau de la décision** (précision singleton 0,65–0,73) | garantie avec retard non démontrée ; variantes fortement adaptatives (AgACI, SAOCP) non testées |
| **Conformal rolling** | supporté dans 8 cadres sur 9 | ELEC2 α = 0,2 : 10,6 % de fenêtres basses > 10 % → échoue « de justesse » (fenêtres de 1000 pas dans le code) | — |
| **Vetoes ensemble / Mahalanobis comme améliorateur générique du risque sélectif** | « REJECT/PARK » | P2 0,243 contre 0,242 pour la confiance seule à même couverture ✔ ; AURC 0,198 → 0,191 | le drapeau de données (manquant/figé) reste utile : stale P3 0,258 contre 0,303 |
| **Drapeaux manquant / figé (HOLD forcé)** | retenu dans la référence simple | AUROC 0,971 (manquant), 0,704 (figé) ✔ | — |
| **Moniteur de calibration fondé sur les étiquettes (z < −3) comme disjoncteur** | retenu dans la référence en ligne | détecte régime, figé, venue, vol dans 100 % des graines, délai médian 411–505 pas ; **fausses alarmes 15 %/6000 pas iid** ✔ | correction de tests multiples non testée |
| **Séparation de causes (Q4)** | non atteinte (2/4) | rappel DATA_GAP 0,968 ; OOD 0,979 ; NO_SIGNAL 0,360 ; MODEL_UNCERTAINTY 0,149 ✔ | signaux plus riches (ensembles profonds, non testés) |
| **Détecteur PSI, MMD, test à deux échantillons par classifieur** | non exécutés (« discovered only ») | — | à tester |
| **Intégration** | aucune revendication | — | — |

**Verdict global du run 1 :** `LIMITED_UNCERTAINTY_METHODS_SUPPORTED` : « calibration + abstention fondée sur le coût dans des conditions stationnaires ou de décalage de covariables, recalibration à fenêtre glissante et ACI sous dérive, mais aucune méthode n'est robuste au choc de régime sans retard ; la calibration ne survit pas à la plupart des chocs ; la taxonomie de causes n'est séparable qu'à moitié ».

### 4.2 Run 2 (PR #24) — tableau de décisions du rapport (`09_ADJUDICATION.md`), avec mon statut de vérification

| Candidat | Décision du rapport | Base chiffrée | Statut de ma vérification |
|---|---|---|---|
| Température sur les logits, ajustée sur un bloc de calibration mis de côté | **ADOPT (référence)** | meilleur ou à égalité dans tous les tests stationnaires ; 1 paramètre ; préserve l'argmax | ✔ (ECE 0,027 / Brier 0,575 contre brut 0,249 / 0,684 ; égale Platt-sklearn d'après mon diagnostic) |
| Température à fenêtre glissante (W ≈ 600), étiquettes mûres seulement, refit ≈ 50 pas | **ADAPT** | récupère ≈ 80–100 % de l'excès d'ECE dû au choc ; gratuit en stationnaire ; nécessite un contrat de maturité et un réglage de fenêtre (bord de grille sur ELEC2) | ✔ (0,107 → 0,025 ; mais W = 600 n'est pas le meilleur sur les graines de réglage : W300 0,0174 contre 0,0179 ; voir 7) |
| Moniteur de perte réalisée sur étiquettes mûres | **ADOPT** comme alarme de choc | seul détecteur des chocs de concept/vol. | ✔ détection ; **✘ nuance** : déclenche dans 58 % des graines sans choc sur 3000 pas |
| Moniteurs NaN et valeur répétée/âge (DATA_GAP) | **ADOPT** | exacts, instantanés | ✔ (détection 1,00 / délai 100) ; mais F1 = 1,0 tautologique |
| Test à deux échantillons par classifieur de domaine | **ADAPT** | meilleur taux de fausse alarme des détecteurs statistiques (2,4 %) ; règle de persistance requise | ✔ 0,024 |
| Abstention par seuil de confiance (τ validé) sur confiance recalibrée en ligne | **ADAPT** | évite de grosses pertes sous chocs à espérance négative ; modeste en distribution ; dépend du gain | ✔ (régime −151 → −36) |
| ACI sur scores rolling (γ = 0,01), monitorage de couverture marginale | **ADAPT (surveillance seulement)** | 0,899 sous tous les chocs testés | ✔ |
| Bêta, isotonique, BBQ-lite | **PARK** | aucun gain sur la température ; isotonique le plus sensible à la fuite | ✔ |
| Conformal rolling / pondéré par récence | **PARK** | heuristique, sous-couverture transitoire | ✔ |
| Conformal pondéré avec rapport de densité estimé | **PARK** | 0,65 contre 0,90 | ✔ 0,651 |
| Abstention conformal singleton comme porte de trading (α = 0,2, signal faible) | **PARK** | écarte 58–76 % des décisions | ✔ (0,55–0,76) |
| Désaccord d'ensemble bootstrap comme score d'abstention/épistémique | **REJECT (tel qu'évalué)** | pas mieux que la probabilité max ; MODEL_UNCERTAINTY F1 0,07 ; ensembles profonds et MC-dropout non testés | ✔ |
| **Platt sur ensembles d'arbres sur-confiants** | **REJECT** | ECE 0,119 | **✘ non fiable : voir section 6/7 — le résultat provient très probablement d'un solveur maison non convergent ; avec un solveur standard Platt égale la température** (mon diagnostic sur 2 graines) |
| Revendications de couverture du split conformal sous dérive | **REJECT** | 0,77 contre 0,90 ; 0,54 pour un saut de vol. | ✔ |
| Intervalles Gaussiens | **REJECT** | 0,75 en stationnaire ; 0,58 sous choc | ✔ |
| Revendications de calibration statique à travers un changement de régime | **REJECT** | dérive d'ECE jusqu'à +0,19 | ✔ |

**Verdict global du run 2 :** `LIMITED_UNCERTAINTY_METHODS_SUPPORTED`.

### 4.3 Où les deux tableaux de candidats s'accordent et divergent (aperçu ; détail en section 8)

* **Accord** : calibrer par 1–2 paramètres suffit en stationnaire ; isotonique/binning n'aident pas ; fenêtre glissante/oubli nécessaire sous dérive (extensible faible) ; split conformal invalide sous dérive ; ACI = couverture marginale seulement ; ensembles/vetoes ne battent pas la confiance seule ; les défauts de données explicites sont détectables par des drapeaux, pas par la statistique ; le choc de concept n'est visible que par un moniteur à étiquettes.
* **Divergence** : Platt (run 1 : dans la référence ; run 2 : REJECT, artefact probable) ; température (run 1 : équivalente à Platt ; run 2 : ADOPT) ; « ADOPT » du moniteur de perte (run 2) contre « disjoncteur » (run 1) ; le run 2 déclare des détecteurs de choc d'entrée (domaine, KS) que le run 1 n'a pas (le run 1 n'a que Mahalanobis, écart-type d'ensemble, confiance, drapeaux, moniteur binomial).

---

## 5. Bloc final complet (reproduit tel quel) et explication ligne par ligne

### 5.1 Bloc final du run 1 (`reports/012_uncertainty_calibration/00_EXECUTIVE_SUMMARY.md`, branche `claude/uncertainty-calibration-v1`)

```
METHODS_DISCOVERED=31
METHODS_EXECUTED=26

STATIC_CALIBRATION_SUPPORTED=YES_STATIONARY_ONLY (NO across time on ELEC2)
ONLINE_CALIBRATION_SUPPORTED=YES_WITH_LIMITS (sliding-window/SGD, PIT-safe; expanding NO)
ABSTENTION_SUPPORTED=YES_WITH_LIMITS (not under concept/regime shift)
CONFORMAL_SUPPORTED=PARTIAL (ACI/weighted marginal coverage only; split invalid under drift; no decision-level guarantee)

CALIBRATION_SURVIVES_SHIFT=NO (2 of 6 shift types)
FALSE_CONFIDENCE_REDUCED=PARTIAL (yes vs raw and via online recalibration; not restored to iid level under shift)

BEST_SIMPLE_REFERENCE=Platt scaling on a held-aside calibration block + cost-derived confidence threshold + missing/stale flags
BEST_ONLINE_REFERENCE=Sliding-window Platt (delayed labels, PIT-asserted) + delayed-feedback ACI + label-based calibration monitor

FINAL_VERDICT=LIMITED_UNCERTAINTY_METHODS_SUPPORTED
```

| Clé | Ce que ça veut dire, en simple | Vérification |
|---|---|---|
| `METHODS_DISCOVERED=31` | 31 méthodes recensées dans le catalogue (le 32ᵉ, variantes tricheuses de fuite, est un outil de test exclu du compte) | ✔ (32 lignes dans `01_METHODS.md`, dont 1 exclue). **Le premier brouillon (commit WIP) disait 24 découvertes / 16 exécutées avec une autre convention de comptage** ; le compte a changé entre les commits, le rapport indique que c'est une convention de bookkeeping |
| `METHODS_EXECUTED=26` | 26 réellement exécutées (5 seulement listées : bayésien complet, CQR, AgACI/SAOCP/EnbPI/PID, PSI, tests à deux échantillons/MMD) | ✔ (27 « YES » dans le tableau, moins la ligne de fuite = 26) |
| `STATIC_CALIBRATION_SUPPORTED=YES_STATIONARY_ONLY (NO across time on ELEC2)` | Calibrer une fois marche seulement si le monde ne change pas ; sur ELEC2 (dérivant) non | ✔ (ECE 0,118 → 0,022 ; ELEC2 LR 0,103 → 0,153) |
| `ONLINE_CALIBRATION_SUPPORTED=YES_WITH_LIMITS (sliding-window/SGD, PIT-safe; expanding NO)` | Recalibrer en continu avec des étiquettes mûres marche, sauf à fenêtre extensible | ✔ (critère : gain ≥ 0,02 avec IC) ; limites = retard de reprise et instabilité de la pente |
| `ABSTENTION_SUPPORTED=YES_WITH_LIMITS (not under concept/regime shift)` | S'abstenir sous τ = 0,6 aide, sauf quand la relation change | ✔ |
| `CONFORMAL_SUPPORTED=PARTIAL (...)` | Les intervalles/ensembles garantis ne tiennent que par la couverture *marginale* (ACI/pondéré), pas pour la décision, et pas pour le split sous dérive | ✔ |
| `CALIBRATION_SURVIVES_SHIFT=NO (2 of 6 shift types)` | Sous les 6 chocs, la calibration figée ne survit que pour 2 (feature shift, données manquantes) | ✔ (17/20 et 19/20 graines survivantes) |
| `FALSE_CONFIDENCE_REDUCED=PARTIAL (...)` | La fausse confiance baisse par rapport au brut et grâce à la recalibration en ligne, mais ne revient pas au niveau iid sous choc | ✔ (0,024 iid contre 0,054–0,107 calibré sous choc) |
| `BEST_SIMPLE_REFERENCE=...` | La recette simple recommandée en externe : Platt + seuil de coût + drapeaux | recommandation, non un fait |
| `BEST_ONLINE_REFERENCE=...` | La recette en ligne : Platt glissant + ACI retardé + moniteur | recommandation |
| `FINAL_VERDICT=LIMITED_UNCERTAINTY_METHODS_SUPPORTED` | Verdict « supporté avec des limites nommées » selon le barème du protocole | ✔ cohérent avec le barème : statique/en ligne/abstention/conformal partiellement supportés, calibration ne survivant pas à la plupart des chocs (il ne pouvait donc pas être « REFERENCE_SUPPORTED ») |

### 5.2 Bloc final du run 2 (`reports/012_uncertainty_calibration/09_ADJUDICATION.md`, branche `claude/uncertainty-calibration-v1-b`)

```
METHODS_DISCOVERED=52
METHODS_EXECUTED=33

STATIC_CALIBRATION_SUPPORTED=YES_IN_STATIONARY_REGIME_ONLY (temperature scaling; large gain for over-confident learners, none for calibrated ones)
ONLINE_CALIBRATION_SUPPORTED=YES (sliding-window/decayed temperature with matured labels; synthetic 12 seeds + ELEC2; needs label-delay contract)
ABSTENTION_SUPPORTED=PARTIAL (modest ~1.4x lift over random; helpful for risk control under negative-EV shift with online-calibrated confidence; utility-negative beyond ~5% abstention in a stationary positive-EV payoff; ensemble-disagreement not supported)
CONFORMAL_SUPPORTED=PARTIAL (valid only for exchangeable data; ACI-type gives empirical long-run marginal coverage under drift; no conditional or finite-sample time-series validity claimed)

CALIBRATION_SURVIVES_SHIFT=NO_FOR_STATIC; YES_WITH_LAG_FOR_ONLINE_RECALIBRATION
FALSE_CONFIDENCE_REDUCED=YES (confident-wrong mass 0.34->0.07 by calibration; 0.13->0.03 under shift by online recalibration; not eliminated for OOD or concept shift without explicit gates)

BEST_SIMPLE_REFERENCE=temperature_scaling_on_logits_fit_on_held_out_calibration_split + validation_chosen_confidence_threshold
BEST_ONLINE_REFERENCE=sliding_window_temperature_scaling(W=600,refit_every=50,label_maturity_delay=10) + realised_loss_monitor; ACI_on_rolling_scores(gamma=0.01) for marginal interval coverage monitoring

FINAL_VERDICT=LIMITED_UNCERTAINTY_METHODS_SUPPORTED
```

| Clé | Ce que ça veut dire | Vérification |
|---|---|---|
| `METHODS_DISCOVERED=52`, `METHODS_EXECUTED=33` | 52 méthodes recensées, 33 exécutées, 19 seulement listées | ✔ (`methods_counts.json` et comptage du tableau) |
| `STATIC_CALIBRATION_SUPPORTED=YES_IN_STATIONARY_REGIME_ONLY (...)` | La température règle un modèle sur-confiant en stationnaire (gain énorme) et ne sert à rien à un modèle déjà bon | ✔ ; **la mention implicite « Platt échoue » n'est pas dans ce bloc mais dans le rapport 03 (artefact probable, section 7)** |
| `ONLINE_CALIBRATION_SUPPORTED=YES (...; needs label-delay contract)` | Recalibrer en continu sur les étiquettes mûres marche, à condition qu'un contrat de délai d'étiquette existe | ✔ (0,107 → 0,025) ; le « YES » sans réserve est plus optimiste que le « YES_WITH_LIMITS » du run 1 alors que les chiffres sont proches |
| `ABSTENTION_SUPPORTED=PARTIAL (...)` | Gain modeste (~1,4 ×) ; l'abstention protège sous choc négatif si la confiance est recalibrée ; elle fait perdre de l'utilité au-delà de ~5 % en monde rentable | ✔ (utilité 405,3 → 392,1 à 25 % ; −151 → −36) |
| `CONFORMAL_SUPPORTED=PARTIAL (...)` | Comme le run 1 : marginal empirique seulement | ✔ |
| `CALIBRATION_SURVIVES_SHIFT=NO_FOR_STATIC; YES_WITH_LAG_FOR_ONLINE_RECALIBRATION` | Figée : non. En continu : oui, avec un retard | ✔ ; mais le « YES_WITH_LAG » ne vaut pas pour le choc de régime où le modèle est simplement faux (Brier 0,665) |
| `FALSE_CONFIDENCE_REDUCED=YES (...)` | La masse « confiant et faux » passe de 0,34 à 0,07 par calibration et de 0,13 à 0,03 sous choc par recalibration en ligne, mais pas éliminée pour OOD ou choc de concept | ✔ (0,336 → 0,073 ; 0,127 → 0,025) |
| `BEST_SIMPLE_REFERENCE=temperature_scaling_on_logits_... + validation_chosen_confidence_threshold` | Recette simple recommandée | recommandation |
| `BEST_ONLINE_REFERENCE=sliding_window_temperature_scaling(W=600,refit_every=50,label_maturity_delay=10) + realised_loss_monitor; ACI_on_rolling_scores(gamma=0.01) ...` | Recette en ligne recommandée avec ses paramètres gelés | recommandation ; paramètres = `frozen_config.json` ✔ |
| `FINAL_VERDICT=LIMITED_UNCERTAINTY_METHODS_SUPPORTED` | Même verdict que le run 1 | ✔ cohérent avec les ADOPT/ADAPT/PARK/REJECT |

**Remarque de forme.** Le bloc final du run 2 est écrit sous forme de lignes de texte (sans clôture de code) à la fin de `09_ADJUDICATION.md`, tandis que celui du run 1 est dans un bloc de code à la fin de `00_EXECUTIVE_SUMMARY.md` ; le run 2 le renvoie aussi à `09_ADJUDICATION.md` depuis sa synthèse (« full final block in 09_ADJUDICATION.md »). Les deux ont les mêmes onze clés, sauf que les valeurs des lignes diffèrent (par exemple `ONLINE_CALIBRATION_SUPPORTED` : `YES_WITH_LIMITS` contre `YES`).

---

## 6. Contrôles de validité

### 6.1 Fuite / lookahead

| Aspect | Run 1 | Run 2 |
|---|---|---|
| Modèle de délai | étiquette du pas j révélée à j + h ; h = 10 (synthétique), 1 ou 48 (ELEC2) | étiquette de la ligne s disponible à s + H, H = 10 ; refit toutes les R = 50 ; blocs servis avec l'ajustement du début de bloc |
| Vérification | booléen `pit_ok` = `audit_ok &= (hi - 1 + h <= s)`, calculé **à partir des mêmes variables** que celles qui délimitent les données ; 216 exécutions PIT-safe, toutes True ✔ | **test de perturbation** : on corrompt toutes les étiquettes non mûres à un instant de coupe, et on vérifie que les probabilités déjà servies sont **bit-à-bit identiques** ; on vérifie aussi que les variantes tricheuses changent bien (la harnais est sensible). **Exécuté par moi : 4 PASS en 6 s** ✔ |
| Couverture des tests | aucun test unitaire | (1) calibrateurs en ligne (bêta, température, isotonique × fenêtre, extensible, decay) ; (2) flux conformal (split, rolling, pondéré, ACI split/rolling) ; (3) couverture split iid (300 répétitions, moyenne à ±0,01 de 0,9) ; (4) préservation de l'argmax des cartes top-label |
| Variantes tricheuses | `leak_block` (calibré sur le bloc qu'il prédit : fuite forte) et `leak_global` (sur tout le futur) | `leak_h0` (H = 1) et `leak_peek` (voit un bloc de 50 lignes en avant, H = 1) : fuites **légères** |
| Ce que montrent les tricheuses | `leak_block` : pire tronçon 0,048 contre 0,104 honnête (≈ 2× plus plat) ; `leak_global` fait *pire* (0,119) — une carte globale ne suit pas le changement | température : ECE 0,0249 honnête, 0,0246 (h0), 0,0255 (peek) : quasi rien ; isotonique : Brier 0,694 honnête contre 0,686 (peek) : inflation ; ELEC2 LR isotonique 0,355 contre 0,339 (rapport, non recalculé `?`) |
| Ce qui n'est pas couvert | étiquettes à horizon chevauchant (labels de rendement futur, triple-barrière), délai variable | idem, et jitter de délai ; les autres chemins (turnover, abstention, détection de perte) ne sont pas dans les tests, mais la fenêtre de perte utilise `hi = b − 10` ✔ à la lecture |

**Verdict de validité.** Le contrôle du run 2 est nettement plus probant (test de perturbation) que celui du run 1 (assertion arithmétique). Cela ne veut pas dire que le run 1 fuit : à la lecture du code (`run_online`, `known_end = s − h + 1`, SGD avec `j = t − h` mis à jour *après* la prédiction), je n'ai pas trouvé de fuite. Mais l'assertion ne le *prouve* pas.

### 6.2 Déterminisme et reproductibilité vérifiés par moi

| Test | Résultat |
|---|---|
| Run 1 : `exp_static.py` relancé depuis un `git archive` de la branche (sauf chemin de sortie redirigé) | 28,7 s ; `static_raw.csv` **identique octet pour octet** (`cmp`), 1586 lignes, écart max 0,0 ✔ |
| Run 1 : `exp_taxonomy.py` | 29,6 s ; `taxonomy_raw.csv` (101 883 lignes) **identique octet pour octet** ✔ |
| Run 2 : `tests/test_no_lookahead.py` | 4 PASS, 6,1 s ✔ |
| Run 2 : `run_static.py 0-1 1.0` (graine 0, LR+GBM, 8 scénarios) | 53,8 s ; 288 lignes de métriques ; **écart maximum 0,0** contre `static_hold_0-6_metrics.csv` pour la graine 0 ✔ |
| Autres composantes (en ligne, conformal, abstention, diagnostic, public) | **non relancées** (`?`) — coût 115 s/graine (en ligne), 73 s/graine (conformal 6 graines = 437 s) etc. |

### 6.3 Contrôles négatifs / positifs

* **Positifs (là où la théorie s'applique)** : run 1 `iid_control` : toutes les méthodes conformal à 0,796–0,802 ✔ ; oracle ECE 0,017 comme plancher d'estimation. Run 2 : témoin iid split 0,902 ± 0,006 ✔ ; test unitaire de couverture split iid.
* **Négatifs / témoins** : run 1 : contrôle stationnaire de l'en ligne = expérience statique (0,013) — c'est ce qui a révélé le bug de calibrateur ajusté sur l'entraînement ; classes « bruit pur » x7 > 1 (vraie proba 0,5). Run 2 : scénario `none` ; `iid_control`; variantes tricheuses ; ablations du diagnostic (sans drapeaux DATA_GAP → macro F1 0,325 ✔ ; sans OOD 0,479 ✔ ; sans MI 0,585 ✔ ; confiance seule 0,181 ✔).
* **Ce qui manque** : dans les deux runs, aucune comparaison croisée avec une bibliothèque de référence (MAPIE, netcal, crepes, puncc) ; aucune vérification de la littérature (théorèmes recopiés de mémoire ou titres seulement).

### 6.4 Erreurs corrigées en cours de route et écarts au protocole

**Run 1 (`08_FAILURE_MODES.md`, section « Process failures ») :**

1. **Fuite de définition d'étiquette sur ELEC2** : prédire y_t à partir de `prix − moyenne des 48 précédents` donnait un Brier de 0,004 (invraisemblable) parce que l'étiquette *est* « prix au-dessus de la moyenne mobile ». Tâche redéfinie en prévision de y_{t+1} ; tous les chiffres des rapports 03/04/06 utilisent la version prévision. *(Le premier essai n'est pas dans le dépôt ; non vérifiable `?`, mais l'argument est correct : voir 7.)*
2. **Calibrateur ajusté sur des lignes d'entraînement (bug en ligne)** : `run_online` ajustait sur `p[:t0]` (entraînement + calibration) ; le HGB est *en échantillon* sur l'entraînement, donc Platt statique était ajusté sur des données artificiellement confiantes (ECE stationnaire 0,117). Corrigé avec `c0` (début du bloc de calibration) ; le contrôle stationnaire redonne 0,013 comme l'expérience statique. **✔ Vérifié dans Git** : le diff `73a1650 → 40a9721` de `ulib.py` montre exactement ce changement (`init = Platt().fit(p[c0:t0], y[c0:t0])`), et `online_raw.csv` a été régénéré (288 lignes modifiées). C'est la seule expérience dont les CSV changent entre les deux commits, avec l'ajout de `conformal_*.csv`, `shift_riskcov.csv`, `shift_survival.csv`.
3. Sur-souscription CPU : premiers runs bloqués (charge ≈ 20) ; relancés avec `OMP_NUM_THREADS=1`, « résultats inchangés (md5 identique de `shift_cal.csv`) » `?` (ancien md5 non conservé ; mais mon re-run partiel donne bien des fichiers identiques aux fichiers du dépôt).
4. Un `pkill -f` accidentel a tué son propre shell une fois, sans effet sur les résultats.

*Écarts au protocole du run 1 (ma lecture)* : (a) le protocole dit « validation » servir à régler τ ; en pratique τ est dérivé du coût et la validation n'est utilisée que pour l'affichage statique (`part = val`) ; (b) le conformal ELEC2 utilise des fenêtres de 1000 pas ; (c) le comptage de méthodes est passé de 24/16 (commit WIP) à 31/26 (final) ; (d) l'écart de formulation du constat 3 (section 3.A.0).

**Run 2 (`02_PROTOCOL.md`, divulgations)** : (i) bug de masque dans `regime_transition` corrigé avant toute sortie test ; (ii) GBM 150 → 100 itérations et ensembles statiques 5 membres pour la durée, avant tout test ; (iii) banc d'abstention conçu après avoir vu les tables statique et en ligne ; (iv) 4 graines de réglage, 12 de test. **Écarts que je constate en plus** : (a) le rapport 04 dit que W = 600 « a donné le meilleur compromis ECE/Brier » alors que les CSV de réglage montrent W = 300 meilleur en ECE (0,0174 contre 0,0179) et demi-vie 150 meilleure que 400 (0,0165 contre 0,0196 ; Brier 0,6155 contre 0,6155) (✘ mineur : écarts « petits »; le rapport dit lui-même que les voisins diffèrent peu) ; (b) le rapport 04 cite « largest added turnover +0.023 » alors que le max (LR) est +0.039 ✘ mineur ; (c) la conclusion « Platt échoue sur confiances saturées » (voir ci-dessous). *(À noter : la notation « seeds 100-104 » du README est semi-ouverte comme « 0-6 » et désigne bien les graines 100 à 103, conformément à la config ✔ — ce n'est pas un écart.)*

### 6.5 Nouvelle erreur trouvée par moi dans le run 2 : le résultat « Platt échoue » est très probablement un artefact du solveur

Le rapport 03 (et `09_ADJUDICATION.md` : « Platt scaling on over-confident tree ensembles : REJECT — ECE 0,119 ») explique l'échec de Platt sur GBM par la saturation des confiances (logit ≈ ±14) qui empêcherait une sigmoïde à 2 paramètres de représenter la courbe de fiabilité, et l'étiquette *INFERENCE (non diagnostiqué séparément)*. J'ai fait le diagnostic (script scratch, `bench/uncertainty_v1/py` du run 2 réutilisé sans modification) sur les graines 0 et 1 du scénario `none`, GBM, avec la même confiance top-label et le même codage :

| graine | solveur du dépôt (`fit_logistic`, Newton à pas borné ±3, 50 itérations) | `sklearn LogisticRegression(C=1e4)` sur les mêmes points | ECE Platt (solveur dépôt) | ECE Platt (sklearn) | ECE température | ECE brut |
|---|---|---|---|---|---|---|
| 0 | (pente, ordonnée) = (1,596 ; −2,642) | (0,327 ; −0,449) | 0,101 | **0,014** | 0,015 | 0,251 |
| 1 | (2,090 ; −2,600) | (0,374 ; −0,583) | 0,144 | **0,021** | 0,012 | 0,238 |

Les deux ajustements devraient donner la même droite (c'est le même problème convexe) ; ils ne le font pas. **Le solveur maison ne converge pas vers l'optimum sur ces confiances quasi-saturées** (part de confiances > 0,999 : 0,8 % et 3,4 %). Avec un solveur standard, Platt (top-label) fait **aussi bien que la température** (0,014–0,021 contre 0,012–0,015). Conséquences : (1) le `REJECT` de Platt du run 2 et la phrase « Platt failed on saturated confidences (ECE 0.119) » ne sont **pas soutenus** ; (2) la cause est logicielle, pas statistique ; (3) l'affirmation reste donc à l'état de bug probable — mon diagnostic porte sur 2 graines et 1 scénario, il n'a pas été refait sur les 12 graines (`?`), et je n'ai pas comparé les log-vraisemblances des deux ajustements. Le même solveur sert aussi à bêta (`fit_logistic` à 2 variables) ; bêta sort à 0,029, donc correct ; son optimalité n'est pas vérifiée (`?`). Cela **réconcilie** les deux runs : le run 1 (ajustement scikit-learn sur le logit) trouve Platt ≈ température (0,022 et 0,022).

### 6.6 Tableau de vérification : chiffres clés des rapports contre les résultats bruts

**Run 1 (recalcul sur `results/*.csv` de la branche ; voir `shift_*`, `static_raw`, `online_raw`, `conformal_*`, `taxonomy_*`)**

| # | Chiffre du rapport | Valeur recalculée | Statut |
|---|---|---|---|
| 1 | HGB brut : ECE 0,118 ; FCR 0,119 (`03`) | 0,118 ; 0,119 | ✔ |
| 2 | Platt/température/bêta : ECE 0,022 ; oracle 0,017 | 0,022 / 0,022 / 0,022 ; 0,017 | ✔ |
| 3 | ELEC2 LR : brut 0,103 ; Platt 0,153 ; température 0,168 | 0,103 ; 0,153 ; 0,168 | ✔ |
| 4 | ELEC2 HGB : brut 0,107 ; température 0,068 | 0,107 ; 0,068 | ✔ |
| 5 | Survie : 0/20, 1/20, 17/20, 19/20, 0/20, 7/20 | 0, 1, 17, 19, 0, 7 (sur 20) | ✔ |
| 6 | ECE et FCR par choc (HGB Platt), 7 lignes | 0,021/0,024 ; 0,141/0,107 ; 0,172/0,096 ; 0,036/0,037 ; 0,030/0,023 ; 0,076/0,054 ; 0,068/0,040 | ✔ |
| 7 | AUROC (24 valeurs) | identiques à 3 décimales | ✔ |
| 8 | Moniteur : alarme iid 0,15 ; régime 1,0 / 454,5 ; feature 0,5 / 1203,5 | identiques | ✔ |
| 9 | P1 iid : couverture 0,686 ; risque 0,256 ; évitées 0,449 ; gardées 0,750 ; utilité 0,198 | identiques ; P0 : 0,318 / 0,163 | ✔ |
| 10 | Régime : risque 0,486 → 0,482, utilité −0,171 → −0,112 | identiques | ✔ |
| 11 | En ligne abrupt : ECE statique 0,100 ; glissant 0,017 ; pire tronçon 0,182 → 0,104 ; SGD 0,064 | identiques | ✔ |
| 12 | Gains critère : 0,079 ± 0,040 ; 0,125 ± 0,063 ; 0,073 ± 0,014 ; extensible 0,031 ± 0,016 / 0,026 ± 0,010 | identiques | ✔ |
| 13 | `pit_ok` True sur 216 exécutions | True ; 216 | ✔ |
| 14 | ELEC2 en ligne : statique HGB 0,177 / LR 0,283 → glissant 0,044 / 0,057 ; pente sd 0,782 | identiques ; h = 48 ≈ h = 1 (0,045 / 0,056 ; pente 0,778) | ✔ |
| 15 | Conformal α = 0,2 : abrupt split 0,733 / 60 % ; ACI 0,800 ; vol split 0,723 ; ELEC2 rolling 10,6 % | identiques | ✔ |
| 16 | Régression : split vol 0,512 ; rampe 0,452 ; housing 0,498 / 0,799 | 0,512 ; 0,452 ; 0,498 ; 0,799 | ✔ |
| 17 | Matrice de confusion Q4 (25 cases) | identique | ✔ |
| 18 | Constat 3 de la synthèse : « fausse confiance ×2–4,5 sous feature shift et vol jump » | feature shift ×1,5 (0,037) ; vol jump ×4,5 (0,107) ; stale ×2,3 (0,054) | **✘ mineur** (attribution) |
| 19 | « 500-step rolling windows » pour ELEC2 | le code utilise 1000 pas pour ELEC2 | **✘ mineur** |
| 20 | « Lookahead audit passes » | arithmétique interne uniquement (voir 6.1) | ✔ chiffre exact, mais **portée limitée** |
| 21 | Bug de calibrateur ajusté sur l'entraînement corrigé | diff Git visible ; CSV en ligne régénérés | ✔ |
| 22 | md5 identique de `shift_cal.csv` avant/après re-run CPU | ancien md5 absent | ? |
| 23 | Effets ECE des figures/PNG, littérature | figures non ouvertes ; littérature non relue | ? |

**Run 2 (recalcul sur `results/*.csv` de la branche)**

| # | Chiffre du rapport | Valeur recalculée | Statut |
|---|---|---|---|
| 1 | GBM brut / température / Platt : ECE 0,249 / 0,027 / 0,119 ; CWM 0,336 / 0,073 / 0,153 | identiques | ✔ (mais voir 6.5 pour Platt) |
| 2 | Δ appariés GBM température : −0,109 ± 0,003 ; −0,222 ± 0,003 ; −0,263 ± 0,008 | identiques | ✔ |
| 3 | Dérive d'ECE statique (7 × 2 valeurs) | identiques | ✔ |
| 4 | ECE en ligne après choc (8 × 4 valeurs GBM) | identiques | ✔ |
| 5 | Moyennes 7 chocs : ECE 0,107 → 0,025 ; CWM 0,127 → 0,025 ; Brier 0,670 → 0,641 ; LR 0,117 → 0,035 | identiques | ✔ |
| 6 | Coût stationnaire : ECE 0,020 vs 0,025 ; Brier 0,577 vs 0,576 | identiques | ✔ |
| 7 | Fuite : Brier isotonique 0,694 vs 0,686 (GBM) ; 0,634 vs 0,622 (LR) | identiques | ✔ |
| 8 | ELEC2 : GBM ECE 0,164 → 0,021 ; Brier 0,471 → 0,386 ; LR 0,189 → 0,043 ; LR statique pire que brut (Brier 0,456 → 0,478) | identiques | ✔ |
| 9 | Abstention budgets 10/25/40 % (6 valeurs GBM, 4 LR) ; τ val 4,9 % ; 405,3 → 407,4 | identiques | ✔ |
| 10 | Abstention sous choc : régime −151 → −36 ; figé 122 → 146 ; feature 120 → 147 ; vol 414 → 403 | −151,3 → −35,7 ; 121,9 → 146,1 ; 119,9 → 146,8 ; 413,8 → 402,7 | ✔ |
| 11 | Agrégat tous chocs : 4,6 % / +6,8 ; 17,9 % / +22,1 | identiques (avec `none` inclus) | ✔ (le libellé « all shifts » inclut `none`) |
| 12 | Régression sous choc : split 0,766 ; rolling 0,890 ; ACI-rolling 0,899 ; ACI-split infini 0,093 ; vol split 0,538 ; Gaussien 0,368 ; régime split 0,729 | identiques | ✔ |
| 13 | LAC α = 0,2 LR : split 0,668 ; ACI 0,796–0,800 ; taille 2,05 ; singleton 0,24–0,25 ; précision 0,63 | identiques | ✔ |
| 14 | Détection : tableau 7 × 6 + fausses alarmes 2,4 / 4,8 / 5,4 / 7,7 % | identiques | ✔ |
| 15 | Diagnostic : P/R/F1 (5 classes) ; macro F1 0,604 ; fausse étiquette 5,9 % ; erreur par cause | identiques ; ablations 0,325 / 0,479 / 0,585 / 0,181 ✔ | ✔ |
| 16 | AURC (16 valeurs) | identiques | ✔ |
| 17 | ELEC2 conformal par bloc : split 0,59–0,87 ; ACI-rolling 0,785–0,812 | 0,588–0,866 ; 0,785–0,812 | ✔ |
| 18 | California : iid 0,901 ; décalage 0,589 ; pondéré 0,651 ; Gaussien 0,546 | identiques | ✔ |
| 19 | credit-g GBM 0,210 → 0,054 ; LR 0,092 → 0,060 | identiques | ✔ |
| 20 | « largest added turnover +0.023 ; réduction jusqu'à −0.10 » | GBM +0,023 / −0,101 ; LR +0,039 / −0,192 | **✘ mineur** (limité au GBM) |
| 21 | « W = 600 meilleur compromis ECE/Brier (tuning) » | W300 ECE 0,0174 < W600 0,0179 ; HL150 0,0165 < HL400 0,0196 | **✘ mineur** |
| 22 | « Platt échoue (saturation) » | artefact de solveur probable (6.5) | **✘ explication non soutenue** |
| 23 | γ = 0,02 : infinis 4 % → 9 % | 4,7 % (γ = 0,01) → 10,3 % (γ = 0,02) sur les graines de réglage | ✔ approx. |
| 24 | Gel de `frozen_config.json` avant le test | un seul commit, aucun horodatage | ? |
| 25 | Ordre de grandeur des durées (logs) | cohérent avec mes re-runs (54 s pour la graine 0) | ✔ |
| 26 | Figures PNG | non ouvertes | ? |

**Bilan : 23 lignes de vérification pour le run 1 (dont 2 `?`) et 26 pour le run 2 (dont 3 `?`) ; 0 écart matériel sur les chiffres des rapports ; écarts mineurs de formulation ou de portée : 2 (run 1) et 3 (run 2 : borne de turnover, « meilleur compromis », γ approximatif) ; 1 explication causale non soutenue (Platt, run 2).**

---

## 7. Critique indépendante

### 7.1 Ce que les deux runs font bien

* Chiffres des rapports **fidèles aux CSV** (aucune erreur de recopie détectée sur ~50 contrôles) ; expériences relançables et déterministes ✔.
* Honnêteté des limites (les deux runs rappellent que les résultats sont synthétiques, que la littérature est non relue, que les gains sont jouets).
* Le run 2 a un vrai harnais anti-fuite, un monde à 3 classes, des chocs variés, un test de diagnostic de causes plus riche, des jeux publics supplémentaires et une distinction claire entre réglage et test.
* Le run 1 a un critère de décision pré-déclaré chiffré (facilitant l'audit) et le contrôle négatif de fuite très parlant (triche « bloc »).

### 7.2 Points faibles communs

1. **Tout le poids repose sur des mondes synthétiques écrits par les auteurs.** Les chocs sont stylisés ; la « vérité » est connue ; aucune donnée financière (ni crypto, ni or, ni FX, ni carnet d'ordres) n'est utilisée. ELEC2 est un prix d'électricité, pas un problème BUY/SELL. Les chiffres ne sont **pas** des performances de trading.
2. **Le gain de décision est un jouet** (±1/coût 0,2 ; ou +1/−1/−0,3/0). Le résultat d'abstention en dépend directement : dans le run 1 τ = 0,6 est le seuil de rentabilité *par construction* ; dans le run 2 l'abstention est presque toujours coûteuse hors choc parce que même les trades peu confiants ont une espérance positive.
3. **Statistique fragile pour les comparaisons fines** : 8 graines (run 1 en ligne/conformal) ou 12 graines (run 2) ; intervalles normaux/t partageant le générateur ; aucune correction de comparaisons multiples ; ELEC2 = une réalisation, pas d'IC.
4. **Aucune vérification croisée avec MAPIE / netcal / crepes** ; toutes les implémentations sont maison (coût de maintenance, risque de bug — le cas Platt du run 2 en est une illustration).
5. **Littérature non relue** : les théorèmes cités (Barber, Gibbs & Candès, Tibshirani…) sont de mémoire (run 1) ou identifiés par titre (run 2).
6. **Délai d'étiquette fixe et connu** (H = 10) : pas de délai variable, pas d'horizon de rendement chevauchant ; c'est précisément le point critique pour un système PIT (les deux runs le disent).
7. **Signal très faible en 3 classes (run 2)** : la précision des singletons conformal (≈ 0,63–0,74) reflète la difficulté du monde, pas seulement les méthodes.

### 7.3 Run 1 — critiques spécifiques

1. **Pré-enregistrement non prouvable.** Le protocole « déclaré avant de regarder les chiffres » a été committé avec les CSV statique/choc/taxonomie (même commit `73a1650`). Le texte est identique au final, ce qui *ne contredit pas* la déclaration, mais ne la prouve pas (`?`).
2. **Assertion `pit_ok` tautologique** (6.1). Le résultat « 216 exécutions, toutes propres » est vrai mais peu informatif.
3. **Seuils de décision « à la main » avec effets de bord** : « survit » = ECE ≤ 0,05 et FCR ≤ 1,5 × iid + 0,01. Avec ces valeurs, feature_shift (0,036) et missing (0,030) passent ; venue_change (0,068 ; 7/20 graines) et stale (0,076 ; 0/20) échouent. Un seuil d'ECE à 0,07 ferait passer venue en moyenne (mais 7 graines sur 20 seulement), et à 0,08 stale passerait sur l'ECE tout en échouant encore sur le critère FCR (0,054 contre un plafond de 1,5 × 0,024 + 0,01 = 0,046). Le résultat « 2 sur 6 » est donc **sensible au seuil** (le rapport le reconnaît en limite 10). Il est en outre mesuré sur HGB+Platt seulement.
4. **Bord de grille / choix ad hoc** : W = 1000 (2000 ELEC2), refit 250, lr SGD 0,02, γ = 0,005, λ = 0,998, τ = 0,6 : fixés sans exploration ni analyse de sensibilité. Aucune « réglage sur validation » ; donc aucun sur-ajustement, mais aucune assurance de proximité de l'optimum.
5. **Choc appliqué d'un bloc** : `regime_transition` inverse les coefficients dès le début du bloc test (pas de transition progressive) ; `feature_shift` **recalcule l'étiquette avec les features décalées** (vrai décalage de covariables : c'est la raison pour laquelle la calibration y « survit », alors que dans le run 2 l'étiquette reste issue des features d'origine, et la calibration s'y effondre).
6. **Instabilité de la pente (ELEC2-LR, sd 0,78)** : non traitée (lissage/plafonnement non testés) alors que la référence en ligne recommandée en dépend.
7. **Écart de portée de la conclusion sur les conformal** : « précision singleton 0,65–0,73 bien en dessous de 0,80 » — la précision maximale accessible est bornée par la précision de Bayes (≈ 0,71 dans ce monde) ; la comparaison avec 0,80 est un contraste de définitions (couverture sur toutes les lignes vs précision sur les singletons), utile pédagogiquement mais pas une défaillance de la méthode.
8. **Jeu de données embarqué** : `data/elec2.csv` (≈ 3 Mo) est committé ; statut de redistribution non vérifié (`?`) — le run 2 télécharge à l'exécution et ne redistribue rien.
9. **Le comparateur `matched_conf_risk` est calculé sur les mêmes lignes** (favorable par construction : c'est un classement par confiance « à l'oracle » du volume réalisé) ; usage assumé par le rapport.
10. **Écart entre rapport et résultats bruts** : deux mineurs (constat 3 de la synthèse ; fenêtres ELEC2 de 1000).

### 7.4 Run 2 — critiques spécifiques

1. **Le REJECT de Platt repose sur un solveur non convergent** (6.5). C'est l'écart le plus lourd de toute la lane : une décision « REJECT » et une phrase d'explication sont fondées sur un artefact logiciel. Le run 2 aurait dû comparer avec scikit-learn (coût : trois lignes).
2. **Gel des hyper-paramètres non prouvable** : commit unique ; pas de horodatage dans les journaux. Le rapport reconnaît que le banc d'abstention a été dessiné après avoir vu des résultats de test ; ce n'est pas du réglage, mais c'est une liberté du chercheur.
3. **Choix W = 600 / demi-vie 400 non optimaux sur les graines de réglage** (et présentés comme « meilleur compromis ») ; sur ELEC2, W = 2000 et demi-vie 1000 au bord de la grille : une fenêtre plus longue pourrait faire mieux (F19).
4. **Le moniteur de perte « ADOPT comme alarme de choc » a une spécificité mal quantifiée** : fausse alarme dans 58 % des graines sur 3000 pas sans choc (délai médian 700 pas), contre 4,8 % de fausses alarmes par bloc avant le choc. L'unité de mesure des deux nombres diffère (par graine sur 3000 pas contre par bloc de 100 pas) et le rapport ne les concilie pas. La comparaison avec le moniteur du run 1 (15 % par 6000 pas à z < −3) suggère que le seuil « maximum sur validation » du run 2 est plus agressif.
5. **Tautologies partielles** : DATA_GAP (vérité = faute injectée = drapeau) ; NO_SIGNAL (vérité = probabilité oracle max < 0,5 ; règle = confiance calibrée < 0,5 : les deux mesurent presque la même chose). Le F1 de 0,71 pour NO_SIGNAL n'est pas indépendant.
6. **Fuites simulées trop douces** : `leak_h0` (H = 1) et `leak_peek` (50 lignes) flattent peu la température ; cela ne prouve pas que « la fuite ne compte pas » — seulement que les fuites *testées* sont légères. Le run 1 a une fuite forte (bloc) et voit un effet ×2.
7. **Métriques non comparables au run 1** : Brier multi-classes (somme sur 3 classes), ECE 10 classes de largeur égale (plancher ≈ 0,04 à n = 500 d'après le rapport), FCR défini par conditionnelle à conf ≥ 0,6 : les tableaux ne se comparent pas nombre à nombre (section 8).
8. **IC t sur 12 graines de mondes qui partagent la même conception** (les scénarios d'une même graine sont corrélés) : optimistes ; les écarts < 0,01 d'ECE sont qualifiés de bruit par le rapport lui-même.
9. **Détection : seuils « max sur validation »** ad hoc (fausses alarmes par bloc 2–8 %), non contrôlés.
10. **Nowcast ELEC2** : le run 2 prédit l'étiquette de la ligne courante à partir de ses features (incluant le prix courant) ; le run 1 a montré qu'un lien de définition existe entre l'étiquette et le prix vs moyenne mobile. La précision de test (0,70–0,71) n'indique pas de fuite flagrante (le run 1 sur la version « fuite » obtenait un Brier de 0,004), mais la tâche n'est pas une prévision et ne doit pas être lue comme telle.
11. **Contradictions internes** : aucune contradiction matérielle trouvée entre rapports 00–10 du run 2 ; incohérences mineures : borne de turnover limitée au GBM ; statement « meilleur compromis » contredit par les tables de réglage.

### 7.5 Ce que les chiffres ne prouvent PAS

* Que ces méthodes marchent sur des données de marché réelles (aucune donnée financière testée).
* Que le seuil τ = 0,6 (run 1) ou les budgets (run 2) soient adaptés à un vrai coût de transaction, au slippage ou à la sélection adverse.
* Que la recalibration en ligne soit stable face à des étiquettes à horizon chevauchant ou à délai variable (les deux runs le disent).
* Qu'ACI ou les variantes de récence aient une garantie avec étiquettes retardées (aucun théorème vérifié).
* Que la séparation NO_SIGNAL / MODEL_UNCERTAINTY soit impossible en général : seule une classe d'ensembles bootstrap du même apprenant a été testée (ensembles profonds, MC-dropout non testés).
* Que « ADOPT » signifie « compatible avec AurumShift » : non, c'est un verdict externe.

---

## 8. Comparaison point par point des deux runs (section obligatoire)

**Principe de lecture.** Les deux runs répondent aux mêmes quatre questions (Q1 à Q4) avec le même verdict final, mais sur des mondes simulés **différents** et avec des **définitions de métriques différentes**. Un même mot (« ECE », « fausse confiance », « couverture ») ne désigne donc pas exactement la même quantité. Je compare d'abord les conceptions (8.0), puis les résultats côte à côte (8.1 à 8.9), puis les accords et les divergences avec leurs causes probables (8.10 et 8.11). Tous les chiffres viennent des rapports et des CSV lus (✔ = recalculés).

### 8.0 Ce qui diffère dans la conception (à garder en tête pour tout le reste)

| Élément | Run 1 | Run 2 | Conséquence |
|---|---|---|---|
| Problème | **binaire** haut/bas ; abstention = HOLD sur un appel binaire | **3 classes** SELL/HOLD/BUY (FLAT 46 %) | le run 2 est plus proche de BUY/SELL/HOLD ; signal plus faible |
| Modèle de génération | logistique à 8 features + terme croisé ; précision de Bayes ≈ 0,71 ; zone `x7 > 1` = bruit pur | rendement latent linéaire + volatilité en grappes (Markov cachée) + cluster rare ; oracle exact | run 2 : non-échangeabilité plus réaliste (vol. en grappes) |
| Modèles | LR, GNB, HGB (300 it., sur-confiant) | LR sur [x, x²], HGB (100 it., taux 0,3, sur-confiant) | HGB différent : degré de saturation des confiances différent |
| Graines | 20 (choc, taxonomie, statique), 8 (en ligne, conformal) ; pas de graines de réglage | 12 test + 4 réglage (magnitude 0,6) | run 2 sépare mieux réglage et test |
| Chocs | 6 (vol, régime, feature, manquant, figé, venue) | 7 (+ rare_cluster) + `none` ; magnitudes paramétrées | mêmes noms, **définitions différentes** (8.3) |
| Début du choc | tout le bloc test est choqué (comparaison appariée avec le même bloc non choqué) | choc à l'étape 1500 d'un bloc de 4500 (avant/après) | run 2 mesure la dérive « après − avant » |
| ECE | **15 classes à masse égale** | **10 classes de largeur égale** (masse égale stockée) | valeurs non comparables nombre à nombre |
| Fausse confiance | FCR = P(faux ∧ conf ≥ 0,8) sur toutes les lignes (+ deux autres formes) | FCR = P(faux \| conf ≥ 0,6) et CWM = P(conf ≥ 0,6 ∧ faux) | seuils 0,8 / 0,6 ; conditionnelle / jointe |
| Brier | binaire | somme sur 3 classes (≈ 2 × binaire) | non comparables |
| Gain de décision | +1 / −1, coût 0,2 par trade ; τ* = 0,6 | +1 / −1 / −0,3 (trade quand FLAT) / 0 ; τ choisi sur validation | conclusions d'abstention divergentes (8.5) |
| Critères | **pré-déclarés, chiffrés** (ECE ≤ 0,03 ; FCR ≤ 1,5 × ; gain ≥ 0,02 ; couverture ±0,03…) | pas de seuils globaux ; verdicts par comparaisons + IC | le run 1 est plus auditable, le run 2 plus descriptif |
| Anti-fuite | assertion arithmétique + variantes tricheuses fortes | test de perturbation (4 PASS) + variantes tricheuses légères | run 2 plus probant |
| Données publiques | ELEC2 **en prévision** (t → t+1), breast cancer, California | ELEC2 **nowcast** (même ligne), credit-g, breast cancer, California | ELEC2 : tâches différentes |
| Méthodes | 31 recensées / 26 exécutées | 52 / 33 | conventions de comptage différentes |
| Code | `ulib.py` monolithique + 5 scripts | 12 modules + test + config gelée | — |

### 8.1 Q1 — calibration statique dans la distribution

| Mesure | Run 1 (ECE 15 classes masse égale) | Run 2 (ECE 10 classes largeur égale) |
|---|---|---|
| GBM sur-confiant brut | ECE **0,118** ; FCR (conf ≥ 0,8) 0,119 ; Brier 0,218 ; log-loss 0,660 | ECE **0,249** ; FCR (conf ≥ 0,6) 0,432 ; CWM 0,336 ; Brier 0,684 ; log-loss 1,339 |
| GBM après Platt | 0,022 ; FCR 0,028 ; log-loss 0,586 | **0,119** ; CWM 0,153 ; log-loss 1,279 (⚠ solveur, 6.5) |
| GBM après température | **0,022** ; FCR 0,028 ; log-loss 0,586 | **0,027** ; CWM 0,073 ; log-loss 0,964 ; Brier 0,575 |
| GBM après bêta | 0,022 | 0,029 |
| GBM après isotonique | 0,023 | 0,030 |
| GBM après binning bayésien | 0,028 | 0,028 |
| LR brut → calibré | 0,022 → 0,022–0,028 (aucun gain) | 0,022 → 0,021–0,024 (aucun gain) |
| Plancher / oracle | oracle 0,017 | — (oracle non reporté en ECE) |

**Où ils s'accordent** : (a) un GBM sur-confiant est très mal calibré (ECE 0,12–0,25) et 1–2 paramètres le ramènent à ≈ 0,02–0,03 ; (b) un modèle bien spécifié (LR) n'a rien à gagner ; (c) isotonique et binning bayésien n'apportent rien à n = 3000 ; (d) la calibration ne change pas le classement des confiances (AURC identique). **Où ils divergent** : Platt (0,022 contre 0,119). J'ai montré (6.5) que la valeur du run 2 est très probablement un artefact du solveur ; **la convergence des deux runs sur « Platt ≈ température » est donc rétablie**, sous réserve que mon diagnostic (2 graines) soit étendu.

**Petit échantillon / iid publics.** Run 1 : breast cancer (calibration n ≈ 170) : aucune méthode discernable du brut sauf gains de log-loss pour GNB/HGB ; isotonique pire pour LR (0,039 contre 0,024). Run 2 : breast cancer : LR brut est déjà le meilleur (0,028 contre 0,033 après température) ; credit-g GBM 0,210 → 0,054 (Brier 0,457 → 0,358), LR 0,092 → 0,060. **Accord** : sur petit échantillon, le brut d'un modèle bien spécifié ne se laisse pas améliorer. La comparaison ne peut pas aller plus loin (tâches différentes).

### 8.2 Fausse confiance (« sûr et faux »)

| | Run 1 | Run 2 |
|---|---|---|
| Définition | P(faux ∧ conf ≥ 0,8) | CWM = P(conf ≥ 0,6 ∧ faux) ; FCR = P(faux \| conf ≥ 0,6) |
| Brut (GBM) | 0,119 (dans la distribution) | CWM 0,336 |
| Calibré, dans la distribution | 0,028 | CWM 0,073 (température) |
| Calibré statique **après choc** | 0,023 à 0,107 selon le choc : vol **0,107**, régime 0,096, stale 0,054, venue 0,040, feature 0,037, missing 0,023 (iid 0,024) | CWM : feature **0,174**, régime 0,169, stale 0,138, venue 0,127, vol 0,107, missing 0,086 (référence 0,073) |
| Après recalibration en ligne | FCR régime abrupt 0,065 → 0,015 (Platt glissant) ; jamais nul | CWM (GBM, fenêtre) 0,013–0,026 dans 6 chocs (0,057 pour `rare_cluster`) contre 0,086–0,174 statique |
| Oracle | 0,035 (référence de bruit) | — |

**Accord** : la calibration statique laisse une fausse confiance élevée sous choc (jusqu'à ×4,5 dans le run 1 pour vol_jump, ×2,3 pour les données figées, ×1,5 seulement pour feature_shift ; ×1,2 à ×2,4 dans le run 2 par rapport à la référence) et la recalibration en ligne la ramène près de la référence sans jamais la supprimer. **Divergence de niveau** entre chocs : le run 1 voit le pire cas sur vol_jump (0,107), le run 2 sur feature_shift (0,174) — voir 8.3 (définitions des chocs).

### 8.3 Q3 — la calibration survit-elle au choc ? (statique)

| Choc | Run 1 : ECE Platt HGB, calibré avant choc (iid 0,021) ; survit ? | Run 2 : ECE statique GBM température après début (`none` 0,025) ; dérive après−avant |
|---|---|---|
| vol_jump | 0,141 — NON (0/20) | 0,082 ; dérive +0,053 |
| regime_transition | 0,172 — NON (1/20) | 0,178 ; dérive +0,150 |
| feature_shift | **0,036 — OUI (17/20)** | **0,154** ; dérive **+0,126** |
| missing_features | 0,030 — OUI (19/20) | 0,069 ; dérive +0,040 |
| stale_features | 0,076 — NON (0/20) | 0,136 ; dérive +0,108 |
| venue_change | 0,068 — NON (7/20) | 0,094 ; dérive +0,066 |
| rare_cluster | — | 0,033 ; dérive +0,005 |
| Brut (HGB/GBM) | 0,113–0,283 | 0,273–0,421 (rare_cluster inclus ; 0,250 pour `none`) |

**Accord** : le régime (ECE 0,17–0,18) et les données figées (0,08–0,14) sont parmi les pires ; la calibration statique ne tient pas en général (run 1 : 2 chocs sur 6 ; run 2 : aucune tenue, toutes dérives ≥ +0,04 sauf rare_cluster).

**Divergences et causes** (lu dans les générateurs) :

1. **feature_shift** : run 1 = **vrai décalage de covariables** (l'étiquette est recalculée avec les features décalées : P(y | x observé) inchangé) → la calibration « survit » (0,036) ; run 2 = **entrées corrompues** (les features observées sont décalées, l'étiquette reste issue des features d'origine : P(y | x observé) change) → effondrement (0,154). Ce n'est pas une contradiction : ce sont deux phénomènes distincts portant le même nom. Le contraste est en soi un résultat utile : *un décalage de covariables « propre » est sans danger pour la calibration ; une corruption des entrées est dangereuse.*
2. **vol_jump** : run 1 = features ×1,5 **et** rapport signal/bruit ×0,35 (le signal s'affaiblit, la relation change fortement) → 0,141 ; run 2 = bruit ×2,5 seulement (features inchangées) → 0,082.
3. **missing_features** : run 1 = 30 % de NaN sur les 8 features → ECE 0,030 ; run 2 = 40 % sur 3 features → 0,069 ; niveaux de dégradation différents.
4. **regime_transition** : run 1 = coefficients inversés sur tout le bloc ; run 2 = rotation de 120° sur 1000 pas ; ECE final comparable (0,172 contre 0,178).
5. **Base de comparaison** : le run 1 compare à un iid apparié sur les mêmes lignes ; le run 2 à la portion pré-choc.

**Réponse à Q3, par les deux runs** : la calibration **statique** ne survit pas ; le run 2 ajoute que la recalibration **en ligne** restaure (8.4). *Le run 1 a aussi conclu que la recalibration à fenêtre glissante restaure « avec retard »* (`09_ADJUDICATION.md` : « Sliding-window online recalibration restores it with a lag ») — accord.

### 8.4 Recalibration en ligne

| Mesure | Run 1 (Platt glissant W = 1000, refit 250, h = 10) | Run 2 (température glissante W = 600, refit 50, H = 10) |
|---|---|---|
| Baseline statique sous choc | ECE 0,100 (abrupt), 0,110 (graduel), 0,092 (vol.) | ECE 0,154 / 0,178 / 0,136 / 0,094 / 0,082 / 0,069 (selon choc) |
| Après recalibration glissante | 0,017 / 0,016 / 0,016 | 0,026 / 0,055 / 0,018 / 0,014 / 0,024 / 0,020 |
| Pire tronçon (500–1000 pas) | 0,182 → 0,104 (abrupt) | spike ≈ 0,06–0,09 puis retour en 500–1000 pas (rapport ; figure non ouverte) |
| Extensible (expanding) | ECE 0,067 (abrupt), critère NON | ECE moyen des chocs 0,080 (contre 0,025) — « mild improvement » |
| Fenêtre vs extensible | glissante bien meilleure | glissante bien meilleure |
| Coût en stationnaire | aucun (0,013 contre 0,013) | aucun (0,020 contre 0,025) |
| Turnover de décision | 0,76–0,98 × brut sous dérive (glissant/SGD) | −0,10 (GBM régime) … +0,023 (GBM) / +0,039 (LR) vs statique |
| Instabilité du paramètre | mesurée : pente sd 0,04 (glissant stationnaire), 0,13–0,23 (dérive), **0,56–0,78 (ELEC2-LR)** | **non mesurée** (F20 UNKNOWN) |
| ELEC2 statique → en ligne | HGB ECE 0,057 → 0,017 ; pire tronçon 0,177 → 0,044 ; LR 0,130 → 0,024 ; 0,283 → 0,057 | GBM 0,164 → 0,021 ; LR 0,189 → 0,043 |
| Fuite mesurée | tricheuse « bloc » 0,048 contre 0,104 (forte) ; « global » 0,119 (pire) | température : 0,0249 / 0,0246 / 0,0255 (quasi rien) ; isotonique : Brier 0,694 / 0,686 |
| Verdict | `YES_WITH_LIMITS` | `YES` (avec contrat de délai d'étiquette) |

**Accord** : la fenêtre glissante marche, l'extensible non ; sans coût en stationnaire ; sur ELEC2 la recalibration en ligne divise l'ECE par 3 à 8 ; la recalibration ne crée pas d'information et reprend avec retard (« lag »). **Divergences** : (i) le run 2 ne mesure pas l'instabilité de paramètre, le run 1 la mesure et la juge préoccupante sur LR ; (ii) le run 2 utilise température (1 paramètre, donc probablement plus stable — INFERENCE), le run 1 Platt (2 paramètres, pente instable) ; (iii) l'ampleur de la fuite testée diffère (forte contre légère), donc les deux évaluations de la fuite se complètent sans se contredire ; (iv) le verdict du run 2 est plus affirmatif alors que ses réglages W/HL ne sont pas optimaux sur ses graines de réglage.

### 8.5 Q2 — abstention

| Mesure | Run 1 | Run 2 |
|---|---|---|
| Règle | τ = 0,6 dérivé du coût (aucun réglage) | τ choisi sur validation (grille 0,34–0,90) ; ou budgets fixes 10/25/40 % |
| Volume d'abstention | 31,4 % des lignes (couverture 0,686) | 4,9 % des trades (τ val., τ moyen 0,373) ; ou 10/25/40 % |
| Bonnes décisions conservées / mauvaises évitées (dans la distribution) | 0,750 / 0,449 | budget 25 % : 0,826 / 0,362 ; 40 % : 0,696 / 0,539 ; 10 % : 0,935 / 0,151 |
| Effet sur l'utilité | 0,163 → **0,198** (+21 %) | 405,3 → 407,4 (τ val.) ; **392,1 (−3 %)** à 25 % ; 352,2 (−13 %) à 40 % |
| Lift sur le hasard | risque 0,256 contre 0,318 (hasard = plein risque) | ≈ 1,4× (25 % : 36 % / 25 % retirés ; 83 % / 75 % gardés) |
| Sous choc de régime | confiance **statique** : risque 0,486 → 0,482 ; utilité −0,171 → −0,112 (toujours négative) | confiance statique : −151,3 → −141,7 ; confiance **en ligne** : −151,3 → **−35,7** (hasard −95,9) |
| Sous choc « vol_jump » | utilité −0,040 → 0,004–0,023 en tradant moins | confiance en ligne : 413,8 → 402,7 (−11) : détruit de la valeur |
| Vetoes ensemble / distance | pas mieux que relever le seuil de confiance (0,243 contre 0,242) ; drapeaux de défaut de données utiles (stale 0,258 contre 0,303) | ensemble non meilleur que probabilité max (AURC 0,339 contre 0,342 GBM ; pire pour LR) ; Mahalanobis anti-informatif |
| Verdict | `YES_WITH_LIMITS` (pas sous choc de concept) | `PARTIAL` |

**Accord solide** : (a) la calibration ne change pas le classement, elle donne un sens au seuil ; (b) l'ensemble bootstrap n'aide pas ; (c) sous choc de concept, une confiance **statique** n'aide pas (run 1 : 0,486 → 0,482 ; run 2 : −151 → −142). (d) Le run 2 complète le run 1 : **avec une confiance recalibrée en ligne, l'abstention protège** sous choc négatif (−151 → −36), ce que le run 1 n'a pas testé (il utilise une confiance statique dans ses politiques). **Divergence de magnitude et de signe** : le run 1 conclut « l'abstention aide dans la distribution » (+21 % d'utilité), le run 2 « elle coûte de l'utilité au-delà de 5 % dans la distribution ». **Cause probable** : structure du gain. Dans le run 1, chaque trade coûte 0,2 et τ = 0,6 est *exactement* le point de rentabilité nulle : s'abstenir en dessous est mécaniquement profitable. Dans le run 2, il n'y a pas de coût de transaction fixe : les trades peu confiants gardent une espérance positive (le gain d'un mauvais trade est −1 contre +1 pour un bon, avec −0,3 pour un trade en marché plat), donc s'abstenir retire de la valeur. Les deux constats sont cohérents avec leur gain respectif ; **aucun ne dit ce qui se passerait avec les vrais coûts d'AurumShift** (inconnus ici).

### 8.6 Prédiction conforme — validité

| Mesure | Run 1 | Run 2 |
|---|---|---|
| Témoin échangeable | iid_control α = 0,2 : split 0,796 ± 0,011 ; toutes 0,796–0,802 | iid_control régression α = 0,1 : split **0,902 ± 0,006** ; California iid **0,901** ; credit-g / breast 0,80–0,81 (cible 0,80) |
| Cible | α = 0,2 (0,80) (classification), α = 0,2 (régression), α = 0,1 pour ELEC2/AR/abrupt | α = 0,1 (régression, 0,90) ; α = 0,2 (classification 3 classes, 0,80) |
| **Split sous dérive** (classification, cible 0,80) | abrupt **0,733** ; graduelle **0,726** ; vol **0,723** ; ELEC2 **0,764** | sets LR, moyenne des 7 chocs : **0,668** ; ELEC2 blocs 0,588–0,866 (moyenne 0,720 LR / 0,734 GBM) |
| **Split, régression** | α = 0,2 : vol ×3 **0,512** ; rampe **0,452** (cible 0,80) | α = 0,1 : moyenne des chocs **0,766** ; vol jump **0,538** ; régime 0,729 (cible 0,90) |
| **Split, décalage de covariables (California)** | **0,498** (cible 0,80) | **0,589** (cible 0,90) ; Gaussien 0,546 ; pondéré (rapport estimé) 0,651 |
| ACI (retardé) | 0,800 dans tous les cadres ; pire fenêtre 0,755 (abrupt) | classification 0,796–0,800 ; régression 0,897–0,899 ; pire fenêtre de 300 pas 0,865–0,869 (moyenne des chocs) ; 0,864 (vol) |
| Rolling | 0,795–0,797 ; pire fenêtre 0,703–0,711 ; 8/9 critères | 0,793 (clf) / 0,890 (rég.) ; pire fenêtre 0,817 (moy.) / 0,733 (vol) |
| Pondéré | 0,797–0,798 ; pire fenêtre 0,718–0,728 | 0,793 (clf) / 0,894 (rég.) ; pire fenêtre 0,828 |
| Effet du retard sur ACI | ≤ 0,001 de couverture (h = 10 contre 0) | non testé (pas de variante h = 0) |
| Intervalles infinis (ACI scores split) | non rapporté (`?`) | **9,3 %** des pas après choc (0,3 % sur scores rolling) |
| Couverture conditionnelle | non mesurée | split : **0,981 (basse vol.) contre 0,823 (haute vol.)** même en iid ; normalisé+ACI 0,931 / 0,871 |
| Précision des singletons (moment où on agirait) | **0,65–0,67** sous dérive (abrupt 0,663) ; 0,73 stationnaire ; ELEC2 0,78–0,81 | **0,62–0,63** sous choc ; 0,73–0,74 stationnaire |
| Part de « les deux classes » (abstention) | 0,24–0,26 (stationnaire), 0,37–0,42 (dérive) ; α = 0,1 : 0,51–0,64 | 0,58 (stationnaire) ; 0,755–0,763 (choc) |
| Critère de validité | ACI et pondéré : 9/9 ; rolling 8/9 ; split 0/6 sous dérive | pas de critère chiffré ; ACI rolling et normalisé+ACI les meilleurs |
| Verdict | `PARTIAL` | `PARTIAL` |

**Accord fort** (le plus net de toute la lane) : le split conformal perd 5 à 30 points de couverture sous dérive/décalage (0,50–0,77) ; ACI, pondéré et rolling rétablissent la couverture *marginale* de long terme ; la couverture locale sous-couvre après la cassure ; la couverture ne dit rien de la précision des décisions (singletons ≈ 0,62–0,67 sous choc). **Divergences** : (a) les niveaux absolus diffèrent parce que α et cibles diffèrent (0,80 contre 0,90) ; (b) le run 2 ajoute la couverture conditionnelle (0,98 / 0,82) et les intervalles infinis ; le run 1 ajoute l'effet du retard (négligeable) et la mesure par fenêtre de 500 pas ; (c) statistique « pire fenêtre » non comparable (fenêtres de 300 pas sur ≤ 10 fenêtres par graine contre 500 pas sur 14 000 pas) ; (d) la couverture du California sous décalage : 0,498 (cible 0,80) et 0,589 (cible 0,90) : **manque de couverture de 0,30 et 0,31** — quasiment identique en écart.

### 8.7 Détection de choc et Q4 (attribution de cause)

| Mesure | Run 1 | Run 2 |
|---|---|---|
| Détecteurs d'entrée | Mahalanobis (AUROC 0,86–0,88 pour feature/vol ; 0,50 régime/venue ; 0,31 manquants), écart-type d'ensemble (0,47–0,63), faible confiance (0,39 feature ; 0,43 vol : anti-informative), drapeaux (0,97 manquant ; 0,70 figé) | domaine (AUC), KS, Mahalanobis, taux de manquants, taux de répétitions (taux de détection/délai ; 1,00 pour feature/venue ; manquants/répétitions détectés à 100 pas exactement) |
| Choc de régime | invisible aux détecteurs sans étiquettes (AUROC 0,50) | invisible aux détecteurs d'entrée (taux 0,42–0,67 = fausses alarmes) |
| Moniteur à étiquettes | binomial z < −3, fenêtre 300, h = 10 : 100 % des graines, délai médian 411–505 (vol 411, régime 454,5, figé 505, venue 488,5) ; **fausse alarme 15 % par 6000 pas iid** | fenêtre de perte sur étiquettes mûres : 100 % des graines, délai 150 (vol), 500 (régime), 100 (figé), 250 (manquants) ; **fausse alarme dans 58 % des graines sur 3000 pas sans choc** (4,8 % par fenêtre évaluée avant choc) |
| Q4 : cause DATA_GAP | rappel **0,968** | P = R = **1,000** (par construction) |
| Q4 : OOD | rappel **0,979** | précision 0,966 / rappel **0,389** |
| Q4 : NO_SIGNAL | rappel **0,360** | précision 0,602 / rappel **0,873** / F1 0,713 |
| Q4 : MODEL_UNCERTAINTY | rappel **0,149** | précision 0,047 / rappel 0,168 / **F1 0,073** |
| Critère | rappel ≥ 0,7 pour les 4 : **NON (2/4)** | pas de critère ; macro-F1 0,604 |

**Accord** : DATA_GAP se détecte par des drapeaux explicites, pas par la statistique (Mahalanobis aveugle après imputation : AUROC 0,31 / détection 0 %) ; MODEL_UNCERTAINTY n'est pas séparable par un ensemble bootstrap du même apprenant (0,149 / F1 0,073) ; le choc de concept n'est vu que par un moniteur à étiquettes retardées ; l'OOD garde une confiance élevée (run 2 : conf 0,726 pour erreur 0,479 ; run 1 : confiance anti-informative). **Divergences** : (a) **NO_SIGNAL : rappel 0,36 contre 0,87.** Causes : dans le run 1 la vérité NO_SIGNAL = région où la vraie probabilité est exactement 0,5 (`x7 > 1`, bruit pur) et la règle est |p − 0,5| < 0,08 ; un signal faible (mais non nul) se confond avec l'absence de signal. Dans le run 2 la vérité est « probabilité oracle max < 0,5 » (3 classes) et la règle « confiance calibrée < 0,5 » : quasi la même quantité. Le F1 de 0,71 est donc en partie définitionnel. (b) **OOD : rappel 0,98 contre 0,39.** Dans le run 1 l'OOD est fabriqué fortement (features ×1,5 et +3σ : « exactement ce que le détecteur est fait pour attraper », circulaire, dit le rapport) ; dans le run 2 l'OOD est un décalage modéré (« beaucoup de lignes décalées restent dans le support d'entraînement »). (c) **Fausses alarmes du moniteur de perte** : 15 % (run 1) contre 58 % (run 2) — les unités et les seuils diffèrent (z < −3 sur lignes agies contre maximum sur validation), donc les deux sont à réconcilier (11).

### 8.8 ELEC2 (seule donnée réelle dérivante commune)

| | Run 1 (prévision t → t+1, cal. 9000–13500, test 18000–fin) | Run 2 (nowcast, cal. 6000–9000, test 12000–fin, 33 312 lignes) |
|---|---|---|
| Statique LR | brut ECE 0,103 → Platt 0,153 / température 0,168 : **pire** | brut 0,157 → température 0,189 (Brier 0,456 → 0,478) : **pire** |
| Statique GBM/HGB | brut 0,107 → température 0,068 | brut 0,240 → température 0,164 |
| Variation entre tronçons/blocs | HGB température 0,025–0,125 (6 tronçons) | GBM statique 0,01–0,37 (16 blocs) |
| En ligne | HGB 0,057 → 0,017 ; LR 0,130 → 0,024 | GBM 0,164 → 0,021 ; LR 0,189 → 0,043 |
| Conformal α = 0,2 : split / ACI | 0,764 / 0,800 | 0,720–0,734 / 0,800 |
| Précision | non rapportée | 0,711 (LR), 0,697 (GBM) |

**Accord total** : sur des données réelles dérivantes, (i) un calibrateur statique peut être pire que ne rien faire pour LR ; (ii) la recalibration en ligne divise l'ECE par un facteur 3 à 8 ; (iii) le split conformal sous-couvre (0,72–0,76) et ACI tient 0,800. C'est **la convergence la plus forte entre les deux runs sur des données réelles**, malgré des tâches différentes (prévision contre nowcast). Avertissement : ce n'est qu'un seul jeu, qui n'est pas un problème financier.

### 8.9 Recommandations finales

| | Run 1 | Run 2 |
|---|---|---|
| Référence simple | Platt (≈ température) sur bloc de calibration mis de côté + τ = (1+c)/2 + drapeaux manquant/figé → HOLD | **température** sur les logits + seuil de confiance choisi sur validation |
| Référence en ligne | Platt glissant (W ≈ 1000, refit ≈ 250, étiquettes mûres, `assert j+h ≤ t`) + **ACI retardé** + moniteur de calibration à étiquettes (disjoncteur) | **température glissante** (W = 600, refit 50, H = 10) + **moniteur de perte réalisée** ; ACI sur scores rolling (γ = 0,01) pour surveiller la couverture marginale |
| À rejeter / mettre de côté | split conformal en non stationnaire ; recalibration extensible ; isotonique/binning à n ≲ 3000 ; vetoes ensemble/OOD ; couverture iid | Platt sur arbres (⚠ artefact) ; intervalles Gaussiens ; revendications de couverture split sous dérive ; calibration statique à travers un régime ; ensemble bootstrap ; conformal singleton comme porte de trade |
| Verdict | `LIMITED_UNCERTAINTY_METHODS_SUPPORTED` | `LIMITED_UNCERTAINTY_METHODS_SUPPORTED` |

### 8.10 Synthèse : où les deux runs s'accordent

1. Calibrer un modèle sur-confiant par 1 ou 2 paramètres suffit en stationnaire (ECE 0,02–0,03) ; rien à gagner pour un modèle déjà calibré.
2. Isotonique / binning bayésien : pas mieux (variance) ; le run 2 ajoute une sensibilité plus forte à la fuite.
3. La calibration statique ne survit pas aux chocs (régime, données figées, entrées corrompues) ; sur ELEC2 elle peut empirer.
4. Recalibration en ligne à fenêtre glissante / oubli : indispensable et efficace, avec retard ; l'extensible est faible.
5. Split conformal invalide hors échangeabilité (0,50–0,77 de couverture) ; ACI/pondéré/rolling : couverture marginale de long terme seulement.
6. La couverture marginale ne mesure pas la qualité de décision (précision des singletons ≈ 0,62–0,67 sous choc) ; le choix de α fixe le taux d'abstention.
7. L'ensemble bootstrap n'apporte pas d'information utile à l'abstention.
8. Les défauts de données explicites se détectent par des drapeaux exacts ; le choc de concept exige des étiquettes.
9. MODEL_UNCERTAINTY non séparable ; NO_SIGNAL et DATA_GAP séparables selon la définition.
10. Même verdict final et mêmes limites déclarées (monde synthétique, gain jouet, délai fixe, littérature non relue).

### 8.11 Synthèse : où ils divergent, et pourquoi (probable)

| # | Divergence | Cause probable | Statut |
|---|---|---|---|
| 1 | Platt : ECE 0,022 contre 0,119 | **solveur maison non convergent dans le run 2** (mon diagnostic : pente 1,60 contre 0,33) | OBSERVED par moi sur 2 graines ; à étendre |
| 2 | Survie sous `feature_shift` : OUI contre effondrement | l'étiquette suit les features décalées (run 1) contre les features d'origine (run 2) | LU dans le code (PROVEN par lecture) |
| 3 | Sévérité de `vol_jump` : 0,141 contre 0,082 | run 1 affaiblit aussi le signal (SNR ×0,35) ; run 2 ne fait que gonfler le bruit | LU dans le code |
| 4 | Abstention : +21 % d'utilité contre −3 % à 25 % | gain avec coût fixe 0,2 (τ = 0,6 breakeven) contre gain sans coût fixe | INFERENCE cohérente avec les définitions |
| 5 | NO_SIGNAL : rappel 0,36 contre 0,87 | définitions de la vérité et de la règle | LU |
| 6 | OOD : rappel 0,98 contre 0,39 | intensité du décalage (run 1 : ×1,5 et +3σ ; run 2 : décalage modéré) | LU |
| 7 | Fausses alarmes du moniteur à étiquettes : 15 % / 6000 pas contre 58 % des graines / 3000 pas | seuils et unités différents ; règle z < −3 (agi) contre max-validation | non réconcilié `?` |
| 8 | En ligne : `YES_WITH_LIMITS` contre `YES` | run 1 mesure l'instabilité (ELEC2-LR pente sd 0,78) et l'affiche ; run 2 ne la mesure pas | LU |
| 9 | Nombre de méthodes : 31/26 contre 52/33 | conventions différentes (le run 2 catalogue des sous-familles) | LU |
| 10 | Critères : chiffrés (run 1) contre descriptifs (run 2) | choix de conception | LU |
| 11 | Ampleur de la fuite : forte (run 1) contre légère (run 2) | variantes tricheuses de sévérité différente | LU |
| 12 | Niveaux d'ECE/FCR/Brier | définitions différentes (8.0) | LU |

**Lequel croire, pour quoi ?** Pour la *validité du contrôle anti-fuite*, le run 2 (test de perturbation). Pour l'*auditabilité des critères de succès*, le run 1 (seuils chiffrés). Pour la *question Platt*, le run 1 (implémentation standard, résultat cohérent avec la littérature usuelle ; **DOCUMENTED_CLAIM non vérifié**) — le run 2 est douteux sur ce point. Pour la *séparation des causes*, aucun des deux n'est concluant (définitions circulaires). Pour les *intervalles conformal*, les deux sont d'accord ; le run 2 apporte en plus la couverture conditionnelle et les intervalles infinis.

---

## 9. Reproductibilité

### 9.1 Comment relancer

**Environnement de mes essais** (celui de cette machine, pas forcément celui des auteurs) : Python 3.11 ; scikit-learn 1.9.1, numpy 2.4.6, scipy 1.17.1, pandas 3.0.6 ; 4 cœurs. Aucune des deux branches ne fournit de fichier `requirements` ni de versions figées (`?` : les versions utilisées par les auteurs sont inconnues).

**Run 1** (README de `bench/uncertainty_v1/`) — depuis `bench/uncertainty_v1/py/` (les chemins `../results/` et `../data/elec2.csv` sont relatifs) :

```
pip install numpy scipy scikit-learn pandas
python exp_static.py      # Q1 : synthétique 20 graines + ELEC2 + breast cancer   (mesuré : 28,7 s)
python exp_shift.py       # Q2/Q3 : 7 chocs, politiques d'abstention, risque-couverture, moniteur (non chronométré)
python exp_taxonomy.py    # Q4 : 5 causes, 20 graines                             (mesuré : 29,6 s)
python exp_online.py      # §6 : en ligne, Pool(4), 8 graines + ELEC2 h=1 et h=48 (non chronométré ; online_time.txt : 20,9 s réel)
python exp_conformal.py   # §7 : conformal, Pool(4)                                (non chronométré)
python make_tables.py     # résultats -> results/tables/*.md
```

`OMP_NUM_THREADS=1` recommandé si plusieurs processus. Durée annoncée : « ~10 min sur 4 cœurs » (non vérifiée en bloc). **Fourni** : code, données ELEC2 (copie de 2 998 235 octets dans `data/`), CSV bruts, tables Markdown, `ALLDONE`. **Manque** : versions des paquets, script d'orchestration unique, tests unitaires, journaux d'exécution des autres composantes. Note : `exp_static.py` etc. écrivent dans `../results/` et écraseraient les résultats livrés (j'ai redirigé vers un dossier `results_new` dans ma copie). California housing et breast cancer viennent de scikit-learn (California nécessite un téléchargement).

**Run 2** (README) — Python 3.11 ; numpy, scipy, scikit-learn, pandas, tabulate, matplotlib ; **accès Internet requis** (OpenML `electricity`, `credit-g` ; scikit-learn `california_housing`), rien n'est redistribué :

```
cd bench/uncertainty_v1/py
python3 run_static.py 0-6 1.0 ../results/static_hold_0-6     # puis 6-12 ; réglage : 100-104 0.6 (static_tune_a / _b)
python3 online.py 0-6 1.0 ../results/hold_a '{"W":[600],"HL":[400]}' leaky   # puis 6-12 -> hold_b
python3 conformal.py 0-6 1.0 ../results/hold_a '{"W":300,"HL":150,"gamma":0.01}'
python3 run_abstain.py 0-6 1.0 ../results/hold_a             # (arguments : graines, magnitude, préfixe de sortie)
python3 shift.py hold 0-6 1.0 ../results/diag                # puis tune 100-104 0.6
python3 run_public.py ../results/public
cd .. && python3 py/analyze.py && python3 py/figures.py && python3 py/methods_catalog.py
python3 tests/test_no_lookahead.py                            # depuis bench/uncertainty_v1
```

`py/tune_conformal.sh <seeds> <tag>` rejoue les 5 grilles de réglage conformal. Durées mesurées dans les journaux du dépôt (`results/logs/*.log`) : statique ≈ 73 s/graine ; en ligne ≈ 115 s/graine ; conformal ≈ 73 s/graine (437 s pour 6 graines) ; réglage conformal ≈ 65 s/graine par grille. **Mesuré par moi** : test anti-fuite 6,1 s ; graine 0 du statique 53,8 s avec écart maximum 0,0 contre les résultats livrés. **Fourni** : code, configuration gelée, test, CSV bruts par graine (compressés pour le diagnostic), tables, figures PNG (3), journaux. **Manque** : versions figées ; les `*_reliability.csv` de 6-12 et de réglage sont vides (1 octet) car la fiabilité n'est calculée que pour les graines < 3 (donc seulement dans le fichier 0-6) ; les journaux `diag_hold_a/b.log` sont vides ; pas d'horodatage.

### 9.2 Ce qui rend la reproduction facile ou difficile

* Facile : petites tailles (≤ 45 k lignes), aucun GPU, graines fixes, déterminisme confirmé sur deux composantes du run 1 et une composante du run 2.
* Difficile : dépendance à OpenML (run 2) ; disparité de versions de bibliothèques (`HistGradientBoostingClassifier` peut varier entre versions de scikit-learn : `?`) ; aucun conteneur.
* **Non testé par moi** : `exp_shift.py`, `exp_online.py`, `exp_conformal.py`, `make_tables.py` (run 1) ; `online.py`, `conformal.py`, `run_abstain.py`, `shift.py`, `run_public.py`, `analyze.py`, `figures.py` (run 2) — leurs sorties ont néanmoins été recalculées à partir des CSV livrés (section 6.6), ce qui vérifie les *agrégations* mais pas la *génération* des CSV bruts.

---

## 10. Implications pratiques pour AurumShift — uniquement des pistes « à adjuger plus tard »

**Cadre.** Aucune de ces lignes n'affirme qu'une méthode est compatible avec AurumShift : le code privé n'a pas été lu, l'existence des composants supposés est **UNKNOWN** (`claude.md` : « never claim compatibility from this repository »). Chaque piste se termine par ce qu'il faudrait vérifier dans le vrai dépôt.

1. **Piste — mesurer d'abord la calibration existante sur un bloc PIT-sûr.** Les deux runs convergent sur le fait qu'un modèle sur-confiant se corrige avec 1–2 paramètres (ECE 0,12–0,25 → 0,02–0,03). *À adjuger* : les scores de confiance d'AurumShift sont-ils des probabilités ? Existe-t-il un bloc de calibration disjoint de l'entraînement et de la validation, respectant PIT ?
2. **Piste — recalibrer avec oubli plutôt qu'en accumulant.** Fenêtre glissante ou décroissance exponentielle ont battu l'extensible dans les deux runs. *À adjuger* : le système dispose-t-il d'un **magasin d'étiquettes avec délai de maturité connu et enregistré par étiquette** (les deux runs supposent un H fixe ; les étiquettes de rendement futur se chevauchent) ? PostgreSQL-first et PIT : la question est de savoir si « date de disponibilité de l'étiquette » est une colonne de première classe.
3. **Piste — drapeaux de qualité de données comme entrées de premier rang** (NaN, valeur répétée, âge). Détection exacte et instantanée dans les deux runs ; les détecteurs statistiques échouent après imputation. *À adjuger* : ces métadonnées existent-elles déjà dans le pipeline, et une fonction « HOLD forcé » est-elle possible sans coût opérateur ?
4. **Piste — alarme de choc de concept fondée sur les pertes réalisées** (seul détecteur des chocs de régime/volatilité dans les deux runs). *À adjuger* : quels taux de fausses alarmes sont tolérables ? Les deux runs ne s'accordent pas (15 % par 6000 pas contre 58 % des graines par 3000 pas) ; une règle de persistance et un budget de fausses alarmes seraient à définir contre le vrai flux.
5. **Piste — traiter l'abstention comme contrôle du risque, pas comme source de gain.** Les deux runs le disent. Le signe du gain dépend du modèle de coût. *À adjuger* : le vrai coût de transaction / slippage / sélection adverse, qui déterminerait le seuil (pas 0,6, qui n'est valable que pour le gain jouet).
6. **Piste — ne pas s'appuyer sur des intervalles « garantis » du split conformal pour les séries temporelles**, et ne pas confondre couverture marginale et fiabilité de la décision. ACI/rolling servent à *surveiller* la couverture marginale, sans garantie conditionnelle ni locale. *À adjuger* : si des intervalles/ensembles sont utilisés dans des décisions, sur quelle mesure de fiabilité conditionnelle (par volatilité, par régime) ?
7. **Piste — ne pas utiliser un ensemble bootstrap d'un même apprenant comme mesure d'incertitude « épistémique ».** Rejeté dans les deux runs (MODEL_UNCERTAINTY F1 0,07 ; rappel 0,15). *À adjuger* : si une vraie mesure épistémique est requise, il faut tester des approches non couvertes ici (ensembles profonds, MC-dropout, Dirichlet, etc.).
8. **Piste — prévoir la surveillance de l'instabilité des paramètres de recalibration** (pente sd 0,78 sur ELEC2-LR dans le run 1). *À adjuger* : besoin de lissage/plafonds ; température (1 paramètre) est une option plus stable — INFERENCE, non mesurée.
9. **Piste — exigence de tests anti-fuite de type perturbation** (corrompre les étiquettes non mûres et vérifier l'identité des sorties servies) : le test du run 2 est une méthode transposable. *À adjuger* : intégrer ce genre de test au dépôt réel si une recalibration en ligne est un jour envisagée.

---

## 11. Questions ouvertes et suites recommandées (classées par valeur décroissante)

| Rang | Question / suite | Pourquoi (valeur) | Coût |
|---|---|---|---|
| 1 | **Refaire le Platt du run 2 avec un solveur standard** (et comparer bêta) sur les 12 graines ; corriger le rapport 03/09 | corrige la seule erreur d'interprétation importante ; réconcilie les deux runs | très faible |
| 2 | **Tester des étiquettes à horizon chevauchant / délai variable / triple-barrière**, avec test de perturbation par étiquette (`maturity_ts`) | c'est le point critique PIT pour toute recalibration en ligne ; les deux runs l'ont écarté | moyen |
| 3 | **Passer à des données financières réelles PIT** (pas ELEC2) : au moins une série d'actif avec coûts | tout le reste est synthétique ; aucune revendication de performance possible aujourd'hui | élevé |
| 4 | **Réconcilier les fausses alarmes du moniteur à étiquettes** (15 % / 6000 pas contre 58 % des graines / 3000 pas) : courbe ROC, règle de persistance, budget de fausses alarmes par pas | le « ADOPT alarme de choc » du run 2 en dépend | faible à moyen |
| 5 | **Croiser les codes** : exécuter le code du run 2 dans le monde du run 1 et inversement (mêmes métriques) | isole les effets « monde » et « méthode » que la section 8 ne fait que déduire | moyen |
| 6 | **Analyse de sensibilité** : W, R, γ, λ, demi-vie ; élargir la grille ELEC2 (W = 2000 est au bord) ; τ | les hyper-paramètres sont ad hoc (run 1) ou au bord/mal optimaux (run 2) | moyen |
| 7 | **Mesurer l'instabilité des paramètres en ligne** (trajectoire de la température, lissage, plafonds) | manquant dans le run 2 ; alerte dans le run 1 | faible |
| 8 | **Méthodes non testées** : AgACI, SAOCP, conformal PID, EnbPI, CQR, Learn-then-Test, Dirichlet / vector scaling, ensembles profonds, MC-dropout, détecteurs séquentiels (CUSUM/ADWIN) | 19 méthodes du run 2 et 5 du run 1 restent sans test | élevé |
| 9 | **Gain réaliste** (frais, slippage, asymétrie, 3 classes) et τ optimisé | l'abstention est très sensible au gain | moyen |
| 10 | **Relire les articles** (Gibbs & Candès, Barber et al., Tibshirani et al., etc.) et vérifier les théorèmes cités ; ACI avec retard : existe-t-il une garantie ? | toutes les citations sont DOCUMENTED_CLAIM non relues | faible |
| 11 | **Protocole vérifiable** : figer et committer critères et `frozen_config.json` *avant* tout résultat test (commit distinct) | permet de prouver l'absence de dérive de protocole (`?` aujourd'hui pour les deux runs) | très faible |
| 12 | **Comparaison croisée avec MAPIE / netcal / crepes** | respecte REUSE → ADAPT ; sécurise contre les bugs (cf. Platt) | faible |
| 13 | Vérifier le statut de redistribution du fichier `data/elec2.csv` du run 1 | hygiène de licence | très faible |

---

## 12. Index des fichiers lus

**Dépôt (racine)** : `claude.md` — doctrine du laboratoire, contraintes AurumShift, frontière d'intégration (lu en entier). `SYNTHESE_LANES.md`, `analyses/LANE_004_pit_safe_evidence_replay.md` — présents, **non lus** (hors périmètre).

**Run 1 — branche `origin/claude/uncertainty-calibration-v1` (PR #19)**

| Chemin | Contenu | Lu |
|---|---|---|
| `reports/012_uncertainty_calibration/00_EXECUTIVE_SUMMARY.md` | synthèse en 7 constats + bloc final | oui, en entier |
| `.../01_METHODS.md` | catalogue de 32 lignes (31 méthodes + tricheuses), notes d'implémentation, bug corrigé | oui |
| `.../02_PROTOCOL.md` | données, découpages, critères pré-déclarés, métriques, statistiques | oui |
| `.../03_STATIC_CALIBRATION.md` | Q1 : synthétique, breast cancer, ELEC2 | oui |
| `.../04_ONLINE_CALIBRATION.md` | en ligne : 4 scénarios, ELEC2, critère, fuite | oui |
| `.../05_ABSTENTION.md` | Q2 : politiques P0–P4, risque-couverture | oui |
| `.../06_CONFORMAL.md` | conformal : théorie, classification, régression, housing | oui |
| `.../07_SHIFT_TESTS.md` | Q3/Q4 : ECE, FCR, survie, AUROC, moniteur, confusion | oui |
| `.../08_FAILURE_MODES.md` | F1–F14 + 4 défaillances de processus | oui |
| `.../09_ADJUDICATION.md` | critères, réponses Q1–Q4, références | oui |
| `.../10_LIMITATIONS.md` | 11 limites | oui |
| `bench/uncertainty_v1/README.md` | commandes de reproduction | oui |
| `bench/uncertainty_v1/py/ulib.py` | bibliothèque : métriques, calibrateurs, `run_online`, conformal, monde | oui, en entier |
| `.../py/exp_static.py`, `exp_shift.py`, `exp_taxonomy.py`, `exp_online.py`, `exp_conformal.py` | scripts d'expériences | oui, en entier |
| `.../py/make_tables.py` | génération des tables | partiel (30 premières lignes) |
| `.../results/static_raw.csv`, `online_raw.csv`, `conformal_cls.csv`, `conformal_reg.csv`, `conformal_housing.csv`, `shift_cal.csv`, `shift_policy.csv`, `shift_auroc.csv`, `shift_monitor.csv`, `shift_riskcov.csv`, `taxonomy_confusion.csv`, `taxonomy_raw.csv` | résultats bruts | oui, recalculés en Python |
| `.../results/tables/shift_survival.md`, `conformal_criterion.md`(début), `online_pit_audit.md`, `online_stdout.txt`(fin), `ALLDONE`, `online_time.txt` | tables et journaux | partiel |
| `.../results/shift_detect.csv`, `shift_survival.csv`, `conformal_stdout.txt`, autres `tables/*.md`, `data/elec2.csv` | — | **non lus** (redondants avec les rapports ou données) |
| Historique Git : `73a1650` (WIP) et `40a9721` (final) | diff de `ulib.py`, `exp_shift.py`, `01_METHODS.md`, `02_PROTOCOL.md`, statistiques de fichiers | oui |

**Run 2 — branche `origin/claude/uncertainty-calibration-v1-b` (PR #24)**

| Chemin | Contenu | Lu |
|---|---|---|
| `reports/012_uncertainty_calibration/00_EXECUTIVE_SUMMARY.md` … `10_LIMITATIONS.md` (11 fichiers) | synthèse, méthodes (52), protocole, statique, en ligne, abstention, conformal, chocs/diagnostic, modes de défaillance, adjudication + bloc final, limites | oui, en entier (11/11) |
| `bench/uncertainty_v1/README.md`, `frozen_config.json` | commandes ; paramètres gelés | oui |
| `bench/uncertainty_v1/py/worlds.py`, `calibrators.py`, `metrics.py`, `models.py`, `online.py`, `conformal.py`, `shift.py`, `run_abstain.py`, `run_static.py`, `run_public.py`, `analyze.py`, `tune_conformal.sh` | code | oui, en entier |
| `.../py/figures.py`, `methods_catalog.py` | figures, catalogue | **non lus** (sauf sortie `methods_catalog.md` : début) |
| `.../tests/test_no_lookahead.py` | 4 tests | oui, **exécuté** |
| `.../results/key_numbers.json`, `methods_counts.json` | chiffres clés, comptage | oui |
| `.../results/static_hold_*_metrics.csv`, `static_hold_*_riskcov.csv`, `static_tune_*_metrics.csv`, `hold_*_online.csv`, `tune_*_online.csv`, `hold_*_abstain.csv`, `hold_*_conf_reg.csv`, `hold_*_conf_clf.csv`, `ctune_*_conf_reg.csv`, `diag_detection_*.csv`, `diag_diagrows_hold_*.csv.gz`, `public_elec_metrics.csv`, `public_elec_blocks.csv`, `public_elec_conformal.csv`, `public_iid_metrics.csv`, `public_iid_conformal.csv`, `public_california.csv` | résultats bruts | oui, recalculés |
| `.../results/logs/*.log` | journaux (temps, graines) | oui (échantillon de 7) |
| `.../results/*_reliability.csv`, `hold_*_rolling.csv`, `tune_*_rolling.csv`, `ctune_*_conf_clf.csv`, `diag_diag_tuning.csv`, `public_iid_riskcov.csv`, `tables/*.md` (sauf début de `methods_catalog.md`), `figures/*.png` | — | **non lus / non ouverts** (redondants ou visuels) |

**Exécutions faites par moi (scratchpad, aucune branche modifiée ni checkout)** : re-run run 1 `exp_static.py` et `exp_taxonomy.py` (identiques octet pour octet) ; run 2 `tests/test_no_lookahead.py` (4 PASS), `run_static.py 0-1 1.0` (écart 0,0), et un diagnostic Platt (script `diag_platt.py`, graines 0–1, scénario `none`). Rien n'a été poussé.
