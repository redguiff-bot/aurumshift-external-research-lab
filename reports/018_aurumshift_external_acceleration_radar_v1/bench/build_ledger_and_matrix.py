"""Fusionne evidence/candidates_*.csv -> CANDIDATE_MATRIX.csv et extrait SOURCE_LEDGER (URLs primaires).

Ajoute deux colonnes d'orchestration : lane_classification (proposée par la sous-recherche)
et final_classification (adjudication du rapport, cf. REPORT.md §4), plus orchestrator_note.
Usage : python3 bench/build_ledger_and_matrix.py  (depuis le dossier du rapport)
"""
import csv
import glob
import json
import re
from collections import defaultdict

OVERRIDES = json.load(open("bench/final_adjudication.json"))
EXTRA = "evidence/candidates_orchestrator.csv"

rows = []
for f in sorted(glob.glob("evidence/candidates_*.csv")):
    for r in csv.DictReader(open(f)):
        r = {k: (v if v is not None else "") for k, v in r.items()}
        r["source_file"] = f.split("/")[-1]
        rows.append(r)

header = list(rows[0].keys())
header.remove("source_file")
header = header[:header.index("classification")] + ["lane_classification", "final_classification", "orchestrator_note"] + \
    header[header.index("classification") + 1:] + ["source_file"]
out = []
for r in rows:
    o = dict(r)
    o["lane_classification"] = r["classification"]
    ov = OVERRIDES.get(r["candidate_id"], {})
    o["final_classification"] = ov.get("final", r["classification"])
    o["orchestrator_note"] = ov.get("note", "")
    del o["classification"]
    out.append(o)

with open("CANDIDATE_MATRIX.csv", "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=header, quoting=csv.QUOTE_MINIMAL)
    w.writeheader()
    w.writerows(out)

missing = [k for k in OVERRIDES if k not in {r["candidate_id"] for r in rows}]
print("rows", len(out), "overrides", len(OVERRIDES), "unmatched_overrides", missing)

# Source ledger
url_re = re.compile(r"https?://[^\s)>\"`|,;\]]+")
by_url = defaultdict(set)
for f in sorted(glob.glob("evidence/raw_*.md")) + sorted(glob.glob("evidence/candidates_*.csv")):
    lane = re.sub(r"^(raw_|candidates_)|\.(md|csv)$", "", f.split("/")[-1])
    for u in url_re.findall(open(f).read()):
        by_url[u.rstrip(".'")].add(lane)


def kind(u):
    h = u.split("/")[2]
    if "github.com" in h or "githubusercontent" in h or "gitlab" in h or "crates.io" in h or "docs.rs" in h:
        return "CODE_REPO"
    if "pypi.org" in h or "npmjs" in h:
        return "PACKAGE_REGISTRY"
    if "arxiv" in h or "doi.org" in h or "jstor" in h or "academic.oup" in h or "projecteuclid" in h or "ssrn" in h:
        return "PAPER"
    if any(x in u for x in ("pricing", "/plans", "price")):
        return "PRICING"
    if any(x in h for x in ("okx.com", "binance", "bybit", "tardis.dev", "bea.gov", "bls.gov", "federalreserve",
                             "ecb.europa", "bankofengland", "boj.or.jp", "stlouisfed", "kalshi", "polymarket",
                             "gdeltproject", "faireconomy")):
        return "OFFICIAL_API_OR_DATA"
    return "DOCS_OR_OTHER"


lines = ["# SOURCE_LEDGER — AURUMSHIFT_EXTERNAL_ACCELERATION_RADAR_V1", "",
         "Registre généré par `bench/build_ledger_and_matrix.py` à partir des notes de travail `evidence/raw_*.md` et",
         "des colonnes `primary_sources` de `evidence/candidates_*.csv`. Chaque URL est rattachée aux lanes qui la citent ;",
         "le contexte exact (citation, étiquette VERIFIED_FACT / VENDOR_CLAIM / etc.) est dans la note de lane.",
         "Type = heuristique sur le domaine (CODE_REPO, PACKAGE_REGISTRY, PAPER, PRICING, OFFICIAL_API_OR_DATA, DOCS_OR_OTHER).",
         "Les URLs d'API exécutées sont des endpoints interrogés, pas des pages lues.", "",
         f"Total URLs uniques : {len(by_url)}", ""]
for k in ("PAPER", "PRICING", "OFFICIAL_API_OR_DATA", "CODE_REPO", "PACKAGE_REGISTRY", "DOCS_OR_OTHER"):
    us = sorted(u for u in by_url if kind(u) == k)
    lines += [f"## {k} ({len(us)})", "", "| URL | lanes |", "|---|---|"]
    lines += [f"| {u} | {', '.join(sorted(by_url[u]))} |" for u in us]
    lines.append("")
open("SOURCE_LEDGER_URLS.md", "w").write("\n".join(lines))
print("urls", len(by_url))
