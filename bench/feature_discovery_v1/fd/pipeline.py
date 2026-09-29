"""Discovery pipeline (train/validation only) -> frozen candidates -> one-shot held-out evaluation.

Panels: dict market -> (X ndarray (n,p) of standardised primitives, y ndarray (n,)); markets share a time grid.
"""
import hashlib, json
from dataclasses import dataclass, asdict
import numpy as np
from sklearn.linear_model import Ridge

from . import expr as E
from .metrics import spearman, rank01, boot_ic, boot_p_greater, block_idx, BLOCK
from .screening import gauss, knn_mi, cmi_forward, partial_corr
from .sparse import stability_selection
from .symbolic import gp_programs
from .interactions import screen as inter_screen


@dataclass
class Cfg:
    seeds: tuple = (11, 23, 37, 41, 59)
    row_frac: float = 0.7          # fraction of train blocks each seed sees
    stab_B: int = 60
    stab_pi: float = 0.7
    gp_pop: int = 300
    gp_gens: int = 10
    gp_rows: int = 20000
    max_nodes: int = 15
    lam_node: float = 0.0005       # complexity penalty (IC units per node)
    lam_const: float = 0.001       # parameter penalty (IC units per fitted constant)
    val_boot: int = 300
    val_p: float = 0.10
    val_sign_frac: float = 0.75
    redundancy_corr: float = 0.80
    cluster_corr: float = 0.85
    min_seed_freq: float = 0.6
    top_inter: int = 8
    top_gp: int = 6
    max_per_seed: int = 5


def cols(X, names):
    return {n: X[:, i] for i, n in enumerate(names)}


def _pool(P):
    ms = list(P)
    return np.vstack([P[m][0] for m in ms]), np.concatenate([P[m][1] for m in ms]), [len(P[m][1]) for m in ms]


def _subsample_blocks(P, rng, frac, block=336):
    out = {}
    for m, (X, y) in P.items():
        nb = len(y) // block
        pick = np.sort(rng.choice(nb, max(1, int(nb * frac)), replace=False))
        idx = np.concatenate([np.arange(b * block, (b + 1) * block) for b in pick])
        out[m] = (X[idx], y[idx])
    return out


def _ic_by_market(P, names, ex, sign=1.0):
    return {m: spearman(sign * E.evaluate(ex, cols(X, names)), y) for m, (X, y) in P.items()}


def base_ridge(tr, names, mains, alpha=100.0):
    Xp, yp, _ = _pool(tr)
    ix = [names.index(n) for n in mains]
    if not ix:
        return None
    return Ridge(alpha=alpha).fit(Xp[:, ix], yp), ix


def val_gate(ex, tr, va, names, cfg, rng, base):
    """Validation statistics for one candidate expression. Sign is fixed on TRAIN."""
    t = E.parse(ex)
    nodes, nc = E.size(t), E.consts(t)
    if nodes > cfg.max_nodes:
        return None
    ic_tr = np.mean(list(_ic_by_market(tr, names, ex).values()))
    sign = 1.0 if ic_tr >= 0 else -1.0
    vals = {m: sign * E.evaluate(ex, cols(X, names)) for m, (X, y) in va.items()}
    ms, ic, bt = boot_ic(vals, {m: va[m][1] for m in va}, B=cfg.val_boot, seed=int(rng.integers(1 << 30)))
    pool_draws = bt.mean(1)
    p = boot_p_greater(pool_draws, ic.mean())
    nov = np.nan
    if base is not None:
        mdl, ix = base
        nv = []
        for m, (X, y) in va.items():
            bp = mdl.predict(X[:, ix])
            nv.append(partial_corr(gauss(vals[m]), gauss(y), bp[:, None]))
        nov = float(np.mean(nv))
    ok = ((ic > 0).mean() >= cfg.val_sign_frac) and p < cfg.val_p
    score = float(ic.mean() - cfg.lam_node * nodes - cfg.lam_const * nc)
    return dict(expr=ex, nodes=nodes, consts=nc, sign=sign, train_ic=float(ic_tr), val_ic=dict(zip(ms, map(float, ic))),
                val_ic_mean=float(ic.mean()), val_p=p, novelty=nov, score=score, gate=bool(ok and score > 0))


def simplify(ex, tr, va, names, cfg, max_iter=8):
    """Greedy hill-climb on the validation *penalised* score: replace subtrees by a child / constant 0 when the
    penalised score does not fall (removes GP hitchhikers/bloat). Sign fixed on train for each variant."""
    def sc(t):
        s_ = E.tostr(t)
        try:
            ic_tr = np.mean(list(_ic_by_market(tr, names, s_).values()))
        except Exception:
            return -9, s_
        sg = 1.0 if ic_tr >= 0 else -1.0
        ic = np.mean([spearman(sg * E.evaluate(s_, cols(va[m][0], names)), va[m][1]) for m in va])
        return ic - cfg.lam_node * E.size(t) - cfg.lam_const * E.consts(t), s_
    cur = E.parse(ex); best, _ = sc(cur)
    for _ in range(max_iter):
        improved = None
        for v in E.variants(cur):
            if not E.variables(v):
                continue
            s_v, _ = sc(v)
            if s_v >= best - 1e-4 and E.size(v) < E.size(cur) and (improved is None or s_v > improved[0]):
                improved = (s_v, v)
        if improved is None:
            break
        best, cur = improved
    return E.tostr(cur)


def discover_seed(tr, va, names, seed, cfg):
    rng = np.random.default_rng(seed)
    trs = _subsample_blocks(tr, rng, cfg.row_frac)
    Xp, yp, sizes = _pool(trs)
    diag = {}
    mi = knn_mi(Xp, yp, rng)
    diag["mi"] = dict(zip(names, map(float, mi)))
    sub = np.arange(0, len(yp), 2)
    G, gy = gauss(Xp[sub]), gauss(yp[sub])
    cmi_sel, cmi_order = cmi_forward(G, gy, names, rng, max_k=6, n_null=20)
    diag["cmi_selected"] = cmi_sel; diag["cmi_order"] = cmi_order
    stab, ev = stability_selection(Xp, yp, sizes, rng, B=cfg.stab_B, pi=cfg.stab_pi)
    diag["stab"] = dict(zip(names, map(float, stab))); diag["stab_EV_bound"] = float(ev)
    s_stab = [n for n, f in zip(names, stab) if f >= cfg.stab_pi]
    mains = sorted(set(s_stab) | set(cmi_sel))
    diag["mains"] = mains
    cm = {m: cols(X, names) for m, (X, y) in trs.items()}
    inter = inter_screen(cm, {m: y for m, (X, y) in trs.items()}, list(names), mains, rng, top=cfg.top_inter)
    diag["interaction_screen"] = [(e, r, t) for e, r, t in inter]
    ex_inter = [e for e, _, _ in inter]
    nrow = min(cfg.gp_rows, len(yp)); gi = np.sort(rng.choice(len(yp), nrow, replace=False))
    ex_gp = gp_programs(Xp[gi], yp[gi], names, seed, pop=cfg.gp_pop, gens=cfg.gp_gens, top=cfg.top_gp)
    diag["gp_programs"] = ex_gp
    base = base_ridge(trs, names, mains) if mains else None
    recs = []
    for kind, lst in (("interaction", ex_inter), ("symbolic", ex_gp)):
        for ex in lst:
            ex = simplify(ex, tr, va, names, cfg) if kind == "symbolic" else ex
            r = val_gate(ex, tr, va, names, cfg, rng, base)
            if r is not None:
                r["kind"] = kind; r["seed"] = seed; recs.append(r)
    diag["n_evaluated"] = len(recs); diag["n_gate_pass"] = sum(r["gate"] for r in recs)
    passing = sorted([r for r in recs if r["gate"]], key=lambda r: -r["score"])
    sel, vecs = [], []
    for r in passing:
        v = rank01(np.concatenate([r["sign"] * E.evaluate(r["expr"], cols(va[m][0], names)) for m in va]))
        if all(abs(v @ w) < cfg.redundancy_corr for w in vecs):
            sel.append(r); vecs.append(v)
        if len(sel) >= cfg.max_per_seed:
            break
    return dict(seed=seed, selected=sel, all=recs, diag=diag)


def consolidate(seed_results, tr, va, names, cfg):
    """Cluster selected candidates across seeds by validation-value correlation; keep families found in
    >= min_seed_freq of seeds; representative = fewest nodes (then best score)."""
    C = [r for sr in seed_results for r in sr["selected"]]
    if not C:
        return [], {}
    V = np.column_stack([rank01(np.concatenate([r["sign"] * E.evaluate(r["expr"], cols(va[m][0], names)) for m in va])) for r in C])
    order = np.argsort([-r["score"] for r in C])
    clusters = []
    for i in order:
        for c in clusters:
            if abs(V[:, i] @ V[:, c["rep"]]) >= cfg.cluster_corr:
                c["members"].append(i); break
        else:
            clusters.append(dict(rep=i, members=[i]))
    n_seeds = len(seed_results)
    fams = []
    for c in clusters:
        seeds = sorted({C[i]["seed"] for i in c["members"]})
        freq = len(seeds) / n_seeds
        rep = min(c["members"], key=lambda i: (C[i]["nodes"], -C[i]["score"]))
        fams.append(dict(freq=freq, seeds=seeds, rep=C[rep], members=[C[i]["expr"] for i in c["members"]]))
    kept = [f for f in fams if f["freq"] >= cfg.min_seed_freq]
    kept.sort(key=lambda f: -f["rep"]["score"])
    final, vecs = [], []
    for f in kept:   # non-redundancy among survivors
        r = f["rep"]
        v = rank01(np.concatenate([r["sign"] * E.evaluate(r["expr"], cols(va[m][0], names)) for m in va]))
        if all(abs(v @ w) < cfg.redundancy_corr for w in vecs):
            final.append(f); vecs.append(v)
    stab = {n: float(np.mean([sr["diag"]["stab"][n] for sr in seed_results])) for n in names}
    cmi_cnt = {n: sum(n in sr["diag"]["cmi_selected"] for sr in seed_results) for n in names}
    mains = [n for n in names if stab[n] >= cfg.stab_pi or cmi_cnt[n] >= int(np.ceil(cfg.min_seed_freq * n_seeds))]
    return final, dict(families_all=len(fams), families_kept=len(kept), mains=mains, stab_mean=stab, cmi_count=cmi_cnt)


def freeze(final, tr, names):
    Xp = np.vstack([tr[m][0] for m in tr])
    out = []
    for i, f in enumerate(final):
        r = f["rep"]
        v = r["sign"] * E.evaluate(r["expr"], cols(Xp, names))
        out.append(dict(id=f"C{i + 1:02d}", kind=r["kind"], expr=r["expr"], sign=r["sign"], mu=float(v.mean()),
                        sd=float(v.std() + 1e-12), nodes=r["nodes"], consts=r["consts"], seed_freq=f["freq"],
                        seeds=f["seeds"], family_members=f["members"], train_ic=r["train_ic"], val_ic=r["val_ic"],
                        val_ic_mean=r["val_ic_mean"], val_p=r["val_p"], novelty_val=r["novelty"], score=r["score"]))
    return out


def cand_value(c, X, names):
    return (c["sign"] * E.evaluate(c["expr"], cols(X, names)) - c["mu"]) / c["sd"]


def digest(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, default=float).encode()).hexdigest()


def evaluate_heldout(frozen, ho, unseen, names, base_pred, B=2000, seed=7):
    """ho: dict market -> (X,y) for ALL held-out markets (discovery + unseen). base_pred: dict market -> baseline
    (raw-primitive ridge) predictions. Returns per-candidate records with raw one-sided bootstrap p-values."""
    ms = list(ho); recs = []
    for c in frozen:
        v = {m: cand_value(c, ho[m][0], names) for m in ms}
        y = {m: ho[m][1] for m in ms}
        _, ic, bt = boot_ic(v, y, B=B, seed=seed)
        p = boot_p_greater(bt.mean(1), ic.mean())
        rf = {}; ry = {}
        for m in ms:
            bp = base_pred[m][:, None]
            gf, gy_ = gauss(v[m]), gauss(y[m])
            Z = np.column_stack([np.ones(len(bp)), gauss(bp[:, 0])])
            rf[m] = gf - Z @ np.linalg.lstsq(Z, gf, rcond=None)[0]
            ry[m] = gy_ - Z @ np.linalg.lstsq(Z, gy_, rcond=None)[0]
        _, pic, pbt = boot_ic(rf, ry, B=B, seed=seed)
        pn = boot_p_greater(pbt.mean(1), pic.mean())
        un = [i for i, m in enumerate(ms) if m in unseen]
        recs.append(dict(id=c["id"], ic=dict(zip(ms, map(float, ic))), ic_mean=float(ic.mean()),
                         ic_ci90=[float(np.quantile(bt.mean(1), .05)), float(np.quantile(bt.mean(1), .95))],
                         p_raw=p, frac_pos=float((ic > 0).mean()), unseen_pos=int((ic[un] > 0).sum()), n_unseen=len(un),
                         partial_ic=dict(zip(ms, map(float, pic))), partial_ic_mean=float(pic.mean()), p_partial_raw=pn))
    return recs


def decide(recs, alpha=0.05, family_size=None):
    """Pre-registered held-out decision rules. Holm across the whole frozen family (family_size >= len(recs))."""
    from .metrics import holm
    if not recs:
        return recs
    k = family_size or len(recs)
    p = list(holm([r["p_raw"] for r in recs] + [1.0] * (k - len(recs)), alpha))[:len(recs)]
    pn = list(holm([r["p_partial_raw"] for r in recs] + [1.0] * (k - len(recs)), alpha))[:len(recs)]
    for r, a, b in zip(recs, p, pn):
        r["p_holm"] = a; r["p_partial_holm"] = b
        r["stable"] = bool(a < alpha and r["frac_pos"] >= 0.75 and r["unseen_pos"] > r["n_unseen"] / 2)
        r["novel_vs_baseline"] = bool(r["stable"] and b < alpha)
    return recs
