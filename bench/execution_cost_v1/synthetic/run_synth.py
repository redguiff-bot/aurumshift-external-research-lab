"""Runs all synthetic experiments deterministically (fixed seeds). Writes results/*.json|csv.
python run_synth.py  (from bench/execution_cost_v1)"""
import sys, json, time, os, itertools
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "models"))
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
from dataclasses import replace
from scipy.optimize import least_squares
from synth import *
import models as M

RES = os.path.join(os.path.dirname(__file__), "..", "results")
os.makedirs(RES, exist_ok=True)
NT = 300
SIZES = [1e3, 1e4, 1e5, 1e6, 1e7]

SCEN = {
    "base":        Scenario(name="base"),
    "deep":        Scenario(name="deep", A=2.0e6, V_day=1.0e10),
    "hivol":       Scenario(name="hivol", sigma=2.7),
    "lovol":       Scenario(name="lovol", sigma=0.3),
    "shallow":     Scenario(name="shallow", A=3e4, spread=4.0, V_day=1.5e8),
    "withdraw":    Scenario(name="withdraw", shock_mult=0.15, shock_spread_mult=3.0),
    "trend":       Scenario(name="trend", drift=0.5, lat=3.0),
    "meanrev":     Scenario(name="meanrev", ou_kappa=0.15, lat=5.0),
    "gap":         Scenario(name="gap", jump_bps=15.0, lat=1.0),
    "wall":        Scenario(name="wall", wall_at=10.0, wall_thin=0.03),
    "fragmented":  Scenario(name="fragmented", n_venues=4),
    "coupled_hivol": Scenario(name="coupled_hivol", sigma=2.7, A=1.33e5, spread=3.0),   # vol up => depth thins, spread widens (liquidity-vol coupling)
    "coupled_lovol": Scenario(name="coupled_lovol", sigma=0.3, A=1.2e6, spread=0.5),
    "concave_book": Scenario(name="concave_book", beta=0.5, A=2.0e6),   # depth(x)~x^0.5 : matches the concavity seen in live top-of-book (beta 0.3-0.6)
}
TRAIN = ["base", "deep", "hivol", "lovol"]
TEST = ["shallow", "withdraw", "trend", "meanrev", "gap", "wall", "fragmented", "concave_book", "coupled_hivol", "coupled_lovol"]


def ctx_for(sc, N, qo, xo, regime):
    c = dict(N=N, sigma=sc.sigma, V_day=sc.V_day, lat=sc.lat, slices=1, horizon=0.0)
    if regime in ("L2", "L2_top20"):
        n = 400 if regime == "L2" else 80          # 100 bps vs 20 bps of depth visible
        c.update(q=qo[:n], x=xo[:n], spread=sc.spread, D1=float(qo[:4].sum()))
    elif regime == "L1":
        c.update(spread=sc.spread, D1=float(qo[:4].sum()))
    elif regime == "OHLCV":
        pass
    return c


def fit(fn, bounds, keys, data_items, extra=None):
    """least squares fit of scalar params of a cost model on mean(IS) over train items."""
    def resid(th):
        p = dict(zip(keys, th)); p.update(extra or {})
        out = []
        for (sc, N, r) in data_items:
            pr = np.mean([fn(ctx_for(sc, N, r["obs"][i][0], r["obs"][i][1], "L2"), p) for i in range(0, NT, 10)])
            out.append(pr - r["IS"].mean())
        return out
    sol = least_squares(resid, x0=[max(b[0], min(b[1], 1.0)) for b in bounds], bounds=([b[0] for b in bounds], [b[1] for b in bounds]))
    return dict(zip(keys, sol.x))


def exp_single_orders(seed_off=0, write=True):
    t0 = time.time()
    truth = {}
    for name in TRAIN + TEST:
        for N in SIZES:
            seed = 1000 + seed_off + list(SCEN).index(name) * 10 + int(np.log10(N))
            truth[(name, N)] = simulate_market(SCEN[name], N, NT, seed=seed)
    train_items = [(SCEN[n], N, truth[(n, N)]) for n in TRAIN for N in SIZES]
    hs_train = float(np.mean([SCEN[n].spread / 2 for n in TRAIN]))
    P = {}
    P["fixed_bps"] = dict(c=float(np.mean([r["IS"].mean() for _, _, r in train_items])))
    P["fixed_5bps_default"] = dict(c=5.0)
    P["spread_prop"] = fit(M.m_spread_prop, [(0, 50)], ["k"], train_items)
    P["vol_scaled"] = fit(M.m_vol_scaled, [(0, 50)], ["a"], train_items)
    P["size_depth"] = fit(M.m_size_depth, [(0, 50)], ["b"], train_items)
    P["sqrt"] = fit(M.m_sqrt, [(0, 10)], ["Y"], train_items)
    P["sqrt_ohlcv"] = dict(Y=P["sqrt"]["Y"], hs_fallback=hs_train)
    P["sqrt"]["hs_fallback"] = hs_train
    P["walk"] = {}; P["walk_fallback"] = dict(P["sqrt"]); P["mid_fill"] = {}; P["half_spread"] = {}
    fns = {
        "E1_mid_fill": (M.m_mid_fill, "mid_fill", "OHLCV"),
        "fixed_bps_calibrated": (M.m_fixed, "fixed_bps", "OHLCV"),
        "fixed_5bps_default": (M.m_fixed, "fixed_5bps_default", "OHLCV"),
        "half_spread_only(E3)": (M.m_half_spread, "half_spread", "L1"),
        "spread_prop": (M.m_spread_prop, "spread_prop", "L1"),
        "vol_scaled": (M.m_vol_scaled, "vol_scaled", "L1"),
        "size_depth(L1+D1bp)": (M.m_size_depth, "size_depth", "L1"),
        "sqrt_law(L1 spread)": (M.m_sqrt, "sqrt", "L1"),
        "sqrt_law(OHLCV-only)": (M.m_sqrt_no_spread, "sqrt_ohlcv", "OHLCV"),
        "book_walk_L2(100bps)": (M.m_walk, "walk", "L2"),
        "book_walk_L2_top20(20bps)": (M.m_walk, "walk", "L2_top20"),
        "book_walk_L2_top20+sqrt_fallback": (M.m_walk_fallback, "walk_fallback", "L2_top20"),
    }
    rows = []
    timing = {}
    for label, (fn, pk, regime) in fns.items():
        tt = time.time(); ncalls = 0
        for name in TRAIN + TEST:
            for N in SIZES:
                r = truth[(name, N)]; sc = SCEN[name]
                preds = np.array([fn(ctx_for(sc, N, r["obs"][i][0], r["obs"][i][1], regime), P[pk]) for i in range(NT)])
                ncalls += NT
                err = preds - r["IS"]
                rows.append(dict(model=label, regime=regime, scenario=name, split="train" if name in TRAIN else "test",
                                 N=N, truth=float(r["IS"].mean()), truth_ex_drift=float((r["IS"] - r["drift"]).mean()),
                                 pred=float(np.nanmean(preds)), bias=float(np.nanmean(err)),
                                 sd_err=float(np.nanstd(err)), rmse=float(np.sqrt(np.nanmean(err ** 2))),
                                 filled=float(r["filled"].mean()), nan_frac=float(np.mean(np.isnan(preds)))))
        timing[label] = (time.time() - tt) / ncalls * 1e6
    if not write:
        return rows, P, truth
    json.dump(dict(params=P, timing_us_per_pred=timing, sizes=SIZES, n_trials=NT), open(f"{RES}/single_params_timing.json", "w"), indent=1, default=float)
    import csv
    with open(f"{RES}/single_orders.csv", "w") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    # truth decomposition table
    dec = []
    for (name, N), r in truth.items():
        dec.append(dict(scenario=name, N=N, IS=r["IS"].mean(), drift=r["drift"].mean(), half_spread=r["half_spread"].mean(),
                        walk=r["walk"].mean(), impact=r["impact"].mean(), filled=r["filled"].mean(),
                        identity_maxabs=float(np.abs(r["IS"] - (r["drift"] + r["half_spread"] + r["walk"] + r["impact"])).max()),
                        IS_se=float(r["IS"].std() / np.sqrt(NT))))
    with open(f"{RES}/truth_decomposition.csv", "w") as f:
        w = csv.DictWriter(f, fieldnames=list(dec[0])); w.writeheader(); w.writerows(dec)
    print("single orders done", time.time() - t0)
    return rows, P, truth


def exp_sliced():
    """Parent order executed as 1/5/20 slices over 600s. Models: independent walks, AC, propagator (true shape / wrong shape), sqrt."""
    cfgs = {"sl_base": Scenario(name="sl_base", A=1.5e5, lam=0.4, V_day=7.5e8),
            "sl_highimpact": Scenario(name="sl_highimpact", A=1.5e5, lam=1.2, tau0=100.0, gamma=0.3, V_day=7.5e8),
            "sl_thin": Scenario(name="sl_thin", A=4e4, lam=0.4, spread=3.0, V_day=2e8),
            "sl_lowimpact": Scenario(name="sl_lowimpact", A=1.5e5, lam=0.1, phi=0.7, V_day=7.5e8)}
    Ns = [2e5, 1e6, 5e6]; slices = [1, 5, 20]; T = 600.0
    truth = {}
    for k, sc in cfgs.items():
        for N in Ns:
            for s in slices:
                truth[(k, N, s)] = simulate_market(sc, N, 200, seed=7 + int(np.log10(N)) * 3 + s, slices=s, horizon=T if s > 1 else 0.0)
    # calibrate on sl_base only
    def ctx(sc, N, s, r, i):
        return dict(N=N, sigma=sc.sigma, V_day=sc.V_day, lat=sc.lat, slices=s, horizon=T if s > 1 else 0.0,
                    q=r["obs"][i][0][:400], x=r["obs"][i][1][:400], spread=sc.spread, D1=float(r["obs"][i][0][:4].sum()))
    base_items = [(cfgs["sl_base"], N, s, truth[("sl_base", N, s)]) for N in Ns for s in slices]
    def resid_prop(th):
        p = dict(lam=th[0], phi=0.4, tau0=30.0, gamma=0.5)   # shape fixed at truth of sl_base, only lambda fitted
        return [np.mean([M.m_sliced_propagator(ctx(sc, N, s, r, i), p) for i in range(0, 200, 20)]) - (r["IS"] - r["drift"]).mean() for sc, N, s, r in base_items]
    lam_hat = float(least_squares(resid_prop, [0.2], bounds=([0.0], [10.0])).x[0])
    def resid_ac(th):
        p = dict(g=th[0], eta=th[1])
        return [np.mean([M.m_sliced_ac(ctx(sc, N, s, r, i), p) for i in range(0, 200, 20)]) - (r["IS"] - r["drift"]).mean() for sc, N, s, r in base_items]
    ac = least_squares(resid_ac, [0.1, 0.1], bounds=([0, 0], [50, 50])).x
    def resid_sq(th):
        p = dict(Y=th[0], hs_fallback=0.5)
        return [np.mean([M.m_sliced_sqrt(ctx(sc, N, s, r, i), p) for i in range(0, 200, 20)]) - (r["IS"] - r["drift"]).mean() for sc, N, s, r in base_items]
    Y = float(least_squares(resid_sq, [0.5], bounds=([0], [10])).x[0])
    params = dict(prop_true_shape=dict(lam=lam_hat, phi=0.4, tau0=30.0, gamma=0.5),
                  prop_wrong_shape=dict(lam=lam_hat, phi=1.0, tau0=30.0, gamma=0.5),   # permanent-only kernel = common simplification
                  ac=dict(g=float(ac[0]), eta=float(ac[1])), sqrt=dict(Y=Y, hs_fallback=0.5), none={})
    models = {"independent_walks(no memory)": (M.m_sliced_independent, "none"),
              "propagator(true shape, lambda fitted)": (M.m_sliced_propagator, "prop_true_shape"),
              "propagator(permanent-only kernel)": (M.m_sliced_propagator, "prop_wrong_shape"),
              "almgren_chriss_linear": (M.m_sliced_ac, "ac"),
              "sqrt_total(no schedule info)": (M.m_sliced_sqrt, "sqrt")}
    rows = []
    for k, sc in cfgs.items():
        for N in Ns:
            for s in slices:
                r = truth[(k, N, s)]
                for lab, (fn, pk) in models.items():
                    preds = np.array([fn(ctx(sc, N, s, r, i), params[pk]) for i in range(0, 200, 4)])
                    rows.append(dict(scenario=k, split="train" if k == "sl_base" else "test", N=N, slices=s, model=lab,
                                     truth=float(r["IS"].mean()), truth_ex_drift=float((r["IS"] - r["drift"]).mean()),
                                     truth_se=float(r["IS"].std() / np.sqrt(200)), pred=float(preds.mean()),
                                     bias=float(preds.mean() - (r["IS"] - r["drift"]).mean()),
                                     truth_walk=float(r["walk"].mean()), truth_impact=float(r["impact"].mean())))
    # schedule ranking: does the model order {1,5,20 slices} like the truth (using ex-drift truth, drift is zero-mean noise)?
    from scipy.stats import kendalltau
    rk = []
    for k in cfgs:
        for N in Ns:
            tr = [truth[(k, N, s)]["IS"].mean() - truth[(k, N, s)]["drift"].mean() for s in slices]
            for lab, (fn, pk) in models.items():
                pr = [np.mean([fn(ctx(cfgs[k], N, s, truth[(k, N, s)], i), params[pk]) for i in range(0, 200, 20)]) for s in slices]
                best_t = int(np.argmin(tr)); best_p = int(np.argmin(pr))
                rk.append(dict(scenario=k, N=N, model=lab, truth_best_slices=slices[best_t], model_best_slices=slices[best_p],
                               truth_costs=[round(x, 3) for x in tr], model_costs=[round(x, 3) for x in pr],
                               regret_bps=float(tr[best_p] - tr[best_t])))
    json.dump(dict(params=params, rows=rows, ranking=rk), open(f"{RES}/sliced.json", "w"), indent=1, default=float)
    print("sliced done")
    return rows, rk, params


def exp_competing():
    """E14/E15: k same-direction orders hitting one book simultaneously (E14) or in sequence with partial recovery (E15)."""
    sc = Scenario(A=1.0e5, rho=0.05)
    rows = []
    for k in [1, 2, 5, 10]:
        for N in [1e5, 5e5]:
            # simultaneous: total k*N walks the book once. order i (random priority) gets average of its own segment.
            tot = simulate_market(sc, N * k, 200, seed=11)
            solo = simulate_market(sc, N, 200, seed=11)
            rows.append(dict(kind="E14_simultaneous", k=k, N=N, truth_avg_cost_per_order=float((tot["half_spread"] + tot["walk"]).mean()),
                             naive_independent=float((solo["half_spread"] + solo["walk"]).mean())))
    # E15 sequential repeat with recovery rho: k children of N with gap dt
    for dt in [1.0, 10.0, 60.0, 600.0]:
        r = simulate_market(sc, 5e5 * 5, 200, seed=12, slices=5, horizon=dt * 5)
        solo = simulate_market(sc, 5e5, 200, seed=12)
        rows.append(dict(kind="E15_sequential_recovery", gap_s=dt, k=5, N=5e5,
                         truth_avg_cost_per_order=float((r["half_spread"] + r["walk"] + r["impact"]).mean()),
                         naive_independent=float((solo["half_spread"] + solo["walk"]).mean())))
    json.dump(rows, open(f"{RES}/competing.json", "w"), indent=1, default=float)
    print("competing done"); return rows


def exp_latency():
    """Sweep latency, staleness, fragmentation, participation for a mid-size order."""
    rows = []
    for lat in [0.05, 0.25, 1, 5, 20]:
        for label, extra in [("rw", {}), ("trend", dict(drift=0.03)), ("meanrev", dict(ou_kappa=0.15)), ("gap", dict(jump_bps=15.0))]:
            sc = replace(SCEN["base"], lat=lat, **({**extra, "drift": 0.5} if extra.get("drift") else extra))
            r = simulate_market(sc, 1e5, 400, seed=21)
            rows.append(dict(regime=label, lat=lat, mean_drift=float(r["drift"].mean()), sd_drift=float(r["drift"].std()),
                             se=float(r["drift"].std() / 20), sqrt_lat_sigma=float(sc.sigma * np.sqrt(lat)),
                             half_spread=sc.spread / 2, ratio_sd_to_half_spread=float(r["drift"].std() / (sc.spread / 2))))
    for nv in [1, 2, 4, 8]:
        sc = replace(SCEN["base"], n_venues=nv, A=2e5)
        r = simulate_market(sc, 1e6, 300, seed=22)
        obs_cost = np.mean([M.m_walk(dict(N=1e6, q=o[0][:400], x=o[1][:400], spread=sc.spread), {}) for o in r["obs"]])
        rows.append(dict(regime="fragmentation", n_venues=nv, truth_routed_all=float((r["half_spread"] + r["walk"]).mean()),
                         single_venue_walk_estimate=float(obs_cost)))
    json.dump(rows, open(f"{RES}/latency_fragmentation.json", "w"), indent=1, default=float)
    print("latency done"); return rows


def exp_spread_estimators():
    rows = []
    for spread in [0.2, 1.0, 5.0, 20.0]:
        for sigma in [0.3, 0.9, 2.7]:
            for bar in [60, 300]:
                for tick in [0.0, 1.0]:
                    nb = 250 if bar == 60 else 60
                    o = simulate_ohlc(spread, sigma, nb, bar, seed=int(spread * 100 + sigma * 10 + bar), tick_bps=tick)
                    base = 1e5   # price level so log-returns ~ bps/1e4
                    px = lambda a: base * (1 + a / 1e4)
                    H, L, C = px(o["H"]), px(o["L"]), px(o["C"])
                    rl = M.roll(C) / base * 1e4
                    cs, cs_neg = M.corwin_schultz(H, L); cs = cs * 1e4
                    ar = M.abdi_ranaldo(C, H, L) * 1e4
                    hl = M.hl_range_proxy(H, L) * 1e4
                    rows.append(dict(spread=spread, sigma=sigma, bar_s=bar, tick=tick, eff_spread_truth=o["eff_spread"], roll=rl,
                                     corwin_schultz=cs, cs_negative_frac=cs_neg, abdi_ranaldo=ar, hl_range_proxy=hl))
    json.dump(rows, open(f"{RES}/spread_estimators_synth.json", "w"), indent=1, default=float)
    print("spread est done"); return rows


def exp_limit_fills():
    grid = []
    for qf, V, drift, info, sig, fees, spr in itertools.product([0.0, 0.5, 1.0], [5e2, 2e3, 2e4], [0.0, 0.1, 0.4], [0.0, 0.5], [0.3, 0.9],
                                                          [(2.0, 5.0), (8.0, 10.0)], [1.0, 5.0]):
        sc = Scenario(sigma=sig, drift=drift, spread=spr, fee_maker_bps=fees[0], fee_taker_bps=fees[1])
        l = simulate_limit(sc, 800, seed=31, queue_frac=qf, V=V, info=info, top_depth=2e5, H=60, M=30, tick=0.5)
        f = l["ff"] > 0
        grid.append(dict(queue_frac=qf, V=V, drift=drift, info=info, sigma=sig, fee_m=fees[0], fee_t=fees[1], spread=spr,
                         ff=float(l["ff"].mean()),
                         p_any_fill=float(f.mean()), adverse=float(np.nanmean(l["adverse"][f])) if f.any() else np.nan,
                         IS_maker=float(l["IS"].mean()), IS_taker=float(l["taker"][0]),
                         chase=float((l["chase"] + sc.fee_taker_bps).mean()), half=sc.spread / 2, bid0=float(l["bid0"])))
    # models of fill fraction
    import models as M2
    P = dict(p=float(np.mean([g["ff"] for g in grid])), cv=0.5)
    rows = []
    for g in grid:
        ctx = dict(H=60, tick=0.5, sigma=g["sigma"], queue_ahead=g["queue_frac"] * 2e5 + 1e-9, order_n=2e4, sell_rate=g["V"])
        pred = {"always_fill(E1-maker)": M2.f_always(ctx, P), "const_p": M2.f_const(ctx, P),
                "price_through(sigma,tick)": M2.f_price_through(ctx, P), "queue_volume(L1 size+trade rate)": M2.f_queue_volume(ctx, P),
                "hybrid(through OR queue)": M2.f_hybrid(ctx, P)}
        for k, v in pred.items():
            rows.append(dict(model=k, **{kk: g[kk] for kk in ["queue_frac", "V", "drift", "info", "sigma"]}, truth_ff=g["ff"], pred=float(v), err=float(v - g["ff"])))
    # maker/taker decision: model's expected maker IS = P*(bid0+fee_m) + (1-P)*(taker_IS + drift_hat*H)
    KEYS = ["queue_frac", "V", "drift", "info", "sigma", "fee_m", "spread"]
    summary = {}
    for mod in ["always_fill(E1-maker)", "const_p", "price_through(sigma,tick)", "queue_volume(L1 size+trade rate)", "hybrid(through OR queue)"]:
        for alpha_aware in (False, True):
            regrets = []; correct = 0
            for g in grid:
                ctx = dict(H=60, tick=0.5, sigma=g["sigma"], queue_ahead=g["queue_frac"] * 2e5 + 1e-9, order_n=2e4, sell_rate=g["V"])
                pr = {"always_fill(E1-maker)": M2.f_always, "const_p": M2.f_const, "price_through(sigma,tick)": M2.f_price_through,
                      "queue_volume(L1 size+trade rate)": M2.f_queue_volume, "hybrid(through OR queue)": M2.f_hybrid}[mod](ctx, P)
                dh = g["drift"] * 60 if alpha_aware else 0.0
                maker_hat = pr * (g["bid0"] + g["fee_m"]) + (1 - pr) * (g["IS_taker"] + dh)
                dec_model = maker_hat < g["IS_taker"]
                dec_truth = g["IS_maker"] < g["IS_taker"]
                correct += int(dec_model == dec_truth)
                chosen = g["IS_maker"] if dec_model else g["IS_taker"]
                regrets.append(chosen - min(g["IS_maker"], g["IS_taker"]))
            summary[mod + ("|alpha_aware" if alpha_aware else "|blind")] = dict(decision_accuracy=correct / len(grid), mean_regret_bps=float(np.mean(regrets)))
    truth_share_maker = float(np.mean([g["IS_maker"] < g["IS_taker"] for g in grid]))
    json.dump(dict(grid=grid, fill_rows=rows, always_taker_regret=float(np.mean([max(0, g["IS_taker"] - g["IS_maker"]) for g in grid])), always_maker_regret=float(np.mean([max(0, g["IS_maker"] - g["IS_taker"]) for g in grid])), decision=summary, const_p=P["p"], truth_share_maker_better=truth_share_maker),
              open(f"{RES}/limit_fills.json", "w"), indent=1, default=float)
    print("limit fills done"); return summary


def exp_fullfill():
    """How often does 'full fill at touch' materially distort? Sweep order size vs total book depth (thin books)."""
    rows = []
    for A in [3e2, 1e3, 3e3, 1e4, 1e5]:
        for N in [1e4, 1e5, 1e6, 1e7]:
            sc = replace(SCEN["base"], A=A)
            r = simulate_market(sc, N, 100, seed=61)
            Dtot = A * 600.0 ** sc.beta
            rows.append(dict(A=A, N=N, depth_600bps_usd=Dtot, N_over_depth=N / Dtot, filled=float(r["filled"].mean()),
                             naive_full_fill_cost=sc.spread / 2, truth_cost_filled_part=float((r["half_spread"] + r["walk"]).mean()),
                             unfilled_notional=float((1 - r["filled"].mean()) * N)))
    json.dump(rows, open(f"{RES}/fullfill.json", "w"), indent=1)
    print("fullfill done"); return rows


def exp_seed_stability():
    import pandas as pd
    out = {}
    for off in (0, 100, 200, 300, 400):
        rows, P, _ = exp_single_orders(seed_off=off, write=False)
        d = pd.DataFrame(rows)
        for m, g in d.groupby("model"):
            out.setdefault(m, []).append(dict(seed_off=off, test_abs_bias=float(g[g.split == "test"].bias.abs().mean()), train_abs_bias=float(g[g.split == "train"].bias.abs().mean()),
                                              Y_or_k=float(next(iter({"sqrt_law(L1 spread)": P["sqrt"], "spread_prop": P["spread_prop"], "vol_scaled": P["vol_scaled"], "size_depth(L1+D1bp)": P["size_depth"]}.get(m, {"x": np.nan}).values())))))
    json.dump(out, open(f"{RES}/single_seed_stability.json", "w"), indent=1)
    print("seed stability done")


if __name__ == "__main__":
    exp_fullfill(); exp_seed_stability(); exp_single_orders(); exp_sliced(); exp_competing(); exp_latency(); exp_spread_estimators(); exp_limit_fills()
