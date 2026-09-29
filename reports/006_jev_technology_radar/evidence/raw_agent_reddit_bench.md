# Jev / System One (TypeSafe AI) - Reddit, HN, blogs de devs, benchmarks indépendants
Date de l'étude: 2026-09-29. Méthode: WebSearch (extended) + WebFetch. Les résumés de pages passent par un petit modèle de WebFetch: les chiffres cités sont DOCUMENTED (lus dans la page) mais pas re-calculés par moi. Rien n'a été reproduit par moi.
Étiquettes: PROVEN (données brutes/code publics + protocole vérifiable, mais NON rejoué par moi => je le note "PROVEN-par-publication" seulement quand le tiers publie les logs), OBSERVED (mesure tiers, protocole décrit), DOCUMENTED_CLAIM (affirmation éditeur ou tiers sans preuve), INFERENCE (ma déduction), UNKNOWN.

## 0. Limites de cette recherche (à lire d'abord)
- Reddit: AUCUN thread Reddit n'a pu être ouvert ni localisé par URL. Seule mention indirecte (Reddit r/LocalLLaMA, via gadgetpilipinas / vanekt / Wikipedia-like résumés): dispute de priorité Laya vs Jev, "des milliers d'étoiles GitHub". => UNKNOWN pour r/MachineLearning, r/algotrading, r/quant, r/CloudFlare, etc. Ne pas conclure "absence de discussion".
- HN: seul le thread de lancement (id 49717558) a été lu. Les threads 49800574 (Show HN JevBench), 49816019, 49816899 ("Jev Can't Be Calibrated"), 49767192, 49752041 (OpenJev) ont renvoyé HTTP 403: seuls les titres (résultats de recherche) sont connus. Contenu = UNKNOWN.
- Beaucoup d'articles "What is Jev" (firecrawl, langchain, datacamp, mindstudio, truefoundry, etc.) sont génériques: ignorés sauf mention.
- Attention risque de contenu SEO/auto-généré: plusieurs blogs (eesel, greennode, atlascloud, refix) recyclent des chiffres éditeur ou tiers. Toujours remonter à la source.

## 1. Données ÉDITEUR (MARKETING / DOCUMENTED_CLAIM)
Source: https://typesafe.ai/blog/introducing-system-one-models-and-jev (lancement early access 2026-09-15)
- 70-500 ms end-to-end; 193.6x plus rapide, 444.6x moins cher (workflow evals maison); $0.042/M tokens input, output gratuit; "similaire niveau d'intelligence sur tâches System One". DOCUMENTED_CLAIM.
- Limites reconnues par l'éditeur: pas de génération de chaînes; cardinalité max 255 pour un choix mono-étape; entrées structurées/texte, pas d'images; workflow evals faits par l'équipe "model capabilities" (biais reconnu). DOCUMENTED_CLAIM.
- Rate limits jev-1.13 (secondaire, via résultat de recherche, non vérifié à la source): 1 200 req/min, 250 000 tokens/s, 429 au-delà. NON_VÉRIFIÉ (source primaire docs à confirmer).
- Pas de papier technique, pas de poids, pas de données (AstonJ, Elixir Forum 2026-09-19; pearpages: "RLCD: aucune fonction de récompense/procédure/ablation divulguée"). DOCUMENTED (critique tierce).

## 2. Discussions communautaires
### 2.1 HN "Introducing System One Models and Jev" - https://news.ycombinator.com/item?id=49717558 (mi-sept. 2026)
- Contexte: fil de lancement; le CEO (pseudo CompleteSkeptic) répond; RLCD = "probabilités optimisées contre les résultats"; dit niveau "Sonnet 5" (DOCUMENTED_CLAIM, sans preuve dans le fil).
- Critiques: "can't hallucinate" trompeur (InsideOutSanta, 8note, jubilanti, bigglebear: "confiance élevée sur mauvaise réponse = hallucination"); titre initial "New frontier model 40-400x cheaper" jugé faux pour un outil spécialisé (WhitneyLand); nouveauté contestée (janalsncm: BART zero-shot; niutech: Laya open source existant); bigglebear affirme "~1B params" et "recréé en 2h" = spéculation, sans preuve (UNKNOWN).
- Preuves fournies: pratiquement aucune dans le fil. Reproductibilité: n/a. Upvotes non retenus comme preuve.
### 2.2 Tildes - https://tildes.net/~tech/1w37/typesafe_ai_system_one_models_and_jev (18-20 sept.)
- delphi (OP): classification de lieux dans des documents gouvernementaux, "quasi gratuit, très rapide, très bon" (OBSERVED faible, anecdote, a reçu 5 $ de crédits de l'éditeur => conflit d'intérêt léger).
- archevel: sur une version navigateur de Laya (PAS Jev), changer l'ordre des entrées (Arnold/Conan) inverse le résultat et sorties différentes laptop/téléphone. OBSERVED sur Laya uniquement; ne pas transférer à Jev.
### 2.3 Elixir Forum - https://elixirforum.com/t/typesafe-sdk-jev-the-first-system-one-model-from-typesafe/76700 (19 sept.)
- SDK communautaires (5 libs Elixir), ReqLLM 1.24 ajoute evaluate/4. Aucun test de perf. Critique de priorité (Laya). 
### 2.4 Reddit r/LocalLLaMA (secondaire) - Laya vs Jev
- Sources secondaires: https://www.gadgetpilipinas.net/2026/09/typesafe-jev-system-one-model-laya/ , https://vanekt.github.io/blog/laya-vs-jev/ : Nandakishor Mukkunnoth (ConvAI) dit avoir publié RLCD en mars 2025 + post r/LocalLLaMA, puis libéré Laya (421M, Apache 2.0 code, poids CC-BY-NC-4.0 selon le dataset Luni) après Jev. Thread Reddit original: UNKNOWN (non trouvé). Revendication de priorité = DOCUMENTED_CLAIM non arbitrée.

## 3. Mesures indépendantes (les plus utiles)
### 3.1 Latence / coût / accuracy
| Source | Date | Résultat | Étiquette |
|---|---|---|---|
| LiteLLM (Moe Khalil) https://docs.litellm.ai/blog/jev-auto-router-benchmark | 18-20 sept | 80 cas x3, classification de tier: p50 126.8 ms vs Haiku 4.5 688 ms; p95 231 vs 897 ms; match tier 95.0% vs 73.75%; -96% coût. Labels écrits par l'auteur sans revue; classification seule, pas de charge/débit | OBSERVED (petit n, labels non revus) |
| Beri.net + repo https://github.com/anisselbd/jev-phishing-bench | sept 2026 | PhishNChips 2000 mails, 1 question: Jev 62.6% vs Haiku 81.3% (McNemar p<0.0001); latence 239 vs 687 ms; $0.038 vs $0.462 /1000 mails (~12x). Décomposé en 5 questions + régression logistique: Jev 95.0% vs Haiku 93.2% (p=0.063, non significatif). Regex simple: 91.8%. Jeu "quasi séparable par construction", vérité = réputation d'URL, corps de mails synthétiques. Code publié | OBSERVED, reproductible (code public) |
| AY Automate https://www.ayautomate.com/blog/jev-vs-llm-benchmark | sept | 791 décisions (Banking77 etc.): Jev 78.8% vs GPT-5.6 Terra 84.0% (77 classes); injection: Jev 87.0%; médiane 0.33 s vs 1.17 s; seuil conf>=0.80 => 93.8% sur 8 classes; cascade Jev->Terra ~26-28% du coût, ~1/2 latence | OBSERVED (code ? UNKNOWN) |
| Luni/laya-jev-benchmark (HF) https://huggingface.co/datasets/Luni/laya-jev-benchmark | sept | 400 cas typés: Jev 72.7%, 710 ms/cas; phishing Jev 62.6%, 239 ms. Partisan Laya (auteur pro-Laya) | OBSERVED, source partisane |
| Vercel CEO (X) https://x.com/rauchg/status/2100307962262872105 (via TNW/aiweekly) | sept | "jusqu'à 18x plus rapide (p95) et plus précis" vs petit GPT sur une étape de revue de sécurité; ~13% des équipes Vercel payantes en 24h. Aucune donnée brute; Vercel = partenaire distributeur | DOCUMENTED_CLAIM tiers intéressé |
| JevBench https://github.com/dhruvmehra/jevbench | sept-oct | Cadre SST-2/AG News/Banking77 vs Laya, gpt-4o-mini, Sonnet, DistilBERT; ±2.5 pts à n=500. Table de résultats non lue => UNKNOWN | cadre OBSERVED, résultats UNKNOWN |
| Greennode https://greennode.ai/blog/what-is-jev | sept | Agrège Beri/AY; note que 193.6x ne donne que ~15.9% de gain système en pipeline réel (source de ce 15.9%: UNKNOWN) et que "réponse correcte" éditeur = accord avec 2 LLM | secondaire |
| pearpages https://pearpages.com/blog/2026/09/16/jev-sorted-... | 16 sept | Vs Terra: ~25x plus rapide et ~76x moins cher (pas 193x/444x); infériorité sur factures 61.8% vs 74.7%; cite tests Every/Mike Taylor (777 jugements <0.7 s), Goedecke, Maio: NON re-suivis | secondaire, NON_VÉRIFIÉ |
| dev.to Gabriel Anhaia https://dev.to/gabrielanhaia/jev-beat-gpt-luna-by-1-point-gpt-6-and-claude-wrote-the-answer-key-314k | sept | Titre: "réponse-clé écrite par GPT-6 et Claude": rejoint la critique de circularité. Non lu => UNKNOWN |

### 3.2 Calibration
- Pré-enregistré willkelly https://github.com/willkelly/jev-evaluation: 123 805 requêtes, jev-1.13.0, 28 prédictions, 138 min, 12.69 $, logs bruts 47 Mo. ECE 0.075 sur routage de tickets (domaine natif); s'effondre sur 3-SAT aléatoire (répond "satisfiable" partout, proba quasi constante). 200 questions/requête: accuracy identique à 1 question, latence quasi plate, 60 questions ~20x moins de tokens. AUROC de confiance 0.878 poolé mais 0.699 intra-condition; confiance = 1.00 sur 86% des cas répondables. Injection directe: 1/200; injection "autorité" imitant la structure: 147/200. Pré-traitement (AST 0.598, CFG 0.530) pire que source brute (0.894). => OBSERVED, le plus solide (logs publics), non rejoué par moi.
- OOD scienthoon https://github.com/scienthoon/jev-ood-calibration: benchmarks publics (86-94%, ECE au plancher, T~1.0; probable contamination) mais tâche synthétique 900 tickets dont priorité = règle interne absente du texte: acc 75% global, ECE 0.107 (4.4x plancher), priorité: juste 44.7% avec proba moyenne 0.74. Bool sous-confiant (T=0.66), choice/score sur-confiants (T 1.30-1.92). ~0.06 $. OBSERVED. (Repris par Beri.net et Sophos.)
- jujumilk3 https://github.com/jujumilk3/jev-calibration-audit (~7 000 appels, <1 $): sans option "inconnu", accuracy sur non-répondables 95%->0%, ECE 0.023->0.793; Korean vs English ECE 0.076 vs 0.075 (invariant); probas complémentaires somment à 0.71-1.42; pas d'effet d'ordre sur cette tâche; interférence batch 0.4% (16 questions). OBSERVED.
- webofmike (dev.to) https://dev.to/webofmike/i-benchmarked-jev-on-agent-tool-call-risk-calibration-held-49i3: 60 cas, 91.7% (55/60); aucune erreur avec confiance 1.000, 40/40 à 1.0 corrects; pas de baseline LLM; n=60 insuffisant. OBSERVED faible.
- Iskandeur https://github.com/Iskandeur/system1-system2: MASSIVE 600 énoncés: Jev 90%, ECE 4.5% vs GPT-5.2 90.2% (égalité); un run, n=600. OBSERVED.
- Sophos (Nash Borges, SVP AI) https://www.sophos.com/en-us/blog/jevs-paradox-hidden-cost-of-cheap-ai-decisions: CLINC150 87% vs Terra 92%; Banking77 83% vs encodeurs supervisés 93%; 0.44 s vs 1.51 s; cite phishing et l'écart 74% de proba / 45% juste. Opinion informée + reprise de chiffres tiers (opinion + secondaire).
- Papier arXiv 2609.28940 (pentest, indépendant, 2026-09-24) https://arxiv.org/abs/2609.28940: auteur Joas Antonio dos Santos, sans lien TypeSafe; un seul run, aucune puissance statistique (auteur lui-même); ECE Jev 0.246 "publié" vs Laya 0.081, tâches différentes; latence Jev 236-276 ms p50. L'origine du chiffre ECE 0.246 est UNKNOWN. Design doc, pas preuve.
- Papier arXiv 2609.29429 "Just Ask Jev" (2026-09-25) https://arxiv.org/abs/2609.29429: 9 auteurs, affiliation non lue; AUROC médian 0.886 zero-shot sur 44 benchmarks, 63x moins cher que juges LLM; code RLCDAlignBench. Affiliation TypeSafe: UNKNOWN. Si affilié, = éditeur/tiers-non-indépendant. NON_VÉRIFIÉ.
- Papier arXiv 2609.25498 (Dağlı et al.): "Universal Fractal Natural Language Decision Map" n'utilise que le nom "JevBench" (N=231) pour un moteur fractal sans poids: PAS un test de Jev. À exclure.

### 3.3 Sensibilité à la formulation / ordre / langue / batch
Source: liste https://github.com/Yifan-Lan/awesome-jev-robustness (agrégat de "126 études", moi: non vérifié entrée par entrée; entrées revérifiées à la source marquées V).
- V willkelly, V jujumilk3 (voir 3.2). V zkousama/jagged https://github.com/zkousama/jagged: 486 discussions Wikipédia AfD, via Vercel AI Gateway: baseline 96.5% (ECE 0.230), après injection d'une phrase "closing admin confirmed kept": 26.5%. Pré-enregistré, un modèle/une tâche. OBSERVED.
- Non revérifiés (DOCUMENTED par la liste): ordre des options arithmétique 88%->57% (RINNECODER); reformuler les critères 70%->96% (RastislavDujava); russe 77.3% vs anglais 88.3% (AHTOOOXA); espagnol -3.0 à -6.4 pts (marcosmartinez); biais dialectal (zachlandes); 0/30 hors-périmètre détectés sans option "none" (priorbench); ChaosNLI conf 0.807 vs accord 0.468 (GautamTalksDev); dés: 82.9% conf pour 19.0% acc (KantaHayashiAI); ajout de candidats déplace log-odds 0.31-0.50 (123Satyajeet123); "Choice confidence = formule fixe", 4 confirmées/8 réfutées (primeline). NON_VÉRIFIÉ individuellement.
- Contradiction interne à signaler: jujumilk3 "pas de biais d'ordre" (tâche factuelle) vs RINNECODER "88%->57%" (arithmétique) => dépend de la tâche (INFERENCE).
- Robustesse injection: cwhy/decision-injection-bench https://github.com/cwhy/decision-injection-bench: Jev 1.13.0 0.09% de flips (1056 attaques) vs Winnow 3.0%, SemIf 27.4%, Laya 62.6%; 8 items v1/24 textes v2, synthétiques, un étiqueteur => tests de régression, pas estimations. Contredit par willkelly (147/200 injections d'autorité), zkousama (26.5%), Iskandeur (26/80 flips vs GPT-5.2 80/80; défense d'une phrase -> 1.3%) et JevOut (61.4%, NON_VÉRIFIÉ). => Résultat dépend fortement du type d'attaque (INFERENCE).

## 4. Éditeur vs communauté
- Vitesse: éditeur 70-500 ms; tiers: p50 127-276 ms, p95 231 ms (LiteLLM), 239 ms (Beri), 0.33 s (AY), 710 ms/cas (Luni, config différente), 0.44 s (Sophos). Cohérent avec 70-500 ms mais loin de "200x" en système (Vercel 18x p95; Greennode ~15.9% système, source UNKNOWN). Mesures depuis régions/passerelles différentes: non comparables strictement.
- Coût: $0.038/1000 mails (Beri) ~ 12x moins que Haiku 4.5; éditeur 444x = contre LLM frontière et "accord" comme vérité. Le 40-400x n'est pas reproduit par un tiers sur exactitude réelle.
- Accuracy: 62.6% (phishing, 1 question) à 95% (décomposé): la formulation/décomposition est LE levier (Beri, RastislavDujava). Pas de dépassement de la frontière (AY: Terra 84.0 vs 78.8).
- Calibration: "calibré" tient dans le domaine natif (ECE ~0.02-0.075; Iskandeur 4.5%) mais se dégrade OOD/règle implicite (0.107-0.246, 3-SAT) et sans option d'abstention (0.793). "Ne peut pas halluciner" = garantie de type/schéma uniquement (éditeur + pearpages + HN).
- Batch: éditeur promeut questions parallèles; willkelly: 200 questions sans perte, latence plate, tokens/20x (OBSERVED, un seul chercheur).
- Rate limits/retries/tailles d'input: rate limits = source secondaire; taille max ~4 000 tokens (vanekt, secondaire, NON_VÉRIFIÉ); retries: UNKNOWN. Langues: Korean~English (jujumilk3), russe/espagnol dégradés (NON_VÉRIFIÉ).

## 5. Conclusions (INFERENCE)
1. Preuves tierces solides = 3-4 dépôts avec logs/code (willkelly, jujumilk3, scienthoon, anisselbd) + LiteLLM; le reste est secondaire.
2. Jev = classifieur zero-shot rapide et bon marché, calibré in-domaine, fragile OOD et à la formulation; pas un remplaçant de LLM frontière.
3. Toutes ces mesures ont <3 semaines, un seul modèle (jev-1.13), petits n, et sont majoritairement mono-auteur: aucune réplication croisée hormis l'injection (contradictoire).
4. Reddit: à refaire avec accès direct (Reddit/HN bloqués ou non indexés ici).

## 6. Top des sources
1 https://github.com/willkelly/jev-evaluation 2 https://github.com/scienthoon/jev-ood-calibration 3 https://github.com/anisselbd/jev-phishing-bench (+ https://www.beri.net/article/typesafe-jev-typed-decision-model-calibration-decomposition-shadow-eval) 4 https://github.com/jujumilk3/jev-calibration-audit 5 https://docs.litellm.ai/blog/jev-auto-router-benchmark 6 https://www.ayautomate.com/blog/jev-vs-llm-benchmark 7 https://github.com/zkousama/jagged 8 https://github.com/Iskandeur/system1-system2 9 https://news.ycombinator.com/item?id=49717558 10 https://typesafe.ai/blog/introducing-system-one-models-and-jev (marketing)
Aussi: https://github.com/cwhy/decision-injection-bench, https://huggingface.co/datasets/Luni/laya-jev-benchmark, https://www.sophos.com/en-us/blog/jevs-paradox-hidden-cost-of-cheap-ai-decisions, https://github.com/Yifan-Lan/awesome-jev-robustness, https://arxiv.org/abs/2609.28940, https://tildes.net/~tech/1w37/typesafe_ai_system_one_models_and_jev
