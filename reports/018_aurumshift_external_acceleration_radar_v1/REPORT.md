# 018 — AURUMSHIFT_EXTERNAL_ACCELERATION_RADAR_V1

Mode : recherche approfondie + validation pratique bornée (laboratoire externe). Date : 2026-10-05 (horloge sandbox, UTC).
Aucun code, aucune base, aucun credential ni chemin d'exécution AurumShift n'a été lu ou modifié. Les compatibilités
avec le code AurumShift privé ne sont **pas** affirmées. L'adjudication d'intégration finale se fait contre le dépôt
réel (`claude.md`).

Livrables du dossier :
- `REPORT.md` (ce document)
- `CANDIDATE_MATRIX.csv` (211 lignes, 19 scores, classification de lane + finale)
- `SOURCE_LEDGER.md`
- `BENCHMARKS.md`
- `BENCH_NEXT_72H.md`
- `evidence/` (notes de lanes, CSV par lane)
- `bench/` (harnais reproductibles et résultats JSON)

**Étiquettes de preuve.** Les affirmations sont étiquetées :
- VERIFIED_FACT : source primaire lue, URL dans le ledger ;
- MEASURED_BY_THIS_MISSION : exécuté ici ;
- UPSTREAM_BENCHMARK ;
- PAPER_RESULT ;
- VENDOR_CLAIM ;
- INFERENCE ;
- UNKNOWN.

« LAB_PRIOR nnn » renvoie à une étude antérieure du laboratoire, réutilisée et non refaite.

**Convention des scores (0–5).** 5 est toujours favorable à AurumShift : INTEGRATION_COST 5 = bon marché,
SECOND_AUTHORITY_RISK 5 = risque négligeable, EXIT_COST 5 = sortie facile. `?` signifie preuve insuffisante. Les
scores sont qualitatifs, sans précision numérique simulée.

---

## 0. Résumé exécutif

1. **Le goulot principal n'est pas technologique, c'est la taille d'échantillon** (MEASURED, bench Q1).
   - Pour détecter +10 bps nets par décision (σ ≈ 50 bps, autocorrélation φ ≈ 0,3) avec une puissance de 0,7–0,9, il
     faut **≈ 250–500 outcomes QUORUM_ONLY_SUPPRESSED**.
   - Le t-test naïf sous-couvre (0,84–0,87 au lieu de 0,95) dès φ = 0,3, à tout N.
   - Si l'opérateur regarde le résultat tous les 10 outcomes, la probabilité de « découvrir » un edge inexistant monte
     à **30–69 %**.
   - Le composant le plus précieux pour l'expérience quorum est donc une **procédure pré-enregistrée** : HAC
     `statsmodels` en primaire, `arch` pour SPA/StepM, une betting confidence sequence comme moniteur d'arrêt. Une
     librairie causale n'apporterait pas cela.

2. **Il existe un oracle de coût indépendant, gratuit et déterministe** contre COST_CONTRACT_V1 (MEASURED, lane CD).
   - Il combine les échantillons Tardis gratuits (1er jour de chaque mois), une marche dans le carnet et la
     reconstruction L2 par `hftbacktest`.
   - Mesures : un BUY de 100 k USDT coûte 4,2 bps (DOGE Binance spot) et **7,1 bps (DOGE OKX spot)** en médiane,
     contre 0,0006–0,3 bps pour BTC. Un coût fixe de 5 bps et le demi-spread seul sont faux, dans des directions
     opposées selon l'actif.
   - Le moteur de fills de hftbacktest est **défectueux pour cet usage** : ordres market plafonnés à 100 ticks, fills
     partiels non appliqués. On garde l'utilitaire de données, pas le moteur.

3. **C0 :**
   - **ccxt 4.5.85 (ccxt.pro désormais inclus, MIT)** sert 22 cases sur 36 (12 surfaces × 3 venues) sans code
     spécifique à une venue. Le résiduel PIT/provenance tient en ~42 lignes. Sur OKX, le carnet WS est **identique au
     top-25 sur 598 messages sur 598** (MEASURED).
   - En revanche, ccxt **perd silencieusement** des champs PIT : `confirm` de la barre en formation, `ts` du funding
     OKX, `seqId` REST, unités d'OI.
   - **Fait actionnable immédiat** (VERIFIED_FACT + MEASURED) : OKX a déprécié le checksum CRC32 du carnet le
     2026-06-23 (valeur 0 dans 100 % des messages). Un contrôle CRC32 dans C0 est aujourd'hui inopérant ; il faut
     utiliser `seqId/prevSeqId`.

4. **PIT :**
   - Aucun candidat ne justifie de remplacer l'autorité Postgres, ce qui confirme LAB_PRIOR 004.
   - Gain nouveau : la forme **« timeline-ASOF »**. On pose `available_at = greatest(ingested_at, event_time)` et on
     prend le max cumulé de (event_time, revision). Elle rend `join_asof` Polars/DuckDB exact : 0 écart et 0 lookahead
     sur 200 000 décisions, ~550× plus rapide que la référence (MEASURED, synthétique).
   - L'ASOF naïf reste une **fuite massive** : 57 423 décisions sur 200 000.

5. **Ledger d'expérience forward :**
   - Une table Postgres append-only à chaîne de hash (51 lignes SQL) suffit.
   - MLflow 3.16 est **rejeté comme autorité** (MEASURED) : 59 tables, tags réécrivables, métriques écrasables, runs
     supprimables.

6. **Calendrier économique :**
   - L'horaire faisant autorité vient des sources officielles : BEA ICS en UTC avec UID, page Fed + RSS, ECB, BoE,
     BoJ.
   - Le consensus n'est disponible qu'en payant ou via ForexFactory (CGU UNKNOWN). Le compte guest de Trading
     Economics est supprimé (HTTP 410).
   - **Aucun fournisseur examiné ne donne l'instant réel de publication de l'actual** : AurumShift doit le stamper
     lui-même en capture forward.
   - Kalshi et Polymarket fournissent une **probabilité d'événement PIT-native à la minute**. Sur la décision Fed
     d'octobre, les deux concordent à ~2 points de pourcentage (MEASURED).

7. **Lanes à faible valeur immédiate :**
   - portefeuille (2 actifs BUY-only : l'inverse-volatilité suffit, et HRP de skfolio plante à 2 actifs) ;
   - NLP financier (FinBERT se trompe de signe sur des titres macro triviaux, MEASURED) ;
   - mémoire agent ;
   - infrastructure (aucun goulot mesuré).

8. **Synthèse chiffrée :**
   - 211 lignes candidates criblées ; L1 46, L2 39, L3 18 ; 7 benchs différentiels « forme AurumShift ».
   - Classification finale : ADOPT_NOW 14, BENCH_NOW 18, SHADOW 10, WATCH 37, PARK 89, REJECT 43.
   - Les ADOPT_NOW sont presque tous des **bibliothèques d'analyse hors runtime** ou des **sources officielles** :
     aucun n'entre dans le chemin d'exécution.

---

## 1. Périmètre, méthode, limites

- **Organisation de la recherche.**
  - Six sous-recherches parallèles : A ; B+J+K+L ; C+D ; E ; F+G+H ; I.
  - Toutes partagent un brief commun (`evidence/AGENT_BRIEF.md`) : règles de preuve, entonnoir L0→L3, venvs isolés,
    CSV à en-tête fixe.
  - L'orchestrateur a exécuté le bench Q1, testé le connecteur TipRanks et confseq, puis adjugé.
- **Réutilisation des études du labo.** Onze études antérieures (LAB_PRIOR 002, 004–006, 008–017) ont été réutilisées,
  et non refaites.
- **Ordre de priorité imposé.**
  - A : Outcome forward
  - B : oracles de coût
  - C : inférence quorum
  - D : PIT
  - E : C0
  - F : ledger
  - G : calibration et dérive
  - H : calendrier
  - L'infrastructure n'est retenue que contre un goulot mesuré.
- **Limites majeures.**
  - Données synthétiques ou publiques : aucune donnée AurumShift.
  - Binance et Bybit sont **inaccessibles depuis l'egress** (451 / 403). Leur couverture vient de la lecture de code et
    de docs ; ce n'est pas un verdict négatif.
  - API GitHub refusée : la maintenance est déduite de git clone, PyPI, crates et npm.
  - Machine de 4 vCPU partagée : les temps sont des ordres de grandeur.
  - Une seule journée de microstructure (2026-10-01) pour l'oracle de coût.
  - Prix : seulement ceux publiés, sinon UNKNOWN_PRICE.
  - Aucun fill propre : le coût **réalisé** est inconnu.
- **Écarts de procédure déclarés par les lanes.**
  - `apt install libboost-dev` (lane A) ;
  - `postgresql-16` du sandbox passé de 16.14 à 16.15, et `vector.so` installé (lane BJKL) ;
  - patchs de port et de TLS pour barter-data (lane E).

  Tous ces écarts restent dans le sandbox ; aucun ne touche AurumShift.

---

## 2. Constats par lane (avec étiquettes)

### Lane A — Expérience causale quorum (priorité C)

- **Nature du design.** A (quorum 2), B (quorum 1, shadow) et C (single-family) partagent le **même DecisionInput
  gelé** : c'est un design **apparié**. La décision n'a pas de confusion à corriger (INFERENCE).
  - DoubleML, EconML, DoWhy, CausalML et l'off-policy (obp) répondent à une autre question.
  - Ils sont surdimensionnés : 500 Mo à 1,3 Go d'empreinte (MEASURED).
  - obp n'est pas défini avec des politiques déterministes (propension 0/1) et ne s'installe pas sur Py3.11 (MEASURED).
  - Classement : **PARK/REJECT**.
- **Pile retenue (MEASURED, Q1 + lane A).** Aucun composant externe ne traite l'honnêteté de l'Outcome contrefactuel
  de B (voir §8).

| Rôle | Composant | Constat |
|---|---|---|
| Intervalle primaire | `statsmodels 0.15` HAC | meilleure couverture à N fixe |
| Second avis + comparaisons A/B/C | `arch 8.0` | StationaryBootstrap avec bloc Politis-White, SPA/StepM/MCS (0,04 s pour 3 bras) |
| Corrections multiples | `statsmodels.multitest` | — |
| Non-infériorité | TOST adapté HAC | — |
| N requis | PSR/MinTRL | ~20 lignes ; concorde avec quantstats à 4e-4 |
| Monitoring anytime-valid | betting CS `confseq` (vendorisé) | — |

- **Couverture, puissance et peeking** (MEASURED, Q1, 1 000 réplications ; détail dans BENCHMARKS.md).

| Méthode | Constat |
|---|---|
| HAC | 0,906 → 0,936 → 0,942 à N = 120 / 250 / 500 (φ = 0,3) ; sous-couvre à N ≤ 60 et à φ = 0,6 |
| Bootstrap par blocs | ne fait pas mieux que HAC à petit N |
| Betting CS | FWER sous peeking 0–1,7 % (contre 30–69 %) ; IC 2–4,5× plus larges ; puissance 0,44–0,53 à N = 500 |

  Rôle de la betting CS : **moniteur de nuisance**, pas preuve de gain.
- **confseq 0.0.11.**
  - Dernière release en 2023, un contributeur principal : maintenance dormante.
  - Ne compile pas sur Python 3.11 (pybind11) et casse avec NumPy 2 (MEASURED). Un patch de 6 lignes est fourni.
  - Recommandation : vendoriser la partie betting.
- **Écartés pour licence ou intégrité.**
  - `pingouin` : GPL-3.
  - `expectation` : GPL-3 plus une clause anti-IA (VERIFIED).
  - `mlfinlab` : propriétaire, £100/mois/utilisateur (VENDOR_CLAIM).
  - DVC/DataLad : créeraient une seconde autorité de provenance.
- **Préregistration.** Un hash sha256 du plan d'analyse commité **avant le premier Outcome B** suffit. OSF Registries
  (gel, embargo jusqu'à 4 ans, VERIFIED) n'est qu'un témoin externe optionnel.

### Lane B — PIT / bitemporel (priorité D)

- **PostgreSQL temporel** (VERIFIED, doc officielle).
  - PG18 apporte `WITHOUT OVERLAPS` (PK/UNIQUE) et `PERIOD` (FK).
  - `FOR PORTION OF` est absent de PG18 et de PG19 beta 4 (24-09-2026).
  - Le « system time » n'est pas supporté.
  - Le motif append-only + horloge DB + verrous de LAB_PRIOR 004 reste donc nécessaire.
- **Timeline-ASOF** (MEASURED, 5 M lignes).
  - Exacte : 0 écart, 0 lookahead, Polars ≡ DuckDB.
  - Rapide : 3,8 s pour 200 000 décisions.
  - Garde-fou : `greatest()` masque une horloge biaisée, donc le contrôle `ingested_at ≥ event_time` reste un test
    séparé.
- **XTDB v2 (MPL, serveur JVM), Dolt, Iceberg/Delta (time travel sur le temps de *commit*), Feast, Chronon,
  Hopsworks : PARK.** Ils créeraient une seconde base, sans goulot mesuré et sans dossier de migration.
- **Détection de fuite.** Aucun outil générique ne vaut le test de troncature/préfixe custom (BENCH_NOW comme oracle).
  deepchecks est en PARK (maintenance ralentie).

### Lane C — Oracles de coût / Outcome économique (priorité B)

- **Oracle Tardis gratuit + walk-the-book** (MEASURED, voir BENCHMARKS CD-1).
  - Déterministe : même sha256 sur 2 exécutions ; md5 des 20 fichiers vérifiés.
  - PIT : le carnet est lu à `local_timestamp ≤ T`. Écart de réception de 2–6 ms en médiane, aucun ordre inversé.
  - Profondeur : le top-25 est insuffisant pour BTC dans 20 % des cas à 100 k et 86 % à 1 M. Il faut alors
    `incremental_book_L2`, ou classer le cas en `UNKNOWN_COST`. **Jamais 0.**
- **Funding.**
  - Tardis `derivative_ticker` égale l'officiel OKX `realizedRate` 6 fois sur 6, et Binance 3 fois sur 6 (écarts
    ≤ 1e-6).
  - La vérité reste l'API officielle OKX et Binance Vision `fundingRate`.
- **Commerciaux.**

| Offre | Prix | Statut | Constat |
|---|---|---|---|
| Tardis Solo Spot / All | 900 / 1 200 USD/mois (VENDOR_CLAIM) | TIER_C, SHADOW | mensuel = 4 mois d'historique ; annuel = 4 ans ; CSV uniquement |
| Crypto Lake | 80 USD/mois particulier, 500 USD/mois société | WATCH | 20 niveaux |
| Kaiko | UNKNOWN_PRICE | WATCH | snapshots toutes les 30 s |
| Amberdata | UNKNOWN_PRICE | WATCH | — |
| CoinAPI | — | PARK | — |
| Databento | — | **REJECT** | aucun venue crypto spot (VERIFIED) |

- **Engines.**
  - `nautilus_trader` (2.0.0rc6 publié le 05-10-2026, LGPL, Python ≥ 3.12) : WATCH. Il tronque à 10 niveaux et perd
    l'échéance de funding (MEASURED).
  - `cvxportfolio` (GPL, bus factor 1) : PARK.
  - `tcapy`, `abides` : REJECT.
- **Constat d'architecture** (INFERENCE). Aucun moteur externe ne peut devenir autorité de fill/position sans risque :
  ils ont tous un modèle de fill non réaliste ou incomplet. L'oracle ne sert qu'à **contrôler** COST_CONTRACT_V1.

### Lane D — Microstructure / replay

- **hftbacktest 2.4.4** (MIT, aucun commit depuis le 2025-12-23).
  - Reconstruction L2 depuis Tardis : exacte à 3,4e-4 bps (MEASURED).
  - Moteur de fills : 3 défauts mesurés (plafond de 100 ticks, partiels non comptés, mode sans partiel irréaliste).
  - Pour de l'intraday non-HFT, la file d'attente n'est pas l'enjeu. L'enjeu est la **profondeur traversée** et la
    **fraîcheur du carnet** : 83 ms en médiane côté Binance, publication toutes les 100 ms (MEASURED).
- **Fills passifs.** Non estimables sans ordres propres (LAB_PRIOR 006). Aucun composant ne comble ce manque.

### Lane E — Données de marché / C0 (priorité E)

- **ccxt 4.5.85** (MIT, ccxt.pro inclus gratuitement : VERIFIED) — détails dans BENCHMARKS E-1.
  - Résiduel PIT de 42 lignes.
  - Reconnexion : `CancelledError` à intercepter.
  - Liquidations OKX non supportées.
- **API OKX native.** Référence d'intégrité. Contrat mouvant : checksum supprimé ; l'endpoint `liquidation-orders`
  est « délisté » mais répond encore.
- **tardis-machine 18.3.8** (MPL-2.0, local).
  - Même schéma en live et en replay, avec double horodatage.
  - Replay keyless limité au 1er du mois ; Node ≥ 24.19 requis.
  - BENCH_NOW comme **oracle différentiel C0**.
- **cryptofeed 3.0.1** (AGPL, réécriture de septembre 2026, Python ≥ 3.13, un seul mainteneur).
  - Fournit un `receipt_timestamp` natif.
  - **Piège PIT** : backlog de liquidations d'environ 3,9 h au démarrage.
  - SHADOW au mieux.
- **barter-data (Rust).** Bon modèle PIT, mais couverture C0 insuffisante (pas de funding ni d'OI) : WATCH.
- **Agrégateurs (CoinGlass, Velo, Coinalyze).** Révisions non documentées : oracles de cohérence seulement (WATCH).
- **REJECT** : cryptostore, crypto-crawler-rs, ccxt-rs, hummingbot (autorité d'ordres).

### Lane F — Online / dérive / régime / calibration (priorité G)

- **Constat transversal** (MEASURED) : **les queues épaisses dominent le choix de l'algorithme.**
  - Focus (`changepoint_online`, GPL-3) détecte un saut de volatilité ×3 en 4 obs sans fausse alarme sous bruit
    gaussien, mais donne **90 % de fausses alarmes** sous t(4) avec un seuil gaussien.
  - River PageHinkley : 50 % de fausses alarmes.
  - Conséquence : calibrer les seuils par bootstrap par blocs sur une période calme réelle.
- **Conformal.**
  - `crepes` normalisé par la volatilité : 0,85 de couverture après le saut, pour un coût quasi nul.
  - MAPIE ACI : référence de test (concorde avec l'ACI maison à ≤ 0,002) mais 7× plus lent, avec des bornes infinies.
  - EnbPI : REJECT.
  - Rappel LAB_PRIOR 012 : couverture marginale ≠ fiabilité de décision.
- **Usage recommandé.** Moniteurs SHADOW sur coût, slippage et latence réalisés (bandes conformal, détection de
  changement), jamais des gates.

### Lane G — Portefeuille / risque

- Avec 2 actifs BUY-only, l'optimisation se réduit à l'inverse-volatilité (3 lignes).
- skfolio HRP est identique à Riskfolio (1,7e-18), mais plante à 2 actifs (MEASURED).
- Riskfolio-Lib pèse 85 paquets et environ 963 Mo.
- **Tout PARK** jusqu'à ≥ 5–10 actifs qualifiés. Risque principal : une seconde autorité de dimensionnement.

### Lane H — Économétrie / causal time series

- **statsmodels VECM / Johansen / Granger : BENCH_NOW** sur la basis spot/perp et le lead/lag cross-venue.
  - MEASURED : cointégration détectée à 100 %, faux positifs 0–2 %.
  - **Un décalage d'horodatage d'un seul pas fabrique un lead « certain » à 100 %.** Un audit des horodatages C0 est
    donc un préalable.
- **tigramite** (GPL-3) : PARK. Sans FDR, 16–30 % de faux liens ; avec FDR, 2 %.
- Rappel LAB_PRIOR 011 : le lead/lag significatif a été tué par les coûts.

### Lane I — News / politique / calendrier (priorité H)

- **Sources officielles d'horaire : ADOPT_NOW** (MEASURED).
  - BEA ICS : 119 événements en UTC, UID uniques ; le JSON contient 6 dates dupliquées.
  - Fed : dates sur la page, heure (14:00 ET) attestée par le RSS.
  - ECB, BoE, BoJ : dates seulement.
  - BLS ICS : 403 aujourd'hui depuis cet egress (lu dans LAB_PRIOR 010).
- **ForexFactory export** (SHADOW).
  - Pas d'`actual`.
  - JSON à l'heure de New York avec offset, XML en UTC sans marqueur.
  - Aucun id d'occurrence ; mise à jour horaire ; 429 au-delà d'environ 1 requête toutes les 5 minutes.
  - CGU illisibles depuis l'egress (UNKNOWN).
- **Fournisseurs payants.**
  - Trading Economics : schéma le plus complet (`CalendarId`, `Forecast`, `Revised`, `LastUpdate`), guest supprimé
    (410). Prix primaire illisible ; SECONDAIRE ~149–199 USD/mois, TIER_B : BENCH_NOW en essai.
  - Benzinga : `id` et delta `updated`, prix sur devis.
  - Finnhub : calendrier premium.
  - EODHD : « personal use ».
  - FMP : non vérifié depuis l'egress.
- **Connecteur TipRanks** (WATCH).
  - Fournit actual, estimate et prev en un appel.
  - Pas d'id, pas de fuseau, `unit` paddé d'espaces, zone euro absente, données « may be delayed » (MEASURED).
- **Marchés de prédiction** (SHADOW, MEASURED).
  - Kalshi (régulé CFTC) : candles à 1 min ; partition historique avant le 2026-08-06.
  - Polymarket : historique à 1 min par fenêtres ≤ 15 j ; trading géobloqué en FR/US/UK/DE, lecture OK.
  - Accord sur P(hausse Fed oct.) à ~2 points de pourcentage.
- **GDELT bulk** (SHADOW) : `DATEADDED` est une étiquette de lot environ 9 min *après* la disponibilité réelle. C'est
  une borne conservatrice ; il faut doubler d'un stamp de réception.
- **FinBERT : REJECT** (erreurs de signe sur NFP et ECB, MEASURED).
- **LLM d'extraction** : PARK, avec un **risque de fuite par knowledge cutoff** en backtest (INFERENCE forte).
- **OKX announcements** (`pTime` en ms, keyless) : BENCH_NOW pour les listings et délistings des venues C0.

### Lane J — Stockage / compute / événements

- **ADBC Postgres et scanner DuckDB** : lecture vers Arrow 3,4× plus rapide que psycopg (MEASURED). Aucun goulot
  AurumShift mesuré : WATCH.
- **TimescaleDB** (fonctions utiles sous licence Timescale), NATS, Redpanda (BSL), pg_duckdb, pgmq : PARK.
- **Règle.** `pg_stat_statements` d'abord, pour prouver un goulot.

### Lane K — Observabilité / qualité / tracking

- **Ledger d'expérience** : Postgres append-only à chaîne de hash, BENCH_NOW. MLflow : REJECT comme autorité, PARK
  comme miroir en lecture seule.
- **Pandera 0.33** : même détection que du Polars écrit à la main, **sans gain de code** (26 lignes contre 13).
  BENCH_NOW comme contrat déclaratif seulement si plusieurs équipes ou agents écrivent dans C0. Piège : la sémantique
  des nulls dépend du backend.
- **OpenTelemetry SDK 1.45.**
  - SDK léger : 3 Mo, 16–43 µs par span.
  - Le backend serait un second magasin.
  - WATCH tant que l'observabilité d'autorité existe.
- **Soda Core** (ELv2) : REJECT. **GX, Evidently, NannyML, whylogs, deepchecks** : PARK.

### Lane L — Mémoire / agent

- **pgvector 0.8.7** : compile en 11 s (MEASURED). Aucun besoin sur le chemin critique : PARK. Si une mémoire devient
  nécessaire, la placer dans un schéma séparé explicitement **non autoritaire**.
- **Mem0, Letta, LightRAG, Cognee** (mémoire réécrite par LLM) : PARK.
- **Graphiti** (pas de Postgres) : REJECT. **ParadeDB** (AGPL) et **VectorChord** (AGPL/ELv2) : PARK / REJECT.
- La mémoire agent ne doit jamais devenir une autorité économique ou scientifique.

---

## 3. Matrice d'évaluation (extrait des candidats sérieux)

Matrice complète : `CANDIDATE_MATRIX.csv`, avec les 19 scores, les métadonnées (maturité, release, bus factor,
langage, déploiement, licence, prix, poids), les modes de défaillance et les sources.

Abréviations des colonnes :

| Abréviation | Score |
|---|---|
| FF | FUNCTIONAL_FIT |
| SF | SCIENTIFIC_FIT |
| EV | ECONOMIC_VALUE |
| PIT | PIT_COMPATIBILITY |
| DET | DETERMINISM |
| ACC | ACCURACY_OR_CALIBRATION |
| MNT | MAINTENANCE |
| IC | INTEGRATION_COST |
| CCR | CUSTOM_CODE_REMOVED |
| SA | SECOND_AUTHORITY_RISK |
| EXIT | EXIT_COST |
| LIC | LICENSE_LEGAL_USE |
| TTT | TIME_TO_OPERATIONAL_TRUTH |

Les colonnes LATENCY, THROUGHPUT, CPU_RAM_IO, SECURITY, API_STABILITY et TOTAL_COST figurent dans le CSV.

| Candidat | Rôle | Licence / prix | Release | FF | SF | EV | PIT | DET | ACC | MNT | IC | CCR | SA | EXIT | LIC | TTT | Classe finale |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Tardis gratuits + walk-the-book (CD01+CD08) | ORACLE | gratuit, Derived Data (§9 CGU, INFERENCE) | données 2026-10-01 | 5 | 5 | 5 | 5 | 5 | 4 | 4 | 4–5 | 4 | 5 | 5 | 4 | 5 | ADOPT_NOW / BENCH_NOW |
| statsmodels 0.15 (A02) | MODULE | BSD-3, 0 € | 2026-08-27 | 5 | 5 | 4 | 5 | 5 | 4 | 5 | 5 | 4 | 5 | 5 | 5 | 5 | ADOPT_NOW |
| arch 8.0 (A01) | MODULE | NCSA, 0 € | 2026 | 5 | 5 | 4 | 5 | 5 | 3 | 4 | 5 | 4 | 5 | 5 | 5 | 5 | ADOPT_NOW |
| confseq 0.0.11 vendorisé (A05) | MODULE | MIT, 0 € | 2023 | 4 | 5 | 3 | 5 | 5 | 4 | 1 | 3 | 3 | 5 | 5 | 5 | 3 | BENCH_NOW |
| ccxt 4.5.85 + pro (E01) | ADAPTER | MIT, 0 € | 2026-10 | 4 | 3 | 4 | 3 | 4 | 4 | 5 | 4 | 4 | 5 | 4 | 5 | 5 | BENCH_NOW |
| tardis-machine 18.3.8 (E05) | ORACLE | MPL-2.0 ; replay payant hors 1er du mois | 2026 | 4 | 4 | 4 | 5 | 4 | 4 | 4 | 4 | 3 | 4 | 4 | 4 | 4 | BENCH_NOW |
| hftbacktest `tardis.convert` (CD05) | ADAPTER | MIT, 0 € | 2025-12 | 5 | 4 | 4 | 5 | 5 | 5 | 2 | 4 | 4 | 5 | 5 | 5 | 4 | BENCH_NOW |
| Timeline-ASOF Polars/DuckDB (B01) | MODULE offline | MIT, 0 € | Polars 1.44 / DuckDB 1.5.6 | 5 | 4 | 3 | 5 | 4 | 5 | 5 | 5 | 3 | 5 | 5 | 5 | 5 | BENCH_NOW |
| Ledger PG hash-chain (K01) | MODULE dans l'autorité | PostgreSQL, 0 € | — | 5 | 4 | 3 | 5 | 5 | ? | 5 | 5 | 3 | 5 | 5 | 5 | 5 | BENCH_NOW |
| Calendriers officiels BEA/Fed/ECB/BoE/BoJ (I02–I06) | ORACLE horaire | domaine public, 0 € | — | 3–4 | 3 | 3–4 | 4 | 4 | 4 | 4 | 4–5 | 3 | 5 | 5 | 5 | 4–5 | ADOPT_NOW |
| Trading Economics (I08) | ADAPTER payant | propriétaire, TIER_B (SECONDAIRE) | — | 5 | 3 | 4 | 2 | ? | ? | 4 | 4 | 4 | 3 | 3 | 3 | 3 | BENCH_NOW (essai) |
| Kalshi / Polymarket (I27–I28) | ORACLE / SHADOW | CGU UNKNOWN, 0 € | — | 4 | 4 | 3 | 5 | 4 | 4 | 4 | 4 | 2 | 4 | 5 | 2 | 4 | SHADOW |
| Funding officiel OKX / Binance Vision (CD12–13) | ORACLE | officiel, 0 € | — | 4–5 | 4 | 4 | 4 | 5 | 5 | 5 | 5 | 3 | 5 | 5 | 5 | 3–5 | ADOPT_NOW (si perps) |
| crepes 0.9.1 (F03) | ORACLE bande | BSD-3, 0 € | 2026 | 4 | 4 | 3 | 4 | 5 | 4 | 3 | 5 | 3 | 5 | 5 | 5 | 4 | BENCH_NOW |
| Tardis abonnement Solo (CD02) | ORACLE historique | 900–1 200 USD/mois (TIER_C, VENDOR_CLAIM) | — | 5 | 4 | 4 | 4 | 5 | 5 | 4 | 4 | 4 | 5 | 4 | 3 | 4 | SHADOW (achat conditionnel) |
| MLflow 3.16 comme autorité (K-mlflow) | — | Apache-2 | 2026 | 3 | 2 | 1 | 2 | 3 | ? | 5 | 3 | 2 | **1** | 3 | 5 | 3 | REJECT (autorité) / PARK (miroir) |
| hftbacktest moteur de fills | — | MIT | 2025-12 | 2 | 2 | 1 | 4 | 5 | **1** | 2 | 3 | 1 | 3 | 4 | 5 | 2 | PARK |

Lecture : les scores ci-dessus reprennent ceux des lanes, harmonisés par l'orchestrateur quand deux lanes notaient
le même composant. Ils sont qualitatifs.

---

## 4. Classification finale (adjudication de l'orchestrateur)

Les lanes avaient proposé 20 ADOPT_NOW. L'orchestrateur en a **rétrogradé** six (`bench/final_adjudication.json`) :

| Candidat | Nouvelle classe | Motif |
|---|---|---|
| `ccxt` | BENCH_NOW | L3 sur OKX seulement ; remplacer un collecteur est une migration |
| `hftbacktest tardis.convert` | BENCH_NOW | amont inactif depuis plus de 9 mois |
| walk-the-book maison | BENCH_NOW | c'est un oracle à confronter, pas un composant externe |
| `tardis-dev` client | PARK | curl + md5 suffit |
| OSF | WATCH | — |
| BLS ICS | BENCH_NOW | 403 aujourd'hui |

Comptes finaux : ADOPT_NOW 14 · BENCH_NOW 18 · SHADOW 10 · WATCH 37 · PARK 89 · REJECT 43.

Les ADOPT_NOW finaux, et pourquoi ils passent la barre :
- `statsmodels`, `arch` (doublon A01/F01), PSR/MinTRL, préregistration hash+commit : outils **d'analyse hors
  runtime**, matures, testés et sans autorité.
- Tardis gratuits : oracle **vérifié par md5 et par déterminisme**.
- Funding officiels OKX et Binance : ce sont des sources de vérité.
- API OKX native : **action seqId**.
- DuckDB/Polars offline : déjà prouvés par LAB_PRIOR 004 et 017.
- Calendriers officiels BEA, Fed, ECB, BoE/BoJ : dates d'autorité.

---

## 5. Red team obligatoire (top recommandations)

Pour chaque composant, six questions :
1. pourquoi il pourrait rendre AurumShift **pire** ;
2. quelle autorité cachée il pourrait acquérir ;
3. quelle fuite PIT il peut introduire ;
4. quel piège de maintenance, de fournisseur ou de licence ;
5. le benchmark de falsification le plus simple ;
6. la preuve qui entraîne un rejet immédiat.

**R1. Oracle de coût Tardis + walk-the-book (+ hftbacktest convert)**
1. Une seule journée par mois peut sous-représenter le stress. Le walk-the-book ignore l'impact propre, la
   réaction du carnet et la latence AurumShift, ce qui donne une fausse assurance si l'oracle est lu comme
   « coût réalisé ».
2. Si un écart oracle–contrat déclenche automatiquement une correction de COST_CONTRACT_V1, l'oracle devient
   l'autorité de coût.
3. Lire le carnet sur `timestamp` (exchange) au lieu de `local_timestamp` utilise un état publié mais pas encore
   reçu. Fenêtres de warm-up incomplètes.
4. Licence « Derived Data » (§9) interprétée, non validée juridiquement. hftbacktest est inactif ; les formats
   Tardis peuvent changer.
5. Falsification : X1. Le biais médian contrat − oracle aux tailles PAPER est-il ≤ 0,5 bps ?
6. Rejet immédiat si le carnet reconstruit ≠ snapshot (> 0,01 bps), si deux runs donnent des hashes différents, ou si
   un cas INSUFFICIENT_DEPTH est compté à 0.

**R2. statsmodels HAC + arch (SPA/StepM/MCS) + préregistration**
1. Fausse rigueur : HAC sous-couvre à N ≤ 120 (0,86–0,92), ce qui revient à déclarer un edge trop tôt. Le bootstrap
   par blocs ne corrige pas cela.
2. Si un verdict « SUPPORTED » modifie automatiquement le quorum, l'outil d'analyse devient l'autorité de décision.
3. Le lag HAC est choisi sur les données. Des observations d'outcomes clos après la date d'analyse sont incluses.
4. Faible : licences BSD et NCSA, projets actifs. statsmodels 0.15 a cassé `verbose=` dans Granger : il faut figer
   les versions.
5. Falsification : rejouer Q1 au N et au φ effectivement observés ; il faut une couverture ≥ 0,93.
6. Rejet immédiat si la couverture est < 0,90 au N prévu, ou si le plan est hashé après le premier Outcome B.

**R3. Betting CS (confseq vendorisé)**
1. Trop conservatrice : elle peut masquer un vrai gain (puissance 0,44 à N = 500). La borne K tronque les queues et
   biaise la moyenne.
2. Si un « stop » de la CS coupe le shadow B automatiquement, elle devient une autorité de gouvernance.
3. Elle suppose une moyenne conditionnelle constante, que l'autocorrélation viole (BetCI à 0,765 à φ = 0,6).
4. Paquet dormant qui ne compile pas en Py3.11 / NumPy 2 : il faut vendoriser.
5. Falsification : FWER sous H0 avec regards hebdomadaires au φ observé ; il faut ≤ 0,05.
6. Rejet immédiat si le FWER est > 0,10, ou si K est choisi après avoir vu les données.

**R4. ccxt / ccxt.pro sous enveloppe PIT**
1. Des champs `None` silencieux (`ts` du funding OKX, `confirm`) et des unités variables (OI en contrats) peuvent
   corrompre C0 sans erreur. `CancelledError` non géré peut figer la collecte.
2. S'il remplace le collecteur et que DecisionV1 lit ses sorties, il devient l'autorité de données de marché.
3. Barre en formation renvoyée comme close. `timestamp` exchange utilisé comme heure de connaissance.
4. Version très mobile : il faut figer et passer un test de contrat par surface. Les ports et racines TLS codés en
   dur sont surchargeables.
5. Falsification : X3 (parité OKX 24 h).
6. Rejet immédiat sur un trou de séquence non signalé, ou un champ PIT perdu non détecté par le wrapper.

**R5. Timeline-ASOF (Polars / DuckDB)**
1. `greatest()` masque les horloges biaisées. La finalité n'est pas représentée.
2. Si le rejeu offline sert directement d'entrée à la décision au lieu du DecisionInput persisté.
3. Ex aequo non déterministes : Polars ≠ DuckDB d'une ligne en mode naïf.
4. Faible : MIT, mais les sémantiques ASOF changent d'une version à l'autre ; il faut figer.
5. Falsification : X4, 0 écart contre la fonction PIT d'autorité.
6. Rejet immédiat sur un seul écart non expliqué.

**R6. Ledger d'expérience Postgres hash-chain**
1. Fausse immuabilité : un superuser contourne le trigger. La falsification est détectée mais pas empêchée.
2. Faible : il reste **dans** l'autorité. Risque inverse : un MLflow miroir devient lu comme vérité.
3. `recorded_at` non normalisé en UTC avant hash. Lignes insérées a posteriori avec des dates passées.
4. Aucun.
5. Falsification : altérer une ligne ; la vérification de chaîne doit échouer (démontré).
6. Rejet immédiat si la vérification de chaîne ne détecte pas une altération.

**R7. Calendrier officiel assemblé (+ ForexFactory forward)**
1. Mauvais fuseau (le JSON FF est à l'heure de New York, le XML en UTC sans marqueur, et le décalage change au DST
   US), ce qui masque la mauvaise fenêtre. Doublons BEA JSON.
2. Un gate DecisionV1 « fenêtre d'annonce » activé avant qualification.
3. Utiliser un `actual` d'un fichier horaire, ou d'un historique réécrit, comme connu à l'heure prévue.
4. CGU ForexFactory UNKNOWN. BLS bloque (403) les clients scriptés.
5. Falsification : X5, concordance horaire UTC d'au moins 2 sources pour 100 % des événements high-impact.
6. Rejet immédiat sur un écart d'horaire non résolu pour un high-impact.

**R8. Trading Economics (essai TIER_B)**
1. Dépendance fournisseur pour le consensus. `Forecast` possiblement réécrit après publication.
2. Si son `Actual` est pris comme valeur d'autorité au lieu d'une valeur observée et stampée.
3. `LastUpdate` ≠ instant de publication. Historique révisé.
4. Redistribution facturée en sus ; prix primaire illisible.
5. Falsification : essai d'une semaine. Mesurer le fuseau de `Date`, le délai d'apparition de `Actual`, la stabilité
   de `CalendarId` et les réécritures de `Forecast`.
6. Rejet immédiat si `Forecast` est réécrit après l'actual sans trace, ou si `CalendarId` est instable.

**R9. tardis-machine (oracle C0) / abonnement Tardis**
1. Un second collecteur crée la tentation de « choisir la meilleure des deux sources » a posteriori.
2. Que ses fichiers alimentent DecisionV1.
3. `localTimestamp` Tardis ≠ heure de réception AurumShift. Ne jamais les substituer l'un à l'autre.
4. MPL ; replay payant ; Node ≥ 24.19 ; abonnement mensuel limité à 4 mois d'historique.
5. Falsification : différentiel par identifiant de trade (100 % d'égalité mesurée sur OKX).
6. Rejet immédiat sur une divergence de trades non expliquée.

**R10. Kalshi / Polymarket (probabilités d'événement)**
1. Liquidité faible sur certains strikes, ce qui donne des probabilités bruitées. La tentation de trader le signal
   sans test de valeur incrémentale (cf. LAB_PRIOR 016).
2. Un gate « risk-off si P(hausse) > x » non qualifié.
3. `updated_time` des marchés Kalshi = métadonnée, pas l'heure de la cote. Partition historique avant le 2026-08-06.
4. CGU non lues ; géoblocage du trading (pas de la lecture) ; schéma Kalshi migré (`*_fp`).
5. Falsification : capture forward plus test de valeur incrémentale pré-enregistré sur des fenêtres d'annonce.
6. Rejet immédiat si les CGU interdisent la réutilisation, ou si l'information n'apporte rien au-delà du calendrier.

---

## 6. Plans d'assemblage (BENCH_NOW / ADOPT_NOW)

Les cinq plans complets se trouvent dans `BENCH_NEXT_72H.md` (X1–X5). Ils suivent tous la même grille : BASELINE,
BASELINE_PLUS_COMPONENT, contrats d'entrée et de sortie, adaptateur, frontière d'autorité, corpus, métriques,
seuils, effort, code retiré, rollback. Ils couvrent R1, R2/R3, R4, R5, R7/R8.

Plans compacts pour les autres :

| Candidat | Baseline → + composant | Entrée → sortie | Frontière | Corpus / métriques | Succès / rejet | Effort | Code retiré | Rollback |
|---|---|---|---|---|---|---|---|---|
| Ledger PG hash-chain (K01) | logs ad hoc → table append-only `experiment_event(prev_hash,row_hash,…)` + Parquet hashé | événements A/B/C → chaîne vérifiable | dans l'autorité, en écriture seule | altération injectée ; 10⁵ lignes | altération détectée 100 % / non détectée | 0,5 j | pas de tracking-server | DROP du schéma |
| Funding officiels (CD12/13) | accrual PAPER → recalcul indépendant `rate × notionnel` aux instants de règlement | positions perp → coût de portage oracle | rapport seulement | 3 mois OKX ; mois Binance | écart ≤ 0,01 bps / 8 h / écart > 0,1 bps | 0,5 j | pas de collecte funding maison pour l'audit | supprimer le script |
| crepes (F03) | coût réalisé brut → bande conformal normalisée par la volatilité | (coût modèle, coût oracle) → [lo, hi] | moniteur SHADOW | journées Tardis | couverture ≥ 0,8 après saut / < 0,7 | 0,5 j | conformal maison | retirer le moniteur |
| Focus / River (F06/F07) | aucun → détection de rupture sur slippage et latence | séries de résidus → alarmes | SHADOW, jamais gate | période calme réelle bootstrapée par blocs | FAR ≤ 5 % à seuil calibré / > 20 % | 0,5 j | détecteur maison | idem |
| statsmodels VECM / Johansen (F02) | aucun → audit basis spot/perp et lead/lag cross-venue | séries C0 auditées horodatage → stats + FDR | analyse | C0 observation-only | résultat stable aux décalages ±1 pas / artefact d'horodatage | 1 j | — | — |
| MAPIE ACI (F04) | ACI maison → référence de test | même flux → écart de couverture | test seulement | synthétique | écart ≤ 0,005 / > 0,02 | 0,25 j | — | — |
| Pandera (K03) | contrôles Polars → schéma déclaratif | lot C0 → rapport d'échecs | frontière C0 | 1 M lignes, 8 fautes | mêmes comptes / divergence | 0,5 j | 0 (aucun gain mesuré) | retirer |
| Test troncature/préfixe (B17) | aucun → oracle de fuite des features | pipeline → égalité prefix vs full | test CI | features C0 | 0 écart / ≥ 1 | 0,5 j | — | — |
| tardis-machine (E05) | C0 → différentiel live par identifiant de trade | flux OKX → égalité trades/carnet | processus séparé | 24 h | 100 % trades / écart non expliqué | 0,5 j | collecteur de contrôle | arrêter |
| OKX announcements (I34), FRED dates (I07), BLS ICS (I03) | aucun → capture forward stampée | API → événements `(type, pTime, receipt_ts)` | observation-only | 72 h | 0 trou / 403 récurrent | 0,25 j chacun | scrapers | arrêter |

---

## 7. Priorisation

Le rang du backlog suit **VALEUR_ATTENDUE / (COÛT_INTÉGRATION × RISQUE_AUTORITÉ × TEMPS_JUSQU'À_LA_VÉRITÉ)**, évalué
qualitativement en H (élevé), M (moyen) ou L (bas). Le ratio n'est pas numérique : les entrées sont qualitatives.

### AURUMSHIFT_EXTERNAL_ACCELERATION_BACKLOG

| Rang | Item | Valeur | Coût | Risque d'autorité | Temps vers la vérité | Pourquoi ce rang |
|---|---|---|---|---|---|---|
| 1 | Vérifier seqId/prevSeqId OKX dans C0 (E02) | M | L (heures) | L | L | correctif d'intégrité, quasi gratuit |
| 2 | Oracle coût Tardis vs COST_CONTRACT_V1 (X1) | H | L | L | L (données déjà là) | condition du « NET » de l'endpoint |
| 3 | Plan d'inférence pré-enregistré + harnais Q1 (X2 : statsmodels/arch/PSR/hash) | H | L | L | L | évite les faux edges ; fixe N |
| 4 | Betting CS vendorisée comme moniteur (A05) | M | L | L | L | rend le peeking opérateur inoffensif |
| 5 | Timeline-ASOF pour rejouer B/C sur l'input identique (X4) | H | L–M | L (offline) | M | multiplie les paires A/B/C sans attendre |
| 6 | Ledger d'expérience PG hash-chain (K01) | M | L | L | L | lignée de l'expérience sans seconde autorité |
| 7 | Calendrier officiel assemblé + capture FF (X5) | M | M | L | M | comble le manque connu, autorité de date |
| 8 | ccxt.pro shadow OKX → futures venues (X3) | M–H | M | M | M | gros retrait de code potentiel ; migration |
| 9 | Trading Economics, essai 1 semaine | M | L–M | M | M | consensus et ids ; dépendance fournisseur |
| 10 | tardis-machine différentiel C0 | M | L | M | M | oracle de qualité C0 |
| 11 | Funding officiels (si PAPER perps) | M | L | L | M | coût de portage ; nul en spot |
| 12 | crepes + Focus/River moniteurs coût/latence | L–M | L | L | M | utiles après les premiers fills |
| 13 | Kalshi / Polymarket capture shadow | M (scientifique) | L | M | H (accumulation) | probabilité d'événement PIT-native |
| 14 | Achat Tardis Solo (TIER_C) | M | L (financier ~900–1 200 USD/mois) | L | L | **seulement si** X1 montre un écart matériel |
| 15 | VECM / Johansen sur basis C0 | L–M | L | L | M | après audit des horodatages |
| 16+ | Portefeuille, NLP, mémoire, infra | L | — | — | — | PARK jusqu'à un déclencheur |

### Listes demandées

**TOP_10_HIGHEST_VALUE_CANDIDATES**
1. Oracle de coût Tardis gratuit + walk-the-book + hftbacktest `tardis.convert`.
2. Pile d'inférence `statsmodels` (HAC, multitest, TOST) + `arch` (SPA/StepM/MCS) + préregistration hash.
3. Betting confidence sequence (`confseq`, vendorisée).
4. ccxt / ccxt.pro sous enveloppe PIT (avec l'action seqId OKX).
5. Timeline-ASOF Polars/DuckDB pour le rejeu offline A/B/C.
6. Ledger d'expérience Postgres append-only à chaîne de hash.
7. Calendrier officiel assemblé (BEA/Fed/ECB/BoE/BoJ/FRED) + ForexFactory en forward.
8. Trading Economics (essai TIER_B).
9. tardis-machine (+ abonnement Tardis conditionnel).
10. Kalshi / Polymarket (probabilités d'événement, shadow).

**TOP_5_FASTEST_WINS**
1. Contrôle seqId OKX.
2. Oracle de coût X1.
3. Pile d'inférence + plan hashé.
4. Calendriers officiels (ICS/RSS).
5. Timeline-ASOF.

**TOP_5_SCIENTIFIC_MULTIPLIERS**
1. Pile d'inférence pré-enregistrée (HAC/SPA/MinTRL).
2. Betting CS anti-peeking.
3. Oracle de coût (rend « net » vérifiable).
4. Timeline-ASOF (paires A/B/C sur input identique, plus nombreuses).
5. Kalshi / Polymarket (régime d'événement PIT-native).

**TOP_5_ENGINEERING_COST_REDUCERS**
1. ccxt / ccxt.pro.
2. arch + statsmodels (au lieu d'un bootstrap, de SPA et de corrections maison).
3. hftbacktest `tardis.convert` (reconstruction L2).
4. tardis-machine (normalisation live et replay).
5. Trading Economics (au lieu de 24–40 h d'assemblage, INFERENCE).

**TOP_5_INDEPENDENT_ORACLES**
1. Walk-the-book sur Tardis contre COST_CONTRACT_V1.
2. Funding officiel OKX `realizedRate` / Binance Vision.
3. tardis-machine / trades Tardis contre C0 (différentiel par identifiant).
4. Kalshi + Polymarket (probabilités croisées, ~2 points de pourcentage d'accord).
5. Bande conformal `crepes` sur coût réalisé contre coût modèle.

---

## 8. Ce qu'aucun composant externe ne résout

Ces points sont à construire en interne, au plus petit possible :

- **Attribution des gates.**
  - Classer chaque candidat B en QUORUM_ONLY_SUPPRESSED ou QUORUM_PLUS_OTHER_GATE exige la trace interne de
    DecisionV1 (quels gates auraient bloqué).
  - C'est de la logique métier : aucune librairie.
- **Honnêteté de l'Outcome contrefactuel B/C.** Cinq règles sont à pré-enregistrer :
  - même COST_CONTRACT_V1 et même règle de sortie que A ;
  - position isolée ;
  - deux scénarios de coût ;
  - contrôle négatif : des trades réels de A passés dans le pipeline shadow ;
  - lag HAC ≥ horizon de détention.

  Aucun outil off-policy n'est applicable (politiques déterministes).
- **Coût réalisé et fills passifs.** Aucun fill propre n'existe ; aucune donnée publique ne permet d'estimer le fill
  passif (LAB_PRIOR 006).
- **Instant réel de publication des actuals macro.** Aucun fournisseur examiné ne le donne : il faut stamper soi-même.
- **Borrow costs** : UNKNOWN_COST tant qu'aucun barème n'est fourni.
- **Normalisation cross-venue de l'OI et du funding** (unités, contrats). Elle est partiellement couverte par ccxt et
  reste spécifique à chaque venue.

---

## 9. Question finale : deux semaines d'ingénierie

> Quelles intégrations externes tester en premier pour maximiser la probabilité de découvrir un edge net réel ?

### Semaine 1 — rendre la mesure vraie

| Jours | Action | Bench |
|---|---|---|
| J1 | Contrôle seqId OKX dans C0. Geler et hasher le plan d'analyse du quorum. Installer la pile d'inférence (statsmodels, arch, CS vendorisée), calibrée sur le harnais Q1 aux N et φ attendus. | X2 |
| J2–J3 | **Oracle de coût contre COST_CONTRACT_V1** sur les journées Tardis gratuites (août, septembre, octobre 2026), BTC et DOGE, Binance et OKX, aux tailles PAPER. | X1 |
| J4–J5 | Rejeu timeline-ASOF pour produire les shadows B (et C) **sur les mêmes DecisionInput**. Contrôle négatif : trades réels de A passés dans le pipeline shadow. | X4 |

### Semaine 2 — élargir l'échantillon sans corrompre l'autorité

| Jours | Action | Bench |
|---|---|---|
| J6–J7 | Ledger hash-chain pour A/B/C. Moniteur CS. | — |
| J8–J9 | ccxt.pro shadow OKX (parité C0). | X3 |
| J10 | Calendrier officiel assemblé, pour étiqueter les fenêtres d'annonce comme strate d'analyse, pas comme gate. | X5 |
| J10 | Décision d'achat Tardis Solo **seulement si** X1 montre un écart de coût matériel. | — |

### Pourquoi cet ordre

1. **La probabilité de découvrir un edge net réel est bornée par trois choses, pas par la sophistication des
   modèles :**
   - la vérité du coût (sinon « net » est une hypothèse) ;
   - la validité de l'inférence sous dépendance et petits N (sinon on « découvre » du bruit dans 30 à 69 % des cas
     sous peeking, MEASURED) ;
   - le **nombre** de paires A/B sur input identique (≈ 250–500 outcomes supprimés requis pour un effet de
     +10 bps, MEASURED).
2. **Les trois premières intégrations attaquent chacune une de ces bornes** pour environ 3 j-dev au total. Elles sont
   gratuites (TIER_A) et hors runtime, avec un risque d'autorité minimal.
3. **Le rejeu timeline-ASOF est le seul levier qui raccourcit TIME_TO_SCIENTIFIC_TRUTH.** Il transforme
   l'historique d'observations C0 déjà capturé en paires shadow supplémentaires, sans attendre le forward. Cela vaut
   à condition que l'archive PIT C0 couvre la période et que l'Outcome contrefactuel respecte les cinq règles du §8
   (INFERENCE).
4. **ccxt, le calendrier et Tardis payant viennent ensuite.** Ils réduisent le coût d'ingénierie et élargissent la
   couverture, mais n'augmentent pas directement la probabilité de détecter un edge dans l'expérience quorum en cours.

---

## 10. Blocs finaux

```
TOP_10=1.Tardis_free_samples+walk_the_book+hftbacktest_tardis_convert(COST_ORACLE) > 2.statsmodels_HAC+arch_SPA_StepM_MCS+prereg_hash(INFERENCE_STACK) > 3.confseq_betting_CS_vendored(ANYTIME_MONITOR) > 4.ccxt+ccxt.pro_under_PIT_wrapper(+OKX_seqId_action) > 5.timeline_ASOF_Polars_DuckDB(OFFLINE_REPLAY) > 6.Postgres_append_only_hash_chain_experiment_ledger > 7.official_calendar_assembly(BEA_ICS,Fed_page+RSS,ECB,BoE,BoJ,FRED_dates)+ForexFactory_forward > 8.Trading_Economics_trial(TIER_B) > 9.tardis-machine(+conditional_Tardis_Solo_TIER_C) > 10.Kalshi+Polymarket_event_probabilities(SHADOW)
FASTEST_WINS=1.OKX_seqId_check_in_C0 > 2.COST_ORACLE_DIFF(X1) > 3.inference_stack+hashed_plan(X2) > 4.official_calendars_ICS/RSS > 5.timeline_ASOF(X4)
SCIENTIFIC_MULTIPLIERS=1.preregistered_HAC/SPA/MinTRL_stack > 2.betting_CS_anti_peeking > 3.Tardis_walk_the_book_cost_oracle > 4.timeline_ASOF_paired_A/B/C_replay > 5.Kalshi+Polymarket_event_probabilities
ENGINEERING_COST_REDUCERS=1.ccxt/ccxt.pro > 2.arch+statsmodels > 3.hftbacktest_tardis.convert > 4.tardis-machine > 5.Trading_Economics_API
INDEPENDENT_ORACLES=1.Tardis_walk_the_book_vs_COST_CONTRACT_V1 > 2.OKX_realizedRate+Binance_Vision_fundingRate > 3.tardis-machine/Tardis_trades_vs_C0_by_trade_id > 4.Kalshi+Polymarket_cross_probabilities > 5.crepes_conformal_band_on_realized_vs_modeled_cost

BENCH_NEXT_72H=X1.COST_ORACLE_DIFF_V1 ; X2.QUORUM_INFERENCE_PREREG_V1 ; X3.C0_CCXT_SHADOW_V1(+OKX_checksum_check) ; X4.PIT_TIMELINE_ASOF_REPLAY_V1 ; X5.EVENT_CALENDAR_ASSEMBLY_V1

DO_NOT_BUILD_YET=custom block bootstrap / optimal block length / SPA / StepM / MCS / multiple-testing corrections (use arch+statsmodels) ; custom historical L2 reconstruction (use hftbacktest tardis.convert on Tardis files) ; custom fill-simulation engine for market orders (walk-the-book oracle suffices; hftbacktest fill engine is defective, do not adopt either) ; new custom per-venue WebSocket collectors for future venues (ccxt.pro / tardis-machine shadow first) ; custom economic-calendar scrapers beyond official ICS/RSS (Trading Economics trial first) ; custom drift/changepoint detectors (River PageHinkley, changepoint_online Focus as references) ; custom conformal intervals (crepes / MAPIE as reference) ; experiment-tracking server or UI (hash-chain ledger + Parquet first; MLflow only as read-only mirror) ; portfolio optimizer (inverse-vol for 2 assets; skfolio when >=5-10 qualified assets) ; agent memory/RAG stack (pgvector in separate non-authoritative schema, later) ; any new datastore/stream bus (prove a bottleneck with pg_stat_statements first)

GAPS_WITH_NO_GOOD_EXTERNAL_COMPONENT=gate attribution QUORUM_ONLY_SUPPRESSED vs QUORUM_PLUS_OTHER_GATE (requires DecisionV1 internal gate trace) ; honest counterfactual Outcome for shadow arms B/C (same COST_CONTRACT_V1, exit rule, isolation, negative control) ; realized slippage and passive fill probability for own orders (no own fills; not estimable from public data) ; actual-publication instant of macro releases (no provider exposes it; must self-stamp receipt_ts) ; borrow cost history (no defensible free source; UNKNOWN_COST) ; cross-venue OI/funding unit normalization semantics (partial in ccxt, venue-specific residual) ; live verification of Binance/Bybit adapters from this lab (egress 451/403; not a component gap but an evidence gap)

VERDICT=RADAR_COMPLETE
```
