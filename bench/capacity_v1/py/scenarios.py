"""Scenario families S1..S12 (+ held-out-only compositions H1..H3) and split-specific variants.

Splits use DISJOINT variant-parameter draws and DISJOINT seed ranges:
    TUNING     seeds 1000..   variant rng seed 11
    VALIDATION seeds 2000..   variant rng seed 22
    HELDOUT    seeds 9000..   variant rng seed 33  (wider jitter range => mild distribution shift)
"""
import numpy as np
from env import BASE

CAP_REF = 4

SC = {
    "S1_sparse":        dict(load=0.15),
    "S2_moderate":      dict(load=1.0),
    "S3_chronic":       dict(load=4.0),
    "S4_late_quality":  dict(load=2.0, dur_base=20.0, wave=dict(period=60, frac_low=0.6, mu_low=-2.0, mu_high=38.0, load_low=1.8, load_high=0.5), mu_sd=3.0, q_sd=8.0),
    "S5_correlated":    dict(load=3.0, NCL=2, cl_bonus=[10.0, -4.0], sig_c=12.0, sig_i=5.0),
    "S6_short_vs_long": dict(load=4.0, fast_slow=dict(dur_fast=2.0, dur_slow=36.0, mu_fast=6.0, mu_slow=45.0), dh_sd=0.2, rho_d=0.1, q_sd=8.0, mu_sd=0.0),
    "S7_regime_shift":  dict(load=3.0, regime=dict(t_frac=0.5, perm_mu=True, b_after=[1.0, -0.5, 1.0, -0.5], sig_c_mult=2.0, mu_shift=0.0), mu_sd=10.0),
    "S8_noisy_ranking": dict(load=3.0, score_sd=28.0, score_het=0.6),
    "S9_missing_quality": dict(load=3.0, p_miss=0.4, p_cost_unk=0.35, p_miss_dur=0.3),
    "S10_spam":         dict(load=2.5, spam=dict(rate=1.2, mu=-2.0, bias=12.0, inst=0)),
    "S11_burst":        dict(load=1.2, burst=(100, 3, 12.0)),
    "S12_all_equal":    dict(load=3.0, mu_sd=0.0, q_sd=1.0, score_sd=3.0, dur_het=0.0, dur_sd=0.2, sig_het=0.0, score_het=0.0, mu_mean=14.0, fee_lo=6.0, fee_hi=6.0, slip_lo=2.0, slip_hi=2.0),
}
# held-out-only compositions (never seen in tuning/validation)
HO_ONLY = {
    "H1_chronic_corr_regime": {**SC["S3_chronic"], **dict(NCL=2, cl_bonus=[8.0, -3.0], sig_c=10.0, regime=dict(t_frac=0.5, perm_mu=True, b_after=[1.0, -0.3], sig_c_mult=1.8))},
    "H2_burst_noisy_missing": {**SC["S11_burst"], **dict(load=2.0, score_sd=22.0, p_miss=0.3, p_cost_unk=0.25)},
    "H3_spam_fastslow":       {**SC["S10_spam"], **dict(fast_slow=dict(dur_fast=3.0, dur_slow=30.0, mu_fast=7.0, mu_slow=38.0), mu_sd=0.0, load=3.5)},
}

JITTER = {  # multiplicative range per split
    "TUNING":     (0.8, 1.25),
    "VALIDATION": (0.75, 1.3),
    "HELDOUT":    (0.65, 1.5),
}
JIT_KEYS = ["load", "score_sd", "dur_base", "sig_c", "q_sd"]
SPLIT_RNG = {"TUNING": 11, "VALIDATION": 22, "HELDOUT": 33}
SPLIT_SEED0 = {"TUNING": 1000, "VALIDATION": 2000, "HELDOUT": 9000}
# S6 fast/slow density ratio variants (different sets per split)
S6_RATIO = {"TUNING": [1.5, 2.5, 1.0], "VALIDATION": [1.25, 2.0, 0.8], "HELDOUT": [1.8, 0.9, 3.0]}


def families(split):
    d = dict(SC)
    if split == "HELDOUT":
        d.update(HO_ONLY)
    return d


def variants(name, split, nvar=3):
    fam = families(split)[name]
    rng = np.random.default_rng([SPLIT_RNG[split], abs(hash_str(name))])
    lo, hi = JITTER[split]
    out = []
    for v in range(nvar):
        p = dict(BASE); p.update(fam)
        for k in JIT_KEYS:
            base = p[k]
            if k == "load" and name in ("S1_sparse",):
                f = rng.uniform(lo, hi)
            else:
                f = rng.uniform(lo, hi)
            p[k] = base * f
        if name == "S6_short_vs_long" or "fast_slow" in fam:
            fs = dict(p["fast_slow"])
            ratio = S6_RATIO[split][v % 3]
            # fast density = mu_fast/dur_fast ; set slow so that fast/slow density = ratio
            dens_fast = fs["mu_fast"] / fs["dur_fast"]
            fs["mu_slow"] = dens_fast / ratio * fs["dur_slow"]
            p["fast_slow"] = fs
        p["_name"], p["_variant"], p["_split"] = name, v, split
        out.append(p)
    return out


def hash_str(s):
    h = 0
    for ch in s:
        h = (h * 131 + ord(ch)) % 1000003
    return h
