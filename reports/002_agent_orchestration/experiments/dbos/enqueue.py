import os, sys, time
from dbos import DBOS, DBOSConfig, Queue
import app
from dbos import DBOSClient
c = DBOSClient(system_database_url=app.DB)
n = int(sys.argv[1]) if len(sys.argv)>1 else 20
for i in range(n):
    c.enqueue({"queue_name":"q","workflow_name":"pipeline","workflow_id":f"t{i}","app_version":"v1"}, i)
print(f"[{time.time():.3f}] enqueued {n}")
