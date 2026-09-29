import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import numpy as np, pandas as pd
import pipeline as pl
from panels import synth_panel, null_panel
from features import build, primitives_raw, H

def test_features_are_causal():
    """Recompute primitives on a truncated series: rows up to the cut must be identical (no lookahead)."""
    from data import load
    df = load("BTCUSDT").iloc[:3000]; cut = 2500
    a = primitives_raw(df); b = primitives_raw(df.iloc[:cut])
    pd.testing.assert_frame_equal(a.iloc[:cut].reset_index(drop=True), b.reset_index(drop=True), check_exact=False, rtol=1e-9)
    ba, bb = build(df), build(df.iloc[:cut])
    m = min(len(bb), len(ba)); common = ba._t.isin(bb._t)
    feats = [c for c in ba.columns if c not in ("y", "fwd_raw", "_t")]
    x1 = ba[common][feats].values[: len(bb) - H - 5]; x2 = bb[bb._t.isin(ba._t)][feats].values[: len(bb) - H - 5]
    np.testing.assert_allclose(x1, x2, rtol=1e-7, atol=1e-9)   # z-scores use only past windows

def test_target_not_in_primitives():
    from data import load
    X = build(load("BTCUSDT").iloc[:3000])
    from features import PRIMS
    assert "y" not in PRIMS and "fwd_raw" not in PRIMS
    assert all(k in X.columns for k in PRIMS)

def test_heldout_untouched_before_lock():
    pan, _ = synth_panel(3, T=4000, beta=0.08)
    locked = {}
    r = pl.run(pan, 3, sym_seeds=2, sym_pars=[0.01], sym_pop=80, sym_gens=3, log=lambda *a: None, on_lock=lambda l: locked.update(l))
    ev = pan.access
    assert "LOCK" in ev and locked["sha256"]
    first_test = ev.index("test"); assert ev.index("LOCK") < first_test, ev
    assert "test" not in ev[: ev.index("LOCK")]

def test_splits_are_disjoint_and_ordered():
    pan, _ = synth_panel(4, T=3000)
    s = pan.sl; assert s["train"].stop < s["val"].start < s["val"].stop < s["test"].start
    assert s["val"].start - s["train"].stop >= 24

def test_null_panel_breaks_link_keeps_marginal():
    pan, _ = synth_panel(5, T=3000, beta=0.2); n = null_panel(pan, 1)
    assert np.allclose(np.sort(pan.y[:, 0]), np.sort(n.y[:, 0]))
    c = pl.pooled_ic(pan.P[..., 0], pan.y)[0]; c0 = pl.pooled_ic(n.P[..., 0], n.y)[0]
    assert abs(c) > 3 * abs(c0)

def test_bh_and_orientation_frozen():
    ok = pl.bh([0.001, 0.02, 0.5, 0.9], 0.10); assert ok.tolist() == [True, True, False, False]
    pan, _ = synth_panel(6, T=2000)
    c = pl.Cand("prim", ("f0",), 1, "f0"); c.fit_std(pan.P[pan.sl["train"]][:, pan.disc], pan.prims, pan.y[pan.sl["train"]][:, pan.disc])
    s0 = c.sgn; c.eval(pan.P[pan.sl["test"]], pan.prims); assert c.sgn == s0
