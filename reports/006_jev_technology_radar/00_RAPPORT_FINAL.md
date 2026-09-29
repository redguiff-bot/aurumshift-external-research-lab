# 006 — AURUMSHIFT_JEV_TECHNOLOGY_RADAR_AND_REUSE_SURVEY_V1

Date : 2026-09-29. Périmètre : recherche externe uniquement. Aucun code AurumShift, aucun changement DecisionV1 / quorum / runtime.
Légende (doctrine du lab) : PROVEN (reproduit ou exécuté par nous sur artefacts bruts) · OBSERVED (lu dans code/données/README tiers, non rejoué) · DOCUMENTED_CLAIM (affirmation sans artefact vérifié) · INFERENCE · UNKNOWN.

## 0. Limites de cette recherche (à lire d'abord)

1. **Aucune clé TypeSafe** : aucun appel réel à Jev n'a été fait. Toutes les mesures Jev viennent de tiers. Ce qui est PROVEN ci-dessous l'est sur artefacts publiés (logs bruts, code) ou sur le code de l'adapter, jamais sur l'API.
2. **Reddit : INACCESSIBLE** pour nos outils (domaine refusé par le crawler, aucun thread ouvert ni localisé). Aucun thread r/quant, r/algotrading, r/MachineLearning, r/LocalLLaMA, r/CloudFlare n'est cité. La seule mention indirecte est une dispute de priorité Laya vs Jev sur r/LocalLLaMA, rapportée par des blogs (thread original UNKNOWN). **Ne pas conclure à l'absence de discussion.** Hacker News : seul le fil de lancement a pu être lu ; trois autres fils (dont « Jev Can't Be Calibrated ») ont renvoyé 403.
3. Code search GitHub exigeant un login, la recherche par symboles (`Noul`, `TypeSafeClient`, `system_one`) n'est pas exhaustive. Couverture compensée par awesome-lists, WebSearch et clones.
4. **Tout l'écosystème a ≤ 14 jours** (lancement early access 2026-09-15), un seul modèle testé (`jev-1.13.0`), petits échantillons, majoritairement des auteurs uniques. Aucun recul de production.
5. Une partie des chiffres est passée par des résumés WebFetch (petit modèle) : ils sont étiquetés OBSERVED/DOCUMENTED_CLAIM, jamais PROVEN. Les notes brutes des sous-recherches sont dans `evidence/raw_agent_*.md` (non relues ligne à ligne ; à traiter comme notes de travail).
6. Un tiers (jevcal) affirme que l'accord client TypeSafe restreindrait la publication de performances : DOCUMENTED_CLAIM non vérifié, **à contrôler dans les CGU avant toute publication** de résultats.

Vérifications faites par nous (PROVEN) :
- Adapter `system-one-adapter` v0.2.1 : **424 tests passent hors ligne** (cassettes) après installation des extras openai/anthropic/gemini.
- La frontière `Provider` de l'adapter accepte un **fournisseur personnalisé déterministe** : un même `QuestionSet` (Noul+Choice+Score) a été évalué par une baseline à règles via `SystemOneAdapterClient` (`evidence/exp_custom_provider_seam.py`).
- Recalcul sur données brutes (`jujumilk3/jev-calibration-audit`, `abstention.jsonl`, 1 200 lignes) : items ambigus **sans option « inconnu » : accuracy 0,000, p_max moyen 0,793, ECE 0,793** ; **avec option : 0,950 / 0,927 / ECE 0,023**.
- Le README de `cwhy/decision-injection-bench` contient bien « 1/1 056 flips (0,09 %) » pour Jev 1.13.0, mais sur une campagne d'ajouts non adaptatifs contre une politique de confiance stricte, synthétique, avec un README qui signale lui-même que la campagne plus large « still found a way through Jev's strict policy ». Le chiffre est réel mais non généralisable.

---

## 1. EXECUTIVE_FINDINGS

1. **Jev est un service hébergé fermé** (`api.typesafe.ai`, un seul modèle `jev-1.13.0`, alias `jev-latest`/`jev-preview` identiques). Architecture, base model, cutoff, données, méthode « RLCD » : non publiés (UNKNOWN). Exit cost et reproductibilité PIT dépendent donc de la journalisation append-only des réponses brutes.
2. **« Type-safe » ≠ correct ni calibré.** La validité de schéma est bien tenue (0 sortie invalide sur 4 621 appels et 23 703 agrégés, OBSERVED). Rien de plus n'est garanti.
3. **Calibration : bonne dans le domaine, mauvaise hors domaine.** ECE 0,02–0,08 sur QA public et routage de tickets ; 0,107 sur tâche synthétique avec règle implicite (priorité : 44,7 % de justesse pour 0,74 de probabilité moyenne) ; 0,793 sans option d'abstention (PROVEN). Aucune métrique de calibration publiée par TypeSafe.
4. **Sorties quantifiées à 0,01, souvent 0 ou 1** ; `confidence` (Choice) = (N·p_max−1)/(N−1), donc **pas un signal indépendant de p_max** (PROVEN sur brut et dans le code de l'adapter). NLL non borné : clipping obligatoire.
5. **Aucun edge finance démontré.** Six études indépendantes convergent vers « pas d'alpha » (jev-alpha-bench IC −0,008 tradable ; BTC backtest perdant après 14 bps ; ΔBrier 1,4e-05 vs volatilité ; 8-K : 0,97 annoncé pour 49,1 % réel ; avec/sans Jev : −2,1/−2,8/+4,9 pts = bruit). Sur du **texte** (annonces d'exchanges) Jev est solide (99,3 % à confiance ≥ 0,8, Siim). Voir §7.
6. **Robustesse aux données non fiables : risque majeur.** Injection « d'évidence/autorité » : 147/200 (willkelly), précision 96,5 % → 26,5 % (zkousama), 61,4 % de décisions détournées par ajouts « naturels » (JevOut, arXiv). Les injections brutales échouent. Le contenu adversarial est admis comme risque par la doc TypeSafe.
7. **Sensibilité à la formulation** : inverser les rubriques oui/non change 32,5 % des réponses (un seul auteur) ; l'ordre des options est négligeable sur tâches factuelles mais pas sur d'autres (résultats mixtes) ; décomposer en questions atomiques fait passer 62,6 % → 95,0 % (phishing).
8. **Perf/coût** : latence médiane 127–430 ms selon région/passerelle, jamais < 100 ms (0/35 685, Siim) ; p95 231 ms (LiteLLM) ; coût ≈ 12× moins que Haiku 4.5 (Beri), pas 444×. Batch de 200 questions/requête sans perte (un seul auteur).
9. **Abstraction multi-provider : `system-one-adapter-python` est réutilisable comme couche, pas comme contrat canonique.** Il fournit Claude/GPT/Gemini avec les mêmes primitives Noul/Choice/Score et un point d'extension `Provider`. Mais v0.2.1 a 2 semaines, 3 renommages publics, une rupture (msgspec → pydantic), 5 issues ouvertes dont « carte de probabilités toute à zéro acceptée comme valide », et un seul appel LLM pour toutes les questions d'un état.
10. **La distinction des causes de HOLD n'est pas fournie nativement.** Aucun projet ne fournit « absence / contradiction / insuffisance / signal valide bloqué » ; les repos qui le font l'écrivent en code. Le quorum multi-agents autour de Jev : NONE_FOUND.

## 2. TOP_RESOURCES (17)

Fiches structurées complètes : `01_RESOURCE_CARDS.md`. Tableau de synthèse :

| # | Ressource | Pourquoi utile | Reco |
|---|---|---|---|
| 1 | typesafe-ai/system-one-adapter-python | seul cadre multi-provider à primitives partagées (officiel, MIT) | ADAPT |
| 2 | typesafe-ai/typesafe-sdk-python | types Question/Answer, retry, client Jev | ADOPT_FOR_BENCH |
| 3 | typesafe-ai/WorkflowEvals (Apache-2.0) | protocole d'eval multi-provider de l'éditeur | WATCH |
| 4 | willkelly/jev-evaluation | 123 805 requêtes, pré-enregistré, logs bruts | ADOPT_FOR_BENCH (protocole) |
| 5 | jujumilk3/jev-calibration-audit | abstention, ordre, interférence (recalculé PROVEN) | ADOPT_FOR_BENCH (protocole) |
| 6 | scienthoon/jev-ood-calibration | ECE par primitive, OOD | ADOPT_FOR_BENCH (protocole) |
| 7 | zkousama/jagged ; xzx34/JevOut ; cwhy/decision-injection-bench | injection/state poisoning | ADOPT_FOR_BENCH (jeux de sondes) |
| 8 | Siim/jev-claim-vs-measured | latence, précision finance, reproductible | ADOPT_FOR_BENCH (protocole) |
| 9 | alakise/calibration-is-not-alpha | ΔBrier vs baseline déterministe (27 tests PROVEN) | ADOPT_FOR_BENCH (protocole) |
| 10 | Spykoninho/trading-bot-jev | seule mesure avec/sans Jev ; state unique + questions par source | ADAPT (pattern) |
| 11 | buberlo/jev-trader | 6 jugements atomiques → politique → vetos → journal Brier/ECE (61 tests PROVEN) | ADAPT (pattern) |
| 12 | Rmanjini/jev-signals | event relevance/horizon/priced_in en 1 appel | WATCH |
| 13 | reachjalil/jevlogs ; koala73/worldmonitor | pré-filtre avec coût chiffré ; mode shadow + journal de désaccords | ADAPT (pattern) |
| 14 | MohibShaikh/jev-skillbench | cascade Jev → LLM sur bande incertaine, protocole résumable | ADAPT (pattern) |
| 15 | nikkoxgonzales/jev-certify | conformal risk control, casse sous décalage de prévalence | WATCH |
| 16 | stillmarcus24/jev-verify | détecte les sorties Jev « fabriquées » dans les dépôts tiers | ADOPT_FOR_BENCH (contrôle d'intégrité) |
| 17 | lizhuojunx86/llm-memory-audit (étude Jev) | test pré-enregistré de mémoire d'earnings (AUC 0,506) | WATCH (non cloné) |

## 3. TOP_REUSABLE_COMPONENTS (intégrer plutôt qu'écrire)

| Composant | Source | Ce qu'on n'écrit pas | Réserve |
|---|---|---|---|
| Modèles Noul/Choice/Score + réponses typées (pydantic) | typesafe-sdk-python 0.7.x | schéma de questions/réponses, retries, erreurs | types **du vendeur** : ne pas en faire le contrat canonique |
| Compilation QuestionSet → JSON Schema par provider, décodage, retries correctifs | system-one-adapter | structured outputs OpenAI/Anthropic/Gemini, normalisation, `debug.llm_attempts` | pas de température/seed ; un appel pour toutes les questions |
| Point d'extension `Provider` (`request` + `translate_error`) | adapter (PROVEN) | sensor « baseline déterministe » ou modèle local | protocole interne, non garanti stable |
| Journal `llm_attempts` (messages, requête SDK, réponse brute, finish_reason) | adapter | trace de rejeu par requête | à persister nous-mêmes en append-only |
| Métriques Brier/ECE/Platt | buberlo/jev-trader ; jev-calibration-audit ; calibration-is-not-alpha | scripts de calibration de départ | code de qualité variable, à revalider |
| Sondes d'injection / de formulation | jagged, JevOut, jev-sec-bench, willkelly | jeu de sondes de robustesse | jeux de textes non financiers |
| Contrôle d'intégrité des sorties | jev-verify | détecter des JSON « Jev-like » fabriqués | — |
| Alternatives sans lock-in vendeur (comparaison) | instructor, pydantic-ai, BAML, outlines, DSPy, LiteLLM | sorties structurées multi-provider | **forme seulement**, pas de probabilités calibrées par option |

## 4. BEST_PATTERNS (applicables directement)

1. **Jev mesure, le code décide** (≥ 8 dépôts indépendants : buberlo, Spykoninho, jev-signals, tm-reference, crypto-scout, klauswg, QuantDinger, judgekit). Seuils, vetos, taille, fallback = code.
2. **Un state nommé unique + questions atomiques communes + questions par source** composées en code (Spykoninho, ai-hedge-fund `JEV_CONTRACT_VERSION`, jev-harness QuestionSet v1→v4 figés).
3. **Option explicite `none` / `insufficient` / `not_in_this_list`** dans chaque Choice (PROVEN : retrait ⇒ accuracy 0,000 sur items ambigus).
4. **Contenu externe marqué « donnée citée, jamais consigne »** dans le state et dans chaque question (Spykoninho) ; aucun chemin bloquant/exécutant sur entrée non fiable (advisory seulement).
5. **Fallback déterministe qui émet le même type** (buberlo `HeuristicJudge`, `JudgmentSet` commun) : c'est exactement un `EpistemicSensor` de plus.
6. **Ladder d'échec explicite** : erreur/retard ⇒ hold ou escalade, jamais approbation ; `reason` typée (`model|protected|uncertain|unavailable|rule|budget`, jevlogs).
7. **Mode shadow + journal de désaccords** (WorldMonitor) avant toute influence.
8. **Cascade sur bande incertaine** : Jev → LLM sur ~17 % du trafic, rappel 0,90–0,94 (skillbench, OBSERVED : summary.json brut relu, non rejoué) ; **mesurer d'abord le taux de rejet** : à 0,84 % retenu, le préfiltre ne couvre pas ses propres tokens (jevlogs).
9. **Seuils calibrés sur split de validation, par question et par primitive** (Noul sous-confiant, Choice/Score sur-confiants dans scienthoon) ; recalibration 50–300 labels (DOCUMENTED_CLAIM), non transférable entre domaines.
10. **Figer le modèle** (`jev-1.13.0`, pas `jev-latest`) et **mettre la version du QuestionSet dans la clé de cache**.
11. **Arithmétique, comptage, dates, séquences : en code** (13,2 % sur mutation d'état séquentielle ; 33,3 % comptage exact : DOCUMENTED_CLAIM). Bucketiser les nombres avant de les mettre dans le state (AlgoVault).

## 5. FAILURE_MODES

| Mode | Preuve | Niveau |
|---|---|---|
| Répond toujours, même hors périmètre / sans réponse dans le texte | calibration-audit (recalcul), priorbench 0/30 signalés | PROVEN / OBSERVED |
| Injection d'évidence/autorité ; ajouts « naturels » | willkelly 147/200 ; jagged 96,5→26,5 % ; JevOut 61,4 % ; JevAdvBench 8,9–12,1 % (attaques simples) ; Decision Hijacking 1,8→3,5 % adaptatif ; cwhy 0,09 % (campagne étroite) | OBSERVED, **contradictoires selon l'attaque** |
| Confiance ≈ f(p_max), quantifiée 0,01, 1,0 exact sur ~56 % ; `choice` parfois 0,01 sous le max | jev-verify, jev-certify, SDK issue #15 | PROVEN (formule) / OBSERVED |
| Calibration non transférable entre domaines ; recalibration isotonique idem | scienthoon, Anthus, d3code | OBSERVED |
| Sensibilité à la formulation (rubrique oui/non inversée : 32,5 %) ; décomposition | xbill (secondaire), Beri | OBSERVED (un auteur) |
| Position/identification dans un state multi-lignes (0,420 par position vs 1,000 par nom) | willkelly | OBSERVED |
| Dérive silencieuse : alias `jev-latest`, « changements sans préavis » | doc TypeSafe | DOCUMENTED_CLAIM |
| Répétabilité imparfaite : 64 % de scores identiques sur 2 passes, écart moyen 0,005, max 0,08 | skillbench | OBSERVED |
| Limites : 32k tokens (state + question la plus longue), 64k total, 255 options/Choice | doc | DOCUMENTED_CLAIM |
| Pare-feu Cloudflare 403 HTML sur contenu ressemblant à des commandes curl | SDK-js #15, skillbench | OBSERVED ×2 |
| Console 500 pendant 2 jours ; 429 via Vercel gateway ; rate limits 1 200 req/min et 250 k tokens/s « modifiables » | skills #10, Vercel thread | OBSERVED |
| Clé API dans les messages d'exception (corrigé en 0.7.1) ; validation client incomplète (noul vide, state null, score null) | SDK issues #9/#14/#17/#12 | OBSERVED |
| Adapter : carte à zéro acceptée (#45), pas de timeout par provider (#48), refus ignorés (#46), `length` accepté (#38, corrigé) | issues adapter | OBSERVED |
| Égalité parfaite : `choice` = premier label, `confidence` = 0 | notre expérience | PROVEN |
| Sorties « Jev » fabriquées dans des dépôts tiers (121 fixtures ; 19/80 réimplémentations conformes) | jev-verify | OBSERVED |
| Données/annotations dérivées d'un LLM (accord avec 2 LLM comme vérité éditeur ; 82,4 % de labels dérivés du modèle dans JevAdvBench) | doc/papers | OBSERVED |
| Contamination temporelle inconnue : cutoff/base model UNKNOWN ; un seul test de mémoire d'earnings (AUC 0,506) | llm-memory-audit | OBSERVED (non cloné) |

## 6. CALIBRATION_EVIDENCE — état des preuves indépendantes

Séparation stricte **TYPE-SAFE OUTPUT** / **CALIBRATED-CORRECT DECISION**.

**Type-safe (établi)** : 0 sortie invalide sur 4 621 (scienthoon), 23 703 (agrégé), 5 échecs API sur 123 805 (willkelly). Les champs hors schéma ne sont pas facturés.

**Calibré/correct (partiel et conditionnel)** :

| Source | Résultat | Préc. |
|---|---|---|
| TypeSafe | aucun Brier/ECE/NLL/reliability publié ; « calibrated » = allégation | DOCUMENTED_CLAIM |
| willkelly (pré-enregistré) | ECE 0,075 routage tickets ; 3-SAT : probabilité ~constante ; AUROC confiance 0,878 poolé, 0,699 intra-condition | OBSERVED (logs bruts publics) |
| scienthoon | QA public ECE 0,024–0,032 (contamination probable) ; synthétique 0,107 ; priorité 44,7 %/0,74 ; signe de l'erreur dépend de la primitive | OBSERVED |
| jujumilk3 | ECE 0,023 (avec option) → 0,793 (sans) | **PROVEN** (recalcul) |
| Anthus, jourdanlabs | Noul 79,0 % annoncé/72,3 % réel ; Choice 91,4/76,1 ; CLINC150 0,020, Banking77 0,094 | OBSERVED |
| jev-certify | cible 5 % : 84,75 % traité seul à 2,65 % d'erreur ; casse sous décalage de prévalence ×3,6 | OBSERVED |
| jev-edgar (8-K) | à 0,97 annoncé : 49,1 % réel (n=636) | OBSERVED |
| Distribution shift | tickets → 3-SAT, règle inconnue, prévalence : dégradation | OBSERVED |
| Sensibilité question | rubrique inversée 32,5 % ; ordre ~0 (factuel) ; hétérogène | OBSERVED, mixte |

**Ce qui n'existe pas** : reliability diagrams indépendants multi-domaines répliqués par ≥ 2 auteurs ; calibration sur données financières PIT ; calibration après mise à jour de modèle ; tout audit de lookahead de Jev (AUC 0,506 sur earnings est le seul test connu). Conclusion : **calibration = hypothèse à mesurer par primitive et par question sur nos données, jamais un acquis.**

## 7. QUANT_FINANCE_EVIDENCE

Résultat global : **aucune preuve crédible d'edge prédictif** ; preuves crédibles de **classification de texte financier** et de **patterns d'architecture**.

- Spykoninho/trading-bot-jev (MIT) : 49 496 publications, ~2,50 $ ; avec/sans biais news : −2,1 pts (EUR), −2,8 pts (USDC), +4,9 ; « le signe change, c'est du bruit » ; coefficients d'effet à 0 sauf `crypto_support`. **Seule mesure avec/sans.** (code lu ; chiffres auto-déclarés)
- Gaurav-Gosain/jev-alpha-bench : 5 000 titres Nasdaq-100 2022–2023, IC de rang +0,237 jour de publication (non tradable), −0,008 tradable ; −18,4 bps net. Risque de lookahead reconnu.
- egrm07/jev_bitcoin_backtest : 10 représentations de barres BTC 5 min ; AUC 0,471–0,503 ; toutes perdantes après 14 bps.
- alakise/calibration-is-not-alpha : Brier 0,2131, ECE 0,042 mais ΔBrier vs volatilité 1,4e-05 ; « NO CURRENT ALPHA CANDIDATE » (27 tests PROVEN).
- Siim/jev-claim-vs-measured : 35 685 réponses ; latence médiane 294 ms, 0,00 % < 100 ms ; 53,4 % à 1 s (+0,04 bp) ; texte d'annonces d'exchanges 99,3 % à conf ≥ 0,8. « 2 NUMBERS DID NOT REPRODUCE » (XGBoost, pas Jev).
- nishioka-shinji/jev-edgar : 1 054 8-K, Brier 0,4276 vs 0,2494 base.
- aiihaz/jev-tm-reference : une régression logistique fait mieux ; scoreboard AML.
- klauswg/jev-guard : 50 % Jev vs 68 % règles seules (100 cas synthétiques) ; distil-labs : 0,79 vs 0,98 (fine-tuné 4B) sur décision multi-documents ; myc0576/SmartMoney-Cub : 78,43 % vs 83,33 % règles.
- ruyianry/JevGym : gain annoncé, non vérifié, licence non commerciale.
- Prototypes d'architecture sans performance : jarrodwatts/jev-trader (mock par défaut), aowang-ai/jev-trade, buberlo (fallback déterministe, pas de live), Rmanjini/jev-signals, QuantDinger (gate fail-open), moomoo-jev-trader, AlgoVault, ai-hedge-fund (adaptateur).
- **NONE_FOUND** : anomaly detection de séries de marché avec Jev ; pré-filtre Jev → LLM sur news financières ; quorum multi-agents autour de Jev ; backtest significatif d'un signal Jev ; multi-classes d'actifs (actions/FX/taux).

## 8. PROPOSED_AURUMSHIFT_V1 (architecture minimale, 5 composants nouveaux)

Cadrage : Jev = **capteur épistémique** qui écrit des observations append-only ; il ne lit ni n'écrit DecisionV1, ne touche ni quorum ni exécution. Toute promotion passe par OutcomeV1/Retex. INFERENCE : la faisabilité réelle dépend du dépôt AurumShift privé (non vu) ; ce qui suit est un candidat à adjuger plus tard.

1. **QuestionSetV1 (registre versionné, canonique et neutre vis-à-vis du vendeur)** : identifiants de questions immuables, hash de contenu, primitive (noul/choice/score), critères littéraux, **option `none/insufficient` obligatoire** sur tout Choice. Se compile vers `typesafe_sdk.Noul/Choice/Score` (réutilisation) mais reste défini chez nous (exit cost faible).
2. **AurumStateV1 → StateView pour capteurs** : rendu déterministe, borné en tokens, horodaté `as_of` PIT, nombres bucketisés en code, contenu externe explicitement balisé « donnée citée » ; hash du rendu. (Le PIT est dans notre state ; rien dans Jev n'aide le PIT.)
3. **EpistemicSensor (protocole mince) + 3 adaptateurs** : `JevSensor` (typesafe-sdk, modèle épinglé `jev-1.13.0`), `LLMSensor` (system-one-adapter → Claude/GPT, même QuestionSet), `RuleSensor` (baseline déterministe, via le point d'extension Provider éprouvé). Sortie unique typée.
4. **JudgmentObservationV1 (journal append-only, PostgreSQL)** : state hash, QuestionSet version+hash, sensor+model id exact, requête/réponse brute (`llm_attempts`), latence, tokens, coût, retries, erreurs. Jamais de mise à jour ; rejouable hors ligne (le service peut changer ou disparaître).
5. **SensorEvalHarness** : jointure PIT observation ↔ OutcomeV1, Brier/NLL(clippé)/ECE/reliability **par primitive et par question**, recalibration **sur split de tuning uniquement**, comparaison appariée à la baseline, sondes de stabilité (répétition, reformulation, ordre, rubrique inversée), sondes d'injection, lookahead, coût/latence.

Hors périmètre (à ne pas construire) : routeur, cache sémantique, prompts par instrument/agent/provider, changement de quorum. **Prompt debt** : un seul contrat d'état + un QuestionSet versionné + trois primitives ⇒ N jugements sans N prompts ; l'adapter génère lui-même les instructions par provider à partir du QuestionSet.

## 9. EXPERIMENT_MATRIX

Principe : mêmes observations PIT, mêmes labels/outcomes (OutcomeV1), mêmes métriques, mêmes splits (tuning / held-out non touché avant gel), pré-enregistrement des seuils, **évaluation prospective (forward-only) comme preuve principale**, rétrospective seulement avec états anonymisés + test de lookahead préalable.

| Bras | Contenu | Rôle |
|---|---|---|
| **B0 BASELINE** | signal/scores existants AurumShift + `RuleSensor` sur le même QuestionSet | référence à battre ; plancher déterministe |
| **B1 BASELINE + JEV** | B0 + probabilités Jev (`jev-1.13.0`) comme features observationnelles (aucune autorité) | valeur incrémentale |
| **B2 CLAUDE** | même StateView + même QuestionSet via adapter (`probabilities` ; température/seed fixés côté provider si possible ; K répétitions) | même schéma, autre capteur |
| **B3 GPT** | idem B2 | idem |

Métriques communes : Brier, NLL (probabilités clippées, ε déclaré), ECE (bins adaptatifs) + reliability, AUROC, courbe risque/couverture (abstention), ΔBrier apparié vs B0 avec IC bootstrap, stabilité (K répétitions, reformulation, ordre, rubrique oui/non inversée), matrice de confusion **des causes de HOLD** vs sous-échantillon étiqueté par humain (absence / contradiction / insuffisance / valide-bloqué), latence p50/p95/p99, tokens, coût, taux d'erreurs/retries.

Sondes fixes (mêmes pour tous les bras) : injection d'évidence/autorité sur états falsifiés, ajouts « naturels », option `none` retirée, hors-périmètre, décalage temporel (avant/après cutoff supposé), état encombré.

Critères de décision proposés (INFERENCE, à geler avant exécution) : **continuer** seulement si (a) ΔBrier apparié vs B0 a un IC excluant 0 sur held-out ; (b) ECE post-recalibration (tuning) ≤ 0,05 par primitive utilisée ; (c) taux de flips sous injection sur nos sondes ≤ seuil fixé ; (d) test de lookahead sans signal ; sinon rester en WATCH ou REJECT pour la tâche concernée. Différentiel B1 vs B2/B3 à coût égal est un résultat en soi.

Note : la recherche précédente suggère que la valeur la plus plausible est **triage/classification de texte, séparation de causes de HOLD et juge de Retex**, pas la prédiction de prix (§7).

## 10. VERDICT

**JEV_AURUMSHIFT = ADOPT_FOR_BENCH** — strictement en capteur hors ligne/shadow, sans autorité, sans changement DecisionV1/quorum/runtime.

Preuves pour :
- Coût dérisoire (~0,042 $/M tokens d'entrée, DOCUMENTED_CLAIM ; ~0,038 $/1000 emails, OBSERVED), donc un bench complet coûte quelques dollars.
- Validité de schéma établie ; latence médiane 127–430 ms ; batch de nombreuses questions sur un même état.
- Bonne calibration **dans le domaine** et classification de texte financier solide ; patterns d'architecture réutilisables (Jev mesure, code décide).
- Le protocole d'évaluation tiers est abondant et rejouable (willkelly, calibration-audit, jagged, Siim).

Preuves contre / réserves (pourquoi pas plus que « bench ») :
- **Aucun edge finance** ; calibration OOD dégradée ; injection efficace ; modèle fermé, sans cutoff ni architecture connus ⇒ **PIT/lookahead non garanti**.
- Écosystème de 2 semaines, un modèle, mono-auteur : aucune réplication solide.
- Le sujet HOLD n'est pas résolu nativement : à traiter par questions atomiques composées en code.

**WATCH** appliqué à : l'ajout de Jev au chemin de décision, au pré-filtre finance → LLM (NONE_FOUND), aux gains de vitesse « 40–200× » (tiers : 0,5× à 18×).
**REJECT** appliqué à : tout usage de Jev comme autorité ou seuil bloquant sur texte externe non filtré ; l'usage de `confidence` comme signal indépendant.
**system-one-adapter-python** : **ADAPT** (couche d'exécution multi-provider derrière notre propre QuestionSet/EpistemicSensor, version épinglée, vendored si besoin) — voir `02_ADAPTER_REVIEW.md`.

Prochaines étapes suggérées (hors périmètre de cette mission) : obtenir une clé, contrôler les CGU (publication de résultats), exécuter d'abord les sondes d'injection/lookahead et la calibration par primitive sur un jeu PIT gelé, avant toute jonction avec des outcomes.
