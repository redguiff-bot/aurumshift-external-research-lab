# Analyse approfondie de la lane 005 — Résilience des flux de données et sources gratuites (PR #5 mergée)

> Document d'analyse écrit pour Jean-François. Il tutoie le lecteur et explique chaque terme technique à sa première occurrence.
> Périmètre : branche `origin/main`, dossiers `reports/005_data_feed_resilience/` (rapports 00 à 12) et `bench/data_feeds_v1/` (code, captures brutes, JSON dérivés, citations de conditions d'utilisation). Rien n'a été modifié dans le dépôt, hors ce fichier.
> Convention de vérification utilisée partout : **✔ vérifié** (recalculé ou relu dans un fichier de résultats/brut), **✘ écart** (le rapport dit autre chose que les fichiers), **? non vérifiable** (aucun fichier du dépôt ne permet de trancher).
> Labels de preuve du dépôt (`claude.md`) : PROVEN (prouvé, reproductible), OBSERVED (vu dans une exécution), DOCUMENTED_CLAIM (affirmé par une doc officielle ou un rapport, non testé), INFERENCE (déduit), UNKNOWN (inconnu).

---

## Lexique express (pour ne pas te perdre)

| Terme | Explication simple |
|---|---|
| **Branche / commit / PR / merge** | Sur GitHub, une *branche* est une copie de travail du projet ; un *commit* est une sauvegarde datée avec un message ; une *PR* (pull request) est une demande de fusion d'une branche dans la branche principale ; un *merge* est cette fusion. Ici « PR #5 mergée » = le travail a été accepté et fusionné dans `main`. |
| **Flux de données / source** | Un service internet qui fournit des prix ou des indicateurs (une Bourse de cryptos, la BCE, la Fed…). |
| **API (REST / WebSocket)** | Une « prise » informatique. *REST* : tu poses une question, tu reçois une réponse (comme un formulaire). *WebSocket* : la connexion reste ouverte et le serveur te pousse les données en continu. |
| **Sans clé (« keyless »)** | Utilisable sans compte ni mot de passe. |
| **Bougie 1 minute (OHLC)** | Résumé d'une minute de marché : prix d'ouverture (Open), plus haut (High), plus bas (Low), fermeture (Close), plus le volume. |
| **bps (points de base)** | 1 bps = 0,01 %. 13 bps = 0,13 %. |
| **Perp (perpétuel)** | Contrat dérivé crypto sans échéance. Il verse périodiquement un **funding** (taux de financement) entre acheteurs et vendeurs pour rester proche du prix réel. |
| **Open interest (OI)** | Nombre de contrats dérivés encore ouverts (position totale du marché). |
| **Liquidation** | Fermeture forcée d'une position trop endettée. |
| **Basis** | Écart entre le prix d'un contrat à échéance (future) et le prix « comptant » (spot). |
| **Options, IV, skew** | Les options sont des droits d'acheter/vendre à un prix fixé. L'*IV* (volatilité implicite) est la nervosité anticipée que ces prix reflètent ; le *skew* est l'asymétrie de cette nervosité entre options à la baisse et à la hausse. |
| **PIT (point-in-time)** | « Tel que connu à cet instant-là ». Une donnée PIT-safe ne contient jamais d'information qui n'était pas encore publiée à la date simulée. |
| **Lookahead / fuite** | Utiliser sans le vouloir une information du futur dans un test (par exemple une bougie encore en formation). Cela rend les résultats trop beaux pour être vrais. |
| **Revision / backfill** | Un fournisseur peut corriger a posteriori une valeur passée (*revision*) ou remplir l'historique après coup (*backfill*). |
| **Geo-block / HTTP 451, 403, 429** | Codes d'erreur web : 451 = interdit pour raison légale/géographique ; 403 = accès refusé ; 429 = trop de requêtes. |
| **Checksum SHA-256** | Empreinte numérique d'un fichier : si elle correspond à celle publiée, le fichier n'a pas été altéré. |
| **ToS** | Conditions d'utilisation d'un service. |
| **Gap-filling** | Le fournisseur invente une bougie « plate » à volume nul quand il n'y a eu aucun échange, pour ne pas laisser de trou. |
| **Consensus (dans ce rapport)** | La médiane des prix des autres plateformes d'un même groupe, utilisée comme référence de comparaison (pas comme vérité). |
| **Corrélation de rendements** | À quel point deux séries montent et descendent ensemble minute par minute (1 = identiques, 0 = sans lien). |
| **Egress** | Le point de sortie internet du conteneur cloud utilisé pour les tests (ici filtré par un proxy). |

---

## 0. Fiche d'identité

| Champ | Valeur (source) |
|---|---|
| Lane | 005 — Résilience des flux de données et découverte de sources gratuites. Nom de mission dans le rapport : `AURUMSHIFT_EXTERNAL_DATA_FEED_RESILIENCE_AND_FREE_SOURCE_DISCOVERY_V1` (`reports/005_data_feed_resilience/00_EXECUTIVE_SUMMARY.md`) |
| Dépôt | `https://github.com/redguiff-bot/aurumshift-external-research-lab` (`git remote -v`) |
| Branche lue | `origin/main` (HEAD au moment de la lecture : `1a449df`, merge de la PR #6, autre lane) |
| Branche de travail d'origine | `claude/data-feed-resilience-v1` (déduite du message de merge « Merge pull request #5 from redguiff-bot/claude/data-feed-resilience-v1 ») |
| Commit de contenu | `01af16a` « Add data feed resilience & free-source discovery study (report 005) », auteur « Claude », 2026-09-29 13:18:43 UTC (`git show 01af16a`) |
| Commit de merge (PR #5) | `ce8f91f`, 2026-09-29 15:20:44 +0200, auteur du merge « RedGuiff GitHub », parents `9100649` (PR #4) et `01af16a` |
| Nombre de commits de la lane | 1 seul commit de contenu (`git log origin/main -- reports/005… bench/data_feeds_v1`) |
| Fichiers de la lane | **131** = 13 rapports `.md` + 1 `README.md` + 15 scripts `py/` + 86 captures `raw/` + 16 fichiers `results/`. Le commit annonce 134 fichiers : les 3 fichiers en plus sont des `.pyc` (fichiers Python compilés) de `bench/pit_v1/py/__pycache__/`, sans rapport avec la lane et absents de `origin/main` (✔ `git ls-tree`) |
| Taille | 3 247 418 octets pour les 131 fichiers (raw : 2 701 834 octets ; 3 fichiers `bars_t0/t1/t2.json` d'environ 358 Ko chacun). Insertions du commit : 18 228 lignes |
| Rapports | 3 353 lignes en tout pour les rapports et scripts ; `01_SOURCE_LANDSCAPE.md` seul = 1 175 lignes (68 « fiches sources ») |
| Date des mesures | Toutes le 2026-09-29, environ 12:50–13:15 UTC (`12_LIMITATIONS.md` point 1), depuis un seul point d'accès internet (conteneur cloud derrière un proxy) |
| Nature de l'étude | Étude de **découverte et de mesure de comportement** de sources de données gratuites. Ce n'est PAS un backtest, pas une optimisation, pas un test d'hypothèse avec seuils préenregistrés (voir §2 et §7) |
| Verdict final | `FINAL_VERDICT=MULTIPLE_DATA_SOURCE_CANDIDATES_SUPPORTED` (`bench/data_feeds_v1/results/final_block.txt`) |
| Garde-fous du verdict | `ANY_DROP_IN_SOURCE=NO` et `ANY_SCIENTIFIC_INVALIDATION=NO` |
| Force du verdict | **Faible à modérée, purement descriptive.** Traduction : « il existe plusieurs sources gratuites utilisables comme candidates de travail », mais aucune n'est jugée « prête à l'emploi », et l'étude repose sur un seul instant, un seul point d'accès et 240 minutes de bougies. Mon appréciation : le verdict est sûr pour la question « ces sources répondent-elles et se ressemblent-elles ? » ; il est fragile pour toute question de stabilité, de licence ou d'absence de fuite dans le temps (§7). |

Le nombre de lignes de mon analyse est indiqué en fin de réponse.

---

## 1. Mission et question posée

### 1.1 Question reformulée simplement

AurumShift est un système de recherche de trading « papier » (sans argent réel). Il dépend de flux de données de marché. La mission demande : **si un flux venait à manquer (panne, licence, coût), quelles sources gratuites pourrait-on utiliser à la place, et dans quelles conditions ?** Elle demande en pratique :

1. Découvrir des sources gratuites pour plusieurs « classes de manques » : prix crypto spot (bougies 1 min et multi-échelles), dérivés (funding, open interest, liquidations, basis, options), FX (devises), or/métaux, matières premières, macro-économie, calendrier/actualités.
2. Les **exécuter réellement** (appels HTTP/WebSocket réels), pas seulement lire leur documentation.
3. Comparer les fournisseurs entre eux (mêmes minutes, mêmes horodatages), tester la latence, les limites, les révisions.
4. Évaluer la **préparation PIT** (peut-on reconstruire ce qui était connu à l'instant T ?), la licence et le coût.
5. Produire une matrice de résilience (qui peut être principal, secondaire, secours…) et un verdict par source (ADOPT/ADAPT/PARK/REJECT).

### 1.2 Contraintes du dépôt (`claude.md`, ✔ lu)

- Le dépôt est un **laboratoire de recherche externe** : il ne contient pas le code d'AurumShift et ne doit jamais prétendre connaître l'implémentation privée actuelle. La lane le respecte : `12_LIMITATIONS.md` point 13 dit « No AurumShift code, schema or data was read ».
- Doctrine : **REUSE → ADAPT → WRAP → COMPOSE → CUSTOM en dernier** (réutiliser tel quel, adapter, envelopper, composer, écrire sur mesure en dernier recours).
- Ne pas classer les projets sur les étoiles GitHub, ne pas fabriquer de résultats de benchmark, inspecter le code réel plutôt que croire les README.
- Distinguer PROVEN / OBSERVED / DOCUMENTED_CLAIM / INFERENCE / UNKNOWN.
- Contraintes AurumShift rappelées : recherche seule / papier, PostgreSQL d'abord, **PIT / provenance / no-lookahead critiques**, événementiel/intrajournalier (pas de haute fréquence), **une source faisant autorité par sujet**, « l'absence de preuve n'est pas une preuve d'absence », coûts de marché réalistes, complexité d'infrastructure justifiée.
- Frontière : ne jamais affirmer la compatibilité avec AurumShift depuis ce dépôt. Le résultat est un ensemble de candidats ADOPT/ADAPT/PARK/REJECT ; l'adjudication finale se fait plus tard contre le vrai dépôt local.

Point d'attention : la lane emploie le mot **ADOPT_REFERENCE**, défini dans `11_ADJUDICATION.md` comme « à utiliser comme source de référence pour la classe dans des recherches ultérieures ; rien n'est intégré ». Ce n'est pas un ADOPT au sens d'intégration.

---

## 2. Méthode

### 2.1 Ce qui a été fait (inventaire, `00_EXECUTIVE_SUMMARY.md` et `counts.json`)

| Élément | Chiffre |
|---|---|
| Sources cataloguées | 68 |
| Exécutées de bout en bout (HTTP 200 + données lues) | 46 |
| Partiellement (joignable mais données non lues) | 1 (FRED) |
| Bloquées par le point d'accès de test | 9 |
| Non exécutées (clé/compte requis, erreur propre, choix délibéré) | 12 |
| Vérification : 46 + 1 + 9 + 12 = 68 | ✔ recalculé depuis `catalog.py` (`exe`: Y 46, N 12, BLK 9, PART 1) |
| Sondes de découverte (1 appel chacune) | 119 (54 dans `sweep1.json` + 65 dans `sweep2.json`) ; 90 en HTTP 200, 29 en échec ou non-200 ✔ recalculé |
| Séries de bougies 1 min | 18 (venue × instrument) récupérées 3 fois : t0, +78 s (t1), +362 s (t2) |
| Latence répétée | 14 endpoints REST × 10 appels séquentiels espacés d'1 s |
| WebSocket | 14 endpoints, échantillons de 20 s |
| Dérivés | funding sur 9 plateformes, OI sur 8, liquidations sur 4 en REST + 2 en WS, options (Deribit vs OKX), basis (contrats à échéance Deribit) |
| Historique en masse | Binance Vision (fichiers journaliers/mensuels avec checksum), décodage de ticks Dukascopy |
| Citations de conditions d'utilisation | `docs_facts.json` : 47 fournisseurs + une entrée `_meta`, dont 43 avec au moins une citation (✔ recalculé : 43/47) |

### 2.2 Données, univers, « simulateur »

- **Pas de simulateur, pas de backtest.** Ce sont des appels réels à des services internet, effectués à un instant donné. Le seul « jeu de données » est la fenêtre de 240 minutes de bitcoin (BTC) du 2026-09-29, de 08:55Z à 12:55Z pour t0 (`bars_analysis_t2.json` → `window.start=1790672100000`, `end=1790686500000`). Note : les prix observés (BTC environ 84 000 USD, or environ 4 150 USD) sont ceux renvoyés par les services ; l'étude n'a pas cherché à les valider ailleurs (`12_LIMITATIONS.md` point 12).
- **Univers** : 18 séries BTC — spot USD (Kraken, Coinbase, Bitstamp, Bitfinex, Gemini), spot USDT (OKX, KuCoin, Gate, Bitget, MEXC, HTX, miroir Binance data-api.binance.vision), Binance.US, et perpétuels (OKX SWAP, Hyperliquid, Deribit, dYdX ; BitMEX XBTUSD rend 0 ligne car l'instrument est « Settled », ✔ `raw/bitmex_instr.json` : `state: "Settled"`, `expiry 2026-09-16`).
- **USD vs USDT** : l'USDT est une « cryptomonnaie-dollar » privée ; un prix coté en USDT peut différer de quelques bps d'un prix coté en vrais dollars. C'est un effet de cotation, pas une erreur de donnée.

### 2.3 Protocole de comparaison des bougies

Décrit par le code (`bars_lib.py`, `run_bars.py`, `analyze_bars.py`, `consensus.py`, `lagtest.py`) :

1. `run_bars.py <tag>` : calcule `end = minute courante − 1 min` et `start = end − 240 min`, appelle chaque plateforme (une tentative par plateforme, 0,4 s de pause entre plateformes) et normalise chaque bougie en `[ts_ouverture_ms, o, h, l, c, volume_base, drapeau_clos]`.
2. `analyze_bars.py t2` : pour chaque plateforme, compte les bougies dans la fenêtre `[S, E)` de t0 (doublons, minutes manquantes, ordre, bougies à volume nul, bougies « plates » O=H=L=C), puis compare t0 et t2 sur la zone commune (233 minutes) pour détecter des révisions (changement OHLC ou volume) et des arrivées tardives. Ensuite calcule pour les 136 paires de plateformes (au moins 30 minutes communes) l'écart médian en bps sur ouverture/haut/bas/clôture, le nombre de bougies strictement identiques sur les 4 champs, le rapport de volumes et la corrélation des rendements.
3. `consensus.py` : pour chaque plateforme, écart signé de sa clôture à la **médiane des autres plateformes du même groupe** (USD spot, USDT spot, perps). Explicitement « référence de comparaison, pas vérité ».
4. `lagtest.py` : corrélation des rendements par rapport à Kraken pour un décalage de −3 à +3 minutes ; le décalage optimal est retenu (test d'alignement des horodatages).

Point de méthode important (✘ relevé) : `consensus.py` et `lagtest.py` lisent la fenêtre de **t2** (09:02Z à 13:02Z), tandis que le tableau du rapport 02 mélange les compteurs de t0 (fenêtre 08:55–12:55Z) et les écarts de consensus de t2. Le rapport n'annonce qu'une seule fenêtre (« ending 12:55Z »). Impact faible (écarts entre t1 et t2 de moins de 0,17 bps sur les médianes de paires, ✔ recalculé) mais c'est une imprécision documentaire.

### 2.4 Splits, pré-enregistrement, gel des paramètres, graines

- **Splits tuning/validation/held-out** : *non applicable*. Il n'y a rien à ajuster, donc pas de jeu d'entraînement ni de jeu réservé.
- **Pré-enregistrement** : *absent*. Aucun fichier de protocole ni de seuils écrit avant l'exécution n'existe dans la lane (README et rapports seulement). Les seuils de classification sont des définitions écrites dans le rapport 08 (PIT) et 11 (« drop-in ») ; elles n'ont pas été fixées avant la mesure de façon vérifiable.
- **Gel des paramètres** : aucun paramètre à geler. Les seuls réglages sont des choix de mesure (240 minutes, 10 appels espacés d'1 s, 20 s de WebSocket, seuil de 30 minutes communes pour une paire).
- **Graines aléatoires** : aucune (aucun tirage aléatoire). Les résultats dépendent de l'horloge et du réseau.
- **Déterminisme du traitement** : ✔ vérifié (voir §6) — refaire tourner `analyze_bars.py t2`, `consensus.py` et `lagtest.py` sur les captures fournies donne des fichiers octet pour octet identiques, et `gen_reports.py` régénère les 13 rapports à l'identique.

### 2.5 Critères de décision (seuils exacts)

Les définitions de la lane, telles qu'écrites :

| Notion | Définition exacte (source) |
|---|---|
| **PIT_NATIVE** | le fournisseur fournit lui-même des sémantiques « as-of / vintage » (`08_PIT_READINESS.md`) |
| **PIT_ADAPTABLE** | horodatage d'événement + au moins l'un de : identifiant, drapeau de finalité, indicateur de révision, horodatage de réception serveur, métadonnées de fichier immuable ; le consommateur peut alors bâtir du PIT avec ses propres horodatages de réception |
| **PIT_WEAK** | uniquement des valeurs écrasées/« dernière valeur » ou un horodatage trop grossier |
| **PIT_UNSUITABLE** | instantané sans historique ni horodatage fiable |
| **Rôles de résilience** | PRIMARY / SECONDARY / FALLBACK / CORROBORATION_ONLY / HISTORICAL_ONLY ; une source n'apparaît que si un test exécuté soutient le rôle (`10_RESILIENCE_MATRIX.md`) |
| **Verdicts** | ADOPT_REFERENCE, ADAPT_CANDIDATE, PARK (preuve insuffisante, bloqué, mince, restreint), REJECT ; « aucun classement synthétique, aucun score » (`11_ADJUDICATION.md`) |
| **« Drop-in » (prêt à l'emploi)** | accès gratuit stable ou sans clé + exécuté + PIT natif ou finalité signalée par le fournisseur + **licence permissive documentée** + couvre une classe de manques sans adaptation (`11_ADJUDICATION.md`). Aucune source ne remplit toutes les conditions → `ANY_DROP_IN_SOURCE=NO` |
| **« Invalidation scientifique »** | non définie dans la lane ; `ANY_SCIENTIFIC_INVALIDATION=NO` signifie « rien n'a réfuté une hypothèse de la mission », alors qu'aucune hypothèse chiffrée n'est énoncée (§7) |

Constat structurel (✔ lu dans `catalog.py`) : les colonnes **PIT, rôle et verdict sont saisies à la main** pour chaque source (`S("okx", …, "PIT_ADAPTABLE", {...roles...}, "ADOPT_REFERENCE", …)`), pas calculées par une règle. `gen_reports.py` ne fait que compter et mettre en forme. La cohérence entre définitions et attributions n'est donc pas mécanique (voir §7).

---

## 3. Résultats détaillés, rapport par rapport

### 3.1 Rapport 00 — Synthèse

Les 7 « constats » de tête (tous étiquetés OBSERVED sauf mention) sont repris ci-dessous et testés au fil des sections. Bilan de vérification à la fin de ce paragraphe :

1. Couverture crypto sans clé large et propre : 17 séries sur 18 ont rendu des données ; 0 doublon, 0 timestamp non aligné, 0 révision sur 6 minutes. « 16/17 avec 0 minute manquante (Bitget : 1) » → **✘** pour Bitget (voir §3.2, minute manquante artefactuelle).
2. « Aucune paire ne concorde sur l'OHLC » : 0 concordance exacte sur 233 minutes pour chaque paire → ✔ (0 sur 31 688 minutes-paires).
3. Classes de dérivés couvertes gratuitement → ✔ chiffres vérifiés (§3.3).
4. Funding et OI sont des grandeurs propres à chaque plateforme → ✔ (§3.3), avec un défaut de méthode sur la somme Hyperliquid (✘, §3.3).
5. Posture PIT faible partout → ✔ cohérent avec les données (Deribit `usIn/usOut` ✔ vu ; NY Fed `revisionIndicator` ✔ présent mais vide).
6. Pièges qui corrompraient silencieusement un pipeline (unité ms→µs Binance Vision, ordre des colonnes Coinbase, bougie en formation Kraken non signalée, bougies plates remplies) → partiellement ✔ (Coinbase et Kraken vus dans le code/les données ; l'unité ms→µs entre 2024-12 et 2025-01 est **?**, voir §6).
7. Ce que le point d'accès n'a pas pu atteindre (Binance principal 451, Bybit 403, MEXC futures 403, FRED/ALFRED, Stooq, GDELT, IMF, BLS ICS) → ✔ cohérent avec `sweep1/2.json`.

Décompte des verdicts : ADOPT_REFERENCE 8 · ADAPT_CANDIDATE 22 · PARK 37 · REJECT 1 ✔ (`counts.json`, recalculé depuis `catalog.py`).

### 3.2 Rapport 02 — Bougies crypto spot et perp (1 minute)

Fenêtre : 240 minutes fermées se terminant le 2026-09-29 12:55Z (t0 récupéré à 12:56:58Z ; t2 à 13:03:00Z, soit 362 s plus tard).

**Tableau complet du rapport (reproduit), avec vérification ligne à ligne contre `bars_analysis_t2.json`, `consensus_dev.json` et `lag_test_vs_kraken.json` : les 17 lignes de données et la ligne BitMEX correspondent ✔**

| Plateforme | bougies | manq. | doubl. | ordre natif | vol nul | plates | révisées OHLC/vol | écart signé (bps) | écart abs. médian | écart abs. p95 | corr. rdts vs Kraken |
|---|---|---|---|---|---|---|---|---|---|---|---|
| OKX BTC-USDT | 240/240 | 0 | 0 | décroissant | 0 | 0 | 0/0 | 0,34 | 0,44 | 1,31 | 0,986 |
| KuCoin BTC-USDT | 240/240 | 0 | 0 | décroissant | 0 | 0 | 0/0 | −0,02 | 0,76 | 1,82 | 0,944 |
| Gate BTC_USDT | 240/240 | 0 | 0 | croissant | 0 | 0 | 0/0 | 0,12 | 0,37 | 1,09 | 0,988 |
| Bitget BTCUSDT | 239/240 | 1 | 0 | croissant | 0 | 0 | 0/0 | 0,87 | 0,87 | 2,19 | 0,983 |
| MEXC BTCUSDT | 240/240 | 0 | 0 | croissant | 0 | 0 | 0/0 | −1,32 | 1,32 | 2,67 | 0,968 |
| HTX btcusdt | 240/240 | 0 | 0 | décroissant | 2 | 8 | 0/0 | −4,54 | 4,54 | 6,37 | 0,933 |
| Miroir Binance BTCUSDT | 240/240 | 0 | 0 | croissant | 0 | 0 | 0/0 | 0,50 | 0,51 | 1,49 | 0,983 |
| Kraken XBTUSD | 240/240 | 0 | 0 | croissant | 0 | 0 | 0/0 | −0,29 | 0,43 | 1,74 | 1,000 |
| Coinbase BTC-USD | 240/240 | 0 | 0 | décroissant | 0 | 0 | 0/0 | −0,28 | 0,62 | 1,97 | 0,982 |
| Bitstamp btcusd | 240/240 | 0 | 0 | croissant | 0 | 0 | 0/0 | −0,68 | 0,70 | 2,01 | 0,978 |
| Bitfinex tBTCUSD | 240/240 | 0 | 0 | croissant | 0 | 1 | 0/0 | 13,24 | 13,24 | 15,41 | 0,937 |
| Gemini btcusd | 240/240 | 0 | 0 | décroissant | 16 | 23 | 0/0 | 0,08 | 0,88 | 3,52 | 0,787 |
| Binance.US BTCUSDT | 240/240 | 0 | 0 | croissant | 112 | 174 | 0/0 | (hors groupe) | | | 0,592 |
| OKX SWAP (perp) | 240/240 | 0 | 0 | décroissant | 0 | 0 | 0/0 | −0,83 | 1,02 | 3,18 | 0,986 |
| Hyperliquid BTC (perp) | 240/240 | 0 | 0 | croissant | 0 | 0 | 0/0 | −0,57 | 0,86 | 2,97 | 0,974 |
| Deribit BTC-PERPETUAL | 240/240 | 0 | 0 | croissant | 0 | 0 | 0/0 | 2,20 | 2,20 | 3,69 | 0,969 |
| dYdX BTC-USD (perp) | 240/240 | 0 | 0 | décroissant | 150 | 202 | 0/0 | −0,40 | 2,74 | 9,29 | 0,428 |
| BitMEX XBTUSD | 0/240 | 240 | 0 | — | — | — | — | — | — | — | — |

**Comment lire ce tableau en langage simple**

- Une colonne « écart signé » positive veut dire « plus cher que la médiane des autres plateformes de son groupe ». Un écart absolu de 0,4 bps (0,004 %) est minuscule à côté des frais de transaction habituels.
- « Bougies plates » et « volume nul » : ces bougies ne représentent pas de vrais échanges, mais des minutes remplies artificiellement. Sur dYdX, 202 bougies sur 240 sont plates, donc la série est peu informative (corrélation de 0,428 avec Kraken).
- **Note d'étiquetage (✘)** : la colonne « ret corr@0 » est la corrélation **avec Kraken** (`lagtest.py`), pas avec un consensus. Kraken affiche 1,000 parce qu'il est comparé à lui-même (valeur triviale). Mais `01_SOURCE_LANDSCAPE.md`, `catalog.py` et `11_ADJUDICATION.md` disent « ret. corr vs consensus 0.79 / 0.43 / 0.988 » : c'est une erreur d'étiquette (les valeurs sont celles du tableau, vs Kraken).

**Observations du rapport et vérification**

| Affirmation du rapport | Vérification |
|---|---|
| « Seul Bitget montre un vrai trou : minute 09:02Z absente dans les deux récupérations » | **✘ contredit par les captures brutes.** Dans `raw/bars_t0.json`, la série Bitget va de 08:56 à 12:55 sans aucun trou interne (240 lignes), donc 09:02 y est présente. La minute « manquante » comptée dans la fenêtre [08:55, 12:55) de t0 est **08:55**, soit la toute première minute demandée. Dans t1 la première minute demandée est 08:57 et Bitget commence à 08:58 ; dans t2 la première demandée est 09:02 et Bitget commence à 09:03. **09:02 est simplement la première minute de la fenêtre t2.** Le « trou » est donc un artefact de borne de requête : Bitget semble renvoyer la bougie de `endTime` mais pas celle de `startTime` (inférence, 3/3 récupérations identiques). Il n'y a pas de minute réellement manquante observée chez Bitget. |
| « 0 bougie tardive, 0 révision entre t0 et t2 » | ✔ (`revised_ohlc_bars = revised_vol_bars = 0` pour toutes les plateformes). Contrôle supplémentaire fait pour cette analyse sur l'ensemble des minutes communes, volume compris : 0 changement partout sauf Kraken (voir ci-dessous). |
| « La bougie fermée depuis moins de 60 s avant t0 était identique à t2 » | ✔ pour les 11 plateformes qui ont renvoyé la minute 12:55 dans t0 et t2 (aucune différence) ; cette minute est hors de la fenêtre d'analyse et le rapport ne l'a pas mesurée dans le script, mais le fait est exact. |
| « Kraken renvoie 3 lignes à/après la fin de fenêtre (bougie en formation incluse, non signalée) » | ✔ 3 lignes (12:55, 12:56, 12:57 ; 244 lignes au total). **Nuance :** seule la dernière était réellement en formation. Constat nouveau : la ligne 12:57 de t0 a **changé** entre t0 et t2 (bas, clôture et volume différents), ce qui démontre concrètement le risque de fuite (§6, §7). |
| « Bitstamp a ignoré start/end et renvoyé 1000 lignes ; Gemini renvoie environ 1 440 bougies fixes » | ✔ pour Bitstamp (`raw/bars_t0.json` : 1000 lignes). Gemini : la sonde de découverte a reçu un bloc fixe, cohérent avec la doc citée. |
| « Différence USDT vs USD environ 3 à 5 bps » | **✘ imprécis.** Les 24 paires USD × USDT hors Bitfinex et HTX vont de 1,81 (MEXC/Gemini) à 4,08 (Bitget/Bitstamp) bps ; HTX monte à 5,20 (Bitget/HTX) ; Bitfinex à 9,5–14,5 bps. L'ordre de grandeur est juste ; la borne basse « 3 » est trop haute, et la synthèse annonce « 3–4,7 ». |
| « Valeurs aberrantes : Bitfinex +13 bps, HTX −4,5 bps, MEXC −1,3 bps » | ✔ (13,24 ; −4,54 ; −1,32). Causes UNKNOWN, ce que le rapport écrit honnêtement. |

**Comparaison croisée (rapport 07, ✔ recalculée)** : 136 paires ; chacune a n = 233 minutes communes ; 136 × 233 = 31 688 minutes-paires, dont **0 concordance exacte OHLC** ✔. Les 8 paires les plus proches du rapport (écart médian de clôture en bps) : OKX/Gate 0,33 (p95 1,05, corr. 0,9852), Kraken/Coinbase 0,40 (1,19 ; 0,9837), OKX/miroir Binance 0,46 (1,50 ; 0,9833), Gate/miroir Binance 0,46 (1,40 ; 0,9861), Kraken/Bitstamp 0,48 (1,49 ; 0,9777), OKX SWAP/Hyperliquid 0,52 (1,71 ; 0,9712), Bitget/miroir Binance 0,53 (1,75 ; 0,9781), OKX/Bitget 0,58 (1,52 ; 0,9836) — toutes ✔. Kraken contre OKX : écart signé 3,31 bps (OKX plus cher) ✔ ; Kraken contre Bitfinex : −13,17 bps ✔.

**Volumes** : non comparables entre plateformes (base, quote, contrats, USD). Le rapport dit « ratio de volumes base entre 0,003× et 9× la médiane du groupe » ; je n'ai pas revérifié cette plage (**?**) ; le ratio OKX SWAP/Hyperliquid de 522,9 dans `bars_analysis_t2.json` illustre bien le problème d'unités (contrats vs base).

**Historique en masse Binance Vision** (`fxgold_bulk.json`, `binance_vision_fix.json`)

- Fichier spot BTCUSDT 1 minute du 2026-09-26 : 1 440 lignes, 0 doublon, 0 manquant, `checksum_ok = true` → l'empreinte SHA-256 du fichier zippé correspond au `.CHECKSUM` publié ✔ (PROVEN).
- Comparaison avec l'API `data-api.binance.vision` : `fxgold_bulk.json` (exécution d'origine) affiche `common = 0` parce que l'API est en millisecondes et le fichier en microsecondes. Un correctif, `binance_vision_fix.json`, affiche `common = 1440`, `ohlcv_differs = 0` ✔ — **mais le script qui a produit ce correctif n'est pas dans `py/`** (voir §9). La valeur du rapport (1440/1440) est donc ✔ dans les résultats mais sans code pour la reproduire.
- Fichier de 2026 en unité microsecondes (16 chiffres) ✔ (`ts_unit_digits: 16`, premier champ `1790380800000000`). Fichier d'août 2017 : premier timestamp `1502942400000` (13 chiffres, millisecondes) et 21 360 lignes ✔. Le rapport dit que « le fichier mensuel 2024-12 est en 13 chiffres, celui de 2025-01 en 16 » : **? non vérifiable**, aucune capture de ces deux fichiers n'est dans le dépôt (seules 2017-08 et 2026-09-26 le sont). Le fait que l'unité ait changé quelque part entre 2017 et 2026 est vérifié ; la date exacte du changement ne l'est pas.
- Futures USD-M : klines en ms ✔ (`1790380800000`). Fichier `metrics` (OI, ratios long/short) : le rapport dit « 289 lignes/jour » ; le fichier compte 289 lignes **en-tête comprise**, soit 288 lignes de données à 5 min (✘ mineur). Somme OI au 2026-09-26 00:00 : 95 234,404 BTC ✔.
- `liquidationSnapshot` et `bookTicker` : HTTP 404 ✔.

### 3.3 Rapport 03 — Dérivés

**Funding (taux de financement des perpétuels), 7 derniers jours**

Cadence relevée (`derivs_analysis.json → funding_summary`, ✔ toutes les lignes) : 8 h pour OKX (30 lignes), Gate (30 ; écarts 479 et 480 min), Bitget (30), KuCoin (21), BitMEX XBTUSDT (30, mais données du 09-06 au 09-16 seulement) ; 1 h pour Hyperliquid (168 lignes, écarts 59/60 min), dYdX (200), Kraken Futures (200, taux « relatif »), Deribit (168).

**Comparaison aux 15 frontières de 8 heures (unité : bps par 8 h)** — le tableau du rapport est intégralement ✔ (chaque cellule recalculée depuis `funding_8h_compare`) :

| Frontière | OKX | Gate | Bitget | KuCoin | Hyperliquid Σ |
|---|---|---|---|---|---|
| 09-24 16Z | −0,03 | −0,08 | +0,44 | +0,26 | +0,88 |
| 09-25 00Z | −0,04 | +0,07 | +0,27 | +0,09 | +1,13 |
| 09-25 08Z | +0,72 | +0,28 | +0,53 | +0,26 | +1,13 |
| 09-25 16Z | +0,34 | −0,07 | +0,78 | +0,29 | +1,13 |
| 09-26 00Z | +0,17 | −0,28 | +0,48 | −0,28 | +1,02 |
| 09-26 08Z | +0,21 | −0,09 | +0,71 | −0,05 | +0,77 |
| 09-26 16Z | −0,06 | −0,20 | +0,24 | −0,14 | +1,02 |
| 09-27 00Z | −0,09 | −0,15 | +0,24 | +0,22 | +0,73 |
| 09-27 08Z | −0,18 | −0,04 | +0,17 | +0,04 | +1,13 |
| 09-27 16Z | −0,11 | +0,04 | +0,07 | +0,05 | +1,13 |
| 09-28 00Z | +0,46 | −0,23 | +0,12 | −0,01 | +0,98 |
| 09-28 08Z | −0,08 | −0,15 | +1,00 | −0,22 | −0,03 |
| 09-28 16Z | +0,71 | +0,51 | +1,00 | +0,65 | +1,00 |
| 09-29 00Z | +0,54 | +0,17 | +1,00 | +0,17 | +0,57 |
| 09-29 08Z | +0,25 | +0,00 | +1,00 | +0,28 | +0,32 |

Lecture : à chaque échéance de 8 h, quatre plateformes qui financent « le même BTC perpétuel » affichent des taux différents et souvent de signe opposé. Désaccord de signe en 11 frontières sur 15 ✔ (recalculé, zéros exclus). Conclusion du rapport (« comparer des distributions, pas des valeurs ») ✔ raisonnable.

**Deux écarts trouvés ici :**

1. **✘ Bitget « exactement 1,00 bps dans 3 des 4 dernières lignes »** : les données montrent **4 sur 4** (09-28 08Z, 09-28 16Z, 09-29 00Z, 09-29 08Z valent toutes 1,00). L'hypothèse « plafond/plancher » (INFERENCE) est donc encore plus plausible que le rapport ne le dit.
2. **✘ Colonne Hyperliquid Σ : somme de 9 lignes horaires pour une fenêtre de 8 heures.** Le code (`dv.py`) somme les lignes dont l'horodatage `k` vérifie `t − 8 h < k ≤ t + 60 s`. À cause de la gigue de quelques millisecondes d'Hyperliquid (`…:00:00.059`), cela capte **9 lignes** (`hl_n = 9` dans les 15 lignes). À taux de base de 1,25e-5 par heure, 9 lignes = 1,125e-4 = **1,13 bps**, alors que 8 lignes = **1,00 bps**. Les valeurs « +1,13 » du tableau sont donc surévaluées de 12,5 % environ par ce décalage d'une heure. Le rapport écrit « sum of the 9 hourly rows covering the window » : il le dit, sans en signaler la conséquence. La conclusion qualitative (Hyperliquid n'est pas superposable aux autres) n'est pas remise en cause, mais la colonne ne devrait pas servir de valeur.

**Open interest (OI), instantané**

Tableau du rapport, tous ✔ contre `oi_snapshot` :

| Plateforme | champ | unité | valeur | ≈ BTC (à 84 340 USD, pour l'échelle seulement) |
|---|---|---|---|---|
| OKX BTC-USDT-SWAP | oiCcy | BTC | 28 328,5 | 28 329 |
| Bitget BTCUSDT | size | BTC | 31 577,4 | 31 577 |
| Hyperliquid BTC | openInterest | BTC | 34 292,4 | 34 292 |
| Deribit BTC-PERPETUAL | open_interest | USD | 796 941 590 | 9 449 (✔ 796 941 590 / 84 340 ≈ 9 449) |
| Gate BTC_USDT | position_size × 0,0001 | contrats→BTC | 26 681,8 | 26 682 (✔ 266 817 520 × 0,0001) |
| Kraken Futures PF_XBTUSD | openInterest | unité INCONNUE | 2 335,4 | 2 335 |
| dYdX BTC-USD | openInterest | BTC (non vérifié) | 201,1 | 201 |

Le prix de 84 340 utilisé pour la conversion est **codé en dur** dans `gen_reports.py` (`btc=84340.0`) ; il ne sert qu'à donner un ordre de grandeur. Bitfinex : la ligne positionnelle contient 8 933,01 à l'index 18 ✔ (correspond à la case « open interest » de la doc, position déduite = INFERENCE). Historique : OKX 100 lignes = 8,25 h à 5 min ✔ ; Gate 99 lignes à 5 min ✔.

**Liquidations**

| Source | Observé | Vérification |
|---|---|---|
| OKX REST `/public/liquidation-orders` | 100 lignes sur 164 min ; endpoint **absent de la doc actuelle** | ✔ (100 lignes, 163,69 min) ; note doc ✔ dans `docs_facts.json` |
| OKX WebSocket | 5 événements en 15 s (port 443) ; port 8443 réinitialisé par le proxy | ✔ (`ws_okx_retry.json`) |
| Gate REST | 13 lignes / 19 min | ✔ (19,4 min) |
| Bitfinex REST | 500 lignes / 78 h, toutes paires confondues | ✔ (4 676 min ≈ 77,9 h) |
| BitMEX | REST `[]` ; WS : 1 liquidation en 20 s | ✔ WS ; REST vide ✔ (`raw/bitmex_liq.json` = 2 octets) |
| Binance Vision bulk `liquidationSnapshot` | HTTP 404 | ✔ |
| Binance principal / Bybit | bloqués (451 / 403) | ✔ |

Les flux de liquidation sont des échantillons, pas des rubans complets : aucun n'a d'identifiant d'événement propre dans les lignes sondées. Exhaustivité non vérifiable (dit le rapport, ✔ cohérent).

**Basis (contrats à échéance Deribit, 12 lignes)** : recalculé pour 3 lignes (BTC-30SEP26 : (84 329,79 − 84 337,71) / 84 337,71 = −0,0094 % ✔ ; BTC-25DEC26 : +1,200 % sur 86,8 j ≈ 5,05 % annualisé ✔ ; BTC-24SEP27 : +5,204 % sur 359,8 j ≈ 5,28 % ✔). Les autres valeurs de marque, index et OI (ex. BTC-30OCT26 OI 69 544 490 USD, BTC-25DEC26 311 788 310 USD) sont ✔ dans `deribit_futures`. Le nombre de jours jusqu'à l'échéance suppose une expiration à 08:00Z et un instant d'observation vers 13:00Z (**?** hypothèse de calcul non écrite dans un fichier, mais cohérente). Kraken Futures `FI_XBTUSD_261030` et `_261225` : OI 0, pas de dernier prix ✔.

**Options IV (Deribit vs OKX)** : 944 instruments Deribit, 1 272 OKX, 690 en commun ✔. Différence d'IV (points de volatilité) Deribit − OKX : médiane +0,34 (0,336 ✔), moyenne +0,67 ✔, |médiane| 0,48 (0,475 ✔), p05 −1,14 ✔, p95 +2,37 ✔. Tableau ATM : 8 expirations, différence maximale +2,37 à 1 jour (30 septembre : 26,56 contre 24,19) ✔, décroissant jusqu'à +0,15 (30 octobre) puis +0,26 (27 nov.) ✔. DVOL (indice de volatilité Deribit) : 72 lignes horaires sur 3 jours ✔. Skew (asymétrie 25Δ) non calculé (« NOT TESTED »). Remarque : la mise en commun compare des `mark_iv` (volatilités « de marque », des estimations de la plateforme), pas des prix exécutables ; le rapport 12 point 9 le dit.

**WebSocket (20 s par endpoint)** : tableau du rapport ✔ contre `ws_sample.json` (Deribit 76 messages, latence médiane 68,6 ms, p95 292,1 ; Hyperliquid 68, 300,5 / 625,8 ; Binance data-stream 627, 66,0 / 80,1 ; Bitstamp 12, 45,6 ; Kraken 39 = 17 trades + 20 heartbeats ; Coinbase 214 sans horodatage numérique lu ; Gemini 2 102 mises à jour de carnet ; BitMEX 5 ; dYdX 2 sans trade ; Bybit 1 message de contrôle ; KuCoin 0 avec erreur 502 du proxy sur une URL factice). OKX : 40 messages en 15 s, médiane 67,8 ms (`ws_okx_retry.json`) ✔ (« environ 68 »). La latence est `heure locale du conteneur − horodatage fournisseur`, sans correction de décalage d'horloge (limite déclarée).

### 3.4 Rapport 04 — FX, or, matières premières

**Instantané de l'or (2026-09-29 13:02:35Z)** — valeurs et pourcentages du rapport :

| Source | Prix | Écart vs gold-api XAU (4 152,40) | Vérification |
|---|---|---|---|
| gold-api.com XAU | 4 152,40 | — | ✔ (`fxgold_bulk.json`, `updatedAt 13:02:10Z`) |
| Swissquote XAU/USD standard | 4 152,875 / 4 153,565 | +0,01 % / +0,03 % | **? valeurs non retrouvées dans les fichiers de résultats.** Dans `fxgold_bulk.json` l'appel Swissquote a échoué (`IndexError`). La seule capture Swissquote brute (`raw/swissquote_xau.json`, horodatage 12:53:59Z) donne 4 151,325 / 4 152,015. Les valeurs 4 152,875 / 4 153,565 n'existent que dans le texte codé en dur de `catalog.py` / `gen_reports.py`. Elles viennent sans doute d'un appel manuel non enregistré. |
| Hyperliquid `xyz` GOLD (perp) | 4 153,05 | +0,02 % | ✔ (`hl_xyz_GOLD`) |
| OKX XAUT-USDT | 4 155,2 | +0,07 % | ✔ (+0,067 %) |
| Kraken XAUTUSD | 4 154,3 | +0,05 % | ✔ (+0,046 %) |
| Kraken PAXGUSD | 4 160,29 | +0,19 % | ✔ |
| Coinbase PAXG-USD | 4 161,26 | +0,21 % | ✔ |
| Deribit PAXG_USDC-PERPETUAL | 4 168,87 | +0,40 % | ✔ |
| Yahoo GC=F (future COMEX) | 4 186,6 | +0,82 % | ✔ (+0,824 %) |
| Yahoo XAUUSD=X | aucune donnée | — | ✔ (erreur `NoneType` dans `fxgold_bulk.json`) |

Lecture : « les sources de type spot se rejoignent à environ 3 bps ; l'or tokenisé (PAXG/XAUT, jetons adossés à de l'or) se paie 5 à 20 bps plus cher ; le contrat à terme ajoute environ 80 bps (contango et roll, autre instrument) ». Ce sont des instruments différents ; aucune source n'est traitée comme référence. (Note : l'instantané est un seul point, non une série ; les prix ne sont pas pris exactement à la même seconde.)

Autres faits de ce rapport :

- LBMA (fixing or AM/PM) : 14 844 lignes du 1968-01-02 au 2026-09-28 ✔ (`macro_tests.json`). Redistribution : licence IBA requise ; la citation trouvée concerne le platine/palladium, pas l'or.
- Dukascopy : fichier de ticks XAUUSD du 2024-01-02 10h décodé : 4 969 ticks ✔, premier couple ask/bid 2 077,255 / 2 076,965 ✔ ; les endpoints de bougies renvoient HTTP 429 dès les premiers appels ✔ (`dukascopy_old_candle` et `dukascopy_2026_candle_1m` = 429). Licence : non commerciale (citation).
- FX : ECB SDMX, 8 fixings récupérés, historique dès le 1999-01-04 (paramètre `updatedAfter` accepté, colonne `OBS_STATUS`) ✔. Frankfurter : 10 valeurs (09-15 à 09-28), les 8 dates communes égales à la BCE à 4 décimales ✔ (dérivé de la BCE, non indépendant). Alpha Vantage (clé de démonstration) EURUSD du 09-28 : O 1,13840 H 1,13910 L 1,13520 C 1,13700 ✔ ; Twelve Data (démo) C 1,13716 ✔ ; fixing BCE 1,1378 ✔ ; écarts de 0,6 à 0,8 pip = différences d'heure de coupure ✔ (1,1378 − 1,13700 = 0,8 pip ; 1,1378 − 1,13716 = 0,64 pip).
- **✘ « Yahoo EURUSD=X suit la BCE à environ 10 pips sur les dates communes »** : sur les 5 dates portant la même étiquette dans les deux séries (09-17, 09-21, 09-22, 09-23, 09-24), l'écart va de 5 à **29 pips** (09-21 : 25 pips ; 09-23 : 29 pips). De plus, Yahoo étiquette des dimanches (09-20, 09-27), signe d'un décalage de fuseau dans les dates. La clôture du 2026-09-28 est bien `null` ✔.
- Intraday FX sans clé : seulement Yahoo (non officiel, 429 vu) et ticks Dukascopy (non commerciaux) ✔ cohérent avec les sondes.
- Matières premières via Yahoo : CL=F, BZ=F, HG=F, SI=F, DX-Y.NYB : 106 barres horaires sur 5 jours chacune ✔ ; NG=F : 429 ✔ ; GC=F : 534 barres 1 min, 0 clôture nulle ✔. CFTC COT (positionnement hebdomadaire) : GOLD-COMEX OI 412 800 au 2026-09-22 ✔, PAX GOLD PERP STYLE OI 1 310 ✔, historique dès 1986-01-15 ✔. World Bank Pink Sheet : XLSX de 765 Ko téléchargé (765 246 octets dans `sweep2.json`) ✔. EIA : HTTP 403 (clé requise) ✔.
- **Omission :** le rapport conclut « aucun flux intraday officiel d'énergie ou de métaux de base sans clé » et ne cite que ALUMINIUM parmi les perps de matières premières d'Hyperliquid. La capture `raw/hl_xyz_gold.json` liste aussi `xyz:CL` (90,628), `xyz:BRENTOIL` (96,2175) et `xyz:COPPER` (6,6151). Ce ne sont pas des sources « officielles » (risque de plateforme/instrument), mais l'inventaire est incomplet par rapport à ce que la capture contenait.

### 3.5 Rapport 05 — Macro et calendrier

| Source | Résultat du rapport | Vérification |
|---|---|---|
| FRED API | atteignable (HTTP 400 « api_key not registered ») ; `fredgraph.csv`, ALFRED, hôtes web : connexion coupée par le proxy | ✔ (`macro_tests.json` : erreurs `ProxyError … RemoteDisconnected` pour 4 URL, HTTP 400 pour l'API) — le rapport dit « 5 tentatives » : 4 URL en échec de connexion + 1 HTTP 400 dans le second script, plus 4 timeouts dans `sweep2.json` ✔ cohérent |
| ALFRED | injoignable ; vintages non testés | ✔ |
| Trésor US (courbe de taux CSV) | « 24 lignes pour 2026 YTD, 35 pour 1990 — inexpliqué » | ✔ 24 et 35, **mais** le fichier couvre uniquement du 08/25/2026 au 09/28/2026 (pas l'année depuis janvier) : l'étiquette « YTD » est trompeuse ; la pagination reste non investiguée |
| Trésor FiscalData | 200, plus ancien 2001-01-31 | non revérifié (**?**) |
| NY Fed SOFR | 200 ; 2026-09-28 = 3,90 ; recherche jusqu'à 2018-04-03 (1,75) | ✔ ; `revisionIndicator` présent mais vide ✔ |
| ECB SDMX | 200 ; `updatedAfter` accepté | ✔ (8 lignes retournées avec `updatedAfter=2026-09-01`) |
| Eurostat HICP | 200 ; `updated` 2026-02-06 | ✔ (`2026-02-06T23:00:00+0100`) ; valeurs 2,1 / 2,1 / 2,0 pour 2025-10 à 2025-12 |
| BLS API | v1 sans clé : première sonde `REQUEST_NOT_PROCESSED`, plus tard `REQUEST_SUCCEEDED` ; v2 sans clé : message de seuil | ✔ (`raw/bls_api_v1.json` = NOT_PROCESSED à 12:55:29 ; `macro_tests.json` : v1 SUCCEEDED, v2 sans clé NOT_PROCESSED). Le message parle d'un « registration key » alors qu'aucune clé n'était fournie : comportement curieux du service |
| Banque du Canada, BoE, CFTC, World Bank, SNB | 200 | ✔ (World Bank `lastupdated 2026-07-13` ✔) |
| EIA / BEA | clé requise | ✔ (EIA 403) |
| IMF / OECD | IMF 403 ; OECD requête mal formée | ✔ |

**Calendrier économique** : Faireconomy/ForexFactory JSON : 141 événements, 9 devises, impacts High/Medium/Low/Holiday, champs `title, country, date, impact, forecast, previous`, **aucun champ `actual` (0/141)**, fichiers `nextweek`/`lastweek` en 404, deux récupérations à 2 s d'intervalle identiques ✔ (tous confirmés dans `macro_tests.json`). Trading Economics : clé « guest » supprimée (HTTP 410) ✔. Fear & Greed alternative.me : 3 159 lignes quotidiennes ✔.

**Énoncé de lacune** : « les sources officielles sans clé donnent la date d'observation mais rarement l'instant où la valeur est devenue publique » — c'est le point le plus important pour un système PIT et il est bien mis en avant.

### 3.6 Rapport 06 — Tests d'exécution

- Sondes de découverte : 119 ; 90 en 200 ; 29 en échec ✔ (liste complète des 29 dans `sweep1/2.json` : codes 401, 403, 405, 410, 429/451, ou erreurs de connexion).
- **Latence (10 appels séquentiels)** — tableau du rapport entièrement ✔ contre `latency_ratelimit.json` : par exemple OKX médiane 666,1 ms (p90 690,7 ; max 716,3), Kraken 590,8, Coinbase 509,6, Bitstamp 644,8 (max 1 351,5), Deribit 613,8, Hyperliquid 724,8, KuCoin 707,5 (max 1 912,8), Gate 1 297,3, Bitget 710,3, dYdX 562,7, Binance data-api 1 180,3 (max 2 124,2), Frankfurter 508,8, ECB 905,4, NY Fed 677,8. **Ces latences incluent le proxy et ne représentent pas un client colocalisé** (le rapport le dit).
- **« Rafales »** : OKX 20 appels demandés en 4 s → réalisés en 13,59 s ; Coinbase 8 en 2 s → 4,02 s ; Deribit 20 en 4 s → 11,26 s ; tous en 200 ✔. Conclusion honnête : « c'est le point d'accès, pas le fournisseur, qui a limité le débit ; aucune 429 provoquée ». L'application des limites n'a été observée que passivement (Dukascopy 429, Yahoo 429, BLS, géo-blocages).
- En-têtes de limite de débit essentiellement absents (seulement `Date`/`Server`) ✔ (`hdr` ne contient que `Date` et `Server` dans les rafales).
- Non mesuré : récupération après 429/Retry-After, stabilité sur des heures, reconnexion WebSocket et trous de séquence, dérive tardive, latence corrigée du décalage d'horloge ✔ (déclaré).

### 3.7 Rapport 08 — Préparation PIT

Répartition (✔ recalculée depuis `catalog.py`) :

| Classe | Toutes | Exécutées |
|---|---|---|
| PIT_NATIVE | 1 | 0 |
| PIT_ADAPTABLE | 34 | 30 |
| PIT_WEAK | 30 | 13 |
| PIT_UNSUITABLE | 3 | 3 |

Signaux réellement observés (extraits du rapport) : horodatage d'événement partout sauf gold-api et open.er-api ; **horodatage serveur de réception : seulement Deribit** (`usIn` = 1790686334589959, `usOut` = 1790686334590220 dans `raw/deribit_ticker_perp.json` ✔) ; identifiants d'événement : trade_id Deribit/Coinbase/Binance/Hyperliquid, hauteur de bloc dYdX ; signal de révision : NY Fed `revisionIndicator`, ECB `OBS_STATUS`/`updatedAfter`, Eurostat `updated`, BLS footnotes ; finalité : drapeau `confirm` OKX, drapeau de clôture Gate, fichiers immuables Binance Vision (avec CHECKSUM, ETag, Last-Modified) ; distinction backfill/direct : seulement Binance Vision.

Cinq constats clés du rapport : (1) aucune source PIT native exécutée (ALFRED reste DOCUMENTED_CLAIM) ; (2) les API de bougies/funding/OI permettent de re-télécharger la même clé sans métadonnée d'ingestion : le consommateur doit tamponner lui-même l'heure de réception ; (3) finalité signalée seulement par OKX et Gate, sinon à inférer (`ouverture + 60 s < réception`) ; (4) backfills séparables seulement avec Binance Vision (bon usage : Binance Vision pour l'historique, API pour le bord récent, avec règle de jonction testée : 1 440/1 440 identiques pour 2026-09-26) ; (5) dérive d'unité de timestamp, ordre des colonnes et bougie en formation non signalée sont des pièges PIT.

### 3.8 Rapport 09 — Licences et coûts

Classes de coût : FREE_UNAUTHENTICATED 43, UNKNOWN 17, PAID_ONLY 1, FREE_TIER 3, FREE_WITH_ACCOUNT 4 ✔ (`counts.json`). Exécutées : 43 sans clé + 3 avec clé de démonstration.

Faits marquants (DOCUMENTED_CLAIM, tirés de citations officielles condensées) :

- **Restrictif** : Dukascopy (non commercial, pas de revente), Twelve Data gratuit (« personnel, interne, non commercial »), Finnhub (pas de redistribution des données ni des résultats dérivés), open.er-api (attribution, pas de redistribution), Yahoo (conditions développeur interdisant revente/sous-licence), Bitstamp (usage commercial : contacter le fournisseur), LBMA/IBA (licence pour redistribuer), FRED (séries de tiers potentiellement protégées ; mention obligatoire).
- **Permissif avec attribution** : World Bank (CC BY 4.0), CoinGecko (attribution « Powered by CoinGecko »), alternative.me (commercial autorisé avec attribution), BCE (citer la source), Banque du Canada (usage libre sous conditions), NY Fed (« intention de permettre l'utilisation et le partage »), Eurostat (réutilisation avec attribution).
- **Type domaine public** : Trésor US FiscalData (« sans restriction »), EIA (publications du gouvernement US), BLS (« pas de contrôles sur l'usage final »).
- **Aucun texte de licence retrouvé (UNKNOWN)** pour : OKX, Kraken, Coinbase, KuCoin, Gemini, Gate, Bitget, HTX, Deribit, BitMEX, Hyperliquid, miroir Binance/Vision, Swissquote, Faireconomy, Frankfurter (délègue), CFTC, BoE. Beaucoup de pages étaient rendues en JavaScript ou en 403. **Une lecture manuelle des CGU est nécessaire avant toute décision de stockage/redistribution.**

Contradiction interne (**✘**) : `09_LICENSE_AND_COST.md` parle de « verbatim short quote », mais `docs_facts.json → _meta` indique « quotes may be lightly condensed or paraphrased where marked; long quotes joined from adjacent sentences », et `12_LIMITATIONS.md` point 7 l'admet (« condensed or spliced »). Les citations ne sont donc pas garanties textuelles.

Détail : la catégorie « `NOT_FOUND` » pour 17 sources exécutées avec succès (OKX, Kraken, Coinbase…) signifie que l'absence de texte est plus une limite du procédé de recherche automatique (pages JS/403) que de l'absence de licence.

### 3.9 Rapport 10 — Matrice de résilience

Reprise de la matrice (rôle → sources) :

| Classe de manque | PRIMARY | SECONDARY | FALLBACK | CORROBORATION_ONLY | HISTORICAL_ONLY |
|---|---|---|---|---|---|
| Bougies crypto spot | OKX, Kraken, Coinbase, Binance data-api.binance.vision | Gate.io | — | Bitstamp, KuCoin, Gemini, Bitget, MEXC, HTX, CoinGecko | Binance Vision bulk |
| Funding | OKX | Deribit, Hyperliquid | Kraken Futures, Gate.io | KuCoin, Bitget | Binance Vision bulk |
| Open interest | OKX | Deribit, Hyperliquid | Gate.io | Kraken Futures, Bitget | Binance Vision bulk |
| Liquidations | — | OKX | Gate.io | Bitfinex | — |
| Basis | Deribit | OKX | — | — | Binance Vision bulk |
| Options IV/skew | Deribit | OKX | — | — | — |
| FX | BCE | — | Frankfurter, Alpha Vantage | BoE, BoC, Yahoo | Dukascopy |
| Or / métaux | — | Paires d'or tokenisé | — | Coinbase, Yahoo, gold-api, Swissquote | Dukascopy, LBMA |
| Matières premières | CFTC COT | — | — | Yahoo | World Bank Pink Sheet |
| Macro | NY Fed | BLS, courbe Trésor, Eurostat | — | — | — |
| Calendrier/actualités | — | — | Faireconomy/ForexFactory | Fed FOMC (page) | — |

18 sources exécutées détiennent au moins un rôle PRIMARY/SECONDARY/FALLBACK ✔ (recalculé). Le texte d'interprétation du rapport :

- **10 plateformes crypto spot** avec un écart médian absolu ≤ 1,32 bps par rapport au consensus de leur groupe ✔ (0,43 ; 0,62 ; 0,70 ; 0,88 ; 0,44 ; 0,76 ; 0,37 ; 0,87 ; 1,32 ; 0,51).
- « Substituer une plateforme à une autre change la série » (0 correspondance exacte) — point crucial : ce sont des *plateformes* indépendantes, pas des copies.
- Dérivés : OKX + Deribit + Hyperliquid + Gate donnent au moins 3 flux indépendants ; options : exactement 2 fournisseurs sans clé (Deribit, OKX).
- FX/or/macro/calendrier : redondance mince et surtout quotidienne ; Frankfurter est dérivé de la BCE (donc pas un secours indépendant).
- Notes de défaillance corrélée (INFERENCE) : plusieurs sources derrière Cloudflare ; Coinbase PAXG et le perp PAXG de Deribit partagent le même jeton sous-jacent.

---

## 4. Candidats évalués un par un

Rappel : les verdicts sont saisis à la main dans `catalog.py` ; je restitue chaque verdict, son fondement chiffré, puis les conditions qui pourraient le faire changer (mes formulations sont des pistes, pas des affirmations du rapport).

### 4.1 ADOPT_REFERENCE (8) — « référence pour la recherche future », rien d'intégré

| Source | Fondement chiffré | Condition de changement (mon avis) |
|---|---|---|
| OKX v5 public | Seule plateforme avec spot + funding + OI + liquidations + options + basis sans clé ; écart abs. médian 0,44 bps ; drapeau `confirm` de clôture ; 0 révision. Risque : endpoint REST de liquidation **absent de la doc actuelle** ; WebSocket :8443 réinitialisé (443 OK) ; licence NOT_FOUND | Retrait de l'endpoint non documenté, preuve de licence restrictive, ou révisions observées sur de longues durées |
| Kraken spot REST/WS | USD ; écart abs. médian 0,43 bps ; **bougie en formation non signalée** (constatée : 12:57 modifiée entre t0 et t2) ; 720 lignes max par appel | Il faut un filtre de bougie fermée ; une preuve de fuite non filtrable changerait le verdict |
| Coinbase Exchange public | USD ; 0,62 bps ; 300 bougies/appel ; **ordre de colonnes différent** ; PAXG-USD comme proxy or | Idem ; licence NOT_FOUND |
| Binance data-api.binance.vision (miroir) | 0,51 bps ; 1 440/1 440 identique au fichier de masse ; WS 627 messages/20 s. L'API principale répond 451 ici | Le miroir est « market data only » ; sa licence est NOT_FOUND ; un changement de politique du miroir suffit |
| Binance Vision bulk | Somme de contrôle vérifiée ; métadonnées de fichier ; OI 5 min, funding, premium index ; `liquidationSnapshot` et `bookTicker` en 404 ; **unité de temps qui change** | Découverte d'une correction rétroactive des fichiers, ou d'un changement de licence |
| Deribit public v2 | Seule source sans clé avec toute la surface d'options BTC (944 instruments) + DVOL ; seul à fournir `usIn/usOut` ; OI en USD | Licence NOT_FOUND ; dépendance à un seul fournisseur pour les options |
| ECB Data Portal (SDMX) | Fixing quotidien depuis 1999 ; `OBS_STATUS`, `updatedAfter` ; citation de licence permissive (citer la BCE) | C'est un taux de référence (14:15 CET), pas un prix négociable |
| NY Fed Markets (SOFR) | `revisionIndicator` (vide dans l'échantillon) ; historique dès 2018 ; permission de partage | Aucune révision observée : le signal n'est pas prouvé en action |

### 4.2 ADAPT_CANDIDATE (22)

Chacun avec son motif (`11_ADJUDICATION.md`, ✔ conformes à `catalog.py`) :

Alpha Vantage démo (25 requêtes/jour, EURUSD 1,13700) · BLS API (quota partagé imprévisible) · Banque du Canada (usage libre sous attribution) · Banque d'Angleterre IADB (GBP/USD 16 h ; XUDLERS = EUR par GBP, pas EURUSD) · **Bitfinex** (niveau +13 bps inexpliqué, « ne pas utiliser pour un travail sensible au niveau » ; l'historique de liquidations est utile) · **Bitget** (« 1 minute manquante » : **artefact**, voir §3.2 ; funding figé à 0,0001) · Bitstamp (usage commercial → contacter le fournisseur) · CFTC COT (positionnement, pas prix ; pas d'heure de publication) · Dukascopy (non commercial, décodeur nécessaire, 20 s de téléchargement) · Eurostat (horodatage de mise à jour au niveau du jeu) · Faireconomy (planning + prévu/précédent, pas de valeurs publiées) · Frankfurter (identique à la BCE) · Gate.io (meilleure corrélation USDT, 0,988 ; OI en contrats à multiplicateur 0,0001 : **piège d'unité**) · Hyperliquid (OI en BTC, funding + prime en un appel ; dex `xyz` de matières premières/actions) · Kraken Futures (contrats à échéance : OI 0, pas de dernier prix) · KuCoin (funding différent des autres) · LBMA (licence IBA) · Paires d'or tokenisé (jeton ≠ or spot : +0,05 % à +0,40 %) · Courbe des taux du Trésor (nombre de lignes anormal) · World Bank (CC BY 4.0) · Yahoo (429, XAUUSD=X vide, CGU restrictives) · alternative.me Fear & Greed (commercial avec attribution).

Observation : le verdict ADAPT est appliqué à des sources aux profils très différents (par exemple Bitfinex avec un écart de 13 bps et Gate avec 0,37 bps). Il signifie « candidat sous conditions » et ne classe rien.

### 4.3 REJECT (1)

**Trading Economics API** : « abonnement payant requis » (HTTP 410 sur la clé « guest » ✔). Non exécuté. Le rejet est fondé sur le coût, pas sur la qualité des données.

### 4.4 PARK (37) — preuve insuffisante, bloqué, mince ou restreint

Regroupés par raison :

- **Trop mince ou peu informatif (exécutés)** : Binance.US (112/240 volume nul ; corr. 0,592), dYdX (150/240 volume nul ; corr. 0,428), Gemini (16 volume nul, 23 plates ; corr. 0,787), HTX (−4,54 bps ; 8 plates), MEXC (pas de facts docs), BitMEX (XBTUSD réglé/clôturé le 2026-09-16, liquidation REST vide).
- **Restreint ou hors périmètre** : open.er-api (attribution, pas de redistribution), fawazahmed0 (licence NOT_FOUND), gold-api (instantané seul), Swissquote (endpoint non documenté), Twelve Data (non commercial), CoinGecko (agrégé, barres de 30 min ; attribution ; le connecteur MCP CoinGecko a échoué à se connecter dans cette session), page FOMC de la Fed (scraping seulement, non analysée), mempool.space/blockchain.info (hors périmètre), SNB (joignable seulement), FiscalData (basse fréquence).
- **Bloqués par le point d'accès de test (non jugés)** : Binance principal (451), Bybit (403), FRED/ALFRED, Stooq, GDELT, IMF, BLS ICS, goldprice.org/metals.live, CryptoPanic.
- **Non exécutés (clé/compte)** : BEA, CryptoCompare/CoinDesk, Coinalyze, EIA, FMP, Finnhub, OANDA, Polygon, exchangerate.host, OECD (requête mal formée par la lane), TipRanks (volontairement non exécuté pour préserver un quota de compte).
- Parmi eux, deux sont signalés comme prioritaires : **FRED/ALFRED** (« suivi de plus haute priorité », seule piste PIT native) et **Coinalyze** (« candidat non testé de plus haute pertinence », agrégateur d'OI/funding/liquidations).

Règle de lecture : PARK pour « bloqué » n'est **pas** un verdict négatif (`claude.md` : « missing evidence is not negative evidence »).

---

## 5. Bloc final complet (reproduit tel quel) et explication ligne par ligne

```
SOURCES_DISCOVERED=68
SOURCES_EXECUTED=46 (data path executed, HTTP 200 and parsed); 1 reachable-but-data-path-not-completed (FRED); 9 blocked from the test egress; 12 not executed (key/account/own error/deliberate)
FREE_PUBLIC_SOURCES=43 classified FREE_UNAUTHENTICATED (43 of them executed)
FREE_ACCOUNT_SOURCES=4 classified FREE_WITH_ACCOUNT (0 executed with an account; +3 FREE_TIER executed with a shared demo key; 17 UNKNOWN; 1 PAID_ONLY)

CRYPTO_SPOT_CANDIDATES=11
DERIVATIVES_CANDIDATES=9
FX_CANDIDATES=7
COMMODITY_CANDIDATES=9 (incl. gold proxies; strictly energy/base-metal price feeds: 1, Yahoo unofficial - see 04)
MACRO_CANDIDATES=9

PIT_NATIVE_COUNT=0 observed (+1 DOCUMENTED_CLAIM only: ALFRED, execution blocked)
PIT_ADAPTABLE_COUNT=34 classified (30 executed)

FALLBACK_CAPABLE_COUNT=18 (executed sources holding a PRIMARY/SECONDARY/FALLBACK role in at least one gap class)

ANY_DROP_IN_SOURCE=NO
ANY_SCIENTIFIC_INVALIDATION=NO

FINAL_VERDICT=MULTIPLE_DATA_SOURCE_CANDIDATES_SUPPORTED
```
(`bench/data_feeds_v1/results/final_block.txt`, identique au bloc de `00_EXECUTIVE_SUMMARY.md` ✔ et régénéré à l'identique par `gen_reports.py`.)

| Clé | Explication simple | Vérification |
|---|---|---|
| `SOURCES_DISCOVERED=68` | 68 sources ont été inventoriées dans le catalogue. | ✔ |
| `SOURCES_EXECUTED=46` | 46 ont répondu en HTTP 200 et leurs données ont été lues ; 1 (FRED) est joignable mais les données n'ont pas été lues ; 9 ont été bloquées par le réseau de test (pas un jugement sur la source) ; 12 n'ont pas été exécutées (clé requise, erreur de la lane, choix). | ✔ 46+1+9+12=68 |
| `FREE_PUBLIC_SOURCES=43` | 43 sources sont classées « gratuites sans authentification » et ces 43 ont toutes été exécutées. | ✔ |
| `FREE_ACCOUNT_SOURCES=4` | 4 sont « gratuites avec compte » ; aucune n'a été exécutée avec un compte ; 3 « niveau gratuit » ont été exécutées avec une clé de démonstration partagée ; 17 sont de coût inconnu ; 1 payante. | ✔ |
| `CRYPTO_SPOT_CANDIDATES=11` | 11 sources exécutées avec verdict ADOPT ou ADAPT pour le spot crypto. | ✔ liste dans `counts.json` |
| `DERIVATIVES_CANDIDATES=9` | 9 pour les dérivés (funding, OI, liquidations, options, basis). | ✔ |
| `FX_CANDIDATES=7` | 7 pour les devises. | ✔ |
| `COMMODITY_CANDIDATES=9` | 9 pour matières premières y compris or ; mais seule 1 source (Yahoo, non officielle) couvre strictement l'énergie/les métaux de base. | ✔ (avec l'omission Hyperliquid xyz notée §3.4) |
| `MACRO_CANDIDATES=9` | 9 pour la macro. | ✔ |
| `PIT_NATIVE_COUNT=0 observed` | Aucune source exécutée n'offre nativement des « vintages ». ALFRED est la seule qui le prétend, mais sur documentation seulement. | ✔ |
| `PIT_ADAPTABLE_COUNT=34 (30 executed)` | 34 sources permettraient de bâtir du PIT avec ses propres horodatages de réception ; 30 ont été exécutées. | ✔ |
| `FALLBACK_CAPABLE_COUNT=18` | 18 sources exécutées ont au moins un rôle principal/secondaire/secours. | ✔ |
| `ANY_DROP_IN_SOURCE=NO` | Aucune n'est « prête à l'emploi » selon la définition stricte. | ✔ cohérent avec la définition ; mais la définition exige une licence permissive documentée, ce qui n'est vrai pour aucun exchange dans les fichiers |
| `ANY_SCIENTIFIC_INVALIDATION=NO` | Rien n'a réfuté une hypothèse de la mission. | Vide de sens, car aucune hypothèse chiffrée n'est énoncée (§7) |
| `FINAL_VERDICT=MULTIPLE_DATA_SOURCE_CANDIDATES_SUPPORTED` | Plusieurs sources candidates sont soutenues par les observations. | Descriptif |

Remarque : les nombres de candidats par classe ne sont pas des comptages disjoints (une même source, comme Hyperliquid ou Yahoo, est comptée dans plusieurs classes) ; le rapport le présente comme des listes par classe (✔ `counts.json`).

---

## 6. Contrôles de validité

### 6.1 Ce que la lane a contrôlé (ou déclare avoir contrôlé)

| Contrôle | Résultat | Statut |
|---|---|---|
| Doublons de minutes | 0 pour les 17 séries | ✔ |
| Alignement sur la minute (`t % 60 000 = 0`) | vrai partout | ✔ (`aligned_60s` dans le code ; conclusion reprise dans le rapport) |
| Décalage d'horodatage (test de corrélation avec décalage −3…+3 min) | Meilleur décalage = 0 pour les 17 séries | ✔ (`lag_test_vs_kraken.json`) |
| Révisions sur t0→t2 | 0 sur 17 séries | ✔ ; t0→t1 (78 s) : 0 aussi ✔ (`bars_analysis.json`) |
| Bougie fermée < 60 s avant t0 | identique à t2 | ✔ (11 plateformes) |
| Empreinte SHA-256 Binance Vision | correspond | ✔ PROVEN |
| Égalité API/fichier de masse | 1 440/1 440 | ✔ résultat ; code du correctif absent |
| Lecture double du calendrier | octets identiques à 2 s d'écart | ✔ |
| Reproductibilité du traitement hors ligne | Rejouer `analyze_bars.py t2`, `consensus.py`, `lagtest.py` sur les captures fournies produit des fichiers identiques octet pour octet ; `gen_reports.py` régénère les 13 rapports, `final_block.txt` et `counts.json` à l'identique | ✔ (contrôle fait pour cette analyse, dans un répertoire temporaire, sans toucher au dépôt) |

### 6.2 Tests de fuite / lookahead

Il n'y a **pas de test de fuite au sens strict** (l'étude ne teste pas une stratégie). La question PIT est traitée par classification (rapport 08). Le seul risque de lookahead effectivement observé est la **bougie en formation renvoyée sans drapeau par Kraken** (ligne 12:57 modifiée entre t0 et t2 : bas, clôture, volume). Cette observation est faite ici ; le rapport la mentionne comme risque, pas comme mesure.

### 6.3 Contrôles négatifs / positifs

- Négatif implicite : BitMEX XBTUSD renvoie 0 ligne car l'instrument est réglé ✔ (détecté et expliqué).
- Aucun contrôle négatif formel (par exemple injecter une révision artificielle pour vérifier que le détecteur la voit) et aucun contrôle positif formel (la détection de révision n'a jamais été testée sur un cas connu) — le « 0 révision » est donc une absence de signal, avec un détecteur non validé, sur un horizon de 6 minutes.
- Le seul cas où un changement existe (la ligne en formation de Kraken) est hors de la fenêtre analysée par `analyze_bars.py`, donc le script ne l'aurait pas signalé.

### 6.4 Erreurs corrigées en cours de route / écarts déclarés

- Correctif d'unité Binance Vision (ms vs µs) : `binance_vision_fix.json` (script non fourni).
- Fichiers > 400 Ko tronqués puis supprimés (Deribit/OKX option summaries, Kraken Futures funding, LBMA, SNB, Pink Sheet) : les statistiques viennent des réponses complètes en direct, mais ces corps bruts ne sont pas archivés (`12_LIMITATIONS.md` point 8). Le README indique que « large bodies >400 KB removed ». Conséquence : les chiffres des options (944/1272/690, médiane 0,34) ne peuvent pas être recalculés depuis le dépôt (les résultats agrégés sont fournis).
- Requête OECD malformée « par moi » (rapport 12 point 3) : signalée.
- Autres écarts au protocole : aucun protocole écrit.

---

## 7. Critique indépendante

### 7.1 Écarts entre rapports et résultats bruts (résumé)

| # | Affirmation du rapport | Ce que montrent les fichiers | Gravité |
|---|---|---|---|
| 1 | Bitget : minute 09:02Z absente « dans les deux récupérations » ; 239/240 ; 16/17 sans trou | Aucune minute interne manquante dans `bars_t0/t1/t2.json`. La minute comptée manquante est **la première minute demandée** de chaque fenêtre (08:55 en t0, 08:57 en t1, 09:02 en t2). 09:02 est simplement le début de la fenêtre t2. Artefact de bornes de requête. | **Moyenne** : c'est le seul « vrai trou » du rapport, repris dans le verdict Bitget et l'exécutif |
| 2 | Hyperliquid Σ8 h (colonne du tableau de funding) | Somme de 9 lignes horaires (gigue de 59 ms) au lieu de 8 → surévalué de 12,5 % (1,13 au lieu de 1,00 bps au taux de base) | Faible à moyenne (colonne à ne pas utiliser en valeur) |
| 3 | Bitget « 1,00 bps dans 3 des 4 dernières lignes » | 4 sur 4 | Faible |
| 4 | « ret. corr vs consensus » (catalog, 01, 11) | Ce sont des corrélations **vs Kraken** ; celle de Kraken (1,000) est triviale | Faible (étiquette) |
| 5 | Yahoo EURUSD « environ 10 pips de la BCE » | 5 à 29 pips sur 5 dates communes ; étiquettes de dimanche | Faible |
| 6 | USD vs USDT « 3–5 bps » (« 3–4,7 » en synthèse) | 1,81 à 4,08 bps hors Bitfinex/HTX (jusqu'à 5,20 avec HTX) | Faible |
| 7 | Swissquote 4 152,875/4 153,565 à 13:02Z | Non retrouvé ; la capture brute donne 4 151,325/4 152,015 à 12:53:59Z | Faible (non vérifiable) |
| 8 | Binance Vision `metrics` « 289 lignes/jour » | 289 lignes en-tête incluse = 288 données | Cosmétique |
| 9 | Unité ms→µs « entre 2024-12 et 2025-01 » | Fichiers non capturés ; seuls 2017 (ms) et 2026 (µs) le sont | Non vérifiable |
| 10 | Courbe Trésor « 2026 YTD » = 24 lignes | Le fichier couvre 08/25→09/28/2026 uniquement | Faible (libellé) |
| 11 | Fenêtre unique « se terminant 12:55Z » | Le tableau mélange les compteurs de t0 (jusqu'à 12:55Z) et les écarts de consensus de t2 (jusqu'à 13:02Z) | Faible |
| 12 | Citations « verbatim » | `_meta` du fichier dit « lightly condensed or paraphrased » | Faible à moyenne (pour les décisions de licence) |
| 13 | Énergie/métaux : un seul flux (Yahoo) | La capture `hl_xyz_gold.json` liste aussi CL, BRENTOIL, COPPER | Faible (inventaire incomplet) |

Bonne nouvelle : les tableaux des rapports sont **produits par code** à partir des résultats (`gen_reports.py` les régénère à l'identique) ; les chiffres vérifiés dans ces tableaux sont exacts. Les écarts ci-dessus viennent surtout du **texte d'interprétation codé en dur** dans `gen_reports.py` et `catalog.py`.

### 7.2 Points faibles méthodologiques

1. **Un seul instant, un seul point d'accès, un seul actif.** Tout vient de ~25 minutes d'exécution un mardi, depuis un conteneur cloud derrière un proxy. Aucune donnée de week-end, de nuit, de maintenance, ni de volatilité extrême. Les comparaisons de bougies portent sur 240 minutes de BTC, un actif très liquide ; on ne peut pas en extrapoler aux autres actifs ni aux jours agités.
2. **Détecteur de révisions non validé et horizon de 6 minutes.** « 0 révision » sur 6 minutes de bougies fermées de BTC ne dit presque rien sur les corrections tardives (jours), les données de funding/OI/macro, ni sur les reconstitutions historiques. La lane le reconnaît (§12), mais l'en-tête du rapport 00 affiche encore « 0 revisions » en tête des constats.
3. **Test d'égalité exacte trop facile à échouer.** Trouver « 0 égalité OHLC exacte » entre des places de marché différentes est la conséquence attendue du fait qu'elles ont des trades différents ; c'est un constat correct, mais peu informatif. Il aurait fallu aussi une mesure tolérante (part de bougies à moins de X bps sur les 4 champs).
4. **Le « consensus » est circulaire et sensible à sa composition.** La médiane des « autres » du groupe est utilisée pour juger chaque membre ; dans le groupe USD elle inclut Bitfinex (+13 bps) et Gemini (mince). C'est robuste à un aberrant, mais cela suppose que la majorité a raison. Bitfinex à +13 bps est donc désigné aberrant par construction ; la cause (par exemple une différence de cotation en USD ou un autre mécanisme) est inconnue et non investiguée.
5. **Verdicts et classes PIT saisis à la main, définitions appliquées de façon inégale.** Exemple : selon la définition, PIT_ADAPTABLE exige un identifiant, un drapeau de finalité, un indicateur de révision, un horodatage de réception ou des métadonnées de fichier immuable. Or le rapport 08 écrit lui-même que les endpoints de bougies n'ont ni identifiant (« candle endpoints (no IDs) ») ni drapeau de finalité (sauf OKX et Gate). Coinbase, Bitstamp, KuCoin, MEXC, HTX, Bitfinex et Kraken sont pourtant classés PIT_ADAPTABLE, tandis que Gemini (aussi sans ID ni finalité) est PIT_WEAK. La colonne « Why » du tableau 08 est un texte identique pour toutes les sources d'une classe. La classification se justifie par des capacités *d'autres endpoints* (WebSocket, trade_id) sans que le rapport précise quel endpoint est visé.
6. **`ADOPT_REFERENCE` avec licence inconnue.** OKX, Kraken, Coinbase, Binance (miroir et Vision), Deribit sont « référence » alors que leur licence est `NOT_FOUND`. La définition « drop-in » les exclut bien, mais le mot « ADOPT » pourrait être lu trop vite. Le rapport 09 lui-même exige une lecture manuelle des CGU avant tout stockage ou redistribution.
7. **Qualité de « exécutée » inégale.** « Exécutée » signifie HTTP 200 + analyse ; pour de nombreuses sources (SNB, FiscalData, page FOMC) le rapport dit « joignable seulement / non analysée ». Le décompte de 46 « exécutées » inclut donc des sources dont les données n'ont pas été évaluées.
8. **Limites de débit uniquement documentaires.** Les limites viennent de citations ; aucune n'a été mesurée sur un exchange (le point d'accès à ~1,5 req/s empêchait toute rafale utile). La gestion des erreurs 429 et du Retry-After (comportement d'un client résilient) n'est pas testée : c'est pourtant central pour une étude de « résilience ».
9. **La résilience n'a pas été testée comme telle.** Aucun scénario de panne simulée (bascule primaire→secours, écart au moment de la bascule, rattrapage de trous). La « matrice de résilience » est un inventaire de capacités déduit de mesures ponctuelles, pas le résultat d'un test de bascule. Le rapport le dit (« no automatic failover design is proposed »).
10. **Prix d'illustration codé en dur** (84 340 USD) pour convertir l'OI ; sans conséquence sur les conclusions, mais signalé.
11. **Choix en bord de grille** : la fenêtre de 240 minutes, le seuil de 30 minutes communes par paire, les 10 appels de latence, les 20 s de WebSocket sont des choix ronds, non justifiés ; aucune analyse de sensibilité n'a été faite (par exemple 60 vs 240 vs 1 440 minutes). Les écarts entre t1 et t2 sont cependant très petits (≤ 0,17 bps sur les médianes de paires, ✔), ce qui rassure sur la stabilité *à court terme*.
12. **Hypothèses fragiles** : (a) l'égalité de sens des timestamps (heure d'ouverture) est démontrée seulement à la minute près (résolution du test) ; (b) `USDT ≈ USD` implicite dans les comparaisons de groupes ; (c) l'or tokenisé comme proxy de l'or spot ; (d) le mapping positionnel Bitfinex `status/deriv` (inférence) ; (e) l'unité de l'OI Kraken Futures et dYdX (non vérifiée).
13. **Contradiction interne mineure** : le résumé annonce « 46 exécutées » et « 43 sans clé toutes exécutées » ; parmi elles, 16 sont finalement PARK (§4.4). Ce n'est pas une erreur, mais « exécutée » ne veut pas dire « soutenue ».
14. **Biais de sélection possibles** : les 68 sources ont été choisies par l'analyste (connaissance préalable, ce qui est joignable depuis le conteneur). Les blocages géographiques (Binance, Bybit) retirent précisément des sources parmi les plus utilisées ; le résultat « plusieurs candidats » est donc probablement *conservateur* pour les dérivés crypto, mais optimiste pour la licence (non vérifiée).

### 7.3 Ce que les chiffres NE prouvent PAS

- Qu'une source est *fiable dans la durée* (disponibilité, pannes, changements d'API) : non testé.
- Qu'une source est *légalement utilisable* pour stocker, redistribuer ou dériver : non établi ; 17 sources en coût UNKNOWN, la plupart des exchanges sans licence retrouvée.
- Qu'un flux est *exempt de lookahead* : le protocole ne fait pas ce test ; il liste des indices.
- Que le remplacement d'une source par une autre est *neutre* : au contraire, les écarts de 0,3 à 13 bps et l'absence de bougies identiques montrent que la bascule change la série.
- Que les 4 « références » sont *meilleures* que les autres : le classement de rôles n'est pas issu d'un score (assumé par le rapport).
- Que les options/funding d'une plateforme représentent « le marché » : chaque plateforme n'a que ses propres traders.
- Que les prix observés (BTC 84 k, or 4,15 k) sont vrais : non validés hors fournisseurs.

---

## 8. Comparaison de plusieurs runs / branches

La lane n'a qu'une seule branche de contenu et un seul commit. Il n'y a pas de deuxième run indépendant. Deux comparaisons internes existent toutefois :

| Comparaison | Résultat |
|---|---|
| t0 vs t1 (+78 s) et t0 vs t2 (+362 s) | 0 révision dans les deux cas ; les écarts médians de paires bougent de 0,17 bps au plus entre t1 et t2 (✔ recalculé : maximum des différences de `close_bps_med`) ; nombre de minutes communes 240/239 (t1) contre 233 (t2) |
| Exécution d'origine vs correctif Binance Vision | `common: 0` puis `common: 1440` (même fichier, unités différentes) : démonstration concrète du piège d'unité |
| Sondes de découverte (1 appel) vs séries complètes | Les deux concordent sur les statuts (200/403/451) ; les deux montrent la BLS `NOT_PROCESSED` puis `SUCCEEDED` |

Aucune autre lane n'est comparée ici. La lane 003 (PIT-safe evidence & replay) traite d'un sujet voisin (structures PIT côté base de données) mais n'est pas dans mon périmètre de lecture.

---

## 9. Reproductibilité

### 9.1 Pour rejouer

Selon `bench/data_feeds_v1/README.md` : `pip install requests websockets`, puis exécuter les scripts depuis `bench/data_feeds_v1/py/`. Ordre logique déduit du code :

1. `python sweep1.py` et `python sweep2.py` (sondes de découverte → `results/sweep1.json`, `sweep2.json`).
2. `python run_bars.py t0`, puis `t1` après ~78 s, puis `t2` après ~6 min (→ `raw/bars_t*.json`).
3. `python analyze_bars.py t2`, `python consensus.py`, `python lagtest.py` (→ `results/bars_analysis_t2.json`, `consensus_dev.json`, `lag_test_vs_kraken.json`) : **hors ligne, moins d'une seconde**.
4. `python dv.py` (dérivés), `python ws_sample.py` (WebSocket), `python latency.py`, `python fxgold.py`, `python macro.py`.
5. `python gen_reports.py` (régénère les 13 rapports, `final_block.txt`, `counts.json`).

Dépendances : Python 3 (testé ici en 3.11), `requests`, `websockets`. Le module `lzma`, `struct`, `zipfile` sont dans la bibliothèque standard.

### 9.2 Ce qui est fourni

- Code de tous les appels, tous les traitements, et du générateur de rapports.
- Captures normalisées de bougies (`bars_t0/t1/t2.json`, ≈358 Ko chacune) permettant de **recalculer exactement** les analyses de bougies (✔ fait).
- Captures brutes de premières réponses (86 fichiers), JSON dérivés, citations de CGU.

### 9.3 Ce qui manque ou limite

- **Non reproductible à l'identique en direct** : dépend de l'heure, du réseau, de la géolocalisation, des quotas ; les prix ont changé.
- Script du correctif Binance Vision (`binance_vision_fix.json`) absent.
- Corps bruts > 400 Ko supprimés (options Deribit/OKX, Kraken Futures funding, LBMA, SNB, Pink Sheet) : les chiffres options/LBMA ne sont pas recalculables depuis le dépôt (résultats agrégés fournis).
- Les données ad hoc (Swissquote 13:02Z) sans capture.
- Clés : les sources à clé (FRED, EIA, BEA, Coinalyze…) demandent des clés gratuites non fournies.
- Durée d'une rejouée complète en direct : non mesurée ; dominée par les 30-40 s de timeouts FRED, les pauses, ~25 minutes de mesures selon `12_LIMITATIONS.md` (12:50–13:15 UTC).
- Point d'attention de propreté : `__pycache__` n'est pas dans `origin/main` pour cette lane (le `.gitignore` l'exclut), ce qui est correct.

---

## 10. Implications pratiques pour AurumShift (pistes « à adjuger plus tard », aucune affirmation de compatibilité)

Rappel de `claude.md` : cette lane ne connaît pas le code d'AurumShift. Tout ce qui suit est une piste de travail à confronter plus tard au dépôt local.

1. **Distinguer bascule de source et continuité de série.** Les données montrent qu'une bascule entre plateformes change le prix de 0,3 bps (voisines) à ~13 bps (Bitfinex), et que USD et USDT se séparent de 2 à 4 bps. Piste : à adjuger plus tard, se demander si le système exige *une source faisant autorité par sujet* (règle `claude.md`) et si un secours doit être une source de la même famille (mêmes contrats, même devise de cotation).
2. **Piste de « contrats de source » testables** : la lane révèle des pièges répétables (unité ms/µs, ordre des colonnes Coinbase, bougie en formation Kraken, ordre croissant/décroissant, plafond d'appels différent, bougies remplies plates). Piste : des tests de contrat par source, à évaluer plus tard, pourraient les attraper.
3. **PIT** : la lane conclut que presque toutes les sources exigent que le consommateur tamponne l'heure de réception et conserve chaque téléchargement. Piste : à adjuger contre le modèle PIT/provenance existant d'AurumShift (PostgreSQL d'abord) : est-ce déjà le cas ?
4. **Historique + bord récent** : combinaison Binance Vision (fichiers immuables avec empreinte) + API du miroir pour le bord récent, avec règle de jonction (1 440/1 440 identiques sur un jour testé). Piste candidate, à confirmer sur d'autres jours et à confronter à la licence.
5. **Dérivés** : les valeurs de funding et d'OI ne sont pas comparables telles quelles (unités, cadences, 11 désaccords de signe sur 15). Piste : normalisation explicite avant toute utilisation croisée.
6. **Licences** : plusieurs sources tentantes sont non commerciales ou sans redistribution (Dukascopy, Twelve Data, Finnhub, open.er-api, Yahoo). Piste : décider tôt si le projet est strictement « recherche interne » ou si la redistribution est envisagée ; lire manuellement les CGU de toute plateforme retenue.
7. **Macro PIT** : lacune majeure, le seul candidat PIT natif (ALFRED) n'a pas pu être testé ; en attendant, les sources officielles ne donnent pas l'heure de publication. Piste : test de FRED/ALFRED depuis un réseau non filtré (voir §11).

Aucune de ces pistes n'affirme que le système actuel en a besoin ou qu'une source « convient ».

---

## 11. Questions ouvertes et suites recommandées (classées par valeur)

1. **Exécuter FRED/ALFRED avec une clé gratuite depuis un réseau sans filtre** : seul candidat de macro PIT natif ; conclusion actuelle = DOCUMENTED_CLAIM. Valeur très élevée pour la contrainte PIT.
2. **Test de stabilité sur plusieurs jours** (au moins 7 jours, dont un week-end et un événement macro) : recapture des mêmes bougies à +1 h, +1 j, +7 j pour mesurer les vraies révisions et les trous ; ajouter un contrôle positif (injecter une révision artificielle pour valider le détecteur).
3. **Vérification des CGU de chaque plateforme retenue** (OKX, Kraken, Coinbase, Deribit, Binance mirror/Vision) par lecture humaine, avec citation exacte et lien daté. Sans cela, aucune décision de stockage/redistribution.
4. **Corriger le protocole Bitget** : refaire la récupération avec des bornes sûres (marge de ± 1 minute, dédoublonnage) pour confirmer l'absence de trou réel, et mettre à jour le verdict.
5. **Binance principal et Bybit depuis un réseau autorisé** : les dérivés les plus utilisés ne sont pas évalués. Ajouter Coinalyze avec sa clé gratuite (agrégateur d'OI/funding/liquidations).
6. **Ajouter un vrai test de bascule** : simuler la perte d'une source primaire, basculer sur le secours, mesurer le saut de niveau (bps), la fenêtre de rattrapage et le comportement 429/Retry-After.
7. **Comprendre le +13 bps de Bitfinex** (et le −4,5 bps de HTX) : cause de cotation, de contrat ou d'agrégation ; cela déterminerait s'il s'agit d'une propriété stable.
8. **Normaliser le funding et l'OI** (par 8 h, en BTC) et corriger la somme Hyperliquid à 8 lignes ; calculer le skew 25Δ ; comparer les bougies natives multi-échelles aux bougies rééchantillonnées (NOT TESTED).
9. **Compléter l'inventaire des matières premières** (Hyperliquid xyz : CL, BRENTOIL, COPPER, ALUMINIUM) et revoir l'énoncé « un seul flux ».
10. **Ajouter le code du correctif Binance Vision** et archiver (ou fournir par empreinte) les corps bruts supprimés, afin que les chiffres options/LBMA soient recalculables.
11. **Rendre les définitions applicables mécaniquement** : règle explicite pour PIT_ADAPTABLE par endpoint (bougies vs WebSocket), pour que les classes ne dépendent plus d'une saisie manuelle.

---

## 12. Index des fichiers lus

Tous lus intégralement sauf mention. Chemins relatifs à la racine du dépôt (branche `origin/main`).

### Rapports (`reports/005_data_feed_resilience/`)

| Fichier | Contenu |
|---|---|
| `00_EXECUTIVE_SUMMARY.md` | Mission, ce qui a été fait, 7 constats de tête, décompte des verdicts, bloc final |
| `01_SOURCE_LANDSCAPE.md` | 1 175 lignes : 68 fiches sources. **Lu en partie** : début intégral (OKX à Gemini/Gate), puis extraction systématique des titres, classes, coûts, statut d'exécution et notes des 68 fiches ; les champs de détail (limites de débit, profondeur, citations) des fiches intermédiaires n'ont pas été relus ligne à ligne |
| `02_CRYPTO_SPOT.md` | Tableau des 18 séries de bougies, observations, historique en masse |
| `03_CRYPTO_DERIVATIVES.md` | Funding, OI, liquidations, basis, options, WebSocket |
| `04_FX_GOLD_COMMODITIES.md` | Or (instantané), FX, matières premières |
| `05_MACRO.md` | Sources macro, calendrier, lacune de dates de publication |
| `06_EXECUTION_TESTS.md` | 119 sondes, latence, rafales |
| `07_CROSS_PROVIDER_COMPARISON.md` | Horodatages, OHLC, paires les plus proches, volumes |
| `08_PIT_READINESS.md` | Définitions PIT, signaux observés, classement par source |
| `09_LICENSE_AND_COST.md` | Coûts et citations de conditions d'utilisation |
| `10_RESILIENCE_MATRIX.md` | Matrice de rôles par classe de manque |
| `11_ADJUDICATION.md` | Verdicts ADOPT/ADAPT/REJECT/PARK, définition « drop-in » |
| `12_LIMITATIONS.md` | 13 limites déclarées |

### Code (`bench/data_feeds_v1/`)

| Fichier | Contenu |
|---|---|
| `README.md` | Description des dossiers et consigne de reproduction |
| `py/probe_lib.py` | Aide HTTP : chronométrage, capture brute, en-têtes de limites |
| `py/bars_lib.py` | Récupérateurs normalisés par plateforme (18 séries) |
| `py/run_bars.py` | Fenêtre de 240 min, appel des 18 séries, sauvegarde `raw/bars_<tag>.json` |
| `py/analyze_bars.py` | Comptages, révisions, statistiques par paire |
| `py/consensus.py` | Écart au consensus de groupe |
| `py/lagtest.py` | Corrélation avec décalage −3…+3 min |
| `py/dv.py` | Funding, OI, options, basis, liquidations |
| `py/ws_sample.py` | Échantillons WebSocket de 20 s |
| `py/latency.py` | Latence répétée et rafales |
| `py/fxgold.py` | Binance Vision, Dukascopy, or, FX |
| `py/macro.py` | FRED/ALFRED, Trésor, NY Fed, BLS, Eurostat, CFTC, LBMA, calendrier, Yahoo |
| `py/sweep1.py`, `py/sweep2.py` | Sondes de découverte (début lu intégralement, listes d'endpoints) |
| `py/catalog.py` | Catalogue de 68 sources avec PIT, rôles, verdicts saisis à la main (début lu, comptages recalculés par exécution) |
| `py/gen_reports.py` | 506 lignes : générateur des rapports (en-tête, comptages, logique de tableaux lus ; les longs gabarits de texte relus par sondage) |
| `results/final_block.txt`, `counts.json` | Bloc final ; comptages et listes par classe |
| `results/bars_analysis.json` (t0→t1), `bars_analysis_t2.json` (t0→t2) | Statistiques par plateforme et par paire |
| `results/consensus_dev.json`, `lag_test_vs_kraken.json` | Écarts de consensus ; test de décalage |
| `results/derivs_analysis.json` | Funding, OI, options, basis, liquidations |
| `results/ws_sample.json`, `ws_okx_retry.json` | WebSocket |
| `results/latency_ratelimit.json`, `sweep1.json`, `sweep2.json` | Latence, rafales, sondes |
| `results/fxgold_bulk.json`, `binance_vision_fix.json`, `macro_tests.json` | Or/FX/Binance Vision/Dukascopy ; correctif d'unité ; macro |
| `results/docs_facts.json` | Citations de CGU/docs pour 47 fournisseurs + `_meta` (lu par extraction : citations de débit et licences ; pas lu en entier ligne à ligne) |
| `raw/bars_t0.json`, `bars_t1.json`, `bars_t2.json` | Bougies normalisées des 3 récupérations (analysées par programme) |
| `raw/swissquote_xau.json`, `gold_api_xau.json`, `bls_api_v1.json`, `deribit_ticker_perp.json`, `nyfed_sofr.json`, `okx_liq.json`, `hl_xyz_gold.json`, `bitmex_instr.json`, `binance_vision_um.txt`, `hyperliquid_funding.json` | Échantillons bruts lus pour vérifier des chiffres |
| autres `raw/*` (≈76 fichiers) | **Non lus individuellement** (captures de première passe par source) |

Autres fichiers consultés hors lane : `claude.md` (doctrine), `.gitignore`.
