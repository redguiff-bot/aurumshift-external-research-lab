# 05 — Licence and maintenance

Not legal advice. Licence texts were read from each clone's `LICENSE` (first lines) and cross-checked against PyPI metadata; the licence of AurumShift itself is unknown to this study, so "compatible" below means only *permissive, no copyleft obligations on the caller*.
Dates are as of 2026-09-29. "365d/90d" = commits reachable from HEAD in that window; "authors" = distinct commit e-mails in 365 d (author-name distribution used for VW).
All rows: **OBSERVED** (clone `git log`/tags, PyPI JSON) unless marked.

## 1. Maintenance table

| Project | Last commit | Latest release (source) | 365d / 90d commits | Authors 365d | Open issues (WebFetch, model-summarised) | Verdict |
|---|---|---|---|---|---|---|
| River | 2026-09-28 | 0.26.1 · 2026-08-21 (tag+PyPI) | 299 / 69 | 39 | 52 | Active |
| Vowpal Wabbit | 2026-09-28 | 9.11.9 · 2026-09-27 (tag+PyPI) | 182 / 51 | 5 (**178 commits under one author name**) | "0" — **UNKNOWN reliability** (issues may be disabled or summary wrong) | Active but single-maintainer |
| MABWiser | 2024-08-30 | 2.7.4 · 2024-08-30 | 0 / 0 | 0 | "0 issues, 0 PRs" — UNKNOWN reliability | **Stale (760 days)** |
| Optuna | 2026-09-25 | 5.0.0 · 2026-09-04 (RC 2026-07-31) | 1,793 / 430 | 102 | 9 | Very active |
| SMPyBandits | 2026-06-19 (community PR merge) | 0.9.7 · **2019-10-25** | 2 / 0 | 2 | 27 (newest visible: 2022) | **Abandoned** (import broken, PROVEN) |
| Ax | 2026-09-21 | 1.3.1 · 2026-06-09 | 747 / 45 | 57 | 36 | Active (not selected: weight/fit) |
| contextualbandits | 2026-06-28 | 0.3.30 · 2026-02-22 (PyPI) | 7 / 0 | 3 | not fetched (UNKNOWN) | Slow, single-author |
| OSS Vizier | 2026-09-15 | 0.1.24 · 2025-02-01 | 34 / 19 | 9 | not fetched | Active repo, stale PyPI channel |
| Nevergrad | 2026-03-16 | 1.0.12 · 2025-04-23 | 4 / — | 1 | not fetched | Near-dormant |
| modAL | 2023-06-01 | 0.4.2 · 2023-06-01 | 0 | 0 | not fetched | Abandoned |
| Open Bandit Pipeline | 2022-11-04 | 0.5.7 · 2023-04-14 (PyPI) | 0 | 0 | not fetched | Abandoned |
| scikit-multiflow | 2020-11-19 | 0.5.3 · 2020-06-17 | 0 | 0 | not fetched | Archived/abandoned (superseded by River) |
| irace (R) | 2026-09-15 | v4.5 | 59 | — | not fetched | Active |
| GrowthBook | 2026-09-29 | v5.1.0 · 2026-09-21 | 1,587 | 69 | not fetched | Active (wrong problem/licence shape) |
| Ray | — (not cloned) | 2.58.0 · 2026-08-23 (PyPI) | — | — | — | Active (not reviewed) |

Caveat on issues: github.com pages and the GitHub REST API were blocked for this session's proxy (HTTP 403); issue lists were obtained through `WebFetch`, whose answers are produced by a small summarising model. Treat counts as **DOCUMENTED_CLAIM-grade**, not exact. Titles quoted in other files come from the same source.

## 2. Licences

| Project | Licence (OBSERVED) | Third-party notices | Obligations for a permissive downstream (INFERENCE) |
|---|---|---|---|
| River | BSD-3-Clause | — | keep notice; no endorsement use |
| VW | BSD-3-Clause (custom text with Microsoft/Yahoo/contributors header; PyPI "BSD 3-Clause") | `ThirdPartyNotices.txt` present in repo | keep notices; bundled C++ third-party code covered by that file (not audited: UNKNOWN) |
| MABWiser | Apache-2.0 (file + SPDX header) | — | keep notice + NOTICE/patent clause |
| Optuna | MIT | `LICENSE_THIRD_PARTY` present | keep notice |
| SMPyBandits | MIT | — | keep notice |
| Ax | MIT (Meta) | — | — |
| contextualbandits | BSD-2-Clause | — | — |
| Vizier | Apache-2.0 | — | — |
| Nevergrad | MIT | — | — |
| modAL | MIT | — | — |
| Open Bandit Pipeline | Apache-2.0 | — | — |
| scikit-multiflow | BSD-3-Clause | — | — |
| **irace** | **GPL (≥ 2)** (`DESCRIPTION: License: GPL (>= 2)`) | — | **copyleft**: linking/embedding would impose GPL terms; process-level use only, needs legal review |
| **GrowthBook** | **MIT-Expat outside `packages/*/src/enterprise` & `packages/front-end/enterprise`; "GrowthBook Enterprise License" inside those directories** | — | mixed licensing — a compliance hazard when vendoring |
| Statsig / Eppo / Optimizely-type SaaS | proprietary, opaque | — | rejected by mission rule; products not individually examined (UNKNOWN) |

**Transitive licences of the wheels I actually installed** (from `importlib.metadata`, OBSERVED): River → numpy (BSD-3 AND 0BSD AND MIT AND Zlib …), scipy (BSD), narwhals (MIT). Optuna → alembic/SQLAlchemy/PyYAML (MIT), colorlog (MIT), MarkupSafe (BSD-3), packaging (Apache-2.0 OR BSD-2), typing_extensions (PSF-2.0), **tqdm (MPL-2.0 AND MIT — weak file-level copyleft, unmodified use is normally fine; flag for legal review)**.
MABWiser → BSD/MIT/PSF/Apache stack (pandas, scikit-learn, matplotlib PSF, pillow MIT-CMU, …). VW → no dependencies. **No GPL/AGPL among the installed wheels** (OBSERVED for the versions listed). Ax's 69-package closure (torch, CUDA wheels with NVIDIA licences) was **not** audited (UNKNOWN).

## 3. Dependency weight and abandoned-dependency scan

| Project | Runtime deps (clean venv) | site-packages | Abandoned/at-risk deps |
|---|---|---|---|
| River | numpy≥2.2.5, scipy≥1.14.1, narwhals (4 pkgs) | 256 MB | none observed; Python ≥3.11 requirement is a constraint (OBSERVED) |
| VW | none | 34 MB | none; native wheel per platform (build from source needs C++ toolchain: UNKNOWN effort) |
| MABWiser | joblib, numpy, pandas, scikit-learn, scipy, seaborn (20 pkgs total) | 474 MB | itself stale; incompatibility with numpy 2.4.6 in one test (OBSERVED) |
| Optuna | alembic, colorlog, numpy, packaging, sqlalchemy, tqdm, PyYAML (11 pkgs) | 139 MB | none observed |
| SMPyBandits | numpy, scipy, matplotlib, joblib, seaborn, scikit-learn, **scikit-optimize** | — | **`scikit-optimize` abandoned (1 commit 2021-10, PyPI-era code); `btdtri` import failure vs SciPy 1.17.1 (PROVEN)** |
| Ax | botorch, gpytorch, **torch 2.14 + CUDA-13 wheels**, plotly, sympy, ipywidgets… (69 pkgs) | not installed | heavy, active |

## 4. Reproducibility of the study itself

`bench/requirements-observed.txt` pins the versions actually run. Clone HEADs: river `03b481820`, mabwiser `b104071`, vowpal_wabbit `00196b35`, optuna `0d05a9673`, Ax `57efa05a`, SMPyBandits `012fc13`, contextualbandits `fc49364`.
Note that "today" in this environment is 2026-09-29; other dates in the table are **as reported by the clones/PyPI at that time**, not from my memory.
