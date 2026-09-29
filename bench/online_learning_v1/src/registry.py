"""Model registry: name -> (task, factory(params, seed), grid, default)."""
from river import linear_model, tree, forest, ensemble, optim
import models as M
from functools import partial

R = {}


def reg(name, task, factory, grid, default, family, complexity):
    R[name] = dict(task=task, factory=factory, grid=grid, default=default,
                   family=family, complexity=complexity)


def rw(task, make):
    return lambda p, seed: M.RiverWrap(task, lambda: make(p, seed))


# ---------------- regression ----------------
reg("null_reg", "reg", lambda p, s: M.Null("reg"), [{}], {}, "control", 0)
reg("frozen_ridge", "reg", lambda p, s: M.BatchModel("reg", "frozen", n0=p["n0"]),
    [{"n0": 250}, {"n0": 1000}], {"n0": 500}, "baseline", 1)
reg("periodic_ridge", "reg", lambda p, s: M.BatchModel("reg", "periodic", R=p["R"]),
    [{"R": 100}, {"R": 250}, {"R": 500}], {"R": 250}, "baseline", 1)
reg("rolling_ridge", "reg", lambda p, s: M.BatchModel("reg", "rolling", W=p["W"], K=25),
    [{"W": 100}, {"W": 200}, {"W": 400}, {"W": 800}], {"W": 400}, "baseline", 1)
reg("rolling_ridge_drift", "reg",
    lambda p, s: M.BatchModel("reg", "rolling_drift", drift_delta=p["delta"], wmax=1000, K=25),
    [{"delta": 0.1}, {"delta": 0.02}, {"delta": 0.002}], {"delta": 0.002}, "drift_composite", 2)
reg("rls", "reg", lambda p, s: M.RLS(lam=p["lam"]),
    [{"lam": 0.99}, {"lam": 0.995}, {"lam": 0.998}, {"lam": 0.9995}], {"lam": 0.998}, "incremental", 1)
reg("kalman_rw", "reg", lambda p, s: M.KalmanRW(q=p["q"]),
    [{"q": 1e-5}, {"q": 1e-4}, {"q": 1e-3}, {"q": 1e-2}], {"q": 1e-3}, "incremental", 1)
reg("river_sgd_lin", "reg",
    rw("reg", lambda p, s: linear_model.LinearRegression(optimizer=optim.SGD(p["lr"]))),
    [{"lr": 0.005}, {"lr": 0.02}, {"lr": 0.05}], {"lr": 0.02}, "incremental", 1)
reg("river_pa_reg", "reg",
    rw("reg", lambda p, s: linear_model.PARegressor(C=p["C"], mode=1)),
    [{"C": 0.01}, {"C": 0.1}, {"C": 1.0}], {"C": 0.1}, "incremental", 1)
reg("river_hoeffding_reg", "reg",
    rw("reg", lambda p, s: tree.HoeffdingTreeRegressor(grace_period=p["gp"])),
    [{"gp": 50}, {"gp": 200}], {"gp": 50}, "tree", 3)
reg("river_arf_reg", "reg",
    rw("reg", lambda p, s: forest.ARFRegressor(n_models=5, grace_period=p["gp"], seed=s)),
    [{"gp": 50}, {"gp": 200}], {"gp": 50}, "tree", 4)
reg("rls_reset_adwin", "reg",
    lambda p, s: M.Reset(partial(M.RLS, lam=1.0), p["delta"], "reg"),
    [{"delta": 0.1}, {"delta": 0.02}, {"delta": 0.002}], {"delta": 0.002}, "drift_composite", 2)
reg("rls_bank_custom", "reg",
    lambda p, s: M.Bank(partial(M.RLS, lam=0.999), p["delta"], "reg"),
    [{"delta": 0.1}, {"delta": 0.02}, {"delta": 0.002}], {"delta": 0.002}, "custom", 4)

# ---------------- classification ----------------
reg("null_clf", "clf", lambda p, s: M.Null("clf"), [{}], {}, "control", 0)
reg("frozen_logit", "clf", lambda p, s: M.BatchModel("clf", "frozen", n0=p["n0"]),
    [{"n0": 250}, {"n0": 1000}], {"n0": 500}, "baseline", 1)
reg("periodic_logit", "clf", lambda p, s: M.BatchModel("clf", "periodic", R=p["R"]),
    [{"R": 100}, {"R": 250}, {"R": 500}], {"R": 250}, "baseline", 1)
reg("rolling_logit", "clf", lambda p, s: M.BatchModel("clf", "rolling", W=p["W"], K=25),
    [{"W": 200}, {"W": 400}, {"W": 800}, {"W": 1600}], {"W": 400}, "baseline", 1)
reg("rolling_logit_drift", "clf",
    lambda p, s: M.BatchModel("clf", "rolling_drift", drift_delta=p["delta"], wmax=1600, K=25),
    [{"delta": 0.1}, {"delta": 0.02}, {"delta": 0.002}], {"delta": 0.002}, "drift_composite", 2)
reg("ekf_logit", "clf", lambda p, s: M.EKFLogit(lam=p["lam"]),
    [{"lam": 0.99}, {"lam": 0.995}, {"lam": 0.998}, {"lam": 0.9995}], {"lam": 0.998}, "incremental", 1)
reg("river_sgd_logit", "clf",
    rw("clf", lambda p, s: linear_model.LogisticRegression(optimizer=optim.SGD(p["lr"]))),
    [{"lr": 0.005}, {"lr": 0.02}, {"lr": 0.05}], {"lr": 0.02}, "incremental", 1)
reg("river_pa_clf", "clf",
    rw("clf", lambda p, s: linear_model.PAClassifier(C=p["C"], mode=1)),
    [{"C": 0.01}, {"C": 0.1}, {"C": 1.0}], {"C": 0.1}, "incremental", 1)
reg("river_hoeffding_clf", "clf",
    rw("clf", lambda p, s: tree.HoeffdingTreeClassifier(grace_period=p["gp"])),
    [{"gp": 50}, {"gp": 200}], {"gp": 50}, "tree", 3)
reg("river_arf_clf", "clf",
    rw("clf", lambda p, s: forest.ARFClassifier(n_models=5, grace_period=p["gp"], seed=s)),
    [{"gp": 50}, {"gp": 200}], {"gp": 50}, "tree", 4)
reg("river_adaboost_clf", "clf",
    rw("clf", lambda p, s: ensemble.AdaBoostClassifier(
        tree.HoeffdingTreeClassifier(grace_period=p["gp"]), n_models=5, seed=s)),
    [{"gp": 50}, {"gp": 200}], {"gp": 50}, "tree", 4)
reg("ekf_reset_adwin", "clf",
    lambda p, s: M.Reset(partial(M.EKFLogit, lam=1.0), p["delta"], "clf"),
    [{"delta": 0.1}, {"delta": 0.02}, {"delta": 0.002}], {"delta": 0.002}, "drift_composite", 2)
reg("ekf_bank_custom", "clf",
    lambda p, s: M.Bank(partial(M.EKFLogit, lam=0.999), p["delta"], "clf"),
    [{"delta": 0.1}, {"delta": 0.02}, {"delta": 0.002}], {"delta": 0.002}, "custom", 4)
reg("sgd_logit_platt", "clf",
    lambda p, s: M.Platt(M.RiverWrap("clf", lambda: linear_model.LogisticRegression(optimizer=optim.SGD(0.02))), lr=p["lr"]),
    [{"lr": 0.005}, {"lr": 0.02}], {"lr": 0.01}, "calibration", 2)
reg("hoeffding_platt", "clf",
    lambda p, s: M.Platt(M.RiverWrap("clf", lambda: tree.HoeffdingTreeClassifier(grace_period=50)), lr=p["lr"]),
    [{"lr": 0.005}, {"lr": 0.02}], {"lr": 0.01}, "calibration", 4)


def build(name, params, seed):
    return R[name]["factory"](params, seed)
