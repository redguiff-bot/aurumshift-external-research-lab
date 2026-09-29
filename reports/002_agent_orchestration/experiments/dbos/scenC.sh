#!/bin/bash
cd $(dirname $0); . ./lib.sh; killall_app; ./reset.sh >/dev/null 2>&1
P=$(REVIEW_SLEEP=2 startw w1 C_w1.log); sleep 5
$PY enqueue.py 20; sleep 4.5
PM=$(head -1 /tmp/lab/pg/dbos/postmaster.pid); echo "kill -9 postmaster $PM at $(date +%s.%N)"; kill -9 $PM
pkill -9 -u lab postgres 2>/dev/null; sleep 12
echo "PG down 12s; app alive? $(ps -eo pid,args | grep -c '[b]in/python app.py')"
echo "restart PG at $(date +%s.%N)"; /tmp/lab/bin/pgstart.sh dbos 55402 >/dev/null 2>&1; RT=$(date +%s.%N)
for i in $(seq 1 40); do snap; sleep 1; done | awk 'NR%2==1' | tee C_timeline.txt
Q "select status,count(*) from dbos.workflow_status group by 1"
echo "dups:"; cut -d, -f1,2 $SE_LOG | sort | uniq -c | awk '$1>1'; wc -l < $SE_LOG
cp $SE_LOG C_side_effects.log; grep -ci "error\|exception" $W/C_w1.log; grep -i "error\|exception" $W/C_w1.log | cut -c1-160 | sort | uniq -c | sort -rn | head -8
killall_app
