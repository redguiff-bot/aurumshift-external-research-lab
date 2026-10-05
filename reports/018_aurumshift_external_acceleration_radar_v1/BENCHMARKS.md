# BENCHMARKS — preuves exécutées par cette mission

Toutes les mesures ci-dessous sont **MEASURED_BY_THIS_MISSION** sauf mention contraire, exécutées en sandbox isolée
(4 vCPU partagés entre lanes, 15 Go RAM), le 2026-10-05, sur données **synthétiques ou publiques**. Aucune donnée,
base ou credential AurumShift n'a été utilisé. Les temps sont des mesures uniques sur machine partagée : ordre de
grandeur, pas benchmark de performance.

Entonnoir d'exécution réalisé :

| Niveau | Définition | Nombre de candidats |
|---|---|---|
| L0 seulement | sources/docs/release/licence | 108 |
| L1 max | import/build/smoke (ou sondage d'endpoint) | 46 |
| L2 max | micro-bench fonctionnel | 39 |
| L3 | bench différentiel « forme AurumShift » | 18 lignes candidates, couvertes par 7 benchs différentiels (Q1, CD-1, CD-2, CD-3, E-1, B-1, I-1) |

Total : 211 lignes candidates dans les 7 CSV (niveau maximal atteint par candidat : colonne `eval_level` de
`CANDIDATE_MATRIX.csv`, telle que déclarée par chaque lane).

---

## Q1 — Inférence de l'endpoint quorum sous dépendance (L3, orchestrateur)

Fichiers : `bench/quorum_inference/bench_quorum_inference.py`, `results.json` (1 000 réplications ; 400 pour les
méthodes betting), `results_quick.json`. Environnement : Python 3.10, `arch 8.0.0`, `statsmodels 0.15.0`,
`confseq 0.0.11`, `numpy 1.26.4`. Durée : 798 s.

**DGP.** PnL net par décision QUORUM_ONLY_SUPPRESSED, en bps : `x_t = μ + e_t`, `e_t = φ e_{t-1} + innovation`,
innovations Student-t(4), écart-type marginal 50 bps, variante « régime » (σ ×3 sur un bloc de 20 %).
μ ∈ {0, +10 bps} (+10 bps ≈ Sharpe 0,2 par décision). Les betting CS sont appliquées au PnL borné à
K = ±300 bps (borne pré-enregistrée), et leur cible est la moyenne du PnL borné.

### Couverture d'un IC à 95 % (μ = 0, sans régime ; ± ≈ 0,014 d'erreur Monte Carlo à 1 000 réplications)

| n | φ | t naïf | HAC Newey-West | arch Stationary | arch Circular | betting CI (n fixe) | betting CS (anytime) |
|---|---|---|---|---|---|---|---|
| 30 | 0 | 0,959 | 0,920 | 0,909 | 0,910 | 1,000 | 1,000 |
| 30 | 0,3 | 0,853 | 0,857 | 0,817 | 0,823 | 1,000 | 1,000 |
| 30 | 0,6 | 0,655 | 0,788 | 0,708 | 0,724 | 1,000 | 1,000 |
| 60 | 0,3 | 0,867 | 0,905 | 0,874 | 0,873 | 1,000 | 1,000 |
| 120 | 0,3 | 0,845 | 0,905 | 0,882 | 0,891 | 1,000 | 1,000 |
| 250 | 0,3 | 0,858 | 0,936 | 0,925 | 0,932 | 0,998 | 1,000 |
| 250 | 0,6 | 0,685 | 0,881 | 0,899 | 0,906 | 0,902 | 0,953 |
| 500 | 0,3 | 0,866 | 0,942 | 0,935 | 0,938 | 0,943 | 0,988 |
| 500 | 0,6 | 0,642 | 0,892 | 0,903 | 0,910 | **0,765** | 0,930 |

### Puissance (rejet de H0 : μ = 0 quand μ = +10 bps) et largeur moyenne de l'IC (bps)

| n | φ | t naïf | HAC | arch Stationary | betting CS |
|---|---|---|---|---|---|
| 60 | 0 | 0,36 / 25 | 0,41 / 24 | 0,41 / 24 | 0,00 / 74 |
| 120 | 0 | 0,64 / 18 | 0,66 / 17 | 0,66 / 17 | 0,00 / 42 |
| 250 | 0 | 0,86 / 12 | 0,87 / 12 | 0,86 / 12 | 0,09 / 25 |
| 250 | 0,3 | (0,83, IC invalide) | 0,72 / 15 | 0,73 / 15 | 0,16 / 25 |
| 500 | 0 | 0,99 / 9 | 0,99 / 9 | 0,99 / 9 | 0,53 / 17 |
| 500 | 0,3 | (0,96, IC invalide) | 0,91 / 11 | 0,90 / 11 | 0,44 / 17 |

### Regards répétés (« peeking ») sous H0 : un regard tous les 10 outcomes, de 20 à 500 (300 réplications)

| φ | t naïf | HAC | betting CS |
|---|---|---|---|
| 0 | **0,303** | **0,393** | 0,000 |
| 0,3 | **0,693** | **0,527** | 0,017 |

### Coût de calcul par appel à n = 500

t 0,3 ms · HAC 0,5 ms · bootstrap (B = 499) ≈ 12 ms · betting CI/CS ≈ 60 ms (grille `breaks=200`).

### Lecture

1. Le t naïf est **invalide** dès φ = 0,3 (0,84–0,87), quel que soit N. Les PnL de décisions rapprochées dans le
   temps sont autocorrélés par construction (holding periods qui se chevauchent).
2. **HAC (statsmodels) est le meilleur estimateur à N fixe**. Il atteint ≥ 0,93 dès N ≥ 250 à φ ≤ 0,3, mais
   sous-couvre à N ≤ 120 (0,86–0,92) et à φ = 0,6 (0,79–0,89). À N ≤ 60, ni HAC ni le bootstrap par blocs ne
   sauvent l'inférence.
3. **Le bootstrap par blocs `arch` ne bat pas HAC** à petit N (il fait légèrement pire). Son intérêt réside dans
   SPA/StepM/MCS (comparaison A/B/C) et dans le second avis, pas dans l'intervalle primaire.
4. **La betting CS est la seule procédure robuste au peeking** (FWER 0–1,7 % contre 30–69 %). Elle est en revanche
   2 à 4,5 fois plus large et sa puissance est faible (0,44–0,53 à N = 500). Elle se dégrade aussi sous forte
   dépendance (betting CI à N fixe : 0,765 à φ = 0,6 ; la CS reste à 0,93). Rôle recommandé : **moniteur d'arrêt pour
   nuisance/sécurité**, pas preuve de gain.
5. Ordre de grandeur du temps de vérité : pour un effet de +10 bps net par décision avec σ = 50 bps, il faut
   **N ≈ 250–500 outcomes QUORUM_ONLY_SUPPRESSED** pour une puissance de 0,7–0,9 sous φ = 0,3. Un canari à
   quelques dizaines d'outcomes ne peut rien conclure de positif. INFERENCE : c'est la contrainte dominante de
   TIME_TO_SCIENTIFIC_TRUTH, plus que tout composant.

Limites : DGP synthétique (AR(1) + t(4) + un bloc de régime), pas de chevauchement explicite de positions, pas de coût
incertain. B = 499 pour les bootstraps. La couverture de la betting CS dépend de la borne K et du clipping.

---

## CD-1 — Oracle de coût indépendant « walk-the-book » sur données Tardis gratuites (L3, lane CD)

Fichiers : `bench/laneCD/` (`download_tardis_samples.sh`, `cost_oracle_bench.py`, `cost_oracle_result.json`,
`determinism.txt`, `tardis_sample_md5.txt`). Données : échantillons gratuits Tardis du 2026-10-01 (binance,
binance-futures, okex), 20 fichiers dont le md5 correspond à celui publié. Grille de 276 instants (toutes les 5 min).
Carnet lu à `local_timestamp ≤ T`.

| Instrument | BUY 10 k USDT p50/p90 (bps) | 100 k | 1 M |
|---|---|---|---|
| BTC-USDT Binance spot | ≈ 0,001 | 0,0006 / 0,59 (carnet complet) | 0,94 / 2,0 (carnet complet) |
| BTC-USDT OKX spot | — | 0,28 / 0,91 | — |
| DOGE-USDT Binance spot | 0,71 / 1,8 | 4,2 / 6,1 | 26,0 / 34,2 |
| DOGE-USDT OKX spot | — | 7,1 / 8,5 | — |
| DOGEUSDT perp Binance | — | 2,0 / 3,0 | 10,4 / 12,4 |

Ces coûts s'entendent hors commissions (taker spot Binance VIP0 : 10 bps, VENDOR_CLAIM page officielle). Le top-25
est insuffisant pour BTC dans 20 % des cas à 100 k et 86 % à 1 M : exclure ces cas biaise le p90 de 0,59 à 0,001 bps.
Au-delà de 10 k, il faut donc le carnet L2 reconstruit, ou classer le cas en `UNKNOWN_COST`.

Contre l'oracle, le coût fixe de 5 bps et le demi-spread seul sont REJECT. Le modèle demi-spread + racine carrée
(Y = 1) est biaisé de +1,5 bps (BTC) à +12 bps (DOGE) à 100 k : PARK, à garder comme prior quand on n'a que des
bougies.

Déterminisme : 2 exécutions donnent le même sha256 du résultat (`409884d8…`).

Sémantique PIT : `timestamp` = horodatage de l'exchange ; `local_timestamp` = réception Tardis. Écart médian de 2 à
6 ms (p99 de 3 à 56 ms), sans écart négatif ni réception hors ordre. Le carnet est vieux de 83 ms en médiane à
l'instant de décision (BTC Binance, publication toutes les 100 ms).

Markouts : aucune dérive moyenne aux instants de la grille (|moyenne| ≤ 0,21 bps à 60 s). Après des achats agressifs
publics ≥ 10 k, le mid monte de +0,5 à +2 bps en médiane.

## CD-2 — Funding : Tardis `derivative_ticker` contre les sources officielles (L3, lane CD)

Avec OKX, le dernier taux vu avant le règlement est égal au `realizedRate` officiel 6 fois sur 6. Avec Binance, il est
exact 3 fois sur 6, et les 3 autres écarts sont ≤ 1e-6. La vérité côté Binance reste `fundingRate` de Binance Vision.
Fichier : `funding_crosscheck_result.json`.

## CD-3 — hftbacktest 2.4.4 comme reconstructeur L2 et comme moteur de fills (L3, lane CD)

- Le convertisseur Tardis fonctionne tel quel et est déterministe (hashes identiques). Le carnet reconstruit
  correspond au snapshot à **3,4e-4 bps** près.
- **Défaut 1 :** les ordres MARKET sont plafonnés à 100 ticks puis expirent (`partialfillexchange.rs`,
  `// todo: set the proper upper bound.`). La part d'ordres expirés est exactement égale à la part d'ordres qui
  traversent plus de 100 ticks : 26,1 % (BTC 100 k), 94,6 % (BTC 1 M).
- **Défaut 2 :** les fills partiels ne sont pas appliqués à la position ni au solde (même défaut que l'issue amont
  #316).
- **Défaut 3 :** en mode « no partial fill », toute la quantité est remplie au meilleur ask. Pour DOGE 1 M, cela donne
  0,53 bps contre 26 bps réels.

Conséquence : hftbacktest est adopté comme **utilitaire de données** (reconstruction L2), et son moteur de fills est
mis en PARK.

---

## E-1 — ccxt 4.5.85 / ccxt.pro contre l'API native OKX et tardis-machine (L3, lane E)

Fichiers : `bench/laneE/`.

- **Carnet WS ccxt.pro :** top-25 identique à un carnet reconstruit indépendamment sur 598 messages sur 598, sans trou
  de séquence en 30 s. ccxt.pro vérifie `prevSeqId == nonce` et n'utilise pas de CRC32.
- **OKX a déprécié le checksum** des canaux `books` (VERIFIED_FACT : changelog du 2026-06-23). Mesuré : 598 messages
  sur 598 portent `checksum = 0`.
- **Différentiel de trades :** 119 trades rapprochés par identifiant (tardis-machine live, REST natif OKX,
  `ccxt.fetch_trades`) sont identiques à 100 % en prix, côté, horodatage exchange et quantité. Pour le swap, la
  quantité reste en contrats.
- **Pertes PIT de ccxt sur OKX :**
  - la barre en formation est renvoyée sans `confirm` ;
  - le funding courant a `timestamp = None` ;
  - le carnet REST a `nonce = None` alors que la réponse native porte un `seqId` ;
  - l'OI est en contrats ;
  - `indexPrice = None` ;
  - `fetchLiquidations` n'est pas supporté.

  Le brut reste disponible dans `info`.
- **Matrice 12 surfaces × 3 venues :** 22 cases sur 36 unifiées ou émulées, 10 servies avec correctif, 4 manquantes.
  13 des 22 cases unifiées concernent Binance/Bybit et n'ont pas été mesurées (egress 451/403).
- **Résiduel custom :** 42 lignes non vides (`pit_wrapper_sketch.py`, exécuté sur OKX).
- **Reconnexion :** `CancelledError` (et non `NetworkError`) sur les `watch*` en attente ; reconnexion et nouveau
  snapshot en 1,5 à 4,3 s.

## E-2 — cryptofeed 3.0.1, tardis-machine 18.3.8, barter-data 0.13 (L1/L2, lane E)

- **cryptofeed 3.0.1** est une réécriture de septembre 2026 qui exige Python ≥ 3.13 et reste sous AGPL. Les 6 canaux
  OKX ont un `receipt_timestamp`. Au démarrage, le canal liquidations pousse **un historique d'environ 3,9 h** en
  médiane : piège PIT.
- **tardis-machine** donne le même schéma en live et en replay, avec `timestamp` et `localTimestamp`.
- **barter-data** compile en 6 min 22 s et ne fonctionne qu'après 2 patchs. Côté OKX il ne couvre que les trades, et
  n'expose ni funding ni OI.

---

## B-1 — Jointure PIT « timeline-ASOF » contre la référence 004 (L3, lane BJKL)

Fichiers : `bench/laneBJKL/pit_asof_bench.py`, `res_pit_asof_5000000.json`. Table de 5 M lignes avec révisions.

- **ASOF naïf sur `event_time` :** 57 423 décisions sur 200 000 voient une ligne ingérée après T. **REJECT.**
- **ASOF naïf sur `ingested_at` :** 328 écarts et 72 lookahead sur 2 000 décisions.
- **Les ex aequo ne sont pas déterministes :** Polars et DuckDB diffèrent d'une ligne sur les mêmes données.
- **Timeline-ASOF :** on pose `available_at = greatest(ingested_at, event_time)` et on prend le max cumulé de
  `(event_time, revision)`. Résultat : **0 écart et 0 lookahead** contre la référence range+QUALIFY de LAB_PRIOR 004,
  et Polars ≡ DuckDB sur 200 000 décisions.
- **Temps :** 3,8 s (Polars) et 5,3 s (DuckDB) pour 200 000 décisions, contre 21,3 s pour seulement 2 000 décisions
  avec la référence. Le gain d'environ 550× par décision est une extrapolation linéaire.

## B-2 — Ledger d'expérience : Postgres append-only contre MLflow 3.16.1 (L2, lane BJKL)

- **Postgres append-only :** 51 lignes SQL, avec chaîne de hash et triggers. UPDATE et DELETE sont refusés. Une
  falsification par un superuser qui contourne le trigger est **détectée** (1 rupture de chaîne), mais pas empêchée.
- **MLflow sur Postgres :**
  - il crée 59 tables dans `public` ;
  - 89 paquets, 630 Mo ;
  - tags réécrivables (un hash `TAMPERED` est accepté) ;
  - métriques re-loggables, runs supprimables, artefacts non hashés.

  Verdict : **REJECT comme autorité**, PARK comme miroir.

## B-3 — Pandera 0.33.1 (backend Polars) contre des contrôles Polars écrits à la main (L2, lane BJKL)

Sur 1 M lignes « observation C0 » avec 8 fautes injectées, les comptes sont identiques. Pandera demande 26 lignes et
0,60 s, contre 13 lignes et 0,50 s à la main : aucun gain de code. Avec un `bid` nul, le contrôle `bid < ask` passe
en Polars mais échoue en pandas.

## B-4 — Divers (L1/L2, lane BJKL)

- **ADBC PostgreSQL 1.12 et scanner DuckDB :** lecture vers Arrow en 0,93 / 0,86 s, contre 3,16 s avec psycopg, sur
  1 M lignes.
- **OpenTelemetry SDK 1.45 :** 16 à 43 µs par span.
- **pgvector 0.8.7 :** compile pour PG16 en 11 s.

---

## F-1 à F-5 — Changement, conformal, portefeuille, lead/lag (L2, lane FGH)

Fichiers : `bench/laneFGH/`.

- **Détection de changement sur un saut de volatilité :**
  - `changepoint_online` Focus détecte en 4 obs (×3) et 43,5 obs (×1,5) sans fausse alarme sous bruit gaussien,
    mais donne **90 % de fausses alarmes sous Student-t(4)** avec un seuil calibré sur une gaussienne ;
  - River PageHinkley : 50 % de fausses alarmes sous queues épaisses ;
  - `ruptures` appliqué offline regarde le futur, et devient 240× plus lent quand on le rend causal.
- **Conformal après un saut de volatilité ×3 :**
  - `crepes`, normalisé par la volatilité récente : couverture de 0,845 à 0,858 sur 100 pas ;
  - MAPIE ACI : identique à l'ACI maison à ≤ 0,002 près, mais 7× plus lent, et jusqu'à 15 bornes infinies pour
    1 000 pas ;
  - EnbPI : 0,48 de couverture. **REJECT.**
- **skfolio HRP :** identique à Riskfolio (écart de 1,7e-18) ; plante avec 2 actifs sauf avec `max_clusters=1`.
- **Lead/lag :** un décalage d'horodatage d'un seul pas fabrique un lead « significatif » dans 100 % des cas.
  tigramite sans FDR donne 16 à 30 % de faux liens, contre 2 % avec `fdr_bh`.
- **Bootstrap par blocs à n = 150, φ élevé :** couverture de 0,89, contre 0,80 pour le t naïf. C'est cohérent
  avec Q1.

## A-1 — Pile d'inférence : vérifications croisées (L2, lane A)

- **Longueur de bloc :** arch et tsbootstrap concordent à 1e-15 près.
- **PSR :** le code maison et quantstats concordent à 4e-4 près.
- **ESS :** concorde avec arviz, avec une précision d'environ ±40 % à n = 60.
- **SPA/StepM/MCS :** 0,04 s pour 3 bras.
- **Installation de confseq :** échoue sur Python 3.11 et avec NumPy 2 ; un patch de 6 lignes est fourni.
- **Installation d'obp :** échoue sur Python 3.11.

## I-1 — Calendrier économique : assemblage officiel, ForexFactory, connecteur TipRanks (L2, lane I + orchestrateur)

Voir `evidence/raw_laneI.md` §1–2 et `evidence/raw_orchestrator.md` O1.

- **Export ForexFactory :**
  - pas de champ `actual` ;
  - le JSON est à l'heure de New York avec offset, le XML en UTC sans marqueur ; les 79 événements sont cohérents
    entre les deux une fois convertis ;
  - aucun identifiant d'occurrence ;
  - mise à jour horaire, et HTTP 429 au-delà d'environ 4 requêtes en 7 min.
- **BEA :**
  - ICS : 119 événements en UTC, avec des UID uniques ;
  - JSON : 6 dates dupliquées.
- **Guest Trading Economics :** HTTP 410 (supprimé).
- **FMP, Finnhub :** HTTP 401 (clé requise).
- **TipRanks (connecteur) :**
  - actual, estimate et prev présents ;
  - heure en UTC sans marqueur ;
  - pas d'identifiant ;
  - aucun événement « Euro Zone » renvoyé.
