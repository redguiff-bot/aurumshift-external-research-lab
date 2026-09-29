# Lane 011 — Primitives d'alpha : analyse approfondie de deux runs indépendants

Analyse rédigée pour Jean-François. Chaque terme technique est expliqué à sa première occurrence. Convention de lecture : ce que **le rapport affirme** est distingué de ce que **j'ai vérifié** moi-même en relisant les fichiers de résultats (marques ✔ vérifié / ✘ écart / ? non vérifiable). Les chemins entre parenthèses désignent le fichier d'où vient le chiffre. « R1 » = run 1 (branche `claude/alpha-primitives-v1`, PR #12). « R2 » = run 2 (branche `claude/amazing-pasteur-o4csin`, PR #22). Les extractions de travail ont été faites dans un dossier temporaire, sans checkout ni modification d'aucune branche.

Deux lexiques utiles d'entrée :
- **Primitive d'alpha** : un « signal élémentaire » (par ex. « le prix a monté sur 72 h, donc je parie qu'il continue ») dont on teste s'il prédit les rendements futurs. Ce n'est pas une stratégie complète.
- **Alpha** : rendement qui ne s'explique pas par le simple fait d'être exposé au marché crypto (le « bêta »).
- **Sharpe** : rendement moyen annualisé divisé par sa volatilité annualisée. Autour de 0 = rien ; 1 = bon ; > 2 = exceptionnel. Sur 3-4 ans de données, l'incertitude sur un Sharpe est d'environ ±0,5 à ±1 : un Sharpe de 0,5 ne se distingue pas du hasard.
- **Brut / net** : brut = gain de prix avant frais ; net = après frais de trading (et financement).
- **Perp / perpétuel** : contrat à terme crypto sans échéance ; les positions longues et courtes se versent un **funding** (taux de financement) périodique (toutes les 8 h sur Binance).
- **Turnover** : volume échangé rapporté à la taille du portefeuille. Un turnover élevé multiplie les frais.

---

## 0. Fiche d'identité

| | Run 1 | Run 2 |
|---|---|---|
| Branche | `origin/claude/alpha-primitives-v1` | `origin/claude/amazing-pasteur-o4csin` |
| PR | #12 (brouillon, ouverte, non fusionnée) « Report 011 … NO_ROBUST_ALPHA_PRIMITIVE_SUPPORTED » (créée 2026-09-29 18:04 UTC) | #22 (brouillon, ouverte, non fusionnée) « … independent run … » (créée 2026-09-29 19:01 UTC) |
| Commits | 2 : `8738106` (17:51 UTC, « pipeline code, primitive contracts and adjudication rules (pre-declared, before full results) ») et `2af33e4` (18:04 UTC, résultats + rapports) | 1 : `0eb39d7` (19:01 UTC) |
| Base | `main` = `1a449df` (merge PR #6) | idem |
| Fichiers (dossiers de la lane) | 70 fichiers, ≈ 24,6 Mo (dont `pnl_primary.parquet` 21,9 Mo) ; +12 547 lignes | 39 fichiers, ≈ 1,8 Mo (dont `vision_manifest.json` 1,2 Mo) ; +16 682 lignes |
| Univers | 10 perpétuels Binance USD-M (BTC ETH SOL XRP BNB DOGE ADA LINK AVAX LTC), barres 1 h | idem (mêmes 10) |
| Période | 2023-01 → 2026-08 (DEV 2023-24 / TEST 2025-26) ; 2022-Q4 = échauffement | 2024-03-01 → 2026-08-31 = 914 jours (DEV 2024-03→2025-05 / HOLDOUT 2025-06→2026-08) |
| Primitives découvertes / exécutées | 34 / 15 | 43 / 15 |
| Verdict final | `NO_ROBUST_ALPHA_PRIMITIVE_SUPPORTED` | `NO_ROBUST_ALPHA_PRIMITIVE_SUPPORTED` |
| Force du verdict | **Forte pour la partie « les frais mangent tout »** (t-stats nets jusqu'à −31) ; **faible/limitée pour « aucun alpha n'existe »** : puissance statistique insuffisante (un vrai Sharpe net < ≈ 1 est indétectable) | Idem ; bande de bootstrap 90 % du Sharpe net HOLDOUT ≈ ±1,5 |

Les deux PR se disent explicitement en collision (la PR #22 le signale : « Branch collision — needs a human decision », une seule des deux doit être fusionnée car elles écrivent dans les mêmes chemins). Ce sont deux réplications de la même mission, avec des choix de conception différents.

Bloc final R1 et R2 : voir section 5.

---

## 1. Mission et question posée

**Question reformulée simplement** : « Existe-t-il, dans la littérature et les données publiques gratuites, de petits signaux de marché (tendance, retour à la moyenne, funding, open interest, saisonnalité horaire, etc.) qui prédisent les rendements crypto et qui *restent rentables une fois les frais payés*, sans regarder le futur ? » Mission nommée `AURUMSHIFT_EXTERNAL_ALPHA_PRIMITIVE_DISCOVERY_V1`, mode `EXTERNAL_RESEARCH_ONLY`.

**Contraintes du dépôt** (`claude.md`) :
- Priorité **REUSE → ADAPT → WRAP → COMPOSE → CUSTOM en dernier** (réutiliser avant d'adapter, encapsuler, composer, et ne coder sur mesure qu'en dernier recours).
- Labels de preuve : **PROVEN** (démontré), **OBSERVED** (mesuré), **DOCUMENTED_CLAIM** (affirmé par une source, non reproduit), **INFERENCE**, **UNKNOWN**.
- Le dépôt ne contient aucun code privé AurumShift et ne doit pas prétendre connaître l'implémentation actuelle.
- Contraintes AurumShift : recherche/papier seulement, pas de capital réel, PIT (*point-in-time* : n'utiliser que ce qui était connu à l'instant) / provenance / pas de regard sur le futur (*lookahead*) critiques, intraday plutôt que haute fréquence, « l'absence de preuve n'est pas une preuve d'absence », coûts de marché réalistes.
- Les deux runs ont respecté le cadre : labels DOCUMENTED_CLAIM pour toute la littérature (lue via extraits/abstracts), `LOCAL_INTEGRATION_AUTHORIZED=FALSE`, `ANY_DROP_IN_STRATEGY=FALSE`.

---

## 2. Méthode

### 2.1 Run 1

- **Données** (`04_PUBLIC_DATA.md`) : Binance Vision (archives publiques en vrac : klines 1 h perp, indice de prime, historique de funding, métriques 5 min d'open interest), Deribit DVOL (indice de volatilité implicite BTC/ETH), Hyperliquid (funding horaire, depuis 2023-06), Coinbase spot (test « mauvais lieu », 2024-12 →). OKX/Kraken/Gate : seulement sondés pour accessibilité le 2026-09-29, **non utilisés**. L'API REST principale de Binance est géo-bloquée depuis l'environnement (HTTP 451) ; seules les archives fonctionnent. Aucune clé, aucune donnée privée. Données brutes (~400 Mo) **git-ignorées** (`bench/alpha_primitives_v1/.gitignore` : `data/`, `__pycache__/`, `results/pnl_primary.parquet`).
- **Simulateur** (`py/lib.py`) : barres horaires étiquetées à l'ouverture ; décision à la clôture ; exécution à l'ouverture suivante (délai 0). Portefeuille en **tranches chevauchantes** : 1/H du livre est reformé chaque heure et conservé H heures (H = 4 ou 24). Mode **TS** (*time-series* : chaque actif dimensionné seul, poids = clip(signal/écart-type glissant 720 h, ±1)/N, exposition brute ≤ 1) ou **CS** (*cross-sectional* : neutre en dollars, on achète les « meilleurs » actifs et vend les « pires », exposition brute 1, ≥ 60 % de l'univers valide).
- **Coûts** (par côté, en points de base ; 1 bp = 0,01 %) : BTC/ETH 6, autres 8, actifs hold-out 10 (≈ 5 taker + 1/3/5 de demi-spread/glissement). Multiplicateurs de stress ×2/×3/×5 ; ×0,5 seulement comme borne optimiste. Le funding réel est débité/crédité selon le signe de la position. « Coût inconnu ≠ coût nul ».
- **Splits** : DEV 2023-01→2024-12, TEST 2025-01→2026-08. Aucun paramètre ajusté sur l'un ou l'autre (aucune optimisation) ; le *design* a été fait avec connaissance de la littérature.
- **Pré-enregistrement** : contrats des 15 primitives (signe, mode, horizon primaire, paramètres) et règles d'adjudication **commités avant les résultats complets** (commit `8738106` à 17:51 puis résultats à 18:04). **Réserve importante** : un test rapide sur 3 actifs (BTC/ETH/SOL) a été *lu* avant la version complète ; aucune définition n'a changé ensuite (seules des corrections de traitement de données, `min_periods`, OI=0→manquant, réindexation), mais les sorties du test rapide sont dans le commit et ont été écrasées ensuite (`11_LIMITATIONS.md` §2).
- **Statistique** : Sharpe annualisé sur P&L horaire (√8760) ; t de **Newey-West** (correction d'autocorrélation) avec lags = max(2H,24). Adjudication sur les seules **15 spécifications primaires** (mode+horizon pré-déclarés) ; **Benjamini-Hochberg** (contrôle du taux de fausses découvertes) sur 15 tests nets unilatéraux. Les 45 autres spécifications (l'autre mode/horizon de chaque primitive) sont exploratoires et non corrigées.
- **Graines** : placebo `default_rng(11)`, test de fuite `default_rng(7)` (6 points de coupe), données manquantes/périmées 3 graines (1,2,3).
- **Critères de décision exacts** (`02_PRIMITIVE_CONTRACTS.md`) :
  - C1 : test de troncature réussi.
  - C2 : Sharpe net > 0 en DEV **et** en TEST à coûts ×1.
  - C3 : t Newey-West net FULL ≥ 2,0 **et** BH-q < 0,10.
  - C5 : Sharpe net > 0 à coûts ×2.
  - C6 : ≥ 70 % des tests de falsification applicables passés (délai +1, perturbation de paramètres min > 0, 25 % manquant, 25 % figé, actifs hold-out brut > 0, signal Coinbase brut > 0).
  - `SUPPORTED_ROBUST` = C1∧C2∧C3∧C5∧C6 ; `SUPPORTED_FRAGILE` = C1∧C2∧C3 ; `GROSS_ONLY` = t brut ≥ 2 mais pas net ; sinon `NOT_SUPPORTED`.
  - Non redondant = supporté et |corr signal| et |corr P&L brut| < 0,5 vs tout supporté mieux classé.
  - Dépendant du régime = t net ≤ −1,5 dans un seuil et ≥ +1,5 dans l'opposé, ou t ≥ 2,5 dans un seau alors que t net FULL < 2.
  - Verdict : MULTIPLE (≥ 3 ROBUST non redondants), LIMITED (1-2), NO_ROBUST (aucun), INCONCLUSIVE (échec pipeline ou placebo incapable de séparer signal et bruit).

### 2.2 Run 2

- **Données** (`04_PUBLIC_DATA.md`, `results/vision_manifest.json`) : Binance Vision (spot et perp 1 h 2024-01→2026-08, indice de prime, funding mensuel, métriques 5 min quotidiennes ; 320 fichiers demandés/retrouvés pour chacun des 4 premiers jeux, 9 740 pour les métriques, avec sha256 par fichier) ; OKX, Coinbase, Gate (seulement depuis 2025-09-10 selon 04, mais 2025-12-19 selon 09/`s5_falsify.json` pour la fenêtre d'évaluation — voir §7), Kraken (721 dernières barres), Hyperliquid (bougies depuis 2026-03-05 seulement, funding 2024-01→), Deribit DVOL. Pas d'archive de liquidations (404). Cache git-ignoré (`cache/`).
- **Simulateur** (`py/alpha_lib.py`) : décision après la barre i, gain de la barre i+1 (clôture-à-clôture, exécution à la clôture précédente). Poids égaux 1/N ; CS neutre en dollars brut 1. Le P&L « brut » **inclut le funding** ; « net » = brut − frais. Coûts par côté identiques à R1 (6/8 bp) ; jambe spot du carry +5 bp ; **coût inconnu = 15 bp**. Sharpe sur P&L **quotidien** (√365).
- **Splits** : évaluation 2024-03-01→2026-08-31 ; DEV 2024-03-01→2025-05-31 (458 j), HOLDOUT 2025-06-01→2026-08-31 (457 j).
- **Pré-enregistrement** : paramètres « par défaut pré-enregistrés » fixés avant résultats, **sauf** (a) seuil P07 et déclencheur P12 (ré-sélectionnés sur DEV après un premier passage dégénéré), (b) le null du placebo (décalage circulaire → randomisation de signe par blocs après avoir vu que le premier null était contaminé), (c) la définition de l'IC (centrée → non centrée après avoir constaté une incohérence), (d) corrections de bord de P14/P15 (`11_LIMITATIONS.md` §3). Contrairement à R1, aucun commit ne prouve la chronologie (un seul commit).
- **Incertitude** : bootstrap stationnaire (blocs de 7 jours, 2 000 tirages, graine 0) ; Holm sur 15 tests hold-out ; placebo 200 tirages ; test de permutation pour les régimes (300 décalages circulaires, graine 1) ; 45 tests primitive×régime.
- **Critères exacts** (`py/s6_adjudicate.py`, `10_ADJUDICATION.md`) : F1 brut > 0 et p bootstrap unilatéral ≤ 0,10 (FULL) ; F2 brut > 0 en DEV et HOLDOUT ; F3 net > 0 en FULL, DEV **et** HOLDOUT ; F4 net > 0 à ×1,5 coûts ; F5 ≥ 70 % des perturbations de paramètres nettes > 0 ; F6 net > 0 avec +1 barre de latence ; F7 placebo p brut ≤ 0,10 ; F8 brut > 0 sur majeurs **et** mineurs ; F9 brut > 0 sur chaque autre lieu testé ; F10 net > 0 avec 20 % de données manquantes. **NET_POSITIVE_EXTERNAL_CANDIDATE** = F3∧F4∧F5∧F6∧F7∧ p bootstrap net hold-out ≤ 0,10. **GROSS_INFORMATION_ONLY** = F1, ou (F2 ∧ placebo p ≤ 0,10), sans être net-positif. Sinon WEAK_GROSS_NOT_SIGNIFICANT (brut > 0 sans signification) ou REJECTED. Non redondant = max|ρ| < 0,5 et R² < 0,35.

---

## 3. Résultats détaillés

### 3.1 Run 1 — spécifications primaires (rapport 05, `results/tables/05_primary.md`)

Sharpe brut vs net ; t = Newey-West ; BH_q = valeur ajustée pour les 15 tests. FULL = 2023-01→2026-08 (3,66 an).

| primitive | mode | H | brut DEV | brut TEST | brut FULL | t brut | net DEV | net TEST | net FULL | t net | BH_q |
|---|---|---|---|---|---|---|---|---|---|---|---|
| P01_TSMOM | TS | 24 | +0,72 | −0,38 | +0,20 | +0,41 | +0,24 | −0,83 | −0,27 | −0,57 | 1,00 |
| P02_XS_RS7D | CS | 24 | +0,84 | +0,33 | +0,63 | +1,26 | +0,20 | −0,65 | −0,13 | −0,26 | 1,00 |
| P03_REV4H | TS | 4 | +1,01 | −0,93 | +0,09 | +0,20 | −2,80 | −4,47 | −3,58 | −7,84 | 1,00 |
| P04_VOLCOMP_BRK | TS | 24 | +0,40 | +0,68 | +0,55 | +1,08 | −0,26 | +0,19 | −0,00 | −0,00 | 1,00 |
| P05_BRK_PERSIST | TS | 24 | +0,95 | −0,03 | +0,47 | +0,98 | +0,32 | −0,58 | −0,11 | −0,23 | 1,00 |
| P06_FUND_CARRY | CS | 24 | +0,86 | −0,20 | +0,45 | +0,83 | +0,87 | −0,76 | +0,24 | +0,44 | 1,00 |
| P07_PREMIUM | TS | 4 | −0,62 | +0,39 | −0,24 | −0,50 | −1,91 | −2,51 | −2,10 | −4,41 | 1,00 |
| P08_OI_PRICE | TS | 24 | +1,37 | −0,17 | +0,71 | +1,60 | +0,34 | −1,32 | −0,37 | −0,84 | 1,00 |
| P09_OI_FLUSH | TS | 4 | +0,89 | −0,40 | +0,28 | +0,73 | +0,01 | −1,13 | −0,53 | −1,40 | 1,00 |
| P10_TAKER_IMB | TS | 4 | −0,85 | +0,60 | −0,20 | −0,44 | −4,50 | −3,42 | −4,02 | −8,50 | 1,00 |
| P11_LIQ_SHOCK | TS | 4 | −0,13 | −0,81 | −0,42 | −0,93 | −2,13 | −3,10 | −2,53 | −5,54 | 1,00 |
| P12_LEADLAG_BTC | CS | 4 | −1,86 | +0,56 | −0,92 | −1,77 | −15,34 | −17,57 | −16,02 | −31,11 | 1,00 |
| P13_SEASON_HOD | TS | 4 | +1,80 | −0,80 | +0,61 | +1,18 | −2,68 | −4,73 | −3,62 | −6,99 | 1,00 |
| P14_VRP_DVOL | TS | 24 | −0,55 | +1,08 | +0,21 | +0,40 | −0,69 | +0,97 | +0,09 | +0,17 | 1,00 |
| P15_FUND_DIV | CS | 24 | −0,51 | +1,26 | +0,22 | +0,40 | −1,51 | −0,59 | −1,13 | −2,10 | 1,00 |

**Lecture simple** : personne n'a un t brut ≥ 2 (max 1,60 pour P08). Un t de 2 correspond à ≈ 95 % de confiance ; le bruit pur (150 signaux aléatoires lissés) produit un t brut d'écart-type 0,94, p95 = 1,58, p99 = 2,05 (`falsification.json` `_placebo`) : le « meilleur » brut (P08, 1,60) est exactement au niveau du 95ᵉ centile du bruit. Six primitives (P03, P07, P10, P11, P12, P13) sont nettes-négatives avec forte confiance (t net −4,4 à −31) : ce n'est pas « pas prouvé », c'est « prouvé perdant » à cause des frais.

**Économie annualisée** (`05_econ.md`, exposition brute ≤ 1) : gross_ann / net_ann / coût / funding / turnover-par-jour / IC rang (t).

| primitive | brut %/an | net %/an | coût %/an | funding %/an | turn/jour | IC rang CS (t) |
|---|---|---|---|---|---|---|
| P01 | +7,59 | −10,46 | 16,54 | +1,50 | 0,60 | −0,01 (−0,83) |
| P02 | +13,05 | −2,66 | 16,33 | −0,62 | 0,59 | −0,01 (−1,31) |
| P03 | +3,02 | −116,24 | 119,94 | −0,68 | 4,32 | +0,03 (+8,03) |
| P04 | +1,45 | −0,01 | 1,36 | +0,09 | 0,05 | +0,02 (+0,84) |
| P05 | +18,17 | −4,33 | 20,72 | +1,79 | 0,75 | −0,01 (−0,87) |
| P06 | +7,80 | +4,14 | 9,24 | −5,58 | 0,33 | +0,04 (+4,02) |
| P07 | −8,86 | −78,29 | 73,57 | −4,14 | 2,65 | +0,01 (+3,02) |
| P08 | +13,16 | −6,95 | 19,15 | +0,96 | 0,69 | −0,02 (−2,35) |
| P09 | +2,28 | −4,38 | 6,69 | −0,03 | 0,24 | +0,03 (+2,66) |
| P10 | −6,52 | −128,72 | 123,60 | −1,40 | 4,48 | −0,01 (−1,43) |
| P11 | −4,51 | −27,48 | 23,08 | −0,10 | 0,83 | +0,00 (+0,57) |
| P12 | −14,75 | −254,06 | 239,38 | −0,07 | 8,44 | +0,03 (+6,65) |
| P13 | +20,38 | −121,11 | 140,26 | +1,23 | 5,05 | +0,02 (+5,04) |
| P14 | +1,62 | +0,66 | 0,85 | +0,10 | 0,04 | +0,02 (+0,88) |
| P15 | +3,52 | −18,39 | 21,66 | +0,25 | 0,78 | +0,02 (+2,13) |

L'**IC** (coefficient d'information : corrélation de rang entre le signal et le rendement futur) montre un paradoxe expliqué par le rapport : IC très significatifs pour P03 (t 8,0), P12 (6,6), P13 (5,0), P06 (4,0) mais P&L brut ≈ 0 ou négatif. Explication du rapport : l'IC pèse tous les actifs pareillement, le P&L est dominé par les gros mouvements. **Point que le rapport n'exploite pas** : P08 (le « meilleur brut ») a un IC **négatif significatif** (−0,021, t −2,35) : sur le classement entre actifs, son signal se classe dans le mauvais sens alors que son P&L de séries temporelles est positif. Cela renforce l'idée que le brut de P08 est du bruit ou un effet de bêta/timing plutôt qu'un pouvoir prédictif propre.

**Spécifications non primaires** (exploratoire, 45 tests non corrigés ; extrait de `05_allspecs_top.md`) :

| spec | t brut | brut DEV | brut TEST | coût %/an | break-even ×coût | net S | turn/jour |
|---|---|---|---|---|---|---|---|
| P13\|CS\|H4 | +5,30 | +3,87 | +1,19 | 233 | 0,18 | −12,44 | 8,39 |
| P05\|CS\|H4 | +4,44 | +3,85 | −0,05 | 107 | 0,42 | −3,09 | 3,85 |
| P01\|CS\|H4 | +3,18 | +2,94 | −0,28 | 79 | 0,48 | −1,76 | 2,84 |
| P08\|TS\|H4 | +2,82 | +1,66 | +1,02 | 65 | 0,48 | −1,45 | 2,36 |
| P05\|CS\|H24 | +2,36 | +2,39 | −0,43 | 33 | 0,62 | −0,75 | 1,20 |
| P02\|CS\|H4 | +2,26 | +1,51 | +0,64 | 41 | 0,63 | −0,70 | 1,46 |
| P04\|TS\|H4 | +2,00 | +0,60 | +1,61 | 7,7 | 0,65 | −0,59 | 0,27 |

Le **break-even** est le multiple des coûts supposés auquel le net devient nul (< 1 = perd de l'argent aux coûts supposés). Aucune de ces pistes n'atteint 1.

### 3.2 Run 1 — orthogonalité, persistance (rapport 06)

- 11 clusters (liaison moyenne, seuil |ρ| ≈ 0,3) ; nombre effectif de paris indépendants (rapport de participation PCA) : 10,35 (signaux), 9,93 (P&L brut) sur 15.
- Redondances : {P01, P05, P02} (ρ signal P01-P05 = +0,77, P&L +0,83 ; P01-P02 signal +0,54) ; {P03, P10, P12} (P03-P10 signal −0,56, P&L −0,62 : le déséquilibre d'achats agressifs sur 4 h est l'image miroir du rendement 4 h).
- Information incrémentale (régression du P&L brut journalier de chacune sur les 14 autres) : aucune ordonnée |t| > 2 (extrêmes P01 −1,26, P12 −1,40 ; P05 +1,05 avec R² 0,76).
- Autocorrélation des signaux : lente pour P06/P14/P15/P02 (0,9+ à 24 h), rapide pour P03/P10/P12/P11/P09 ; P13 ≈ 0,98 à 24 h par construction mécanique (moyennes de même heure).

### 3.3 Run 1 — régimes (rapport 07)

Régimes causaux : volatilité BTC (RV 168 h en percentile vs 365 jours glissants, bas < ⅓ / haut > ⅔) ; tendance = signe du rendement BTC à 30 j ; étiquette à t appliquée au P&L de t+1. Parts : bas-vol = 33,25 % des heures (`regime_table.json`).

- Règle pré-déclarée (net) : **0 candidat dépendant du régime**.
- Tendance descriptive non comptée : cluster tendance/breakout positif en LOWVOL et négatif en HIGHVOL (brut P01 +1,71/−0,81 ; P04 +1,46/−0,31 ; P05 +1,34/−0,64 ; P14 +1,26/−0,61 ; P10 +0,45/−1,73). Différences bas-moins-haut avec t ≈ 1,3-2,1 (P10 2,10 ; P01 1,93). Inverse (mieux en HIGHVOL) pour P03 (+1,04), P09 (+1,06), P08 (+1,06). Les coûts restent décisifs dans tous les régimes.

### 3.4 Run 1 — coûts (rapport 08)

Sharpe net selon multiplicateur de coûts et break-even (`cost_table.json`) :

| primitive | brut | ×0,5 | ×1 | ×2 | ×3 | ×5 | break-even | funding %/an |
|---|---|---|---|---|---|---|---|---|
| P01 | +0,20 | −0,06 | −0,27 | −0,70 | −1,13 | −1,99 | 0,37 | +1,50 |
| P02 | +0,63 | +0,27 | −0,13 | −0,92 | −1,72 | −3,30 | 0,84 | −0,62 |
| P03 | +0,09 | −1,73 | −3,58 | −7,31 | −11,05 | −18,56 | 0,03 | −0,68 |
| P04 | +0,55 | +0,26 | −0,00 | −0,52 | −1,04 | −2,08 | 1,00 | +0,09 |
| P05 | +0,47 | +0,16 | −0,11 | −0,65 | −1,19 | −2,26 | 0,79 | +1,79 |
| P06 | +0,45 | +0,50 | +0,24 | −0,29 | −0,82 | −1,89 | 1,45 | −5,58 |
| P07 | −0,24 | −1,11 | −2,10 | −4,08 | −6,05 | −9,99 | −0,06 | −4,14 |
| P08 | +0,71 | +0,14 | −0,37 | −1,40 | −2,43 | −4,50 | 0,64 | +0,96 |
| P09 | +0,28 | −0,13 | −0,53 | −1,35 | −2,16 | −3,76 | 0,35 | −0,03 |
| P10 | −0,20 | −2,09 | −4,02 | −7,86 | −11,68 | −19,25 | −0,04 | −1,40 |
| P11 | −0,42 | −1,47 | −2,53 | −4,64 | −6,74 | −10,82 | −0,19 | −0,10 |
| P12 | −0,92 | −8,44 | −16,02 | −31,33 | −46,81 | −78,02 | −0,06 | −0,07 |
| P13 | +0,61 | −1,52 | −3,62 | −7,81 | −11,99 | −20,28 | 0,14 | +1,23 |
| P14 | +0,21 | +0,14 | +0,09 | −0,02 | −0,14 | −0,36 | 1,78 | +0,10 |
| P15 | +0,22 | −0,46 | −1,13 | −2,46 | −3,78 | −6,44 | 0,15 | +0,25 |

À ×2 coûts **toutes** les primitives primaires sont nettes-négatives (meilleures : P14 −0,02, P06 −0,29). Un break-even ≈ 1 sur un brut non significatif signifie « zéro edge à zéro coût », pas une marge de sécurité.

### 3.5 Run 1 — falsification (rapport 09)

Batterie appliquée à la spec primaire (Sharpe net sauf colonnes brutes ; `falsification_table.json`) :

| primitive | base | délai+1 | délai+2 | ×2 | ×3 | manq10 | manq25 | figé10 | figé25 | k_min | k_max | hold brut | hold net | lieu base (brut) | lieu Coinbase (brut) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| P01 | −0,27 | −0,22 | −0,18 | −0,70 | −1,13 | −0,32 | −0,39 | −0,26 | −0,25 | −0,37 | +0,12 | +0,07 | −0,57 | −0,42 | −0,41 |
| P02 | −0,13 | −0,17 | −0,21 | −0,92 | −1,72 | −0,41 | −0,81 | −0,15 | −0,21 | −0,36 | +0,07 | +0,48 | −0,29 | +0,35 | +0,27 |
| P03 | −3,58 | −3,74 | −3,95 | −7,31 | −11,05 | −3,71 | −3,93 | −3,70 | −3,88 | −3,96 | −2,39 | −0,22 | −4,96 | −0,92 | −0,91 |
| P04 | −0,00 | −0,16 | −0,10 | −0,52 | −1,04 | +0,01 | −0,03 | −0,00 | +0,01 | −0,31 | +0,12 | +0,30 | −0,47 | +0,77 | +0,94 |
| P05 | −0,11 | −0,07 | −0,05 | −0,65 | −1,19 | −0,16 | −0,26 | −0,11 | −0,11 | −0,54 | +0,02 | +0,42 | −0,34 | −0,04 | −0,11 |
| P06 | +0,24 | +0,24 | +0,24 | −0,29 | −0,82 | −0,18 | −0,87 | +0,23 | +0,25 | −0,18 | +0,55 | +0,16 | −0,08 | n/a | n/a |
| P07 | −2,10 | −2,10 | −1,93 | −4,08 | −6,05 | −2,47 | −2,98 | −2,07 | −1,97 | −2,67 | −1,14 | +0,19 | −2,37 | n/a | n/a |
| P08 | −0,37 | −0,47 | −0,57 | −1,40 | −2,43 | −0,42 | −0,55 | −0,36 | −0,39 | −0,78 | −0,13 | +0,32 | −1,09 | n/a | n/a |
| P09 | −0,53 | −0,37 | −0,15 | −1,35 | −2,16 | −0,47 | −0,50 | −0,51 | −0,43 | −0,83 | +0,45 | +0,01 | −1,13 | n/a | n/a |
| P10 | −4,02 | −3,95 | −3,91 | −7,86 | −11,68 | −4,29 | −4,83 | −4,09 | −4,06 | −5,55 | −2,10 | +0,36 | −4,53 | n/a | n/a |
| P11 | −2,53 | −2,71 | −3,17 | −4,64 | −6,74 | −2,50 | −2,52 | −2,48 | −2,48 | −2,75 | −2,09 | −0,56 | −2,91 | −0,89 | −0,54 |
| P12 | −16,02 | −16,61 | −16,58 | −31,33 | −46,81 | −16,78 | −17,22 | −17,16 | −18,03 | −16,02 | −13,27 | −0,93 | −16,35 | +0,47 | +0,41 |
| P13 | −3,62 | −4,46 | −5,23 | −7,81 | −11,99 | −4,00 | −4,58 | −3,89 | −4,34 | −4,54 | −3,40 | +0,39 | −5,07 | −0,81 | −0,99 |
| P14 | +0,09 | +0,11 | +0,13 | −0,02 | −0,14 | −0,02 | −0,10 | +0,01 | +0,03 | −0,05 | +0,75 | n/a | n/a | n/a | n/a |
| P15 | −1,13 | −1,16 | −1,20 | −2,46 | −3,78 | −1,40 | −1,75 | −1,08 | −1,10 | −1,27 | −0,98 | n/a | n/a | n/a | n/a |

(« hold » = univers hold-out DOT ATOM NEAR TRX BCH ETC ; « lieu » = signal calculé à partir de barres spot Coinbase, P&L sur Binance, fenêtre TEST, 9 actifs.)

- **Contrôles** : placebo (150 signaux aléatoires EWMA-24h, TS, H=24) : σ(t brut)=0,94, p95=1,58, p99=2,05, p95 du t net = −1,62, σ(Sharpe)=0,48. Signal « futur planté » : Sharpe brut 26,7 (H=4) et 16,7 (H=24) ; avec un retard d'une barre 21,7/15,9 ; même signal désaligné de 3H : −0,39/−0,60 (`falsify.log`).
- **Suivi exploratoire des six pistes non primaires** (`exploratory_followup.json`) : P13\|CS\|H4 brut 2,80 (DEV 3,87, TEST 1,19), survit à 1 barre de retard (1,27) mais pas 2 (−0,02), signal Coinbase TEST 1,87 vs Binance 1,70, univers hold-out 0,61 seulement, net positif seulement en dessous de ≈ 0,18× les coûts. P05\|CS\|H4 et P01\|CS\|H4 : DEV 2,9-3,9 → TEST ≈ 0 (période spécifique). P08\|TS\|H4 : 1,66/1,02 stable, positif en hold-out (0,53), robuste au délai, mais break-even 0,48×.

### 3.6 Run 1 — adjudication (rapport 10)

Critères C1 tous vrais ; C2 faux partout (aucune primitive nette positive dans les deux moitiés, même P06 : +0,87 DEV / −0,76 TEST) ; C3 faux partout. **0 ROBUST, 0 FRAGILE, 0 GROSS_ONLY** (aucun t brut primaire ≥ 2). C6 (taux de réussite de la falsification) : P06 0,60 ; P04 et P14 0,50 ; P02 0,33 ; P01/P05 0,17 ; P03/P11/P15 0,00 ; etc.

### 3.7 Run 2 — décomposition complète (rapport 05, §5.1)

| primitive | Sharpe brut | Sharpe net | brut an. | prix | funding | coût | net an. | turnover/an | break-even bp/côté |
|---|---|---|---|---|---|---|---|---|---|
| P01_TSMOM | −0,06 | −0,61 | −2,6 % | −0,6 % | −2,0 % | −23,9 % | −26,5 % | 314 | −0,8 |
| P02_XS_RS | 0,16 | −0,60 | 3,2 % | 3,4 % | −0,3 % | −15,0 % | −11,8 % | 197 | 1,6 |
| P03_REV_4H | 0,38 | −2,33 | 11,5 % | 10,9 % | 0,6 % | −80,0 % | −68,5 % | 1052 | 1,1 |
| P04_DONCHIAN | 0,17 | −0,19 | 8,3 % | 10,7 % | −2,4 % | −17,5 % | −9,2 % | 230 | 3,6 |
| P05_VOL_SQUEEZE_BREAK | 0,66 | 0,10 | 5,4 % | 5,6 % | −0,2 % | −4,6 % | 0,9 % | 60 | 9,0 |
| P06_FUND_XS | 0,72 | −0,80 | 11,9 % | 8,8 % | 3,1 % | −25,1 % | −13,2 % | 329 | 3,6 |
| P07_BASIS_CARRY | 3,10 | 0,64 | 1,4 % | 0,0 % | 1,4 % | −1,1 % | 0,3 % | 6 | 26,1 |
| P08_SPOT_PERP_BASIS | −0,39 | −1,45 | −8,7 % | −10,4 % | 1,6 % | −23,5 % | −32,2 % | 308 | −2,8 |
| P09_OI_PRICE | 0,52 | −0,86 | 13,0 % | 14,0 % | −1,0 % | −34,4 % | −21,4 % | 453 | 2,9 |
| P10_LIQ_FLUSH_PROXY | −0,31 | −0,74 | −2,7 % | −2,8 % | 0,0 % | −3,8 % | −6,6 % | 51 | −5,4 |
| P11_TAKER_FLOW | 0,61 | −3,08 | 11,8 % | 12,2 % | −0,5 % | −71,3 % | −59,5 % | 940 | 1,3 |
| P12_ILLIQ_SHOCK | 0,45 | −0,63 | 0,8 % | 0,8 % | 0,0 % | −2,0 % | −1,2 % | 27 | 3,2 |
| P13_BTC_LEADLAG | −0,09 | −5,81 | −2,0 % | −1,9 % | −0,0 % | −119,7 % | −121,7 % | 1531 | −0,1 |
| P14_HOUR_SEASON | 0,85 | −11,58 | 22,6 % | 22,7 % | −0,1 % | −332,9 % | −310,3 % | 4410 | 0,5 |
| P15_RV_IV_VRP | −0,02 | −0,13 | −1,1 % | −0,9 % | −0,2 % | −4,6 % | −5,7 % | 77 | −1,4 |

Référence : **baseline « long égal-pondéré des 10 perp »** : Sharpe brut = net 0,20, prix +18,7 %/an, funding −5,4 %/an (brut an. 13,3 %), DEV 0,68 / HOLDOUT −0,35 (`s1_main.json` `baseline_ew_long`). Le rapport note que la « perte max » de −101,6 % est une somme de rendements journaliers, pas une courbe de capital.

**DEV vs HOLDOUT, avec bootstrap** (§5.2) :

| primitive | brut DEV | net DEV | brut HO | net HO | bande 90 % du net HO | p unilatéral net HO | Holm(15) | p brut FULL |
|---|---|---|---|---|---|---|---|---|
| P01 | 1,19 | 0,66 | −1,36 | −1,94 | −3,78 .. −0,26 | 0,96 | 1,00 | 0,55 |
| P02 | −0,06 | −0,68 | 0,55 | −0,52 | −2,09 .. 0,95 | 0,70 | 1,00 | 0,40 |
| P03 | 0,73 | −1,86 | 0,01 | −2,84 | −4,10 .. −1,70 | 1,00 | 1,00 | 0,25 |
| P04 | 0,16 | −0,17 | 0,20 | −0,20 | −1,62 .. 1,08 | 0,60 | 1,00 | 0,38 |
| P05 | 0,89 | 0,45 | 0,40 | −0,27 | −1,77 .. 1,08 | 0,61 | 1,00 | 0,14 |
| P06 | 0,27 | −0,94 | 1,40 | −0,62 | −2,19 .. 0,78 | 0,72 | 1,00 | 0,10 (0,097 brut) |
| P07 | 4,44 | 0,91 | plat/NA | plat/NA | 0 .. 0 | 1,00 | 1,00 | 0,00 |
| P08 | −0,95 | −1,74 | 0,40 | −1,10 | −2,66 .. 0,41 | 0,88 | 1,00 | 0,74 |
| P09 | 0,85 | −0,37 | 0,09 | −1,54 | −3,37 .. 0,08 | 0,92 | 1,00 | 0,20 |
| P10 | 0,49 | −0,04 | −0,93 | −1,28 | −2,26 .. −0,48 | 0,98 | 1,00 | 0,74 |
| P11 | 0,13 | −3,46 | 1,13 | −2,67 | −4,33 .. −1,17 | 0,99 | 1,00 | 0,14 |
| P12 | 0,49 | −0,61 | 0,41 | −0,65 | −2,15 .. 0,66 | 0,75 | 1,00 | 0,20 |
| P13 | −0,63 | −5,74 | 0,67 | −6,14 | −7,79 .. −4,62 | 1,00 | 1,00 | 0,57 |
| P14 | 0,28 | −11,26 | 1,46 | −11,91 | −13,81 .. −10,25 | 1,00 | 1,00 | 0,07 (0,065 brut) |
| P15 | −1,05 | −1,14 | 1,15 | 1,02 | −0,38 .. 2,30 | 0,09 | 1,00 | 0,50 |

Lecture : aucune bande de bootstrap net hold-out n'est entièrement positive. Le seul net hold-out positif (P15, +1,02) a un DEV de −1,14 (retournement de signe) sur 2 actifs (BTC/ETH), avec exposition moyenne 0,71 : c'est probablement du bêta directionnel BTC/ETH en 2025-26, pas un effet de prime de variance.

**IC** (§5.3, corrélation cosinus « position vs rendement futur normalisé », blocs hebdomadaires) : tous faibles (|IC| ≤ 0,05 sauf primitives rares) ; les seuls t ≥ 1,5 sont P06 (+0,0090, t 1,6), P14 (+0,0088, t 1,8), P08 hold-out (t 1,5). P01 hold-out −0,0479 (t −2,1) : le signal de tendance devient *anti-prédictif* en 2025-26.

**Réévaluation de deux déclencheurs (§5.4)** : grille DEV pour P07 : seuils {1e-4, 1,5e-4, 2e-4, 3e-4, 5e-4} → net DEV {−2,93, −0,09, −0,23, +0,91, −0,19}, sélection 3e-4 (11 rotations/an, brut DEV 4,44). Pour P12 : z ∈ {1,25, 1,5, 1,75, 2,0} → net DEV {−3,10, −2,08, −0,61, −0,51} ; la règle « meilleur net DEV parmi ≥ 20 rotations/an » choisit 1,75 (selon le rapport). *Vérifié* : `s0_tune.json` sélectionne bien `thr=0.0003` pour P07 ; la sélection z=1,75 pour P12 est celle du rapport (la grille montre −0,61 pour 1,75 et −0,51 pour 2,0, donc 2,0 aurait le meilleur net DEV brut ; le code de `s0_tune.py` prend `max` sur le net DEV sans contrainte d'activité, mais le défaut de `primitives.py` est 1,75 — voir §7).

### 3.8 Run 2 — orthogonalité, persistance (rapport 06)

- Paires redondantes (|ρ| ≥ 0,5 sur P&L brut journalier) : P01↔P04 (+0,79), P03↔P11 (−0,55). Nombre effectif de paris : 10,4 sur 14 (P07 exclue car flux quasi constant), `s2_ortho.json` : 10,3518.
- Bêta/alpha vs marché EW : alphas bruts annualisés petits et non significatifs (P14 22,3 %, t 1,33 ; P06 12,6 %, t 1,22 ; P05 5,4 %, t 1,04) sauf P07 (1,4 %, t 4,90 : flux quasi déterministe, t sans HAC trompeur).
- Persistance : durée moyenne de détention de 2,4 h (P14) à 219 h (P15) ; part de fenêtres de 90 j brutes > 0 de 0,18 (P07) à 0,76 (P11).

### 3.9 Run 2 — régimes (rapport 07)

Trois familles de régimes causaux (vol BTC vs 90 j, tendance 30 j, « chaleur » du funding = percentile du funding moyen vs 90 j). Test de permutation sur l'écart entre états : 45 tests → ≈ 2 faux positifs attendus au seuil 5 %. Résultat : 4 « dépendants du régime » (p ≤ 0,05 et signes cohérents DEV→HOLDOUT) : P02 (tendance p 0,02 ; funding_heat p 0,00), P03 (vol p 0,01), P08 (funding_heat p 0,02), P12 (tendance p 0,04). Exemples : P02 gagne en marché haussier (+32,7 % brut, t 1,8) et perd en baissier (−32,1 %, t −2,0) ; P08 perd en funding « chaud » (−70,3 %, t −2,6). Aucun ne survit à la correction pour multiplicité par construction (non appliquée).

### 3.10 Run 2 — coûts (rapport 08)

Net Sharpe selon multiplicateur (extrait) : P05 0,66 / 0,38 / **0,10** / −0,17 / −0,45 / −1,00 (×0, ×0,5, ×1, ×1,5, ×2, ×3) ; P07 3,10 / 1,97 / **0,64** / −0,39 / −1,06 / −1,80 ; P14 0,85 / −5,41 / −11,58 / … ; ratio brut/coût > 1 pour exactement deux primitives (P05 1,19 et P07 1,29). Rendement net annuel à coût uniforme 8 bp/côté : P05 +0,6 %, P07 +0,3 %, toutes les autres négatives ; à 2 bp : P04 +3,7 %, P05 +4,2 %, P06 +5,3 %, P09 +4,0 %. Hold-out ×1 / ×2 : seuls P15 (+1,02 / +0,90) et P07 (plat) ne sont pas négatifs.

### 3.11 Run 2 — falsification (rapport 09)

- **Autre lieu (§9.2)** : les stratégies purement basées sur le prix donnent des bruts très proches sur OKX perp / Coinbase spot (ex. P02 OKX 0,93 vs 0,91 de référence ; P04 OKX 0,63 vs 0,57 ; P05 OKX 0,92, Coinbase 0,78 vs 0,93 de référence). Sur Gate (fenêtre courte depuis 2025-12-19 pour l'évaluation) P05 est négatif (−0,31). Le rapport avertit lui-même que ces lieux cotent des prix quasi identiques (corrélation > 0,99) : c'est un contrôle de cohérence de flux, pas une confirmation indépendante. Signal funding Hyperliquid pour P06 : brut −1,54 (vs 0,05 avec le funding Binance sur prix OKX) ; corrélations funding HL~Binance 0,76-0,85.
- **Autres actifs (§9.3)** : P05 brut 0,67 majeurs / 0,51 mineurs ; P06 0,03 / −0,10 ; P09 1,45 / −0,33 ; P12 1,14 / −0,40 ; sortie d'un actif à la fois (net Sharpe P05 −0,07 .. 0,25).
- **Stabilité par trimestre (§9.4)** : part de trimestres bruts > 0 : de 0,27 (P07) à 0,82 (P11) ; nets > 0 : 0,00 pour P11/P13/P14, 0,55 pour P02/P05.
- **Données manquantes (§9.5)** : à 5 % d'observations manquantes P02, P15, P05 (à 20 %) deviennent « plat/NA » (fermé en cas d'échec car la fenêtre glissante stricte ne peut plus être remplie) ; P05 net 0,37 à 5 %.
- **Latence (§9.6)** : P05 net 0,10 → 0,52 (+1h), 0,61 (+2h), 0,92 (+3h), 0,14 (+6h) ; le retard *améliore* P05 (voir §7).
- **Perturbation de paramètres (§9.7)** : part net > 0 : P05 0,58 (min −0,72, max +1,04), P07 0,75, toutes les autres ≤ 0,25.
- **Placebo (§9.8)** : null par randomisation de signe par blocs de 24 h (200 tirages) : p(null ≥ observé) P05 0,08 ; P14 0,07 ; P06 0,19 ; P07 0,03 (par décalage circulaire) ; autres > 0,10.

### 3.12 Run 2 — adjudication (rapport 10)

Tableau F1-F10 reproduit dans le rapport ; résumé :

| Niveau | Primitives |
|---|---|
| NET_POSITIVE_EXTERNAL_CANDIDATE | aucune |
| GROSS_INFORMATION_ONLY | P05, P06, P07, P14 |
| WEAK_GROSS_NOT_SIGNIFICANT | P02, P03, P04, P09, P11, P12 |
| REJECTED | P01, P08, P10, P13, P15 |

Dispositions doctrine : P07 PARK, P05 PARK, P06 PARK (diagnostic), P14 PARK (diagnostic) ; toutes les autres REJECT. Non redondantes (max|ρ|<0,5, R²<0,35) dans le niveau GROSS_INFORMATION_ONLY : P05, P06, P07, P14 (`NONREDUNDANT_CANDIDATES=4`, **mais explicitement non nets-positives**). Dépendants du régime : P02, P03, P08, P12.

---

## 4. Candidats évalués un par un

Verdicts « ADOPT/ADAPT/PARK/REJECT » : **PARK** = mis de côté avec conditions de réouverture ; **REJECT** = écarté pour cet univers/résolution/coût. Aucun ADOPT/ADAPT dans aucun run.

### R1 (rapport 10, tableau de disposition)

| Primitive R1 | Disposition | Justification chiffrée | Condition de changement |
|---|---|---|---|
| P03 REV4H | REJECT (seule, à 1 h) | IC significatif (t 8,0) mais brut ≈ 0 (Sharpe 0,09) ; 4,3 rotations/jour ⇒ −116 %/an net | exécution à coûts très bas / sub-heure |
| P10 TAKER_IMB | REJECT | image miroir de P03 ; brut −0,20 ; 4,5 rot./jour | idem |
| P12 LEADLAG_BTC | REJECT à 1 h | IC t 6,6 mais 8,4 rot./jour, brut −15 %/an ; effet probablement à l'échelle de la minute | données sub-minute, exécution rapide |
| P07 PREMIUM | REJECT | brut −0,24, 2,65 rot./jour | — |
| P11 LIQ_SHOCK | REJECT | brut −0,42 | — |
| P13 SEASON_HOD | PARK | plus fortes statistiques brutes (CS H4 t 5,3) mais break-even 0,18× et sensible à la latence ; utile comme normaliseur/porte plutôt que signal directionnel | exécution maker/coûts ≪ 1 bp ; ou usage comme variable de contexte |
| P15 FUND_DIV | PARK | brut +0,22 non significatif ; net −1,13 | test avec vraies données de funding par lieu |
| P09 OI_FLUSH | PARK | brut 0,28 non signif. ; besoin de vraies liquidations | flux de liquidations horodaté |
| P01/P02/P05 (grappe tendance) | PARK comme référence | redondantes ; P01/P05 positives 2023-24, ≤ 0 en 2025-26 ; P02 reste faiblement positif (+0,84/+0,33) | comme porte de régime |
| P08 OI_PRICE | PARK | « lead » brut le plus cohérent (H4 : DEV 1,66 / TEST 1,02, hold-out 0,53, robuste au délai) mais break-even 0,48-0,64× ; IC négatif (−2,35) | coûts nets plus bas, échantillon plus long |
| P04 VOLCOMP_BRK | PARK | net ≈ 0, turnover 0,05/j, brut 0,55 non signif. ; signal rare | échantillon plus long |
| P06 FUND_CARRY | PARK | seul net ≥ 0 à ×1 mais bascule de signe DEV/TEST et échoue au test des données manquantes ; contenu économique = portage à couvrir (spot/daté) non testé | implémentation couverte (delta-neutre) |
| P14 VRP_DVOL | PARK | +0,09 net, 2 actifs, aucune puissance | plus d'actifs/ténors |

### R2 (rapport 10)

| Primitive R2 | Niveau | Justification | Disposition |
|---|---|---|---|
| P01 TSMOM | REJECTED | brut −0,06 ; DEV +1,19 → HO −1,36 ; IC HO t −2,1 | REJECT |
| P02 XS_RS | WEAK_GROSS | brut 0,16 (0,91 sur 5 actifs) ; dépend du régime (tendance/funding) | REJECT |
| P03 REV_4H | WEAK_GROSS | brut 0,38, net −2,33 ; 1 052 rotations/an | REJECT |
| P04 DONCHIAN | WEAK_GROSS | brut 0,17, net −0,19 ; redondant avec P01 (0,79) | REJECT |
| P05 VOL_SQUEEZE_BREAK | GROSS_INFO_ONLY | brut 0,66, net 0,10 (= ≈ 0), fragile à ×1,5 (−0,17) ; IC change de signe DEV→HO | PARK |
| P06 FUND_XS | GROSS_INFO_ONLY | brut 0,72 (p 0,097), net −0,80 ; ≈ 0 sur majeurs et négatif sur mineurs ; signal HL −1,54 | PARK (diagnostic) |
| P07 BASIS_CARRY | GROSS_INFO_ONLY | brut 3,10 mais 1,4 %/an de capital, net 0,3 %/an, **inactif en HOLDOUT** ; seuil choisi sur DEV | PARK (surveiller le régime de carry) |
| P08 SPOT_PERP_BASIS | REJECTED | brut −0,39 | REJECT |
| P09 OI_PRICE | WEAK_GROSS | brut 0,52 (1,45 majeurs, −0,33 mineurs) ; sur OKX brut 1,68/net 0,56 (5 actifs) | REJECT |
| P10 LIQ_FLUSH_PROXY | REJECTED | brut −0,31 | REJECT |
| P11 TAKER_FLOW | WEAK_GROSS | brut 0,61, net −3,08 | REJECT |
| P12 ILLIQ_SHOCK | WEAK_GROSS | brut 0,45 ; 4 % d'activité ; seuil réajusté | REJECT |
| P13 BTC_LEADLAG | REJECTED | brut −0,09 ; net −5,81 | REJECT |
| P14 HOUR_SEASON | GROSS_INFO_ONLY | brut 0,85 (HO 1,46) mais 4 410 rot./an ; net −11,58 ; break-even 0,5 bp | PARK (diagnostic) |
| P15 RV_IV_VRP | REJECTED | brut −0,02 ; net HO +1,02 mais DEV −1,14 | REJECT |

**Conditions communes de changement de verdict** (les deux runs) : exécution maker avec modèle de file d'attente et paliers de frais réels ; données sub-heure / carnet d'ordres / flux de liquidations horodatés ; carry couvert (spot/daté) ; échantillon plus long / plus large ; données indépendantes postérieures à 2026-09 comme vrai hold-out.

---

## 5. Blocs finaux (reproduits tels quels) et explications

### 5.1 Bloc final R1 (`bench/alpha_primitives_v1/results/final_block.txt`, identique à 00 et 10)

```
PRIMITIVES_DISCOVERED=34
PRIMITIVES_EXECUTED=15

FORWARD_SAFE_COUNT=12            # strict class FORWARD_SAFE (+16 FORWARD_SAFE_WITH_RECEIPT_STAMP, 1 OFFLINE_ONLY)
LOOKAHEAD_RISK_COUNT=5          # all among the discovered-not-executed variants; 0 of 15 executed

NONREDUNDANT_CANDIDATES=0
REGIME_DEPENDENT_CANDIDATES=0

NET_POSITIVE_EXTERNAL_CANDIDATES=0

ANY_DROP_IN_STRATEGY=FALSE
LOCAL_INTEGRATION_AUTHORIZED=FALSE

FINAL_VERDICT=NO_ROBUST_ALPHA_PRIMITIVE_SUPPORTED
```

### 5.2 Bloc final R2 (`results/final_block.txt`, identique à 00)

```
PRIMITIVES_DISCOVERED=43
PRIMITIVES_EXECUTED=15

FORWARD_SAFE_COUNT=9   # executed primitives classed strictly FORWARD_SAFE (a further 6 executed are FORWARD_SAFE_WITH_RECEIPT_STAMP; catalogue-wide: 21 + 12)
LOOKAHEAD_RISK_COUNT=7   # discovered candidates classed LOOKAHEAD_RISK (0 among executed; OFFLINE_ONLY discovered: 3)

NONREDUNDANT_CANDIDATES=4   # gross-information-only tier AND max|rho|<0.5 AND R2<0.35: P05_VOL_SQUEEZE_BREAK, P06_FUND_XS, P07_BASIS_CARRY, P14_HOUR_SEASON. NOT net-positive.
REGIME_DEPENDENT_CANDIDATES=4   # statistical flags only (45 tests, ~2 expected by chance): P02_XS_RS, P03_REV_4H, P08_SPOT_PERP_BASIS, P12_ILLIQ_SHOCK

NET_POSITIVE_EXTERNAL_CANDIDATES=0

ANY_DROP_IN_STRATEGY=FALSE
LOCAL_INTEGRATION_AUTHORIZED=FALSE

FINAL_VERDICT=NO_ROBUST_ALPHA_PRIMITIVE_SUPPORTED
```

### 5.3 Explication ligne par ligne

| Clé | Signification | R1 | R2 |
|---|---|---|---|
| `PRIMITIVES_DISCOVERED` | nombre de signaux candidats répertoriés dans la littérature/OSS (exécutés ou non) | 34 | 43 |
| `PRIMITIVES_EXECUTED` | ceux réellement simulés sur données | 15 | 15 |
| `FORWARD_SAFE_COUNT` | signaux calculables à l'instant de décision sans détail d'horodatage. **Attention : les deux runs ne comptent pas sur la même base** : R1 = 12 sur les 34 découverts (exécutés : 9 strict + 6 « avec tampon de réception » = 15 sûrs) ; R2 = 9 sur les 15 exécutés (21 sur 43 au niveau catalogue) | 12 (de 34) | 9 (de 15) |
| `FORWARD_SAFE_WITH_RECEIPT_STAMP` (dans le commentaire) | sûr seulement si la donnée est capturée en direct avec son propre horodatage de réception (les archives ne prouvent pas la disponibilité) | 16 (de 34) | 6 exécutés, 12 catalogue |
| `LOOKAHEAD_RISK_COUNT` | candidats *découverts* qui utilisent le futur tels qu'implémentés couramment (filtre centré, HMM lissé, normalisation plein échantillon, etc.) ; aucun exécuté | 5 | 7 |
| `NONREDUNDANT_CANDIDATES` | primitives « supportées » et peu corrélées aux autres. R1 : 0 car aucune supportée. R2 : définition **plus laxiste** (niveau brut seulement) donc 4, explicitement non nettes-positives | 0 | 4 |
| `REGIME_DEPENDENT_CANDIDATES` | primitives dont le comportement change avec le régime. R1 : règle basée sur le net ⇒ 0 ; R2 : règle basée sur le brut par permutation (≈ 2 attendus par hasard) ⇒ 4 | 0 | 4 |
| `NET_POSITIVE_EXTERNAL_CANDIDATES` | primitives rentables *après frais*, robustes | 0 | 0 |
| `ANY_DROP_IN_STRATEGY` | y a-t-il une stratégie prête à brancher ? | FALSE | FALSE |
| `LOCAL_INTEGRATION_AUTHORIZED` | l'intégration dans le code AurumShift est-elle autorisée ? | FALSE | FALSE |
| `FINAL_VERDICT` | `NO_ROBUST_ALPHA_PRIMITIVE_SUPPORTED` = aucun signal robuste et soutenu par les preuves | idem | idem |

Comptes vérifiés ✔ : R1 12+16+1+5 = 34 (recomptés d'après `02_PRIMITIVE_CONTRACTS.md`) ; R2 21+12+3+7 = 43 (recomptés dans `02_PRIMITIVE_CONTRACTS.md`). Les libellés `NONREDUNDANT`/`REGIME_DEPENDENT` ne sont **pas comparables** entre R1 et R2 (voir §8.6).

---

## 6. Contrôles de validité

### 6.1 Run 1
- **Test de troncature (fuite d'information)** : pour 6 points de coupe aléatoires (graine 7), on recalcule chaque signal sur des données coupées à T et on compare avec la valeur pleine sur les lignes T-300…T. Résultat : **15/15 PASS**, écart max 0,0 (`lookahead_test.json`, cellules comparées 3 612 à 36 120 selon la primitive). Contrôle négatif (signal = rendement de la barre suivante) : **échoue comme il se doit** (`max_abs_diff` 1,0). ✔
- **Contrôles du simulateur** : signal futur planté détecté (Sharpe 26,7 ; 16,7) ; décalé de 3H ≈ −0,39/−0,60 ; placebo calibré (σ(t)=0,94). ✔ (`falsify.log`)
- **Déterminisme** : graines fixes ; résultats dépendent d'un instantané au 2026-09-29 et de l'historique des fournisseurs (Deribit/HL/Coinbase peuvent être révisés).
- **Corrections en cours de route déclarées** : `min_periods`, OI=0→manquant, réindexation de colonnes ; ajout de contrôles (`11_LIMITATIONS.md` §2).
- **Écarts au protocole** : le test rapide 3 actifs a été lu avant ; les sorties du test rapide sont dans le commit 8738106 (écrasées ensuite).
- **Non testable** : délais réels de publication, révisions rétroactives des archives Binance (UNKNOWN).

### 6.2 Run 2
- **Audit de causalité** : poids recalculés sur données coupées à 5 instants (2024-09-15, 2025-03-03, 2025-08-20, 2026-01-11, 2026-06-30), comparaison avec tolérance 1e-9 : 15/15 PASS, écart 0,0. ✔ (`s1_main.json`). Limite : la comparaison s'arrête à T−1 h pour toutes les primitives (le rapport le justifie pour P14 seulement), donc une fuite d'exactement la dernière heure ne serait pas détectée ; pas de contrôle négatif (signal volontairement fuité) documenté, contrairement à R1.
- **Manifestes** : sha256 de chaque fichier Binance Vision et des séries cross-lieux commités : atout de reproductibilité (R1 n'en a pas).
- **Écarts au protocole déclarés** : P07/P12 (DEV seulement), null du placebo, définition IC, bords P14/P15. Les premiers résultats de P07/P12 ont été vus.
- **Placebo** : le null circulaire a été *rejeté* pour cause de contamination (P14 : null 2,1 vs observé 0,85) — bon signe de rigueur, mais le remplaçant (signe aléatoire par blocs de 24 h) teste « direction » et non « timing ».

---

## 7. Critique indépendante

### 7.1 Points communs (fragilités partagées)
1. **Puissance faible** : 3,7 ans (R1) / 2,5 ans (R2) ; erreur type du Sharpe ≈ 0,5 (R1 le dit : σ placebo 0,48) ; un vrai Sharpe net < ≈ 1 est indétectable. Le verdict « pas de support » ≠ « pas d'alpha ».
2. **Coûts génériques** : 6/8 bp par côté = hypothèse, pas devis ; taker uniquement. Toute la conclusion « les frais mangent tout » dépend de l'exécution au prix taker : le maker (frais souvent plus bas ou rebate) n'est pas testé. Or les primitives à plus fort brut (P13/P14, P03, P10-P12) sont exactement celles où la qualité d'exécution change tout.
3. **Survivorship** : 10 actifs choisis rétrospectivement parmi les liquides de 2026 (les deux runs le déclarent).
4. **Résolution 1 h** : les effets de microstructure (retard BTC→alt, déséquilibres) vivent à la minute/seconde : les tester en 1 h les rend structurellement inactifs.
5. **Une seule source principale** (Binance) ; les lieux croisés cotent des prix quasi identiques (R2 le dit).
6. **Littérature** = DOCUMENTED_CLAIM via extraits ; sources non toutes ouvertes (R1 : « the lead analyst did not independently re-open every page ») ; plusieurs sources 2026 non relues par les pairs. R2 : OSS jugés sur documentation web uniquement.
7. **Aucun ajustement de multiplicité complet pour les explorations** (R1 : 45 spécifications non primaires ; R2 : 45 tests de régime).

### 7.2 Run 1
- **Test partiellement vu** avant les résultats complets (smoke 3 actifs), non effaçable : P02 TS et P08 TS H4 avaient déjà t > 2 sur 3 actifs (`11_LIMITATIONS.md`). Le pré-enregistrement est donc « fort mais pas aveugle ».
- **Documentation contradictoire** : `04_PUBLIC_DATA.md`, `11_LIMITATIONS.md` §12 et `.gitignore` disent que `pnl_primary.parquet` (P&L horaire) n'est pas commité ; il **l'est** (21,9 Mo, présent dans l'arbre de la branche, lu et réutilisé par moi). ✘ écart documentaire mineur (favorable à la reproductibilité). De même le README dit que les données brutes ~400 Mo ne sont pas commitées : correct.
- **IC négatif de P08** (t −2,35) non discuté alors que P08 est présenté comme « lead le plus cohérent ».
- **Sensibilité à la définition des tranches** : le mode TS pondère par z/écart-type glissant, exposition brute moyenne faible (P04 0,024, P14 0,14, P01 0,50, P08 0,35 — calculé depuis `pnl_primary.parquet`), donc des Sharpe/volatilités calculés sur un capital largement inutilisé.
- **Net annualisé aberrant** : P12 net −254 %/an, P10 −129 % : un rendement < −100 % n'a pas de sens pour un capital réel (arithmétique additive, pas composée) ; sans conséquence sur le verdict mais à lire comme « très perdant ».
- **Choix en bord de grille** : les horizons 4 h et 24 h sont les seuls testés ; la moitié des primitives pré-déclarées à H=4 (P03, P07, P09-P13) sont précisément celles à turnover élevé, pré-condamnées par les coûts. Bien que l'ensemble soit défendable, cela rend le résultat « frais > edge » presque mécanique pour ces 7 primitives.
- **Gestion des données manquantes** : « figé 25 % » ne change presque rien, ce que le rapport présente honnêtement comme « insensible plutôt que robuste ».
- **Univers hold-out** = actifs aussi survivants ; le brut positif sur hold-out (P02 +0,48, P04 +0,30, P05 +0,42, P08 +0,32, P10 +0,36, P13 +0,39…) est non significatif.

### 7.3 Run 2
- **Fenêtre courte et mi-tuning** : 914 j ; la période 2024-03→2026-08 a peu de régimes ; bande bootstrap ±1,5.
- **Pré-enregistrement partiel avec modifications post hoc** : P07/P12, null du placebo, IC, bords P14/P15 (déclarés). Un seul commit : impossible de vérifier la chronologie.
- **P07 est fragile et sur-interprété** : seuil sélectionné sur DEV (grille de 5), puis Sharpe « FULL » 3,10 calculé en incluant DEV (in-sample) ; actif ≈ 4 % du temps (`active_share` 0,0398) ; rendement 1,4 %/an ; inactif en HOLDOUT (Sharpe NA). Le placebo p = 0,03 (décalage circulaire) et l'alpha t 4,9 (OLS sans HAC) ne signifient pas grand-chose pour un flux presque constant ; le rapport le nuance mais le classe malgré tout « GROSS_INFORMATION_ONLY » et « non redondant ». Le Sharpe brut de 3,10 est un artefact de faible volatilité.
- **Classement sur un seuil de p au bord** : P06 classé « GROSS_INFORMATION_ONLY » avec p brut = 0,097 (seuil 0,10) ; P14 p 0,065 ; P05 (p brut 0,143 ne passe pas F1) classé via F2∧placebo p 0,08. Avec 15 tests, ≈ 1,5 succès à 10 % sont attendus (le rapport le dit). Les 4 étiquettes GROSS_INFORMATION_ONLY sont donc compatibles avec le hasard.
- **Latence « améliore » P05** (net 0,10 → 0,92 à +3 h) : l'écart-type d'un Sharpe ≈ 0,5-0,6 sur 914 j ; ce n'est pas un effet démontré mais cela souligne que le net de P05 est du bruit.
- **Chiffre codé en dur non vérifiable** : « le funding moyen sur 8 h est passé de 7,6e-5 à 2,4e-5 » n'existe que comme texte (`catalog.py`, `gen_reports2.py`), sans calcul dans un JSON de résultats. ? non vérifiable.
- **Ambiguïté de signe** : P11 « continuation » pré-enregistrée alors que la littérature citée (arXiv 2608.21888) annonce un *renversement* après déséquilibre (le rapport le dit dans « Failure modes »). Sur le principe cela ne biaise pas l'audit mais le test sonde la mauvaise direction d'après sa propre source.
- **« Plat/NA » = échec fermé** pour P02/P15 dès 5 % de données manquantes : c'est un artefact de fenêtres strictes (`min_periods=window`), pas de la marché.
- **Incohérences internes mineures** : fenêtre Gate « depuis 2025-09-10 » (04) vs « 2025-12-19 » (09 et `s5_falsify.json`, fenêtre d'évaluation effective) ; le rapport §5.4 affiche deux fois « thr 0.0001 » (1e-4 et 1,5e-4 arrondi) — artefact d'arrondi ✔ (`s0_tune.json` : 0,0001 et 0,00015) ; le rapport §5.4 décrit la règle de sélection de P12 comme « meilleur net DEV parmi ceux ≥ 20 rotations/an » alors que `s0_tune.py` prend simplement le max du net DEV (sélection automatique = 2,0 avec −0,51), tandis que le défaut de `primitives.py` est 1,75 : la sélection a donc été ajustée à la main (documenté en prose, non dans le code). ✘ écart entre code et rapport, sans effet sur le verdict.
- **Bêta/alpha sans HAC** (déclaré) : t d'alpha de P07 (4,90) et autres sont sur-optimistes.

### 7.4 Ce que les chiffres ne prouvent PAS
- Qu'aucun alpha n'existe ; qu'un carry couvert (spot/perp) soit inintéressant (R2 P07 est un embryon, avec capital/marge/risque de contrepartie non modélisés) ; que le maker soit non rentable ; que des horizons plus lents ou d'autres classes d'actifs soient sans signal.
- Que les « pistes brutes » (P13 CS H4 t 5,3 ; P14 R2 brut 0,85) soient réelles : elles sont exploratoires, non corrigées ; et leur coût est 2 à 3 ordres de grandeur supérieur au brut.

### 7.5 Écarts rapport vs résultats bruts (synthèse)
Aucun écart numérique trouvé sur ≥ 500 valeurs recontrôlées (voir tableaux §7.6). Seuls écarts : documentation (`pnl_primary.parquet` R1), sélection P12 (code vs prose R2), fenêtre Gate (R2), chiffre de funding non calculé (R2).

### 7.6 Vérifications effectuées (chiffres clés)

**Run 1** (fichiers `results/main_results.json`, `falsification.json`, `pnl_primary.parquet`, `adjudication.json`, `regime_table.json`)

| # | Affirmation du rapport | Valeur relue | Statut |
|---|---|---|---|
| 1 | Table 05 primaire (15 lignes × 8 valeurs = 120 chiffres) | tous identiques au json à 0,006 près | ✔ |
| 2 | Table économique 05 (15 × 7 = 105 chiffres) | identiques | ✔ |
| 3 | Table de falsification 09 (15 × 16 = 240 cellules) | identiques | ✔ |
| 4 | P08 meilleur brut +0,71, t 1,60 | 0,708 ; 1,596 | ✔ |
| 5 | P06 meilleur net +0,24 (t 0,44) | 0,238 ; 0,442 | ✔ |
| 6 | Placebo σ 0,94, p95 1,58, p99 2,05, net p95 −1,62 | 0,938 ; 1,580 ; 2,053 ; −1,621 | ✔ |
| 7 | Sharpe recalculé indépendamment depuis le P&L horaire commité (P01, P04, P06, P08, P12, P13, P14) | égalité exacte (ex. P12 brut −0,922, net −16,016 ; turnover 8,436/j) et t NW recalculés identiques | ✔ |
| 8 | Comptes de classes 12/16/1/5 sur 34 | recomptés à partir de 02 | ✔ |
| 9 | Positif en DEV pour 9/15, en TEST pour 7/15, dans les deux : P02 et P04 seulement | recomptés | ✔ |
| 10 | Suivi exploratoire P13 CS H4 : 2,80/3,87/1,19, délais 1,27 | `exploratory_followup.json` | ✔ |
| 11 | Corrélation Binance/Coinbase, ADA 0,968 | `data_audit.json` 0,968 | ✔ |
| 12 | Régime P01 LOWVOL brut 1,71 ; P10 bas−haut t 2,10 | 1,709 ; 2,099 | ✔ |
| 13 | BH_q = 1,00 partout | reconstitué par la formule | ✔ |
| 14 | `pnl_primary.parquet` « non commité » (11 §12) | présent, 21,9 Mo | ✘ (documentaire) |

**Run 2** (`s1_main.json`, `s2_ortho.json`, `s4_cost.json`, `s5_falsify.json`, `s6_adjudication.json`)

| # | Affirmation | Valeur relue | Statut |
|---|---|---|---|
| 1 | Table 5.1 (15 lignes) | identiques (les 4 « écarts » du script ne sont que le signe d'affichage des coûts) | ✔ |
| 2 | Table 5.2 : DEV/HO brut/net, bandes, p | 58 valeurs identiques | ✔ |
| 3 | Baseline EW : 0,20 ; +18,7 % prix ; −5,4 % funding | 0,2047 ; 0,1875 ; −0,0542 | ✔ |
| 4 | §9.6 latence (60 valeurs) | identiques | ✔ |
| 5 | §9.7 perturbations (75 valeurs) | identiques | ✔ |
| 6 | §9.8 placebo (60 valeurs) | identiques | ✔ |
| 7 | §9.3 actifs (28 cellules) | identiques | ✔ |
| 8 | §9.4 sous-périodes | identiques | ✔ |
| 9 | Paires redondantes P01-P04 0,79, P03-P11 −0,55 ; PR 10,4 | 0,791 ; −0,546 ; 10,352 | ✔ |
| 10 | Coûts P05/P07/P14 (×0…×3) et ratios brut/coût 1,19 / 1,29 | identiques | ✔ |
| 11 | P07 inactif en HOLDOUT | turnover 0, exposition 0, Sharpe NaN | ✔ |
| 12 | Comptes de classes 21/12/3/7 | recomptés | ✔ |
| 13 | Holm-15 = 1,00 partout | P15 : 0,09×15 → plafonné à 1 | ✔ |
| 14 | Funding moyen 7,6e-5 → 2,4e-5 | uniquement du texte | ? |
| 15 | Fenêtre Gate depuis 2025-09-10 (04) | `s5_falsify.json` : 2025-12-19 (début d'évaluation, avec 100 jours de délai possible) | ? ambigu |

---

## 8. Comparaison des deux runs (obligatoire)

### 8.1 Différences de protocole (pourquoi les chiffres ne coïncident pas)

| Dimension | R1 | R2 |
|---|---|---|
| Période d'évaluation | 2023-01 → 2026-08 (3,66 an, 32 136 h) | 2024-03 → 2026-08 (914 j) |
| Split | DEV 2023-24 / TEST 2025-26 | DEV 2024-03→2025-05 / HOLDOUT 2025-06→2026-08 |
| Portefeuille | tranches chevauchantes (1/H reformé chaque heure), H ∈ {4, 24} | poids fixes réévalués tous les R (1 à 24 h), sans chevauchement |
| Modes | chaque signal en TS et CS (60 combinaisons dont 15 primaires) | un mode par primitive |
| Fill | ouverture suivante | clôture de la barre de décision (équivalent) |
| « Brut » | prix seul ; funding compté dans le net | prix + funding |
| Sharpe | horaire √8760 ; t Newey-West | journalier √365 ; bootstrap par blocs |
| Adjudication | bar sévère : t net ≥ 2 et BH-q < 0,10 + C2, C5, C6 | 10 drapeaux F1-F10 + p bootstrap hold-out |
| Pré-enregistrement | commit d'avance (mais smoke test vu) | affirmé, non prouvable, dérogations déclarées |
| Références | ancre : placebo 150 + signal planté + contrôle fuite | ancre : baseline long EW + placebo par signe + manifestes sha256 |
| Coûts | 6/8/10 bp, ×0,5..×5 | 6/8 bp, ×0..×3, uniforme 0-30 bp, 15 bp inconnu |
| Univers de test externe | 6 actifs hold-out + Coinbase 9 actifs | majeurs/mineurs, leave-one-out, OKX/Coinbase/Gate/Kraken/HL sur 5 actifs |
| Univers découvert | 34 (18 familles) | 43 (19 étiquettes de famille) |

### 8.2 Correspondance des primitives

| Famille | Primitive R1 | Primitive R2 | Même définition ? |
|---|---|---|---|
| Tendance TS | P01 TSMOM (moyenne 24 h/72 h) | P01 TSMOM (72 h, réajust. 6 h) | proche |
| Force relative CS | P02 XS_RS7D | P02 XS_RS (168 h) | quasi identique |
| Renversement 4 h | P03 REV4H | P03 REV_4H | quasi identique |
| Compression → breakout | P04 VOLCOMP_BRK | P05 VOL_SQUEEZE_BREAK | différentes (Parkinson/Donchian vs percentile d'écart-type + z6) |
| Breakout | P05 BRK_PERSIST (position continue dans le canal 48 h) | P04 DONCHIAN (machine à états 48 h/24 h) | différentes |
| Funding | P06 FUND_CARRY (CS directionnel, moyenne 72 h) | P06 FUND_XS (CS, 3 derniers règlements) et P07 BASIS_CARRY (delta-neutre, seuil) | R2 ajoute le portage couvert |
| Base | P07 PREMIUM (indice de prime, TS 4 h) | P08 SPOT_PERP_BASIS (z du perp/spot) | différentes |
| OI/prix | P08 OI_PRICE | P09 OI_PRICE | proches |
| Liquidations (proxy) | P09 OI_FLUSH | P10 LIQ_FLUSH_PROXY | proches |
| Flux taker | P10 TAKER_IMB | P11 TAKER_FLOW | proches |
| Choc de liquidité | P11 LIQ_SHOCK (volume z>1,5) | P12 ILLIQ_SHOCK (Amihud) | différentes |
| Lead-lag BTC | P12 LEADLAG_BTC | P13 BTC_LEADLAG | proches |
| Saisonnalité horaire | P13 SEASON_HOD (moyenne des 60 derniers jours, même heure) | P14 HOUR_SEASON (moyenne expansive, t-stat) | différentes |
| VRP | P14 VRP_DVOL | P15 RV_IV_VRP | proches |
| Divergence de funding inter-lieux | P15 FUND_DIV (Binance vs Hyperliquid) | (aucune primitive ; ne figure qu'en test de falsification de P06) | non comparable |

### 8.3 Chiffres côte à côte — mes recalculs sur la fenêtre commune

Pour comparer à conditions égales, j'ai recalculé les Sharpe de R1 (depuis son `pnl_primary.parquet`, P&L journalier agrégé, √365) sur la fenêtre de R2. Ces recalculs sont les miens (ils ne sont pas dans les rapports). « Brut+funding » = brut R1 − coût de funding, pour aligner sur la définition de R2. Lecture : arrondis à 0,01 ; l'échantillonnage journalier donne de légers écarts avec les Sharpe horaires du rapport R1 (ex. P08 0,80 vs 0,71).

**Fenêtre 2024-03 → 2026-08 (celle de R2), spécification primaire de R1**

| Famille | Brut+funding R1 | Brut R2 | Net R1 | Net R2 | Turnover/an R1 | Turnover/an R2 |
|---|---|---|---|---|---|---|
| TSMOM | +0,10 | −0,06 | −0,33 | −0,61 | 220 | 314 |
| Force relative | +0,69 | +0,16 | −0,15 | −0,60 | 216 | 197 |
| Renversement 4 h | −0,33 | +0,38 | −4,30 | −2,33 | 1 579 | 1 052 |
| Compression/breakout | +0,74 | +0,66 | +0,19 | +0,10 | 19 | 60 |
| Breakout (canal / Donchian) | +0,53 | +0,17 | −0,00 | −0,19 | 271 | 230 |
| Funding directionnel | +0,28 | +0,72 | −0,32 | −0,80 | 133 | 329 |
| Base | −0,53 | −0,39 | −2,76 | −1,45 | 1 035 | 308 |
| OI/prix | +0,47 | +0,52 | −0,63 | −0,86 | 256 | 453 |
| OI flush | −0,09 | −0,31 | −1,08 | −0,74 | 85 | 51 |
| Flux taker | +0,01 | +0,61 | −3,97 | −3,08 | 1 641 | 940 |
| Choc de liquidité | −0,59 | +0,45 | −2,90 | −0,63 | 299 | 27 |
| Lead-lag BTC | −0,86 | −0,09 | −16,39 | −5,81 | 3 074 | 1 531 |
| Saisonnalité horaire | −0,33 | +0,85 | −4,13 | −11,58 | 1 777 | 4 410 |
| VRP | +0,11 | −0,02 | +0,01 | −0,13 | 14 | 77 |

**Sous-période « hold-out » de R2 (2025-06 → 2026-08)**

| Famille | Brut+fund R1 | Brut HO R2 | Net R1 | Net HO R2 |
|---|---|---|---|---|
| TSMOM | −0,37 | −1,36 | −0,83 | −1,94 |
| Force relative | +0,90 | +0,55 | −0,22 | −0,52 |
| Renversement | −0,88 | +0,01 | −4,90 | −2,84 |
| Compression/breakout | −0,03 | +0,40 | −0,74 | −0,27 |
| Breakout | −0,31 | +0,20 | −0,89 | −0,20 |
| Funding | −0,33 | +1,40 | −1,32 | −0,62 |
| Base | +0,80 | +0,40 | −2,37 | −1,10 |
| OI/prix | −0,33 | +0,09 | −1,58 | −1,54 |
| OI flush | −1,10 | −0,93 | −2,08 | −1,28 |
| Taker | +0,80 | +1,13 | −3,52 | −2,67 |
| Choc liquidité | −0,61 | +0,41 | −3,22 | −0,65 |
| Lead-lag | +1,51 | +0,67 | −18,93 | −6,14 |
| Saisonnalité | −0,52 | +1,46 | −4,55 | −11,91 |
| VRP | +1,08 | +1,15 | +0,96 | +1,02 |

**Chiffres tels que rapportés (non alignés)**, primitive par primitive :

| Primitive (famille) | R1 brut / net FULL (2023-26) | R2 brut / net FULL (2024-26) | Accord ? |
|---|---|---|---|
| TSMOM | +0,20 / −0,27 (DEV +0,72 → TEST −0,38) | −0,06 / −0,61 (DEV +1,19 → HO −1,36) | **Oui** : brut ≈ 0, net négatif, décroissance 2025-26 |
| Force relative | +0,63 / −0,13 | +0,16 / −0,60 | Sens : brut faiblement positif, net négatif ; ampleur différente (0,63 vs 0,16) |
| Renversement 4 h | +0,09 / −3,58 | +0,38 / −2,33 | **Oui** sur l'essentiel : brut ≈ 0, net très négatif |
| Compression/breakout | +0,55 / −0,00 | +0,66 / +0,10 | **Oui** : brut ~0,6, net ≈ 0 ; c'est la seule paire où les deux nets sont ≥ 0 |
| Breakout persistant | +0,47 / −0,11 | +0,17 / −0,19 | Oui (net ≈ −0,1/−0,2), brut plus élevé en R1 |
| Funding directionnel | +0,45 / +0,24 (DEV +0,87 → TEST −0,76) | +0,72 / −0,80 | **Non pour le net** : R1 +0,24, R2 −0,80 ; définitions et fenêtres différentes (R1 net inclut +5,6 %/an de funding reçu) |
| Base | −0,24 / −2,10 | −0,39 / −1,45 | Oui (négatif) |
| OI/prix | +0,71 / −0,37 | +0,52 / −0,86 | **Oui** : brut ~0,5-0,7, net négatif |
| OI flush | +0,28 / −0,53 | −0,31 / −0,74 | Net oui ; brut de signes opposés (bruit) |
| Taker | −0,20 / −4,02 | +0,61 / −3,08 | Net oui ; brut de signes opposés |
| Choc de liquidité | −0,42 / −2,53 | +0,45 / −0,63 | Net négatif partout ; brut signes opposés |
| Lead-lag BTC | −0,92 / −16,02 | −0,09 / −5,81 | Oui (négatif, R1 très pénalisé par 8,4 rot./jour) |
| Saisonnalité horaire | +0,61 / −3,62 | +0,85 / −11,58 | Brut ~0,6-0,85 dans les deux ; net très négatif (turnover 5 vs 12/jour) |
| VRP (BTC/ETH) | +0,21 / +0,09 | −0,02 / −0,13 | Oui : ≈ 0 |
| Divergence funding Binance/HL | +0,22 / −1,13 | (signal HL testé sur P06 : −1,54 brut) | Direction concordante : négatif |
| Carry delta-neutre | non exécuté | brut 3,10 / net 0,64 (inactif en HO) | R2 seulement |

### 8.4 Là où les deux s'accordent (solide)
- **Verdict identique** et mêmes 0 candidat net-positif.
- **Les frais dominent** : R1 : t nets jusqu'à −31 ; R2 : break-even 0,5 bp (saison) / 1,1 bp (renversement) / 1,3 bp (taker) contre 6-8 payés. Dans les deux, les primitives à >1 000 rotations/an (en R2) ou > 4 rot./jour (en R1) perdent de 68 % à > 300 %/an.
- **Toutes deux positives en brut mais non significatives** pour compression/breakout, OI/prix et saisonnalité horaire ; **≈ 0 pour la tendance** et le VRP.
- **Décroissance de la tendance en 2025-26** (TSMOM : R1 0,72 → −0,38 ; R2 1,19 → −1,36).
- **Redondances** : tendance/breakout (R1 P01-P05 ρ +0,83 en P&L ; R2 P01-P04 +0,79) ; renversement/flux (R1 P03-P10 −0,62 ; R2 P03-P11 −0,55) ; nombre effectif de paris ≈ 10 (R1 10,35 ; R2 10,4).
- **Aucun ne survit à ×1,5-×2 coûts** (R1 : tout négatif à ×2 ; R2 : rien à ×1,5).
- **Audit de causalité 15/15 PASS** dans les deux.
- **Puissance limitée** reconnue par les deux.
- **Les tests de robustesse à la donnée manquante pénalisent le portage (R1 P06 : +0,24 → −0,87 à 25 %)** et les fenêtres strictes (R2 : « plat/NA »).

### 8.5 Là où ils divergent, et pourquoi (probable)
1. **Carry/funding.** R1 P06 (net FULL +0,24, seul net positif, « PARK ») vs R2 P06 (net −0,80). Raisons probables : fenêtre (R1 inclut 2023 où le funding reçu était plus abondant : DEV 2023-24 = +0,87), définition (moyenne 72 h vs 3 derniers règlements), rééquilibrage (24 h en tranches chevauchantes vs 24 h fixe), et le fait que le « net » de R1 inclut le funding *encaissé* directement (+5,6 %/an de funding reçu selon les colonnes fund_ann). Sur la fenêtre commune, mon recalcul donne un brut+funding R1 de +0,28 (contre +0,72 rapporté par R2) et un net de −0,32 : les deux convergent vers « net négatif » une fois la fenêtre alignée.
2. **Force relative** : R1 brut 0,63 vs R2 0,16 ; sur la fenêtre commune R1 = 0,69 : la divergence n'est donc pas due à la période mais à la construction (R1 : z normalisé et clip ; R2 : rang neutre, réajustement sans chevauchement) et surtout à un effet de bruit d'univers que R2 mesure (0,91 sur 5 actifs vs 0,16 sur 10).
3. **Renversement 4 h, taker, choc de liquidité, saisonnalité** : bruts de signe opposé sur la même fenêtre (ex. saisonnalité R1 −0,33 vs R2 +0,85 ; renversement −0,33 vs +0,38 ; taker +0,01 vs +0,61 ; choc de liquidité −0,59 vs +0,45). Deux causes : (a) définitions différentes (P13 R1 est une moyenne 60 j de même heure sur H=4 avec sizing TS ; P14 R2 est un t-stat expansif à rotation horaire), (b) tranches chevauchantes vs pas d'overlap, qui changent le rythme d'exécution des signaux courts. Ces écarts de ±0,5 à ±1 sur des Sharpe bruts sont de l'ordre de l'erreur type (≈ 0,5-0,6), ce qui confirme qu'ils sont du bruit.
4. **Nombre de succès « brut »** : R1 : 0 primitive à t brut primaire ≥ 2 ; R2 : 4 « GROSS_INFORMATION_ONLY ». La différence vient d'un **standard statistique différent**, pas d'une découverte : R2 accepte p unilatéral ≤ 0,10 par bootstrap ou (brut>0 des deux côtés ∧ placebo ≤ 0,10) sans correction de multiplicité (≈ 1,5 succès attendus par hasard sur 15) ; R1 exige t Newey-West ≥ 2 pour le net et BH.
5. **Étiquettes « non redondant » et « dépendant du régime »** : R1 = 0/0 (règles conditionnées à un support net), R2 = 4/4 (règles appliquées au brut, sans correction). Ce n'est pas un désaccord empirique mais de définition.
6. **P07 carry couvert** : présent seulement dans R2 (net +0,64 sur 4 % d'activité, inactif en HOLDOUT). Aucune contrepartie en R1 → pas de réplication. Le sujet « carry couvert » reste donc **non répliqué**.
7. **Chiffres de saisonnalité nette** : R1 −3,62 vs R2 −11,58 : R2 fait 4 410 rotations/an contre ≈ 1 777 en R1 (recalcul), par conception d'un signal réévalué toutes les heures avec poids t-stat ± 1.
8. **Univers cross-lieu** : R1 utilise 9 actifs Coinbase ; R2 5 actifs sur 4 lieux plus Hyperliquid/Kraken (mais fenêtres courtes). R2 documente mieux l'universalité du prix entre lieux (corrélation Kraken 0,995-0,999), R1 mesure la corrélation Binance-Coinbase (0,968 ADA à 0,9997 ETH).
9. **Contrôles de validité** : R1 a un contrôle négatif de fuite et un signal planté ; R2 a des manifestes sha256 et un bootstrap. Chacun a ce que l'autre n'a pas.

### 8.6 Points de vigilance de comparaison
- Les comptes de la même clé du bloc final ne sont pas comparables (FORWARD_SAFE, NONREDUNDANT, REGIME_DEPENDENT : voir §5.3).
- Les Sharpe de R1 sont calculés sur P&L horaire (et √8760), ceux de R2 sur P&L quotidien (√365) : petit effet de méthode (P08 : 0,71 horaire vs 0,80 journalier en R1).
- Les deux fenêtres se recoupent seulement à partir de 2024-03 ; le hold-out de R2 (2025-06→) est inclus dans le TEST de R1 (2025-01→).

### 8.7 Réplication mutuelle : verdict
Ensemble, les deux runs constituent une réplication *quasi indépendante* du même constat négatif. La partie qui **se réplique** : « les frais rendent non rentables les signaux 1-4 h ; la tendance s'affaiblit en 2025-26 ; rien ne passe ×1,5-×2 coûts ; les signaux brut sont du bruit à ±0,5 ». La partie qui **ne se réplique pas** (ou n'est testée qu'une fois) : le portage funding directionnel en net, le carry couvert (R2 seul), la saisonnalité horaire en brut (signe de sous-période opposé), les « leads » bruts individuels (P08 R1 ≈ P09 R2 en brut, ok, mais pas en tests de corrélation entre lieux).

---

## 9. Reproductibilité

### R1 (`bench/alpha_primitives_v1/README.md`)
- Dépendances : `numpy pandas scipy pyarrow requests`.
- Ordre : `fetch_binance_vision.py`, `fetch_other.py`, `fetch_hl.py` → `data_audit.py` → `run_main.py` → `lookahead_test.py` → `falsify.py` → `exploratory_followup.py` → `analysis.py` → `gen_contracts.py` / `gen_reports.py`. Depuis `py/`.
- Durée : non indiquée ; ? (le simulateur est sur ≈ 34 000 lignes horaires × 10 actifs, batterie de falsification lourde : 150 placebo + boucles).
- Fournis : code, JSON dérivés, tableaux, P&L horaire de la spécification primaire et journalier, signaux journaliers, logs de fetch ; **manquent** : données brutes (≈ 400 Mo, à re-télécharger), manifeste d'intégrité (pas de sha256). Dépend de l'instantané du 2026-09-29 (Deribit/HL/Coinbase révisables ; Binance REST bloqué → archives seulement).
- Ce que j'ai pu refaire sans données brutes : recalcul de Sharpe, t Newey-West, intensité de turnover et exposition depuis `pnl_primary.parquet` ✔ ; régénération des tables depuis les JSON.

### R2 (`bench/alpha_primitives_v1/README.md`)
- Dépendances : `numpy pandas scipy requests` (scipy pour le clustering).
- Ordre : `fetch_vision.py` → `fetch_xvenue.py` → construction du panel en pickle → `s0_tune.py` → `s1_main.py` → `s2_ortho.py` → `s3_regime.py` → `s4_cost.py` → `s5_falsify.py` (~2 min annoncé) → `s6_adjudicate.py` → `gen_reports.py` → `gen_reports2.py`.
- Fournis : code, tous les JSON dérivés (les tableaux des rapports sont générés depuis eux ✔), manifestes sha256 Binance Vision et cross-lieux. **Manquent** : P&L horaire ou quotidien (aucun parquet), données brutes (cache git-ignoré), donc pas de recalcul indépendant du Sharpe à partir des séries de P&L ; seulement des vérifications de cohérence interne entre rapports et JSON.
- Sensibilité : les API cross-lieux sont plafonnées (Gate, Hyperliquid, Kraken fenêtres courtes) et peuvent changer.

---

## 10. Implications pratiques pour AurumShift (pistes à adjuger plus tard, aucune affirmation de compatibilité)

Rien ci-dessous n'est une recommandation d'intégration ; ce sont des pistes à examiner ultérieurement, contre le vrai dépôt local (qui n'est pas connu ici).

1. **Éviter de viser les signaux 1-4 h à coûts taker** : les deux runs montrent une perte nette structurelle. À adjuger : si AurumShift dispose d'une exécution à coûts réels très bas, ce constat pourrait changer ; sinon ces familles sont mortes.
2. **Portage/funding comme variable de contexte plutôt que comme stratégie** (P06 R1, P07 R2) : à adjuger en couplant avec une capture en direct horodatée (le seul moyen d'éviter la classe `FORWARD_SAFE_WITH_RECEIPT_STAMP` problématique).
3. **Compression de volatilité → expansion** (R1 P04 / R2 P05) : seule paire avec net ≥ 0 dans les deux runs, mais ≈ 0 : à considérer comme *une porte de régime ou un déclencheur d'attention*, pas comme signal de pari.
4. **Saisonnalité horaire comme normaliseur/porte** (recommandation de R1) plutôt que directionnel.
5. **Le pipeline lui-même** (test de troncature avec contrôle négatif, placebo, signal planté, tranches chevauchantes ; bootstrap par blocs et manifestes sha256) est une pièce réutilisable pour valider un futur signal local. À adjuger : quelles parties adapter (doctrine REUSE→ADAPT).
6. **Capture forward-only** des liquidations, du funding, de l'OI avec horodatage de réception, car aucune archive publique fiable n'existe.
7. **Éviter d'inférer** que l'absence de support dans ces deux runs implique l'absence d'alpha pour AurumShift : les deux le disent.

---

## 11. Questions ouvertes et suites recommandées (classées par valeur)

1. **Trancher la collision de branches** : une seule des PR #12 / #22 doit être fusionnée (ou fusionner leurs contributions complémentaires). Suggestion : conserver #12 pour la rigueur de pré-enregistrement/contrôles de fuite, importer de #22 les manifestes sha256, le bootstrap et le carry couvert. (Valeur : élevée, décision humaine.)
2. **Test de portage couvert (spot/perp) sur 2023-2026** avec modèle de marge, capital et risque de base, sur une fenêtre plus longue que la seule DEV de R2 : la question économique la plus crédible, non répliquée.
3. **Modèle d'exécution maker/file d'attente + paliers de frais réels** pour les primitives à fort brut/fort turnover (saisonnalité, renversement, taker).
4. **Capture en direct horodatée** (funding, OI, liquidations) pour lever la limite `FORWARD_SAFE_WITH_RECEIPT_STAMP`, puis un vrai hold-out postérieur à 2026-09.
5. **Réplication à d'autres résolutions (5 min, carnet d'ordres)** pour lead-lag et déséquilibres.
6. **Étendre l'univers et retirer le survivorship** (actifs délistés) et tester sur un jeu de coûts mesurés.
7. **Corriger les petits écarts** : documenter que `pnl_primary.parquet` est bien commité (R1), aligner la prose et le code sur le choix de z pour P12 (R2), calculer et stocker le funding moyen DEV/HOLDOUT (R2), documenter la date de départ de Gate (R2).
8. **Uniformiser les définitions des blocs finaux** avant toute agrégation (FORWARD_SAFE, NONREDUNDANT, REGIME_DEPENDENT).

---

## 12. Index des fichiers lus

### Racine et dépôt
- `claude.md` : doctrine (lue en partie, début).
- PR #12 et #22 (métadonnées via l'API) : titres, dates, commits, statut brouillon.

### Run 1 (`origin/claude/alpha-primitives-v1`)
- `reports/011_alpha_primitives/00_EXECUTIVE_SUMMARY.md` : résumé + bloc final.
- `01_LANDSCAPE.md` : paysage des sources (lu en-tête, tableau des familles, début de l'annexe A ; annexes détaillées survolées via titres — **partiellement non lu**).
- `02_PRIMITIVE_CONTRACTS.md` : contrats pré-déclarés + règles d'adjudication, 15 primitives et 19 non exécutées.
- `03_FORWARD_SAFETY.md` : classes de sûreté et test de troncature.
- `04_PUBLIC_DATA.md` : sources et couverture.
- `05_RESULTS.md` : tables primaires, économie, spécifications secondaires.
- `06_ORTHOGONALITY.md` : corrélations, clusters, persistance.
- `07_REGIME_CONDITIONAL.md` : tables par régime.
- `08_COST_SENSITIVITY.md` : multiplicateurs de coût.
- `09_FALSIFICATION.md` : batterie et suivi exploratoire.
- `10_ADJUDICATION.md` : critères, dispositions, bloc final.
- `11_LIMITATIONS.md` : 13 limites.
- `bench/alpha_primitives_v1/README.md`, `.gitignore`.
- `py/lib.py` (simulateur, statistiques), `py/primitives.py` (15 signaux), `py/run_main.py`, `py/falsify.py`, `py/lookahead_test.py`, `py/analysis.py` (adjudication), `py/exploratory_followup.py`, `py/data_audit.py` (en-tête), `py/fetch_other.py` (en-tête) ; `catalog.py`, `gen_contracts.py`, `gen_reports.py`, `fetch_binance_vision.py`, `fetch_hl.py` : **non lus intégralement** (grep ciblé pour `gen_reports.py`).
- `results/main_results.json` (58 spécifications), `falsification.json`, `falsification_table.json`, `adjudication.json`, `regime_table.json`, `cost_table.json`, `exploratory_followup.json`, `lookahead_test.json`, `data_audit.json`, `final_block.txt`, logs (`run_main.log` en partie, `falsify.log`, `lookahead_test.log`, `analysis.log`, `fetch_*.log`), `pnl_primary.parquet` (relu et recalculé), `pnl_primary_daily.parquet`, `signals_daily.parquet` (**non lu**), `tables/*.md` (structure vérifiée via le script de génération), `all_specs_table.json`, `primary_table.json` (via analysis).

### Run 2 (`origin/claude/amazing-pasteur-o4csin`)
- `reports/011_alpha_primitives/00` à `11` : résumé, paysage (01), contrats (02 : 15 exécutées lues intégralement, début des non exécutées), sûreté (03), données (04), résultats (05), orthogonalité (06), régimes (07), coûts (08), falsification (09), adjudication (10), limites (11). La fin de `02_PRIMITIVE_CONTRACTS.md` (D07-D28) : **non lue**.
- `bench/alpha_primitives_v1/README.md`, `.gitignore`.
- `py/alpha_lib.py`, `py/common.py`, `py/primitives.py`, `py/s0_tune.py`, `py/s1_main.py`, `py/s2_ortho.py`, `py/s3_regime.py`, `py/s4_cost.py`, `py/s5_falsify.py`, `py/s6_adjudicate.py` ; `fetch_vision.py`, `fetch_xvenue.py` (en-têtes) ; `catalog.py` (en-tête + grep) ; `gen_reports.py`, `gen_reports2.py` (grep ciblé) : non lus intégralement.
- `results/final_block.txt`, `s0_tune.json`, `s1_main.json`, `s2_ortho.json`, `s4_cost.json`, `s5_falsify.json`, `s6_adjudication.json`, `vision_manifest.json` et `xvenue_manifest.json` (structure lue seulement), `s3_regime.json` (**non lu directement** ; résultats via `s6_adjudication.json` et le rapport 07).
