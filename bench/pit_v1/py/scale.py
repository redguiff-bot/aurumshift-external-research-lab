"""Expérience d'échelle indicative (PAS un benchmark de production). Usage: scale.py plain|ts"""
import sys, time, random, json, statistics as st, datetime as dt
from common import *
from gen import gen

def ts_sql():
    s1 = (ROOT/"sql/001_schema.sql").read_text()
    s1 = s1.replace("obs_id              bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,", "obs_id              bigint GENERATED ALWAYS AS IDENTITY,")
    s1 = s1.replace("  CHECK (known_collector_at <= ingested_at)\n);", "  CHECK (known_collector_at <= ingested_at),\n  PRIMARY KEY (obs_id, event_time)\n);\nSELECT create_hypertable('pit.obs','event_time', chunk_time_interval => interval '14 days');")
    s1 = s1.replace("(source, provider_event_id, revision, content_hash) NULLS NOT DISTINCT", "(source, provider_event_id, revision, content_hash, event_time) NULLS NOT DISTINCT")
    s1 = s1.replace("REFERENCES pit.obs(obs_id)", "")  # FK impossible vers un hypertable sans event_time
    s2 = (ROOT/"sql/002_functions.sql").read_text()
    s2 = s2.replace("ON CONFLICT (source, provider_event_id, revision, content_hash) DO NOTHING", "ON CONFLICT (source, provider_event_id, revision, content_hash, event_time) DO NOTHING")
    s2 = s2.replace("AND revision IS NOT DISTINCT FROM p_revision AND content_hash = v_hash;", "AND revision IS NOT DISTINCT FROM p_revision AND content_hash = v_hash AND event_time = p_event_time;")
    return s1, s2

def pct(xs, p): xs = sorted(xs); return xs[min(len(xs)-1, int(len(xs)*p))]

def main(kind):
    db = "pitlab" if kind == "plain" else "pitts"
    conn = connect(db)
    if kind == "plain": load_sql(conn, "001_schema.sql", "002_functions.sql")
    else:
        conn.execute("CREATE EXTENSION IF NOT EXISTS timescaledb")
        a, b = ts_sql(); conn.execute(a); conn.execute(b)
    conn.execute("UPDATE pit.config SET strict_clock=false")
    conn.execute("SET synchronous_commit=off")
    rows = gen(n_instr=250, bars=4200)
    random.Random(1).shuffle(rows)  # ingestion DÉSORDONNÉE (l'ordre d'arrivée n'est pas l'ordre d'event)
    out = {"kind": kind, "rows_submitted": len(rows), "pg_version": conn.execute("show server_version").fetchone()[0]}
    sql = ("SELECT pit.ingest(%s,%s,%s,%s,%s,%s,%s,%s::pit.finality,%s,%s::pit.provenance,%s,%s::jsonb,%s)")
    t0 = time.perf_counter(); B = 5000
    with conn.cursor() as cur:
        for i in range(0, len(rows), B):
            batch = rows[i:i+B]
            with conn.transaction():
                for r in batch:
                    cur.execute(sql, (r[0],r[1],r[2],r[3],r[4],r[5],r[6],r[7],r[8],r[9],r[10],json.dumps({"c": r[12]}),r[11]))
    el = time.perf_counter() - t0
    out["insert_seconds"] = round(el, 1); out["insert_rows_per_s_function_path"] = round(len(rows)/el)
    conn.execute("ANALYZE pit.obs"); conn.execute("ANALYZE pit.obs_receipt")
    q = lambda s: conn.execute(s).fetchone()[0]
    out["obs_rows"] = q("SELECT count(*) FROM pit.obs"); out["receipt_rows"] = q("SELECT count(*) FROM pit.obs_receipt")
    out["heap_bytes"] = q("SELECT pg_table_size('pit.obs')"); out["index_bytes"] = q("SELECT pg_indexes_size('pit.obs')")
    out["receipt_total_bytes"] = q("SELECT pg_total_relation_size('pit.obs_receipt')")
    out["bytes_per_obs_total"] = round((out["heap_bytes"]+out["index_bytes"])/out["obs_rows"])
    out["index_detail"] = {r[0]: r[1] for r in conn.execute("SELECT indexrelid::regclass::text, pg_relation_size(indexrelid) FROM pg_index WHERE indrelid='pit.obs'::regclass")} if kind=="plain" else "voir chunks"
    # Latence PIT
    rnd = random.Random(7); lat = {"asof_one_instrument": [], "latest_known": [], "asof_collector_one": [], "fleet_asof_250_instr": []}
    span = 4200*300
    def rT(): return D0 + dt.timedelta(seconds=rnd.uniform(0.1, 1.0) * span + 300)
    for _ in range(60):
        inst = f"I{rnd.randrange(250):04d}"; T = rT()
        a = time.perf_counter(); conn.execute("SELECT count(*) FROM pit.asof(%s,%s)", (T, inst)).fetchone(); lat["asof_one_instrument"].append((time.perf_counter()-a)*1000)
        a = time.perf_counter(); conn.execute("SELECT * FROM pit.latest_known(%s,'A',%s,'5m')", (T, inst)).fetchall(); lat["latest_known"].append((time.perf_counter()-a)*1000)
        a = time.perf_counter(); conn.execute("SELECT count(*) FROM pit.asof_collector(%s,%s)", (T, inst)).fetchone(); lat["asof_collector_one"].append((time.perf_counter()-a)*1000)
    for _ in range(3):
        T = rT(); a = time.perf_counter(); conn.execute("SELECT count(*) FROM pit.asof(%s,NULL)", (T,)).fetchone(); lat["fleet_asof_250_instr"].append((time.perf_counter()-a)*1000)
    out["latency_ms"] = {k: {"n": len(v), "p50": round(pct(v,.5),2), "p95": round(pct(v,.95),2), "max": round(max(v),2)} for k, v in lat.items()}
    # Exactitude vs oracle (30 échantillons, deux axes)
    bad = 0; n = 0
    for _ in range(30):
        inst = f"I{rnd.randrange(250):04d}"; T = rT()
        cur = conn.execute("SELECT obs_id, source, instrument, timeframe, event_time, revision, ingested_at, known_collector_at FROM pit.obs WHERE instrument=%s", (inst,))
        cols = [d.name for d in cur.description]; rr = [dict(zip(cols, r)) for r in cur.fetchall()]
        for axis, fn in (("ingested","asof"), ("collector","asof_collector")):
            got = {r[0] for r in conn.execute(f"SELECT obs_id FROM pit.{fn}(%s,%s)", (T, inst)).fetchall()}
            if got != oracle_asof(rr, T, axis, instrument=inst): bad += 1
            n += 1
    out["oracle_samples"] = n; out["oracle_mismatches"] = bad
    # Append-only effectif ?
    try: conn.execute("UPDATE pit.obs SET source=source WHERE obs_id=(SELECT min(obs_id) FROM pit.obs)"); out["append_only_update"] = "NOT_BLOCKED"
    except Exception as e: out["append_only_update"] = "BLOCKED: " + str(e).splitlines()[0]
    if kind == "ts":
        out["chunks"] = q("SELECT count(*) FROM timescaledb_information.chunks WHERE hypertable_name='obs'")
        try:
            conn.execute("ALTER TABLE pit.obs SET (timescaledb.compress, timescaledb.compress_segmentby='source,instrument,timeframe', timescaledb.compress_orderby='event_time DESC')")
            a = time.perf_counter()
            conn.execute("SELECT count(compress_chunk(c, if_not_compressed=>true)) FROM show_chunks('pit.obs') c").fetchone()
            out["compress_seconds"] = round(time.perf_counter()-a, 1)
            out["size_after_compress_bytes"] = q("SELECT sum(total_bytes) FROM hypertable_detailed_size('pit.obs')") if False else q("SELECT hypertable_size('pit.obs')")
            a = time.perf_counter(); c1 = conn.execute("SELECT count(*) FROM pit.asof(%s,%s)", (D0+dt.timedelta(days=8), "I0010")).fetchone()[0]
            out["asof_after_compress_ms"] = round((time.perf_counter()-a)*1000, 2); out["asof_after_compress_rows"] = c1
            try: conn.execute("DELETE FROM pit.obs WHERE obs_id=(SELECT min(obs_id) FROM pit.obs)"); out["append_only_delete_on_compressed"] = "NOT_BLOCKED"
            except Exception as e: out["append_only_delete_on_compressed"] = "BLOCKED: " + str(e).splitlines()[0]
        except Exception as e: out["compression_error"] = str(e).splitlines()[0]
    save(f"scale_{kind}.json", out)
    print(json.dumps(out, indent=1, default=str))

main(sys.argv[1])
