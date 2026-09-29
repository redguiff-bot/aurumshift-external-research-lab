#!/bin/bash
cd /tmp/lab/work/restate
E=/home/user/aurumshift-external-research-lab/reports/002_agent_orchestration/experiments/restate
export RESTATE_ADMIN_URL=http://127.0.0.1:55412
setsid nohup $E/start_server.sh >/dev/null 2>&1 &
sleep 12; echo "server up after unclean death of both procs; deployments:"; curl -s localhost:55412/deployments | grep -o '"id":"dp_[^"]*"' | head -2
rm -f sidefx.log
for i in $(seq 1 20); do curl -s -X POST localhost:55411/Agent/d$i/run/send -H 'content-type: application/json' -d "\"task$i\"" >/dev/null; done
echo submitted 20 with service DOWN
SP=$(cat /proc/$(pgrep -x restate-server | head -1)/status >/dev/null; pgrep -x restate-server | head -1)
kill -TERM $SP; T=$(date +%s); while kill -0 $SP 2>/dev/null; do sleep 0.2; done; echo graceful stop took $(( $(date +%s)-T ))s
du -sh restate-data
sleep 60
setsid nohup $E/start_server.sh >/dev/null 2>&1 &
sleep 12; echo pending after restart: $(./node_modules/.bin/restate --yes invocations list 2>&1 | grep -c Target)
setsid nohup $E/start_svc.sh >/dev/null 2>&1 &
sleep 45
echo START $(grep -c WORK_START sidefx.log) END $(grep -c WORK_END sidefx.log) REVIEW $(grep -c REVIEW sidefx.log)
./node_modules/.bin/restate --yes invocations list 2>&1 | head -3
ps -o rss,nlwp,cmd -C restate-server | cut -c1-60; du -sh restate-data
