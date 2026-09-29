| structure | pooled IC | Cochran-Q p | sign agree | ICP accepted | ICP ∩ | do(X) effect | do(X) p | class (observational only) | class (+ randomised design) | truth: X causes Y |
|---|---|---|---|---|---|---|---|---|---|---|
| A_causal_shifted_envs | +0.303 | 0.428 | 1.00 | 1/2 | ['X'] | +0.297 | 0.000 | CAUSAL_HYPOTHESIS | CAUSAL_IDENTIFIED | True |
| B_confounded_shifted_envs | +0.186 | 0.000 | 1.00 | 2/2 | [] | -0.011 | 0.017 | PREDICTIVE | PREDICTIVE | False |
| B_confounded_exchangeable_envs | +0.192 | 0.690 | 1.00 | 2/2 | [] | -0.000 | 0.949 | INVARIANT_ASSOCIATION | INVARIANT_ASSOCIATION | False |
| C_reverse_exchangeable_envs | +0.665 | 0.857 | 1.00 | 2/2 | [] | +0.002 | 0.701 | INVARIANT_ASSOCIATION | INVARIANT_ASSOCIATION | False |
| D_flipping_confounder | -0.002 | 0.000 | 0.50 | 2/2 | [] | -0.011 | 0.022 | NONE | NONE | False |
