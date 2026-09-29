# 02 — Methods discovered, and what was executed

Evidence labels follow `claude.md`: PROVEN (shown by a run in this repo), OBSERVED (seen in code
inspected here), DOCUMENTED_CLAIM (from the literature, **recalled from the primary papers; the
papers were not re-fetched in this session**), INFERENCE, UNKNOWN.

## A. Literature families (discovered)

| # | Method | Primary source (recalled) | Handles absent experts? | Label |
|---|---|---|---|---|
| 1 | Weighted majority / Hedge | Littlestone–Warmuth 1994; Freund–Schapire 1997 | no (all experts always awake) | DOCUMENTED_CLAIM |
| 2 | Exponentiated Gradient (EG) | Kivinen–Warmuth 1997; Helmbold et al. 1998 | no | DOCUMENTED_CLAIM |
| 3 | Specialists (experts that "abstain") | Freund, Schapire, Singer, Warmuth 1997 | yes — update only awake experts, preserve mass | DOCUMENTED_CLAIM |
| 4 | Sleeping experts | Blum 1997; Blum–Mansour 2007; Kleinberg–Niculescu-Mizil–Sharma 2010 | yes; regret vs each expert on its awake rounds | DOCUMENTED_CLAIM |
| 5 | Fixed-share / tracking the best expert | Herbster–Warmuth 1998 | via mixing; sleeping variants: Adamskiy et al. "Putting Bayes to sleep" 2012 | DOCUMENTED_CLAIM |
| 6 | Adaptive-regret / discounted-loss experts | Hazan–Seshadhri 2009; Chernov–Zhdanov 2010 | discount clock is a design choice (wall-clock vs evidence-time) | DOCUMENTED_CLAIM |
| 7 | Parameter-free / second-order (AdaNormalHedge, Squint-type) | Luo–Schapire 2015; Koolen–van Erven 2015; Gaillard et al. 2014 | AdaNormalHedge has a sleeping formulation | DOCUMENTED_CLAIM (not executed) |
| 8 | Growing / changing expert sets | Mourtada–Maillard 2017 (growing number of experts) | yes (newcomer initialisation) | DOCUMENTED_CLAIM |
| 9 | Bayesian / dynamic model averaging | Raftery et al. 2010 (DMA, forgetting factor); Hoeting et al. 1999 (BMA) | via prior / forgetting | DOCUMENTED_CLAIM |
| 10 | Context-conditioned mixtures / mixture of experts, contextual experts (EXP4) | Jacobs et al. 1991; Auer et al. 2002 (EXP4) | via context gating | DOCUMENTED_CLAIM |
| 11 | Sleeping bandits, EXP3(.S), discounted UCB | Kleinberg et al. 2010; Auer et al. 2002; Garivier–Moulines 2011 | bandit feedback | DOCUMENTED_CLAIM |
| 12 | Diversity / correlation-aware combining (decorrelation penalties, negative-correlation ensembles; "ensemble of correlated experts" analyses) | assorted; no single canonical online-regret result recalled | n/a | INFERENCE |
| 13 | Follow-the-leader / winner-take-all | Hannan 1957; known to be unstable without perturbation | n/a | DOCUMENTED_CLAIM |

Discovered = 13 method families (+ baselines: equal, static, WTA, EWMA counted inside them).

## B. Open-source implementations inspected (REUSE-first check)

Downloaded wheels/sdists and inspected the source (PROVEN by inspection, this session, PyPI,
not by running them):

| Package | Finding |
|---|---|
| `river` 0.26.1 (BSD-3) | `ensemble/ewa.py` `EWARegressor` is plain Hedge/EWA: every model is updated every step, weights multiply by `exp(-lr*loss)`; **no availability mask, no specialist/sleeping/fixed-share/discount option** (OBSERVED). Only a doc reference to weighted-majority/Hedge. |
| `mabwiser` 2.7.4 | bandit policies (greedy, UCB, softmax, Thompson, ...); grep for sleeping/specialist/fixed-share/hedge/exp3 found nothing (OBSERVED). |
| `contextualbandits` 0.3.30 | same grep, nothing found (OBSERVED). |
| others (opytimizer downloaded, not relevant) | not used. |

Consequence (INFERENCE): the sleeping-expert update is ~15 lines and is not available as a
maintained drop-in in these libraries, so any adoption would be ADAPT/CUSTOM-small, not REUSE. No
maintained package specialising in sleeping experts for finance was found in this brief search
(UNKNOWN whether one exists beyond PyPI's top hits; the search was not exhaustive).

## C. What was actually executed (bench/ensemble_v1)

All in `learners.py`, own implementation, ~20 method rows, tuned on separate seeds:

| Row | Family | Notes |
|---|---|---|
| Equal | baseline | uniform over allocated |
| Static | baseline | weights frozen after a 250-round calibration window |
| WTA | baseline | argmax of EWMA score, hard choice |
| EWMA | baseline | softmax of exponentially weighted mean reward, observation-gated |
| HedgePlain | Hedge (non-sleeping ref.) | cumulative loss, unobserved adds nothing |
| SleepHedge | specialists / sleeping | Freund et al. update; mass of observed set preserved |
| SleepEG | EG, sleeping | multiplicative on r/(w·r) |
| FixedShare | fixed-share (sleeping) | share only on evidence rounds |
| DiscFreeze / DiscAmnesty | discounted experts | forgetting on evidence-time vs wall-clock |
| SH_bounded / EWMA_bounded | bounded adaptive weighting | log-weight bound B, uniform floor, cap 0.7 |
| BMA | Bayesian model averaging (DMA-style) | Gaussian conjugate posterior mean, forgetting, cohort-shrunk prior |
| CtxOracle / CtxLag / CtxNoisy | context-conditioned mixture | per-regime + global sleeping weights; true / 1-round-lagged / 20%-flipped label |
| DivEWMA / DivSH | diversity-aware | base weights ÷ crowding from online correlation |
| SleepEXP3 / DUCB | bandit comparators | bandit feedback / hard choice |

Not executed: AdaNormalHedge/Squint (parameter-free) and full Bayesian predictive BMA — 
the latter reduces to Hedge under exponential-loss likelihood (INFERENCE), so `BMA` here is the
posterior-mean/forgetting (DMA-style) *adaptation*, not textbook BMA. `METHODS_DISCOVERED=13`,
`METHODS_EXECUTED=20` (row count in the registry, listed above).
