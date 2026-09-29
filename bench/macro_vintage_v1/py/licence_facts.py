import re
from common import *
U = {
 "fred_api_terms": ("https://fred.stlouisfed.org/docs/api/terms_of_use.html", r"(commercial|redistribut|copyright|cache|store|third.party|API key)"),
 "fred_legal": ("https://fred.stlouisfed.org/legal/", r"(copyright|third.party|permission|commercial|redistribut)"),
 "bls_copyright": ("https://www.bls.gov/opub/copyright-information.htm", r"(public domain|copyright|permission|cite|citation)"),
 "bls_api_signature": ("https://www.bls.gov/developers/api_signature_v2.htm", r"(daily|queries|registration|threshold|years|series per query)"),
 "bea_api_terms": ("https://apps.bea.gov/API/signup/", r"(terms|key|limit|per minute|100)"),
 "eia_reuse": ("https://www.eia.gov/about/copyrights_reuse.php", r"(public domain|copyright|cite|permission|reuse)"),
 "eia_api_docs": ("https://www.eia.gov/opendata/documentation.php", r"(api key|register|rate|5000)"),
 "nyfed_terms": ("https://www.newyorkfed.org/terms-of-use", r"(personal|commercial|redistribut|copyright|permission)"),
 "ecb_copyright": ("https://www.ecb.europa.eu/services/disclaimer/html/index.en.html", r"(reproduc|copyright|source|commercial|permitted)"),
 "eurostat_copyright": ("https://ec.europa.eu/eurostat/about-us/policies/copyright", r"(reuse|reproduc|CC BY|licen|free of charge|source)"),
 "boe_terms": ("https://www.bankofengland.co.uk/legal", r"(copyright|Open Government|licen|reproduc|commercial)"),
 "boc_terms": ("https://www.bankofcanada.ca/terms/", r"(non-commercial|commercial|reproduc|permission|licen|Valet)"),
 "ust_fiscaldata_terms": ("https://fiscaldata.treasury.gov/api-documentation/", r"(public domain|no restrictions|key|rate limit|licen|free)"),
 "cftc_terms": ("https://www.cftc.gov/PublicReporting/index.htm", r"(public|copyright|reuse|api)"),
 "wb_terms": ("https://www.worldbank.org/en/about/legal/terms-of-use-for-datasets", r"(CC BY|Creative Commons|licen|attribution|commercial)"),
 "imf_terms": ("https://www.imf.org/en/About/copyright-and-terms", r"(non-commercial|commercial|reproduc|permission|licen|attribution)"),
 "oecd_terms": ("https://www.oecd.org/en/about/terms-conditions.html", r"(CC BY|licen|commercial|reproduc|attribution|redistribut)"),
 "philly_rtds": ("https://www.philadelphiafed.org/surveys-and-data/real-time-data-research/real-time-data-set-for-macroeconomists", r"(cite|citation|copyright|permission|licen|use)"),
}
res = {}
for k, (u, pat) in U.items():
    r = get(u, name=f"lic_{k}", timeout=45)
    t = re.sub(r"\s+", " ", re.sub(r"<script.*?</script>|<style.*?</style>|<[^>]+>", " ", r["body"].decode("utf8", "replace"), flags=re.S))
    sents = [s.strip() for s in re.split(r"(?<=[.!?]) ", t) if re.search(pat, s, re.I) and 40 < len(s) < 400]
    res[k] = {"url": u, "status": r["status"], "receipt": r["receipt_time_utc"], "quotes": sents[:4]}
    print(k, r["status"], len(sents))
dump(res, "licence_facts.json")
