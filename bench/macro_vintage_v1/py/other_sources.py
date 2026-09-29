"""Semantics tests for non-FRED sources. Everything stamped with our own RECEIPT_TIME."""
import re, csv, io, json
from common import *
from alfred_test import at
R = {"run_utc": utcnow()}
def T(name, url, **kw):
    r = get(url, name=name, timeout=60, **kw); return r, r["body"].decode("utf8", "replace")
# --- BLS
# BLS v1 shares a per-IP daily quota: the successful call is in raw/bls_api_v1 (probe); a re-call hits the threshold (recorded below)
r2, t2 = T("bls_v1_recall", "https://api.bls.gov/publicAPI/v1/timeseries/data/CES0000000001?startyear=2024&endyear=2026")
r = {"status": 200}; t = open(os.path.join(RAW, "bls_api_v1"), encoding="utf8").read()
j = json.loads(t); d = j["Results"]["series"][0]["data"]
bls = {(x["year"]+"-"+x["period"][1:]+"-01"): float(x["value"]) for x in d}
alf = at("PAYEMS", "2026-09-28", cosd="2025-01-01")["obs"]
common = sorted(set(bls) & set(alf))
R["bls_v1"] = {"status": r["status"], "n": len(d), "keys": sorted(d[0].keys()), "footnote_codes": sorted({f.get("code","") for x in d for f in x.get("footnotes", [])}),
    "has_latest_flag": any("latest" in x for x in d), "has_release_timestamp": False, "has_vintage_param": False,
    "bls_vs_alfred_latest_equal": sum(1 for k in common if abs(bls[k]-alf[k]) < 1e-9), "compared": len(common),
    "v1_recall_message": json.loads(t2).get("message"), "api_v2_nokey": json.loads(open(os.path.join(RAW, "bls_api_v2_nokey")).read())["message"][:1]}
# independent check of ALFRED initial value vs BLS archived release
r, t = T("bls_empsit_2009_01_09", "https://www.bls.gov/news.release/archives/empsit_01092009.htm")
m = re.search(r"[Nn]onfarm payroll employment[^.]{0,200}\.", re.sub(r"<[^>]+>", " ", t))
a1 = at("PAYEMS", "2009-01-09", cosd="2008-10-01", coed="2008-12-01")["obs"]
R["bls_archive_vs_alfred_initial"] = {"status": r["status"], "bytes": r["bytes"], "bls_text": re.sub(r"\s+", " ", m.group(0))[:300] if m else None,
    "alfred_vintage_2009-01-09": a1, "alfred_dec_minus_nov": (a1.get("2008-12-01", 0) - a1.get("2008-11-01", 0)) if a1 else None}
# --- ECB
r, t = T("ecb_hicp_hist", "https://data-api.ecb.europa.eu/service/data/ICP/M.U2.N.000000.4.ANR?lastNObservations=24&format=csvdata")
rows = list(csv.DictReader(io.StringIO(t)))
R["ecb"] = {"obs_status_values": sorted({x["OBS_STATUS"] for x in rows}), "n": len(rows), "columns_with_time_semantics": [c for c in rows[0] if c in ("TIME_PERIOD","OBS_STATUS","OBS_CONF","COLLECTION")]}
for nm, q in [("upd_z", "updatedAfter=2026-08-01T00:00:00Z"), ("upd_plus", "updatedAfter=2026-08-01T00:00:00%2B00:00"), ("hist", "includeHistory=true"), ("upd_and_hist", "updatedAfter=2026-08-01T00:00:00Z&includeHistory=true")]:
    r, t = T(f"ecb_{nm}", f"https://data-api.ecb.europa.eu/service/data/EXR/D.USD.EUR.SP00.A?{q}&format=csvdata&lastNObservations=2")
    R["ecb"][nm] = {"status": r["status"], "head": t[:200].replace("\n", " | ")}
# --- Eurostat
r, t = T("eurostat_hicp_json", "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/prc_hicp_manr?lang=EN&geo=EA&coicop=CP00&sinceTimePeriod=2025-09&format=JSON")
j = json.loads(t)
R["eurostat"] = {"updated_field": j.get("updated"), "status_flags": j.get("status"), "n_values": len(j.get("value", {})), "extension_keys": list(j.get("extension", {}).keys()) if isinstance(j.get("extension"), dict) else None}
r, t = T("eurostat_sdmx_updatedAfter", "https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/data/prc_hicp_manr/M.RCH_A.CP00.EA?updatedAfter=2026-01-01T00:00:00Z&lastNObservations=2")
R["eurostat"]["sdmx_updatedAfter"] = {"status": r["status"], "head": t[:300].replace("\n", " ")}
# --- NY Fed
r, t = T("nyfed_sofr_250", "https://markets.newyorkfed.org/api/rates/secured/sofr/last/250.json")
j = json.loads(t)["refRates"]
R["nyfed"] = {"n": len(j), "fields": sorted(j[0].keys()), "revisionIndicator_values": sorted({x.get("revisionIndicator", "") for x in j}), "first_rows_with_revision": [x for x in j if x.get("revisionIndicator")][:3]}
r, t = T("nyfed_release_schedule", "https://markets.newyorkfed.org/api/rates/all/latest.json")
R["nyfed"]["all_latest_head"] = t[:300].replace("\n", " ")
# --- BoE
r = get("https://www.bankofengland.co.uk/boeapps/iadb/fromshowcolumns.asp?csv.x=yes&Datefrom=01/Jan/2026&Dateto=now&SeriesCodes=IUDBEDR&CSVF=TN&UsingCodes=Y&VPD=Y&VFD=N", name="boe_iadb_v2b")
R["boe"] = {"status": r["status"], "headers": {k: v for k, v in r["headers"].items() if k.lower() in ("last-modified", "date", "etag", "content-type")}, "head": r["body"][:120].decode()}
# --- BoC
r = get("https://www.bankofcanada.ca/valet/observations/CPI_TRIM/json?recent=3", name="boc_cpi_trim")
R["boc"] = {"headers": {k: v for k, v in r["headers"].items() if k.lower() in ("last-modified", "date", "etag", "content-type")}, "top_keys": list(json.loads(r["body"]).keys())}
# --- Treasury
r, t = T("ust_yield_xml_full", "https://home.treasury.gov/resource-center/data-chart-center/interest-rates/pages/xml?data=daily_treasury_yield_curve&field_tdr_date_value_month=202609")
R["treasury"] = {"feed_updated": re.findall(r"<updated>([^<]+)</updated>", t)[:2], "n_entries": t.count("<entry>"), "entry_updated_times": re.findall(r"<updated>([^<]+)</updated>", t)[1:4]}
r, t = T("ust_fiscaldata_meta", "https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/accounting/od/rates_of_exchange?page[size]=1&sort=-record_date")
R["treasury"]["fiscaldata_fields"] = list(json.loads(t)["data"][0].keys()) if r["status"] == 200 else t[:200]
# --- CFTC Socrata system fields
r, t = T("cftc_socrata_sys", "https://publicreporting.cftc.gov/resource/6dca-aqww.json?$select=report_date_as_yyyy_mm_dd,:updated_at,:created_at,:id&$limit=3&$order=report_date_as_yyyy_mm_dd%20DESC")
R["cftc"] = {"status": r["status"], "rows": json.loads(t)[:3] if r["status"] == 200 else t[:300]}
# --- World Bank
r, t = T("wb_sources", "https://api.worldbank.org/v2/sources?format=json&per_page=100")
src = json.loads(t)[1]
R["worldbank"] = {"n_sources": len(src), "archive_like": [(s["id"], s["name"], s.get("lastupdated")) for s in src if re.search("archive|vintage|revis", s["name"], re.I)],
                  "wdi_lastupdated": [s["lastupdated"] for s in src if s["id"] == "2"]}
r, t = T("wb_gdp_meta", "https://api.worldbank.org/v2/country/US/indicator/NY.GDP.MKTP.CD?format=json&per_page=2&date=2020:2025")
R["worldbank"]["meta_page"] = json.loads(t)[0]; R["worldbank"]["row_fields"] = list(json.loads(t)[1][0].keys())
# --- IMF
r, t = T("imf_api_dataflow", "https://api.imf.org/external/sdmx/2.1/dataflow")
R["imf"] = {"api_imf_org_dataflow_status": r["status"], "head": t[:200].replace("\n", " ")}
r, t = T("imf_weo_pages", "https://www.imf.org/en/Publications/WEO/weo-database/2026/April")
R["imf"]["weo_2026_april_page"] = {"status": r["status"], "bytes": r["bytes"]}
r, t = T("imf_datamapper_gdp_usa", "https://www.imf.org/external/datamapper/api/v1/NGDP_RPCH/USA")
R["imf"]["datamapper_keys"] = list(json.loads(t).keys()); R["imf"]["datamapper_vintage_param"] = False
# --- OECD
t = open(os.path.join(RAW, "oecd_dataflow_list"), encoding="utf8", errors="replace").read()
fl = re.findall(r'<structure:Dataflow id="([^"]+)"[^>]*>\s*<common:Name xml:lang="en">([^<]+)</common:Name>', t)
R["oecd"] = {"n_dataflows": len(fl), "revision_related": [(i, n) for i, n in fl if re.search(r"revis|original release|vintage|real.time", n, re.I)][:20]}
# --- Philly Fed
t = open(os.path.join(RAW, "philly_realtime_dataset"), encoding="utf8", errors="replace").read()
R["philly"] = {"data_links": sorted(set(re.findall(r'href="([^"]+\.(?:xlsx?|zip|csv|txt))"', t)))[:30]}
# --- EIA demo key
r, t = T("eia_demo", "https://api.eia.gov/v2/petroleum/stoc/wstk/data/?api_key=DEMO_KEY&frequency=weekly&data[0]=value&length=1")
R["eia"] = {"demo_key_status": r["status"], "head": t[:200].replace("\n", " ")}
# --- BEA api
r, t = T("bea_nokey_head", "https://apps.bea.gov/api/data?UserID=&method=GETDATASETLIST&ResultFormat=JSON")
R["bea"] = {"status": r["status"], "body": t[:300]}
dump(R, "other_sources.json")
print(json.dumps(R, indent=1, default=str)[:9000])
