#!/bin/bash
cd $(dirname $0); . ./lib.sh; killall_app; ./reset.sh >/dev/null 2>&1
P=$(FAIL_MODE=flaky WORK_SLEEP=1 startw w1 B_w1.log); sleep 5
$PY enqueue.py 20; sleep 35
for i in 0 1 5 6; do echo "--- task $i work executions:"; grep "^work,$i," $SE_LOG; done
Q "select status,count(*) from dbos.workflow_status group by 1"
Q "select workflow_uuid,status,left(error,150) from dbos.workflow_status where status<>'SUCCESS' order by 1"
Q "select function_id,function_name,left(error,80),completed_at_epoch_ms-started_at_epoch_ms as ms from dbos.operation_outputs where workflow_uuid='t0' order by 1"
Q "select function_id,function_name,left(error,100) from dbos.operation_outputs where workflow_uuid='t5' order by 1"
cp $SE_LOG B_side_effects.log; killall_app
