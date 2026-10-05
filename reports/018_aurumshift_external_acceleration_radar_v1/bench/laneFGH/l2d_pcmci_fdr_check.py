"""Contrôle : faux positifs PCMCI sous NULL avec et sans correction FDR (fdr_bh) de tigramite. 50 réplications."""
import json, time, numpy as np, warnings
warnings.filterwarnings("ignore")
from tigramite import data_processing as pp
from tigramite.pcmci import PCMCI
from tigramite.independence_tests.parcorr import ParCorr
rng = np.random.default_rng(777); raw = fdr = 0; t0 = time.perf_counter(); R = 50
for _ in range(R):
    e = rng.standard_normal((1000, 2))
    pc = PCMCI(dataframe=pp.DataFrame(e, var_names=["a", "b"]), cond_ind_test=ParCorr(), verbosity=0)
    r = pc.run_pcmci(tau_max=3, pc_alpha=0.05)
    raw += bool((r["p_matrix"][0, 1, 1:] < 0.05).any())
    q = pc.get_corrected_pvalues(p_matrix=r["p_matrix"], fdr_method="fdr_bh")
    fdr += bool((q[0, 1, 1:] < 0.05).any())
out = {"NULL_pcmci_a->b_raw": raw / R, "NULL_pcmci_a->b_fdr_bh": fdr / R, "sec_per_run": round((time.perf_counter() - t0) / R, 2)}
print(out); json.dump(out, open("l2d_pcmci_fdr_check.json", "w"), indent=1)
