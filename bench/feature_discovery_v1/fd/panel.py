"""Real-data panels with strict time splits (per-market, common grid).

train : 2021-01-01+warmup .. 2023-06-30    validation: 2023-07-08 .. 2024-12-31 (7d embargo after train)
heldout: 2025-01-08 .. 2026-08-31 (7d embargo after validation). Unseen markets contribute ONLY held-out rows.
"""
import numpy as np, pandas as pd
from . import data, features

T_TRAIN_END = pd.Timestamp("2023-07-01", tz="UTC")
T_VAL_START = pd.Timestamp("2023-07-08", tz="UTC")
T_VAL_END = pd.Timestamp("2025-01-01", tz="UTC")
T_HO_START = pd.Timestamp("2025-01-08", tz="UTC")


def _frames(markets):
    return {m: features.build(data.load(m)) for m in markets}


def panels(target, split, markets=None):
    """split in {'train','val','heldout'}. heldout access is gated by the caller (heldout script only)."""
    assert split in ("train", "val", "heldout") and target in ("y_ret", "y_vol")
    ms = markets or (data.DISCOVERY_MARKETS + (data.UNSEEN_MARKETS if split == "heldout" else []))
    fr = _frames(ms)
    sl = {"train": (None, T_TRAIN_END), "val": (T_VAL_START, T_VAL_END), "heldout": (T_HO_START, None)}[split]
    idx = None
    out = {}
    for m, f in fr.items():
        f = f.dropna(subset=[target])
        if sl[0] is not None:
            f = f[f.index >= sl[0]]
        if sl[1] is not None:
            f = f[f.index < sl[1]]
        out[m] = f
    common = sorted(set.intersection(*[set(f.index) for f in out.values()]))
    return {m: (out[m].loc[common, features.NAMES].values.astype(float), out[m].loc[common, target].values.astype(float))
            for m in ms}, pd.DatetimeIndex(common)
