# 01 — Landscape: where candidate primitives were discovered

Sources searched (2026-09-29): arXiv/SSRN/RePEc and journal pages, BIS/NY Fed/Bank of Canada working papers, exchange/vendor research (Deribit Insights, Amberdata, K33, Bytetree), serious OSS (CCXT, hmmlearn, ruptures, alphalens-reloaded, Freqtrade, Hummingbot), and the lab's prior corpus (report 005 on public feeds). Two research passes were run by sub-agents; each source carries a status: VERIFIED (page opened, title/authors/year confirmed), PARTIAL (only via search snippet), NON_VÉRIFIÉ. **The lead analyst did not independently re-open every page**; all empirical claims are `DOCUMENTED_CLAIM` (reported by the source, not reproduced here). Formulas labelled generic are standard definitions, not extractions from the PDFs.

## Family → what was found → what was executed
| Family (requested) | Evidence quality found | Executed as | Not executed (see 02 tail) |
|---|---|---|---|
| momentum / trend | crypto trend factor (Fieberg et al., JFQA 2025), intraday TS momentum (Shen et al. 2022) — DOCUMENTED_CLAIM of net survival on wide coin universes | P01 | D24, D27, D28 |
| mean reversion | De Nicola 2021 (1–4h negative autocorr, BTC); Zaremba et al. 2021 (reversal only in illiquid coins) | P03, P11 | — |
| vol compression/expansion | no verified academic crypto source (gap); blogs only | P04 | D34 |
| carry | BIS WP 1087 (Crypto Carry), He–Manela–Ross–von Wachter perpetual-futures paper | P06 | D30, D33 |
| basis | BIS WP 1087; premium-index mechanism | P07 | D16, D17 |
| funding divergence | cross-venue funding differences documented in lab report 005; no verified predictive paper | P15 | — |
| OI / price divergence | no verified academic source on predictive power (gap); vendor/blog narrative | P08 | D20 |
| liquidation pressure | cascade-dynamics papers (2026 arXiv, very recent, not peer-reviewed); no complete public liquidation history | P09 (OI-flush *proxy*) | D21 |
| volume imbalance | Cont–Kukanov–Stoikov OFI (equities), Kim & Hansen quarter-hour effect 2026 | P10 (taker-flow, 1h) | D26 |
| liquidity shocks | Deng & Zhou 2023/2025 (Amihud-type); "Realized Illiquidity" not verifiable | P11 | D19 |
| realized vs implied vol | Almeida et al. 2024/25 (BTC VRP); Alexander & Imeraj (not verifiable) | P14 | D32 |
| term structure | BIS carry paper; Deribit reports not verifiable | — | D16, D17 |
| cross-asset lead/lag | Kurihara–Matsumoto 2026 (PARTIAL), Pascual et al. 2025 (price discovery) | P12 | D31 |
| cross-sectional relative strength | Fieberg et al., Liu–Tsyvinski–Wu (PARTIAL) | P02 | — |
| intraday seasonality | Padyšák–Vojtko 2022 vs Baur et al. 2017 (contradictory); Hansen–Kim–Kimbrough 2021; Krohn–Mueller–Whelan (FX fixings) | P13 | D29 |
| breakout persistence | no verified academic source (gap) | P05 (baseline), P04 | — |
| regime-conditioned | HMM (Koki et al.), Daniel–Moskowitz momentum crashes; smoothed-state lookahead risk | regime analysis layer (07) + P04 gate | D22, D23 |
| event-driven macro | NY Fed / Croushore–Stark vintages (lookahead), no verified 2023–26 CPI/FOMC crypto/gold effect | — | D18 |

Honest gaps: no verified academic source for OI/price predictive power, breakout persistence in crypto, or intraday reversal on majors post-2023; FX-carry sources are pre-2016; several 2026 arXiv items are unreviewed and one PDF was unreadable. Where evidence was thin, the primitive was still executed as a *falsifiable mechanism*, not as an evidence-backed claim.

## Appendix A — sub-agent notes: crypto derivatives / microstructure families
# Landscape A - Primitives de signal marché crypto intraday (paper only)

Date de vérification : 2026-09-29. "VÉRIFIÉ" = page ouverte via WebFetch, titre/auteurs/date confirmés.
Toute affirmation empirique = DOCUMENTED_CLAIM (rapportée par la source, non reproduite ici).
Les formules marquées [GÉNÉRIQUE] sont des définitions standard, PAS extraites d'un papier sauf mention.
Lacunes honnêtes : peu de sources académiques vérifiées sur (a) OI-vs-prix prédictif, (b) breakout/compression crypto ; voir "Trous".

## 1. Funding rate / carry perp

| Source | Mécanisme | Signal / formule | Horizon | Inputs | Limites / lookahead | Claim (DOCUMENTED_CLAIM) |
|---|---|---|---|---|---|---|
| S1 He, Manela, Ross, von Wachter, "Fundamentals of Perpetual Futures" (arXiv 2212.06888, v1 2022, dernière révision v7 sept. 2026) VÉRIFIÉ | Le funding (longs paient shorts, proportionnel à l'écart perp-spot) ancre le perp au spot ; l'écart au prix sans-arbitrage est exploitable | Prix perp no-arb + bornes avec coûts de transaction ; stratégie implicite d'arbitrage (long spot / short perp quand écart > bornes) | jours-semaines (funding périodique) | perp, spot/index, funding, frais | Coûts de trading, marge, risque de contrepartie ; détails de lookahead NON lus dans le texte complet | Écarts crypto >> FX traditionnel, décroissent dans le temps, corrélés entre devises ; Sharpe élevé même avec les frais Binance les plus hauts |
| S2 Kim & Park, "Designing funding rates for perpetual futures in cryptocurrency markets" (arXiv 2506.08573, juin 2025) VÉRIFIÉ | Conception théorique du funding pour garder le perp aligné à la cible | BSDE infinies path-dependent ; funding path-dependent | théorique | modèle | Purement théorique, pas de signal de trading | Un funding bien conçu maintient le perp près de la valeur cible ; portefeuille de réplication pour l'émetteur |
| S3 Zhu (avec Hasu), "Perpetual Swaps: Comparisons and Findings" (Deribit Insights, 17 déc. 2019) VÉRIFIÉ (hors fenêtre 2023-26, contexte) | Funding varie selon devise de règlement, fenêtre, indice de référence | Pas de formule explicite dans l'article | 8h | funding par exchange | Données 2019 seulement | Funding annualisé 14-26 % sept-nov 2019 ; levier réel << levier affiché |
| S4 Amberdata (Marshall), "Leverage & Liquidations: The $31B Deleveraging" (25 mars 2026) VÉRIFIÉ (blog, non peer-reviewed) | Funding élevé prolongé = positionnement long saturé | Seuil heuristique funding > 15 % APR soutenu = alerte (choisi par l'auteur) | jours | funding, OI | Seuils ad hoc, pas de test out-of-sample | Pic 29,9 % APR ; 8,7 % APR à date de rédaction |

Pour la primitive : `funding_z = (funding_8h - MA_n) / sd_n` ; `carry_ann = funding_8h * 3 * 365` [GÉNÉRIQUE]. Utiliser uniquement le funding *déjà publié* à t (le funding prédit vs réalisé est un piège de lookahead).

## 2. Basis et term structure futures

| Source | Mécanisme | Signal | Horizon | Inputs | Limites | Claim |
|---|---|---|---|---|---|---|
| S5 Schmeling, Schrimpf, Todorov, "Crypto Carry" (BIS Working Paper 1087, 4 avr. 2023) https://www.bis.org/publ/work1087.htm VÉRIFIÉ | Demande de levier des petits investisseurs + capital d'arbitrage limité ; variation du carry = convenience yield | Carry = base annualisée future vs spot (cash-and-carry) | semaines-mois | futures BTC/ETH, spot | Détails lookahead non lus (résumé de page) ; marges/liquidation limitent l'arbitrage | Carry crypto > 10 %/an en moyenne, >> autres classes ; carry élevé prédit des crashs ; futures plus volatils que spot |
| S6 Matsui, Al-Ali, Knottenbelt, "On the Dynamics of Solid, Liquid and Digital Gold Futures" (arXiv 2202.09845, fév. 2022) VÉRIFIÉ (hors 2023-26) | Convergence du basis vers 0 à l'échéance | Régression basis ~ maturité, volume, OI | journalier | prix, maturité, volume, OI 2017-2021 | Échantillon 2017-2021 | Maturité affecte positivement le basis BTC ; volume -> volatilité (+) ; OI parfois effet négatif |
| S7 K33 Research (Lunde), "500,000 Leveraged Bitcoins" (11 oct. 2022) VÉRIFIÉ (hors fenêtre, blog) | Basis CME 3M bas + OI perp record | Basis, OI/market cap (BTC 3,21 %) | jours-semaines | basis, funding, OI | Anecdotique, une seule période | Levier record + vol implicite basse => squeeze attendu (thèse de l'auteur) |
| S8 Deribit Insights, rapports hebdomadaires (ex. week 36, 45) : URL trouvées par recherche, NON_VÉRIFIÉ (contenu non ouvert) | Rendements annualisés par échéance | Courbe de rendement futures | hebdo | prix futures | - | NON_VÉRIFIÉ |

Primitive : `basis_ann(T) = (F_T/S - 1) * 365/dte` ; pente = basis(3M) - basis(1M) ; perp-vs-trimestriel [GÉNÉRIQUE].

## 3. Open interest vs prix (divergence)

| Source | Mécanisme | Signal | Horizon | Inputs | Limites | Claim |
|---|---|---|---|---|---|---|
| S4 Amberdata (ci-dessus) VÉRIFIÉ | OI en hausse + prix en baisse = levier contre-tendance ; fragilité | OI, liquidations/OI | jours | OI agrégé | Blog | OI pic 54,7 Mds$ (été 2025), -42 % ensuite |
| S7 K33 (ci-dessus) VÉRIFIÉ | Levier record | OI / market cap | semaines | OI, market cap | Une observation | Voir ci-dessus |
| S9 Cheng, Deng, Wang, Yu, "Liquidation, Leverage and Optimal Margin in Bitcoin Futures Markets" (arXiv 2102.04591, fév. 2021) VÉRIFIÉ (hors fenêtre) | Liquidations/OI mesurent le levier moyen | Liquidations forcées / futures en circulation ; théorie des valeurs extrêmes | journalier | volume, liquidations, OI, OHLC (BitMEX) | BitMEX 2021 seulement | Liquidations quotidiennes 3,51 % (longs) / 1,89 % (shorts) de l'OI ; levier moyen des liquidés ~60x |
| axeladlerjr.com "Bitcoin Open Interest vs Price: 4 Divergence Patterns" NON_VÉRIFIÉ (extrait de recherche seulement) | - | - | - | - | - | NON_VÉRIFIÉ |

Primitive : `dOI_z`, `sign(dOI) * sign(dPrice)` en 4 quadrants ; OI normalisé par volume ou market cap [GÉNÉRIQUE]. Attention : OI par exchange arrive avec des délais/restatements, à aligner point-in-time. Aucune source académique vérifiée démontrant un pouvoir prédictif de la divergence OI/prix : à traiter comme hypothèse à tester.

## 4. Liquidations / cascades

| Source | Mécanisme | Signal | Horizon | Inputs | Limites | Claim |
|---|---|---|---|---|---|---|
| S10 Garcia Seuma, "Measuring the engine of a liquidation cascade: subcritical branching inside a first-order transition" (arXiv 2608.03616, 2026) VÉRIFIÉ (via RePEc/arXiv résumé) | Cascade = branchement auto-excité (feedback liquidation -> prix -> liquidation) | Ratio de branchement lambda (processus de Hawkes-like), couplage cross-asset | minutes (88 % du forcé en 30 min) | liquidations on-chain d'un venue transparent, 7 cascades 2022-25 | 7 événements ; un seul venue ; papier très récent, non peer-reviewed | lambda ~0,1-0,2 (sous-critique) ; 63 % absorbé par backstop ; couplage inter-actifs +1,6 à +4,4 sigma au début ; sévérité = choc x liquidité retirée |
| S11 Garcia Seuma, "Where does the criticality live? Early-warning signals are event-heterogeneous across seven crypto-perpetual liquidation cascades" (arXiv 2607.27070, 2026) : titre/auteur/ID vérifiés via métadonnées PDF ; contenu PDF illisible => résultats NON_VÉRIFIÉ ; un résumé de recherche (secondaire) indique pas de hausse pré-cascade de l'autocorrélation lag-1 sur prix, mais signal possible sur flux taker et OI | Early-warning (critical slowing down) | Autocorrélation lag-1, variance | minutes-heures | prix, taker flow, OI | Hétérogène selon événement | Résumé secondaire seulement |
| S4 Amberdata VÉRIFIÉ | Intensité de liquidation | `liq_intensity = liquidations_jour / OI` ; normal 0,5-2 %, élevé 2-5 %, cascade > 5 % | jour | liquidations, OI | Seuils empiriques ad hoc | 10 oct. 2025 : 4,82 % ; record 2,3 Mds$ (86 % longs) |
| S9 Cheng et al. VÉRIFIÉ | voir §3 | | | | | |

Note : deux sources donnent des chiffres différents pour le 10 oct. 2025 (1,05 Md$ dans S11 via résumé secondaire vs 2,3 Mds$ dans S4) : dépend du périmètre (venue vs agrégé). Ne pas mélanger.
Lookahead : les flux de liquidations publics (Binance forceOrder stream) sont échantillonnés/partiels ; risque de biais de couverture.

## 5. Déséquilibre taker / order-flow imbalance

| Source | Mécanisme | Signal / formule | Horizon | Inputs | Limites | Claim |
|---|---|---|---|---|---|---|
| S12 Cont, Kukanov, Stoikov, "The Price Impact of Order Book Events" (arXiv 1011.6402, 2010 ; J. Financial Econometrics 12(1), 2014) VÉRIFIÉ (fondation, hors fenêtre, actions US) | Variation de prix ~ déséquilibre offre/demande au meilleur bid/ask | OFI = somme des variations de taille au best bid/ask signées ; DeltaP = beta * OFI, beta ~ 1/profondeur | secondes-minutes | L1 order book | Actions NYSE ; crypto à valider ; volume moins informatif que OFI | Relation linéaire, stable entre échelles et titres ; explique la racine carrée |
| S13 Kim & Hansen, "The Quarter-Hour Effect: Periodic Algorithmic Trading and Return Predictability in Cryptocurrency Futures" (arXiv 2607.09426, juil. 2026) VÉRIFIÉ | Trading algo périodique aux marques 1/5/15 min | Order imbalance à l'ouverture du quart d'heure (calendrier, indépendant du volume total) | 4-12 h | trades Binance, 6 perps | 6 perps Binance seulement ; papier récent | Imbalance au quart d'heure prédit les rendements sur 4-12 h ; effet faible aux résolutions fines |
| S14 Bieganowski & Slepaczuk, "Explainable Patterns in Cryptocurrency Microstructure" (arXiv 2602.00776, 31 janv. 2026) VÉRIFIÉ | Features carnet + trades, SHAP | OFI, spread, adverse selection ; CatBoost, validation temporelle | court terme | carnet + trades Binance Futures 1 s, BTC LTC ETC ENJ ROSE 2022-oct. 2025 | ML ; coûts/latence réels à vérifier | Importance des features et formes SHAP similaires entre actifs ; backtests taker top-of-book et maker profondeur fixe |
| S15 Rahman & Upadhye, "Hybrid Vector Auto Regression and Neural Network Model for Order Flow Imbalance Prediction in High Frequency Trading" (arXiv 2411.08382, nov. 2024) VÉRIFIÉ | Prédire l'OFI lui-même | VAR + FNN | non précisé | données Binance + synthétiques | Horizon non spécifié | Hybride > modèles seuls |

Primitive : `taker_imb = (V_buy_taker - V_sell_taker)/(V_buy + V_sell)` ; OFI L1 selon S12 [S12 pour OFI ; taker_imb GÉNÉRIQUE]. Lookahead : agréger sur des barres clôturées, signer les trades avec le flag `isBuyerMaker` fourni, pas la règle de Lee-Ready sur données arrondies.

## 6. Chocs de liquidité (Amihud, volume shocks)

| Source | Mécanisme | Signal | Horizon | Inputs | Limites | Claim |
|---|---|---|---|---|---|---|
| S16 Deng & Zhou, "Liquidity Premium, Liquidity-Adjusted Return and Volatility, and Extreme Liquidity" (arXiv 2306.15807, juin 2023, rév. fév. 2024) VÉRIFIÉ | Illiquidité extrême ; prime de liquidité minute | ILR Amihud minute-level à partir de tick data ; beta de prime de liquidité ; ARMA-GARCH ajusté | minute-jour | tick data 10 cryptos | Validation par portefeuille moyenne-variance | Modèles ajustés supérieurs en prédictibilité à liquidité extrême |
| S17 Deng & Zhou, "Liquidity-adjusted Return and Volatility, and Autoregressive Models" (arXiv 2503.08693, mars 2025) VÉRIFIÉ | Liquidity jump / diffusion | Métriques de saut/diffusion de liquidité | intraday | crypto | idem | Plus de sensibilité aux chocs passés, moins de persistance de vol |
| S18 "Realized Illiquidity", Management Science (DOI 10.1287/mnsc.2023.02505) : page inaccessible (HTTP 403) ; NON_VÉRIFIÉ (auteurs/année non confirmés). Résumé de recherche secondaire : "realized Amihud" = variation puissance réalisée intraday / volume quotidien, prédit les rendements court terme | | | | | | NON_VÉRIFIÉ |

Primitive : `amihud_t = |r_t| / dollar_vol_t` sur barres 1-5 min, z-score contre distribution saisonnière (heure du jour) ; `volume_shock = vol_t / median_vol(même heure, N jours)` [GÉNÉRIQUE]. Résultat secondaire de recherche (non vérifié) : la mesure d'Amihud aurait des problèmes en crypto ; à tester empiriquement.

## 7. Realized vs implied vol / VRP (DVOL)

| Source | Mécanisme | Signal | Horizon | Inputs | Limites | Claim |
|---|---|---|---|---|---|---|
| S19 Almeida, Grith, Miftachov, Wang, "Risk Premia in the Bitcoin Market" (arXiv 2410.15195, oct. 2024, rév. août 2025) VÉRIFIÉ | Le vendeur d'options est rémunéré ; VRP dépend du régime de vol | BVRP = variance risque-neutre (densités implicites d'options) - variance réalisée ; clustering de densités | mensuel (dérivé d'options) | options BTC (Deribit selon résumé de recherche, non confirmé dans la page ouverte) | Horizon long ; pas un signal intraday | BTC a un VRP > S&P 500 ; VRP plus haut en régime bas-vol ; régimes deux états |
| S20 Alexander & Imeraj, "The Bitcoin VIX and its variance risk premium" (Journal of Alternative Investments, 2020-2021) : existence corroborée par plusieurs résultats de recherche (Sussex/SSRN) mais page figshare 403 ; NON_VÉRIFIÉ pour formule/claims | | | | | | NON_VÉRIFIÉ |
| S21 Pervaiz et al., "Fear and Volatility in Digital Assets" (arXiv 2010.15611, oct. 2020) VÉRIFIÉ (hors fenêtre) | Vol implicite prévisible à partir de prix, momentum de vol, données alt | Prédiction de vol implicite BTC à 5 min | 5 min | prix, vol momentum, Google Trends, sentiment ; code GitHub | 2020 ; prévisibilité "modeste" | Vol implicite à 5 min modestement prédictible |
| S22 Qian, Wang, Ma, Li, "Bitcoin volatility predictability - The role of jumps and regimes" (Finance Research Letters 47, 2022) VÉRIFIÉ | Sauts + régimes améliorent la prévision de RV | MIDAS + saut continu + Markov-switching | jour | RV BTC | Hors fenêtre | Gains de précision et économiques significatifs, surtout en périodes volatiles |
| Documentation Amberdata DVOL https://docs.amberdata.io/docs/iv-dvol et Deribit DVOL : trouvées par recherche, NON_VÉRIFIÉ en détail (DVOL = vol implicite 30j annualisée depuis le smile) | | | | | | résumé secondaire |

Primitive : `VRP_t = DVOL_t^2 - RV_{t-30d..t}^2` (RV annualisée à même unité), ou `DVOL - RV_forward` pour l'étude *ex post* seulement. LOOKAHEAD CRITIQUE : ne jamais utiliser RV future dans le signal live ; RV trailing uniquement.

## 8. Compression / expansion de volatilité et persistance de breakout

| Source | Mécanisme | Signal | Horizon | Inputs | Limites | Claim |
|---|---|---|---|---|---|---|
| S23 Morris & Ali, "Bitcoin's Bullish Volatility Signal" (Bytetree, 12 août 2026) VÉRIFIÉ (blog) | Compression de vol précède les mouvements directionnels | Vol 30j < 20 % | 12 mois | prix BTC journalier | 87 jours depuis 2010, événements chevauchants, pas de test statistique, biais de survie du narratif | Vol 30j < 20 % seulement 1,7 % des jours ; hausse dans les 12 mois, une exception 2018 à +23 % |
| S22 Qian et al. VÉRIFIÉ | Régimes de vol persistants | Markov-switching | jour | RV | | Régimes prévisibles |
| Documentation squeeze Bollinger/Keltner (sentimentrader, LuxAlgo, TradingView) : trouvées par recherche, NON_VÉRIFIÉ ; ne constituent pas des preuves académiques. Signalent le risque de faux positifs sur barre partielle (ATR/écart-type en formation) : utile comme piège de lookahead intrabarre | | | | | | NON_VÉRIFIÉ |

Primitive : `bw = (BB_up - BB_low)/SMA` ; percentile rolling de `RV_short/RV_long` ; squeeze = bw < percentile_p ; direction du breakout via signe de retour sur barre CLÔTURÉE [GÉNÉRIQUE]. Aucune source académique vérifiée sur la persistance de breakout crypto : trou.

## Projets OSS (licences vérifiées sur les pages GitHub)

| Projet | URL | Licence | Pertinence |
|---|---|---|---|
| CCXT | https://github.com/ccxt/ccxt | MIT | API unifiée >100 exchanges ; collecte OHLCV/trades ; support funding/OI par exchange non confirmé sur la page, à vérifier dans la doc |
| Freqtrade | https://github.com/freqtrade/freqtrade | licence présente, type non affiché dans l'extrait (un résultat secondaire de recherche indique GPLv3, NON_VÉRIFIÉ) | Backtest, futures (Binance, Bybit, OKX...) |
| Hummingbot | https://github.com/hummingbot/hummingbot | Apache 2.0 | Framework, perps, paper trading |

## Trous / à faire
- Pas de source académique vérifiée pour : OI-vs-prix prédictif, persistance de breakout crypto, Amihud crypto intraday (S18 inaccessible).
- Nombreux papiers 2026 (2607.*, 2608.*) très récents, non revus par les pairs : traiter avec prudence.
- Les tests de lookahead / point-in-time n'ont pas été extraits du texte complet des papiers (seulement résumés/abstracts ouverts) : les colonnes "Limites" reflètent l'abstract, pas une lecture intégrale.
- Le résultat de recherche de la source S11 (chiffre 1,05 Md$) est secondaire, non confirmé.
- Sources trouvées mais jamais ouvertes : Deribit weekly reports, axeladlerjr.com, Kaiko (Conor Ryder, extrait Bloomberg), Alexander & Imeraj.


## Appendix B — sub-agent notes: classic factors, seasonality, regimes, macro
# Landscape B — Primitives de signal (crypto + FX/or/indices, intraday, paper only)

Date de recherche : 2026-09-29. Statuts : VÉRIFIÉ = page ouverte (titre/auteurs/année confirmés par WebFetch) ; PARTIEL = confirmé seulement via résultats de recherche (page non lisible) ; NON_VÉRIFIÉ = non ouvert. Les claims sont des DOCUMENTED_CLAIM (affirmations des auteurs, non reproduites ici). Aucune formule n'est extraite des PDF sauf mention ; les "formules" ci-dessous sont la définition standard de la primitive, à re-vérifier dans le papier avant implémentation.

Limites : WebFetch résume via un petit modèle -> les chiffres cités sont ceux de la page/abstract, pas relus dans les tableaux. Peu de sources 2023-26 sur certains axes (FX carry, reversal intraday) : dit explicitement ci-dessous.

## Tableau de synthèse par famille

| Famille | Primitive (définition standard) | Horizon | Inputs | Risque lookahead principal | Sources (statut) |
|---|---|---|---|---|---|
| Momentum TS/CS crypto | r_{t-k,t} (vol-scalé : r/σ), signe ou rang ; CTREND = agrégat ML d'indicateurs techniques prix+volume | jours-mois | OHLCV daily, univers de coins | survivorship (coins délistés), univers "3000 coins" illiquides, rebalance au close utilisé pour signal | S1, S2 (VÉRIFIÉ) |
| Reversal court terme | -r_{t-1} (cross-section) ; autocorr négative 1-4h BTC | 1h-1j | prix/volume, illiquidité | signal calculé sur bar en cours ; coûts/spread sur petits coins | S3, S4 (VÉRIFIÉ) |
| Carry (crypto) | basis annualisé = (F/S - 1)*365/jours ; funding perp | jours-semaines | spot, futures/perp, funding | funding versé à des instants discrets ; mark vs last ; liquidation | S5, S6 (VÉRIFIÉ) |
| Carry (FX) & momentum FX | carry = i_high - i_low (ou forward discount) ; mom = rendement passé 1-12m | mois (daily rebal.) | taux/forwards, spots | taux de dépôt vs forwards (données point-in-time), crash risk | S7, S8, S9 (VÉRIFIÉ, anciens) |
| Lead/lag cross-asset | corr(r_BTC,t-lag ; r_alt,t) ; Granger ; DTW | secondes-heures | ticks/1m multi-symboles synchronisés | désynchronisation d'horodatage, latence d'exécution vs lag de l'effet | S10 (PARTIEL), S11, S12 (VÉRIFIÉ) |
| Force relative CS | rang de r/σ ou d'un score composite | jours | OHLCV | idem momentum | S2, S13 (VÉRIFIÉ pour S2) |
| Saisonnalité intraday | moyenne conditionnelle heure-du-jour (UTC), vol par heure ; fixing FX | heure | barres 1h/1m UTC | data-snooping sur heure choisie ; fuseau/DST ; effet instable | S14-S17 |
| Régimes / gating | HMM, clusters, vol-scaling, panic state | j-semaines | rendements, vol réalisée, implicite | HMM ajusté full-sample = lookahead (états lissés) ; utiliser filtered probs | S18, S19, S20 (VÉRIFIÉ) |
| Événements macro | fenêtre 1h autour FOMC/CPI, surprise = actual - consensus | minutes-1h | calendrier, consensus, actual (horodaté) | timestamps de publication ; consensus vs révisions ; vintages | S21, S22 (VÉRIFIÉ / PARTIEL), S23 |
| Term structure vol / futures | VIX-like BTC (formule variance swap), VRP = IV² - RV², pente futures | j-semaines | chaînes d'options Deribit, futures | RV calculée avec fenêtre future ; IV snapshot non simultané | S24 (PARTIEL), S25 (VÉRIFIÉ) |

## Sources détaillées

### Momentum / trend / relative strength crypto
**S1. A Trend Factor for the Cross Section of Cryptocurrency Returns** — Fieberg, Liedtke, Poddig, Walker, Zaremba. JFQA 60(7), publié en ligne juil. 2025. https://www.cambridge.org/core/journals/journal-of-financial-and-quantitative-analysis/article/trend-factor-for-the-cross-section-of-cryptocurrency-returns/4C1509ACBA33D5DCAF0AC24379148178 — VÉRIFIÉ.
- Mécanisme : sous-réaction/tendance ; combinaison de signaux techniques multi-horizons. Signal : CTREND (agrégation par ML d'indicateurs prix+volume, détails à lire dans le papier). Horizon : hebdo (à confirmer). Inputs : OHLCV >3000 coins.
- DOCUMENTED_CLAIM : prédit les rendements, non subsumé par facteurs connus, robuste par sous-périodes/états de marché, survit aux coûts et persiste sur coins grands/liquides.
- Lookahead : entraînement ML -> exiger walk-forward ; survivorship de l'univers.

**S2. Common Risk Factors in Cryptocurrency** — Liu, Tsyvinski, Wu. Journal of Finance 77(2), 2022. Confirmé par résultat de recherche (pas de page ouverte) -> PARTIEL. Facteurs cross-section : taille, momentum, "value". Ancien (2022) mais référence de base ; à ouvrir avant citation finale.

**S2b. Momentum Trading in Cryptocurrencies: A Comparative Study of Time-Series and Cross-Sectional Strategies** — https://www.journals.vu.lt/BATP/article/view/44540 — auteurs/année NON_VÉRIFIÉ (page non ouverte). Claim rapporté par le moteur de recherche : TSMOM > CSMOM en risque-ajusté. À traiter comme piste seulement.

**S2c. Bitcoin Intraday Time-Series Momentum** — Shen, Urquhart, Wang. Financial Review 57(2), 319-344, 2022. DOI 10.1111/fire.12290. https://research.birmingham.ac.uk/en/publications/bitcoin-intraday-time-series-momentum/ — VÉRIFIÉ.
- Signal : rendement de la première demi-heure prédit la dernière demi-heure (sessions définies par le volume, BTC 24/7). Horizon : intraday. Claim : gains surtout en marché baissier ; attribué à la fourniture de liquidité. Lookahead : définition de "première/dernière demi-heure" doit être fixée ex ante (session par volume calculée avec données du jour = risque).

### Mean reversion / reversal court terme crypto
**S3. Up or down? Short-term reversal, momentum, and liquidity effects in cryptocurrency markets** — Zaremba, Bilgin, Long, Mercik, Szczygielski. Int. Review of Financial Analysis 78, 2021. https://ideas.repec.org/a/eee/finana/v78y2021ics1057521921002349.html — VÉRIFIÉ.
- Signal : -r(t-1) en cross-section. DOCUMENTED_CLAIM : coins à faible rendement de la veille surperforment (>3600 coins), dû à l'illiquidité ; les plus grands coins montrent du momentum journalier, pas du reversal. Implication : ne pas transférer le reversal aux majors.

**S4. On the Intraday Behavior of Bitcoin** — De Nicola. Ledger 6, 2021. https://ledger.pitt.edu/ojs/ledger/article/view/213 — VÉRIFIÉ.
- DOCUMENTED_CLAIM : autocorrélation d'ordre 1 négative significative à 1h, 2h, 4h ; reversals plus forts après grands mouvements ; explications : overreaction, liquidations en cascade ; stratégies simples profitables en backtest. Lookahead : return de barre courante inutilisable avant clôture. Sources hors fenêtre 2023-26 : nous n'avons pas trouvé de source plus récente vérifiée.

### Carry crypto et FX
**S5. Crypto Carry** — Schmeling, Schrimpf, Todorov. BIS WP 1087, avr. 2023 (révisé oct. 2025). https://bis.org/publ/work1087.htm — VÉRIFIÉ.
- Signal : basis futures/spot annualisé (cash-and-carry). Claim : carry moyen >10 % p.a., pics jusqu'à 40-60 % ; variation liée aux rendements de commodité/convenance et à la rareté de capital d'arbitrage ; carry élevé prédit des crashs ; risque de liquidation de la jambe d'arbitrage ; segmentation crypto/finance traditionnelle. Horizon : jours-mois.

**S6. Fundamentals of Perpetual Futures** — He, Manela, Ross, von Wachter. arXiv 2212.06888 (soumis 2022, révisions jusqu'à 2026). https://arxiv.org/abs/2212.06888 — VÉRIFIÉ.
- Mécanisme : funding proportionnel à l'écart futures-spot. Claim : déviations vs prix sans arbitrage plus grandes qu'en FX, corrélées entre coins, décroissantes ; stratégie d'arbitrage à Sharpe élevé même avec frais Binance (à re-tester net de slippage). Lookahead : timestamp du funding et de l'index price.

**S7. Currency Momentum Strategies** — Menkhoff, Sarno, Schmeling, Schrimpf. BIS WP 366, 2011 (JFE 2012). https://www.bis.org/publ/work366.pdf — VÉRIFIÉ (ancien, référence).
- Signal : rang des devises sur le rendement passé ; spread gagnants-perdants jusqu'à 10 % p.a. ; limites à l'arbitrage, coûts. Formation period non lue dans l'extrait.

**S8. Carry and Trend Following Returns in the Foreign Exchange Market** — Clare, Seaton, Smith, Thomas. Univ. of York DP 15/07, 2015. https://ideas.repec.org/p/yor/yorken/15-07.html — VÉRIFIÉ.
- Claim : carry et trend-following ont des excès de rendement comparables ; trend sans skewness négative, donc hedge du carry ; liquidité de marché explique >90 % de la variation des portefeuilles (CAPM conditionnel).

**S9. Carry Trades and Currency Crashes** — Brunnermeier, Nagel, Pedersen (NBER 2008). Trouvé via recherche (AQR/Princeton), page NON_VÉRIFIÉ. Ne pas citer sans ouverture. Note : je n'ai pas trouvé de source FX-carry 2023-26 vérifiée ; une mention d'un papier de juil. 2024 (crash risk = 62 % du carry) est NON_VÉRIFIÉ (titre/auteurs inconnus).

### Lead/lag cross-asset
**S10. Price Transmission from Bitcoin to Altcoins: High-Frequency Evidence and Implications for Trading Strategy** — Kurihara, Matsumoto. Asia-Pacific Financial Markets, 2026. Repo : https://t2r2.star.titech.ac.jp/rrws/file/CTT100941776/ATD100000413/ — PARTIEL (PDF non lisible par l'outil ; métadonnées via recherche).
- Claim rapporté : petits coins réagissent en retard aux rendements BTC ; causalité de Granger BTC->alts ; stratégie "lag" > buy-and-hold. À relire avant usage (latence d'exécution, coûts, ML).

**S11. Price Discovery in Cryptocurrency Markets** — Pascual, Rubio, Cebada, Veciana. arXiv 2506.08718, juin 2025. https://arxiv.org/abs/2506.08718 — VÉRIFIÉ.
- Méthodes : Hasbrouck information share, Gonzalo-Granger, Hayashi-Yoshida. Claim : exchanges centralisés (Binance) dominent Uniswap v2 pour ETH ; futures CME mènent le spot BTC en général, incohérent en forte vol. Utile pour choisir le venue de référence (leader) ; un an de données, échantillon limité.

**S12. Cross Cryptocurrency Relationship Mining for Bitcoin Price Prediction** — Li, Gong, Xu, Zhou, Yu, Xuan. arXiv 2205.00974, 2022. https://arxiv.org/abs/2205.00974 — VÉRIFIÉ. DTW pour lead-lag altcoins -> BTC ; prédiction ML ; faible poids (deep learning, validation à examiner).

Lien crypto<->actions/macro : sources trouvées = blogs/analyses de marché (The Block, K33, etc.), corrélation BTC-Nasdaq instable, forte en stress. NON_VÉRIFIÉ, pas de papier académique récent confirmé.

### Saisonnalité intraday
**S14. Are There Seasonal Intraday or Overnight Anomalies in Bitcoin?** — Padyšák, Vojtko (Quantpedia). 2022. https://quantpedia.com/are-there-seasonal-intraday-or-overnight-anomalies-in-bitcoin/ — VÉRIFIÉ (page de synthèse, pas le papier SSRN).
- Signal : long 21:00->23:00 UTC ; pire 03-04 UTC. Données Gemini horaires 2015-02/2022. Claim ~33 % annualisé, vol 20,9 %, MDD -22,5 %. Risque : data-snooping massif (choix de l'heure ex post), pas de frais.

**S15. Periodicity in Cryptocurrency Volatility and Liquidity** — Hansen, Kim, Kimbrough. arXiv 2109.12142, 2021. https://arxiv.org/abs/2109.12142 — VÉRIFIÉ.
- Patterns récurrents (jour-de-semaine, heure, intra-heure) en vol et volume, BTC/ETH sur Coinbase Pro, Binance, Uniswap ; plus forts avec le temps, liés au trading algo et aux calendriers de funding. Bon candidat : modèle de vol saisonnière comme normalisation/gating plutôt que signal directionnel.

**S16. Bitcoin Time-of-Day, Day-of-Week and Month-of-Year Effects in Returns and Trading Volume** — Baur, Cahill, Godfrey, Liu. Working paper (UWA), 2017. https://research-repository.uwa.edu.au/en/publications/bitcoin-time-of-day-day-of-week-and-month-of-year-effects-in-retu/ — VÉRIFIÉ. Claim : effets variables dans le temps, sans patterns persistants -> contre-évidence à S14. Ancien.

**S17. Foreign Exchange Fixings and Returns Around the Clock** — Krohn, Mueller, Whelan. Journal of Finance 79(1), 2024 (Bank of Canada SWP 2021-48). https://ideas.repec.org/p/bca/bocawp/21-48.html — VÉRIFIÉ.
- Signal : USD s'apprécie avant les fixings et se déprécie après (forme en W) ; canal = couverture des dealers. Applicable FX/or (fixings WMR 16:00 Londres, LBMA) ; horodatage précis des fixes + DST = risque principal.

### Régimes / gating
**S18. Exploring the Predictability of Cryptocurrencies via Bayesian Hidden Markov Models** — Koki, Leonardos, Piliouras. arXiv 2011.03741, 2020. https://arxiv.org/abs/2011.03741 — VÉRIFIÉ. HMM non homogène à 4 états, meilleure prévision 1 pas ; régimes bull/bear/calme pour BTC. Risque : états lissés = lookahead ; utiliser probabilités filtrées.

**S19. Momentum Crashes** — Daniel, Moskowitz. NBER WP 20439 (2014). https://causalclaims.trfetzer.com/paper/w20439.html — VÉRIFIÉ (miroir, pas nber.org). Momentum dynamique (forecast de moyenne et variance, états "panic") ~double alpha et Sharpe. Primitive de gating : réduire l'exposition momentum après baisse de marché + vol élevée.

**S20. Risk Premia in the Bitcoin Market** — Almeida, Grith, Miftachov, Wang. arXiv 2410.15195, 2024 (rév. août 2025). https://arxiv.org/abs/2410.15195 — VÉRIFIÉ. Clustering de densités risque-neutres (options) -> 2 régimes de vol ; VRP plus élevée en régime calme. Inputs : options Deribit 2017-2022.

### Événements macro
**S21. Is There a Bitcoin–Macro Disconnect?** — Benigno, Rosa. NY Fed Staff Report (2023). https://ideas.repec.org/p/fip/fednls/95609.html — VÉRIFIÉ (numéro de staff report non confirmé). Claim : BTC ne réagit pas significativement aux news macro/monétaires US (échantillon ancien), analyse haute fréquence.

**S22. NY Fed Staff Report 1052** (lien issu de recherche sur réaction crypto CPI/FOMC). https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr1052.pdf — PDF illisible par l'outil, titre/auteurs NON_VÉRIFIÉ ; ne pas citer avant lecture.

**S23. Real-time data (lookahead macro)** — Croushore, Stark. "A Real-Time Data Set for Macroeconomists", Philadelphia Fed WP 99-4, juin 1999. https://www.philadelphiafed.org/the-economy/macroeconomics/a-real-time-data-set-for-macroeconomists — VÉRIFIÉ. Vintages des données macro : analyses sur données révisées = résultats trompeurs. Implication moteur : utiliser première publication horodatée (ALFRED/vintages) et consensus contemporain ; jamais la série finale révisée. Pour le trading événementiel : surprise = actual (1ère publi.) - consensus ex ante ; Pas de source 2023-26 vérifiée pour l'effet CPI/FOMC sur or/FX ; les chiffres de blogs (Block Scholes, R² 1h ~80 %) sont NON_VÉRIFIÉS.

### Term structure de vol / futures
**S24. The Bitcoin VIX and its Variance Risk Premium** — Alexander, Imeraj. Journal of Alternative Investments (2023). Page Sussex figshare (403 à l'ouverture) : PARTIEL via recherche. Indices de vol implicite à échéances 1 sem-3 mois (formule variance swap CBOE), Deribit, mars 2019-mars 2020, 15 min ; VRP BTC ≫ S&P.

**S25.** S20 (Almeida et al.) et S5 (Crypto Carry : pente futures) couvrent aussi cette famille. Blog Deribit Insights "bitcoin options finding edge in four years of volatility regimes" : NON_VÉRIFIÉ (non ouvert).

## OSS (licences lues sur les pages GitHub)
| Repo | Usage | Licence | Statut |
|---|---|---|---|
| https://github.com/hmmlearn/hmmlearn | HMM (régimes) | BSD-3-Clause | VÉRIFIÉ ; "limited-maintenance" ; attention aux probabilités lissées |
| https://github.com/deepcharles/ruptures | change-point offline | BSD-2-Clause | VÉRIFIÉ ; offline -> lookahead si utilisé en full-sample |
| https://github.com/stefan-jansen/alphalens-reloaded | analyse IC/quantiles de facteurs | Apache-2.0 | VÉRIFIÉ ; orienté actions |
| https://github.com/ccxt/ccxt | données/exécution multi-exchanges | MIT | VÉRIFIÉ |
| https://github.com/freqtrade/freqtrade | bot/backtest crypto | licence non lue sur la page (GPL-3.0 de mémoire) | NON_VÉRIFIÉ |

## Points de vigilance transverses
1. Beaucoup d'effets crypto sont documentés sur peu de coins liquides ou univers de milliers de coins illiquides ; vérifier la capacité (S3, S1).
2. Saisonnalité (S14) contredite par S16 -> à traiter comme hypothèse à tester en walk-forward, pas comme signal acquis.
3. Sources FX (S7-S9) anciennes ; aucune source 2023-26 FX-carry vérifiée dans cette passe.
4. Lookahead : régimes (HMM lissé), ML (CTREND), événements macro (vintages, horodatage), fixings (DST).

