"""Extra starvation tables incl. naive_zero semantics. Writes ../results/starvation_extra.md"""
import json, gzip, numpy as np
rec = {}
for line in gzip.open("../results/heldout_runs.jsonl.gz", "rt"):
    m = json.loads(line)
    if m["tag"] == "heldout":
        rec.setdefault((m["method"], m["mode"], m["scenario"]), []).append(m)
def col(meth, mode, sc, f):
    return [f(m) for m in rec[(meth, mode, sc)]]
L = ["| method | mode | S2 rare w25 ep1 | ep2 (after ~840 dormant) | S3 new-expert tts median | S3 reached<400 | S7 rare w25 ep1 (unlucky start) | ep2 | ep3 | S7 LATE recovery median |", "|---|---|---|---|---|---|---|---|---|---|"]
ms = sorted({k[0] for k in rec})
for mode, meths in (("correct", ms), ("naive_zero", [m for m in ms if (m, "naive_zero", "S2_dormancy") in rec])):
    for m in meths:
        e = np.array(col(m, mode, "S2_dormancy", lambda r: r["ev"]["rare_first25"]))
        t3 = np.array(col(m, mode, "S3_new_expert", lambda r: r["ev"]["tts_new"]))
        e7 = np.array(col(m, mode, "S7_temp_underperf", lambda r: r["ev"]["rare_first25"]))
        lr = np.array(col(m, mode, "S7_temp_underperf", lambda r: r["ev"]["late_recovery"]))
        L.append(f"| {m} | {mode} | {np.nanmean(e[:,0]):.3f} | {np.nanmean(e[:,1]):.3f} | {np.median(t3):.0f} | {(t3<400).mean():.2f} | {np.nanmean(e7[:,0]):.3f} | {np.nanmean(e7[:,1]):.3f} | {np.nanmean(e7[:,2]):.3f} | {np.median(lr):.0f} |")
open("../results/starvation_extra.md", "w").write("\n".join(L)); print("\n".join(L))
