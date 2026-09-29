# 09 — Limitations

1. **Discovery is not exhaustive.** GitHub search was unavailable from the sandbox; candidates come from ecosystem knowledge, PyPI metadata and three web searches. Recall is UNKNOWN; niche Rust/C++/Java/Go projects (e.g. Databento-adjacent tools, Java LOB simulators) are under-represented.
2. **Synthetic data only.** All engine, book, feature and DQ tests use seeded synthetic data; real L2/L3 archives, corporate actions and venue outages were not replayed. Results establish arithmetic/semantic correctness on known answers, not performance on real markets.
3. **Known answers are partly tester-derived.** Analytic PnL, closed-form min-variance and the FIFO reference were written by the tester; the NYSE holiday list was not re-fetched in this run. Two independent calendar libraries agree with it.
4. **One configuration per test.** E.g. the backtesting.py exit-spread deviation was seen with `position.close()`; other order paths untested. T12a does not discriminate probabilistic queue models. T04 checks only a moving-average strategy.
5. **Footprint is shared-venv upper bound**, not isolated per package; throughput numbers include Python overhead and are not like-for-like across libraries.
6. **Time-dependent network results.** T11 reflects 2026-09-29 egress; Binance (451), Bybit (403) and OKX WebSocket failures are egress outcomes, not verdicts. ccxt CA handling findings are specific to this sandbox's TLS-inspecting proxy.
7. **Maintenance metrics are commit-history proxies.** Bus factor = authors for 50 % of 12-month commits; squash merges, bots and vendored history distort it. Rust inline tests are not counted in test-file presence. pandas-ta and duckdb histories were not obtained.
8. **Not executed (22 projects)** are classified from limited evidence; licence statements for hummingbot, mlfinlab, original zipline are from memory (INFERENCE).
9. **PIT, revision handling and provenance** were evaluated only where a library exposes timestamps (cryptofeed receipt, DBN fields, ArcticDB versions). No test involved provider revisions.
10. **Security/supply chain** (transitive dependency audit, wheel provenance) was not assessed. Licence notes are not legal advice.
11. **No AurumShift code was read**; nothing here asserts compatibility with, or need within, the private system. Gaps listed in `08` are gaps in OSS coverage, not in AurumShift.
12. Harness mistakes fixed during the run are listed in `06`; results in `bench/.../results` are from the final versions of the scripts.
