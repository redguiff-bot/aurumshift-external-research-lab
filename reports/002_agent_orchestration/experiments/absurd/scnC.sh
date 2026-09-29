#!/bin/bash
# usage: scnC.sh <reconnect:0|1> <outdir>   kill -9 postmaster at +4s, restart PG after 4s down
cd $(dirname $0); export PATH=/tmp/lab/work/absurd/venv/bin:$PATH
RC=$1; R=$2; ./reset.sh $R; export ABS_LOGDIR=$R WORK_SECS=3 REVIEW_SECS=2
RECON=""; [ "$RC" = 1 ] && RECON=reconnect
ts(){ python -c "import time;print(f'{time.time():.3f}',end=' ')"; }
python submit.py 20 5 > $R/submit.log
python worker.py main 20 5 $RECON > $R/w_M.log 2>&1 & M=$!
python worker.py main 20 5 $RECON > $R/w_M2.log 2>&1 & M2=$!
python worker.py review 20 5 $RECON > $R/w_R.log 2>&1 & RP=$!
sleep 4
PMPID=$(head -1 /tmp/lab/pg/absurd/postmaster.pid)
echo "$(ts)kill -9 postmaster $PMPID" >> $R/events.log; kill -9 $PMPID
sleep 4
echo "$(ts)restarting PG (pgstart.sh)" >> $R/events.log
rm -f /tmp/.s.PGSQL.55401.lock
/tmp/lab/bin/pgstart.sh absurd 55401 >> $R/events.log 2>&1
echo "$(ts)PG up" >> $R/events.log
for i in $(seq 1 90); do
  s=$(psql -h 127.0.0.1 -p 55401 -U lab postgres -Atq -c "select count(*) from absurd.t_main where state not in ('completed','failed','cancelled')" 2>/dev/null)
  [ "$s" = 0 ] && break; sleep 1; done
echo "$(ts)polls=$i last_nonterminal=$s" >> $R/events.log
echo "worker procs alive: $(kill -0 $M 2>/dev/null && echo M1) $(kill -0 $M2 2>/dev/null && echo M2) $(kill -0 $RP 2>/dev/null && echo R)" >> $R/events.log
kill $M $M2 $RP 2>/dev/null; sleep 0.3
./state.sh | tee $R/final_state.txt
psql -h 127.0.0.1 -p 55401 -U lab postgres -Atq -c "select attempt,state,count(*) from absurd.r_main group by 1,2 order by 1,2" > $R/run_counts.txt
python - <<PY | tee $R/analysis.txt
import collections
rows=[l.strip().split(',') for l in open('$R/sideeffects.log')]
c=collections.Counter((k,n) for k,n,*_ in rows)
for kind in ('work','review'):
    tot=sum(v for (k,n),v in c.items() if k==kind); uniq=len({n for (k,n) in c if k==kind}); print(kind,'exec',tot,'unique',uniq,'dups',tot-uniq)
PY
cat $R/events.log; cat $R/run_counts.txt; grep -h CRASH $R/w_*.log | cut -c1-160
