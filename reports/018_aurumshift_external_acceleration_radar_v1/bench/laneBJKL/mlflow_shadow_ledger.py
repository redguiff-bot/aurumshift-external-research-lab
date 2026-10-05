"""laneBJKL — MLflow 3.x comme « miroir » d'un shadow experiment (A quorum=2 / B quorum=1 / C single-family)
sur un DecisionInput gelé synthétique. Backend : argv[1] (sqlite:///... ou postgresql+psycopg://...).
Mesure : ce que MLflow stocke (tables, artefacts) = ce qui deviendrait un 2e magasin s'il n'était pas miroir.
Compare à l'alternative « ledger append-only Postgres + Parquet + sha256 » (voir ledger_pg_minimal.sql)."""
import hashlib, json, os, sys, tempfile, time
import numpy as np, mlflow
from mlflow.tracking import MlflowClient

uri = sys.argv[1]; art = sys.argv[2]
rng = np.random.default_rng(18)
# DecisionInput gelé (synthétique) : 1 000 candidats, familles de signaux votantes
di = rng.integers(0, 2, size=(1000, 3))
di_bytes = di.tobytes(); di_hash = hashlib.sha256(di_bytes).hexdigest()
mlflow.set_tracking_uri(uri)
t0 = time.perf_counter()
exp_id = mlflow.create_experiment("quorum_shadow_v1", artifact_location=art) \
    if mlflow.get_experiment_by_name("quorum_shadow_v1") is None else mlflow.get_experiment_by_name("quorum_shadow_v1").experiment_id
t_setup = time.perf_counter() - t0
out = {"mlflow": mlflow.__version__, "backend": uri.split(":")[0], "t_first_connect_and_migrate_s": round(t_setup, 2)}
runs = {}
t0 = time.perf_counter()
for arm, q in [("A_quorum2", 2), ("B_quorum1_shadow", 1), ("C_single_family_shadow", None)]:
    votes = di.sum(1) if q else di[:, 0]
    take = votes >= (q or 1)
    pnl = rng.normal(0.0002, 0.003, take.sum())  # placeholder : PAS une mesure économique
    with mlflow.start_run(experiment_id=exp_id, run_name=arm) as r:
        mlflow.log_params({"arm": arm, "quorum": q, "decision_input_sha256": di_hash, "cost_contract": "COST_CONTRACT_V1"})
        mlflow.set_tags({"authority": "MIRROR_READ_ONLY", "source_of_truth": "postgres:experiment_ledger"})
        mlflow.log_metrics({"n_decisions": int(take.sum()), "net_expectancy_placeholder": float(pnl.mean())})
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, f"{arm}_decisions.npy"); np.save(p, take)
            h = hashlib.sha256(open(p, "rb").read()).hexdigest()
            mlflow.log_artifact(p); mlflow.set_tag("artifact_sha256", h)
        runs[arm] = r.info.run_id
out["t_log_3_runs_s"] = round(time.perf_counter() - t0, 2)
c = MlflowClient()
r = c.get_run(runs["B_quorum1_shadow"])
out["params_roundtrip_ok"] = r.data.params["decision_input_sha256"] == di_hash
# mutabilité : MLflow permet-il de réécrire un métrique / tag / supprimer un run ? (=> pas append-only)
c.set_tag(runs["A_quorum2"], "artifact_sha256", "TAMPERED")
c.log_metric(runs["A_quorum2"], "net_expectancy_placeholder", 999.0)
out["tag_overwrite_allowed"] = c.get_run(runs["A_quorum2"]).data.tags["artifact_sha256"] == "TAMPERED"
out["metric_latest_after_relog"] = c.get_run(runs["A_quorum2"]).data.metrics["net_expectancy_placeholder"]
out["metric_history_len"] = len(c.get_metric_history(runs["A_quorum2"], "net_expectancy_placeholder"))
c.delete_run(runs["C_single_family_shadow"])
out["deleted_run_lifecycle"] = c.get_run(runs["C_single_family_shadow"]).info.lifecycle_stage
try:
    c.log_param(runs["B_quorum1_shadow"], "quorum", "2"); out["param_overwrite_allowed"] = True
except Exception as e:
    out["param_overwrite_allowed"] = False; out["param_overwrite_error"] = type(e).__name__
print(json.dumps(out, indent=1))
