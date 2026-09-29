# Pre-registration — ensemble_v1 (frozen BEFORE tuning and BEFORE any held-out run)

Everything below is committed before `tune.py` / `heldout.py` are executed. Thresholds are
deliberately simple and arbitrary-but-declared; raw numbers are always reported so a reader can
re-judge with other thresholds.

## Data split
* Tuning seeds: 0..5 (6 seeds x 12 CORE scenarios), T=1200, default snr=1, noise=1.
* Held-out seeds: 1000..1039 (40 seeds). Never used for tuning. Parameters frozen from tuning.
* Stress held-out: seeds 2000..2019 x {snr=0.5,noise=1}, {snr=1,noise=1.6}. Reported, gates G4b.
* Tuning objective per method: mean over CORE scenarios of mean per-round expected regret to the
  truth oracle (equal scenario weight). Ties -> first grid point. Grid edges are flagged, and one
  extension round is allowed per method (documented); no held-out data are ever touched.
* Div* wrappers use the tuned base parameters of EWMA / SleepHedge (stage 2).

## Primary metric
PR(m) = mean over CORE scenarios of mean_t [ max_{i allocated} mu_it - sum_i w_it mu_it ]
(noise-free expected regret; realised reward is also reported).

## Gates (candidate m; baselines are scored on G2-G4 too)
* G1 accuracy: PR(m) <= 0.90 * PR(best baseline) AND paired bootstrap 95% CI over seeds
  (2000 resamples) of PR(best baseline) - PR(m) excludes 0. Best baseline = min held-out PR among
  {Equal, Static, WTA, EWMA}.
* G2 missing-evidence semantics: (a) regret in S6a, S6b, S6d each <= 1.5 x own regret in S0;
  (b) for methods in NAIVE_SUBSET, PR under `naive_zero` (missing/inactive fed as worst reward)
  is worse than under correct semantics with paired CI excluding 0.
* G3 starvation:
  (a) new expert (S3): median allocated rounds until trailing-25 mean weight >= 0.25 is <= 150 and
      >= 80% of seeds reach it within the 400 cap;
  (b) rare specialist after dormancy (S2, 2nd episode, first 25 allocated rounds): mean weight of
      the specialist >= 0.35;
  (c) temporary underperformance (S7): median rounds to recover 50% of pre-patch weight <= 100.
* G4 robustness: (a) in no CORE scenario is regret > 1.5 x the best non-bandit method's regret in
  that scenario; (b) PR under each stress set <= PR of the best baseline on that stress set.

## Families
A = sleeping/specialist lineage (SleepHedge, SleepEG, FixedShare, DiscFreeze, DiscAmnesty,
    SH_bounded, CtxOracle/Lag/Noisy, DivSH)
B = score/EWMA lineage (EWMA, EWMA_bounded, WTA, BMA, DivEWMA), plus Static, Equal
C = bandit comparators (SleepEXP3, DUCB), HedgePlain = non-sleeping Hedge reference.
Context variants using the true current regime label (CtxOracle) are an optimistic upper bound and
are not eligible to be the sole basis of a verdict (CtxLag / CtxNoisy are).

## Verdict rules (evaluated in this order)
1. NO_ROBUST_ENSEMBLE_METHOD if no method (baselines included) satisfies G2-G4.
2. STATIC_OR_EWMA_SUFFICIENT if Static or EWMA satisfies G2-G4 and PR <= 1.10 x min PR over all
   eligible methods (i.e. no candidate is materially better).
3. MULTIPLE_ENSEMBLE_METHODS_SUPPORTED if candidates from >= 2 different families (A,B) satisfy
   G1-G4, or >= 2 family-A methods satisfy G1-G4 with PR within 10% of each other and neither is
   dominated (CI) by the other.
4. SLEEPING_EXPERT_REFERENCE_SUPPORTED if the passing set (G1-G4) is exactly family A with a
   single best method (PR more than 10% below the others or CI-separated), and family B fails G1
   or G3.
5. STUDY_INCONCLUSIVE if the verdict of rules 1-4 changes when the top method is replaced by its
   neighbouring grid point (sensitivity) or when the stress set is substituted for the held-out set.
Bandit comparators cannot be the verdict; they are reported for comparison only.

## Caveats declared in advance
* Synthetic generator; every effect is bounded by what the generator can express.
* Experts are shadow-evaluable (full information among observed experts) — an assumption.
* No real market data are used; nothing here claims compatibility with private AurumShift code.
