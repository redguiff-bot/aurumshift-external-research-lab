# 03 — Baselines and controls

Mandatory controls (all implemented in `bench/capacity_v1/py/policies.py`, all run on every scenario/seed/cap, held-out results in the table below):

| ID | Class | Rule |
|---|---|---|
| A | `FIFO` | admit the oldest pending opportunities first, no filter (admits negative-value opps) |
| B | `ROUND_ROBIN` | rotate a pointer over instruments, take each instrument's oldest opp |
| C | `RANDOM_SEEDED` | uniform random among pending, fixed seed (`12345 + world seed`) |
| D | `EQUAL_QUOTA` | least-admitted-instrument-first (equal opportunity), ties FIFO |
| E | `OLDEST_SLOT` | FIFO admission; when full, force-close the oldest position (held ≥ 12 h, tuned) to admit the oldest waiting opp — "turnover-neutral" churn control |

Added controls (not in the mission list, added to separate effects):
* `FIFO_NETPOS` — FIFO restricted to opps whose estimated net edge (score − cost) is positive. Separates "filtering out negative-EV opps" from "ranking".
* `RANK_SCORE_RAW`, `RANK_NET` — simplest value ranking (raw score / score minus cost).
* Ablations `RANK_NET_UNKCOST_ZERO`, `RANK_NET_MISSING_REJECT`.
* Post-hoc, validation worlds only (not pre-registered): `LIFO_NETPOS` (freshest-first with filter).

## Held-out results (15 families × 3 variants × 10 seeds × caps 3/4/6/10)
Absolute means over all held-out cells, bps per slot-hour (latent), plus a few guard-rails:

| policy | lat_per_slot_hour | real_per_slot_hour | utilisation | hq_missed_frac | hhi_cluster | starved_pos_inst | n_evict | mean_hold | ret_to_risk |
|---|---|---|---|---|---|---|---|---|---|
| EQUAL_QUOTA | 0.250 | 0.251 | 0.861 | 0.469 | 0.496 | 0.000 | 0.000 | 14.423 | 0.291 |
| FIFO | 0.162 | 0.158 | 0.863 | 0.474 | 0.511 | 0.000 | 0.000 | 14.218 | 0.190 |
| FIFO_NETPOS | 0.422 | 0.421 | 0.802 | 0.413 | 0.543 | 0.000 | 0.000 | 14.522 | 0.494 |
| OLDEST_SLOT | -0.019 | -0.020 | 0.853 | 0.314 | 0.512 | 0.000 | 154.728 | 10.007 | -0.000 |
| RANDOM_SEEDED | 0.190 | 0.185 | 0.860 | 0.479 | 0.518 | 0.001 | 0.000 | 14.045 | 0.218 |
| ROUND_ROBIN | 0.241 | 0.243 | 0.859 | 0.471 | 0.497 | 0.000 | 0.000 | 14.292 | 0.278 |

Paired differences (dz = difference in latent per-slot-hour value divided by RMS density, mean over caps, bootstrap 95% CI over family×variant×seed blocks):

| policy | vs FIFO | vs FIFO_NETPOS | vs RANK_NET |
|---|---|---|---|
| FIFO_NETPOS | +0.090 [+0.085,+0.096] | nan | -0.058 [-0.065,-0.051] |
| EQUAL_QUOTA | +0.029 [+0.025,+0.033] | -0.061 [-0.068,-0.055] | -0.119 [-0.127,-0.111] |
| ROUND_ROBIN | +0.029 [+0.025,+0.033] | -0.061 [-0.068,-0.055] | -0.119 [-0.126,-0.112] |
| RANDOM_SEEDED | +0.021 [+0.016,+0.026] | -0.070 [-0.077,-0.062] | -0.127 [-0.135,-0.120] |
| FIFO | nan | -0.090 [-0.096,-0.085] | -0.148 [-0.158,-0.139] |
| OLDEST_SLOT | -0.070 [-0.076,-0.064] | -0.161 [-0.169,-0.153] | -0.218 [-0.230,-0.207] |

## Reading
* **OBSERVED**: `ROUND_ROBIN` and `EQUAL_QUOTA` beat `FIFO` by about +0.03 dz but sit far below `FIFO_NETPOS` (+0.09); `RANDOM_SEEDED` is statistically close to them. Forcing fairness across instruments buys nothing except by accident.
* **OBSERVED**: `OLDEST_SLOT` is the only control clearly worse than FIFO (−0.07 dz) — churn cost (≈155 forced exits per run at the tuned setting) outweighs any freshness gain; it shortens the mean hold from 14.2 h to 10.0 h and *raises* HQ-opportunity capture (`hq_missed_frac` 0.31 vs 0.47) but loses money on net.
* **OBSERVED** (post-hoc, validation worlds): `FIFO` takes the *stalest* candidate first; because the simulated edge decays (`exp(-age/8h)`), FIFO loses value even among equal-quality opps. `LIFO_NETPOS` beats `FIFO` by 0.153 dz and `FIFO_NETPOS` by 0.050 dz, and is only 0.008 dz below `RANK_NET` (see 12). A large part of what "ranking" earns over FIFO in this simulator is freshness plus filtering, not quality discrimination. That is a property of the assumed decay (INFERENCE: real edge decay is UNKNOWN).
