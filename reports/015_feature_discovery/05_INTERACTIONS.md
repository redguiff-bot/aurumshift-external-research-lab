# 05 — Interaction discovery

Library: 190 products + 380 gated (`a*|b|`) terms over 20 primitives. Pair-wise only (no triples).

- **Real (OBSERVED):** of the 80 distinct candidates, >90 % were composite/symbolic (0–2 bare primitives per seed); 0 passed the validation gate; 0 retained; 0 incremental over the raw primitive span. No interaction survived the temporal hold-out.
- **Known truth (OBSERVED):** `f1*f2` (product) and `f3*|f4|` (gated) recovered in 12/12 runs, both held-out stable and non-redundant, both "new" (partial IC vs raw ≥0.003, p<0.10). The trap `f5` (sign flips by market) is a primitive present in the raw baseline, so it can never register as "new"; the trap is therefore **not informative** about invariance screening (design flaw, disclosed). `f6 ≈ f0 + noise` (redundant proxy) was never retained.
- **Multiplicity:** ≈ 590 real candidates screened per seed; the validation gate on 18–22 shortlisted candidates plus the BIC step is the control. Under the null (8 runs) 5 candidates in total passed the validation gate (~0.6/run of ~21), all removed by the BIC step; 0 reached held-out.

Verdict for interactions: **NO_STABLE** on real data; method validity demonstrated on synthetic data.
