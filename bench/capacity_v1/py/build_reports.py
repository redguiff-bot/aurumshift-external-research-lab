"""Inline generated tables ({{T:name}}) into the report markdown files."""
import os, re, glob
HERE = os.path.dirname(os.path.abspath(__file__))
TAB = os.path.join(HERE, "..", "results", "tables")
REP = os.path.join(HERE, "..", "..", "..", "reports", "008_risk_capacity_turnover")
BASE = ["FIFO", "ROUND_ROBIN", "RANDOM_SEEDED", "EQUAL_QUOTA", "OLDEST_SLOT", "FIFO_NETPOS"]
pz = open(f"{TAB}/heldout_pooled_dz.md").read().splitlines()
open(f"{TAB}/heldout_pooled_dz_baselines.md", "w").write("\n".join(pz[:2] + [l for l in pz[2:] if l.split("|")[1].strip() in BASE]) + "\n")
for f in sorted(glob.glob(f"{REP}/*.md")):
    s = open(f).read()
    def sub(m):
        return open(f"{TAB}/{m.group(1)}.md").read().strip("\n")
    s2 = re.sub(r"\{\{T:([A-Za-z0-9_]+)\}\}", sub, s)
    open(f, "w").write(s2)
    print(os.path.basename(f), len(re.findall(r"\{\{T:", s)), "tables")
