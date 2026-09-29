#!/bin/bash
# D: submit 20, workers run 5s, ALL workers stopped (SIGTERM), idle 25s (no workers at all), fresh workers started -> resume?
cd $(dirname $0); export PATH=/tmp/lab/work/absurd/venv/bin:$PATH
R=$1; ./reset.sh $R; export ABS_LOGDIR=$R WORK_SECS=3 REVIEW_SECS=2
ts(){ python -c "import time;print(f'{time.time():.3f}',end=' ')"; }
python submit.py 20 5 > $R/submit.log
python worker.py main 15 5 > $R/w1_M.log 2>&1 & M=$!
python worker.py review 15 5 > $R/w1_R.log 2>&1 & RP=$!
sleep 5; echo "$(ts)stop all workers (SIGTERM)" >> $R/events.log; kill $M $RP; wait 2>/dev/null
./state.sh >> $R/events.log; sleep 25
echo "$(ts)start NEW workers (session 2)" >> $R/events.log
python worker.py main 15 5 > $R/w2_M.log 2>&1 & M=$!
python worker.py review 15 5 > $R/w2_R.log 2>&1 & RP=$!
for i in $(seq 1 90); do s=$(psql -h 127.0.0.1 -p 55401 -U lab postgres -Atq -c "select count(*) from absurd.t_main where state not in ('completed','failed','cancelled')"); [ "$s" = 0 ] && break; sleep 1; done
echo "$(ts)done after $i s" >> $R/events.log; kill $M $RP; sleep .3; ./state.sh >> $R/events.log
psql -h 127.0.0.1 -p 55401 -U lab postgres -Atq -c "select attempt,state,count(*) from absurd.r_main group by 1,2 order by 1,2" >> $R/events.log
python - <<PY >> $R/events.log
import collections
rows=[l.strip().split(',') for l in open('$R/sideeffects.log')]
c=collections.Counter((k,n) for k,n,*_ in rows)
for kind in ('work','review'):
    tot=sum(v for (k,n),v in c.items() if k==kind); uniq=len({n for (k,n) in c if k==kind}); print(kind,'exec',tot,'unique',uniq,'dups',tot-uniq)
PY
cat $R/events.log
