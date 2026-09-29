"""Installed footprint + declared license per distribution (from installed metadata)."""
import json, sys, subprocess, os
from importlib import metadata
names = sys.argv[1:]
out = {}
for n in names:
    try: d = metadata.distribution(n)
    except Exception as e: out[n] = {"error": str(e)}; continue
    m = d.metadata
    lic = m.get("License-Expression") or ""
    if not lic:
        cl = [c for c in m.get_all("Classifier") or [] if c.startswith("License")]
        lic = "; ".join(cl) or (m.get("License") or "")[:60].replace("\n"," ")
    reqs = [r for r in (d.requires or []) if "extra ==" not in r]
    size = sum((d.locate_file(f).stat().st_size for f in (d.files or []) if d.locate_file(f).exists()), 0)
    out[n] = dict(version=d.version, license=lic, hard_requires=len(reqs), own_files_mb=round(size/1e6,1))
print(json.dumps(out))
