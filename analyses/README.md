# Analyses approfondies lane par lane

Une analyse détaillée par lane, écrite à partir des rapports, scripts et résultats bruts livrés (branches `origin/claude/*`). Chaque fichier suit le même plan : identité, mission, méthode, résultats détaillés, candidats, bloc final expliqué, contrôles de validité, critique indépendante, comparaison des runs, reproductibilité, pistes pour AurumShift (à adjuger plus tard), questions ouvertes, index des fichiers lus.

Les chiffres cités viennent de fichiers lus par les analystes. Les écarts « rapport contre résultats bruts » sont détectés par recalcul quand c'était possible ; ce qui n'a pas pu être vérifié est dit dans chaque fichier. Le synthétique reste synthétique : aucun verdict ne prouve une compatibilité avec AurumShift. Vue d'ensemble et actions GitHub : `../SYNTHESE_LANES.md`.

| Lane | Fichier | Lignes | Verdict | Point clé |
|---|---|---|---|---|
| 001 | [LANE_001](LANE_001_adaptive_strategy_fleet.md) | 714 | aucun ADOPT système ; ADAPT partiels | La garde d'obsolescence est réglée sur les scénarios évalués, et sa métrique « obsolète » utilise la même constante de 200 tours |
| 002 | [LANE_002](LANE_002_agent_orchestration.md) | 680 | Absurd ADAPT, Procrastinate ADAPT (repli) | Doublons d'exécution après panne dans tous les runtimes : idempotence obligatoire |
| 003 | [LANE_003](LANE_003_cell_attention_heldout_v2.md) | 776 | ADAPTIVE_POLICY_SUPPORTED_FOR_LOCAL_EVALUATION | La politique A ≈ tourniquet ; B bat A 200/200, mais C2 fait mieux en information |
| 004 | [LANE_004](LANE_004_pit_safe_evidence_replay.md) | 729 | POSTGRES_NATIVE_PIT_PATTERN_SUPPORTED | Course de commit réelle ; horloge « inattaquable » non testée (`strict_clock=false`) |
| 005 | [LANE_005](LANE_005_data_feed_resilience.md) | 716 | MULTIPLE_DATA_SOURCE_CANDIDATES_SUPPORTED | 0 bougie identique entre plateformes ; licences non établies |
| 006 | [LANE_006](LANE_006_execution_cost_intelligence.md) | 985 | LIMITED_EXECUTION_MODELS_SUPPORTED | Le « biais quasi nul » de la marche du carnet vient d'un test de persistance peu probant |
| 008A | [LANE_008A](LANE_008A_capacity_study_A.md) | 695 | CAPACITY_ALLOCATION_REFERENCE_SUPPORTED (fragile) | Le verdict tient à la famille « spam » ; la décote de péremption est inerte |
| 008B | [LANE_008B](LANE_008B_capacity_study_B.md) | 748 | MULTIPLE_CAPACITY_METHODS_SUPPORTED | Gain construit en partie par le générateur ; à δ=0,5 le verdict devient « FIFO suffit » |
| 009 | [LANE_009](LANE_009_capacity_replication_adjudication.md) | 824 | CAPACITY_REPLICATION_INCONCLUSIVE (provisoire) | Sept conclusions à ré-adjuger depuis l'arrivée du held-out de A |
| 010 | [LANE_010](LANE_010_macro_vintage_event_data.md) | 665 | LIMITED_MACRO_PIT_SOURCES_SUPPORTED | Lookahead des valeurs révisées confirmé ; concordance des calendriers en partie circulaire |
| 011 | [LANE_011](LANE_011_alpha_primitives.md) | 715 | NO_ROBUST_ALPHA_PRIMITIVE_SUPPORTED (2 runs) | Les frais dominent ; les étiquettes des deux runs ne sont pas comparables |
| 012 | [LANE_012](LANE_012_uncertainty_calibration.md) | 1 365 | LIMITED_UNCERTAINTY_METHODS_SUPPORTED (2 runs) | Le rejet de Platt du run 2 vient sans doute d'un solveur maison bogué (vérifié sur 2 graines) |
| 013 | [LANE_013](LANE_013_online_learning.md) | 626 | LIMITED_ONLINE_METHODS_SUPPORTED (run 1) | Run 2 : tuning seul, sans held-out ni rapport |
| 014 | [LANE_014](LANE_014_strategy_ensemble.md) | 659 | INCONCLUSIVE (run 1) / NO_ROBUST (run 2) | Seule une méthode qui triche passe les portes du run 1 ; sans elle, mêmes verdicts |
| 015 | [LANE_015](LANE_015_feature_discovery.md) | 927 | LIMITED_STABLE (run 1) / NO_STABLE (run 2) | Sur la cible commune, les deux runs concluent la même chose ; la différence vient de la cible volatilité et des règles |
| 016 | [LANE_016](LANE_016_alternative_data.md) | 1 015 | INCONCLUSIVE (run 1) / LIMITED (run 2) | Les deux runs ne testent pas la même chose ; les 2 candidats du run 2 sont fragiles |
| 017 | [LANE_017](LANE_017_oss_trading_infra.md) | 930 | MULTIPLE_OSS_COMPONENTS_SUPPORTED (2 runs) | 13 verdicts divergent sur 45 projets communs ; la fuite de `ta` vient de `series.mean()` |

Lane « Regime changepoint » : aucun livrable poussé, donc pas d'analyse.

## Constats transversaux

1. **Runs indépendants :** quand deux runs divergent, la cause est presque toujours une définition (cible, seuil, règle de verdict, périmètre), pas un désaccord factuel (014, 015, 016). Compare les protocoles avant les étiquettes.
2. **Bord de grille :** de nombreux optima sont sur un bord de grille ou n'ont aucun effet mesurable (001, 003, 008A, 013). Un paramètre « choisi » y est parfois une égalité départagée arbitrairement.
3. **Verdicts fragiles :** plusieurs verdicts se retournent avec une marge un peu différente (008A/008B, 014). Un verdict mécanique n'est pas une preuve robuste.
4. **Vérification :** dans presque toutes les lanes, les tableaux produits par code sont exacts. Les écarts trouvés viennent du texte d'interprétation écrit à la main.
5. **Conflits de fichiers avant merge :** 008, 011, 012, 014, 015, 016, 017 ont deux PR qui écrivent dans les mêmes dossiers. La branche de 015-b embarque en plus 8 fichiers `.whl` (≈ 62,5 Mo), à retirer.
