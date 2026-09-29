"""Revision/re-fetch test: fetch same historical window twice, gap >= 150 s; compare all rows except the last 2 days. Also stamp what a PIT capture would record."""
import time, pandas as pd, numpy as np
from lib import *
def bc():
    o = get("https://api.blockchain.info/charts/n-transactions", {"timespan": "60days", "format": "json", "sampled": "false"}); v = pd.DataFrame(o["body"]["values"]).set_index("x").y; return v, o
def llama():
    o = get("https://stablecoins.llama.fi/stablecoincharts/all"); return pd.Series({int(x["date"]): x["totalCirculatingUSD"]["peggedUSD"] for x in o["body"]}), o
def cftc():
    o = get("https://publicreporting.cftc.gov/resource/gpe5-46if.json", {"$where": "market_and_exchange_names like 'BITCOIN - CHICAGO MERCANTILE%'", "$limit": 200, "$order": "report_date_as_yyyy_mm_dd"}); return pd.Series({r["report_date_as_yyyy_mm_dd"]: float(r["lev_money_positions_short"]) for r in o["body"]}), o
def fng():
    o = get("https://api.alternative.me/fng/", {"limit": 90}); return pd.Series({int(x["timestamp"]): float(x["value"]) for x in o["body"]["data"]}), o
def tga():
    o = get("https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/accounting/dts/operating_cash_balance", {"filter": "account_type:eq:Treasury General Account (TGA) Closing Balance", "page[size]": 120, "sort": "-record_date"}); return pd.Series({r["record_date"]: r["close_today_bal"] for r in o["body"]["data"]}), o
def hn():
    import time as t; a = int(t.time()) - 30 * 86400
    o = get("https://hn.algolia.com/api/v1/search_by_date", {"query": "bitcoin", "tags": "story", "numericFilters": f"created_at_i>={a-86400*3},created_at_i<{a}", "hitsPerPage": 0}); return pd.Series({0: o["body"]["nbHits"]}), o
tests = dict(blockchain_info_ntx=bc, defillama_stable=llama, cftc_btc_lev_short=cftc, fear_greed=fng, treasury_tga=tga, hn_algolia_count=hn)
A = {k: f() for k, f in tests.items()}; t0 = time.time(); time.sleep(170)
res = {}
for k, f in tests.items():
    b, o2 = f(); a, o1 = A[k]; common = a.index.intersection(b.index)
    common = common[:-2] if len(common) > 4 else common
    x = pd.to_numeric(a.loc[common], errors="coerce"); y = pd.to_numeric(b.loc[common], errors="coerce"); diff = (x != y) & ~(x.isna() & y.isna())
    res[k] = dict(rows_compared=int(len(common)), rows_changed=int(diff.sum()), gap_s=round(time.time() - t0 + 170 * 0, 0), last_modified_t0=o1["hdr"].get("last-modified"), last_modified_t1=o2["hdr"].get("last-modified"))
    print(k, res[k], flush=True)
jdump(res, "revision_test.json")
