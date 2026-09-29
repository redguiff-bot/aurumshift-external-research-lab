#!/bin/bash
cd $(dirname $0); . ./lib.sh; killall_app; ./reset.sh >/dev/null 2>&1
P=$(REVIEW_SLEEP=2 startw w1 D_w1.log); sleep 5
$PY enqueue.py 20; sleep 4.5; kill -9 $P; pkill -9 -P $P; killall_app; echo "ALL STOPPED at $(date +%s.%N)"; snap
sleep 20; echo "-- after 20s idle (no processes):"; snap
echo "-- D2: start NEW executor id w3 (same version v1)"; P=$(REVIEW_SLEEP=2 startw w3 D_w3.log); sleep 25; snap
Q "select workflow_uuid,executor_id,status from dbos.workflow_status where status<>'SUCCESS' order by 1"; killall_app
echo "-- D3: start w1 with app version v2"; P=$(APP_VER=v2 REVIEW_SLEEP=2 startw w1 D_w1v2.log); sleep 15; snap; killall_app
echo "-- D1: start w1 version v1 (the original identity) at $(date +%s.%N)"; P=$(REVIEW_SLEEP=2 startw w1 D_w1b.log)
for i in $(seq 1 15); do snap; sleep 1; done | awk 'NR%2==1'
echo dups:; cut -d, -f1,2 $SE_LOG | sort | uniq -c | awk '$1>1'; wc -l < $SE_LOG; cp $SE_LOG D_side_effects.log; killall_app
