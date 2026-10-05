# BENCH_NEXT_72H — 5 expériences maximum

Chaque expérience est **différentielle** (baseline vs baseline + composant), **falsifiable** en ≤ 72 h, et ne crée
aucune seconde autorité : le composant externe produit un *chiffre de contrôle* comparé à la sortie de l'autorité
AurumShift, jamais une décision, un fill, une position ou un Outcome.
Elles sont décrites ici sans lire le code AurumShift ; l'adaptation finale se fait contre le dépôt réel (cf. `claude.md`).

Ordre = ordre recommandé d'exécution (X1 et X2 en parallèle dès J0).

---

## X1 — `COST_ORACLE_DIFF_V1` : COST_CONTRACT_V1 contre un oracle « walk-the-book » Tardis

| Champ | Contenu |
|---|---|
| Question | COST_CONTRACT_V1 sous- ou sur-facture-t-il le coût d'entrée/sortie des ordres PAPER BTC-USDT / DOGE-USDT, par taille et par venue ? |
| BASELINE | Coût calculé par COST_CONTRACT_V1 (lecture seule) pour une grille d'ordres BUY/SELL market synthétiques aux tailles PAPER réelles. |
| BASELINE_PLUS_COMPONENT | Même grille, coût recalculé par l'oracle `bench/laneCD/cost_oracle_bench.py` (walk-the-book sur `book_snapshot_25` + `incremental_book_L2` reconstruit par `hftbacktest.data.utils.tardis.convert`), données gratuites Tardis 1er du mois. |
| INPUT CONTRACT | `(venue, symbol, side, notional_quote, decision_ts_utc)` ; carnet lu **à `local_timestamp ≤ decision_ts`** ; commissions par barème officiel en ligne séparée. |
| OUTPUT CONTRACT | `{oracle_cost_bps, half_spread_bps, depth_status ∈ {OK, INSUFFICIENT_VISIBLE_DEPTH}, book_age_ms, markout_bps@1s/10s/60s}` ; `INSUFFICIENT` ⇒ `UNKNOWN_COST`, jamais 0. |
| THIN ADAPTER | ≤ 150 lignes : mapping symbol/venue, lecture CSV.gz, appel de la fonction de coût AurumShift en mode pur. |
| AUTHORITY BOUNDARY | L'oracle écrit seulement dans un fichier de rapport ; aucune écriture dans OutcomeV1 / ledger économique. |
| TEST CORPUS | Tardis gratuits 2026-08-01, 2026-09-01, 2026-10-01 × {binance, okex} × {BTC-USDT, DOGE-USDT} spot (+ perps si PAPER en utilise) ; grille 5 min ; md5 vérifiés. |
| METRICS | Biais signé (contrat − oracle) en bps, MAE, p90 de l'écart absolu, par (actif, venue, taille) ; part `UNKNOWN_COST` ; part où le contrat met 0 alors que l'oracle est > 0. |
| SUCCESS (contrat validé) | \|biais médian\| ≤ 0,5 bps **et** p90 \|écart\| ≤ 2 bps pour toutes les cellules aux tailles PAPER ; 0 cas « contrat = 0 / oracle > 0 ». |
| REJECTION (contrat à corriger) | Biais médian > 1 bps sur DOGE ou > 0,5 bps sur BTC à une taille PAPER, ou tout coût inconnu compté 0. |
| Composant rejeté si | Le carnet reconstruit diffère du snapshot Tardis de > 0,01 bps au top-25 (vérifié à 3,4e-4 bps par la lane CD), ou non-déterminisme (hash différent sur 2 runs). |
| EFFORT | 0,5–1 j-dev. |
| CODE CUSTOM RETIRÉ | Pas de collecte/reconstruction L2 historique maison pour l'audit (≈ 300–600 lignes évitées, INFERENCE). |
| ROLLBACK | Supprimer le script ; aucune dépendance runtime. |

---

## X2 — `QUORUM_INFERENCE_PREREG_V1` : plan d'analyse gelé + harnais d'inférence réutilisé

| Champ | Contenu |
|---|---|
| Question | Quelle procédure d'inférence (pré-enregistrée) pour « espérance nette incrémentale des QUORUM_ONLY_SUPPRESSED » tient sa couverture sous autocorrélation, petits N et regards répétés ? |
| BASELINE | t-test naïf / moyenne simple sur les Outcomes shadow (ce que l'on ferait sans composant). |
| BASELINE_PLUS_COMPONENT | Primaire : `statsmodels` OLS-constante HAC (lag ≥ horizon de détention max en nb de décisions). Secondaire : `arch` StationaryBootstrap (bloc Politis-White). Moniteur d'arrêt : betting CS (`confseq`, vendorisé) sur PnL borné par K pré-déclaré. Comparaisons A/B/C : `arch` SPA/StepM ; multiplicité : `statsmodels.multitest` (Holm/BH). TOST-HAC pour non-infériorité. |
| INPUT CONTRACT | Table gelée `(decision_id, decision_ts, family_set, gate_attribution ∈ {QUORUM_ONLY_SUPPRESSED, QUORUM_PLUS_OTHER_GATE, NOT_SUPPRESSED}, arm ∈ {A,B,C}, net_pnl_bps_central, net_pnl_bps_pessimistic, cost_status)` ; `cost_status = UNKNOWN` ⇒ exclu ou borné (règle pré-écrite). |
| OUTPUT CONTRACT | JSON signé sha256 : estimation, IC HAC, IC bootstrap, CS courante, p-values ajustées, N, ESS, MinTRL, verdict ∈ {SUPPORTED, NOT_SUPPORTED, INCONCLUSIVE}. |
| THIN ADAPTER | 80–120 lignes (endpoint, strates, TOST-HAC, PSR/MinTRL, placebo) + `bench/quorum_inference/bench_quorum_inference.py` comme test de calibration. |
| AUTHORITY BOUNDARY | Lit RetexV1/OutcomeV1, n'écrit qu'un rapport ; le verdict n'altère aucun paramètre runtime (changement de quorum = décision opérateur hors de ce harnais). |
| TEST CORPUS | (1) Synthétique Q1 (couverture connue) ; (2) contrôle négatif : trades que A a réellement exécutés passés dans le pipeline shadow (écart shadow − réel = biais du simulateur) ; (3) placebo : étiquettes d'arm permutées par blocs. |
| METRICS | Couverture empirique sur synthétique au N attendu ; biais shadow vs réel ; FWER sous regards répétés ; N requis (MinTRL) à l'effet minimal d'intérêt. |
| SUCCESS | Couverture ≥ 0,93 au N et φ plausibles **pour la méthode primaire** ; FWER du moniteur ≤ 0,05 ; plan hashé + commité **avant** le premier Outcome B. |
| REJECTION | Couverture < 0,90 au N prévu (⇒ allonger N ou abandonner la conclusion), ou biais shadow − réel > effet minimal d'intérêt. |
| EFFORT | 1–1,5 j. |
| CODE CUSTOM RETIRÉ | Bootstrap par blocs, choix de bloc, SPA/StepM/MCS, corrections multiples, HAC (≈ 400–800 lignes, INFERENCE). |
| ROLLBACK | Bibliothèques d'analyse hors runtime ; retrait = suppression du script. |

---

## X3 — `C0_CCXT_SHADOW_V1` : ccxt.pro sous enveloppe PIT vs collecteur C0 actuel (OKX d'abord)

| Champ | Contenu |
|---|---|
| Question | Un adaptateur ccxt (+ enveloppe PIT de ~42 lignes) reproduit-il les observations C0 d'OKX (BBO, depth, trades, funding, OI, bars) avec ≤ écarts tolérés, et combien de code collecteur pourrait-il retirer ? |
| BASELINE | Collecteur C0_V2 actuel (fichiers d'observation existants, lecture seule). |
| BASELINE_PLUS_COMPONENT | Processus shadow séparé : `ccxt.pro` watchOrderBook/watchTrades/watchTicker + REST funding/OI/OHLCV + `bench/laneE/pit_wrapper_sketch.py` (receipt_ts, hash du brut, exclusion barre en formation, ts funding OKX, OI→base). |
| INPUT CONTRACT | Mêmes instruments C0 OKX (BTC-USDT, DOGE-USDT spot + swaps) ; horloge NTP ; versions figées (`ccxt==4.5.85`). |
| OUTPUT CONTRACT | Fichiers shadow `(surface, venue, symbol, exchange_ts, receipt_ts, seqId/prevSeqId, payload_sha256, value_fields)` dans un répertoire séparé. |
| AUTHORITY BOUNDARY | Aucune lecture par DecisionV1 ; répertoire shadow non référencé par le runtime. |
| METRICS | Parité par surface (égalité exacte trades par id ; top-25 carnet ; funding/OI) ; trous de séquence ; reconnexions ; lag receipt − exchange ; nombre de champs PIT perdus ; lignes de code collecteur équivalentes. |
| SUCCESS | Trades 100 % égaux par id ; carnet top-25 égal ≥ 99,9 % des instants ; aucun trou non détecté ; résiduel custom ≤ 150 lignes. |
| REJECTION | Un champ silencieusement `None` non détecté par le wrapper ; trou de séquence non signalé ; `CancelledError` non géré qui fige la collecte. |
| VÉRIFICATION ANNEXE (bloquante) | Le C0 actuel valide-t-il encore le **checksum CRC32 OKX**, déprécié le 2026-06-23 (fixé à 0) ? Si oui, il est inopérant ⇒ passer à seqId/prevSeqId. |
| EFFORT | 1 j (OKX) ; Binance/Bybit à rejouer depuis un egress qui les atteint. |
| ROLLBACK | Arrêter le processus shadow. |

---

## X4 — `PIT_TIMELINE_ASOF_REPLAY_V1` : rejeu rapide et exact du DecisionInput gelé pour B/C shadow

| Champ | Contenu |
|---|---|
| Question | La forme « timeline-ASOF » (Polars `join_asof` sur `available_at = greatest(ingested_at, event_time)` + max cumulé de (event_time, revision)) reproduit-elle exactement la fonction PIT d'autorité sur les observations C0, et accélère-t-elle le rejeu A/B/C ? |
| BASELINE | Fonction PIT d'autorité (Postgres) appelée par décision. |
| BASELINE_PLUS_COMPONENT | Rejeu offline Polars/DuckDB sur export Parquet des mêmes observations. |
| INPUT / OUTPUT | Entrée : export append-only `(fact_key, event_time, ingested_at, revision, finality, payload_hash)` + liste `(decision_id, T)`. Sortie : `(decision_id, fact_key, payload_hash)` choisi. |
| AUTHORITY BOUNDARY | Outil d'analyse uniquement ; DecisionInput d'autorité reste celui persisté par le runtime ; le rejeu sert à vérifier et à générer les shadows B/C **sur le même input**, avec comparaison de hash. |
| METRICS | Écarts vs autorité (doit être 0), lookahead (0), ex aequo, temps/décision. |
| SUCCESS | 0 écart, 0 lookahead sur ≥ 100 k décisions réelles ; ≥ 50× plus rapide. |
| REJECTION | ≥ 1 écart non expliqué ; ou dépendance à la finalité non représentable. |
| GARDE-FOU | Le contrôle `ingested_at ≥ event_time` reste un test séparé (le `greatest()` masquerait une horloge biaisée). |
| EFFORT | 0,5–1 j. |

---

## X5 — `EVENT_CALENDAR_ASSEMBLY_V1` : calendrier éco à coût de développement minimal, en capture forward

| Champ | Contenu |
|---|---|
| Question | L'assemblage officiel (BEA ICS/JSON + Fed FOMC/RSS + ECB + BoE/BoJ) + ForexFactory (forecast/previous, ≤ 1 requête/h) + un oracle d'actual (TipRanks connecteur ou fournisseur payant TIER_A/B en essai) couvre-t-il les événements à fort impact de la semaine avec horaires UTC exacts et actual capté avec `receipt_ts` ? |
| BASELINE | Absence de calendrier (gap connu) / calendrier actuel. |
| BASELINE_PLUS_COMPONENT | Capture forward 72 h de chaque source avec `receipt_ts` + sha256 du brut ; table d'événements normalisée `(series_key, scheduled_utc, source, forecast, previous, actual, actual_receipt_ts)`. |
| AUTHORITY BOUNDARY | Données d'observation (C0-like, observation-only) ; aucun gate DecisionV1 avant qualification. |
| METRICS | Couverture high-impact US/EU (vs union des sources) ; écarts d'horaire UTC ; délai actual (receipt − scheduled) ; doublons ; dérive de fuseau (piège JSON NY vs XML UTC). |
| SUCCESS | 100 % des high-impact US/EU de la fenêtre avec horaire UTC concordant entre ≥ 2 sources ; actual capté ≤ 5 min après publication pour ≥ 80 % (via source payante ou connecteur). |
| REJECTION | Écart d'horaire non résolu sur un high-impact ; CGU incompatibles (FF / TipRanks) pour un usage systématique ⇒ basculer sur fournisseur payant. |
| EFFORT | 1 j. |

---

Hors 72 h (préparés mais non prioritaires) : abonnement Tardis Solo (TIER_C) pour calibrer une table coût×taille
sur 4 mois ; conformal `crepes` comme bande indépendante de slippage ; capture Kalshi/Polymarket pour les événements
Fed (shadow).
