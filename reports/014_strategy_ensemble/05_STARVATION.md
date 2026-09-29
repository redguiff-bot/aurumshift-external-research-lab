# 05 — Starvation tests

Held-out means over 40 seeds. "w25" = mean weight of the specialist over its first 25 allocated rounds of an
episode. Fair share among ~4–5 valid experts is ≈0.2; the specialist is truly best.

| method | mode | S2 rare w25 ep1 | ep2 (after ~840 dormant) | S3 new-expert tts median | S3 reached<400 | S7 rare w25 ep1 (unlucky start) | ep2 | ep3 | S7 LATE recovery median |
|---|---|---|---|---|---|---|---|---|---|
| BMA | correct | 0.880 | 1.000 | 25 | 1.00 | 0.026 | 0.999 | 1.000 | 56 |
| CtxLag | correct | 0.853 | 0.960 | 42 | 0.97 | 0.112 | 0.963 | 0.966 | 38 |
| CtxNoisy | correct | 0.790 | 0.911 | 25 | 1.00 | 0.121 | 0.919 | 0.942 | 39 |
| CtxOracle | correct | 0.862 | 0.979 | 58 | 0.97 | 0.111 | 0.984 | 0.983 | 34 |
| DUCB | correct | 1.000 | 1.000 | 25 | 1.00 | 0.177 | 0.783 | 0.905 | 77 |
| DiscAmnesty | correct | 0.992 | 0.994 | 25 | 1.00 | 0.211 | 0.996 | 0.997 | 110 |
| DiscFreeze | correct | 1.000 | 1.000 | 25 | 1.00 | 0.712 | 1.000 | 1.000 | 57 |
| DivEWMA | correct | 0.690 | 0.999 | 36 | 1.00 | 0.017 | 0.999 | 1.000 | 55 |
| DivSH | correct | 0.996 | 1.000 | 25 | 1.00 | 0.465 | 1.000 | 1.000 | 22 |
| EWMA | correct | 0.672 | 0.999 | 38 | 1.00 | 0.014 | 0.999 | 1.000 | 56 |
| EWMA_bounded | correct | 0.523 | 0.699 | 32 | 1.00 | 0.052 | 0.700 | 0.700 | 43 |
| Equal | correct | 0.173 | 0.172 | 400 | 0.00 | 0.173 | 0.174 | 0.174 | 10 |
| FixedShare | correct | 0.961 | 0.977 | 25 | 1.00 | 0.181 | 0.986 | 0.988 | 21 |
| HedgePlain | correct | 1.000 | 1.000 | 28 | 1.00 | 1.000 | 1.000 | 1.000 | 10 |
| SH_bounded | correct | 0.695 | 0.698 | 25 | 1.00 | 0.207 | 0.700 | 0.699 | 12 |
| SleepEG | correct | 0.998 | 1.000 | 25 | 1.00 | 0.214 | 0.950 | 0.950 | 80 |
| SleepEXP3 | correct | 0.090 | 0.068 | 25 | 1.00 | 0.056 | 0.089 | 0.062 | 38 |
| SleepHedge | correct | 0.995 | 1.000 | 25 | 1.00 | 0.463 | 1.000 | 1.000 | 22 |
| Static | correct | 0.862 | 0.866 | 25 | 1.00 | 0.173 | 0.691 | 0.690 | 10 |
| WTA | correct | 0.672 | 1.000 | 38 | 1.00 | 0.014 | 0.999 | 1.000 | 55 |
| BMA | naive_zero | 0.000 | 0.000 | 38 | 1.00 | 0.000 | 0.000 | 0.000 | 48 |
| DiscFreeze | naive_zero | 0.000 | 0.000 | 25 | 1.00 | 0.000 | 0.000 | 0.000 | 50 |
| EWMA | naive_zero | 0.000 | 0.000 | 72 | 1.00 | 0.000 | 0.000 | 0.000 | 48 |
| FixedShare | naive_zero | 0.572 | 0.613 | 30 | 1.00 | 0.099 | 0.690 | 0.558 | 31 |
| HedgePlain | naive_zero | 0.000 | 0.000 | 400 | 0.00 | 0.000 | 0.000 | 0.000 | 300 |
| SleepHedge | naive_zero | 0.000 | 0.000 | 25 | 1.00 | 0.000 | 0.000 | 0.000 | 300 |

## Reading

1. **New-expert starvation (S3): not observed for any observation-gated method.** Median 25 allocated rounds
   (the measurement floor: trailing window is 25) for SleepHedge/FixedShare/Disc*/BMA/SleepEG, 36–42 for WTA/EWMA/
   DivEWMA/CtxLag; only Equal never reaches 0.25 weight. Caveat (INFERENCE, plainly): this is mostly produced by the
   *neutral cohort initialisation* rule I chose, not by the learning rule; the newcomer is strong (edge 0.06) so
   there is little to starve. An optimism-free, penalty-free prior is what matters.
2. **Recurring rare specialist after dormancy (S2): controlled.** After ~840 dormant rounds every observation-gated
   method has ≥0.87 (most ≥0.98) weight on it in the first 25 rounds of the return (freeze semantics). Bounded
   floor/cap variants cap it at 0.70 by construction. Bandit EXP3 never finds it (0.07). Static holds 0.87 (INFERENCE: the frozen calibration weights happened to favour it). Naive semantics: 0.000.
3. **Rare specialist with an unlucky start (S7): a real starvation mode of score-based rules.** WTA/EWMA/BMA/DivEWMA give
   it 0.014–0.026 in its first episode (15 unlucky observations) — it is starved for that entire 80-round episode —
   and only recover on later episodes (0.999). SleepHedge/DiscFreeze/DivSH give 0.46–0.71 because the specialist
   update compares against co-awake peers, and the round-relative loss of an unlucky start is bounded. Ctx* ≈0.11–0.12,
   FixedShare 0.18, bounded variants ≈0.2. No method both protects unlucky specialists and keeps regret low without a
   prior; bounded floors control starvation but cost regret (SH_bounded 25.3 vs 13.2).
4. **Temporary underperformance of a strong generalist (S7 patch): recovery is fast for most** (median 21–57 rounds to regain half its prior weight for the adaptive rules (Static/HedgePlain/Equal 10 = they never lost it);
   DiscAmnesty 110, SleepEG 80, DUCB 77; SleepHedge 22; INFERENCE: its huge η makes it near hard-max in both directions).
   The 150-round patch itself is expensive for un-forgetting SleepHedge (S7 regret 16.7 vs 11.2 for WTA)
   because accumulated advantage delays reaction.
5. Bounded adaptive weighting (`SH_bounded`, `EWMA_bounded`) was *tuned toward zero bounding* (floor 0–0.02, B at the grid maximum): under
   this generator floors are pure insurance that is never paid back (PR 23–25 vs 12–13).

Verdict for this dimension: `STARVATION_CONTROLLED = PARTIAL` — controlled for new and recurring experts by
initialisation + freeze semantics; NOT controlled for early-bad-luck specialists under absolute-score rules.
