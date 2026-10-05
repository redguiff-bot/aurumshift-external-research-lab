-- laneBJKL — alternative « ledger d'expérience forward » minimal : 1 table append-only dans le Postgres existant,
-- artefacts en Parquet référencés par URI + sha256, chaîne de hash pour détecter une réécriture.
-- Usage : psql -v ON_ERROR_STOP=0 -f ledger_pg_minimal.sql (instance jetable laneBJKL)
CREATE SCHEMA IF NOT EXISTS xp;
CREATE EXTENSION IF NOT EXISTS pgcrypto;
DROP TABLE IF EXISTS xp.run_ledger;
CREATE TABLE xp.run_ledger (
  seq                    bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  experiment             text        NOT NULL,
  arm                    text        NOT NULL,
  decision_input_sha256  text        NOT NULL CHECK (decision_input_sha256 ~ '^[0-9a-f]{64}$'),
  params                 jsonb       NOT NULL,
  metrics                jsonb       NOT NULL,
  artifact_uri           text,
  artifact_sha256        text        CHECK (artifact_sha256 ~ '^[0-9a-f]{64}$'),
  code_ref               text        NOT NULL,           -- commit git du code d'expérience
  recorded_at            timestamptz NOT NULL DEFAULT clock_timestamp(),
  prev_hash              text,
  row_hash               text        NOT NULL
);
CREATE FUNCTION xp.ledger_chain() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  PERFORM pg_advisory_xact_lock(hashtext('xp.run_ledger'));
  SELECT row_hash INTO NEW.prev_hash FROM xp.run_ledger ORDER BY seq DESC LIMIT 1;
  NEW.recorded_at := clock_timestamp();
  NEW.row_hash := encode(digest(concat_ws('|', NEW.prev_hash, NEW.experiment, NEW.arm, NEW.decision_input_sha256,
                    NEW.params::text, NEW.metrics::text, NEW.artifact_uri, NEW.artifact_sha256, NEW.code_ref,
                    NEW.recorded_at::text), 'sha256'), 'hex');
  RETURN NEW;
END $$;
CREATE TRIGGER ledger_chain BEFORE INSERT ON xp.run_ledger FOR EACH ROW EXECUTE FUNCTION xp.ledger_chain();
CREATE FUNCTION xp.ledger_no_mutation() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN RAISE EXCEPTION 'xp.run_ledger is append-only (% refused)', TG_OP; END $$;
CREATE TRIGGER ledger_no_upd BEFORE UPDATE OR DELETE ON xp.run_ledger FOR EACH ROW EXECUTE FUNCTION xp.ledger_no_mutation();
CREATE TRIGGER ledger_no_trunc BEFORE TRUNCATE ON xp.run_ledger FOR EACH STATEMENT EXECUTE FUNCTION xp.ledger_no_mutation();

-- vérification de chaîne (recalcul) : 0 ligne = intègre
CREATE VIEW xp.ledger_chain_breaks AS
SELECT seq FROM (
  SELECT seq, row_hash, prev_hash, lag(row_hash) OVER (ORDER BY seq) AS expected_prev,
         encode(digest(concat_ws('|', prev_hash, experiment, arm, decision_input_sha256, params::text, metrics::text,
                artifact_uri, artifact_sha256, code_ref, recorded_at::text), 'sha256'), 'hex') AS recomputed
  FROM xp.run_ledger) s
WHERE recomputed <> row_hash OR prev_hash IS DISTINCT FROM expected_prev;

-- démonstration
INSERT INTO xp.run_ledger(experiment, arm, decision_input_sha256, params, metrics, artifact_uri, artifact_sha256, code_ref, row_hash)
SELECT 'quorum_shadow_v1', a, repeat('ab', 32), jsonb_build_object('quorum', q), jsonb_build_object('n_decisions', n),
       'file:///ledger/' || a || '.parquet', repeat('cd', 32), 'deadbeef', ''
FROM (VALUES ('A_quorum2', 2, 412), ('B_quorum1_shadow', 1, 877), ('C_single_family_shadow', NULL, 503)) v(a, q, n);
SELECT seq, arm, left(prev_hash, 12) AS prev, left(row_hash, 12) AS hash FROM xp.run_ledger ORDER BY seq;
UPDATE xp.run_ledger SET metrics = '{"n_decisions": 999}' WHERE arm = 'A_quorum2';   -- doit échouer
DELETE FROM xp.run_ledger WHERE arm = 'C_single_family_shadow';                       -- doit échouer
SELECT count(*) AS chain_breaks_before_tamper FROM xp.ledger_chain_breaks;
-- falsification par un superutilisateur qui désactive les triggers : détectée par la chaîne
ALTER TABLE xp.run_ledger DISABLE TRIGGER ledger_no_upd;
UPDATE xp.run_ledger SET metrics = '{"n_decisions": 999}' WHERE arm = 'A_quorum2';
ALTER TABLE xp.run_ledger ENABLE TRIGGER ledger_no_upd;
SELECT count(*) AS chain_breaks_after_tamper FROM xp.ledger_chain_breaks;
