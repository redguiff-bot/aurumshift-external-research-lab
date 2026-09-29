"""Maintenance / bus-factor metrics from bare blobless clones (git log only)."""
import subprocess, json, sys, collections, glob, os
ROOT = sys.argv[1]; NOW = "2026-09-29"
out = {}
def git(repo, *a):
    return subprocess.run(["git","-C",repo,*a],capture_output=True,text=True).stdout
for repo in sorted(glob.glob(ROOT+"/*.git")):
    n = os.path.basename(repo)[:-4]
    total = int(git(repo,"rev-list","--count","HEAD").strip() or 0)
    last = git(repo,"log","-1","--format=%cs").strip()
    first = git(repo,"log","--reverse","--format=%cs").splitlines()[0] if total else ""
    def authors(since):
        a = git(repo,"log",f"--since={since}","--format=%aN").splitlines()
        return collections.Counter(a)
    y1 = authors("2025-09-29"); y3 = authors("2023-09-29")
    tot = sum(y1.values()); top = y1.most_common(1)[0] if y1 else ("",0)
    # bus factor: min authors covering >=50% of last-12m commits
    acc=0; bf=0
    for _,c in y1.most_common():
        acc+=c; bf+=1
        if acc>=0.5*tot: break
    tags = git(repo,"tag","--sort=-creatordate").splitlines()[:1]
    out[n] = dict(commits_total=total, first_commit=first, last_commit=last,
                  commits_12m=tot, authors_12m=len(y1), authors_36m=len(y3),
                  top_author_share_12m=round(top[1]/tot,3) if tot else None,
                  bus_factor_50pct_12m=bf if tot else None, latest_tag=tags[0] if tags else None)
json.dump(out, open(sys.argv[2],"w"), indent=1)
for k,v in out.items(): print(k, v)
