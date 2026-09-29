"""Replay determinism, checkpoint/restore, cross-process identity, no-future-leakage (with a negative control)."""
import sys, os, json, pickle, hashlib, subprocess, numpy as np, warnings; warnings.filterwarnings("ignore")
import scenarios as S, harness as H
from models import GRID, Base
TUNED = json.load(open(os.path.join(os.path.dirname(__file__), "../results/tuned_config.json")))
def hp(name, kind): return TUNED[f"{name}|{kind}"]["hp"]
def h(a): return hashlib.sha256(np.asarray(a).tobytes()).hexdigest()[:16]

class Cheater(Base):
    """NEGATIVE CONTROL: peeks at the true label of the *current* sample. The leakage test must flag it."""
    kind = "C"
    def __init__(s, labels): s.labels = labels; s.t = 0
    def _learn(s, x, y, now): pass
    def predict(s, x): p = 0.05 + 0.9 * s.labels[s.t]; s.t += 1; return p

def child(name, kind, sc, seed):     # executed in a fresh interpreter with a different PYTHONHASHSEED
    st = S.make(sc, seed); r = H.run(st, kind, name, hp(name, kind)); print(r["hash"])

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "child": child(sys.argv[2], sys.argv[3], sys.argv[4], int(sys.argv[5])); sys.exit()
    out = []; SC, SEED, CUT, C0 = "abrupt_delayed", 1, 2000, 1500
    for (name, kind) in GRID:
        st = S.make(SC, SEED); cfg = hp(name, kind); row = dict(model=name, kind=kind)
        r1 = H.run(st, kind, name, cfg); r2 = H.run(S.make(SC, SEED), kind, name, cfg)
        row["replay_same_process"] = r1["hash"] == r2["hash"]
        # cross-process, two different PYTHONHASHSEED values
        hs = []
        for ph in ("1", "12345"):
            o = subprocess.run([sys.executable, __file__, "child", name, kind, SC, str(SEED)], capture_output=True, text=True,
                               env={**os.environ, "PYTHONHASHSEED": ph}); hs.append(o.stdout.strip())
        row["replay_cross_process"] = hs[0] == hs[1] == r1["hash"]
        # checkpoint at CUT: pickle model -> bytes -> restore -> continue; must equal uninterrupted run
        pa, m = H.run(S.make(SC, SEED), kind, name, cfg, stop_at=CUT)
        blob = pickle.dumps(m, protocol=4); m2 = pickle.loads(blob)
        pb, _ = H.run(S.make(SC, SEED), kind, name, cfg, model=m2, start=CUT, stop_at=S.T)
        row["checkpoint_resume_identical"] = h(np.concatenate([pa, pb])) == h(r1["pred"]); row["checkpoint_bytes"] = len(blob)
        # leakage: corrupt every label with index >= C0; predictions at t<=C0 must be unchanged
        rc = H.run(S.make(SC, SEED), kind, name, cfg, corrupt_after=C0)
        row["no_future_leakage"] = bool(np.array_equal(rc["pred"][:C0 + 1], r1["pred"][:C0 + 1]))
        row["last_update_ts"] = r1["last_update"]; out.append(row); print(row, flush=True)
    st = S.make(SC, SEED)
    # negative control: a cheater that reads y_t at prediction time is exposed by the same corrupt-future-labels protocol
    yc = st.yC.copy(); yc[C0:] = 1 - yc[C0:]
    ch_base = H.run(st, "C", "frozen", {}, model=Cheater(st.yC)); ch_cor = H.run(st, "C", "frozen", {}, model=Cheater(yc))
    neg = dict(cheater_detected=bool(not np.array_equal(ch_base["pred"][:C0 + 1], ch_cor["pred"][:C0 + 1])))
    print(neg); json.dump(dict(rows=out, negative_control=neg), open("../results/determinism.json", "w"), indent=1)
