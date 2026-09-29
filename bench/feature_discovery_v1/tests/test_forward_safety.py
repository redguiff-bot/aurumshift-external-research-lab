import os, sys
import numpy as np, pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from fd import data, features, expr as E, pipeline as P


def _df():
    return data.load("BTCUSDT").iloc[:6000]


def test_prefix_invariance():
    """Primitives at row t computed on data[:t+1] must equal those computed on the full series."""
    d = _df(); full = features.build(d)
    for k in (2500, 4000, 5500):
        part = features.build(d.iloc[:k + 1])
        a, b = full.loc[part.index[-1], features.NAMES].values, part.iloc[-1][features.NAMES].values
        assert np.allclose(a, b, atol=1e-9), (k, np.abs(a - b).max())


def test_future_perturbation():
    d = _df(); t = 4000
    d2 = d.astype(float).copy(); d2.iloc[t + 1:, :] = d2.iloc[t + 1:, :].values[::-1] * 1.7   # scramble the future
    a = features.build(d).iloc[t - features.WARMUP][features.NAMES].values
    b = features.build(d2).iloc[t - features.WARMUP][features.NAMES].values
    assert np.allclose(a, b, atol=1e-9)


def test_target_uses_future_only_as_label():
    d = _df(); f = features.build(d)
    # features must not equal/contain target information: correlation of each feature with y_ret is small in-sample
    c = f[features.NAMES].corrwith(f["y_ret"]).abs().max()
    assert c < 0.1


def test_expr_roundtrip():
    cols = {"a": np.array([1., -2., 3.]), "b": np.array([0.5, 0.0, -1.])}
    assert np.allclose(E.evaluate("mul(a, sgn(b))", cols), [1., 0., -3.])
    assert np.allclose(E.evaluate("div(a, b)", cols), [2., 1., -3.])


def test_split_ordering():
    from fd import panel
    assert panel.T_TRAIN_END < panel.T_VAL_START < panel.T_VAL_END < panel.T_HO_START
    assert (panel.T_VAL_START - panel.T_TRAIN_END).days >= 7 and (panel.T_HO_START - panel.T_VAL_END).days >= 7
