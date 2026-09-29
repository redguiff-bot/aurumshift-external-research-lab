# 11 — Final adjudication (external, generic)

Boundary: all classifications below come from an **external synthetic benchmark**. `ADOPT_REFERENCE` means only *"strong external reference policy for future local evaluation"* and **does not authorise any AurumShift integration**; none was built. Policy A is the operator-supplied contract (00 §2.2), not V1 evidence. Conclusions are of the form *"policy implementation X showed behaviour Y under held-out benchmark Z"* — no library is ranked from these results (10).

## 1. Required output block

```
TRAIN_SCENARIOS=T1_mixed_abrupt, T2_mixed_drift_gap, T3_churn_lowinfo, T4_dormancy_rare   (seeds 1000-1004)
VALIDATION_SCENARIOS=V1_coldstart_outage, V2_abrupt_then_drift, V3_silence_rare_lowinfo    (seeds 2000-2004)
HELDOUT_SCENARIOS=S1_MASSIVE_COLD_START, S2_ABRUPT_REGIME_CHANGE, S3_SLOW_DRIFT, S4_TEMPORARY_SILENCE,
                  S5_PROVIDER_DATA_GAP, S6_STALE_BUT_VALID, S7_GENUINELY_LOW_INFORMATION,
                  S8_RARE_HIGH_INFORMATION, S9_LONG_DORMANCY_RETURN, S10_DYNAMIC_POPULATION  (seeds 3000-3019, 20 per scenario)

POLICY_A_LIFECYCLE_FLOOR=EXECUTED (operator-supplied contract, fixed, not tuned; evidence-derived classifier is V2-defined)
POLICY_B_DUCB_GUARD=EXECUTED (custom D-UCB idea + guard + backoff; tuned on TRAIN/VALIDATION: gamma 0.9995, S 25, M 4)
POLICY_C_RIVER=EXECUTED (river 0.26.1 EpsilonGreedy+EWMean as shipped, hygiene wrapper; tuned: fading 0.1, eps 0.2); C2 = C + shared guard (diagnostic)
POLICY_D_VW=EXECUTED (vowpalwabbit 9.11.9 cb_explore_adf, shared observable features, no id feature; tuned: epsilon 0.2, lr 0.05, group feature off) — valid formulation existed; not NOT_EXECUTED_FOR_VALIDITY

HELDOUT_ISOLATION=PASS   (17 automated checks, results/isolation_report.json; 18/18 unit tests)

NEW_ARM_STARVATION_A=NOT_OBSERVED (0 % of new cells unseen; mean per-run max first attempt 8 cycles)
NEW_ARM_STARVATION_B=NOT_OBSERVED (0 %; max 8 cycles)
NEW_ARM_STARVATION_C=OBSERVED (4.7 % of new cells never attempted in S1, 12.6 % in S10; mean per-run max first attempt 306 cycles)
NEW_ARM_STARVATION_D=OBSERVED_MILD (0.7 % S1, 2.1 % S10; mean per-run max first attempt 114 cycles)   [C2: 0 % S1, 7.8 % S10]

SILENT_CELL_CAPTURE_A=NOT_OBSERVED (+2.4 to +3.4 pts over uniform baseline: proportional, floor-driven; X1 permanent silence: information 0.304 < round-robin 0.336)
SILENT_CELL_CAPTURE_B=NOT_OBSERVED with the frozen backoff (-2.6 to -11.2 pts vs baseline); OBSERVED if backoff disabled (M=1: 67 % of attention on permanently silent cells in X1)
SILENT_CELL_CAPTURE_C=OBSERVED (+2.4 S4, +10.6 S5, +26.4 pts S9: 39.5 % of attention on silent cells vs 13 % baseline)
SILENT_CELL_CAPTURE_D=NOT_OBSERVED in S4/S5/S9 (-0.3 to -4.0 pts); OBSERVED in post-hoc X5 (+17 pts)   [C2: -2.8 to -11.5 pts]

REGIME_ADAPTATION_A=NONE (adaptation delay censored in 100 % of S2/S3/S9 runs; = round-robin)
REGIME_ADAPTATION_B=YES, moderate (delay S2 54 / S3 174 / S9 60 cycles; 0 % censored)
REGIME_ADAPTATION_C=YES but with starvation/capture (S2 89, S3 215, S9 9 cycles; 10 % censored in S2)
REGIME_ADAPTATION_D=YES, moderate (S2 82 / S3 183 / S9 32; 5 % censored in S3, S9)   [C2: S2 95, S3 199, S9 censored 100 %]

PARAMETER_ROBUSTNESS_A=ROBUST (trivially: floor 0-20 %, flat/steep weights, alt classifier all leave behaviour ~ round-robin)
PARAMETER_ROBUSTNESS_B=SENSITIVE (0.69 acceptable; gamma trades information vs adaptation, S trades coverage vs information, M=1 is unsafe)
PARAMETER_ROBUSTNESS_C=BRITTLE (0.10; no configuration free of starvation)
PARAMETER_ROBUSTNESS_D=BRITTLE (0.27; learning-rate / exploration dominated)   [C2: SENSITIVE 0.40, borderline]

BEST_EXTERNAL_REFERENCE=B (D-UCB + staleness guard + bounded no-evidence backoff)
BEST_ADAPTIVE_CANDIDATE=C2 (River primitives + shared guard: best information and best worst-case information; needs a fix for cold start and return-from-dormancy) — runner-up B

ANY_POLICY_DOMINATES_ACROSS_HELDOUT=NO
ANY_SCIENTIFIC_INVALIDATION=NO

FINAL_VERDICT=ADAPTIVE_POLICY_SUPPORTED_FOR_LOCAL_EVALUATION
```

Verdict strength: **MODERATE** (synthetic model; 20 seeds × 10 fixed scenarios; A's classifier V2-defined; B selected at grid edges). Why this verdict rather than `NO_POLICY_DOMINATES`: the latter is *also true* and is reported as `ANY_POLICY_DOMINATES_ACROSS_HELDOUT=NO`; the verdict list asks which decision the evidence supports. The evidence supports evaluating an *adaptive* policy locally: `B` is non-dominated, showed no catastrophic failure in 10 held-out scenarios and 5 post-hoc attacks, beats the fixed reference `A` on information gain in 10/10 scenarios and 200/200 seeds with a practically negligible coverage cost, and is deterministic. It does **not** support "the lifecycle reference wins", "any library wins", or "B generalises".

## 2. Per-policy classification

| Policy | Class | Confidence | Evidence (label: OBSERVED in this model unless stated) | Would change it |
|---|---|---|---|---|
| **B — D-UCB + staleness guard + backoff** | **ADOPT_REFERENCE** (strong external reference for local evaluation) | Medium | pooled info 0.649 (A 0.508), starvation 0.005, silent excess −0.025, +0.141 vs A [0.138, 0.144]; 0 catastrophic failures in X1–X5; deterministic (18/18) | local replay contradicting synthetic silence/return model; a fleet where `S·M` exceeds the real cycle structure; parameters selected on real data at grid edges |
| **C2 — River + shared guard** (diagnostic composition) | **ADAPT_CANDIDATE** | Medium-Low | best information (0.757) and worst-case (min 0.657), starvation ≤ 0.077 in every run; but 35-cycle new-cell latency and 100 %-censored return in S9 | a fix of cold start (e.g. force unseen cells, as B does) and phase-independent return detection, then re-validation on fresh held-out seeds |
| **A — operator-supplied lifecycle-weighted reference** | **ADAPT_CANDIDATE** (keep as the fixed baseline in any local evaluation; its skeleton is sound, its constants give no adaptation) | Medium | ≡ round-robin on information (Δ +0.001, below threshold), zero starvation and stale ≈ 0, exact conservation (7e-15), all semantic invariants hold; adaptation censored 100 %; below round-robin in X1; behaviour insensitive to floor/weights/classifier (07) | a local state model that reacts within < 20 evidence events, or the real private classifier — **untested here, UNKNOWN** |
| **D — VW shared-feature contextual policy** | **PARK** | Low-Medium | valid, leak-free, executed; information ≈ C (0.728), starvation 0.073, BRITTLE (0.27), ≈ 100× cost; group/feature sharing brought no measurable gain (dev: `grp0` ≥ `grp1`; sensitivity: differences within noise) | features that truly co-move across cells (regime descriptors), `--epsilon_decay` champion/challenger, or a cost budget that tolerates VW |
| **C — River bandit as shipped** | **REJECT** (as an attention allocator) | High (for this behaviour; library quality is separate, 10) | starvation 0.147 (worst 0.274), max starvation 289, 4.7–12.6 % new cells unseen, silent capture +26 pts in S9, BRITTLE (0.10); reproduces V1's in-sample finding on independent scenarios | none within this benchmark; River primitives inside a guarded composition are a different object (C2) |

## 3. What survives from V1 (V1 labels quoted; nothing upgraded)

| V1 statement (V1 label) | V2 outcome |
|---|---|
| Reward-greedy library policies starve (PROVEN in-sample, V1 03 §3) | **Survives out-of-sample** in a new model: C and D starve (0.147 / 0.073 pooled), OBSERVED |
| Silent cells capture attention under forgetting/UCB rules when no-evidence is not modelled (PROVEN in-sample) | **Survives and is sharpened**: B without backoff is captured (67 %, X1); River-ε with frozen estimates is captured (S9: 39.5 %); with backoff the effect vanishes — OBSERVED |
| D-UCB γ frontier: coverage ↔ adaptation (PROVEN in-sample) | **Survives** as OBSERVED: γ trades information/adaptation (07); the coverage side moved to the guard interval `S` |
| Staleness guard + discounting is "the right direction" (INFERENCE, in-sample, own code) | **Partly survives**: B is the safest adaptive candidate out-of-sample; **but** its safety depends on the V1-untested backoff (OBSERVED), its parameters sit at grid edges, and a guarded River (C2) reaches higher information |
| No-evidence backoff untested (V1 04 P4, UNKNOWN) | **Now OBSERVED**: without it B fails; with it, return latency ≤ `S·M` (phase-dependent) is the price |
| VW feature sharing untested (V1 UNKNOWN) | **Tested here**: no measurable benefit with the group/observable features used; VW is brittle and slow — OBSERVED; richer features remain UNKNOWN |
| MABWiser rejected, River strongest reusable component | MABWiser not re-run (not a V2 contender). River-as-shipped is rejected as an allocator (C), River primitives inside a guard are competitive (C2) — consistent with V1's "primitives, not policy" ranking; not a library ranking |

## 4. Scientific validity review (mission §19)

* **Held-out isolation:** PASS (17 automated checks, 02 §4, `results/isolation_report.json`). No held-out result influenced any parameter; selected files were committed (`3328e4d`) before the held-out results (`d98ef1a`).
* **Defects found and handled** (none invalidated a result):
  1. `tune.py` tie-break implemented as "train rank" instead of the pre-registered "nearest the grid centre" — detected before any held-out run; corrected; **all four tunings re-run**; changed selections documented (01 §9).
  2. `analysis.py` referenced a metric without a pre-registered threshold (`new_never_attempted`) — crashed on first execution *after* Phase B; the metric was removed from the dominance set (it is still reported); analysis re-run; raw results untouched.
  3. Pilot invariant tests executed policies on pilot seeds before the freeze commit; no metric was read; disclosed in `freeze_manifest.json`.
  4. `X3` shows `info_ratio` degenerates (=1) when the oracle has nothing to find; reported as a metric limitation, not a policy result.
* **Held-out contamination check for sensitivity/adversarial work:** performed on held-out generators/seeds but strictly descriptive/post-hoc, no re-selection; marked as such.
* **No stop condition triggered:** every dependency installed and ran reproducibly; VW feature sharing was definable without leakage; no defect invalidated earlier outputs. Hence `ANY_SCIENTIFIC_INVALIDATION=NO` (this is a statement about defects found, not proof that none exist: UNKNOWN).

## 5. Remaining unknowns

Behaviour on real evidence latency/rewards; > 250 cells; the private lifecycle classifier feeding A; cross-machine determinism; heavier-tailed noise; correlated change-plus-silence; River drift detectors as restart triggers (V1 PARK); VW `--epsilon_decay`; open-issue backlogs of River/VW; whether `S`, `M` in cycles have any meaning outside this simulation.

## 6. Reproduce

```bash
python3 -m venv v && . v/bin/activate && pip install -r bench/v2/environment/requirements.lock.txt
cd bench/v2 && PYTHONPATH=src pytest -q tests                # 18 tests
cd src && python tune.py B && python tune.py C && python tune.py C2 && python tune.py D   # dev tuning (writes configs/selected_*.json)
python heldout.py --seeds 20                                   # Phase B (exclusive-create; refuses to overwrite)
python analysis.py && python determinism.py && python verify_isolation.py
# descriptive/post-hoc: sensitivity.py <A|B|C|C2|D>, sens_summary.py, adversarial.py, adv_followup.py
```
Stopped here as instructed: no AurumShift integration implemented.
