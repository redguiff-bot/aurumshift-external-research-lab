"""Non-heldout diagnostics (split=validation, frozen params, fresh seeds)."""
import json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
import common as C, policies as P, world as W, engine as E

fz = json.load(open(f"{C.ROOT}/configs/frozen_params.json"))
OUT = os.path.join(C.ROOT, "results", "diagnostics")
POLS = list(fz)
R_SEEDS = range(6000, 6008); F_SEEDS = range(7000, 7010)

def cell(p, scen, sd, tag, K=4, ov=None, cm=1.0, bel="known", params=None, ing=None):
    return dict(scen=scen, seed=sd, split="validation", policy=p, params=fz[p]["params"] if params is None else params,
                ingest=ing or fz[p]["ingest_primary"], K=K, overrides=ov, cost_mult=cm, belief=bel, tag=tag)

if __name__ == "__main__":
    # D1 robustness OFAT on S3 (chronic saturation)
    ofat = {"load": [("load", v, {"load": v}) for v in (1.0, 2.0, 3.5, 6.0)],
            "score_noise": [("tau_mult", v, {"tau_mult": v}) for v in (0.0, 0.5, 1.0, 2.0, 4.0)],
            "duration_dist": [("cv/dist", n, o) for n, o in (("ln_cv0.3", {"cv": 0.3}), ("ln_cv0.6", {"cv": 0.6}), ("ln_cv1.2", {"cv": 1.2}), ("pareto", {"dist": "pareto"}))],
            "correlation": [("rho_g", v, {"rho_g": v}) for v in (0.1, 0.35, 0.6, 0.85)],
            "regime_persistence": [("regime_p", v, {"regime_p": v}) for v in (1 / 30, 1 / 100, 1 / 300, 1 / 3000)]}
    rows = []
    for fam, lst in ofat.items():
        for (k, v, ov) in lst:
            for p in POLS:
                for sd in R_SEEDS:
                    c = cell(p, "S3_chronic", sd, f"D1|{fam}|{v}", ov=ov); rows.append(c)
    for K in (3, 4, 6, 10):
        rows += [cell(p, "S3_chronic", sd, f"D1|slots|{K}", K=K) for p in POLS for sd in R_SEEDS]
    C.write_csv(C.run_many(rows), f"{OUT}/D1_robustness.csv"); print("D1", len(rows))
    # D2 score-quality ladder
    ladder = [("perfect_UB_only", {"tau_mult": 0.0}), ("calibrated_noisy", {}), ("noisy_x2", {"tau_mult": 2.0}),
              ("poor_calibration", {"cal": "poor"}), ("inverted", {"cal": "invert"}), ("missing50", {"p_miss": 0.5}), ("stale60", {"p_stale": 0.6})]
    rows = [cell(p, "S3_chronic", sd, f"D2|{n}", ov=ov) for n, ov in ladder for p in POLS for sd in R_SEEDS]
    C.write_csv(C.run_many(rows), f"{OUT}/D2_score_quality.csv"); print("D2", len(rows))
    # D3 cost uncertainty
    rows = [cell(p, sc, sd, f"D3|{cm}|{b}", cm=cm, bel=b) for sc in ("S3_chronic", "S6_short_vs_long") for cm in (0.5, 1.0, 2.0, 3.0)
            for b in ("known", "zero", "unknown_conservative") for p in POLS for sd in R_SEEDS]
    C.write_csv(C.run_many(rows), f"{OUT}/D3_cost.csv"); print("D3", len(rows))
    # D4 failure-mode battery
    scs = list(W.FAILURE_SCENARIOS) + ["S4_late_hq", "S10_spam", "S7_regime_shift", "S8_noisy_rank", "S3_chronic", "S6_short_vs_long"]
    rows = [cell(p, s, sd, "D4") for s in scs for p in POLS for sd in F_SEEDS]
    rows += [cell(p, "S10_spam", sd, f"D4i|{ing}", ing=ing) for ing in E.INGEST_MODES for p in POLS for sd in F_SEEDS]
    C.write_csv(C.run_many(rows), f"{OUT}/D4_failure_modes.csv"); print("D4", len(rows))
    # D5 full-grid parameter sensitivity at frozen ingest (all 13 scenarios)
    rows = []
    for p, grid in P.GRIDS.items():
        if len(grid) > 1:
            for prm in grid:
                rows += [cell(p, s, sd, "D5", params=prm, ing=fz[p]["ingest_primary"] if p != "OLDEST_SLOT" else "RAW")
                         for s in W.SCENARIOS for sd in R_SEEDS]
    C.write_csv(C.run_many(rows), f"{OUT}/D5_param_sensitivity.csv"); print("D5", len(rows))
