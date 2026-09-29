"""Leakage harness: predictions served at time t must not depend on labels that are not yet mature (s > t_abs-H).
Run: python3 tests/test_no_lookahead.py   (from bench/uncertainty_v1)"""
import sys, numpy as np; sys.path.insert(0, "py")
import online as O, conformal as CF, calibrators as C
from worlds import *; from models import *


def test_online_calibration_invariant_to_future_labels():
    Wd = make_world(1, "none", 1.0, n_hold=1200); s = Wd["sl"]; X, y = Wd["x"], Wd["y"]
    base = Base(seed=1, n_ens=1).fit(X[s["train"]], y[s["train"]])
    Lall = base.logits(np.vstack([X[s["val"]], X[s["hold"]]])); yall = np.r_[y[s["val"]], y[s["hold"]]]; off = N_VAL
    for cal in ("beta", "temperature", "isotonic"):
        for mode in ("window", "expanding", "decay"):
            P0 = O.online_probs(Lall, yall, off, cal, mode=mode)
            t_cut = 600; y2 = yall.copy(); y2[off + t_cut - O.H + 1:] = (y2[off + t_cut - O.H + 1:] + 1) % 3   # corrupt every label not mature at t_cut
            P1 = O.online_probs(Lall, y2, off, cal, mode=mode)
            assert np.allclose(P0[:t_cut], P1[:t_cut]), (cal, mode)          # served before t_cut => identical
            assert not np.allclose(P0[t_cut + 200:], P1[t_cut + 200:]), (cal, mode)   # sanity: harness is sensitive
            Pl0 = O.online_probs(Lall, yall, off, cal, mode="window", delay=1, peek=O.R)
            Pl1 = O.online_probs(Lall, y2, off, cal, mode="window", delay=1, peek=O.R)
            assert not np.allclose(Pl0[:t_cut], Pl1[:t_cut])                 # leaky variant IS detected as leaking


def test_conformal_invariant_to_future_scores():
    rng = np.random.default_rng(0); sc = rng.random(2000); off = 500; cal = rng.random(300)
    for m in ("split", "rolling", "weighted", "aci_split", "aci_rolling"):
        q0, _ = CF.stream_scores(sc, off, m, 0.1, cal_scores=cal)
        s2 = sc.copy(); s2[off + 800 - CF.H + 1:] = 99
        q1, _ = CF.stream_scores(s2, off, m, 0.1, cal_scores=cal)
        assert np.allclose(q0[:800], q1[:800]), m


def test_split_conformal_iid_coverage():
    rng = np.random.default_rng(0); cov = []
    for _ in range(300):
        c = np.abs(rng.standard_normal(200)); t = np.abs(rng.standard_normal(200)); cov.append((t <= CF.qhat(c, 0.9)).mean())
    assert abs(np.mean(cov) - 0.9) < 0.01


def test_top_label_preserves_argmax():
    rng = np.random.default_rng(0); L = rng.standard_normal((500, 3)) * 3; y = rng.integers(0, 3, 500)
    for cn in ("platt", "beta", "isotonic", "bayes_bin"):
        f = C.fit_apply(cn, L, y); P = f(L)
        assert (P.argmax(1) == L.argmax(1)).all() and np.allclose(P.sum(1), 1), cn


if __name__ == "__main__":
    for k, f in list(globals().items()):
        if k.startswith("test_"): f(); print("PASS", k)
