# 01 — Problem statement

Mode: `EXTERNAL_RESEARCH_ONLY`. No private AurumShift code was read or assumed. Nothing here says
anything about compatibility with the real system; it produces ADOPT / ADAPT / PARK / REJECT
*candidates* for a later, local integration adjudication.

## The question

A trading system runs several heterogeneous strategy families (trend, mean-reversion, carry,
volatility specialists, a rare-event specialist, ...). In any market state only a subset of them is
*valid*. We need an online rule that turns the currently valid strategies into weights, learning
from realised results, without a dedicated regime oracle. The question is **not** "which bandit";
it is which family of online aggregation rules is defensible, given that:

* the set of available experts changes every round (sleeping / specialist experts),
* experts arrive (new strategy) and disappear (retired strategy),
* evidence for an expert is sparse, gapped, or absent for long stretches,
* leadership changes and regimes recur,
* several experts can be near-duplicates.

## Why "just use a bandit" is not assumed

A bandit chooses one action and observes one payoff. Strategy evaluation is different in two ways:
(1) shadow/paper returns of all *valid* strategies are observable each round, i.e. full information
within the valid set, which is the setting of expert-advice algorithms and gives far lower regret
than bandit feedback; (2) the output is a weight vector (a portfolio of strategies), not a single
choice. Bandit variants are therefore kept only as comparators (`SleepEXP3`, `DUCB`).

## Semantics that must not be conflated (see 04_SLEEPING_EXPERTS.md)

| Term | Meaning in this study | Allocated? | Learner state updated? |
|---|---|---|---|
| inactive strategy | regime makes the strategy invalid | no | no |
| strategy abstention | valid but declines to act this round | no | no |
| data gap | allocated, result realised but not observed by the learner | yes | no |
| missing evidence | too few observations for an expert (new / dormant / rare) | n/a | prior, not penalty |
| negative evidence | observed reward below peers | yes | yes (down) |
| bad realised performance | observed reward below neutral | yes | yes (via relative comparison) |

Rule under test: **missing evidence must not automatically become negative performance.** The
`naive_zero` mode feeds every non-observed existing expert as worst reward to measure the cost of
violating it.

## Scope limits

Synthetic scenarios only (bench/ensemble_v1). Real strategy P&L has heavy tails, costs, capacity
interactions, non-stationary correlations and delayed/censored outcomes that the generator only
partly represents (10_LIMITATIONS.md). Results are evidence about *algorithm behaviour under
declared mechanisms*, not about profitability.
