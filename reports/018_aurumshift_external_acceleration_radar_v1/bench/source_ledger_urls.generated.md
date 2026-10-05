# SOURCE_LEDGER — AURUMSHIFT_EXTERNAL_ACCELERATION_RADAR_V1

Registre généré par `bench/build_ledger_and_matrix.py` à partir des notes de travail `evidence/raw_*.md` et
des colonnes `primary_sources` de `evidence/candidates_*.csv`. Chaque URL est rattachée aux lanes qui la citent ;
le contexte exact (citation, étiquette VERIFIED_FACT / VENDOR_CLAIM / etc.) est dans la note de lane.
Type = heuristique sur le domaine (CODE_REPO, PACKAGE_REGISTRY, PAPER, PRICING, OFFICIAL_API_OR_DATA, DOCS_OR_OTHER).
Les URLs d'API exécutées sont des endpoints interrogés, pas des pages lues.

Total URLs uniques : 288

## PAPER (6)

| URL | lanes |
|---|---|
| https://arxiv.org/abs/1810.08240 | laneA |
| https://arxiv.org/abs/2009.02824 | laneA |
| https://arxiv.org/abs/2010.09107 | laneFGH |
| https://arxiv.org/abs/2010.09686 | laneA |
| https://arxiv.org/abs/2110.08205 | laneFGH |
| https://ssrn.com/abstract=2460551 | laneA |

## PRICING (11)

| URL | lanes |
|---|---|
| https://clob.polymarket.com/prices-history | laneI |
| https://docs.kaiko.com/rest-api/data-feeds/level-1-and-level-2-data/level-2-aggregations/raw-order-book-snapshot/raw-order-book-snapshot-+-market-depth-bid-ask-spread-and-price-slippage | laneCD |
| https://eodhd.com/pricing | laneI |
| https://glassnode.com/pricing | laneE |
| https://newsapi.org/pricing | laneI |
| https://tardis.dev/#pricing | laneCD, laneE |
| https://tradingeconomics.com/api/pricing.aspx | laneI |
| https://www.amberdata.io/pricing | laneCD, laneE |
| https://www.coinapi.io/products/market-data-api/pricing | laneCD, laneE |
| https://www.coinglass.com/pricing | laneCD, laneE |
| https://www.kaiko.com/about-kaiko/pricing-and-contracts | laneE |

## OFFICIAL_API_OR_DATA (36)

| URL | lanes |
|---|---|
| https://api.elections.kalshi.com/trade-api/v2/series/KXFED | laneI |
| https://api.gdeltproject.org/api/v2/doc/doc | laneI |
| https://apps.bea.gov/API/signup/release_dates.json | laneI |
| https://bybit-exchange.github.io/docs/v5/market/open-interest | laneE |
| https://bybit-exchange.github.io/docs/v5/websocket/public/all-liquidation | laneE |
| https://bybit-exchange.github.io/docs/v5/websocket/public/orderbook | laneE |
| https://bybit-exchange.github.io/docs/v5/… | laneE |
| https://data.binance.vision/data/futures/um/monthly/fundingRate/ | laneCD |
| https://data.gdeltproject.org/gdeltv2/lastupdate.txt | laneI |
| https://developers.binance.com/docs/derivatives/usds-margined-futures | laneE |
| https://docs.kalshi.com/getting_started/historical_data.md | laneI |
| https://docs.kalshi.com/llms.txt | laneI |
| https://docs.polymarket.com/api-reference/geoblock.md | laneI |
| https://docs.polymarket.com/api-reference/rate-limits.md | laneI |
| https://docs.tardis.dev/ | laneE |
| https://docs.tardis.dev/api/tardis-machine | laneE |
| https://docs.tardis.dev/downloadable-csv-files/api.md | laneCD |
| https://docs.tardis.dev/downloadable-csv-files/data-types.md | laneCD |
| https://docs.tardis.dev/faq/billing-and-subscriptions.md | laneCD |
| https://docs.tardis.dev/historical-data-details/binance.md | laneCD |
| https://docs.tardis.dev/legal/terms-of-service.md | laneCD |
| https://fred.stlouisfed.org/docs/api/fred/releases_dates.html | laneI |
| https://nfs.faireconomy.media/ff_calendar_thisweek.json | laneI |
| https://nfs.faireconomy.media/ff_calendar_thisweek.xml | laneI |
| https://www.bankofengland.co.uk/monetary-policy/upcoming-mpc-dates | laneI |
| https://www.bea.gov/news/schedule/ics/online-calendar-subscription.ics | laneI |
| https://www.binance.com/en/fee/schedule | laneCD |
| https://www.bls.gov/schedule/news_release/bls.ics | laneI |
| https://www.boj.or.jp/en/mopo/mpmsche_minu/index.htm | laneI |
| https://www.ecb.europa.eu/press/calendars/mgcgc/html/index.en.html | laneI |
| https://www.federalreserve.gov/feeds/press_all.xml | laneI |
| https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm | laneI |
| https://www.okx.com/api/v5/public/funding-rate-history | laneCD |
| https://www.okx.com/api/v5/support/announcements?annType=announcements-new-listings | laneI |
| https://www.okx.com/docs-v5/en/ | laneE |
| https://www.okx.com/docs-v5/log_en/ | laneE |

## CODE_REPO (81)

| URL | lanes |
|---|---|
| https://crates.io/crates/barter-data | laneE |
| https://crates.io/crates/ccxt-rs | laneE |
| https://crates.io/crates/crypto-crawler | laneE |
| https://crates.io/crates/crypto-ws-client | laneE |
| https://github.com/AI4Finance-Foundation/FinGPT | laneI |
| https://github.com/CrunchyData/pg_parquet | laneBJKL |
| https://github.com/DoubleML/doubleml-for-py | laneA |
| https://github.com/InvestmentSystems/recombinator | laneA |
| https://github.com/Mooncake-Labs/pg_mooncake | laneBJKL |
| https://github.com/NorskRegnesentral/skchange | laneFGH |
| https://github.com/airbnb/chronon | laneBJKL |
| https://github.com/apache/age | laneBJKL |
| https://github.com/arviz-devs/arviz | laneA |
| https://github.com/assuncaolfi/savvi | laneA |
| https://github.com/astrogilda/tsbootstrap | laneA |
| https://github.com/barter-rs/barter-rs | laneE |
| https://github.com/bashtage/arch | laneA, laneFGH |
| https://github.com/binance/binance-spot-api-docs/blob/master/web-socket-streams.md | laneE |
| https://github.com/bmoscon/cryptofeed/blob/master/CHANGES.md | laneE |
| https://github.com/bmoscon/cryptostore | laneE |
| https://github.com/bybit-exchange/pybit | laneE |
| https://github.com/ccxt/ccxt/blob/master/wiki/ccxt.pro.manual.md | laneE |
| https://github.com/cuemacro/tcapy | laneCD |
| https://github.com/cvxgrp/cvxportfolio | laneCD |
| https://github.com/databento/dbn/blob/main/rust/dbn/src/publishers.rs | laneCD |
| https://github.com/datalad/datalad | laneA |
| https://github.com/dcajasn/Riskfolio-Lib | laneFGH |
| https://github.com/deepcharles/ruptures | laneFGH |
| https://github.com/dolthub/doltgresql | laneBJKL |
| https://github.com/duckdb/pg_duckdb | laneBJKL |
| https://github.com/eguidotti/bidask | laneCD |
| https://github.com/gostevehoward/confseq | laneA |
| https://github.com/grosed/changepoint_online | laneFGH |
| https://github.com/henrikbostrom/crepes | laneFGH |
| https://github.com/hudson-and-thames/mlfinlab | laneA |
| https://github.com/huggingface/transformers | laneI |
| https://github.com/hummingbot/hummingbot | laneE |
| https://github.com/ip200/venn-abers | laneFGH |
| https://github.com/jakorostami/expectation | laneA |
| https://github.com/jpmorganchase/abides-jpmc-public | laneCD |
| https://github.com/nats-io/nats-server | laneBJKL |
| https://github.com/nautechsystems/nautilus_trader | laneCD |
| https://github.com/nautechsystems/nautilus_trader/tree/develop/crates/adapters | laneE |
| https://github.com/nkaz001/hftbacktest | laneCD |
| https://github.com/nkaz001/hftbacktest/blob/master/hftbacktest/src/backtest/proc/partialfillexchange.rs | laneCD |
| https://github.com/nkaz001/hftbacktest/issues | laneCD |
| https://github.com/okxapi/python-okx | laneE |
| https://github.com/oliver-zehentleitner/unicorn-binance-websocket-api | laneE |
| https://github.com/pgmq/pgmq | laneBJKL |
| https://github.com/pgvector/pgvector | laneBJKL |
| https://github.com/probml/dynamax | laneFGH |
| https://github.com/prometheus/prometheus | laneBJKL |
| https://github.com/puolival/multipy | laneA |
| https://github.com/py-why/EconML | laneA |
| https://github.com/py-why/dowhy | laneA |
| https://github.com/pymc-labs/CausalPy | laneA |
| https://github.com/ranaroussi/quantstats | laneA |
| https://github.com/raphaelvallat/pingouin | laneA |
| https://github.com/scikit-learn-contrib/MAPIE | laneFGH |
| https://github.com/skfolio/skfolio | laneFGH |
| https://github.com/spotify/confidence | laneA |
| https://github.com/st-tech/zr-obp | laneA |
| https://github.com/statsmodels/statsmodels | laneA |
| https://github.com/tardis-dev/tardis-machine | laneCD |
| https://github.com/tardis-dev/tardis-python | laneCD |
| https://github.com/treeverse/dvc | laneA |
| https://github.com/uber/causalml | laneA |
| https://github.com/xtdb/xtdb | laneBJKL |
| https://raw.githubusercontent.com/getzep/graphiti/main/README.md | laneBJKL |
| https://raw.githubusercontent.com/hmmlearn/hmmlearn/main/README.rst | laneFGH |
| https://raw.githubusercontent.com/jakobrunge/tigramite/master/license.txt | laneFGH |
| https://raw.githubusercontent.com/mlflow/mlflow/master/LICENSE.txt | laneBJKL |
| https://raw.githubusercontent.com/online-ml/river/main/docs/releases/0.25.0.md | laneFGH |
| https://raw.githubusercontent.com/online-ml/river/main/docs/releases/0.26.0.md | laneFGH |
| https://raw.githubusercontent.com/oraios/serena/main/LICENSE | laneBJKL |
| https://raw.githubusercontent.com/paradedb/paradedb/main/README.md | laneBJKL |
| https://raw.githubusercontent.com/redpanda-data/redpanda/dev/licenses/README.md | laneBJKL |
| https://raw.githubusercontent.com/sodadata/soda-core/main/LICENSE | laneBJKL |
| https://raw.githubusercontent.com/tensorchord/VectorChord/main/LICENSE | laneBJKL |
| https://raw.githubusercontent.com/timescale/pgvectorscale/main/LICENSE | laneBJKL |
| https://raw.githubusercontent.com/timescale/timescaledb/main/LICENSE | laneBJKL |

## PACKAGE_REGISTRY (95)

| URL | lanes |
|---|---|
| https://pypi.org/project/MAPIE/ | laneFGH |
| https://pypi.org/project/PyWavelets/ | laneFGH |
| https://pypi.org/project/adbc-driver-postgresql/ | laneBJKL |
| https://pypi.org/project/aim/ | laneBJKL |
| https://pypi.org/project/arch/ | laneA, laneFGH |
| https://pypi.org/project/arviz/ | laneA |
| https://pypi.org/project/bayesian-changepoint-detection/ | laneFGH |
| https://pypi.org/project/bidask/ | laneCD |
| https://pypi.org/project/binance-connector/ | laneE |
| https://pypi.org/project/binance-futures-connector/ | laneE |
| https://pypi.org/project/binance-sdk-spot/ | laneE |
| https://pypi.org/project/bocd/ | laneFGH |
| https://pypi.org/project/causal-learn/ | laneFGH |
| https://pypi.org/project/causalml/ | laneA |
| https://pypi.org/project/causalpy/ | laneA |
| https://pypi.org/project/ccxt/ | laneE |
| https://pypi.org/project/changepoint-online/ | laneFGH |
| https://pypi.org/project/chronon-ai/ | laneBJKL |
| https://pypi.org/project/cognee/ | laneBJKL |
| https://pypi.org/project/conformal-tights/ | laneFGH |
| https://pypi.org/project/confseq/ | laneA |
| https://pypi.org/project/crepes/ | laneFGH |
| https://pypi.org/project/cryptofeed/ | laneE |
| https://pypi.org/project/cvxportfolio/ | laneCD, laneFGH |
| https://pypi.org/project/cvxpy/ | laneFGH |
| https://pypi.org/project/databento/ | laneCD |
| https://pypi.org/project/datafusion/ | laneBJKL |
| https://pypi.org/project/datalad/ | laneA |
| https://pypi.org/project/dbt-core/ | laneBJKL |
| https://pypi.org/project/deepchecks/ | laneBJKL |
| https://pypi.org/project/deltalake/ | laneBJKL |
| https://pypi.org/project/doubleml/ | laneA |
| https://pypi.org/project/dowhy/ | laneA |
| https://pypi.org/project/dvc/ | laneA, laneBJKL |
| https://pypi.org/project/dynamax/ | laneFGH |
| https://pypi.org/project/econml/ | laneA |
| https://pypi.org/project/elementary-data/ | laneBJKL |
| https://pypi.org/project/evidently/ | laneBJKL |
| https://pypi.org/project/expectation/ | laneA |
| https://pypi.org/project/feast/ | laneBJKL |
| https://pypi.org/project/featureform/ | laneBJKL |
| https://pypi.org/project/filterpy/ | laneFGH |
| https://pypi.org/project/great-expectations/ | laneBJKL |
| https://pypi.org/project/hftbacktest/ | laneCD |
| https://pypi.org/project/hmmlearn/ | laneFGH |
| https://pypi.org/project/hopsworks/ | laneBJKL |
| https://pypi.org/project/hummingbot/ | laneE |
| https://pypi.org/project/lakeapi/ | laneCD |
| https://pypi.org/project/lakefs/ | laneBJKL |
| https://pypi.org/project/letta/ | laneBJKL |
| https://pypi.org/project/lightrag-hku/ | laneBJKL |
| https://pypi.org/project/linearmodels/ | laneFGH |
| https://pypi.org/project/lingam/ | laneFGH |
| https://pypi.org/project/multipy/ | laneA |
| https://pypi.org/project/nannyml/ | laneBJKL |
| https://pypi.org/project/nautilus-trader/ | laneCD |
| https://pypi.org/project/nautilus_trader/ | laneE |
| https://pypi.org/project/networkx/ | laneFGH |
| https://pypi.org/project/nonlinshrink/ | laneFGH |
| https://pypi.org/project/numpyro/ | laneFGH |
| https://pypi.org/project/obp/ | laneA |
| https://pypi.org/project/online-cp/ | laneFGH |
| https://pypi.org/project/openlineage-python/ | laneBJKL |
| https://pypi.org/project/opentelemetry-sdk/ | laneBJKL |
| https://pypi.org/project/pandera/ | laneBJKL |
| https://pypi.org/project/pingouin/ | laneA |
| https://pypi.org/project/puncc/ | laneFGH |
| https://pypi.org/project/pybit/ | laneE |
| https://pypi.org/project/pyfolio-reloaded/ | laneCD |
| https://pypi.org/project/pyiceberg/ | laneBJKL |
| https://pypi.org/project/pymc/ | laneFGH |
| https://pypi.org/project/pyportfolioopt/ | laneFGH |
| https://pypi.org/project/python-okx/ | laneE |
| https://pypi.org/project/quantstats/ | laneA |
| https://pypi.org/project/recombinator/ | laneA |
| https://pypi.org/project/riskfolio-lib/ | laneFGH |
| https://pypi.org/project/river/ | laneFGH |
| https://pypi.org/project/ruptures/ | laneFGH |
| https://pypi.org/project/skchange/ | laneFGH |
| https://pypi.org/project/skfolio/ | laneFGH |
| https://pypi.org/project/sktime/ | laneFGH |
| https://pypi.org/project/spotify-confidence/ | laneA |
| https://pypi.org/project/statsforecast/ | laneFGH |
| https://pypi.org/project/statsmodels/ | laneA, laneFGH |
| https://pypi.org/project/tardis-dev/ | laneCD |
| https://pypi.org/project/tcapy/ | laneCD |
| https://pypi.org/project/tigramite/ | laneFGH |
| https://pypi.org/project/torchcp/ | laneFGH |
| https://pypi.org/project/tsbootstrap/ | laneA |
| https://pypi.org/project/unicorn-binance-websocket-api/ | laneE |
| https://pypi.org/project/universal-portfolios/ | laneFGH |
| https://pypi.org/project/venn-abers/ | laneFGH |
| https://pypi.org/project/whylogs/ | laneBJKL |
| https://pypi.org/pypi/<pkg | laneFGH |
| https://www.npmjs.com/package/tardis-machine | laneE |

## DOCS_OR_OTHER (59)

| URL | lanes |
|---|---|
| https://api.coinalyze.net/v1/exchanges | laneE |
| https://api.manifold.markets/v0/markets | laneI |
| https://api.polygon.io/v1/reference/economic-calendar | laneI |
| https://arch.readthedocs.io/en/latest/bootstrap/bootstrap.html | laneFGH |
| https://aspredicted.org/ | laneA |
| https://assuncaolfi.github.io/savvi/ | laneA |
| https://calendar-api.fxstreet.com/en/api/v1/eventDates/ | laneI |
| https://centre-borelli.github.io/ruptures-docs/ | laneFGH |
| https://coinalyze.net/api/ | laneE |
| https://cran.r-project.org/package=blocklength | laneA |
| https://cran.r-project.org/package=boot | laneA |
| https://cran.r-project.org/package=np | laneA |
| https://cran.r-project.org/package=safestats | laneA |
| https://cran.r-project.org/package=tseries | laneA |
| https://crepes.readthedocs.io | laneFGH |
| https://crypto-lake.com/coverage | laneCD |
| https://crypto-lake.com/subscribe/ | laneCD |
| https://cryptopanic.com/developers/api/ | laneI |
| https://data-api.coindesk.com/news/v1/article/list | laneI |
| https://data.coindesk.com/derivatives | laneE |
| https://data.nasdaq.com/ | laneI |
| https://docs.benzinga.com/api-reference/calendar-api/get-economics.md | laneI |
| https://docs.mem0.ai/components/vectordbs/dbs/pgvector | laneBJKL |
| https://docs.pola.rs/api/python/stable/reference/dataframe/api/polars.DataFrame.join_asof.html | laneBJKL |
| https://docs.tokenomist.ai/api-documents | laneI |
| https://docs.tradingeconomics.com/economic_calendar/snapshot/ | laneI |
| https://docs.velo.xyz/api | laneE |
| https://docs.xtdb.com/ | laneBJKL |
| https://duckdb.org/docs/current/sql/query_syntax/from | laneBJKL |
| https://eodhd.com/financial-apis/economic-events-data-api | laneI |
| https://eventregistry.org/ | laneI |
| https://finnhub.io/docs/api/economic-calendar | laneI |
| https://finnhub.io/static/swagger.json | laneI |
| https://help.osf.io/article/158-create-a-preregistration | laneA |
| https://hudsonthames.org/mlfinlab/ | laneA |
| https://huggingface.co/ProsusAI/finbert | laneI |
| https://openbb.co/blog/velo-brings-digital-assets-market-data-to-OpenBB/ | laneCD |
| https://osf.io/registries | laneA |
| https://proceedings.neurips.cc/paper/2021/file/0d441de75945e5acbc865406fc9a2559-Paper.pdf | laneFGH |
| https://scikit-learn.org/stable/modules/covariance.html | laneFGH |
| https://site.financialmodelingprep.com/developer/docs/economic-calendar-api | laneI |
| https://skfolio.org | laneFGH |
| https://www.alphavantage.co/premium/ | laneI |
| https://www.bigdata.com/ | laneI |
| https://www.dowjones.com/professional/factiva/ | laneI |
| https://www.econoday.com/ | laneI |
| https://www.investing.com/economic-calendar/ | laneI |
| https://www.jblanked.com/news/api/docs/ | laneI |
| https://www.postgresql.org/docs/18/pgstatstatements.html | laneBJKL |
| https://www.postgresql.org/docs/18/release-18.html | laneBJKL |
| https://www.postgresql.org/docs/18/sql-notify.html | laneBJKL |
| https://www.postgresql.org/docs/19/ddl-temporal-tables.html | laneBJKL |
| https://www.postgresql.org/docs/19/release-19.html | laneBJKL |
| https://www.postgresql.org/support/versioning/ | laneBJKL |
| https://www.quicknode.com/builders-guide/tools/laevitas-by-laevitas | laneCD |
| https://www.science.org/doi/10.1126/sciadv.aau4996 | laneFGH |
| https://www.statsmodels.org/stable/generated/statsmodels.tsa.statespace.dynamic_factor_mq.DynamicFactorMQ.html | laneFGH |
| https://www.statsmodels.org/stable/regime_switching.html | laneFGH |
| https://www.statsmodels.org/stable/vector_ar.html | laneFGH |
