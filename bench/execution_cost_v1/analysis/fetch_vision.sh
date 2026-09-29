#!/bin/sh
# Re-download the Binance Vision files used (public, no auth). Run from bench/execution_cost_v1/data/vision
B=https://data.binance.vision/data
for d in 2026-09-20 2026-09-21 2026-09-22 2026-09-23; do curl -s -o aggTrades_BTCUSDT_$d.zip $B/spot/daily/aggTrades/BTCUSDT/BTCUSDT-aggTrades-$d.zip; done
for d in 2026-09-21 2026-09-22; do curl -s -o aggTrades_ETHUSDT_$d.zip $B/spot/daily/aggTrades/ETHUSDT/ETHUSDT-aggTrades-$d.zip; done
for m in 2026-06 2026-07 2026-08; do curl -s -o klines_BTCUSDT_1m_$m.zip $B/spot/monthly/klines/BTCUSDT/1m/BTCUSDT-1m-$m.zip; done
curl -s -o klines_ETHUSDT_1m_2026-08.zip $B/spot/monthly/klines/ETHUSDT/1m/ETHUSDT-1m-2026-08.zip
for m in 2026-05 2026-06 2026-07 2026-08; do for s in BTCUSDT ETHUSDT; do curl -s -o fund_${s}_$m.zip $B/futures/um/monthly/fundingRate/$s/$s-fundingRate-$m.zip; done; done
curl -s -o bookDepth_um_BTCUSDT_2026-09-20.zip $B/futures/um/daily/bookDepth/BTCUSDT/BTCUSDT-bookDepth-2026-09-20.zip
