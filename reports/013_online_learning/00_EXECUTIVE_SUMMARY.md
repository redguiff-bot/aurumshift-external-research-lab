# 00 — Executive summary: online learning / continual adaptation (external research, synthetic)

**Verdict: `LIMITED_ONLINE_METHODS_SUPPORTED`.** External research only; no AurumShift code, no market data, no integration claim. Streams are synthetic with a known truth; see 10 for what that does *not* license.

## What was done
* Studied 12 candidate families (01); **executed 15 candidate algorithms (19 model×track entries) + 3 baselines** (frozen, expanding batch retrain, bounded rolling refit) — River 0.26.1 estimators plus small numpy RLS/Kalman/Platt/reset/bank wrappers (07).
* 10 drift scenarios × 2 tracks × 15 held-out seeds (3 750 runs), hyper-parameters frozen on separate tuning seeds, a 3×-lower-SNR sensitivity run (600 runs) and a replay/checkpoint/leakage suite with a negative control (`bench/online_learning_v1/`). Decision rules were committed **before** the held-out run (02).

## Findings (OBSERVED)
1. **Ignoring drift is expensive**: frozen 5.4× (C) / 7.9× (R) and expanding batch retrain 3.1× / 5.2× the regret of a bounded rolling refit on the 8 drift scenarios.
2. **Bounded rolling refit is a hard baseline.** Only two incremental methods clear all four pre-registered gates: **RLS with forgetting (track R, 0.85× rolling)** and **SGD-logistic with a drift bank (track C, 0.88×)**. No method passes on both tracks. Gain vs the best simple reference: 12–15 %; ≈20–28 % at 3× lower SNR (untuned).
3. **Complexity does not earn its place beyond linear recursive estimators.** Hoeffding trees, adaptive trees, ARF and ADWIN-bagging are 2.6–5.2× *worse* than rolling, grow state ×4–6 and cost 0.04–1.1 ms/label; ADWIN-triggered resets are no better than the plain learner they wrap.
4. **Recurring states:** only the explicit memory bank recovers cheaply (return-cost 0.42 C / 0.34 R; 39 vs 431 steps) at the price of worse tracking in gradual/random-walk drift.
5. **Determinism:** all 25 (model,track) entries replay bit-for-bit in-process and across interpreters, restore identically from a pickle checkpoint, and show no future leakage; a cheating model is caught by the same test. One platform only.
6. **Fragility:** un-guarded SGD/BLR/ARF/HAT break on a pure feature-scale/noise shock ("false drift"; 1.6–29× rolling). Any adopted online learner needs a scale guard.

## What to take away
* Reference design (research-level): **bounded rolling refit as baseline; RLS-with-forgetting (or SGD-logistic) as the incremental challenger; optional snapshot bank only if recurrence is demonstrated on real data.**
* Do **not** conclude the same on real markets: SNR, tails, autocorrelation, and drift geometry are unmeasured (10).

Files: 01 landscape · 02 protocol · 03 scenarios · 04 results · 05 forgetting · 06 determinism · 07 OSS · 08 falsification · 09 adjudication · 10 limitations · code/results in `bench/online_learning_v1/`.

## Final block
```
ALGORITHMS_DISCOVERED=12 families (+ 5 named but not executed: AdaBoost/ADWINBoosting/SRP/LeveragingBagging, VW/MOA)
ALGORITHMS_EXECUTED=15 candidate algorithms (19 model×track entries) + 3 baselines

FROZEN_BASELINE=executed; 5.4x (C) / 7.9x (R) rolling-refit regret under drift; best only when stationary/shock
BATCH_RETRAIN_BASELINE=executed (expanding, period 250); 3.1x (C) / 5.2x (R) rolling-refit regret under drift; best on stationary/false-drift controls

ONLINE_ADAPTATION_BENEFIT=12% (C, bank_sgd_log 0.88 [0.87,0.90]) to 15% (R, rls 0.85 [0.84,0.85]) below a tuned rolling refit; ~20-28% at 3x lower SNR (untuned); synthetic only
RECURRING_STATE_RECOVERY=only with explicit memory bank (return-cost 0.42 C / 0.34 R; 39-40 vs 373-431 steps); all single-state learners ~1.0
DETERMINISTIC_REPLAY_SUPPORTED=YES (25/25 entries: replay, cross-process, checkpoint, no-leak; negative control detected; single platform)

BEST_SIMPLE_REFERENCE=bounded rolling-window refit (window 150-300, refit every 25)
BEST_INCREMENTAL_REFERENCE=rls (RLS, lambda=0.99) for regression; bank_sgd_log (SGD logistic + drift bank) for classification

FINAL_VERDICT=LIMITED_ONLINE_METHODS_SUPPORTED
```
