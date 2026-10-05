#!/usr/bin/env bash
# laneCD — télécharge les échantillons GRATUITS Tardis.dev (1er jour du mois, sans clé API)
# et vérifie l'intégrité via l'en-tête x-md5 renvoyé par datasets.tardis.dev.
# Usage : ./download_tardis_samples.sh [DATE=2026/10/01] [OUTDIR]
# Note : les requêtes HTTP Range renvoient 403 ; HEAD renvoie 404 -> GET complet obligatoire.
set -euo pipefail
DATE="${1:-2026/10/01}"
OUT="${2:-${SCRATCH:-/tmp}/data_laneCD}"
mkdir -p "$OUT"
BASE="https://datasets.tardis.dev/v1"
LIST=(
  "binance/book_snapshot_25/BTCUSDT" "binance/book_snapshot_25/DOGEUSDT"
  "binance/trades/BTCUSDT" "binance/trades/DOGEUSDT"
  "binance/quotes/BTCUSDT" "binance/quotes/DOGEUSDT"
  "binance/incremental_book_L2/DOGEUSDT" "binance/incremental_book_L2/BTCUSDT"
  "okex/book_snapshot_25/BTC-USDT" "okex/book_snapshot_25/DOGE-USDT"
  "okex/trades/BTC-USDT" "okex/trades/DOGE-USDT"
  "okex/quotes/BTC-USDT" "okex/quotes/DOGE-USDT"
  "binance-futures/derivative_ticker/BTCUSDT" "binance-futures/derivative_ticker/DOGEUSDT"
  "okex-swap/derivative_ticker/BTC-USDT-SWAP" "okex-swap/derivative_ticker/DOGE-USDT-SWAP"
  "binance-futures/book_snapshot_25/DOGEUSDT" "binance-futures/trades/DOGEUSDT"
)
for item in "${LIST[@]}"; do
  ex="${item%%/*}"; rest="${item#*/}"; dt="${rest%%/*}"; sym="${rest#*/}"
  f="$OUT/${ex}_${dt}_${DATE//\//-}_${sym}.csv.gz"
  if [[ -s "$f" ]]; then echo "skip $f"; continue; fi
  hdr="$f.headers"
  curl -sS --retry 3 -D "$hdr" -o "$f" "$BASE/$ex/$dt/$DATE/$sym.csv.gz"
  want=$(grep -i '^x-md5' "$hdr" | tr -d '"\r' | awk '{print $2}')
  got=$(md5sum "$f" | awk '{print $1}')
  echo "$item size=$(stat -c %s "$f") md5_header=$want md5_file=$got $([[ "$want" == "$got" ]] && echo OK || echo MISMATCH)"
done
