# 08 — Bug and implementation check, and capacity conclusion

Rule followed: document, do not fix, do not alter any result. Everything below was found by reading source and re-deriving numbers from committed raw files; nothing was patched.

## Part 1 — Material disagreements: bug or semantics?

For each disagreement in 07, I looked for an implementation cause before accepting a semantic one.

| Item | Bug candidate examined | Verdict |
|---|---|---|
| D1 preemption | Eviction accounting in both engines: A `close(..., "evict")` books `edge·k/d + market − cost − 3`; B `evictions` truncates to `gross(i, t_in, hh) − cost`. Both forfeit remaining edge and pay full cost. B's `OLDEST_SLOT.on_close` feeds a truncated hold into the shared hold estimator, but `OLDEST_SLOT.select` does not use it | consistent accounting; **no bug**; sign reproduced by parameter change in A's engine |
| D2 FIFO vs random | A's `FIFO` sorts by `(-age, cid)`; B's by `(t_first, inst)`. Both are oldest-first. The gap disappears when waiting decay is switched off | **no bug** |
| D3 spam | reading of `env.py` `spam=` vs `world.py` `spam=True` | different threat models, **no bug** |
| D4 K=10 | B sizes arrivals from `mean(dmean)` while realised holds are clipped to ≥1 h, so realised load is slightly above nominal; A's Erlang-B check shows the simulator under-blocks by up to 0.020 | small, in opposite directions, cannot explain a gap of this size; **no bug** |
| D5 slot-hour | A `est()`: `key = net/(dur+h0)`; B `rate = val/h_est`. Both correct for their inputs | information difference, **no bug** |
| D6 label | thresholds | statistical protocol, **no bug** |

## Part 2 — Defects found

### Study A as merged (`main` `1a449df`)
1. **Estimator warm-up bias — CONFIRMED (author-acknowledged).** `Stats.init_stats` sets `self.cov = np.eye(N) * 40.0` and then decays it slowly, so early-period covariance is dominated by the prior. It biases `CORR_PENALTY`, `MARGINAL_RISK`, `CORR_HARD_REJECT` and `COMPOSED` (all consume `corr_hat`). The unmerged branch replaces it with a bias-corrected EWMA (`a = max(1/n, 0.01)`) and reduces shrinkage from 0.2 to 0.05. `main` still contains the flawed version.
2. **Normaliser blow-up — CONFIRMED independently.** The tuning objective divides by `dens0_sd`, which collapses in near-identical worlds. In `tuning_raw.csv.gz` (`main`), `SLOTHOUR_DENSITY − FIFO` is +1.268 z in S12 against 0.011–0.285 in the other eleven families. S12 supplies **48%** of the pooled mean; whether the selected parameters would differ without it was not tested. The branch switches to `dens0_rms`.
3. **Dangling held-out guard.** `runner.heldout()` opens `../prereg/PREREGISTRATION.json`; that file is not on `main`, so the documented held-out entry point fails as committed. Minor.
4. **Erlang-B validation has a systematic bias.** All nine rows show `sim_block < erlang_b` by 0.002–0.020. Consistent with discrete-time rounding of durations; the simulator's own acceptance test passes with a loose implicit tolerance, never stated. Minor, OBSERVED.
5. **Impact.** Every strict-level A number in 05/06 inherits defects 1–2. That is why strict labels are limited to direction and ordering.

### Study A branch (`cb13041`, supplementary)
6. **Unexplained NaN warnings — UNCONFIRMED.** `heldout.log` shows repeated `RuntimeWarning: invalid value encountered in divide` at `policies.py:190` (`S / np.outer(sd, sd)`). `corr_hat` is guarded by `cov_n >= 60` at the decision site, so the cause is not established. If NaNs reach the correlation policies they would silently disable the penalty. I did not find evidence they do; run 2 correlation results (≈ tie with `RANK_NET`) look sane. Needs the author's confirmation.

### Study B (PR #8 `0ff4f71`)
7. **No code defect found.** 77/77 tests pass on a scratch copy; no-lookahead metamorphic test has power (oracle flagged); `frozen_params.json` hash equals the pre-registered hash; ingest confound tested (none); accounting for cost, eviction and capacity read correctly.
8. **Report over-generalisation (documentation, not code).** `14_LIMITATIONS.md` limitation 1 says the ranking gain is "reversing with inversion", and `00_EXECUTIVE_SUMMARY.md` item 9 says "in the separate inversion battery (D4) SCORE_RANK falls below FIFO". The data are mixed: in D4 (`F_inversion`, load 3.0) SCORE_RANK 2.43 < FIFO 2.62 but SLOTHOUR 2.73 > FIFO; in D2 (`inverted`, other base scenario) every ranker, including SCORE_RANK (2.24 vs 1.89), stays above FIFO with the gain cut ≈47%. "Reverses" holds for one method in one battery only. The 13_ADJUDICATION sentence "no policy protects itself online" is fair for absolute performance but not for beating FIFO.
9. **Headline label vs meaning.** `MULTIPLE_CAPACITY_METHODS_SUPPORTED` is produced by |T|=6 under δ=0.25 including `LINTS` (a bandit whose CI includes zero vs SLOTHOUR). B says this itself; a reader of the PR title alone would not know. Framing issue, not error.
10. **`SCORE_RANK` name.** It ranks net value, not raw score. Documented in code (`val = sc − cost_est`); confusing next to Study A's `RANK_SCORE_RAW`.

### Not verified
- I did not re-run B's tuning, validation or held-out; I did re-derive every B contrast used here from the committed CSVs, and re-ran its tests. B's "300 held-out cell re-executions, 0 mismatches" is taken from its report (`determinism_check.json` exists).
- I did not re-run A's leakage suite; I read `validation.json` (135 runs, 0 failures, canaries detected on all 5 cases).

## Part 3 — Capacity conclusion (mission §8)

| Question | Answer | Basis |
|---|---|---|
| Can either study authorise changing `max_open_positions`? | **NO** | Both are synthetic, same-family generators with constructed edge, cost and scores; neither uses AurumShift data or code. B's report 13 states "Nothing about `max_open_positions`, the current allocator, any production policy or any cap"; A has no report and no such claim |
| Can either study authorise deploying an allocator? | **NO** | B: `ANY_DROP_IN_ALLOCATOR=FALSE`. A: no verdict on `main`; run-2 dry run explicitly a dry run |
| Can either study authorise changing PAPER behaviour? | **NO** | no PAPER data, no integration, no runtime coupling in either corpus |
| Are K=3/4/6/10 results anything more than sensitivity? | **NO** | offered load fixed in absolute terms; parameters tuned at K=4 (B) or 4/6 (A), not retuned per K; the two studies disagree on K=10 (07 D4), which is itself evidence the number is generator-dependent |

`CAP_CHANGE_AUTHORIZED=FALSE`, `LOCAL_INTEGRATION_AUTHORIZED=FALSE`.
