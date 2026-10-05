"""laneI — L2 calendar snapshot (ForexFactory JSON+XML, BEA ICS/JSON, Fed/ECB/BoE/BoJ pages, BLS ICS).
Usage: python fetch_calendars.py <snapshot_tag>
Writes raw/<tag>_<name>.<ext> and raw/<tag>_<name>.meta.json (receipt_time_utc, status, headers, sha256, latency).
Volumes modestes : 1 requête par source et par snapshot.
"""
import hashlib, json, sys, time, datetime as dt, pathlib
import requests

OUT = pathlib.Path(__file__).parent / "raw"
OUT.mkdir(exist_ok=True)
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) research-lab/0.1 (contact: operator)"}
SOURCES = {
    "ff_json": ("https://nfs.faireconomy.media/ff_calendar_thisweek.json", "json"),
    "ff_xml": ("https://nfs.faireconomy.media/ff_calendar_thisweek.xml", "xml"),
    "bea_ics": ("https://www.bea.gov/news/schedule/ics/online-calendar-subscription.ics", "ics"),
    "bea_json": ("https://apps.bea.gov/API/signup/release_dates.json", "json"),
    "bls_ics": ("https://www.bls.gov/schedule/news_release/bls.ics", "ics"),
    "fed_fomc": ("https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm", "html"),
    "fed_press_rss": ("https://www.federalreserve.gov/feeds/press_all.xml", "xml"),
    "ecb_mp": ("https://www.ecb.europa.eu/press/calendars/mgcgc/html/index.en.html", "html"),
    "boe_mpc": ("https://www.bankofengland.co.uk/monetary-policy/upcoming-mpc-dates", "html"),
    "boj_mpm": ("https://www.boj.or.jp/en/mopo/mpmsche_minu/index.htm", "html"),
}


def main(tag: str):
    only = sys.argv[2].split(",") if len(sys.argv) > 2 else None
    for name, (url, ext) in SOURCES.items():
        if only and name not in only:
            continue
        t0 = time.time()
        receipt = dt.datetime.now(dt.timezone.utc).isoformat()
        try:
            r = requests.get(url, headers=UA, timeout=30)
            body, status, hdr = r.content, r.status_code, dict(r.headers)
        except Exception as e:  # noqa
            body, status, hdr = repr(e).encode(), None, {}
        lat = round((time.time() - t0) * 1000)
        (OUT / f"{tag}_{name}.{ext}").write_bytes(body)
        meta = dict(name=name, url=url, receipt_time_utc=receipt, status=status, latency_ms=lat,
                    bytes=len(body), sha256=hashlib.sha256(body).hexdigest(),
                    headers={k: v for k, v in hdr.items() if k.lower() in (
                        "date", "last-modified", "etag", "cache-control", "age", "expires", "content-type")})
        (OUT / f"{tag}_{name}.meta.json").write_text(json.dumps(meta, indent=1))
        print(status, lat, "ms", len(body), name)


if __name__ == "__main__":
    main(sys.argv[1])
