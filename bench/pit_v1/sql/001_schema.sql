-- Modèle de référence PostgreSQL pur — evidence append-only, deux axes de connaissance.
-- Aucune dépendance d'extension. Testé PostgreSQL 18.6.
DROP SCHEMA IF EXISTS pit CASCADE;
CREATE SCHEMA pit;

CREATE TYPE pit.finality AS ENUM ('PRELIMINARY','FINAL','CORRECTED','UNKNOWN');
CREATE TYPE pit.provenance AS ENUM ('LIVE','BACKFILL','UNKNOWN');

-- Configuration (1 ligne). strict_clock=true : ingested_at est TOUJOURS l'horloge DB (non falsifiable
-- par l'appelant). false : n'existe que pour simuler des scénarios rejoués (tests).
CREATE TABLE pit.config (
  singleton      boolean PRIMARY KEY DEFAULT true CHECK (singleton),
  strict_clock   boolean NOT NULL DEFAULT true,
  max_lag        interval NOT NULL DEFAULT '60 seconds'  -- borne de confiance sur l'horloge collecteur
);
INSERT INTO pit.config DEFAULT VALUES;

-- Une ligne = un CONTENU distinct (version d'un fait). Identité de contenu = hash.
CREATE TABLE pit.obs (
  obs_id              bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  -- identité du fait
  source              text        NOT NULL,           -- fournisseur
  instrument          text        NOT NULL,
  timeframe           text        NOT NULL,
  event_time          timestamptz NOT NULL,           -- quand le fait s'est produit (axe "valid time")
  -- identité du message
  provider_event_id   text        NOT NULL,           -- id message fournisseur (synthétisé par l'adaptateur sinon)
  revision            integer,                        -- révision déclarée par le fournisseur (NULL = non révisionné)
  content_hash        text        NOT NULL,           -- md5(instrument|timeframe|event_time|finality|payload)
  -- version / provenance
  dataset_version     text        NOT NULL,           -- lot d'import de la PREMIÈRE réception
  finality_status     pit.finality NOT NULL DEFAULT 'UNKNOWN',
  finality_basis      text        NOT NULL DEFAULT 'NONE',  -- PROVIDER_FLAG | ADAPTER_RULE | NONE
  provenance          pit.provenance NOT NULL,
  -- axes de connaissance
  first_observed_at   timestamptz,                    -- horloge COLLECTEUR à la première réception (peut être NULL/fausse)
  ingested_at         timestamptz NOT NULL,           -- horloge DB à l'insertion (axe STRICT)
  known_collector_at  timestamptz NOT NULL,           -- axe COLLECTEUR validé (jamais < first_observed_at valide, sinon = ingested_at)
  known_basis         text        NOT NULL,           -- COLLECTOR_CLOCK | DB_CLOCK_* (pourquoi cet axe)
  payload             jsonb       NOT NULL,
  CHECK (known_collector_at <= ingested_at)
);
-- Dédoublonnage par contenu : un même message re-livré n'ajoute aucune ligne.
CREATE UNIQUE INDEX obs_identity ON pit.obs (source, provider_event_id, revision, content_hash) NULLS NOT DISTINCT;
-- Index PIT (lecture "dernière version connue à T" par fait, et as-of par event_time)
CREATE INDEX obs_pit_ing ON pit.obs (source, instrument, timeframe, event_time DESC, revision DESC NULLS LAST, ingested_at DESC, obs_id DESC);
CREATE INDEX obs_pit_col ON pit.obs (source, instrument, timeframe, event_time DESC, revision DESC NULLS LAST, known_collector_at DESC, obs_id DESC);

-- Journal de TOUTES les réceptions (doublons, ré-imports) : préserve la lignée sans polluer PIT.
CREATE TABLE pit.obs_receipt (
  receipt_id          bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  obs_id              bigint NOT NULL REFERENCES pit.obs(obs_id),
  dataset_version     text   NOT NULL,
  provenance          pit.provenance NOT NULL,
  first_observed_at   timestamptz,
  ingested_at         timestamptz NOT NULL,
  is_first            boolean NOT NULL
);
CREATE INDEX obs_receipt_obs ON pit.obs_receipt (obs_id);

-- Append-only mécanique (contournable par le propriétaire de la table / superuser : voir 11_LIMITATIONS)
CREATE FUNCTION pit.deny_mutation() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN RAISE EXCEPTION 'pit: table % is append-only (% refused)', TG_TABLE_NAME, TG_OP USING ERRCODE = 'restrict_violation'; END $$;
CREATE TRIGGER obs_ro_row  BEFORE UPDATE OR DELETE ON pit.obs         FOR EACH ROW       EXECUTE FUNCTION pit.deny_mutation();
CREATE TRIGGER obs_ro_stmt BEFORE TRUNCATE          ON pit.obs         FOR EACH STATEMENT EXECUTE FUNCTION pit.deny_mutation();
CREATE TRIGGER rcp_ro_row  BEFORE UPDATE OR DELETE ON pit.obs_receipt FOR EACH ROW       EXECUTE FUNCTION pit.deny_mutation();
CREATE TRIGGER rcp_ro_stmt BEFORE TRUNCATE          ON pit.obs_receipt FOR EACH STATEMENT EXECUTE FUNCTION pit.deny_mutation();
