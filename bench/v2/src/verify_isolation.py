"""Isolation audit -> results/isolation_report.json.  PASS iff every check holds."""
import hashlib, json, os, subprocess, ast, glob
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(os.path.dirname(ROOT))
def sha(p): return hashlib.sha256(open(p, "rb").read()).hexdigest()
def git(*a): return subprocess.check_output(["git", *a], cwd=REPO).decode().strip()
checks = {}
fm = json.load(open(os.path.join(ROOT, "configs", "freeze_manifest.json")))
for f, h in fm["files"].items():
    cur = sha(os.path.join(ROOT, f))
    ok = cur == h
    if f == "src/tune.py" and not ok:      # documented amendment (tie rule), before any held-out run
        ok = cur == fm["amendments"][-1]["tune_py_sha256"]
    checks[f"frozen_file_unchanged:{f}"] = ok
lock = json.load(open(os.path.join(ROOT, "results", "heldout", "params_lock.json")))
for k, h in lock["selected_file_sha256"].items():
    checks[f"selected_params_match_lock:{k}"] = sha(os.path.join(ROOT, "configs", f"selected_{k}.json")) == h
checks["heldout_generator_matches_lock"] = sha(os.path.join(ROOT, "src", "scenarios_heldout.py")) == lock["heldout_generator_sha256"]
sel_commit = git("log", "-1", "--format=%H", "--", "bench/v2/configs/selected_D.json")
raw_commit = git("log", "--diff-filter=A", "--format=%H", "--", "bench/v2/results/heldout/S1_MASSIVE_COLD_START.json").splitlines()[-1]
checks["selected_params_committed_before_heldout_results"] = subprocess.run(["git", "merge-base", "--is-ancestor", sel_commit, raw_commit], cwd=REPO).returncode == 0
for f in ("tune.py", "scenarios_dev.py"):
    tree = ast.parse(open(os.path.join(ROOT, "src", f)).read())
    mods = {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)} | {a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
    checks[f"no_heldout_import:{f}"] = "scenarios_heldout" not in mods and "scenarios_adv" not in mods
prot = json.load(open(os.path.join(ROOT, "configs", "protocol.json")))
rng = {k: set(range(*v)) for k, v in prot["seeds"].items()}
names = list(rng)
checks["seed_ranges_disjoint"] = all(not (rng[a] & rng[b]) for i, a in enumerate(names) for b in names[i + 1:])
seen = set()
for k in ("B", "C", "C2", "D"):
    tun = json.load(open(os.path.join(ROOT, "results", "tuning", f"{k}_raw.json")))
    seen |= {r["seed"] for split in ("train", "validation") for rs in tun[split].values() for r in rs}
checks["tuning_runs_used_only_dev_seeds"] = seen <= (rng["train"] | rng["validation"])
heldout_seeds = {r["seed"] for f in glob.glob(os.path.join(ROOT, "results", "heldout", "S*.json")) for r in json.load(open(f))["runs"]}
checks["heldout_runs_used_only_heldout_seeds"] = heldout_seeds == rng["heldout"]
checks["v1_artifacts_unmodified"] = git("diff", "--stat", "034d04a", "HEAD", "--", "reports/001_adaptive_strategy_fleet") == ""
res = dict(checks=checks, HELDOUT_ISOLATION="PASS" if all(checks.values()) else "FAIL", head=git("rev-parse", "HEAD"))
json.dump(res, open(os.path.join(ROOT, "results", "isolation_report.json"), "w"), indent=1)
print(json.dumps(res, indent=1))
