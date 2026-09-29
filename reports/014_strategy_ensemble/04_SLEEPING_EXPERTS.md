# 04 — Sleeping experts and the missing-evidence semantics

## Contract (implemented, unit-tested)

| State | Allocated | Learner state | Where it comes from |
|---|---|---|---|
| NOT_EXIST | no | none; newcomer initialised at cohort-mean weight/score when first seen | roster change |
| INACTIVE | no | frozen | regime makes strategy invalid |
| ABSTAIN | no | frozen | strategy declines (random 5%, or informative in S6d) |
| GAP | yes | frozen | realised but unobserved (MCAR 10-30%, 350-round burst, MNAR stress) |
| OBS | yes | updated | observed reward |

* Specialist update (Freund et al. 1997): only observed experts move and the *total observed mass is
  preserved*, so an expert is compared with its peers on rounds where both are present, never with rounds
  where it was absent. PROVEN by the S6d result below.
* "Evidence-time": fixed-share mixing and forgetting advance only on rounds with ≥1 observation, so a
  data outage does not itself erode weights. `DiscAmnesty` is the deliberate wall-clock exception.
* Missing evidence is a *prior*, not a penalty: newcomers/unseen experts get the cohort mean.

## What violating it costs (PROVEN, 40 held-out seeds, pooled regret ×1e-3, paired bootstrap CI)

| method | correct | naive_zero | diff | CI |
|---|---|---|---|---|
| EWMA | 11.83 | 34.94 | +23.11 | [22.69,23.52] |
| HedgePlain | 17.58 | 42.55 | +24.96 | [24.08,25.90] |
| SleepHedge | 13.16 | 40.47 | +27.31 | [26.52,28.10] |
| FixedShare | 13.33 | 26.61 | +13.28 | [12.98,13.59] |
| BMA | 10.97 | 34.85 | +23.88 | [23.44,24.31] |
| DiscFreeze | 10.59 | 34.73 | +24.14 | [23.69,24.58] |


Feeding "not observed" as worst reward (`naive_zero`) multiplies pooled regret by 2.0–3.3× for every
method (+13 to +27 in regret units, CI far from 0). This is larger than any difference *between* the
correct-semantics methods (10.5–13.2). Under naive semantics a specialist's weight collapses to 0.000
(EWMA, BMA, SleepHedge, DiscFreeze, HedgePlain) and never recovers; only FixedShare (which keeps
re-injecting mass) retains ~0.6. This is the single strongest result in the study.

## Sleeping update vs absolute scores (PROVEN in S6a/S6b/S6d/S6c, held-out regret ×1e-3)

| scenario | mechanism | WTA | EWMA | SleepHedge | DiscFreeze | BMA |
|---|---|---|---|---|---|---|
| S6a | 30% MCAR gaps | 13.6 | 13.7 | 11.0 | 11.8 | 12.4 |
| S6b | 350-round burst gap | 12.3 | 12.4 | 11.1 | 17.7 | 11.5 |
| S6d | informative abstention | 16.2 | 16.2 | 10.6 | 9.3 | 15.3 |
| S6c (stress) | MNAR: bad outcomes missing | 13.0 | 13.2 | 11.4 | 10.5 | 12.4 |

* S6d: generalists abstain when they would have lost, so their *observed* mean is inflated relative to
  never-abstaining specialists. Absolute-score rules (WTA/EWMA/BMA) mis-rank across experts (+53–56% regret vs
  their own S0); relative (co-awake) comparison is robust. INFERENCE for the mechanism, PROVEN for the effect.
* S6b exposes a hazard of "freeze + forgetting" (DiscFreeze 17.7 vs 9.3 in S0, ratio 1.9): forgetting shrinks
  observed experts toward the mean while the unobserved expert keeps stale extreme evidence. INFERENCE
  (not isolated by an ablation).
* S6c (MNAR) is not fixable by any of these rules — censoring of bad news is unidentifiable without extra
  structure; methods degrade by roughly 6–25% vs S0 (SleepHedge least, EWMA most); the reason is not isolated (INFERENCE: censoring affects all generalists similarly).
  Reported as stress, not gated.

## Non-sleeping Hedge reference
`HedgePlain` (cumulative loss, unobserved adds nothing) has the exposure flaw: totals are compared over
different exposure lengths. Observed effect: after the RARE specialist's unlucky start (S7) HedgePlain gives it weight
1.000 in every episode (short exposure = low cumulative loss), and its regret is 17.6 vs 13.2 for SleepHedge.
