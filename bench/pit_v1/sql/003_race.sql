-- Sérialisation ordre-de-stamp == ordre-de-commit. Verrou exclusif (écrivains) / partagé (lecteurs de décision).
CREATE FUNCTION pit.ingest_locked(
  p_source text, p_instrument text, p_timeframe text, p_event_time timestamptz,
  p_provider_event_id text, p_revision integer, p_dataset_version text,
  p_finality pit.finality, p_finality_basis text,
  p_provenance pit.provenance, p_first_observed_at timestamptz, p_payload jsonb
) RETURNS bigint LANGUAGE plpgsql AS $$
BEGIN
  PERFORM pg_advisory_xact_lock(hashtext('pit.stamp_order'));   -- AVANT tout estampillage
  RETURN pit.ingest(p_source,p_instrument,p_timeframe,p_event_time,p_provider_event_id,p_revision,
                    p_dataset_version,p_finality,p_finality_basis,p_provenance,p_first_observed_at,p_payload,NULL);
END $$;
-- Cutoff de décision sûr : attend la fin des écritures en vol, puis fixe T. Doit être appelé dans la transaction de décision.
CREATE FUNCTION pit.decision_cutoff() RETURNS timestamptz LANGUAGE plpgsql AS $$
BEGIN
  PERFORM pg_advisory_xact_lock_shared(hashtext('pit.stamp_order'));
  RETURN clock_timestamp();
END $$;
