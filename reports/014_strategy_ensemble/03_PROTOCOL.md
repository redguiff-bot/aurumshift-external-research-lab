# 03 — Protocol

Everything is in `bench/ensemble_v1/`. The decision rules were frozen in
`bench/ensemble_v1/PREREGISTRATION.md` and committed (commit "scenario generator, learners, runner
and pre-registration (no results yet)") **before** any tuning or held-out run.

## Simulator
* K=12 expert slots, T=1200 rounds, reward in [0,1] centred at 0.5, true mean = 0.5 + edge(regime).
  Noise = common market factor (sd 0.10) + idiosyncratic (sd 0.10), clipped.
* 4 regimes, Markov with ~33-round dwell; regime R3 is rare (~5%) and only the specialist RARE is
  valid there. Specialists: VOLSPEC (R2), RARE (R3), BRK (R0,R2); generalists TREND, MREV, CARRY, DUD (bad),
  LATE (strong, can be introduced late); clones CLN0-2.
* Per (round, expert) state: NOT_EXIST / INACTIVE / ABSTAIN / GAP / OBS (semantics in 04).
* Full information among OBS experts (shadow returns). Bandit rows only use the sampled/chosen expert.
* Metric: noise-free expected regret to the truth oracle (best truly-valid allocated expert each round),
  plus realised reward. No transaction costs, no capacity, linear (risk-neutral) objective — see 10.

## Scenarios (12 CORE + 1 stress)
S0 base · S1 leadership rotates at T/4,T/2,3T/4 · S2 rare-regime dormancy (~840 rounds) · S3 new expert
at T/3 · S4 best regime-0 generalist retired at T/2 · S5a 3 clones of the bad expert · S5b 3 clones of
the best generalist · S6a 30% MCAR data gaps · S6b 350-round burst gap on TREND · S6d informative
abstention (generalists abstain when they would lose) · S7 temporary underperformance (LATE 150-round
bad patch; RARE unlucky first 15 observations) · S8 composite · S6c MNAR gaps (bad outcomes go missing;
stress only).

## Split and tuning
* Tuning seeds 0-5; grid search per method; pooled regret (12 scenarios equal weight).
* Round 1 grids -> many optima on grid edges -> ONE pre-declared extension round (tune2.py) -> frozen.
  Several optima are still on an edge after extension (e.g. SleepHedge eta=400, WTA-like hard
  concentration): the objective plateaus toward winner-take-all (see 10).
* Held-out seeds 1000-1039 (40), stress seeds 2000-2019 (lowsnr = edges x0.5; highnoise = noise x1.6),
  sensitivity seeds 3000-3007 (reporting only), 22,880 held-out runs.
* Unit tests (`py/test_semantics.py`, results/unit_tests.json): for all 20 rows — valid simplex and
  support inside allocation; an update with no observation leaves every state array bit-identical
  (except DiscAmnesty, by design); weights at t unchanged when all rewards from t+1 on are replaced
  (no look-ahead). All pass.

## Reproduce
```
cd bench/ensemble_v1/py
python3 test_semantics.py; python3 tune.py; python3 tune2.py; python3 heldout.py
python3 analyze.py; python3 analyze_amended.py; python3 sensitivity.py; python3 label_noise.py; python3 starvation_extra.py
```
Needs only numpy (2.4.6 used, Python 3.11). Wall-clock: tuning ~9 min, held-out ~9 min on 4 cores.
