#!/bin/bash
# kill -9 a writing bd process at random points; then verify.
cd /tmp/lab/work/beads/t2
ok=0; killed=0; fail=0
for i in $(seq 1 60); do
  bd create "k-$i" --silent >/tmp/k.out 2>&1 &
  P=$!
  python3 -c "import random,time; time.sleep(random.uniform(0.02,0.6))"
  if kill -9 $P 2>/dev/null; then killed=$((killed+1)); else ok=$((ok+1)); fi
  wait $P 2>/dev/null
done
echo "loop: killed_alive=$killed finished_before_kill=$ok"
