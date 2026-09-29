"""Step 1: keyless reachability + semantics probe of every priority source."""
import json, re
from common import fetch, text, RES

P = []
def probe(src, name, url, **kw):
    r = fetch(url, name, **kw)
    body = text(r)
    P.append({"source": src, "name": name, "url": url, "status": r["status"],
              "bytes": len(r["body"]), "head": body[:300].replace("\n", " ")})
    return r, body

# --- FRED official API without key (expected: refused) + keyless csv endpoints
probe("FRED_API", "fred_api_nokey.json", "https://api.stlouisfed.org/fred/series/observations?series_id=GDPC1&file_type=json")
probe("FRED_API", "fred_api_badkey.json", "https://api.stlouisfed.org/fred/series/observations?series_id=GDPC1&file_type=json&api_key=" + "0"*32)
probe("FRED_CSV", "fredgraph_GDPC1_latest.csv", "https://fred.stlouisfed.org/graph/fredgraph.csv?id=GDPC1&cosd=2014-01-01&coed=2015-12-31")
probe("FRED_CSV", "fredgraph_GDPC1_vintageparam.csv", "https://fred.stlouisfed.org/graph/fredgraph.csv?id=GDPC1&cosd=2014-01-01&coed=2015-12-31&vintage_date=2015-01-01")
probe("FRED_CSV", "fredgraph_GDPC1_realtime.csv", "https://fred.stlouisfed.org/graph/fredgraph.csv?id=GDPC1&cosd=2014-01-01&coed=2015-12-31&realtime_start=2015-01-01&realtime_end=2015-01-01")
probe("ALFRED", "alfredgraph_GDPC1_20150101.csv", "https://alfred.stlouisfed.org/graph/alfredgraph.csv?id=GDPC1&cosd=2014-01-01&coed=2015-12-31&vintage_date=2015-01-01")
# --- BLS
probe("BLS", "bls_v2_nokey_CES.json", "https://api.bls.gov/publicAPI/v2/timeseries/data/CES0000000001?startyear=2025&endyear=2026")
probe("BLS", "bls_v2_nokey_CES_post.json", "https://api.bls.gov/publicAPI/v2/timeseries/data/", method="POST",
      data=json.dumps({"seriesid": ["CES0000000001", "CUUR0000SA0"], "startyear": "2025", "endyear": "2026", "calculations": True}),
      )
probe("BLS", "bls_schedule_ces.html", "https://www.bls.gov/schedule/news_release/ces.htm")
probe("BLS", "bls_schedule_ics.ics", "https://www.bls.gov/schedule/news_release/bls.ics")
# --- BEA
probe("BEA", "bea_api_nokey.json", "https://apps.bea.gov/api/data?method=GETDATASETLIST&ResultFormat=JSON")
probe("BEA", "bea_schedule.html", "https://www.bea.gov/news/schedule")
probe("BEA", "bea_schedule_ics.ics", "https://www.bea.gov/news/schedule/ical")
# --- EIA
probe("EIA", "eia_v2_nokey.json", "https://api.eia.gov/v2/petroleum/stoc/wstk/data/?frequency=weekly&data[0]=value&length=1")
probe("EIA", "eia_v2_demokey.json", "https://api.eia.gov/v2/petroleum/stoc/wstk/data/?api_key=DEMO_KEY&frequency=weekly&data[0]=value&length=1")
probe("EIA", "eia_schedule.html", "https://www.eia.gov/petroleum/supply/weekly/schedule.php")
# --- NY Fed
probe("NYFED", "nyfed_sofr_last5.json", "https://markets.newyorkfed.org/api/rates/secured/sofr/last/5.json")
probe("NYFED", "nyfed_sofr_search.json", "https://markets.newyorkfed.org/api/rates/secured/sofr/search.json?startDate=2026-09-01&endDate=2026-09-10")
# --- ECB
probe("ECB", "ecb_exr_last3.csv", "https://data-api.ecb.europa.eu/service/data/EXR/D.USD.EUR.SP00.A?lastNObservations=3&format=csvdata")
probe("ECB", "ecb_hicp_updatedafter.csv", "https://data-api.ecb.europa.eu/service/data/ICP/M.U2.N.000000.4.ANR?lastNObservations=3&format=csvdata&detail=full")
probe("ECB", "ecb_updatedafter.csv", "https://data-api.ecb.europa.eu/service/data/EXR/D.USD.EUR.SP00.A?updatedAfter=2026-09-25T00:00:00%2B00:00&format=csvdata")
# --- Eurostat
probe("EUROSTAT", "eurostat_une_rt_m.json", "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/une_rt_m?geo=EA20&s_adj=SA&age=TOTAL&sex=T&unit=PC_ACT&lastTimePeriod=3")
probe("EUROSTAT", "eurostat_prc_hicp_manr.json", "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/prc_hicp_manr?geo=EA&coicop=CP00&lastTimePeriod=3")
probe("EUROSTAT", "eurostat_calendar.html", "https://ec.europa.eu/eurostat/web/main/news/release-calendar")
# --- BoE
probe("BOE", "boe_iadb.csv", "https://www.bankofengland.co.uk/boeapps/database/fromshowcolumns.asp?csv.x=yes&SeriesCodes=IUDBEDR&CSVF=TN&UsingCodes=Y&VPD=Y&VFD=N&Datefrom=01/Sep/2026&Dateto=now")
probe("BOE", "boe_calendar.html", "https://www.bankofengland.co.uk/monetary-policy/upcoming-mpc-dates")
# --- BoC Valet
probe("BOC", "boc_fx.json", "https://www.bankofcanada.ca/valet/observations/FXUSDCAD/json?recent=3")
probe("BOC", "boc_lists.json", "https://www.bankofcanada.ca/valet/lists/series/json")
# --- US Treasury FiscalData
probe("TREASURY", "treasury_debt.json", "https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/accounting/od/debt_to_penny?page[size]=3&sort=-record_date")
probe("TREASURY", "treasury_yields.csv", "https://home.treasury.gov/resource-center/data-chart-center/interest-rates/daily-treasury-rates.csv/2026/all?type=daily_treasury_yield_curve&field_tdr_date_value=2026&page&_format=csv")
# --- CFTC
probe("CFTC", "cftc_legacy_last.json", "https://publicreporting.cftc.gov/resource/6dca-aqww.json?$limit=2&$order=report_date_as_yyyy_mm_dd%20DESC")
probe("CFTC", "cftc_meta.json", "https://publicreporting.cftc.gov/api/views/6dca-aqww.json")
probe("CFTC", "cftc_schedule.html", "https://www.cftc.gov/MarketReports/CommitmentsofTraders/ReleaseSchedule/index.htm")
# --- World Bank
probe("WORLDBANK", "wb_gdp.json", "https://api.worldbank.org/v2/country/US/indicator/NY.GDP.MKTP.CD?format=json&per_page=3")
probe("WORLDBANK", "wb_sources.json", "https://api.worldbank.org/v2/sources?format=json&per_page=100")
# --- IMF
probe("IMF", "imf_datamapper_ngdp.json", "https://www.imf.org/external/datamapper/api/v1/NGDP_RPCH/USA")
probe("IMF", "imf_weo_apr2024.ashx", "https://www.imf.org/-/media/Files/Publications/WEO/WEO-Database/2024/April/WEOApr2024all.ashx")
probe("IMF", "imf_weo_oct2025.ashx", "https://www.imf.org/-/media/Files/Publications/WEO/WEO-Database/2025/October/WEOOct2025all.ashx")
# --- OECD
probe("OECD", "oecd_dataflows.xml", "https://sdmx.oecd.org/public/rest/dataflow/all")
# --- FRED calendars
probe("FRED", "fred_release_calendar.html", "https://fred.stlouisfed.org/releases/calendar")
probe("ALFRED", "alfred_release_dates_50.txt", "https://alfred.stlouisfed.org/release/downloaddates?rid=50&ff=txt")

json.dump(P, open(RES + "/probe_sources.json", "w"), indent=1)
for p in P:
    print(f'{p["status"]!s:5} {p["bytes"]:>9}  {p["source"]:9} {p["name"]}')
