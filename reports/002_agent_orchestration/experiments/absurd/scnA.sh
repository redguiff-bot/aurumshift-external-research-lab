#!/bin/bash
# usage: scnA.sh <kill_after_secs> <outdir>   (SIGKILL worker M1 mid-run; claim_timeout=10)
cd $(dirname $0); export PATH=/tmp/lab/work/absurd/venv/bin:$PATH
KA=$1; R=$2; ./reset.sh $R; export ABS_LOGDIR=$R WORK_SECS=3
T0=$(date +%s.%N)
python submit.py 20 5 > $R/submit.log
python worker.py main 10 5 > $R/w_M1.log 2>&1 & M1=$!
python worker.py review 10 5 > $R/w_R.log 2>&1 &
sleep 0.3
python worker.py main 10 5 > $R/w_M2.log 2>&1 &
sleep $KA; python - <<PY >> $R/events.log
import time;print(f"{time.time():.3f} SIGKILL M1 pid=$M1")
PY
kill -9 $M1
for i in $(seq 1 120); do
  s=$(psql -h 127.0.0.1 -p 55401 -U lab postgres -Atq -c "select count(*) from absurd.t_main where state not in ('completed','failed','cancelled')")
  [ "$s" = 0 ] && break; sleep 1; done
python - <<PY >> $R/events.log
import time;print(f"{time.time():.3f} all main tasks terminal after {i} polls")
PY
pkill -f "worker.py" ; sleep 0.5
./state.sh > $R/final_state.txt
psql -h 127.0.0.1 -p 55401 -U lab postgres -Atq -c "select r.task_id is not null, r.attempt, r.state, r.claimed_by, extract(epoch from r.started_at) s, extract(epoch from r.failed_at) f, r.failure_reason->>'name' from absurd.r_main r where r.attempt>1 or r.state='failed' order by started_at" > $R/attempt_gt1_runs.txt
psql -h 127.0.0.1 -p 55401 -U lab postgres -Atq -c "select attempt,state,count(*) from absurd.r_main group by 1,2 order by 1,2" > $R/run_counts.txt
python - <<PY > $R/analysis.txt
import collections,csv
rows=[l.strip().split(',') for l in open('$R/sideeffects.log')]
c=collections.Counter((k,n) for k,n,*_ in rows)
for kind in ('work','review'):
    tot=sum(v for (k,n),v in c.items() if k==kind); uniq=len({n for (k,n) in c if k==kind})
    print(kind,'executions',tot,'unique tasks',uniq,'duplicate executions',tot-uniq)
print('tasks with >1 work:',sorted(n for (k,n),v in c.items() if k=='work' and v>1))
PY
cat $R/events.log $R/analysis.txt $R/final_state.txt $R/run_counts.txt
