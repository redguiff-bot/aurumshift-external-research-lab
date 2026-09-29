"""Low-SNR sensitivity: frozen tuned configs from the normal-SNR tuning; 8 seeds; ratio of regret to rolling."""
import json, numpy as np
from collections import defaultdict
rows = json.load(open("../results/main_lowsnr.json")); d = defaultdict(list)
for r in rows: d[(r["kind"], r["model"], r["scenario"])].append(r["regret"])
sc = ["abrupt", "recurring", "random_walk"]; out = ["| track | model | " + " | ".join(sc) + " | geomean ratio vs rolling |", "|---|---|" + "---|" * 4]
for k in "CR":
    ms = sorted({m for (kk, m, _) in d if kk == k})
    for m in ms:
        v = [np.mean(d[(k, m, s)]) for s in sc]; ratio = [np.mean(d[(k, m, s)]) / np.mean(d[(k, "rolling", s)]) for s in sc]
        out.append(f"| {k} | {m} | " + " | ".join(f"{x:.3f}" for x in v) + f" | {np.exp(np.mean(np.log(ratio))):.2f} |")
open("../results/tables_lowsnr.md", "w").write("\n".join(out)); print("\n".join(out))
