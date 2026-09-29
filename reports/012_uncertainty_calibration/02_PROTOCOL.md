# 02 — Protocol (declared before looking at the final numbers)

## Scope / boundary
External research only. No private AurumShift code, no integration claims. Synthetic worlds are *stylised*; none of the numbers are trading performance.

## Data
| Set | What | Role |
|---|---|---|
| **S** synthetic | AR(1)(φ=0.7, φ=0 for exchangeable control) 8-d features; label ~ Bernoulli(σ(w·x[:4] + 0.7·x0·x1)), Bayes accuracy ≈ 0.71; region x7>1 is *pure noise* (true P=0.5). 20 seeds (8 for online, 8 for conformal, 20 for shift/taxonomy), each seed a fresh world | Ground-truth probability known → calibration error against truth measurable |
| **E** ELEC2 (OpenML `electricity` v1, NSW electricity market, 45,312 half-hourly rows, 1996-98) | real, time-ordered, documented drift. Task rewritten as **forecasting**: past-only features at t → label at t+1 (first attempt predicting y_t from a price-minus-past-mean feature leaked the label definition: Brier 0.004 — discarded, see 10_LIMITATIONS) | real non-stationary check |
| **B** breast cancer (sklearn) | exchangeable, small-n (569) | small-sample calibration behaviour |
| **H** California housing (sklearn) | regression, iid vs deliberate covariate shift (MedInc) | conformal PI validity |

## Splits (never mixed)
* Synthetic: train [0:4000] | calibration [4000:7000] | validation [7000:10000] | held-out [10000:16000] (chronological). Shift tests apply a transformation to the held-out block only.
* ELEC2 (after 48-row warm-up): train 0–9000 | cal 9000–13500 | val 13500–18000 | held-out 18000–end in 6 chunks.
* Breast cancer: 65/35 stratified outer split; inner 40% train / 30% cal / 30% val. 20 seeds.
* Online: base model frozen after training; calibrators update only inside the stream.

## Pre-declared decision criteria
* **Calibrated** = top-label ECE ≤ 0.03 on held-out (synthetic, n=6000) *and* better than raw on ECE or log-loss (or raw already ≤ 0.03: "no harm").
* **Calibration survives a shift** = ECE_shift ≤ 0.05 **and** false-confidence rate (FCR) ≤ 1.5× its iid value (+0.01 floor).
* **False-confidence rate** = P(wrong ∧ confidence ≥ 0.8) over all rows; also P(wrong | conf ≥ 0.8) and a confident-wrong penalty mean(1[acted ∧ wrong]·(2·conf−1)).
* **Abstention helps** = at the same coverage, selective risk is lower than *random* abstention (which leaves risk = full risk) **and** utility (payoff ±1, cost 0.2 per trade) is not lower than trading everything, **and** ≥ 50% of correct decisions retained at the operating point.
* **Online recalibration supported** = under drift, PIT-safe online variant beats static on worst-chunk ECE by ≥ 0.02 (mean over seeds, non-overlapping 95% CI) without decision turnover exceeding raw-model turnover by > 20% relative, and its results are far from the lookahead variants' (i.e. no reliance on leaks).
* **Conformal method supported under a setting** = mean coverage within ±0.03 of 1−α **and** ≤ 10% of 500-step windows below 1−α−0.05 (worst-window statistic reported separately).
* **Q4** = per-class recall of a rule cascade ≥ 0.7 for each of the four causes, on generator-labelled pools (upper bound; generator defines the labels).
* Verdict rubric: `UNCERTAINTY_ABSTENTION_REFERENCE_SUPPORTED` needs static + online + abstention + conformal (at least one non-iid-valid method) supported *and* calibration surviving most shifts; `LIMITED_...` = some supported with named limits; `NO_ROBUST_...` = none; `STUDY_INCONCLUSIVE` = evidence insufficient/contradictory.

## Metrics
Brier, log-loss, top-label ECE, positive-class ECE, reliability tables, coverage, selective risk, abstention rate, bad-decisions-avoided, good-decisions-retained, FCR (3 forms), utility, AUROC of shift detectors, ECE drift (per-chunk and worst-chunk ECE), decision turnover (fraction of consecutive steps whose BUY/SELL/HOLD changes), conformal coverage (marginal / rolling-window / worst-window), singleton rate, singleton accuracy.

Decision mapping: `p ≥ τ → BUY`, `p ≤ 1−τ → SELL`, else `HOLD`. τ = 0.6 (cost-model τ* for c = 0.2). Accuracy alone is never used as a headline.

## Statistics
Mean over seeds with 95% t-type interval (1.96·sd/√n). Where seeds are few (online n=8, conformal n=8) intervals are approximate; ELEC2 has a single realisation (no interval).

## Code
`bench/uncertainty_v1/py/`: `ulib.py` (library), `exp_static.py`, `exp_shift.py`, `exp_taxonomy.py`, `exp_online.py`, `exp_conformal.py`. Raw CSVs in `bench/uncertainty_v1/results/`.
