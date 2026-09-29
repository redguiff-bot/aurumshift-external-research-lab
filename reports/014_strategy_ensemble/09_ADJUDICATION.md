# 09 — Adjudication

## Held-out results (40 seeds, tuned parameters frozen; PR ×1e3; ✔/✘ = pre-registered gates, literal definitions)

| method | fam | PR x1e3 | vs best baseline | CI(bb-m) x1e3 | reward | best_mass | starved | G1 | G2a | G2b | G3a | G3b | G3c | G4a | G4b |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CtxOracle | A | 8.36 | 0.71x | [3.15,3.53] | 0.5790 | 0.755 | 0.054 | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ |
| CtxLag | A | 10.52 | 0.90x | [1.01,1.35] | 0.5769 | 0.710 | 0.077 | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✘ | ✔ |
| DiscFreeze | A | 10.59 | 0.91x | [0.92,1.31] | 0.5769 | 0.590 | 0.398 | ✘ | ✘ | ✔ | ✔ | ✔ | ✔ | ✘ | ✔ |
| BMA | B | 10.97 | 0.94x | [0.68,0.77] | 0.5769 | 0.583 | 0.364 | ✘ | ✘ | ✔ | ✔ | ✔ | ✔ | ✘ | ✔ |
| DiscAmnesty | A | 11.35 | 0.97x | [0.14,0.55] | 0.5763 | 0.527 | 0.463 | ✘ | ✘ | ✔ | ✔ | ✔ | ✘ | ✘ | ✔ |
| WTA | B | 11.69 | 1.00x | [0.00,0.00] | 0.5761 | 0.575 | 0.425 | ✘ | ✘ | ✔ | ✔ | ✔ | ✔ | ✘ | ✔ |
| DivEWMA | B | 11.74 | 1.00x | [-0.06,-0.03] | 0.5761 | 0.575 | 0.369 | ✘ | ✘ | ✔ | ✔ | ✔ | ✔ | ✘ | ✘ |
| EWMA | B | 11.83 | 1.01x | [-0.15,-0.12] | 0.5760 | 0.572 | 0.371 | ✘ | ✘ | ✔ | ✔ | ✔ | ✔ | ✘ | ✘ |
| SleepEG | A | 12.64 | 1.08x | [-1.29,-0.61] | 0.5750 | 0.475 | 0.522 | ✘ | ✔ | ✔ | ✔ | ✔ | ✔ | ✘ | ✘ |
| DivSH | A | 13.16 | 1.13x | [-1.68,-1.23] | 0.5744 | 0.467 | 0.531 | ✘ | ✔ | ✔ | ✔ | ✔ | ✔ | ✘ | ✔ |
| SleepHedge | A | 13.16 | 1.13x | [-1.68,-1.24] | 0.5744 | 0.467 | 0.531 | ✘ | ✔ | ✔ | ✔ | ✔ | ✔ | ✘ | ✔ |
| FixedShare | A | 13.33 | 1.14x | [-1.78,-1.49] | 0.5741 | 0.627 | 0.181 | ✘ | ✔ | ✔ | ✔ | ✔ | ✔ | ✘ | ✘ |
| CtxNoisy | A | 14.40 | 1.23x | [-2.87,-2.53] | 0.5730 | 0.626 | 0.114 | ✘ | ✔ | ✔ | ✔ | ✔ | ✔ | ✘ | ✘ |
| HedgePlain | C | 17.58 | 1.50x | [-6.26,-5.49] | 0.5699 | 0.444 | 0.555 | ✘ | ✘ | ✔ | ✔ | ✔ | ✔ | ✘ | ✘ |
| DUCB | C | 17.94 | 1.53x | [-6.55,-5.96] | 0.5699 | 0.498 | 0.502 | ✘ | ✔ | ✔ | ✔ | ✔ | ✔ | ✘ | ✘ |
| EWMA_bounded | B | 23.21 | 1.98x | [-11.67,-11.36] | 0.5646 | 0.453 | 0.169 | ✘ | ✔ | ✔ | ✔ | ✔ | ✔ | ✘ | ✘ |
| Static | B | 24.92 | 2.13x | [-13.89,-12.54] | 0.5630 | 0.378 | 0.482 | ✘ | ✔ | ✔ | ✔ | ✔ | ✔ | ✘ | ✘ |
| SH_bounded | A | 25.29 | 2.16x | [-13.78,-13.39] | 0.5622 | 0.500 | 0.126 | ✘ | ✔ | ✔ | ✔ | ✔ | ✔ | ✘ | ✘ |
| SleepEXP3 | C | 59.35 | 5.07x | [-48.24,-47.06] | 0.5281 | 0.174 | 0.524 | ✘ | ✔ | ✔ | ✔ | ✘ | ✔ | ✘ | ✘ |
| Equal | B | 63.34 | 5.42x | [-51.97,-51.30] | 0.5242 | 0.176 | 0.000 | ✘ | ✔ | ✔ | ✘ | ✘ | ✔ | ✘ | ✘ |


G3a/b/c = starvation gates, G2a/b = missing-evidence gates, G4a/b = robustness gates (05, 04, 06). CI(bb−m) is the paired-bootstrap
95% interval of (best-baseline − method) pooled regret ×1e3; positive = method better.

## Stress sets (PR ratio vs best baseline of that set)

| method | lowsnr(0.5x edges) | highnoise(1.6x) |
|---|---|---|
| CtxOracle | 0.81 | 0.87 |
| CtxLag | 0.91 | 0.99 |
| DiscFreeze | 0.82 | 0.82 |
| BMA | 0.97 | 0.95 |
| DiscAmnesty | 0.83 | 0.86 |
| WTA | 1.00 | 1.00 |
| DivEWMA | 1.01 | 1.00 |
| EWMA | 1.01 | 1.01 |
| SleepEG | 0.84 | 1.85 |
| DivSH | 0.77 | 0.85 |
| SleepHedge | 0.77 | 0.85 |
| FixedShare | 1.08 | 1.26 |
| CtxNoisy | 1.09 | 1.19 |
| HedgePlain | 0.92 | 1.03 |
| DUCB | 1.32 | 1.43 |
| EWMA_bounded | 1.48 | 1.60 |
| Static | 1.49 | 1.60 |
| SH_bounded | 1.47 | 1.76 |
| SleepEXP3 | 3.05 | 3.44 |
| Equal | 3.08 | 3.66 |

## Applying the frozen rules

* Literal: only `CtxOracle` satisfies G1–G4. It is ineligible as the sole basis of a verdict (true label). No realisable method satisfies G2–G4, but
  rule 1 (as written: "no method") does not fire because `CtxOracle` satisfies it; rules 2–4 do not fire (EWMA/Static fail G2a/G4; no realisable G1 passer). The rule tree is
  unresolved => `STUDY_INCONCLUSIVE`.
* POST_HOC amended gates (`results/gates_amended.json`): the only realisable method passing G1–G4 is `CtxLag` (0.90×, worst scenario 1.24×). By rule 4
  that would read `SLEEPING_EXPERT_REFERENCE_SUPPORTED` (single family-A passer; family B fails G1). **Rule 5 then fires**: replacing it with its sibling `CtxNoisy` (same method, 20% label flips) fails G1 (1.23×), the label-noise curve flips it at ≈92.5% label accuracy, its own grid is brittle (10.5–22.2), and the non-context sleeping methods
  (SleepHedge, FixedShare, DiscFreeze) miss G1 (0.91–1.14×). => `STUDY_INCONCLUSIVE`.
* Both routes agree.

## What the evidence DOES support (descriptive, not a verdict)

1. PROVEN (synthetic): missing evidence must be *frozen/neutral*; `naive_zero` costs 2.0–3.3× regret, more than any algorithm choice.
2. PROVEN: observation-gated adaptive rules (WTA/EWMA/BMA/SleepHedge/DiscFreeze/FixedShare/SleepEG) cluster at 10.6–13.3, vs Equal 63, Static 25, bandits 18–59.
3. PROVEN: no adaptive rule dominates; families trade places by mechanism (sleeping update wins under gaps/informative abstention; forgetting/EWMA win under leadership
   change; context wins under recurrence if the label is ≳95% accurate).
4. PROVEN: sleeping-expert updates (specialist rule) are *robust to differential selection* and to unlucky-start specialists; score rules are not.
5. NOT SHOWN: benefit of diversity-aware weighting, bounded weights, or a parameter-free variant; those need a risk-aware objective and real data.

## Candidate labels (external research only — no integration claim)

| Candidate | Label | Reason |
|---|---|---|
| Explicit availability/evidence semantics (freeze, neutral prior for unseen) | **ADOPT (as a contract)** | dominant effect; zero algorithmic cost |
| Discounted sleeping Hedge (`DiscFreeze`) as reference implementation | **ADAPT** | most robust across grid (10.8–12.4), best non-context PR, but 1.9× in burst-gap scenario and misses the 10% margin |
| Plain sleeping Hedge / fixed-share | **PARK** | slow on leadership change (η large) or costs stationary regret (η small) |
| EWMA / WTA as the baseline to beat | **KEEP AS BASELINE** | hard to beat by 10% without a label; but starves unlucky-start specialists and mis-ranks under informative abstention |
| Context-conditioned mixture | **PARK pending label quality** | needs regime label accuracy ≳95% |
| Diversity-aware weighting | **PARK** | no accuracy benefit; only relevant with a risk objective |
| Bounded floor/cap | **PARK** | insurance cost 2× under this generator |
| Bandit variants | **REJECT as primary frame** | 1.5–5× regret |
| Off-the-shelf libraries (`river` EWA, `mabwiser`, `contextualbandits`) | **REJECT for this need** | no availability mask / sleeping / fixed-share (OBSERVED in source) |

Final adjudication of any of these against the real repository happens later, locally.
