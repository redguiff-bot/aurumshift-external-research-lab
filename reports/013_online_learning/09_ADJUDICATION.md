# 09 — Adjudication (external research; ADOPT / ADAPT / PARK / REJECT — not an integration decision)

Verdict is computed from the pre-registered rules in 02 §7 by `py/analyze.py` and may not be overridden here.

* Earns place on **track C**: `bank_sgd_log` only. Earns place on **track R**: `rls` only. No method earns it on both → rule "passes on one track only" → **`LIMITED_ONLINE_METHODS_SUPPORTED`**.
* Ranking agreement tuning vs held-out: Spearman 0.97 (C), 0.72 (R) → not `STUDY_INCONCLUSIVE`.
* Some incremental methods pass (a) → not `BATCH_RETRAIN_REMAINS_SUFFICIENT` (but see the honest reading below).
* Winners pass (b)–(d) → not `NO_ROBUST_ADAPTATION_METHOD`.

| candidate | call | reason |
|---|---|---|
| **Bounded rolling refit** (window ~150–300, refit every 25) | **ADOPT as the reference baseline** | 3–8× better than frozen/batch under drift, bounded state (18–35 KB), bit-replayable, no detector; only 12–15 % behind the best incremental methods |
| **RLS with forgetting (λ≈0.99)** — regression | **ADOPT as incremental reference (R)** | 0.85× rolling, 840 B state, 11 µs/update, replay/checkpoint OK, passes all 4 gates; CUSTOM ~10 LOC (no library needed). Guard-rail: no scale-shock protection (worst scenario 0.98× — fine here) |
| **SGD logistic + drift-bank (`bank_sgd_log`)** — classification | **ADAPT (guard-railed)** | passes all gates (0.88×; worst 1.14× on gradual), is the only method that exploits recurrence (0.42 return-cost); CUSTOM wrapper, benefit specific to recurring regimes whose existence in real data is UNKNOWN. Plain `sgd_log`/`sgd_log_platt` are within 2–8 % of it without the machinery |
| `sgd_log_platt`, `sgd_log`, `reset_sgd_log`, `pa_*` | PARK | ≤10 % gain or fail no-blow-up (false_drift 2.4× for un-calibrated SGD); online Platt helps stability but slows re-adaptation |
| `blr` (BayesianLinearRegression, smoothing 0.98) | PARK | best raw R regret (0.78×) but 1.58× worse than rolling on the feature-scale shock; needs a scale guard |
| `kalman`, `sgd_lin`, `par_reg`, `reset_rls`, `bank_rls` | PARK | ≈ rolling or worse (1.05–1.25×); Kalman under-explored (grid edge) |
| HT / HAT / ARF / ADWIN-bagging | **REJECT for this use** | 2.6–5.2× worse than rolling, state ×4–6 growth, 0.4–1.1 ms/label, highest seed variance; nonlinear-concept edge negligible (ARF −4 %) |
| Frozen / expanding batch | REJECT as adaptive answer; KEEP as controls | best (batch) only when nothing moves |

## Honest reading of the verdict
The mission's question was "does complexity earn its place?". The measured answer is: **barely, and only for the simplest recursive estimators**. A tuned bounded rolling refit is already within 12–15 % of the best online method; drift detectors, forests and boosting add nothing here; the only mechanism with a *distinct* capability is recurrence memory (banked snapshots), which is a niche. That the formal rule yields `LIMITED_ONLINE_METHODS_SUPPORTED` rather than `BATCH_RETRAIN_REMAINS_SUFFICIENT` hinges on the pre-registered 10 % / CI threshold: with a 15 % threshold `rls` (0.85) would only just pass and `bank_sgd_log` (0.88) would not. Results are synthetic, so this must be re-run on real point-in-time data before any policy depends on it (10).

## Suggested next study (not done)
Re-run `rolling` vs `rls`/`bank_sgd_log`/`blr`+scale-guard on real, PIT-safe data with the same harness (`bench/online_learning_v1/py/harness.py` already enforces arrival-time discipline), including per-window re-tuning of the rolling baseline.
