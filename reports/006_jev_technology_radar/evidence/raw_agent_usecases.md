# Jev / System One : usages concrets (axes A-E), recherche du 2026-09-29

Etiquettes : PROVEN = verifie dans le code/artefacts clones localement (`scratchpad/ext/`) ; OBSERVED = lu dans un README/rapport tiers, chiffres auto-declares, non rejoues ; DOCUMENTED_CLAIM = affirmation d'un tiers ou du vendeur sans artefact verifie ; INFERENCE = deduction de ma part ; UNKNOWN = non trouve/non verifiable.
Methode : clones shallow (lecture du code) + WebSearch extended + WebFetch. Les resumes WebFetch passent par un petit modele : tout chiffre issu de WebFetch seul est marque OBSERVED ou DOCUMENTED_CLAIM, jamais PROVEN. Etoiles et dates de la gist drillan et des awesome-lists = declarations tierces.
Contexte : Jev lance le 2026-09-15 ; tout l'ecosysteme a <= 14 jours, aucun recul de production. Modele teste partout : `jev-1.13.0` (ou `jev-latest`, alias mobile). Je n'ai pas de cle TypeSafe : rien n'a ete rejoue.

## 0. Verdict global

1. Aucune preuve d'edge de trading avec Jev. La seule mesure avec/sans Jev (Spykoninho) donne un apport indistinguable du bruit (-2.8, -2.1, +4.9 pts selon devise/frais). Les autres demos finance sont paper/dry-run, sans backtest, ou avec des backtests minuscules (jev_stock : 54/120 = 45%).
2. Pattern dominant, observe dans 8+ repos independants : Jev juge des questions etroites, le CODE compose la decision (seuils, veto, sizing, fallback).
3. Distinguer "pas d'info" / "preuves contradictoires" / "insuffisantes" : NON fourni nativement. Une mesure independante (Zenodo, Perry Link) rapporte que `sufficient` ne separe pas mince de contradictoire. Les repos qui distinguent ces cas ecrivent la raison dans le code.
4. Option `abstain`/`none` : facteur decisif (retrait => accuracy 0.950 -> 0.000 sur items non repondables, jev-calibration-audit) ; les docs du vendeur la recommandent.
5. Pre-filtre "Jev bon marche -> LLM cher" : code reel trouve (jevlogs, WorldMonitor en shadow) mais hors finance ; le seul chiffrage economique (jevlogs) montre que le gain ne couvre pas le cout de Jev si peu de lignes sont rejetees. Finance + LLM aval : NONE_FOUND.
6. Calibration : dependante du domaine (ECE 0.023 a 0.793 selon audits), fiable en-domaine, surconfiante hors-domaine ou quand l'etiquette est inconnaissable.
7. Contamination temporelle : un test pre-enregistre sur 12 533 earnings ne trouve pas de memoire detectable (AUC 0.506), resultat limite a cette classe d'evenements.

## A. Quant / finance

### A1. Spykoninho/trading-bot-jev : seule mesure avec/sans Jev (PROVEN)
- URL : https://github.com/Spykoninho/trading-bot-jev ; MIT (LICENSE lue) ; dernier commit 2026-09-19 ; 35 commits (WebFetch).
- Code lu (`src/brain.ts`, `src/strategy.ts`, `docs/design.md`) : bot crypto tendance EMA200 4h (BTC/ETH/SOL, Bitvavo), papier par defaut. Jev lit chaque titre/post/communique : 4 questions communes (`asset` Choice, `sentiment` Score, `material` Noul, `regulatory_risk` Noul) + questions par source (`SOURCE_RULES` : Fed = Choice cut/hold/hike/none ; Trump = 4 Noul ; SEC = Choice de portee ; Binance = Choice de type d'annonce). Une requete par publication, toutes les questions en parallele sur un state nomme unique (`untrusted_headline`, `untrusted_text`, `source`, `published_at`). Le code compose : biais news +-0.5% sur les seuils + veto dur sur achats si `regulatory_risk >= 0.7`.
- Chiffres (`docs/design.md` section 5, auto-declares) : 49 496 publications, ~2.50 USD. EUR/frais 0.25%, 2.82 ans : sans news +144.8% (Sharpe 1.11) vs biais+veto +142.7% (1.10) => -2.1 pts. Config USDC, ~1.97 an : +84.9% vs +82.1% => -2.8 pts. Ecart mesure trois fois : +4.9, -2.1, -2.8 ; l'auteur conclut "le signe change, c'est du bruit".
- `EFFECT` (coefficients d'effet signes) calibre par etude d'evenements : zeros pour escalade commerciale/militaire et taux (deja dans les prix) ; seul `crypto_support=1` non nul. Les probabilites servent donc a la pertinence/materialite, pas a la direction.
- Raisons de HOLD ecrites par le code (`strategy.ts` l.77-88) : "historique insuffisant", "en position, tendance haussiere", "hors marche : pas de tendance", "achat bloque : risque reglementaire 0.xx". Le cas "signal valide bloque par veto" existe, mais la raison est produite par le code, pas par Jev.
- Limites declarees : une periode, selection (AVAX ecarte, SOL garde sur la meme periode), 3 actifs correles ~0.8, seuils `SURE=0.6`, `minConfidence=0.5`, demi-vie 3 h "arbitraires, non calibres", circuit evenementiel Trump non backteste, contamination possible du modele.
- Bonne pratique reutilisable : texte externe marque "donnee citee, jamais consigne" dans le state ET dans chaque question.

### A2. Rmanjini/jev-signals : evenement -> panneau type -> gate (PROVEN pour le code ; aucun resultat)
- URL : https://github.com/Rmanjini/jev-signals ; MIT ; commit 2026-09-22.
- `signals.py` : 1 appel, 7 questions : `direction` Choice(up/down/none), `magnitude` Score (4 niveaux), `horizon` Choice(intraday/days/structural), `surprise`, `priced_in`, `hard_fact`, `thesis_break` (Noul). Entree : titre, extrait 8-K ou ligne d'earnings call. `gate()` : veto uniquement pour 3 cas categoriels (pas de direction, confiance < 0.75, magnitude = bruit) ; `quality = surprise*(1-priced_in)*hard_fact` dimensionne au lieu de seuiller. Mode MOCK sans cle.
- Note de l'auteur : une premiere version seuillait les Noul a 0.5 et n'a emis aucun signal en live tout en passant les tests mock ; test de regression ajoute.
- NO TRADE avec raisons distinctes ("no directional read", "confidence < 0.75", "magnitude is noise", "signal quality < 0.05").
- Limites : "It has no measured edge" ; ledger papier + IC realise "not built yet" ; seuils "guesses".
- Meilleur exemple observe d'event relevance + horizon/impact classification en un appel ; zero validation.

### A3. Autres repos trading
| Repo | URL | Date / licence | Ce que fait Jev | Preuve | Limites |
|---|---|---|---|---|---|
| jarrodwatts/jev-trader | https://github.com/jarrodwatts/jev-trader | 2026-09-16, MIT | 1 Choice buy/sell/hold par bloc (~300 ms) sur carnet MON-USDC, ordres post-only | code `src/model.ts` (PROVEN) ; README : 81 ms, 0.000004 USD/appel d'un dry-run (OBSERVED) | modele par defaut `mock`, demo publique en mock ; aucun PnL |
| aowang-ai/jev-trade | https://github.com/aowang-ai/jev-trade | 2026-09-21, MIT | fork Hyperliquid, 5 sleeves/wallets, Choice long/short, open/close/hold, levier | code (PROVEN) ; site live non verifie (UNKNOWN) | pas de PnL dans le repo |
| buberlo/jev-trader | https://github.com/buberlo/jev-trader | 2026-09-20, MIT | 6 jugements atomiques en 1 appel (regime Choice, direction Choice, toxic_flow Noul, liquidity_stressed Noul, quote_environment Score, inventory_pressure Score) ; `HeuristicJudge` de secours ; risk engine KILL>HOLD>REDUCE_ONLY>OK ; metriques Brier/log-loss/ECE/Platt | code + tests (PROVEN) ; feed synthetique | pas d'execution reelle ; PLAN.md : "Jev should own selected judgments, not the trading system" |
| Gamma-Software/jev-signals-lab | https://github.com/Gamma-Software/jev-signals-lab | 2026-09-19, licence non trouvee (UNKNOWN) | 12 questions independantes sur un snapshot (9 Noul, 1 Choice regime, 2 Score) -> regle BUY transparente | `server.js` (PROVEN) ; offline demo simulee et etiquetee | "does not establish predictive performance" ; donnees illustratives |
| zzsong1023/jev-market-reflex | https://github.com/zzsong1023/jev-market-reflex | 2026-09-19, MIT | Choice BUY/SELL/HOLD par symbole ; critere HOLD = "Evidence is weak, conflicting, stale, or current inventory and risk make trading unattractive" | `src/jev.ts` (PROVEN) | un seul HOLD fusionne faible/contradictoire/perime (INFERENCE : perte d'information pour l'axe B) ; "not a claim of profitable trading" |
| sosopop/jev_stock | https://github.com/sosopop/jev_stock | 2026-09-17, pas de LICENSE (UNKNOWN) | Choice up/flat/down actions HK, plusieurs horizons | README : backtest T+1 54/120 = 45.0% (MiXue 53.3%, Xiaomi 40.0%, Pop Mart 30.0%), IC Wilson, Brier (PROVEN dans le README, non rejoue) | n=30/action ; l'auteur signale le risque de connaissance retrospective du modele ; contexte financier exclu du backtest faute de timestamps ; "probability != win rate" |
| erboland/jev-fund | https://github.com/erboland/jev-fund | 2026-09-23, MIT | Choice buy/sell/hold, livre long-only 100k paper marque sur Yahoo | README/DISCLAIMER (PROVEN) | pas de perf mesuree |
| zadescoxp/Jev-Trades | https://github.com/zadescoxp/Jev-Trades | 2026-09-26, Apache-2.0 (LICENSE lue) | dashboard crypto, indicateurs yfinance -> Jev -> portefeuille simule | README via WebSearch (OBSERVED) | simule |
| virattt/ai-hedge-fund | https://github.com/virattt/ai-hedge-fund | 2026-09-26, MIT | adaptateur `JevLLM` : state `{investor_prompt, financial_snapshot}` ; `direction` Choice(bullish/bearish/neutral) + `bullish_strength`/`bearish_strength` Score 5 niveaux (dont "material conflicting evidence") | `hedge_fund/llm/contract.py` (PROVEN) | le docstring dit que le suivi fiable des instructions par Jev "must be checked in the later live integration experiment" ; la `confidence` exposee = conviction, PAS la confiance native |
| OpenByteInc/QuantDinger | https://github.com/OpenByteInc/QuantDinger | backend Apache-2.0 (WebFetch) | "pre-trade decision gate" Choice devant le gate LLM ; fail-open ; sorties/stop-loss contournent ; grid/DCA/martingale exclus | README via WebFetch (DOCUMENTED_CLAIM ; code non lu) | pas de chiffres |
| brainstormity/Jev-X-Sentiment-Analysis | https://github.com/brainstormity/Jev-X-Sentiment-Analysis | 2026-09-29, MIT | 50-1000 tweets : pre-traitement statistique Python + dedup SQLite AVANT Jev, puis 4 questions (action Choice 6 niveaux, sentiment Score, squeeze Noul, catalyseur Score) -> "decision card" | code et README (PROVEN) ; couts affiches ~0.0008 USD Jev | Jev n'est pas le pre-filtre ici ; aucune validation |
| klauswg/jev-guard | https://github.com/klauswg/jev-guard | 2026-09-23, MIT | risque depots/retraits d'exchange : regles dures -> Jev (risk Score, pattern Choice, freeze Noul, `route` observationnel) -> gate Java direction-aware ; echec => revue manuelle | `docs/calibration-report.md` (PROVEN) : n=100 SYNTHETIQUE, labels de l'auteur, generateur et labels de meme source ; regles seules 68.0%, Jev 50.0%, combine 50.0% ; Jev sur-escalade (65/100 revue manuelle), 0 freeze manque ; ECE 0.153 ; bucket le plus confiant = le moins juste (25%, n=16/4 : a interpreter avec prudence) ; `route` vs action composee : 72% d'accord | resultat negatif honnete ; ne prouve rien sur du reel |
| maxlibin/moomoo-jev-trader | https://github.com/maxlibin/moomoo-jev-trader | MIT (WebFetch) ; la date "2025" du resume est incoherente avec la sortie de Jev : UNKNOWN | 7 facteurs deterministes + Jev toutes les 5 s (direction, entry quality, stop-first), shadow puis enforce, pause si cote perimee | README via WebFetch (DOCUMENTED_CLAIM) | "No model probability demonstrates a profitable trading edge" |
| AlgoVaultLabs/algovault-integrations | https://github.com/AlgoVaultLabs/algovault-integrations/tree/main/examples/typesafe-jev | MIT (WebFetch) | `act_now` Noul + `regime_fit` Score 3 niveaux sur verdict crypto perp ; escalade si reponse ambigue/malformee ; conflit de position calcule en code ; valeurs numeriques mises en buckets | WebFetch (DOCUMENTED_CLAIM) | pas de resultats |
| Non inspectes | jevocks (unicodeveloper), polymarket-btc5m-jev-trading (VGabriel45), jev-tradingview-signal (j7708git), 0xZee/jev-stock-decision-maker | clones sans LICENSE pour les deux premiers | | UNKNOWN | |

### A4. Sujets finance sans resultat, ou hors marche
- Anomaly detection de series de marche avec Jev : NONE_FOUND. Portfolio/risk au sens quant : seulement klauswg (risque de transfert) et QuantDinger (gate d'ordre).
- Macro : Spykoninho (Fed/Trump/SEC) et jev-signals-lab (regime risk_on/off), sans validation.
- IslamBaraka90/jev-typesafe-real-financial-use-cases (https://github.com/IslamBaraka90/jev-typesafe-real-financial-use-cases, MIT, commit 2026-09-20) : 50 demos, 9 domaines ; `data/synthetic/*.labels.json` (ledgers, fraude, AML triage, reconciliation...) et backtests simules (Yahoo, entree a l'open suivant, 5 bps/cote) ; la verite terrain est synthetique ; les donnees Yahoo en cache ne sont pas sous MIT (arborescence lue = PROVEN ; details README via WebFetch = OBSERVED).
- Classification documentaire financiere (gist drillan, DOCUMENTED_CLAIM) : simonmesmith BANKING77 92.40% vs 93.66% BERT fine-tune ; kyotofin tax-doc-classifier 100% strict, ~0.001 USD/page.
- Contamination temporelle : lizhuojunx86/llm-memory-audit, etude `studies/2026-09-jev` (https://github.com/lizhuojunx86/llm-memory-audit/tree/main/studies/2026-09-jev) : 12 533 earnings US, 38 956 appels, AUC intra-firme 0.506 (beat/miss) et ~0.48 (performance) ; controle positif Claude Sonnet 5 = 0.587 ; pre-enregistre, ancrage OpenTimestamps ; 757 evenements prospectifs a scorer apres 2027-01-08 (OBSERVED via WebFetch, non clone).

## B. Qualite epistemique

### B1. Le vendeur ne fournit pas nativement la distinction absence / contradiction / insuffisance
- Zenodo, "When a Judgment Layer's Self-Reported Fields Lie" (Perry Link, v2, 2026-09-22, CC BY 4.0) https://zenodo.org/doi/10.5281/zenodo.22901853 : OBSERVED (WebFetch) : 68 items finaux (sur 96 prevus) ; 0.9909 quand la reponse est explicite ; 0.3091 quand il faut "remarquer qu'une chose est absente" ; P(true) moyen 0.5643 quand la valeur candidate n'apparait jamais dans l'entree (l'absence est lue comme un appui) ; checkpoint anglais, fenetre 512 tokens ; jugements a un pas seulement.
- GitHub issue typesafe-ai/typesafe-sdk-python#11 (PerryLink, 2026-09-22, "Closed as not planned") https://github.com/typesafe-ai/typesafe-sdk-python/issues/11 : OBSERVED (WebFetch) : sur 7 lectures live d'un outil `jev_check` (non identifie par l'auteur), `conflicted` et `undecided` n'apparaissent jamais ; contradiction (supports 0.43 / contradicts 0.67 / sufficient 0.07 ; 0.55 / 0.67 / 0.14) => `insufficient`. L'auteur admet "no artifact behind" ces 7 lectures : preuve faible. "Closed as not planned" = pas de position de fond de TypeSafe (INFERENCE : hors perimetre SDK).
- yibie/awesome-jev (clone lu, `categories/calibration-research.md`) reprend la meme etude : "sufficient field does not separate thin evidence from contradictory evidence" (meme source, pas une confirmation independante).
- INFERENCE : pour separer les etats de HOLD, poser des questions distinctes sur des preuves structurees et composer en code ; ne pas s'appuyer sur un champ unique de suffisance.

### B2. Patterns de gating avec abstention
- Docs vendeur "Nine Failure Modes of Jev 1.13" https://docs.typesafe.ai/model-jaggedness/jev-1.13 (WebFetch, DOCUMENTED_CLAIM du vendeur) : lecture litterale, nombres, dates, indirection, grand state avec details non pertinents, contenu adversarial, criteres contradictoires, invariants structurels non garantis, generation. Guidance : "avoid hiding multiple judgments in one question; use abstain/none options for missing data; design state minimally".
- jujumilk3/jev-calibration-audit (https://github.com/jujumilk3/jev-calibration-audit, MIT, 2026-09-18 ; README lu, chiffres auto-declares) : sans option abstain, accuracy 0.950 -> 0.000 et ECE 0.023 -> 0.793 sur items non repondables ; complements Noul P(x)+P(non x) de 0.71 a 1.42 ; pas de biais d'ordre (400 tests) ; 16 questions vs 1 sur le meme state : confiance +0.008, flips 0.4% (pas d'interference mesuree entre questions groupees).
- TypeSafeAI/jev-harness (https://github.com/TypeSafeAI/jev-harness, MIT, 2026-09-26 ; depot communautaire "independent of the official TypeSafe AI team" : PROVEN) : table de decision deterministe (validation, puis 4 questions Jev, seuil fixe 0.8) ; verdicts permit / proposal_only / hold ; 25 fixtures synthetiques ; question set v1 47/50, v4 50/50 et 150/150 en confirmation ; les auteurs notent "adaptive tuning on the same cases" et "does not establish calibration".
- Sovereign-Communication/harness PR#109 (fusionnee 2026-09-28, WebFetch) : `evaluate_decision` : `is_destructive` Noul, `disposition` Choice(proceed/needs_improvement/escalate), `advances_goal` ; fail-closed (signal manquant -> ESCALATE, confiance < 0.95 -> ESCALATE) ; 24 decisions etiquetees, 0 faux proceed a 0.95 (OBSERVED, primitive non branchee).
- jev-oncall (mingleiw, MIT, 2026-09-29) : bande d'incertitude : page si P(SEV1)+P(SEV2) >= 0.80, drop si < 0.20 et actionnable en accord, sinon humain avec ack 15 min (README lu).
- jevlogs (reachjalil, MIT, 2026-09-21) : `reason` typee de la route `model | protected | uncertain | unavailable | rule | budget` ; les cas incertains, en erreur, proteges ou en panne restent eligibles a l'analyse (PROVEN dans `src/index.ts`). Meilleur exemple observe de raisons de non-decision explicites.
- Quorum multi-agents autour de Jev (signal valide bloque par quorum) : NONE_FOUND. Le plus proche : veto en code (Spykoninho, klauswg) et fail-open (QuantDinger).
- EvidenceScope (chinmay29/evidence-scope, MIT, 2026-09-26) : design answer / retrieve more / abstain qui distingue insuffisance et conflit ; aucun code fonctionnel, aucun resultat (WebFetch : "design and initial scaffold") : DOCUMENTED_CLAIM/design uniquement.
- sre-agent issue #11 (RushObservability, 2026-09-26) : propose une option `abstain`/`insufficient_evidence` dans chaque requete : simple proposition (OBSERVED).

### B3. Calibration : audits independants (auto-declares)
- scienthoon/jev-ood-calibration (MIT, 2026-09-22 ; README lu) : 900 tickets synthetiques jamais vus, ECE 0.107 (4.4x le plancher 0.024) ; Score "priorite selon regle d'organisation" 44.7% de precision avec 0.74 de probabilite moyenne (inconnaissable) ; correction du 2026-09-22 : T de refit Choice 3.29 -> 1.30 (artefact du plancher de zeros), signe conserve (Choice/Score surconfiants, Noul sous-confiant) ; probabilites quantifiees a 0.01.
- KantaHayashiAI/jev-does-not-play-dice (MIT) : de equilibre 400 lancers : face 1 choisie 400/400, probabilite moyenne 82.9%, accuracy 19.0% ; documents de prevision : 45% vs 55% -> 6.6% vs 95.9% ; "ne prouve pas que les probabilites soient inutilisables" (OBSERVED via WebFetch).
- LangChain (Shea & Roche, 2026-09-20) : 100% d'accord avec l'oracle humain sur 5 runs d'un agent meteo x100, variance 92-913x plus faible que des juges LLM, 0.00035 USD/appel, 0.44 s (OBSERVED via WebFetch ; petit protocole).
- arXiv 2609.26550 "JEV-as-a-Judge" (Li, Miao, Krishnan, Padman ; soumis 2026-09-22, rev. 2026-09-27) : a moins de 3 pts de GPT-4 sur verdicts textuels, ~0.36% du cout (41% avec escalade), latence mediane 0.15 s ; degrade en maths, code, logique, paires adverses stylistiques (OBSERVED, resume arXiv).
- manankumarthakkar/jev-escalation-gate (2026-09-24, pas de LICENSE) : meme gate 100% ou 69.5% selon la construction des mauvaises reponses ; confiance 97% => juste 97.6% ; un "cannot answer" confiant permet de sauter la generation sur 14.5% des jugements ; n=600 (OBSERVED, README lu).
- abhixhek/jevcal (MIT, 2026-09-18) : outil de seuil par question + split held-out + cascade + CI ; son README affirme que l'accord client de TypeSafe restreint la publication de performances (DOCUMENTED_CLAIM d'un tiers, non verifie ; d'autres auteurs publient des chiffres).
- jmanhype/jev-dspy-lab (MIT, 2026-09-20) : harnais de calibration, selective risk, abstention fail-closed ; fixture SYNTHETIQUE, "not a claim about Jev model quality" (PROVEN).
- INFERENCE : `confidence` et P(Noul) non transferables entre domaines ; mesurer par question ; figer le modele.

## C. News / narratif : flux massif -> Jev -> sous-ensemble -> analyse couteuse

Verdict : le pattern existe en code hors finance ; en finance, Jev est composant final (Spykoninho) ou observateur shadow. Finance + LLM aval : NONE_FOUND.

### C1. koala73/worldmonitor (PROVEN)
- https://github.com/koala73/worldmonitor ; AGPL-3.0 (LICENSE lue) ; commit 2026-09-29.
- `shared/jev-classify.js` : 2 Choice par titre (niveau critical/high/medium/low/info, criteres en situations concretes ; categorie parmi 14). `scripts/lib/jev-classify-relay.cjs` : Jev en MODE SHADOW a cote du labeller LLM ; chaque desaccord de niveau ajoute a une liste Redis plafonnee (2000 lignes, TTL 14 j) ; concurrence 6, timeout 5 s, disjoncteur apres 5 echecs consecutifs ; titres non latins exclus (documentes plus faibles) ; `levelOnly` : 1 030 -> 618 tokens d'entree ; eval `scripts/eval-jev-classify.mjs` sur un jeu golden de 255 titres juges en aveugle par Opus.
- Commentaire du code (non rejoue) : sur 413 titres juges en aveugle, Jev "TIED" le LLM sur les alertes, les deux ratent des titres differents, ~30% de desaccords de niveau : d'ou le shadow.
- Domaine geopolitique, pas marche ; Jev ne filtre pas vers un LLM.

### C2. reachjalil/jevlogs : pre-filtre avant analyse LLM, avec chiffrage economique
- https://github.com/reachjalil/jevlogs ; MIT ; commit 2026-09-21 (`benchmarks/README.md`, `benchmarks/results/metrics.json`, `docs/article/jevlogs-vs-gpt56-luna.md` lus).
- Code : score par log OTel (valeur 0-100, priorite, probabilite actionnable), `route retain|analyze` ; ERROR/FATAL contournent le modele ; echec/budget/entree trop grande => reste sur la route analyse ; cache par hash normalise ; `maxModelCalls`.
- Chiffres (auto-declares ; HDFS/BGL, 2 500 lignes/jeu, 30% d'anomalies par construction) : 6 840 appels, ~3.67 M tokens, ~0.154 USD ; rappel 0.992 avec 1% retenu (HDFS) vs GPT-5.6 Luna 0.833 a 14% ; BGL 1.0 des deux.
- L'article du depot calcule que, pour couvrir les tokens de Jev face a Luna en aval, il faut sauter ~19% des lignes ; Jev n'a retenu que 0.84% sur HDFS : "not enough to cover Jev's own tokens". Le prefiltre ne paie que si le taux de rejet est eleve ou le modele aval bien plus cher.
- Benchmark pager (synthetique, 3 000 lignes) : v3 `page_now` seul rappel 1.0 / precision 1.0 ; mais v3 vient de retouches sur le meme flux (v2 faisait 189 faux pages avec `urgency` discret) : sur-ajustement probable => OBSERVED seulement.

### C3. Autres
- AiPersonacademy/jev-resume-disqualifier : question disqualifiante d'abord, survivants evalues ensuite (< 25 ms) : DOCUMENTED_CLAIM (awesome-jev), non clone.
- Rerankers/RAG : MemSearch, LlamaIndex Jev, jev-reranker, jselect ; resultat negatif cite : "Jev reranking is not a free win" (33 047 entrees, 164 requetes, tweet @GoSailGlobal, DOCUMENTED_CLAIM) ; anessbelbati/jev-rerank-bench (MIT, 2026-09-25) cloné mais chiffres non extraits : UNKNOWN.
- Notra : bascule de classifieurs d'un LLM vers Jev Boolean a 0.5 (liste awesome-jev ; DOCUMENTED_CLAIM).
- Cross-asset relevance : `asset` Choice de Spykoninho (BTC/ETH/SOL/crypto/unrelated ; "crypto" couvre macro et politique) est le seul exemple (PROVEN) ; multi-classes d'actifs (actions/FX/rates) : NONE_FOUND.
- Anti-preuve : Spykoninho montre que pertinence/materialite ne se convertit pas en alpha (A1).

## D. Retex / attribution / evals

### D1. TokenTrim/jev-agent-failure-benchmark
- https://github.com/TokenTrim/jev-agent-failure-benchmark ; code Apache-2.0 (README) ; commit 2026-09-18.
- Code (`src/jevbench/backends/jev.py` lu) : 3 Choice par trace (agent, pas, mode = taxonomie de 17 codes) dans un seul appel ; les options sont extraites de la trace ; test anti-fuite `tests/test_leakage.py` (PROVEN).
- Resultat declare (`RESULTS.md`, 6 257 traces texte Who&When Pro, CC-BY-4.0) : Who 73.4, When 76.4, What (F1 macro) 23.7, All 31.3 vs gpt-5.4 (chiffres du papier) 55.7/72.3/15.3/21.3 ; cout 1.28 USD ; ECE du mode d'erreur 0.287.
- Limites (dites par l'auteur) : Who et When sont "adaptation-favoured" (Jev choisit dans une liste, le LLM genere) ; seul l'axe What est comparable (23.7 vs 22.2 GLM-5, IC [22.4, 24.9]) ; echecs INJECTES, pas des incidents reels ; comparaison aux chiffres publies, non rejouee avec les memes prompts. Le titre "outperforms on every axis" est a nuancer.
- Pilote negatif non-Jev dans le meme depot : `pilots/gliclass-routerarena`.

### D2. mingleiw/jev-oncall : RCA sans LLM
- https://github.com/mingleiw/jev-oncall ; MIT ; 2026-09-29 (README lu, chiffres auto-declares).
- 3 modes : LLM seul, LLM + scores Jev apres chaque verification, "jev-agent" (Jev + code, sans LLM). Run 1 (60 pannes enregistrees Sock Shop/Train Ticket, RCAEval RE2 instance 1, scenarios generes par code et geles avant le 1er essai) : bon service 57/60 vs 53/58 (DeepSeek V4.1 Flash) et 52/54 (GLM-5.3) ; diagnostic supporte 35/60 (moins bien que 39/58 et 41/54) ; 5.3 s vs 32/119 s ; ~0.004 USD/cas. Run 2 (120 cas non vus, pre-enregistre) : v6 diagnostic supporte 90/120 vs v5 68/120 (p<0.001) ; 0 reponse fausse marquee "verified" sur 30 verifiees. Faiblesses : 10/12 erreurs v6 = pannes reseau imputees au voisin ; disque 15/18 "right-but-unsupported".
- Pertinent pour D et B : "verified/unverified" est un signal de suffisance calcule par le code.

### D3. Evals automatiques et taxonomies
- LangChain, arXiv 2609.26550, blog Harness (Gattupalle & Jindal, 2026-09-21 ; routing 83% de precision, V2 +26% de cout car un acheminement vers un modele moins cher peut allonger les boucles : OBSERVED WebFetch). Langfuse (2026-09-18) et HoneyHive : non lus (UNKNOWN). Convergence : juge rapide et peu variable ; degrade sur les verdicts a deriver.
- teatree issue #4819 (souliane, 2026-09-20 ; WebFetch) : "advisory/additive uniquement, jamais sur un chemin bloquant" quand l'entree est non fiable et la sortie autorise une action (DOCUMENTED_CLAIM d'un utilisateur, coherent avec les docs vendeur).
- sutro-sh/jev-align (Apache-2.0, 2026-09-20) : lignes CSV/JSONL en Choice/Score/Boolean, ambigus et audit envoyes a un humain, definition optimisee avec GEPA (liste ; non lu en detail).
- arXiv 2609.24052 (Rafe & Das, 2026-09-21 ; WebFetch) : 499 500 recits de crashs Texas, 195 857 codes avec un schema de 27 questions ; F1 0.908 vs libelles humains ; recalibration : erreur /3.3 ; "cost governed by schema size rather than narrative length" ; "calibration varies by model rather than by paradigm". Hors finance ; bon analogue de "recit -> variables typees" avec schema partage.

## E. Prompt debt : pratiques observees

1. State contract unique, plusieurs jugements (PROVEN)
   - ai-hedge-fund : `state={investor_prompt, financial_snapshot}` pour tous les investisseurs ; 3 questions communes ; `JEV_CONTRACT_VERSION=1` a inclure dans l'identite de cache, a incrementer quand la semantique change ; les prompts d'investisseur sont fournis "verbatim as reference material".
   - Spykoninho : state nomme unique, questions communes + `SOURCE_RULES` par source, `compose` en code ; `knownSignals()` derive du code (pas de desynchronisation) ; `migrateJudgment` et `judgeVersion` pour archives.
   - buberlo : `build_questions()` (6 questions), `parse_response` -> `JudgmentSet` type unique, que `HeuristicJudge` produit aussi (contrat commun Jev/fallback).
2. QuestionSet versionne : TypeSafeAI/jev-harness : `REVIEW_QUESTION_SET_VERSION=4`, `REVIEW_QUESTIONS_V1..V3` figes, ids de questions immuables, receipts lies a la version ; historique de 4 iterations mesurees avec aveu de tuning adaptatif. jevkit (ariel-frischer, MIT, 2026-09-26) : `jev lint`, 13 regles offline avant appel (README lu ; le nombre de regles vient d'awesome-jev).
3. Meme primitives sur plusieurs providers : system-one-adapter-python (officiel TypeSafe, v0.2.1 du 2026-09-22, LICENSE presente ; README lu) : meme `system_one(state, questions, provider, model)` vers OpenAI/Anthropic/Gemini avec sortie structuree native ou JSON invite, `llm_answer_mode` probabilities|discrete, `normalize_probabilities`, retries correctifs, `debug.llm_attempts` ; objectif declare : comparer cout/vitesse/intelligence. Aucun resultat comparatif finance publie. jevper (zhulinchng, Apache-2.0, 2026-09-27) : implementation independante non affiliee du format de fil sur tout modele OpenAI-compatible (logprobs, grammaire ou JSON schema).
4. Ecriture des criteres : RastislavDujava/jev-classification-prompting (MIT, 2026-09-21) : 41 items, 70% -> 96% avec criteres precis, "not established fact" (OBSERVED). WorldMonitor et Spykoninho decrivent les niveaux par des situations concretes ; AlgoVault met les nombres en buckets ; docs vendeur : pas de comptage/dates.
5. Securite du state : donnees externes marquees non fiables (Spykoninho), liste blanche (klauswg) ; VentureBeat via awesome-jev-robustness : injection ayant fait baisser P(block) de 0.76 a 0.48 (DOCUMENTED_CLAIM).
6. Un prompt par instrument/agent/provider evite en pratique : ai-hedge-fund, forks jev-trader (state par symbole), jev-market-reflex (`questionFor(symbol)` avec criteres identiques). Aucune mesure du cout de maintenance : "moins de dette de prompts" reste une INFERENCE.

## F. Analogues non-Jev (COMPARAISON UNIQUEMENT, pas des preuves Jev)

| Outil | URL | Licence | Fonction | Limite pour la comparaison |
|---|---|---|---|---|
| Instructor | https://github.com/567-labs/instructor | MIT | schema Pydantic `response_model` multi-provider, retries de validation | valide la forme ; pas de probabilites calibrees par option |
| PydanticAI | https://github.com/pydantic/pydantic-ai | MIT | agents a sorties Pydantic multi-providers, `pydantic-evals` | idem |
| BAML | https://github.com/BoundaryML/baml | Apache-2.0 | fonctions de prompt typees, schema-aligned parsing, multi-provider, tests | idem |
| Outlines | https://github.com/dottxt-ai/outlines | Apache-2.0 | generation contrainte (Literal/regex/grammaire) modeles locaux et API | garantit la forme, pas le jugement |
| LiteLLM | https://github.com/BerriAI/litellm | coeur open source + licence commerciale enterprise (details UNKNOWN) | interface unifiee OpenAI-format vers 100+ providers | transport ; prismhq/jev-router (MIT, 2026-09-16) l'utilise pour router avec Jev |
| DSPy | https://github.com/stanfordnlp/dspy | MIT | signatures typees portables entre LM + optimiseurs | le plus proche de E ; jev-dspy-lab mesure le couplage |
| FinBERT | https://huggingface.co/ProsusAI/finbert ; arXiv 1908.10063 (Araci, 2019-08-27) | non confirmee : UNKNOWN | sentiment financier 3 classes (Financial PhraseBank) | prefiltre classique ; etiquettes fixes, pas de questions ad hoc |
| BART-large-MNLI | https://huggingface.co/facebook/bart-large-mnli | MIT | zero-shot NLI, `multi_label=True` | analogue direct de "criteres = hypotheses" ; poorjev (rupeshpoojary9) en fait une replique de l'interface Jev avec abstention conforme, ECE 0.170 -> 0.071 (DOCUMENTED_CLAIM via awesome-jev) |
| FrugalGPT | https://arxiv.org/abs/2305.05176 (Chen, Zaharia, Zou, 2023-05-09) | n/a | cascade de LLM ; papier : "jusqu'a 98% de reduction de cout a performance egale" | analogue academique de "modele bon marche puis cher" |

## G. NONE_FOUND / UNKNOWN
- Quorum multi-agents avec Jev : NONE_FOUND.
- Backtest significatif d'un signal financier base sur Jev : NONE_FOUND ; le seul test avec/sans est negatif (A1).
- Prefiltre Jev -> LLM sur news financieres : NONE_FOUND.
- Anomaly detection de series de marche via Jev : NONE_FOUND.
- Mesure du gain de maintenance sur la dette de prompts : UNKNOWN.
- Licence FinBERT : UNKNOWN ; licences UNKNOWN pour jev_stock, jev-signals-lab, jev-escalation-gate.
- Aucun chiffre rejoue (pas de cle TypeSafe).
- Cites mais non lus : jev-radar (everyinfra), jev-reliability, jev-certify, jev-orderby-bench, Convex evals, jevals.com, hermes-nerve, dsh-jev-guard, jev-tradingview-signal, Langfuse/HoneyHive blogs.
- La gist drillan et les awesome-lists sont des index tiers (etoiles/dates declaratives), pas des preuves.

## H. Recommandations (INFERENCE)
1. Gate de decision : Jev = mesure atomique ; code = politique, veto, sizing ; fallback deterministe qui emet le meme type ; erreur => escalade, jamais approbation (buberlo, klauswg, jev-signals).
2. HOLD par cause : ne pas s'appuyer sur `sufficient` ; questions distinctes (donnees absentes / preuves en conflit / preuves minces / signal valide bloque), option `none/abstain`, criteres litteraux, `reason` ecrite en code (jevlogs, Spykoninho), tests sur cas contradictoires.
3. News : mesurer le taux de rejet avant de promettre une economie (jevlogs : 0.84% retenu ne paie pas) ; demarrer en shadow avec journal de desaccords (WorldMonitor) ; valider par etude d'evenements avant l'allocation (Spykoninho : coefficients a zero).
4. Eval/retex : choix sur listes candidates fermees, ECE par question (0.287 sur le mode d'erreur), incidents reels separes des echecs injectes.
5. Prompt debt : figer `jev-1.13.0`, versionner le QuestionSet (harness v4 + receipts), inclure la version dans la cle de cache, linter offline (jevkit), jeu de probes fixe pour detecter la derive.
