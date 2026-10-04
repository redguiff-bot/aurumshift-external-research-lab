"""Shared fetch helper: every HTTP call is cached to raw/ and logged with a
receipt timestamp (RECEIPT_TIME = our local UTC clock at response end)."""
import hashlib, json, os, time, datetime as dt, requests

ROOT = os.path.join(os.path.dirname(__file__), "..")
RAW = os.path.join(ROOT, "raw")
RES = os.path.join(ROOT, "results")
# NOTE: FRED/ALFRED/IMF stalled or 403'd a custom research User-Agent (observed 2026-09-29);
# default python-requests UA is accepted. Kept default.
UA = {}
KEEP = ("Date", "Last-Modified", "ETag", "Content-Type", "Age", "Cache-Control")


def fetch(url, name, method="GET", data=None, timeout=60, params=None, refresh=False):
    path = os.path.join(RAW, name)
    if os.path.exists(path) and not refresh:
        return {"status": None, "cached": True, "path": path, "body": open(path, "rb").read()}
    t0 = time.time()
    r = None
    for attempt in range(4):  # transient proxy disconnects observed; retry with backoff
        try:
            r = requests.request(method, url, data=data, params=params, headers=UA, timeout=timeout)
            break
        except Exception as e:  # network/proxy failure is itself a result if persistent
            err = repr(e)
            time.sleep(2 ** attempt)
    if r is None:
        _log({"url": url, "name": name, "error": err, "attempts": 4})
        return {"status": None, "error": err, "body": b""}
    body = r.content
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(body)
    rec = {
        "url": r.url, "name": name, "method": method, "status": r.status_code,
        "receipt_time_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "elapsed_s": round(time.time() - t0, 2), "bytes": len(body),
        "sha256": hashlib.sha256(body).hexdigest(),
        "headers": {k: r.headers[k] for k in KEEP if k in r.headers},
    }
    _log(rec)
    return {"status": r.status_code, "path": path, "body": body, "headers": r.headers, "rec": rec}


def _log(rec):
    os.makedirs(RAW, exist_ok=True)
    with open(os.path.join(RAW, "_receipts.jsonl"), "a") as f:
        f.write(json.dumps(rec) + "\n")


def text(res):
    return res["body"].decode("utf-8", "replace")
