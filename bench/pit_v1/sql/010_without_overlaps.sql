CREATE EXTENSION IF NOT EXISTS btree_gist;
DROP SCHEMA IF EXISTS w CASCADE; CREATE SCHEMA w;
-- (A) Table SCD2 MUTABLE avec intervalle de connaissance + contrainte PG18 WITHOUT OVERLAPS
CREATE TABLE w.scd2 (instrument text, event_time timestamptz, val int, known tstzrange NOT NULL,
  PRIMARY KEY (instrument, event_time, known WITHOUT OVERLAPS));
-- publication v1 connue à 10:05, ouverte
INSERT INTO w.scd2 VALUES ('X','2026-03-02 10:00', 100, tstzrange('2026-03-02 10:05', NULL));
-- correction à 11:20 : le motif SCD2 impose UPDATE de la ligne ouverte (RÉÉCRITURE) puis INSERT
UPDATE w.scd2 SET known = tstzrange('2026-03-02 10:05','2026-03-02 11:20') WHERE instrument='X';
INSERT INTO w.scd2 VALUES ('X','2026-03-02 10:00', 101, tstzrange('2026-03-02 11:20', NULL));
-- backfill tardif : un adaptateur qui déclare known = [event_time, ...) chevauche v1 -> refusé par la contrainte
DO $$ BEGIN
  BEGIN INSERT INTO w.scd2 VALUES ('X','2026-03-02 10:00', 999, tstzrange('2026-03-02 10:00', NULL));
    RAISE NOTICE 'OVERLAP_ACCEPTED';
  EXCEPTION WHEN exclusion_violation OR unique_violation THEN RAISE NOTICE 'OVERLAP_REJECTED (%)', SQLSTATE; END;
END $$;
-- backfill sur un instrument neuf, known rétroactif = event_time : ACCEPTÉ, et contamine une requête à T=10:05 (fuite)
INSERT INTO w.scd2 VALUES ('Y','2026-03-02 10:00', 100, tstzrange('2026-03-02 10:00', NULL));  -- réellement arrivé à 20:00
SELECT 'LEAK_QUERY_T=10:05 sees Y' AS test, count(*) AS rows FROM w.scd2 WHERE instrument='Y' AND known @> '2026-03-02 10:05'::timestamptz;
-- (B) Table DÉRIVÉE de l'axe append-only : intervalles calculés par LEAD, contrainte WITHOUT OVERLAPS comme INVARIANT (jamais UPDATE)
CREATE TABLE w.obs (obs_id bigint generated always as identity primary key, instrument text, event_time timestamptz, val int, ingested_at timestamptz);
INSERT INTO w.obs (instrument,event_time,val,ingested_at) VALUES
 ('X','2026-03-02 10:00',100,'2026-03-02 10:05'),('X','2026-03-02 10:00',101,'2026-03-02 11:20'),('Y','2026-03-02 10:00',100,'2026-03-02 20:00');
CREATE TABLE w.derived AS SELECT instrument,event_time,val,
  tstzrange(ingested_at, LEAD(ingested_at) OVER (PARTITION BY instrument,event_time ORDER BY ingested_at, obs_id)) AS known FROM w.obs;
ALTER TABLE w.derived ADD PRIMARY KEY (instrument,event_time, known WITHOUT OVERLAPS);
SELECT 'DERIVED_PK_OK' AS test, count(*) FROM w.derived;
SELECT 'DERIVED_LEAK_QUERY_T=10:05 sees Y' AS test, count(*) FROM w.derived WHERE instrument='Y' AND known @> '2026-03-02 10:05'::timestamptz;
-- même ingested_at pour 2 versions du même fait : intervalle vide -> l'invariant ne détecte PAS l'ambiguïté d'ordre
INSERT INTO w.obs (instrument,event_time,val,ingested_at) VALUES ('Z','2026-03-02 10:00',1,'2026-03-02 12:00'),('Z','2026-03-02 10:00',2,'2026-03-02 12:00');
SELECT 'TIE_EMPTY_RANGES' AS test, count(*) FILTER (WHERE isempty(known)) AS empty_ranges FROM (SELECT tstzrange(ingested_at, LEAD(ingested_at) OVER (PARTITION BY instrument,event_time ORDER BY ingested_at,obs_id)) known FROM w.obs WHERE instrument='Z') s;
