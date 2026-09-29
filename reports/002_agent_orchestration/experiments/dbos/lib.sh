PY=/tmp/lab/work/dbos/v/bin/python; W=/tmp/lab/work/dbos
export SE_LOG=$W/side_effects.log
Q() { psql -h 127.0.0.1 -p 55402 -U lab dbos_app -Atc "$1"; }
snap() { echo "$(date +%s.%N | cut -c1-14) $(Q "select status||'='||count(*) from dbos.workflow_status group by status order by 1" | tr '\n' ' ') exec=$(Q "select coalesce(executor_id,'-')||':'||status||'='||count(*) from dbos.workflow_status where status in ('PENDING','ENQUEUED') group by 1 order by 1" | tr '\n' ' ')"; }
killall_app() { ps aux | grep "[p]y app" | awk '{print $2}' | xargs -r kill -9; }
startw() { # id log
  EXEC_ID=$1 setsid $PY app.py > $W/$2 2>&1 & echo $! ; }
