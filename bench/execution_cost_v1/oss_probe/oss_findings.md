# OSS probe: execution / transaction-cost modelling

Probe date 2026-09-29. Clones in /tmp/oss_clones (shallow, depth 1); venvs in /tmp/venvs; smoke scripts in /tmp/smoke. GitHub API was unreachable (no release/contributor counts); latest tag is from `git ls-remote --tags` sorted with `sort -V` and is APPROXIMATE (unreliable for freqtrade/ccxt/vnpy). Contributor counts UNKNOWN (shallow clones). Stars deliberately not used.

Labels: PROVEN (I executed it), OBSERVED (I read source/files), DOCUMENTED_CLAIM (authors' text), INFERENCE, UNKNOWN.

Counts: discovered 21, cloned+source-inspected 21, smoke-executed 9 (tick is partial).

| Candidate | License | Last commit | Executed | Adjudication |
|---|---|---|---|---|
| zipline-reloaded slippage models | Apache-2.0 | 2025-11-13 | True | ADOPT_REFERENCE |
| zipline (Quantopian, original) | Apache-2.0 | 2020-10-14 | False | REJECT |
| hftbacktest | MIT | 2025-12-23 | True | PARK |
| nautilus_trader FillModel | LGPL-3.0-or-later | 2026-09-29 | True | PARK |
| QuantConnect LEAN slippage/fill/fee models | Apache-2.0 | 2026-09-28 | False | ADOPT_REFERENCE |
| vectorbt (open-source) | Apache-2.0 with Commons Clause (non-SPDX; Commons Clause forbids selling) | 2026-09-26 | True | PARK |
| backtesting.py | AGPL-3.0 | 2026-08-05 | True | REJECT |
| backtrader broker slippage | GPL-3.0 | 2023-04-19 | False | REJECT |
| bidask (EDGE spread estimator) | MIT | 2025-10-13 | True | ADOPT_REFERENCE |
| Almgren-Chriss notebook (joshuapjacob) | MIT | 2022-02-02 | True | ADAPT_CANDIDATE |
| mbt_gym | BSD-3-Clause | 2024-01-08 | False | PARK |
| tick (Hawkes / point processes) | BSD-3-Clause | 2026-05-04 | True | REJECT |
| ABIDES original (execution agents) | BSD-3-Clause | 2020-11-19 | False | PARK |
| ABIDES-JPMC-public (abides-markets/gym) | BSD-3-Clause | 2023-12-13 | False | PARK |
| Corwin-Schultz / Abdi-Ranaldo / Roll in pyfolio-reloaded & quantstats | Apache-2.0 (both) | 2025-06-02 (pyfolio) / 2026-09-27 (quantstats) | False | REJECT |
| freqtrade funding-fee handling | GPL-3.0 | 2026-09-29 | False | ADOPT_REFERENCE |
| ccxt fee & funding-rate history | MIT | 2026-09-29 | True | ADOPT_REFERENCE |
| hummingbot executors (TWAP etc.) | Apache-2.0 | 2026-09-22 | False | PARK |
| PyLOB | MIT | 2026-08-14 | False | PARK |
| bmoscon orderbook (order-book on PyPI) | GPL-3.0 | 2026-09-02 | False | REJECT |
| vnpy | MIT | 2026-08-06 | False | PARK |

## zipline-reloaded slippage models
- Repo: stefan-jansen/zipline-reloaded
- License: Apache-2.0
- Last commit: 2025-11-13 | latest tag (approx): v1.3.0 (tag sort approx)
- Activity: Moderate: community fork, last commit ~10 months before probe date (2026-09-29)
- Dependencies: pandas, numpy, bcolz-zipline-era stack, exchange-calendars; heavy install
- Asset-class assumptions: US equities + futures (AllowedAssetMarker EquitySlippageModel/FutureSlippageModel); minute bars
- Required data: Minute OHLCV incl. volume; 20-day ADV and volatility window for VolatilityVolumeShare
- Online/offline: Offline backtest simulator; classes usable standalone only via mock BarData/Order
- Fit for non-HFT intraday execution: Good reference for bar-level slippage: VolumeShareSlippage (quadratic in volume share), FixedBasisPointsSlippage (default 5bp, 10% vol cap), VolatilityVolumeShare (eta*sigma*sqrt(psi), futures)
- Failure modes: Bar-close price as reference (no spread/queue); quadratic-in-share law is ad hoc (price_impact=0.1 default, not calibrated); volume_limit caps fills (LiquidityExceeded); ROOT_SYMBOL_TO_ETA calibrated for US futures; needs full zipline calendar/asset infra to use in-situ
- Source paths:
  - `/tmp/oss_clones/zipline-reloaded/src/zipline/finance/slippage.py:241 VolumeShareSlippage.process_order (l.288-331)`
  - `/tmp/oss_clones/zipline-reloaded/src/zipline/finance/slippage.py:603 FixedBasisPointsSlippage.process_order (l.663-681)`
  - `/tmp/oss_clones/zipline-reloaded/src/zipline/finance/slippage.py:368 MarketImpactBase.process_order (l.421)`
  - `/tmp/oss_clones/zipline-reloaded/src/zipline/finance/slippage.py:520 VolatilityVolumeShare.get_simulated_impact (l.~56 of class; MI=eta*sigma*sqrt(psi))`
- Smoke executed: **True**. Imported classes, called process_order with mock data (vol 10000, close 50, order 200): VolumeShareSlippage -> (50.002, 200) matching 50*(1+0.1*0.02^2)=50.002; FixedBasisPoints(5bp) -> (50.025, 200). Executed in /tmp/venvs/zipline-reloaded.
- Claim labels: formula_matches_docstring=PROVEN (smoke output); default_eta_calibration=DOCUMENTED_CLAIM; fit_non_hft=INFERENCE
- **Adjudication: ADOPT_REFERENCE** - Cleanest small, Apache-2.0 formulas for bar-level slippage baselines; use as reference/oracle not as dependency.

## zipline (Quantopian, original)
- Repo: quantopian/zipline
- License: Apache-2.0
- Last commit: 2020-10-14 | latest tag (approx): v1.3.0
- Activity: Dead/archived-equivalent: no commits since 2020-10
- Dependencies: legacy pandas/numpy pins
- Asset-class assumptions: US equities/futures
- Required data: Minute OHLCV
- Online/offline: Offline
- Fit for non-HFT intraday execution: Superseded by zipline-reloaded; same slippage classes
- Failure modes: Does not install on modern Python/pandas (INFERENCE, not attempted)
- Source paths:
  - `/tmp/oss_clones/zipline/zipline/finance/slippage.py`
- Smoke executed: **False**. Not installed; cloned and file present (superseded by zipline-reloaded which was executed).
- Claim labels: dead=OBSERVED (git log)
- **Adjudication: REJECT** - Unmaintained since 2020; use zipline-reloaded as reference instead.

## hftbacktest
- Repo: nkaz001/hftbacktest
- License: MIT
- Last commit: 2025-12-23 | latest tag (approx): v1.8.4 (repo tag) / PyPI 2.4.4
- Activity: Active through 2025 (last commit ~9 months before probe date); single main maintainer (INFERENCE from repo/email in LICENSE)
- Dependencies: Rust core + numba, numpy, pandas, polars (PyPI 2.4.4 wheel)
- Asset-class assumptions: Crypto perp/spot L2/L3 tick data (linear & inverse assets, tick_size/lot_size); no equity calendar concept
- Required data: Tick-by-tick depth + trade events (event_dtype: ev, exch_ts, local_ts, px, qty ...), optional order-latency data
- Online/offline: Offline event-driven backtest; live via connector crate (separate)
- Fit for non-HFT intraday execution: Low direct fit: models queue position, latency, maker/taker fees at tick level; irrelevant to minute-bar non-HFT execution unless you have L2 data. Useful as a fee/latency/queue reference.
- Failure modes: Needs full L2 event feed (expensive to collect/store); numba-jit'd user loop; queue models (risk-adverse, prob power/log) are heuristics; results sensitive to latency assumption; partial-fill exchange models differ
- Source paths:
  - `/tmp/oss_clones/hftbacktest/hftbacktest/src/backtest/models/queue.rs: RiskAdverseQueueModel l.44, ProbQueueModel l.139, PowerProbQueueFunc l.221, L3FIFOQueueModel l.481`
  - `/tmp/oss_clones/hftbacktest/hftbacktest/src/backtest/models/fee.rs: TradingValueFeeModel/TradingQtyFeeModel l.55-93`
  - `/tmp/oss_clones/hftbacktest/hftbacktest/src/backtest/models/latency.rs: ConstantLatency l.28, IntpOrderLatency l.98`
- Smoke executed: **True**. Built 7-event synthetic npz (snapshot + 5 sell trades at bid), ROIVector/HashMapMarketDepthBacktest with risk_adverse_queue_model, constant latency, trading_value_fee_model(maker 2bp,taker 7bp), buy limit 99.9 x1. Output (position, balance, fee) = (1.0, -99.9, 0.01998): filled as maker, fee=2bp*99.9. Deprecation warning: constant_latency -> constant_order_latency.
- Claim labels: fill_and_fee_behaviour=PROVEN (smoke); queue_model_realism=UNKNOWN (not validated against real data); fit_non_hft=INFERENCE
- **Adjudication: PARK** - Correct and mature, but tick/LOB-centric; park as reference for maker fee/queue modelling if L2 data ever exists.

## nautilus_trader FillModel
- Repo: nautechsystems/nautilus_trader
- License: LGPL-3.0-or-later
- Last commit: 2026-09-29 | latest tag (approx): v2.0.0rc5 (repo); PyPI installed 1.221.0
- Activity: Very active (daily commits), commercial-backed team
- Dependencies: Rust core, Python/Cython; large
- Asset-class assumptions: Multi-asset (FX, equities, crypto, futures); L1/L2/L3 book-based matching
- Required data: Quotes/trades/bars/order book deltas
- Online/offline: Offline backtest engine + live engine
- Fit for non-HFT intraday execution: Fill model is coarse: prob_fill_on_limit, prob_slippage (1 tick) plus book-based matching in v2; no volume-impact law. Good architecture reference for order state machine, not for cost calibration.
- Failure modes: Slippage is a random 1-tick event not volume-dependent; bar-only data gives crude fills; LGPL constraint if linked; huge dependency; repo is v2.0 rc while PyPI wheel is 1.221 (API skew)
- Source paths:
  - `/tmp/oss_clones/nautilus_trader/crates/execution/src/models/fill.rs: ProbabilisticFillState l.166 (is_limit_filled l.198, is_slipped l.202), DefaultFillModel l.265`
  - `/tmp/oss_clones/nautilus_trader/crates/execution/src/python/fill.rs`
- Smoke executed: **True**. pip 1.221.0: FillModel(prob_fill_on_limit=0.3, prob_slippage=0.5, random_seed=42) -> is_limit_filled x10 = [F,T,T,T,F,F,F,T,F,T], is_slipped x10 = [T,F,T,T,F,F,T,F,F,T]. Confirms Bernoulli behaviour only. Source inspected is v2 Rust, executed is v1 PyPI (different code).
- Claim labels: bernoulli_fill_slip=PROVEN (smoke, on 1.221) + OBSERVED (v2 source); cost_realism=INFERENCE
- **Adjudication: PARK** - Structure reference only; cost model is probability toggles. LGPL + weight not justified.

## QuantConnect LEAN slippage/fill/fee models
- Repo: QuantConnect/Lean
- License: Apache-2.0
- Last commit: 2026-09-28 | latest tag (approx): v2.4.0.1 (approx)
- Activity: Very active, commercial
- Dependencies: C# .NET (Python via pythonnet); huge repo (503MB shallow)
- Asset-class assumptions: Equity, futures, options, FX, crypto; venue-specific fee models (IB, Binance, Kraken, Coinbase, Bybit, dYdX...)
- Required data: Trade/quote bars incl. volume; fundamentals SharesOutstanding for liquidity adj.
- Online/offline: Offline backtest engine; live engine
- Fit for non-HFT intraday execution: Best breadth of fee schedules + two slippage models. MarketImpactSlippageModel implements Almgren-style permanent (G) + temporary (H) impact; VolumeShare is quadratic. Formulas portable to Python.
- Failure modes: Not executed (needs .NET SDK). MarketImpact model rejects Forex/CFD (needs volume); uses random Gaussian noise (seeded); default constants (alpha .891, beta .6, gamma .314, eta .142, delta .267) provenance = DOCUMENTED_CLAIM; ConstantSlippage ignores size; VolumeShare requires bar volume
- Source paths:
  - `/tmp/oss_clones/Lean/Common/Orders/Slippage/MarketImpactSlippageModel.cs: GetSlippageApproximation l.~85-130, G() l.142, H() l.152`
  - `/tmp/oss_clones/Lean/Common/Orders/Slippage/VolumeShareSlippageModel.cs l.46-75 (slippage = volumeLimit^2 * priceImpact)`
  - `/tmp/oss_clones/Lean/Common/Orders/Fees/*FeeModel.cs (35 files)`
  - `/tmp/oss_clones/Lean/Common/Orders/Fills/FillModel.cs (Market/Limit/Stop fills)`
- Smoke executed: **False**. Not executed: .NET SDK build out of scope for probe; formulas read from source only.
- Claim labels: formula_text=OBSERVED (source); constants_provenance=DOCUMENTED_CLAIM; runtime_behaviour=UNKNOWN (not run)
- **Adjudication: ADOPT_REFERENCE** - Apache-2.0, richest fee-schedule catalogue and an explicit permanent/temporary impact model to port and validate.

## vectorbt (open-source)
- Repo: polakowo/vectorbt
- License: Apache-2.0 with Commons Clause (non-SPDX; Commons Clause forbids selling)
- Last commit: 2026-09-26 | latest tag (approx): v1.1.1
- Activity: Active
- Dependencies: numpy, pandas, numba, scipy, plotly
- Asset-class assumptions: Any OHLC series; no market microstructure
- Required data: Close/OHLC price arrays; fees, fixed_fees, slippage as scalars/arrays
- Online/offline: Offline vectorised
- Fit for non-HFT intraday execution: Very fast parametric sweeps; costs are flat proportional fees + slippage only. Useful as sweep harness, not as cost model.
- Failure modes: Slippage is a constant fraction, no size or volatility dependence; Commons Clause license restricts commercial redistribution; numba warm-up
- Source paths:
  - `/tmp/oss_clones/vectorbt/vectorbt/portfolio/nb.py: execute_order_nb l.~77-160 (adj_price = price*(1+slippage), req_fees = req_cash*fees + fixed_fees l.149)`
- Smoke executed: **True**. Portfolio.from_signals(fees=0.001, slippage=0.001) 10 shares: Buy price 100.100 fee 1.001; Sell price 103.896 fee 1.03896 (=104*(1-0.001)). Correct symmetric treatment.
- Claim labels: flat_cost_behaviour=PROVEN (smoke); license_restriction=DOCUMENTED_CLAIM (license text read)
- **Adjudication: PARK** - Constant costs only and Commons Clause license; not a cost model.

## backtesting.py
- Repo: kernc/backtesting.py
- License: AGPL-3.0
- Last commit: 2026-08-05 | latest tag (approx): 0.6.6
- Activity: Moderate/active
- Dependencies: numpy, pandas, bokeh
- Asset-class assumptions: Any OHLC
- Required data: OHLCV; spread & commission (float, (fixed,rel) tuple, or callable)
- Online/offline: Offline
- Fit for non-HFT intraday execution: Simple: single 'spread' param applied per side plus commission callable.
- Failure modes: AGPL copyleft; spread applied fully on each side (so it is effectively half-spread; naming trap); no volume/size dependence; fills at next open
- Source paths:
  - `/tmp/oss_clones/backtesting.py/backtesting/backtesting.py: _Broker.__init__ l.727-741; adjusted_price in _Broker`
- Smoke executed: **True**. Backtest(spread=0.002,commission=0.0005): entry 102.204 vs 102.0 at spread 0 => spread is applied as price*(1+spread) per side (i.e. spread = half-spread); exit at finalize (149) had no spread applied. Confirms naming trap and that finalize_trades exits skip spread.
- Claim labels: per_side_spread=PROVEN (smoke); license=OBSERVED
- **Adjudication: REJECT** - AGPL and trivial cost model; only lesson is the per-side spread semantics.

## backtrader broker slippage
- Repo: mementum/backtrader
- License: GPL-3.0
- Last commit: 2023-04-19 | latest tag (approx): 1.94.15.104 (approx tag)
- Activity: Effectively unmaintained since 2023
- Dependencies: pure Python
- Asset-class assumptions: Any
- Required data: Bars; slip_perc/slip_fixed/slip_open/slip_match/slip_limit/slip_out
- Online/offline: Offline
- Fit for non-HFT intraday execution: Constant slippage with match/limit semantic flags
- Failure modes: GPL; abandoned; constant slippage only; edge cases with slip_limit/slip_match
- Source paths:
  - `/tmp/oss_clones/backtrader/backtrader/brokers/bbroker.py: params l.230-240, _slip_up l.994, _slip_down l.1017, _execute l.687`
- Smoke executed: **False**. Not executed (deprecated, GPL).
- Claim labels: maintenance=OBSERVED
- **Adjudication: REJECT** - GPL + abandoned + constant slippage.

## bidask (EDGE spread estimator)
- Repo: eguidotti/bidask
- License: MIT
- Last commit: 2025-10-13 | latest tag (approx): python pkg 2.1.0
- Activity: Active; academic (Ardia, Guidotti, Kroencke JFE 2024)
- Dependencies: numpy, pandas only
- Asset-class assumptions: Any asset with OHLC (equities, crypto, FX)
- Required data: Open/High/Low/Close arrays, >=3 obs
- Online/offline: Offline/rolling; edge_rolling/edge_expanding for streaming windows
- Fit for non-HFT intraday execution: Strong fit: cheap spread proxy from bars when no quotes (non-HFT). Handles missing values.
- Failure modes: Spread is a statistical estimate needing many bars (noise at short windows); assumes mid-price random walk and close/open quote independence; degrades in trending or illiquid/discrete-tick data; only implements EDGE (no CS/AR/Roll in this repo, OBSERVED: only edge*.py). 
- Source paths:
  - `/tmp/oss_clones/bidask/python/bidask/edge.py: edge() l.5; edge_rolling.py; edge_expanding.py; multi-language ports c++/julia/matlab/r/sas`
- Smoke executed: **True**. Synthetic 500-bar series with true 40bp spread built with my own crude OHLC generator: edge() = 0.00269 (27bp). Underestimate reflects my non-realistic synthetic data (highs/lows not built per model); NOT a validation of the estimator. Function runs correctly.
- Claim labels: runs=PROVEN (smoke); accuracy=UNKNOWN (smoke data was synthetic and crude); paper_claims=DOCUMENTED_CLAIM
- **Adjudication: ADOPT_REFERENCE** - MIT, tiny, numpy-only; strongest spread-from-OHLC candidate. Must be validated on real bars vs quotes before use.

## Almgren-Chriss notebook (joshuapjacob)
- Repo: joshuapjacob/almgren-chriss-optimal-execution
- License: MIT
- Last commit: 2022-02-02 | latest tag (approx): none
- Activity: Dead (last commit 2022), single-author notebook
- Dependencies: numpy, scipy (sqrtm), matplotlib
- Asset-class assumptions: Any; model-agnostic (single/multi asset)
- Required data: Parameters: lambda, sigma, epsilon, eta, gamma, tau, X, T
- Online/offline: Offline planning; closed form so can run online
- Fit for non-HFT intraday execution: Trajectory/trade-list generator; direct fit for parent-order schedules (intraday slices)
- Failure modes: Logic lives only inside .ipynb (no package, no tests); trajectory cast to int (rounding drift); requires eta_tilde=eta-0.5*gamma*tau>0; parameters (eta, gamma) must be calibrated separately or output is meaningless; linear impact assumed
- Source paths:
  - `/tmp/oss_clones/almgren-chriss-optimal-execution/Almgren-Chriss Optimal Execution Model.ipynb: class AlmgrenChriss1D (kappa=arccosh(0.5*kappa~^2*tau^2+1)/tau; trajectory=sinh(kappa(T-t))/sinh(kappa T)*X), class AlmgrenChriss (multi-asset)`
- Smoke executed: **True**. Extracted AlmgrenChriss1D from notebook and ran X=1e6,T=10: trajectory front-loaded [1000000,815173,...,0]; with lambda=1e-12 trade list ~ -100000 per slice (TWAP), as theory predicts.
- Claim labels: closed_form_correct=PROVEN (smoke, twap limit); parameter_calibration=UNKNOWN
- **Adjudication: ADAPT_CANDIDATE** - MIT, formula correct, but must be re-implemented as tested module with calibrated eta/gamma; use as oracle test.

## mbt_gym
- Repo: JJJerome/mbt_gym
- License: BSD-3-Clause
- Last commit: 2024-01-08 | latest tag (approx): none
- Activity: Stale (>2y)
- Dependencies: gym==0.21 (pinned; setuptools==65.5.0), stable_baselines3, torch, stochastic
- Asset-class assumptions: Simulated model-based trading (Avellaneda-Stoikov/Cartea-Jaimungal style), synthetic midprice
- Required data: None (simulation): impact coefficients
- Online/offline: Offline simulation for RL/optimal control
- Fit for non-HFT intraday execution: Research reference for temporary/permanent/transient impact processes (Cartea-Jaimungal). Not data driven.
- Failure modes: Old pinned gym breaks installs; models are stylised continuous-time, not empirical; bare copy of a few classes would be needed
- Source paths:
  - `/tmp/oss_clones/mbt_gym/mbt_gym/stochastic_processes/price_impact_models.py: TemporaryPowerPriceImpact l.34, TemporaryAndPermanentPriceImpact l.64, TemporaryAndTransientPriceImpact l.99`
- Smoke executed: **False**. Attempted to exec the module with stubbed base class: FAILED (TypeError unexpected kwarg 'step_size' - my stub signature mismatch, not a library defect). Not pip-installed (torch/gym pins). Source-inspected only.
- Claim labels: impact_forms=OBSERVED (source); runtime=UNKNOWN
- **Adjudication: PARK** - Theory reference for transient impact; too stale/heavy to adopt.

## tick (Hawkes / point processes)
- Repo: X-DataInitiative/tick
- License: BSD-3-Clause
- Last commit: 2026-05-04 | latest tag (approx): v0.8.0.2
- Activity: Low-moderate; maintenance mode
- Dependencies: numpy, scipy, C++ extension (swig)
- Asset-class assumptions: Any event stream (order flow, trades)
- Required data: Event timestamps (multi-dim)
- Online/offline: Offline fitting
- Fit for non-HFT intraday execution: Marginal fit: Hawkes for order-flow/self-excitation modelling; not a cost model. Propagator-style impact would need to be built on it.
- Failure modes: Recent numpy (2.4.6) incompatibility observed; compiled ext; not a propagator library despite the label
- Source paths:
  - `/tmp/oss_clones/tick/tick/hawkes/model/model_hawkes_expkern_loglik.py l.12; tick/hawkes/simulation/simu_hawkes_exp_kernels.py l.126; tick/hawkes/inference`
- Smoke executed: **True**. PARTIAL. pip 0.8.0.2 installs; SimuHawkesExpKernels(adjacency=[[0.3]],decays=[[2.0]],baseline=[0.5],end_time=2000) simulated 1368 events OK. HawkesExpKern.fit(timestamps) FAILED: AttributeError: 'HawkesExpKern' object has no settable attribute 'events' (likely numpy 2.x / tick base __setattr__ incompat; cause INFERENCE).
- Claim labels: sim_runs=PROVEN; fit_failure=PROVEN (cause INFERENCE)
- **Adjudication: REJECT** - Not an impact/cost library; fit path broken on numpy 2.x.

## ABIDES original (execution agents)
- Repo: abides-sim/abides
- License: BSD-3-Clause
- Last commit: 2020-11-19 | latest tag (approx): v1.1
- Activity: Dead since 2020
- Dependencies: numpy 1.16.3, pandas 0.25.1 (pinned, ancient)
- Asset-class assumptions: Simulated equities LOB (NASDAQ ITCH-like), Python 3.7 era
- Required data: Synthetic agents; oracle fundamental value
- Online/offline: Offline multi-agent simulation
- Fit for non-HFT intraday execution: Provides TWAP/VWAP/POV execution agents and OrderBookImbalanceAgent as readable schedule logic; simulation-centric, not calibrated
- Failure modes: Cannot install on modern stack; VWAP uses a synthetic volume profile (INFERENCE from function name synthetic_volume_profile); simulation results depend on agent population
- Source paths:
  - `/tmp/oss_clones/abides/agent/execution/TWAPExecutionAgent.py (37 lines)`
  - `/tmp/oss_clones/abides/agent/execution/VWAPExecutionAgent.py: generate_schedule l.25, synthetic_volume_profile l.43`
  - `/tmp/oss_clones/abides/agent/execution/POVExecutionAgent.py: wakeup l.40, receiveMessage l.53`
- Smoke executed: **False**. Not executed (pins numpy 1.16/pandas 0.25 incompatible with py3.11).
- Claim labels: schedule_logic=OBSERVED (source read at function level, not line by line)
- **Adjudication: PARK** - Schedule logic readable as reference for TWAP/VWAP/POV; nothing to adopt.

## ABIDES-JPMC-public (abides-markets/gym)
- Repo: jpmorganchase/abides-jpmc-public
- License: BSD-3-Clause
- Last commit: 2023-12-13 | latest tag (approx): none
- Activity: Dormant (last commit 2023-12)
- Dependencies: numpy==1.22.0, pandas==1.2.4 pinned, gym
- Asset-class assumptions: Simulated equities LOB
- Required data: Simulation config; agent populations
- Online/offline: Offline simulation; abides-gym for RL execution env
- Fit for non-HFT intraday execution: Has LOB implementation (order_book.py) and execution env in abides-gym; research sandbox, not cost estimation
- Failure modes: Pinned old deps; no execution agents in abides-markets (TWAP/VWAP live only in original abides, OBSERVED by ls); simulated only
- Source paths:
  - `/tmp/oss_clones/abides-jpmc-public/abides-markets/abides_markets/order_book.py`
  - `/tmp/oss_clones/abides-jpmc-public/abides-markets/abides_markets/agents/`
- Smoke executed: **False**. Not executed (old pins).
- Claim labels: agent_inventory=OBSERVED (ls)
- **Adjudication: PARK** - Simulation sandbox; no direct use.

## Corwin-Schultz / Abdi-Ranaldo / Roll in pyfolio-reloaded & quantstats
- Repo: stefan-jansen/pyfolio-reloaded ; ranaroussi/quantstats
- License: Apache-2.0 (both)
- Last commit: 2025-06-02 (pyfolio) / 2026-09-27 (quantstats) | latest tag (approx): v0.8.0 / v0.0.86
- Activity: pyfolio dormant, quantstats active
- Dependencies: pandas, numpy, scipy
- Asset-class assumptions: Equity returns analytics
- Required data: Returns/transactions
- Online/offline: Offline analytics
- Fit for non-HFT intraday execution: No spread estimators found. pyfolio txn.py has adjust_returns_for_slippage (flat bps * turnover) and get_turnover only; quantstats grep for slippage/spread yielded nothing in quantstats/*.py
- Failure modes: Negative result: the user-hypothesised Corwin-Schultz/AR/Roll are not in these libs
- Source paths:
  - `/tmp/oss_clones/pyfolio-reloaded/src/pyfolio/txn.py: adjust_returns_for_slippage l.113, get_turnover l.148`
- Smoke executed: **False**. Not executed; negative finding from grep.
- Claim labels: absence_of_CS_AR_Roll=OBSERVED (grep of these repos; not an exhaustive claim about the internet)
- **Adjudication: REJECT** - Not sources of spread estimators; only post-hoc flat-bps slippage adjustment.

## freqtrade funding-fee handling
- Repo: freqtrade/freqtrade
- License: GPL-3.0
- Last commit: 2026-09-29 | latest tag (approx): stable releases yearly-tagged; tag sort unreliable
- Activity: Very active
- Dependencies: pandas, ccxt, TA-Lib etc.
- Asset-class assumptions: Crypto futures (Binance, Bybit, OKX, etc.)
- Required data: Funding-rate candles and mark-price candles (candle_type funding_rate/mark)
- Online/offline: Offline backtest + live
- Fit for non-HFT intraday execution: Good reference for funding cost accrual: sum(funding_rate*mark_price*amount) over funding timestamps between open and close; sign negated for longs
- Failure modes: GPL-3.0 (copyleft; read as reference only); funding timeframe per exchange (8h default 'funding_fee_timeframe' 1h in ft_has); missing candles yield zero fees (isnan -> 0.0) silently
- Source paths:
  - `/tmp/oss_clones/freqtrade/freqtrade/exchange/exchange.py: calculate_funding_fees l.4166-4202, get_funding_fees l.4204, _fetch_funding_rate_history l.3225, funding_fee_timeframe l.165/2856`
- Smoke executed: **False**. Not executed: full freqtrade install heavy; source read only.
- Claim labels: funding_accrual_logic=OBSERVED (source); nan_to_zero=OBSERVED
- **Adjudication: ADOPT_REFERENCE** - Concept reference only (GPL - do not copy code). Note the silent NaN->0 failure mode.

## ccxt fee & funding-rate history
- Repo: ccxt/ccxt
- License: MIT
- Last commit: 2026-09-29 | latest tag (approx): v4.5.84
- Activity: Very active
- Dependencies: requests, aiohttp, cryptography; ~570MB clone
- Asset-class assumptions: Crypto spot/perp across 100+ exchanges
- Required data: Live exchange API keys for some endpoints; public for funding history
- Online/offline: Online (network) - offline parsing possible
- Fit for non-HFT intraday execution: Standardised fetchFundingRateHistory / fetchTradingFee / parse_funding_rate_history. Data-collection adapter, not a model.
- Failure modes: Per-exchange inconsistencies (has flags 'emulated' vs true); rate limits; pagination limits on history; fees may be static defaults vs account tier
- Source paths:
  - `/tmp/oss_clones/ccxt/python/ccxt/binance.py: fetch_funding_rate_history l.10326, parse_funding_rate l.10426, fetch_trading_fee l.10008`
  - `/tmp/oss_clones/ccxt/python/ccxt/base/exchange.py: fetch_funding_rate_history l.6406 (NotSupported default), parse_funding_rate l.6824`
- Smoke executed: **True**. Offline (no network): ccxt.binanceusdm().has -> fetchFundingRateHistory True, fetchTradingFee True, fetchFundingRate True; parse_funding_rate_history on a hand-made raw row returned fundingRate 0.0001, timestamp 1700000000000 ISO 2023-11-14T22:13:20Z. No live call made.
- Claim labels: offline_parse=PROVEN (smoke); live_endpoint_behaviour=UNKNOWN
- **Adjudication: ADOPT_REFERENCE** - MIT; standard adapter for fee/funding data schemas. Live behaviour UNKNOWN (no network calls made).

## hummingbot executors (TWAP etc.)
- Repo: hummingbot/hummingbot
- License: Apache-2.0
- Last commit: 2026-09-22 | latest tag (approx): v2.17.0
- Activity: Very active
- Dependencies: Cython, pandas, many connectors
- Asset-class assumptions: Crypto CEX/DEX
- Required data: Live connector order books
- Online/offline: Online live executors
- Fit for non-HFT intraday execution: TWAPExecutor in strategy_v2 is an execution scheduler reference (create_order_plan, evaluate_create_order); slippage handled via slippage_pct retries for gateway
- Failure modes: Live-only architecture, heavy; TWAP is time-sliced without volume profile (INFERENCE from file listing/short read)
- Source paths:
  - `/tmp/oss_clones/hummingbot/hummingbot/strategy_v2/executors/twap_executor/twap_executor.py: TWAPExecutor l.24, create_order_plan l.50, evaluate_create_order l.98`
  - `/tmp/oss_clones/hummingbot/hummingbot/strategy_v2/executors/gateway_utils.py (is_slippage_failure, next_slippage_pct)`
- Smoke executed: **False**. Not executed (live-only stack).
- Claim labels: twap_structure=OBSERVED (signatures only)
- **Adjudication: PARK** - Executor design reference; no cost model.

## PyLOB
- Repo: DrAshBooth/PyLOB
- License: MIT
- Last commit: 2026-08-14 | latest tag (approx): v1.0.0
- Activity: Recently touched (AGENTS.md/CLAUDE.md present, suggests AI-assisted refresh, INFERENCE)
- Dependencies: pure Python
- Asset-class assumptions: Generic LOB
- Required data: Order messages
- Online/offline: Offline LOB
- Fit for non-HFT intraday execution: Educational limit order book matching engine; useful for unit-testing fill logic, not for costs
- Failure modes: Not performance oriented; not calibrated; no market impact
- Source paths:
  - `/tmp/oss_clones/PyLOB/src/PyLOB/engine.py, replay.py, events.py`
- Smoke executed: **False**. Not executed.
- Claim labels: scope=OBSERVED (ls)
- **Adjudication: PARK** - Toy matching engine; could serve as a test oracle for sweep-the-book cost.

## bmoscon orderbook (order-book on PyPI)
- Repo: bmoscon/orderbook
- License: GPL-3.0
- Last commit: 2026-09-02 | latest tag (approx): v1.1.0
- Activity: Active
- Dependencies: C extension, requires Python 3.13+ (README)
- Asset-class assumptions: Generic L2/L3 book
- Required data: Book updates
- Online/offline: Online/offline
- Fit for non-HFT intraday execution: High-performance book data structure; not a cost model. Useful for computing walk-the-book cost.
- Failure modes: GPL-3.0; needs Python 3.13+; PyPI name is 'order-book' - I installed 'orderbook' (a different, broken package)
- Source paths:
  - `/tmp/oss_clones/orderbook/orderbook/orderbook.c, orderbook.h, sorteddict.c`
- Smoke executed: **False**. FAILED: pip install orderbook (wrong PyPI package 0.1.2) -> ImportError circular import; source install on Python 3.11 also import-failed (repo needs 3.13+). executed=false.
- Claim labels: import_failure=PROVEN; python_requirement=DOCUMENTED_CLAIM (README)
- **Adjudication: REJECT** - GPL and data-structure only.

## vnpy
- Repo: vnpy/vnpy
- License: MIT
- Last commit: 2026-08-06 | latest tag (approx): v2.1.7 (tag sort unreliable)
- Activity: Active
- Dependencies: many modules
- Asset-class assumptions: China futures/equities + crypto gateways
- Required data: Bars/ticks
- Online/offline: Offline+live
- Fit for non-HFT intraday execution: Slippage in vnpy is in the separate vnpy_ctastrategy package (not in this repo core); only notebooks/README mention slippage in core repo (grep)
- Failure modes: Not covering slippage model source here; UNKNOWN in separate package
- Source paths:
  - `/tmp/oss_clones/vnpy (grep for slippage: README_ENG.md, examples/*/backtesting.ipynb only)`
- Smoke executed: **False**. Not executed.
- Claim labels: slippage_location=OBSERVED (grep negative in core repo)
- **Adjudication: PARK** - Relevant code lives in a package not cloned; revisit if needed.
