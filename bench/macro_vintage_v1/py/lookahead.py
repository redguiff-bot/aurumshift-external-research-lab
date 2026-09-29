"""Step 3: quantify lookahead if 'latest revised value' is used instead of the
value that was published on the first release date (ALFRED vintages).
For each series: for every vintage v in the window in which a NEW newest observation appears,
compare first_print(o) [snapshot at v] with latest(o) [snapshot at last vintage]."""
import json, statistics as st, datetime as dt
from common import RES
from alfred_vintage import vintages, snap

WIN = ("2018-01-01", "2025-12-31")
SERIES = {"PAYEMS": "M", "INDPRO": "M", "CPIAUCSL": "M", "UNRATE": "M", "GDPC1": "Q", "DGS10": "D"}

def prev_obs(o, freq):
    y, m, d = map(int, o.split("-"))
    if freq == "M":
        m -= 1
        if m == 0: y, m = y - 1, 12
    elif freq == "Q":
        m -= 3
        if m <= 0: y, m = y - 1, m + 12
    return f"{y:04d}-{m:02d}-{d:02d}"

def main():
    out = {}
    for s, freq in SERIES.items():
        if freq == "D":
            continue  # control handled separately (market series, no vintages expected)
        vl = vintages(s)
        latest_v = vl[-1]
        latest = snap(s, latest_v, "2010-01-01", "2026-12-31")
        rows, prev_new = [], None
        cand = [v for v in vl if WIN[0] <= v <= WIN[1]]
        for v in cand:
            look = (dt.date.fromisoformat(v) - dt.timedelta(days=200)).isoformat()
            sn = snap(s, v, look, v)
            obs = sorted(k for k, x in sn.items() if x is not None)
            if not obs: continue
            o = obs[-1]
            if o == prev_new: continue
            prev_new = o
            po = prev_obs(o, freq)
            fp, fp_prev = sn.get(o), sn.get(po)
            lt, lt_prev = latest.get(o), latest.get(po)
            if None in (fp, lt): continue
            chg_fp = None if fp_prev is None else fp - fp_prev
            chg_lt = None if lt_prev is None else lt - lt_prev
            rows.append({"obs": o, "release_vintage": v, "first_print": fp, "latest": lt,
                         "abs_rev": lt - fp, "pct_rev": 100 * (lt - fp) / abs(fp) if fp else None,
                         "chg_first_asof_v": chg_fp, "chg_latest": chg_lt,
                         "sign_flip": (chg_fp is not None and chg_lt is not None and chg_fp * chg_lt < 0)})
        ar = [abs(r["abs_rev"]) for r in rows]
        summ = {"n": len(rows), "median_abs_rev": st.median(ar) if ar else None,
                "mean_abs_rev": st.mean(ar) if ar else None, "max_abs_rev": max(ar) if ar else None,
                "share_value_changed": sum(1 for r in rows if r["abs_rev"] != 0) / max(1, len(rows)),
                "n_sign_flips_in_change": sum(r["sign_flip"] for r in rows),
                "median_abs_pct_rev": st.median(abs(r["pct_rev"]) for r in rows if r["pct_rev"] is not None) if rows else None}
        print(s, json.dumps(summ))
        out[s] = {"summary": summ, "rows": rows, "latest_vintage": latest_v}
        json.dump(out, open(RES + "/lookahead_latest_vs_firstprint.json", "w"), indent=1)

    # release-day inclusion test (does vintage_date=T include values published on T?)
    t = {}
    for s, o, rel in [("PAYEMS", "2020-05-01", "2020-06-05"), ("GDPC1", "2020-04-01", "2020-07-30")]:
        d0 = (dt.date.fromisoformat(rel) - dt.timedelta(days=1)).isoformat()
        t[s] = {"obs": o, "release_date": rel,
                "vintage_day_before": snap(s, d0, o, o).get(o), "vintage_release_day": snap(s, rel, o, o).get(o)}
    print(t)
    json.dump(t, open(RES + "/release_day_inclusion.json", "w"), indent=1)

if __name__ == "__main__":
    main()
