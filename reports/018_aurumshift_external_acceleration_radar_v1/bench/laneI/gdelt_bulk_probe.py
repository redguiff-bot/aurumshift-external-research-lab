"""laneI — GDELT 2.0 bulk: lastupdate.txt -> export.CSV.zip ; vérifie md5, DATEADDED vs receipt, nb lignes, sous-ensemble 'central bank'."""
import requests, zipfile, io, hashlib, datetime as dt, json, collections
rec = dt.datetime.now(dt.timezone.utc)
lu = requests.get("https://data.gdeltproject.org/gdeltv2/lastupdate.txt", timeout=30)
lines = [l.split() for l in lu.text.strip().splitlines()]
size, md5, url = lines[0]
url = url.replace("http://", "https://")
z = requests.get(url, timeout=60).content
o = dict(receipt_utc=rec.isoformat(), lastupdate_http_date=lu.headers.get("Date"), lastupdate_last_modified=lu.headers.get("Last-Modified"),
         file=url, size_declared=int(size), size_got=len(z), md5_ok=hashlib.md5(z).hexdigest() == md5)
rows = io.TextIOWrapper(zipfile.ZipFile(io.BytesIO(z)).open(zipfile.ZipFile(io.BytesIO(z)).namelist()[0]), encoding="utf8").read().splitlines()
cols = [r.split("\t") for r in rows]
o["n_rows"] = len(cols); o["n_cols"] = collections.Counter(len(c) for c in cols).most_common(3)
o["DATEADDED_values"] = collections.Counter(c[59] for c in cols).most_common(5)  # col 60 = DATEADDED (YYYYMMDDHHMMSS UTC)
o["SQLDATE_values"] = collections.Counter(c[1] for c in cols).most_common(5)
cb = [c for c in cols if any(k in "\t".join(c).upper() for k in ("CENTRAL BANK", "FEDERAL RESERVE", "CBN", "ECB"))]
o["rows_mentioning_central_bank_actor"] = len(cb)
o["sample_sourceurls"] = [c[60] for c in cb[:3]]
open("results/gdelt_bulk_probe.json", "w").write(json.dumps(o, indent=1)); print(json.dumps(o, indent=1))
