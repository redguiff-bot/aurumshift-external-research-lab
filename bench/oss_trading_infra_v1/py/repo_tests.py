"""Upstream test-suite proxy from git trees only (no blobs): #test files, share of source files, CI workflow files. Says nothing about test quality beyond presence/size."""
import subprocess, json, glob, os, sys, re
out = {}
for repo in sorted(glob.glob(sys.argv[1] + "/*.git")):
    n = os.path.basename(repo)[:-4]
    files = subprocess.run(["git", "-C", repo, "ls-tree", "-r", "--name-only", "HEAD"], capture_output=True, text=True).stdout.splitlines()
    src = [f for f in files if re.search(r"\.(py|rs|cs|ts|js|pyx)$", f)]
    tst = [f for f in src if re.search(r"(^|/)(tests?|test_[^/]*|[^/]*_test\.(py|rs|cs)|[^/]*Tests?\.cs)", f)]
    ci = [f for f in files if f.startswith(".github/workflows/") or f in (".travis.yml", "azure-pipelines.yml", ".circleci/config.yml")]
    out[n] = dict(source_files=len(src), test_files=len(tst), test_share=round(len(tst)/max(1, len(src)), 3), ci_files=len(ci))
json.dump(out, open(sys.argv[2], "w"), indent=1)
for k, v in out.items(): print(k, v)
