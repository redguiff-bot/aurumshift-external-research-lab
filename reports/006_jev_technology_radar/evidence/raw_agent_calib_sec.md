# Jev (TypeSafe AI) - Calibration / Sécurité / Papers (au 2026-09-29)

Étiquettes: PROVEN = mesuré par tiers avec code/données rejouables ET vérifié par moi via la source primaire (au niveau résumé WebFetch, pas re-exécuté); OBSERVED = mesure tierce non rejouée par moi; DOCUMENTED_CLAIM = déclaration vendeur; INFERENCE = mon raisonnement; UNKNOWN.
IMPORTANT: je n'ai rien rejoué. "PROVEN" ici = vérifié sur source primaire lue, pas répliqué par moi. Les WebFetch passent par un petit modèle de résumé: les chiffres sont à recouper sur les sources avant décision. Aucun accès à Jev (pas de clé API).

## 1. Documentation officielle TypeSafe (docs.typesafe.ai)

Pages lues: /introduction, /api, /models.md, /confidence.md, /introduction/machine-learning-primer.md, /model-jaggedness/jev-1.13.md, index /llms.txt.

- Modèle: un seul, Jev 1.13 (`jev-1.13.0`), alias `jev-latest` et `jev-preview` identiques. [DOCUMENTED_CLAIM]
- Architecture: "System One model"; questions évaluées "en parallèle et isolément" sur le même state; "ajouter des questions change à peine le temps de réponse". Aucun détail encoder/decoder, taille, base model. Wikipedia/presse: "transformer-based", aucune archi/poids/paper technique publiés. [DOCUMENTED_CLAIM; archi = UNKNOWN]
- Entraînement: "RLCD" (Reinforcement Learning for Calibrated Decisions), méthode propriétaire non publiée. Données: "entièrement synthétiques" (déclaration CEO Diogo Almeida, rapportée par presse/dev.to, pas retrouvée sur la doc lue). Mêmes poids pour tous les comptes, pas de fine-tuning par client. [DOCUMENTED_CLAIM]
- Prétention d'un training "calibration by construction via proper scoring rules": vient du paper tiers 2609.28940 (Table II), pas de TypeSafe. [INFERENCE d'un tiers, non documenté]
- Métriques de calibration publiées par TypeSafe: aucune trouvée (pas de Brier, ECE, NLL, reliability diagram). Deux sources tierces (jujumilk3, dev.to/xbill) le disent explicitement. Un chiffre ECE 0.246 "de TypeSafe" circule dans 2609.28940 (mesuré sur une autre tâche, les auteurs disent non comparable). [UNKNOWN pour TypeSafe; 0.246 = DOCUMENTED_CLAIM de provenance floue]
- OOD/limites: la page "Jev 1.13 Jaggedness" liste: lecture littérale, pas de calcul/comptage fiable, mauvais sur valeurs numériques/dates (lues comme texte), double négations/indirection, précision qui baisse quand le state contient beaucoup de contenu non pertinent, contenu adversarial "peut déplacer la réponse", instructions contradictoires, pas d'invariants entre questions (P(noul) et 1-P(not noul) non comparables), non entraîné à générer du texte. [DOCUMENTED_CLAIM, aveu vendeur]
- Confidence: statistique dérivée de la distribution, pas une probabilité; Choice: (3*pmax - 1)/2 (page doc; le repo awesome-robustness écrit (N*pmax-1)/(N-1), formule générale, cohérente pour N=3? non vérifié). Doc: seuils dépendent du domaine, à tester sur ses données. [DOCUMENTED_CLAIM]
- Contexte: 64k tokens par requête; 32k pour state + question la plus longue. Texte seul (string/JSON/array); anglais optimal. [DOCUMENTED_CLAIM]
- Max options par Choice: 255; Score: 2 à 10 niveaux. Max questions/requête: non spécifié dans la doc (le test willkelly a poussé jusqu'à 255 questions/requête sans dégradation). [DOCUMENTED_CLAIM / OBSERVED]
- Prix: $0.042 / M tokens input (=$42/B), output gratuit. [DOCUMENTED_CLAIM]
- Rate limits: 250 000 tokens/s et 1 200 req/min, "peuvent changer sans préavis"; codes 401/422/429/529. [DOCUMENTED_CLAIM]
- Latence: pas de spec dans la doc. Marketing: 70-500 ms (presse), 193.6x plus rapide / 444.6x moins cher (homepage, comparateurs non nommés, 97.8-193.6x selon workflow selon dev.to). [DOCUMENTED_CLAIM]
- Benchmark TypeSafe: 711 cas, 4 workflows (Security Incidents, Agent Trace Observability, Invoice Processing, Customer Service); Jev 67.8% d'accord avec une référence = moyenne de 2 LLM frontier (la référence n'est donc pas une vérité terrain); 76.0% service client, 61.8% factures; comparateur non nommé 74.1%. Sources secondaires (layer3labs, autres blogs), pas le dashboard vendeur lu directement. [DOCUMENTED_CLAIM, non répliqué]
- "Cannot hallucinate": la garantie porte sur la validité de schéma. Voir section 2. [DOCUMENTED_CLAIM: type-safe seulement]
- Non trouvé: model card technique, paper TypeSafe, arXiv TypeSafe, repo HF officiel. [UNKNOWN]

## 2. Évaluations indépendantes

### 2.1 TYPE-SAFE OUTPUT (sortie valide)
- 0 réponse invalide sur 4 621 appels (scienthoon). [OBSERVED]
- 0 invalide sur 23 703 appels (agrégé par xbill/dev.to). [OBSERVED, secondaire]
- willkelly: 5 échecs sur 123 805 requêtes (échecs = erreurs API/transport, nature exacte non vérifiée). [OBSERVED]
- Champs hors schéma facturés 0 token, "l'API agit comme un pare-feu" (JevAdvBench). [OBSERVED]
=> Conclusion: la validité de type est bien tenue. Ceci ne dit RIEN sur la justesse ni la calibration.

### 2.2 CALIBRATION / JUSTESSE
Tous les chiffres ci-dessous: OBSERVED (tiers, mesures rejouables mais non rejouées par moi).

| Source | Protocole | Résultat |
|---|---|---|
| scienthoon/jev-ood-calibration (19 sept 2026, ~$0.06, via Vercel AI Gateway) | 3 benchmarks publics (probablement vus à l'entraînement) + 900 tickets synthétiques | OpenBookQA acc 94.2% ECE 0.024 (T=0.96); CommonsenseQA 88.1% / 0.032 (T=1.35); HellaSwag 86.1% / 0.029 (T=1.00). Synthétique: queue (choice) 89.0% ECE 0.082 (surconfiant), angry (bool) 91.7% ECE 0.079 (T=0.66 sous-confiant), priority (score, non déductible du texte) 44.7% ECE 0.325 (T=1.92, proba moyenne 0.74), global 75.1% ECE 0.107 (4.4x le noise floor). Le signe de la mis-calibration change selon la primitive. Probabilités quantifiées à 0.01, souvent exactement 0 ou 1 (un item OpenBookQA a 0.00 sur la bonne réponse). "Ne pas seuiller sur `confidence`": moins bon que pmax. |
| willkelly/jev-evaluation (pré-enregistré, 9 expériences, 28 prédictions, 123 805 requêtes, $12.69) | jev-1.13.0 | ECE 0.075 sur routage de tickets support (domaine cible). Sur 3-SAT aléatoire: répond "satisfiable" partout, proba moyenne varie de 0.026 alors que la vérité varie de 1.0; un programme trivial le bat sur 41/75 conditions. AUROC de confidence 0.878 global mais 0.699 intra-condition. Injection grossière: échoue (1/200 tickets); injection "autorité": 147/200 réussies, confidence 0.983 -> 0.680. Batching jusqu'à 255 questions sans perte de justesse. |
| jujumilk3/jev-calibration-audit (~7 000 appels, <$1, MMLU-ProX, KoBBQ, IC bootstrap) | API seule | Retirer l'option "abstain": accuracy 0.950 -> 0.000 sur items sans réponse, confidence reste 0.79, ECE 0.793. P(x)+P(non x): moyenne ~1.02, plage 0.71-1.42; Noul vs Choice à 2 options sur la même question: écart moyen 0.125. Ordre des options: shift moyen 0.005, 0 flip d'argmax sur 400. Batching de 16 questions: 0.4% de flips. Coréen ~ anglais. |
| xbill, dev.to (24 sept 2026, revue secondaire de 14 preprints/104 repos/33 posts; sources collectées avec Claude, GDE non lié à TypeSafe) | Re-scoring de données publiées | ECE livré 0.071 sur suite publique de 13 sous-ensembles (meilleur des modèles testés, source Bespoke Labs, qui vend un concurrent). Le stockage à 0.01 -> 70.4% des probas de choix exactement 0 dans un échantillon. Une température unique ajustée sur 50-300 labels réduit l'erreur ~74%. Surconfiant sur GoEmotions (15% d'acc à confiance 0.80-0.95), sous-confiant sur récits d'accidents. Accuracy vs LLM: Jev 72.5% vs 74.5-84% pour les LLM comparés (noms de modèles rapportés tels quels par la source, non vérifiés par moi). BANKING77: 75.3-84.0% sur 8 runs. Encodeur fine-tuné 310M/200 labels bat Jev de 12 pts en classification de news. Répétabilité: 1.33-2.2% de variance entre appels identiques. Russe XNLI 88.3 -> 77.3. **Échange de la rubrique derrière "oui"/"non": 32.5% de réponses changées (vs ~2% avec noms neutres), AUROC 0.81 -> 0.58.** Confiance ~0.79-0.83 sur mauvaises réponses quand la question n'a pas de réponse dans le texte. |
| jmanhype/jev-dspy-lab | 24 cas synthétiques, live jev-1.13.0 | ECE 0.0583, 91.3% de précision à 95.8% de couverture (seuil 0.7). Auteurs: "pas une claim de qualité du modèle". Trop petit pour conclure. |
| 2609.33401 (arXiv, Yixuan Liu et al.; l'entête indique FSE "juillet 2027", incohérence de date à vérifier) | Jev, Laya, Decider, Nimble sur décisions de sécurité agents, partitions calibration/seuil/test séparées | Jev rate les 129 attaques sans instruction directe; ne signale qu'1 entrée bénigne. Sur détection d'injection: <0.21% de proba "unsafe" sur les entrées classées sûres, mais 9.14% étaient dangereuses. Avec budgets d'erreur stricts (1% manquées, 5% fausses alertes), quasi aucune décision automatisable. Second juge: complémentarité limitée. |
| 2609.28940 (dos Santos, 24 sept 2026) | Papier conceptuel pentest, 1 seul run | Pas de preuve statistique (les auteurs le disent). Latence citée 236-276 ms Jev (autre source: ~105 ms serveur, ~76 ms réseau à soustraire). |

Contradictions à noter:
- Un blog dit "aucun benchmark indépendant n'existe" (layer3labs): périmé, faux au 29 sept.
- Le résumé awesome-jev-robustness cite "0.09% de flips sur 1 056 attaques vs 3.0-62.6% pour les concurrents": je n'ai pas retrouvé la source primaire; contredit JevOut (61.4%) et willkelly (147/200). Traiter comme NON_VÉRIFIÉ.
- Les listes "awesome-jev*" sont des agrégateurs (nombreux forks); pas des preuves.

INFERENCE (mes conclusions):
1. La calibration est acceptable dans le domaine d'entraînement (ECE ~0.02-0.08 sur QA/routage) et s'effondre hors domaine ou sur questions sans réponse (0.3-0.8). Ne pas transférer à la finance sans mesure propre.
2. Probabilité quantifiée à 0.01 et souvent 0/1: NLL/log-loss non borné, à clipper; pas de résolution fine près de 0/1. Cela pénalise fortement Brier/NLL sur les erreurs confiantes.
3. Recalibrer par primitive (Noul, Choice, Score) avec 50-300 labels au minimum; signe d'erreur différent selon la primitive.
4. Il faut toujours une option "aucune/abstain" et tester son retrait.
5. Sensibilité à la formulation: inversion oui/non très forte (xbill), mais ordre des options négligeable (jujumilk3). Résultats mixtes: tester les deux dans notre schéma.

## 3. Sécurité / robustesse

Preuves Jev (tests tiers):
- **JevOut** arXiv 2609.30243 (Zixiang Xu, USC, 24 sept 2026): optimisation guidée par probabilité d'ajouts de contexte "naturels"; sur 7 datasets (MMLU-Pro, SuperGPQA, MuSR, ToMBench, LAR-ECHR, SATA-Bench, BFCL V4). Jev 1.13.0: 61.4% (312/508) des décisions initialement correctes redirigées vers une mauvaise réponse en 64 évaluations; 229 cas avec p >= 0.7 sur la mauvaise option; 40.0% (juridique) à 85.7% (tool routing); médiane 31 mots ajoutés, 81.1% en <= 2 phrases. Autres systèmes 64.9-73.2% (OpenSourceJev Qwen3-1.7B 72.6%, Von 1.0 395M non-AR 73.2%, Qwen scorer 64.9%). OBSERVED (attaque boîte noire avec accès aux scores; PDF non lu en entier, résumé HTML). Pertinence: state poisoning naturel = risque majeur.
- **Decision Hijacking** arXiv 2609.28613 (Wu & Lim, 23 sept 2026): 510 cas InjecAgent reconstruits; l'injection déplace les probas d'action mais choisit rarement la cible attaquante; attaque adaptative avec retour de score: succès de 1.8% à 3.5%; marges de décision étroites et contrôle de l'observation aggravent. OBSERVED.
- **JevAdvBench** arXiv 2609.31142 (Hu et al., 25 sept 2026): 812 questions, 66 scénarios, 9 744 variantes, 9 attaques simples sans adaptation, seulement jev-1.13.0. Opinion d'observateur ajoutée au state: 12.1% de flips [8.5-15.5]; usurpation d'autorité 10.1%; override direct 8.9%; paraphrase 1.5% (dans le bruit); 38.0% des réponses confiantes tombent sous 0.8 (donc vers revue humaine). Score: 38.5% de réponses différentes sur appels identiques. Limites: 82.4% de labels dérivés du modèle. OBSERVED.
- willkelly: injection d'"autorité" 147/200 (voir 2.2). Ordre des options: négligeable (jujumilk3). Option manipulation via rubrique oui/non (xbill): 32.5%.
- Doc TypeSafe reconnaît que du contenu adversarial peut déplacer la réponse. DOCUMENTED_CLAIM.
- Non trouvé de test tiers spécifique à: contamination du "state" par données de marché falsifiées, ordre des questions batchées hostile (jujumilk3 a testé 16 questions: 0.4%). Mixte.

Lecture INFERENCE: les chiffres divergent selon l'attaque (naïve ~9-12%, adaptative/autoritaire/naturelle 60%+). Type-safe n'implique pas résistant à l'injection. Toute donnée non fiable dans le state (news, texte de filings) doit être considérée comme vecteur de manipulation; ne jamais acheminer texte tiers non filtré + seuils de confiance comme seule barrière.

Papers génériques (NON Jev, à séparer):
- LLM-as-judge: Survey arXiv 2411.15594 (biais de position, métriques Position Consistency); 2506.22316 Scoring bias; 2505.13348 prompt injection sur judges; 2512.17375 AdvJudge-Zero (flips binaires via tokens de contrôle adverses); 2609.15013 Overflip (flips de label par répétition sur modèles de garde-fou). Conclusion des résumés: les judges ne sont pas robustes aux interférences non liées à la qualité. Pertinence: mêmes modes de défaillance plausibles sur décideur typé (INFERENCE).

## 4. Papers pertinents

| arXiv / URL | Date | Résultat clé | Pertinence |
|---|---|---|---|
| 2305.14975 Tian et al., "Just Ask for Calibration" (openreview g3faCfrwm7) | 2023 | Pour LLM RLHF, confiance verbalisée mieux calibrée que probas conditionnelles tokens (ECE réduit ~50% relatif sur TriviaQA/SciQ/TruthfulQA) | Jev sort des probas natives (non verbalisées); comparaison verbal vs logits pour nos LLM baselines |
| 2410.06707 Calibrating Verbalized Probabilities for LLMs | 2024 | Recalibration post-hoc de probas verbalisées | Baseline de recalibration |
| 2606.03437 LLMs Are Overconfident in Their Own Responses | juin 2026 | Surconfiance des LLM (résumé de recherche seulement, non lu en détail) | Contexte |
| 2512.11998 Direct Confidence Alignment | déc 2025 | Aligne confiance verbalisée et interne (résumé seulement) | Contexte |
| 2512.23847 Gao, Jiang, Yan, "Detecting Lookahead Bias in LLM Forecasts" (rév. 12 juin 2026) | déc 2025 | Métrique Lookahead Propensity; pouvoir prédictif amplifié sur paires firme-date à LAP élevé pendant la période d'entraînement, pas significatif après le cutoff | Critique pour PIT: tester Jev par requête de rappel de date |
| 2609.20554 Chen et al., "Does Training on Future Data Pay?" | 17 sept 2026 | Entraîner sur des données post-origine dégrade la précision: erreurs plus hautes dans 18/20 combinaisons US; CER -1.77 pt (US), -2.14 pt (international) | Contamination temporelle, effet mesuré |
| 2601.13770 Look-Ahead-Bench (Benhenda) | 20 janv 2026 | LLM standard: lookahead bias significatif (alpha decay) vs modèles Point-in-Time (Pitinf) | Benchmark PIT |
| 2603.11838 DatedGPT; 2510.11677 Instruction tuning chronologically consistent LMs; 2607.11889 Scaling PIT LMs; 2607.18867 HindsightBench; 2602.14233 Evaluating LLMs in Finance Requires Explicit Bias Consideration | 2026 | Modèles à cutoff contrôlé et audits boîte noire de hindsight; DatedGPT: prime de 26.4 bp par écart-type pour setups avec lookahead (résumé de recherche) | Pas lus en détail; pistes pour un audit PIT de Jev |
| 2609.28940 Calibrated Decision Models for Pentest Harnesses | 24 sept 2026 | Voir 2.2; conceptuel | Cadre décisionnel, faible preuve |
| Laya, Nimble-9B, Von 1.0, OpenSourceJev, DiffusionGemma | 2026 | Alternatives ouvertes ("non-AR classifiers"); Nimble-9B (base Qwen3.5) derrière Jev sur 11/13 sous-ensembles publics (source Bespoke Labs, conflit d'intérêt); Laya ECE 0.081 post-température (autre tâche) | Papers non lus individuellement; à sourcer avant usage. Aucun paper spécifique "non-autoregressive parallel decoding classifieurs" lu en détail. |

## 5. Lookahead / PIT pour Jev
- Base model, cutoff, corpus: UNKNOWN. Entraînement "synthétique" (DOCUMENTED_CLAIM CEO) n'exclut pas de la connaissance du monde héritée d'une base pré-entraînée. Aucun test de lookahead sur Jev trouvé.
- Test proposé (INFERENCE): protocole LAP (2512.23847) et HindsightBench avant tout backtest; comparer l'accuracy avant/après un cutoff supposé; utiliser des états anonymisés (noms/dates masqués).

## 6. UNKNOWN restants
Taille/archi/base/cutoff; details RLCD; données; ECE/Brier/NLL/reliability vendeur; latence garantie; max questions officiel; version stable (un seul modèle 1.13, alias preview=latest, changements possibles sans préavis: risque de dérive silencieuse); réplication des chiffres 40-200x (mesure tierce: 1.04x à 18x selon source, un cas 0.5-0.65x vs Gemma local, source dev.to/xbill); performance sur tâches financières/PIT.

## Sources principales
docs.typesafe.ai (introduction, api, models, confidence, machine-learning-primer, model-jaggedness/jev-1.13, llms.txt); arxiv.org/abs/2609.30243, 2609.28613, 2609.31142, 2609.33401, 2609.28940, 2512.23847, 2609.20554, 2601.13770; github.com/scienthoon/jev-ood-calibration; github.com/willkelly/jev-evaluation; github.com/jujumilk3/jev-calibration-audit; github.com/jmanhype/jev-dspy-lab; dev.to/gde/jev-after-eight-days-of-independent-tests-...; layer3labs.io/guides/jev-benchmarks; github.com/GautamTalksDev/awesome-jev-robustness (agrégateur).
