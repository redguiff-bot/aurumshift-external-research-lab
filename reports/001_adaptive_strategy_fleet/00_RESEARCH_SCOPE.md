# 00 — Research scope

Mission: `EXTERNAL_RESEARCH_ADAPTIVE_STRATEGY_FLEET_LANDSCAPE_V1`
Date of study: 2026-09-29 (all "current" statements are as of that date).
Doctrine applied: `claude.md` (REUSE → ADAPT → WRAP → COMPOSE → CUSTOM LAST; primary sources; no fabricated benchmarks).

## 1. Problem statement (external, generic)

A fleet of many *cells* (strategy × instrument × horizon × regime × configuration). A research
engine must continuously decide **where to spend evidence-gathering attention**:

* what to explore, what deserves more evidence, what looks promising, what is degrading;
* how to avoid starvation of low-sample or silent cells;
* how to rotate observation/experimentation attention;
* how to adapt online **without** turning the scheduler into a financial capital allocator.

I model this abstractly as a **non-stationary, batched, delayed-feedback, dynamic-arm-set bandit /
racing problem** where the reward is *information value / promise of an evidence increment*, never P&L.

## 2. Boundaries and honesty rules

* AurumShift source was **not** available. Nothing here claims compatibility with private code
  (`claude.md` "Important boundary"). Section 06 only lists *generic* integration surfaces.
* No AurumShift integration was implemented. Work stops at `07_FINAL_ADJUDICATION.md`.
* Evidence labels used everywhere:

| Label | Meaning in this study |
|---|---|
| **PROVEN** | Demonstrated by a reproducible check I ran here, with the artefact in `bench/` (or a deterministic fact of a cloned file). Stronger than OBSERVED: repeatable and falsifiable. |
| **OBSERVED** | I directly saw it (cloned source, `git log`, PyPI metadata, a test/example I ran, a fetched web page) but it is not a general guarantee. |
| **DOCUMENTED_CLAIM** | Stated by upstream docs/paper/README/search snippet; I did not verify it by execution. |
| **INFERENCE** | My reasoning from the above. May be wrong. |
| **UNKNOWN** | Not determined (often because access or time was lacking). Stated explicitly rather than guessed. |

## 3. Method and its limits

| Phase | What was actually done | Limit |
|---|---|---|
| 1 Landscape | GitHub clones (blobless) of 13 repos for `git log`/tags/LICENSE; PyPI JSON; arXiv API metadata check of 14 papers; 5 web searches; GitHub issue-list pages via WebFetch. | GitHub REST API and github.com HTML are **blocked** for this session's proxy (403, "access not enabled"); issue counts therefore come from a **model-summarised WebFetch**, less reliable (see VW/MABWiser "0 open issues" caveat in 05). Ray, Statsig-like SaaS, and irace internals were **not** code-reviewed. |
| 2 Filter | Rules from the mission applied to landscape metadata. | Stars deliberately unused (doctrine #6). |
| 3 Deep review | Source read + installed + tests/examples run for River, MABWiser, VW, Optuna, SMPyBandits. Ax/contextualbandits/Vizier only metadata + dependency resolution. | VW C++ test-suite not built (only pip wheel exercised). |
| 4 Benchmark | One synthetic scenario family, 20 seeds/policy + small sensitivity sweeps (`bench/`). | Single scenario family; Bernoulli rewards; batch size 10; hyper-parameters mostly **untuned**; no significance tests (mean±sd only). Ranks *behaviours under this scenario*, not libraries in general. |
| 5 Adversarial | Attacks derived from source + measurements. | Some attacks are INFERENCE, tagged. |
| 6 Fit | Only `claude.md` constraints. | Final integration adjudication must happen later against the real repo. |

## 4. Environment facts (OBSERVED)

Python 3.11.15, Linux, 4 cores, 15 GB RAM. Versions actually executed: river 0.26.1, vowpalwabbit 9.11.9,
mabwiser 2.7.4, optuna 5.0.0, numpy 2.4.6, scipy 1.17.1, pandas 3.0.6, scikit-learn 1.9.1
(`bench/requirements-observed.txt`). Benchmark runs were executed 4-way parallel on 4 cores, so wall times are
comparable with each other but not absolute.

## 5. AurumShift constraints used as filter (from `claude.md`, verbatim intent)

research-only/paper-only · no live capital · PostgreSQL-first where appropriate · PIT/provenance/no-lookahead critical ·
event-driven/intraday (not HFT) · one authoritative source per concern · **missing evidence is not negative evidence** ·
realistic market costs matter · low operator relay · scientific reproducibility · infrastructure complexity must justify itself.

Consequences drawn for this study (INFERENCE): (a) state should be inspectable/persistable in a relational store, not only an opaque
in-process object; (b) a scheduler must have an explicit path for "attempted but no evidence" that does **not** count as a bad
outcome; (c) determinism under fixed seeds and process restarts is a hard requirement; (d) libraries that permanently *kill*
cells (e.g. pruners) conflict with (b) unless "pruned" is reinterpreted as "deprioritised, revisit later".

## 6. Deliverables

`00_RESEARCH_SCOPE.md` (this) · `01_LANDSCAPE.md` · `02_TOP5_DEEP_DIVE.md` · `03_REPRODUCTION_AND_BENCHMARK.md` ·
`04_ADVERSARIAL_REVIEW.md` · `05_LICENSE_AND_MAINTENANCE.md` · `06_INTEGRATION_SURFACE.md` · `07_FINAL_ADJUDICATION.md` ·
`bench/` (code, raw JSON, generated tables).
