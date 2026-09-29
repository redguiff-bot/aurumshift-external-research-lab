# 02 — Model landscape (A–L) and what this study actually tested

The mission forbids a bibliography-only report. This page is a map: for each family, *what the model claims*, *what data it needs*, *fit for non-HFT (AurumShift scale)*, and *what this study did with it*.
The long sourced notes (formulas, URLs, provenance tiers `[V]` verified-in-session vs `[M]` from memory) are appended verbatim below; **every `[M]` formula must be re-derived before being coded into anything**, and the ones actually coded here (Roll, Corwin–Schultz, Abdi–Ranaldo, Almgren–Chriss cost form, square-root, propagator kernel) were coded from the formulas quoted in the notes and checked only against synthetic data with known truth (they can therefore be wrong in constants; see `12`).

Labels: PROVEN · OBSERVED · DOCUMENTED_CLAIM · INFERENCE · UNKNOWN.

| # | Family | Representative models | Data required | Non-HFT fit | Status in this study |
|---|---|---|---|---|---|
| A | Spread estimation | quoted / effective / realized spread; Roll (1984); Corwin–Schultz (2012); Abdi–Ranaldo (2017); EDGE (Ardia et al. 2024, OSS `bidask`); trade-flip estimator | L1 + trades (effective/realized); OHLC (proxies) | Effective/quoted: excellent. OHLC proxies: only as bound | **Executed**: synthetic grid (`06`), live quotes vs proxies (`05`,`06`), Binance klines (`06`) |
| B | Slippage | fixed bps; spread-proportional; vol-scaled; size/depth; square-root; L2 walk | L1, OHLCV, or L2 | Good | **Executed** (synthetic, live snapshot-to-snapshot) (`07`) |
| C | Market impact | Almgren–Chriss (2000) linear; square-root law (Bouchaud, Tóth…); propagator (Bouchaud et al. 2004); Obizhaeva–Wang (2013); Gatheral no-dynamic-arbitrage constraints | metaorder-tagged fills or full tape + L2 | Square-root/propagator meaningful for multi-child parent orders; linear AC weak | AC-linear, sqrt, propagator **executed** (synthetic); flow–return regression on Binance aggTrades **executed**; Obizhaeva–Wang/Gatheral: theory only (PARK/constraint) |
| D | Fill probability | constant p; price-through (Brownian first-passage); displayed-queue vs trade volume; hybrid; Cont–Stoikov–Talreja; queue-reactive (Huang–Lehalle–Rosenbaum) | trades; L1 size; **L3/queue events** for CST/QR | Simple ones fine; CST/QR need event data | Simple four **executed** (synthetic + live bounds); CST/QR **MODEL_NOT_EMPIRICALLY_CALIBRATABLE_FROM_FREE_DATA** |
| E | Partial fills | depth-capped fills; probabilistic; participation caps | L2 | Good | **Executed** (depth-capped, `filled_fraction`) |
| F | Adverse selection | post-fill markout; realized spread; Kyle λ; VPIN | tape + mids | Markout/λ fine; VPIN contested (Andersen–Bondarenko) | markout, realized spread, λ **executed**; VPIN not executed |
| G | Maker/taker | Cartea–Jaimungal, Avellaneda–Stoikov style HJB; empirical fill/markout trade-off (Albers et al. 2025) | own quote–fill experiments | Only as a coarse decision rule | **Executed** decision grid (synthetic) + fill bounds (live) (`10`) |
| H | Scheduling | TWAP / VWAP / POV | volume profile | fine | TWAP (equal children) **executed**; VWAP/POV UNKNOWN (need intraday profile study) |
| I | Latency-to-price-risk | σ√L drift; winner's-curse on fills | timestamps, σ | simple bounded model adequate in RW regimes | **Executed** (synthetic sweeps, live drift, aggTrades drift) |
| J | Funding/borrow/roll | venue formulas; settlement discrete events; calendar spreads | rate histories, curves | essential | **Executed** on public data (`09`); FX/gold: UNKNOWN |
| K | Fragmentation | cross-impact, venue leadership | synchronous multi-venue books | matters via which book you walk | synthetic **executed**; live cross-venue snapshot dispersion **executed** |
| L | Implementation shortfall | Perold 1988; delay/spread/impact/opportunity/explicit decomposition | decision & arrival prices, fills | the accounting frame | ladder implemented & tested (`11`) |

Models discovered (named distinct models/estimators in this landscape and OSS probe): counted in the final block of `00`.

## Corrections to the appended notes (found while executing)

1. Latency arithmetic in note I: σ_annual = 60 %, L = 200 ms ⇒ σ√L = 0.6·√(0.2/31.536e6) ≈ 4.8e-5 = **0.48 bps**, not 0.15 bp (INFERENCE, arithmetic). Live BTC mid-drift over 1–4 s is measured directly in `10`.
2. Fee schedules for OKX/Bybit/Coinbase came from secondary aggregators and are UNKNOWN until the official tables are read; Binance futures 0.075 %/0.075 % is flagged unverified by the note itself. This study therefore treats fees as a **parameter** (5/2 bps and 10/8 bps taker/maker cells), never as a finding.
3. The "2026-prefixed arXiv IDs" cited in the notes come from the search tool and were not independently validated.
4. The square-root exponent for *current* crypto venues is UNKNOWN in the literature accessible here (one 2014 Mt.Gox-era paper; one non-peer-reviewed counter-example). This study's own Binance aggTrades flow–return exponent (0.67 for BTC 1-min bars, 0.85 ETH; `07`) is an **aggregate-flow regression**, not a metaorder study, and is confounded by reverse causality — it does not settle the question.

---

# Appendix — sourced landscape notes (verbatim)


## 0. How to read this note

Labels on every claim:
- PROVEN: mathematical identity or theorem under stated assumptions (not an empirical statement).
- OBSERVED: empirical finding reported in a paper/dataset, for the sample stated. Not guaranteed to transfer.
- DOCUMENTED_CLAIM: what an official venue/broker document or a paper's abstract says. Not independently verified.
- INFERENCE: my reasoning or synthesis, not a source statement.
- UNKNOWN: could not verify in this session.

Provenance tiers (important, be honest about what was checked):
- [V] = URL surfaced by search or fetched in this session, and the specific fact stated was in the returned text/abstract snippet.
- [M] = canonical reference I know well (formula/title/venue), URL given is the standard location, but the page was NOT opened in this session. Formulas marked [M] should be re-derived or checked against the paper before being coded into a benchmark.
- Several search results carried arXiv IDs with 2026 prefixes (e.g. 2605.*, 2607.*, 2609.*); I treat these as returned by the search tool and did not independently validate them.
- Third-party fee-aggregator sites were used only where the official page could not be fetched; they are flagged DOCUMENTED_CLAIM (secondary) and must be re-checked against the exchange page, since fee schedules change.

Gaps up front: OKX/Bybit/Coinbase official fee pages were not fetchable (404/403/JS-rendered); Binance USD-M futures fetch returned 0.075%/0.075% which contradicts common knowledge of a lower maker fee, so treated as UNVERIFIED (see J/Fees). FX broker and CME/COMEX contract specifics are only partially sourced.

---

## A. Spread estimation

### A.1 Definitions (PROVEN as definitions; standard microstructure) [M]
Let m_t = midquote at trade time, p_t = trade price, D_t = +1 buyer-initiated, -1 seller-initiated.
- Quoted spread: QS = (ask - bid); relative: QS/m.
- Effective spread: ES_t = 2 D_t (p_t - m_t) (relative: divide by m_t). Captures price improvement and trading inside/through quotes; needs the prevailing midquote and a trade-sign rule (Lee-Ready 1991, J. Finance; tick test, or exchange aggressor flag in crypto).
- Realized spread: RS_t = 2 D_t (p_t - m_{t+tau}), tau typically 5 min in equities (Huang-Stoll 1996). Effective spread = realized spread + price impact, where PI_t = 2 D_t (m_{t+tau} - m_t). This decomposition is an identity (PROVEN).
- INFERENCE: for a taker, ES is the right round-trip half-cost proxy; RS is what a maker would have earned net of adverse selection. For crypto venues that publish aggressor side (Binance aggTrades `m` flag, Coinbase `side`), trade signing is exact rather than estimated (DOCUMENTED_CLAIM; see venue API docs).
- Data required: L1 quotes (or L2 top-of-book) timestamped with trades, aggressor flag, tau grid; for tau choice in 24/7 markets, run 1s/10s/1m/5m and report the whole curve.

### A.2 Roll (1984) [M]
Roll, R. (1984), "A simple implicit measure of the effective bid-ask spread in an efficient market", J. Finance 39(4). https://doi.org/10.1111/j.1540-6261.1984.tb03897.x
- Model: p_t = m_t + (S/2) q_t, q_t iid +/-1, m_t random walk. Then Cov(dp_t, dp_{t-1}) = -S^2/4, so S = 2 sqrt(-Cov(dp_t, dp_{t-1})). (PROVEN under the model assumptions.)
- Failure modes (OBSERVED widely; PROVEN where stated): sample covariance often positive -> estimator undefined (usual fix: set to 0 or drop, which biases average); assumes symmetric independent order flow, no serial dependence in order flow (order splitting/autocorrelated flow violates it, typical in crypto); assumes constant spread; sensitive to bid-ask bounce being small relative to noise at higher frequencies. Also picks up only the transitory component.
- Crypto-specific INFERENCE: on tick-constrained pairs (BTCUSDT with 0.1 tick vs price ~1e5, or 0.01 on Binance spot) the spread is pinned at 1 tick most of the time, so Roll returns roughly tick-driven values and has little information beyond the tick.

### A.3 Corwin-Schultz (2012) high-low estimator [M]
Corwin, S. A., Schultz, P. (2012), "A simple way to estimate bid-ask spreads from daily high and low prices", J. Finance 67(2), 719-759. https://doi.org/10.1111/j.1540-6261.2012.01729.x
Formulas (from the paper; [M]):
- beta = sum_{j=0}^{1} [ln(H_{t+j}/L_{t+j})]^2 ; gamma = [ln( max(H_t,H_{t+1}) / min(L_t,L_{t+1}) )]^2
- alpha = (sqrt(2 beta) - sqrt(beta)) / (3 - 2 sqrt 2) - sqrt( gamma / (3 - 2 sqrt 2) )
- S = 2 (e^alpha - 1) / (1 + e^alpha). Negative estimates set to 0 in the paper; two-day overlapping-window adjustment for overnight returns.
- Logic (PROVEN under model): high-low ratio reflects variance (scales with sqrt of time) plus spread (constant in time), so the two-day range separates them.
- Known failure modes: (i) assumes highs are buys at ask and lows sells at bid, and that high-low reflects Brownian range: violated by discrete tick grids, jumps, and stale/zero-volume bars; (ii) upward bias in high-vol, downward/zero in low-vol (negative alphas frequent); (iii) needs the "day" to contain enough trades; (iv) the daily version assumes overnight gap handled -> in 24/7 crypto and near-24h FX/gold there is no overnight; the gap adjustment is moot but the two-period structure still applies; use bars of any length but then the variance-scaling assumption tests intraday seasonality (U-shaped volatility, funding-time and macro-release spikes) (INFERENCE); (v) the estimator becomes uninformative when true spread is a small multiple of tick because H and L are on the tick grid (INFERENCE, see A.6).

### A.4 Abdi-Ranaldo (2017) close-high-low estimator [M]
Abdi, F., Ranaldo, A. (2017), "A simple estimation of bid-ask spreads from daily close, high, and low prices", Rev. Financial Studies 30(12), 4437-4480. https://academic.oup.com/rfs/article/30/12/4437/4047344 [V]; SSRN https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2725981 [V]
- DOCUMENTED_CLAIM [V]: the method generally has the highest cross-sectional and average time-series correlation with the TAQ effective spread benchmark when quote data are unavailable, and is most accurate for less liquid stocks.
- Formula [M]: with log close c_t and mid-range eta_t = (ln H_t + ln L_t)/2, S^2 = E[(c_t - eta_t)(c_t - eta_{t+1})], estimator S_hat = sqrt( max(4 (c_t - eta_t)(c_t - eta_{t+1}), 0) ), averaged over a window (monthly in the paper) before taking the root to reduce noise. Uses the close-to-mid-range distance, which is biased by half-spread when the close is at bid/ask.
- Failure modes (INFERENCE + paper caveats): close price may not be at bid/ask in 24/7 markets where "close" is an arbitrary UTC cut; requires an averaging window; ignores intraday gaps and volume; validated on US equities and (per paper) other classes, not on crypto (UNKNOWN whether the paper's extension covers crypto; not checked). Internet Appendix: https://www.ssrn.com/abstract=2809692 [V].

### A.5 Other OHLC proxies (mostly [M])
- Parkinson (1980) range variance: sigma^2 = (1/(4 ln2)) E[ln(H/L)^2] (PROVEN under driftless BM, continuous monitoring; discrete sampling biases downward).
- Garman-Klass (1980), Rogers-Satchell (1991), Yang-Zhang (2000) for volatility; needed to net variance out of CS/AR (INFERENCE).
- Amihud (2002) illiquidity |r|/dollar volume: a price-impact-per-volume proxy, not a spread. https://doi.org/10.1016/S1386-4181(01)00024-6 [M]
- Kyle-Obizhaeva (2016) invariance: "Market microstructure invariance", J. Finance 71(4). Predicts trading cost scaling with volatility and volume; https://doi.org/10.1111/jofi.12444 [M].
- Ardia, Guidotti, Kroencke (2024), "Efficient estimation of bid-ask spreads from open, high, low, and close prices", J. Financial Economics: extends CS/AR with OHLC; [M] title/authors from memory, UNKNOWN exact formula and URL not opened. Search: https://www.google.com/search?q=Ardia+Guidotti+Kroencke+efficient+estimation+bid-ask+spreads+OHLC
- Fong-Holden-Trzcinka (2017) "What are the best liquidity proxies for global research?", Review of Finance: horse-race of low-frequency proxies. https://doi.org/10.1093/rof/rfx003 [M]

### A.6 Failure modes specific to tick-size-bound and 24/7 markets
- OBSERVED/INFERENCE: On large-tick assets (spread ~1 tick most of the time), quoted spread is a discrete variable; OHLC estimators assume continuous prices and give estimates that are continuous functions of volatility rather than the tick. Robust practice: use L1 quote data when available and use OHLC estimators only for sanity checks (INFERENCE).
- Large-tick literature: Dayri-Rosenbaum (2015), "Large tick assets: implicit spread and optimal tick size", Market Microstructure and Liquidity. https://doi.org/10.1142/S2382626615500057 [M] Also Eisler-Bouchaud-Kockelkoren (2012), "The price impact of order book events: market orders, limit orders and cancellations", Quantitative Finance. https://doi.org/10.1080/14697688.2010.528444 [M]
- 24/7 crypto: no closing auction, no overnight gap, seasonality by regional session and weekend thinning; "daily H/L" depends on the arbitrary UTC day boundary. Weekend liquidity is thinner (OBSERVED in several crypto papers; not sourced here -> UNKNOWN magnitude).
- Perps vs spot: spread proxies from OHLC of mark price vs last price differ; use last-trade OHLC for execution proxies and mark for margin (DOCUMENTED_CLAIM per exchange docs, see J).
- Wash trading / fake volume on some venues distort volume-based measures (Cong et al. 2023, "Crypto wash trading", Management Science; https://doi.org/10.1287/mnsc.2021.02709 [M]). Not verified in this session.
- DATA REQUIRED (spread): L1/L2 snapshots with exchange timestamps and trade tape with aggressor flags for at least one liquid pair per class; 1-min OHLCV as the proxy input; tick size and lot size per instrument (from exchange instrument-info endpoints).

---

## B. Slippage

- Definition (PROVEN as definition): slippage for a fill = D * (P_exec - P_ref), P_ref one of decision price, arrival mid, previous close, VWAP. Sub-components: half-spread crossed + impact + timing/delay drift + fees are usually reported separately (see L).
- Fill-versus-book mismatch is the crypto-specific piece: Albers-Cucuringu-Howison-Shestopaloff, "The Good, the Bad, and Latency: Exploratory Trading on Bybit and Binance" (SSRN https://ssrn.com/abstract=4677989 [V]). DOCUMENTED_CLAIM [V]: they compare realized execution outcomes with outcomes expected from the LOB snapshot at submission for market and marketable limit orders and report discrepancies correlated with volatility, latency and LOB liquidity. Magnitudes: UNKNOWN (abstract only).
- Model form for a benchmark (INFERENCE): slippage_bps = a*half_spread + b*sigma*sqrt(latency) + c*sigma*sqrt(Q/V_interval) + noise; fit a, b, c per venue/instrument/time-of-day. Only c is the impact term; b is latency (see I).
- DATA REQUIRED: own-order logs (decision time, send time, ack time, fill times, prices, sizes, fees), concurrent L1/L2 snapshots, or at minimum tick-level tape. Without own fills, slippage is a model (UNKNOWN) not a measurement.

---

## C. Market impact

### C.1 Almgren-Chriss (2000) [M]
Almgren, R., Chriss, N. (2000), "Optimal execution of portfolio transactions", J. Risk 3(2), 5-39. https://www.smallake.kr/wp-content/uploads/2016/03/optliq.pdf (mirror, [M]); DOI 10.21314/JOR.2001.041 [M].
- Set-up (PROVEN as model): liquidate X shares over T, N intervals, tau = T/N, trade sizes n_k, holdings x_k. Price S_k = S_{k-1} + sigma sqrt(tau) xi_k - tau g(n_k/tau); execution price S~_k = S_{k-1} - h(n_k/tau). Linear forms: permanent g(v) = gamma v; temporary h(v) = epsilon sgn(n) + eta v.
- Expected cost E = (1/2) gamma X^2 + epsilon sum|n_k| + (eta~/tau) sum n_k^2, with eta~ = eta - (1/2) gamma tau; variance V = sigma^2 tau sum x_k^2. Minimise E + lambda V (mean-variance).
- Solution: x_j = X sinh(kappa (T - t_j)) / sinh(kappa T), kappa^2 ~ lambda sigma^2 / eta~ (continuous-time limit). lambda -> 0 gives TWAP-like straight line; large lambda front-loads. (PROVEN.)
- Calibration parameters: sigma (volatility per unit time), gamma, eta, epsilon, lambda. The paper's illustrative parameters are not reproduced here (UNKNOWN from memory; do not use).
- Limits (INFERENCE + literature): linear impact contradicted by concave empirical impact (C.2); no propagator decay, so no resilience; permanent linear impact is what no-arbitrage requires (C.4).

### C.2 Square-root law [V/M]
- Form: I(Q) = Y sigma sqrt(Q/V), Q metaorder size, V period volume, sigma period volatility, Y an O(1) constant. Impact = mean price displacement of the metaorder's final (or average) execution price vs arrival, in price units of sigma.
- Survey/evidence: Bouchaud-Bonart-Donier-Gould, "Trades, Quotes and Prices" (CUP 2018) [M]. Toth et al. (2011), "Anomalous price impact and the critical nature of liquidity in financial markets", Phys. Rev. X 1, 021006, https://arxiv.org/abs/1105.1694 [M]. Donier-Bonart (2015) "A million metaorder analysis of market impact on the Bitcoin", Market Microstructure and Liquidity 1(2): arXiv https://arxiv.org/abs/1412.4503 [V], WSPC https://www.worldscientific.com/doi/10.1142/S2382626615500082 [V].
- DOCUMENTED_CLAIM [V] (Donier-Bonart, search snippets of abstract): more than one million reconstructed metaorders on Bitcoin/USD (Mt.Gox era data); concave impact with exponent ~0.5 over four decades; square-root holds through the trajectory, and largely decays after (uninformed component). Data era is 2011-2013 (INFERENCE from Mt.Gox context: the venue is defunct; transfer to 2024-2026 venues is untested by that paper).
- Counter-evidence (OBSERVED, single-source, non-peer-reviewed): a GitHub study using public Binance aggTrades reports OLS delta between 0.098 and 0.129 and MLP local slope 0.026-0.042 in all four experiments, far from 0.5, using synthetic metaorders reconstructed with the Maitrier-Loeper-Bouchaud (2025) algorithm. https://github.com/SLMolenaar/crypto-market-impact [V]. INFERENCE: synthetic metaorder reconstruction from anonymous public trades tends to lump unrelated flow and can dilute apparent exponents; this repo is not peer reviewed; treat as UNKNOWN evidence about the true law.
- Metaorder reconstruction from public data: Maitrier, Loeper, Bouchaud (2025), "Generating realistic metaorders from public data", https://arxiv.org/pdf/2503.18199 [V] (title only verified).
- Theory: Donier-Bonart-Mastromatteo-Bouchaud (2015), "A fully consistent, minimal model for non-linear market impact", Quantitative Finance, https://arxiv.org/abs/1412.0141 [M] (latent-liquidity/locally linear order book -> square-root). Farmer-Gerig-Lillo-Waelbroeck (2013) "How efficiency shapes market impact", Quant. Finance, https://arxiv.org/abs/1102.5457 [M]. Recent unifying: "The Subtle Interplay between Square-root Impact, Order Imbalance & Volatility", https://arxiv.org/abs/2506.07711 [V]; "The two square root laws of market impact and the role of sophisticated market participants", https://arxiv.org/abs/2311.18283 [V]. Options: https://arxiv.org/abs/1602.03043 [V]. Emilio Said thesis-type review: https://arxiv.org/pdf/2205.07385 [V].
- Practical coefficient: Y is typically reported of order 0.5-1 for equities in prop/broker studies; exact value for crypto/FX/gold: UNKNOWN.
- Crypto flow-based impact (recent): Alexander-Heck-Kaeck-Riordan (2024), "Order Flow Impact and Price Formation in Centralized Crypto Exchanges", SSRN https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4867599 [V]; findings beyond title: UNKNOWN. Albers et al., "Fragmentation, Price Formation, and Cross-Impact in Bitcoin Markets": arXiv https://arxiv.org/abs/2108.09750 [V]; T&F https://www.tandfonline.com/doi/full/10.1080/1350486X.2022.2080083 [V]; abstract [V]: derives a maker strategy using only passive orders and live-tested with ~1.5M USD notional. "Market impact and efficiency in cryptoassets markets", Digital Finance (2023), https://link.springer.com/article/10.1007/s42521-023-00095-9 [V], findings UNKNOWN. Bitcoin ETF flow impact: Boon Chuan Lim, SSRN https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6567058 [V]; DOCUMENTED_CLAIM [V]: causal price impact ~0.20% per USD 100M net inflow over 563 trading days (2024-01 to 2026-04) — macro flow, not execution impact. Kyle-lambda-style estimates on crypto: Frontiers "Microstructure alpha" https://www.frontiersin.org/journals/blockchain/articles/10.3389/fbloc.2026.1811716/full [V] and "Explainable Patterns in Cryptocurrency Microstructure" https://arxiv.org/html/2602.00776v1 [V] (contents: lambda as reduced-form elasticity; numbers UNKNOWN).
- DATA REQUIRED: metaorder-tagged fills (own or broker), or reconstructed from tape; per-interval volume V and sigma (same horizon); arrival mid; participation rate Q/V; need enough range in Q/V spanning 3+ decades, and the same instrument set.

### C.3 Propagator / transient impact
- Bouchaud-Gefen-Potters-Wyart (2004), "Fluctuations and response in financial markets: the subtle nature of 'random' price changes", Quant. Finance 4(2), https://arxiv.org/abs/cond-mat/0307332 [M]. Model: p_t = sum_{s<t} G(t-s) eps_s V_s^{?}... [exact volume nonlinearity UNKNOWN from memory] with sign-persistent order flow (long memory) balanced by G(l) decaying as power law ~ l^{-beta}, beta ~ 0.25 (paper's empirical value? UNKNOWN, do not code) to keep prices diffusive. The general logic (PROVEN as a model property): if signs have autocorrelation C(l) ~ l^{-gamma}, diffusivity requires G(l) ~ l^{-(1-gamma)/2}, hence beta = (1-gamma)/2 [M].
- Bouchaud-Farmer-Lillo (2009), "How markets slowly digest changes in supply and demand", Handbook of Financial Markets, https://arxiv.org/abs/0809.0822 [M].
- Obizhaeva-Wang (2013), "Optimal trading strategy and supply/demand dynamics", J. Financial Markets 16(1), 1-32; SSRN 2005 version https://papers.ssrn.com/sol3/papers.cfm?abstract_id=666541 [M]. Block-shaped LOB of depth q per price unit; price impact per share 1/q; exponential resilience rate rho. Optimal execution (PROVEN in model): discrete block at t=0 and t=T with constant-rate trading in between (in the base model); cost of a single block of size X ~ X^2/(2q) + spread. Calibration: q (depth), rho (resilience), spread. Parameter values: UNKNOWN.
- Gatheral-Schied (2013) "Dynamical models of market impact and algorithms for order execution", Handbook on Systemic Risk, [M]. Alfonsi-Schied-Slynko (2012) order-book resilience and optimal execution, SIAM J. Financial Math [M].
- Bacry-Iuga-Lasnier-Lehalle (2015) "Market impacts and the life cycle of investors orders", Market Microstructure and Liquidity, https://arxiv.org/abs/1412.0217 [M].
- DATA REQUIRED: trade-by-trade signed flow and midquote, at least 10^5-10^6 trades per instrument to estimate G(l) nonparametrically; L2 to calibrate q and rho.

### C.4 Temporary vs permanent; no-dynamic-arbitrage
- Huberman-Stanzl (2004), "Price manipulation and quasi-arbitrage", Econometrica 72(4), 1247-1275, https://doi.org/10.1111/j.1468-0262.2004.00531.x [M]. Result (PROVEN): with permanent impact, absence of price manipulation requires linear permanent impact; nonlinear permanent impact admits round-trip profit.
- Gatheral (2010), "No-dynamic-arbitrage and market impact", Quantitative Finance 10(7), 749-759, arXiv https://arxiv.org/pdf/0903.2428 [V]. Setting: price impact = integral f(dx_s) G(t-s) ds. PROVEN under model: with power-law kernel G(t) ~ t^{-gamma} and impact function f(x) ~ x^delta, no-dynamic-arbitrage requires delta + gamma >= 1 (as I recall; [M], re-check). With delta = 0.5 this implies gamma >= 0.5 (a decay at least as fast as t^{-0.5}). Search snippet [V]: relationship derived from principle that trading costs be non-negative on average; nonlinear permanent impact is inconsistent with no-dynamic-arbitrage (Curato-Gatheral-Lillo, arXiv https://arxiv.org/abs/1305.0413 [V]; cross-impact https://arxiv.org/abs/1612.07742 [V]; "No-arbitrage implies power-law market impact and rough volatility" https://arxiv.org/abs/1805.07134 [V]).
- INFERENCE: a benchmark cost model that is (square-root temporary) + (linear permanent) is a defensible compromise; pure sqrt permanent is inconsistent with no-arbitrage.
- DATA REQUIRED: post-trade decay data: prices for ~1-10x the execution duration after the metaorder ends; enough to estimate what fraction of peak impact remains (OBSERVED in equities/BTC: large fraction decays, ~2/3 rule of thumb is [M]/UNKNOWN for crypto).

---

## D. Fill probability and queue models

- Cont-Stoikov-Talreja (2010), "A stochastic model for order book dynamics", Operations Research 58(3), 549-563. https://doi.org/10.1287/opre.1090.0780 [V]; PDF https://www.columbia.edu/~ww2040/orderbook.pdf [V]; SSRN https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1273160 [V]. DOCUMENTED_CLAIM [V]: continuous-time Markov model; via Laplace transforms compute probability of mid-price increase, fill at bid before ask moves, both fill before move. Model [M]: per-price-level independent Poisson limit arrivals lambda(i) (decaying with distance i from touch), Poisson cancellations proportional to queue length (theta * n), market orders rate mu. Parameter estimation from data [M].
- Huang-Lehalle-Rosenbaum (2015), "Simulating and analyzing order book data: the queue-reactive model", JASA 110(509), 107-122. arXiv https://arxiv.org/abs/1312.0563 [V]; https://ideas.repec.org/a/taf/jnlasa/v110y2015i509p107-122.html [V]. DOCUMENTED_CLAIM [V]: LOB as a Markov queueing system within periods of constant reference price; event intensities depend on current queue sizes, with switches between reference price periods. Extensions: order-size QR https://arxiv.org/html/2405.18594v1 [V]; deep learning QR https://arxiv.org/abs/2501.08822 [V]; RL execution with QR https://arxiv.org/html/2511.15262v1 [V]; simulation realism https://arxiv.org/html/2603.24137v1 [V]; exogenous price moves localization http://www.cmap.polytechnique.fr/~charles-albert.lehalle/projects/2024QR/ [V].
- Moallemi and coauthors: Moallemi-Yuan (2017) "A model for queue position valuation in a limit order book" (Columbia working paper), [M] URL not opened. Also Maglaras-Moallemi-Zheng (2021) "Queueing dynamics and state space collapse in fluid models of limit order books" [M]. Value of queue position: UNKNOWN numerical results.
- Fill-probability vs post-fill return trade-off in crypto: Albers et al. (2025), "The Market Maker's Dilemma" / "To Make, or to Take, That Is the Question: Impact of LOB Mechanics on Natural Trading Strategies", arXiv https://arxiv.org/abs/2502.18625 [V]; https://arxiv.org/html/2502.18625v1 [V]. DOCUMENTED_CLAIM [V]: Binance BTC perpetual live experiment; negative correlation between maker fill likelihood and post-fill returns; maker strategies must be contrarian to imbalance. Numbers: UNKNOWN.
- Simple non-parametric model for benchmark (INFERENCE): P(fill within T | queue ahead Q0, expected traded volume at level per T) ~ 1 - exp(-lambda_fill T) or first-passage of net (trades - cancels) hitting Q0. Use empirical hazard from own limit-order logs conditioned on Q0, imbalance, spread.
- Exchange order priority is price-time (DOCUMENTED_CLAIM in venue docs; details of self-trade prevention, pro-rata for some products UNKNOWN here). CME Globex uses FIFO for most, with other matching algorithms for some products (Eurodollar-type; [M]).
- DATA REQUIRED: L2/L3 with order IDs, or at minimum L2 depth updates with trades; to know queue position you need L3 or own-order-ack-based inference; cancellations are not visible in L2 aggregates (OBSERVED limitation; queue position inference is approximate: "conservative/probabilistic queue" models, INFERENCE).

---

## E. Partial fills

- INFERENCE (structural): For a passive order, partial fill arises when traded volume at the level < queue ahead + own size within the horizon. For marketable orders, partial fill when book depth to limit price < size; residual either rests (marketable limit / IOC vs GTC) or is cancelled.
- Time-in-force semantics are venue-specific; e.g., IOC/FOK/post-only flags are documented per venue API (DOCUMENTED_CLAIM in API docs; not enumerated here: UNKNOWN specifics). Binance spot order types: https://developers.binance.com/docs/binance-spot-api-docs/enums [M]; Bybit v5: https://bybit-exchange.github.io/docs/v5/intro [V] (funding-history page fetched).
- Empirical fill-vs-expected discrepancy: Albers et al. 4677989 above [V].
- Model: expected residual cost for a strategy "post then cross after timeout tau": E[c] = P(fill)*(-rebate or maker fee + adverse selection) + (1-P(fill))*(taker fee + half spread + drift over tau). Cartea-Jaimungal-Penalva "Algorithmic and High-Frequency Trading" (CUP 2015) [M]. INFERENCE: drift over tau is the "opportunity cost" leg in implementation shortfall (L).
- DATA REQUIRED: order lifecycle logs: submit/ack/partial/complete/cancel timestamps with sizes; venue min-notional and lot-size rules.

---

## F. Adverse selection and toxicity

- Kyle (1985), "Continuous auctions and insider trading", Econometrica 53(6), 1315-1335. https://doi.org/10.2307/1913210 [M]. Kyle's lambda: dp = lambda * (signed order flow) + noise; PROVEN in model: lambda = (1/2) sigma_v / sigma_u, where sigma_v = std of asset value, sigma_u = std of noise trading. Empirical proxy: OLS regression of price change on signed volume per interval. Hasbrouck (2009) alternative (square-root signed volume) [M].
- Glosten-Milgrom (1985) sequential trade [M]; Hasbrouck (1991) VAR impact [M].
- VPIN: Easley-Lopez de Prado-O'Hara (2012), "Flow toxicity and liquidity in a high-frequency world", Rev. Financial Studies 25(5), 1457-1493. https://academic.oup.com/rfs/article-abstract/25/5/1457/1569929 [V]; SSRN https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1695596 [V]. DOCUMENTED_CLAIM [V]: order-flow toxicity adversely selects market makers; VPIN estimated from volume imbalance and trade intensity in volume time without unobservable-parameter estimation. Formula [M]: VPIN = sum_{tau=1}^{n} |V_tau^S - V_tau^B| / (n V) over volume buckets of size V.
- Critique: Andersen-Bondarenko (2014), "VPIN and the flash crash", J. Financial Markets 17, 1-46. https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1881731 [V]. DOCUMENTED_CLAIM [V]: VPIN peaked after not before the flash crash; controlling for trading intensity removes incremental predictive power for volatility; predictive content is largely mechanical via trading intensity. Rejoinder: https://www.sciencedirect.com/science/article/abs/pii/S1386418113000293 [V]. Also sensitive to trade classification (bulk volume classification vs tick rule): Andersen-Bondarenko "Assessing measures of order flow toxicity via perfect trade classification" [M, not verified].
- Realized spread / price impact decomposition (A.1) gives per-trade adverse selection ex post. Crypto: Albers et al. above [V] show maker fill-return trade-off.
- INFERENCE: for a non-HFT executor the useful uses of toxicity indicators are (i) widening passive quotes or switching to taker under high imbalance, (ii) regime flags; VPIN specifically should be validated out-of-sample against realized spread before use.
- DATA REQUIRED: signed trade tape with volume buckets; post-trade midquote at horizons; for toxicity validation, realized volatility / spread widening events.

---

## G. Maker/taker decision literature

- Cartea-Jaimungal-Penalva, "Algorithmic and High-Frequency Trading", CUP 2015 [M]; Cartea-Jaimungal (2016) "Incorporating order-flow into optimal execution", Math. Financ. Econ. https://doi.org/10.1007/s11579-016-0162-z [M]; Cartea-Jaimungal-Ricci (2014) "Buy low sell high: a HF trading perspective", SIAM J. Financial Math. [M]. Common structure (PROVEN in models): HJB control with limit order fill intensity lambda(delta) = A exp(-k delta) where delta is depth from touch; optimal depth delta* = 1/k + adjustments for inventory and drift. Parameters A, k must be estimated from own quote-fill data.
- Avellaneda-Stoikov (2008), "High-frequency trading in a limit order book", Quantitative Finance 8(3), 217-224 [M]: reservation price r = s - q gamma sigma^2 (T-t); optimal spread gamma sigma^2 (T-t) + (2/gamma) ln(1 + gamma/k). (PROVEN in model.)
- Guéant-Lehalle-Fernandez-Tapia (2012) "Optimal portfolio liquidation with limit orders", SIAM J. Financial Math [M].
- Albers, Cucuringu, Howison, Shestopaloff — crypto empirical: arXiv 2502.18625 [V] ("To Make, or to Take"), 2108.09750 [V], SSRN 4677989 [V], Hyperliquid L4 data SSRN https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6465720 [V]. These are the closest live-trading-evidence sources for crypto maker/taker decisions found.
- Fee interplay (PROVEN arithmetic): taker cost per unit = half spread + taker fee + impact; maker cost = maker fee (may be negative rebate) + adverse selection (1 - P(fill)) * missed-move. Break-even fill probability p* where E[maker] = E[taker]; p* depends on delta-fee (taker - maker fee) relative to expected drift; with Binance spot 0.1%/0.1% [see fee section] the fee difference is 0 at base tier, so the maker/taker decision at base tier is purely fill risk vs spread (INFERENCE).
- DATA REQUIRED: own limit-order experiment data (fill rate by distance from touch, time-to-fill, post-fill return), fee tier.

---

## H. Scheduling: VWAP / TWAP / POV

- TWAP: n_k = X/N constant (PROVEN as AC solution with lambda=0 and linear impact). VWAP: n_k proportional to expected volume profile v_k / sum v; benchmark is interval volume-weighted price. POV: n_k = rho * (realized volume in interval), rho participation.
- Volume-profile forecasting: Bialkowski-Darolles-Le Fol (2008) "Improving VWAP strategies: a dynamic volume approach", J. Banking & Finance 32(9) [M]; Kaastra-Boyd? UNKNOWN. Brownlees-Cipollini-Gallo (2011), "Intra-daily volume modeling and prediction for algorithmic trading", J. Financial Econometrics 9(3) [M].
- Crypto/24-7 intraday volume profile: no closing-auction spike; seasonality driven by Asia/EU/US sessions and funding settlement times (INFERENCE; OBSERVED in general but not sourced -> UNKNOWN magnitudes).
- Gold/FX: OTC market with venue-dependent volumes; a "market volume" for VWAP/POV is not defined for spot FX/XAUUSD (only venue or broker-specific volume; CME futures volume is a proxy) (INFERENCE).
- Implementation shortfall optimum under AC/OW (C.1, C.3) is an alternative to VWAP; for sqrt-law impact, the cost of a schedule is roughly Y sigma sqrt(Q/V) regardless of schedule shape to first order, while schedule affects timing risk (INFERENCE).
- Schedule with square-root impact: Curato-Gatheral-Lillo optimal execution with nonlinear transient impact, Quantitative Finance (2017) https://arxiv.org/abs/1412.5916 [M]; Almgren (2003) "Optimal execution with nonlinear impact functions and trading-enhanced risk", Applied Math Finance [M].
- DATA REQUIRED: intraday volume by 1-5 minute bar, multiple days, by weekday/weekend; for FX/gold, use venue/ECN volume or futures volume as proxy.

---

## I. Latency-to-price-risk

- Latency cost model (PROVEN under Brownian mid): expected absolute drift over latency L is sigma * sqrt(L) * sqrt(2/pi) (E|N(0, sigma^2 L)|); std = sigma sqrt(L). For sigma_annual = 60% (illustrative, not sourced) and L = 200 ms, sigma sqrt(L) is ~0.6*sqrt(0.2/31.5e6) ~ 0.15 bp (INFERENCE, arithmetic only). So for non-HFT with 50-500 ms latency the latency price-risk is a small fraction of half-spread on liquid pairs; it grows with sqrt(L) and with vol spikes (INFERENCE).
- Adverse selection during latency is not symmetric: the fills that hit are those where price moved away (winner's curse). Albers et al. (SSRN 4677989) [V] measured this on Bybit/Binance; magnitudes UNKNOWN.
- Latency and toxicity for makers: Budish-Cramton-Shim (2015), "The high-frequency trading arms race", QJE 130(4) [M] https://doi.org/10.1093/qje/qjv027; discrete-time frequency-batch argument; relevant to HFT, marginal for non-HFT.
- Delay cost inside implementation shortfall (L): decision-to-arrival time (human/system latency, minutes) dominates network latency for non-HFT (INFERENCE).
- DATA REQUIRED: timestamps at each hop (decision, send, ack, fill), exchange-side matching timestamps, realized 1-second returns around the time.

---

## J. Funding, borrow, swaps, roll

### J.1 Perpetual funding: Binance USD-M
Source: https://www.binance.com/en/support/faq/introduction-to-binance-futures-funding-rates-360033525031 [V, fetched]
- DOCUMENTED_CLAIM [V]: F = [Average Premium Index P + clamp(Interest rate - P, +0.05%, -0.05%)] / (8/N), where N is the number of funding intervals per 8 hours (interval hours dependent).
- Default settlement every 8 hours at 00:00, 08:00, 16:00 UTC; adjusts to 1-hour intervals under extreme volatility when the prior settlement hit cap/floor (DOCUMENTED_CLAIM [V]).
- Interest rate: 0.03% per day by default (0.01% per 8h interval); 0% for certain pairs such as ETHBTC (DOCUMENTED_CLAIM [V]).
- Clamp: +/-0.05% on (interest - premium) so that if it falls in the band, funding equals the interest rate itself (DOCUMENTED_CLAIM [V]).
- Cap/floor: for major contracts (BTCUSDT, ETHUSDT) cap = 0.75 * MMR and floor = -0.75 * MMR; other USD-M contracts +/-2% (DOCUMENTED_CLAIM [V]; per-symbol overrides exist, UNKNOWN).
- Funding payment = position notional (mark price * size) * funding rate; longs pay shorts when positive (standard; DOCUMENTED_CLAIM, from FAQ context; exact sentence not captured).
- Premium index construction and data endpoints: UNKNOWN in this session (see API docs: https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Get-Funding-Rate-History [M]).

### J.2 OKX
Search-returned summaries of official OKX help articles [V, snippet only; official page fetch returned 404 on my URL guess]:
- DOCUMENTED_CLAIM [V]: Funding rate = clamp[ Average premium index + clamp(Interest rate - Average premium index, 0.05%, -0.05%), cap, floor ], interest rate = 0.03% / (24 / settlement interval hours). Newer version divides the bracket by (8/N) (revision notice). Premium index = [Max(0, Impact bid - Index) - Max(0, Index - Impact ask)] / Index, with impact prices from order book depth.
- URLs [V]: https://www.okx.com/en-us/help/iv-introduction-to-perpetual-swap-funding-fee ; https://www.okx.com/en-us/help/important-update-revision-of-the-funding-rate-formula-for-okx-perpetual ; https://okx.com/support/hc/en-us/articles/360053909272-X-Introduction-to-perpetual-swap-funding-fee
- Interval: 8h default, some contracts differ (UNKNOWN which; instrument-specific). Cap/floor values: UNKNOWN.

### J.3 Bybit
- DOCUMENTED_CLAIM [V] (search summary of help center): F = P + clamp(I - P, 0.05%, -0.05%), interest I = 0.03% per day (0.01% per 8h interval); premium index P uses fair-buy/impact ask vs index; funding rate is computed each minute and a TWAP over the interval; funding fee = position value * funding rate. https://www.bybit.com/en/help-center/article/Funding-fee-calculation [V]; https://www.bybit.com/en/help-center/article/Introduction-to-Funding-Rate [V].
- API [V, fetched]: funding history endpoint GET /v5/market/funding/history, each symbol has its own funding interval (see instruments-info); returns fundingRate and fundingRateTimestamp; 200 records max per query. https://bybit-exchange.github.io/docs/v5/market/history-fund-rate
- Intervals other than 8h and dynamic caps: UNKNOWN specifics.

### J.4 Effect on backtests (INFERENCE)
Funding is an accrual per position notional, paid at settlement only if the position is open at the timestamp (Binance/OKX/Bybit documentation says paid/received by those holding at settlement: DOCUMENTED_CLAIM, not quoted here → treat as [M]). So intraday holding periods that avoid settlement instants pay zero funding; those crossing pay full interval regardless of holding fraction. Model funding as discrete events on the exchange's timestamps, not a continuous rate.
- DATA REQUIRED: historical funding rates with timestamps (Binance/OKX/Bybit REST), mark and index price series, symbol-specific interval changes over time.

### J.5 Crypto short borrow / margin interest
- Spot margin borrow: interest rates are set by venue (hourly/daily accrual, VIP-tier-dependent) — Binance Margin, OKX, Bybit; exact rate tables: UNKNOWN (dynamic). Kraken margin has an opening fee plus rollover fee every 4 hours per docs [M, unverified]. Coinbase Advanced does not offer spot shorting for retail (INFERENCE / [M]; UNKNOWN).
- Shorting via perps avoids borrow but pays/receives funding (J.1-J.3).
- DATA REQUIRED: borrow rate history per asset (venue endpoints), borrow availability caps.

### J.6 FX swap / rollover
- Conventions [M]: spot FX settles T+2 (T+1 for USD/CAD etc.); overnight positions are rolled via tom-next swap; swap points ~ spot * (r_quote - r_base) * (days/360 or 365) with market-specific day counts; Wednesday rollover triples (three days) for T+2 currencies.
- OANDA docs: https://www.oanda.com/au-en/trading/financing-costs/ [V], https://www.oanda.com/us-en/trading/financing-fees/ [V], https://www.oanda.com/uk-en/trading/financing-costs [V]. DOCUMENTED_CLAIM [V] (from search summary): positions held past 5 p.m. ET are financed; two quoted rates per instrument (long and short), annualised, may change daily; formula for metals: size or position value x funding rate x duration x conversion rate; gold CFDs settle T+2 so weekend financing applied earlier (triple Wednesday) [V snippet].
- Numeric rates: UNKNOWN (instrument-specific, changing).

### J.7 Gold (XAU)
- XAUUSD spot/CFD financing: broker applies tom-next-based swap plus markup (DOCUMENTED_CLAIM from OANDA snippet [V]: "commonly based on tom-next plus/minus a broker adjustment", from a secondary summary — treat as INFERENCE). Gold lease rate/GOFO historically defined swap economics (LBMA GOFO discontinued 2015; [M], UNKNOWN URL).
- COMEX gold futures: cost of carry in the calendar spread; contract specs at https://www.cmegroup.com/markets/metals/precious/gold.contractSpecs.html [M, not fetched].

### J.8 Futures roll
- Roll yield / calendar spread (PROVEN identity): F(T2) - F(T1) = carry (financing + storage - convenience yield); roll cost per unit = F_far - F_near when rolling a long from near to far; in contango a long pays. For intraday strategies, roll matters only when holding through expiry or when using continuous contract series; artificial roll gaps in back-adjusted series contaminate backtests (INFERENCE).
- Commodity roll references: Gorton-Rouwenhorst (2006) "Facts and fantasies about commodity futures", Financial Analysts Journal 62(2), 47-68 [M]; Erb-Harvey (2006) "The strategic and tactical value of commodity futures", FAJ [M].
- Perp vs quarterly futures basis in crypto: annualised basis = (F/S - 1) * 365/days (identity).
- DATA REQUIRED: contract calendars, per-contract settlement prices, volume/open interest by expiry, calendar-spread quotes.

---

## K. Venue fragmentation / cross-venue liquidity

- Albers et al. (2021/2022), "Fragmentation, price formation and cross-impact in Bitcoin markets", arXiv 2108.09750 [V], T&F link above [V]: cross-impact between venues; abstract [V] in section C.
- Alexander et al. (2024) SSRN 4867599 [V]: price leadership across centralized exchanges; details UNKNOWN.
- Boon Chuan Lim, SSRN 6567058 [V]: theoretical multi-venue Kyle model for ETF flows, aggregate impact linear then convex when flow exceeds venue capacity (DOCUMENTED_CLAIM [V]); ETF flow only.
- Makarov-Schoar (2020), "Trading and arbitrage in cryptocurrency markets", J. Financial Economics 135(2), 293-319 [M]. https://doi.org/10.1016/j.jfineco.2019.07.001. Documents persistent cross-country price gaps (OBSERVED, [M]).
- Cross-impact theory: Benzaquen-Mastromatteo-Eisler-Bouchaud (2017) "Dissecting cross-impact on stock markets", J. Stat. Mech. https://arxiv.org/abs/1609.02395 [M].
- INFERENCE: for a single-account non-HFT trader, fragmentation matters via (a) which venue's book you should use to estimate impact (the deepest, where you actually trade), (b) index-price and mark-price composition for perps (derived from multiple spot venues; DOCUMENTED_CLAIM in exchange docs, composition per venue UNKNOWN), (c) smart order routing across venues only if you hold accounts and inventory on several.
- DATA REQUIRED: synchronized (same-clock, NTP/PTP-disciplined) book snapshots across venues; inventory constraints per venue.

---

## L. Implementation shortfall and TCA decomposition

- Perold (1988), "The implementation shortfall: paper versus reality", J. Portfolio Management 14(3), 4-9. https://doi.org/10.3905/jpm.1988.409150 [M]. Definition (PROVEN as accounting identity): IS = (paper portfolio return at decision-price with no costs) - (actual portfolio return). For a buy of X shares with fills: IS = sum_i q_i (P_i - P_decision) + (X - sum q_i)(P_end - P_decision) + explicit costs (fees, commissions).
- Standard decomposition of shortfall (definitions; [M] Kissell-Glantz and Almgren-Chriss lineages):
  1. Delay/timing cost = X * (P_arrival - P_decision) — decision to order submission.
  2. Spread cost = sum_i q_i * D * (mid_i - P_i)^{-} ... equivalently half effective spread paid at fills.
  3. Market impact = sum_i q_i * D * (mid_i^{pre} - P_arrival) less timing drift (requires a counterfactual: impact vs market drift are not separately identified from one order; only in aggregate over many orders with a model).
  4. Opportunity cost = (X - filled) * D * (P_end - P_decision).
  5. Explicit costs = fees (maker/taker), rebates, funding, borrow.
  Signs conventions: D = +1 buy.
- Kissell (2013) "The Science of Algorithmic Trading and Portfolio Management" (Academic Press) [M]: I-Star model: MI = a1 (Q/ADV)^{a2} sigma^{a3} + b1 POV^{a4}... UNKNOWN exact form from memory; do not use.
- Almgren-Thum-Hauptmann-Li (2005), "Direct estimation of equity market impact", Risk, July [M]: OBSERVED on Citigroup equity orders: temporary impact ~ 0.6 power, permanent linear-ish... (exponent 0.6 I recall; UNKNOWN whether exactly; treat as UNKNOWN).
- Identifiability (INFERENCE): impact vs drift confounding requires a control (arrival-price benchmark averaged over many trades, randomized order timing/A-B experiments like Albers et al. live trading [V]).
- DATA REQUIRED: decision timestamp+price (signal timestamp), arrival mid at order release, all fills with fees, end-of-horizon price, unfilled qty, funding/borrow accruals, concurrent market data.

---

## M. Official fee schedules (as documented; verify before use)

### M.1 Binance
Source fetched [V]: https://www.binance.com/en/fee/schedule
- Spot, regular user (<1,000,000 USD 30d volume and/or 0 BNB): 0.100% maker / 0.100% taker; BNB payment gives 25% discount (DOCUMENTED_CLAIM [V]).
- USD-M futures, regular: fetch returned 0.07500% / 0.07500%. UNVERIFIED: this looks inconsistent with widely published values (maker lower than taker) and may be a parsing error of the summarizer; UNKNOWN until the page is re-read with the fee table; do not use 0.075/0.075.
- Trade volume for tiering includes Spot, Margin, Convert, Copy Trading and Trading Bots volumes (DOCUMENTED_CLAIM [V]).

### M.2 OKX
Official page https://www.okx.com/fees fetched but the table was not returned. Secondary summaries of the regular (Lv1) tier: spot 0.08% maker / 0.10% taker, USDT perpetual 0.02% maker / 0.05% taker (DOCUMENTED_CLAIM, secondary [V]: search summary citing bitdegree/tradersunion; https://www.bitdegree.org/crypto/tutorials/okx-fees ; https://www.okx.com/en-us/help/fee-details [V] not fetched). Tier by 30d volume and daily balances (DOCUMENTED_CLAIM [V]). Verify before use; OKX US and EEA schedules differ (UNKNOWN).

### M.3 Bybit
Secondary [V]: VIP 0 spot 0.10%/0.10%; linear perpetuals and futures 0.020% maker / 0.055% taker; no liquidation fee on perps/futures (DOCUMENTED_CLAIM, secondary; sources https://www.bybit.com/en/announcement-info/fee-rate/ [V URL only], https://www.bitdegree.org/crypto/tutorials/bybit-fees [V URL only]). Official page not fetched.

### M.4 Coinbase Advanced
Official page https://www.coinbase.com/advanced-fees returned 403. Secondary aggregator [V] lists (30d volume): 0.60%/1.20% (Intro 1 base), 0.35%/0.75% (>=1K), 0.25%/0.40% (>=10K), 0.15%/0.25% (>=50K), 0.10%/0.20% (>=500K), 0.07%/0.16% (>=1M), 0.05%/0.14% (>=15M), 0.02%/0.10% (>=50M), 0.00%/0.08% (>=100M), 0.00%/0.05% (>=250M) as maker/taker; tiers refreshed hourly on trailing volume (DOCUMENTED_CLAIM, secondary; https://www.datawallet.com/crypto/coinbase-fees , https://tokenecho.io/guides/coinbase-advanced-trade-fees/). The same summary also stated an "0.40%/0.60%" entry-level; the two statements conflict (INTERNAL INCONSISTENCY) so Coinbase numbers are UNKNOWN until the official table is read.

### M.5 Kraken
Fetched official [V]: https://www.kraken.com/features/fee-schedule
- Spot (maker/taker by 30d volume or assets on platform, whichever gives the higher tier): T1 (0+) 0.40%/0.80%; T2 ($2.5K+) 0.30%/0.60%; T3 ($10K+) 0.22%/0.38%; T4 ($25K+) 0.20%/0.35%; T5 ($50K+) 0.15%/0.30%; T6 ($100K+) 0.12%/0.25%; T7 ($250K+) 0.10%/0.22%; T8 ($500K+) 0.08%/0.20%; T9 ($1M+) 0.06%/0.18%; T10 ($2.5M+) 0.04%/0.15%; T11 ($5M+) 0.02%/0.12%; T12 ($10M+) 0.00%/0.10%; Pro tiers 0.00%/0.05%-0.09% (DOCUMENTED_CLAIM [V]).
- Futures: maker 0% down to -0.006%, taker 0.0125% to 0.05% depending on tier (DOCUMENTED_CLAIM [V], summarized).

### M.6 FX and gold brokers
- OANDA financing (see J.6) and spread/commission model: variable spread embedded in price; specifics UNKNOWN. OANDA XAU/USD page https://www.oanda.com/bvi-en/cfds/instruments/xau-usd/ [V URL only]. Interactive Brokers, IG, etc.: UNKNOWN (not fetched).
- Cost model for an FX/gold trade at a retail broker (INFERENCE): cost = quoted spread (broker's, which can widen at rollover 17:00 ET and news) + swap (if held past rollover, long/short different, sometimes both negative) + commission (ECN accounts). Data: broker tick history with bid/ask, swap tables.
- DATA REQUIRED: broker tick bid/ask history (own account's server), swap table history, commission schedule, rollover time.

---

## N. Recent (2024-2026) items found, summarised
- Alexander-Heck-Kaeck-Riordan 2024, SSRN 4867599 [V]: crypto order flow impact and price formation, CEX (details UNKNOWN).
- Albers et al. 2025 (arXiv 2502.18625) [V]: maker fill probability vs post-fill return, Binance BTC perp live experiment.
- Albers et al. SSRN 4677989 [V]: Bybit/Binance execution vs book snapshot; SSRN 6465720 [V]: Hyperliquid L4 data.
- Maitrier-Loeper-Bouchaud 2025 arXiv 2503.18199 [V]: metaorder reconstruction from public data.
- Square-root theory unifications: arXiv 2506.07711 [V], 2311.18283 [V].
- Queue-reactive ML/RL: arXiv 2405.18594, 2501.08822, 2511.15262, 2603.24137 [V].
- Non-parametric self/cross-impact estimation: https://arxiv.org/html/2510.06879 [V] (contents UNKNOWN).
- Cross-impact/ETF flow: SSRN 6567058 [V].
- Crypto sqrt-law counter-evidence: GitHub crypto-market-impact [V], non-peer-reviewed.
- Nonlinear-impact price manipulation: arXiv 2609.02447 [V] (title only).
- Not found/verified: a peer-reviewed paper establishing a square-root exponent for Binance/OKX perps with own-order (true metaorder) data. UNKNOWN.

---

## O. Summary table: what to calibrate and from which data

| Component | Parameters | Minimum data |
|---|---|---|
| Spread | half-spread by instrument/time-of-day, tick bound | L1 quotes + trades; OHLC only as fallback |
| Slippage | latency term, book-walk term | own fills + book snapshots |
| Impact | Y (sqrt law), gamma (permanent), G(l) decay, q/rho | metaorder-tagged fills; tape |
| Fill prob | lambda_fill(delta, imbalance, queue) | own limit-order lifecycle logs; L2/L3 |
| Partial fills | fill fraction distribution | order logs |
| Adverse selection | realized-spread curve, lambda_Kyle | tape with sign, post-trade mids |
| Maker/taker | A, k in lambda(delta)=A e^{-k delta}, p* | own quote-fill experiments |
| Schedule | volume profile, POV cap | 1-5 min volume history |
| Latency | sigma, L distribution | timestamps at each hop |
| Funding/carry | rate series, intervals, borrow | venue funding/borrow history; swap tables |
| Fragmentation | cross-impact, venue depth | synchronized multi-venue books |
| IS/TCA | decision, arrival, end prices | signal timestamps + fills |

## P. Key gaps and cautions
1. Exact fee tables for OKX, Bybit, Coinbase not read from official pages; Binance futures value contradictory.
2. Almgren-Chriss / propagator constants, Kissell I-Star, Almgren et al. 2005 exponents: not verified, marked UNKNOWN.
3. No verified crypto-specific Y for square-root law on current venues; the 2014 Bitcoin result is Mt.Gox era; one non-peer-reviewed counterexample.
4. FX/gold broker swaps and spreads only sketched (OANDA); CME spec pages not fetched.
5. All [M] items need verification from the paper before being encoded as a benchmark.

