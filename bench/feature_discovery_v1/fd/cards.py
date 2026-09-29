"""Interpretability card for a retained expression (auto-generated; failure modes are rule-based, not exhaustive)."""
import numpy as np
from . import expr as E, features
from .metrics import spearman

VOLUME_LIKE = {"lvol_1", "lvol_24", "lnt_1", "lnt_24", "lsz_1", "tbr_1", "tbr_24", "lami_24"}
CAL = {"hod_sin", "hod_cos", "wknd"}


def _val(c, X, names, override=None):
    cols = {n: X[:, i].copy() for i, n in enumerate(names)}
    if override:
        for k, v in override.items():
            cols[k] = v
    return c["sign"] * E.evaluate(c["expr"], cols)


def card(c, tr, va, names, target):
    t = E.parse(c["expr"]); vs = sorted(E.variables(t))
    Xv = np.vstack([va[m][0] for m in va]); yv = np.concatenate([va[m][1] for m in va])
    Xt = np.vstack([tr[m][0] for m in tr])
    rng = np.random.default_rng(0); ix = rng.choice(len(Xt), min(5000, len(Xt)), replace=False)
    base_ic = spearman(_val(c, Xv, names), yv)
    mono, abl = {}, {}
    for v in vs:
        j = names.index(v)
        lo = _val(c, Xt[ix], names); hi = _val(c, Xt[ix], names, {v: Xt[ix, j] + 0.25})
        d = hi - lo; nz = d[np.abs(d) > 1e-12]
        frac = float((nz > 0).mean()) if len(nz) else 0.5
        mono[v] = "increasing" if frac >= 0.95 else "decreasing" if frac <= 0.05 else f"non-monotone/interaction-dependent ({frac:.0%} of rows increase)"
        abl[v] = float(base_ic - spearman(_val(c, Xv, names, {v: np.zeros(len(Xv))}), yv))
    lookback = max(features.META[v]["lookback"] for v in vs)
    fields = sorted({f for v in vs for f in features.META[v]["fields"].split(",")})
    fm = []
    if "div(" in c["expr"]:
        fm.append("protected division: returns 1 when |denominator|<0.001, creating a discontinuity near zero denominators")
    if any(v in VOLUME_LIKE for v in vs):
        fm.append("uses volume/trade-count/taker fields: depends on venue microstructure, wash-trading, fee-tier or listing changes and on exchange field availability (taker fields exist only on some venues)")
    if any(v in CAL for v in vs):
        fm.append("uses calendar features: fragile to changes in market-hours structure / DST-free UTC assumption")
    if any(v.startswith("lrv") or v.startswith("lpk") or v.startswith("lrng") for v in vs):
        fm.append("volatility inputs are rolling-standardised over 720 bars (~30 d): lags behind abrupt volatility regime shifts")
    fm.append("inputs clipped at +-5 sd: saturates in extreme moves (crashes/squeezes), where the relation is unverified")
    fm.append("relationship estimated on 2021-2024 crypto spot only; regime change (e.g. market-structure or fee change) can invalidate it")
    fm.append("data gaps (exchange maintenance) make 'N bars' lookbacks span more than N hours")
    hitch = [v for v, d in abl.items() if abs(d) < 0.002]
    tgt_unit = ("forward 4h log-return divided by (168h hourly vol x sqrt 4): dimensionless, in units of forward volatility"
                if target == "y_ret" else "log(forward 24h realised vol / trailing 24h realised vol): dimensionless log-ratio")
    return dict(id=c["id"], formula=E.to_infix(t), formula_prefix=c["expr"], sign=c["sign"], nodes=c["nodes"], constants=c["consts"],
                variables={v: dict(formula=features.META[v]["formula"], raw_unit=features.META[v]["unit"]) for v in vs},
                units=dict(inputs="dimensionless rolling z-scores (720-bar window, clipped +-5) of the listed primitives (calendar features unscaled)",
                           output="dimensionless, standardised by train mean/sd; monotone rank-signal, not a calibrated forecast",
                           target=tgt_unit),
                input_requirements=dict(fields=fields, max_primitive_lookback_bars=int(lookback), standardisation_window_bars=720,
                                        min_history_bars=int(lookback + 720), bar="1h closed bars, PIT at bar close"),
                expected_monotonicity={v: mono[v] for v in vs}, variable_ablation_delta_ic_val=abl,
                possible_hitchhikers=hitch, failure_modes=fm,
                forward_safety=dict(uses_only_bars_leq_t=True, verified_by="tests/test_forward_safety.py (prefix-invariance + future-scramble)",
                                    label_horizon_bars=(4 if target == "y_ret" else 24),
                                    note="any downstream CV must embargo >= label horizon between train and test rows"))
