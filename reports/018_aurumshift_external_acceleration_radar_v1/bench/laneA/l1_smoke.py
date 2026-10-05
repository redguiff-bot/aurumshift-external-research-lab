"""LANE A — L1 smoke : import (sous-processus frais) + appel trivial par bibliothèque.

Usage : <venv>/bin/python l1_smoke.py > l1_smoke_results.json
Aucune donnée AurumShift. Données = bruit synthétique seedé.
"""
import json
import subprocess
import sys

SMOKES = {
    "arch": "from arch.bootstrap import StationaryBootstrap, optimal_block_length, SPA, StepM, MCS;"
            "import numpy as np; x=np.random.default_rng(0).normal(size=100);"
            "print(optimal_block_length(x).to_dict('records'))",
    "statsmodels": "import numpy as np, statsmodels.api as sm;"
                   "from statsmodels.stats.multitest import multipletests;"
                   "from statsmodels.stats.weightstats import ttost_paired;"
                   "x=np.random.default_rng(0).normal(size=100);"
                   "m=sm.OLS(x,np.ones_like(x)).fit(cov_type='HAC',cov_kwds={'maxlags':4});"
                   "print(float(m.bse[0]), multipletests([0.01,0.04,0.2],method='fdr_bh')[0].tolist())",
    "confseq": "import numpy as np; from confseq.betting import betting_cs;"
               "x=np.random.default_rng(0).uniform(size=50); l,u=betting_cs(x,alpha=0.05,parallel=False); print(float(l[-1]),float(u[-1]))",
    "pingouin": "import numpy as np, pingouin as pg; r=np.random.default_rng(0);"
                "print(pg.tost(r.normal(size=50),r.normal(size=50),bound=0.5,paired=True).to_dict('records'))",
    "arviz": "import numpy as np, arviz as az; x=np.random.default_rng(0).normal(size=(1,200)); print(float(az.ess(x)))",
    "tsbootstrap": "import tsbootstrap; print(tsbootstrap.__name__)",
    "recombinator": "import recombinator; from recombinator.optimal_block_length import optimal_block_length; print('ok')",
    "doubleml": "import doubleml; print(doubleml.__version__)",
    "econml": "from econml.dml import LinearDML; print('ok')",
    "dowhy": "import dowhy; print(dowhy.__version__)",
    "causalml": "import causalml.inference.meta; print('ok')",
    "spotify_confidence": "import spotify_confidence; print('ok')",
    "quantstats": "import numpy as np, pandas as pd, quantstats as qs;"
                  "s=pd.Series(np.random.default_rng(0).normal(0.001,0.01,300),index=pd.date_range('2025-01-01',periods=300));"
                  "print(float(qs.stats.probabilistic_sharpe_ratio(s)))",
}

out = {}
for name, code in SMOKES.items():
    timed = ("import time as _t; _t0=_t.perf_counter();" + code.split(";")[0] +
             "; _ti=_t.perf_counter()-_t0;" + ";".join(code.split(";")[1:]) +
             ("; " if len(code.split(";")) > 1 else "") + "print('IMPORT_S', round(_ti,3))")
    p = subprocess.run([sys.executable, "-W", "ignore", "-c", timed], capture_output=True, text=True, timeout=600)
    lines = p.stdout.strip().splitlines()
    imp = next((l.split()[1] for l in lines if l.startswith("IMPORT_S")), None)
    out[name] = {
        "rc": p.returncode,
        "first_import_stmt_s": float(imp) if imp else None,
        "stdout_tail": [l for l in lines if not l.startswith("IMPORT_S")][-2:],
        "stderr_tail": p.stderr.strip().splitlines()[-2:] if p.returncode else [],
    }
print(json.dumps(out, indent=1))
