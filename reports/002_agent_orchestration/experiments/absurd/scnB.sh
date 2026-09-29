#!/bin/bash
# usage: scnB.sh <FAIL_FIRST> <max_attempts> <outdir>  ; retry strategy exponential base=2s factor=2
cd $(dirname $0); export PATH=/tmp/lab/work/absurd/venv/bin:$PATH
FF=$1; MA=$2; R=$3; ./reset.sh $R; export ABS_LOGDIR=$R WORK_SECS=3 FAIL_FIRST=$FF
python submit.py ${NTASKS:-20} $MA 2 > $R/submit.log
python worker.py main 30 10 > $R/w_M.log 2>&1 & M=$!
python worker.py review 30 10 > $R/w_R.log 2>&1 & RP=$!
for i in $(seq 1 90); do
  s=$(psql -h 127.0.0.1 -p 55401 -U lab postgres -Atq -c "select count(*) from absurd.t_main where state not in ('completed','failed','cancelled')")
  [ "$s" = 0 ] && break; sleep 1; done
kill $M $RP; sleep 0.3
./state.sh > $R/final_state.txt; cat $R/final_state.txt
P="psql -h 127.0.0.1 -p 55401 -U lab postgres -Atq"
$P -c "select attempt, state, round(extract(epoch from started_at - lag_fail)::numeric,2) as gap_after_prev_fail_s, round(extract(epoch from failed_at-started_at)::numeric,2) dur, failure_reason->>'name' from (select r.*, lag(failed_at) over (partition by task_id order by attempt) lag_fail, task_id tid from absurd.r_main r) x where task_id=(select task_id from absurd.t_main order by enqueue_at limit 1) order by attempt" > $R/task0_timeline.txt; cat $R/task0_timeline.txt
$P -c "select state, attempts, max_attempts, count(*) from absurd.t_main group by 1,2,3" | tee $R/task_summary.txt
$P -c "select run_id is not null from (select 1) z, absurd.r_main limit 0" >/dev/null
python - <<PY | tee $R/analysis.txt
import collections
rows=[l.strip().split(',') for l in open('$R/sideeffects.log')]
c=collections.Counter(k for k,*_ in rows); print(dict(c))
PY
