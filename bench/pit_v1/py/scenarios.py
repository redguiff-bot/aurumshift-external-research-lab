"""Scénarios adversariaux S1–S12 + contrôles fuyants. Attentes écrites à la main (indépendantes de l'oracle)."""
import json, sys
from common import *

def run():
    conn = connect(); fresh_schema(conn, strict_clock=False)
    ids = {}
    def ing(label, instr, source, ev, pid, rev, ds, fin, prov, fo, payload, ing_at, basis="PROVIDER_FLAG", tf="5m"):
        r = conn.execute("SELECT pit.ingest(%s,%s,%s,%s,%s,%s,%s,%s::pit.finality,%s,%s::pit.provenance,%s,%s::jsonb,%s)",
                         (source, instr, tf, ev, pid, rev, ds, fin, basis, prov, fo, json.dumps(payload), ing_at)).fetchone()[0]
        ids[label] = r
        return r
    F, P, U = "FINAL", "PRELIMINARY", "UNKNOWN"
    # S1 live normal
    ing("S1.a","S1","A",t(10),"a1",None,"live",F,"LIVE",t(10,0,2),{"c":100},t(10,0,3))
    # S2 arrivée tardive (LIVE, 2m30 après l'événement)
    ing("S2.a","S2","A",t(10,5),"a1",None,"live",F,"LIVE",t(10,7,30),{"c":100},t(10,7,31))
    # S3 backfill 20:00 pour événement 10:00 ; S3b backfill avec first_observed_at MENSONGER ; S3c backfill étiqueté LIVE
    ing("S3.a","S3","A",t(10),"a1",None,"bf1",F,"BACKFILL",t(20),{"c":100},t(20))
    ing("S3b.a","S3b","A",t(10),"a1",None,"bf1",F,"BACKFILL",t(10,0,1),{"c":100},t(20))
    ing("S3c.a","S3c","A",t(10),"a1",None,"bf1",F,"LIVE",t(10,0,1),{"c":100},t(20))
    # S4 correction fournisseur (revision 1 puis 2) ; S4b ordre inversé (rev2 avant rev1 retardée)
    ing("S4.r1","S4","A",t(11),"e1",1,"live",F,"LIVE",t(11,0,4),{"c":100},t(11,0,5))
    ing("S4.r2","S4","A",t(11),"e1",2,"live","CORRECTED","LIVE",t(11,20),{"c":101},t(11,20,1))
    ing("S4b.r2","S4b","A",t(11),"e1",2,"live","CORRECTED","LIVE",t(11,20),{"c":101},t(11,20,1))
    ing("S4b.r1","S4b","A",t(11),"e1",1,"live",F,"LIVE",t(11,25),{"c":100},t(11,25,1))
    # S5 doublons : même message 3 fois ; S5b redélivrance d'un message SUPERSEDÉ (révisions NULL)
    ing("S5.a1","S5","A",t(12),"d1",None,"live",F,"LIVE",t(12,0,4),{"c":100},t(12,0,5))
    ing("S5.a2","S5","A",t(12),"d1",None,"live",F,"LIVE",t(12,0,8),{"c":100},t(12,0,9))
    ing("S5.a3","S5","A",t(12),"d1",None,"replay-import",F,"BACKFILL",t(12,15),{"c":100},t(12,15))
    ing("S5b.A","S5b","A",t(12),"mA",None,"live",F,"LIVE",t(12,0,4),{"c":100},t(12,0,5))
    ing("S5b.B","S5b","A",t(12),"mB",None,"live","CORRECTED","LIVE",t(12,10),{"c":102},t(12,10,1))
    ing("S5b.A2","S5b","A",t(12),"mA",None,"live",F,"LIVE",t(12,20),{"c":100},t(12,20,1))
    # S6 deux fournisseurs en désaccord
    ing("S6.A","S6","A",t(13),"z1",None,"live",F,"LIVE",t(13,0,1),{"c":200},t(13,0,2))
    ing("S6.B","S6","B",t(13),"y1",None,"live",F,"LIVE",t(13,0,29),{"c":201},t(13,0,30))
    # S7 préliminaire -> final À CHIFFRES IDENTIQUES ; S7b final puis restatement préliminaire
    ing("S7.p","S7","A",t(14),"x7",None,"live",P,"LIVE",t(14,0,3),{"c":100},t(14,0,4))
    ing("S7.f","S7","A",t(14),"x7",None,"live",F,"LIVE",t(14,5),{"c":100},t(14,5,1))
    ing("S7b.f","S7b","A",t(14),"x8",None,"live",F,"LIVE",t(14,5),{"c":100},t(14,5,1))
    ing("S7b.p","S7b","A",t(14),"x8",None,"live",P,"LIVE",t(14,8),{"c":100},t(14,8,1))
    # S8 manquante : 15:05 jamais observée ; S8b : 15:05 arrivée par backfill à 20:00
    for i,(inst,skip_late) in enumerate([("S8",False),("S8b",True)]):
        ing(f"{inst}.0",inst,"A",t(15),"m0",None,"live",F,"LIVE",t(15,0,1),{"c":1},t(15,0,2))
        ing(f"{inst}.2",inst,"A",t(15,10),"m2",None,"live",F,"LIVE",t(15,10,1),{"c":3},t(15,10,2))
    ing("S8b.1","S8b","A",t(15,5),"m1",None,"bf",F,"BACKFILL",t(20),{"c":2},t(20))
    # S9 périmée
    ing("S9.a","S9","A",t(16),"s1",None,"live",F,"LIVE",t(16,0,1),{"c":100},t(16,0,2))
    # S10 ré-import identique (dédup) puis restatement silencieux
    ing("S10.v1","S10","A",t(17),"k1",1,"v1",F,"LIVE",t(17,0,4),{"c":100},t(17,0,5))
    ing("S10.v2","S10","A",t(17),"k1",1,"v2",F,"BACKFILL",t(17,30),{"c":100},t(17,30))
    ing("S10.v3","S10","A",t(17),"k1",1,"v3",F,"BACKFILL",t(18),{"c":105},t(18))
    rows = fetch_rows(conn)
    byid = {r["obs_id"]: r for r in rows}
    lab = {}
    for k, v in ids.items(): lab.setdefault(v, k)  # doublons dédoublonnés => même obs_id : on garde le 1er libellé
    out_dedup = {k: lab[v] for k, v in ids.items() if lab[v] != k}
    def q(fn, T, instr):
        return {lab[r[0]] for r in conn.execute(f"SELECT obs_id FROM pit.{fn}(%s, %s)", (T, instr)).fetchall()}
    # (label, fonction, instrument, T, attendu) — attendu écrit à la main
    checks = [
     ("S1 avant réception",            "asof","S1",t(10,0,1), set()),
     ("S1 après réception",            "asof","S1",t(10,0,4), {"S1.a"}),
     ("S2 avant arrivée tardive",      "asof","S2",t(10,6),   set()),
     ("S2 après arrivée tardive",      "asof","S2",t(10,8),   {"S2.a"}),
     ("S3 BACKFILL décision 10:05",    "asof","S3",t(10,5),   set()),
     ("S3 après backfill",             "asof","S3",t(20,0,1), {"S3.a"}),
     ("S3b backfill à first_observed mensonger","asof","S3b",t(10,5), set()),
     ("S3c backfill mal étiqueté LIVE","asof","S3c",t(10,5),  set()),
     ("S4/S11 décision entre publication et correction","asof","S4",t(11,10), {"S4.r1"}),
     ("S4 après correction",           "asof","S4",t(11,30),  {"S4.r2"}),
     ("S4b rev2 arrivée avant rev1: rev2 gagne","asof","S4b",t(11,30), {"S4b.r2"}),
     ("S4b avant rev1 retardée",       "asof","S4b",t(11,22), {"S4b.r2"}),
     ("S5 doublons: 1 seule version",  "asof","S5",t(12,30),  {"S5.a1"}),
     ("S5b redélivrance superseded ignorée","asof","S5b",t(12,30), {"S5b.B"}),
     ("S6 A seul avant B",             "asof","S6",t(13,0,10),{"S6.A"}),
     ("S6 A et B après",               "asof","S6",t(13,1),   {"S6.A","S6.B"}),
     ("S7 préliminaire visible (ALL)", "asof","S7",t(14,2),   {"S7.p"}),
     ("S7 FINAL_ONLY avant final",     "asof_final","S7",t(14,2), set()),
     ("S7 FINAL_ONLY après final",     "asof_final","S7",t(14,6), {"S7.f"}),
     ("S7b restatement préliminaire: dernier gagne (ALL)","asof","S7b",t(14,10), {"S7b.p"}),
     ("S7b FINAL_ONLY select-puis-filtre: rien","asof_final","S7b",t(14,10), set()),
     ("S9 dernier connu",              "asof","S9",t(16,30),  {"S9.a"}),
     ("S10 avant ré-import",           "asof","S10",t(17,10), {"S10.v1"}),
     ("S10 après ré-import identique", "asof","S10",t(17,40), {"S10.v1"}),
     ("S10 après restatement",         "asof","S10",t(18,5),  {"S10.v3"}),
    ]
    out = {"checks": [], "controls": {}, "counts": {}, "dedup_aliases": out_dedup}
    ok = True
    for name, fn, inst, T, exp in checks:
        got = q(fn, T, inst)
        o = {lab[i] for i in oracle_asof(rows, T, "ingested", instrument=inst)}
        if fn == "asof_final":
            o = {l for l in o if byid[ids[l]]["finality_status"] in ("FINAL","CORRECTED")}
        passed = (got == exp == o)
        ok &= passed
        out["checks"].append({"scenario": name, "T": T, "sql": sorted(got), "expected": sorted(exp), "oracle": sorted(o), "pass": passed})
    # Comptages (dédup) et vues
    cnt = lambda s: conn.execute(s).fetchone()[0]
    out["counts"] = {
      "S5_obs_rows": cnt("SELECT count(*) FROM pit.obs WHERE instrument='S5'"),
      "S5_receipts": cnt("SELECT count(*) FROM pit.obs_receipt r JOIN pit.obs o USING(obs_id) WHERE o.instrument='S5'"),
      "S5b_obs_rows": cnt("SELECT count(*) FROM pit.obs WHERE instrument='S5b'"),
      "S5_first_known_unchanged": cnt("SELECT ingested_at FROM pit.obs WHERE instrument='S5'") == t(12,0,5),
      "S10_obs_rows": cnt("SELECT count(*) FROM pit.obs WHERE instrument='S10'"),
      "S10_receipts": cnt("SELECT count(*) FROM pit.obs_receipt r JOIN pit.obs o USING(obs_id) WHERE o.instrument='S10'"),
      "S10_silent_restatements": cnt("SELECT count(*) FROM pit.silent_restatements WHERE provider_event_id='k1'"),
      "S6_disagreement_view": cnt("SELECT count(*) FROM pit.provider_disagreement WHERE instrument='S6'"),
    }
    out["counts_pass"] = (out["counts"]["S5_obs_rows"]==1 and out["counts"]["S5_receipts"]==3 and out["counts"]["S5b_obs_rows"]==2
       and out["counts"]["S5_first_known_unchanged"] and out["counts"]["S10_obs_rows"]==2 and out["counts"]["S10_receipts"]==3
       and out["counts"]["S10_silent_restatements"]==1 and out["counts"]["S6_disagreement_view"]==1)
    ok &= out["counts_pass"]
    # Slots / garde fail-closed (S8, S8b, S9)
    def slots(inst, T):
        return [(r[0], r[1]) for r in conn.execute("SELECT slot,status FROM pit.slots(%s,'A',%s,'5m',%s,%s,'5 minutes')", (T, inst, t(15), t(15,10))).fetchall()]
    s8 = [s for _, s in slots("S8", t(15,12))]; s8b = [s for _, s in slots("S8b", t(15,12))]
    out["slots"] = {"S8": s8, "S8b": s8b,
      "S8_expected": ["AVAILABLE","NEVER_OBSERVED","AVAILABLE"], "S8b_expected": ["AVAILABLE","NOT_YET_KNOWN_AT_T","AVAILABLE"]}
    ok &= (s8 == out["slots"]["S8_expected"] and s8b == out["slots"]["S8b_expected"])
    def gate(inst, T, stale=None, frm=t(15), to=t(15,10)):
        try:
            conn.execute("SELECT pit.assert_replayable(%s,'A',%s,'5m',%s,%s,'5 minutes',%s)", (T, inst, frm, to, stale)); return "PASS"
        except Exception as e:
            return "FAIL_CLOSED: " + str(e).splitlines()[0]
    out["gate"] = {"S8_missing": gate("S8", t(15,12)), "S8b_backfilled_later": gate("S8b", t(15,12)),
                   "S8b_after_backfill": gate("S8b", t(20,1)),
                   "S9_stale_30m": gate("S9", t(16,30), "10 minutes", t(16), t(16)),
                   "S9_fresh_5m": gate("S9", t(16,5), "10 minutes", t(16), t(16))}
    exp_gate = {"S8_missing":"FAIL","S8b_backfilled_later":"FAIL","S8b_after_backfill":"PASS","S9_stale_30m":"FAIL","S9_fresh_5m":"PASS"}
    gate_ok = all(out["gate"][k].startswith(v) for k, v in exp_gate.items())
    out["gate_pass"] = gate_ok; ok &= gate_ok
    # --- CONTRÔLES FUYANTS : doivent être détectés par la même batterie (validation de la batterie) ---
    ctl = {}
    def leak_of(result_ids, T):
        return sorted(lab[i] for i in result_ids if byid[i]["ingested_at"] > T)
    def ctl_sql(name, sql_template):
        res = {"leaks": [], "wrong": []}
        for cname, fn, inst, T, exp in checks:
            if fn != "asof": continue
            got_ids = {r[0] for r in conn.execute(sql_template, {"T": T, "i": inst}).fetchall()}
            leaks = leak_of(got_ids, T)
            got = {lab[i] for i in got_ids}
            if leaks: res["leaks"].append({"check": cname, "leaked": leaks})
            elif got != exp: res["wrong"].append({"check": cname, "got": sorted(got), "expected": sorted(exp)})
        res["verdict"] = "LOOKAHEAD_DETECTED" if res["leaks"] else ("WRONG_RESULT_NO_LEAK" if res["wrong"] else "LOOKAHEAD_PREVENTED")
        ctl[name] = res
    # C1: filtre event_time seul (aucune notion de connaissance)
    ctl_sql("C1_event_time_only", """SELECT DISTINCT ON (source,instrument,timeframe,event_time) obs_id FROM pit.obs
        WHERE instrument=%(i)s AND event_time <= %(T)s ORDER BY source,instrument,timeframe,event_time,revision DESC NULLS LAST,ingested_at DESC,obs_id DESC""")
    # C2: axe first_observed_at brut (NULL exclus silencieusement)
    ctl_sql("C2_first_observed_at_raw", """SELECT DISTINCT ON (source,instrument,timeframe,event_time) obs_id FROM pit.obs
        WHERE instrument=%(i)s AND first_observed_at <= %(T)s ORDER BY source,instrument,timeframe,event_time,revision DESC NULLS LAST,first_observed_at DESC,obs_id DESC""")
    # C3: axe COLLECTEUR validé (référence variante)
    ctl_sql("C3_collector_axis_validated", """SELECT DISTINCT ON (source,instrument,timeframe,event_time) obs_id FROM pit.obs
        WHERE instrument=%(i)s AND known_collector_at <= %(T)s ORDER BY source,instrument,timeframe,event_time,revision DESC NULLS LAST,known_collector_at DESC,obs_id DESC""")
    # C4: dernière version au sens ARRIVÉE sans tri par révision (ordre d'arrivée pur)
    ctl_sql("C4_arrival_order_only", """SELECT DISTINCT ON (source,instrument,timeframe,event_time) obs_id FROM pit.obs
        WHERE instrument=%(i)s AND ingested_at <= %(T)s ORDER BY source,instrument,timeframe,event_time,ingested_at DESC,obs_id DESC""")
    # C5: SCD-1 (état courant écrasé en place) rejoué à T : le contenu final est ce que l'on lit
    conn.execute("DROP TABLE IF EXISTS pit.ctl_scd1")
    conn.execute("CREATE TABLE pit.ctl_scd1 AS SELECT DISTINCT ON (source,instrument,timeframe,event_time) obs_id, source,instrument,timeframe,event_time FROM pit.obs ORDER BY source,instrument,timeframe,event_time,revision DESC NULLS LAST,ingested_at DESC,obs_id DESC")
    ctl_sql("C5_scd1_current_state_overwrite", "SELECT obs_id FROM pit.ctl_scd1 WHERE instrument=%(i)s AND event_time <= %(T)s")
    # C6: coalesce(first_observed_at, event_time) — hypothèse « à défaut, l'événement était connu à son heure »
    ctl_sql("C6_coalesce_event_time", """SELECT DISTINCT ON (source,instrument,timeframe,event_time) obs_id FROM pit.obs
        WHERE instrument=%(i)s AND COALESCE(first_observed_at, event_time) <= %(T)s ORDER BY source,instrument,timeframe,event_time,revision DESC NULLS LAST,obs_id DESC""")
    out["controls"] = ctl
    # Référence : axe STRICT via fonction pit.asof — aucune fuite sur toute la batterie
    ref_leaks = []
    for cname, fn, inst, T, exp in checks:
        got_ids = {r[0] for r in conn.execute(f"SELECT obs_id FROM pit.{fn}(%s,%s)", (T, inst)).fetchall()}
        if leak_of(got_ids, T): ref_leaks.append(cname)
    out["reference_leaks"] = ref_leaks
    out["reference_verdict"] = "LOOKAHEAD_DETECTED" if ref_leaks else "LOOKAHEAD_PREVENTED"
    out["all_reference_checks_pass"] = ok
    run.ctx = dict(checks=checks, rows=rows, lab=lab, ids=ids)
    save("scenarios.json", out) if not __import__('os').environ.get('PITNOSAVE') else None
    n_pass = sum(c["pass"] for c in out["checks"])
    print(f"checks {n_pass}/{len(out['checks'])} pass ; counts_pass={out['counts_pass']} ; gate_pass={gate_ok} ; slots ok={s8==out['slots']['S8_expected'] and s8b==out['slots']['S8b_expected']}")
    print("reference:", out["reference_verdict"])
    for k, v in ctl.items(): print(f"  {k}: {v['verdict']} (leaks={len(v['leaks'])}, wrong={len(v['wrong'])})")
    for c in out["checks"]:
        if not c["pass"]: print("FAIL", c)
    print("gate:", json.dumps(out["gate"], ensure_ascii=False))
    return ok

if __name__ == "__main__":
    sys.exit(0 if run() else 1)
