# 10 — PR #8 disposition

Repository/corpus disposition only. No AurumShift integration. I did not merge, comment on, or modify PR #8.

## Decision

**`REQUIRES_CORRECTION_BEFORE_MERGE`**

The results are sound and independent; the corrections are small, textual, and about provenance and claims. After them I would move it to `MERGE_AS_INDEPENDENT_REPLICATION`.

## Why not the other three

| Option | Verdict | Reason |
|---|---|---|
| `SUPERSEDED_BY_PR6` | **No** | PR #6 is a work-in-progress snapshot of a run its own authors retired: no held-out, no pre-registration, no reports, no verdict, estimator and normaliser defects (08). It cannot supersede a completed, pre-registered, tested study. If anything, the reverse is true today |
| `KEEP_DRAFT_AS_RESEARCH_ARCHIVE` | **No** | PR #8 is a full protocol-clean study: tests 77/77 pass (my run), pre-registration precedes held-out in git, frozen-parameter hash verified, no code defect found. Archiving would discard the only completed held-out evidence in the repository |
| `MERGE_AS_INDEPENDENT_REPLICATION` | **Not yet** | Merging now would put two same-named implementations under `bench/capacity_v1/`, one of them retired, with nothing to tell a reader which is which, and would publish two claims (below) that its own data do not fully support |

## Corrections required (none touch results or code)

1. **Fix the inversion claim.** `reports/008…/14_LIMITATIONS.md` limitation 1 ("reversing with inversion") and `00_EXECUTIVE_SUMMARY.md` item 9 ("SCORE_RANK falls below FIFO") generalise from one battery. In D4 `SCORE_RANK` < FIFO but `SLOTHOUR` > FIFO; in D2 every ranker remains above FIFO with the gain cut ≈47% (08 item 8). Restate as "gain shrinks by roughly half with poor or inverted calibration; in one battery `SCORE_RANK` falls below FIFO".
2. **Qualify the headline label.** Add to `00_EXECUTIVE_SUMMARY.md` and the PR body that `MULTIPLE_CAPACITY_METHODS_SUPPORTED` follows from |T|=6 under a permissive δ=0.25 bps (57% of the best simple method's gain) and that the best complex method adds a detectable +0.062 (14%); the verdict does not say six algorithms are needed.
3. **Add provenance.** A short `bench/capacity_v1/README.md` section (or a directory rename) stating: this implementation is independent of `py/` on the default branch; the default-branch `py/` content is an early snapshot of a run its author later retired; the two must not be pooled. This also removes the file-layout ambiguity the PR body already raises.
4. **Repair the PR state.** PR #8 is open and non-draft while its own body asks for a maintainer decision on a parallel session; convert to draft or record the decision. Re-check for conflicts once Study A's branch lands, since both write under `bench/capacity_v1/results/`.

## Not required
- No re-run, no re-tune, no change to frozen parameters or held-out files.
- No change to the K=10 or preemption statements: they are correctly labelled synthetic and assumption-dependent (07 D1, D4).

## After Study A completes
Re-run this adjudication when Study A's held-out finishes and run 2 is merged (or PR #6 is amended to say it is superseded). The supplementary column of 05 predicts most of it will replicate; the strict column will then be recomputable on a like-for-like basis.
