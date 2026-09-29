"""Metadata screen: blobless shallow clone (commits since 2025-09-29) + PyPI JSON. Writes results/screen.json"""
import json, subprocess, os, sys, urllib.request, datetime as dt, collections, re, shutil
from concurrent.futures import ThreadPoolExecutor
from catalog import C
W = "/tmp/oss_clones"; os.makedirs(W, exist_ok=True)
SINCE = "2025-09-29"
def sh(cmd, cwd=None, t=240):
    try:
        r = subprocess.run(cmd, cwd=cwd, shell=True, capture_output=True, text=True, timeout=t)
        return r.returncode, r.stdout
    except subprocess.TimeoutExpired:
        return 124, ""
def pypi(name):
    try:
        with urllib.request.urlopen(f"https://pypi.org/pypi/{name}/json", timeout=20) as r:
            d = json.load(r)
    except Exception as e:
        return {"error": str(e)}
    i = d["info"]; rel = d["releases"]
    dates = sorted((f["upload_time"][:10], v) for v, fs in rel.items() for f in fs[:1])
    last = dates[-1] if dates else None
    recent = [x for x in dates if x[0] >= SINCE]
    return {"version": i["version"], "license": i.get("license_expression") or (i.get("license") or "")[:80],
            "classifiers_license": [c for c in i["classifiers"] if c.startswith("License")],
            "requires_python": i.get("requires_python"), "requires_dist": i.get("requires_dist") or [],
            "last_release": last, "releases_12m": len(recent), "n_releases": len(dates),
            "first_release": dates[0][0] if dates else None, "yanked_latest": None}
def git(item):
    name, cls, repo, py, lang = item
    d = f"{W}/{repo.replace('/','__')}"
    out = {"repo": repo}
    if not os.path.isdir(d):
        rc, o = sh(f"git clone --bare --filter=blob:none --shallow-since={SINCE} --single-branch https://github.com/{repo}.git {d}", t=300)
        if rc != 0:
            rc, o = sh(f"git clone --bare --filter=blob:none --depth=200 --single-branch https://github.com/{repo}.git {d}", t=300)
            if rc != 0:
                out["error"] = "clone failed"; return out
    _, log = sh("git log --since=2025-09-29 --format='%ad|%an|%ae' --date=short", cwd=d)
    rows = [l.split("|") for l in log.strip().splitlines() if l]
    out["commits_12m"] = len(rows)
    cnt = collections.Counter(r[1] for r in rows)
    out["authors_12m"] = len(cnt)
    out["top_author_share"] = round(cnt.most_common(1)[0][1]/len(rows), 3) if rows else None
    # authors needed for 50% of commits
    acc, k = 0, 0
    for a, n in cnt.most_common():
        acc += n; k += 1
        if acc >= len(rows)/2: break
    out["authors_for_50pct"] = k if rows else None
    _, ld = sh("git log -1 --format=%ad --date=short", cwd=d)
    out["last_commit"] = ld.strip()
    _, ls = sh("git ls-tree -r --name-only HEAD", cwd=d, t=120)
    files = ls.splitlines()
    out["n_files"] = len(files)
    out["test_files"] = sum(1 for f in files if re.search(r"(^|/)(tests?|testing)/|(^|/)test_[^/]*\.|_test\.(py|rs|go|ts|cs|java)$|\.Tests?/", f, re.I))
    out["ci"] = sorted({f.split('/')[1] if f.startswith('.github/workflows/') and f.count('/')>=2 else f for f in files if f.startswith('.github/workflows/') or f in ('.travis.yml','.gitlab-ci.yml','azure-pipelines.yml','.circleci/config.yml')})[:6]
    for lf in ("LICENSE","LICENSE.md","LICENSE.txt","LICENCE","COPYING","LICENSE.rst","LICENSE-APACHE","LICENSE.APACHE"):
        if lf in files:
            _, t = sh(f"git show HEAD:{lf} | head -c 400", cwd=d)
            out["license_file"] = lf; out["license_head"] = " ".join(t.split())[:160]; break
    else:
        out["license_file"] = None
    _, ar = sh("git show HEAD:README.md | head -c 3000 | grep -i -E 'archiv|deprecat|no longer maintain|unmaintain' | head -2", cwd=d)
    out["readme_flags"] = ar.strip()[:200]
    out["lockfiles"] = [f for f in files if f in ("Cargo.toml","pyproject.toml","setup.py","requirements.txt","package.json","go.mod","pom.xml","CMakeLists.txt","Dockerfile","docker-compose.yml")][:8]
    return out
def one(item):
    r = {"name": item[0], "classes": item[1].split(","), "lang": item[4]}
    r["git"] = git(item)
    r["pypi"] = pypi(item[3]) if item[3] else None
    print("done", item[0], r["git"].get("commits_12m"), r["git"].get("error"), flush=True)
    return r
if __name__ == "__main__":
    with ThreadPoolExecutor(6) as ex: res = list(ex.map(one, C))
    json.dump(res, open("../results/screen.json","w"), indent=1)
