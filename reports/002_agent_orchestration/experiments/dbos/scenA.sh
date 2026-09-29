#!/bin/bash
# Scenario A: two executors w1,w2; SIGKILL w1 mid-work; watch whether w2 takes over; then restart w1
cd $(dirname $0); . ./lib.sh; killall_app; ./reset.sh >/dev/null 2>&1
T0=$(date +%s.%N); echo "T0=$T0"
P1=$(startw w1 A_w1.log); P2=$(startw w2 A_w2.log); sleep 5
$PY enqueue.py 20
sleep 4.5; echo "KILL w1 pid(shell)=$P1 at $(date +%s.%N)"; pkill -9 -P $P1 2>/dev/null; kill -9 $P1 2>/dev/null; ps aux|grep "[p]y app"|awk '{print $2,$NF, $0}'|cut -c1-80
KT=$(date +%s.%N)
for i in $(seq 1 45); do snap; sleep 1; done | tee A_timeline_phase1.txt | awk 'NR%3==1'
echo "--- steps of stuck workflows"; Q "select workflow_uuid,executor_id,status from dbos.workflow_status where status<>'SUCCESS' order by 1" | tee A_stuck.txt
echo "=== restart w1 (operator intervention #1) at $(date +%s.%N)"; RT=$(date +%s.%N)
P1=$(startw w1 A_w1_restart.log)
for i in $(seq 1 30); do snap; sleep 1; done | tee A_timeline_phase2.txt | awk 'NR%3==1'
Q "select status,count(*) from dbos.workflow_status group by 1"
echo "kill_time=$KT restart_time=$RT"
echo "work executions per task (>1 => duplicated side effect):"; cut -d, -f1,2 $SE_LOG | sort | uniq -c | awk '$1>1'
echo "total lines"; wc -l $SE_LOG; cp $SE_LOG A_side_effects.log
Q "select workflow_uuid, function_id, function_name from dbos.operation_outputs where workflow_uuid in (select workflow_uuid from dbos.workflow_status) order by 1,2" > A_ops.txt
killall_app
