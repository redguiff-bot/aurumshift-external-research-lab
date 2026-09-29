# 01 — Fiches ressources (format AurumShift)

Toutes dates au 2026-09-29. « Preuve » = niveau de preuve du lab. Coûts/latences : voir 00_RAPPORT_FINAL.md §0 (aucun appel Jev réel par nous). PIT_COMPATIBILITY : aucune des ressources ne fournit de PIT ; le state est JSON opaque, l'horodatage `as_of` et le hash restent à notre charge.

---
## 1. typesafe-ai/system-one-adapter-python
- NAME: system-one-adapter · URL: https://github.com/typesafe-ai/system-one-adapter-python · SOURCE_TYPE: repo officiel
- LAST_ACTIVITY: 2026-09-22 (v0.2.1) · LICENSE: MIT · MAINTENANCE: 2 mainteneurs éditeur, bot de release ; 5 issues ouvertes ; 0 dépendant ; 54 forks
- WHAT_IT_DOES: `system_one(state, questions, provider, model)` vers OpenAI/Anthropic/Gemini/custom, mêmes primitives Noul/Choice/Score, sorties structurées ou prompted, retries correctifs, journal des tentatives
- WHY_RELEVANT: même state + mêmes questions typées → Claude/GPT/baseline (bras B2/B3/B0)
- REUSABLE_COMPONENT: compilation QuestionSet→schéma, décodage, retries, `llm_attempts`, `Provider` protocol
- CUSTOM_CODE_REMOVED: génération de prompts/schémas par provider ; gestion de structured outputs et erreurs
- PIT_COMPATIBILITY: neutre (JSON opaque) · DECISION_AUTHORITY_RISK: nul (bibliothèque client)
- CALIBRATION_EVIDENCE: aucune (probabilités LLM verbalisées) · LATENCY_EVIDENCE: `usage.latency` mesurée par appel ; pas de bench publié · COST_EVIDENCE: tokens comptés ; prix = ceux du provider
- SECURITY_RISK: état marqué non fiable dans le prompt (mitigation partielle, non garantie) ; pas de timeout par provider (#48)
- INTEGRATION_EFFORT: faible · EXIT_COST: faible si QuestionSet canonique interne
- RECOMMENDATION: **ADAPT** (PROVEN : 424 tests hors ligne ; fournisseur custom exécuté) — détail : `02_ADAPTER_REVIEW.md`

## 2. typesafe-ai/typesafe-sdk-python
- URL: https://github.com/typesafe-ai/typesafe-sdk-python · SOURCE_TYPE: SDK officiel · LAST_ACTIVITY: 2026-09-26 (v0.7.2)
- LICENSE: MIT (fichier LICENSE avec placeholders `[year] [fullname]` non remplis : à noter) · MAINTENANCE: 12 issues, 0 PR ; breaking 0.6.0 et 0.7.0
- WHAT_IT_DOES: client `TypeSafeClient`/Async, types Question/Answer pydantic, `RetryPolicy`, erreurs, défaut `jev-latest`, base `https://api.typesafe.ai`, timeout 10 s, `POST /v1/systemone`
- WHY_RELEVANT: unique voie officielle vers Jev ; types de questions/réponses réutilisables
- REUSABLE_COMPONENT: client, retries (Retry-After), types · CUSTOM_CODE_REMOVED: HTTP, sérialisation, retry
- PIT_COMPATIBILITY: neutre · DECISION_AUTHORITY_RISK: nul
- CALIBRATION_EVIDENCE: voir rapport §6 · LATENCY/COST: voir rapport §1.8 · SECURITY_RISK: clé dans exceptions (corrigé 0.7.1) ; 403 Cloudflare sur contenu type curl (JS #15)
- INTEGRATION_EFFORT: faible · EXIT_COST: faible derrière `JevSensor`
- RECOMMENDATION: **ADOPT_FOR_BENCH** (épingler `0.7.2` et le modèle `jev-1.13.0`)

## 3. typesafe-ai/typesafe-sdk-js
- URL: https://github.com/typesafe-ai/typesafe-sdk-js · SOURCE_TYPE: SDK officiel · LAST_ACTIVITY: 2026-09-15 (v0.6.0, mirror ; 14 issues ouvertes, 0 PR) · LICENSE: MIT
- WHAT_IT_DOES: client TS (`systemOne`, `noul/choice/score`) · RELEVANT: source de bugs/limites documentés (statuts 402/413 génériques, `Retry-After` vide, nombres non finis → null, pas de cache de critères, pas de multi-label calibré)
- RECOMMENDATION: **WATCH** (pas notre langage ; utile comme registre de failure modes)

## 4. typesafe-ai/WorkflowEvals
- URL: https://github.com/typesafe-ai/WorkflowEvals · Apache-2.0 · 4 étoiles · MAJ 2026-09-28/29
- WHAT: code de reproduction d'evals.typesafe.ai : 4 workflows (invoice 150, customer_service 204, agent_trace 111, security_incidents 240 = 705 cas ; TypeSafe annonce 711), providers openai/anthropic/fireworks/groq/cerebras/typesafe ; datasets HuggingFace
- LIMITE: vérité = accord avec 2 LLM frontier (DOCUMENTED_CLAIM : 67,8 % d'accord), pas de vérité terrain ; workflows éditeur
- RECOMMENDATION: **WATCH** (modèle de protocole ; ne prouve ni justesse ni calibration)

## 5. willkelly/jev-evaluation
- URL: https://github.com/willkelly/jev-evaluation · MIT · 2026-09-21 · SOURCE_TYPE: benchmark tiers pré-enregistré
- WHAT: 123 805 requêtes, 9 expériences, 28 prédictions (12/25 testables confirmées), 12,69 $, logs bruts 47 Mo ; batch 200 questions ; injection ; 3-SAT ; PROMPTING.md (13 règles)
- WHY: meilleur protocole tiers (preregistration + logs) pour notre harnais ; résultats calibration/injection/batch
- CALIBRATION_EVIDENCE: ECE 0,075 (domaine natif) ; effondrement hors domaine · LATENCY: batch latence quasi plate · COST: 20× moins de tokens par batch
- SECURITY_RISK (mesuré): injection d'autorité 147/200 · INTEGRATION_EFFORT: faible (scripts) · EXIT_COST: nul
- RECOMMENDATION: **ADOPT_FOR_BENCH** (protocole et sondes)

## 6. jujumilk3/jev-calibration-audit
- URL: https://github.com/jujumilk3/jev-calibration-audit · MIT · 2026-09-18 · benchmark tiers
- WHAT: ~7 000 appels < 1 $ ; abstention, ordre, complémentarité Noul, interférence batch, coréen/anglais
- **PROVEN par nous** : abstention.jsonl recalculé (ECE 0,793 sans option vs 0,023 avec)
- WHY: directement lié au problème HOLD (option d'abstention obligatoire) · RECOMMENDATION: **ADOPT_FOR_BENCH**

## 7. scienthoon/jev-ood-calibration
- URL: https://github.com/scienthoon/jev-ood-calibration · MIT · 2026-09-22 · ~0,06 $
- WHAT: ECE par primitive, OOD sur règle implicite (priorité 44,7 %/0,74), température par primitive ; correction du 09-22 documentée
- RECOMMENDATION: **ADOPT_FOR_BENCH** (protocole) · réserve : QA public probablement vu à l'entraînement

## 8. Sondes d'injection : zkousama/jagged ; xzx34/JevOut (arXiv 2609.30243) ; cwhy/decision-injection-bench ; Gaurav-Gosain/jev-sec-bench
- jagged: 486 discussions AfD, 96,5 % → 26,5 % après une phrase injectée · JevOut: 61,4 % (312/508) en ≤ 64 évaluations · cwhy: 1/1 056 flips (campagne étroite, PROVEN présent dans le README) · sec-bench: acc 96,5 %/AUC 0,9927 sur deepset/prompt-injections, contexte de déploiement +20 pts de rappel
- SECURITY_RISK: c'est l'objet même · RECOMMENDATION: **ADOPT_FOR_BENCH** (jeux de sondes, pas de conclusion d'immunité)

## 9. Siim/jev-claim-vs-measured
- URL: https://github.com/Siim/jev-claim-vs-measured · MIT · 2026-09-21
- WHAT: réfute un post « Jev pour le HFT » ; 35 685 réponses en cache SQLite ; latence médiane 294 ms (p99 447), 0 % < 100 ms ; +0,04 bp à 1 s, −0,30 bp à 15–60 min ; texte d'annonces d'exchanges 99,3 % à conf ≥ 0,8
- PROVEN (agent) : `check_headline_numbers.py` reproduit tout sauf 2 valeurs (XGBoost, pas Jev)
- QUANT_FINANCE: NONE alpha · RECOMMENDATION: **ADOPT_FOR_BENCH** (protocole latence/PnL brut vs net)

## 10. alakise/calibration-is-not-alpha
- URL: https://github.com/alakise/calibration-is-not-alpha · MIT · 2026-09-20 · 40 320 états BTC ; Brier 0,2131, ECE 0,042, ΔBrier vs volatilité 1,4e-05
- PROVEN (agent) : tables reconstruites hors ligne, 27 tests OK · WHY: **calibré ≠ informatif** : modèle de rapport pour notre B1 · RECOMMENDATION: **ADOPT_FOR_BENCH**

## 11. Spykoninho/trading-bot-jev
- URL: https://github.com/Spykoninho/trading-bot-jev · MIT · 2026-09-19 · Bot crypto EMA200 4h (Bitvavo), paper par défaut
- WHAT: 1 requête par publication ; 4 questions communes (asset Choice, sentiment Score, material Noul, regulatory_risk Noul) + questions par source (Fed/Trump/SEC/Binance) sur un state nommé unique ; code compose : biais ±0,5 % + veto si `regulatory_risk ≥ 0,7` ; coefficients d'effet calibrés par étude d'événements (zéros sauf `crypto_support`)
- PREUVE: −2,1 / −2,8 / +4,9 pts avec/sans ; 49 496 publications, ~2,50 $ ; limites déclarées (une période, actifs corrélés, seuils arbitraires, contamination possible)
- AUTHORITY_RISK: Jev n'a qu'un biais/veto borné · RECOMMENDATION: **ADAPT** (pattern state unique + SOURCE_RULES + veto codé + texte externe « donnée citée »)

## 12. buberlo/jev-trader
- URL: https://github.com/buberlo/jev-trader · MIT · 2026-09-20 · 34 fichiers Python
- WHAT: features déterministes → snapshot < 400 tokens → 6 jugements atomiques en 1 requête → politique → vetos de risque codés en dur → paper → journal (état, décision, résultat) + Brier/ECE/Platt ; `HeuristicJudge` émet le même `JudgmentSet`
- PROVEN (agent) : `pytest` 61 tests OK ; `paper --blocks 2000` tourne **sans Jev** (fallback) : 154 fills, realized −89,94 (flux synthétique) ; Phase « Live Jev » non cochée
- RECOMMENDATION: **ADAPT** (pattern capteur + fallback même type ; aucune preuve de performance)

## 13. Pré-filtre / shadow : reachjalil/jevlogs ; koala73/worldmonitor ; MohibShaikh/jev-skillbench
- jevlogs (MIT, 2026-09-21): route `retain|analyze`, ERROR/FATAL contournent, cache par hash, `reason` typée ; HDFS rappel 0,992 avec 1 % retenu vs 0,833 à 14 % (Luna) ; **0,84 % retenu ne couvre pas les tokens de Jev** (calcul du dépôt)
- worldmonitor (AGPL-3.0 : **contamination copyleft si code réutilisé**, ne réutiliser que le pattern): Jev en **shadow** à côté du LLM, journal de désaccords (Redis, cap 2 000, TTL 14 j), disjoncteur ; ~30 % de désaccords de niveau sur 413 titres (commentaire du code, non rejoué)
- skillbench (MIT): 7 907 skills, rappel 0,755/FPR 0,0008 ; cascade sur bande 0,05–0,5 (17,1 % du trafic) → rappel 0,898–0,944 ; 21/1000 requêtes 403 edge ; alias mouvant
- RECOMMENDATION: **ADAPT** (pattern) — hors finance ; finance + LLM aval NONE_FOUND

## 14. Rmanjini/jev-signals
- URL: https://github.com/Rmanjini/jev-signals · MIT · 2026-09-22 · 7 questions/appel (direction, magnitude, horizon, surprise, priced_in, hard_fact, thesis_break), gate catégoriel, `quality = surprise×(1−priced_in)×hard_fact`
- « It has no measured edge » (auteur) · leçon : seuillage Noul à 0,5 n'a émis aucun signal en live tout en passant les tests mock
- RECOMMENDATION: **WATCH** (meilleur exemple event relevance/horizon/impact ; zéro validation)

## 15. nikkoxgonzales/jev-certify
- URL: https://github.com/nikkoxgonzales/jev-certify · MIT · CLINC150 2 412 réponses ; conformal risk control ; cible 5 % → 84,75 % traité seul à 2,65 % d'erreur ; cible 1 % infaisable ; casse sous décalage de prévalence
- RECOMMENDATION: **WATCH** (outil pour garanties de risque sélectif ; utilise un endpoint OpenRouter `alpha`)

## 16. stillmarcus24/jev-verify
- URL: https://github.com/stillmarcus24/jev-verify · MIT · 279 842 réponses de 88 dépôts, 96,79 % conformes ; 121 fixtures « fabriquées » ; 19/80 réimplémentations « Jev-compatibles » conformes
- WHY: **contrôle d'intégrité de toute donnée tierce Jev-like** que nous voudrions réutiliser · RECOMMENDATION: **ADOPT_FOR_BENCH**

## 17. lizhuojunx86/llm-memory-audit (étude 2026-09-jev)
- URL: https://github.com/lizhuojunx86/llm-memory-audit/tree/main/studies/2026-09-jev · 12 533 earnings US, 38 956 appels, AUC intra-firme 0,506 (beat/miss) ; contrôle positif Claude Sonnet 5 = 0,587 ; pré-enregistré ; 757 événements prospectifs après 2027-01-08
- LIMITE: résultat borné à la classe « earnings » ; non cloné par nous (OBSERVED via résumé) · RECOMMENDATION: **WATCH** (méthode à réutiliser pour l'audit de lookahead PIT)

---
## Références de contexte (non des candidats)
- Papiers : arXiv 2609.28613 (Decision Hijacking), 2609.31142 (JevAdvBench), 2609.33401 (sécurité agents, date de venue incohérente à vérifier), 2609.26550 (JEV-as-a-Judge), 2609.24052 (récits de crashs → 27 questions), 2512.23847 / 2609.20554 / 2601.13770 (lookahead LLM), 2305.14975 (calibration verbalisée), 2609.28940 (pentest, sans puissance statistique), 2609.29429 (affiliation UNKNOWN), 2609.25498 (**exclu** : « JevBench » homonyme, pas un test de Jev).
- Alternatives ouvertes non-autorégressives (sources non lues individuellement) : Laya (poids CC-BY-NC-4.0 selon un dataset tiers), OpenSourceJev, Von 1.0, Nimble-9B : à sourcer avant toute évaluation ; priorité Laya vs Jev contestée (revendication non arbitrée).
- Pas de traçabilité individuelle des chiffres des listes awesome-* (agrégats) : ne pas les citer comme preuves.
