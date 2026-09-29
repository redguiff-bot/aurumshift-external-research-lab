"""Discovery on TRAIN+VALIDATION only (real markets, both targets). Never touches held-out."""
import sys, os, json, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import numpy as np
from joblib import Parallel, delayed
from fd import panel, features, pipeline as P, cards, data

RES = os.path.join(os.path.dirname(__file__), "..", "results")
N = features.NAMES


def one(target, seed, cfg):
    tr, _ = panel.panels(target, "train"); va, _ = panel.panels(target, "val")
    return P.discover_seed(tr, va, N, seed, cfg)


if __name__ == "__main__":
    cfg = P.Cfg()
    out = {}
    for target in ("y_ret", "y_vol"):
        t0 = time.time()
        tr, tri = panel.panels(target, "train"); va, vai = panel.panels(target, "val")
        sr = Parallel(n_jobs=4)(delayed(one)(target, s, cfg) for s in cfg.seeds)
        fin, info = P.consolidate(sr, tr, va, N, cfg)
        frozen = P.freeze(fin, tr, N)
        for c in frozen:
            c["card"] = cards.card(c, tr, va, N, target)
        out[target] = dict(cfg=cfg.__dict__, n_train_rows={m: len(tr[m][1]) for m in tr}, n_val_rows={m: len(va[m][1]) for m in va},
                           train_span=[str(tri[0]), str(tri[-1])], val_span=[str(vai[0]), str(vai[-1])],
                           seeds=[dict(seed=s["seed"], diag=s["diag"], selected=s["selected"], all=s["all"]) for s in sr],
                           consolidation=info, frozen=frozen)
        print(target, "seconds", round(time.time() - t0), "families", info.get("families_all"), "kept", info.get("families_kept"),
              "frozen", [(c["id"], c["expr"], round(c["val_ic_mean"], 4), c["seed_freq"]) for c in frozen], "mains", info.get("mains"), flush=True)
    json.dump(out, open(os.path.join(RES, "discovery_train_val.json"), "w"), indent=1, default=float)
    frozen_all = {t: [{k: c[k] for k in ("id", "kind", "expr", "sign", "mu", "sd", "nodes", "consts")} for c in out[t]["frozen"]] for t in out}
    frozen_all["mains"] = {t: out[t]["consolidation"].get("mains", []) for t in out}
    frozen_all["digest"] = P.digest({k: v for k, v in frozen_all.items()})
    json.dump(frozen_all, open(os.path.join(RES, "FROZEN.json"), "w"), indent=1)
    print("FROZEN digest", frozen_all["digest"])
