"""Course commit-order != timestamp-order. Trois régimes : NONE, WRITER_LOCK_ONLY, WRITER_LOCK+READER_SHARED_CUTOFF."""
import threading, time, json
from common import *

ARGS = lambda inst, pid, c: ("A", inst, "5m", t(10), pid, None, "v", "FINAL", "X", "LIVE", None, json.dumps({"c": c}))

def digest(conn, T, inst):
    return sorted(r[0] for r in conn.execute("SELECT provider_event_id FROM pit.asof(%s,%s)", (T, inst)).fetchall())

def regime(name):
    admin = connect(); fresh_schema(admin, strict_clock=True); load_sql(admin, "003_race.sql")
    inst = "RACE"
    # Le fait est distinct par event_time pour A et B
    A = connect(autocommit=False); B = connect(autocommit=True); R = connect(autocommit=False)
    locked = name != "NONE"
    ing = "pit.ingest_locked" if locked else "pit.ingest"
    extra = "" if locked else ",NULL"
    def call(c, pid, ev, val):
        return c.execute(f"SELECT {ing}(%s,%s,%s,%s,%s,%s,%s,%s::pit.finality,%s,%s::pit.provenance,%s,%s::jsonb{extra})",
                         ("A", inst, "5m", ev, pid, None, "v", "FINAL", "X", "BACKFILL", None, json.dumps({"c": val}))).fetchone()[0]
    call(A, "a", t(10), 1)                       # A stampe t1, NON commité
    res = {}
    def writer_b():
        res["b_start"] = time.time(); call(B, "b", t(10, 5), 2); res["b_done"] = time.time()
    def decider():
        if name == "LOCK_RW":
            T = R.execute("SELECT pit.decision_cutoff()").fetchone()[0]
        else:
            T = R.execute("SELECT clock_timestamp()").fetchone()[0]
        res["T"] = T; res["decision"] = digest(R, T, inst); R.commit()
    if name == "NONE" or name == "LOCK_W":
        thb = threading.Thread(target=writer_b); thb.start(); thb.join(timeout=3 if name=="LOCK_W" else 10)
        time.sleep(0.3)
        decider()
        A.commit()
        thb.join(timeout=10)
    else:  # LOCK_RW : lecteur en attente derrière A, puis B derrière lecteur
        thr = threading.Thread(target=decider); thr.start(); time.sleep(0.3)
        thb = threading.Thread(target=writer_b); thb.start(); time.sleep(0.5)
        A.commit(); thr.join(timeout=10); thb.join(timeout=10)
    replay = digest(admin, res["T"], inst)
    stable = res["decision"] == replay
    return {"regime": name, "T": res["T"], "decision_saw": res["decision"], "replay_sees": replay,
            "REPLAY_STABLE": stable, "verdict": "LOOKAHEAD_PREVENTED" if stable else "LOOKAHEAD_DETECTED"}

if __name__ == "__main__":
    out = [regime(n) for n in ("NONE", "LOCK_W", "LOCK_RW")]
    save("race.json", out)
    for o in out: print(o["regime"], "decision=", o["decision_saw"], "replay=", o["replay_sees"], o["verdict"])
