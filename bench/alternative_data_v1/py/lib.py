"""Shared helpers for alternative_data_v1: HTTP with timing/retry, logging. External research only."""
import json, os, time, requests, datetime as dt
HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data"); RES = os.path.join(HERE, "..", "results"); RAW = os.path.join(HERE, "..", "raw")
UA = {"User-Agent": "aurumshift-external-research-lab/altdata-probe (research)"}
RLH = ("retry-after", "x-ratelimit-limit", "x-ratelimit-remaining", "x-ratelimit-reset", "ratelimit-limit",
       "ratelimit-remaining", "ratelimit-reset", "last-modified", "etag", "cache-control", "date", "age", "content-length")
for d in (DATA, RES, RAW): os.makedirs(d, exist_ok=True)

def get(url, params=None, headers=None, timeout=30, retries=2, backoff=4.0, raw=False):
    """GET with retries on 429/5xx. Returns dict(ok,status,ms,bytes,hdr,body(json|text|bytes),err,attempts)."""
    h = dict(UA); h.update(headers or {})
    o = {"url": url, "params": params, "attempts": 0}
    for a in range(retries + 1):
        o["attempts"] = a + 1; t0 = time.time()
        try:
            r = requests.get(url, params=params, headers=h, timeout=timeout)
            o.update(status=r.status_code, ms=round((time.time() - t0) * 1000, 1), bytes=len(r.content),
                     hdr={k: v for k, v in r.headers.items() if k.lower() in RLH}, ctype=r.headers.get("content-type"),
                     recv_utc=dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"))
            o["ok"] = r.status_code == 200
            if raw: o["body"] = r.content
            else:
                try: o["body"] = r.json()
                except Exception: o["body"] = r.text
            if r.status_code in (429, 500, 502, 503, 504) and a < retries:
                time.sleep(float(r.headers.get("retry-after", backoff * (a + 1))) if r.headers.get("retry-after", "").isdigit() else backoff * (a + 1)); continue
            return o
        except Exception as e:
            o.update(ok=False, err=repr(e)[:200], ms=round((time.time() - t0) * 1000, 1))
            if a < retries: time.sleep(backoff * (a + 1))
    return o

def brief(o): return {k: v for k, v in o.items() if k not in ("body",)}
def jdump(obj, name):
    with open(os.path.join(RES, name), "w") as f: json.dump(obj, f, indent=1, default=str)
