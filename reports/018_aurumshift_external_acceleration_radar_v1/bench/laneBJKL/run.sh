#!/usr/bin/env bash
# laneBJKL — reproduction (sandbox 2026-10-05). Données toutes synthétiques et seedées (seed 18).
# Prérequis : uv, python3.11, PostgreSQL 16 (binaires) + postgresql-server-dev-16 pour pgvector.
set -euo pipefail
V=${V:-./venvs}; mkdir -p "$V"
uv venv -q -p 3.11 "$V/laneBJKL" && uv pip install -q -p "$V/laneBJKL/bin/python" polars==1.44.2 duckdb==1.5.6 pandas==3.0.6 \
  pyarrow==25.0.1 pandera==0.33.1 numpy "psycopg[binary]==3.3.6" adbc-driver-postgresql==1.12.0 adbc-driver-manager
uv venv -q -p 3.11 "$V/mlflow" && uv pip install -q -p "$V/mlflow/bin/python" mlflow==3.16.1 "psycopg[binary]"
uv venv -q -p 3.11 "$V/otel" && uv pip install -q -p "$V/otel/bin/python" opentelemetry-sdk==1.45.0
P="$V/laneBJKL/bin/python"
$P -W ignore pit_asof_bench.py 1000000 200000 2000 0.001 > res_pit_asof_1000000.json
$P -W ignore pit_asof_bench.py 5000000 200000 2000 0.001 > res_pit_asof_5000000.json
$P -W ignore dq_c0_bench.py 1000000 > res_dq_c0_1M.json
"$V/otel/bin/python" otel_smoke.py > res_otel.json
# PG16 jetable (port 55433, data hors répertoire root-only car postgres ne peut pas traverser le scratchpad)
D=/tmp/laneBJKL_pg; B=/usr/lib/postgresql/16/bin; mkdir -p $D; chown postgres:postgres $D; chmod 777 $D
su postgres -c "cd /tmp; $B/initdb -D $D/data -U postgres -A trust >/dev/null; $B/pg_ctl -D $D/data -o '-p 55433 -k $D -c listen_addresses=localhost -c fsync=off -c shared_preload_libraries=pg_stat_statements' -l $D/log.txt start"
# pgvector : git clone --depth 1 -b v0.8.7 https://github.com/pgvector/pgvector && make PG_CONFIG=$B/pg_config && make install
psql -h localhost -p 55433 -U postgres -c "create extension vector"
$P pgvector_smoke.py > res_pgvector.json
psql -h localhost -p 55433 -U postgres -q -f ledger_pg_minimal.sql > res_ledger_pg_minimal.txt 2>&1 || true
psql -h localhost -p 55433 -U postgres -qc "create database mlflow"
"$V/mlflow/bin/python" -W ignore mlflow_shadow_ledger.py "sqlite:///$D/mlflow.db" "$D/art_sqlite"
"$V/mlflow/bin/python" -W ignore mlflow_shadow_ledger.py "postgresql+psycopg://postgres@localhost:55433/mlflow" "$D/art_pg"
$P -W ignore pg_transfer_bench.py > res_pg_transfer.json
su postgres -c "cd /tmp; $B/pg_ctl -D $D/data stop -m fast"; rm -rf $D
