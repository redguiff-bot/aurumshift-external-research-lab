"""Step 6: the concrete lookahead demo. For as-of times T, compare
(a) FRED 'today' fredgraph.csv value (latest revised) with (b) ALFRED vintage T (what was known)."""
import csv, io, json
from common import fetch, text, RES
from alfred_vintage import snap

CASES = [("PAYEMS", "2020-04-01", "2020-06-15"), ("PAYEMS", "2022-12-01", "2023-01-20"),
         ("INDPRO", "2020-04-01", "2020-05-20"), ("INDPRO", "2022-03-01", "2022-04-20"),
         ("CPIAUCSL", "2022-06-01", "2022-07-20"), ("GDPC1", "2020-04-01", "2020-08-01"),
         ("GDP", "2020-04-01", "2020-08-01"), ("UNRATE", "2020-04-01", "2020-06-01")]
out = []
for s, o, T in CASES:
    r = fetch(f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={s}&cosd={o}&coed={o}", f"fred/{s}_{o}_today.csv")
    rows = list(csv.reader(io.StringIO(text(r))))
    today = float(rows[1][1]) if len(rows) > 1 and rows[1][1] not in ("", ".") else None
    known = snap(s, T, o, o).get(o)
    out.append({"series": s, "obs": o, "as_of_T": T, "value_known_at_T_ALFRED": known,
                "value_returned_today_FRED": today,
                "lookahead_diff": None if None in (known, today) else today - known,
                "receipt_time_utc": r.get("rec", {}).get("receipt_time_utc")})
    print(out[-1])
json.dump(out, open(RES + "/asof_vs_today.json", "w"), indent=1)
