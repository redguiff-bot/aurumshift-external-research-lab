"""Execute an external OSS ensemble component on the same synthetic streams: river.ensemble.EWARegressor (exponentially weighted average / Hedge).
river has no notion of sleeping experts; asleep experts must be given a forced forecast. We test the two available workarounds
 (a) forced 0.5   (b) forced = mean of awake forecasts (approximate abstention trick, done by the caller, not by the library)
and compare with our vectorised reference learners. Learning rates: small grid on separate tuning seeds. Writes results/oss_probe.json"""
import os, json, math, numpy as np, importlib.metadata as md
from river import ensemble, base, optim
import env as E, learners as Ls, runner as R
HERE = os.path.dirname(os.path.abspath(__file__)); RES = os.path.join(HERE, "..", "results")

class Fixed(base.Regressor):
    def __init__(self, i): self.i = i
    def predict_one(self, x): return x[self.i]
    def learn_one(self, x, y): pass

def run_river(W, s, lr, mode):
    """genuine library calls: predict_one (uses the library's own weights) then learn_one (library's Hedge update over ALL models)."""
    K = W["K"]; m = ensemble.EWARegressor([Fixed(i) for i in range(K)], learning_rate=lr); e = 0.0; T = W["T"]
    for t in range(T):
        aw = W["awake_t"][t, s]; p = W["p_t"][t, s]
        fill = (0.5 if mode == "half" or not aw.any() else float(p[aw].mean()))
        x = {i: (float(p[i]) if aw[i] else fill) for i in range(K)}
        e += (m.predict_one(x) - W["q_t"][t, s]) ** 2
        m.learn_one(x, float(W["y_t"][t, s]))
    return e / T

def main():
    out = {"river_version": md.version("river")}
    best = json.load(open(os.path.join(RES, "tuned_params.json")))
    rows = []
    for scen in ["S0_BASE_CLEAN", "S1_SEMANTICS_GAPS", "S3_RECURRENCE"]:
        Wt = R.prep(E.make_scenario(scen, 4, 2500, 55)); Wh = R.prep(E.make_scenario(scen, 4, 2500, 66))
        res = {}
        for mode in ["half", "meanfill"]:
            sc = {lr: np.mean([run_river(Wt, s, lr, mode) for s in range(4)]) for lr in [0.3, 1., 3., 10.]}
            lr = min(sc, key=sc.get); res[f"river_EWA_{mode}"] = dict(lr=lr, mse=float(np.mean([run_river(Wh, s, lr, mode) for s in range(4)])))
        for nm, L in [("EQUAL", Ls.Equal(4, 10)), ("SLEEP_HEDGE(tuned)", R.FACT["SLEEP_HEDGE"](4, 10, **best["SLEEP_HEDGE"])), ("ORACLE", Ls.Oracle(4, 10))]:
            e, _ = R.simulate(Wh, L); res[nm] = dict(mse=float(e.mean()))
        out[scen] = res; print(scen, json.dumps(res))
    json.dump(out, open(os.path.join(RES, "oss_probe.json"), "w"), indent=1)
if __name__ == "__main__": main()
