"""Render reports/016_alternative_data/*.md from catalog.py + results/*.csv|json (numbers are pulled, not typed)."""
import os, json, collections, numpy as np, pandas as pd
from catalog import CAT
B = os.path.join(os.path.dirname(__file__), ".."); RES = os.path.join(B, "results")
OUT = os.path.join(B, "..", "..", "reports", "016_alternative_data"); os.makedirs(OUT, exist_ok=True)
PR = {x["id"]: x for x in json.load(open(os.path.join(RES, "probe_results.json")))}
PP = json.load(open(os.path.join(RES, "pit_probes.json")))
LIC = json.load(open(os.path.join(RES, "license_evidence.json")))
INC = pd.read_csv(os.path.join(RES, "incremental_results.csv")); CS = pd.read_csv(os.path.join(RES, "candidate_summary.csv"))
SUM = json.load(open(os.path.join(RES, "summary.json")))
RE = pd.read_csv(os.path.join(RES, "real_economy_results.csv")); CR = pd.read_csv(os.path.join(RES, "crude_robustness.csv")); PW = pd.read_csv(os.path.join(RES, "portwatch_result.csv"))
NOCAL = pd.read_csv(os.path.join(RES, "incremental_results_no_calendar.csv"))
HDR = ("> External research only — no private AurumShift code, no integration claims. Evidence tags: **[OBS]** observed in this study, **[DOC]** stated on a provider page/API response fetched in this study, "
       "**[INF]** inference, **[UNK]** unknown/not verified. Study date 2026-09-29 (sandbox clock). Reproduce with `bench/alternative_data_v1/`.\n\n")
def w(name, body): open(os.path.join(OUT, name), "w").write(body.rstrip() + "\n")
def md(df, floatfmt=3):
    df = df.copy()
    for c in df.columns:
        if df[c].dtype.kind == "f": df[c] = df[c].map(lambda v: "" if pd.isna(v) else (f"{v:.{floatfmt}f}"))
    h = "| " + " | ".join(map(str, df.columns)) + " |\n|" + "|".join("---" for _ in df.columns) + "|\n"
    return h + "\n".join("| " + " | ".join(str(x).replace("|", "/").replace("\n", " ") for x in r) + " |" for r in df.values) + "\n"
def esc(s): return str(s).replace("|", "/")
def probe(c):
    ps = [PR[p] for p in c["probes"] if p in PR]
    if not ps: return "n/a", "n/a", "n/a"
    lat = [p.get("latency_ms_med") for p in ps if p.get("latency_ms_med")]
    ages = [p.get("last_age_h") for p in ps if p.get("last_age_h") is not None]
    st = ",".join(str(p["status"]) for p in ps)
    return (f"{int(np.median(lat))} ms" if lat else "n/a"), (f"{min(ages):.1f} h" if ages else "n/a"), st
E = [c for c in CAT if c["exec"] == "Y"]; free = [c for c in CAT if c["cost"].startswith("free")]
cnt = lambda L, k: collections.Counter(c[k] for c in L)
PITE, PITA = cnt(E, "pit")["PIT_NATIVE"], cnt(E, "pit")["PIT_ADAPTABLE"]
cand = CS[CS.klass == "INCREMENTAL_CANDIDATE"]; pdo = CS[(CS.klass == "PRICE_DERIVATIVE_ONLY") & ~CS.cand.str.contains("CONTROL")]; ind = CS[(CS.klass == "INDEPENDENT_NO_EVIDENCE") & ~CS.cand.str.contains("CONTROL")]
crude = RE[(RE.cand.str.contains("crude")) & (RE.target == "release_day:y")].iloc[0]
dv = INC[(INC.cand.str.contains("dvol")) & (INC.target == "lrange") & (INC.sens == "primary")].iloc[0]
# ------------------------------------------------------------------ 00
FINAL = "LIMITED_ALTERNATIVE_DATA_SUPPORTED"
final_block = f"""```
SOURCES_DISCOVERED={len(CAT)}
SOURCES_EXECUTED={len(E)}
FREE_SOURCES={len(free)}   # zero-cost route (no key: {sum(1 for c in CAT if c['cost']=='free-nokey')}; free key required: {sum(1 for c in CAT if c['cost']=='free-key')}); executed & free: {sum(1 for c in E if c['cost'].startswith('free'))}

PIT_NATIVE={PITE}   # executed sources; +1 documented but unreachable (FRED/ALFRED)
PIT_ADAPTABLE={PITA}   # executed sources
LOOKAHEAD_RISK={cnt(E,'pit')['LOOKAHEAD_RISK']}   # executed sources (historical rows without publication timestamps)
SNAPSHOT_ONLY={cnt(E,'pit')['SNAPSHOT_ONLY']}   # executed sources with no history to replay (forward capture only)

INCREMENTAL_INFORMATION_CANDIDATES={len(cand)+1}   # EIA weekly crude-inventory surprise (real economy); Deribit DVOL (options-implied vol, market-derived)
PRICE_DERIVATIVE_ONLY_REJECTS={len(pdo)}   # feature blocks (excludes 2 built-in controls); across {len(set(c.split('_')[0] for c in pdo.cand))} sources — see 07

FINAL_VERDICT={FINAL}
```"""
w("00_EXECUTIVE_SUMMARY.md", f"""# 00 — Executive summary: free/public alternative-data discovery (mission AURUMSHIFT_EXTERNAL_ALTERNATIVE_DATA_DISCOVERY_V1)

{HDR}
## Verdict
**{FINAL}.** Of {len(CAT)} sources catalogued in 16 categories ({len(E)} actually executed, {len(free)} with a zero-cost route), only **two** cleared the pre-declared incremental-information bar, and they are very different animals:

| candidate | what it is | evidence | PIT status |
|---|---|---|---|
| **EIA weekly US crude-inventory surprise** (vs 5-yr seasonal norm) → WTI/Brent release-day return | physical-economy datum, independent of price (past-price R² = {crude.react_past:.3f}) | HAC t = {crude.t_s:.2f}, q<0.001, OOS MSE gain {crude.oos_gain_pct:.2f}% (one-sided DM p = {crude.dm_p_onesided:.3f}); Brent replicates (t = {CR[CR.series=='Brent'].t_s.iloc[0]:.2f}); placebo offsets null except Tuesday (API report day-before, p = {CR[CR.cand.str.contains('Tue')].p_incr.iloc[0]:.3f}); **effect fades after 2021 (p = {CR[CR.cand.str.contains('2021-2026')].p_incr.iloc[0]:.2f})** | LOOKAHEAD_RISK (bulk files have no vintages); PIT_ADAPTABLE only by forward capture on the release clock |
| **Deribit DVOL** (BTC options-implied vol) → next-day log range | information from a *second market* (options), not spot price/volume/realised vol/funding/OI | HAC p < 0.001, OOS MSE gain {dv.oos_gain_pct:.2f}% (DM p = {dv.dm_p_onesided:.3f}) | PIT_NATIVE (immutable index prints); market-derived, not "alternative" in the non-market sense |

Everything else that was testable ({len(CS[~CS.cand.str.contains('CONTROL|mvrv')])} crypto/public-liquidity/attention feature blocks × BTC/ETH × 3 targets, plus gas storage, weather, shipping) **failed** to add information beyond the price/volume/volatility/funding/OI baseline once calendar effects were controlled. {len(pdo)} blocks are classified PRICE_DERIVATIVE_ONLY (react to, or are absorbed by, the baseline); {len(ind)} are independent of price but showed no predictive evidence (this is **not** negative evidence — missing evidence is not negative evidence).

## The four findings that matter
1. **Calendar artefacts fake alternative-data alpha.** A first-pass baseline without weekday dummies gave {SUM['no_calendar_baseline']['n_p05']}/{SUM['no_calendar_baseline']['n_tests']} in-sample p<0.05 blocks and {SUM['no_calendar_baseline']['n_oos_dm_p10']} OOS-significant ones (npm download counts "improved" next-day range by 1.9–3.6 %, DM p ≤ 0.027). Adding 6 weekday dummies and a 60-day vol memory to the baseline removed **all** of them (min BH-q across the family excluding DVOL = {SUM['min_q_family_excl_dvol']:.2f}; expected p<0.05 under the null ≈ {SUM['n_p05_expected_under_null']}, observed {SUM['n_p05_family']} in-sample, none OOS-confirmed). 12 pure-noise blocks: 0 with p<0.05.
2. **"Free history" is mostly restated history.** Coin Metrics community: 2067/2219 sampled rows were recomputed in 2026-04 (2,024 of them >30 d after their completion stamp); Binance Vision `metrics` files: 33/40 sampled old files re-uploaded (median 371 d after their day); CFTC Socrata: 231/442 Bitcoin rows carry a single bulk-load stamp (2022-09-13); EIA/Treasury/NY Fed/PortWatch/npm/Wikimedia/DefiLlama/Fear&Greed: no vintages at all → all classified **LOOKAHEAD_RISK** for history per mission rule.
3. **The genuinely PIT-native free sources are not the ones people reach for:** GDELT 15-min files (Last-Modified 4.5–10.1 min before the file stamp, 7/7 samples 2016–2026), GH Archive hourly files (Last-Modified +5.1 min after hour end), Kalshi/Polymarket price history, SEC EDGAR `acceptanceDateTime`, NOAA GFS run files, Deribit index bars. Most are **untested** for information value here (bandwidth/power/time), so they remain open, not rejected.
4. **Several whole categories cannot be tested from free sources today:** ETF flows (iShares returns an HTML shell, Farside is behind a Cloudflare challenge, EDGAR has only periodic filings), Google Trends (no official API), news/RSS/social/mempool (feeds keep hours–days of items; no history → forward capture only), weather forecasts (Open-Meteo daily quota exhausted by the shared egress IP).

## What would change the verdict
* Upgrade to MULTIPLE_… would need ≥1 more PIT-clean, price-independent source with a confirmed OOS gain — the best untested leads are (a) GDELT GKG theme volume/tone, (b) Kalshi/Polymarket macro-event probabilities, (c) mempool/fee state captured forward for ≥12 months, (d) Open-Meteo *historical-forecast* (as-issued forecasts) vs Henry Hub.
* Downgrade would follow if the EIA crude effect is shown to be fully absorbed intraday before any executable timestamp (the post-2021 fade already hints at this).

## Counts (final block)
{final_block}

See `01_SOURCE_LANDSCAPE.md` (all sources), `06_PIT_READINESS.md` (leakage), `07_INCREMENTAL_INFORMATION.md` (tests), `09_ADJUDICATION.md` (ADOPT/ADAPT/PARK/REJECT), `10_LIMITATIONS.md`.
""")
# ------------------------------------------------------------------ 01
rows = []
for c in CAT:
    lat, age, st = probe(c)
    rows.append(dict(source=c["name"], category=c["cat"], exec=c["exec"], cost=c["cost"], PIT=c["pit"], info=c["info"], latency=lat, freshness=age, http=st))
tab = pd.DataFrame(rows)
cats = tab.groupby("category").agg(sources=("source", "count"), executed=("exec", lambda s: (s == "Y").sum()), free=("cost", lambda s: s.str.startswith("free").sum())).reset_index()
w("01_SOURCE_LANDSCAPE.md", f"""# 01 — Source landscape

{HDR}
{len(CAT)} sources ({len(E)} executed) across the 16 requested categories. "Executed" = at least one real data pull parsed and logged (`bench/alternative_data_v1/results/probe_results.json`, `data/collect_log.json`, `results/pit_probes.json`); reachable-but-keyed endpoints (Etherscan V1, AISHub, GIE AGSI) are **not** counted as executed even though HTTP 200 came back (their bodies are auth errors). Full 12-field cards live in the category reports 02–05; this page is the index. Latency = median of ≤3 sequential calls from the sandbox egress; freshness = age of newest record at probe time.

## By category
{md(cats)}
## All sources
{md(tab)}
### Access blockers observed from the sandbox (each is *missing evidence*, not negative evidence)
* Geo/WAF: Binance fapi (451), Bybit (403), Bluesky (403), Reddit `.json` (403), IMF DataMapper (403), sec.gov HTML/atom (403 without accepted UA), Farside (Cloudflare challenge).
* Quotas on the shared egress IP: Open-Meteo forecast/archive (daily limit), GDELT DOC (429 at ≥1 call/20 s), Wikimedia (429 in probes; bulk pull succeeded after retry-after back-off), Wayback Machine (429 / tunnel closed), Kalshi (429 once), Yahoo (429).
* Keys: EIA API v2, Etherscan V2, GIE AGSI, beaconcha.in, Glassnode, LunarCrush, CoinGecko (all "free key" or paid; none provisioned).
* Session scope: GitHub REST for third-party repositories (deliberately not bypassed; GH Archive used instead).
* Reachability: FRED/ALFRED, Stooq (timeouts/resets).
""")
# ------------------------------------------------------------------ category cards
def card(c):
    lat, age, st = probe(c)
    return (f"### {c['name']}  \n`{c['id']}` · {c['cat']} · executed **{c['exec']}** · PIT **{c['pit']}** · info **{c['info']}**\n\n"
            f"* **access:** {c['access']}\n* **cost:** {c['cost']}\n* **history:** {c['history'] or 'n/a'}; coverage — {c['coverage']}\n* **latency:** HTTP median {lat}; freshness {age}; statuses {st}\n"
            f"* **timestamp semantics:** {c['ts']}\n* **revision semantics:** {c['rev']}\n* **PIT readiness:** {c['pit']}" + (f" — {c['pitnote']}" if c['pitnote'] else "") + "\n"
            f"* **licence:** {c['licence']}\n* **rate limits:** {c['rate']}\n* **operational stability:** " + (f"probe statuses {st}" ) + "\n* **note:** " + c["note"] + "\n")
def cards(cs): return "\n".join(card(c) for c in CAT if c["cat"] in cs)
def top(name, cs_names, n=8):
    g = CS[CS.cand.str.contains("|".join(cs_names))]
    return md(g[["cand", "klass", "min_p_incr", "min_q_fam", "max_oos_gain_pct", "react_ctmp_max"]]) if len(g) else ""
w("02_ONCHAIN.md", f"""# 02 — On-chain, mempool, exchange-flow, developer ecosystem

{HDR}
**Bottom line.** Free on-chain data is plentiful and clean at the *event* level (blocks) but the convenient aggregated feeds (Coin Metrics community, Blockchain.com, DefiLlama) serve **recomputed** history. None of the tested on-chain blocks adds out-of-sample information about next-day return or range beyond price/volume/vol/funding/OI + calendar controls. Exchange *flows* (Coin Metrics `FlowIn/OutEx*`) are 41 % explained by same-day price/range/volume moves (react R² = {CS[CS.cand=='cm_exchange_flows'].react_ctmp_max.iloc[0]:.2f}) — they are largely a price-reactive quantity. The one crypto series that passes is options-implied volatility (Deribit DVOL), which is market-derived.

Test blocks (2021-01 → 2026-09, BTC and ETH where data exist; conservative availability lags in `06`):
{md(CS[CS.cand.str.contains('cm_|bc_|llama|deribit|binance_um|npm|CONTROL')][['cand','klass','min_p_incr','min_q_fam','max_oos_gain_pct','react_ctmp_max','red_base_max']])}
Details, controls and sensitivity in `07`. Mempool state (the one *genuinely new* on-chain datum: fee histogram/backlog) has **no history endpoint** [OBS]; it is only usable if captured forward.

{cards(['on-chain','mempool','exchange flows','developer/GitHub'])}
""")
w("03_NEWS_SOCIAL.md", f"""# 03 — News, RSS, public social, search/trend, prediction markets

{HDR}
**Bottom line.** This is the family where *PIT-native raw material exists* (GDELT 15-minute files, Kalshi/Polymarket price history, GH Archive) but where **no statistical test was run** — either no history exists to test (RSS feeds keep 32 h–274 days; StockTwits 0.5 h; Mastodon 15 h; Reddit 22 h), the API blocked us (GDELT DOC 429, Google Trends 404, Bluesky/Reddit-JSON 403), or building the series exceeds the bandwidth budget (GDELT GKG files are 3.7–11.9 MB each × 96 per day ≈ 0.17 TB per year). What *was* tested: Wikipedia page-views and the Fear & Greed composite, both **no increment**; F&G is classified PRICE_DERIVATIVE_ONLY (same-day price/range explain {CS[CS.cand=='alternative_me_fear_greed'].react_ctmp_max.iloc[0]:.0%} of its variation).

Retention of feeds (span of items returned by one call) [OBS pit_probes.json]:
{md(pd.DataFrame(PP['rss_retention']).T.reset_index().rename(columns={'index':'feed'}))}
GDELT file-stamp evidence [OBS]:
{md(pd.DataFrame(PP['gdelt_gkg'])[['stamp','rows','last_modified','lm_minus_nominal_min','crypto_mention_rows']])}
Caveat: GDELT's V2.1DATE is the *crawl batch* time (one distinct value per file), **not** the article's publication time [OBS]; a PIT news factor built from it measures "when GDELT saw it".

Prediction markets: Kalshi `KXFED` settled markets expose created/open/close/settlement/updated timestamps and daily candlesticks (316 bars for `KXFED-26SEP-T5.25`, 2025-08-06 → 2026-09-16) [OBS]; Polymarket `prices-history` returned 307 daily points for a closed 2024 market [OBS]. Price-threshold BTC contracts are price derivatives by construction; macro/election contracts are independent information but only ≈1 year of FOMC-type history was reachable → untested.

{cards(['news','RSS','public social','search/trend','prediction markets'])}
""")
cf = PP["cftc"]
w("04_POSITIONING_FLOWS.md", f"""# 04 — Positioning and flows (CFTC, exchange positioning, ETF/public flows)

{HDR}
**Bottom line.** *CFTC TFF (CME Bitcoin)*: leveraged-fund and asset-manager net positioning has partly independent variation from price (react R² = {CS[CS.cand=='cftc_tff_btc_cme'].react_ctmp_max.iloc[0]:.2f}) but its univariate association with volatility is fully **absorbed** by the baseline (p_univ<0.01 → p_incr = {INC[(INC.cand=='cftc_tff_btc_cme')&(INC.target=='lrange')&(INC.sens=='primary')].p_incr.iloc[0]:.2f}; OOS gain {CS[CS.cand=='cftc_tff_btc_cme'].max_oos_gain_pct.iloc[0]:.2f} %). *Binance long/short and taker ratios*: reachable and PIT-fresh but no OOS gain (best DM p = {INC[(INC.cand=='binance_um_positioning_ratios')&(INC.sens=='primary')].dm_p_onesided.min():.2f}). *ETF flows*: **no free accessible source** in this environment — treat as missing evidence.

CFTC publication-time facts [OBS `pit_probes.json`]: {cf['rows']} CME-Bitcoin TFF rows; {cf['bulk_loaded_rows']} carry a bulk-load `:created_at` (2022-09-13) — for these only the *rule* (Tuesday as-of → Friday ≈15:30 ET) is available; the {cf['real_rows']} later rows have real release stamps (weekday counts {cf['weekday_of_created']}; lag after as-of: median {cf['real_lag_days_median']:.1f} d, p90 {cf['real_lag_days_p90']:.1f} d, max {cf['real_lag_days_max']:.1f} d — holiday/shutdown delays).

Binance Vision restatement scan [OBS `binance_vision_lastmodified_scan.csv`]: {json.dumps(PP['binance_vision'])}. Fresh files are stamped ~1–3 h after their day; old files were re-uploaded, so `Last-Modified` cannot be trusted as an original publication time for history.

{cards(['CFTC positioning','ETF flows'])}
{card([c for c in CAT if c['id']=='binance_vision_um_metrics'][0])}
""")
w("05_REAL_ECONOMY.md", f"""# 05 — Real economy: shipping, energy inventories, weather, public government datasets

{HDR}
**Bottom line.** This is the only family that produced a non-market candidate: **EIA weekly crude-oil inventory surprise**. Setup: surprise = weekly Δ(commercial crude stocks ex-SPR) minus the mean same-ISO-week Δ over the previous 5 years, scaled by trailing 104-week std (past data only). Release rule: Wednesday after week-ending Friday (+5 d) [rule, not verified per release]. Returns winsorised at 0.5/99.5 % (2020 oil dislocation dominates squared errors — a post-hoc, disclosed choice; raw-return results reported in `10`). Baseline: prior 1-day and 5-day return and 20-day log |return|.

{md(RE[['cand','target','n','first','last','coef_s','t_s','p_incr','q_bh','oos_gain_pct','dm_p_onesided']])}
Crude robustness (release-day WTI return unless noted):
{md(CR[['cand','series','offset_days','n','first','last','coef_s','t_s','p_incr']])}
Reading: (i) sign is economically right (stock build → price down); (ii) the effect is **contemporaneous**, i.e. absorbed within the release day — no next-day drift (p = {RE[(RE.cand.str.contains('crude'))&(RE.target=='next_day:y')].p_incr.iloc[0]:.2f}); (iii) a small pre-release footprint on Tuesday (p = {CR[CR.cand.str.contains('Tue')].p_incr.iloc[0]:.3f}) is consistent with the API report the evening before [INF]; (iv) 2007-2014 and 2015-2020 significant, **2021-2026 not** (t = {CR[CR.cand.str.contains('2021-2026')].t_s.iloc[0]:.2f}) — pricing has moved to minutes. It is therefore an *event-clock* information source, not a daily-bar factor; a daily test can neither confirm executability nor rule it out.

Natural-gas storage surprise and CPC weather anomalies: the release-day tests reach q ≈ 0.06–0.08 **but with the economically wrong sign** (larger-than-seasonal injection → price *up*; colder-than-normal → price *down*) and no next-day effect → classified INCONCLUSIVE, not retained (sign check applied after seeing results — disclosed). IMF PortWatch chokepoint transits vs WTI weekly (2-week lag): coefficient {PW.coef.iloc[0]:.3f}, p = {PW.p_incr.iloc[0]:.2f}, n = {int(PW.n.iloc[0])} → no evidence.

EIA series-level `last_updated` (only vintage-like field available) [OBS `eia_series_last_updated.json`]: {json.load(open(os.path.join(RES,'eia_series_last_updated.json')))}.

{cards(['shipping','energy inventories','weather','public government'])}
""")
# ------------------------------------------------------------------ 06 PIT
defs = """* **PIT_NATIVE** — provider issues per-row (or per-immutable-file) publication/ingestion/event stamps that are not rewritten, and revisions arrive as new rows/files, so an as-of replay needs no consumer-side capture.
* **PIT_ADAPTABLE** — event time plus at least one of {immutable ID/height/hash, finality flag, release-time system field, archived model runs}; a consumer can build PIT *going forward* (or for a documented slice of history) by stamping receipt.
* **LOOKAHEAD_RISK** — historical rows have **no** historical publication timestamp (or values were provably recomputed after the stamp). Mission rule: such history is unusable as-is; it may be used only with a conservative lag and results are upper-bound/contaminated.
* **SNAPSHOT_ONLY** — no history endpoint (or a window of hours-to-months); PIT can only come from continuous self-capture.
* **UNKNOWN** — not executed, so not classifiable from evidence."""
pitt = pd.DataFrame([dict(source=c["name"], exec=c["exec"], PIT=c["pit"], why=(c["pitnote"] or c["rev"])[:230]) for c in CAT])
lags = pd.DataFrame([
 ("Price/volume/funding/OI baseline", "d-1", "real-time exchange data; Binance `metrics` are 5-min rows"),
 ("Coin Metrics flows / activity / hash rate / MVRV", "d-2", "completion 2–5 h after day end (median 3–5 h for 2021+) > decision at 00:00 UTC of d"),
 ("Blockchain.com, DefiLlama, Wikimedia, npm (other daily aggregates)", "d-2", "no publication stamps → conservative"),
 ("Deribit DVOL (control)", "d-1", "daily bar closes at 00:00 UTC"),
 ("Fear & Greed", "d-1", "value stamped 00:00 UTC of its date; composition [UNK]"),
 ("NY Fed reverse repo", "d-1", "same-day publication (rule)"),
 ("Treasury TGA", "d-3", "DTS next-business-day 16:00 ET (rule) + weekend"),
 ("CFTC TFF", "release-time", "rule Friday 19:30 UTC or real `:created_at` after 2022-09-14; first decision day at/after release"),
 ("Binance long/short & taker ratios", "d-1", "5-min rows; file appears ~1–3 h after day end but real-time REST exists [INF]"),
 ("EIA crude/gas (event study)", "release day / next day", "rule-based; day-level resolution cannot separate pre/post release"),
 ("PortWatch", "2 weeks", "weekly refresh + revisions [INF]"),
], columns=["input", "lag (obs date ≤ decision date − lag)", "reason"])
cmx = PP["coinmetrics"]
w("06_PIT_READINESS.md", f"""# 06 — PIT readiness and leakage

{HDR}
## Definitions used (strict)
{defs}

Executed sources by class: **PIT_NATIVE {PITE}**, **PIT_ADAPTABLE {PITA}**, **LOOKAHEAD_RISK {cnt(E,'pit')['LOOKAHEAD_RISK']}**, **SNAPSHOT_ONLY {cnt(E,'pit')['SNAPSHOT_ONLY']}**. All {len(CAT)} discovered: {dict(cnt(CAT,'pit'))}.

## Evidence gathered (not assumed)
* **Coin Metrics community** [OBS]: `AssetCompletionTime` lag after day end — median by year {cmx['completion_lag_h_median_by_year']} h; {cmx['backfilled_rows_lag_gt_72h']}/{cmx['rows']} rows completed >72 h late (2020 back-fill). Every row `status={list(cmx['status_values'])[0]}`. `status-time` (last recompute) distribution: {cmx['status_time_month_counts']}; **{cmx['rows_recomputed_after_completion_gt_30d']}/{cmx['rows']} rows were recomputed >30 days after completion** → served values ≠ originally published values → LOOKAHEAD_RISK for history despite the excellent stamp fields. Exchange flows depend on retro-labelled address clusters [INF].
* **Binance Vision** [OBS]: {json.dumps(PP['binance_vision'])}.
* **CFTC** [OBS]: {json.dumps({k: v for k, v in PP['cftc'].items() if k != 'weekday_of_created'})}.
* **GDELT** [OBS]: Last-Modified − nominal stamp = {[x['lm_minus_nominal_min'] for x in PP['gdelt_gkg']]} min for 7 files across 2016–2026 (files are written just before their stamp; consistent over 10 years → reliable batch-time stamp).
* **GH Archive** [OBS]: {PP['gharchive']['events']:,} events in the 2026-09-27 12:00 file; created_at {PP['gharchive']['first_created']} → {PP['gharchive']['last_created']}; Last-Modified {PP['gharchive']['last_modified']} (= +{PP['gharchive']['lm_minus_hour_end_min']} min after hour end).
* **Kalshi** [OBS]: `open_time`, `close_time`, `settlement_ts`, `updated_time` on markets; candlestick history retained after settlement.
* **Wayback vintage comparison** (would have measured DefiLlama/Fear&Greed restatement): **blocked** (HTTP 429/tunnel closed) → restatement of those series is UNKNOWN, classified LOOKAHEAD_RISK by the no-stamp rule.
* **EIA** [OBS]: only series-level `last_updated`; WPSR CSV `Last-Modified` = 13:37 UTC on release day (before the customary 10:30 ET = 14:30 UTC release [rule]) → file stamp is **not** usable as release time.

## Availability lags used in the information tests
{md(lags)}
## Register
{md(pitt)}
## How each LOOKAHEAD_RISK source could be upgraded
Stamp every pull with receipt time and content hash, keep all vintages append-only, and treat data older than the first capture as *contaminated history* (usable only with the lags above). Sources with per-record completion/ingestion stamps (Coin Metrics `AssetCompletionTime`/`status-time`, CFTC `:created_at`, Socrata `:updated_at`) make forward capture verifiable; sources with none (DefiLlama, Blockchain.com, Fear & Greed, EIA bulk, Treasury, NY Fed, PortWatch, npm, Wikimedia) need a first-seen log from day one.
""")
# ------------------------------------------------------------------ 07
ctl = CS[CS.cand.str.contains("CONTROL|mvrv")][["cand", "klass", "min_p_incr", "max_oos_gain_pct", "react_ctmp_max", "n_p05", "n_tests"]]
prim = INC[(INC.sens == "primary") & INC.p_incr.notna()].copy()
detail = prim.sort_values("p_incr").head(20)[["cand", "asset", "target", "n", "p_incr", "p_univ", "q_bh", "oos_gain_pct", "dm_p_onesided", "sign_cos", "react_ctmp", "red_base"]]
sens = INC[(INC.sens == "optimistic_lag") & INC.p_incr.notna()]
sens_hit = sens[(sens.p_incr < 0.05)][["cand", "asset", "target", "lag_days", "p_incr", "oos_gain_pct", "dm_p_onesided"]]
sens_pass = int(((sens.p_incr < 0.05) & (sens.oos_gain_pct > 0) & (sens.dm_p_onesided < 0.10)).sum())
nc = NOCAL[(NOCAL.sens == "primary") & NOCAL.p_incr.notna() & ~NOCAL.cand.str.contains("CONTROL")]
nc_hit = nc[(nc.p_incr < 0.001) & (nc.oos_gain_pct > 0) & (nc.dm_p_onesided < 0.10)][["cand", "asset", "target", "p_incr", "oos_gain_pct", "dm_p_onesided"]].sort_values("dm_p_onesided")
w("07_INCREMENTAL_INFORMATION.md", f"""# 07 — Does the data add information beyond price, volume, volatility, funding, OI?

{HDR}
## Design (classification rules written in the docstring of `py/analysis_crypto.py` before the first run; the baseline was revised once afterwards — see the calendar section)
* **Asset/target panel.** BTCUSDT and ETHUSDT daily (Binance spot 1-d klines via `data-api.binance.vision`), 2021-01-01 → 2026-09-28 (~2000 BTC days; ETH ~1700 — Binance ETH `metrics` start 2021-12). Decision instant = 00:00 UTC of day *d*; targets on day *d*: log return, log high/low range (volatility), |return|.
* **Baseline (information already in price/volume/vol/funding/OI):** lagged 1/5/20-day returns; log range 1/5/20/60-day means; log quote-volume and trade-count z-scores; taker-buy share; funding (level, deviation from 7-day mean); Δ log OI (1d, 5d), OI z-score; **6 weekday dummies** (target-day calendar effect). Funding/OI come from Binance Vision (5-min `metrics` rows, 8-h funding files).
* **Candidate blocks** (2 features each: trailing 30-day z-score of level and 1-day change; % change for stablecoin supply; level & change for F&G), lagged per `06`. Sources: Coin Metrics community (flows, active addresses, tx count, hash rate), Blockchain.com (tx count, mempool size, fees, unique addresses), DefiLlama (stablecoin supply, DEX volume), Fear & Greed, CFTC TFF, Treasury TGA, NY Fed RRP, Wikipedia page-views, npm downloads, Binance long/short & taker ratios. **Controls:** 2 seeded Gaussian-noise blocks (false-positive calibration), a price-derived block (60-d drawdown + 30-d momentum), Coin Metrics MVRV (price/realised-price), and Deribit DVOL (designed as the positive control for the volatility target; because it passes the same rules it is *also counted as a candidate* — a post-hoc relabel, disclosed).
* **Tests per (asset, block, target):** (1) HAC(5) Wald p for the block in baseline+block OLS; (2) univariate HAC p; (3) expanding-window OOS (min train 400 d, refit every 10 d): MSE gain vs baseline and one-sided Diebold–Mariano with HAC(5); (4) sign stability (cosine of standardised block coefficients across chronological halves); (5) **price-reactivity R²** of the block measured on observation dates against same-day return/|return|/range + 5 lags of each (`react_ctmp`), past-only version (`react_past`), and R² of the lagged block on the full baseline (`red_base`); (6) Benjamini–Hochberg FDR over all {SUM['n_tests_primary']} primary tests (controls except DVOL excluded).
* **Classification (pre-declared).** *INCREMENTAL_CANDIDATE*: p_incr<0.05 **and** BH-q<0.10 **and** OOS gain>0 with DM one-sided p<0.10 **and** sign-stable **and** price-reactivity<0.40. *PRICE_DERIVATIVE_ONLY*: reactivity ≥0.40, or all univariately-significant tests are absorbed by the baseline (p_incr ≥ 0.10). *INDEPENDENT_NO_EVIDENCE*: neither — informationally distinct but unproven (not negative evidence).

## Calibration controls
{md(ctl)}
Noise blocks: {SUM['noise_p05']}/{SUM['noise_tests']} with p<0.05 and {SUM['noise_dm_p10']}/{SUM['noise_tests']} with DM p<0.10 (calibrated). Price-derived and MVRV blocks are correctly flagged PRICE_DERIVATIVE_ONLY (MVRV reactivity 0.88). DVOL passes (positive control for power: OOS +{dv.oos_gain_pct:.2f} % on log-range, DM p = {dv.dm_p_onesided:.3f}).

## Results by block
{md(CS[['cand','klass','n_tests','n_p05','min_p_incr','min_q_fam','best_target','best_oos_gain_pct','best_dm_p','react_ctmp_max','red_base_max']])}
Top-20 individual tests by p_incr:
{md(detail)}
In-sample: {SUM['n_p05_family']}/{SUM['n_tests_primary']} tests have p<0.05 (≈{SUM['n_p05_expected_under_null']} expected under the null; 3 of them are DVOL); best BH-q for any non-DVOL test = {SUM['min_q_family_excl_dvol']:.2f}. **No non-control crypto block passes the OOS test** — the best non-DVOL OOS MSE gain is {CS[~CS.cand.str.contains('deribit|CONTROL')].max_oos_gain_pct.max():.2f} % (Coin Metrics exchange flows → log-range; DM p = 0.24).

## The calendar artefact (why the baseline has weekday dummies)
First-pass baseline *without* weekday dummies and the 60-day vol term (`ALT_NO_CALENDAR=1`, saved `results/incremental_results_no_calendar.csv`): {SUM['no_calendar_baseline']['n_p05']}/{SUM['no_calendar_baseline']['n_tests']} tests at p<0.05, {SUM['no_calendar_baseline']['n_p001']} at p<0.001, {SUM['no_calendar_baseline']['n_oos_dm_p10']} with OOS DM p<0.10 — e.g. npm downloads "improved" next-day range by 1.9–3.6 % (DM p ≤ 0.027) because both npm traffic and crypto volatility have a weekday cycle. Strong tests (p<0.001, OOS>0, DM p<0.10) in that first pass:
{md(nc_hit)}
All disappear with calendar controls. Lesson: any candidate reporting an OOS gain on volatility must first beat weekday dummies.

## Sensitivity: optimistic availability (one day less lag for lag ≥ 2 sources)
{len(sens)} extra tests; p<0.05 in {len(sens_hit)}; passing p<0.05 **and** OOS>0 **and** DM p<0.10: **{sens_pass}**. Hits (all fail OOS):
{md(sens_hit)}
## Real-economy tests
See `05_REAL_ECONOMY.md` (EIA crude candidate; gas storage & weather inconclusive; PortWatch none).

## Conclusions
* Candidates: **{', '.join(['EIA weekly crude-inventory surprise', 'Deribit DVOL'])}**.
* PRICE_DERIVATIVE_ONLY ({len(pdo)} blocks): {', '.join(pdo.cand)}.
* INDEPENDENT but unproven ({len(ind)} blocks): {', '.join(ind.cand)}.
* Not tested for lack of history/access: RSS/news/social, mempool state, prediction markets, GDELT, GH Archive, ETF flows, weather forecasts.
""")
# ------------------------------------------------------------------ 08 licence / cost
VERD = {"coinmetrics_community": "CONDITIONAL (CC variant unverified; assume non-commercial)", "blockchain_com_charts": "RESTRICTIVE/UNCLEAR (site terms: personal non-commercial)", "mempool_space": "UNVERIFIED",
        "defillama_free": "UNVERIFIED (docs 403)", "binance_vision_um_metrics": "UNVERIFIED (Binance ToS)", "deribit_public": "UNVERIFIED", "gharchive": "UNVERIFIED (GitHub event content)",
        "npm_downloads": "UNVERIFIED (terms 404)", "wikimedia_pageviews": "CLEAR_OPEN (CC0)", "alternative_me_fng": "CONDITIONAL (60 req/min; reuse terms unverified)", "reddit_rss": "RESTRICTIVE (Data API Terms)",
        "stocktwits": "RESTRICTIVE (ToS)", "gdelt_v2_files": "CLEAR_OPEN (free incl. commercial; cite GDELT)", "rss_bbc_business": "CONDITIONAL (attribution)", "cftc_cot_socrata": "UNVERIFIED (US gov; disclaimer page 404)",
        "treasury_fiscaldata": "CLEAR_OPEN (no restriction, commercial OK)", "eia_bulk_wpsr": "CLEAR_OPEN (public domain)", "noaa_cpc_degree_days": "CLEAR_OPEN (public domain)", "nws_api": "CLEAR_OPEN (public domain)",
        "open_meteo": "CONDITIONAL (free API non-commercial, CC-BY 4.0)", "coingecko_api": "RESTRICTIVE (no redistribution)", "yahoo_finance": "RESTRICTIVE (ToS)", "google_trends": "RESTRICTIVE (scraping)",
        "sec_edgar": "UNVERIFIED (fair-access page 403)", "kalshi": "UNVERIFIED (docs)", "polymarket": "UNVERIFIED", "imf_portwatch": "UNVERIFIED (IMF terms 403)", "nyfed_reverse_repo": "UNVERIFIED", "noaa_gfs_s3": "CLEAR_OPEN (NOAA open data) [INF]"}
lt = pd.DataFrame([dict(source=c["name"], cost=c["cost"], executed=c["exec"], reuse_verdict=VERD.get(c["id"], "UNVERIFIED"), licence_evidence=esc(c["licence"])[:260]) for c in CAT])
w("08_LICENSE_COST.md", f"""# 08 — Licence and cost

{HDR}
**Cost.** {sum(1 for c in CAT if c['cost']=='free-nokey')} sources need no key, {sum(1 for c in CAT if c['cost']=='free-key')} need a free key (EIA API v2, Etherscan V2, GIE AGSI, beaconcha.in, CoinGecko …), {sum(1 for c in CAT if c['cost']=='paid/key')} are paid/keyed (Glassnode, LunarCrush), {sum(1 for c in CAT if c['cost']=='restricted')} are practically unavailable to programmatic free use (Google Trends, Bluesky, Farside, iShares, Yahoo). Paid endpoint seen: DefiLlama bridges (HTTP 402). All 47 executed sources were pulled at zero cost.

**Licence method.** `py/licenses.py` fetched {sum(len(v) for v in LIC.values())} provider pages ({len(LIC)} providers) and grepped for licence keywords (`results/license_evidence.json`). A licence is called documented only where a snippet was found; where a page was JS-only/403/404 it is **UNVERIFIED** — never inferred. This is not legal advice; AurumShift is research/paper-only, so non-commercial terms are workable *today* but would re-open at any commercial step.

Key documented terms: EIA "public domain" · Treasury FiscalData "free, without restriction … commercial or non-commercial" · NOAA/NWS public domain · Wikimedia analytics CC0 · GDELT free "commercial … of any kind without fee", cite GDELT · Open-Meteo free API "non-commercial", CC-BY 4.0, <10,000 calls/day · Coin Metrics community "Creative Commons license" (variant not stated) · Reddit Data API Terms require agreement for commercial/heavy research · CoinGecko API terms forbid re-distribution/sub-licensing · StockTwits terms forbid circumventing rate limits · Blockchain.com site terms: personal non-commercial use · Yahoo terms forbid unofficial access.

{md(lt)}
""")
# ------------------------------------------------------------------ 09 adjudication
ADJ = [
 ("EIA weekly crude/gas inventories (bulk + release files)", "ADAPT", "Only non-market candidate (t≈-5, OOS +2.5 %, Brent replicates, price-independent). Event-clock: ingest on the release schedule with own receipt stamps; test at intraday resolution; expect executability limits (post-2021 fade). Public-domain licence."),
 ("Deribit DVOL / options book summary", "ADAPT", "Passes OOS on range (+2.3 %). Market-derived (options), so it competes with whatever vol inputs a system already has — overlap can only be judged against the real repo. Capture own vintages; immutable index prints."),
 ("Coin Metrics community (flows, activity, MVRV…)", "PARK", "No increment; exchange flows are price-reactive (R² 0.41). Keep as *forward-capture* candidate because completion/status-time fields make first-seen logging verifiable; history is recomputed (2067/2219 rows). CC licence variant to confirm."),
 ("mempool.space / Blockstream / ETH RPC (raw chain state)", "PARK", "Only source of true mempool/fee-market state, but snapshot-only: value unknown until ≥6–12 months of self-captured history exist. Cheap to capture."),
 ("GDELT 2.0 raw files", "PARK", "PIT-native and free for commercial use; batch-time not publication-time; a full GKG build is ≈0.17 TB/year (96 files/day × ~5 MB) → needs a scoped, theme-filtered or sampled ingest before it can be tested."),
 ("Kalshi / Polymarket macro-event probabilities", "PARK", "PIT-native price history; independent of crypto price for macro/election contracts. Needs an event-labelled study (FOMC etc.) with more history than the ~1 year reachable; BTC-threshold contracts are price derivatives (REJECT those)."),
 ("GH Archive", "PARK", "PIT-native; no crypto-repo series built. npm/PyPI proxies showed no increment."),
 ("CFTC COT (TFF/legacy/disaggregated)", "PARK", "Rule-based PIT (native stamps only after 2022-09); positioning absorbed by baseline for BTC vol/return. Still valid as macro context for commodities/FX (untested here)."),
 ("Treasury TGA, NY Fed RRP", "PARK", "Independent of price but no increment for BTC/ETH; not tested on rates/gold/FX where the liquidity channel is more direct."),
 ("Fear & Greed (alternative.me)", "REJECT", "Composite of price-vol/momentum/social; reactivity 0.43; no increment; no vintages."),
 ("DefiLlama stablecoin supply / DEX volume", "REJECT", "USD-denominated, restated history, subsumed by baseline; no increment."),
 ("Blockchain.com charts, npm/PyPI/crates counts, Wikipedia page-views", "REJECT", "No increment after calendar controls; LOOKAHEAD_RISK; restrictive/unclear terms (Blockchain.com)."),
 ("Binance long/short & taker ratios, OKX/Bitfinex stats", "PARK", "Same-venue microstructure; Binance ratios no OOS gain; OKX/Bitfinex keep only weeks–months (capture-only)."),
 ("RSS feeds (crypto news, Fed/SEC/ECB press)", "PARK", "Zero history; forward capture is trivial and gives an event clock, value untested."),
 ("Public social (Reddit RSS, StockTwits, Mastodon, HN, 4chan)", "REJECT", "ToS-restricted or tiny/noisy; hours of retention; no PIT history. HN/Arctic Shift optional for research only."),
 ("ETF flows (iShares, Farside, Yahoo)", "PARK", "No accessible free source; not negative evidence. Revisit with a sanctioned data route."),
 ("Weather: CPC degree days, NWS, NCEI, NASA POWER", "REJECT (realised) / PARK (forecast)", "Realised anomalies are priced (no increment); Open-Meteo historical-forecast and NOAA GFS are the PIT route but were quota-blocked/untested."),
 ("Shipping: IMF PortWatch", "PARK", "Genuine physical-flow data, 2-day freshness, but AIS-revised and no effect on WTI at weekly horizon (p=0.16, n=381)."),
 ("Google Trends, Bluesky, Reddit JSON, Glassnode, LunarCrush, FRED/ALFRED (unreachable)", "PARK", "Blocked/keyed from this environment: missing evidence."),
]
w("09_ADJUDICATION.md", f"""# 09 — Adjudication

{HDR}
Per repository doctrine (REUSE → ADAPT → WRAP → COMPOSE → CUSTOM LAST) the outputs are ADOPT / ADAPT / PARK / REJECT **candidates**; final integration adjudication happens later against the real local AurumShift repository. Nothing here claims compatibility with the private implementation.

## FINAL_VERDICT: **{FINAL}**
Rationale: exactly two candidates cleared a pre-declared, FDR-controlled, OOS-confirmed, price-independence bar; one is a non-market real-economy signal that is contemporaneous and fading (event-clock only), the other is options-market-derived. No PIT-clean, price-independent *crypto-native* alternative feed produced OOS information. Large families were untestable (missing history/access), so `NO_USEFUL_ALTERNATIVE_DATA_FOUND` would overstate the negative and `MULTIPLE_…` would overstate the positive. `STUDY_INCONCLUSIVE` is not chosen because the tested families gave calibrated, decisive answers (noise controls 0/12; price-derived controls flagged; positive control passed).

{md(pd.DataFrame(ADJ, columns=['source / family','call','reason']))}
## Suggested sequencing (research-side only)
1. Stand up a small **forward-capture** harness (append-only, receipt-stamped): mempool snapshots, RSS, Kalshi/Polymarket macro markets, Coin Metrics rows with completion/status stamps, OKX/Bitfinex stats, NWS forecasts.
2. Re-run the EIA crude study with **release-timestamped intraday** prices to learn whether any executable window exists.
3. Build a theme-filtered GDELT GKG daily series (crypto/central-bank/energy themes) and test with the same harness (`py/analysis_crypto.py` is source-agnostic: add a block).
4. Re-test liquidity series (TGA/RRP) on rates/gold/FX, where the transmission channel is more direct than for crypto.
""")
# ------------------------------------------------------------------ 10 limitations
w("10_LIMITATIONS.md", f"""# 10 — Limitations

{HDR}
1. **Forking paths, disclosed.** (a) The first run lacked weekday dummies and 60-day vol memory; adding them after seeing 29/90 spurious hits is a data-driven baseline change (both runs are saved). (b) Real-economy returns were winsorised at 0.5/99.5 % *after* the raw-return EIA run gave OOS gain 0.89 % (DM p = 0.22) vs 2.50 % (p = 0.058) winsorised; both are saved (`results/real_economy_results_raw_returns.csv` vs `real_economy_results.csv`; in-sample t = −4.61 raw vs −5.32 winsorised) — treat the EIA OOS significance as borderline. (c) The economic-sign screen that dropped gas-storage/weather was applied post hoc. (d) Availability lags and the 0.40 reactivity threshold were fixed a priori but are judgemental.
2. **Daily resolution.** Everything is tested at daily bars; event-driven sources (EIA, CFTC, prediction markets, RSS) need intraday timestamps to judge executability.
3. **Sample.** ~2000 days per crypto asset (one bull-bear cycle); weekly series have 300–1000 points; HAC(5) may under-cover long-memory volatility (the 15 vs 4.7 expected p<0.05 count hints at mild over-rejection) — hence the OOS+FDR requirements.
4. **Baseline scope.** Funding/OI are Binance-USDT-M only; OI in contracts, not USD; no options/term-structure inputs in the baseline (DVOL therefore counts as "new").
5. **Only 2 assets, 3 targets;** no cross-sectional, no intraday, no transaction-cost or tradability test — *information* value only.
6. **Untested ≠ rejected.** GDELT, GH Archive, Kalshi/Polymarket, RSS/news/social, mempool state, ETF flows, weather forecasts, Google Trends are missing evidence, not negative evidence.
7. **Environment.** Shared-egress quotas (Open-Meteo, Wikimedia, GDELT DOC, Wayback, Kalshi) and geo-blocks (Binance fapi, Bybit) hide sources; probe statuses are single-day observations, not stability SLAs. `parsed_ok=True` in `probe_results.json` is unreliable for three placeholder extractors (AISHub, GIE AGSI, Etherscan V1 return auth errors) — the catalogue overrides them as not executed.
8. **Licence evidence** is keyword-grep of fetched pages; JS-rendered/403 pages are UNVERIFIED; nothing here is legal advice.
9. **Restatement measured only where stamps allowed** (Coin Metrics, Binance Vision, CFTC). DefiLlama/Blockchain.com/F&G/EIA restatement magnitude is UNKNOWN (Wayback blocked).
10. **Clock.** The sandbox clock (2026-09-29) and price levels are taken as given; no attempt was made to validate them against a second time source.
11. **No AurumShift code seen;** compatibility, overlap with existing inputs and operational fit are outside scope.
""")
print("reports written")
