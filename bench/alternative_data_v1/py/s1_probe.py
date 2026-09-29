"""Execute every catalogued probe: 3 calls spaced >=2 s (latency/stability), capture status, bytes, headers, parse shape. Plus a re-fetch revision test."""
import sys, json, time, hashlib, statistics as st
from lib import *
from catalog import S
def shape(b):
    if isinstance(b, dict): return "dict:" + ",".join(list(b.keys())[:8])
    if isinstance(b, list): return f"list[{len(b)}]" + (":" + ",".join(list(b[0].keys())[:8]) if b and isinstance(b[0], dict) else "")
    if isinstance(b, str): return "text:" + b[:80].replace("\n", " ")
    return type(b).__name__
out = {}
only = sys.argv[1:]
for s in S:
    if only and s["id"] not in only: continue
    res = []
    for lab, url, params, hdr in s["probes"]:
        calls = []
        for i in range(3):
            o = get(url, params, headers=hdr, retries=0, timeout=40)
            calls.append(dict(status=o.get("status"), ms=o.get("ms"), bytes=o.get("bytes"), hdr=o.get("hdr"), err=o.get("err"), shape=shape(o.get("body")) if o.get("ok") else (str(o.get("body"))[:120] if o.get("body") else None)))
            time.sleep(2.5)
        ok = [c for c in calls if c["status"] == 200]
        res.append(dict(label=lab, url=url, n_ok=len(ok), statuses=[c["status"] for c in calls], ms_median=round(st.median([c["ms"] for c in ok]), 1) if ok else None,
                        ms_max=max([c["ms"] for c in ok]) if ok else None, bytes=ok[0]["bytes"] if ok else None, hdr=(ok or calls)[0].get("hdr"), shape=(ok or calls)[0]["shape"], err=[c["err"] for c in calls if c.get("err")][:1]))
        print(s["id"], lab, res[-1]["statuses"], res[-1]["ms_median"], flush=True)
    out[s["id"]] = res
old = json.load(open(os.path.join(RES, "probe_results.json"))) if os.path.exists(os.path.join(RES, "probe_results.json")) else {}
old.update(out); jdump(old, "probe_results.json")
