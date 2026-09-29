"""Child process for cross-process replay tests."""
import sys, os, json, pickle, hashlib; sys.path.insert(0, 'src')
import numpy as np
import harness as H, registry as REG
from streams import make_stream

best = json.load(open("results/tune.json"))["best"]
CASES = [("recurring", 0), ("delayed_50", 1)]


def sha(b): return hashlib.sha256(b).hexdigest()[:16]


if __name__ == "__main__":
    mode = sys.argv[1]
    out = {}
    if mode == "hashes":
        for n in REG.R:
            task = REG.R[n]["task"]
            for sc, sd in CASES:
                S = make_stream(sc, sd)
                m = REG.build(n, best[n]["params"], sd)
                pr = H.run(m, S, task)
                out[f"{n}|{sc}|{sd}"] = [H.phash(pr), sha(pickle.dumps(m, protocol=4))]
    elif mode == "resume":
        d = sys.argv[2]
        for n in REG.R:
            task = REG.R[n]["task"]
            for sc, sd in CASES:
                S = make_stream(sc, sd)
                m = pickle.load(open(f"{d}/{n}|{sc}|{sd}.pkl", "rb"))
                pr = np.zeros(S.T)
                H.run(m, S, task, 2000, S.T, pr)
                out[f"{n}|{sc}|{sd}"] = [H.phash(pr[2000:]), sha(pickle.dumps(m, protocol=4)), m.meta()]
    print(json.dumps(out))
