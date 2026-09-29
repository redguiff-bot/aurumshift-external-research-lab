# 00 — Executive summary (external research; no AurumShift code read, no integration claim)

**Question.** How should heterogeneous strategy families be combined online when only some are valid in a given market
state — sleeping/specialist experts, online model averaging, bounded adaptive weights — without assuming a bandit?

**What was done.** 13 method families surveyed (literature recalled, OSS source inspected: `river`, `mabwiser`,
`contextualbandits`); 20 method rows implemented and executed in a synthetic 12-scenario simulator (+1 stress), with an explicit
five-state semantics contract (inactive / abstain / data-gap / missing evidence / observed). Rules were pre-registered and committed before tuning; tuning on seeds 0–5,
22,880 held-out runs on seeds 1000–1039 + stress + sensitivity + label-noise studies. Unit tests confirm freeze-on-missing and no look-ahead.

**Headline results (held-out pooled regret ×1e-3, lower is better).**

| | PR | note |
|---|---|---|
| Equal | 63.3 | clones hurt (S5a 79.9) |
| Static fixed | 24.9 | 3.2–4.0× worse under leadership change |
| WTA / EWMA (best baselines) | 11.7 / 11.8 | tuned to near-hard-max |
| DiscFreeze (sleeping Hedge + forgetting) | 10.6 | best non-context, 0.91× baseline, 1.9× worse in burst-gap scenario |
| SleepHedge / FixedShare / SleepEG | 13.2 / 13.3 / 12.6 | slow after leadership change / costs stationary regret |
| BMA (DMA-style) | 11.0 | brittle to hyper-parameters (11.0 … 47.1) |
| Context mixture (lagged label / 20% flips / true label) | 10.5 / 14.4 / 8.4 | needs ≳95% label accuracy to beat baseline by 10% |
| Bandits (DUCB / SleepEXP3) | 17.9 / 59.4 | 1.5× / 5× the best baseline |

1. **Semantics dominate algorithms.** Feeding "not observed" as worst reward multiplies regret by 2.0–3.3× and drives specialist weights to 0.000 forever. Freeze + neutral prior is free and decisive.
2. **Sleeping-expert update is genuinely more robust** than absolute scores under differential selection (informative abstention: 10.6 vs 16.2) and MCAR gaps (11.0 vs 13.7), and to an unlucky-start specialist (0.46–0.71 vs 0.014–0.026 weight).
3. **It does not win overall.** Un-forgetting sleeping Hedge is worst realisable under leadership changes (21–23.5 vs 11.5); EWMA/WTA are hard to beat by the pre-registered 10% margin.
4. **Starvation:** new and recurring (dormant 840 rounds) specialists are not starved under freeze semantics; early-bad-luck specialists are starved by EWMA/WTA/BMA; floors/caps fix it but cost ~2× regret here.
5. **Diversity-aware weighting and bounded weights showed no benefit** — but the objective is risk-neutral, so this study cannot speak for risk.
6. **Bandits are not the right frame** when valid experts' returns are observable.

**Verdict logic.** Literal pre-registered rules leave only the label-oracle context mixture passing (ineligible) → unresolved. A post-hoc corrected gate set leaves a single realisable
passer (`CtxLag`) whose status flips under its own neighbours (20% label flips; label-noise break-even ≈92.5% accuracy; brittle grid) → rule 5 → inconclusive. Both routes: `STUDY_INCONCLUSIVE`.
Two of my gate definitions were flawed (declared in 08); the verdict is threshold-sensitive.

**Practical reading (candidates, not decisions).** ADOPT the availability/evidence contract; ADAPT discounted sleeping Hedge as a reference implementation to test against EWMA on real data;
keep EWMA/WTA as the baseline to beat; PARK context mixtures until label quality is known, and diversity/bounding until a risk objective exists; REJECT bandit-first framing and off-the-shelf libraries lacking availability masks.

## Final block

```
METHODS_DISCOVERED=13 (families; 4 of them baselines/variants counted inside)
METHODS_EXECUTED=20 (19 tuned + Equal; + 6 re-run under naive_zero semantics)

STATIC_WEIGHTS_RESULT=Static PR 24.9 (2.1x best baseline; 3.2-4.0x in leadership/composite); insufficient
EWMA_RESULT=EWMA PR 11.8 / WTA 11.7 = best baselines; hard to beat by 10%; but +53% on informative abstention, +25% on MCAR gaps vs sleeping update, starves unlucky-start specialist (w25=0.014), brittle grid (11.9-51.1)
SLEEPING_EXPERTS_RESULT=SleepHedge 13.2 / FixedShare 13.3 / SleepEG 12.6 / DiscFreeze 10.6: robust to gaps, selection and unlucky starts; slow on leadership change unless forgetting/share added; no 10%-margin win without a regime label

MISSING_EVIDENCE_HANDLED=YES with freeze + neutral-prior contract (unit-tested); violating it costs 2.0-3.3x regret; MNAR censoring not fixable
STARVATION_CONTROLLED=PARTIAL (new expert and 840-round-dormant specialist: yes; early-bad-luck specialist under absolute-score rules: no; floors control it at ~2x regret)
RECURRING_SPECIALIST_RECOVERY=YES under freeze semantics (>=0.87 weight in first 25 rounds after 840 dormant rounds for all gated rules; 0.000 under naive semantics)

COMPLEXITY_JUSTIFIED=NOT_DEMONSTRATED (no non-oracle-context method clears a 10% margin over EWMA/WTA; context needs >=~95% label accuracy; diversity/bounding/bandits unjustified under this risk-neutral synthetic objective)

FINAL_VERDICT=STUDY_INCONCLUSIVE
```
