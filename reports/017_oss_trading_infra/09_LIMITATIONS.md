# 09 — Limitations

## Scope and independence
* External research only. No private AurumShift code was read; nothing here says a candidate is compatible with, or replaces, any AurumShift component. "Drop-in" in the final block means *capability-level* (pure library, no service, permissive licence, behaviour verified) — the fit against the real repository is left to the later integration adjudication.
* Candidate discovery is from prior knowledge plus live upstream checks; **it is not exhaustive** (67 names). Absence from the list is not a negative finding. Candidates that were metadata-only (23) cannot be classified above PARK by rule.

## Test validity
* Synthetic data throughout (seeded GBM-like series, hand-built L2 feeds, injected faults). It gives exact oracles but says nothing about real-market behaviour: queue models, impact parameters, calendars for real venues beyond the dates checked, and DQ recall on real feed errors are **not** validated.
* One hand-built L2 scenario for queue/latency (`03`): it proves a risk-averse fill time and latency handling for hftbacktest, but does not discriminate the three probabilistic queue models and does not test partial fills, cancels, or own-order market impact.
* **Nautilus passive fill is UNKNOWN, not "unsupported".** 9 configurations produced no print-driven passive fill; my setup or my reading of its fill semantics may be incomplete, and a newer build (PyPI shows 1.231.0 and 2.0.0rc5; 1.221.0 was installed for Python 3.11) may differ.
* Single-run timings on a shared 4-core sandbox: throughput and latency figures are indicative; ratios are more reliable than absolutes. Install times were measured on a warm cache and are omitted.
* Determinism was checked over 2–3 repeated runs in one process/container, not across machines, CPU architectures or library versions.
* PROVEN is used only where an independent oracle exists (numpy/scipy, closed form, hand derivation, cross-library equality on the same input, known calendar dates). Cross-library equality can share a common bug (e.g. `pandas_market_calendars` sits on `exchange_calendars`, so their agreement is not two independent opinions — noted in `02`).
* Screen metrics are proxies: commit counts, distinct authors and top-author share are computed from a shallow history since 2025-09-29 and do not measure code quality, review depth or who holds release rights. Test-file counts are path regexes.

## Environment effects
* All network results depend on the sandbox egress: Binance API 451, Bybit 403, QuestDB release download 403, GitHub REST API 403; a TLS-terminating proxy required a CA path for ccxt. These are egress outcomes, not provider verdicts.
* Several candidates were not executed for reasons unrelated to quality: no API key (databento), platform size (openbb, LEAN, qlib, vnpy), live-order runtime (freqtrade, hummingbot, pysystemtrade), server products (QuestDB, InfluxDB, VictoriaMetrics), or dependency stack (tcapy). ClickHouse was run only as `clickhouse-local`; its git metadata could not be collected.
* TimescaleDB was tested only in the Timescale-License build; the Apache-2-only feature set was not run (DOCUMENTED_CLAIM that compression/caggs are TSL features; `SHOW timescaledb.license` = `timescale` OBSERVED).
* Python versions differ by candidate (3.9 for ABIDES, 3.11 default, 3.12 for pandas-ta); results are not a statement about a single common runtime.
* The `PyPortfolioOpt` and `empyrical-reloaded` import failures occurred in an isolated venv; in a shared venv the missing modules were provided transitively by other packages.

## Licence and legal
* Licence names come from LICENSE files and PyPI metadata at the time of the run. Copyleft/source-available terms are flagged, **not interpreted**; AGPL/GPL/LGPL/BSL/Commons-Clause/Elastic obligations depend on the way AurumShift would use a component and are UNKNOWN here.

## Things deliberately not done
* No integration, adapter, or change proposal against AurumShift code; no platform recommendation; no scoring of frameworks against each other.
* No live-capital or authenticated venue access; no API keys used; the only paid-data path touched was a vendor's keyless free sample.
* No attempt to make a failing candidate work beyond a timeboxed fix (ABIDES on 3.9 and the cryptofeed event-loop line are the exceptions, and both are recorded as environment workarounds).
