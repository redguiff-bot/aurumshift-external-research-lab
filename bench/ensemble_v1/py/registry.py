"""Method registry and tuning grids. Every method: (builder(hp)->learner, grid list-of-dicts)."""
import itertools
import learners as L


def grid(**kw):
    ks = list(kw)
    return [dict(zip(ks, v)) for v in itertools.product(*[kw[k] for k in ks])] or [{}]


K = 12
REG = {
    # baselines
    "Equal":        (lambda hp: L.Equal(K), grid()),
    "Static":       (lambda hp: L.Static(K, **hp), grid(kappa=[5, 20, 60], C=[150, 300])),
    "WTA":          (lambda hp: L.WTA(K, **hp), grid(a=[0.02, 0.05, 0.15])),
    "EWMA":         (lambda hp: L.EWMA(K, **hp), grid(a=[0.02, 0.05, 0.15], beta=[10, 30, 100])),
    # candidates
    "HedgePlain":   (lambda hp: L.HedgePlain(K, **hp), grid(eta=[1, 3, 10, 30])),
    "SleepHedge":   (lambda hp: L.SleepHedge(K, **hp), grid(eta=[3, 10, 30, 100])),
    "SleepEG":      (lambda hp: L.SleepEG(K, **hp), grid(eta=[5, 20, 60, 200])),
    "FixedShare":   (lambda hp: L.SleepHedge(K, **hp), grid(eta=[10, 30, 100], alpha=[0.002, 0.01, 0.05])),
    "DiscFreeze":   (lambda hp: L.SleepHedge(K, dorm="freeze", **hp), grid(eta=[10, 30], gamma=[0.98, 0.995])),
    "DiscAmnesty":  (lambda hp: L.SleepHedge(K, dorm="amnesty", **hp), grid(eta=[10, 30], gamma=[0.99, 0.997])),
    "SH_bounded":   (lambda hp: L.SleepHedge(K, cap=0.7, **hp), grid(eta=[10, 30, 100], B=[2.0, 4.0], floor=[0.05, 0.2])),
    "EWMA_bounded": (lambda hp: BoundedEWMA(**hp), grid(a=[0.05, 0.15], beta=[30, 100], floor=[0.1, 0.3])),
    "BMA":          (lambda hp: L.BMA(K, **hp), grid(kappa=[15, 50, 150], lam=[0.97, 0.995], opt=[0.0, 0.03])),
    "CtxOracle":    (lambda hp: L.CtxMix(K, ctx_key="regime", alpha=0.005, **hp), grid(eta=[10, 30], n0=[30, 100])),
    "CtxLag":       (lambda hp: L.CtxMix(K, ctx_key="regime_lag", alpha=0.005, **hp), grid(eta=[10, 30], n0=[30, 100])),
    "CtxNoisy":     (lambda hp: L.CtxMix(K, ctx_key="regime_noisy", alpha=0.005, **hp), grid(eta=[10, 30], n0=[30, 100])),
    "DivEWMA":      (lambda hp: DivOver("EWMA", hp), grid(tau=[0.3, 0.5, 0.7])),
    "DivSH":        (lambda hp: DivOver("SleepHedge", hp), grid(tau=[0.3, 0.5, 0.7])),
    # bandit comparators
    "SleepEXP3":    (lambda hp: L.SleepEXP3(K, **hp), grid(eta=[0.02, 0.1, 0.5], gamma=[0.02, 0.1])),
    "DUCB":         (lambda hp: L.DUCB(K, **hp), grid(gamma=[0.98, 0.995], c=[0.05, 0.2])),
}

# second-stage bases for Div* (filled by tuning driver with the winning base hyper-parameters)
BASE_HP = {"EWMA": {"a": 0.05, "beta": 30.0}, "SleepHedge": {"eta": 10.0}}


class BoundedEWMA(L.EWMA):
    name = "EWMA_bounded"

    def __init__(self, floor=0.1, cap=0.7, **hp):
        super().__init__(K, **hp)
        self.floor, self.cap = floor, cap

    def weights(self, alloc, ctx):
        return L.bound(super().weights(alloc, ctx), alloc, self.floor, self.cap)


def DivOver(base, hp):
    hp = dict(hp)
    tau = hp.pop("tau")
    b = L.EWMA(K, **BASE_HP["EWMA"]) if base == "EWMA" else L.SleepHedge(K, **BASE_HP["SleepHedge"])
    return L.Div(K, b, tau=tau)


# Methods rerun under the 'naive_zero' semantic error (missing/inactive => worst reward)
NAIVE_SUBSET = ["EWMA", "HedgePlain", "SleepHedge", "FixedShare", "BMA", "DiscFreeze"]
BASELINES = ["Equal", "Static", "WTA", "EWMA"]
BANDITS = ["SleepEXP3", "DUCB"]
