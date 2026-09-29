#!/bin/bash
psql -h 127.0.0.1 -p 55403 -U lab -d postgres -qc "drop database if exists $1" -qc "create database $1"
cd /home/user/aurumshift-external-research-lab/reports/002_agent_orchestration/experiments/procrastinate
DB=$1 PYTHONPATH=$PWD PGHOST=127.0.0.1 PGPORT=55403 PGUSER=lab PGDATABASE=$1 /tmp/lab/work/procrastinate/v/bin/procrastinate --app=app.app schema --apply
