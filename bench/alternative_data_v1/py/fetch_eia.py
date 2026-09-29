"""Download EIA bulk files used by real_economy.py into data/raw (gitignored, ~60 MB)."""
import os, requests
from h import UA
raw = os.path.join(os.path.dirname(__file__), "..", "data", "raw"); os.makedirs(raw, exist_ok=True)
for f in ("PET", "NG"):
    r = requests.get(f"https://www.eia.gov/opendata/bulk/{f}.zip", headers=UA, timeout=300); r.raise_for_status()
    open(os.path.join(raw, f"{f}.zip"), "wb").write(r.content); print(f, len(r.content), r.headers.get("last-modified"))
