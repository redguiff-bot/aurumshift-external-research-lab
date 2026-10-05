#!/usr/bin/env bash
# Lane E — smoke tardis-machine (MPL-2.0). Replay normalisé de l'échantillon gratuit + stream live normalisé.
set -e
D=${1:-./tm}; mkdir -p $D; cd $D
npm install tardis-machine@18.3.8
NODE_EXTRA_CA_CERTS=${NODE_EXTRA_CA_CERTS:-/root/.ccr/ca-bundle.crt} node node_modules/tardis-machine/bin/tardis-machine.js --port=8072 --cache-dir=$PWD/cache &
sleep 5
OPTS=$(python3 -c 'import urllib.parse,json;print(urllib.parse.quote(json.dumps({"exchange":"okex-swap","symbols":["BTC-USDT-SWAP"],"from":"2026-09-01T00:00:00.000Z","to":"2026-09-01T00:01:00.000Z","dataTypes":["trade","book_snapshot_5_1s","derivative_ticker"]})))')
curl -s "localhost:8072/replay-normalized?options=$OPTS" -o tm_replay.ndjson; wc -l tm_replay.ndjson
# live : ws://localhost:8073/ws-stream-normalized?options=[...] (voir trade_id_differential.py)
