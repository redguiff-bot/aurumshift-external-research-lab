\timing off
\set ON_ERROR_STOP off
CREATE EXTENSION IF NOT EXISTS timescaledb;
CREATE EXTENSION IF NOT EXISTS pg_partman;
SELECT extname, extversion FROM pg_extension ORDER BY 1;
-- 1) same 3M-row tick table three ways: plain, native declarative partition (no extension), timescaledb hypertable
DROP SCHEMA IF EXISTS t CASCADE; CREATE SCHEMA t; SET search_path=t,public;
CREATE TABLE ticks_plain(ts timestamptz NOT NULL, sym int, px double precision, qty double precision);
INSERT INTO ticks_plain SELECT '2024-01-01'::timestamptz + (g * interval '1 second')*0.5, g % 20, 100 + (g % 1000)*0.01, 1 + g % 7 FROM generate_series(1,3000000) g;
CREATE INDEX ON ticks_plain(sym, ts);
CREATE TABLE ticks_native(LIKE ticks_plain) PARTITION BY RANGE (ts);
DO $$ DECLARE d date; BEGIN FOR d IN SELECT generate_series('2024-01-01'::date,'2024-01-20'::date,'1 day') LOOP
  EXECUTE format('CREATE TABLE ticks_native_%s PARTITION OF ticks_native FOR VALUES FROM (%L) TO (%L)', to_char(d,'YYYYMMDD'), d, d+1); END LOOP; END $$;
INSERT INTO ticks_native SELECT * FROM ticks_plain;
CREATE INDEX ON ticks_native(sym, ts);
CREATE TABLE ticks_hyper(LIKE ticks_plain);
SELECT create_hypertable('ticks_hyper','ts', chunk_time_interval => interval '1 day');
INSERT INTO ticks_hyper SELECT * FROM ticks_plain;
CREATE INDEX ON ticks_hyper(sym, ts);
ANALYZE ticks_plain; ANALYZE ticks_native; ANALYZE ticks_hyper;
SELECT 'rows' k, (SELECT count(*) FROM ticks_plain) plain, (SELECT count(*) FROM ticks_native) native, (SELECT count(*) FROM ticks_hyper) hyper;
SELECT 'size_MB_uncompressed' k, pg_total_relation_size('ticks_plain')/1e6 plain, (SELECT sum(pg_total_relation_size(c.oid)) FROM pg_class c JOIN pg_inherits i ON i.inhrelid=c.oid WHERE i.inhparent='ticks_native'::regclass)/1e6 native, hypertable_size('ticks_hyper')/1e6 hyper;
-- 2) query: 1-minute OHLC bars for one symbol / one day
\echo == 1-min OHLC one symbol one day: plain / native / hyper (EXPLAIN ANALYZE execution time)
EXPLAIN (ANALYZE, SUMMARY ON, TIMING OFF, COSTS OFF) SELECT date_trunc('minute',ts) b, (array_agg(px ORDER BY ts))[1] o, max(px) h, min(px) l, (array_agg(px ORDER BY ts DESC))[1] c, sum(qty) FROM ticks_plain WHERE sym=3 AND ts>='2024-01-05' AND ts<'2024-01-06' GROUP BY 1;
EXPLAIN (ANALYZE, SUMMARY ON, TIMING OFF, COSTS OFF) SELECT date_trunc('minute',ts) b, (array_agg(px ORDER BY ts))[1] o, max(px) h, min(px) l, (array_agg(px ORDER BY ts DESC))[1] c, sum(qty) FROM ticks_native WHERE sym=3 AND ts>='2024-01-05' AND ts<'2024-01-06' GROUP BY 1;
EXPLAIN (ANALYZE, SUMMARY ON, TIMING OFF, COSTS OFF) SELECT time_bucket('1 minute',ts) b, first(px,ts) o, max(px) h, min(px) l, last(px,ts) c, sum(qty) FROM ticks_hyper WHERE sym=3 AND ts>='2024-01-05' AND ts<'2024-01-06' GROUP BY 1;
-- equality of results across the three
SELECT 'bars_equal' k,
 (SELECT md5(string_agg(b::text||o||h||l||c, ',' ORDER BY b)) FROM (SELECT date_trunc('minute',ts) b, (array_agg(px ORDER BY ts))[1] o, max(px) h, min(px) l, (array_agg(px ORDER BY ts DESC))[1] c FROM ticks_native WHERE sym=3 AND ts>='2024-01-05' AND ts<'2024-01-06' GROUP BY 1) x) = 
 (SELECT md5(string_agg(b::text||o||h||l||c, ',' ORDER BY b)) FROM (SELECT time_bucket('1 minute',ts) b, first(px,ts) o, max(px) h, min(px) l, last(px,ts) c FROM ticks_hyper WHERE sym=3 AND ts>='2024-01-05' AND ts<'2024-01-06' GROUP BY 1) y) AS native_eq_hyper;
-- 3) timescale compression (columnar) - licence: Timescale License (TSL) feature
ALTER TABLE ticks_hyper SET (timescaledb.compress, timescaledb.compress_segmentby='sym', timescaledb.compress_orderby='ts');
SELECT count(compress_chunk(c)) compressed_chunks FROM show_chunks('ticks_hyper') c;
SELECT 'size_MB_compressed' k, hypertable_size('ticks_hyper')/1e6 hyper_after;
SELECT 'rows_after_compress' k, count(*) FROM ticks_hyper;
SHOW timescaledb.license;
-- 4) continuous aggregate (materialised 1-min bars) - TSL feature
CREATE MATERIALIZED VIEW bars1m WITH (timescaledb.continuous) AS SELECT time_bucket('1 minute',ts) b, sym, first(px,ts) o, max(px) h, min(px) l, last(px,ts) c, sum(qty) v FROM ticks_hyper GROUP BY 1,2 WITH NO DATA;
CALL refresh_continuous_aggregate('bars1m', NULL, NULL);
SELECT 'caggs' k, count(*) FROM bars1m;
-- 5) pg_partman: create + maintain
CREATE TABLE ev(ts timestamptz NOT NULL, id bigint, payload text) PARTITION BY RANGE (ts);

SELECT public.create_parent('t.ev','ts','1 day', p_premake := 4);
SELECT count(*) partman_children FROM pg_inherits WHERE inhparent='t.ev'::regclass;
