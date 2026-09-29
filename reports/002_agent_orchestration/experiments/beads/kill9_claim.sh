#!/bin/bash
# kill -9 claim processes at random points on t1 workers 6..15; then check consistency of status/assignee/lease
cd /tmp/lab/work/beads/t1
W=($(cat ../workers.txt))
for r in 1 2 3; do for i in $(seq 6 15); do
  BEADS_ACTOR=kc$r bd update ${W[$i]} --claim >/dev/null 2>&1 & P=$!
  python3 -c "import random,time; time.sleep(random.uniform(0.05,0.5))"; kill -9 $P 2>/dev/null; wait $P 2>/dev/null
done; done
bd list --json -n 0 --all 2>/dev/null | python3 -c "
import sys,json
d=json.load(sys.stdin); bad=0
for i in d:
  if i['title'].startswith('worker'):
    s=i['status']; a=i.get('assignee'); l=i.get('lease_expires_at')
    ok = (s=='open' and not a and not l) or (s=='in_progress' and a) or s=='closed'
    if not ok: bad+=1; print('INCONSISTENT',i['id'],s,a,l)
print('checked',len([i for i in d if i['title'].startswith('worker')]),'inconsistent',bad)
from collections import Counter; print(Counter((i['status'],bool(i.get('lease_expires_at'))) for i in d if i['title'].startswith('worker')))"
