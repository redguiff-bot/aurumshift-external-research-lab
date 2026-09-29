"""Générateur déterministe (seed fixe) de ≥1M observations : multi-instruments, révisions, arrivées tardives, backfills, doublons."""
import random, datetime as dt
from common import D0

def gen(n_instr=200, bars=4000, seed=42, dup=0.02, late=0.03, rev=0.05, backfill=0.02, tf_s=300):
    rnd = random.Random(seed); rows = []
    for i in range(n_instr):
        inst = f"I{i:04d}"
        for b in range(bars):
            ev = D0 + dt.timedelta(seconds=b * tf_s)
            r = rnd.random()
            if r < backfill:
                prov, lag = "BACKFILL", rnd.uniform(3600, 72000)
            elif r < backfill + late:
                prov, lag = "LIVE", rnd.uniform(60, 900)
            else:
                prov, lag = "LIVE", rnd.uniform(0.2, 5)
            ing = ev + dt.timedelta(seconds=tf_s + lag)     # barre close à ev+tf
            fo = None if prov == "BACKFILL" and rnd.random() < .5 else (ing - dt.timedelta(seconds=rnd.uniform(0, 1)) if prov == "LIVE" else ing)
            pid = f"{inst}-{b}"; c = round(100 + rnd.gauss(0, 1), 4)
            rows.append(("A", inst, "5m", ev, pid, None, "live", "FINAL", "X", prov, fo, ing, c))
            if rnd.random() < rev:
                ing2 = ing + dt.timedelta(seconds=rnd.uniform(600, 40000))
                rows.append(("A", inst, "5m", ev, pid, 1, "live", "CORRECTED", "X", "LIVE", ing2 - dt.timedelta(seconds=.5), ing2, round(c + rnd.gauss(0, .1), 4)))
            if rnd.random() < dup:
                rows.append(("A", inst, "5m", ev, pid, None, "live", "FINAL", "X", prov, fo, ing + dt.timedelta(seconds=rnd.uniform(1, 30)), c))
    return rows
