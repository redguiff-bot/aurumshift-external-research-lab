"""Metric computation (ground truth is used HERE only, never by policies)."""
import numpy as np
from scenario_core import K, R, T0, FRESH, H_STARVE, W_COV, MAG_RARE, LOW_INFO_EV

ADAPT_W = 10
LONG_SILENT = 40


def gini(x):
    x = np.sort(np.asarray(x, float))
    n = len(x)
    if n == 0 or x.sum() == 0:
        return 0.0
    return float((2 * np.arange(1, n + 1) - n - 1).dot(x) / (n * x.sum()))


def compute(sc, att, evd, val, picks):
    """att,evd (R,n) bool; val (R,n) float; picks (R,K) int (-1 pad)."""
    n = sc.n
    t_idx = np.arange(R)
    elig = (sc.birth[None, :] <= t_idx[:, None]) & (t_idx[:, None] < sc.death[None, :])
    sil = sc.silent & elig
    ev = sc.ev()
    ok = elig & ~sc.silent
    m = {}
    Ev = slice(T0, R)
    picks_eval = att[Ev].sum()

    # attempts on ineligible (retired/unborn) cells must be zero
    m["attempts_on_ineligible"] = int((att & ~elig).sum())

    # ---- coverage ------------------------------------------------------------------------
    covs = []
    for w in range(T0, R - W_COV + 1, W_COV):
        full = elig[w:w + W_COV].all(0)
        if full.sum():
            covs.append(att[w:w + W_COV][:, full].any(0).mean())
    m["coverage_W"] = float(np.mean(covs)) if covs else np.nan
    ever = elig[Ev].any(0)
    m["coverage_ever"] = float(att[Ev][:, ever].any(0).mean())

    # ---- starvation ----------------------------------------------------------------------
    ecum = np.vstack([np.zeros(n), np.cumsum(elig, 0)])
    acum = np.vstack([np.zeros(n), np.cumsum(att, 0)])
    rates = []
    for t in range(T0, R):
        a = t - H_STARVE + 1
        full = (ecum[t + 1] - ecum[a]) == H_STARVE
        if full.sum():
            zero = (acum[t + 1] - acum[a]) == 0
            rates.append((zero & full).sum() / full.sum())
    m["starvation_rate"] = float(np.mean(rates)) if rates else np.nan
    m["starvation_rate_max_t"] = float(np.max(rates)) if rates else np.nan
    maxrun = 0
    for c in range(n):
        s, e = int(sc.birth[c]), int(min(sc.death[c], R))
        ts = np.flatnonzero(att[:, c] & elig[:, c])
        pts = np.concatenate([[s - 1], ts, [e]])
        gaps = np.diff(pts) - 1
        ends = pts[1:]
        keep = ends > T0
        if keep.any():
            maxrun = max(maxrun, int(gaps[keep].max()))
    m["max_starvation_duration"] = maxrun

    # ---- staleness (last evidence, warm shift honoured) ------------------------------------
    last = np.full(n, -10 ** 6)
    seen = np.zeros(n, bool)
    st_ok, st_all = [], []
    silent_run = np.zeros(n, int)
    ls_num = ls_den = 0.0
    for t in range(R):
        newev = evd[t]
        last[newev] = t - sc.warm_shift if t < T0 else t
        seen |= newev
        silent_run = np.where(sil[t], silent_run + 1, 0)
        if t >= T0:
            ref = np.where(seen, last, sc.birth)
            stale = (t - ref) > FRESH
            e_ = elig[t]
            if e_.sum():
                st_all.append(stale[e_].mean())
                o_ = ok[t]
                if o_.sum():
                    st_ok.append(stale[o_].mean())
            ls = silent_run > LONG_SILENT
            k_t = att[t].sum()
            ls_num += (att[t] & ls).sum()
            ls_den += k_t * (ls[e_].sum() / max(e_.sum(), 1))
    m["stale_rate"] = float(np.mean(st_ok)) if st_ok else np.nan          # among cells able to produce evidence
    m["stale_rate_all"] = float(np.mean(st_all)) if st_all else np.nan
    m["longsilent_share"] = float(ls_num / max(picks_eval, 1))
    m["longsilent_baseline"] = float(ls_den / max(picks_eval, 1))

    # ---- silent / low-information attention ------------------------------------------------
    base_sil = sum(att[t].sum() * (sil[t].sum() / max(elig[t].sum(), 1)) for t in range(T0, R)) / max(picks_eval, 1)
    m["silent_share"] = float((att & sil)[Ev].sum() / max(picks_eval, 1))
    m["silent_baseline"] = float(base_sil)
    m["silent_excess"] = m["silent_share"] - m["silent_baseline"]
    low = ok & (ev < LOW_INFO_EV)
    base_low = sum(att[t].sum() * (low[t].sum() / max(elig[t].sum(), 1)) for t in range(T0, R)) / max(picks_eval, 1)
    m["lowinfo_share"] = float((att & low)[Ev].sum() / max(picks_eval, 1))
    m["lowinfo_baseline"] = float(base_low)
    m["lowinfo_excess"] = m["lowinfo_share"] - m["lowinfo_baseline"]

    # ---- rare high information --------------------------------------------------------------
    rare = np.flatnonzero(sc.rare)
    if len(rare):
        hi = (val[Ev][:, rare] >= 0.99 * MAG_RARE)
        disc = hi.any(0)
        first = np.where(disc, hi.argmax(0), R - T0)
        m["rare_discovery_rate"] = float(disc.mean())
        m["rare_time_to_discovery"] = float(first.mean())
    else:
        m["rare_discovery_rate"] = m["rare_time_to_discovery"] = np.nan

    # ---- information / regret ---------------------------------------------------------------
    pol_info = np.array([(att[t] & ~sc.silent[t]).dot(ev[t]) for t in range(R)])
    orc = np.zeros(R)
    top2 = []
    for t in range(R):
        okc = np.flatnonzero(ok[t])
        v = ev[t, okc]
        srt = np.argsort(-v)
        orc[t] = v[srt[:K]].sum()
        top2.append(set(okc[srt[:2 * K]].tolist()))
    m["info_expected"] = float(pol_info[Ev].sum())
    m["info_oracle"] = float(orc[Ev].sum())
    m["info_ratio"] = m["info_expected"] / max(m["info_oracle"], 1e-9)
    m["info_realized"] = float(val[Ev].sum())
    m["regret"] = m["info_oracle"] - m["info_expected"]
    e40 = slice(T0, T0 + 40)
    m["info_ratio_first40"] = float(pol_info[e40].sum() / max(orc[e40].sum(), 1e-9))

    # ---- concentration ----------------------------------------------------------------------
    cyc = elig[Ev].sum(0)
    good = cyc >= 20
    rate = att[Ev].sum(0)[good] / cyc[good]
    m["gini_attention_rate"] = gini(rate)
    tot = att[Ev].sum(0)
    srt = np.sort(tot)[::-1]
    m["top10pct_share"] = float(srt[:max(1, int(round(0.1 * ever.sum())))].sum() / max(tot.sum(), 1))

    # ---- turnover ---------------------------------------------------------------------------
    sets = [set(p[p >= 0].tolist()) for p in picks]
    m["turnover"] = float(np.mean([1 - len(sets[t] & sets[t - 1]) / max(len(sets[t]), 1) for t in range(T0 + 1, R)]))

    # ---- new cells (P1/P5/P6) ---------------------------------------------------------------
    newc = np.flatnonzero(sc.birth >= T0)
    if len(newc):
        ttfa, never = [], 0
        for c in newc:
            ts = np.flatnonzero(att[:, c] & elig[:, c])
            if len(ts):
                ttfa.append(ts[0] - sc.birth[c])
            else:
                ttfa.append(min(sc.death[c], R) - sc.birth[c]); never += 1
        m["new_ttfa_median"] = float(np.median(ttfa)); m["new_ttfa_p95"] = float(np.percentile(ttfa, 95))
        m["new_ttfa_max"] = float(np.max(ttfa)); m["new_never_attempted"] = never / len(newc)
        b0 = sc.birth[newc].min()
        coh = newc[sc.birth[newc] == b0]
        def _first(c):
            ts = np.flatnonzero(att[:, c] & elig[:, c])
            return ts[0] - b0 if len(ts) else R - b0
        firsts = sorted(_first(c) for c in coh)
        j = int(np.ceil(0.9 * len(coh))) - 1
        m["new_cohort_cov90_time"] = float(firsts[j])
    else:
        m["new_ttfa_median"] = m["new_ttfa_p95"] = m["new_ttfa_max"] = m["new_never_attempted"] = m["new_cohort_cov90_time"] = np.nan

    # ---- adaptation (structural change) -------------------------------------------------------
    ch, tgt, deg = sc.meta.get("change_t"), sc.meta.get("target", []), sc.meta.get("degraded", [])
    if ch is not None and len(tgt):
        tgt = np.asarray(tgt)
        share = att[:, tgt].sum(1) / np.maximum(att.sum(1), 1)
        frac = np.array([elig[t, tgt].sum() / max(elig[t].sum(), 1) for t in range(R)])
        delay, cens = R - ch, 1.0
        for t in range(ch + ADAPT_W - 1, R):
            a = t - ADAPT_W + 1
            if share[a:t + 1].mean() >= 2 * frac[a:t + 1].mean():
                delay, cens = t - ch, 0.0
                break
        m["adapt_delay"], m["adapt_censored"] = float(delay), cens
        a, b = ch + 50, min(ch + 150, R)
        m["target_share_post"] = float(share[a:b].mean()); m["target_baseline_post"] = float(frac[a:b].mean())
        hr = [len(set(picks[t][picks[t] >= 0].tolist()) & top2[t]) / max((picks[t] >= 0).sum(), 1) for t in range(ch, R)]
        m["hit_rate_post"] = float(np.mean(hr))
    else:
        m["adapt_delay"] = m["adapt_censored"] = m["target_share_post"] = m["target_baseline_post"] = m["hit_rate_post"] = np.nan
    if ch is not None and len(deg):
        deg = np.asarray(deg)
        share = att[:, deg].sum(1) / np.maximum(att.sum(1), 1)
        frac = np.array([elig[t, deg].sum() / max(elig[t].sum(), 1) for t in range(R)])
        a, b = ch + 50, min(ch + 150, R)
        m["degraded_share_post"] = float(share[a:b].mean()); m["degraded_baseline_post"] = float(frac[a:b].mean())
        m["degraded_excess_post"] = m["degraded_share_post"] - m["degraded_baseline_post"]
    else:
        m["degraded_share_post"] = m["degraded_baseline_post"] = m["degraded_excess_post"] = np.nan
    return m
