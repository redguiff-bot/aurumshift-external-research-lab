"""T15 — wraquant.execution.almgren_chriss known-answer test: (a) lambda=0 => linear liquidation; (b) lambda>0 => sinh trajectory x_k = X sinh(kappa (T-t_k))/sinh(kappa T), kappa=sqrt(lambda sigma^2/eta) (continuous-time AC form; discretisation differences expected);
(c) monotone front-loading with lambda; (d) determinism. Impact-coefficient calibration is NOT provided by the library."""
import json, numpy as np, warnings; warnings.filterwarnings("ignore")
from wraquant.execution.optimal import almgren_chriss as ac
X, sig, eta, gam, n = 10_000, 0.02, 0.001, 0.0001, 20
res = {}
x0 = np.asarray(ac(X, sigma=sig, eta=eta, gamma=gam, lambda_risk=0.0, n_periods=n), float)
lin = X*(1-np.arange(n+1)/n); res["lambda0_max_abs_dev_from_linear_shares"] = float(np.max(np.abs(x0-lin)))
for lam in (1e-3, 1e-2, 1e-1, 1.0):
    x = np.asarray(ac(X, sigma=sig, eta=eta, gamma=gam, lambda_risk=lam, n_periods=n), float)
    kappa = np.sqrt(lam*sig**2/eta); t = np.arange(n+1); ref = X*np.sinh(kappa*(n-t))/np.sinh(kappa*n)
    res[f"lambda_{lam}"] = dict(ends=[float(x[0]), float(x[-1])], monotone=bool(np.all(np.diff(x) <= 1e-9)), first_trade=float(x[0]-x[1]), max_rel_dev_from_continuous_sinh=float(np.max(np.abs(x-ref))/X))
a = np.asarray(ac(X, sigma=sig, eta=eta, gamma=gam, lambda_risk=0.1, n_periods=n), float); b = np.asarray(ac(X, sigma=sig, eta=eta, gamma=gam, lambda_risk=0.1, n_periods=n), float)
res["deterministic"] = bool(np.array_equal(a, b))
print(json.dumps(res))
