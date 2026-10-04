"""Step 5: capture official licence/terms pages verbatim (no legal conclusions)."""
import re, html, json
from common import fetch, text, RES
U = {
 "FRED_API_terms": "https://fred.stlouisfed.org/docs/api/terms_of_use.html",
 "FRED_legal": "https://fred.stlouisfed.org/legal",
 "FRED_api_key": "https://fred.stlouisfed.org/docs/api/api_key.html",
 "BLS_api_signup": "https://www.bls.gov/developers/api_faqs.htm",
 "BLS_linking": "https://www.bls.gov/opub/linking-and-copyright-info.htm",
 "BEA_api": "https://apps.bea.gov/API/signup/",
 "BEA_terms": "https://www.bea.gov/about/policies-and-information/terms-of-use",
 "EIA_open": "https://www.eia.gov/opendata/",
 "EIA_reuse": "https://www.eia.gov/about/copyrights_reuse.php",
 "NYFED_terms": "https://www.newyorkfed.org/terms-of-use",
 "ECB_reuse": "https://www.ecb.europa.eu/services/using-our-site/disclaimer/html/index.en.html",
 "ECB_data_terms": "https://data.ecb.europa.eu/help/api/overview",
 "EUROSTAT_reuse": "https://ec.europa.eu/eurostat/about-us/policies/copyright",
 "BOE_terms": "https://www.bankofengland.co.uk/legal",
 "BOC_terms": "https://www.bankofcanada.ca/terms/",
 "TREASURY_fiscaldata": "https://fiscaldata.treasury.gov/api-documentation/",
 "CFTC_policy": "https://www.cftc.gov/PublicReporting/Web-Policy/index.htm",
 "WB_terms": "https://www.worldbank.org/en/about/legal/terms-of-use-for-datasets",
 "IMF_terms": "https://www.imf.org/en/about/copyright-and-terms",
 "OECD_terms": "https://www.oecd.org/en/about/terms-conditions.html",
}
KW = re.compile(r"(redistribut|copyright|public domain|licen[cs]e|CC BY|attribution|commercial|cache|store|storing|rate limit|requests per|terms of use|api key|registration|register|open data)", re.I)
out = {}
for k, u in U.items():
    r = fetch(u, f"licence/{k}.html")
    t = text(r)
    t = re.sub(r"<script.*?</script>|<style.*?</style>", " ", t, flags=re.S)
    t = html.unescape(re.sub(r"<[^>]+>", " ", t)); t = re.sub(r"\s+", " ", t)
    sents = [s.strip() for s in re.split(r"(?<=[.!?])\s+", t) if KW.search(s) and 40 < len(s) < 400]
    out[k] = {"url": u, "status": r["status"], "chars": len(t), "snippets": sents[:8]}
    print(k, r["status"], len(t))
json.dump(out, open(RES + "/licence_snippets.json", "w"), indent=1)
