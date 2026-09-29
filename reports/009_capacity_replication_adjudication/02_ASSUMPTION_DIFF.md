# 02 — Assumption diff

Read from source (`env.py`, `scenarios.py`; `world.py`, `engine.py`), not from README claims. A = Study A simulator (same in `main` and in the unmerged run 2 apart from the estimator fixes). B = Study B. Labels: IDENTICAL / SEMANTICALLY_EQUIVALENT / DIFFERENT / UNKNOWN.

| # | Dimension | Study A | Study B | Label |
|---|---|---|---|---|
| 1 | Time step | 1 hour | 1 hour | IDENTICAL |
| 2 | Horizon | T=1000 | W=600 (+48 padding) | DIFFERENT |
| 3 | Instruments | N=12, 4 clusters of 3 | N=10/12/15 by split (held-out 15), 5 groups of 3 | DIFFERENT |
| 4 | Slot count | cap ∈ {3,4,6,10}; tuned at 4 and 6 | K ∈ {3,4,6,10}; tuned at 4 only | SEMANTICALLY_EQUIVALENT (grid) / DIFFERENT (tuning caps) |
| 5 | Candidate load definition | `load` × `cap_ref`(4) slot-equivalents of **distinct opportunities**, each with its own latent edge/duration; families 0.15–4.0 × jitter | `load` × 4 / mean(dmean) raw **emissions** per hour, 0.4–3.5; many emissions repeat the same instrument | DIFFERENT |
| 6 | One position per instrument | **not enforced**; positions are keyed by candidate id, so several may sit on one instrument | enforced (`open_inst`); all pool copies of an admitted instrument are dropped | DIFFERENT |
| 7 | Candidate unit and TTL | each arrival is a separate opportunity, TTL=3 h from arrival; score can refresh with age | per-instrument emissions; TTL=4 h from *last* emission; four ingestion modes (RAW/DEDUP/COOLDOWN/SCORE_UPDATE) | DIFFERENT |
| 8 | Latent edge | per opportunity: instrument mean (10±6) + N(0,14²) draw; decays `exp(-age/8)` while waiting | per instrument-hour: regime-scaled mean (5–38) + AR(1) φ=0.9 state (sd 5–6); state at *admission* time is what accrues | DIFFERENT |
| 9 | Score generation | `S = a + b·edge·exp(-age/8) + persistent(0.5σ) + iid(0.85σ)`, σ = 10 × heterogeneity; refreshed each age step | `s = a_i + b_g·E[i,t_emit] + τ·N(0,1)`, τ = 8–10 | DIFFERENT structure; SEMANTICALLY_EQUIVALENT noise scale (sd ≈ 10 vs 8–10) |
| 10 | Score calibration | slope 1, intercept 0 by construction; S7 flips slope on half the clusters after the regime shift | slope 1 by construction in all 13 held-out scenarios; miscalibration only in validation-only battery (D2, F_*) | SEMANTICALLY_EQUIVALENT baseline; DIFFERENT coverage |
| 11 | Missing / stale scores | NaN with p_miss (S9: 0.4); `refresh=False` gives stale-age scores (not used in a scenario) | NaN with p_miss (S9: 0.5); stale (repeat last score) only in validation battery | SEMANTICALLY_EQUIVALENT (missing); DIFFERENT (stale) |
| 12 | Cost model | per instrument fee 4–8 + slippage 1–3 bps, constant per admission; forced close adds 3 bps | per instrument 4–9 (held-out 4–10) bps, constant per admission; no extra eviction fee; ×cost_mult in diagnostics | SEMANTICALLY_EQUIVALENT form; DIFFERENT level (see row 13) |
| 13 | **Edge-to-cost ratio** | edge ≈ 10, cost ≈ 8.5: near break-even before noise | edge ≈ 20, cost ≈ 6.5: comfortably positive | DIFFERENT (decisive, see 07) |
| 14 | Hold duration | per opportunity lognormal around instrument mean 12 h (het 0.5), clipped 1–96; mean hold ≈ 15 h; allocator sees a **candidate-level noisy estimate** `dur_hat` (ρ=0.3, sd 0.25, 5–30% missing) | per instrument-hour lognormal CV 0.6–0.7 around 3–14 h, clipped 1–48; mean hold ≈ 8.7 h; allocator has **no candidate-level hold**, only a per-instrument EWMA of past realised holds | DIFFERENT |
| 15 | Edge accrual | pro-rata linear over the hold; early close forfeits the rest, pays full cost | linear `(E/D)·h`; early close forfeits the rest, pays full cost | SEMANTICALLY_EQUIVALENT |
| 16 | Market noise in outcome | cluster factor (β=1, σ_c 6–12) + idiosyncratic σ_i 6 per √h, added to realised net | group factor ρ_g 0.35 (0.8 in S5), market factor ρ_m 0.15 (0.7 in collapse), σ_i 8–22 | DIFFERENT |
| 17 | Primary metric noise | **latent** net (edge − cost, noise excluded) normalised by `dens0` → dz | **realised** net (noise included), raw bps per available slot-hour | DIFFERENT (scales not poolable) |
| 18 | Correlation model | 4 clusters, one factor each, zero cross-cluster correlation | group factor + market factor + crisis/collapse variants | DIFFERENT |
| 19 | Regime model | S7: half-time permutation of instrument means, slope flip on half of clusters, σ_c ×2; scores become **miscalibrated** | S7: half-time flip of means (`max+min−mu`); scores stay calibrated (`s` tracks new `E`); slow Markov regimes elsewhere | DIFFERENT (A tests score corruption, B only edge shift) |
| 20 | Spam semantics | high-rate candidates on instrument 0, true edge −2, **score bias +12** (harmful, score-gaming) | two instruments at 20× rate with **median edge, honest scores** (harmless volume) | DIFFERENT (decisive for S10) |
| 21 | Preemption | `EVICT_SWAP` (value-based) and `OLDEST_SLOT`; forced close costs +3 bps and forfeits the remaining edge | `OLDEST_SLOT` only; no extra fee | DIFFERENT |
| 22 | Feedback delay | outcome (`realized`) delivered at close; policies also receive past returns (`on_returns`) | outcome delivered at close; public `sigma_pub` only | SEMANTICALLY_EQUIVALENT (delay), DIFFERENT (extra public returns in A) |
| 23 | UNKNOWN_COST handling | cost observed as NaN in 10% (S9: 35%) of candidates; true cost never zero; variants `RANK_NET_UNKCOST_ZERO`, `MISSING_REJECT` | belief modes `known` (primary), `zero`, `unknown_conservative` (prior 10); only in diagnostic D3, not in held-out scenarios | DIFFERENT |
| 24 | Oracle | score- or density-oracle on latent edge/duration; LP relaxation bound; excludes market noise | greedy perfect foresight on **realised** net per hold-hour, noise included, skips negative trades | DIFFERENT (headroom not comparable) |
| 25 | Determinism / RNG | `SeedSequence([seed, 20260929])` split into 5 streams | crc32(name\|split)+1000003·seed | SEMANTICALLY_EQUIVALENT |
| 26 | Split shift | jitter ranges widen 0.8–1.25 → 0.75–1.3 → 0.65–1.5; held-out-only H1–H3 compositions | structural parameter changes per split (N, G, τ, CV, edge/vol/cost ranges) | SEMANTICALLY_EQUIVALENT in intent (both same-family shift) |

## Consequences
- **No effect size is poolable** (rows 5, 8, 13, 14, 17). Only sign, rank order and shares-of-a-gain are compared (06).
- Rows 6, 13, 19, 20, 21 are where I expect, and in 07 demonstrate, genuine disagreements.
- Rows 9, 15, 25 are the only ones where the studies are effectively the same model, so agreement there is not independent evidence of robustness.
