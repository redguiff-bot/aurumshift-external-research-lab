# 08 — Falsification log

Hypotheses were written before the runs (01, 02). Outcomes use held-out results (04/05/06).

| # | hypothesis | outcome | evidence |
|---|---|---|---|
| H1 | Incremental methods beat a tuned rolling refit by ≥10 % on drift | **PARTLY SUPPORTED** — only 2 of 19 candidate entries pass all four gates; best gains are 12 % (C, `bank_sgd_log`) and 15 % (R, `rls`) | 04 §4.2 |
| H2 | Trees / forests / ADWIN-bagging handle drift better than linear learners | **FALSIFIED here** — 2.6–5.2× worse than rolling; only ARF on the nonlinear scenario is marginally better (0.309 vs 0.321) | 04 |
| H3 | Drift-triggered reset beats the plain recursive learner | **FALSIFIED** — `reset_rls` 1.25× vs `rls` 0.85× rolling; `reset_sgd_log` 0.93 vs `sgd_log` 0.90; resets are worse after shocks (5.3) | 04, 05 |
| H4 | Reset is harmful on false drift | **NOT SUPPORTED as stated** — `reset_sgd_log` false_drift 0.019 vs rolling 0.016 (1.2×): mild. The actually fragile ones are un-guarded SGD (2.4×), ARF/HAT (R: 22–29×), PA-raw | 04 |
| H5 | RLS/Kalman are the strongest incremental methods on linear drift | **SUPPORTED for RLS, weakly for Kalman** — `rls` (λ=0.99) 0.85; `kalman` 1.05 with q at its grid edge (1e-5) — under-explored (INFERENCE that a larger grid would match RLS; not tested). `blr` had the lowest raw regret (0.78) but fails (b) | 04 |
| H6 | A memory bank recovers recurring regimes | **SUPPORTED** (return-cost 0.42 C / 0.34 R; 39–40 steps vs 373–431) **but** costs: gradual/random-walk (R) and it fails (a) on R | 05 |
| H7 | Online calibration fixes PA/SGD probabilities | **MIXED** — Platt cuts stationary/false-drift regret 3–5× (PA: 0.049→0.010; 0.053→0.012) but slows re-adaptation (recurring PA 0.073→0.124; missing 0.073→0.148) | 04 |
| H8 | Frozen and expanding-batch retraining are sufficient | **FALSIFIED under drift** (5–8× / 3–5× worse), **but true under stationarity/shock/false drift** where batch is best (0.003 vs 0.014) | 04 |
| H9 | Missing / delayed feedback reverses rankings | **NOT SUPPORTED** — regret roughly doubles for all (rolling 0.042→0.097 missing; →0.070 delayed) but the ordering of top methods is stable; plain `sgd_log` is best under missing feedback (0.068), `reset_sgd_log` under delay (0.062) — differences small | 04 |
| H10 | All candidates can be replayed bit-for-bit and checkpointed | **NOT FALSIFIED** (25/25 on 4 tests, negative control detected) on one platform | 06 |
| H11 | Complexity earns its place | **ONLY THE SIMPLEST** — the winning R method is 840 bytes and 10 lines; forests/bagging/detector stacks never earn it | 04 |
| H12 | Result is a low-SNR artefact / robust to lower SNR | **Direction robust**: at ~3× lower SNR, linear recursive learners gain 20–28 % over rolling; trees still 2–5× worse (configs not re-tuned) | 04 §4.4 |

## Things that could still overturn the conclusion (not run)
* Re-tune the rolling window and all baselines per scenario (protocol forbids it here; it would shrink online gains).
* Grid edges: `kalman` q=1e-5, `sgd_lin` lr=0.003, `sgd_log` lr=0.1, `rolling|R` window=150, `batch` period=250 were chosen at the edge of their grids.
* Longer streams / real, heavy-tailed, autocorrelated data (10).
