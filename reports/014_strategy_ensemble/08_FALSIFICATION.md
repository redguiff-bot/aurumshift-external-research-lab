# 08 — Falsification

Each hypothesis was stated so that a held-out result could refute it. `PR` = pooled held-out regret ×1e-3
(lower = better); best baseline = WTA 11.69 (EWMA 11.83, Static 24.92, Equal 63.34).

| # | Hypothesis | Result | Status |
|---|---|---|---|
| H1 | A sleeping/specialist method beats the best baseline by ≥10% (CI excl. 0) without a regime label | best non-context: DiscFreeze 0.91×, BMA 0.94×, SleepHedge 1.13×, FixedShare 1.14× | **FALSIFIED** |
| H2 | Treating missing/inactive as negative evidence costs materially | +13…+27 regret units, 2.0–3.3× | **SUPPORTED (strong)** |
| H3 | Simple EWMA is sufficient | Best baseline overall (WTA/EWMA within 1%), but +53% regret on informative abstention (S6d), +25% on MCAR gaps vs sleeping update, starves an unlucky-start specialist (0.014), brittle to its own hyper-parameters (17 grid points: 11.9 … 51.1) | **PARTLY FALSIFIED** |
| H4 | Static fixed weights are sufficient | 2.1× the best baseline; 3.2–4.0× in leadership/composite scenarios | **FALSIFIED** |
| H5 | Bounded weights (floor/cap) protect small experts at acceptable cost | tuned toward no bounding; PR 23–25 vs 12–13 | **FALSIFIED here** (insurance never paid back) |
| H6 | A bandit is the right frame | SleepEXP3 5.1×, DUCB 1.5× the best baseline; full information among valid experts is available | **FALSIFIED** as the primary frame |
| H7 | Diversity-aware weighting helps | DivSH ≡ SleepHedge, DivEWMA +0.8% | **NOT SUPPORTED** (objective is risk-neutral) |
| H8 | Context-conditioned mixture helps under regime recurrence | CtxLag 0.90×, CtxOracle 0.71× — but see label-noise curve | **SUPPORTED, conditional** |
| H9 | New expert / dormant specialist are not starved | S3 and S2: not starved (freeze semantics + neutral init); S7 unlucky start: starved under WTA/EWMA/BMA | **PARTLY SUPPORTED** |

## Label-noise break-even for the context mixture (held-out seeds 1000–1019, tuned CtxOracle hp)

| label flip prob p | PR ×1e3 | ÷ WTA | ÷ EWMA |
|---|---|---|---|
| 0.00 | 8.32 | 0.72 | 0.71 |
| 0.05 | 10.18 | 0.87 | 0.86 |
| 0.10 | 11.88 | 1.02 | 1.01 |
| 0.20 | 14.42 | 1.24 | 1.22 |
| 0.30 | 16.31 | 1.40 | 1.39 |
| 0.50 | 18.95 | 1.63 | 1.61 |

The label is flipped to a uniformly random regime with probability p (so accuracy = 1 − 0.75p). The context mixture beats the best baseline by ≥10%
only for p ≲ 0.066 (accuracy ≳95%, linear interpolation); break-even at p≈0.10 (accuracy ≈92.5%); at p=0.2 (accuracy 85%) it is 24% *worse*. Whether AurumShift can supply such a label is UNKNOWN from this repo.

## Hyper-parameter sensitivity (fresh seeds 3000–3007, all grid points incl. extension; PR ×1e3)

| method | #grid points | best | median | worst |
|---|---|---|---|---|
| DiscFreeze | 12 | 10.8 | 11.0 | 12.4 |
| SleepHedge | 6 | 13.4 | 13.4 | 14.3 |
| WTA | 3 | 11.8 | 13.2 | 13.9 |
| CtxLag | 19 | 10.5 | 12.6 | 22.2 |
| EWMA | 17 | 11.9 | 15.0 | 51.1 |
| BMA | 38 | 11.0 | 12.9 | 47.1 |
| FixedShare | 17 | 13.4 | 16.4 | 36.5 |
| CtxNoisy | 19 | 14.4 | 15.4 | 23.3 |

Robust: DiscFreeze, SleepHedge (flat). Brittle: EWMA, BMA, FixedShare, Ctx*. Note the optimum of several rules sits
on the "concentrate hard" edge (SleepHedge η=400, EWMA β=400): the generator rewards near-winner-take-all.

## Deviations from the pre-registration (declared)

Two gate definitions were mis-specified by me and are visible only in hindsight:
1. **G4a** measured worst-scenario ratio against "the best non-bandit method", which included `CtxOracle` — a method that
   uses the true regime label and which I had already declared ineligible as a verdict basis.
2. **G4b** required PR ≤ the best baseline exactly, so any baseline other than the best fails by construction (EWMA fails by 1%).

The literal result is reported in 09. A post-hoc amendment (G4a reference excludes CtxOracle; G4b 5% tolerance) is reported
alongside and labelled `POST_HOC`. No threshold on G1 (10%) or G2/G3 was altered.
