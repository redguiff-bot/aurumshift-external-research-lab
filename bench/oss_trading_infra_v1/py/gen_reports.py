"""Generates reports/017_oss_trading_infra/01_LANDSCAPE.md (screen table), 08_ADJUDICATION.md (table + counts) and results/final_block.txt
from results/screen.json, results/footprint.json and adjudication.py. Narrative reports are hand-written."""
import json, os, sys
from collections import Counter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from adjudication import A; from catalog import C
R = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results"); OUT = os.path.join(R, "..", "..", "..", "reports", "017_oss_trading_infra")
screen = {r["name"]: r for r in json.load(open(f"{R}/screen.json"))}
fp = {r["name"]: r for r in json.load(open(f"{R}/footprint.json"))}
# ---------- 01 screen table
def lic(n):
    return A[n][4]
rows = []
for name, cls, repo, py, lang in C:
    g = screen[name]["git"]; p = screen[name]["pypi"] or {}
    def f(x): return "—" if x in (None, "") else str(x)
    c12 = g.get("commits_12m"); au = g.get("authors_12m"); top = g.get("top_author_share")
    rel = p.get("last_release"); rel = rel[0] if rel else None
    rows.append(f"| {name} | {','.join(cls.split(','))} | {lang} | {lic(name)} | {f(c12)} | {f(au)} | {f(None if top is None else round(top*100))} | {f(g.get('last_commit'))} | {f(rel)} | {f(p.get('releases_12m'))} | {f(g.get('test_files'))} | {A[name][1]} | {A[name][0]} |")
hdr = "| Candidate | Classes | Language | Licence (as observed) | Commits 12 m | Authors 12 m | Top author % | Last commit | Last PyPI release | PyPI rel. 12 m | Test files (path regex) | Executed | Class |\n|---|---|---|---|---|---|---|---|---|---|---|---|---|"
open(f"{OUT}/_landscape_table.md", "w").write(hdr + "\n" + "\n".join(rows) + "\n")
# ---------- 08 adjudication
cnt = Counter(v[0] for v in A.values()); ex = Counter(v[1] for v in A.values())
svc = [k for k, v in A.items() if v[2] == "Y"]; ds = [k for k, v in A.items() if v[3] == "Y"]
lines = ["| # | Candidate | Class | Executed | 2nd service | 2nd datastore | Licence | Evidence |", "|---|---|---|---|---|---|---|---|"]
order = {"ADOPT_REFERENCE": 0, "ADAPT_CANDIDATE": 1, "PARK": 2, "REJECT": 3}
for i, (k, v) in enumerate(sorted(A.items(), key=lambda kv: (order[kv[1][0]], kv[0].lower())), 1):
    lines.append(f"| {i} | {k} | **{v[0]}** | {v[1]} | {v[2]} | {v[3]} | {v[4]} | {v[5]} |")
open(f"{OUT}/_adjudication_table.md", "w").write("\n".join(lines) + "\n")
fb = f"""PROJECTS_DISCOVERED={len(C)}
PROJECTS_EXECUTED={ex['EXEC']} (behavioural microtest run); {ex['INSTALL']} install/import only; {ex['NO']} screened from metadata only

ADOPT_REFERENCE_COUNT={cnt['ADOPT_REFERENCE']}
ADAPT_CANDIDATE_COUNT={cnt['ADAPT_CANDIDATE']}
PARK_COUNT={cnt['PARK']}
REJECT_COUNT={cnt['REJECT']}

SECOND_SERVICE_REQUIRED_CANDIDATES={len(svc)} ({', '.join(svc)})
SECOND_DATASTORE_REQUIRED_CANDIDATES={len(ds)} ({', '.join(ds)})
"""
open(f"{R}/final_block_counts.txt", "w").write(fb); print(fb)
# footprint table for 07
fl = ["| Candidate | Distributions installed (alone, fresh py3.11 venv) | site-packages MB | Import s | Import OK in isolation |", "|---|---|---|---|---|"]
for k, v in fp.items():
    fl.append(f"| {k} | {v.get('n_distributions_installed','—')} | {v.get('site_packages_MB','—')} | {v.get('import_seconds','—')} | {'yes' if v.get('import_ok') else 'NO: '+v.get('import_err','')} |")
open(f"{OUT}/_footprint_table.md", "w").write("\n".join(fl) + "\n")
