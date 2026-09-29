"""Write configs/freeze_manifest.json: sha256 of the files that define the scenarios / protocol.  Run BEFORE any held-out policy run."""
import hashlib, json, os, subprocess, datetime, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILES = ["src/scenario_core.py", "src/scenarios_dev.py", "src/scenarios_heldout.py", "src/tune.py", "configs/protocol.json"]
def sha(p): return hashlib.sha256(open(os.path.join(ROOT, p), "rb").read()).hexdigest()
if __name__ == "__main__":
    m = dict(frozen_utc=datetime.datetime.utcnow().isoformat() + "Z", files={f: sha(f) for f in FILES},
             parent_git_head=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip(),
             statement="Scenario generators, split, seeds, search spaces, selection objective and practical thresholds were fixed before any policy other than the fixed reference A and round-robin was run on held-out/pilot scenarios.")
    json.dump(m, open(os.path.join(ROOT, "configs", "freeze_manifest.json"), "w"), indent=1)
    print(json.dumps(m, indent=1))
