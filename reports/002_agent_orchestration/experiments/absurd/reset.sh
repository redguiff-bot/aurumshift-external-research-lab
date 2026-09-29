#!/bin/bash
# fresh state: drop queues; new run dir
export PGOPTIONS=; P="psql -h 127.0.0.1 -p 55401 -U lab postgres -q"
$P -c "select absurd.drop_queue(q) from unnest(array['main','review']) q where q in (select queue_name from absurd.queues)" >/dev/null 2>&1
rm -rf $1; mkdir -p $1; export ABS_LOGDIR=$1
