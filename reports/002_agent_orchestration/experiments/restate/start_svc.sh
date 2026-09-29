#!/bin/bash
cd /tmp/lab/work/restate
exec node svc.mjs >> svc.log 2>&1
