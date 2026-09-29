import json,os,collections,statistics as st
from datetime import datetime,timezone
import catalog
R="../results/";OUT="../../../reports/005_data_feed_resilience/"
os.makedirs(OUT,exist_ok=True)
L=json.load(open(R+"latency_ratelimit.json"));D=json.load(open(R+"derivs_analysis.json"));BA=json.load(open(R+"bars_analysis_t2.json"))
CD=json.load(open(R+"consensus_dev.json"));LAG=json.load(open(R+"lag_test_vs_kraken.json"));DOC=json.load(open(R+"docs_facts.json"))
WS=json.load(open(R+"ws_sample.json"));FX=json.load(open(R+"fxgold_bulk.json"));MAC=json.load(open(R+"macro_tests.json"))
S1=json.load(open(R+"sweep1.json"));S2=json.load(open(R+"sweep2.json"))
C=catalog.C
for s in C:
    if s["id"] in("goldapi","swissquote","openerapi"): s["pit"]="PIT_UNSUITABLE"
by={s["id"]:s for s in C}
def w(n,t): open(OUT+n,"w").write(t.rstrip()+"\n")
def q(d,k,n=170):
    if not d: return "NOT_FOUND"
    x=d.get(k)
    if isinstance(x,dict): 
        s=(x.get("quote") or "NOT_FOUND").replace("\n"," ").replace("|","/")
        return (s[:n]+("…" if len(s)>n else ""))
    return "NOT_FOUND"
def docurl(d,k):
    if not d: return ""
    x=d.get(k);return x.get("url","") if isinstance(x,dict) else ""
yes=lambda s:s["exe"]=="Y"
# ---------- counts
disc=len(C);exe=sum(1 for s in C if s["exe"]=="Y");part=sum(1 for s in C if s["exe"]=="PART");blk=sum(1 for s in C if s["exe"]=="BLK")
cost=collections.Counter(s["cost"] for s in C);cost_e=collections.Counter(s["cost"] for s in C if yes(s))
pit=collections.Counter(s["pit"] for s in C);pit_e=collections.Counter(s["pit"] for s in C if yes(s))
ver=collections.Counter(s["verdict"] for s in C)
good=lambda s:yes(s) and s["verdict"] in("ADOPT_REFERENCE","ADAPT_CANDIDATE")
def cnt(*tags): return sorted({s["name"] for s in C if good(s) and any(t in s["classes"] for t in tags)})
spot=cnt("SPOT");deriv=cnt("FUND","OI","LIQ","OPT","BASIS");fxc=cnt("FX");comm=cnt("COMM","GOLD");mac=cnt("MACRO")
gold=cnt("GOLD");cal=cnt("CAL")
fb=sorted({s["name"] for s in C if yes(s) and any(r in("PRIMARY","SECONDARY","FALLBACK") for r in s["roles"].values())})
FINAL=f"""SOURCES_DISCOVERED={disc}
SOURCES_EXECUTED={exe} (data path executed, HTTP 200 and parsed); {part} reachable-but-data-path-not-completed (FRED); {blk} blocked from the test egress; {disc-exe-part-blk} not executed (key/account/own error/deliberate)
FREE_PUBLIC_SOURCES={cost['FREE_UNAUTHENTICATED']} classified FREE_UNAUTHENTICATED ({cost_e['FREE_UNAUTHENTICATED']} of them executed)
FREE_ACCOUNT_SOURCES={cost['FREE_WITH_ACCOUNT']} classified FREE_WITH_ACCOUNT (0 executed with an account; +{cost['FREE_TIER']} FREE_TIER executed with a shared demo key; {cost['UNKNOWN']} UNKNOWN; {cost['PAID_ONLY']} PAID_ONLY)

CRYPTO_SPOT_CANDIDATES={len(spot)}
DERIVATIVES_CANDIDATES={len(deriv)}
FX_CANDIDATES={len(fxc)}
COMMODITY_CANDIDATES={len(comm)} (incl. gold proxies; strictly energy/base-metal price feeds: 1, Yahoo unofficial - see 04)
MACRO_CANDIDATES={len(mac)}

PIT_NATIVE_COUNT=0 observed (+1 DOCUMENTED_CLAIM only: ALFRED, execution blocked)
PIT_ADAPTABLE_COUNT={pit['PIT_ADAPTABLE']} classified ({pit_e['PIT_ADAPTABLE']} executed)

FALLBACK_CAPABLE_COUNT={len(fb)} (executed sources holding a PRIMARY/SECONDARY/FALLBACK role in at least one gap class)

ANY_DROP_IN_SOURCE=NO
ANY_SCIENTIFIC_INVALIDATION=NO

FINAL_VERDICT=MULTIPLE_DATA_SOURCE_CANDIDATES_SUPPORTED"""
open("../results/final_block.txt","w").write(FINAL+"\n")
json.dump({"counts":dict(discovered=disc,executed=exe,part=part,blocked=blk,cost=cost,pit=pit,verdict=ver),"lists":dict(spot=spot,deriv=deriv,fx=fxc,comm=comm,mac=mac,fallback=fb)},open("../results/counts.json","w"),indent=1)
# ---------- 00
w("00_EXECUTIVE_SUMMARY.md",f"""# 00 — Executive summary

Mission: `AURUMSHIFT_EXTERNAL_DATA_FEED_RESILIENCE_AND_FREE_SOURCE_DISCOVERY_V1` — external research only; no private AurumShift code read; no integration proposed.
Run date (test-egress clock): 2026-09-29 (UTC). Evidence labels follow `claude.md`: PROVEN / OBSERVED / DOCUMENTED_CLAIM / INFERENCE / UNKNOWN.

## What was actually done
* {disc} candidate sources catalogued; **{exe} executed end-to-end** (real HTTP/WS calls, parsed, stored in `bench/data_feeds_v1/`), {part} partially, {blk} blocked by the test egress, the rest not executed (key / account / own query error / deliberate).
* 18 venue×instrument 1-minute BTC series fetched 3× (t0, +78 s, +362 s); 240-minute window, pairwise + consensus comparison, lag test, re-fetch revision test.
* 14 REST endpoints × 10 sequential calls (latency); 14 WebSocket endpoints × 20 s bounded live samples.
* Derivatives: funding on 9 venues, OI on 8, liquidations on 4 (REST) + 2 (WS), options (Deribit vs OKX, 690 common instruments), dated-futures basis.
* Bulk: Binance Vision daily/monthly files incl. checksum verification and API-vs-bulk equality; Dukascopy tick decode.
* Macro/FX/gold/commodity: 20+ official/quasi-official endpoints; docs/ToS facts gathered separately (`bench/data_feeds_v1/results/docs_facts.json`, 43/47 providers with at least one verbatim quote; the rest `NOT_FOUND`).

## Headline findings (all OBSERVED unless stated)
1. **Keyless crypto coverage is broad and clean.** All 17 crypto bar series that returned data had 0 duplicates, 0 unaligned timestamps and 0 revisions over a 6-minute re-fetch; 16/17 had 0 missing minutes (Bitget: 1), although 4 venues reach that by gap-filling flat zero-volume bars; timestamp label agreement across all venues is exact (best cross-correlation lag = 0 for every venue, `results/lag_test_vs_kraken.json`).
2. **No two venues agree on OHLC.** Exact 4-field OHLC match between any two venues: 0 of 233 common minutes for every pair. Median close difference is 0.3–1.0 bps between the best pairs (Gate/OKX/Binance mirror; Kraken/Coinbase/Bitstamp), 3–4.7 bps across USD-vs-USDT quote currencies, and 13 bps for Bitfinex vs its USD peers (cause UNKNOWN). Volume is not comparable across venues (units differ: base, quote, contracts, USD).
3. **Derivatives gap classes have keyless candidates.** Funding (9 venues), OI snapshot (8), OI history (OKX 8 h @5 min; Gate ~8 h; Binance Vision metrics 5 min daily files), liquidations (OKX REST/WS, Gate, Bitfinex, BitMEX WS), basis (Deribit dated futures; OKX listing), options IV/skew (Deribit 944 + OKX 1272 BTC instruments, 690 common; median IV difference {D['opt_iv_diff_pts']['median']:.2f} vol pts, |median| {D['opt_iv_diff_pts']['abs_median']:.2f}, p05 {D['opt_iv_diff_pts']['p05']:.2f}, p95 {D['opt_iv_diff_pts']['p95']:.2f}; DVOL).
4. **Funding and OI are venue-specific quantities, not one series seen through several windows.** At the 15 shared 8-hour boundaries OKX, Gate, Bitget, KuCoin disagree in sign or magnitude in most rows; OI units differ by an order of magnitude (BTC, USD, contracts×multiplier). Cross-venue use needs explicit normalisation.
5. **PIT posture is weak across the board.** No executed source exposes a provider revision signal *and* a receipt timestamp; Deribit responses carry server `usIn/usOut` microsecond stamps (receipt-side, usable), Binance Vision files carry `Last-Modified`/ETag/CHECKSUM, NY Fed rows carry `revisionIndicator`, ECB SDMX has `OBS_STATUS`/`updatedAfter`. Everything else requires the consumer to stamp receipt time itself (PIT_ADAPTABLE at best).
6. **Hazards found that would silently corrupt a pipeline:** Binance Vision *spot* files change timestamp unit from ms to µs between the 2024-12 and 2025-01 monthly files; Coinbase candle column order differs from every other venue; Kraken returns the forming bar unflagged; gap-filled zero-volume flat bars (Gemini 23/240 flat, Binance.US 174/240, dYdX 202/240) make "0 missing" misleading; OKX REST liquidation endpoint works but is absent from current docs.
7. **Coverage the test egress could not reach:** Binance main API (HTTP 451), Bybit (403), MEXC futures (403), FRED/ALFRED (connection closed by proxy), Stooq, GDELT, IMF, BLS ICS. These are *egress* outcomes, not provider verdicts; the most valuable untested items are FRED/ALFRED (PIT-native macro) and Binance/Bybit derivatives.

## Adjudication counts
ADOPT_REFERENCE {ver['ADOPT_REFERENCE']} · ADAPT_CANDIDATE {ver['ADAPT_CANDIDATE']} · PARK {ver['PARK']} · REJECT {ver['REJECT']} (no synthetic ranking; see `11_ADJUDICATION.md`).

## Final block
```
{FINAL}
```
""")
# ---------- 01 landscape
def card(s):
    d=DOC.get(s["docs"]) if s["docs"] else None
    lic=q(d,"license");rl=q(d,"rate_limit");rev=q(d,"revision");hist=q(d,"history")
    tsq=q(d,"timestamp")
    return f"""#### {s['name']}  `{s['id']}`
* **Asset/gap classes:** {', '.join(s['classes'])} · **cost:** {s['cost']} · **executed:** {s['exe']}
* **Endpoint:** {s['endpoint'] or 'UNKNOWN'}
* **Auth:** {s['auth'] or 'UNKNOWN'}
* **Free tier / public access:** {s['cost']}
* **Rate limit (DOCUMENTED_CLAIM):** {rl}
* **Historical depth (OBSERVED):** {s['hist'] or 'UNKNOWN'}  ·  docs: {hist}
* **Streaming:** {s['stream'] or 'UNKNOWN'}
* **Update frequency:** {s['freq'] or 'UNKNOWN'}
* **Timestamp semantics:** {s['ts'] or 'UNKNOWN'}  ·  docs: {tsq}
* **Provider IDs:** {s['ids'] or 'UNKNOWN'}
* **Revision behaviour:** {s['rev'] or 'UNKNOWN'}  ·  docs: {rev}
* **Finality semantics:** {s['fin'] or 'UNKNOWN'}
* **Licence / ToS (DOCUMENTED_CLAIM):** {lic}
* **Commercial use / redistribution:** {'see licence quote; NOT verified beyond quote' if lic!='NOT_FOUND' else 'UNKNOWN (no official text retrieved)'}
* **Note:** {s['note'] or '-'}
"""
sec=collections.OrderedDict([("Crypto exchanges & bulk",["okx","kraken","kraken_fut","coinbase","bitstamp","bitfinex","kucoin","gemini","gate","bitget","mexc","htx","deribit","bitmex","hyperliquid","dydx","binance_api","binance_vision","binance_us","binance_main","bybit","coingecko","cryptocompare","coinalyze","alt_fng","onchain"]),("FX / gold",["ecb","frankfurter","boe","boc","openerapi","fawaz","yahoo","dukascopy","goldapi","swissquote","tokgold","lbma","tradingeconomics","exchangerate_host","alphavantage","twelvedata","polygon","finnhub","fmp","oanda","stooq","metals_live"]),("Commodities / macro",["fred","alfred","eia","bls","treasury_yc","treasury_fd","nyfed","cftc","worldbank","eurostat","snb","bea","imf","oecd"]),("Calendar / news",["faireconomy","fomc","blsics","gdelt","tipranks","cryptopanic"])])
t="# 01 — Source landscape\n\nSource cards. `docs:` text is a short quote captured from official pages (`results/docs_facts.json`; NOT_FOUND where the page was unreachable/JS-only). Nothing is inferred: empty means UNKNOWN. Cards for sources that were **not executed** carry only what the probe response itself showed.\n\n"
t+="| Group | Discovered | Executed (HTTP 200 + parsed) |\n|---|---|---|\n"
for g,ids in sec.items(): t+=f"| {g} | {len(ids)} | {sum(1 for i in ids if by[i]['exe']=='Y')} |\n"
t+=f"| **Total** | **{disc}** | **{exe}** |\n\n"
for g,ids in sec.items():
    t+=f"### {g}\n\n"+"\n".join(card(by[i]) for i in ids)+"\n"
w("01_SOURCE_LANDSCAPE.md",t)
# ---------- 02 spot
pv=BA["per_venue"]
def row(v,lab):
    r=pv[v];c=CD.get(v,{})
    return f"| {lab} | {r['in_window']}/{r['expected']} | {r['missing']} | {r['dupes']} | {r['order']} | {r['zero_vol_bars']} | {r['flat_bars']} | {r['revised_ohlc_bars']}/{r['revised_vol_bars']} | {c.get('signed_med_bps','-')} | {c.get('abs_med_bps','-')} | {c.get('abs_p95_bps','-')} | {LAG[v]['corr_by_lag'].get('0','-') if v in LAG else '-'} |"
names={"okx_spot_BTCUSDT":"OKX BTC-USDT","kucoin_BTC-USDT":"KuCoin BTC-USDT","gate_BTC_USDT":"Gate BTC_USDT","bitget_BTCUSDT":"Bitget BTCUSDT","mexc_BTCUSDT":"MEXC BTCUSDT","htx_btcusdt":"HTX btcusdt","binance_dataapi_BTCUSDT":"Binance mirror BTCUSDT","kraken_spot_XBTUSD":"Kraken XBTUSD","coinbase_BTC-USD":"Coinbase BTC-USD","bitstamp_btcusd":"Bitstamp btcusd","bitfinex_tBTCUSD":"Bitfinex tBTCUSD","gemini_btcusd":"Gemini btcusd","binance_us_BTCUSDT":"Binance.US BTCUSDT","okx_swap_BTC-USDT-SWAP":"OKX BTC-USDT-SWAP (perp)","hyperliquid_perp_BTC":"Hyperliquid BTC (perp)","deribit_perp_BTC-PERPETUAL":"Deribit BTC-PERPETUAL","dydx_perp_BTC-USD":"dYdX BTC-USD (perp)","bitmex_XBTUSD":"BitMEX XBTUSD"}
w("02_CRYPTO_SPOT.md",f"""# 02 — Crypto spot (and perp) 1-minute bars

Window: 240 closed minutes ending {datetime.fromtimestamp(BA['window']['end']/1000,timezone.utc):%Y-%m-%d %H:%MZ} (t0 fetched {datetime.fromtimestamp(BA['window']['t0_fetch']/1000,timezone.utc):%H:%M:%SZ}; re-fetch t2 {(BA['window']['t1_fetch']-BA['window']['t0_fetch'])/1000:.0f} s later). Raw normalised bars: `bench/data_feeds_v1/raw/bars_t0.json|t1|t2`; code: `py/bars_lib.py`, `py/run_bars.py`, `py/analyze_bars.py`, `py/consensus.py`, `py/lagtest.py`.

Columns: in-window bars / expected · missing · duplicates · native order · zero-volume bars · flat (O=H=L=C) bars · bars whose OHLC / volume changed between t0 and t2 · signed median close deviation and |median|, |p95| in bps versus the **median of the other venues in the same group** (a consensus for comparison, *not* ground truth) · return correlation with the Kraken series at lag 0.

| Venue | bars | miss | dup | order | zero-vol | flat | revised (OHLC/vol) | dev bps (signed) | |dev| med | |dev| p95 | ret corr@0 |
|---|---|---|---|---|---|---|---|---|---|---|---|
"""+"\n".join(row(v,n) for v,n in names.items() if v in pv)+f"""

Groups for consensus: USD spot (Kraken, Coinbase, Bitstamp, Bitfinex, Gemini), USDT spot (OKX, KuCoin, Gate, Bitget, MEXC, HTX, Binance mirror), perp (OKX, Hyperliquid, Deribit, dYdX). Binance.US is not in a consensus group (too thin). BitMEX XBTUSD returned 0 rows: instrument state `Settled` (OBSERVED in `/instrument`).

## Observations
* **Missing intervals.** Only Bitget shows a real gap: minute 2026-09-29T09:02Z absent in both fetches while OKX, MEXC, Kraken carry trades in it (OBSERVED). All "0 missing" for Gemini, Binance.US, dYdX, HTX are gap-filled flat zero-volume bars, not observed trades.
* **Late arrivals / revisions.** 0 bars appeared late and 0 bars were revised for any venue between t0 and t2 (6 min). The bar closed <60 s before t0 was identical at t2 for every venue. This does not exclude revisions on longer horizons (NOT TESTED).
* **Forming bar.** Kraken returned 3 rows at/after the window end (forming bar included, unflagged). OKX and Gate flag closed bars (`confirm`, closed-flag); other venues do not.
* **Pagination/limits.** OKX 100 rows/call (3 calls for 240 bars) and Coinbase 300/call; Bitstamp ignored the start/end window in one call and returned 1000 rows; Gemini returns a fixed ~1440-bar block without range parameters.
* **Quote-currency effect.** USDT-quoted venues sit ≈3–5 bps from USD venues in the same minute; that is a quote-asset basis, not a data fault.
* **Outliers.** Bitfinex ≈ +13 bps above USD peers (persisting through 3 fetches, timing ruled out by lag test); HTX ≈ −4.5 bps within its USDT group; MEXC −1.3 bps. Causes UNKNOWN.

## Bulk historical
Binance Vision spot BTCUSDT 1m daily file 2026-09-26: 1440 rows, 0 duplicates, 0 missing, SHA-256 matches published `.CHECKSUM` (PROVEN), and 1440/1440 bars identical to `data-api.binance.vision` klines for the same day after unit conversion. **Timestamp unit hazard:** 2024-12 monthly file = 13-digit ms, 2025-01 monthly = 16-digit µs, 2026 daily = 16-digit µs (OBSERVED). Futures um klines remain ms. Oldest spot file observed: 2017-08 (21,360 rows).

## MTF bars
Every source above serves 1m natively; coarser bars are also native on the exchange APIs (OKX `bar=`, Kraken `interval=`, Coinbase `granularity`, Hyperliquid `interval`, Binance klines). Only 1m equivalence and 1h/1d samples were executed (1h on the gold-proxy venues; daily on FX). Consistency of native MTF bars versus resampled 1m bars: NOT TESTED.
""")
# ---------- 03 derivatives
fs=D["funding_summary"];oi=D["oi_snapshot"]
fr="\n".join(f"| {k} | {v['n']} | {v['gap_minutes_set']} | {datetime.fromtimestamp(v['first']/1000,timezone.utc):%m-%d %H:%M} → {datetime.fromtimestamp(v['last']/1000,timezone.utc):%m-%d %H:%M} |" for k,v in fs.items() if v["n"])
fc=D["funding_8h_compare"]
def f8(x): return "-" if x is None else f"{x*1e4:+.2f}"
fr8="\n".join(f"| {datetime.fromtimestamp(r['t']/1000,timezone.utc):%m-%d %H}Z | {f8(r['okx'])} | {f8(r['gate'])} | {f8(r['bitget'])} | {f8(r['kucoin'])} | {f8(r['hl_sum8h'])} |" for r in fc)
sign_dis=sum(1 for r in fc if len({(x>0) for x in (r['okx'],r['gate'],r['bitget'],r['kucoin']) if x not in (None,0)})>1)
btc=84340.0
oi_rows=[("OKX BTC-USDT-SWAP","oiCcy","BTC",oi["okx_BTC-USDT-SWAP_btc"]),("Bitget BTCUSDT","size","BTC",oi["bitget_BTCUSDT_btc"]),("Hyperliquid BTC","openInterest","BTC",oi["hyperliquid_btc"]),("Deribit BTC-PERPETUAL","open_interest","USD",oi["deribit_perp_usd"]),("Gate BTC_USDT","position_size × quanto 0.0001","contracts→BTC",int(oi["gate_position_size_contracts"])*float(oi["gate_quanto_multiplier"])),("Kraken Futures PF_XBTUSD","openInterest","unit UNKNOWN",oi["krakenfut_PF_XBTUSD"]),("dYdX BTC-USD","openInterest","BTC (documented unit not verified)",float(oi["dydx_btc"]))]
def toBTC(u,v): return v/btc if u=="USD" else v
oit="\n".join(f"| {n} | {f} | {u} | {v:,.1f} | {toBTC(u,v):,.0f} |" for n,f,u,v in oi_rows)
fut=D["deribit_futures"];idx=[x["est_delivery"] for x in fut][0]
def dte(n):
    m={"JAN":1,"FEB":2,"MAR":3,"APR":4,"MAY":5,"JUN":6,"JUL":7,"AUG":8,"SEP":9,"OCT":10,"NOV":11,"DEC":12}
    import re
    x=re.match(r"BTC-(\d+)([A-Z]{3})(\d+)",n)
    if not x: return None
    d=datetime(2000+int(x.group(3)),m[x.group(2)],int(x.group(1)),8,tzinfo=timezone.utc);return (d-datetime(2026,9,29,13,tzinfo=timezone.utc)).total_seconds()/86400
bt="| Instrument | mark | index (est. delivery) | days to expiry | basis % | annualised % (simple) | OI (USD) |\n|---|---|---|---|---|---|---|\n"
for x in sorted(fut,key=lambda x:(dte(x["n"]) or 0)):
    d=dte(x["n"])
    if d and d>0.5: bt+=f"| {x['n']} | {x['mark']:,.2f} | {x['est_delivery']:,.2f} | {d:.1f} | {(x['mark']/x['est_delivery']-1)*100:+.3f} | {(x['mark']/x['est_delivery']-1)*365/d*100:+.2f} | {x['oi']:,.0f} |\n"
atm="\n".join(f"| {a['exp'][0]}-{a['exp'][1]:02d}-{a['exp'][2]:02d} | {a['strike']:.0f}{a['cp']} | {a['deribit_iv']} | {a['okx_iv']} | {a['deribit_iv']-a['okx_iv']:+.2f} |" for a in D["atm_by_expiry"])
ws={r["name"]:r for r in WS}
w("03_CRYPTO_DERIVATIVES.md",f"""# 03 — Crypto derivatives (funding, OI, basis, liquidations, options)

Code: `py/sweep1.py`, `py/dv.py`, `py/ws_sample.py`. Results: `results/derivs_analysis.json`, `results/ws_sample.json`, `results/ws_okx_retry.json`. Snapshot time ≈ 2026-09-29 13:00 UTC.

## Funding (BTC perpetuals, last 7 d)
| Venue/series | rows | gap between rows (min) | span |
|---|---|---|---|
{fr}

Cadence: 8-hour on OKX, Gate, Bitget, KuCoin, BitMEX; 1-hour on Hyperliquid, dYdX, Deribit, Kraken Futures. Timestamp jitter (OBSERVED): Hyperliquid `time` is …:00:00.059 style (not on the boundary); Gate first row carries +1 s. Kraken Futures returns a 1 MB response for the full history (from 2025-09-24) with `fundingRate` and `relativeFundingRate` (units differ; not normalised here).

Comparison at the 8-hour boundaries (units: bps per 8 h; Hyperliquid = sum of the 9 hourly rows covering the window):

| boundary | OKX | Gate | Bitget | KuCoin | Hyperliquid Σ |
|---|---|---|---|---|---|
{fr8}

Sign disagreement among OKX/Gate/Bitget/KuCoin in {sign_dis}/{len(fc)} boundaries. Bitget printed exactly 1.00 bps in 3 of the last 4 rows (possible cap/floor, INFERENCE); Hyperliquid's per-hour value sits near its base rate. **Conclusion:** funding is a venue-specific realised quantity; cross-venue "corroboration" means comparing distributions, not values.

## Open interest
Snapshot (units as delivered; last column converts to BTC at 84,340 USD only for scale):

| Venue | field | unit | value | ≈ BTC |
|---|---|---|---|---|
{oit}

Bitfinex `status/deriv` positional row carries a value at index 18 (8,933.01) that matches the documented open-interest slot (position mapping is INFERENCE from the API's documented layout; unit not verified). History: OKX `open-interest-history` {oi['okx_oi_hist_rows']} rows = {oi['okx_oi_hist_span_h']} h @5 min; Gate `contract_stats` {oi['gate_stats_rows']} rows @5 min (also carries long/short ratio and liquidation sizes); Binance Vision `futures/um/daily/metrics` 289 rows/day @5 min (sum OI ≈ 95,234 BTC at 2026-09-26 00:00, Binance aggregate — bulk only, main API blocked here).

## Liquidations
| Source | mode | observed |
|---|---|---|
| OKX | REST `/public/liquidation-orders` | {D['liq_okx']['n']} rows spanning {D['liq_okx']['span_min']:.0f} min. **Endpoint not in current docs** (docs list only WS channel) |
| OKX | WS `liquidation-orders` | 5 events in 15 s (port 443 path; :8443 reset by egress) |
| Gate | REST `/futures/usdt/liq_orders` | {D['liq_gate']['n']} rows / {D['liq_gate']['span_min']:.0f} min (BTC_USDT) |
| Bitfinex | REST `/liquidations/hist` | {D['liq_bitfinex_all_symbols']['n']} rows / {D['liq_bitfinex_all_symbols']['span_min']/60:.0f} h across ALL symbols (not per-symbol filtered in the probe) |
| BitMEX | REST / WS | REST `[]` at sample time; WS 1 liquidation msg in 20 s |
| Binance Vision | bulk `liquidationSnapshot` | HTTP 404 for BTCUSDT (folder not present) |
| Binance main / Bybit | REST/WS | BLOCKED at egress (451 / 403) |

Liquidation feeds are sample-based windows, not complete tapes: no source provides an event ID observed in the probe rows except positional/order IDs (Bitfinex position id). Completeness NOT verifiable.

## Basis (Deribit dated futures vs index)
{bt}
Deribit exposes `estimated_delivery_price` (= index) beside `mark_price` in one call. OKX lists dated futures (`BTC-USD-261030`, `…261127`, `…261225`, `…270326`, …) but the basis test was executed on Deribit only. Kraken fixed-maturity `FI_XBTUSD_261030/261225`: OI 0, no last trade (thin).

## Options IV / skew
Deribit BTC options: {D['opt_counts']['deribit_btc_options']} instruments · OKX BTC-USD options: {D['opt_counts']['okx_btc_usd_options']} · common (expiry, strike, type) with both marks: {D['opt_counts']['common_instruments']}.
Mark IV difference Deribit − OKX (vol points): median {D['opt_iv_diff_pts']['median']:+.2f}, mean {D['opt_iv_diff_pts']['mean']:+.2f}, |median| {D['opt_iv_diff_pts']['abs_median']:.2f}, p05 {D['opt_iv_diff_pts']['p05']:+.2f}, p95 {D['opt_iv_diff_pts']['p95']:+.2f}.

| expiry | ATM strike | Deribit mark_iv | OKX markVol | Δ |
|---|---|---|---|---|
{atm}

Near-dated expiries differ most (2.4 vol pts at 1-day). Deribit DVOL: {D['dvol_rows']} hourly rows for 3 days. Deribit `get_book_summary_by_currency(kind=option)` returns the whole surface in one 421 KB call (mark_iv, bid/ask, OI, underlying); OKX `opt-summary` returns 749 KB with greeks (delta, gamma, vega, theta) and `markVol`. Skew (25Δ risk reversal) was not computed: NOT TESTED.

## WebSocket bounded samples (20 s each; `results/ws_sample.json`)
| Endpoint | msgs | notes |
|---|---|---|
| Deribit trades/ticker/index | {ws['deribit_ws']['msgs']} | median recv−event {ws['deribit_ws']['lat_ms_median']} ms, p95 {ws['deribit_ws']['lat_ms_p95']} ms (local clock vs provider ts; clock skew not measured) |
| Hyperliquid trades + L2 | {ws['hyperliquid_ws']['msgs']} | median {ws['hyperliquid_ws']['lat_ms_median']} ms, p95 {ws['hyperliquid_ws']['lat_ms_p95']} ms |
| OKX (port 443) trades+liq+funding | 40 (15 s) | median ≈68 ms; `:8443` connection reset by egress |
| Binance data-stream mirror | {ws['binance_ws_datapub']['msgs']} | median {ws['binance_ws_datapub']['lat_ms_median']} ms, p95 {ws['binance_ws_datapub']['lat_ms_p95']} ms; `stream.binance.com:9443` reset |
| Coinbase matches+ticker | {ws['coinbase_matches']['msgs']} | no numeric event ts parsed |
| Kraken v2 trade | {ws['kraken_trades']['msgs']} | 17 trades + 20 heartbeats |
| Bitstamp | {ws['bitstamp_ws']['msgs']} | median {ws['bitstamp_ws']['lat_ms_median']} ms |
| Bitfinex | {ws['bitfinex_ws']['msgs']} | |
| Gemini book+trades | {ws['gemini_ws']['msgs']} | 2102 update msgs (book-heavy) |
| BitMEX trade+liquidation | {ws['bitmex_ws']['msgs']} | 1 trade, 1 liquidation |
| dYdX v4 trades | {ws['dydx_ws']['msgs']} | connected+subscribed only; 0 trades in 20 s |
| Bybit | {ws['bybit_ws']['msgs']} | 1 control msg, no data (geo-block suspected, INFERENCE) |
| KuCoin | 0 | needs token bootstrap; proxy 502 on placeholder URL (probe artefact) |
""")
# ---------- 04 fx gold commodities
x=FX["xau_snapshot"];fx=FX["fx"]
w("04_FX_GOLD_COMMODITIES.md",f"""# 04 — FX, gold/metals, commodities

Code: `py/sweep2.py`, `py/fxgold.py`, `py/macro.py`. Results: `results/fxgold_bulk.json`, `results/macro_tests.json`.

## Gold snapshot cross-check ({x['snapshot_utc'][:19]}Z; single snapshot, not a series)
| Source | price | vs gold-api XAU (4152.40) | nature |
|---|---|---|---|
| gold-api.com XAU | 4152.40 | — | spot snapshot (`updatedAt` {x['gold-api_updatedAt']}) |
| Swissquote XAU/USD standard | 4152.875 / 4153.565 (bid/ask) | +0.01% / +0.03% | quote, spread ≈ 0.69 USD |
| Hyperliquid `xyz` dex GOLD | 4153.05 | +0.02% | perp mid |
| OKX XAUT-USDT | 4155.2 | +0.07% | tokenised gold, USDT-quoted |
| Kraken XAUTUSD | 4154.3 | +0.05% | tokenised gold |
| Kraken PAXGUSD | 4160.29 | +0.19% | tokenised gold |
| Coinbase PAXG-USD | 4161.26 | +0.21% | tokenised gold |
| Deribit PAXG_USDC-PERPETUAL | 4168.87 | +0.40% | perp on tokenised gold |
| Yahoo GC=F | 4186.6 | +0.82% | COMEX futures (contango/roll, different instrument) |
| Yahoo XAUUSD=X | no data | — | probe returned no result |

Reading (OBSERVED): spot-like sources agree within ~3 bps of each other; tokenised gold trades 5–20 bps above; the futures contract carries ~80 bps. Different instruments, so no source is treated as reference. Gold 24/7 proxies were also fetched as 1H bars on Kraken (PAXG, XAUT), OKX (XAUT), Coinbase (PAXG), Deribit (PAXG perp) — schemas match their BTC counterparts. **LBMA** gold AM/PM benchmark JSON: 14,844 daily rows from 1968-01-02 to 2026-09-28 (OBSERVED); redistribution terms restrictive per IBA (docs quote is for platinum/palladium; gold terms unverified).
**Dukascopy** XAUUSD tick file for 2024-01-02 10h decoded: 4,969 ticks (first ask/bid 2077.255/2076.965), i.e. usable keyless historical ticks; candle endpoints returned HTTP 429 after a few requests (OBSERVED rate-limit enforcement). Licence: non-commercial (docs quote).

## FX (EURUSD and majors)
* **ECB SDMX** (`EXR/D.USD.EUR.SP00.A`): 8 latest daily fixes retrieved; back to 1999-01-04; `updatedAfter` accepted; CSV carries OBS_STATUS.
* **Frankfurter**: 10 daily values 2026-09-15…09-28 — the 8 overlapping dates equal ECB to 4 decimals (derived from ECB, not independent).
* **Alpha Vantage demo key** EURUSD 2026-09-28: O 1.13840 H 1.13910 L 1.13520 C 1.13700; **Twelve Data demo** 2026-09-28: C 1.13716; **ECB fix** 1.1378 (14:15 CET) — differences of 0.6–0.8 pips reflect different cut-off times, not error.
* **Yahoo EURUSD=X** daily closes track ECB within ~10 pips on shared dates but the 2026-09-28 close is `null` (OBSERVED) — null closes must be handled.
* **BoE IADB** GBP/USD XUDLUSS daily CSV; **BoC Valet** FXUSDCAD JSON; **open.er-api** latest only (updates once a day, `time_next_update_utc`); **fawazahmed0** CDN snapshot.
* Intraday FX keyless: only Yahoo (unofficial, 429 seen) and Dukascopy ticks (non-commercial). No keyless official intraday FX source found.

## Commodities / energy
* Keyless price feeds: **Yahoo chart** — CL=F, BZ=F, HG=F, SI=F, DX-Y.NYB each returned 106 hourly bars/5 d (NG=F got HTTP 429, retry not attempted); GC=F 534 one-minute bars/day with 0 null closes.
* **CFTC COT** (Socrata): weekly positioning incl. GOLD–COMEX (OI 412,800 on 2026-09-22) and PAX GOLD PERP STYLE (Coinbase Derivatives, OI 1,310); history from 1986-01-15.
* **World Bank Commodity Pink Sheet** monthly XLSX downloaded (765 KB); **EIA** needs a free key (HTTP 403 API_KEY_MISSING) — NOT executed; **FRED** WTI/gold series not reachable from the test egress.
* No keyless official *intraday* energy or base-metal feed was found. Exchange-native crypto perps on commodities exist (Hyperliquid `xyz` dex lists ALUMINIUM plus equities, e.g. mid 3080.0) — venue/instrument risk, not evaluated as a commodity price source.
""")
# ---------- 05 macro
w("05_MACRO.md",f"""# 05 — Macro and calendar

Code: `py/macro.py`, `py/sweep2.py`. Results: `results/macro_tests.json`.

| Source | Result (OBSERVED) | Auth | PIT-relevant fields |
|---|---|---|---|
| FRED API | reachable at `api.stlouisfed.org` (HTTP 400 "api_key not set/not registered"); **fredgraph.csv, alfred and fred web hosts: connection closed by proxy (5 attempts)** | free key | `realtime_start/realtime_end` documented (not executed) |
| ALFRED | host unreachable from egress; vintage URL parameters untested | key | vintages (DOCUMENTED_CLAIM) |
| US Treasury daily par yield CSV | 24 rows for 2026 YTD, 35 for 1990 (unexpectedly few — likely pagination; UNEXPLAINED); latest row 09/28/2026 | none | none |
| US Treasury FiscalData | 200, earliest 2001-01-31 in probe | none | `record_date` |
| NY Fed SOFR | 200; latest 2026-09-28 = 3.90; search back to 2018-04-03 (1.75) | none | `revisionIndicator` (empty), `effectiveDate` |
| ECB SDMX | 200 (CSV/JSON); `updatedAfter` accepted | none | OBS_STATUS |
| Eurostat HICP | 200; JSON-stat `updated` = 2026-02-06 for the cube read | none | dataset `updated` |
| BLS API | v1 keyless: first probe `REQUEST_NOT_PROCESSED` (daily threshold), later probe `REQUEST_SUCCEEDED`; v2 without key: threshold message | v1 none / v2 key | footnotes |
| Bank of Canada Valet | 200, daily FXUSDCAD | none | — |
| Bank of England IADB | 200 CSV | none | — |
| CFTC COT | 200; from 1986-01-15 | none/app token | `report_date_as_yyyy_mm_dd` (as-of date; release time absent) |
| World Bank | 200; `lastupdated` 2026-07-13 | none | `lastupdated` |
| EIA / BEA | key required; not executed | key | — |
| IMF DataMapper / OECD | IMF 403 from egress; OECD query malformed by me | — | — |
| SNB | 200 (891 KB cube) | none | — |

## Economic calendar and news
* **Faireconomy / ForexFactory JSON**: 141 events for the current week (9 currencies, impact High/Medium/Low/Holiday). Payload fields: title, country, date (ISO with offset), impact, forecast, previous. **No `actual` field** (0/141), `nextweek`/`lastweek` files 404. Two fetches 2 s apart were byte-identical. Suitable for *scheduled-event times* only.
* Trading Economics: guest key discontinued (HTTP 410). FMP/Finnhub/Polygon: key required, free-tier calendar capability UNKNOWN. BLS ICS release schedule: 403 from egress. Fed FOMC calendar HTML (165 KB) reachable; not parsed. GDELT reset by egress. TipRanks connector present in this session but deliberately not executed (account quota, terms unverified).
* Sentiment: alternative.me Fear&Greed (3,159 daily rows).

## Gap statement
Macro/calendar *release values with release timestamps* are the weakest class: the keyless official sources give observation dates but rarely the moment the value became public. That timing has to come from an external schedule (BLS/Fed calendars, FF-style feeds) or from ALFRED-style vintages, which could not be executed here.
""")
# ---------- 06 execution tests
sw={s["name"]:s for s in S1+S2}
def rowsw(s): return f"| `{s['name']}` | {s.get('status')} | {s.get('ms')} | {s.get('bytes')} | {(s.get('err') or '')[:70]} |"
lat="\n".join(f"| {k} | {v['ok']}/10 | {v['ms_med']} | {v['ms_p90']} | {v['ms_max']} |" for k,v in L.items() if not k.startswith("_"))
bur="\n".join(f"| {k[7:]} | {v['n']} | {v['actual_s']} | {','.join(v['statuses'])} |" for k,v in L.items() if k.startswith("_"))
w("06_EXECUTION_TESTS.md",f"""# 06 — Execution tests

All numbers are from the test egress (cloud container via policy proxy), so latencies include the proxy path and are **not** representative of a colocated consumer. Raw first-pass captures: `bench/data_feeds_v1/raw/*.json`; run logs: `results/sweep1.json`, `results/sweep2.json`, `results/latency_ratelimit.json`.

## Discovery sweep (single call each)
{len(S1)+len(S2)} endpoint probes. HTTP 200: {sum(1 for s in S1+S2 if s.get('status')==200)}. Non-200 or failed: {sum(1 for s in S1+S2 if s.get('status')!=200)}.

| probe | status | ms | bytes | error |
|---|---|---|---|---|
"""+"\n".join(rowsw(s) for s in S1+S2)+f"""

## Repeated latency (10 sequential calls, 1 s spacing, small payloads)
| endpoint | ok | median ms | p90 ms | max ms |
|---|---|---|---|---|
{lat}

## "Bursts" — honest description
Three bursts were requested well below documented limits (OKX 20 calls; Coinbase 8; Deribit 20). Because each call takes ~0.5–0.7 s through the egress, achieved rates were ≈1.5 req/s, i.e. **the egress, not the provider, set the throttle; no 429 was provoked on any exchange**:

| burst | calls | actual seconds | statuses |
|---|---|---|---|
{bur}

Rate-limit *enforcement* was only observed passively: Dukascopy candle endpoints HTTP 429 after a few requests; Yahoo HTTP 429 on the root probe and NG=F; BLS daily-threshold message (first probe) that later cleared; geo-blocks Binance 451, Bybit/MEXC-futures/IMF/goldprice 403. Documented limits (quotes in `01`): OKX candles 40/2 s; Coinbase 10/s per IP; Hyperliquid 1200 weight/min per IP; Gemini 120/min; gold-api history 10/h free; Alpha Vantage 25/day; Twelve Data 8/min; BLS v1 25/day. Rate-limit response headers were essentially absent (only `Date`/`Server` captured on OKX, Coinbase, Deribit) — consumers cannot self-throttle from headers on these venues.

## Not measured
HTTP 429/Retry-After recovery behaviour; sustained-hour stability; WS reconnect/gap-recovery/sequence-gap semantics; multi-hour late-arrival/revision drift; clock-skew-corrected latency.
""")
# ---------- 07 cross provider
pr=BA["pairs"]
def p(a,b):
    k=f"{a}|{b}" if f"{a}|{b}" in pr else f"{b}|{a}";v=pr[k];return v
best=sorted(pr.items(),key=lambda kv:kv[1]["close_bps_med"])[:8]
bt7="\n".join(f"| {k.split('|')[0]} | {k.split('|')[1]} | {v['close_bps_med']} | {v['close_bps_p95']} | {v['high_bps_med']} | {v['low_bps_med']} | {v['exact_ohlc_match']}/{v['n']} | {v['ret_corr']} |" for k,v in best)
ex=sum(v["exact_ohlc_match"] for v in pr.values())
w("07_CROSS_PROVIDER_COMPARISON.md",f"""# 07 — Cross-provider comparison

No source is treated as ground truth. Pairwise statistics: `results/bars_analysis_t2.json` ({len(pr)} pairs, ≥30 common minutes; n = 233 each). Consensus deviations: `results/consensus_dev.json`. Lag test: `results/lag_test_vs_kraken.json`.

## Timestamps
Best cross-correlation lag versus Kraken is **0 minutes for all 17 series** (OBSERVED) → all providers label 1-minute bars with the same convention (bar-open time) within the resolution tested. Per-provider raw semantics differ in unit and order (ms vs s vs ISO; newest-first vs oldest-first; Binance Vision spot in µs since 2025-01) — see `01`.

## OHLC
* Exact OHLC equality between any two venues in the same minute: **{ex} occurrences across {sum(v['n'] for v in pr.values())} pair-minutes** (every pair 0). Venues print different trades.
* Closest pairs (median |close diff|, bps): 

| venue A | venue B | close med | close p95 | high med | low med | exact | ret corr |
|---|---|---|---|---|---|---|---|
{bt7}

* Quote currency: USDT-vs-USD pairs differ by ≈3–5 bps median (e.g. Kraken vs OKX {p('okx_spot_BTCUSDT','kraken_spot_XBTUSD')['signed_close_bps_med']} bps signed, OKX − Kraken).
* Spot vs perp: 0.5–5 bps (basis + venue offsets); OKX swap vs Hyperliquid 0.52 bps median.
* Outliers: Bitfinex vs USD peers ≈ 13 bps; HTX ≈ 4.5 bps; dYdX/Binance.US/Gemini low return correlation (0.43/0.59/0.79) because most of their bars are gap-filled or thinly traded.

## Volume
Not comparable: OKX spot base units; OKX swap contracts (ratio to spot ≈ 0.001); Deribit USD notional; dYdX/Hyperliquid base; Gate base; KuCoin base. Within-group base-volume ratios span 0.003×–9× of the group median (consensus table in `02`). Volume from these APIs should be treated as venue-local activity, not as market volume.

## Missing / late / revised
See `02`: 1 real missing minute (Bitget), gap-filling on four venues, 0 late arrivals, 0 revisions in 6 minutes on 17 series; futures/funding/OI revision behaviour over longer windows NOT TESTED.

## Cross-source: options, funding, OI, gold, FX
Options IV Deribit vs OKX, funding at 8 h boundaries, OI units: `03`. Gold cross-check: `04`. ECB vs Frankfurter identical (derived); ECB fix vs intraday-close sources within 0.6–0.8 pips (cut-off effect).
""")
# ---------- 08 PIT
def pl(cls): return sorted([s for s in C if s["pit"]==cls],key=lambda s:s["id"])
t8="""# 08 — PIT readiness

Classification uses what each source *emits*, not what a downstream store could add. Criteria: event timestamp · observation/receipt timestamp · provider event ID · revision/correction signal · finality · backfill discrimination.

* **PIT_NATIVE** = provider itself supplies as-of/vintage semantics.
* **PIT_ADAPTABLE** = event time + ≥1 of (ID, finality flag, revision indicator, server receipt stamp, immutable file metadata) so that a consumer can build PIT with its own receipt stamps.
* **PIT_WEAK** = only overwriting/latest values or missing event time granularity.
* **PIT_UNSUITABLE** = snapshot with no history and no reliable event time.

"""
t8+=f"| class | all | executed |\n|---|---|---|\n"+"\n".join(f"| {c} | {pit[c]} | {pit_e[c]} |" for c in("PIT_NATIVE","PIT_ADAPTABLE","PIT_WEAK","PIT_UNSUITABLE"))+"\n\n"
t8+="""## Signals actually observed (per executed source class)
| Signal | Present in | Absent / not observed |
|---|---|---|
| Event timestamp | all bar/tick/funding sources | gold-api (updatedAt only), open.er-api (daily stamp) |
| Provider receipt/server stamp | **Deribit** (`usIn`/`usOut` µs in every JSON-RPC response); HTTP `Date` header on all (coarse) | all other exchange REST payloads |
| Provider event ID | Deribit trade_id; Coinbase match trade_id/sequence; Binance trade id; Hyperliquid tid; dYdX `effectiveAtHeight` (block) | candle endpoints (no IDs), funding rows |
| Revision/correction signal | NY Fed `revisionIndicator`; ECB `OBS_STATUS`, `updatedAfter`; Eurostat dataset `updated`; BLS footnote codes | every exchange feed; FRED path unexecuted |
| Finality | OKX `confirm`, Gate closed-flag, Binance Vision immutable dated files (+ CHECKSUM, ETag, Last-Modified) | Kraken/Coinbase/Bitstamp etc. (forming bar returned unflagged on Kraken) |
| Backfill discrimination | Binance Vision (bulk vs API distinguishable by origin and `Last-Modified`) | all REST candle endpoints: a re-fetch returns the same rows with no ingestion metadata |

## Per-source classification
| Source | PIT class | Executed | Why |
|---|---|---|---|
"""
why={"PIT_NATIVE":"documented vintage semantics; NOT executed","PIT_ADAPTABLE":"event time + at least one of ID/finality/revision/receipt metadata","PIT_WEAK":"latest-only or coarse/no event ID or revision signal","PIT_UNSUITABLE":"overwritten snapshot, no history"}
for cl in("PIT_NATIVE","PIT_ADAPTABLE","PIT_WEAK","PIT_UNSUITABLE"):
    for s in pl(cl): t8+=f"| {s['name']} | {cl} | {s['exe']} | {why[cl]} |\n"
t8+="""
## Findings
1. No executed source is PIT_NATIVE. The only PIT_NATIVE claim (ALFRED vintages) is DOCUMENTED_CLAIM and the host was unreachable — it must not be counted as evidence.
2. Bar/funding/OI APIs give event time but let the same key be re-fetched with no ingestion metadata; a consumer must stamp `received_at` itself and store every fetch (re-fetch diff over 6 min showed 0 changes on 17 series, so the *risk* appears low on closed 1m bars but was not excluded for longer horizons).
3. Closed-bar finality is provider-signalled only on OKX and Gate; elsewhere it must be inferred from `bar_open + 60 s < received_at`.
4. Backfills are cleanly separable only for Binance Vision (file-level metadata) — a strong reason to use it as the historical reference and the live APIs for the trailing edge, with a tested join rule at the seam (seam consistency for 2026-09-26: 1440/1440 identical).
5. Timestamp-unit drift (µs vs ms), column-order drift and unflagged forming bars are PIT hazards (look-ahead by including the forming bar) and need per-source contract tests.
""".replace("\n\n\n","\n\n")
w("08_PIT_READINESS.md",t8)
# ---------- 09 license & cost
def lic(s):
    d=DOC.get(s["docs"]) if s["docs"] else None;return q(d,"license",150)
t9=f"""# 09 — Licence and cost

Cost classes: {dict(cost)}. Executed-only: {dict(cost_e)}. "Free" is asserted only for the capability actually executed. Licence text is a **verbatim short quote from an official page** where the research pass found one, `NOT_FOUND` otherwise; commercial-use and redistribution status is therefore **UNKNOWN unless the quote says so** and nothing here is legal advice.

"""
for c in("FREE_UNAUTHENTICATED","FREE_WITH_ACCOUNT","FREE_TIER","PAID_ONLY","UNKNOWN"):
    t9+=f"## {c}\n| Source | Executed | Capability actually tested | Licence/ToS quote (official page) |\n|---|---|---|---|\n"
    for s in [s for s in C if s['cost']==c]:
        t9+=f"| {s['name']} | {s['exe']} | {', '.join(s['classes'])} | {lic(s)} |\n"
    t9+="\n"
t9+="""## Constraint highlights (DOCUMENTED_CLAIM, from the quotes above)
* **Restrictive:** Dukascopy (non-commercial, no resale), Twelve Data free (personal/internal/non-commercial), Finnhub (no redistribution of data or derived results), open.er-api (attribution, no redistribution), Yahoo (developer terms prohibit resale/sublicensing), Bitstamp (commercial exploitation → contact vendor), LBMA/IBA (licence to redistribute), FRED (third-party series may carry copyright; attribution notice required).
* **Permissive with attribution:** World Bank (CC BY 4.0), CoinGecko (attribution), alternative.me (commercial allowed with attribution), ECB (cite source, reproduce accurately), Bank of Canada (free use/copy/distribute), NY Fed (share with permission language), Eurostat (reuse with attribution).
* **Public-domain style:** US Treasury FiscalData ("without restriction"), EIA (US government), BLS ("no controls over end use").
* **No official licence text retrieved (UNKNOWN):** OKX, Kraken, Coinbase, KuCoin, Gemini, Gate, Bitget, HTX, Deribit, BitMEX, Hyperliquid, Binance mirror/Vision, Swissquote, Faireconomy, Frankfurter (delegates to underlying providers), CFTC portal, BoE. Exchange public-data terms of use were mostly JS-rendered or 403 to the research pass; **a manual ToS read is required before any storage/redistribution decision.**
* Nothing in this study requires payment for the capability tested; capabilities that appear to need payment or a key are labelled above, not assumed free.
"""
w("09_LICENSE_AND_COST.md",t9)
# ---------- 10 resilience
classes=[("SPOT","Crypto spot bars (1m/MTF)"),("FUND","Funding"),("OI","Open interest"),("LIQ","Liquidations"),("BASIS","Basis"),("OPT","Options IV/skew"),("FX","FX"),("GOLD","Gold/metals"),("COMM","Commodities"),("MACRO","Macro"),("CAL","Calendar/news")]
t10="""# 10 — Resilience matrix

Roles are *capability statements from measured behaviour*; no automatic failover design is proposed. Role vocabulary: PRIMARY / SECONDARY / FALLBACK / CORROBORATION_ONLY / HISTORICAL_ONLY. A source only appears where an executed test supports the role.

| Gap class | PRIMARY | SECONDARY | FALLBACK | CORROBORATION_ONLY | HISTORICAL_ONLY |
|---|---|---|---|---|---|
"""
for k,lab in classes:
    cells=[]
    for r in("PRIMARY","SECONDARY","FALLBACK","CORROBORATION_ONLY","HISTORICAL_ONLY"):
        cells.append(", ".join(s["name"].split(" (")[0] for s in C if s["roles"].get(k)==r and yes(s)) or "—")
    t10+=f"| {lab} | "+" | ".join(cells)+" |\n"
t10+=f"""
Executed sources holding at least one PRIMARY/SECONDARY/FALLBACK role: **{len(fb)}** → {', '.join(fb)}.

## Reading the matrix
* **Crypto spot** has the deepest redundancy: ten keyless venues with |median| close deviation ≤1.32 bps from their group consensus (Kraken, Coinbase, Bitstamp, Gemini, OKX, KuCoin, Gate, Bitget, MEXC, Binance mirror), of which four (OKX, Kraken, Coinbase, Binance mirror) are marked PRIMARY-*capable* on clean-bar evidence — capability, not ranking. Independent *providers* here are independent *venues* (different trade populations), so failover between them changes the series (0 exact OHLC matches) — a substitution is a different price series, not a copy.
* **Derivatives**: OKX + Deribit + Hyperliquid + Gate give ≥3 independent funding/OI feeds; liquidations rely on OKX/Gate/Bitfinex samples (no complete tape verified); options IV has exactly two keyless providers (Deribit, OKX), which agree within 0.5 vol pts (median |Δ|) but up to 2.4 at 1-day expiry.
* **FX/gold/macro/calendar**: redundancy is thin and mostly *daily/reference* data. Official FX is ECB-based (Frankfurter is derived from ECB — not an independent fallback). Intraday FX and commodities depend on Yahoo (unofficial, 429s) and Dukascopy ticks (non-commercial).
* **Blocked-at-egress but potentially decisive:** Binance main/fapi, Bybit, FRED/ALFRED — resilience conclusions for Binance/Bybit derivatives and PIT-native macro are OPEN, not negative.
* Correlated-failure notes (INFERENCE): several sources sit behind Cloudflare; Frankfurter/ECB/Alpha-Vantage EURUSD are not independent of each other's underlying reference; Coinbase PAXG and Deribit PAXG perp share the same underlying token.
"""
w("10_RESILIENCE_MATRIX.md",t10)
# ---------- 11 adjudication
t11="""# 11 — Adjudication

Verdict vocabulary: **ADOPT_REFERENCE** (use as the reference source for the class in further research; nothing is integrated), **ADAPT_CANDIDATE**, **PARK** (insufficient evidence, blocked, thin, or restricted), **REJECT**. No synthetic ranking and no scoring; ordering is by group, then name.

"""
for v in("ADOPT_REFERENCE","ADAPT_CANDIDATE","REJECT","PARK"):
    t11+=f"## {v} ({ver[v]})\n| Source | Executed | Classes | Basis for verdict |\n|---|---|---|---|\n"
    for s in sorted([s for s in C if s["verdict"]==v],key=lambda s:s["name"]):
        t11+=f"| {s['name']} | {s['exe']} | {', '.join(s['classes'])} | {(s['note'] or s['auth'] or '-')[:230].replace('|','/')} |\n"
    t11+="\n"
t11+="""## Class-level candidate view (executed sources with ADOPT_REFERENCE or ADAPT_CANDIDATE)
"""
for lab,l in (("Crypto spot",spot),("Derivatives (funding/OI/liq/basis/options)",deriv),("FX",fxc),("Commodities + gold",comm),("Macro",mac),("Calendar",cal)):
    t11+=f"* **{lab}** ({len(l)}): {', '.join(l)}\n"
t11+="""
## Drop-in and invalidation
* **ANY_DROP_IN_SOURCE = NO.** "Drop-in" was defined as: keyless or stable free access + executed + PIT-native or provider-signalled finality + documented permissive licence + covers a gap class without adaptation. No source meets all conditions (exchange licences unverified; no PIT-native source executed; contract hazards listed in 08).
* **ANY_SCIENTIFIC_INVALIDATION = NO.** Nothing observed invalidates a stated hypothesis of the mission; observed hazards (unit drift, unflagged forming bar, venue-specific funding) are constraints, not refutations.
"""
w("11_ADJUDICATION.md",t11)
# ---------- 12 limitations
w("12_LIMITATIONS.md",f"""# 12 — Limitations

1. **Single vantage point, single time window.** Everything ran from one cloud egress on 2026-09-29 (≈12:50–13:15 UTC), 240-minute bar window, re-fetches only 78 s and 362 s later. No multi-day stability, no overnight/weekend behaviour, no outage or maintenance-window sampling.
2. **Egress-blocked providers are unassessed, not rejected:** Binance main REST/WS/fapi (HTTP 451), Bybit (403), MEXC futures (403), FRED/ALFRED (connection closed by proxy ×5), Stooq, GDELT, IMF, BLS ICS, goldprice.org, metals.live, CryptoPanic. Cost/licence for these is UNKNOWN.
3. **Not executed:** keyed sources without a key (FRED, EIA, BEA, Coinalyze, CryptoCompare/CoinDesk, Polygon, Finnhub, FMP, OANDA); TipRanks connector (deliberately, to spare an account quota); CoinGecko MCP connector failed to connect; OECD query was my own malformed request.
4. **Rate-limit behaviour not stress-tested.** I stayed under documented limits; the egress cap (~1.5 req/s) prevented meaningful bursts. No provider 429 recovery/Retry-After semantics were measured on exchanges.
5. **Revision/late-arrival tests are short (≤6 min) and limited to closed 1-minute bars.** Funding/OI/options/macro revisions over days were not observed.
6. **Latency is proxy-inclusive** and WS latency uses the container clock against provider timestamps with no skew correction.
7. **Docs facts** (`docs_facts.json`) come from an automated official-page pass; several pages were 403/JS-only and are `NOT_FOUND`; some quotes are condensed or spliced from adjacent sentences; licence conclusions are not legal advice. Rate limits in `01` are DOCUMENTED_CLAIM, not measured, except where stated.
8. **Raw artifacts:** files >400 KB were truncated on capture and the truncated copies were deleted (Deribit/OKX option summaries, Kraken Futures funding, LBMA, SNB, Pink Sheet); derived statistics were computed from full live responses in the same scripts (`dv.py`, `fxgold.py`, `macro.py`), so the numbers stand but those raw bodies are not archived.
9. **Small samples for skew/basis:** options compared as marks (not executable quotes); skew (25Δ RR) not computed; basis test on Deribit only.
10. **Instrument mapping caveats:** perp bars compare different contract specs and quote currencies; volumes are not unit-normalised; USDT/USD basis unmodelled.
11. **US Treasury CSV** returned fewer rows than trading days (24 for 2026 YTD) — unexplained, not investigated.
12. **Simulation-era prices:** the observed prices (e.g. BTC ≈ 84 k, gold ≈ 4.15 k) are what the providers returned; no attempt was made to validate them against anything outside the providers.
13. No AurumShift code, schema or data was read; "gap classes" are the mission's stated list, so relevance to actual needs is INFERENCE.
""")
print(FINAL)
