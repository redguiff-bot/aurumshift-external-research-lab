# 07 — Disagreements and their sources

Cause taxonomy from the mission: world assumptions, scoring semantics, cost assumptions, candidate ingestion, capacity definition, hold-duration model, algorithm implementation, tuning protocol, statistical protocol, bugs. Where I could, I tested the suspected cause by running Study A's simulator (scratch copy of the unmerged run-2 code) under altered assumptions. Nothing in either repository was changed. Probe code and output: `evidence/adjudication_probe.py`, `evidence/adjudication_probe_output.txt` (20 seeds × K=4 × family S3; latent bps per slot-hour; differences are means over seeds).

## D1 — Preemption sign (`OLDEST_SLOT`): B +0.185, A −0.085
**Cause: cost and edge levels (cost assumptions + world assumptions). Not a bug. Tested.**

| A-simulator setting | FIFO | `OLDEST_SLOT`(4 h) − FIFO | (12 h) − FIFO |
|---|---|---|---|
| A default (edge ≈10, cost ≈8.5, +3 bps eviction fee) | −0.06 | **−1.404** | −0.254 |
| B-like edge (mean 22), cost 3–7, hold base 7 h, no eviction fee, no waiting decay | 2.22 | **+0.435** | +0.231 |
| same, cost ×3 | 0.85 | **−1.057** | +0.004 |

Study A's engine, given B-like economics, reproduces B's positive preemption gain, and flips it at 3× cost, exactly as B's own D3 diagnostic shows (`OLDEST_SLOT` 3.00 → 1.51 → 0.02 vs FIFO 2.47 → 1.74 → 1.00 at cost ×1/×2/×3). Preemption turns backlog into extra admissions; whether that pays depends on whether an additional partial-hold trade earns more than its fixed cost. B's limitation 3 flags the same dependence (linear accrual). **Consistent with the mission's expectation that this is a local-falsification topic, not a finding to import.** Sign agreement of the *mechanism* is replicated; the *headline sign* is not transferable.

## D2 — FIFO versus random / round-robin / quota: A slightly better than FIFO, B tied or slightly worse
**Cause: waiting-age edge decay in A's world (world assumption) . Tested.**
In A, an opportunity's realised edge decays `exp(−age/8)` while it waits, so arrival-order admission systematically picks the *oldest, most decayed* candidate. Removing decay:

| A setting | RANDOM − FIFO |
|---|---|
| default (tau=8) | **+0.057 ± 0.026** |
| no waiting decay (tau→∞) | −0.019 ± 0.027 (n.s.) |
| B-like economics (also no decay) | −0.020 (n.s.) |

B's world has no such age-based penalty (its state is a per-instrument AR(1) that persists), so arrival order is uninformative there and FIFO ≈ random. Magnitude either way is 12–20% of the ranking gain: secondary. Also relevant: A's FIFO has no one-position-per-instrument rule, so stale opportunities on already-busy instruments can be admitted.

## D3 — Spam (S10): FIFO fails badly in A, is merely equivalent in B
**Cause: scoring semantics / world assumption. Read from source; not run.**
A's spam: high-rate candidates on instrument 0 with true edge −2 and score bias +12, so spam looks attractive and loses money; a net-value ranker can be fooled too, and FIFO is fooled worst (A-run2: best method +0.391 dz vs FIFO, +0.282 vs `FIFO_NETPOS`). B's spam: instruments 0–1 emit at 20× rate with *median* edge and *honest* scores; spam only crowds the pool, and only one position per instrument can be open anyway. B's separate score-gaming battery (`F_score_gaming`) is validation-only and, per B's limitation 15, **unmitigated by every policy**. The two S10 scenarios test different threats. Not comparable.

## D4 — Residual value at K=10: A +0.099, B ≈ 0
**Cause: capacity/load definition and hold model. Read from source; utilisation confirms.**
A's load is measured in slot-equivalents of distinct opportunities (families up to 4× a 4-slot system, hold ≈ 15 h), so at K=10 the busiest families are still over-subscribed (FIFO busy 77%). B's load is an emission rate whose repeated emissions collapse onto one position per instrument, with shorter holds (≈ 8.7 h): at K=10 FIFO is busy only 61% and full 12% of the time. Both simulations therefore answer "does ranking matter as capacity grows *at fixed arrival rate*", but their K=10 worlds are differently saturated. Neither result should be read as a statement about any real capacity.

## D5 — Slot-hour vs net ranking (R4): B +0.07, A ≈ 0
**Cause: hold-duration model and scenario parameterisation. Partly tested by reading source.**
A gives the allocator a *candidate-level* noisy duration estimate (`dur_hat`), B only a per-instrument EWMA. B's gain is concentrated in S6 (+0.358, a designed 2.5:1 fast/slow density split) and S3 (+0.189); A's S6 variants set fast/slow density ratios of 0.8–3.0 (validation 1.25/2.0/0.8; held-out 1.8/0.9/3.0), a much milder contrast, giving +0.004. Excluding S6, B's macro gain is +0.046 (my calculation from the per-scenario table), which is nearer to A's magnitude. The hypothesis "hold normalisation matters only when hold and value density are strongly heterogeneous" is compatible with both and untested as such.

## D6 — Verdict labels (`MULTIPLE_CAPACITY_METHODS_SUPPORTED` vs `CAPACITY_ALLOCATION_REFERENCE_SUPPORTED`)
**Cause: statistical protocol (practical-equivalence margins).** See 06, last section: A's δ_equiv is 13% of the simple gain, B's 57%. Same effect, different label. A's dry run is not final and used thresholds tuned after validation.

## D7 — Secondary differences that are not contradictions
- **B's `UNCERTAINTY_LCB` beats every other method; A's `COMPOSED`/shadow price lead.** Both leaders include shrinkage or thresholding on top of net ranking; spreads are small (B 0.06, A 0.025). Different leaders are expected when differences are this small (statistical protocol).
- **Tuned parameters diverge** (B: θ=0.25, ω=0.6, κ=0, α=0.1; A run 1: k=0.5, κ=25, η=0.1, min_hold 12): different worlds, different optima. No meaning beyond that.
- **Oracle headroom**: B's greedy realised-net oracle sits 5.7 vs 2.3 (best), A's latent-edge oracle sits 0.25 vs 0.18 dz. Not comparable (B's oracle sees realised noise).

## What is *not* a disagreement
- Ranking > FIFO (R1, R3), net screen material (R2), bandits/correlation not helpful (R6, R7), mild starvation cost (R9), declining value with capacity (R10 direction): agree.
- Ingest confound in B: none (03, trap 2).

## Attribution summary

| Disagreement | Cause | Bug? | Evidence level |
|---|---|---|---|
| D1 preemption | cost + world | no | experiment on A's engine + B's D3 |
| D2 FIFO vs random | world (waiting decay) | no | experiment on A's engine |
| D3 spam | scoring semantics | no | source |
| D4 K=10 | capacity/load + hold | no | source + utilisation |
| D5 slot-hour | hold model + scenario design | no | source + B per-scenario table |
| D6 verdict label | statistical protocol | no | arithmetic |
