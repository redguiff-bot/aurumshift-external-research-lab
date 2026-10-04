"""Step 4: source-specific semantics (revision flags, update stamps, archives)."""
import json, re
from common import fetch, text, RES
out = {}
# World Bank WDI Archives: same obs across Versions (vintages)
r = fetch("https://api.worldbank.org/v2/sources/57/country/USA/series/NY.GDP.MKTP.CD/time/YR2015/version/all?format=json&per_page=100", "wb_archive_2015_allversions.json")
try:
    d = json.loads(text(r)); rows = d["source"]["data"] if isinstance(d, dict) else []
    vals = [(next(v["id"] for v in x["variable"] if v["concept"] == "Version"), x["value"]) for x in rows]
    out["worldbank_wdi_archive_USA_GDP_2015"] = vals[:60]
except Exception as e:
    out["worldbank_wdi_archive_USA_GDP_2015"] = f"parse_fail {e!r}: {text(r)[:200]}"
# ECB: OBS_STATUS + updatedAfter
r = fetch("https://data-api.ecb.europa.eu/service/data/ICP/M.U2.N.000000.4.ANR?startPeriod=2025-09&format=csvdata", "ecb_hicp_flags.csv")
out["ecb_hicp_status_values"] = sorted(set(re.findall(r",(\d{4}-\d{2}),([\-\d.]+),([A-Z]),", text(r))))[:14]
# Eurostat: dataset updated stamp + status flags
r = fetch("https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/prc_hicp_manr?geo=EA&coicop=CP00&lastTimePeriod=4", "eurostat_hicp_flags.json")
d = json.loads(text(r)); out["eurostat_hicp"] = {"updated": d.get("updated"), "status": d.get("status"), "time": d["dimension"]["time"]["category"]["index"], "value": d["value"]}
# Eurostat: sinceTimePeriod / lastUpdate params?
r = fetch("https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/prc_hicp_manr?geo=EA&coicop=CP00&lastTimePeriod=2&format=JSON&lang=EN&sinceTimePeriod=2026-06", "eurostat_hicp_since.json")
out["eurostat_since_status"] = r["status"]
# CFTC: fields
r = fetch("https://publicreporting.cftc.gov/resource/6dca-aqww.json?$limit=1&$order=report_date_as_yyyy_mm_dd%20DESC", "cftc_last1.json")
row = json.loads(text(r))[0]; out["cftc_fields_sample"] = {k: row[k] for k in list(row)[:8]}
m = json.loads(text(fetch("https://publicreporting.cftc.gov/api/views/6dca-aqww.json", "cftc_meta.json")))
out["cftc_meta"] = {k: m.get(k) for k in ("rowsUpdatedAt", "viewLastModified", "publicationDate", "createdAt", "license")}
# NYFed 
r = fetch("https://markets.newyorkfed.org/api/rates/secured/sofr/search.json?startDate=2026-09-01&endDate=2026-09-10", "nyfed_sofr_search.json")
d = json.loads(text(r)); out["nyfed_fields"] = list(d["refRates"][0].keys()); out["nyfed_revisions"] = [x for x in d["refRates"] if x.get("revisionIndicator")]
# Treasury FiscalData meta (record_date vs publication)
out["treasury_fields"] = list(json.loads(text(fetch("https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v2/accounting/od/debt_to_penny?page[size]=1&sort=-record_date", "treasury_debt_v2.json")))["data"][0].keys())
# BoC valet: series detail for a macro series w/ release info?
r = fetch("https://www.bankofcanada.ca/valet/series/FXUSDCAD/json", "boc_series_detail.json"); out["boc_series_detail_keys"] = list(json.loads(text(r)).keys())
# OECD: dataflows mentioning revision/vintage/real-time
x = fetch("https://sdmx.oecd.org/public/rest/dataflow/all", "oecd_dataflows.xml"); t = text(x)
names = re.findall(r'<common:Name xml:lang="en">([^<]*)</common:Name>', t)
out["oecd_flow_count"] = len(names); out["oecd_flows_revision_related"] = [n for n in names if re.search(r"revision|vintage|real[- ]time|original release", n, re.I)][:15]
out["oecd_flows_mei_like"] = [n for n in names if re.search(r"Main Economic Indicators|Composite leading|Consumer price", n, re.I)][:8]
json.dump(out, open(RES + "/semantics_probes.json", "w"), indent=1, default=str)
print(json.dumps(out, indent=1, default=str)[:6000])
