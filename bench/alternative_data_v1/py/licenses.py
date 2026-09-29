"""Fetch provider terms/licence/docs pages and record keyword evidence. A licence is only labelled DOCUMENTED (fetched) when
a keyword snippet was actually found on the fetched page; otherwise UNVERIFIED (never inferred)."""
import re, json, os, time, requests, html
from h import UA
OUT = os.path.join(os.path.dirname(__file__), "..", "results")
KW = r"(CC[ -]BY[^.]{0,30}|Creative Commons[^.]{0,60}|non-?commercial[^.]{0,80}|public domain[^.]{0,60}|free of charge[^.]{0,60}|open data[^.]{0,60}|attribution[^.]{0,80}|rate limit[^.]{0,80}|requests? per (?:second|minute|hour|day)[^.]{0,40}|no (?:copyright|restrictions)[^.]{0,60}|redistribut[^.]{0,80}|commercial use[^.]{0,80}|API key[^.]{0,60}|must not[^.]{0,80}|not permitted[^.]{0,80}|prohibited[^.]{0,80}|ODbL[^.]{0,40}|MIT license[^.]{0,30}|AGPL[^.]{0,40})"
PAGES = {
 "coinmetrics_community": ["https://coinmetrics.io/community-network-data/", "https://docs.coinmetrics.io/api/v4/"],
 "defillama": ["https://defillama.com/docs/api", "https://docs.llama.fi/"],
 "blockchain_com": ["https://www.blockchain.com/explorer/api", "https://www.blockchain.com/legal/terms"],
 "mempool_space": ["https://mempool.space/terms-of-service", "https://mempool.space/docs/faq"],
 "blockchair": ["https://blockchair.com/api/docs"],
 "gdelt": ["https://www.gdeltproject.org/about.html", "https://blog.gdeltproject.org/gdelt-2-0-our-global-world-in-realtime/"],
 "cftc": ["https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm", "https://www.cftc.gov/policy/websitedisclaimer/index.htm"],
 "treasury_fiscaldata": ["https://fiscaldata.treasury.gov/api-documentation/", "https://fiscaldata.treasury.gov/about-us/"],
 "nyfed": ["https://www.newyorkfed.org/termsofuse", "https://markets.newyorkfed.org/static/docs/markets-api.html"],
 "eia": ["https://www.eia.gov/about/copyrights_reuse.php", "https://www.eia.gov/opendata/documentation.php"],
 "noaa_cpc": ["https://www.weather.gov/disclaimer", "https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/cdus/degree_days/"],
 "nasa_power": ["https://power.larc.nasa.gov/docs/services/api/"],
 "open_meteo": ["https://open-meteo.com/en/terms", "https://open-meteo.com/en/license"],
 "wikimedia_pageviews": ["https://dumps.wikimedia.org/other/pageviews/readme.html", "https://doc.wikimedia.org/generated-data-platform/aqs/analytics-api/documentation/getting-started.html"],
 "alternative_me": ["https://alternative.me/crypto/api/"],
 "kalshi": ["https://docs.kalshi.com/welcome", "https://kalshi.com/regulatory/rulebook"],
 "polymarket": ["https://docs.polymarket.com/", "https://polymarket.com/tos"],
 "binance_vision": ["https://data.binance.vision/", "https://www.binance.com/en/terms"],
 "deribit": ["https://docs.deribit.com/", "https://www.deribit.com/pages/information/terms-of-service"],
 "okx": ["https://www.okx.com/docs-v5/en/"],
 "sec_edgar": ["https://www.sec.gov/os/webmaster-faq#developers", "https://www.sec.gov/privacy.htm#dissemination"],
 "imf_portwatch": ["https://portwatch.imf.org/pages/data-and-methodology", "https://www.imf.org/en/About/copyright-and-terms"],
 "stocktwits": ["https://stocktwits.com/terms"], "reddit": ["https://www.redditinc.com/policies/data-api-terms"],
 "gharchive": ["https://www.gharchive.org/"], "npm": ["https://docs.npmjs.com/policies/npm-open-source-terms"],
 "bbc_rss": ["https://www.bbc.co.uk/news/10628494"], "cointelegraph": ["https://cointelegraph.com/terms-and-privacy"],
 "coingecko_api": ["https://www.coingecko.com/en/api/documentation", "https://www.coingecko.com/en/api_terms"],
 "yahoo_finance": ["https://legal.yahoo.com/us/en/yahoo/terms/otos/index.html"],
 "fred": ["https://fred.stlouisfed.org/docs/api/terms_of_use.html"],
}
out = {}
for k, urls in PAGES.items():
    out[k] = []
    for u in urls:
        try:
            r = requests.get(u, headers=UA, timeout=30)
            t = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", r.text, flags=re.S | re.I); t = html.unescape(re.sub(r"<[^>]+>", " ", t)); t = re.sub(r"\s+", " ", t)
            sn = []
            for m in re.finditer(KW, t, flags=re.I):
                a = max(0, m.start() - 60); sn.append(t[a:m.end() + 60])
                if len(sn) >= 6: break
            out[k].append(dict(url=u, status=r.status_code, text_chars=len(t), snippets=sn))
        except Exception as e:
            out[k].append(dict(url=u, status=0, err=repr(e)[:120], snippets=[]))
        time.sleep(0.6)
    print(k, [(x["status"], len(x["snippets"])) for x in out[k]], flush=True)
json.dump(out, open(os.path.join(OUT, "license_evidence.json"), "w"), indent=1)
