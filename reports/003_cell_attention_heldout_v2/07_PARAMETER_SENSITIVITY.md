# 07 — Parameter sensitivity (descriptive, bounded)

Purpose (mission §11): determine whether behaviour is ROBUST / SENSITIVE / BRITTLE — **not** to maximise a score. Runs: `src/sensitivity.py` on the held-out generators, **5 seeds (3000–3004)** per configuration × 10 scenarios (A: 7 configs, B: 19, C: 11, C2: 11, D: 12; 0 errors; raw: `results/sensitivity/*.json`). These runs are **descriptive and post-selection**: the primary held-out comparison (05) uses the frozen parameters, and nothing here fed back into any selected parameter (no re-selection was made; the frozen files are hash-locked before the held-out run). Because they use held-out scenarios, they must not be used to *choose* parameters — doing so would be `INVALID_FOR_COMPARISON`.

## 1. Classification rule (defined in `src/sens_summary.py` before its first execution and applied uniformly; not part of the pre-registered `protocol.json`)

For each policy, scenario-averaged `info_ratio`, `starvation_rate`, `stale_rate` and (over S4/S5/S9) `silent_excess` are computed per configuration. An alternative configuration is *acceptable* if, relative to the **frozen** configuration, it is not worse by more than **2× the practical threshold** on each of the four (info ≥ −0.06, starvation ≤ +0.04, stale ≤ +0.06, silent excess ≤ +0.06). Fraction acceptable among alternatives (beyond-grid rows excluded): **≥ 0.75 ROBUST · 0.35–0.75 SENSITIVE · < 0.35 BRITTLE**. Thresholds of this classification are a V2 convention (INFERENCE-level, not tuned); they are stated so that a reader can re-classify.

| Policy | Alternatives | Acceptable fraction | Class | Range of scenario-avg `info_ratio` | Range `starvation_rate` | Range `stale_rate` | Range `silent_excess` (S4/S5/S9) |
|---|---|---|---|---|---|---|---|
| A | 6 | 0.83 | **ROBUST** | 0.505–0.521 | 0.000–0.000 | 0.002–0.002 | +0.007–+0.097 |
| B | 16 | 0.69 | **SENSITIVE** | 0.578–0.685 | 0.000–0.084 | 0.004–0.090 | -0.088–+0.194 |
| C | 10 | 0.10 | **BRITTLE** | 0.591–0.779 | 0.134–0.390 | 0.158–0.462 | +0.066–+0.328 |
| C2 | 10 | 0.40 | **SENSITIVE** | 0.672–0.796 | 0.000–0.082 | 0.005–0.157 | -0.089–+0.100 |
| D | 11 | 0.27 | **BRITTLE** | 0.694–0.824 | 0.053–0.400 | 0.096–0.473 | -0.090–+0.023 |

## 2. Reading (OBSERVED in this model unless marked)

* **A — ROBUST, but trivially so**: none of floor 0 / 5 / 10 / 20 %, flat or steep weights, or the alternative classifier moves `info_ratio` (0.505–0.521), adaptation delay (187–197, censored) or staleness. Robustness here means *insensitivity*: A's behaviour ≈ round-robin is a structural property of "small weight spread + 5 % floor + evidence-derived states", not of the exact constants. The only visible knob is the floor: silent excess grows monotonically with it (+0.007 at 0 % → +0.097 at 20 %), i.e. the `data_gap` mark diverts attention to silent cells in proportion to the floor. INFERENCE: with the operator's fixed constants A cannot become adaptive; adaptivity would need a state model that reacts faster than `n_evidence ≥ 20` (a local design question, untested here).
* **B — SENSITIVE (0.69)**: three effects are visible. (i) **γ trades information for adaptation, monotonically**: information 0.578 (γ=0.98) → 0.685 (γ=0.9995) while adaptation delay improves from 170–197 to 67–105 (the V1 frontier, PROVEN in-sample there, reproduced out-of-sample here as OBSERVED). (ii) **The guard interval `S` trades coverage for information**: `S=25` keeps starvation ≈ 0.005 and coverage 0.984; `S=100` ⇒ starvation 0.028–0.056, coverage 0.84–0.96; beyond the grid `S=200` ⇒ 0.084 starvation, coverage 0.83 (the guard stops protecting), while `S=10` ⇒ starvation 0.000 but information falls to 0.617 (the guard eats more than half the budget). (iii) **The backoff is essential**: `M=1` ⇒ silent excess **+0.194** (vs −0.079) and adaptation unaffected; `M=4` vs `M=16` is indistinguishable in this benchmark. Within the pre-registered grid no configuration failed catastrophically (worst starvation 0.056), so B degrades gracefully; it is "sensitive" because information/coverage/adaptation move by more than 2× the practical thresholds across the grid.
* **C — BRITTLE (0.10)**: only 1 of 10 alternatives is acceptable; starvation is 0.134–0.390 and stale 0.158–0.462 across *all* 11 configurations (no configuration is starvation-free), and new-cell delay spans 1.5–129 cycles. River's reward-following cannot be tuned out of starvation (consistent with V1 03 §4: "structural, not a tuning issue"). The best information (0.779) is bought with the worst coverage.
* **C2 — SENSITIVE (0.40, borderline)**: every configuration keeps starvation ≤ 0.082 (C: 0.134–0.390), but return latency (P7) swings between 11 cycles and censored depending on the backoff phase (06), and stale rate reaches 0.157 for `S=100, M=16`. Its information gain stays high (0.672–0.796).
* **D — BRITTLE (0.27)**: starvation 0.053–0.400 and stale 0.096–0.473 across 12 configurations; the learning rate and exploration knob move behaviour between "nearly uniform" and "greedy and starving" (V1 04 V4 reported the same knob-dominated behaviour with id-only features). Including or excluding the group feature changes little (see the table). VW is ≈ 100× slower here, so sensitivity sweeps are also costlier.

## 3. Full tables (scenario-averaged; adapt_delay averaged over S2/S3/S9, new_ttfa over S1/S10; `policy_s` = policy seconds per run under 4-way parallel load)

### A — ROBUST (acceptable fraction 0.83 of 6 alternative configs; chosen `A|floor0.05`)

| config | info_ratio | starvation | stale | silent_excess | adapt_delay | new_ttfa | coverage | max_starv | policy_s |
|---|---|---|---|---|---|---|---|---|---|
| `A|altcls` | 0.505 | 0.000 | 0.002 | +0.028 | 197 | 3.5 | 1.000 | 49 | 0.0 |
| `A|floor0.0` | 0.521 | 0.000 | 0.002 | +0.007 | 197 | 3.5 | 1.000 | 56 | 0.0 |
| `A|floor0.05` **(chosen)** | 0.517 | 0.000 | 0.002 | +0.030 | 197 | 3.2 | 1.000 | 49 | 0.0 |
| `A|floor0.1` | 0.514 | 0.000 | 0.002 | +0.053 | 197 | 3.1 | 1.000 | 49 | 0.0 |
| `A|floor0.2` | 0.506 | 0.000 | 0.002 | +0.097 | 197 | 2.6 | 1.000 | 49 | 0.0 |
| `A|w_flat` | 0.512 | 0.000 | 0.002 | +0.023 | 197 | 3.4 | 1.000 | 49 | 0.0 |
| `A|w_steep` | 0.516 | 0.000 | 0.002 | +0.040 | 187 | 3.2 | 0.998 | 53 | 0.0 |

### B — SENSITIVE (acceptable fraction 0.69 of 16 alternative configs; chosen `B|g0.9995|S25|M4`)

| config | info_ratio | starvation | stale | silent_excess | adapt_delay | new_ttfa | coverage | max_starv | policy_s |
|---|---|---|---|---|---|---|---|---|---|
| `B|g0.98|S100|M4` | 0.584 | 0.028 | 0.022 | -0.088 | 170 | 1.5 | 0.956 | 99 | 0.0 |
| `B|g0.98|S25|M4` | 0.578 | 0.005 | 0.008 | -0.079 | 186 | 1.5 | 0.984 | 48 | 0.0 |
| `B|g0.98|S50|M4` | 0.578 | 0.017 | 0.022 | -0.082 | 197 | 1.5 | 0.960 | 76 | 0.0 |
| `B|g0.995|S100|M4` | 0.636 | 0.033 | 0.037 | -0.088 | 99 | 1.5 | 0.905 | 128 | 0.0 |
| `B|g0.995|S25|M4` | 0.623 | 0.005 | 0.009 | -0.079 | 108 | 1.5 | 0.984 | 49 | 0.0 |
| `B|g0.995|S50|M4` | 0.627 | 0.016 | 0.023 | -0.082 | 111 | 1.5 | 0.936 | 78 | 0.0 |
| `B|g0.998|S100|M4` | 0.666 | 0.043 | 0.056 | -0.088 | 75 | 1.5 | 0.864 | 130 | 0.0 |
| `B|g0.998|S25|M4` | 0.643 | 0.005 | 0.010 | -0.079 | 100 | 1.5 | 0.984 | 49 | 0.0 |
| `B|g0.998|S50|M4` | 0.653 | 0.016 | 0.023 | -0.082 | 99 | 1.5 | 0.917 | 78 | 0.0 |
| `B|g0.9995|S100|M4` | 0.685 | 0.056 | 0.071 | -0.088 | 67 | 1.5 | 0.835 | 130 | 0.0 |
| `B|g0.9995|S10|M4|BEYOND_GRID` | 0.617 | 0.000 | 0.008 | -0.063 | 124 | 3.0 | 0.998 | 42 | 0.0 |
| `B|g0.9995|S200|M4|BEYOND_GRID` | 0.678 | 0.084 | 0.090 | -0.088 | 96 | 1.5 | 0.834 | 206 | 0.0 |
| `B|g0.9995|S25|M1` | 0.596 | 0.000 | 0.004 | +0.194 | 89 | 1.6 | 1.000 | 34 | 0.0 |
| `B|g0.9995|S25|M16` | 0.651 | 0.006 | 0.012 | -0.079 | 116 | 1.6 | 0.981 | 52 | 0.0 |
| `B|g0.9995|S25|M4` **(chosen)** | 0.654 | 0.005 | 0.010 | -0.079 | 105 | 1.6 | 0.984 | 49 | 0.0 |
| `B|g0.9995|S50|M4` | 0.673 | 0.016 | 0.023 | -0.082 | 100 | 1.5 | 0.905 | 78 | 0.0 |
| `B|g0.99|S100|M4` | 0.608 | 0.030 | 0.026 | -0.088 | 128 | 1.5 | 0.934 | 116 | 0.0 |
| `B|g0.99|S25|M4` | 0.601 | 0.005 | 0.009 | -0.079 | 178 | 1.5 | 0.984 | 49 | 0.0 |
| `B|g0.99|S50|M4` | 0.602 | 0.016 | 0.023 | -0.082 | 146 | 1.5 | 0.946 | 78 | 0.0 |

### C — BRITTLE (acceptable fraction 0.10 of 10 alternative configs; chosen `C|eps_ew|f0.1|e0.2`)

| config | info_ratio | starvation | stale | silent_excess | adapt_delay | new_ttfa | coverage | max_starv | policy_s |
|---|---|---|---|---|---|---|---|---|---|
| `C|eps_ew|f0.05|e0.05` | 0.740 | 0.379 | 0.441 | +0.197 | 118 | 124.7 | 0.386 | 350 | 0.1 |
| `C|eps_ew|f0.05|e0.1` | 0.732 | 0.275 | 0.350 | +0.188 | 111 | 68.7 | 0.476 | 333 | 0.1 |
| `C|eps_ew|f0.05|e0.2` | 0.719 | 0.140 | 0.217 | +0.170 | 108 | 35.8 | 0.622 | 284 | 0.1 |
| `C|eps_ew|f0.1|e0.05` | 0.779 | 0.390 | 0.462 | +0.137 | 117 | 127.8 | 0.352 | 347 | 0.1 |
| `C|eps_ew|f0.1|e0.1` | 0.777 | 0.283 | 0.369 | +0.117 | 118 | 70.5 | 0.446 | 332 | 0.1 |
| `C|eps_ew|f0.1|e0.2` **(chosen)** | 0.756 | 0.150 | 0.233 | +0.106 | 107 | 36.0 | 0.595 | 285 | 0.1 |
| `C|eps_ew|f0.3|e0.05` | 0.767 | 0.356 | 0.435 | +0.136 | 94 | 129.1 | 0.369 | 345 | 0.1 |
| `C|eps_ew|f0.3|e0.1` | 0.762 | 0.266 | 0.355 | +0.107 | 80 | 67.8 | 0.453 | 328 | 0.1 |
| `C|eps_ew|f0.3|e0.2` | 0.745 | 0.149 | 0.233 | +0.066 | 69 | 36.0 | 0.596 | 278 | 0.1 |
| `C|ucb_ew|f0.1|d0.5` | 0.591 | 0.136 | 0.163 | +0.322 | 57 | 1.5 | 0.747 | 265 | 0.2 |
| `C|ucb_mean|d0.5` | 0.601 | 0.134 | 0.158 | +0.328 | 69 | 1.5 | 0.774 | 278 | 0.2 |

### C2 — SENSITIVE (acceptable fraction 0.40 of 10 alternative configs; chosen `C2|S50|M4`)

| config | info_ratio | starvation | stale | silent_excess | adapt_delay | new_ttfa | coverage | max_starv | policy_s |
|---|---|---|---|---|---|---|---|---|---|
| `C2|S100|M1` | 0.750 | 0.064 | 0.155 | +0.100 | 105 | 36.0 | 0.660 | 101 | 0.1 |
| `C2|S100|M16` | 0.796 | 0.082 | 0.157 | -0.089 | 106 | 36.0 | 0.652 | 131 | 0.1 |
| `C2|S100|M4` | 0.796 | 0.082 | 0.157 | -0.089 | 106 | 36.0 | 0.652 | 131 | 0.1 |
| `C2|S25|M1` | 0.672 | 0.000 | 0.005 | +0.067 | 120 | 27.1 | 1.000 | 35 | 0.1 |
| `C2|S25|M16` | 0.706 | 0.006 | 0.012 | -0.079 | 147 | 27.1 | 0.982 | 54 | 0.1 |
| `C2|S25|M4` | 0.708 | 0.005 | 0.010 | -0.079 | 141 | 27.1 | 0.984 | 50 | 0.1 |
| `C2|S50|M1` | 0.731 | 0.000 | 0.007 | +0.080 | 111 | 36.4 | 0.851 | 51 | 0.1 |
| `C2|S50|M16` | 0.767 | 0.014 | 0.022 | -0.083 | 138 | 36.4 | 0.829 | 79 | 0.1 |
| `C2|S50|M4` **(chosen)** | 0.767 | 0.014 | 0.022 | -0.083 | 138 | 36.4 | 0.829 | 79 | 0.1 |
| `C2|S50|M4|e0.05` | 0.783 | 0.014 | 0.023 | -0.083 | 129 | 53.5 | 0.783 | 80 | 0.1 |
| `C2|S50|M4|e0.1` | 0.782 | 0.014 | 0.022 | -0.083 | 143 | 47.2 | 0.796 | 80 | 0.1 |

### D — BRITTLE (acceptable fraction 0.27 of 11 alternative configs; chosen `D|eps|lr0.05|x0.2|grp0`)

| config | info_ratio | starvation | stale | silent_excess | adapt_delay | new_ttfa | coverage | max_starv | policy_s |
|---|---|---|---|---|---|---|---|---|---|
| `D|eps|lr0.01|x0.05|grp0` | 0.801 | 0.362 | 0.436 | -0.089 | 155 | 49.6 | 0.399 | 327 | 3.7 |
| `D|eps|lr0.01|x0.05|grp1` | 0.824 | 0.400 | 0.473 | -0.090 | 174 | 55.9 | 0.348 | 342 | 3.7 |
| `D|eps|lr0.01|x0.2|grp0` | 0.793 | 0.130 | 0.203 | -0.075 | 140 | 13.5 | 0.641 | 270 | 3.7 |
| `D|eps|lr0.01|x0.2|grp1` | 0.793 | 0.141 | 0.220 | -0.074 | 142 | 17.4 | 0.620 | 286 | 3.7 |
| `D|eps|lr0.05|x0.05|grp0` | 0.747 | 0.221 | 0.285 | -0.027 | 136 | 35.2 | 0.576 | 298 | 3.7 |
| `D|eps|lr0.05|x0.05|grp1` | 0.761 | 0.259 | 0.325 | -0.049 | 141 | 18.9 | 0.528 | 311 | 3.7 |
| `D|eps|lr0.05|x0.2|grp0` **(chosen)** | 0.741 | 0.074 | 0.127 | -0.030 | 107 | 13.2 | 0.760 | 238 | 3.7 |
| `D|eps|lr0.05|x0.2|grp1` | 0.737 | 0.083 | 0.140 | -0.044 | 135 | 9.0 | 0.741 | 245 | 3.7 |
| `D|eps|lr0.2|x0.05|grp0` | 0.716 | 0.178 | 0.238 | -0.027 | 115 | 33.0 | 0.631 | 282 | 3.6 |
| `D|eps|lr0.2|x0.05|grp1` | 0.707 | 0.191 | 0.251 | +0.003 | 148 | 15.2 | 0.623 | 310 | 3.7 |
| `D|eps|lr0.2|x0.2|grp0` | 0.694 | 0.053 | 0.096 | +0.014 | 98 | 14.9 | 0.807 | 212 | 3.6 |
| `D|eps|lr0.2|x0.2|grp1` | 0.696 | 0.066 | 0.115 | +0.023 | 86 | 11.9 | 0.779 | 236 | 3.6 |
