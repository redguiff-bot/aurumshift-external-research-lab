"""Shared probe helpers: HTTP call with timing, raw capture, rate-limit header capture."""
import json, os, time, hashlib, requests

RAW = os.path.join(os.path.dirname(__file__), "..", "raw")
UA = {"User-Agent": "aurumshift-external-research-lab/feed-probe (research; contact via repo)"}
RL_HDRS = ("retry-after", "x-ratelimit-limit", "x-ratelimit-remaining", "x-ratelimit-reset",
           "x-mbx-used-weight", "x-mbx-used-weight-1m", "ratelimit-limit", "ratelimit-remaining",
           "ratelimit-reset", "x-rate-limit-remaining", "x-ratelimit-requests-remaining", "date", "server")


def call(name, url, params=None, method="GET", body=None, headers=None, timeout=20, save=True):
    """One HTTP call. Returns dict(ok,status,ms,bytes,json,hdr,err). Saves raw body under raw/<name>.json|txt"""
    h = dict(UA)
    if headers:
        h.update(headers)
    t0 = time.time()
    out = {"name": name, "url": url, "params": params, "method": method}
    try:
        r = requests.request(method, url, params=params, json=body, headers=h, timeout=timeout)
        out["ms"] = round((time.time() - t0) * 1000, 1)
        out["status"] = r.status_code
        out["bytes"] = len(r.content)
        out["hdr"] = {k: v for k, v in r.headers.items() if k.lower() in RL_HDRS}
        out["ctype"] = r.headers.get("content-type")
        out["recv_utc"] = time.time()
        try:
            out["json"] = r.json()
        except Exception:
            out["text"] = r.text[:2000]
        out["ok"] = r.status_code == 200
        if save and r.status_code == 200:
            os.makedirs(RAW, exist_ok=True)
            ext = "json" if "json" in out else "txt"
            with open(os.path.join(RAW, f"{name}.{ext}"), "w") as f:
                if ext == "json":
                    s = json.dumps(out["json"])
                    f.write(s[:400000])
                else:
                    f.write(r.text[:400000])
    except Exception as e:
        out["ms"] = round((time.time() - t0) * 1000, 1)
        out["ok"] = False
        out["err"] = repr(e)[:300]
    return out


def brief(o):
    return {k: v for k, v in o.items() if k not in ("json", "text")}
