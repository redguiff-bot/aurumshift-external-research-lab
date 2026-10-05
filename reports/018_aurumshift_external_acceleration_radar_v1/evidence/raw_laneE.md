# raw_laneE — Données de marché / C0 (collecte multi-venue Binance, OKX, Bybit)

Mission AURUMSHIFT_EXTERNAL_ACCELERATION_RADAR_V1, lane E. Date sandbox : 2026-10-05 (UTC). Aucun code AurumShift lu.
Étiquettes : VERIFIED_FACT (source primaire citée), MEASURED_BY_THIS_MISSION (exécuté ici), UPSTREAM_BENCHMARK,
VENDOR_CLAIM, INFERENCE, UNKNOWN. Bench : `bench/laneE/` (scripts + JSON). Venvs : `scratchpad/venvs/laneE` (py3.11),
`scratchpad/venvs/laneE313` (py3.13, pour cryptofeed 3.x).

## 0. Ce qui est repris de LAB_PRIOR (non refait)
- LAB_PRIOR 005 : OKX v5 public = meilleure couverture dérivés keyless (funding, OI, OI-history 5 min, liquidations, basis) ;
  Binance main API 451 / Bybit 403 depuis l'egress (pas un verdict) ; Binance Vision = référence bulk (µs dans les fichiers
  spot 2025+) ; OKX WS :8443 coupé par l'egress, port 443 OK ; aucune source PIT-native ; funding/OI sont spécifiques venue.
- LAB_PRIOR 017 : ccxt 4.5.84 ADAPT (barre en formation renvoyée sur 4 venues ; pas de receipt ts) ; cryptofeed 2.4.1
  ADAPT (AGPL, receipt ts natif, 39 commits/12 m) ; tardis-python ADAPT (timestamp + local_timestamp) ; nautilus LGPL ;
  hummingbot PARK. Résiduel custom identifié : receipt stamping, forming-bar, unités, provenance, gap detection.

Apport NOUVEAU de cette lane : versions 2026-10 (ccxt 4.5.85, cryptofeed 3.0.1 réécrit, tardis-machine 18.3.8,
barter-data 0.13.0), changement OKX (checksum carnet déprécié 2026-06-23), matrice de capacités 12 surfaces × 3 venues,
différentiel L3 « même trade par trois chemins », mesure du résiduel custom, prix commerciaux publiés.

## 1. API natives — faits PIT utiles (sources primaires)
### OKX v5 (docs https://www.okx.com/docs-v5/en/ et changelog https://www.okx.com/docs-v5/log_en/)
- VERIFIED_FACT (changelog 2026-06-23) : « Deprecation of checksum field in order book channels … The checksum field is still
  present … but its value is fixed to 0 and must no longer be used for integrity verification. Please use seqId/prevSeqId »
  — canaux `books`, `books-l2-tbt`, `books50-l2-tbt` ; `books5`/`bbo-tbt` n'ont pas de checksum.
  MEASURED_BY_THIS_MISSION : 263 + 335 messages `books` (BTC-USDT, BTC-USDT-SWAP) en 30 s : **100 % checksum = 0**.
  ⇒ toute implémentation CRC32 « maison » héritée (C0 ?) échouerait à 100 % ou serait inopérante — à vérifier côté AurumShift.
- VERIFIED_FACT (changelog) : nouveau canal/endpoint `books-rpi` (400 niveaux, 100 ms WS, REST 200 ms), « No checksum » ;
  noms ELP retirés au profit de RPI.
- VERIFIED_FACT (docs candles) : champ `confirm` : « 0 : K line is uncompleted 1 : K line is completed » ; tableau
  `[ts,o,h,l,c,vol,volCcy,volCcyQuote,confirm]`. MEASURED : dernière barre native `confirm="0"` sur les 4 instruments.
- VERIFIED_FACT (docs trades WS) : « Every update may aggregate multiple trades. The message is sent only once per taker
  order, filled price, source. The count field is used to represent the number of aggregated matches. »
- VERIFIED_FACT (changelog) : `GET /api/v5/public/liquidation-orders` figure sous « Delisted endpoints from the document ».
  MEASURED : il répond encore (code "0", 5 détails `bkLoss,bkPx,ccy,posSide,side,sz,time,ts`) ⇒ endpoint fantôme : ne pas
  en faire une dépendance ; utiliser le canal WS `liquidation-orders` (documenté : « doesn't represent the total number of
  liquidations »).
- VERIFIED_FACT : funding-rate REST « Rate Limit: 10 requests per 2 seconds, IP + Instrument ID » ; books « 40 requests per 2 seconds, IP ».
- MEASURED : horloge OKX vs locale (fetchTime) : offset +76 ms au point milieu, RTT 345 ms (via proxy).

### Bybit v5 (https://bybit-exchange.github.io/docs/v5/…)
- VERIFIED_FACT (websocket/public/orderbook) : `ts` = « timestamp (ms) that the system generates the data » ; `u` update ID
  (« Occasionally, you'll receive "u"=1 … snapshot due to the restart of the service ») ; `seq` cross sequence ; `cts` =
  « timestamp from the matching engine … can be correlated with T from public trade channel » ; snapshot L1 re-poussé après
  3 s sans changement avec le même `u`. Pas de checksum.
- VERIFIED_FACT (all-liquidation) : topic `allLiquidation.{symbol}`, champs `ts`, `T`, `S` (Buy = long liquidé), `v`, `p` (bankruptcy price).
- VERIFIED_FACT (market/open-interest) : `openInterest` « sum of both sides », nouveau `singleOpenInterest` (single side) ;
  unité BTC pour BTCUSDT linéaire. ccxt 4.5.85 ne référence pas `singleOpenInterest` (grep = 0) — INFERENCE : resté dans `info`.
- Exécution impossible (403 egress) — non conclusif.

### Binance spot / USD-M
- VERIFIED_FACT (https://github.com/binance/binance-spot-api-docs/blob/master/web-socket-streams.md) : Diff. Depth Stream
  `<symbol>@depth[@100ms]`, « Update Speed: 1000ms or 100ms », champs `E` (event time), `U`/`u`.
- developers.binance.com renvoie 302/202 (challenge JS) depuis le sandbox ⇒ docs USD-M non lues ici (UNKNOWN direct) ;
  structure lue dans le code ccxt (commentaires de payload) : forceOrder `E` + `o.T`, depth futures `U/u/pu`.
- Exécution impossible (451 egress) ; bulk via data.binance.vision déjà couvert par LAB_PRIOR 005.

## 2. ccxt 4.5.85 (MIT) — fiche principale
- VERIFIED_FACT : PyPI ccxt 4.5.85 publié 2026-10-01 ; LICENSE MIT ; 3 937 commits sur 3 mois (dont 2 340 bot de release),
  dernier commit 2026-10-05 (clone partiel).
- VERIFIED_FACT : `wiki/ccxt.pro.manual.md` ligne 3 : « CCXT Pro is a free part of CCXT that adds support for WebSocket
  streaming » ; MEASURED : `import ccxt.pro` fonctionne depuis le paquet PyPI gratuit.
- Matrice `has` (MEASURED, lecture statique, `bench/laneE/ccxt_has_matrix.json`) — points saillants :
  - OKX : tout True sauf `fetchBidsAsks` (None, mais `watchBidsAsks` True via `bbo-tbt`), `fetchLiquidations` None,
    `watchLiquidations` 'emulated' ; `fetchPremiumIndexOHLCV` False.
  - Binance/BinanceUSDM : `fetchLiquidations` False (REST public retiré) mais `watchLiquidations` True ; mark/index/premium OHLCV True.
  - Bybit : `fetchFundingRate` 'emulated', `fetchMarkPrice` None, `watchLiquidations` True, `fetchBidsAsks` 'emulated'.
  - rateLimit interne : binance 50 ms, okx 110 ms, bybit 20 ms (throttle client).
- L2 REST OKX (MEASURED, `okx_rest_l2.json`, BTC/DOGE spot+swap, ~45 requêtes) :
  - Latence par appel 255–485 ms via proxy (natif 215–600 ms) : pas de surcoût mesurable ccxt vs aiohttp brut.
  - Fidélité parse ticker : bid/ask/timestamp == `info` brut sur 4/4 ; clés `info` == clés natives sur 4/4 ⇒ **brut conservé**.
  - OHLCV : ccxt renvoie 6 colonnes, natif 9 ; **flag `confirm` perdu** ; dernière barre = barre en formation (âge 1,8–59,9 s) 4/4.
  - Carnet REST : niveaux 3 colonnes (nb d'ordres OKX perdu), **`nonce=None` alors que la réponse native porte `seqId`**.
  - Funding courant OKX : **`timestamp=None`** (ts natif présent dans `info.ts`) ; `fundingTimestamp` = prochaine échéance
    (16:00), `nextFundingTimestamp` = suivante ; interval '8h' ; markPrice/indexPrice None. Lecture de code : Binance
    (`time`) et Bybit remplissent `timestamp` ⇒ perte spécifique OKX.
  - Funding history : pas 28 800 000 ms ; `realizedRate` gardé dans `info`.
  - OI courant : `openInterestAmount` en **contrats** (BTC 2 897 250 contrats × 0,01 = 28 972 BTC = `oiCcy` natif ; DOGE ×1000) ;
    `baseVolume` (déprécié) donne la base. OI history 5 min OK (10 points, ts alignés 5 min).
  - fetchMarkPrice OKX : indexPrice None ⇒ basis exige `fetchIndexOHLCV` (OK) ou natif.
  - fetchLiquidations OKX : `NotSupported` ; endpoint natif « délisté » répond.
- L2 WS ccxt.pro OKX 30 s (MEASURED, `okx_ws_l2.json`, BTC spot + swap, `watchOrderBook` canal `books`, `watchTrades`,
  `watchBidsAsks` `bbo-tbt`) :
  - Débit : 226–272 MAJ carnet, 256–850 BBO, 32–128 lots de trades par instrument en 30 s ; 0 erreur hors coupure.
  - Lag réception − ts exchange : carnet p50 66 ms / p95 78 ms ; trades p50 62–67 ms ; BBO p50 64 ms (inclut l'offset
    d'horloge ~+76 ms mesuré ⇒ lag réel non séparable de l'offset : UNKNOWN).
  - Validation d'intégrité : ccxt vérifie `prevSeqId == nonce` et rejette par `InvalidNonce` (code `pro/okx.py`
    l. 1318-1327) ; **aucun CRC32** OKX (grep) — cohérent avec la dépréciation OKX. 0 trou de séquence observé.
  - Carnet de référence indépendant (chaînes, deltas appliqués par nous) vs carnet ccxt (floats) : **top-25 identique sur
    598/598 messages**.
  - Coupure forcée (`client.close()`) à 15 s : les `watch*` en attente lèvent **`asyncio.CancelledError`** (pas
    `NetworkError`) — l'appelant doit l'attraper ; ré-appel ⇒ reconnexion + nouveau snapshot en 1,5–4,3 s ; 2 snapshots
    par instrument au total. Coupure « naturelle » serveur (code 64008, upgrade) non testée : UNKNOWN.
  - Aucun receipt timestamp dans les objets ccxt (trades, BBO, carnet) ; ajouté par hook dans notre test.
  - Binance pro : « checksum » = contrôle de continuité U/u/pu (pas de CRC), option `watchOrderBook.checksum` True par
    défaut ⇒ `ChecksumError`. Bybit pro : deltas appliqués **sans** contrôle de continuité `u`/`seq` ; `cts`/`seq` ignorés (lecture code).
- Hazards : forming bar ; OKX funding ts None ; unités OI contrats ; `CancelledError` à la coupure ; OKX WS :8443 bloqué
  ici (URL à surcharger `urls['api']['ws']`) ; `has` ne dit rien de la sémantique (ex. `watchLiquidations` OKX 'emulated').
- Niveau atteint : **L3** (différentiel natif/ccxt/tardis-machine, §5).

## 3. Mesure défendable du « code custom supprimé »
`bench/laneE/custom_residual_matrix.{py,csv}` : 12 surfaces C0 × 3 venues = 36 cellules, statut à partir de `has` +
pertes MESURÉES sur OKX (et lues dans le code pour Binance/Bybit) :
- UNIFIED 20 (dont 13 « _UNMEASURED » Binance/Bybit), EMULATED 2, PARTIAL 10, MISSING 4.
- ⇒ 22/36 cellules (61 %) servies sans code venue-spécifique ; 10/36 (28 %) servies mais avec correctif PIT/unité ;
  4/36 (11 %) manquantes (receipt ts × 3, mark Bybit).
- Ce que ccxt SUPPRIME (INFERENCE argumentée par la matrice) : transport REST/WS, signatures d'endpoint et mapping
  symboles (load_markets, contractSize), throttle client, pagination funding/OI history, gestion abonnement WS, carnet
  local + contrôle de séquence OKX/Binance, normalisation de schéma (ticker/trade/orderbook/funding/OI), conservation du brut (`info`).
- Ce qui RESTE custom (MEASURED via `pit_wrapper_sketch.py`, **42 lignes non vides** exécutées sur OKX) : enveloppe
  d'observation (venue, méthode, exchange_ts, receipt send/recv, version lib, sha256 du brut) ; filtrage barre en formation
  (29/30 barres gardées) ; détection de trous ; restauration ts funding OKX depuis `info.ts` ; OI → base via contractSize.
  Non couverts par l'esquisse et restant custom : persistance PG / idempotence, offset d'horloge, contrôle de continuité
  Bybit, liquidations OKX (WS natif ou émulé), politiques de reconnexion/alerte, calendrier de funding par venue.
- Lecture : la réutilisation retire la **majorité du code de transport/normalisation** ; la **couche PIT/provenance reste
  intégralement custom** et petite. Ratio LOC vs code C0 actuel : UNKNOWN (code AurumShift non lu).

## 4. cryptofeed 3.0.1 (AGPL-3.0-or-later) — réévaluation
- VERIFIED_FACT (PyPI + CHANGES.md) : 2.5.0 (2026-08-08, py≥3.12), 3.0.0 (2026-09-21 « New asyncio core », « REST endpoints
  removed », exchanges morts retirés, free-threaded 3.14t), 3.0.1 (2026-09-27 : correctifs Binance futures depth, OKX data
  quality…), `Requires-Python >=3.13`. Licence toujours AGPL-3.0-or-later (pyproject + LICENSE). Activité : 39 commits/12 m,
  29 par le mainteneur unique (bus factor 1).
- MEASURED (py3.13, `cryptofeed_okx_smoke.json`, 25 s OKX, URL réécrite 8443→443) : ticker 300, L2 446, trades 252,
  funding 4, OI 8, liquidations 200 callbacks ; chaque callback reçoit `receipt_timestamp` natif. Lag p50 trades 86 ms, L2 88 ms.
  Hazard : le canal liquidations OKX pousse d'abord un **historique** (lag médian 14 118 s = 3,9 h) ⇒ receipt ≫ exchange ts :
  sans règle PIT explicite on « observerait » des liquidations anciennes comme nouvelles.
- Code : OKX `books` traité par `seqId/prevSeqId` (pas de CRC) — déjà aligné sur la dépréciation.
- Verdict : techniquement le plus proche du besoin C0 (receipt ts + funding/OI/liq live), mais AGPL + bus factor 1 +
  py≥3.13 ⇒ SHADOW (outil d'observation séparé, jamais lié au cœur) ; décision juridique AGPL : UNKNOWN.

## 5. tardis-machine 18.3.8 (MPL-2.0) + Tardis.dev — L3 différentiel
- VERIFIED_FACT : npm tardis-machine 18.3.8, `engines.node >=24.19`, deps `tardis-dev`, `ws`, `debug` ; 112 commits/12 m
  (dernier 2026-10-03). MEASURED : tourne sous node 22.22 malgré EBADENGINE.
- MEASURED replay sans clé (échantillon gratuit du 1er du mois) : okex-swap BTC-USDT-SWAP 2026-09-01 00:00–00:01 :
  1 128 lignes (821 trades, 247 derivative_ticker, 60 book_snapshot_5_1s), chaque ligne a `timestamp` (exchange) ET
  `localTimestamp` (réception Tardis) ; `derivative_ticker` porte fundingRate, fundingTimestamp, openInterest, mark, index.
- MEASURED live sans clé (`ws-stream-normalized`, 20 s) : même schéma normalisé que le replay (okex-swap trades 903,
  book_snapshot 5×100 ms 186, derivative_ticker 16 ; okex spot quote 57, trades 11), localTimestamp posé par la machine locale.
- **Différentiel L3 « même trade, trois chemins »** (`trade_id_differential.json`) : 119 trades live tardis-machine joints par
  `tradeId` au REST natif OKX et à `ccxt.fetch_trades` : BTC-USDT-SWAP 108/108 et BTC-USDT 11/11 **égaux sur prix, côté,
  timestamp exchange et quantité** (quantité swap = contrats natifs `sz`, non convertie par aucun des deux) ; receipt lag
  p50 71 ms (swap) / 62 ms (spot).
- VERIFIED_FACT (https://tardis.dev/#pricing, lu 2026-10-05) : Academic 350 $/mois, Solo 700, Professional 1 000,
  Business 3 000 ; fourchettes par catégorie Perpetuals 350–3 000, Spot 450–3 500, Derivatives 450–3 500, All Exchanges
  650–6 000 $/mois ; « Tardis Machine » coché seulement Professional/Business (pour le replay historique avec clé) ; minimum 300 $.
- Intérêt AurumShift : **même schéma live et replay, avec double horodatage** ⇒ oracle de replay PIT et C0 challenger
  (ORACLE/SHADOW), sans devenir autorité. Coût : TIER_C (Professional perpétuels ≈ 1 000 $/mois, catégorie exacte à confirmer).

## 6. barter-data 0.13.0 (Rust, MIT)
- VERIFIED_FACT : crates.io barter-data 0.13.0 (2026-08-20), repo barter-rs, 29 commits/12 m, auteur principal 23/29.
- MEASURED : `cargo build --release --example public_trades_streams_multi_exchange` 6 min 22 s (froid). Exécution OKX
  nécessitant 2 patchs (port 443 ; `rustls-tls-native-roots` car webpki-roots refuse la CA du proxy) ; 60 trades/20 s,
  `MarketEvent{time_exchange, time_received}` (double horodatage natif), lag p50 65 ms ; 1 erreur non fatale « pong » texte OKX.
- VERIFIED_FACT (code `src/exchange/*/channel.rs`) : OKX = trades seulement ; Binance = trades, L1, L2, liquidations
  (USD-M) ; Bybit = trades, L1, L2 ; **aucune** surface funding/OI/mark/index/bougies venue.
- Verdict : WATCH (bon modèle de données PIT, couverture C0 insuffisante, Rust hors pile).

## 7. Autres candidats OSS
- nautilus_trader 1.231.0 (LGPL-3.0, PyPI 2026-08-02, 1 856 commits/3 m, 83 % un auteur) : adaptateurs Rust binance/okx/bybit/
  tardis, données de test funding/mark/index/liquidations OKX (arbo `crates/adapters/okx/test_data`). Modèle ts_event/ts_init
  (DOCUMENTED par LAB_PRIOR 017). Plateforme complète = risque de 2ᵉ autorité runtime ⇒ PARK pour C0 (non exécuté ici).
- hummingbot 20260920 (Apache-2.0, 1 733 commits/12 m) : connecteurs orientés trading/market making ⇒ REJECT pour C0 (autorité d'ordres).
- cryptostore (bmoscon) : dernier commit 2024-04-18 ⇒ REJECT (abandonné ; dépend de cryptofeed 2.x).
- crypto-crawler-rs / crypto-ws-client : dernières versions crates 2023-03 / 2023-02 ; repo GitHub non accessible ⇒ REJECT (non maintenu).
- unicorn-binance-websocket-api 2.16.1 (MIT, 2026-09-21, 259 commits/12 m, dont 125 « AIgent ») : Binance seulement ;
  egress bloqué ⇒ PARK (L0).
- pybit 5.17.0 (MIT, 2026-07-14, 79 commits/12 m) : SDK officiel Bybit, brut sans normalisation ⇒ PARK (fallback natif Bybit).
- python-okx 0.4.4 (2026-09-07, 99 commits/12 m ; licence PyPI non renseignée = UNKNOWN) : SDK officiel OKX ⇒ PARK.
- binance-connector 3.13.0 (MIT, 2026-04-30) / binance-sdk-spot 13.0.0 (2026-10-01) / binance-futures-connector 4.2.0 :
  SDK officiels modulaires ⇒ PARK (fallback natif Binance ; egress bloqué).
- ccxt-rs : pas de crate publiée trouvée (crates.io `ccxt-rs` absent) ⇒ REJECT (inexistant comme lib officielle).

## 8. Fournisseurs commerciaux (prix publiés seulement)
| Fournisseur | Prix publié (lu 2026-10-05) | Étiquette |
|---|---|---|
| Tardis.dev | 350–6 000 $/mois selon plan/catégorie ; min 300 $ | VERIFIED_FACT (tardis.dev/#pricing) |
| CoinAPI Market Data | Startup 79 $, Streamer 249 $, Pro 599 $/mois, PAYG 0 $ + 25 $ crédits ; carnet L2 via Pro/FIX ; funding/OI non précisé | VERIFIED_FACT (coinapi.io/products/market-data-api/pricing) |
| CoinGlass API | Hobbyist 29 $, Startup 79 $ (usage personnel), Standard 299 $, Professional 699 $ (usage commercial) ; OI/funding/liquidations ; « Updates ≤ 1 min » ; historique intrajournalier 6–360 j | VERIFIED_FACT (coinglass.com/pricing) |
| Velo | « Velo API keys are available at $199/mo » ; mensuel = 3 mois d'historique, annuel = complet | VERIFIED_FACT (docs.velo.xyz/api) |
| Kaiko | sur devis | UNKNOWN_PRICE (kaiko.com pricing-and-contracts) |
| Amberdata | Startup/Enterprise sans montant affiché, « Request a Price Quote » | UNKNOWN_PRICE |
| CoinDesk Data (ex-CCData/CryptoCompare) | page prix 404 ; pas de montant trouvé | UNKNOWN_PRICE |
| Glassnode | API = add-on « contact sales » (source secondaire costbench : Professional 999 $/mois) | UNKNOWN_PRICE (primaire non lue) |
| Coinalyze | API exige une clé (401 sans) ; conditions free non lues | UNKNOWN_PRICE |
Aucun n'a été exécuté avec clé. CoinGlass/Velo/Coinalyze = agrégats OI/funding/liquidations utiles comme **oracle
indépendant** de cohérence, pas comme source C0 (granularité ≤ 1 min, PIT non documenté = UNKNOWN).

## 9. Commandes clés exécutées
```
uv venv -p 3.11 venvs/laneE && uv pip install ccxt cryptofeed pybit python-okx binance-connector unicorn-binance-websocket-api
uv venv -p /usr/bin/python3.13 venvs/laneE313 && uv pip install cryptofeed==3.0.1
python bench/laneE/ccxt_has_matrix.py > ccxt_has_matrix.json
python bench/laneE/okx_rest_l2.py > okx_rest_l2.json
python bench/laneE/okx_ws_l2.py 30 > okx_ws_l2.json          # 3 runs ; dernier conservé
python3.13 bench/laneE/cryptofeed_okx_smoke.py 25
bash bench/laneE/tardis_machine_smoke.sh ; python bench/laneE/trade_id_differential.py
cargo run --release --example laneE_okx_trades   (voir barter_build_notes.txt)
python bench/laneE/pit_wrapper_sketch.py ; python3 bench/laneE/custom_residual_matrix.py
```

## 10. UNKNOWN restants
Comportement Binance/Bybit live (egress) ; coupure serveur OKX 64008 ; lag réseau réel (offset d'horloge non séparé) ;
ratio LOC réellement retiré du C0 AurumShift ; licence AGPL vs usage AurumShift ; catégorie Tardis exacte et clauses de
redistribution ; qualité PIT des agrégateurs (CoinGlass/Velo) ; prix Kaiko/Amberdata/CoinDesk/Glassnode.
