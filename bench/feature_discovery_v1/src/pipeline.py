"""Feature-discovery pipeline. Fit stages see ONLY the discovery_train segment of the discovery markets.
Validation segment is used to gate / finalize. Held-out is evaluated once, on a frozen final list."""
import re, json, hashlib, time
import numpy as np
from scipy import stats
from sklearn.feature_selection import mutual_info_regression
from sklearn.linear_model import Lasso, Ridge, LassoCV, lasso_path
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.inspection import permutation_importance

PROTO = json.load(open(__import__("os").path.join(__import__("os").path.dirname(__file__), "..", "configs", "protocol.json")))
CLIP = 6.0

# ------------------------------------------------------------------ panel
class Panel:
    """P[T,M,p] primitives (already causal), y[T,M]; markets list; disc = idx of discovery markets."""
    def __init__(self, P, y, prims, markets, disc, fracs=None, embargo=24, neff_div=4.0):
        self.neff_div = neff_div  # overlap of forward-return labels (real: horizon H=4; synthetic: 1)
        self.P, self.y, self.prims, self.markets, self.disc = P, y, list(prims), list(markets), list(disc)
        T = P.shape[0]; f = fracs or PROTO["splits"]
        a, b = int(T * f["discovery_train"][1]), int(T * f["validation"][1])
        self.sl = {"train": slice(0, a - embargo), "val": slice(a + embargo, b - embargo), "test": slice(b + embargo, T)}
        self.access = []
        self.unseen = [i for i in range(len(markets)) if i not in self.disc]

    def seg(self, name):
        self.access.append(name); return self.sl[name]

# ------------------------------------------------------------------ candidates
class Cand:
    def __init__(self, kind, spec, nodes, formula, prog=None):
        self.kind, self.spec, self.nodes, self.formula, self.prog = kind, spec, nodes, formula, prog
        self.mu = self.sd = None; self.sgn = 1.0; self.beta = None; self.parents = []
    @property
    def key(self): return f"{self.kind}:{self.formula}"
    def raw(self, P, prims):
        """P: [..., p] -> [...]"""
        ix = {n: i for i, n in enumerate(prims)}
        k = self.kind
        if k == "prim": return P[..., ix[self.spec[0]]]
        if k == "prod": return P[..., ix[self.spec[0]]] * P[..., ix[self.spec[1]]]
        if k == "gate": return P[..., ix[self.spec[0]]] * np.abs(P[..., ix[self.spec[1]]])
        if k == "sym":
            sh = P.shape[:-1]; out = self.prog.execute(P.reshape(-1, P.shape[-1])); return out.reshape(sh)
        raise ValueError(k)
    def fit_std(self, P, prims, y=None):
        r = self.raw(P, prims); r = np.nan_to_num(r, nan=0.0, posinf=0.0, neginf=0.0)
        self.mu, self.sd = float(r.mean()), float(r.std() + 1e-12)
        if y is not None:
            z = np.clip((r - self.mu) / self.sd, -CLIP, CLIP)
            c = np.corrcoef(z.ravel(), y.ravel())[0, 1]; self.sgn = 1.0 if (c >= 0 or np.isnan(c)) else -1.0
    def eval(self, P, prims):
        r = np.nan_to_num(self.raw(P, prims), nan=0.0, posinf=0.0, neginf=0.0)
        z = np.clip((r - self.mu) / self.sd, -CLIP, CLIP) * self.sgn
        if self.beta is not None:   # orthogonalised: subtract frozen projection on parents
            z = z - sum(b * p.eval(P, prims) for b, p in zip(self.beta, self.parents))
        return z

def library(prims):
    out = [Cand("prim", (a,), 1, a) for a in prims]
    for i, a in enumerate(prims):
        for b in prims[i + 1:]:
            out.append(Cand("prod", (a, b), 3, f"({a}*{b})"))
        for b in prims:
            if a != b: out.append(Cand("gate", (a, b), 4, f"({a}*|{b}|)"))
    return out

# ------------------------------------------------------------------ stats helpers
def flat(A, sl): return A[sl].reshape(-1) if A.ndim == 2 else A[sl].reshape(-1, A.shape[-1])

def block_idx(n, block, rng):
    nb = int(np.ceil(n / block)); st = rng.integers(0, n - block + 1, nb)
    return (st[:, None] + np.arange(block)[None]).ravel()[:n]

def pooled_ic(F, Y):
    """F,Y [T,M]: equal-weight mean over markets of Pearson corr"""
    Fc, Yc = F - F.mean(0), Y - Y.mean(0)
    c = (Fc * Yc).sum(0) / (np.sqrt((Fc ** 2).sum(0) * (Yc ** 2).sum(0)) + 1e-18)
    return c.mean(), c

def ic_boot(F, Y, B=200, block=None, seed=0):
    """time-block bootstrap SE of pooled IC (blocks shared across markets => cross-market dependence preserved)"""
    block = block or PROTO["heldout_criteria"]["bootstrap_block"]; rng = np.random.default_rng(seed)
    n = F.shape[0]; est = np.empty(B)
    for b in range(B):
        i = block_idx(n, block, rng); est[b] = pooled_ic(F[i], Y[i])[0]
    ic, per = pooled_ic(F, Y); se = est.std(ddof=1) + 1e-12
    p = 2 * (1 - stats.norm.cdf(abs(ic) / se))
    return dict(ic=float(ic), se=float(se), p=float(p), per_market=per.tolist())

def decile_profile(F, Y, q=10):
    f = F.reshape(-1); y = Y.reshape(-1); e = np.quantile(f, np.linspace(0, 1, q + 1)); e[-1] += 1e-9
    b = np.clip(np.searchsorted(e, f, side="right") - 1, 0, q - 1)
    return [float(y[b == i].mean()) for i in range(q)]

def cochran_Q(per, se_each):
    w = 1 / np.maximum(se_each, 1e-9) ** 2; m = (w * per).sum() / w.sum()
    Q = (w * (per - m) ** 2).sum(); return float(1 - stats.chi2.cdf(Q, len(per) - 1))

def bh(p, q):
    p = np.asarray(p); m = len(p); o = np.argsort(p); ok = np.zeros(m, bool)
    thr = q * (np.arange(1, m + 1) / m); k = np.where(p[o] <= thr)[0]
    if len(k): ok[o[: k.max() + 1]] = True
    return ok

def ns(x):  # rank -> normal scores
    r = stats.rankdata(x, axis=0) if x.ndim > 1 else stats.rankdata(x)
    return stats.norm.ppf((r - 0.5) / len(r))

# ------------------------------------------------------------------ discovery stages
def stage_screen(cands, Ztr, ytr, rng, n_mi=6000, top_k=None, neff_div=4.0):
    """MI screening (kNN MI, pooled) + greedy Gaussian-copula CMI selection with orthogonalisation."""
    top_k = top_k or PROTO["screens"]["mi_top_k"]
    ix = rng.choice(len(ytr), min(n_mi, len(ytr)), replace=False)
    mi = mutual_info_regression(Ztr[ix], ytr[ix], n_neighbors=5, random_state=int(rng.integers(1 << 30)))
    order = np.argsort(-mi)[:top_k]
    # greedy CMI on Gaussian-copula scores; stop at chi2(1) 99% given effective n = n/H
    Zn = np.column_stack([ns(Ztr[:, j]) for j in order]); yn = ns(ytr)
    n_eff = len(ytr) / neff_div; thr = stats.chi2.ppf(0.99, 1) / (2 * n_eff)
    sel, ortho = [], []           # ortho: (cand idx, parents idx list, beta)
    R = yn.copy(); Q = Zn.copy()
    for _ in range(PROTO["screens"]["cmi_max_steps"]):
        # partial corr of each remaining col with y, both residualised on selected
        best, bj = 0, None
        for k in range(Zn.shape[1]):
            if k in sel: continue
            if sel:
                S = Zn[:, sel]; g = np.linalg.lstsq(S, Zn[:, k], rcond=None)[0]; e = Zn[:, k] - S @ g
                h = np.linalg.lstsq(S, yn, rcond=None)[0]; ry = yn - S @ h
            else: e, ry = Zn[:, k], yn
            if e.std() < 1e-6: continue
            rho = np.corrcoef(e, ry)[0, 1]; cmi = -0.5 * np.log(1 - rho ** 2)
            if cmi > best: best, bj = cmi, k
        if bj is None or best < thr: break
        sel.append(bj)
    return dict(mi=mi, mi_top=order.tolist(), cmi_sel=[int(order[k]) for k in sel], cmi_thr=float(thr))

def stage_stability(Ztr, ytr, T_index, rng, n_sub=None, block=240):
    """Meinshausen-Buhlmann stability selection with time-block subsampling (blocks shared across markets)."""
    n_sub = n_sub or PROTO["screens"]["stab_n_subsamples"]
    Ztr = Ztr.astype(np.float32); y = ytr - ytr.mean()
    # lambda: largest alpha on the full train giving >=10 non-zeros
    sub = rng.choice(len(y), min(20000, len(y)), replace=False)
    al, co, _ = lasso_path(Ztr[sub], y[sub], alphas=40, eps=1e-2)
    nz = (np.abs(co) > 1e-8).sum(0); k = np.where(nz >= 10)[0]; alpha = float(al[k[0]] if len(k) else al[-1])
    blocks = T_index // block; ub = np.unique(blocks); freq = np.zeros(Ztr.shape[1])
    for _ in range(n_sub):
        pick = rng.choice(ub, len(ub) // 2, replace=False); m = np.isin(blocks, pick)
        r = np.flatnonzero(m); r = r[rng.choice(len(r), min(15000, len(r)), replace=False)]
        f = Lasso(alpha=alpha, max_iter=2000, tol=1e-3, precompute=True).fit(Ztr[r], y[r]); freq += np.abs(f.coef_) > 1e-8
    return freq / n_sub, alpha

def stage_symbolic(P, prims, tr, y, seeds, pars, rng, pop=None, gens=None):
    from gplearn.genetic import SymbolicRegressor
    cfg = PROTO["symbolic"]; pop = pop or cfg["pop"]; gens = gens or cfg["gens"]
    Xp = P[tr].reshape(-1, P.shape[-1]); yp = y[tr].reshape(-1)
    ix = rng.choice(len(yp), min(10000, len(yp)), replace=False); Xs, ys = np.nan_to_num(Xp[ix]), yp[ix]
    progs = []
    for s in seeds:
        for pc in pars:
            m = SymbolicRegressor(population_size=pop, generations=gens, tournament_size=15, stopping_criteria=1.0,
                                  function_set=("add", "sub", "mul", "div", "neg", "abs", "max", "min"), metric="pearson",
                                  parsimony_coefficient=pc, init_depth=(2, 3), p_crossover=0.7, p_subtree_mutation=0.1,
                                  p_hoist_mutation=0.05, p_point_mutation=0.1, max_samples=0.7, random_state=int(s), n_jobs=1).fit(Xs, ys)
            last = sorted(m._programs[-1], key=lambda p: -p.fitness_)
            seen = set()
            for p in last:
                if str(p) in seen: continue
                seen.add(str(p))
                if len(seen) > 2: break
                progs.append((s, pc, p))
    out = []
    for s, pc, p in progs:
        f = re.sub(r"X(\d+)", lambda m_: prims[int(m_.group(1))], str(p))
        out.append((s, pc, Cand("sym", (s, pc), len(p.program), f, prog=p)))
    return out

def cluster_symbolic(syms, P, prims, tr, thr=0.9, min_seeds=3):
    """single-linkage clusters of programs on |corr| over train rows; stable = present in >= min_seeds distinct seeds"""
    Xs = P[tr].reshape(-1, P.shape[-1])[::10]
    V = []
    for _, _, c in syms:
        v = np.nan_to_num(c.raw(Xs, prims)); V.append((v - v.mean()) / (v.std() + 1e-12))
    n = len(V); par = list(range(n))
    def f(a):
        while par[a] != a: par[a] = par[par[a]]; a = par[a]
        return a
    for i in range(n):
        for j in range(i + 1, n):
            if abs(np.mean(V[i] * V[j])) > thr: par[f(i)] = f(j)
    groups = {}
    for i in range(n): groups.setdefault(f(i), []).append(i)
    stable, allrep = [], []
    for g in groups.values():
        seeds = {syms[i][0] for i in g}; rep = min(g, key=lambda i: (syms[i][2].nodes, i))
        allrep.append((syms[rep][2], len(seeds)))
        if len(seeds) >= min_seeds and V[rep].std() > 0.5: stable.append((syms[rep][2], len(seeds)))
    return stable, allrep

# ------------------------------------------------------------------ models
def r2_0(y, yh): return 1 - ((y - yh) ** 2).sum() / (y ** 2).sum()

def paired_block_delta(y, a, b, B=200, seed=0):
    """OOS R2 delta (b over a) and time-block bootstrap CI; y,a,b [T,M]"""
    rng = np.random.default_rng(seed); n = y.shape[0]; blk = PROTO["heldout_criteria"]["bootstrap_block"]
    def d(i): return r2_0(y[i], b[i]) - r2_0(y[i], a[i])
    base = d(np.arange(n)); est = [d(block_idx(n, blk, rng)) for _ in range(B)]
    return dict(delta=float(base), lo=float(np.quantile(est, 0.05)), hi=float(np.quantile(est, 0.95)),
                markets_improve=float(np.mean([r2_0(y[:, m], b[:, m]) > r2_0(y[:, m], a[:, m]) for m in range(y.shape[1])])))

def fit_ridge(Xtr, ytr, Xva, yva):
    best = None
    for a in (1, 10, 100, 1000, 10000):
        m = Ridge(alpha=a).fit(Xtr, ytr); s = r2_0(yva, m.predict(Xva))
        if best is None or s > best[0]: best = (s, m, a)
    return best[1], best[2]

def model_matrix(panel, cands, seg, with_raw=True):
    sl = panel.seg(seg); cols = []
    if with_raw: cols.append(np.nan_to_num(panel.P[sl]).reshape(-1, panel.P.shape[-1]))
    for c in cands: cols.append(c.eval(panel.P[sl], panel.prims).reshape(-1, 1))
    return np.hstack(cols) if cols else np.zeros((panel.y[sl].size, 0))

def baselines(panel, library_cands, seed=0):
    """B1 raw ridge, B2 LassoCV(primitives), B3 tree-importance top-k -> ridge, B4 permutation-importance top-k -> ridge, GBM full."""
    tr, va = panel.seg("train"), panel.seg("val"); p = panel.P.shape[-1]
    ytr, yva = panel.y[tr][:, panel.disc].reshape(-1), panel.y[va][:, panel.disc].reshape(-1)
    Xtr = np.nan_to_num(panel.P[tr][:, panel.disc]).reshape(-1, p); Xva = np.nan_to_num(panel.P[va][:, panel.disc]).reshape(-1, p)
    out = {}
    m, a = fit_ridge(Xtr, ytr, Xva, yva); out["B1_raw_ridge"] = dict(model=m, cols=list(range(p)), alpha=a)
    las = LassoCV(cv=4, alphas=30, max_iter=3000, random_state=seed).fit(Xtr, ytr)
    out["B2_lasso"] = dict(model=las, cols=list(range(p)), k=int((np.abs(las.coef_) > 0).sum()))
    gb = HistGradientBoostingRegressor(max_depth=3, max_iter=150, learning_rate=0.05, random_state=seed).fit(Xtr, ytr)
    out["B5_gbm_full"] = dict(model=gb, cols=list(range(p)))
    # tree importance: impurity-style proxy = refit on random subsets? use permutation on TRAIN (tree) vs on VAL (permutation)
    pit = permutation_importance(gb, Xtr[::5], ytr[::5], n_repeats=3, random_state=seed, scoring="neg_mean_squared_error").importances_mean
    k = 5; top = list(np.argsort(-pit)[:k]); m3, a3 = fit_ridge(Xtr[:, top], ytr, Xva[:, top], yva)
    out["B3_tree_importance_top5"] = dict(model=m3, cols=top, names=[panel.prims[i] for i in top])
    pv = permutation_importance(gb, Xva, yva, n_repeats=5, random_state=seed, scoring="neg_mean_squared_error").importances_mean
    top4 = list(np.argsort(-pv)[:k]); m4, a4 = fit_ridge(Xtr[:, top4], ytr, Xva[:, top4], yva)
    out["B4_permutation_importance_top5"] = dict(model=m4, cols=top4, names=[panel.prims[i] for i in top4])
    return out

def predict_panel(panel, mdl, seg):
    sl = panel.seg(seg); T = panel.P[sl].shape[0]; M = panel.P.shape[1]
    X = np.nan_to_num(panel.P[sl]).reshape(-1, panel.P.shape[-1])[:, mdl["cols"]]
    return mdl["model"].predict(X).reshape(T, M)

# ------------------------------------------------------------------ main pipeline
def run(panel, seed, sym_seeds=5, sym_pars=None, sym_pop=None, sym_gens=None, log=print, do_baselines=True, on_lock=None):
    t0 = time.time(); rng = np.random.default_rng(seed); prims = panel.prims; D = panel.disc
    sym_pars = sym_pars or PROTO["symbolic"]["parsimony"]
    tr, va, te = panel.seg("train"), panel.seg("val"), panel.sl["test"]   # slice only; data access logged below
    Ptr = panel.P[tr][:, D]; ytr = panel.y[tr][:, D]
    T_index = np.repeat(np.arange(Ptr.shape[0])[:, None], len(D), 1).reshape(-1)
    lib = library(prims)
    for c in lib: c.fit_std(Ptr, prims, ytr)
    Ztr = np.column_stack([c.eval(Ptr, prims).reshape(-1) for c in lib]).astype(np.float32)
    y1 = ytr.reshape(-1)
    log(f"[{time.time()-t0:.0f}s] library {len(lib)} candidates, train rows {len(y1)}")
    sc = stage_screen(lib, Ztr, y1, rng, neff_div=panel.neff_div)
    log(f"[{time.time()-t0:.0f}s] MI top{len(sc['mi_top'])}, CMI-selected {len(sc['cmi_sel'])}")
    freq, alpha = stage_stability(Ztr, y1, T_index, rng)
    stab = [int(j) for j in np.where(freq >= PROTO["screens"]["stab_select_freq"])[0]]
    log(f"[{time.time()-t0:.0f}s] stability selection alpha={alpha:.4f}: {len(stab)} features with freq>=0.6")
    sy = stage_symbolic(panel.P, prims, tr, panel.y, list(range(seed * 100, seed * 100 + sym_seeds)), sym_pars, rng, sym_pop, sym_gens) if False else \
         stage_symbolic(Ptr, prims, slice(None), ytr, list(range(seed * 100, seed * 100 + sym_seeds)), sym_pars, rng, sym_pop, sym_gens)
    stable_sym, all_sym = cluster_symbolic(sy, Ptr, prims, slice(None))
    for c, _ in all_sym: c.fit_std(Ptr, prims, ytr)
    log(f"[{time.time()-t0:.0f}s] symbolic: {len(sy)} programs, {len(all_sym)} clusters, {len(stable_sym)} stable (>=3 seeds)")

    # ---- candidate pool (each with provenance)
    pool = {}
    def add(c, why):
        pool.setdefault(c.key, dict(c=c, why=set()))["why"].add(why)
    for j in sc["cmi_sel"]: add(lib[j], "CMI")
    for j in sc["mi_top"][:10]: add(lib[j], "MI_top10")
    for j in stab: add(lib[j], "STABSEL")
    for c, ns_ in stable_sym: add(c, f"SYM_STABLE({ns_}seeds)")
    for c, ns_ in all_sym: add(c, "SYM_ANY")
    # de-duplicate near-identical (|corr|>0.97 on train)
    cs = [v["c"] for v in pool.values()]
    Ztr_c = np.column_stack([c.eval(Ptr, prims).reshape(-1) for c in cs])
    keep, dropped = [], []
    for i, c in enumerate(cs):
        if any(abs(np.corrcoef(Ztr_c[:, i], Ztr_c[:, j])[0, 1]) > 0.97 for j in keep): dropped.append(c.key)
        else: keep.append(i)
    discovered = [cs[i] for i in keep]
    for i in keep: pool[cs[i].key]["dedup"] = True
    log(f"[{time.time()-t0:.0f}s] discovered (pre-validation, deduplicated): {len(discovered)}")

    # ---- validation gate (train orientation frozen)
    Pva, yva = panel.P[va], panel.y[va]; Vd = yva[:, D]
    rows = []
    for c in discovered:
        Ftr = c.eval(Ptr, prims); Fva = c.eval(Pva[:, D], prims)
        itr = pooled_ic(Ftr, ytr); iva = ic_boot(Fva, Vd, seed=seed)
        sgn_agree = float(np.mean(np.sign(iva["per_market"]) == 1.0))   # orientation frozen: +1 = same as train
        gate = (iva["ic"] > 0) and (sgn_agree >= PROTO["heldout_criteria"]["min_market_sign_agreement"]) and (iva["p"] < 0.10)
        rows.append(dict(key=c.key, kind=c.kind, nodes=c.nodes, why=sorted(pool[c.key]["why"]), ic_train=float(itr[0]),
                         ic_val=iva["ic"], p_val=iva["p"], sign_agree_val=sgn_agree, gate=bool(gate)))
    gated = [c for c, r in zip(discovered, rows) if r["gate"]]
    log(f"[{time.time()-t0:.0f}s] passed validation gate: {len(gated)}/{len(discovered)}")

    # ---- final selection on VALIDATION ONLY: greedy BIC-penalised incremental OOS(val) gain over raw ridge
    base = baselines(panel, lib) if do_baselines else None
    Xtr_raw = model_matrix(panel, [], "train")[np.tile(np.isin(np.arange(panel.P.shape[1]), D), Ptr.shape[0])]
    ytr_f = ytr.reshape(-1)
    Xva_raw = np.nan_to_num(panel.P[va][:, D]).reshape(-1, len(prims)); yva_f = Vd.reshape(-1)
    n_eff = len(yva_f) / panel.neff_div
    final, cur_r2 = [], None
    m0, a0 = fit_ridge(Xtr_raw, ytr_f, Xva_raw, yva_f); cur_r2 = r2_0(yva_f, m0.predict(Xva_raw))
    F_tr = {c.key: c.eval(Ptr, prims).reshape(-1, 1) for c in gated}
    F_va = {c.key: c.eval(Pva[:, D], prims).reshape(-1, 1) for c in gated}
    remaining = list(gated)
    while remaining and len(final) < 8:
        best = None
        for c in remaining:
            cols_tr = np.hstack([Xtr_raw] + [F_tr[f.key] for f in final] + [F_tr[c.key]])
            cols_va = np.hstack([Xva_raw] + [F_va[f.key] for f in final] + [F_va[c.key]])
            m, a = fit_ridge(cols_tr, ytr_f, cols_va, yva_f); r2 = r2_0(yva_f, m.predict(cols_va))
            d = r2 - cur_r2; k_new = 1 + c.nodes / 4.0
            dbic = n_eff * np.log(max(1 - max(d, 0), 1e-9)) + k_new * np.log(n_eff)   # <0 accept (BIC on val, effective n)
            if best is None or dbic < best[0]: best = (dbic, c, r2, d)
        if best[0] >= 0: break
        final.append(best[1]); cur_r2 = best[2]; remaining.remove(best[1])
    log(f"[{time.time()-t0:.0f}s] final list (validation-selected): {[f.key for f in final]}")
    # freeze: hash of the final list + orientation, BEFORE held-out access
    lock = dict(final=[f.key for f in final], sgn=[f.sgn for f in final], mu=[f.mu for f in final], sd=[f.sd for f in final])
    lock["sha256"] = hashlib.sha256(json.dumps(lock, sort_keys=True).encode()).hexdigest()
    panel.access.append("LOCK")
    if on_lock: on_lock(lock)

    # ---- held-out (frozen); non-redundancy via correlation on TRAIN+VAL only
    res = dict(seed=seed, discovered=rows, lock=lock, provenance={k: sorted(v["why"]) for k, v in pool.items()},
               sym_all=[(c.formula, c.nodes, n_) for c, n_ in all_sym], stab_alpha=alpha, cmi_thr=sc["cmi_thr"])
    panel.access.append("test"); Pte, yte = panel.P[te], panel.y[te]; all_idx = list(range(len(panel.markets)))
    ho = []
    Fte = {f.key: f.eval(Pte, prims) for f in final}
    Fva_vec = {f.key: f.eval(Pva[:, D], prims).reshape(-1)[::20] for f in final}
    # partial IC vs raw primitives: residualise feature on raw primitives (frozen train coeffs) -> incremental
    Xraw_tr_full = Xtr_raw
    for f in final:
        ftr = F_tr[f.key] if f.key in F_tr else f.eval(Ptr, prims).reshape(-1, 1)
        g = np.linalg.lstsq(np.hstack([Xraw_tr_full, np.ones((len(ftr), 1))]), ftr.ravel(), rcond=None)[0]
        Xte_raw = np.nan_to_num(Pte).reshape(-1, len(prims)); T_, M_ = yte.shape
        resid = (Fte[f.key].reshape(-1) - np.hstack([Xte_raw, np.ones((len(Xte_raw), 1))]) @ g).reshape(T_, M_)
        r = ic_boot(Fte[f.key], yte, seed=seed); rr = ic_boot(resid, yte, seed=seed)
        ru = ic_boot(Fte[f.key][:, panel.unseen], yte[:, panel.unseen], seed=seed) if panel.unseen else None
        rd = ic_boot(Fte[f.key][:, D], yte[:, D], seed=seed)
        # heterogeneity across markets (Cochran Q on per-market ICs, se from n_eff)
        per = np.array(r["per_market"]); se_each = np.full(len(per), 1 / np.sqrt(yte.shape[0] / panel.neff_div))
        Qp = cochran_Q(per, se_each)
        # heterogeneity across time halves
        h = yte.shape[0] // 2; a1 = pooled_ic(Fte[f.key][:h], yte[:h])[0]; a2 = pooled_ic(Fte[f.key][h:], yte[h:])[0]
        row = next(x for x in rows if x["key"] == f.key)
        ho.append(dict(key=f.key, kind=f.kind, nodes=f.nodes, why=row["why"], ic_val=row["ic_val"], ic_test=r["ic"], p_test=r["p"],
                       sign_agree_all=float(np.mean(per > 0)), ic_test_disc=rd["ic"], ic_test_unseen=(ru["ic"] if ru else None),
                       partial_ic_vs_raw=rr["ic"], partial_p=rr["p"], Q_p=Qp, half1=float(a1), half2=float(a2), dec_val=decile_profile(f.eval(Pva[:, D], prims), Vd), dec_test=decile_profile(Fte[f.key], yte), formula=f.formula, per_market=r["per_market"], val_vec=[round(float(v), 4) for v in Fva_vec[f.key]]))
    # BH over the frozen final list
    if ho:
        okp = bh([h_["p_test"] for h_ in ho], PROTO["heldout_criteria"]["bh_q"])
        for h_, ok in zip(ho, okp): h_["bh_ok"] = bool(ok)
    hc = PROTO["heldout_criteria"]
    for h_ in ho:
        h_["stable"] = bool(h_["bh_ok"] and h_["ic_test"] > 0 and h_["ic_test"] >= hc["abs_pooled_ic_min"] and h_["ic_val"] > 0
                            and h_["sign_agree_all"] >= hc["min_market_sign_agreement"]
                            and (h_["ic_test_unseen"] is None or h_["ic_test_unseen"] > 0))
        h_["new_incremental"] = bool(h_["kind"] != "prim" and h_["partial_ic_vs_raw"] >= hc["new_composite_min_incremental_ic"] and h_["partial_p"] < 0.10)
        h_["invariant"] = bool(h_["stable"] and h_["Q_p"] >= hc["invariance_Q_p_min"] and h_["half1"] > 0 and h_["half2"] > 0)
    # non-redundancy among held-out-stable (correlation on validation, frozen order = selection order)
    kept = []
    Fva_all = {f.key: f.eval(Pva, prims).reshape(-1) for f in final}
    for h_ in ho:
        if h_["stable"] and all(abs(np.corrcoef(Fva_all[h_["key"]], Fva_all[k])[0, 1]) < hc["nonredundant_max_abs_corr"] for k in kept):
            h_["nonredundant"] = True; kept.append(h_["key"])
        else: h_["nonredundant"] = False
    res["heldout"] = ho

    # ---- models on held-out
    mods = {}
    Xte_raw = np.nan_to_num(Pte).reshape(-1, len(prims)); T_, M_ = yte.shape
    Xall_tr = np.nan_to_num(panel.P[tr][:, D]).reshape(-1, len(prims))
    m_raw, a_raw = fit_ridge(Xall_tr, ytr_f, Xva_raw, yva_f)
    pred_raw = m_raw.predict(Xte_raw).reshape(T_, M_)
    def with_feats(fs):
        cols_tr = np.hstack([Xtr_raw] + [f.eval(Ptr, prims).reshape(-1, 1) for f in fs])
        cols_va = np.hstack([Xva_raw] + [f.eval(Pva[:, D], prims).reshape(-1, 1) for f in fs])
        m, a = fit_ridge(cols_tr, ytr_f, cols_va, yva_f)
        Xt = np.hstack([Xte_raw] + [Fte[f.key].reshape(-1, 1) for f in fs]); return m.predict(Xt).reshape(T_, M_)
    def disc_only(fs):
        cols_tr = np.hstack([f.eval(Ptr, prims).reshape(-1, 1) for f in fs]); cols_va = np.hstack([f.eval(Pva[:, D], prims).reshape(-1, 1) for f in fs])
        m, a = fit_ridge(cols_tr, ytr_f, cols_va, yva_f); return m.predict(np.hstack([Fte[f.key].reshape(-1, 1) for f in fs])).reshape(T_, M_)
    perf = {"B1_raw_ridge": pred_raw}
    if do_baselines:
        for k, v in base.items():
            if k != "B1_raw_ridge": perf[k] = predict_panel(panel, v, "test")
    if final:
        perf["DISC_raw_plus_final"] = with_feats(final)
        perf["DISC_final_only"] = disc_only(final)
        st = [f for f, h_ in zip(final, ho) if h_["stable"] and h_["nonredundant"]]
        if st: perf["DISC_raw_plus_stable_nonredundant"] = with_feats(st)
    def summarize(pr):
        ic = pooled_ic(pr, yte)
        return dict(r2=float(r2_0(yte, pr)), r2_per_market=[float(r2_0(yte[:, m], pr[:, m])) for m in range(M_)], ic=float(ic[0]),
                    r2_disc_mk=float(r2_0(yte[:, D], pr[:, D])), r2_unseen_mk=(float(r2_0(yte[:, panel.unseen], pr[:, panel.unseen])) if panel.unseen else None))
    res["perf"] = {k: summarize(v) for k, v in perf.items()}
    res["baseline_meta"] = {k: {kk: vv for kk, vv in v.items() if kk in ("names", "alpha", "k")} for k, v in (base or {}).items()}
    res["complexity"] = {}
    for k in ("DISC_raw_plus_final", "DISC_raw_plus_stable_nonredundant"):
        if k in perf: res["complexity"][k + "_vs_B1"] = paired_block_delta(yte, pred_raw, perf[k], seed=seed)
    res["complexity"]["nodes_final"] = int(sum(f.nodes for f in final))
    res["counts"] = dict(discovered=len(discovered), passed_validation=len(gated), final=len(final),
                         heldout_stable=int(sum(h_["stable"] for h_ in ho)), nonredundant=int(sum(h_["nonredundant"] for h_ in ho)),
                         new_stable_nonredundant=int(sum(h_["nonredundant"] and h_["new_incremental"] for h_ in ho)),
                         invariant=int(sum(h_["invariant"] and h_["nonredundant"] for h_ in ho)),
                         sym_stable_clusters=len(stable_sym),
                         sym_stable_heldout=int(sum(1 for h_ in ho if h_["kind"] == "sym" and h_["stable"])))
    res["runtime_s"] = time.time() - t0
    log(f"[{time.time()-t0:.0f}s] counts {res['counts']}")
    return res
