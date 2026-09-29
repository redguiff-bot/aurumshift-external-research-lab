#!/bin/bash
P=/tmp/lab/pg18root/usr/lib/postgresql/18/bin
psql -h 127.0.0.1 -p 55402 -U lab postgres -qc "drop database if exists dbos_app with (force)" -c "create database dbos_app"
rm -f /tmp/lab/work/dbos/side_effects.log
