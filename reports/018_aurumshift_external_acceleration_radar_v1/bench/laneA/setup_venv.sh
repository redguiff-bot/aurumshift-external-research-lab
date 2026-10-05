#!/usr/bin/env bash
# LANE A — reproduit le venv (Python 3.11, uv). Usage : bash setup_venv.sh <dir_venv>
set -euo pipefail
V=${1:-./venv_laneA}; HERE=$(cd "$(dirname "$0")" && pwd)
uv venv -p 3.11 "$V"
uv pip install -p "$V/bin/python" "arch==8.0.0" "statsmodels==0.15.0" "tsbootstrap==0.7.3" "arviz==0.23.4" \
  "pingouin==0.7.0" "quantstats==0.0.86" "doubleml==0.11.4" "econml==0.17.0" "dowhy==0.14" "causalml==0.17.0" \
  "spotify-confidence==4.1.0" "recombinator==0.0.6.1"
# confseq 0.0.11 (PyPI, sdist only) ne compile pas en Python 3.11 / numpy 2 : Boost requis + pybind11~=2.6 + np.float_.
# Pré-requis système : libboost-dev (apt). Puis patch (confseq_py311_numpy2.patch) et build local :
T=$(mktemp -d); git clone -q https://github.com/gostevehoward/confseq "$T/confseq"
(cd "$T/confseq" && git checkout -q 5ffe733; git apply "$HERE/confseq_py311_numpy2.patch")
uv pip install -p "$V/bin/python" "$T/confseq"
