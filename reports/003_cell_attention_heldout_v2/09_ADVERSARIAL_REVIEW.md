# 09 — Adversarial review

Goal (mission §13): try to **falsify** the apparent winner. Method: (1) re-read the held-out numbers for weaknesses (05, 06); (2) write **post-hoc** adversarial scenarios *after* Phase B (`src/scenarios_adv.py`, `X1–X5`, seeds 4000–4019, 20 seeds, frozen parameters, never used for selection, generator committed after `results/heldout`); (3) one targeted diagnostic on B's backoff (06 P4). These scenarios are **not held-out scenarios** and **not part of any verdict tally**; they are attack probes. Labels: OBSERVED in this model.

Apparent winner: **`B` (D-UCB + guard)** — non-dominated, no starvation, no silent capture, fast on new cells, +0.141 information over A in 200/200 scenario-seeds. Runner-up on information: `C2`.

## 1. Attack scenarios

| # | Attack | Target weakness |
|---|---|---|
| X1 | half the fleet (60/120 cells) permanently silent from τ=40 | perpetual re-visit loop of the guard (V1 04 P4); A's floor/weights on silent cells |
| X2 | 30 cells flip between value 0.75 and 0.05 every 40 cycles | discount vs frequent regime change; lock-in |
| X3 | **no information gradient** (all 120 cells `P=0.15`) | churn/concentration chasing noise; information metric degenerates (oracle = any policy ⇒ `info_ratio = 1.000` for all — a *degenerate* result, not a success) |
| X4 | very high churn: 20 births and 20 retirements every 10 cycles (cells live ≈ 40 cycles) | guard interval `S` longer than cell lifetime; new-cell latency |
| X5 | the 30 best cells return nothing on 50 % of attempts (independent per attempt) | backoff mistaking flaky-but-valuable cells for dead ones |

## 2. Results (frozen parameters; 20 seeds; mean ± sd [worst run])

**info_ratio** (mean ± sd over 20 seeds; worst run in brackets)

| scenario | A | B | C | D | C2 | R |
|---|---|---|---|---|---|---|
| X1_PERMANENT_SILENCE | 0.304 ± 0.028 [0.247] | 0.694 ± 0.025 [0.635] | 0.216 ± 0.041 [0.145] | 0.547 ± 0.097 [0.385] | 0.807 ± 0.017 [0.757] | 0.336 ± 0.031 [0.274] |
| X2_OSCILLATING_REGIME | 0.555 ± 0.045 [0.474] | 0.683 ± 0.030 [0.634] | 0.781 ± 0.030 [0.726] | 0.703 ± 0.038 [0.607] | 0.759 ± 0.033 [0.692] | 0.556 ± 0.047 [0.467] |
| X3_NO_SIGNAL | 1.000 ± 0.000 [1.000] | 1.000 ± 0.000 [1.000] | 1.000 ± 0.000 [1.000] | 1.000 ± 0.000 [1.000] | 1.000 ± 0.000 [1.000] | 1.000 ± 0.000 [1.000] |
| X4_HIGH_CHURN | 0.574 ± 0.036 [0.509] | 0.622 ± 0.028 [0.571] | 0.681 ± 0.038 [0.610] | 0.693 ± 0.024 [0.654] | 0.679 ± 0.036 [0.615] | 0.575 ± 0.036 [0.512] |
| X5_FLAKY_HIGH_VALUE | 0.486 ± 0.032 [0.423] | 0.557 ± 0.039 [0.491] | 0.529 ± 0.023 [0.486] | 0.526 ± 0.019 [0.495] | 0.617 ± 0.038 [0.549] | 0.483 ± 0.036 [0.415] |

**starvation_rate** (mean ± sd over 20 seeds; worst run in brackets)

| scenario | A | B | C | D | C2 | R |
|---|---|---|---|---|---|---|
| X1_PERMANENT_SILENCE | 0.000 ± 0.000 [0.000] | 0.066 ± 0.000 [0.066] | 0.172 ± 0.013 [0.199] | 0.091 ± 0.025 [0.136] | 0.167 ± 0.003 [0.172] | 0.000 ± 0.000 [0.000] |
| X2_OSCILLATING_REGIME | 0.000 ± 0.000 [0.000] | 0.000 ± 0.000 [0.000] | 0.138 ± 0.016 [0.164] | 0.061 ± 0.031 [0.110] | 0.000 ± 0.000 [0.000] | 0.000 ± 0.000 [0.000] |
| X3_NO_SIGNAL | 0.000 ± 0.000 [0.000] | 0.000 ± 0.000 [0.000] | 0.121 ± 0.011 [0.145] | 0.021 ± 0.016 [0.055] | 0.000 ± 0.000 [0.000] | 0.000 ± 0.000 [0.000] |
| X4_HIGH_CHURN | 0.000 ± 0.000 [0.000] | 0.000 ± 0.000 [0.000] | 0.006 ± 0.028 [0.125] | 0.003 ± 0.014 [0.062] | 0.000 ± 0.000 [0.000] | 0.000 ± 0.000 [0.000] |
| X5_FLAKY_HIGH_VALUE | 0.000 ± 0.000 [0.000] | 0.022 ± 0.002 [0.025] | 0.141 ± 0.012 [0.166] | 0.079 ± 0.025 [0.135] | 0.073 ± 0.006 [0.082] | 0.000 ± 0.000 [0.000] |

**coverage_W** (mean ± sd over 20 seeds; worst run in brackets)

| scenario | A | B | C | D | C2 | R |
|---|---|---|---|---|---|---|
| X1_PERMANENT_SILENCE | 1.000 ± 0.000 [1.000] | 0.812 ± 0.000 [0.812] | 0.567 ± 0.015 [0.596] | 0.718 ± 0.053 [0.805] | 0.626 ± 0.007 [0.639] | 1.000 ± 0.000 [1.000] |
| X2_OSCILLATING_REGIME | 1.000 ± 0.000 [1.000] | 1.000 ± 0.000 [1.000] | 0.618 ± 0.024 [0.654] | 0.787 ± 0.065 [0.892] | 0.860 ± 0.010 [0.882] | 1.000 ± 0.000 [1.000] |
| X3_NO_SIGNAL | 1.000 ± 0.000 [1.000] | 1.000 ± 0.000 [1.000] | 0.647 ± 0.018 [0.684] | 0.906 ± 0.055 [0.994] | 0.863 ± 0.012 [0.880] | 1.000 ± 0.000 [1.000] |
| X4_HIGH_CHURN | 1.000 ± 0.000 [1.000] | 1.000 ± 0.000 [1.000] | 0.844 ± 0.042 [0.902] | 0.957 ± 0.021 [1.000] | 0.857 ± 0.040 [0.927] | 1.000 ± 0.000 [1.000] |
| X5_FLAKY_HIGH_VALUE | 1.000 ± 0.000 [1.000] | 0.908 ± 0.003 [0.916] | 0.608 ± 0.016 [0.641] | 0.739 ± 0.068 [0.849] | 0.763 ± 0.012 [0.781] | 1.000 ± 0.000 [1.000] |

**max_starvation_duration** (mean ± sd over 20 seeds; worst run in brackets)

| scenario | A | B | C | D | C2 | R |
|---|---|---|---|---|---|---|
| X1_PERMANENT_SILENCE | 50 ± 5 [60] | 100 ± 0 [100] | 300 ± 29 [343] | 259 ± 38 [342] | 178 ± 0 [178] | 27 ± 3 [33] |
| X2_OSCILLATING_REGIME | 51 ± 7 [60] | 37 ± 6 [52] | 293 ± 34 [364] | 245 ± 49 [324] | 50 ± 1 [52] | 29 ± 4 [36] |
| X3_NO_SIGNAL | 54 ± 4 [60] | 37 ± 3 [41] | 291 ± 31 [329] | 169 ± 48 [277] | 50 ± 0 [51] | 29 ± 3 [34] |
| X4_HIGH_CHURN | 28 ± 8 [52] | 25 ± 0 [26] | 64 ± 8 [91] | 62 ± 10 [85] | 51 ± 0 [51] | 8 ± 1 [10] |
| X5_FLAKY_HIGH_VALUE | 52 ± 5 [60] | 100 ± 0 [100] | 286 ± 28 [328] | 239 ± 38 [313] | 200 ± 0 [200] | 28 ± 3 [32] |

**stale_rate** (mean ± sd over 20 seeds; worst run in brackets)

| scenario | A | B | C | D | C2 | R |
|---|---|---|---|---|---|---|
| X1_PERMANENT_SILENCE | 0.000 ± 0.000 [0.000] | 0.000 ± 0.000 [0.000] | 0.275 ± 0.024 [0.326] | 0.109 ± 0.044 [0.201] | 0.000 ± 0.000 [0.000] | 0.000 ± 0.000 [0.000] |
| X2_OSCILLATING_REGIME | 0.000 ± 0.000 [0.000] | 0.000 ± 0.000 [0.000] | 0.214 ± 0.018 [0.244] | 0.104 ± 0.046 [0.182] | 0.000 ± 0.000 [0.000] | 0.000 ± 0.000 [0.000] |
| X3_NO_SIGNAL | 0.000 ± 0.000 [0.000] | 0.000 ± 0.000 [0.000] | 0.191 ± 0.014 [0.215] | 0.040 ± 0.027 [0.083] | 0.000 ± 0.000 [0.000] | 0.000 ± 0.000 [0.000] |
| X4_HIGH_CHURN | 0.000 ± 0.000 [0.000] | 0.000 ± 0.000 [0.000] | 0.000 ± 0.000 [0.002] | 0.000 ± 0.000 [0.001] | 0.000 ± 0.000 [0.000] | 0.000 ± 0.000 [0.000] |
| X5_FLAKY_HIGH_VALUE | 0.001 ± 0.000 [0.002] | 0.070 ± 0.004 [0.078] | 0.242 ± 0.016 [0.277] | 0.149 ± 0.041 [0.233] | 0.091 ± 0.005 [0.097] | 0.004 ± 0.002 [0.008] |

**silent_share** (mean ± sd over 20 seeds; worst run in brackets)

| scenario | A | B | C | D | C2 | R |
|---|---|---|---|---|---|---|
| X1_PERMANENT_SILENCE | 0.492 ± 0.005 [0.499] | 0.075 ± 0.000 [0.075] | 0.724 ± 0.039 [0.791] | 0.313 ± 0.099 [0.499] | 0.037 ± 0.000 [0.037] | 0.437 ± 0.001 [0.438] |
| X2_OSCILLATING_REGIME | 0.000 ± 0.000 [0.000] | 0.000 ± 0.000 [0.000] | 0.000 ± 0.000 [0.000] | 0.000 ± 0.000 [0.000] | 0.000 ± 0.000 [0.000] | 0.000 ± 0.000 [0.000] |
| X3_NO_SIGNAL | 0.000 ± 0.000 [0.000] | 0.000 ± 0.000 [0.000] | 0.000 ± 0.000 [0.000] | 0.000 ± 0.000 [0.000] | 0.000 ± 0.000 [0.000] | 0.000 ± 0.000 [0.000] |
| X4_HIGH_CHURN | 0.000 ± 0.000 [0.000] | 0.000 ± 0.000 [0.000] | 0.000 ± 0.000 [0.000] | 0.000 ± 0.000 [0.000] | 0.000 ± 0.000 [0.000] | 0.000 ± 0.000 [0.000] |
| X5_FLAKY_HIGH_VALUE | 0.152 ± 0.005 [0.160] | 0.046 ± 0.001 [0.048] | 0.356 ± 0.022 [0.391] | 0.296 ± 0.035 [0.360] | 0.027 ± 0.001 [0.028] | 0.127 ± 0.005 [0.137] |

**silent_baseline** (mean ± sd over 20 seeds; worst run in brackets)

| scenario | A | B | C | D | C2 | R |
|---|---|---|---|---|---|---|
| X1_PERMANENT_SILENCE | 0.438 ± 0.000 [0.438] | 0.438 ± 0.000 [0.438] | 0.438 ± 0.000 [0.438] | 0.438 ± 0.000 [0.438] | 0.438 ± 0.000 [0.438] | 0.438 ± 0.000 [0.438] |
| X2_OSCILLATING_REGIME | 0.000 ± 0.000 [0.000] | 0.000 ± 0.000 [0.000] | 0.000 ± 0.000 [0.000] | 0.000 ± 0.000 [0.000] | 0.000 ± 0.000 [0.000] | 0.000 ± 0.000 [0.000] |
| X3_NO_SIGNAL | 0.000 ± 0.000 [0.000] | 0.000 ± 0.000 [0.000] | 0.000 ± 0.000 [0.000] | 0.000 ± 0.000 [0.000] | 0.000 ± 0.000 [0.000] | 0.000 ± 0.000 [0.000] |
| X4_HIGH_CHURN | 0.000 ± 0.000 [0.000] | 0.000 ± 0.000 [0.000] | 0.000 ± 0.000 [0.000] | 0.000 ± 0.000 [0.000] | 0.000 ± 0.000 [0.000] | 0.000 ± 0.000 [0.000] |
| X5_FLAKY_HIGH_VALUE | 0.125 ± 0.001 [0.129] | 0.125 ± 0.001 [0.129] | 0.125 ± 0.001 [0.129] | 0.125 ± 0.001 [0.129] | 0.125 ± 0.001 [0.129] | 0.125 ± 0.001 [0.129] |

**gini_attention_rate** (mean ± sd over 20 seeds; worst run in brackets)

| scenario | A | B | C | D | C2 | R |
|---|---|---|---|---|---|---|
| X1_PERMANENT_SILENCE | 0.066 ± 0.005 [0.077] | 0.526 ± 0.021 [0.570] | 0.741 ± 0.009 [0.760] | 0.560 ± 0.087 [0.713] | 0.687 ± 0.017 [0.712] | 0.008 ± 0.000 [0.008] |
| X2_OSCILLATING_REGIME | 0.042 ± 0.008 [0.059] | 0.281 ± 0.017 [0.306] | 0.649 ± 0.027 [0.698] | 0.465 ± 0.089 [0.577] | 0.552 ± 0.019 [0.593] | 0.008 ± 0.000 [0.008] |
| X3_NO_SIGNAL | 0.076 ± 0.004 [0.084] | 0.119 ± 0.006 [0.128] | 0.527 ± 0.020 [0.561] | 0.202 ± 0.050 [0.281] | 0.432 ± 0.018 [0.467] | 0.008 ± 0.000 [0.008] |
| X4_HIGH_CHURN | 0.086 ± 0.002 [0.093] | 0.247 ± 0.008 [0.262] | 0.726 ± 0.010 [0.748] | 0.530 ± 0.053 [0.602] | 0.724 ± 0.010 [0.747] | 0.044 ± 0.000 [0.045] |
| X5_FLAKY_HIGH_VALUE | 0.082 ± 0.006 [0.095] | 0.342 ± 0.016 [0.373] | 0.693 ± 0.015 [0.716] | 0.516 ± 0.070 [0.649] | 0.580 ± 0.021 [0.610] | 0.008 ± 0.000 [0.008] |

## 3. Per-policy adversarial verdicts

Each entry: `BEST_CASE` / `NORMAL_CASE` / `WORST_CASE` are measured (held-out + adversarial), `KNOWN_FAILURE_MODE` was observed, `UNKNOWN_FAILURE_MODE` is what remains untested.

### B — D-UCB + guard (apparent winner; falsification attempt: **not falsified as a safe balanced policy; falsified as "best on information"**)
* **BEST_CASE**: S10 (`info_ratio` 0.617 vs A 0.546 and first attempt at 0 cycles median), S2 (0.672; adaptation 54 cycles), X2 (0.683 with starvation 0), S7 (0.599 vs A 0.324).
* **NORMAL_CASE**: pooled held-out `info_ratio` 0.649 (A 0.508), starvation 0.005, stale 0.010, silent excess −0.025, coverage 0.984, adaptation ≈ 96 cycles; 20/20 seeds better than A in every scenario.
* **WORST_CASE** (measured): X1 permanent silence — coverage 0.812, starvation 0.066, max starvation 100 cycles (the backoff parks half the fleet: but information stays 0.694 vs round-robin 0.336); S5/S9 — starvation 0.021/0.028; X5 — information 0.557, only +0.07 over round-robin (0.483): the backoff under-serves flaky valuable cells (silent share 0.046 vs 0.125 baseline; stale 0.070). Worst single held-out run: starvation 0.028, max starvation 109, min `info_ratio` 0.506.
* **KNOWN_FAILURE_MODE** (OBSERVED): (i) **without backoff (`M=1`) it is captured by silent cells** (X1: 67 % of attention, information 0.209 < round-robin); (ii) **return-from-dormancy latency ≤ `S·M`, phase-dependent** (S9 ≈ 60 cycles, up to censored for other `S`); (iii) **boundary-selected parameters**: `γ`=0.9995 and `S`=25 are at the edge of the searched grid; with `S=25` and a cap of `K/2` forced picks the guard is close to "half round-robin" — which is *why* starvation is low; the benefit over A comes from the other half (UCB). (iv) worse rare-event discovery than uniform (S8: 0.51 vs 0.75).
* **UNKNOWN_FAILURE_MODE**: behaviour with > 250 cells or K/N very small (guard cap `K/2` may then not cover the fleet within `S`); heavy-tailed or non-stationary noise levels; delayed feedback beyond batching; correlated silence with a value change at the same instant; interaction with a real lifecycle model; real evidence latency. A guard interval fixed in cycles has no meaning until the real cycle length is known.

### A — operator-supplied lifecycle-weighted reference
* **BEST_CASE**: perfect invariants — zero starvation in 1 200 held-out runs and all 100 adversarial runs, zero stale cells (max 0.017), attention conservation to 7e-15, no capture, deterministic; X4 first attempt 1 cycle.
* **NORMAL_CASE**: ≈ round-robin (information 0.508 vs 0.507; adaptation censored; silent excess +0.009).
* **WORST_CASE** (measured): X1 permanent silence — `info_ratio` 0.304 **below** round-robin (0.336) because silent cells keep their lifecycle weights (PROVEN/PROMISING) and the `data_gap` floor adds attention (silent excess +0.054); S7 low-information — 0.324 with 55 % of attention on cells that carry almost no information (uniform 60 %); S9 return — never recovers (censored).
* **KNOWN_FAILURE_MODE**: no adaptation with the tested constants and classifiers (07: 7 variants, none adaptive); the classifier is V2-defined — a different local classifier could change this.
* **UNKNOWN_FAILURE_MODE**: behaviour with a state model that reacts within fewer than 20 evidence events; the true private contract's classifier; interaction with real RETIRED decisions (here explicit and random in S10).

### C — River as shipped
* **BEST_CASE**: highest information in six of ten held-out scenarios (S1, S2, S3, S6, S7, S8: 0.753–0.825) and in X2 (0.781), and the fastest return in S9 (9 cycles).
* **NORMAL_CASE**: starvation 0.147, stale 0.23, coverage 0.60, 5–13 % of new cells unseen.
* **WORST_CASE** (measured): X1 — `info_ratio` **0.216 (below round-robin 0.336)**, silent excess +0.287, starvation 0.172, max starvation 300; S9 — 39.5 % of attention on silent cells; worst run starvation 0.274, max starvation 388.
* **KNOWN_FAILURE_MODE**: structural starvation and silent capture (V1 PROVEN in-sample; here OBSERVED out-of-sample); brittle to parameters (07: BRITTLE, no configuration free of starvation).
* **UNKNOWN_FAILURE_MODE**: River's drift detectors as restart triggers (V1 PARK, not tested here).

### C2 — River + the shared guard (composition diagnostic)
* **BEST_CASE**: best information overall (pooled 0.757; worst run 0.657; X1 0.807, X5 0.617) with starvation ≤ 0.077 in every run.
* **NORMAL_CASE**: starvation 0.015, stale 0.023, coverage 0.83, but median new-cell delay 35 cycles.
* **WORST_CASE** (measured): S9 — target share 0.000, censored in 100 % of runs; X1 — starvation 0.167, coverage 0.626, max starvation 178; S10 — 7.8 % of new cells unseen; X5 — starvation 0.073.
* **KNOWN_FAILURE_MODE**: cannot notice returns inside its backoff window; slow cold start because River's ε-greedy only explores at random.
* **UNKNOWN_FAILURE_MODE**: guard + River with other estimators (UCB variants collapsed on dev); larger fleets.

### D — VW shared-feature policy
* **BEST_CASE**: strong information (0.728) with a fast new-cell median (14 cycles; 6 in S10), no silent capture, recovers from dormancy (32 cycles).
* **NORMAL_CASE**: starvation 0.073, stale 0.125, coverage 0.76.
* **WORST_CASE** (measured): worst run starvation 0.174, max starvation 360; X5 silent excess +0.171 (captured by flaky cells); X1 starvation 0.091.
* **KNOWN_FAILURE_MODE**: learning-rate/exploration dominated behaviour (07: BRITTLE); no evidence that feature sharing helps (group feature not selected; effects within noise); ≈ 100× slower per run.
* **UNKNOWN_FAILURE_MODE**: richer features (regime descriptors that truly co-move), champion/challenger `--epsilon_decay` (not run), squarecb with wider `gamma_scale`, cross-machine determinism of VW.

## 4. What the attacks changed and did not change

* Did **not** change the ranking of `B` as the best balanced policy: nothing in X1–X5 produced a catastrophic failure of B with its frozen backoff.
* **Did** show that B's safety comes from a component (backoff) that V1 had not tested, that its `S`/`γ` were selected at grid edges, and that `C2` beats B on information in all 10 held-out scenarios and in X1, X2, X4, X5 (X3 is degenerate) at the price of new-cell latency and return recovery — so "B wins" is false; "B is the safest adaptive candidate" is what survives.
* X3 exposes a metric limitation: `info_ratio` is degenerate when the oracle has nothing to find. Not a policy result.
* Post-hoc status: the probes were designed after seeing held-out results; they can reveal weaknesses but cannot certify strength.
