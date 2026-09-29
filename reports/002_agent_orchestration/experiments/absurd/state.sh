#!/bin/bash
P="psql -h 127.0.0.1 -p 55401 -U lab postgres -Atq"
for q in main review; do echo -n "$q tasks: "; $P -c "select string_agg(state||'='||c, ' ') from (select state,count(*) c from absurd.t_$q group by 1 order by 1) s"; done
