# 10 — Maintenance and licence refresh (only what materially matters to V2)

Scope (mission §14): refresh River, Vowpal Wabbit and the non-stationary-bandit literature since V1. No full landscape redo. Date of both V1 and V2 sessions: **2026-09-29** (the clones/PyPI snapshots below were taken during V2; V1 recorded the same heads), so **nothing material changed since V1** — that is itself the finding. **Library quality is reported here separately from policy behaviour; nothing in 05–09 is used to rank libraries** (mission §15): "River is better/worse than VW" is *not* concluded anywhere.

Method labels: PyPI JSON (`pypi.org/pypi/<pkg>/json`) and `git clone --depth 1 --filter=blob:none` + `git ls-remote` — OBSERVED. arXiv abstract-page/API metadata — OBSERVED (titles/dates only; papers **not read** ⇒ contents UNKNOWN/DOCUMENTED_CLAIM at best). GitHub REST/issue pages were not used (V1 found them blocked); open-issue counts are therefore not refreshed (UNKNOWN).

## 1. River

| Item | Value | Label |
|---|---|---|
| Latest release | 0.26.1 — 2026-08-21 (0.26.0 2026-08-21, 0.25.0 2026-05-31, 0.24.2 2026-04-15) | OBSERVED (PyPI) |
| Git HEAD | `03b4818` — 2026-09-28 05:12 +02:00 — "Add classifiers for PyPI (#2030)" (same commit as V1's `03b481820`) | OBSERVED |
| Licence | BSD-3-Clause (`LICENSE` "BSD 3-Clause License, © 2020 the river developers"; PyPI `license_expression`) | OBSERVED |
| Requirements | Python ≥ 3.11; `scipy>=1.14.1,<2`, `numpy>=2.2.5,<3`, `narwhals>=2.0.0` (pandas optional) | OBSERVED |
| Installed for V2 | river 0.26.1, numpy 2.4.6, scipy 1.17.1, narwhals 2.26.0 (`bench/v2/environment/requirements.lock.txt`) | OBSERVED |
| Change since V1 | none (same head, same release) | OBSERVED |
| What V2 adds | River's `EpsilonGreedy`, `UCB` and `stats.EWMean/Mean` ran without modification on typed-outcome feedback (1 200 runs, 0 errors, 600 `_n == #EVIDENCE` audits, process-deterministic). `EWMean.fading_factor` semantics (weight of the *new* observation) confirmed in the shipped docstring. River has no channel for "attempted, no evidence" and no staleness notion (OBSERVED in source usage; consistent with V1 04 R4) — the guard is custom. | OBSERVED |

## 2. Vowpal Wabbit

| Item | Value | Label |
|---|---|---|
| Latest release | 9.11.9 — 2026-09-27 23:37 UTC; 9.11.8 (20:18 UTC), 9.11.7 (12:39 UTC) the same day; 9.11.6 2026-09-23; previous 9.11.2 2026-03-07 | OBSERVED (PyPI) |
| Git HEAD | `00196b3` — 2026-09-28 09:06 −04:00 — "docs(wasm): npm trusted publishing works; by-hand is the fallback (#4975)" (= V1's `00196b35`) | OBSERVED |
| Licence | BSD 3-Clause (PyPI); repo `LICENSE` starts "Copyright © Microsoft Corp 2012-2014, Yahoo! Inc. 2007-2012, and many individual contributors" (custom BSD text, `ThirdPartyNotices.txt` in repo per V1 — not re-audited) | OBSERVED / V1 |
| Requirements | Python ≥ 3.10; wheel declares no Python dependencies | OBSERVED |
| Installed for V2 | vowpalwabbit 9.11.9 (native wheel, ran on 4 cores) | OBSERVED |
| Change since V1 | none; release churn noted by V1 (four releases in five days: 9.11.6 → 9.11.9) persists as an observation, cause not investigated (V1 attributed 9.11.8/9.11.9 to Java-publishing fixes — DOCUMENTED_CLAIM) | OBSERVED |
| What V2 adds | `--cb_explore_adf` with shared features ran leak-free; deterministic across 3 process seeds (18/18 hash checks including D); ≈ 100× per-run cost of numpy policies in this harness; behaviour dominated by learning rate/exploration (07 BRITTLE). Bus-factor/maintainer concentration (V1: 178/182 commits one author name) was **not re-measured** (blobless shallow clone) — UNKNOWN whether it changed. | OBSERVED |

## 3. Literature (non-stationary bandits, discounted/forgetting UCB)

| Item | Status |
|---|---|
| Garivier & Moulines, *On Upper-Confidence Bound Policies for Non-Stationary Bandit Problems*, arXiv:0805.3415 (D-UCB, SW-UCB) | title confirmed on arXiv (submitted 2008-05-22; page last updated 2026-09-29) — OBSERVED metadata. Policy B follows the D-UCB idea (discount of value **and** count) but is **not** the paper's exact algorithm (0.5 bonus constant, guard, backoff are V2's). |
| arXiv:2511.19240 *Empirical Comparison of Forgetting Mechanisms for UCB-based Algorithms on a Data-Driven Simulation Platform* (2025-11-24) | found by arXiv API search; **title/date only, not read** — potentially relevant to the γ/window frontier; content UNKNOWN. |
| arXiv:2605.25590 *Nonstationary Generalized Linear Bandits with Discounted Online Mirror Descent* (2026-05-25); arXiv:2606.23933 *Flow-Corrected Thompson Sampling for Non-Stationary Contextual Bandits* (2026-06-22); arXiv:2608.19643 *Time-Uniform Self-Normalized Concentration for Discounted Least Squares: Limits and Corrections* (2026-08-20) | title/date only, **not read**; content UNKNOWN. Not used in any V2 design decision. |

No literature result was used to set a V2 parameter; all parameters come from TRAIN/VALIDATION (04).

## 4. Environment provenance (persisted under `bench/v2/environment/`)

`python_version.txt` (3.11.15), `uname.txt`, `install_commands.txt` (venv + `pip install numpy scipy river vowpalwabbit pytest`), `requirements.lock.txt` (`pip freeze`: numpy 2.4.6, scipy 1.17.1, river 0.26.1, vowpalwabbit 9.11.9, narwhals 2.26.0, pytest 9.1.1 + its 4 deps). Same River/VW/numpy/scipy versions as V1 (`reports/001…/bench/requirements-observed.txt`). All installations succeeded ⇒ no policy is `NOT_EXECUTED_DEPENDENCY_BLOCKED`.

## 5. Licence obligations (not legal advice)

River (BSD-3), VW (BSD-3-style), numpy/scipy (BSD), narwhals (MIT), pytest (MIT, test-only): permissive, no copyleft in the installed set (pip metadata not audited beyond the PyPI licence fields for River/VW — UNKNOWN for transitive text). Policy A/B and the harness are the lab's own code (no third-party code copied; the V1 `ref_ducb` was *not* reused — B is a fresh implementation of the D-UCB idea).

## 6. Not refreshed (state as of V1 stands)

MABWiser, Optuna, SMPyBandits (V1 REJECT/ADAPT-idea classifications) — not in V2 scope; open-issue backlogs of River/VW; VW C++ test suite; cross-machine determinism.
