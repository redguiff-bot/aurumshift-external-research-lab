# raw_laneI — News / politique / géopolitique / NLP financier, priorité H : calendrier économique & événements structurés

Mission : AURUMSHIFT_EXTERNAL_ACCELERATION_RADAR_V1 — lane `laneI`. Horloge sandbox : 2026-10-05 (UTC), relevés entre
11:05 et ~11:50 UTC. Aucun code / base / credential AurumShift touché. Aucune clé API utilisée (tout est keyless ou noté 401).

Étiquettes : VERIFIED_FACT (source primaire lue, URL), MEASURED_BY_THIS_MISSION (exécuté ici, fichier de résultats cité),
VENDOR_CLAIM, INFERENCE, UNKNOWN. Les sources secondaires (agrégateurs de prix, blogs) sont marquées « SECONDAIRE / non vérifié ».

Venv : `scratchpad/venvs/laneI` (Python 3.11 ; requests, icalendar, python-dateutil ; torch 2.14.1 + transformers 5.18.0
pour le smoke FinBERT). Code et résultats : `reports/018_aurumshift_external_acceleration_radar_v1/bench/laneI/`.

## 0. Point de départ (LAB_PRIOR, non refait)

* LAB_PRIOR 010 : ALFRED = vintages US prouvés (jour) ; BLS ICS (08:30 ET) et BEA ICS (UTC) = horaires prévus
  machine-lisibles, 100 % d'accord de date avec ALFRED ; **aucune source officielle ne donne de consensus** ; le seul
  calendrier avec actual/estimate/prev testé (TipRanks) n'avait ni id, ni tz, ni révision ; aucun instant réel de
  publication intraday pour la macro.
* LAB_PRIOR 016 : Polymarket/Kalshi = classe PIT-native la plus propre (ADAPT, forward capture) mais non testée ;
  GDELT DOC PARK (429, fenêtre glissante), GDELT bulk (DATEADDED) = route PIT, **non exécutée** ; news non testées.

Apport nouveau ici : (1) comparaison mesurée FF JSON/XML vs BEA/Fed/ECB/BoE/BoJ, fuseaux, ids, rate-limit ;
(2) statut 2026 des fournisseurs payants (guest TE supprimé, Finnhub premium/Enterprise, EODHD perso, CryptoPanic sans
palier dev) ; (3) Polymarket/Kalshi exécutés en L2 (granularité, profondeur, limites de fenêtre, cross-check des
probabilités) ; (4) GDELT bulk exécuté (DATEADDED vs Last-Modified) ; (5) smoke FinBERT ; (6) OKX announcements
(événements crypto structurés, keyless).

## 1. Sondage des endpoints (MEASURED_BY_THIS_MISSION, 2026-10-05 ~11:05 UTC, curl, 1 requête chacun)

| Endpoint | HTTP | Corps / remarque |
|---|---|---|
| nfs.faireconomy.media/ff_calendar_thisweek.json | 200 | 79 évts, 10 658 o, Cloudflare `cache-control: max-age=60` |
| …/ff_calendar_thisweek.xml | 200 | mêmes 79 évts + balise `url` |
| …/ff_calendar_nextweek.json | 404 | semaine suivante non exposée |
| FMP /stable/economic-calendar et /api/v3/economic_calendar | 401 | "Invalid API KEY. Feel free to create a Free API Key" |
| Finnhub /calendar/economic | 401 | "Please use an API key." |
| Trading Economics `c=guest:guest` | **410** | "We are sorry, but the guest account has been discontinued." |
| EODHD `api_token=demo` economic-events | 403 | "Forbidden" |
| BLS bls.ics | **403** | page Akamai "Access Denied" (UA navigateur testé aussi) — LAB_PRIOR 010 l'avait lu → EGRESS_BLOCKED aujourd'hui |
| BEA ICS / release_dates.json | 200 | 119 évts / 30 releases, 142 dates |
| Fed fomccalendars.htm, press_all.xml | 200 | |
| ECB / BoE / BoJ calendriers | 200 | |
| FRED fred/releases/dates sans clé | 400 | "Variable api_key is not set" |
| api.polygon.io/v1/reference/economic-calendar | 404 | aucun endpoint calendrier |
| Alpha Vantage NEWS_SENTIMENT apikey=demo | 200 | message "demo API key is for demo purposes only" (pas de données) |
| CryptoPanic /api/developer/v2/posts | 404 | "Valid paths are /api/{growth\|growth_weekly\|enterprise}/v2/…" → palier dev disparu (INFERENCE) |
| NewsAPI, CoinDesk/CCData news, Event Registry, Benzinga, JBlanked, FXStreet calendar-api | 401 | clé requise |
| Investing.com, FXStreet site, Tiingo, Nasdaq Data Link | 403 | |
| GDELT DOC API | 429 (15,5 s) puis 200 avec corps `{}` en 24,3 s | DOC API inutilisable de cet egress |
| GDELT bulk lastupdate.txt | 200 | (http→https 301) |
| Polymarket gamma, Kalshi series, Manifold | 200 | |

## 2. Calendrier : fiches et mesures L2

Scripts : `fetch_calendars.py <tag> [sources]` (snapshots bruts + meta : receipt_time_utc, status, Last-Modified, ETag,
sha256), `analyze_calendars.py` → `results/calendar_compare.json`. Snapshots : s1 11:05:38Z (tout), s2 11:12:50Z
(FF, BEA, Fed), s3 11:22:08Z (FF JSON), s4 11:47:16Z (FF JSON+XML, après la régénération horaire de 11:42:18Z).

### I01 ForexFactory export (nfs.faireconomy.media) — SHADOW (forward capture forecast/previous) — L2
* Champs JSON (MEASURED) : `title, country, date, impact, forecast, previous`. XML : + `time`, `url`. **Pas de champ
  `actual`**, ni dans JSON ni dans XML, y compris pour les évènements EUR déjà publiés (PMI 07:15-08:00 UTC) alors que
  le fichier date de 10:42:15Z → l'export ne sert pas à capter l'actual.
* Fuseaux (MEASURED) : JSON = heure de New York avec offset explicite (`2026-10-05T03:15:00-04:00`, 79/79 en -04:00) ;
  XML = **UTC** sans marqueur (`10-05-2026` / `7:15am`). Vérifié : 79/79 évts JSON→UTC == XML, 0 écart. Piège : un
  parse naïf de l'XML comme heure locale ou du JSON sans offset décale de 4-5 h (et le décalage change au DST US, pas EU).
* Ids : aucun id d'occurrence. L'`url` XML contient un **id de série** (`/calendar/798-opec-jmmc-meetings`) : 76 ids
  pour 79 évts, chaque id ↔ un seul (titre, pays) → utilisable comme clé de série ; clé d'occurrence à fabriquer
  (series_id + horaire prévu), fragile si l'horaire bouge.
* Qualité (MEASURED) : quasi-doublon `ADP Weekly Employment Change` USD à 08:15 et 08:16 ET (previous "" vs "20.0K") ;
  `10-y Bond Auction previous = "4.83|2.7"` (champ composite) ; impact US cette semaine : 1 High (FOMC Minutes
  18:00Z le 07/10), 4 Medium (ISM Services, Claims, UoM ×2), Trade Balance = Low.
* Fraîcheur / limite (MEASURED + texte fournisseur) : s1 et s3 identiques (sha256 `d790a7602372`, Last-Modified
  10:42:15Z) ; **s2 = HTTP 429** après ~4 requêtes en 7 min depuis l'egress partagé, page : « You've exceeded the limit
  for Calendar Export requests. Please wait five minutes before trying again. The Calendar export file is only updated
  once per hour. Requesting it more than that is unnecessary and can result in being blocked. » → contrat de fraîcheur
  = horaire, polling ≤ 1/h, et un fichier horaire **ne peut pas servir d'horodatage PIT de l'actual**.
* s4 (11:47:16Z, MEASURED) : XML **régénéré** (Last-Modified 11:42:18Z, nouvel ETag `6ac38d1a-6a64`) mais contenu
  identique champ à champ (79/79, 0 ajout/retrait/modif) ; JSON **de nouveau 429** alors que la requête JSON précédente
  datait de 25 min → le compteur est partagé par l'egress (autres agents/utilisateurs derrière la même IP, INFERENCE) :
  en production il faut une IP dédiée ou accepter des trous. JSON et XML ont des compteurs distincts (XML 200 au même
  instant).
* Couverture banques centrales cette semaine : FOMC Minutes (High), ECB Accounts (Low), BOJ Ueda (High), orateurs FOMC
  (Low), BoE Credit Conditions. Cohérence : FOMC Minutes 07/10 14:00 ET = 18:00Z, conforme à la convention Fed (le RSS
  Fed date le statement du 16/09 à 18:00:00 GMT — VERIFIED dans `s1_fed_press_rss.xml`).
* CGU : forexfactory.com/notices → 403 (WebFetch et curl), donc **CGU non lues = UNKNOWN**. Fair Economy, Inc. est
  l'éditeur (SECONDAIRE). Aucune licence de redistribution visible. Risque CGU : moyen-élevé pour un usage commercial ;
  acceptable en forward capture interne à faible fréquence (INFERENCE, à valider par l'opérateur).

### I02 BEA ICS + release_dates.json — ADOPT_NOW (horaire officiel) — L2
* ICS : 119 VEVENT, 2025-01-07 → 2026-12-23, DTSTART en **UTC (Z)**, UID uniques (119/119), titre inclut le stade
  (Advance/Second/Third). JSON : 30 releases, 142 dates ISO avec `+00:00`, `file_last_updated 2026-07-13`, **6 dates
  dupliquées** (ex. trade 2025-06-05 ×2). (MEASURED)
* Cross-check FF : Trade Balance BEA 2026-10-06T12:30Z == FF `Trade Balance` 08:30-04:00 (MEASURED). « Services Supplied
  Through Affiliates » 14:00Z absent de FF (couverture FF ⊂ officiel pour les releases mineures).
* Stabilité : Last-Modified ICS 2026-07-13, JSON 2026-07-14 ; hash identique s1/s2. Un fichier mis à jour 3 mois avant
  ne garantit pas les reports de dernière minute (INFERENCE ; LAB_PRIOR 010 a vu le report shutdown Q3-2025 intégré).

### I03 BLS ICS — ADOPT_NOW (LAB_PRIOR 010) mais EGRESS_BLOCKED aujourd'hui
* 403 Akamai avec UA scripté et UA navigateur (MEASURED). LAB_PRIOR 010 l'avait lu (313 évts, 08:30/10:00 ET).
  Conséquence d'ingénierie : cache local + fallback FRED `releases/dates` (date) + règle d'heure par release.

### I04-I06 Banques centrales — ADOPT_NOW (dates) — L2
* Fed (MEASURED, parse HTML) : 2026 = Jan 27-28, Mar 17-18*, Apr 28-29, Jun 16-17*, Jul 28-29, Sep 15-16*, **Oct 27-28**,
  Dec 8-9* ; 2027 listé aussi. **Pas d'heure sur la page** ; heure 14:00 ET confirmée par pubDate RSS (18:00:00 GMT le
  16/09) et cohérente avec Kalshi `close_time 17:55Z / expected_expiration 18:05Z` (MEASURED). Piège : le HTML change
  de sha256 entre s1 et s2 sans changement de Last-Modified (contenu dynamique) → détecter les changements par parse.
* ECB (MEASURED) : réunions politique monétaire 28-29/10/2026 et 16-17/12/2026 (format jj/mm/aaaa) ; pas d'heure.
* BoE (MEASURED) : 2026 = 5 Feb, 19 Mar, 30 Apr, 18 Jun, 30 Jul, 17 Sep, **5 Nov**, 17 Dec ; 2027 publié ; « Current Bank
  Rate 3.75% Next due: 5 November 2026 ». Pas d'heure.
* BoJ (MEASURED) : tableau 2026 (dates de MPM + Outlook/Summary/Minutes) ; heure de décision non fixe (UNKNOWN).
* Ces pages sont des **sources d'autorité pour la date**, pas pour la valeur ; l'heure vient d'une règle (INFERENCE
  sauf Fed où RSS l'atteste).

### I07 FRED fred/releases/dates — BENCH_NOW (clé gratuite) — L0/L1
* VERIFIED (docs) : champs `release_id, release_name, date` ; **date seulement** ; dates futures seulement avec
  `include_release_dates_with_no_data=true` ; « release dates are published by data sources and do not necessarily
  represent when data will be available on the FRED or ALFRED websites ». Sans clé : 400 (MEASURED). `release_id`
  = identifiant stable de série de releases (bon pivot avec ALFRED de LAB_PRIOR 010).

### I08 Trading Economics — BENCH_NOW (meilleur schéma payant) — L1
* VERIFIED (docs snapshot) : `CalendarId`, `Date`, `Country`, `Category`, `Event`, `Actual`, `Previous`, `Forecast`
  (consensus), `TEForecast`, `Revised`, `Importance` 1-3, `LastUpdate`, `Ticker`, `Reference`, `ReferenceDate`,
  `Source`, `Unit` ; filtres importance/date/pays/CalendarId et **« updates »** (évènements modifiés). tz de `Date` non
  explicitement documentée dans ce que j'ai lu (UNKNOWN ; probablement UTC).
* MEASURED : `guest:guest` → **410 « guest account has been discontinued »** → aucun test keyless possible.
* Prix : page officielle rendue en JS → montant non lisible (UNKNOWN_PRICE primaire) ; texte primaire : « trial users are
  limited to 100000 data points and 100 requests ». SECONDAIRE non vérifié : Standard ~149-199 USD/mois → TIER_B ;
  la redistribution change le prix (texte d'un agrégateur, non vérifié).
* PIT : `LastUpdate` = dernière modification de la ligne, **pas** l'instant de publication de l'actual ; historique
  vraisemblablement réécrit avec `Revised` (INFERENCE) → à capturer en forward avec stamp de réception.

### I09-I13 autres payants
* FMP (WATCH) : docs/prix 403 depuis cet egress ; 401 sans clé (MEASURED). SECONDAIRE : endpoint `/stable/economic-
  calendar`, v3 retiré le 2025-08-31, champs `date, country, event, currency, previous, estimate, actual, change, impact,
  changePercentage`, plan gratuit 250 req/j. Pas d'id ni de stamp de mise à jour connus.
* Finnhub (PARK) : VERIFIED swagger officiel : `"premium": "Premium Access Required"`, « Historical events and surprises
  are available for Enterprise clients », champs `actual, prev, estimate, impact, time, unit, country, event` — **pas
  d'id, `time` sans tz**.
* EODHD (PARK) : VERIFIED docs : champs `type, comparison, period, country, date, actual, previous, estimate, change,
  change_percentage`, « available from 2020 », pas d'id, tz non spécifiée ; inclus dans « All-In-One and Fundamentals
  Data Feed plans » ; page prix : ALL-IN-ONE 99,99 USD/mois, plans « Personal use », commercial sur devis.
* Benzinga (WATCH) : VERIFIED docs : `id`, `date`, `time` (« EST »), `importance` 0-5, `actual`, `consensus`, `prior`,
  `updated` (unix, dernière modification ; paramètre `updated` = delta sync), `confirmed`. Meilleur modèle d'id + delta,
  prix sur devis (E/UNKNOWN).
* Polygon/Massive (REJECT pour ce besoin) : 404 sur tout chemin calendrier testé.
* JBlanked (REJECT) : 401 ; docs : champs dérivés `Outcome/Strength/Quality` ; source des données non attribuée dans la
  doc lue → chaîne de licence douteuse (re-packaging FF/MQL5 probable, INFERENCE).
* Investing.com (REJECT), FXStreet (PARK, 401/403), Econoday (WATCH, licence opaque), Nasdaq Data Link (REJECT, hors sujet).

## 3. Marchés de prédiction (L2)

Scripts : `prediction_markets.py`, `prediction_depth.py`, `crosscheck_fed_oct.py` → `results/prediction_*.json`,
`results/crosscheck_fed_oct.json`.

### I27 Polymarket — SHADOW
* Gamma : event `fed-decision-in-october-20260617190323537` (createdAt 2026-06-17, endDate 2026-10-29T03:59Z), 5 marchés
  (−50, −25, 0, +25, +50+ bp), champs `outcomePrices, bestBid, bestAsk, lastTradePrice, volume, updatedAt, conditionId,
  clobTokenIds`. Latence 59-502 ms. (MEASURED)
* CLOB `prices-history` (MEASURED) : `interval=1d&fidelity=1` → 1 441 points, pas médian 60 s ; `startTs/endTs` 7 j
  fidelity 1 → 10 080 points (1/min) ; **fenêtre max 15 j** (15 j → 200, 18 j/21 j/30 j → 400 « interval is too long ») ;
  `interval=max&fidelity=60` → seulement ~30 j (721 pts) ; `interval=all&fidelity=1440` → 110 points journaliers depuis
  2026-06-19. Marché **clos** (Oct-2025, résolu) : minute-data encore servie (2 514 pts sur 3 j). Donc reconstruction
  historique = boucle de fenêtres ≤15 j ; granularité 1 min ; timestamps en epoch s.
* `book` : timestamp ms + hash ; `data-api/trades` : timestamp s, wallet pseudonyme. (MEASURED)
* Rate limits VERIFIED (docs) : CLOB `/prices-history` 1 000 req/10 s ; data-api général 1 000 req/10 s.
* Géoblocage VERIFIED (docs geoblock) : **France, US, UK, DE bloqués en trading** (« Block completely »). Lecture publique
  OK depuis l'egress. CGU de réutilisation des données : non lues (page ToS rendue en JS) → UNKNOWN.

### I28 Kalshi — SHADOW (meilleur des deux pour la macro US)
* Série KXFED (MEASURED) : `settlement_sources` = page FOMC de la Fed ; `contract_terms_url` PDF ; events ouverts
  KXFED-26OCT/26DEC/27JAN/27MAR/27APR. Ladder KXFED-26OCT : `T3.75` 0,99 / **`T4.00` bid 0,18 ask 0,20** / `T4.25` ≤0,02.
* **Cross-check (MEASURED)** : P(hausse) Kalshi ≈ 0,19 (mid T4.00) vs Polymarket « +25 bp » bid 0,16/ask 0,17 + « +50 »
  0,0045 ≈ 0,17 → accord à ~2 pp, ce qui valide l'usage comme ORACLE indépendant de probabilité d'évènement.
* Candlesticks : `period_interval` 1/60/1440 ; 1 min sur 7 j → 400 « max candlesticks: 5000 » ; 1 min sur 3 j → 2 081
  bougies (bougies seulement quand activité → pas irréguliers, max 3 000 s) ; 1 h sur 60 j → 1 038 ; 1 j sur 400 j → 380
  depuis 2025-09-01. Trades : `created_time` µs, `trade_id`, `taker_side`, `count_fp`, `yes_price_dollars`. (MEASURED)
* Pièges (MEASURED) : schéma migré vers `*_fp` / `*_dollars` (les champs legacy `volume`, `yes_bid` renvoient `null`) ;
  `updated_time` des marchés = 2026-09-30 alors que les prix sont courants → métadonnée, **pas** l'heure de cote ;
  partition live/historique : `/historical/cutoff` → trades/markets < 2026-08-06 seulement via `/historical/*`
  (VERIFIED docs historical_data ; page historique de trades obtenue, 100 trades 2026-05-18→2026-08-05).
* `forecast_percentile_history` (docs : percentiles historiques de la prévision implicite — idéal comme « consensus
  marché » PIT) : **400 bad_request** sur KXCPI/KXPAYROLLS/KXU3/KXFED, 2 serveurs, period 60/1440 → FAILED_L1
  (auth requise ou séries non éligibles : UNKNOWN). Alternative faisable : dériver médiane/quantiles du ladder de strikes
  à partir des candles (calcul trivial).
* CGU / Developer Agreement : 429 sur le PDF → UNKNOWN. Kalshi = marché régulé CFTC (VERIFIED sur `contract_url`
  « product-certifications »). Accès aux données en lecture sans clé.

### I29 Manifold — PARK (play money).

## 4. News / NLP

* I20 GDELT 2.0 bulk — SHADOW (MEASURED, `gdelt_bulk_probe.py`) : `lastupdate.txt` → `20261005111500.export.CSV.zip`
  (69 755 o, md5 OK, 1 075 lignes × 61 colonnes). **DATEADDED = 20261005111500 pour 100 % des lignes, alors que le fichier
  a Last-Modified 11:05:56Z et a été reçu à 11:08:50Z** → DATEADDED est une étiquette de lot ~9 min *après* la
  disponibilité réelle : utilisable comme borne conservatrice (pas de fuite), à doubler d'un stamp de réception.
  SQLDATE : 1 030 lignes du jour, le reste des jours/années passés (évènements re-mentionnés). DOC API : 429 puis `{}`
  après 24 s → PARK (confirme LAB_PRIOR 016).
* I21 NewsAPI — REJECT : VERIFIED pricing : Developer gratuit « 24 hour delay », « cannot be used in a staging or production
  environment » ; Business 449 USD/mois ; Advanced 1 749 USD/mois.
* I22 CryptoPanic — PARK : palier `developer` refusé, seuls `growth|growth_weekly|enterprise` (MEASURED) ; prix UNKNOWN
  (pages en JS).
* I19 Alpha Vantage — PARK : VERIFIED premium 49,99-249,99 USD/mois, free 25 req/j.
* I23-I26 CoinDesk/CCData, RavenPack/Bigdata, Factiva, Event Registry : clé/devis, non testés (UNKNOWN_PRICE ; E pour
  RavenPack/Factiva).
* I30 FinBERT — REJECT pour l'usage (MEASURED, `finbert_smoke.py`) : 8 titres ×4, CPU, 1,10-1,45 s/titre, déterministe
  bit-à-bit sur 2 passes. Erreurs flagrantes : « US payrolls beat expectations, unemployment falls » → negative 0,956 ;
  « Crypto exchange hacked, $200 million drained » → neutral 0,94 ; « ECB cuts deposit rate by 25 bp » → negative 0,593 ;
  « Treasury yields unchanged ahead of FOMC minutes » → negative. Le client HF hub (xet) a bloqué >170 s via le proxy ;
  téléchargement direct `curl` des fichiers en ~5 s puis chargement local OK (note opérationnelle).
* I31-I33 FinGPT / zero-shot / LLM structuré — PARK. **Risque de fuite** : un LLM de knowledge cutoff postérieur à la date
  de l'évènement « connaît » l'issue (ex. décision FOMC, chiffre NFP) → classification ou extraction appliquée à des titres
  historiques = look-ahead silencieux dans un backtest. Usage admissible seulement en forward/shadow avec modèle versionné
  et date de cutoff < début de la fenêtre de test, ou sur des tâches purement syntaxiques vérifiées.

## 5. Crypto-spécifique

* I34 OKX `/api/v5/support/announcements` — BENCH_NOW (MEASURED) : keyless 200 ; `annType=announcements-new-listings`
  5 pages ; sans filtre 7 pages × 20 → plus ancien 2025-11-12 (~11 mois) ; champs `title, url, pTime (ms),
  businessPTime (ms), annType`. `pTime` = instant de publication ; `businessPTime` = heure métier arrondie. Types vus :
  `announcements-delistings`, `announcements-new-listings`, `trading-updates-us-aus` → contenu possiblement régionalisé
  selon l'IP (INFERENCE). `announcements-types` exige auth (7002). Pertinent pour C0 (OKX est une des 3 venues).
* I35 Tokenomist (unlocks) — WATCH : plans payants non chiffrés ; peu utile pour BTC/DOGE.

## 6. Option payante TIER_A/B vs assemblage gratuit officiel (INFERENCE chiffrée, à valider)

| Critère | A. Fournisseur payant (TE en tête ; FMP/Finnhub/EODHD en dessous) | B. Assemblage gratuit (BEA ICS + BLS ICS + FRED dates + Fed/ECB/BoE/BoJ + FF export) |
|---|---|---|
| Horaire prévu + tz | oui (TE `Date`, tz à confirmer ; Finnhub/EODHD sans tz) | oui, officiel (BEA UTC, BLS ET, FF JSON offset/XML UTC) ; banques centrales = date + règle d'heure |
| Importance | TE 1-3 ; Benzinga 0-5 ; FMP impact | FF impact (Low/Med/High) seulement ; officiels : aucune |
| Consensus/forecast | **oui** (seule vraie valeur ajoutée) | FF `forecast` (source non documentée, CGU UNKNOWN), sinon rien |
| Previous / révisions | TE `Previous` + `Revised` | FF `previous` ; révisions via ALFRED (LAB_PRIOR 010) |
| Actual + stamp PIT de l'actual | actual oui ; **stamp de publication non** (TE `LastUpdate`, Benzinga `updated` = dernière modif) | actual depuis ALFRED/BLS/BEA en J+0 (date) ; aucun stamp intraday |
| Ids stables | TE `CalendarId`, Benzinga `id` ; FMP/Finnhub/EODHD aucun | BEA UID, BLS UID, FRED `release_id`, FF id de série ; occurrence = (série, horaire) |
| Banques centrales | oui (TE) | oui, officiel, dates seulement |
| Heures d'ingénierie (INFERENCE) | 8-16 h adaptateur + normalisation + forward capture | 24-40 h (6-8 parseurs, règles d'heure, dédup, mapping des noms FF↔officiel, monitoring des 403/429) |
| Coût | TIER_B (TE, prix SECONDAIRE) ; TIER_A (EODHD perso, FMP probable) | 0 € |
| Risques CGU | redistribution facturée ; EODHD « Personal use » | FF : CGU non lues ; officiels : domaine public / citation |
| Robustesse egress | clé, SLA | BLS 403 aujourd'hui, FF 429 à >~1 req/5 min |

Lecture : pour l'**horaire** (chemin critique = savoir quand masquer/étiqueter une fenêtre autour d'une publication),
l'assemblage officiel suffit et est autoritaire (ADOPT_NOW). Le payant n'apporte vraiment que **consensus + importance +
CalendarId** ; aucun fournisseur examiné ne fournit l'**instant réel de publication de l'actual** → dans tous les cas
AurumShift doit stamper lui-même (receipt_time) en forward. Recommandation : B maintenant ; TE (ou Benzinga si devis
raisonnable) en BENCH_NOW sur un essai 1 semaine (100 requêtes) pour mesurer : tz de `Date`, latence entre heure prévue
et apparition de `Actual`, stabilité de `CalendarId`, réécriture de `Forecast` après publication.
Les marchés Kalshi/Polymarket apportent une **probabilité d'évènement PIT-native, minute par minute**, ce que n'offre
aucun calendrier (SHADOW, oracle indépendant, jamais autorité).

## 7. Commandes reproductibles

```
cd reports/018_aurumshift_external_acceleration_radar_v1/bench/laneI
PY=$SCRATCH/venvs/laneI/bin/python
$PY fetch_calendars.py s1                 # puis s2… espacés (FF : ≥ 5 min, utile ≥ 1 h)
$PY analyze_calendars.py                  # -> results/calendar_compare.json
$PY prediction_markets.py ; $PY prediction_depth.py ; $PY crosscheck_fed_oct.py
$PY kalshi_forecast_percentiles.py        # -> 400 (FAILED_L1)
$PY gdelt_bulk_probe.py
FINBERT_PATH=<dossier local curl> HF_HUB_OFFLINE=1 $PY finbert_smoke.py
python3 make_candidates_csv.py            # -> evidence/candidates_laneI.csv
```
Les dossiers `raw/` contiennent les réponses brutes (< 200 Ko chacune).

## 8. UNKNOWN restants
CGU ForexFactory ; CGU réutilisation Polymarket et Developer Agreement Kalshi ; prix TE/FMP/Finnhub/Benzinga/Econoday/
CryptoPanic/RavenPack (primaire illisible ou devis) ; tz du champ `Date` TE ; existence d'un stamp de publication de
l'actual chez quelque fournisseur que ce soit ; éligibilité de `forecast_percentile_history` Kalshi ; si FF remplit un
jour `actual` (non observé) ; licence exacte du dépôt HF ProsusAI/finbert ; heure de décision BoJ.
