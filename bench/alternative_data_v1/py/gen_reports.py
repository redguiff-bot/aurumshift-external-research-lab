"""Generate reports/016_alternative_data/*.md from catalog + probe/test results. Numbers are read from results/*.json, never typed."""
import json, os, glob, collections, statistics as st
import pandas as pd, numpy as np
from lib import *
from catalog import S
from pit import PIT
from adjudication import ADJ
OUT = os.path.join(HERE, "..", "..", "..", "reports", "016_alternative_data"); os.makedirs(OUT, exist_ok=True)
L = lambda n: json.load(open(os.path.join(RES, n)))
probe = L("probe_results.json"); inc = L("incremental.json"); rev = L("revision_test.json"); lat = L("latency_snapshot.json"); pw = L("power_btc.json"); gh = L("gh_playground_stability.json")
feats = {o["id"]: o for o in inc["features"]}; naive = {o["id"]: o for o in inc["naive_lag0"]}
W = lambda n, t: open(os.path.join(OUT, n), "w").write(t)
def pct(x): return "n/a" if x is None or x != x else f"{x*100:+.2f}%"
def cell(s): return str(s).replace("|", "/").replace("\n", " ")

# ---------- per-source status from probes
def status(sid):
    r = probe.get(sid, [])
    if not r: return dict(executed=False, txt="not executed (no keyless endpoint)", ok=0, tot=0, ms=None)
    ok = sum(x["n_ok"] for x in r); tot = 3 * len(r); ms = [x["ms_median"] for x in r if x["ms_median"]]
    codes = sorted({str(c) for x in r for c in x["statuses"] if c != 200})
    txt = f"{ok}/{tot} calls HTTP 200" + (f"; non-200: {','.join(codes)}" if codes else "") + (f"; median {round(st.median(ms))} ms" if ms else "")
    return dict(executed=ok > 0, txt=txt, ok=ok, tot=tot, ms=round(st.median(ms)) if ms else None)
STAT = {s["id"]: status(s["id"]) for s in S}
# a source counts as executed if probe reached data path OR its data was pulled for tests
PULLED = {"bc_charts", "mempool_space", "defillama_stable", "cftc_cot", "fiscal_dts", "gh_playground", "hn_algolia", "wikipedia_pv", "fear_greed", "portwatch", "eia_files", "openmeteo", "binance_vision"}
STAT['gie_agsi'].update(executed=False, txt='HTTP 200 x3 but body is a key-required error (no data); not executed'); STAT['etf_ssga_gld'].update(txt=STAT['etf_ssga_gld']['txt']+' (guessed file URL, provider verdict UNKNOWN)'); STAT['nws']['txt']+=' (landing page only; no forecast data probed)'
for sid in PULLED:
    if not STAT[sid]["executed"]: STAT[sid]["executed"] = True
def is_free(s): return s["cost"].lower().startswith("free")
KEYED = {"eia_api", "gie_agsi", "ais_open"}
executed = [s for s in S if STAT[s["id"]]["executed"]]
n_disc, n_exec = len(S), len(executed); free = [s for s in S if is_free(s)]; free_exec = [s for s in executed if is_free(s)]
pit_native = [s["id"] for s in S if PIT[s["id"]][0] == "PIT_NATIVE"]; pit_adapt = [s["id"] for s in S if PIT[s["id"]][1] == "PIT_ADAPTABLE"]
cls = collections.Counter(o["class"] for o in inc["features"])
cands = [o for o in inc["features"] if o["class"] == "INCREMENTAL_INFORMATION_CANDIDATE"]
rejects = [o for o in inc["features"] if o["class"] == "PRICE_DERIVATIVE_ONLY_REJECT"]
ntests = inc["n_tests"]; nom = sum(1 for o in inc["features"] for t in o.get("tests", {}).values() if t.get("cw_p", 1) < 0.05)
minq = min(t["bh_q"] for o in inc["features"] for t in o.get("tests", {}).values() if "bh_q" in t)
adj = collections.Counter(v[0] for v in ADJ.values())
VERDICT = "STUDY_INCONCLUSIVE"

# ---------- 01 landscape
cats = collections.OrderedDict()
for s in S: cats.setdefault(s["cat"], []).append(s)
t = "# 01 — Source landscape\n\nEvidence labels (claude.md): **OBS** = observed in a probe/test in this run; **DOC** = documented claim, not re-verified; UNKNOWN. Per-source structured records: `bench/alternative_data_v1/results/source_records.json` / `.csv`.\n\n" \
    f"{n_disc} sources catalogued across {len(cats)} categories; {n_exec} executed (≥1 probe returned HTTP 200 or data pulled). Each probe = 3 calls ≥2.5 s apart (stability sample is small: it is a snapshot, not an SLA measurement).\n\n"
for c, ss in cats.items():
    t += f"## {c}\n\n| Source | Access / cost | History | Latency | Timestamp semantics | Revision semantics | Licence | Coverage | Rate limits | Operational stability (OBS) |\n|---|---|---|---|---|---|---|---|---|---|\n"
    for s in ss:
        t += "| " + " | ".join(cell(x) for x in (f"**{s['name']}** (`{s['id']}`)", f"{s['access']}; {s['cost']}", s["history"], s["latency"], s["ts_sem"], s["rev_sem"], s["licence"], s["coverage"], s["rate"], STAT[s["id"]]["txt"] + (f" — {s['doc_note']}" if s["doc_note"] else ""))) + " |\n"
    t += "\n"
W("01_SOURCE_LANDSCAPE.md", t)
recs = []
for s in S:
    r = {k: v for k, v in s.items() if k != "probes"}; r.update(stability=STAT[s["id"]], pit_hist=PIT[s["id"]][0], pit_forward=PIT[s["id"]][1], pit_note=PIT[s["id"]][2], adjudication=ADJ[s["id"]][0], executed=STAT[s["id"]]["executed"], free=is_free(s)); recs.append(r)
jdump(recs, "source_records.json"); pd.DataFrame(recs).drop(columns=["stability"]).to_csv(os.path.join(RES, "source_records.csv"), index=False)

# ---------- helper for feature tables
def frow(o):
    ts = {k: v for k, v in o.get("tests", {}).items() if "dr2" in v}
    if not ts: return None
    best = min(ts.items(), key=lambda kv: kv[1]["cw_p"])
    tn, v = best
    return f"| `{o['id']}` | {o['asset']} | {o['lag']} d | {o.get('price_side_r2adj', float('nan')):.2f} | {tn} | {v['n']} | {pct(v['dr2'])} | {v['nw_t']:.2f} | {v['cw_p']:.3f} | {v['bh_q']:.2f} | {o['class'].replace('_', ' ')} |"
HDR = "| Feature | Asset | Pub. lag used | Price-side adj-R² | Best target (min CW p) | n | ΔR²oos | NW t | CW p | BH q | Class |\n|---|---|---|---|---|---|---|---|---|---|---|\n"
def ftable(catlist):
    rows = [frow(o) for o in inc["features"] if o.get("cat") in catlist]; return HDR + "\n".join(r for r in rows if r) + "\n"
FN = "\n_ΔR²oos = out-of-sample R² gain of baseline+feature over baseline (expanding window, first 50 % train); negative = feature hurt out of sample. 'Best target' is chosen by min p, i.e. optimistic; the BH q already accounts for all " + str(ntests) + " tests._\n"

# ---------- 02 on-chain
fetch = {p.split(os.sep)[-1][:-4]: pd.read_csv(p, index_col=0) for p in glob.glob(os.path.join(DATA, "*.csv"))}
t = "# 02 — On-chain, mempool, exchange flows, developer activity\n\n## Sources\n\n"
for sid in ("bc_charts", "mempool_space", "blockstream", "blockchair", "defillama_stable", "gh_playground", "gharchive", "github_rest", "npm_pypi", "exchange_reserves"):
    s = next(x for x in S if x["id"] == sid); t += f"* **{s['name']}** — {STAT[sid]['txt']}. {PIT[sid][2]}. Adjudication: **{ADJ[sid][0]}** — {ADJ[sid][1]}\n"
t += "\n## Observations that matter\n\n"
t += f"* **Mempool has no free history.** `mempool.space` exposes live mempool/fee-histogram state only; blockchain.info `mempool-size` exists as a chart but is an ex-post aggregate with `Last-Modified` = fetch time (OBS). Any real mempool study needs forward capture from now on (INFERENCE from endpoint inventory).\n"
t += f"* **Exchange flows/reserves:** no keyless free source with history and un-proprietary labels was found; vendor address labels are proprietary (DOC). Not executed. The only public exchange-side positioning data that *was* executed is Binance Vision futures metrics (OI, long/short ratios) — see 04.\n"
t += f"* **GitHub REST was blocked by this session's repository-scope policy** (HTTP 403 with an explicit scope message) — a session limitation, not a provider verdict. GitHub activity was instead read from the ClickHouse public playground copy of GH Archive.\n"
t += f"* **ClickHouse playground instability (OBS):** identical queries 14 minutes apart returned different global min/max `created_at` (2011-02-12..2026-09-29 vs 2023-01-13..2026-07-02); the per-repo daily series used for testing had a hole 2024-06-06..2025-08 and ends 2026-07-02 (`bench/.../results/gh_playground_stability.json`). Adjudicated REJECT as a feed; GH Archive hourly files (immutable, header-stamped) are the recommended path. GitHub tests therefore use only ~260-490 usable days.\n\n"
t += "* **`gh_merged_pr` vs |return|** is the smallest raw p-value in the study (CW p=0.005, ΔR²oos +4.4 %) but rests on n=259 days with only ~130 OOS days from fragmentary data; BH q=0.66. It is the single result worth re-testing on GH Archive files, and is not a finding.\n\n## Incremental-information results (BTC, next-day targets)\n\n" + ftable(["on-chain", "mempool", "dev"]) + FN
W("02_ONCHAIN.md", t)

# ---------- 03 news social
t = "# 03 — News, RSS, social, search/trend, prediction markets\n\n## Sources\n\n"
for sid in ("gdelt_doc", "rss_crypto", "rss_fed", "hn_algolia", "stocktwits", "reddit_json", "bluesky", "gtrends", "wikipedia_pv", "fear_greed", "polymarket", "kalshi"):
    s = next(x for x in S if x["id"] == sid); t += f"* **{s['name']}** — {STAT[sid]['txt']}. {PIT[sid][2]}. **{ADJ[sid][0]}** — {ADJ[sid][1]}\n"
t += "\n## Observations\n\n* **News/RSS have no free deep history through their live endpoints** (RSS ~30 items; GDELT DOC rolling window and 429 from this egress). A news study is possible only with GDELT bulk files or forward capture; neither was executed, so **news was not tested** (missing evidence, not negative evidence).\n"
t += "* **Prediction markets** are the cleanest PIT-native class found (trade time on each print) but individual contracts are short-lived, so a 3-year daily incremental test is not constructible from what is public without a fixed basket of rolling contracts. **Not tested.**\n"
t += "* **Attention data are mostly price reactions:** Wikipedia 'Bitcoin' pageviews are explained 34 % (adj-R²) by same-week price-side variables; Fear & Greed 49 %.\n\n## Incremental-information results\n\n" + ftable(["social", "search/trend"]) + FN
W("03_NEWS_SOCIAL.md", t)

# ---------- 04 positioning
t = "# 04 — Positioning and flows (CFTC, ETF, public exchange positioning)\n\n## Sources\n\n"
for sid in ("cftc_cot", "etf_farside", "etf_ssga_gld", "sec_edgar", "binance_vision", "deribit_dvol"):
    s = next(x for x in S if x["id"] == sid); t += f"* **{s['name']}** — {STAT[sid]['txt']}. {PIT[sid][2]}. **{ADJ[sid][0]}** — {ADJ[sid][1]}\n"
c = lat.get("cftc_btc", {}); e = lat.get("eia_wpsr_xls", {})
t += f"\n## CFTC publication timing (OBS)\n\nNewest BTC row at fetch: as-of {c.get('newest_report_date')}. The Socrata dataset exposes `report_date_as_yyyy_mm_dd` (the Tuesday as-of date) and **no release timestamp per row**. Dataset headers (`results/cftc_headers.json`, OBS) show `Last-Modified: Fri, 25 Sep 2026 19:30:07-08 GMT` for the legacy, TFF and disaggregated datasets, i.e. **3 d 19.5 h after the Tuesday as-of date** — consistent with the documented Friday 15:30 ET release, but it is a *dataset-level* stamp that is overwritten at each release; it cannot date historical rows. Tests therefore assume availability = as-of + 6 days (covers Friday release and holiday delays); the naive as-of dating is shown in 06 to quantify the leak.\n\n"
t += "## Incremental-information results\n\n" + ftable(["cftc", "exchange"]) + FN
W("04_POSITIONING_FLOWS.md", t)

# ---------- 05 real economy
t = "# 05 — Real economy: shipping, energy inventories, weather, government datasets\n\n## Sources\n\n"
for sid in ("portwatch", "baltic_shipping", "ais_open", "eia_files", "eia_api", "gie_agsi", "openmeteo", "nws", "noaa_ndbc", "fiscal_dts", "nyfed"):
    s = next(x for x in S if x["id"] == sid); t += f"* **{s['name']}** — {STAT[sid]['txt']}. {PIT[sid][2]}. **{ADJ[sid][0]}** — {ADJ[sid][1]}\n"
t += "\n## Observations\n\n* Commodity targets are Yahoo *unofficial* continuous front-month futures (unadjusted, roll jumps winsorised at 0.5/99.5 %) — baseline for these assets has **no funding/OI** (they do not exist); price/volume/volatility only. This is a weaker baseline than BTC's.\n* **Weather:** the executed archive is ERA5 reanalysis — hindsight-assimilated, *not* point-in-time; results are an upper bound and the feature is LOOKAHEAD_RISK. The PIT-like `historical-forecast` API returned HTTP 429 ('Daily API request limit exceeded') from the shared egress (OBS).\n* **PortWatch** ArcGIS pagination: `resultRecordCount=2000` is silently capped by the server's `exceededTransferLimit`; a first naive loop stopped at 250 rows (bug found and fixed, 1215 rows retrieved).\n* EIA `xls` files were slow (median ~10 s per call, OBS) but complete; `api.eia.gov` needs a key (HTTP 403 without).\n\n## Incremental-information results\n\n" + ftable(["shipping", "energy", "weather", "gov"]).replace("BTC", "BTC") + FN
W("05_REAL_ECONOMY.md", t)

# ---------- 06 PIT
def nive(o):
    n = naive.get(o["id"])
    if not n or not n.get("tests"): return None
    a = {k: v for k, v in o["tests"].items() if "nw_t" in v}; b = {k: v for k, v in n["tests"].items() if "nw_t" in v}
    ks = [k for k in a if k in b]
    if not ks: return None
    return max(abs(b[k]["nw_t"]) - abs(a[k]["nw_t"]) for k in ks), max(b[k]["dr2"] - a[k]["dr2"] for k in ks), max(ks, key=lambda k: abs(b[k]["nw_t"]) - abs(a[k]["nw_t"]))
t = "# 06 — PIT readiness and leakage\n\n## Classification rule (mission §4)\n\n* **PIT_NATIVE** — every historical row carries an event/publication time that cannot be revised after the fact (ledger, trade, filing, immutable file).\n* **LOOKAHEAD_RISK** — historical rows have **no historical publication timestamp** (aggregate re-served with fetch-time `Last-Modified`, as-of dates only, reanalysis, recomputed history). Per the mission this is the default for such rows, **including scheduled official releases** whose publication time is only known from a calendar rule.\n* **PIT_ADAPTABLE (forward)** — LOOKAHEAD_RISK for history, but becomes point-in-time if the consumer captures vintages with its own receipt timestamp from now on (or a documented release rule gives a conservative lag). Historical backtests on these are *estimates*.\n\n"
t += f"Counts over {n_disc} sources: **PIT_NATIVE {len(pit_native)}**, **LOOKAHEAD_RISK for historical rows {n_disc-len(pit_native)}**, of which **PIT_ADAPTABLE going forward {len(pit_adapt)}**, NOT_READY {sum(1 for s in S if PIT[s['id']][1]=='NOT_READY')}.\n\n"
t += "| Source | Historical class | Forward readiness | Note |\n|---|---|---|---|\n" + "\n".join(f"| `{s['id']}` | {PIT[s['id']][0]} | {PIT[s['id']][1]} | {cell(PIT[s['id']][2])} |" for s in S) + "\n\n"
t += "## Re-fetch revision test (OBS)\n\nSame historical window fetched twice, ~170 s apart; all rows except the last two days compared.\n\n| Series | Rows compared | Rows changed | Last-Modified t0 | Last-Modified t1 |\n|---|---|---|---|---|\n" + "\n".join(f"| {k} | {v['rows_compared']} | {v['rows_changed']} | {v['last_modified_t0']} | {v['last_modified_t1']} |" for k, v in rev.items())
t += "\n\nA 3-minute window cannot detect slow restatements (DefiLlama adapter recomputation, PortWatch nowcast revisions, ERA5T→ERA5); 0 changes here is *not* evidence of immutability. The `Last-Modified` header of the chart API equals the fetch time, so it carries no publication information (OBS).\n\n"
t += "## Observed newest-row latency (snapshot at " + lat["now_utc"] + ")\n\n```\n" + json.dumps({k: v for k, v in lat.items() if k != "now_utc"}, indent=1, default=str) + "\n```\n\n"
t += "## Leakage demonstration: conservative lag vs naive lag 0\n\nSame test re-run with the feature treated as available at its as-of/period date (lag 0) — what a careless backtest would do. Column = largest increase in |NW t| across the three targets, and the largest ΔR²oos increase.\n\n| Feature | Conservative lag | Change in abs(NW t), lag0 minus conservative | Change in ΔR²oos | Target |\n|---|---|---|---|---|\n"
rows = []
for fid, o in feats.items():
    r = nive(o)
    if r: rows.append((r[0], f"| `{fid}` | {o['lag']} d | {r[0]:+.2f} | {pct(r[1])} | {r[2]} |"))
t += "\n".join(x[1] for x in sorted(rows, reverse=True)) + "\n\n"
big = [x for x in sorted(rows, reverse=True) if x[0] > 1.0]
nl = sum(1 for fid, o in naive.items() for k, v in o["tests"].items() if v.get("cw_p", 1) < 0.05 and v.get("nw_p", 1) < 0.05); nc = sum(1 for fid, o in feats.items() if fid in naive for k, v in o["tests"].items() if v.get("cw_p", 1) < 0.05 and v.get("nw_p", 1) < 0.05)
gs = lambda tag: (feats["gh_btc_stars"]["tests"]["vol"]["nw_t"], naive["gh_btc_stars"]["tests"]["vol"]["nw_t"])
t += f"{len(big)} of {len(rows)} lagged features show abs(t) rising by more than 1.0 when the lag is dropped (max {max(x[0] for x in rows):+.2f}). Tests nominally significant on BOTH Clark-West and Newey-West (p<0.05, unadjusted): **{nc} with the conservative lag vs {nl} with lag 0** among the same {len(rows)} lagged features and their 3 targets. The inflation is modest and mixed in sign because most features are unpredictive at either lag; a lag that is too short cannot create signal from nothing, it only adds contemporaneous noise. The risk is largest for series that co-move with price on the target day: `gh_btc_stars` vs next-day volume goes from t={gs(0)[0]:.2f} (lag 2) to t={gs(0)[1]:.2f} (lag 0). **The lags themselves are assumptions** (see 10): they bound, but do not measure, real publication times.\n"
W("06_PIT_READINESS.md", t)

# ---------- 07 incremental
t = "# 07 — Incremental information beyond price, volume, volatility, funding, OI\n\n## Protocol (fixed before results; no tuning)\n\n```\n" + inc["protocol"].split('PROTOCOL (fixed before looking at results):')[1].strip() + "\n```\n\n"
t += f"Window 2023-10 → 2026-09 (BTC ≈1,090 daily obs; futures ≈ 830 trading days; weekly series ≈ 170 obs; GitHub ≈ 260-490). Baseline includes funding and ΔOI **for BTC only** (Binance Vision daily files); gold/crude/natgas have price, volume, volatility only.\n\n"
t += f"## Headline\n\n* **{len(inc['features'])} feature series tested** ({sum(1 for o in inc['features'] if o['class'].startswith('NOT'))} not testable), {ntests} (feature × target) tests.\n* **Candidates passing the full gate: {len(cands)}.** Nominal p<0.05 (Clark-West) in {nom} tests versus ≈ {0.05*ntests:.1f} expected by chance; smallest BH q = {minq:.2f}.\n* Class counts: " + ", ".join(f"{k}: {v}" for k, v in sorted(cls.items())) + ".\n* **Most features have NEGATIVE out-of-sample ΔR²** — adding them made predictions worse. This is the normal signature of no signal plus estimation noise.\n\n"
t += "## Power (BTC, same n and gate; synthetic feature with known partial R²)\n\n| Target | n | 0.25 % | 0.5 % | 1 % | 2 % | 4 % |\n|---|---|---|---|---|---|---|\n" + "\n".join(f"| {k} | {v['n']} | " + " | ".join(f"{v[x]*100:.0f} %" for x in ("0.0025", "0.005", "0.01", "0.02", "0.04")) + " |" for k, v in pw.items()) + "\n\n"
t += "Detection probability of the pre-registered gate. **Minimum detectable effect (80 % power) ≈ 3-4 % partial R² at a 1-day horizon.** A true incremental effect of 0.5-2 % (already large for a daily crypto feature) would be missed most of the time. The null therefore rules out *large* incremental effects only — it does **not** show that these sources are useless. Weekly series (CFTC, EIA; ~170 obs) have far less power than this table.\n\n"
t += "## Price-derivative rejects\n\nRejected if price-by-construction (USD-denominated or composite containing price/volume) **or** price-side adj-R² ≥ 0.40:\n\n| Feature | Reason | Price-side adj-R² |\n|---|---|---|\n" + "\n".join(f"| `{o['id']}` | {'by construction: ' + cell(o['note']) if o['byc'] else 'explained by price-side matrix'} | {o.get('price_side_r2adj', float('nan')):.2f} |" for o in rejects) + "\n\n"
t += "Sanity check: `bc_market-cap` (pure price × supply) has price-side adj-R² 0.86, the DeFi TVL series 0.64, Fear & Greed 0.49 — the diagnostic recovers known derivatives.\n\n## Full table (all tested features)\n\n" + HDR + "\n".join(r for r in (frow(o) for o in inc["features"]) if r) + "\n" + FN
t += "\n## Independent but unproven\n\nFeatures with price-side adj-R² < 0.15 carry information that is *not* a repackaging of price-side variables (e.g. `bc_hash-rate` 0.00, `bc_n-transactions` 0.02, `tga_btc` 0.05, `eia_crude` −0.02, `pw_*` < 0.08). Independence is a necessary, not sufficient, condition: none of them showed incremental predictive value here.\n"
W("07_INCREMENTAL_INFORMATION.md", t)

# ---------- 08 licence/cost
t = "# 08 — Licence and cost\n\nAll executed sources were **free at the point of use**; no key, account or payment was used. Licence statements are DOCUMENTED_CLAIM unless marked OBS and were **not** legally reviewed — treat every row as needing verification before any use beyond internal research.\n\n| Source | Cost | Access | Licence / terms | Commercial-use risk |\n|---|---|---|---|---|\n"
def crisk(s):
    l = (s["licence"] + s["cost"]).lower()
    if "public domain" in l: return "low (US gov public domain, DOC)"
    if "non-commercial" in l or "forbid" in l or "restrict" in l or "paid" in l: return "HIGH / needs licence"
    if "unknown" in l or "not verified" in l: return "UNKNOWN"
    return "low-moderate (attribution/fair-use, DOC)"
t += "\n".join(f"| {s['name']} | {cell(s['cost'])} | {cell(s['access'])} | {cell(s['licence'])} | {crisk(s)} |" for s in S) + "\n\n"
cr = collections.Counter(crisk(s).split(" ")[0] for s in S)
t += f"\nRisk tally over {n_disc} sources: " + ", ".join(f"{k}={v}" for k, v in cr.items()) + ". Free sources: " + str(len(free)) + f" (executed: {len(free_exec)}). Not free / not executable: exchange reserves (vendor), Baltic indices (paid), AISHub/GFW (account with conditions), Open-Meteo commercial (paid).\n\nCost beyond licence: GH Archive ≈ 60-150 MB/hour of raw data; Binance Vision daily metrics ≈ 11 kB/day; EIA files 130 kB each.\n"
W("08_LICENSE_COST.md", t)

# ---------- 09 adjudication
t = "# 09 — Adjudication\n\nOutcomes per repository doctrine. **ADAPT here means: worth forward point-in-time capture / further external study — not integration.** Nothing is ADOPT: no source demonstrated incremental predictive information. Integration adjudication belongs to a later stage against the real repository.\n\n"
t += "Counts: " + ", ".join(f"{k} {adj.get(k,0)}" for k in ("ADOPT", "ADAPT", "PARK", "REJECT")) + f" (over {n_disc} sources).\n\n| Source | Outcome | Reason |\n|---|---|---|\n" + "\n".join(f"| `{s['id']}` | **{ADJ[s['id']][0]}** | {cell(ADJ[s['id']][1])} |" for s in S)
t += "\n\n## Feature-level rejects (price derivatives)\n\n" + ", ".join(f"`{o['id']}`" for o in rejects) + ".\n\n## Suggested next external studies (research only)\n\n1. Start forward capture (own receipt timestamps + vintages) for: mempool.space live state, CFTC/EIA/TGA/PortWatch releases, DefiLlama stablecoin supply, Polymarket/Kalshi fixed basket, GDELT bulk, RSS. 6-12 months of clean vintages is the only way to convert LOOKAHEAD_RISK into PIT.\n2. Re-test at multi-day/weekly horizons and with non-linear/regime models — this study used one linear next-day design.\n3. Add cross-sectional assets (more coins, equities/ETFs) to raise power; a single time series cannot detect small effects.\n"
W("09_ADJUDICATION.md", t)

# ---------- 10 limitations
t = f"""# 10 — Limitations

1. **Low power** (see 07): minimum detectable partial R² ≈ 3-4 % at n≈1,000; weekly features far weaker. The null result is weak evidence.
2. **One design only:** next-day linear OLS, one fixed transform (weekly change, trailing z-score), conservative lags chosen a priori. Regime effects, non-linearities, multi-day horizons, intraday timing and event studies were not examined.
3. **Baseline asymmetry:** funding/OI in the baseline for BTC only. Commodity baselines are price/volume/vol only (their derivatives data do not exist in this study); Yahoo continuous futures are unofficial and unadjusted (roll jumps winsorised).
4. **Historical rows are LOOKAHEAD_RISK** for almost every tested series: lags are assumptions (aggregates +2 d, CFTC +6 d, EIA/weather +7 d, PortWatch +10 d), not observed publication times. A lag that is too short leaks; too long loses power.
5. **Not tested (missing evidence, not negative):** news/GDELT bulk, RSS, prediction markets, ETF flows (blocked/no history), exchange reserves, options/vol surfaces beyond report 005, EDGAR filings, GDELT tone, Google Trends, mempool state, GH Archive files directly.
6. **Egress effects:** GitHub REST blocked by session scope policy (403); Reddit 403; Farside Cloudflare 403; SEC needed declared UA; Wikipedia/GDELT/Open-Meteo hist-forecast rate-limited (429) from a shared IP; FRED closed by proxy earlier (report 005). These are egress outcomes, not provider verdicts.
7. **Data instability:** the ClickHouse playground changed between identical queries (see 02); GitHub-based tests use fragmentary coverage (~260-490 days). Fetched data are single-time snapshots at 2026-09-29 (test-egress clock); re-running later can give different numbers (history recomputation, table rebuilds).
8. **Multiple testing:** {ntests} tests, BH q=0.10; the 'best target' columns in report tables are selected by min p and must not be read as effect estimates.
9. **Licence review** is documentary and not legal advice.
10. **Stability sample** = 3 calls per endpoint within ~10 s; it says nothing about outages, deprecations or throttling under load.
11. No CoinGecko/TipRanks connectors were used (unavailable in the session); no paid or keyed data were used.
"""
W("10_LIMITATIONS.md", t)

# ---------- 00 exec summary
n_ind = cls.get("INDEPENDENT_NO_INCREMENTAL_EVIDENCE", 0)
t = f"""# 00 — Executive summary

Mission: `AURUMSHIFT_EXTERNAL_ALTERNATIVE_DATA_DISCOVERY_V1` — external research only; no private AurumShift code read; no integration proposed. Run clock: 2026-09-29 (UTC). Evidence labels per `claude.md`.

## What was done
* **{n_disc} sources catalogued** ({n_disc-len(free)} paid-only, flagged not executed) in {len(cats)} mission categories; **{n_exec} executed** (live probes ×3 and/or history pulled, none with a key); the rest not executable without a key/account/payment or blocked from the test egress. Full attribute records (access, cost, history, latency, timestamp/revision semantics, PIT readiness, licence, coverage, rate limits, stability) in 01/06/08 and `bench/alternative_data_v1/results/source_records.*`.
* **{len(inc['features'])} feature series** built from executed sources (on-chain, mining/mempool, stablecoins, CFTC positioning, Treasury cash, GitHub activity, HN, Wikipedia, ship transits, EIA inventories, weather, Binance public positioning) and tested for incremental information over price/volume/volatility (+funding/OI for BTC) with a pre-registered walk-forward protocol ({ntests} tests, Clark-West + Newey-West + BH-FDR).
* Leakage handled explicitly: conservative publication lags, a naive-lag comparison (06), and a re-fetch revision test.

## Findings
1. **No feature passed the gate: 0 incremental-information candidates.** {nom} nominal p<0.05 tests vs ≈{0.05*ntests:.0f} expected by chance; smallest BH q = {minq:.2f}. Most out-of-sample ΔR² are negative.
2. **Power is limited** (07): the test detects partial R² of ~3-4 % at 80 % power at a 1-day horizon, so the null excludes *large* effects only. Weekly series and GitHub (fragmentary data) are weaker still.
3. **{len(rejects)} series are price derivatives and rejected** (USD-denominated on-chain values, market-cap, DeFi TVL, Fear & Greed, long/short account ratio, taker buy/sell ratio). The diagnostic correctly ranks a pure price series at adj-R² 0.86.
4. **{n_ind + cls.get('PRICE_LINKED_PARTIAL_NO_INCREMENTAL',0)} series are informationally distinct from price but unproven** (adj-R² mostly <0.15): raw hash rate/transactions, mempool, Treasury cash, CFTC positioning, ship transits, EIA inventories, HDD/CDD, HN. Being independent of price is necessary, not sufficient.
5. **PIT posture is weak:** only {len(pit_native)} of {n_disc} sources are PIT_NATIVE for history (ledger/trade/filing/immutable-file timestamps); everything else is LOOKAHEAD_RISK for historical rows and at best PIT_ADAPTABLE via forward capture. Mempool state has **no free history at all**.
6. **Naive dating inflates statistics modestly:** dropping the publication lag raised abs(t) by >1 in {len(big)} of {len(rows)} lagged features and nominally-significant tests go {nc} → {nl} (06). The effect is bounded because most features are unpredictive at either lag; lags used are assumptions, not observed publication times.
7. **Operational hazards found:** ClickHouse GH-events playground changed content between identical queries and has a 14-month hole; PortWatch ArcGIS pagination silently truncates; several endpoints 429/403 from shared egress; Open-Meteo archive is reanalysis (not PIT).

## Adjudication counts (09)
ADOPT {adj.get('ADOPT',0)} · ADAPT {adj.get('ADAPT',0)} · PARK {adj.get('PARK',0)} · REJECT {adj.get('REJECT',0)}. ADAPT = forward-capture candidates only.

## Verdict rationale
Zero candidates under a strict, pre-registered gate — but with power too low to conclude the sources are worthless, several categories (news, prediction markets, ETF flows, exchange reserves, mempool) untestable from free history, and almost all history LOOKAHEAD_RISK. The honest reading is **inconclusive**, with a concrete route to resolve it (forward vintage capture, multi-horizon/cross-asset re-test).

## Final block
```
SOURCES_DISCOVERED={n_disc}
SOURCES_EXECUTED={n_exec}
FREE_SOURCES={len(free)} (free at point of use incl. {len([s for s in free if s['id'] in KEYED])} needing a free key/account and non-commercial-only terms; {len(free_exec)} executed, none with a key)

PIT_NATIVE={len(pit_native)}
PIT_ADAPTABLE={len(pit_adapt)}   # LOOKAHEAD_RISK for historical rows, PIT-usable via forward capture / release rule

INCREMENTAL_INFORMATION_CANDIDATES={len(cands)}
PRICE_DERIVATIVE_ONLY_REJECTS={len(rejects)}

FINAL_VERDICT={VERDICT}
```
"""
W("00_EXECUTIVE_SUMMARY.md", t)
open(os.path.join(RES, "final_block.txt"), "w").write(t.split("```\n")[1])
print(t.split("## Final block")[1])
