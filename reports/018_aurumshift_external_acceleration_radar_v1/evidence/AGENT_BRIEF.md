# Brief commun aux sous-recherches — AURUMSHIFT_EXTERNAL_ACCELERATION_RADAR_V1

Date de recherche : 2026-10-05 (horloge sandbox). Laboratoire externe : aucun code AurumShift n'est lu ni modifié ;
aucune base, credential, compte broker ou chemin d'exécution AurumShift n'est touché.

## Contexte AurumShift (fourni par l'opérateur, non vérifiable ici)
Cœur d'autorité étroit et stable : identité PIT/données, identité/lignée économique, DecisionV1, exécution PAPER,
positions, OutcomeV1, comptabilité économique, contrat RetexV1, risque/sécurité, runtime événementiel, autorité
d'observabilité. Les composants externes entrent comme MODULE / CHALLENGER / ORACLE / ADAPTER / SHADOW et ne doivent
JAMAIS devenir une seconde autorité marché/économique/exécution.

Chemin critique actuel :
- C0_V2 : canari d'observation file-only 22 bases × 6 surfaces (bars, BBO, depth, funding, OI, basis…) sur Binance/OKX/Bybit.
- PAPER BTC-USDT et DOGE-USDT, BUY-only. Besoin du premier Outcome économique forward complet :
  observation PIT → DecisionV1 → scope → risk → PAPER → order/fill → position → close → OutcomeV1 → coûts réalistes → RetexV1.
- Hypothèse causale : le quorum de familles (quorum=2) supprime des décisions économiquement utiles.
  Expérience : A quorum=2 / B quorum=1 shadow / C single-family shadow, sur le MÊME DecisionInput gelé.
  Endpoint : espérance NETTE incrémentale des candidats QUORUM_ONLY_SUPPRESSED (vs QUORUM_PLUS_OTHER_GATE).
- UNKNOWN_COST != ZERO_COST. COST_CONTRACT_V1 existe ; on cherche des ORACLES indépendants.
- L'expansion d'univers C0 reste observation-only.

## Études antérieures du labo (ne pas refaire, s'appuyer dessus, citer comme « LAB_PRIOR <n°> »)
Résumés extraits dans /tmp/claude-0/-home-user-aurumshift-external-research-lab/c664940f-5e12-5cd3-8b6d-631b3aa170bf/scratchpad/prior/reports/
(004 PIT Postgres natif ; 005 sources de données ; 006 coûts d'exécution ; 010 macro vintages/calendrier ; 011 primitives alpha ;
012 calibration ; 013 online learning ; 014 ensembles ; 015 feature discovery ; 016 données alternatives ; 017 infra OSS trading).
Lis le 00_* de celles pertinentes pour ta lane avant de chercher. Ton apport doit être NOUVEAU (versions actuelles,
candidats non couverts, commercial, preuves mesurées) et ORIENTÉ vers le chemin critique ci-dessus.

## Règles de preuve
- Sources primaires d'abord : docs officielles, dépôts GitHub (code, releases, issues), PyPI/crates, papiers arXiv/journaux,
  pages de prix/licence officielles. Pas d'articles SEO / listes « best libraries » comme preuve.
- Étiquettes obligatoires sur chaque affirmation matérielle : VERIFIED_FACT (lu dans source primaire, URL citée),
  MEASURED_BY_THIS_MISSION (exécuté par toi ici), UPSTREAM_BENCHMARK, PAPER_RESULT, VENDOR_CLAIM, INFERENCE, UNKNOWN.
- Ne jamais inventer de prix : UNKNOWN_PRICE si non publié. Bandes : TIER_A ≤100 €/mois, B 100–500, C 500–2000,
  D 2000–10000, E >10000/devis.
- Ne pas fabriquer de chiffres. Score qualitatif si preuve insuffisante.
- Entonnoir d'exécution : L0 sources/docs/licence/release → L1 import/build/smoke → L2 micro-bench fonctionnel →
  L3 bench différentiel « forme AurumShift ». Ne pas passer plus de ~15 min à faire marcher un candidat cassé (noter l'échec).
- Installer dans un venv isolé sous le scratchpad : /tmp/claude-0/-home-user-aurumshift-external-research-lab/c664940f-5e12-5cd3-8b6d-631b3aa170bf/scratchpad/venvs/<lane>
  (`uv venv` puis `uv pip install`). Python 3.11 dispo ; Rust, Java, Node, Docker, PostgreSQL 16 (binaires) dispo.
- Egress : Binance API principale = 451, Bybit = 403 (blocage egress, pas verdict fournisseur). OKX, data.binance.vision,
  datasets.tardis.dev (échantillons gratuits du 1er jour de chaque mois), Polymarket, Kalshi, ForexFactory JSON OK.
- Respecter les CGU des API publiques ; volumes modestes.

## Livrables de chaque sous-recherche
1. `evidence/raw_<lane>.md` (dans reports/018_aurumshift_external_acceleration_radar_v1/) : notes de travail en français,
   une fiche par candidat sérieux, URLs primaires, étiquettes, niveau d'exécution atteint, commandes exécutées et sorties clés.
2. `evidence/candidates_<lane>.csv` : une ligne par candidat (même rejetés), en-tête EXACT :
   `candidate_id,name,lane,role,gap_addressed,language,license,deployment_model,last_meaningful_release,maturity,bus_factor,price_tier,price_note,eval_level,FUNCTIONAL_FIT,SCIENTIFIC_FIT,ECONOMIC_VALUE,PIT_COMPATIBILITY,DETERMINISM,ACCURACY_OR_CALIBRATION,LATENCY,THROUGHPUT,CPU_RAM_IO,MAINTENANCE,SECURITY,API_STABILITY,INTEGRATION_COST,CUSTOM_CODE_REMOVED,SECOND_AUTHORITY_RISK,EXIT_COST,LICENSE_LEGAL_USE,TOTAL_COST,TIME_TO_OPERATIONAL_TRUTH,classification,known_failure_modes,primary_sources`
   Convention : TOUS les scores 0–5 avec 5 = favorable à AurumShift (donc INTEGRATION_COST 5 = intégration bon marché,
   SECOND_AUTHORITY_RISK 5 = risque négligeable, EXIT_COST 5 = sortie facile, TOTAL_COST 5 = peu coûteux).
   `?` si inconnu. classification ∈ ADOPT_NOW, BENCH_NOW, SHADOW, WATCH, PARK, REJECT. Champs texte entre guillemets
   doubles, séparer plusieurs URLs par ` | `.
3. Code/résultats de bench éventuels : `bench/<lane>/` (scripts reproductibles, résultats JSON/CSV, pas de gros binaires :
   < 5 Mo par fichier, pas de venv ni de données brutes volumineuses — mettre un script de téléchargement à la place).
4. Message final (retourné à l'orchestrateur) : ≤ 1 200 mots, en français : top candidats avec classification, preuves
   mesurées clés, red-team en une ligne chacun, et ce qui reste UNKNOWN.

Ne PAS faire de git add/commit/push : l'orchestrateur s'en charge.
