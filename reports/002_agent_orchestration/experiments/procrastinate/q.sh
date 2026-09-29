#!/bin/bash
psql -h 127.0.0.1 -p 55403 -U lab -d $1 -At -c "${2:-select task_name,status,attempts,count(*) from procrastinate_jobs group by 1,2,3 order by 1,2,3}"
