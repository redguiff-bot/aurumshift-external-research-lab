"""Probe every priority source: reachability, auth need, data semantics headers. Stores raw + meta."""
from common import *
P = [
 ("fred_api_nokey", "https://api.stlouisfed.org/fred/series/observations?series_id=GDPC1&realtime_start=2009-01-30&realtime_end=2009-01-30&file_type=json"),
 ("fred_graph_csv", "https://fred.stlouisfed.org/graph/fredgraph.csv?id=GDPC1&cosd=2025-01-01"),
 ("alfred_graph_csv", "https://alfred.stlouisfed.org/graph/alfredgraph.csv?id=GDPC1&cosd=2008-07-01&coed=2009-01-01&vintage_date=2009-01-30"),
 ("alfred_downloaddata_page", "https://alfred.stlouisfed.org/series/downloaddata?seid=GDPC1"),
 ("fred_release_calendar_html", "https://fred.stlouisfed.org/releases/calendar"),
 ("bls_api_v2_nokey", "https://api.bls.gov/publicAPI/v2/timeseries/data/CES0000000001"),
 ("bls_api_v1", "https://api.bls.gov/publicAPI/v1/timeseries/data/CES0000000001"),
 ("bls_schedule_html", "https://www.bls.gov/schedule/news_release/cpi.htm"),
 ("bls_schedule_ics", "https://www.bls.gov/schedule/news_release/bls.ics"),
 ("bls_release_calendar_2026", "https://www.bls.gov/schedule/2026/home.htm"),
 ("bea_api_nokey", "https://apps.bea.gov/api/data?method=GETDATASETLIST&ResultFormat=JSON"),
 ("bea_schedule_html", "https://www.bea.gov/news/schedule"),
 ("bea_schedule_ics", "https://www.bea.gov/news/schedule/ical"),
 ("eia_api_nokey", "https://api.eia.gov/v2/petroleum/stoc/wstk/data/?frequency=weekly&data[0]=value&length=1"),
 ("eia_schedule_wpsr", "https://www.eia.gov/petroleum/supply/weekly/schedule.php"),
 ("nyfed_sofr", "https://markets.newyorkfed.org/api/rates/secured/sofr/last/3.json"),
 ("nyfed_sofr_search", "https://markets.newyorkfed.org/api/rates/secured/sofr/search.json?startDate=2026-09-01&endDate=2026-09-10"),
 ("ecb_sdmx_csv", "https://data-api.ecb.europa.eu/service/data/ICP/M.U2.N.000000.4.ANR?lastNObservations=3&format=csvdata"),
 ("ecb_sdmx_updatedAfter", "https://data-api.ecb.europa.eu/service/data/ICP/M.U2.N.000000.4.ANR?updatedAfter=2026-08-01T00:00:00%2B00:00&format=csvdata"),
 ("ecb_calendar", "https://www.ecb.europa.eu/press/calendars/statscal/html/index.en.html"),
 ("eurostat_hicp", "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/prc_hicp_manr?lang=EN&geo=EA&coicop=CP00&sinceTimePeriod=2026-01&format=JSON"),
 ("eurostat_release_cal", "https://ec.europa.eu/eurostat/news/release-calendar"),
 ("boe_iadb", "https://www.bankofengland.co.uk/boeapps/database/fromshowcolumns.asp?csv.x=yes&SeriesCodes=IUDBEDR&CSVF=TN&Datefrom=01/Jan/2026&Dateto=now"),
 ("boe_iadb_v2", "https://www.bankofengland.co.uk/boeapps/iadb/fromshowcolumns.asp?csv.x=yes&Datefrom=01/Jan/2026&Dateto=now&SeriesCodes=IUDBEDR&CSVF=TN&UsingCodes=Y&VPD=Y&VFD=N"),
 ("boc_valet_cpi", "https://www.bankofcanada.ca/valet/observations/CPI_TRIM/json?recent=3"),
 ("boc_valet_fx", "https://www.bankofcanada.ca/valet/observations/FXUSDCAD/json?recent=2"),
 ("boc_schedule", "https://www.bankofcanada.ca/valet/lists/series/json"),
 ("ust_fiscaldata", "https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v2/accounting/od/avg_interest_rates?page[size]=2&sort=-record_date"),
 ("ust_yield_xml", "https://home.treasury.gov/resource-center/data-chart-center/interest-rates/pages/xml?data=daily_treasury_yield_curve&field_tdr_date_value_month=202609"),
 ("cftc_cot_legacy", "https://publicreporting.cftc.gov/resource/6dca-aqww.json?$limit=2&$order=report_date_as_yyyy_mm_dd%20DESC"),
 ("worldbank_gdp", "https://api.worldbank.org/v2/country/US/indicator/NY.GDP.MKTP.CD?format=json&per_page=3"),
 ("worldbank_archive_sources", "https://api.worldbank.org/v2/sources?format=json&per_page=100"),
 ("imf_datamapper_weo", "https://www.imf.org/external/datamapper/api/v1/NGDP_RPCH/USA"),
 ("imf_datamapper_indicators", "https://www.imf.org/external/datamapper/api/v1/indicators"),
 ("oecd_sdmx_cli", "https://sdmx.oecd.org/public/rest/data/OECD.SDD.STES,DSD_STES@DF_CLI/USA.M.LI...AA...H?lastNObservations=2&format=csvfilewithlabels"),
 ("oecd_dataflow_list", "https://sdmx.oecd.org/public/rest/dataflow/all"),
 ("philly_realtime_dataset", "https://www.philadelphiafed.org/surveys-and-data/real-time-data-research/real-time-data-set-for-macroeconomists"),
 ("fed_g17_release_page", "https://www.federalreserve.gov/releases/g17/default.htm"),
 ("fed_g17_calendar", "https://www.federalreserve.gov/releases/g17/release_dates.htm"),
 ("census_econ_indicators_cal", "https://www.census.gov/economic-indicators/calendar-listview.html"),
 ("bls_ces_flat", "https://download.bls.gov/pub/time.series/ce/ce.data.0.AllCESSeries"),
]
res = []
for name, url in P:
    r = get(url, name=name, timeout=45)
    b = r["body"][:160].decode("utf8", "replace").replace("\n", " ")
    hd = {k: v for k, v in r["headers"].items() if k.lower() in ("last-modified","date","etag","content-type","age","x-request-id")}
    res.append({"name": name, "url": url, "status": r["status"], "bytes": r["bytes"], "receipt": r["receipt_time_utc"], "hdr": hd, "head": b})
    print(r["status"], r["bytes"], name, "|", b[:90])
dump(res, "probe_sources.json")
