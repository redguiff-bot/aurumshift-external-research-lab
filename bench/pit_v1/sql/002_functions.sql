-- Ingestion : calcule les axes de connaissance, dédoublonne par contenu, journalise chaque réception.
CREATE FUNCTION pit.ingest(
  p_source text, p_instrument text, p_timeframe text, p_event_time timestamptz,
  p_provider_event_id text, p_revision integer, p_dataset_version text,
  p_finality pit.finality, p_finality_basis text,
  p_provenance pit.provenance, p_first_observed_at timestamptz,
  p_payload jsonb, p_ingested_at timestamptz DEFAULT NULL
) RETURNS bigint LANGUAGE plpgsql AS $$
DECLARE
  cfg pit.config%ROWTYPE; v_ing timestamptz; v_known timestamptz; v_basis text; v_hash text; v_id bigint; v_new boolean := true;
BEGIN
  SELECT * INTO cfg FROM pit.config;
  v_ing := CASE WHEN cfg.strict_clock THEN clock_timestamp() ELSE COALESCE(p_ingested_at, clock_timestamp()) END;
  -- axe COLLECTEUR : l'horloge collecteur n'est crue que si LIVE, présente, non future, et dans max_lag
  IF p_provenance = 'LIVE' AND p_first_observed_at IS NOT NULL
     AND p_first_observed_at <= v_ing AND v_ing - p_first_observed_at <= cfg.max_lag THEN
       v_known := p_first_observed_at; v_basis := 'COLLECTOR_CLOCK';
  ELSE
       v_known := v_ing;
       v_basis := CASE
         WHEN p_provenance = 'BACKFILL'          THEN 'DB_CLOCK_BACKFILL'
         WHEN p_provenance = 'UNKNOWN'           THEN 'DB_CLOCK_UNVERIFIED_PROVENANCE'
         WHEN p_first_observed_at IS NULL        THEN 'DB_CLOCK_NO_FIRST_OBSERVED'
         WHEN p_first_observed_at > v_ing        THEN 'DB_CLOCK_SKEW_CAP'
         ELSE                                         'DB_CLOCK_LAG_CAP' END;
  END IF;
  v_hash := md5(concat_ws('|', p_instrument, p_timeframe, p_event_time::text, p_finality::text, p_payload::text));
  INSERT INTO pit.obs (source, instrument, timeframe, event_time, provider_event_id, revision, content_hash,
                       dataset_version, finality_status, finality_basis, provenance, first_observed_at,
                       ingested_at, known_collector_at, known_basis, payload)
  VALUES (p_source, p_instrument, p_timeframe, p_event_time, p_provider_event_id, p_revision, v_hash,
          p_dataset_version, p_finality, p_finality_basis, p_provenance, p_first_observed_at,
          v_ing, v_known, v_basis, p_payload)
  ON CONFLICT (source, provider_event_id, revision, content_hash) DO NOTHING
  RETURNING obs_id INTO v_id;
  IF v_id IS NULL THEN
    v_new := false;
    SELECT obs_id INTO v_id FROM pit.obs
     WHERE source = p_source AND provider_event_id = p_provider_event_id
       AND revision IS NOT DISTINCT FROM p_revision AND content_hash = v_hash;
  END IF;
  INSERT INTO pit.obs_receipt (obs_id, dataset_version, provenance, first_observed_at, ingested_at, is_first)
  VALUES (v_id, p_dataset_version, p_provenance, p_first_observed_at, v_ing, v_new);
  RETURN v_id;
END $$;

-- REQUÊTE PIT DE RÉFÉRENCE (axe STRICT = ingested_at). "Dernière version de chaque fait connue à T."
-- Sélectionne D'ABORD la dernière version connue, filtre finalité ENSUITE (jamais l'inverse).
CREATE FUNCTION pit.asof(p_T timestamptz, p_instrument text DEFAULT NULL, p_timeframe text DEFAULT NULL)
RETURNS SETOF pit.obs LANGUAGE sql STABLE AS $$
  SELECT DISTINCT ON (source, instrument, timeframe, event_time) o.*
    FROM pit.obs o
   WHERE o.ingested_at <= p_T
     AND (p_instrument IS NULL OR o.instrument = p_instrument)
     AND (p_timeframe  IS NULL OR o.timeframe  = p_timeframe)
   ORDER BY source, instrument, timeframe, event_time, revision DESC NULLS LAST, ingested_at DESC, obs_id DESC
$$;

-- Variante axe COLLECTEUR (known_collector_at)
CREATE FUNCTION pit.asof_collector(p_T timestamptz, p_instrument text DEFAULT NULL, p_timeframe text DEFAULT NULL)
RETURNS SETOF pit.obs LANGUAGE sql STABLE AS $$
  SELECT DISTINCT ON (source, instrument, timeframe, event_time) o.*
    FROM pit.obs o
   WHERE o.known_collector_at <= p_T
     AND (p_instrument IS NULL OR o.instrument = p_instrument)
     AND (p_timeframe  IS NULL OR o.timeframe  = p_timeframe)
   ORDER BY source, instrument, timeframe, event_time, revision DESC NULLS LAST, known_collector_at DESC, obs_id DESC
$$;

-- Politique de finalité (post-sélection) : ALL | FINAL_ONLY (dernière version connue doit être FINAL/CORRECTED)
CREATE FUNCTION pit.asof_final(p_T timestamptz, p_instrument text DEFAULT NULL, p_timeframe text DEFAULT NULL)
RETURNS SETOF pit.obs LANGUAGE sql STABLE AS $$
  SELECT * FROM pit.asof(p_T, p_instrument, p_timeframe) WHERE finality_status IN ('FINAL','CORRECTED')
$$;

-- Jointure as-of décision -> dernier fait connu à T (par source), version correcte (LATERAL + LIMIT 1)
CREATE FUNCTION pit.latest_known(p_T timestamptz, p_source text, p_instrument text, p_timeframe text)
RETURNS SETOF pit.obs LANGUAGE sql STABLE AS $$
  SELECT o.* FROM pit.obs o
   WHERE o.source = p_source AND o.instrument = p_instrument AND o.timeframe = p_timeframe
     AND o.ingested_at <= p_T AND o.event_time <= p_T
   ORDER BY o.event_time DESC, o.revision DESC NULLS LAST, o.ingested_at DESC, o.obs_id DESC
   LIMIT 1
$$;

-- Diagnostic PAR CRÉNEAU (AUDIT SEULEMENT : révèle l'existence future ; ne jamais exposer à la décision).
-- Statuts : AVAILABLE | PRELIMINARY_ONLY | NOT_YET_KNOWN_AT_T | NEVER_OBSERVED | STALE
CREATE FUNCTION pit.slots(p_T timestamptz, p_source text, p_instrument text, p_timeframe text,
                          p_from timestamptz, p_to timestamptz, p_step interval)
RETURNS TABLE(slot timestamptz, status text, obs_id bigint) LANGUAGE sql STABLE AS $$
  WITH grid AS (SELECT g AS slot FROM generate_series(p_from, p_to, p_step) g),
  known AS (SELECT DISTINCT ON (event_time) * FROM pit.obs
             WHERE source=p_source AND instrument=p_instrument AND timeframe=p_timeframe AND ingested_at <= p_T
             ORDER BY event_time, revision DESC NULLS LAST, ingested_at DESC, obs_id DESC),
  anyv AS (SELECT DISTINCT event_time FROM pit.obs WHERE source=p_source AND instrument=p_instrument AND timeframe=p_timeframe)
  SELECT g.slot,
         CASE WHEN k.obs_id IS NOT NULL AND k.finality_status IN ('FINAL','CORRECTED') THEN 'AVAILABLE'
              WHEN k.obs_id IS NOT NULL THEN 'PRELIMINARY_ONLY'
              WHEN a.event_time IS NOT NULL THEN 'NOT_YET_KNOWN_AT_T'
              ELSE 'NEVER_OBSERVED' END,
         k.obs_id
    FROM grid g LEFT JOIN known k ON k.event_time = g.slot LEFT JOIN anyv a ON a.event_time = g.slot
$$;

-- Garde de rejeu FAIL-CLOSED : lève PIT_PROVENANCE_INCOMPLETE si le contexte n'est pas intégralement AVAILABLE
-- ou si des lignes de provenance non vérifiée existent dans la fenêtre.
CREATE FUNCTION pit.assert_replayable(p_T timestamptz, p_source text, p_instrument text, p_timeframe text,
                                      p_from timestamptz, p_to timestamptz, p_step interval,
                                      p_max_stale interval DEFAULT NULL) RETURNS void LANGUAGE plpgsql STABLE AS $$
DECLARE bad int; unv int; stale boolean := false; last_ev timestamptz;
BEGIN
  SELECT count(*) INTO bad FROM pit.slots(p_T,p_source,p_instrument,p_timeframe,p_from,p_to,p_step) WHERE status <> 'AVAILABLE';
  SELECT count(*) INTO unv FROM pit.obs WHERE source=p_source AND instrument=p_instrument AND timeframe=p_timeframe
     AND event_time BETWEEN p_from AND p_to AND known_basis IN ('DB_CLOCK_UNVERIFIED_PROVENANCE','DB_CLOCK_NO_FIRST_OBSERVED');
  IF p_max_stale IS NOT NULL THEN
    SELECT max(event_time) INTO last_ev FROM pit.obs WHERE source=p_source AND instrument=p_instrument
       AND timeframe=p_timeframe AND ingested_at <= p_T AND event_time <= p_T;
    stale := last_ev IS NULL OR p_T - last_ev > p_max_stale;
  END IF;
  IF bad > 0 OR unv > 0 OR stale THEN
    RAISE EXCEPTION 'PIT_PROVENANCE_INCOMPLETE: non_available_slots=%, unverified_provenance_rows=%, stale=%', bad, unv, stale
      USING ERRCODE = 'data_exception';
  END IF;
END $$;

-- Restatements silencieux : même message (source, provider_event_id, revision) avec contenus différents.
CREATE VIEW pit.silent_restatements AS
  SELECT source, provider_event_id, revision, count(*) AS n_contents, min(ingested_at) AS first_seen, max(ingested_at) AS last_seen
    FROM pit.obs GROUP BY 1,2,3 HAVING count(*) > 1;

-- Désaccords inter-fournisseurs (même fait, ≥2 sources, dernière version par source à T=now)
CREATE VIEW pit.provider_disagreement AS
  SELECT instrument, timeframe, event_time, count(DISTINCT payload) AS n_distinct_payloads, array_agg(DISTINCT source) AS sources
    FROM (SELECT DISTINCT ON (source,instrument,timeframe,event_time) * FROM pit.obs
           ORDER BY source,instrument,timeframe,event_time, revision DESC NULLS LAST, ingested_at DESC, obs_id DESC) latest
   GROUP BY 1,2,3 HAVING count(DISTINCT source) > 1 AND count(DISTINCT payload) > 1;
