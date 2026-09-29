#!/bin/bash
# usage: scenC.sh DB mode(immediate|kill9)
cd $(dirname $0); D=$1; MODE=$2; PGD=/tmp/lab/pg/procrastinate
./mkdb.sh $D >/dev/null 2>&1; rm -f /tmp/lab/work/procrastinate/$D.side.log
export RETRY_STALLED=1
./run_worker.sh $D w1 > logs/C_${D}_w1.log 2>&1 & W1=$!
sleep 4
/tmp/lab/work/procrastinate/v/bin/python defer.py $D work 20
sleep 4.5
echo "PG crash ($MODE) at $(date +%s.%N)"
if [ $MODE = immediate ]; then su lab -c "/tmp/lab/pg18root/usr/lib/postgresql/18/bin/pg_ctl -D $PGD -m immediate stop" | tail -1
else PM=$(head -1 $PGD/postmaster.pid); pkill -9 -P $PM; kill -9 $PM; sleep 1; fi
sleep 15
echo "PG down 15s; worker alive? $(kill -0 $W1 2>/dev/null && echo yes || echo NO)"
echo "restart PG at $(date +%s.%N)"; /tmp/lab/bin/pgstart.sh procrastinate 55403 >/dev/null 2>&1
for i in $(seq 1 20); do echo "$(date +%s.%N) worker_alive=$(kill -0 $W1 2>/dev/null && echo y || echo n) $(./q.sh $D "select string_agg(task_name||':'||status||':'||c, ' ' order by task_name,status) from (select task_name,status,count(*) c from procrastinate_jobs group by 1,2) x" 2>&1 | head -1)"; sleep 5; done
kill -TERM $W1 2>/dev/null; sleep 3
cp /tmp/lab/work/procrastinate/$D.side.log logs/C_${D}_side.log
echo "side-effect lines: $(wc -l < logs/C_${D}_side.log); duplicates:"; cut -d, -f1,2 logs/C_${D}_side.log | sort | uniq -c | awk '$1>1'
echo "worker log error lines:"; grep -ci "error\|exception\|warning" logs/C_${D}_w1.log; grep -i "warning\|error\|stopp" logs/C_${D}_w1.log | cut -c1-200 | sort | uniq -c | sort -rn | head -8
