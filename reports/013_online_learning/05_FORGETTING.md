# 05 — Forgetting, recurring states, adaptation speed, variance, state growth

Source: `results/tables.md` (held-out seeds 1–15). Probes are 300 fixed points evaluated **without learning** at t=999/1999/2999/3999 against concept A and concept B.

## 5.1 What "catastrophic forgetting" can and cannot mean here
Concepts A and B are orthogonal by construction. A single linear parameter vector that tracks B *must* be wrong about A: for a perfect B-model the probe-A loss is ≈2.0 (R) and ≈1.0 nats (C, KL). So a high "probeA end-B1" is **not** evidence of a defect for a single-state learner — it is the price of plasticity. The informative quantities are (i) whether A is re-learned **faster the second time** (return-cost ratio), (ii) plasticity (probeB end-B1), (iii) damage from a short blip (shock).

## 5.2 Recurring states (scenario `recurring`)
### Forgetting and recurring-state recovery (scenario `recurring`; probes at t=999 end-A1, 1999 end-B1, 2999 end-A2, 3999 end-B2)


**Track C** (probe loss on fixed probe set; C: KL(p_true||p_model), R: MSE vs true mean; ignorance level R=1.0, C≈see 05 )

| model | probeA end-A1 | probeA end-B1 (forgetting) | probeB end-B1 (plasticity) | probeA end-A2 (re-learned A) | return-cost ratio post600(t=2000)/post600(t=1000) | adapt steps t=2000 vs t=1000 |
|---|---|---|---|---|---|---|
| adwin_bag | 0.055 | 0.264 | 0.177 | 0.107 | 0.49 | 0 vs 600 |
| arf | 0.173 | 0.408 | 0.200 | 0.202 | 0.99 | 45 vs 207 |
| bank_sgd_log | 0.013 | 0.838 | 0.012 | 0.009 | 0.42 | 39 vs 431 |
| batch | 0.007 | 0.155 | 0.254 | 0.122 | 0.26 | 0 vs 600 |
| frozen | 0.010 | 0.010 | 0.994 | 0.010 | 0.01 | 0 vs 600 |
| hat | 0.053 | 0.420 | 0.240 | 0.102 | 0.73 | 0 vs 600 |
| ht | 0.057 | 0.297 | 0.212 | 0.129 | 0.57 | 0 vs 600 |
| pa_platt | 0.012 | 0.887 | 0.013 | 0.015 | 0.93 | 550 vs 600 |
| pa_raw | 0.063 | 0.824 | 0.047 | 0.052 | 1.02 | 68 vs 67 |
| reset_sgd_log | 0.014 | 0.831 | 0.013 | 0.014 | 1.04 | 415 vs 419 |
| rolling | 0.013 | 1.012 | 0.015 | 0.015 | 1.02 | 263 vs 260 |
| sgd_log | 0.028 | 1.105 | 0.021 | 0.024 | 1.00 | 133 vs 124 |
| sgd_log_platt | 0.013 | 1.038 | 0.011 | 0.011 | 0.97 | 435 vs 430 |

**Track R** (probe loss on fixed probe set; C: KL(p_true||p_model), R: MSE vs true mean; ignorance level R=1.0, C≈see 05 )

| model | probeA end-A1 | probeA end-B1 (forgetting) | probeB end-B1 (plasticity) | probeA end-A2 (re-learned A) | return-cost ratio post600(t=2000)/post600(t=1000) | adapt steps t=2000 vs t=1000 |
|---|---|---|---|---|---|---|
| arf | 0.181 | 1.207 | 0.425 | 0.430 | 0.82 | 104 vs 600 |
| bank_rls | 0.003 | 2.040 | 0.003 | 0.001 | 0.34 | 40 vs 373 |
| batch | 0.003 | 0.381 | 0.667 | 0.270 | 0.29 | 0 vs 600 |
| blr | 0.024 | 1.998 | 0.020 | 0.019 | 1.02 | 96 vs 93 |
| frozen | 0.004 | 0.004 | 2.040 | 0.004 | 0.00 | 0 vs 600 |
| hat | 0.048 | 2.031 | 0.064 | 0.053 | 1.01 | 127 vs 142 |
| kalman | 0.007 | 2.022 | 0.005 | 0.005 | 1.01 | 342 vs 380 |
| par_reg | 0.026 | 2.091 | 0.023 | 0.021 | 1.07 | 221 vs 204 |
| reset_rls | 0.003 | 2.040 | 0.002 | 0.002 | 0.99 | 268 vs 278 |
| rls | 0.012 | 2.017 | 0.009 | 0.009 | 1.02 | 204 vs 212 |
| rolling | 0.017 | 2.027 | 0.012 | 0.012 | 1.04 | 141 vs 140 |
| sgd_lin | 0.007 | 2.023 | 0.005 | 0.005 | 0.99 | 347 vs 407 |


* **Only the memory bank recovers a recurring state cheaply**: return-cost ratio 0.42 (C) / 0.34 (R); median adapt steps 39 vs 431 (C) and 40 vs 373 (R) at the return vs the first novel switch. Every single-state method (`rolling`, `rls`, `kalman`, `sgd_*`, `pa_*`, `reset_*`) sits at ratio ≈1.0 (0.93–1.07) — no memory, as expected (OBSERVED).
* The apparently low ratios of `batch`/`frozen`/`ht`/`adwin_bag` are **artefacts**, not memory: they adapt so slowly (censored at 600 steps at the first switch) that returning to A costs little because they never left it (frozen: ratio 0.01 with probeB loss 0.99–2.04, i.e. it never learned B). ARF/HAT/HT retain partial A knowledge (probeA end-B1 0.26–0.42 in C, far below the 0.8–1.1 of linear learners) but at 2–3× the steady regret.
* The bank pays for its memory elsewhere: `gradual` (R: 2.8× rolling), `random_walk` (R: 0.147 vs 0.058) and `abrupt_nonlinear`; snapshots of a moving target are stale. It passes (b) on C (worst 1.14×) but fails (a) on R (ratio 1.23). Bank switching is a **CUSTOM** wrapper (≈40 LOC) and its benefit is confined to genuinely recurring regimes — evidence for recurrence in real data is UNKNOWN.

## 5.3 Temporary shock (100 steps of B, then back to A) — over-reaction damage
Post-return 600-step regret (C): `batch` 0.004 and `frozen` 0.009 (they ignore the blip), `bank_sgd_log` 0.029, `sgd_log_platt` 0.037, `rolling` 0.057, `reset_sgd_log` 0.075, `arf` 0.155. (R): batch/frozen 0.004, `bank_rls` 0.037, `rls` 0.079, `rolling` 0.154 (window of 150 samples is fully overwritten by the blip). Fast adaptation is costly when the change turns out to be transient; drift detectors that reset (`reset_*`) do *worse* than the plain learner here.

## 5.4 Adaptation speed (abrupt, gradual, return)
### Adaptation speed — steps to rolling-50 regret <= 1.5x own pre-change level + 0.01 (censored at 600), pooled over seeds; and 600-step post-change regret


**Track C**

| model | abrupt median steps [%censored] | abrupt post-600 regret | gradual median [%cens] | recurring return(t=2000) median [%cens] | shock post-return regret (t=2100) |
|---|---|---|---|---|---|
| adwin_bag | 600 [93%] | 0.440 | 0 [0%] | 0 [0%] | 0.053 |
| arf | 288 [7%] | 0.323 | 0 [0%] | 45 [0%] | 0.155 |
| bank_sgd_log | 600 [60%] | 0.162 | 0 [0%] | 39 [7%] | 0.029 |
| batch | 600 [100%] | 0.750 | 0 [0%] | 0 [0%] | 0.004 |
| frozen | 600 [100%] | 0.953 | 0 [0%] | 0 [0%] | 0.009 |
| hat | 600 [73%] | 0.460 | 0 [0%] | 0 [7%] | 0.124 |
| ht | 600 [93%] | 0.459 | 0 [0%] | 0 [0%] | 0.055 |
| pa_platt | 600 [100%] | 0.252 | 0 [0%] | 550 [33%] | 0.031 |
| pa_raw | 74 [0%] | 0.097 | 0 [0%] | 68 [0%] | 0.081 |
| reset_sgd_log | 600 [60%] | 0.144 | 0 [0%] | 415 [13%] | 0.075 |
| rolling | 266 [0%] | 0.173 | 0 [0%] | 263 [0%] | 0.057 |
| sgd_log | 144 [0%] | 0.106 | 0 [0%] | 133 [0%] | 0.053 |
| sgd_log_platt | 556 [27%] | 0.177 | 0 [0%] | 435 [0%] | 0.037 |

**Track R**

| model | abrupt median steps [%censored] | abrupt post-600 regret | gradual median [%cens] | recurring return(t=2000) median [%cens] | shock post-return regret (t=2100) |
|---|---|---|---|---|---|
| arf | 600 [100%] | 1.054 | 0 [0%] | 104 [0%] | 0.218 |
| bank_rls | 401 [7%] | 0.326 | 0 [0%] | 40 [0%] | 0.037 |
| batch | 600 [100%] | 1.659 | 0 [0%] | 0 [0%] | 0.004 |
| blr | 93 [0%] | 0.119 | 0 [0%] | 96 [0%] | 0.089 |
| frozen | 600 [100%] | 1.946 | 0 [0%] | 0 [0%] | 0.004 |
| hat | 128 [7%] | 0.279 | 0 [0%] | 127 [0%] | 0.117 |
| kalman | 402 [0%] | 0.288 | 0 [0%] | 342 [0%] | 0.065 |
| par_reg | 213 [0%] | 0.279 | 0 [0%] | 221 [0%] | 0.065 |
| reset_rls | 291 [0%] | 0.291 | 0 [0%] | 268 [0%] | 0.095 |
| rls | 219 [0%] | 0.193 | 0 [0%] | 204 [0%] | 0.079 |
| rolling | 134 [0%] | 0.230 | 0 [0%] | 141 [0%] | 0.154 |
| sgd_lin | 410 [0%] | 0.296 | 0 [0%] | 347 [0%] | 0.065 |


Fastest to recover after an abrupt change (C): `pa_raw` 74 steps, `sgd_log` 144, `rolling` 266; (R): `blr`(smoothing 0.98) 93, `hat` 128, `rolling` 134, `rls`(λ=0.99) 219. Methods whose all-scenario-average tuning favoured slow, low-variance settings (`pa_platt` 100 %, `reset_sgd_log` 60 %, `sgd_log_platt` 27 % censored) recover slowly; `kalman`/`sgd_lin` take ≈400 steps (q=1e-5 and lr=0.003 sit at the **edge** of their grids, so their speed is a tuning artefact, see 10). "Gradual" shows 0 steps because the drift is slow enough that regret is still under the threshold at the change point — treat that column as uninformative (see 10).

## 5.5 Variance and state growth
### Variance, state growth, compute (all scenarios pooled)


**Track C**

| model | median CV of regret across seeds | worst-seed / median-seed regret (max over scenarios) | state bytes @1000 (median) | @4000 (median) | max growth ratio | learn µs/label | predict µs |
|---|---|---|---|---|---|---|---|
| adwin_bag | 0.15 | 1.8 | 323,429 | 821,538 | 3.89 | 377 | 116 |
| arf | 0.07 | 1.2 | 2,341,288 | 8,084,329 | 5.10 | 510 | 102 |
| bank_sgd_log | 0.10 | 1.7 | 20,145 | 20,401 | 1.03 | 20 | 4 |
| batch | 0.04 | 1.8 | 116,260 | 464,326 | 4.33 | 13 | 7 |
| frozen | 0.10 | 2.2 | 334 | 334 | 1.00 | 1 | 6 |
| hat | 0.16 | 1.6 | 69,087 | 165,306 | 4.72 | 83 | 31 |
| ht | 0.11 | 1.7 | 63,342 | 125,620 | 3.96 | 42 | 23 |
| pa_platt | 0.09 | 1.3 | 611 | 611 | 1.00 | 21 | 10 |
| pa_raw | 0.05 | 1.2 | 505 | 505 | 1.00 | 10 | 9 |
| reset_sgd_log | 0.09 | 1.6 | 19,698 | 19,826 | 1.04 | 12 | 4 |
| rolling | 0.09 | 1.3 | 35,169 | 35,169 | 1.00 | 88 | 8 |
| sgd_log | 0.07 | 1.5 | 788 | 788 | 1.00 | 7 | 4 |
| sgd_log_platt | 0.08 | 1.3 | 894 | 894 | 1.00 | 17 | 10 |

**Track R**

| model | median CV of regret across seeds | worst-seed / median-seed regret (max over scenarios) | state bytes @1000 (median) | @4000 (median) | max growth ratio | learn µs/label | predict µs |
|---|---|---|---|---|---|---|---|
| arf | 0.07 | 1.4 | 564,170 | 2,126,360 | 4.70 | 1135 | 114 |
| bank_rls | 0.10 | 2.1 | 20,428 | 21,962 | 1.11 | 19 | 2 |
| batch | 0.04 | 2.1 | 116,247 | 464,313 | 4.33 | 2 | 2 |
| blr | 0.07 | 1.6 | 1,693 | 1,693 | 1.00 | 22 | 7 |
| frozen | 0.05 | 2.5 | 313 | 313 | 1.00 | 0 | 1 |
| hat | 0.17 | 2.7 | 159,369 | 275,844 | 5.87 | 320 | 13 |
| kalman | 0.09 | 1.5 | 838 | 838 | 1.00 | 13 | 2 |
| par_reg | 0.08 | 1.3 | 649 | 649 | 1.00 | 11 | 4 |
| reset_rls | 0.15 | 2.0 | 19,645 | 19,773 | 1.03 | 15 | 2 |
| rls | 0.09 | 1.5 | 841 | 841 | 1.00 | 11 | 1 |
| rolling | 0.09 | 1.5 | 17,755 | 17,755 | 1.00 | 3 | 1 |
| sgd_lin | 0.09 | 1.4 | 693 | 693 | 1.00 | 6 | 3 |


* Seed-to-seed CV of regret: 0.04–0.17 (median across scenarios); worst-seed/median-seed ≤ 2.7 (HAT, R). Trees/HAT have the highest variance (CV 0.16–0.17); `batch`/`arf` the lowest (0.04–0.07).
* **State growth (t=1000→4000):** all linear recursive learners, `rolling`, `frozen`, PA, `reset_*`, `bank_*` are bounded (≤1.11×). `batch` (expanding buffer) ×4.3, HT/HAT ×4–6, ARF ×5.1, ADWIN-bagging ×3.9 — unbounded unless `max_size`/`max_depth` are configured (River exposes these; not used here, UNKNOWN whether bounding them preserves accuracy).
