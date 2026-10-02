# 02 — Protocol

## Synthetic world (`bench/uncertainty_v1/py/worlds.py`)
* Classes: 0=DOWN (SELL), 1=FLAT (HOLD), 2=UP (BUY). Latent return r = w·x + σ_t·ε; y = UP if r>0.6, DOWN if r<−0.6, else FLAT. Base rates ≈ 27/46/27 %.
* Features x∈R⁶ AR(1) with ρ=0.7 (non-iid). σ_t follows a hidden two-state Markov chain (0.9 / 1.6, persistence 0.985) → clustered volatility (non-exchangeable). 1 % of rows belong to a "rare cluster" with a flipped mapping and shifted features (training sees ~40 of them).
* Oracle posterior P(y|x,σ_t) is exact, so NO_SIGNAL rows (oracle max-probability < 0.5, in-distribution) are known.
* Timeline per seed: train 4000 → calibration 3000 → validation 3000 → held-out 4500 (shift onset at held-out step 1500; pre-onset = in-distribution reference, post-onset = 3000 steps).
* Utility of an action (SELL/HOLD/BUY) vs truth (DOWN/FLAT/UP): correct trade +1, wrong-direction trade −1, trade when FLAT −0.3, HOLD 0. **This payoff is a toy; abstention conclusions depend on it** (see `05_ABSTENTION.md`, `10_LIMITATIONS.md`). Abstain ≡ HOLD.
* Scenarios (magnitude m; tuning m=0.6, held-out m=1.0): `vol_jump` σ×(1+1.5m) · `regime_transition` mapping rotates by 120°·m over 1000 steps · `feature_shift` observed features +1.5m on 4 dims and ×(1+0.3m) (P(y|x_true) unchanged, model sees shifted inputs) · `missing_features` 40 %·m NaN on 3 features, mean-imputed · `stale_features` 3 features frozen for 10·m-step runs (values repeat exactly) · `venue_change` observed x = (1−0.3m)x + 0.5m + 0.8m·noise · `rare_cluster` cluster frequency 1 % → 1+7m %. `iid_control`: ρ=0, iid volatility (conformal only).
* Ground-truth causes per row: DATA_GAP (NaN or stale row), OUT_OF_DISTRIBUTION (post-onset feature/venue rows), MODEL_UNCERTAINTY (rare-cluster rows), NO_SIGNAL (in-distribution & oracle max-prob < 0.5), else NORMAL. Note `DATA_GAP` truth is defined by the injected fault, which is also what the flags detect → **that class is close to tautological**.

## Base models
* `lr`: multinomial logistic regression on [x, x²] — well-specified up to the FLAT-class shape, well calibrated out of the box.
* `gbm`: histogram gradient boosting, 100 iterations, lr 0.3, no early stopping — deliberately over-confident. Missing values: mean imputation (pipeline-level), train mean.

## Splits and freezing (the "no peeking" discipline)
| split | seeds | shift magnitude | used for |
|---|---|---|---|
| train | every seed, first 4000 rows | — | base model |
| calibration | next 3000 rows | — | fit calibrators (static), conformal calibration scores |
| validation | next 3000 rows | — | abstention τ / budgets; history buffer for online methods |
| tuning | seeds 100–103 | 0.6 | hyperparameters: online W, decay half-life, conformal W/HL/γ, diagnosis thresholds, choice of best calibrator |
| held-out | seeds 0–11 | 1.0 | reported numbers, one run per component |
`frozen_config.json` was written before the held-out run of the online, conformal and diagnosis components. Static calibrators have no tuned hyperparameters. Process disclosures: (i) a mask-indexing bug in `regime_transition` was found while smoke-testing conformal code and fixed **before** any held-out output was produced (first static launches were killed and restarted); (ii) GBM size was reduced (150→100 iterations) and static ensembles set to 5 members for runtime before any held-out run; (iii) the abstention harness (budgets 10/25/40 %) was designed after the static and online held-out tables had been inspected, then run once on the same held-out seeds and not tuned; (iv) tuning seeds are 4, held-out seeds 12 — CIs are t-intervals over seeds and are optimistic because scenarios share worlds.

## Label maturity and look-ahead
Row s's label is available at time s+H, H=10. At time t (absolute), an online recalibrator may only use rows s ≤ t−H. Refit every R=50 steps; rows served in a block use the fit at the block start. `tests/test_no_lookahead.py` corrupts every non-matured label and asserts that already-served probabilities are bit-identical; the same test asserts that the deliberately leaky variants (`leak_h0`: H=1, `leak_peek`: sees the next block) *do* change — i.e. the harness detects leakage. Conformal streams are tested the same way.

## Metrics
Brier (multiclass sum of squares), log loss, ECE (10 equal-width bins; equal-mass variant stored), reliability tables (`results/*_reliability.csv`), coverage, selective risk / AURC, abstention rate, **false-confidence**: FCR = P(wrong | conf ≥ 0.6) and CWM = P(conf ≥ 0.6 ∧ wrong) (chance level is 1/3, so 0.6 is "clearly confident"). A calibrated model still has FCR > 0 (a 0.7-confidence prediction is wrong 30 % of the time) — FCR is a penalty to be *compared*, not driven to 0. **Calibration drift** = ECE(post-onset) − ECE(pre-onset); 500-step rolling ECE trajectories. **Decision turnover** = fraction of consecutive steps whose action (BUY/SELL/HOLD, abstain=HOLD) changes. ECE has a small-sample floor (≈0.04 at n=500 with 10 bins, visible in the rolling plots), so differences below ~0.01 are not interpreted.

## Public data (`py/run_public.py`, fetched at run time, nothing redistributed)
ELEC2 (OpenML `electricity` v1; rows 0–6000 train, 6000–9000 calibration, 9000–12000 validation, 12000– held-out; W and half-life chosen on validation among {500,1000,2000}/{250,500,1000}); credit-g and breast-cancer (20 random 40/20/20/20 train/cal/val/test re-splits); California housing (HGB regressor; iid split vs train/cal on the lowest 80 % MedInc and test on the top 20 %). Public tasks are not financial return data.
