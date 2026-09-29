# 06 — Numeric comparison

**No pooling, no meta-analysis.** The generators differ in load definition, edge/cost level, hold model, noise treatment and metric (02 rows 5, 8, 13, 14, 17), so absolute effects are not on one scale. What *is* compared is (a) the sign, (b) the ordering of methods, and (c) **each effect as a share of the simple ranking's gain over FIFO**, a unit-free quantity that both studies can express.

All B numbers: held-out H1, 13 scenarios × 20 seeds, K=4, macro over scenarios, paired 95% bootstrap over seeds. All A numbers: run 2 validation split (**unmerged, not held-out**), `dz` = latent net per slot-hour ÷ `dens0_rms`, pooled over caps 3/4/6/10, paired 95% bootstrap over (family, variant, seed) blocks. I recomputed both from the raw CSVs with `evidence/adjudication_probe.py`; B's own tables agree to ±0.004 on every contrast I re-derived (my bootstrap differs slightly in the random-vs-FIFO CI, see below).

## Contrasts on comparable semantics

| Contrast | B: bps/avail-slot-hour [95% CI], wins | A-run2: dz [95% CI] | Same sign | Share of simple gain (B / A) |
|---|---|---|---|---|
| Net screen − FIFO (`FIFO_SCREEN` / `FIFO_NETPOS`) | +0.164 [0.128, 0.200], 11/13 | +0.100 [0.091, 0.109] | yes | 45% / 65% of net-ranking gain |
| Net ranking − FIFO (`SCORE_RANK` / `RANK_NET`) | +0.365 [0.318, 0.411], 12/13 | +0.154 [0.140, 0.168] | yes | reference = 100% |
| Net ranking − net screen | +0.201 [0.157, 0.245], 12/13 | +0.054 [0.045, 0.064] | yes | 55% / 35% |
| Gross-score ranking − FIFO | not run | +0.134 [0.120, 0.148] | n/a | n/a |
| Net − gross-score ranking | not run | +0.020 [0.018, 0.023] | n/a | n/a |
| Slot-hour − net ranking | +0.070 [0.033, 0.110], 11/13 | +0.001 [0.000, 0.003] | sign ≥ 0 both | 19% / 1% |
| Best complex − simple (`UNCERTAINTY_LCB` − `SLOTHOUR`; `COMPOSED` − `RANK_NET`) | +0.062 [0.022, 0.098], 10/13 | +0.025 [0.017, 0.034] | yes | **14% / 16%** |
| `UNCERTAINTY_LCB` − simple | +0.062 (vs SLOTHOUR) | +0.010 [0.005, 0.017] (vs RANK_NET) | yes | 14% / 6% |
| Shadow-price family − simple | +0.009 [−0.026, 0.043] | `SHADOW_PRICE` +0.020, `KNAPSACK` +0.017 (dry-run CIs exclude 0) | same weak sign | 2% / 13% |
| Correlation penalty − simple | −0.022 [−0.052, 0.010] | `CORR_PENALTY` 0.000; `MARGINAL_RISK` +0.004 | ≈0 both | ≈0 |
| Bandit − simple | −0.020 [−0.058, 0.019] (LinTS) | LIN_TS −0.013 [−0.021, −0.004]; LINUCB −0.029 | ≤0 both | −5% / −8% to −19% |
| Random − FIFO | −0.042 (B report CI [−0.087, 0.001]; my re-bootstrap [−0.072, −0.012]) | +0.024 [0.016, 0.032] | **no** | −12% / +16% |
| Round-robin − FIFO | −0.006 [−0.050, 0.035] | +0.030 [0.023, 0.037] | **no** (tiny) | −2% / +19% |
| Equal-quota − FIFO | −0.041 [−0.082, 0.002] | +0.031 [0.024, 0.038] | **no** (tiny) | −11% / +20% |
| Preemption (`OLDEST_SLOT`) − FIFO | +0.185 [0.149, 0.221], 10/13 | −0.085 [−0.101, −0.071] | **no** | n/a |

## Capacity dependence (synthetic sensitivity only)

| K | B: ranking − FIFO (`SLOTHOUR`, macro, 10 seeds) | B: FIFO→best | A-run2: `RANK_NET` − FIFO (dz) | A `FIFO_NETPOS` − FIFO | A: FIFO busy-slot share | B: FIFO all-slots-full fraction |
|---|---|---|---|---|---|---|
| 3 | +0.679 [0.607, 0.756] | +0.878 | +0.192 | +0.117 | 0.90 | 0.84 |
| 4 | +0.476 [0.413, 0.539] | +0.595 | +0.176 | +0.109 | 0.88 | 0.78 |
| 6 | +0.156 [0.102, 0.211] | +0.257 | +0.148 | +0.097 | 0.85 | 0.65 |
| 10 | **−0.041** [−0.059, −0.024] | +0.019 | **+0.099** [0.089, 0.110] | +0.076 | 0.77 | 0.12 (busy-slot share 0.61) |

Ratio K=10 / K=3: B ≈ −6%, A ≈ +52%. Both decline monotonically; A never approaches zero because A's scarce families (S3 at load 4×, S5, S6, S7 at 3×) stay over-subscribed at K=10, while B's fixed absolute load leaves most slots idle there (idle-with-backlog ≈ 0; FIFO full only 12% of the time).

## Scenario dependence (where reported)
- B FIFO-failure scenarios vs raw FIFO (δ=0.25): S12, S3, S4, S5, S5b, S7, S8, S9; equivalent: S1, S2, S6, S10, S11.
- A-run2 (dz, K pooled): fail in S10, S11, S12, S2, S3, S4, S5, S7, S8, S9; equivalent S1; S6 neither.
- Overlap on failure: S12, S3, S4, S5, S7, S8, S9 (7 of 10 A failures are B failures). Differences: S2, S10, S11 (A fails, B equivalent). S10 is explained by spam semantics (07 §3). S2 is borderline in A (best-of-four 0.105 dz against a 0.10 threshold, and best-of selection inflates it), and in S11 A's best-of-four gain over FIFO (+0.135) shrinks to +0.029 once FIFO is given the net screen, so the FIFO gap there is mostly the screen.
- Screen share by world: A default S3 72%; A with B-like edge/cost 33%; B 45%. It falls as the edge/cost ratio rises, which predicts (correctly) B's lower value.

## Study A as merged (strict), for the record
Tuned method − FIFO, tuning split, `dens0_sd` units, K∈{4,6} pooled: `COMPOSED` +0.243, `UNCERTAINTY_LCB` +0.239, `SHADOW_PRICE` +0.232, `MARGINAL_RISK` +0.225, `SLOTHOUR_DENSITY` +0.220, `CORR_PENALTY` +0.216, `LIN_TS` +0.174, `LINUCB` +0.176, `ONLINE_KNAPSACK_PSI` +0.172, `OLDEST_SLOT` −0.116. Family view of `SLOTHOUR_DENSITY` − FIFO: S12 = +1.268, all other families 0.011–0.285. Removing S12 changes the pooled mean from ≈0.22 to ≈0.12, i.e. the strict A numbers cannot be compared in size to anything. Ordering (all tuned smart methods within 0.07 of each other; bandits and preemption at the bottom) is the only usable content, and it agrees with B.

## Why the two studies' margins give different labels for R5
In A-run2 FIFO scores dz ≈ 0.089 and `RANK_NET` ≈ 0.242 (gain 0.154). A's equivalence margin δ_equiv = 0.02 is **13%** of that gain. B's δ = 0.25 bps is **57%** of `SLOTHOUR`'s 0.435 gain (14% of FIFO's 1.78). A best-complex increment of 14–16% of the simple gain is therefore 'material' under A's margin and 'inside the tie' under B's. This one comparison explains why A's dry run reports `CAPACITY_ALLOCATION_REFERENCE_SUPPORTED` (COMPOSED) and B reports `MULTIPLE_CAPACITY_METHODS_SUPPORTED`, without any disagreement in the underlying effect.
