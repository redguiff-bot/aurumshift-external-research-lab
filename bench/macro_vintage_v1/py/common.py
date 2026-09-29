import json, time, hashlib, os, urllib.request, urllib.error, datetime, ssl
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "raw"); RES = os.path.join(ROOT, "results")
UA = "aurumshift-external-research-lab/macro-vintage-v1 (research; contact jf.guiffant@gmail.com)"
def utcnow(): return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
def get(url, name=None, headers=None, data=None, timeout=60, save=True):
    """GET/POST; returns dict with receipt timestamp (our RECEIPT_TIME), status, headers, body(bytes)."""
    h = {"User-Agent": UA, "Accept": "*/*"}
    h.update(headers or {})
    req = urllib.request.Request(url, headers=h, data=data)
    t0 = utcnow(); t = time.time()
    try:
        r = urllib.request.urlopen(req, timeout=timeout); status = r.status; hd = dict(r.headers); body = r.read()
    except urllib.error.HTTPError as e:
        status = e.code; hd = dict(e.headers); body = e.read()
    except Exception as e:
        status = -1; hd = {}; body = repr(e).encode()
    out = {"url": url, "status": status, "receipt_time_utc": utcnow(), "request_time_utc": t0,
           "latency_s": round(time.time()-t, 3), "headers": hd, "bytes": len(body),
           "sha256": hashlib.sha256(body).hexdigest(), "body": body}
    if save and name:
        with open(os.path.join(RAW, name), "wb") as f: f.write(body)
        meta = {k: v for k, v in out.items() if k != "body"}
        with open(os.path.join(RAW, name + ".meta.json"), "w") as f: json.dump(meta, f, indent=1)
    return out
def dump(obj, name):
    with open(os.path.join(RES, name), "w") as f: json.dump(obj, f, indent=1, default=str)
