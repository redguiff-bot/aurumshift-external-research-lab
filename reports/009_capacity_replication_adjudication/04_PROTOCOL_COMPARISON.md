# 04 — Protocol comparison

"A-merged" = Study A on `main`. "A-run2" = unmerged branch tip `cb13041` (supplementary). "B" = PR #8.

| Item | A-merged (run 1) | A-run2 (unmerged) | B (PR #8) |
|---|---|---|---|
| Tuning separation | Yes: seeds 1000+, own variant RNG (11). **Two rounds**: round-2 grids were extended after inspecting round-1 results, so grid edges were chosen with tuning data in view | Same design, rerun on corrected code | Yes: seeds 1000–1005, split `tuning`; grid + ingest mode tuned; grid-edge optima disclosed (limitation 11) |
| Validation separation | Code and seeds defined (2000+, RNG 22), **no policy results committed** | Executed (12 families × 3 variants × 4 seeds × 4 caps); used to pick a shortlist and to set thresholds | Executed (seeds 2000–2007); top-3 of tuning re-run, best frozen |
| Held-out separation | Defined (9000+, RNG 33, jitter 0.65–1.5, 3 held-out-only compositions); **not run** | Not run when analysed; log holds only warnings | Structurally different world parameters, seeds 3000–3019; run once |
| Pre-registration | **None** (hash check in `runner.heldout()` refers to a missing file) | v1 written after seeing validation; superseded; v2 written after re-tuning and validation | `prereg.json` committed in `ad2adda` before any held-out file; rule text, δ margin, code and params sha256 |
| Threshold provenance | n/a | δ_material 0.10, δ_equiv 0.02 "set on the new scale **after seeing validation**" | δ=0.25 bps "INFERENCE: ≈10% of typical FIFO M1", set after tuning/validation, before held-out; sensitivity 0.1/0.5 reported |
| Held-out reuse | n/a | n/a | H1, H2, H3 share seeds 3000–3009 by design (pre-registered, H2/H3 descriptive); analysis code written after H1 existed (disclosed) |
| Post-hoc analysis | none reported | dry-run verdict on validation (labelled dry-run) | targeted pairs, D6 stress, OSS probe labelled post-hoc; no parameter changed after held-out (verified: frozen-params hash matches prereg) |
| Seed independence | tuning 1000+/validation 2000+/held-out 9000+ (disjoint ranges, disjoint variant draws) | same | disjoint ranges, plus split name is in the RNG key |
| Determinism | seeded `SeedSequence`; no committed determinism re-execution | same | unit tests + 300 held-out cell re-executions with 0 mismatches (reported); test suite re-run by me: 77/77 pass |
| No-lookahead tests | Yes: `perturb_future` scrambles all post-t0 latent and score data; `perturb_rejected_latent` counterfactual; static audit for forbidden tokens; 27 policies × 5 cases, 135 runs, **0 failures**, canaries detected | same | Yes: `resample_hidden_after` metamorphic prefix-invariance for 12 policies × 4 ingest × 5 scenarios × 2 cuts; oracle flagged (power check) |
| Oracle separation | oracles flagged `NOT_IMPLEMENTABLE` and excluded from verdict rules | same, explicit in pre-reg | `IMPLEMENTABLE=False`; excluded from verdict; limitation 13 warns it mixes noise foresight |
| Multiple-comparison handling | none in code on `main` | pooled bootstrap over blocks; "best-of-shortlist" FIFO-failure rule acknowledged as inflating | per-scenario flags not multiplicity-corrected (limitation 8); verdict uses pooled macro contrasts with equivalence margin |
| Estimator validity | flawed (see 08) | corrected before any held-out look | not applicable |
| Reports | none | none | 15 reports incl. limitations |

## Protocol weaknesses, honestly

**Study A as merged**
1. It is not a study: no held-out, no pre-registration, no verdict; the merged commit message says "WIP".
2. Its tuning objective is corrupted by the S12 normaliser: `dens0_sd` collapses in near-identical worlds, so S12 contributes 48% of the pooled objective (report 08). Tuned parameters were therefore chosen largely to win S12.
3. Round-2 grid extension used tuning results, which is fine within tuning, but the extended grids were never validated on `main`.
4. Every "improvement over FIFO" on `main` is in-sample for the tuned method (FIFO is untuned): the direction is trustworthy, the size is not.

**Study A run 2 (supplementary)**
5. Thresholds were set after seeing validation; the pre-registration is v2, written after a failed v1 (transparent, but not "blind").
6. Validation seeds are few (4 per variant); CIs are narrow because blocks are cheap, not because worlds are diverse: all worlds share one generator.
7. The `FIFO_FAIL` rule takes the best of four methods per family: acknowledged upward bias.

**Study B**
8. Analysis code postdates H1 results (disclosed); the rules are pre-registered but their implementation was not frozen.
9. δ=0.25 bps is permissive relative to observed method differences (best-vs-simple +0.062), so the verdict rule places six methods in the tied set T, including a bandit. B's own text concedes the label means "the score-ranking family", not six distinct algorithms.
10. All held-out worlds come from the generator that produced tuning worlds (same model class).
11. Tuned at K=4 only, and ingest mode is a tuned hyperparameter that differs between FIFO (RAW) and ranking policies; I tested the confound (03, trap 2) and it does not change conclusions.

**Both**
12. Same-family held-out, calibrated-by-construction scores, constant costs, linear accrual. Agreement between them is agreement between two hand-built, similar-in-spirit generators; it is weaker evidence than independent data.
