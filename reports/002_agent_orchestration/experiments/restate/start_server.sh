#!/bin/bash
# usage: start_server.sh  (data dir = /tmp/lab/work/restate/restate-data via cwd)
cd /tmp/lab/work/restate
exec ./node_modules/@restatedev/restate-server-linux-x64/bin/restate-server --no-logo -c restate.toml >> server.log 2>&1
