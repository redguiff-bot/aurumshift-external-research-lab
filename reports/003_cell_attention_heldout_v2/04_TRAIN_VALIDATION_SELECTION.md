# 04 — Train / validation selection

Code: `bench/v2/src/tune.py`; raw per-run results: `bench/v2/results/tuning/{B,C,C2,D}_raw.json`; chosen parameters: `bench/v2/configs/selected_{B,C,C2,D}.json` (committed in `3328e4d`, **before** the held-out run; their sha256 are in `results/heldout/params_lock.json`).
Only TRAIN (`T1–T4`, seeds 1000–1004, 20 runs/config) and VALIDATION (`V1–V3`, seeds 2000–2004, 15 runs/config for the top-3) scenarios were used. `tune.py` imports only the dev generator (AST-tested). **Policy A was not tuned** (fixed operator constants); it appears below only as a reference value of the objective.

## 1. Objective and rule (pre-registered, 01 §6)

`J = info_ratio − 1.0·starvation_rate − 0.5·stale_rate − 0.5·max(silent_excess,0) − 0.25·max(lowinfo_excess,0)`; top-3 by TRAIN J → best VALIDATION J (ties within 0.005 → nearest the grid centre). Search spaces exactly as in `configs/protocol.json`: B 45 configs (γ × S × M); C 21 (River algo × parameters); C2 27 (guard S × M on the 3 best C configs); D 30 (VW algo × exploration × learning rate × group feature on/off).

## 2. Results

### Policy B: 45 configurations, errors 0

Chosen: `B|g0.9995|S25|M4` — spec `{"kind": "B", "gamma": 0.9995, "S": 25, "M": 4}`; TRAIN J = 0.692, VALIDATION J = 0.632 (generalisation gap +0.059). References on the same objective — A: train 0.526 / val 0.453; round-robin: train 0.527 / val 0.458.

| top-3 by TRAIN J | TRAIN J | VALIDATION J |
|---|---|---|
| `B|g0.9995|S25|M4` | 0.692 | 0.632 |
| `B|g0.9995|S25|M16` | 0.692 | 0.632 |
| `B|g0.998|S25|M4` | 0.680 | 0.608 |

TRAIN J across the whole grid: min 0.418, median 0.588, max 0.692; configs with TRAIN J ≥ round-robin (0.527): 35/45.

### Policy C: 21 configurations, errors 0

Chosen: `C|eps_ew|f0.1|e0.2` — spec `{"kind": "C", "algo": "eps_ew", "fading": 0.1, "eps": 0.2}`; TRAIN J = 0.561, VALIDATION J = 0.514 (generalisation gap +0.047). References on the same objective — A: train 0.526 / val 0.453; round-robin: train 0.527 / val 0.458.

| top-3 by TRAIN J | TRAIN J | VALIDATION J |
|---|---|---|
| `C|eps_ew|f0.3|e0.2` | 0.580 | 0.511 |
| `C|eps_ew|f0.1|e0.2` | 0.561 | 0.514 |
| `C|eps_ew|f0.05|e0.2` | 0.530 | 0.492 |

TRAIN J across the whole grid: min 0.018, median 0.355, max 0.580; configs with TRAIN J ≥ round-robin (0.527): 3/21.

### Policy C2: 27 configurations, errors 0

Chosen: `C2|eps_ew|f0.1|e0.2|S50|M4` — spec `{"kind": "C2", "algo": "eps_ew", "fading": 0.1, "eps": 0.2, "guard": [50, 4]}`; TRAIN J = 0.742, VALIDATION J = 0.750 (generalisation gap -0.008). References on the same objective — A: train 0.526 / val 0.453; round-robin: train 0.527 / val 0.458.

| top-3 by TRAIN J | TRAIN J | VALIDATION J |
|---|---|---|
| `C2|eps_ew|f0.1|e0.2|S50|M4` | 0.742 | 0.750 |
| `C2|eps_ew|f0.1|e0.2|S50|M16` | 0.742 | 0.750 |
| `C2|eps_ew|f0.1|e0.2|S25|M4` | 0.734 | 0.691 |

TRAIN J across the whole grid: min 0.583, median 0.711, max 0.742; configs with TRAIN J ≥ round-robin (0.527): 27/27.

### Policy D: 30 configurations, errors 0

Chosen: `D|eps|e0.2|lr0.05|grp0` — spec `{"kind": "D", "algo": "eps", "expl": 0.2, "lr": 0.05, "use_group": false}`; TRAIN J = 0.645, VALIDATION J = 0.573 (generalisation gap +0.072). References on the same objective — A: train 0.526 / val 0.453; round-robin: train 0.527 / val 0.458.

| top-3 by TRAIN J | TRAIN J | VALIDATION J |
|---|---|---|
| `D|eps|e0.2|lr0.05|grp0` | 0.645 | 0.573 |
| `D|eps|e0.2|lr0.05|grp1` | 0.636 | 0.567 |
| `D|eps|e0.2|lr0.2|grp0` | 0.632 | 0.573 |

TRAIN J across the whole grid: min 0.330, median 0.557, max 0.645; configs with TRAIN J ≥ round-robin (0.527): 22/30.

## 3. Reading (labels: OBSERVED = seen in these dev runs; INFERENCE = my reading)

* **All chosen configurations lie at or near the border of the pre-registered grid** (OBSERVED): B at `γ = 0.9995` (max) and `S = 25` (min); C, C2-River part and D at `ε = 0.2` (max). INFERENCE: the objective `J` (which charges starvation and staleness heavily) pulls every policy toward *more uniform coverage*; the frozen grids may therefore truncate the region a wider search would prefer. Widening a grid using TRAIN/VALIDATION data would have been legitimate, but the protocol was pre-registered and the operator asked for robustness, not score maximisation; boundary selection is instead **carried as a caveat** and probed descriptively in 07 (which includes two beyond-grid guard settings, `S = 10` and `S = 200`, for B).
* **B**: 35 of 45 configs beat round-robin on `J`; the worst have no guard (`M=1`, small γ). The top-3 are near-ties (`M4` and `M16` are *identical* on dev: the backoff cap never binds there). Generalisation gap +0.059.
* **C (River as shipped)**: only **3 of 21** configurations reach round-robin's `J`; UCB variants are far below (worst 0.018). The only region that works is ε-greedy with **ε = 0.2 (grid maximum)**, i.e. mostly random exploration — River's reward-following part contributes little. This reproduces V1's PROVEN finding that shipped reward-following River policies starve, now on independent scenarios (OBSERVED on dev; not yet a held-out claim).
* **C2 (River + guard)**: 27/27 configs beat round-robin; range narrow (0.583–0.742) ⇒ dev-robust; validation ≥ train (−0.008 gap). Best dev `J` of all policies. This does **not** predict held-out behaviour (see 05/06: return from dormancy).
* **D (VW)**: 22/30 beat round-robin; **the group-feature variants did not win** (`grp0` beat `grp1` by 0.009 on TRAIN; validation tied) ⇒ on dev, feature sharing brought no measurable advantage. The chosen ε-greedy `ε = 0.2` again sits at the grid edge. Largest generalisation gap (+0.072).
* **A vs round-robin**: `J` = 0.526 vs 0.527 (train), 0.453 vs 0.458 (validation) ⇒ **indistinguishable on the dev objective** (OBSERVED); this foreshadows the held-out result.
* No run failed (0 errors in 4×(45|21|27|30) configs).
