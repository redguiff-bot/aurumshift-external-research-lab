# 01 — Corpus identity

Mission names match (`AURUMSHIFT_EXTERNAL_RISK_CAPACITY_AND_TURNOVER_ALLOCATION_V1`) but the two corpora are **not** assumed comparable; see 02–04.

## Study A — as merged into the default branch (strict definition)

| Field | Value |
|---|---|
| Default-branch SHA | `1a449df5239753e39d657fdf14813a8f1995a985` (merge of PR #6, 2026-09-29 15:59 +02:00) |
| Content commits | `1d676ff` (simulator, policies, validation, leakage tests; "WIP, held-out not yet run"), `588dc4b` (tuning progress log), `da2f7c4` (tuning round 1 outputs, extended grids for round 2, "tuning split only") |
| Paths | `bench/capacity_v1/py/{env,policies,scenarios,runner,analyze,validate_and_leakage,oss_probe}.py` (1,712 lines); `bench/capacity_v1/results/{tune.log,tuned_params.json,tuned_params_round1.json,tuning_raw.csv.gz,tuning_table.csv,tuning_table_round1.csv,validation.json}` |
| Reports | **none** (`reports/` has no capacity directory on `main`) |
| Pre-registration | **none on `main`**; `runner.heldout()` reads `../prereg/PREREGISTRATION.json`, which does not exist there |
| Held-out results | **none** |
| Validation-split policy results | **none** (`validation.json` holds only simulator checks: Erlang-B, greedy=MILP, assignment=top-k, leakage) |
| Mission name | in code docstrings only |
| Simulator | `env.py`: hourly discrete time, T=1000, N=12 instruments in 4 clusters, pending pool with TTL=3, `cap` identical slots, per-opportunity latent edge/duration/cost |
| Policies (27 + 2 oracles) | FIFO, ROUND_ROBIN, RANDOM_SEEDED, EQUAL_QUOTA, OLDEST_SLOT, FIFO_NETPOS, RANK_SCORE_RAW, RANK_NET, RANK_NET_UNKCOST_ZERO, RANK_NET_MISSING_REJECT, UNCERTAINTY_LCB, SLOTHOUR_DENSITY, SLOTHOUR_HAZARD, SHADOW_PRICE, ONLINE_KNAPSACK_PSI, FLUID_QUANTILE, TRUNK_RESERVATION, SECRETARY_1_OVER_E, CLUSTER_CAP, CORR_PENALTY, MARGINAL_RISK, CORR_HARD_REJECT, EVICT_SWAP, LINUCB, LIN_TS, SLEEPING_HEDGE, COMPOSED; ORACLE_SCORE/ORACLE_DENSITY (not implementable); offline LP bound |
| Scenario sets | 12 families S1–S12, 3 jittered variants each; held-out-only H1–H3 compositions defined but never run |
| Seeds | tuning 1000+ (3 seeds × 3 variants × 12 families, caps 4 and 6; 108 jobs; 72 policy configs; 15,552 rows); validation 2000+ (defined, not run on `main`); held-out 9000+ (defined, not run); robustness 3000+, failure 4000+ (defined, no results) |
| Metrics | `lat_per_slot_hour` (latent net, market noise excluded), `real_per_slot_hour`, utilisation, HQ-missed fractions, HHI/eff-clusters, ret-to-risk, drawdown, starvation, admit ratios, spam share, long-slot share, toggle rate |
| Tuning protocol | grid per policy; objective = mean over (family, variant, seed, cap) cells of `(lat − FIFO lat)/dens0_sd`; two rounds (round 2 extends grids after seeing round 1) |
| Held-out protocol | described in `scenarios.py` (disjoint variant RNG and seeds, wider jitter) and `runner.heldout()` (hash assertion); not executed |

### Study A — unmerged continuation (supplementary only)
Branch `claude/risk-capacity-turnover-v1`, tip `cb130415d0e4211a5379fb29be5cac3a2749859e`, 7 commits after the merge:
- `3bbc451` validation results and pre-registration v1
- `7c991af` **supersedes run 1** ("estimator warm-up bias + normaliser flaw found before any held-out inspection")
- `c4d0b86` reruns tuning and validation on corrected code, pre-registration v2 (frozen tuned-params sha256 `d95c9910…`)
- `cb13041` "held-out run in progress (log)": the log holds only RuntimeWarnings; no held-out data existed at analysis time

`results/superseded_run1/` on that branch holds run 1 through its round-2 tuning and validation (not byte-identical to `main`, which holds only the round-1 tuning outputs of the same run; verified by file hash). The estimator flaw (`cov = eye(N)*40` prior in `policies.py`) is present in the code on `main`. **What `main` calls Study A is an early snapshot of the retired run.** The branch was written by a separate session (`session_013y25LsVGmzcNzKXFo1FEfW`) and may still be live.

## Study B — PR #8 (`claude/festive-archimedes-c3fso6`)

| Field | Value |
|---|---|
| Head SHA | `0ff4f71efe7fd2a3e3014407553f0c3665617d2f` (PR open, not draft, mergeable_state clean, 75 files, +49,515) |
| Commits | `ad2adda` simulator, policies, tests, tuning+validation results, frozen params, **pre-registration**; `c64cbb4` held-out H1/H2/H3; `0ff4f71` diagnostics, analysis, OSS probe, reports 00–14 |
| Paths | `bench/capacity_v1/{src,tests,configs,logs,results/{tuning,validation,heldout,diagnostics,analysis}}`, `reports/008_risk_capacity_turnover/00–14` |
| Mission name | in reports; PR title "research(008)…" |
| Simulator | `world.py` + `engine.py`: hourly, W=600 (+48 padding), N=10/12/15 by split in 5/4/5 groups, emission stream, TTL=4, one position per instrument |
| Policies | 12 implementable (FIFO, ROUND_ROBIN, RANDOM, EQUAL_QUOTA, OLDEST_SLOT, FIFO_SCREEN, SCORE_RANK, SLOTHOUR, SLOTHOUR_SHADOW, UNCERTAINTY_LCB, CORR_AWARE, LINTS) + ORACLE_GREEDY_UB; 4 ingest modes (RAW, DEDUP_LATEST, COOLDOWN, SCORE_UPDATE) |
| Scenario sets | 13 held-out scenarios (S1–S12 + S5b); validation-only failure battery F_*; diagnostics D1–D6 |
| Seeds | tuning 1000–1005; validation 2000–2007 (diagnostics 6000–8019); held-out H1 3000–3019 (13 scen × 20 seeds), H2/H3 3000–3009 |
| Metrics | primary `net_per_avail_slot_hour` (realised, market/idiosyncratic noise included); 20+ secondary reported without composite |
| Tuning protocol | every (policy, params, ingest) on tuning; top-3 re-run on validation; best frozen (`frozen_params.json`, sha256 `ebcd46c4…`, verified) |
| Held-out protocol | pre-registered H1/H2/H3, δ=0.25 bps margin, rule text and code hash in `prereg.json`; run once, files written without overwrite |
| Tests | 77 tests; I ran them in a scratch copy: **77 passed in 16 s** |
