# raw_laneCD — Lanes C+D : oracles de coût de transaction / outcome économique + microstructure / replay

Mission : AURUMSHIFT_EXTERNAL_ACCELERATION_RADAR_V1 · lane `laneCD` · date sandbox 2026-10-05 (UTC).
Labo externe : aucun code, base, credential ni chemin d'exécution AurumShift n'a été lu ni touché.
Étiquettes : VERIFIED_FACT (source primaire citée), MEASURED_BY_THIS_MISSION, UPSTREAM_BENCHMARK, PAPER_RESULT,
VENDOR_CLAIM, INFERENCE, UNKNOWN. Prix : UNKNOWN_PRICE si non publié ; bandes TIER_A…E du brief (USD ≈ EUR, INFERENCE).

Point de départ (ne pas refaire) : LAB_PRIOR 006 (walk-the-book L2 = seule primitive de slippage quasi non biaisée ;
5 bps fixe rejeté ; demi-spread seul rejeté ; sqrt-law = prior OHLCV avec bande ±50–100 % ; funding = taux réglé par
venue × notionnel ; fills passifs non identifiables depuis données gratuites) et LAB_PRIOR 017 (hftbacktest ADAPT,
nautilus ADAPT, cvxportfolio ADAPT GPL/bus factor 1, tardis-python ADAPT, tcapy REJECT, abides PARK).
Ce qui est NOUVEAU ici : (1) un oracle de coût L3 rejoué sur données historiques Tardis 2026-10-01 pour exactement
BTC-USDT et DOGE-USDT, spot Binance + OKX + perp Binance ; (2) recoupement funding Tardis vs sources officielles ;
(3) deux défauts de hftbacktest 2.4.4 mesurés sur ordres MARKET ; (4) état 2026 des fournisseurs et prix publiés.

---------------------------------------------------------------------------------------------------------------------

## 1. Bench L3 « oracle de coût indépendant » (MEASURED_BY_THIS_MISSION)

### 1.1 Données et protocole
* Source : `datasets.tardis.dev`, échantillons gratuits du **2026-10-01** (1er jour du mois, sans clé).
  VERIFIED_FACT : « Historical datasets for the first day of each month are available to download without API key »
  (https://docs.tardis.dev/downloadable-csv-files/api.md).
* Fichiers (20, md5 vérifié contre l'en-tête `x-md5` pour chacun → 20/20 OK, `bench/laneCD/tardis_sample_md5.txt`) :
  binance spot BTCUSDT/DOGEUSDT {book_snapshot_25, trades, quotes, incremental_book_L2}, okex spot BTC-USDT/DOGE-USDT
  {book_snapshot_25, trades, quotes}, binance-futures DOGEUSDT {book_snapshot_25, trades}, derivative_ticker
  binance-futures/okex-swap BTC & DOGE. Volume total ≈ 0,55 Go gz (BTC incremental_book_L2 = 147 Mo).
* Comportements HTTP observés (MEASURED) : `HEAD` → 404 ; requête `Range` → 403 ; GET complet → 200. Un jour ≠ 1er
  du mois sans clé → 403 JSON `code 10` (« only historical CSV market datasets for the first day of each month »).
  Le client officiel `tardis-dev` 5.0.1 (`download_datasets`, l'ancien `datasets.download` n'existe plus — rupture
  d'API vs LAB_PRIOR 017) télécharge sans clé un fichier au md5 identique à curl.
* Grille de décision : toutes les 5 min de 01:00 à 23:55 UTC (276 instants, 1 h de chauffe pour les estimateurs
  causaux). Sélection du carnet **as-of sur `local_timestamp`** (heure de réception = ce qu'un système aurait connu).
* Oracle : walk-the-book BUY côté ask sur les 25 niveaux visibles, notional N ∈ {100, 1 k, 10 k, 100 k, 1 M} USDT,
  coût = (VWAP/mid − 1)·1e4 bps, hors commissions. Si profondeur visible < N → `INSUFFICIENT_VISIBLE_DEPTH` (le coût
  partiel visible est conservé comme borne inférieure, jamais comme coût).
* Modèles comparés : (a) fixe 5 bps ; (b) demi-spread ; (c) demi-spread + Y·σ_j·√(N/V_j), Y = 1, σ_j = écart-type
  des rendements log 1 min de l'heure précédente × √1440, V_j = volume notionnel de l'heure précédente × 24 (causal).
* Markouts : dérive du mid à +1/+10/+60 s après l'instant de décision ; markout BUY 100 k = (mid_{t+h} − VWAP)/mid_t ;
  agresseurs acheteurs publics agrégés par timestamp d'échange ≥ 10 kUSDT, markout du mid vs dernier carnet reçu avant.
* Scripts : `bench/laneCD/download_tardis_samples.sh`, `cost_oracle_bench.py` (≈ 65 s CPU, 4 vCPU),
  résultats `cost_oracle_result.json`.

### 1.2 Déterminisme (MEASURED)
Deux exécutions de `cost_oracle_bench.py` → sha256 identique `409884d8…b829`. Conversion hftbacktest DOGE ×2 → npz
sha256 identique `ac322e03…8f61` ; replays partial/no-partial ×2 → hash des lignes identiques (`determinism.txt`).

### 1.3 Résultats coûts (bps vs mid, hors commissions ; MEASURED, 1 jour, 276 instants)

| Instrument | N (USDT) | INSUFF 25 niv. | walk p50 / p90 / p99 | demi-spread p50 | sqrt p50 | MAE fixe5 / demi-spread / sqrt |
|---|---|---|---|---|---|---|
| binance_spot_BTCUSDT | 100 | 0.0 % | 0.001 / 0.001 / 0.001 | 0.00 | 0.05 | 5.00 / 0.00 / 0.05 |
| binance_spot_BTCUSDT | 1,000 | 0.0 % | 0.001 / 0.001 / 0.050 | 0.00 | 0.15 | 5.00 / 0.00 / 0.15 |
| binance_spot_BTCUSDT | 10,000 | 0.7 % | 0.001 / 0.001 / 0.336 | 0.00 | 0.47 | 4.99 / 0.01 / 0.47 |
| binance_spot_BTCUSDT | 100,000 | 20.3 % | 0.001 / 0.001 / 0.349 (biaisé, cf. 1.5) | 0.00 | 1.48 | 4.98 / 0.02 / 1.51 |
| binance_spot_BTCUSDT | 1,000,000 | 85.9 % | n=39 seulement (borne inf. visible p50 0.08) | 0.00 | 4.60 | — |
| binance_spot_DOGEUSDT | 100 | 0.0 % | 0.528 / 0.532 / 1.521 | 0.53 | 0.99 | 4.45 / 0.03 / 0.47 |
| binance_spot_DOGEUSDT | 1,000 | 0.0 % | 0.528 / 0.532 / 1.565 | 0.53 | 2.00 | 4.41 / 0.06 / 1.41 |
| binance_spot_DOGEUSDT | 10,000 | 0.0 % | 0.714 / 1.801 / 3.571 | 0.53 | 5.17 | 4.03 / 0.44 / 4.21 |
| binance_spot_DOGEUSDT | 100,000 | 0.0 % | 4.180 / 6.110 / 7.080 | 0.53 | 15.19 | 1.11 / 3.80 / 10.89 |
| binance_spot_DOGEUSDT | 1,000,000 | 100.0 % | — (borne inf. visible p50 13.90) | — | — | — |
| binancefut_perp_DOGEUSDT | 100 | 0.0 % | 0.529 / 0.532 / 0.533 | 0.53 | 0.68 | 4.47 / 0.00 / 0.16 |
| binancefut_perp_DOGEUSDT | 1,000 | 0.0 % | 0.529 / 0.532 / 1.228 | 0.53 | 1.02 | 4.45 / 0.02 / 0.49 |
| binancefut_perp_DOGEUSDT | 10,000 | 0.0 % | 0.530 / 1.225 / 1.728 | 0.53 | 2.08 | 4.32 / 0.16 / 1.43 |
| binancefut_perp_DOGEUSDT | 100,000 | 0.0 % | 1.979 / 2.993 / 3.841 | 0.53 | 5.44 | 2.93 / 1.54 / 3.46 |
| binancefut_perp_DOGEUSDT | 1,000,000 | 0.0 % | 10.430 / 12.362 / 13.984 | 0.53 | 16.04 | 5.54 / 9.98 / 5.96 |
| okex_spot_BTC-USDT | 100 | 0.0 % | 0.006 / 0.006 / 0.006 | 0.01 | 0.09 | 4.99 / 0.00 / 0.09 |
| okex_spot_BTC-USDT | 1,000 | 0.0 % | 0.006 / 0.006 / 0.398 | 0.01 | 0.27 | 4.98 / 0.02 / 0.26 |
| okex_spot_BTC-USDT | 10,000 | 0.4 % | 0.006 / 0.231 / 0.872 | 0.01 | 0.85 | 4.93 / 0.06 / 0.77 |
| okex_spot_BTC-USDT | 100,000 | 5.8 % | 0.278 / 0.912 / 1.543 | 0.01 | 2.65 | 4.62 / 0.37 / 2.27 |
| okex_spot_BTC-USDT | 1,000,000 | 98.6 % | n=4 seulement (borne inf. visible p50 0.82) | 0.01 | 7.74 | — |
| okex_spot_DOGE-USDT | 100 | 0.0 % | 0.528 / 0.532 / 1.223 | 0.53 | 1.14 | 4.44 / 0.02 / 0.59 |
| okex_spot_DOGE-USDT | 1,000 | 0.0 % | 0.529 / 1.385 / 2.477 | 0.53 | 2.45 | 4.29 / 0.18 / 1.73 |
| okex_spot_DOGE-USDT | 10,000 | 0.0 % | 1.795 / 3.047 / 4.259 | 0.53 | 6.61 | 3.04 / 1.43 / 4.56 |
| okex_spot_DOGE-USDT | 100,000 | 0.0 % | 7.064 / 8.491 / 10.435 | 0.53 | 19.75 | 2.19 / 6.60 / 12.36 |
| okex_spot_DOGE-USDT | 1,000,000 | 100.0 % | — (borne inf. visible p50 14.71) | — | — | — |

Carnet COMPLET (incremental_book_L2 reconstruit par hftbacktest, §2) — Binance spot, MEASURED :
BTCUSDT 100 k p50/p90 = 0.0006 / 0.587 bps ; **1 M p50/p90 = 0.94 / 2.00 bps** ; DOGEUSDT **1 M p50/p90 = 26.0 / 34.2 bps**
(walk jusqu'à 253 ticks). Concordance avec LAB_PRIOR 006 (BTC live 1.1–2.5 bps @1 M sur d'autres venues) : cohérent.

### 1.4 Lecture
* MEASURED : **fixe 5 bps** sur-facture BTC de ~5 bps à toutes tailles (coût réel < 0.01 bps jusqu'à 10 k) et
  sous-facture DOGE OKX spot dès 100 k (7.1 bps p50) et DOGE perp 1 M (10.4 bps). Confirme le REJECT de LAB_PRIOR 006
  sur un second jeu de données (historique, autres venues, DOGE).
* MEASURED : **demi-spread seul** exact jusqu'à ~1 k USDT (DOGE tick-bound : spread = 1 tick = 1.06 bps) mais
  sous-facture DOGE de 3.8 bps (Binance) / 6.6 bps (OKX) à 100 k et de ~10 bps (perp) / ≥ 13–25 bps (spot) à 1 M.
* MEASURED : **sqrt-law Y=1** sur-facture systématiquement (biais toujours > 0) : BTC +1.5 bps @100 k, DOGE +10.9
  (Binance) / +12.4 (OKX) bps @100 k. INFERENCE : la sqrt-law décrit l'impact d'un méta-ordre étalé, pas la traversée
  instantanée du carnet ; Y=1 n'est pas transportable ⇒ reste un prior OHLCV-only à bande large (LAB_PRIOR 006).
* MEASURED : **la venue compte** : DOGE 100 k coûte 4.2 bps (Binance spot) vs 7.1 bps (OKX spot) vs 2.0 bps (Binance
  perp) le même jour ; BTC 100 k : 0.001 (Binance) vs 0.28 bps (OKX) p50.
* MEASURED : **commissions dominent** pour un PAPER BUY ≤ 100 k : Binance spot VIP0 taker 0.100 % = 10 bps
  (0.075 % avec BNB) — VERIFIED_FACT https://www.binance.com/en/fee/schedule (la même page indique 0.095 % pour
  USDⓈ-M futures VIP0 : valeur inhabituelle, à re-vérifier → UNKNOWN). Tarifs OKX : page non lisible ici → UNKNOWN.

### 1.5 Piège mesuré : exclure INSUFFICIENT biaise le coût vers le bas
BTC Binance 100 k : sur les 220 instants « suffisants » du snapshot 25 niveaux, p90 = 0.001 bps ; sur carnet complet
(276 instants), p90 = 0.587 bps. Les instants où 25 niveaux ne suffisent pas sont précisément les instants de carnet
mince. ⇒ Pour BTC, `book_snapshot_25` est un oracle valide seulement ≤ 10 k USDT ; au-delà il faut
`incremental_book_L2` (ou au minimum garder `INSUFFICIENT_VISIBLE_DEPTH` = UNKNOWN_COST, jamais « échantillon filtré »).
Cause (INFERENCE) : le carnet BTC spot est saturé de micro-ordres à 1 tick (0.01 USDT ≈ 0.0012 bps) ; 25 niveaux ≈
quelques USD de prix.

### 1.6 Timestamps et sémantique PIT (MEASURED + VERIFIED_FACT)
* Définition : `timestamp` = horodatage échange en µs, **avec repli sur `local_timestamp` si l'échange n'en fournit
  pas** (VERIFIED_FACT, https://docs.tardis.dev/downloadable-csv-files/data-types.md). `local_timestamp` = heure de
  réception du collecteur Tardis.
* MEASURED : lag `local − exchange` (p50 / p99) : book Binance spot 1.9–2.4 / 2.4–3.3 ms ; trades Binance 2.8–3.8 /
  21–26 ms ; book OKX 4.3–4.6 / 9.5–10.8 ms ; trades OKX 6.1–6.3 / 34–56 ms (p99.9 jusqu'à 438 ms). 0 lag négatif,
  0 non-monotonie de `local_timestamp`. OKX trades à résolution ms (µs = 000), Binance µs.
* MEASURED : `derivative_ticker` Binance-futures : lag p50 ≈ 60 ms, p99 ≈ 1 s (flux mark price 1 s) ; OKX-swap
  6–7 non-monotonies de `timestamp` échange sur la journée (local monotone).
* MEASURED : première ligne Binance book : `timestamp == local_timestamp` (snapshot REST initial, cohérent avec la doc
  « depthSnapshot … generated » VERIFIED_FACT https://docs.tardis.dev/historical-data-details/binance.md).
* Règle PIT proposée (INFERENCE) : sélectionner sur `local_timestamp` (connu au moment de la réception) ; garder
  `timestamp` comme attribut ; décaler de la latence propre AurumShift si elle diffère de celle de Tardis (collecte
  GCP Londres/Tokyo — VERIFIED_FACT faq/general). Les deux sont distincts dans les données ⇒ compatible bitemporel.
* Cadence : Binance spot `depth@100ms` (VERIFIED_FACT) ⇒ staleness mesurée au point de décision p50 83 ms / p99 509 ms
  (BTC), p99 1.07 s (DOGE). Pas un problème pour un système intraday non-HFT.

### 1.7 Markouts (proxy d'adverse selection) — MEASURED
| Instrument | dérive mid +1/+10/+60 s (moy.) | markout BUY 100 k vs VWAP +60 s p50 | agresseurs ≥10 k : n, markout mid +1/+10/+60 s p50 |
|---|---|---|---|
| binance_spot_BTCUSDT | 0.02 / −0.10 / −0.18 | −0.26 | 13 585 ; 0.48 / 0.72 / 0.74 |
| binance_spot_DOGEUSDT | 0.06 / −0.06 / −0.15 | −4.72 | 302 ; 1.07 / 2.09 / 1.05 |
| binancefut_perp_DOGEUSDT | −0.01 / −0.08 / −0.12 | −2.31 | 4 298 ; 1.06 / 1.06 / 1.06 |
| okex_spot_BTC-USDT | −0.02 / −0.10 / −0.21 | −0.14 | 6 534 ; 0.58 / 0.94 / 0.87 |
| okex_spot_DOGE-USDT | 0.06 / −0.04 / −0.06 | −7.08 | 197 ; 2.09 / 1.06 / 1.06 |

Lecture : à instants non informés (grille 5 min), la dérive du mid est ~0 en moyenne (|moy.| ≤ 0.21 bps à 60 s,
queues ±12–24 bps p1/p99) ⇒ le markout d'un BUY non informé ≈ −coût de traversée ; pas d'adverse selection pour un
preneur aléatoire. Les agresseurs publics ≥ 10 k sont suivis d'une hausse du mid (+0.5 à +2 bps, médianes ; DOGE = 1
tick) : c'est l'impact/la continuation de flux (cohérent avec « flow-conditional drift +0.6…+1.8 bps » de LAB_PRIOR
006). Pour AurumShift, le markout de SES fills PAPER contre ce même oracle sera le diagnostic RetexV1 pertinent.

### 1.8 Funding : Tardis vs sources officielles (MEASURED, `funding_crosscheck.py`)
* OKX-swap BTC & DOGE, 2026-10-01 : dernier `funding_rate` Tardis avant chaque `funding_timestamp` vs
  `/api/v5/public/funding-rate-history` (`realizedRate`) : **6/6 égalité exacte** (diff 0.0).
* Binance-futures BTC & DOGE, 2026-09-01 (Vision mensuel dispo pour septembre ; `fapi` = 451 depuis ce sandbox) :
  3/6 exacts, 3/6 écarts ≤ 1.01e-6 (≤ 0.01 bps/8 h) : le dernier taux streamé avant l'échéance n'est pas toujours le taux
  réglé. ⇒ Tardis `derivative_ticker` = oracle quasi exact pour OKX, approximatif (≤ 0.01 bps) pour Binance ; la vérité
  Binance reste `data.binance.vision …/fundingRate` (mensuel, publié après la fin du mois — l'URL daily 2026-10-01 = 404).
* Ordres de grandeur 2026-10-01 (MEASURED) : BTC 0.27–0.70 bps/8 h (Binance), 0.03–0.63 (OKX) ; DOGE 0.70–1.0 bps/8 h.
* nautilus `TardisCSVDataLoader.load_funding_rates` : `next_funding_ns=None` sur 99 477 lignes (l'échéance est perdue)
  et `instrument_id = DOGEUSDT.BINANCE` pour un fichier **binance-futures** (collision d'identifiant spot/perp) — MEASURED.

---------------------------------------------------------------------------------------------------------------------

## 2. hftbacktest 2.4.4 comme second oracle (L3, MEASURED)

* Version : PyPI 2.4.4 (2025-12-10) ; dernier commit `master` 2025-12-23 ; aucun commit ni release depuis (> 9 mois) —
  VERIFIED_FACT (clone git). LAB_PRIOR 017 notait déjà « slowed upstream ».
* Convertisseur `hftbacktest.data.utils.tardis.convert([trades, incremental_book_L2])` : fonctionne sans modification.
  DOGE : 14.7–19.8 s, npz 38 Mo ; BTC : 78 s, npz 223 Mo ; déterministe (npz hash identique ×2). Le docstring
  avertit : timestamps Binance Futures = `E` (envoi) et non `T` (matching) ⇒ latence légèrement sous-estimée.
* **Concordance carnet** : walk sur le carnet L2 complet reconstruit par hftbacktest vs walk sur `book_snapshot_25` Tardis
  au même instant : écart max 1.35e-4 bps (DOGE) / 3.4e-4 bps (BTC) quand 25 niveaux suffisent ⇒ deux reconstructions
  indépendantes concordent ; le snapshot Tardis est fidèle.
* **Défaut 1 — plafond de 100 ticks des ordres MARKET (PartialFillExchange)** : source
  `hftbacktest/src/backtest/proc/partialfillexchange.rs` (`// todo: set the proper upper bound.` boucle
  `best_ask_tick..best_ask_tick+100`, puis `Status::Expired`). MEASURED : part EXPIRED = part où notre walk dépasse
  100 ticks, **à l'identique** : DOGE 1 M 7.61 % = 7.61 % ; BTC 100 k 26.1 % = 26.1 % ; BTC 1 M 94.6 % = 94.6 %.
  Sur BTC (tick 0.01 ≈ 0.0012 bps), 100 ticks ≈ 0.12 bps de profondeur de prix ⇒ un MARKET BUY ≥ 100 k est tronqué.
* **Défaut 2 — fills partiels non comptabilisés côté local** : `local.rs` applique `state.apply_fill` uniquement si
  `status == Filled`. MEASURED : ordre au statut FILLED mais position locale inférieure à la quantité dans 63 % (DOGE
  10 k) à 100 % (DOGE 100 k) des cas ; le « VWAP » lu via balance = prix du dernier tick (DOGE 100 k : 6.87 bps vs
  4.18 bps vrai walk). Corroboré upstream : issue #316 ouverte « Partial fills of resting orders are never applied to
  position/balance (PartialFillExchange + prob queue models) » (https://github.com/nkaz001/hftbacktest/issues).
* **NoPartialFillExchange** : MARKET rempli en totalité au meilleur ask ⇒ coût = demi-spread quelle que soit la taille
  (DOGE 1 M : 0.53 bps vs 26.0 bps réels) — documenté dans le code (« Takes the market »), dangereux comme oracle.
* Débit : replay journée DOGE 1.2 s (no-partial) / 9.1 s (partial, avec walk Python) ; BTC 9.3 / 15 s.
* Verdict : **convertisseur + reconstruction de carnet = ADOPT comme utilitaire de données** (MIT) ; **moteur de fills =
  pas un oracle de coût** pour ordres marchés > quelques ticks sans patch. Code économisé : la reconstruction L2
  incrémentale (snapshot + deltas + validation d'ordre d'événements) — INFERENCE ≈ 150–300 lignes custom évitées.

## 3. Autres moteurs / bibliothèques

* **nautilus_trader** — VERIFIED_FACT PyPI : 1.231.0 (2026-08-02) et **2.0.0rc6 publié le 2026-10-05**, `requires_python
  >=3.12` (sur py3.11 l'installeur résout 1.221.0). MEASURED (1.221.0) : `TardisCSVDataLoader.load_depth10(levels=25)`
  charge 540 022 snapshots DOGE en 5.9 s mais **ne garde que 10 niveaux** (OrderBookDepth10) ; `ts_event` = timestamp
  échange, `ts_init` = local_timestamp (bon mapping PIT) ; funding : échéance perdue + collision spot/perp (§1.8).
  Passive-fill/print non résolu (LAB_PRIOR 017). LGPL. Statut : SHADOW/WATCH (rupture 2.0 en cours).
* **cvxportfolio** 1.5.1 (2025-07-06), dépôt actif en commits « auto » de démonstration (dernier commit non-auto
  2025-09-19 ; 2025-11 CI) ; GPLv3, bus factor 1 (LAB_PRIOR 017). Modèle de coût = forme a·|z| + b·σ·|z|^1.5/V^0.5
  (vérifié en 017) : c'est une sqrt-like dont nous venons de mesurer la sur-facturation à Y=1. PARK (formule de référence).
* **bidask (EDGE)** 2.1.0 (2024-12-22), dernier commit 2025-10-13 (« Fix CRAN »), MIT. Estimateur OHLC = borne sur
  ≥1 000 barres (LAB_PRIOR 006) ; inutile quand L2 existe. PARK.
* **abides-jpmc-public** : dernier commit 2023-12-13, pas de PyPI ⇒ REJECT pour ce besoin (LAB_PRIOR 017 : py3.9 only).
* **tcapy** : dernier commit 2022-05-23, PyPI 0.1.2 (2021) ⇒ REJECT (confirme 017).
* **pyfolio round-trips** : agrégation de PnL, aucune modélisation de coût ⇒ REJECT comme oracle (statut hors objet).
* `lob-simulator`/petits simulateurs : non évalués (UNKNOWN) ; aucun ne fournit de données historiques, ce qui est le
  vrai besoin d'un oracle.

## 4. Fournisseurs de données (L0 sauf mention)

### 4.1 Tardis.dev (L3 sur échantillon gratuit) — VERIFIED_FACT https://tardis.dev/#pricing et docs
* Prix mensuels équivalents (USD) : Academic Perpetuals 350 / Spot 450 / All 650 ; **Solo** Perpetuals 700 / Spot 900 /
  Derivatives 900 / All Exchanges 1 200 ; Professional 1 000 / 1 350 / 2 200 ; Business 3 000 / 3 500 / 6 000.
  Commande minimale 300 USD ; facturation mensuelle/trimestrielle/annuelle ; pas de remise ; pas de remboursement initial.
* Historique : annuel → 4 ans (Academic/Solo/Pro), tout depuis 2019-03-30 (Business) ; **mensuel → 4 mois seulement**
  (Solo/Pro/Business) ; Academic = trimestriel/annuel uniquement, éligibilité universitaire.
* Accès : Academic & Solo = **CSV seulement** ; Pro & Business = CSV + replay API + tardis-machine + instruments API.
  Délai : CSV d'un jour disponible le lendemain ≈ 06:00 UTC ; replay API ≈ T−6 min.
* Licence (ToS §9) : licence non exclusive pour usage interne, stockage, création de Derived Data ; **pas de
  redistribution** de données brutes (exception : agrégats ≥ 10 min non reconstructibles) ; §9.4 licence **perpétuelle**
  pour les données téléchargées y compris échantillons ; §9.5 modèles quantitatifs internes autorisés, IA générale
  interdite. ⇒ Les données brutes ne sont PAS dans le dépôt (script de téléchargement à la place) ; seuls des
  percentiles agrégés sont committés (INFERENCE : Derived Data non reconstructible).
* Contenu utile au COST_CONTRACT : `incremental_book_L2` (Binance spot via `depth@100ms` + snapshot REST 1 000 niveaux,
  validation `U/u`), `book_snapshot_25/5`, `quotes`, `trades`, `derivative_ticker` (funding/OI/mark/index),
  `liquidations`, et pour Binance un canal généré `borrowInterest` (taux d'emprunt marge, poll ≈ 1/min, depuis
  2021-02-23) — candidat d'oracle borrow (UNKNOWN_COST de LAB_PRIOR 006).
* Bandes : spot BTC/DOGE Binance+OKX ⇒ plan **Spot** Solo 900 USD ⇒ **TIER_C** ; + perps ⇒ All Exchanges Solo 1 200
  (TIER_C) ; Academic Spot 450 (TIER_B) si éligible ; OHLC/fills simulés seulement : l'échantillon gratuit (12 jours/an)
  suffit à un **audit mensuel**.
* Gain vs capture maison (LAB_PRIOR 005/006) : capture maison = gratuite, mais vers l'avant uniquement, receipt-time
  propre (meilleure pour la PIT AurumShift), WS à maintenir, trous non comblables. Tardis = historique rétroactif,
  mêmes instants pour 3 venues, déjà normalisé et contrôlé (séquences), mais latence de collecte ≠ celle d'AurumShift.
  INFERENCE : le gain réel d'un abonnement est (1) un backfill de 4 mois/4 ans pour calibrer la table coût×taille par
  instrument (ADAPT de 006) avant d'avoir assez de capture propre, (2) un oracle tiers pour auditer la capture maison
  (même jour, même instrument). L'échantillon gratuit du 1er de chaque mois fournit déjà (2) **sans coût** : 12
  journées/an × 3 venues.

### 4.2 Crypto Lake (L1 sur échantillon gratuit)
* VERIFIED_FACT https://crypto-lake.com/subscribe/ : individus 80 USD/mois (64 USD promo 6 mois, **interdit aux
  sociétés**, 300 Go/mois) ; sociétés 500 USD/mois (3 To/trimestre) ⇒ TIER_A (individuel) / TIER_C (société).
* VERIFIED_FACT https://crypto-lake.com/coverage : carnet 20 niveaux ; BINANCE book depuis 2022-11-14, OKX depuis
  2022-12-23, BYBIT 2023-10-27 ; couverture book ≈ 98 % ; funding Binance futures ; publication J+1 ≈ 01:15 UTC.
* MEASURED : `lakeapi` 0.22.3 (2025-11-02, Apache-2), `use_sample_data(anonymous_access=True)` : 25 fichiers `book`
  sample (2022, petites paires), chargement BINANCE BTC-USDT 2022-10-01 = 863 465 × 85 colonnes avec `origin_time`
  ET `received_time` (PIT OK). Échantillon trop ancien pour 2026/DOGE ⇒ pas d'oracle comparatif ici.
* Pas d'incremental L2 (snapshots 20 niveaux) ⇒ même limite BTC ≥ 100 k que §1.5 (INFERENCE).

### 4.3 Kaiko — VERIFIED_FACT docs.kaiko.com
Snapshot carnet brut **toutes les 30 s** jusqu'à 10 % de profondeur + agrégats « market depth », « bid/ask spread » et
**« price slippage »** (slippage d'un market buy au moment du snapshot)
(https://docs.kaiko.com/rest-api/data-feeds/level-1-and-level-2-data/level-2-aggregations/raw-order-book-snapshot/raw-order-book-snapshot-+-market-depth-bid-ask-spread-and-price-slippage).
Prix : UNKNOWN_PRICE (devis) ⇒ TIER_E présumé (INFERENCE). Un slippage pré-calculé par un tiers = oracle indépendant
utile, mais cadence 30 s et coût inconnu ⇒ WATCH.

### 4.4 Amberdata — https://www.amberdata.io/pricing
Plans Startup/Enterprise, prix non publiés (UNKNOWN_PRICE) ; mentionne carnet, analytics de slippage, funding
(VENDOR_CLAIM). SDK PyPI `amberdata` 0.1.1 (2023). WATCH.

### 4.5 CoinAPI — https://www.coinapi.io/products/market-data-api/pricing
Startup 79 USD, Streamer 249, Pro 599 /mois (crédits REST & Go/jour), Enterprise devis ; flat files S3 / L2 complet
mentionnés en add-on (VENDOR_CLAIM). Historique de carnet par plan non précisé (UNKNOWN). PARK (Tardis couvre mieux
le besoin, preuve mesurée).

### 4.6 Databento — VERIFIED_FACT (énumération des publishers, `databento/dbn` `publishers.rs`)
Aucun venue crypto spot (Binance/OKX/Coinbase absents) ; seuls CME `GLBX.MDP3` (futures crypto CME) et indices
`CCCY.CGIF`. Client `databento` 0.87.0 (2026-09-22) très actif. ⇒ REJECT pour l'oracle BTC/DOGE-USDT (WATCH pour basis
CME si besoin futur).

### 4.7 CoinGlass — https://www.coinglass.com/pricing (VERIFIED_FACT via la page)
Hobbyist 29, Startup 79 (non commercial), Standard 299, Professional 699 USD/mois (commercial) ; funding/OI/heatmaps
carnet en Professional ; données 1 min limitées (6–12 j en bas de gamme). Agrégateur ⇒ pas un oracle de fill.
WATCH (funding/OI cross-venue).

### 4.8 Laevitas, Velo
Prix non publiés trouvés (UNKNOWN_PRICE) ; Laevitas : API « enterprise subscription » (source secondaire QuickNode,
non primaire) ; Velo : 1 min sur 5 ans (source secondaire OpenBB blog). Non évalués : UNKNOWN. PARK.

### 4.9 Sources officielles gratuites (oracles de portage)
* OKX `/api/v5/public/funding-rate-history` : ≈ 3 mois glissants (100 lignes, plus ancienne 2026-09-02) ; `realizedRate`
  = vérité de règlement — MEASURED (6/6 vs Tardis). ADOPT_NOW comme oracle funding OKX (à archiver soi-même : fenêtre
  glissante).
* Binance Vision `futures/um/monthly/fundingRate` : vérité Binance ; publication mensuelle a posteriori (daily 404).
  ADOPT_NOW (avec vérification `.CHECKSUM`, cf. LAB_PRIOR 017).

## 5. Ce qui reste UNKNOWN
* Coût réalisé de fills PAPER/réels : aucun ordre propre ; walk-the-book reste un PROXY (impact propre, réaction du
  carnet, latence d'AurumShift non modélisés).
* Représentativité : 1 seule journée (2026-10-01) ; régimes de stress non couverts (prochain échantillon : 2026-11-01).
* Bybit : non téléchargé (non prioritaire ; Tardis le couvre — VERIFIED_FACT docs — mais non mesuré ici).
* OKX : barème de commissions non lu ; Binance USDⓈ-M VIP0 0.095 % à re-vérifier.
* Kaiko/Amberdata/Laevitas/Velo : prix et qualité non mesurés.
* Fidélité de la latence Tardis vs latence AurumShift (lag Tardis 2–6 ms ; celle d'AurumShift inconnue).
* Licence : la publication d'agrégats dérivés (percentiles) d'échantillons Tardis dans un dépôt est interprétée comme
  Derived Data autorisée — interprétation non juridique (INFERENCE).

## 6. Commandes clés exécutées
```
uv venv -p 3.11 venvs/laneCD && uv pip install tardis-dev tardis-client hftbacktest nautilus_trader cvxportfolio bidask polars numpy pandas pyarrow lakeapi databento-dbn
bench/laneCD/download_tardis_samples.sh 2026/10/01 $SCRATCH/data_laneCD      # 20 fichiers, md5 20/20 OK
python bench/laneCD/cost_oracle_bench.py $DATA run1.json ; (×2) sha256 identiques 409884d8…
python bench/laneCD/funding_crosscheck.py $DATA funding_crosscheck_result.json   # OKX 6/6 exact ; Binance 3/6 exact, ≤1.01e-6
python bench/laneCD/hftbacktest_crosscheck.py $DATA $WORK out.json DOGEUSDT|BTCUSDT
git clone --filter=blob:none --shallow-since=2025-09-01 (hftbacktest, tardis-python, tardis-machine, cvxportfolio, bidask, lake-api, abides, tcapy)
```
