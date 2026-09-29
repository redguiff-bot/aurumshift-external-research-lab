#!/bin/bash
# usage: run_worker.sh DB name [concurrency] ; env passes through
cd /home/user/aurumshift-external-research-lab/reports/002_agent_orchestration/experiments/procrastinate
export DB=$1 PYTHONPATH=$PWD
exec /tmp/lab/work/procrastinate/v/bin/procrastinate --app=app.app worker --concurrency=${3:-4} --name=$2 ${WORKER_ARGS}
