# MEMORY_DELTA_ASQ_V3_2_STATISTICAL_INFERENCE_CONTRACT_ADJUDICATION_V1

ISOLATED — not written to canonical MEMORY (no unique writer lease).
Amendment: QUORUM_V3_2_STATISTICAL_INFERENCE_AMENDMENT_CANDIDATE.md, SHA256 b874990d13dde9bef4a86ff1a0cc1f47d0e1697aa4398064663639a715bda287
Anchor (quoted, unverified): V3.1 SHA256 8cb9adf43692667e6be98769a9082073447230e73b99b881b5a566e5447237da

## Newly established / adjudicated (INFERENCE unless stated)
- Source limitation (OBSERVED): the external-lab repo @ d0b311d holds no V3/V3.1, SOURCE_DE_VERITE.md or MEMORY; V3.1 mapping BLOCKED.
- Both arms are deterministic offline evaluations of one frozen input: no treatment randomization; inference is over the market process; dependence dominates.
- PAIR_UNIT = frozen pre-treatment DecisionInput x instrument x cutoff; pair_id minted pre-treatment; DEPENDENCE_BLOCK/CLUSTER_KEY = decision epoch; inference series = ordered epoch totals with ratio-of-sums estimator.
- PRIMARY_ESTIMAND = ITT-style mean of (Y_B − Y_A) over all pre-treatment-eligible pairs, bps of reference notional, net of costs; Delta = P(S)·Delta_S.
- QUORUM_ONLY_SUPPRESSED = SECONDARY (post-treatment label; valid subgroup only under determinism, no state feedback, sealed before outcomes), else DESCRIPTIVE_ONLY.
- Identical-decision pairs are known zeros (not UNKNOWN); missingness concerns only active pairs; UNKNOWN stays in denominator; partial identification (Manski bounds + tipping point) REQUIRED; depth/staleness missingness presumed informative.
- Symmetric CF evaluator for both arms; PAPER A = validation only; support gap for B-only trades; Binance @ticker is L1-only (INFERENCE).
- PT1H provisional pending operator attestation; overlap k=ceil(H/cadence) sets effective blocks, bandwidth and block-length floors.
- No method selected. Gates and bands defined pre-benchmark (core non-coverage [3.5%,6.5%] + CP upper ≤7.5%, stress ≤10%/hard 15%, boundary size ≤3.2%, determinism 100%, etc.), rationale = ±3 MC SE and Bradley 1.5× limit.
- CS = sealed anytime monitor emitting only discrete states; positive promotion only at the single final look.
- One confirmatory hypothesis; SPA/StepM not required unless arms/strategies multiply.
- Replay: pooling FORBIDDEN by default; allowed roles listed.
- Open risk: N=757 mismatch=0 may imply tiny p_active (power); operator must say whether those inputs exercised quorum divergence.

## Operator-required (unchosen)
M, claim type, A_min, m_cap, pi_min, W_max, d_min/d_max, max duration, tau* grid, runtime budget, PT1H attestation, PAPER A residual band.

## State unchanged
V3.2 not frozen; AS-Q not activated; quorum unchanged; G3 open; primary economic inference NOT allowed.
