#!/bin/bash
# N parallel `bd update <id> --claim` with distinct BEADS_ACTOR against one ready item; expect exactly one exit=0
cd /tmp/lab/work/beads/t1; Y=$1; N=$2
for a in $(seq 1 $N); do ( BEADS_ACTOR=agent$a bd update $Y --claim >/tmp/race.$a.out 2>&1; echo "agent$a exit=$?" ) & done; wait
