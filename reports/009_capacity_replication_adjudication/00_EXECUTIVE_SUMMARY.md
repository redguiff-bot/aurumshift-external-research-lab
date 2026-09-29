# 00 — Executive summary

Mission: `AURUMSHIFT_CAPACITY_STUDY_A_B_REPLICATION_ADJUDICATION_V1`. External research only. Nothing here touches AurumShift code, PAPER behaviour or `max_open_positions`. Neither corpus was modified. Every number below is synthetic and describes those simulators only.

## The finding that shapes everything

**Study A as merged into `main` (PR #6, `1a449df`) is not a completed study.** It is a work-in-progress snapshot: simulator, 27 policies, tuning-split results, simulator checks and leakage tests. It has **no validation-split policy results, no pre-registration, no held-out run and no reports**. Worse, it is "run 1", which its own authors later declared superseded (commit `7c991af`, on the unmerged branch `claude/risk-capacity-turnover-v1`) because of an EWMA-covariance warm-up bias and a normaliser flaw. I confirmed the normaliser flaw independently in the merged data (report 08): one scenario (S12) supplies 48% of the pooled tuning objective.

So the mission's premise, two independent replications of one protocol, holds only for Study B. Study A can be compared on **assumptions, policies and protocol**, but on **results** only weakly, through its tuning split.

To stay useful without moving the goalposts, the adjudication reports two evidence levels and never mixes them:

| Level | Source | Status |
|---|---|---|
| **Strict** | Study A exactly as merged (`main` `1a449df`, run 1, tuning split only) | the mission's definition |
| **Supplementary** | Study A run 2 on the unmerged branch (`cb13041`): corrected code, validation split, dry-run verdict; held-out still running and unreadable | disclosed, not authoritative, may change |

## Answers (strict / supplementary)

| Q | Question | Strict (A merged) | Supplementary (A run 2 validation) |
|---|---|---|---|
| R1 | Raw FIFO underperforms when scarce | PARTIALLY_REPLICATED | REPLICATED |
| R2 | Net-edge screen explains a material share | NOT_TESTED_IN_ONE_STUDY | REPLICATED |
| R3 | Score ranking beats FIFO | NOT_TESTED_IN_ONE_STUDY | REPLICATED |
| R4 | Net/slot-hour beats raw score ranking | NOT_TESTED_IN_ONE_STUDY | PARTIALLY_REPLICATED |
| R5 | Complexity beyond simple ranking pays | NOT_TESTED_IN_ONE_STUDY | PARTIALLY_REPLICATED |
| R6 | Correlation penalties improve net economics | PARTIALLY_REPLICATED | REPLICATED (no) |
| R7 | Bandits justify complexity | PARTIALLY_REPLICATED | REPLICATED (no) |
| R8 | Score quality dominates allocator quality | NOT_TESTED_IN_ONE_STUDY | NOT_TESTED_IN_ONE_STUDY |
| R9 | Ranking creates starvation/concentration trade-offs | PARTIALLY_REPLICATED | REPLICATED |
| R10 | Allocator value declines as capacity grows | PARTIALLY_REPLICATED | PARTIALLY_REPLICATED |

## What replicates (supplementary level, both effect signs and rough size)
- Arrival-order admission is the weak baseline; **net-value ranking beats it**: B +0.365 bps per available slot-hour (about 20% of FIFO's 1.78); A +0.154 in normalised units.
- A **net-edge screen alone** captures a material but world-dependent share of the ranking gain: B 45% (SCORE_RANK basis), A 65% in its own worlds, 33% when A's simulator is given B-like edge and cost levels.
- **Bandits and correlation penalties do not improve net value**; bandits cost far more compute; they are worse or tied.
- The best complex method adds a **small, detectable** increment over simple ranking: B +0.062 (14% of the simple gain), A +0.025 (16%). Whether that "justifies complexity" depends only on the chosen margin, which is why the two studies' verdict labels differ.
- Ranking causes only modest soft-starvation and concentration; hard starvation is about zero (except A's LinTS).

## What disagrees, and why (report 07)
Four material disagreements, **all traced to world or cost assumptions, none to a bug**, two of them by direct experiment on Study A's simulator:
1. **Preemption**: B's `OLDEST_SLOT` gains +0.185; A's loses 0.085 (dz). Study A's simulator, given B-like edge and cost, reproduces B's gain (+0.435) and flips negative at 3× cost (−1.06). B's own D3 shows the same flip.
2. **FIFO vs random/round-robin**: A finds them slightly *better* than FIFO; B finds them tied or slightly worse. Removing A's waiting-age edge decay removes the effect (+0.057 to −0.019).
3. **Spam (S10)**: A's spam has inflated scores and negative true edge; B's is high-rate but honest. FIFO is the worst case in A's world and merely equivalent in B's.
4. **Residual value at K=10**: A keeps 0.099 dz (about half its K=3 value); B is about zero. Load and hold definitions differ, and A's FIFO stays 77% utilised at K=10 versus B's 61%.

## Verdicts
- Implementation bugs: **2 confirmed in Study A as merged** (self-disclosed, unfixed on `main`); **0 in Study B**. Study B has one report over-generalisation (inversion claim), and Study A's branch has an unexplained NaN warning.
- Capacity: `CAP_CHANGE_AUTHORIZED=FALSE`, `LOCAL_INTEGRATION_AUTHORIZED=FALSE`.
- PR #8 disposition: `REQUIRES_CORRECTION_BEFORE_MERGE` (minor, documentation and provenance only; results are sound).
- **Final verdict: `CAPACITY_REPLICATION_INCONCLUSIVE`**: on the mission's definition Study A cannot replicate anything at held-out level. The supplementary evidence points to `CAPACITY_FINDINGS_PARTIALLY_REPLICATED`. Re-adjudicate when Study A's held-out lands and its run 2 is merged (or PR #6 is amended).

## Final block

```
STUDY_A_SHA=1a449df5239753e39d657fdf14813a8f1995a985 (main, merge of PR #6; content commits 1d676ff, 588dc4b, da2f7c4)  [supplementary: branch tip cb130415d0e4211a5379fb29be5cac3a2749859e]
STUDY_B_SHA=0ff4f71efe7fd2a3e3014407553f0c3665617d2f (PR #8 head; prereg ad2adda, heldout c64cbb4)

ASSUMPTIONS_IDENTICAL=FALSE
POLICY_SEMANTICS_COMPARABLE=PARTIAL (8 of 10 families map with caveats; see 03)

R1_FIFO_SCARCITY=PARTIALLY_REPLICATED   (supplementary: REPLICATED)
R2_NET_SCREEN=NOT_TESTED_IN_ONE_STUDY   (supplementary: REPLICATED)
R3_SCORE_RANKING=NOT_TESTED_IN_ONE_STUDY   (supplementary: REPLICATED)
R4_SLOT_HOUR=NOT_TESTED_IN_ONE_STUDY   (supplementary: PARTIALLY_REPLICATED)
R5_COMPLEXITY=NOT_TESTED_IN_ONE_STUDY   (supplementary: PARTIALLY_REPLICATED)
R6_CORRELATION=PARTIALLY_REPLICATED   (supplementary: REPLICATED)
R7_BANDITS=PARTIALLY_REPLICATED   (supplementary: REPLICATED)
R8_SCORE_QUALITY=NOT_TESTED_IN_ONE_STUDY   (supplementary: NOT_TESTED_IN_ONE_STUDY)
R9_STARVATION=PARTIALLY_REPLICATED   (supplementary: REPLICATED)
R10_CAPACITY_SCARCITY=PARTIALLY_REPLICATED   (supplementary: PARTIALLY_REPLICATED)

MATERIAL_CONTRADICTIONS=4 (preemption sign; FIFO-vs-random sign; spam response; K=10 residual value), all attributed to assumptions
IMPLEMENTATION_BUGS_FOUND=2 confirmed in Study A as merged (run-1 estimator warm-up bias; run-1 normaliser blow-up); 0 in Study B

REPLICATED_LOCAL_HYPOTHESES=H1' (net-value ranking beats arrival order when demand exceeds capacity), H2 (net-edge screen), H5 (bandit/correlation machinery unnecessary without local evidence)
  partially: H3' (hold-normalised ranking as reference), H4 (uncertainty pooling); conditional: H6 (preemption sign depends on cost/edge)

CAP_CHANGE_AUTHORIZED=FALSE
LOCAL_INTEGRATION_AUTHORIZED=FALSE

PR8_DISPOSITION=REQUIRES_CORRECTION_BEFORE_MERGE

FINAL_VERDICT=CAPACITY_REPLICATION_INCONCLUSIVE
```
