"""Utilitaires communs : connexion PG (socket unix, instance jetable), horloge synthétique, oracle."""
import os, json, datetime as dt, pathlib
import psycopg

ROOT = pathlib.Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
D0 = dt.datetime(2026, 3, 2, tzinfo=dt.timezone.utc)

def t(h, m=0, s=0, day=0):
    return D0 + dt.timedelta(days=day, hours=h, minutes=m, seconds=s)

def connect(dbname=None, autocommit=True):
    dbname = dbname or os.environ.get("PITDB", "pitlab")
    host = os.environ.get("PGHOST", str(pathlib.Path.home() / ".cache/tmp/ext"))
    return psycopg.connect(host=host, port=int(os.environ.get("PGPORT", 54329)),
                           user=os.environ.get("PGUSER", "pit"), dbname=dbname,
                           autocommit=autocommit, options="-c default_transaction_read_only=off")

def load_sql(conn, *names):
    for n in names:
        conn.execute((ROOT / "sql" / n).read_text())

def fresh_schema(conn, strict_clock=False):
    load_sql(conn, "001_schema.sql", "002_functions.sql")
    conn.execute("UPDATE pit.config SET strict_clock=%s", (strict_clock,))

def save(name, obj):
    RESULTS.mkdir(exist_ok=True)
    (RESULTS / name).write_text(json.dumps(obj, indent=2, default=str, ensure_ascii=False))

# --- Oracle indépendant (Python pur, aucune SQL de sélection) -------------------------------
def oracle_asof(rows, T, axis="ingested", instrument=None, timeframe=None):
    """rows: liste de dicts {obs_id, source, instrument, timeframe, event_time, revision, ingested_at,
    known_collector_at}. Retourne l'ensemble d'obs_id : dernière version de chaque fait connue à T."""
    kcol = "ingested_at" if axis == "ingested" else "known_collector_at"
    best = {}
    for r in rows:
        if r[kcol] > T: continue
        if instrument and r["instrument"] != instrument: continue
        if timeframe and r["timeframe"] != timeframe: continue
        key = (r["source"], r["instrument"], r["timeframe"], r["event_time"])
        rank = (r["revision"] if r["revision"] is not None else float("-inf"), r[kcol], r["obs_id"])
        if key not in best or rank > best[key][0]:
            best[key] = (rank, r["obs_id"])
    return {v[1] for v in best.values()}

def fetch_rows(conn):
    cur = conn.execute("SELECT obs_id, source, instrument, timeframe, event_time, revision, ingested_at, "
                       "known_collector_at, provider_event_id, finality_status, payload, provenance, first_observed_at FROM pit.obs")
    cols = [d.name for d in cur.description]
    return [dict(zip(cols, r)) for r in cur.fetchall()]
