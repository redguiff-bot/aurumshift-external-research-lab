"""Candidat nearform/temporal_tables (plpgsql) — commit 1824073a. Tests de falsification PIT."""
import json, time, threading
from common import *
c = connect("pitc"); r = {}
c.execute("DROP TABLE IF EXISTS bars, bars_h CASCADE")
c.execute("CREATE TABLE bars (instrument text, event_time timestamptz, close numeric, sys_period tstzrange NOT NULL DEFAULT tstzrange(current_timestamp,null), PRIMARY KEY (instrument,event_time))")
c.execute("CREATE TABLE bars_h (LIKE bars)")
c.execute("CREATE TRIGGER v BEFORE INSERT OR UPDATE OR DELETE ON bars FOR EACH ROW EXECUTE PROCEDURE versioning('sys_period','bars_h',true)")
asof = lambda T, i: c.execute("SELECT close FROM (SELECT * FROM bars UNION ALL SELECT * FROM bars_h) u WHERE instrument=%s AND sys_period @> %s::timestamptz ORDER BY event_time DESC LIMIT 1", (i, T)).fetchall()
# T1 backfill : event 10:00 (2026), inséré maintenant (horloge DB réelle) => invisible à T=2026-03-02 10:05
c.execute("INSERT INTO bars VALUES ('B','2026-03-02 10:00',100)")
r["T1_backfill_invisible_at_decision_time"] = (asof("2026-03-02 10:05", "B") == [])
# T2 falsification d'horloge : l'appelant peut-il forger sys_period ?
try:
    c.execute("INSERT INTO bars VALUES ('F','2026-03-02 10:00',100,tstzrange('2026-03-02 10:00',null))")
    r["T2_caller_supplied_sys_period"] = "ACCEPTED_BUT_TRIGGER_OVERWRITES=" + str(asof("2026-03-02 10:05","F") != [])
except Exception as e: r["T2_caller_supplied_sys_period"] = "REJECTED: " + str(e).splitlines()[0]
# T3 correction = UPDATE de la table courante (mutable) ; l'historique conserve v1
c.execute("INSERT INTO bars VALUES ('C','2026-03-02 11:00',100)"); time.sleep(0.05)
mid = c.execute("SELECT clock_timestamp()").fetchone()[0]; time.sleep(0.05)
c.execute("UPDATE bars SET close=101 WHERE instrument='C'")
r["T3_as_of_before_correction"] = asof(mid, "C")[0][0]; r["T3_as_of_after_correction"] = asof(c.execute("SELECT clock_timestamp()").fetchone()[0], "C")[0][0]
# T4 deux versions du même fait avec arrivée désordonnée par révision : le modèle n'a pas de 'revision' -> dernier arrivé gagne
c.execute("INSERT INTO bars VALUES ('D','2026-03-02 12:00',102)")
c.execute("UPDATE bars SET close=100 WHERE instrument='D'")   # rev1 arrive après rev2
r["T4_out_of_order_revision_current_value"] = float(c.execute("SELECT close FROM bars WHERE instrument='D'").fetchone()[0])  # 100 = rev1 périmée gagne
# T5 deux fournisseurs : clé (instrument,event_time) sans source => conflit
try: c.execute("INSERT INTO bars VALUES ('D','2026-03-02 12:00',105)"); r["T5_two_providers_same_key"]="ACCEPTED"
except Exception as e: r["T5_two_providers_same_key"] = "REJECTED_UNIQUE (un seul fournisseur/fait sans modification du schéma)"
# T6 append-only : la table courante est UPDATE/DELETE-able par conception
c.execute("DELETE FROM bars WHERE instrument='D'")
r["T6_delete_moves_to_history"] = c.execute("SELECT count(*) FROM bars_h WHERE instrument='D'").fetchone()[0]
# T7 course txn-start vs commit : now()=début de transaction (t1) mais visible seulement au commit
A = connect("pitc", autocommit=False); B = connect("pitc")
A.execute("SELECT 1"); A.execute("INSERT INTO bars VALUES ('R1','2026-03-02 13:00',1)")     # sys_period start = début txn A (t1)
time.sleep(0.2); B.execute("INSERT INTO bars VALUES ('R2','2026-03-02 13:05',2)")            # commit immédiat, t2 > t1
T = c.execute("SELECT clock_timestamp()").fetchone()[0]
dec = sorted(x[0] for x in c.execute("SELECT instrument FROM (SELECT * FROM bars UNION ALL SELECT * FROM bars_h) u WHERE instrument IN ('R1','R2') AND sys_period @> %s::timestamptz", (T,)).fetchall())
A.commit()
rep = sorted(x[0] for x in c.execute("SELECT instrument FROM (SELECT * FROM bars UNION ALL SELECT * FROM bars_h) u WHERE instrument IN ('R1','R2') AND sys_period @> %s::timestamptz", (T,)).fetchall())
r["T7_race_decision_saw"] = dec; r["T7_race_replay_sees"] = rep; r["T7_verdict"] = "LOOKAHEAD_PREVENTED" if dec == rep else "LOOKAHEAD_DETECTED"
save("cand_temporal_tables.json", r); print(json.dumps(r, indent=1, default=str))
