# Analyse approfondie — Lane 006 : Intelligence des coûts d'exécution et de transaction (PR #7 ouverte)

Auteur de l'analyse : Claude (analyste de recherche), le 2026-09-29.
Lecteur visé : Jean-François, qui ne connaît ni GitHub ni le trading quantitatif. Chaque terme technique est expliqué à sa première occurrence.

Conventions de lecture de ce document :
- « Le rapport affirme » = ce qui est écrit dans les rapports du dépôt.
- « J'ai vérifié » = j'ai relu ou recalculé le chiffre à partir d'un fichier de résultats bruts, d'un fichier de données brutes ou du code. Marques : ✔ vérifié, ✘ écart, ? non vérifiable.
- Les labels du dépôt (voir section 1) : PROVEN, OBSERVED, DOCUMENTED_CLAIM, INFERENCE, UNKNOWN. Quand j'ajoute un jugement à moi, je l'écris « (mon analyse) ».
- Tous les chemins sont relatifs à la racine du dépôt. J'ai lu la branche `origin/claude/execution-cost-intelligence-v1` sans la checkout : extraction par `git archive` dans mon dossier temporaire, puis lecture et exécution sur cette copie. Aucune branche existante n'a été modifiée, rien n'a été poussé. Le seul fichier écrit dans le dépôt est celui-ci.
- Point d'attention : cette lane est la plus « numérique » que j'aie lue. Presque tous les tableaux des rapports sont générés automatiquement à partir des fichiers de résultats (voir section 9). J'ai donc pu prouver que « rapport = résultats », mais la vraie question est « résultats = réalité ? », et là, les limites sont importantes (section 7).

---

## 0. Fiche d'identité

| Élément | Valeur | Source |
|---|---|---|
| Lane | 006 — Intelligence des coûts d'exécution et de transaction (« execution cost intelligence ») | `reports/006_execution_cost_intelligence/` |
| Branche | `origin/claude/execution-cost-intelligence-v1` (une seule branche, pas de variante « -b ») | `git branch -r` |
| Pull request (PR) | n° 7, « research(exec-cost): external execution & transaction-cost intelligence V1 — LIMITED_EXECUTION_MODELS_SUPPORTED ». **État : ouverte, en brouillon (`draft: true`), non fusionnée**, créée le 2026-09-29 à 14:05:01 UTC, 1 commit, 141 fichiers modifiés, +72 117 lignes, `mergeable_state: clean` | API GitHub (PR #7) |
| Commit unique | `76d94ff`, auteur `Claude <noreply@anthropic.com>`, 2026-09-29 14:04:49 UTC | `git log` |
| Parent du commit | `9100649` = fusion de la PR #4 (lane 004). Attention : `main` a avancé depuis (`1a449df` = fusion de la PR #6). La branche n'a donc pas les commits de la lane 005/006-risque, mais GitHub la dit « clean » (aucun conflit) car elle n'ajoute que de nouveaux dossiers | `git merge-base`, API GitHub |
| Fichiers de la lane | 141 : 15 rapports (00 à 14) dans `reports/006_execution_cost_intelligence/` + 126 fichiers dans `bench/execution_cost_v1/` | `git ls-tree` |
| Taille | 12 018 171 octets (~11,5 Mio) : rapports 242 403 octets (2 627 lignes) ; données brutes `bench/execution_cost_v1/data/` 10 227 248 octets ; le reste = code, résultats, sondes OSS | `git ls-tree -l` |
| Nature des données | Mixte : (a) un monde **synthétique** inventé par le code (le « banc »), (b) des captures **réelles publiques** d'environ 50 min + 8 min le 2026-09-29 (13:00:59 → 13:59:16 UTC) sur OKX, Coinbase, Kraken, (c) des historiques publics Binance Vision, OKX (funding, dérivés), (d) des chandelles horaires Yahoo pour FX/or/pétrole. **Aucun ordre réel n'a été passé** | `05`, `14`, mes lectures des `jsonl.gz` |
| Verdict final | `FINAL_VERDICT=LIMITED_EXECUTION_MODELS_SUPPORTED` | `00_EXECUTIVE_SUMMARY.md` |
| Force du verdict (mon analyse) | **Modérée pour le périmètre étroit (ordres « au marché » sur BTC/ETH/SOL, coûts de détention), faible à nulle au-delà.** Raisons : une seule fenêtre de 50 minutes, aucun ordre réel, un monde synthétique construit par l'auteur, des « biais faibles » qui sont en partie mécaniques (section 7). Le libellé « LIMITED » est honnête et bien calibré ; ce sont certains titres internes (« near-unbiased », « executed and falsified 40 of 51 ») qui vendent un peu plus que les preuves | sections 3, 7 |
| Ce que j'ai refait moi-même | J'ai relancé le banc synthétique, les analyses des captures live/deep, les tests de contrat comptable et le générateur de rapports sur une copie : **21 fichiers de résultats et les 15 rapports sont identiques au bit près** aux fichiers de la branche (seule la colonne « µs par prédiction », un chronométrage, varie). Détails en section 9 | mon exécution |

### Petit lexique (à consulter en lisant)

- **bps (basis points, « points de base »)** : 1 bps = 0,01 %. Un coût de 5 bps sur 100 000 USD = 50 USD.
- **Ordre « au marché » (market order)** : tu achètes tout de suite au prix disponible. **Ordre « limite » (limit order)** : tu poses un prix et tu attends qu'on vienne te le prendre.
- **Taker / maker** : le taker prend la liquidité (ordre au marché), le maker en fournit (ordre limite posé). Les bourses font payer plus cher le taker que le maker.
- **Carnet d'ordres (order book), niveaux L1 / L2** : la liste des offres d'achat (bid) et de vente (ask) en attente. L1 = seulement le meilleur prix de chaque côté. L2 = plusieurs niveaux de prix avec les quantités. « Marcher dans le carnet » (book walk) = calculer le prix moyen que tu obtiendrais en consommant les niveaux successifs pour un montant donné.
- **Mid** : milieu entre meilleur achat et meilleure vente. **Spread** : écart entre les deux. **Demi-spread** : la moitié, ce que tu paies en traversant. **Tick** : plus petit pas de prix.
- **Slippage (glissement)** : écart entre le prix visé et le prix obtenu. **Impact de marché** : effet de ton propre ordre sur le prix.
- **Adverse selection (sélection adverse)** : quand ton ordre limite n'est exécuté que quand le prix va contre toi.
- **Latence / staleness** : délai entre ce que tu vois et ce qui s'exécute ; « stale » = périmé.
- **Funding (financement) d'un perpétuel** : un « perp » est un contrat dérivé crypto sans échéance ; toutes les 8 h, les acheteurs paient les vendeurs (ou l'inverse) un taux pour que son prix reste près du spot. **Borrow** : intérêts pour emprunter un actif à vendre à découvert. **Roll** : passage d'un contrat à échéance au suivant.
- **OHLCV** : bougies (ouverture, haut, bas, clôture, volume). **PAPER** : mode de simulation d'AurumShift sans argent réel.
- **Synthétique** : données fabriquées par un générateur dont on connaît la « vérité ». Utile pour tester des formules, sans valeur de preuve sur le marché réel.
- **Bootstrap par blocs** : technique statistique pour donner une marge d'erreur (intervalle de confiance, IC) quand les observations se ressemblent d'un instant à l'autre.

---

## 1. Mission et question posée

### 1.1 Question, reformulée simplement

Quand AurumShift simule des transactions en mode PAPER (sans argent réel), il faut que la simulation facture des **coûts réalistes** : écart achat/vente, glissement quand on achète un gros montant, effet de son propre ordre, risque que l'ordre ne soit pas exécuté ou le soit trop tard, frais de financement d'un perpétuel, coût d'emprunt, coût de passage d'un contrat au suivant. Le rapport `00` pose la question ainsi : *quelles primitives d'exécution et de coût de transaction sont assez fondées et assez pratiques pour être évaluées plus tard, localement, dans AurumShift PAPER ?* Domaine : crypto spot/perpétuels, FX, or, matières premières, intraday, pas de haute fréquence (HFT).

Autrement dit : « si on veut arrêter de supposer que les transactions se font gratuitement au prix milieu, quelle est la façon la plus honnête, la plus simple et la moins chère de facturer les coûts ? ». La lane ne construit rien pour AurumShift : elle regarde ce que la littérature, les outils open source et des données publiques permettent de dire.

### 1.2 Sous-questions traitées (familles A à L du rapport `02`)

A. mesure du spread ; B. glissement (slippage) ; C. impact de marché ; D. probabilité d'exécution d'un ordre limite ; E. exécutions partielles ; F. sélection adverse ; G. choix maker/taker ; H. découpage d'ordres (TWAP/VWAP/POV) ; I. latence ; J. funding/emprunt/roll ; K. fragmentation entre bourses ; L. « implementation shortfall » (le cadre comptable qui décompose le coût total).

### 1.3 Contraintes du dépôt (`claude.md`)

- Doctrine **REUSE → ADAPT → WRAP → COMPOSE → CUSTOM LAST** (réutiliser d'abord, écrire du sur-mesure en dernier). Ici : les rapports préfèrent de petites primitives de référence (formules, un « grand livre » de coûts) et rejettent l'idée d'un modèle clé en main ; aucun des 21 dépôts open source sondés n'est proposé comme dépendance d'exécution (`03`, `13`).
- Labels **PROVEN / OBSERVED / DOCUMENTED_CLAIM / INFERENCE / UNKNOWN** : utilisés partout dans `01`, `02`, `09`, `14`. Bon point : les formules de la littérature écrites de mémoire sont marquées `[M]` (« from memory ») et le rapport `02` demande qu'elles soient re-vérifiées avant tout usage.
- « Ne pas fabriquer de résultats de benchmark », « ne jamais prétendre à la compatibilité avec AurumShift » : respectés dans la lettre (`00`, `14` §11 : « nothing here licenses using it in production or inside AurumShift »).
- Contraintes AurumShift : recherche seulement / paper seulement, pas de capital réel, PIT (point-in-time, pas de regard vers le futur) critique, intraday plutôt que HFT, « le manque de preuve n'est pas une preuve négative », « les coûts de marché réalistes comptent ». Cette lane répond directement à l'avant-dernière.
- Mode annoncé : `EXTERNAL_RESEARCH_ONLY`, aucun code privé AurumShift.

### 1.4 Ce que la lane ne prétend pas faire

Elle ne mesure pas de coûts réalisés (aucun ordre passé), n'évalue pas de stratégie, ne teste rien de HFT (WebSocket L3, files d'attente fines). Elle le dit elle-même (`14` §1, §9).

---

## 2. Méthode

### 2.1 Vue d'ensemble : cinq briques de preuve

| Brique | Nature | Fichiers principaux | Poids comme preuve (mon analyse) |
|---|---|---|---|
| 1. Paysage de la littérature (A–L) | Notes sourcées, formules, avec provenance `[V]` vérifié en session / `[M]` de mémoire | `02_MODEL_LANDSCAPE.md`, `oss_probe/landscape_notes.md` | Documentaire ; les `[M]` sont faibles par nature |
| 2. Sonde open source | 21 dépôts clonés et lus (source, pas README), 9 exécutés en test de fumée | `03_OSS_COMPONENTS.md`, `oss_probe/oss_findings.{json,md}` | Bonne pratique (`claude.md` §2-3), mais le résultat de la sonde n'est pas reproductible depuis le dépôt (clones dans `/tmp`) |
| 3. Banc synthétique | Un « monde » fabriqué avec vérité connue ; 14 scénarios, ordres uniques, découpés, concurrents, latence, fragmentation, fills passifs | `synthetic/synth.py`, `synthetic/run_synth.py`, `models/models.py` | Fort pour tester la cohérence interne ; **faible pour dire ce que fait le marché** |
| 4. Captures publiques réelles | Carnets et transactions OKX/Coinbase/Kraken, 3 actifs, ~50 min + 8 min ; Binance Vision ; OKX funding/dérivés ; chandelles horaires FX/or/WTI | `capture/live_capture.py`, `analysis/*.py`, `data/*` | Réel mais court (une fenêtre, un jour) et sans ordre propre |
| 5. Contrat comptable | Un « grand livre » du coût d'un ordre, avec états MEASURED/ESTIMATED/UNKNOWN…, testé | `contract/cost_contract.py`, `contract/tests_and_threats.py` | Cohérence algébrique seulement (section 6/7) |

### 2.2 Données et univers

- **Live** (`data/live`, 29 fichiers) : 2026-09-29 de 13:00:59 à ~13:51 UTC. OKX (spot BTC/ETH/SOL-USDT + perpétuels BTC/ETH-USDT-SWAP), Coinbase Exchange (BTC/ETH/SOL-USD), Kraken (XBT/ETH/SOL-USD). Chaque série : carnet REST toutes les ~2,0–2,5 s (25 niveaux), transactions récentes avec côté de l'agresseur. Nombre de photos du carnet : 1 264 (OKX) / 1 498 (Coinbase) / 1 483 (Kraken). Latence de requête (RTT) médiane : OKX 275–278 ms, Coinbase 76–166 ms, Kraken 161–164 ms (`05` §1).
- **Deep** (`data/deep`) : juste après (13:51:18 → 13:59:16), 400 niveaux de carnet, 192 photos (OKX) / 240 (Coinbase, Kraken). Utile pour marcher dans le carnet jusqu'à 3 M USD.
- **Binance Vision** (`data/vision`, seulement funding + `bookDepth` sont dans le dépôt ; les gros fichiers `aggTrades_*.zip` et `klines_*.zip` sont dans `.gitignore`) : transactions BTC 2026-09-20 à 23 (4 316 070 transactions), ETH 09-21/22 (2 383 021), klines 1 minute BTC juin–août, ETH août, funding mai–août 2026, profondeur de carnet lointain du 09-20. Rôle : étalonnage historique seulement.
- **OKX API publique** : historique de funding (~3 mois, 277 règlements), courbe des futures datés BTC-USD (6 échéances), taux d'emprunt de base.
- **Yahoo (endpoint non officiel)** : chandelles horaires sur 6 mois (2026-03-29 → 2026-09-29) pour or COMEX (GC=F), EURUSD, USDJPY, WTI (CL=F), BTC-USD en contrôle. Utilisé uniquement pour la volatilité et les sauts de session (pas de cotes, donc **aucun modèle de coût FX/or/matières n'est calibré**).
- Non atteignables depuis le bac à sable : Binance live (HTTP 451), Bybit (403).

### 2.3 Simulateur (monde synthétique) — paramètres exacts

Défini dans `synthetic/synth.py`, classe `Scenario` :

| Élément | Valeur de base |
|---|---|
| Prix milieu | marche aléatoire arithmétique en bps, σ = 0,9 bps/√s (≈ 50 % de volatilité annuelle), dérive optionnelle, retour à la moyenne (OU) optionnel, un saut optionnel |
| Carnet | profondeur cumulée `C(x)=A·x^β`, A = 4×10⁵ USD par bps^β, β = 1,5 (« convexe »), grille de 0,25 bps sur 600 bps, bruit log-normal (écart-type 0,35), persistance 0,7 entre le carnet observé et le carnet exécuté |
| Spread | 1 bp constant (×3 dans « withdraw ») |
| Impact propre | noyau propagateur `G(τ)=λ[φ+(1−φ)(1+τ/τ0)^−γ]` par million USD, λ=0,4 bps, φ=0,4, τ0=30 s, γ=0,5 ; épuisement du carnet qui se reconstitue à ρ = 0,05/s |
| Latence | uniforme ±50 % autour de la moyenne du scénario (0,5 s par défaut) |
| Frais | taker 5 bps / maker 2 bps (ou 10/8 pour la sensibilité), traités comme une ligne à part et exclus des comparaisons de modèles |
| Volume quotidien | V_day = 2×10⁹ USD (pour les modèles en racine carrée) |

Scénarios : entraînement (TRAIN) = `base, deep, hivol, lovol` ; test (TEST, dits « held-out ») = `shallow, withdraw, trend, meanrev, gap, wall, fragmented, concave_book, coupled_hivol, coupled_lovol` (10). Tailles d'ordre : 1 000, 10 000, 100 000, 1 000 000, 10 000 000 USD. 300 essais par cellule (`NT=300`).

Paramètres des scénarios de test (`run_synth.py` l.17–31) : `shallow` A=3×10⁴, spread 4 bps, V_day 1,5×10⁸ ; `withdraw` profondeur ×0,15 et spread ×3 après la photo ; `trend` dérive 0,5 bps/s, latence 3 s ; `meanrev` κ=0,15/s, latence 5 s ; `gap` saut de 15 bps, latence 1 s ; `wall` mur à 10 bps, épaisseur 0,03 ; `fragmented` 4 bourses ; `concave_book` β=0,5, A=2×10⁶ ; `coupled_hivol` σ=2,7, A=1,33×10⁵, spread 3 ; `coupled_lovol` σ=0,3, A=1,2×10⁶, spread 0,5.

### 2.4 Protocole : splits, pré-enregistrement, gel des paramètres, graines

- **Pas de pré-enregistrement formel** (aucun fichier de protocole daté avec hypothèses et seuils figés avant les calculs). Le rapport `12` parle d'hypothèses « pre-registered-in-spirit » : c'est une formule, pas un dépôt d'hypothèses. À dire clairement : *les seuils de décision ci-dessous sont des règles d'interprétation, pas des critères figés avant de voir les données.*
- **Synthétique** : calibrage des paramètres scalaires de chaque modèle par moindres carrés sur la moyenne de la vérité des 4 scénarios TRAIN × 5 tailles ; évaluation sur TRAIN et sur les 10 scénarios TEST. Paramètres ajustés (`results/single_params_timing.json`) : constante fixe c = 1,6470 bps ; spread-proportionnel k = 3,2940 ; vol-scalé a = 0,6499 ; taille/profondeur b = 0,2059 ; racine carrée Y = 0,11683 avec repli de demi-spread 0,5 bps.
- **Graines** : toutes les expériences utilisent `numpy.random.default_rng(seed)` avec graines fixes : ordres uniques `1000 + décalage + indice_scénario×10 + log10(N)` ; découpés `7 + 3·log10(N) + tranches` ; concurrents 11/12 ; latence 21/22 ; fills complets 61 ; ordres limites 31 ; estimateurs de spread `int(spread×100+σ×10+durée_bougie)`. Le test de stabilité relance 5 jeux de graines (décalages 0, 100, 200, 300, 400).
- **Live** : calibrage sur la 1re moitié de la capture, test sur la 2e (`empirical_live.py` l.132–147) ; **leave-one-series-out** (calibrer sur 8 séries venue×actif, prédire la 9e ; `analysis/transport_loo.py`) ; bootstrap par blocs de 20 photos, 400 rééchantillonnages, graine 5 pour l'IC du marquage post-exécution.
- **Gel** : les modèles sont ajustés sur TRAIN puis figés avant d'être évalués sur TEST (le code ne réajuste pas). Mais le scénario `concave_book` a été ajouté *après* avoir vu la concavité du carnet live (`04` §2 le dit) : il est « test » sur le papier, pas en aveugle.

### 2.5 Critères de décision (seuils exacts cités)

Les verdicts de `13` sont qualitatifs, pas des seuils chiffrés. Les règles chiffrées effectives sont :

- Un modèle est « supporté » s'il a été **exécuté et non falsifié** dans le régime de données et la plage testés (`14` §11).
- Sonde OSS : critères = licence, activité, dépendances, exécution en test de fumée, adéquation non-HFT (`03`).
- Portées chiffrées : couverture de profondeur visible **≥ 95 %** pour inclure une série dans le test de transport (`transport_loo.py`) ; « **≥ 1 000 barres** » pour utiliser EDGE comme borne (`06` §5, `13` n°8, non testée : c'est un choix d'auteur, les tests Vision utilisent ≥ 1 000 minutes par jour) ; bande **±50–100 %** et **queue 3–5×** pour le prior racine carrée (dérivés des erreurs de transport LOO : médiane 36–53 %, pire 3–5,5×) ; « diffs < ~0,1 bps dans les tables live = bruit » (`14` §10) ; règle maker/taker `P* = X/(X+2·hs+Δfee)` (`10` A.1) avec verdict `MAKER_TAKER_UNDECIDABLE` quand la fourchette [P_lower, P_upper] contient P*.
- Étiquetage des falsifications : FALSIFIED / SURVIVED / PARTIAL / INCONCLUSIVE / CIRCULAR (`12`).

### 2.6 Ce qu'aucune de ces méthodes ne contient

Pas de test statistique formel avec correction pour tests multiples (`14` §10 le dit), pas d'intervalles de confiance sur la plupart des tableaux live (seulement pour le marquage post-exécution), pas de validation contre des exécutions réelles.

---

## 3. Résultats détaillés

Règle de lecture : chaque tableau est reproduit depuis le rapport correspondant. J'ai prouvé (section 9) que ces tableaux sont exactement ceux que produisent les fichiers de résultats. Le fichier de résultats est cité entre parenthèses. « ✔ » = revérifié par mes soins (voir aussi la section 3.13, le registre de vérification).

### 3.1 Rapport `01` — Matrice de menaces E1 à E15 (`results/threat_matrix_and_contract_tests.json`)

Idée : on compare ce que facturerait un simulateur PAPER **naïf** (sans frictions) à ce que vaut le coût « correct » selon le monde synthétique ou des données publiques. Unité : bps du notionnel ; positif = coût pour le trader.

| id | menace | naïf | « correct » | erreur | unité |
|---|---|---|---|---|---|
| E1 | remplir au prix milieu | 0,00 | 0,81 | −0,81 | bps |
| E2 | spread nul | 0,00 | 0,50 | −0,50 | bps |
| E3 | pas de glissement (spread seul, 1 M USD) | 0,50 | 1,68 | −1,18 | bps |
| E4 | liquidité infinie (50 M USD, livre mince) | 0,50 | 360,56 | −360,06 | bps |
| E5 | cote périmée (tendance, latence 3 s) | 0,00 | 1,63 | −1,63 | bps |
| E5b | cote périmée à travers un saut | 0,00 | 13,58 | −13,58 | bps |
| E6 | exécution complète malgré profondeur insuffisante | 1,00 | 0,88 | 0,12 | fraction exécutée |
| E7 | pas de sélection adverse (passif toujours exécuté au touch) | 1,50 | 4,24 | −2,74 | bps |
| E8 | funding omis (perp long tenu 7 j, BTC, mai–août 2026) | 0,00 | 9,35 | −9,35 | bps |
| E9 | emprunt inconnu traité comme zéro | 0,00 | n/a | n/a | bps |
| E10 | roll ignoré (OKX BTC-USD 261127 → 261225, long) | 0,00 | 33,81 | −33,81 | bps |
| E11 | latence ignorée (marche aléatoire, 5 s) | 0,00 | 2,01 | −2,01 | bps (1 écart-type ; moyenne ≈ 0) |
| E12 | la cote disparaît (profondeur ×0,15, spread ×3) | 1,68 | 5,51 | −3,83 | bps |
| E13 | ordre au marché traversant plusieurs niveaux (10 M USD) | 0,50 | 5,72 | −5,22 | bps |
| E14 | 5 ordres simultanés de 500 k USD chiffrés indépendamment | 2,28 | 5,65 | −3,37 | bps/ordre |
| E15 | 5 ordres répétés à 1 s d'intervalle | 2,28 | 5,10 | −2,82 | bps/ordre |

Ce que ça veut dire : même avec un demi-spread de 0,5 bps, un comptable sans friction sous-facture de 0,8 bps (100 000 USD) à 5 bps (10 M USD). L'erreur dépend de la taille, donc une correction constante ne suffit pas. E4 : avec un carnet mince, « liquidité infinie » sous-estime un ordre de 50 M USD de ~360 bps. E14 : 5 ordres de 500 000 USD *en même temps* sur le même côté paient 5,65 bps chacun, pas 2,28 (facteur 2,5). E15 : 5 ordres espacés de 1 s coûtent 5,10 contre 2,28 (facteur 2,2). ✔ vérifié (fichier identique après relance). Attention : « correct » veut dire « vérité du monde synthétique » sauf E8/E10 (données publiques réelles) ; E11 est un écart-type, pas un coût (le rapport le précise). E9 n'a volontairement pas de valeur correcte.

### 3.2 Rapport `04` — Banc synthétique

**(a) Décomposition de la vérité** (`results/truth_decomposition.csv`, moyenne de 300 essais, `IS_se` = erreur standard). IS = coût total ; « drift » = dérive du prix pendant la latence. Extraits :

| scénario / taille | IS | dérive | demi-spread | walk (marche) | impact | exécuté | IS_se |
|---|---|---|---|---|---|---|---|
| base / 1e4 | 0,65 | 0,03 | 0,50 | 0,12 | 0,00 | 1,00 | 0,04 |
| base / 1e6 | 1,59 | −0,03 | 0,50 | 1,12 | 0,00 | 1,00 | 0,04 |
| base / 1e7 | 5,60 | −0,03 | 0,50 | 5,14 | 0,00 | 1,00 | 0,04 |
| shallow / 1e4 | 2,24 | −0,06 | 2,00 | 0,30 | 0,00 | 1,00 | 0,04 |
| shallow / 1e6 | 8,26 | 0,02 | 2,00 | 6,24 | 0,00 | 1,00 | 0,04 |
| shallow / 1e7 | 30,80 | −0,01 | 2,00 | 28,81 | 0,00 | 1,00 | 0,05 |
| withdraw / 1e6 | 5,43 | −0,02 | 1,50 | 3,95 | 0,00 | 1,00 | 0,04 |
| withdraw / 1e7 | 19,58 | −0,07 | 1,50 | 18,16 | 0,00 | 1,00 | 0,04 |
| trend / 1e6 | 3,15 | 1,54 | 0,50 | 1,11 | 0,00 | 1,00 | 0,10 |
| gap / 1e4 | 13,86 | 13,23 | 0,50 | 0,12 | 0,00 | 1,00 | 0,28 |
| gap / 1e7 | 19,08 | 13,43 | 0,50 | 5,15 | 0,00 | 1,00 | 0,26 |

L'« identité de l'échelle » (IS = timing + spread + walk + impact) a un résidu maximal de 0,0 partout. **Attention (mon analyse) : c'est une tautologie du code, voir 6.3.**

**(b) Ordre unique au marché : 12 modèles comparés** (`results/single_orders.csv`, relancé identique). « Biais » = moyenne(prédiction − vérité), frais exclus, en valeur absolue moyennée sur (scénario, taille). Entraînement ("train") = 4 scénarios ; test = 10 scénarios.

| modèle | données requises | |biais| train | |biais| TEST | TEST hors gap+withdraw | gap+withdraw seuls | RMSE train | RMSE TEST |
|---|---|---|---|---|---|---|---|
| E1 remplissage au mid | OHLCV | 1,65 | 5,00 | 3,59 | 10,62 | 2,00 | 5,36 |
| 5 bps par défaut | OHLCV | 3,55 | 4,73 | 4,04 | 7,49 | 3,74 | 5,06 |
| bps fixe calibré | OHLCV | 1,26 | 4,00 | 2,75 | 8,97 | 1,68 | 4,52 |
| demi-spread seul (E3) | L1 | 1,15 | 4,27 | 2,81 | 10,12 | 1,67 | 4,79 |
| proportionnel au spread | L1 | 1,26 | 4,01 | 2,77 | 8,97 | 1,68 | 4,48 |
| échelonné à la volatilité | L1 | 1,19 | 4,00 | 2,62 | 9,53 | 1,59 | 4,51 |
| taille/profondeur (L1 + 1 bp) | L1 | 0,25 | 7,05 | 6,59 | 8,92 | 0,98 | 7,83 |
| racine carrée (OHLCV seul) | OHLCV | 0,67 | 3,65 | 2,19 | 9,48 | 1,27 | 4,18 |
| racine carrée (avec spread L1) | L1 | 0,67 | 3,42 | 1,90 | 9,48 | 1,27 | 4,02 |
| marche du carnet, 20 bps visibles | L2 top20 | 0,04 | 2,48 | 0,91 | 8,76 | 0,84 | 3,24 |
| marche 20 bps + repli racine carrée | L2 top20 | 0,04 | 2,57 | 1,02 | 8,76 | 0,84 | 3,33 |
| marche du carnet, 100 bps visibles | L2 | 0,04 | 2,13 | 0,47 | 8,76 | 0,84 | 2,92 |

En clair : « biais TEST 2,13 » veut dire que, sur des marchés synthétiques jamais vus, la marche du carnet se trompe en moyenne de 2,13 bps ; sans les deux scénarios « catastrophe » (saut de prix, retrait de liquidité) l'erreur tombe à 0,47 bps. Un modèle fixe à 5 bps se trompe de 4,73. Aucun modèle ne prédit les queues : `gap` laisse tous les modèles ≈ 13 bps trop bas, `withdraw` ≈ 4,3 à 5,6 bps trop bas.

Par scénario de test (|biais| moyen sur 5 tailles), lignes clés : marche du carnet 100 bps : concave_book 0,03 ; coupled_hivol 0,12 ; coupled_lovol 0,01 ; fragmented 1,99 ; gap 13,25 ; meanrev 0,05 ; shallow 0,04 ; trend 1,48 ; wall 0,02 ; withdraw 4,27. Taille/profondeur : wall **35,60**. Demi-spread seul : shallow 7,35 ; gap 14,61. Racine carrée (spread L1) : shallow 5,03, gap 13,97.

Biais signé par taille (extrait, bps) : `shallow`, ordre de 10 M USD : demi-spread seul −28,80 ; racine carrée (spread L1) −20,82 ; marche 20 bps −16,81 (profondeur tronquée) ; marche 100 bps +0,04. `base`, 10 M USD : demi-spread seul −5,10 ; racine carrée −2,92 ; marche +0,04. `concave_book`, 1 M USD : racine carrée **+0,56** (mauvais signe) contre marche +0,03.

**(c) Stabilité aux graines** (`results/single_seed_stability.json`, 5 jeux de graines) : le |biais| TEST bouge de ≤ 0,04 bps pour tous les modèles sauf « taille/profondeur » (0,25). Le rapport dit « ≤ 0,03 » : légère imprécision (voir 3.13). Ordre des modèles inchangé. Lecture : le Monte-Carlo est stable ; la variance est dans le choix des scénarios.

**(d) Fragmentation** (`results/latency_fragmentation.json`) : coût réel du routage intelligent sur N bourses égales vs coût estimé en ne marchant que dans le carnet d'une bourse, ordre de 1 M USD :

| bourses | vérité (routé partout) | estimation à partir d'un seul carnet |
|---|---|---|
| 1 | 2,26 | 2,26 |
| 2 | 2,26 | 3,28 |
| 4 | 2,26 | 4,91 |
| 8 | 2,26 | 7,50 |

Soit surestimation ×1,45 / ×2,17 / ×3,32 (le rapport écrit 1,4 / 2,2 / 3,3). ✔

**(e) Ordres découpés (TWAP)** (`results/sliced.json`) : ordre parent de 0,2 à 5 M USD en 1, 5 ou 20 enfants sur 600 s, 4 régimes d'impact, calibrage sur `sl_base` seul. Biais moyen absolu sur la vérité sans dérive :

| modèle | test | train |
|---|---|---|
| Almgren–Chriss linéaire | 1,13 | 0,36 |
| marches indépendantes (sans mémoire) | 0,32 | 0,19 |
| propagateur (noyau permanent seul) | 0,21 | 0,10 |
| propagateur (forme vraie, λ ajusté) | 0,21 | 0,02 |
| racine carrée totale (sans info de calendrier) | 1,33 | 0,95 |

Détail à fort impact, 5 M USD (vérité sans dérive vs prédiction, en bps) : 1 tranche : 6,74 / 6,75 pour les trois modèles à marche ; 5 tranches : 4,62 vs marches indépendantes 2,60 (−2,03), propagateur vrai 3,17 (−1,46), permanent seul 3,53 (−1,10), AC 2,67 (−1,95) ; 20 tranches : 3,91 vs 1,34 (−2,57), 2,05 (−1,86), 2,44 (−1,47), AC 2,67 (−1,23). Classement des calendriers : AC regret moyen 0,68 bps, « part correcte » 0 % ; les trois modèles à marche 0,00 bps et 100 % ; racine carrée totale regret 3,05 bps et 0 %. **Vérifié en lisant `sliced.json` : la vérité préfère 20 tranches dans les 60 cas sur 60.** Les trois modèles « à 100 % » répondent donc tous « 20 » ; le test est dégénéré (le rapport dit « weakly discriminating », c'est un euphémisme).

**(f) Ordres concurrents E14/E15** (`results/competing.json`) : voir 3.1 ; table complète : k=1 → 1,12 / 2,28 (100 k / 500 k) ; k=2 → 1,48 / 3,31 ; k=5 → 2,28 / 5,65 ; k=10 → 3,31 / 8,65 (facteurs sous-estimation 1,32 / 1,45 ; 2,03 / 2,48 ; 2,95 / 3,80). Séquentiel, 5 ordres de 500 k : intervalle 1 s → 5,10 (×2,24) ; 10 s → 3,67 (×1,61) ; 60 s → 2,59 (×1,14) ; 600 s → 2,47 (×1,09).

**(g) Latence** (`results/latency_fragmentation.json`) : dérive moyenne et écart-type selon la latence L (0,05 à 20 s) : marche aléatoire et retour à la moyenne : moyenne ≈ 0, écart-type = σ√L (0,20 → 4,03 bps) ; tendance : moyenne ≈ dérive × L (0,02 → 9,93) ; saut : moyenne ≈ 13 bps quelle que soit L, écart-type 5,04 à 6,28.

**(h) Estimateurs de spread sur bougies synthétiques** (`results/spread_estimators_synth.json`) : voir 3.4.

### 3.3 Rapport `05` — Expérience sur données publiques : ce que les données montrent

Tableau de synthèse des 9 séries (`results/empirical_live.json`, relancé identique) : spread moyen en bps (p95), part du temps à un tick, profondeur visible (25 niveaux), exposant de profondeur β médian, σ (bps/√s), nombre de transactions.

| venue | actif | photos | spread moyen | p95 | tick (bps) | profondeur visible (bps) | β | σ | transactions |
|---|---|---|---|---|---|---|---|---|---|
| OKX | BTC | 1264 | 0,012 | 0,012 | 0,012 | 1,77 | 0,31 | 0,773 | 18 050 |
| OKX | ETH | 1264 | 0,037 | 0,037 | 0,037 | 2,50 | 0,41 | 1,009 | 12 214 |
| OKX | SOL | 1264 | 0,826 | 0,828 | 0,826 | 20,23 | 0,44 | 1,355 | 18 112 |
| Coinbase | BTC | 1498 | 0,069 | 0,466 | 0,001 | 2,14 | 0,63 | 0,818 | 20 793 |
| Coinbase | ETH | 1498 | 0,287 | 0,953 | 0,037 | 3,06 | 0,55 | 1,024 | 8 879 |
| Coinbase | SOL | 1498 | 1,151 | 1,656 | 0,826 | 20,63 | 0,66 | 1,396 | 9 656 |
| Kraken | BTC | 1483 | 0,038 | 0,012 | 0,012 | 2,48 | 0,58 | 0,754 | 7 914 |
| Kraken | ETH | 1483 | 0,191 | 1,029 | 0,037 | 3,60 | 0,62 | 0,937 | 3 352 |
| Kraken | SOL | 1483 | 0,942 | 1,653 | 0,826 | 20,28 | 0,73 | 1,407 | 2 801 |

Lecture : BTC et ETH sont quasi toujours à un tick d'écart (0,012 bps sur OKX/Kraken pour BTC : c'est un « écart de 1 centime »). Le spread est un détail pour BTC/ETH, un vrai coût pour SOL (~0,8–1,2 bps). Détail curieux (Kraken BTC : moyenne 0,038 > p95 0,012) : possible si plus de 5 % des photos ont un spread élargi ; cohérent avec « one_tick_frac 0,95 ».

**Profondeur** (USD disponibles dans x bps du meilleur prix, côté vente, run 25 niveaux, médiane) : p. ex. OKX BTC 186 851 USD à 1 bp, 421 468 à 5 et 10 bps (les 25 niveaux s'arrêtent avant 10 bps) ; Coinbase SOL 8 017 / 19 294 / 54 105 / 162 124 ; Kraken BTC 765 212 / 1 033 909 / 1 303 705 / 1 304 033.

**Couplage volatilité–liquidité** (Spearman entre la volatilité récente et le spread / le coût de marche) : positif pour le spread dans les 9 séries (0,26 à 0,78) ; pour le coût de marche 10 000 USD 0,04 à 0,54, pour 100 000 USD −0,06 à 0,56. Sens : quand ça bouge, le carnet s'écarte ; mais la corrélation pour le coût de marche est faible pour SOL.

**Run profond (400 niveaux, 8 min)** — coût de marche (bps vs mid, achat au marché) selon le montant, moyenne des photos (`results/empirical_deep.json`) :

| venue | actif | 1 k | 10 k | 100 k | 300 k | 1 M | 3 M |
|---|---|---|---|---|---|---|---|
| Coinbase | BTC | 0,10 | 0,20 | 0,77 | 1,32 | 2,30 | 6,14 |
| Coinbase | ETH | 0,22 | 0,41 | 1,46 | 2,31 | 5,12 | 12,76 |
| Coinbase | SOL | 0,70 | 1,08 | 3,95 | 7,47 | 15,21 | 32,96 |
| Kraken | BTC | 0,04 | 0,10 | 0,29 | 0,41 | 1,09 | 3,23 |
| Kraken | ETH | 0,24 | 0,65 | 1,63 | 2,49 | 4,00 | 7,15 |
| Kraken | SOL | 0,73 | 0,99 | 3,62 | 5,72 | 9,98 | 20,10 |
| OKX | BTC | 0,01 | 0,05 | 0,33 | 1,06 | 2,46 | 5,25 |
| OKX | ETH | 0,03 | 0,08 | 1,15 | 2,22 | 4,00 | 7,84 |
| OKX | SOL | 0,47 | 0,63 | 2,67 | 6,37 | 17,62 | 60,63 |

Couverture (part des photos dont la profondeur visible couvre le montant) : 1,00 partout sauf OKX BTC à 3 M (0,98). **J'ai recalculé ces coûts depuis les fichiers bruts** (mon propre code) pour OKX BTC (0,33 / 2,46 / 5,25 ; couverture 1,00 / 1,00 / 0,98), Coinbase BTC (0,77 / 2,30 / 6,14), OKX SOL (2,67 / 17,62 / 60,63), Kraken ETH (1,63 / 4,00 / 7,15) : ✔ identiques. Sens : acheter 100 000 USD de BTC coûte environ 0,3 à 0,8 bps (3 à 8 USD), 1 M USD environ 1,1 à 2,5 bps ; SOL 1 M USD : 10 à 18 bps.

Forme de la profondeur (run profond, exposant β médian, p10–p90) : OKX BTC 1,00 (0,82–1,35) ; OKX ETH 1,17 ; OKX SOL 0,71 ; Coinbase BTC 1,10 ; Coinbase ETH 1,03 ; Coinbase SOL 0,77 ; Kraken BTC 0,77 ; Kraken ETH 0,87 ; Kraken SOL 0,62. Profondeur visible médiane : 12,9 bps (OKX BTC) à 614 bps (Kraken SOL). Le carnet lointain de Binance USD-M (`bookDepth` 2026-09-20) a une pente log-log de 0,8123 entre 20 et 500 bps (`results/empirical_vision.json`) ✔.

**Cross-venue** : décalage de mid entre bourses, après avoir retiré la base USDT/USD (~2 bps) : écart-type 0,86 à 1,53 bps ; le rapport insiste : ce n'est **pas** de l'arbitrage (photos décalées de 1,5 à 3 s, frais dominants). Table `05` §5 : p. ex. BTC OKX–Coinbase, moyenne 2,643 bps, sd 0,902, `frac_crossed` 0,962, p99 2,947.

**FX / or / pétrole** (chandelles horaires Yahoo ; `results/fx_gold_ohlc.json`, que j'ai recalculé depuis `data/ohlc/*.csv`) :

| instrument | barres | h/semaine | σ (bps/√s) | vol annuelle % | sauts > 3 h | |saut| moyen (bps) | saut/σ-heure |
|---|---|---|---|---|---|---|---|
| or (GC=F) | 2912 | 104,0 | 0,52 | 24,31 | 27 | 53,99 | 1,73 |
| EURUSD | 3127 | 111,7 | 0,11 | 5,03 | 26 | 11,51 | 1,78 |
| USDJPY | 3110 | 111,1 | 0,16 | 7,68 | 26 | 10,99 | 1,11 |
| WTI (CL=F) | 2908 | 103,9 | 1,25 | 58,40 | 26 | 250,18 | 3,33 |
| BTC-USD (contrôle) | 4417 | 157,8 | 0,69 | 38,80 | 0 | — | — |

✔ recalculé : σ = 0,521 / 0,108 / 0,165 / 1,252 / 0,691 ; sauts 27/26/26/26/0 ; ratio 1,73 / 1,78 / 1,11 / 3,33. Message : le monde FX/or n'est pas ouvert 24/7 (104–112 h/semaine), il a des sauts de session de l'ordre de 1 à 3 fois la volatilité horaire ; la série WTI est un contrat continu dont les rolls gonflent probablement les sauts (INFERENCE du rapport).

### 3.4 Rapport `06` — Modèles de spread

**Spread coté** : voir tableau ci-dessus.

**Spread effectif et réalisé sur photos décalées** (2·|prix−mid|, `empirical_live.json`) :

| venue | actif | coté | effectif moyen | effectif médian | réalisé 5 s | réalisé 30 s | accord du drapeau de côté |
|---|---|---|---|---|---|---|---|
| OKX | BTC | 0,012 | 0,660 | 0,012 | −1,242 | −0,752 | 0,805 |
| OKX | ETH | 0,037 | 1,267 | 0,475 | −0,760 | −0,485 | 0,811 |
| OKX | SOL | 0,826 | 1,478 | 0,827 | −1,143 | 0,127 | 0,748 |
| Coinbase | BTC | 0,069 | 0,390 | 0,001 | −0,661 | −0,369 | 0,330 |
| Coinbase | ETH | 0,287 | 1,509 | 0,587 | −0,872 | −0,670 | 0,308 |
| Coinbase | SOL | 1,151 | 1,950 | 0,827 | −0,315 | 0,169 | 0,247 |
| Kraken | BTC | 0,038 | 1,294 | 0,606 | −1,317 | −0,755 | 0,850 |
| Kraken | ETH | 0,191 | 1,432 | 0,623 | −1,230 | 0,100 | 0,787 |
| Kraken | SOL | 0,942 | 1,766 | 0,826 | 0,112 | −0,358 | 0,704 |

Rapports effectif/coté (mon recalcul, ✔) : OKX BTC ×55,7 ; Kraken BTC ×34,2 ; Coinbase BTC ×5,7 ; OKX ETH ×34,6 ; SOL ×1,7 à 1,9. Le rapport dit « 6–55× trop haut sur BTC » ✔. Explication (INFERENCE du rapport, plausible et chiffrée) : le « mid » de la photo a en moyenne 1–1,5 s de retard ; avec σ ≈ 0,8 bps/√s, l'erreur de fraîcheur attendue est σ√âge·√(2/π) ≈ 0,7 bps, ce qui correspond à 0,66 mesuré. Autrement dit, ce « spread effectif » mesure la péremption de la photo, pas le coût. Le spread réalisé à 5 s est négatif dans 8 séries sur 9 (exception Kraken SOL +0,112) ✔ : signe de sélection adverse/continuation de flux, mais contaminé par le même bruit.

**Estimateur par retournement de transaction** (Binance Vision, transactions consécutives < 5 ms de côtés opposés, `empirical_vision.json`) :

| symbole | jours | transactions | jour-USD (Md) | tick (bps) | médiane du spread lu | moyenne | part de zéros |
|---|---|---|---|---|---|---|---|
| BTCUSDT | 4 | 4 316 070 | 1,828 | 0,00117 | 0,00117 | 0,0473 | 0,0935 |
| ETHUSDT | 2 | 2 383 021 | 1,196 | 0,03651 | 0,03651 | 0,1381 | 0,1560 |

La médiane égale exactement un tick ✔ (json). Non recalculable de mon côté (les fichiers `aggTrades` ne sont pas dans le dépôt).

**Proxys sur bougies vs cotes** — bougies d'1 min construites avec les transactions live (`ohlc_proxies_1m_bps`) :

| venue | actif | barres | Corwin–Schultz | CS négatif | Abdi–Ranaldo | Roll | amplitude H/L | spread coté | effectif |
|---|---|---|---|---|---|---|---|---|---|
| OKX | BTC | 51 | 2,127 | 0,440 | 1,979 | 4,386 | 3,406 | 0,012 | 0,660 |
| OKX | ETH | 51 | 3,027 | 0,320 | 4,503 | 7,231 | 4,693 | 0,037 | 1,267 |
| OKX | SOL | 51 | 4,942 | 0,360 | 4,507 | 8,921 | 7,018 | 0,826 | 1,478 |
| Coinbase | BTC | 51 | 2,300 | 0,420 | 2,277 | 4,593 | 3,813 | 0,069 | 0,390 |
| Coinbase | ETH | 52 | 2,962 | 0,314 | 3,580 | 6,079 | 4,641 | 0,287 | 1,509 |
| Coinbase | SOL | 51 | 5,051 | 0,340 | 4,312 | 8,756 | 7,019 | 1,151 | 1,950 |
| Kraken | BTC | 60 | 1,960 | 0,424 | 1,680 | 4,566 | 3,121 | 0,038 | 1,294 |
| Kraken | ETH | 70 | 1,898 | 0,464 | 2,734 | 6,065 | 3,699 | 0,191 | 1,432 |
| Kraken | SOL | 75 | 3,216 | 0,419 | 3,591 | 9,205 | 5,794 | 0,942 | 1,766 |

Klines Binance 1 min, moyenne journalière : BTC CS 1,516 / 0,837 / 0,781 bps (juin/juil/août), AR 0,414 / 0,296 / 0,090, Roll 1,339 / 1,091 / 0,701 ; ETH août CS 1,254, AR 0,124, Roll 1,083 ; alors que le tick vaut 0,0012 bps (BTC) et 0,037 (ETH) et que la médiane par retournement égale ce tick. Sur bougies synthétiques avec spread vrai connu, CS lit p. ex. 1,2 / 3,8 / 12,4 bps pour un spread vrai de 0,2 bps à σ = 0,3 / 0,9 / 2,7 (moyenne sur bougies de 60 s et 300 s, voir 7.2).

**Ratios proxys / cote** (mon recalcul, ✘ partiel) : les proxys lisent de ×3,4 (CS Kraken SOL) à ×370 (Roll OKX BTC) la cote ; le rapport écrit « ×3 … ×700 ». Je ne retrouve pas ×700 avec ces quatre estimateurs et ces neuf séries live (maximum ×370 ; avec Binance CS/tick on dépasse ×1 000, mais ce n'est pas la même comparaison).

**EDGE** (OSS `bidask`) : sur la grille synthétique EDGE lit 5,04 pour un vrai spread 5 (σ=0,9, tick 1 bp), mais surestime les spreads ≤ 1 tick à forte volatilité (vrai 0,2 → 2,27–2,69 à σ=2,7) ; Binance klines : 0,10 / 0,06 / 0,07 bps (BTC), 0,18 (ETH) contre un tick de 0,0012 et 0,037 ; sur ~51 bougies live : instable (0,09 à 2,67 bps). Verdict rapport : borne de cohérence sur ≥ 1 000 barres, jamais une mesure.

### 3.5 Rapport `07` — Glissement (slippage) et impact

**Tableau des modèles** (entrées, hypothèses) : reproduit dans `07` §1 — mid, bps fixe, demi-spread, proportionnel au spread, échelonné à la volatilité, taille/profondeur, racine carrée `s/2 + Y·σ_jour·√(N/V_jour)`, marche du carnet.

**Capture 25 niveaux (coût de marche par montant)** — les cellules « n/a » viennent d'une profondeur visible insuffisante ; les couvertures montrent que les valeurs pour 1 M USD reposent parfois sur 1 à 4 % des photos :

| venue | actif | 1 k | 10 k | 100 k | 300 k | 1 M | 3 M | couverture à 300 k / 1 M |
|---|---|---|---|---|---|---|---|---|
| Coinbase | BTC | 0,09 | 0,21 | 0,61 | 1,09 | 0,93 | n/a | 0,92 / 0,01 |
| Coinbase | ETH | 0,19 | 0,37 | 1,44 | 1,96 | n/a | n/a | 0,26 / 0,00 |
| Coinbase | SOL | 0,83 | 1,67 | 5,24 | 9,92 | 14,66 | n/a | 1,00 / 0,04 |
| Kraken | BTC | 0,09 | 0,17 | 0,34 | 0,42 | 0,75 | n/a | 0,98 / 0,76 |
| Kraken | ETH | 0,21 | 0,52 | 1,45 | 2,01 | 2,74 | n/a | 0,85 / 0,06 |
| Kraken | SOL | 0,58 | 1,02 | 3,53 | 5,60 | 9,79 | 15,94 | 1,00 / 0,95 |
| OKX | BTC | 0,02 | 0,08 | 0,37 | 0,69 | n/a | n/a | 0,78 / 0,00 |
| OKX | ETH | 0,03 | 0,09 | 0,78 | 1,38 | n/a | n/a | 0,72 / 0,00 |
| OKX | SOL | 0,49 | 0,66 | 3,13 | 7,19 | 14,88 | n/a | 1,00 / 0,00 |

Remarque (mon analyse) : Coinbase BTC 1 M = 0,93, plus bas que 300 k = 1,09, pour 1 % de couverture ; OKX SOL 1 M = 14,88 avec couverture arrondie à 0,00. Ces valeurs sont des moyennes sur des photos exceptionnellement profondes (biais de sélection) et ne devraient pas être lues comme des coûts. Le rapport donne les couvertures dans le tableau voisin, ce qui suffit à un lecteur attentif, mais le tableau des coûts n'est pas masqué là où la couverture est < 50 %.

**Constats du rapport** (✔ = vérifié par moi) : à 100 k USD le coût de marche est 0,29–0,77 bps (BTC), 1,15–1,63 (ETH), 2,7–4,0 (SOL) ; à 1 M USD 1,1–2,5, 4,0–5,1, 10–18 ✔. Exposant local du coût en N entre 100 k et 1 M : 0,39 à 0,87, médiane 0,55 ✔ (calculé à la main à partir du tableau profond : 0,475 ; 0,545 ; 0,585 ; 0,575 ; 0,39 ; 0,44 ; 0,873 ; 0,54 ; 0,82). Un défaut à 5 bps surestime BTC à ≤ 100 k de ≥ 6× (jusqu'à ~500× à 1 k USD : 5/0,01) ✔ et sous-estime SOL à 1 M de 2 à 3,5× ✔.

**Fraîcheur du carnet** (`stale_walk_error`) : erreur de prédire le coût à t+Δ avec la photo à t ; extraits (Δ = 4 s / 30 s) : OKX BTC 100 k : erreur moyenne 0,000 / 0,011, MAE 0,386 / 0,412, coût moyen 0,368 / 0,377 ; OKX SOL 100 k : −0,001 / 0,005, MAE 0,728 / 0,813 ; Coinbase SOL 100 k : −0,008 / −0,008, MAE 1,080 / 1,299 ; Kraken SOL 1 M : −0,002 / 0,001, MAE 0,773 / 0,898. Le rapport conclut « quasi non biaisé » (|erreur moyenne| ≤ 0,05 bps live, ≤ 0,11 bps jusqu'à 300 k en profond, jusqu'à 0,53 bps à 1 M et 1,62 bps à 3 M pour OKX SOL à 30 s).

Mes recalculs (`empirical_live.json` / `empirical_deep.json`) : ✔ live Δ∈{4,30} |erreur moyenne| max 0,052 (Coinbase ETH, 300 k) ; ✔ deep ≤ 300 k max 0,107 ; ✔ deep ≥ 1 M : max 0,181 à 4 s et 1,624 à 30 s (OKX SOL 3 M) ; ✔ erreur relative maximale 13,7 % (OKX ETH deep, 10 k, 30 s), médiane 0,7 %. Nuance : le rapport écrit « MAE à 30 s seulement 7 à 20 % au-dessus de 4 s » ; sur les 92 paires série×montant le rapport MAE(30 s)/MAE(4 s) va de 0,84 à 1,96 (médiane 1,10 ; 90e centile 1,32 ; 21 paires au-dessus de +20 % ; 4 au-dessus de +50 %) ; les quatre maximaux (+55 % à +96 %) sont des cas SOL 300 k–3 M en run profond (Coinbase SOL 1 M : 1,12 → 2,19). Donc « 7–20 % » vaut pour les cas cités, pas pour toute la population.

**Le walk bat-il des constantes calibrées ?** (`baseline_vs_next_book_walk_dt4s`, 1re moitié calibrage, 2e moitié test, cible = coût de marche à t+4 s) : extraits (MAE, bps) :

| venue | actif | N | marche (photo t) | constante (moy. train) | demi-spread | prop. spread | racine carrée |
|---|---|---|---|---|---|---|---|
| Coinbase | BTC | 100 k | 0,396 | 0,319 | 0,618 | 3,535 | 0,318 |
| Coinbase | SOL | 100 k | 1,091 | 2,257 | 5,662 | 2,416 | 2,178 |
| Kraken | SOL | 1 M | 0,810 | 0,955 | 9,650 | 2,723 | 0,935 |
| OKX | BTC | 100 k | 0,436 | 0,338 | 0,399 | 0,338 | 0,338 |
| OKX | SOL | 100 k | 0,787 | 0,646 | 2,679 | 0,646 | 0,646 |

Profond : OKX SOL 3 M : marche 3,287 vs constante 13,293 vs demi-spread 66,958 ; Coinbase ETH 3 M : 1,136 vs 4,318 vs 14,824. Agrégat : **92 cellules** (série × montant × run) ; marche meilleure que la constante en MAE dans 34 cellules (37 %) ; meilleure que le demi-spread seul dans 55 (60 %) ; |biais| moyen 0,025 bps pour la marche contre 0,518 pour la constante ; part de cellules où la marche bat la constante : 28 % à 1 k/10 k/100 k (n=18 chacun), 39 % à 300 k, 45 % à 1 M (n=11), **78 % à 3 M (n=9)**. Ces 92 cellules mélangent le run 25 niveaux et le run profond, donc les mêmes séries deux fois (7.1).

**Transport de calibrage (leave-one-series-out)** (`results/transport_loo_live.json`, `transport_loo_deep.json`, relancés identiques) :

| run | N | modèle | erreur relative médiane | erreur signée moyenne | pire facteur | MAE (bps) |
|---|---|---|---|---|---|---|
| top-25 | 10 k | constante | 0,77 | 1,61 | 6,97 | 0,44 |
| top-25 | 10 k | racine carrée | 0,37 | 0,35 | 3,27 | 0,16 |
| top-25 | 10 k | prop. spread | 0,54 | −0,21 | 5,35 | 0,20 |
| top-25 | 10 k | demi-spread | 0,80 | −0,72 | 14,25 | 0,34 |
| top-25 | 100 k | constante | 0,72 | 1,40 | 6,10 | 1,57 |
| top-25 | 100 k | racine carrée | 0,53 | 0,38 | 3,30 | 0,73 |
| top-25 | 100 k | prop. spread | 0,39 | −0,25 | 6,63 | 0,52 |
| top-25 | 100 k | demi-spread | 0,93 | −0,92 | 61,92 | 1,68 |
| profond | 1 M | constante | 0,80 | 1,17 | 6,96 | 5,55 |
| profond | 1 M | racine carrée | 0,41 | 0,69 | 5,50 | 3,98 |
| profond | 1 M | prop. spread | 0,66 | −0,23 | 12,20 | 3,36 |
| profond | 1 M | demi-spread | 0,98 | −0,98 | 414,21 | 6,67 |

(Les lignes 10 k et 100 k du run profond : constante 0,64 / 0,60 ; racine 0,36 / 0,46.) Lecture : une constante calibrée sur d'autres marchés se trompe de 60 à 80 % en médiane ; la loi en racine carrée fait mieux (36 à 53 %), pas mieux qu'un facteur 2 dans le pire cas ; ne pas facturer le glissement (demi-spread seul) sous-facture de 75 à 98 %. Noter que « prop. spread » gagne en médiane sur 100 k top-25 (0,39) : le rapport dit « le sqrt est le meilleur transporteur » alors qu'à 100 k top-25 c'est le proportionnel au spread qui a la plus petite erreur médiane (mais un pire facteur 6,63 contre 3,30).

**Impact agrégé (Binance aggTrades, pas un métaordre)** (`empirical_vision.json`) :

| symbole | barre (s) | barres | λ (bps par M USD net) | R² | pente log-log | RMSE hors-échantillon : zéro / linéaire / racine |
|---|---|---|---|---|---|---|
| BTCUSDT | 60 | 5760 | 2,634 | 0,280 | 0,672 | 5,109 / 4,402 / 4,057 |
| BTCUSDT | 300 | 1152 | 2,271 | 0,344 | 0,562 | 11,766 / 9,538 / 9,313 |
| ETHUSDT | 60 | 2880 | 6,599 | 0,217 | 0,850 | 6,809 / 6,460 / 6,084 |
| ETHUSDT | 300 | 576 | 6,483 | 0,279 | 1,005 | 15,101 / 13,609 / 13,095 |

Verdict du rapport : « inconclusif entre racine carrée et linéaire », le flux explique 22 à 34 % de la variance de la barre. Endogénéité explicite : le rendement cause aussi le flux ; ce n'est pas l'impact d'un ordre. ✔ json.

**Comptabilité sans double comptage** (`07` §5) : tableau des « barreaux » contenus dans chaque modèle (fixe = spread+glissement+timing moyen ; racine carrée calibrée sur le coût total = spread+glissement+timing ; marche = demi-spread+glissement, etc.) : ajouter une ligne de spread à un modèle racine carrée est « le double comptage le plus courant ».

### 3.6 Rapport `08` — Remplissages et remplissages partiels

**Ordres au marché** (`results/fullfill.json`, grille 5 profondeurs × 4 tailles) : 5 % des 20 cellules ont un remplissage < 99 % ; ces cellules ont N/profondeur > 2,3 ; toutes les cellules avec N/profondeur < 0,1 sont remplies à 100 %. Exemple A=300, N=10⁷ : rempli 0,441, notionnel non exécuté 5,59×10⁶ (56 % inexécutable). Distorsion la plus fréquente : « remplir au touch » facture 0,5 bps là où la vraie marche vaut 0,6 à 360 bps.

**Ordres passifs synthétiques** (432 cellules) : remplissage moyen 0,70 ; 96 % des cellules < 0,95 ; 16 % < 0,5 ; minimum 0,10. Erreurs des modèles sur la fraction remplie :

| modèle | biais | MAE | RMSE |
|---|---|---|---|
| toujours rempli | 0,30 | 0,30 | 0,39 |
| probabilité constante | 0,00 | 0,21 | 0,25 |
| hybride (traversée OU file) | 0,25 | 0,26 | 0,35 |
| traversée du prix (σ, tick) | 0,18 | 0,21 | 0,30 |
| volume de file (L1 + taux de transactions) | −0,12 | 0,40 | 0,50 |

**Bornes live** (`passive_fill_bounds`, ordre d'achat hypothétique au meilleur achat, 30 et 60 s) :

| venue | actif | H | n | P_haut (tête de file) | P_traversée | P_bas (queue de file) | largeur |
|---|---|---|---|---|---|---|---|
| OKX | BTC | 30 | 413 | 0,869 | 0,768 | 0,496 | 0,373 |
| OKX | BTC | 60 | 409 | 0,907 | 0,831 | 0,631 | 0,276 |
| OKX | ETH | 30 | 413 | 0,889 | 0,840 | 0,528 | 0,361 |
| OKX | SOL | 30 | 413 | 0,874 | 0,765 | 0,508 | 0,366 |
| Coinbase | BTC | 30 | 490 | 0,898 | 0,800 | 0,741 | 0,157 |
| Coinbase | ETH | 30 | 490 | 0,871 | 0,865 | 0,755 | 0,116 |
| Coinbase | SOL | 30 | 490 | 0,839 | 0,718 | 0,586 | 0,253 |
| Kraken | BTC | 30 | 485 | 0,829 | 0,761 | 0,416 | 0,412 |
| Kraken | ETH | 30 | 485 | 0,786 | 0,744 | 0,464 | 0,322 |
| Kraken | SOL | 30 | 485 | 0,800 | 0,674 | 0,357 | 0,443 |

(18 lignes série×horizon dans le rapport ; ci-dessus, extraits ; `P_haut` minimum 0,786 maximum 0,939, `P_bas` minimum 0,357 maximum 0,843 ✔.) La fourchette [P_bas, P_haut] a une largeur moyenne **0,2725** (min 0,0701, max 0,4433) ✔ recalculée. Le modèle brownien de traversée surestime la probabilité de traversée de +0,170 en moyenne, dans les 18 cas (min +0,079, max +0,250) ✔ recalculé avec ma propre formule 2·(1−Φ(tick/(σ√H))). Sens : sans connaître ta position dans la file d'attente, la probabilité d'être exécuté à cheval sur le meilleur prix ne peut pas être fixée avec les données publiques ; c'est structurel (annulations invisibles).

Minimum utile par régime (`08` §4) : OHLCV seul → marché : plafond de participation, passif : pas de modèle (fill = UNKNOWN, ou règle « bas de bougie < limite » à traiter comme borne optimiste) ; L1 → « remplir au touch » seulement si N ≤ taille affichée, `INSUFFICIENT_DEPTH` au-delà ; L2 → marche exacte avec fraction exécutée ; L2+transactions → + bande de péremption + marquage post-exécution.

### 3.7 Rapport `09` — Funding, emprunt, roll

**Funding perpétuel** (Binance Vision USD-M, mai–août 2026, 369 règlements) :

| série | n | de | à | moyenne bps/8 h | écart-type | part positive | annualisé % |
|---|---|---|---|---|---|---|---|
| BTCUSDT | 369 | 2026-05-01 00:00 | 2026-08-31 16:00 | 0,44 | 0,40 | 0,87 | 4,80 |
| ETHUSDT | 369 | idem | idem | 0,32 | 0,41 | 0,81 | 3,47 |

Coût d'un long tenu (bps du notionnel, fenêtres glissantes chevauchantes) : BTC 1 j moyenne 1,32 (p05 −0,63, p95 2,78) ; **7 j 9,35 (−0,78 ; 17,26)** ; 30 j 40,51 (20,27 ; 57,75) ; ETH 1 j 0,95 ; 7 j 6,82 (−3,76 ; 14,97) ; 30 j 26,90 (4,97 ; 46,00). ✔ recalculé depuis les zips (BTC 9,35 / −0,78 / 17,26 ; ETH 6,82 / −3,76 / 14,97 ; 369 lignes, 0 trou de 8 h, part positive 0,867 / 0,808).

Comparaison de bourses (règlements OKX vs Binance, mêmes instants) : BTC n=277, 191 en commun, corrélation **0,43**, écart absolu moyen 0,27 bps, Binance−OKX +0,09 ; ETH corrélation 0,49, écart absolu 0,28 ; taux « réalisé vs annoncé » identiques (écart max 0,00 bps). Source : `funding_borrow_roll.json` (non régénérable hors ligne, voir 9).

**Emprunt** : les taux de base publiés par OKX (USDT 0,000096 quota 5 M ; BTC 0,00001392 quota 175 ; ETH 0,0000276 quota 7 000 ; USDC 0,000096 ; SOL 0,00010968 quota 40 000). Unité (par heure ou par jour) **non vérifiée** (UNKNOWN). Illustration du rapport (arithmétique, INFERENCE) : à 5 %–50 % d'intérêt annuel, un short de 7 jours coûte 9,6 à 96 bps.

**Roll** — courbe OKX BTC-USD (futures inverses datés, indice 84 398,1) :

| échéance | jours | mid | spread (bps) | base (bps) | base annualisée % |
|---|---|---|---|---|---|
| 261030 | 30,78 | 84 687,70 | 6,02 | 34,31 | 4,07 |
| 261127 | 58,78 | 85 066,00 | 1,81 | 79,14 | 4,91 |
| 261225 | 86,78 | 85 339,75 | 1,44 | 111,57 | 4,69 |
| 270326 | 177,78 | 86 427,50 | 8,75 | 240,46 | 4,94 |
| 270625 | 268,78 | 87 552,05 | 3,03 | 373,70 | 5,07 |
| 270924 | 359,78 | 88 693,15 | 36,95 | 508,90 | 5,16 |

| de → vers | spread calendaire | demi-spreads des 2 jambes | coût tout compris (long) | jours |
|---|---|---|---|---|
| 261030 → 261127 | 44,67 | 3,92 | 48,59 | 28 |
| 261127 → 261225 | 32,18 | 1,63 | 33,81 | 28 |
| 261225 → 270326 | 127,46 | 5,09 | 132,56 | 91 |
| 270326 → 270625 | 130,11 | 5,89 | 136,00 | 91 |
| 270625 → 270924 | 130,33 | 19,99 | 150,32 | 91 |

✔ arithmétique recalculée. Point de compréhension : ce « coût de roll » (34 à 150 bps) est, à peu de chose près, le **coût de portage** (carry) : la base annualisée est de 4 à 5 % sur toutes les échéances, ce qui équivaut au taux de financement. Ce n'est un « oubli » de simulateur que si le PAPER marque ses positions par rapport au spot ou à l'indice (voir 7.3).

### 3.8 Rapport `10` — Maker vs taker et latence

**Structure** (arithmétique) : coût taker = demi-spread + marche + frais taker ; maker (poser puis, si non exécuté après H, poursuivre au marché) ; `maker − taker = −P·(2·hs + Δfee) + (1−P)·X` où X est la dérive attendue si non exécuté, Δfee l'écart de frais taker−maker. P\* = X/(X+2·hs+Δfee).

**Synthétique** (432 cellules × 800 essais, H=60 s) : maker meilleur dans 61,8 % des cellules ; regret moyen « toujours maker » 4,30 bps, « toujours taker » 2,29. Selon la dérive (bps/s) : 0 → rempli 0,92, IS maker 4,59 vs taker 9,12 ; 0,1 → 0,79, 6,88 vs 9,12 ; 0,4 → 0,40, 21,95 vs 9,12. Maker meilleur : 100 % des cellules à dérive 0, 85 % à 0,1, 0 % à 0,4 (mon recalcul depuis `limit_fills.json`). **Le 61,8 % vient de cette grille : (100+85+0)/3 = 61,7 %.** C'est un artefact du choix de trois niveaux de dérive, pas une propriété du marché.

Qualité de décision des modèles de remplissage (précision « maker ou taker ? » / regret) : à l'aveugle (dérive inconnue) tous les modèles : 0,62 / 4,30 bps (identiques à « toujours maker »). Avec la dérive connue : probabilité constante 0,95 / 0,03 ; traversée 0,70 / 2,79 ; file 0,71 / 2,05 ; hybride 0,65 / 3,76. ✔ (json : 0,951 / 0,025 ; 0,701 / 2,790 ; 0,711 / 2,046 ; 0,646 / 3,761).

**Live** : sélection adverse (marquage du milieu 30 s après l'exécution, conditionnel à l'exécution moins inconditionnel) : différence de +0,29 à +1,40 bps dans 18 séries×horizons, IC à 95 % (bootstrap par blocs de 20 photos) excluant zéro dans 16 sur 18 (les deux exceptions : OKX SOL 30 s [−0,047 ; 0,656] et 60 s [−0,196 ; 0,725]) ✔ recalculé. Exemples : OKX BTC 30 s : +0,554 [0,351 ; 0,767] ; Kraken ETH 30 s : +1,405 [0,946 ; 1,933].

Dérive si non exécuté à 30 s (X) et probabilités d'équilibre :

| venue | actif | demi-spread | X (dérive si non exécuté) | n non exec. | P_bas | P_haut | P\*(Δ=0) | P\*(1) | P\*(2) | P\*(5) |
|---|---|---|---|---|---|---|---|---|---|---|
| OKX | BTC | 0,006 | 3,467 | 54 | 0,496 | 0,869 | 0,997 | 0,774 | 0,633 | 0,409 |
| OKX | ETH | 0,018 | 4,395 | 46 | 0,528 | 0,889 | 0,992 | 0,809 | 0,683 | 0,466 |
| OKX | SOL | 0,413 | 6,515 | 52 | 0,508 | 0,874 | 0,887 | 0,781 | 0,697 | 0,528 |
| Coinbase | BTC | 0,034 | 4,029 | 50 | 0,741 | 0,898 | 0,983 | 0,790 | 0,661 | 0,443 |
| Coinbase | ETH | 0,143 | 4,412 | 63 | 0,755 | 0,871 | 0,939 | 0,774 | 0,659 | 0,455 |
| Coinbase | SOL | 0,576 | 6,905 | 79 | 0,586 | 0,839 | 0,857 | 0,762 | 0,687 | 0,529 |
| Kraken | BTC | 0,019 | 3,281 | 83 | 0,416 | 0,829 | 0,989 | 0,760 | 0,617 | 0,394 |
| Kraken | ETH | 0,096 | 4,136 | 104 | 0,464 | 0,786 | 0,956 | 0,776 | 0,654 | 0,443 |
| Kraken | SOL | 0,471 | 5,589 | 97 | 0,357 | 0,800 | 0,856 | 0,742 | 0,655 | 0,485 |

Vérifié à la main : avec Δfee = 2 bps, P\* est dans [P_bas, P_haut] pour 7 des 9 séries (sauf Coinbase BTC et ETH où P_bas > P\*) ✔ ; avec Δfee = 5 bps, la marche gagne même en queue de file dans 7 séries sur 9 (ambigu : OKX SOL, Kraken SOL) ✔. D'où le drapeau `MAKER_TAKER_UNDECIDABLE`.

**Latence** : dérive du mid sur l'horizon (live, photos ≥ 4 s d'écart) : écart-type OKX BTC 1,752 (4 s) / 2,759 (10 s) / 4,432 (30 s) contre prédiction σ√L 1,546 / 2,444 / 4,233 ; moyenne toujours proche de zéro (−0,02 à −0,41 bps). Rapport écart-type/σ√L (mon recalcul) : 4 s : +11 % à +16 % (Kraken ETH +16,2 %, le maximum, légèrement au-dessus de « ~15 % ») ; 10 s : +3 % à +13 % ; 30 s : −8 % à +7 %. Sur Binance (tape de transactions, BTC) : σ/√h passe de 3,25 (0,1 s) à 1,96 (1 s), 1,56 (10 s), 1,29 (60 s) → extrapoler un σ à 1 minute sous-estime la bande à 100 ms d'un facteur 2,5 (3,25/1,29) ✔. Momentum après le quartile supérieur de flux signé : BTC 0,591 à 1,837 bps (0,880 à 1 s), ETH 0,570 à 1,069 ✔ (« +0,6…+1,8 »).

Ordres de grandeur relatifs : pour OKX BTC, l'écart-type de dérive à 4 s (1,75 bps) vaut ~300 fois le demi-spread (0,006 bps) et ≥ 4× le coût de marche de 100 000 USD (0,37 bps) : le risque de timing domine la distribution des coûts, même si sa moyenne est nulle.

### 3.9 Rapport `11` — Contrat comptable

Échelle des prix pour un achat : `decision_mid --timing--> exec_mid --spread--> touch --slippage(marche)--> avg_fill --frais--> prix net`, plus `impact` (déplacement du mid dû à mes ordres précédents) et coûts de détention hors échelle (funding, borrow, roll). Chaque déplacement de prix appartient à **une seule ligne**. États d'une ligne : `measured`, `estimated` (modèle + régime en source), `embedded_by_basis` (déjà dans le prix de remplissage : 0 ajouté), `zero_cost_proven` (source obligatoire), `unknown` (jamais additionné, `complete=False`), `not_applicable`. Bases de remplissage : MID (rien d'inclus), TOUCH (spread), BOOK_VWAP (spread+glissement), LAST_TRADE et BAR_CLOSE (rien de prouvable), REAL_FILL (spread, glissement, timing, impact). Voir le bloc JSON complet du test en `01` §4 : résidu d'identité 0,0 ; pour MID/TOUCH/BOOK_VWAP le total « inclus + ajouté » égale la vérité 1,6134885861 bps avec écart 0,0 ; refus du sur-facturage ; pile naïve (spread entier 1 bp + 1 bp de glissement + modèle racine carrée) = 3,192 bps contre 1,613 (×1,978).

### 3.10 Rapport `12` — Falsification (26 lignes F1–F26)

Résumé : **FALSIFIED** F2 (défaut 5 bps), F3 (proportionnel au spread), F6 (taille/profondeur), F8 (péremption jusqu'à 30 s dégradant beaucoup la marche : « en cette fenêtre »), F9 (Corwin–Schultz / Abdi–Ranaldo / Roll ≈ cote), F11 (spread effectif de photos décalées), F12 (AC linéaire classe les calendriers), F14 (traversée brownienne), F15 (file plus utile qu'une constante), F16 (meilleur modèle de fill ⇒ meilleure décision maker/taker), F17 (identifiabilité du fill passif), F18 (sélection adverse négligeable), F20 (funding d'une autre bourse comme proxy), F23 (un carnet d'une seule bourse = le marché), F24 (empilement naïf inoffensif), F26 (modèle clé en main) ; **PARTIAL** F1, F4, F5, F7, F10, F13, F19 ; **INCONCLUSIVE** F22 (loi en racine carrée) ; **UNTESTABLE** F21 (emprunt) ; **CIRCULAR** F25. Liste des « invalidations scientifiques » : F2, F3, F6, F9, F11, F12, F14, F15, F16, F17, F18, F20, F23, F24, F26 = 15 (F8 est un test qui échoue à falsifier la robustesse de la marche, pas une invalidation ; le rapport ne la met donc pas dans la liste).

### 3.11 Rapport `13` — Adjudication de 51 modèles (voir section 4)

### 3.12 Rapport `14` — Limites (voir sections 6 et 7)

### 3.13 Registre de vérification (au moins 10 chiffres clés)

| # | Chiffre / affirmation du rapport | Où | Mon contrôle | Résultat |
|---|---|---|---|---|
| 1 | Spread moyen OKX BTC 0,012 bps, 1 264 photos, ~50 min | `05` §1 | recalculé depuis `data/live/okx_book_BTC-USDT.jsonl.gz` : 0,01186 bps, 1 264 photos, 49,98 min | ✔ |
| 2 | Coût de marche profond OKX BTC : 0,33 / 2,46 / 5,25 bps (100 k / 1 M / 3 M), couverture 0,98 à 3 M ; Coinbase BTC 0,77 / 2,30 / 6,14 ; OKX SOL 2,67 / 17,62 / 60,63 ; Kraken ETH 1,63 / 4,00 / 7,15 | `05` §3, `07` §3 | recalculé avec mon code depuis `data/deep/*.jsonl.gz` | ✔ (4 séries × 3 montants) |
| 3 | Funding BTC long 7 j : moyenne 9,35 bps, p05 −0,78, p95 17,26 ; ETH 6,82 ; 369 règlements, 0 trou | `09`, `00` | recalculé depuis `data/vision/fund_*.zip` | ✔ |
| 4 | Matrice E1–E15 | `01` | relance de `tests_and_threats.py` : fichier identique | ✔ |
| 5 | 21 fichiers de résultats + 15 rapports | tous | relance complète, comparaison valeur à valeur | ✔ (sauf µs/prédiction) |
| 6 | Transport LOO : constante 60–80 %, racine carrée 36–53 %, pire 3–5,5× | `07` §3.3 | relance de `transport_loo.py` | ✔ |
| 7 | Bracket de fill largeur 0,07–0,44 (moyenne 0,27) ; CI exclut 0 dans 16/18 ; différence +0,29…+1,40 ; traversée brownienne +0,17 dans 18/18 | `08`, `10` | recalculé depuis `empirical_live.json` (formule indépendante pour le brownien) | ✔ |
| 8 | Spread effectif ×6–55 trop haut sur BTC ; réalisé 5 s négatif dans 8/9 séries | `06` §2 | recalcul depuis `empirical_live.json` : ×5,7 / ×34,2 / ×55,7 ; 8/9 négatifs | ✔ |
| 9 | Péremption : |erreur| ≤ 0,05 live ; ≤ 0,11 deep jusqu'à 300 k ; 0,18 (4 s) et 1,6 (30 s) à 1–3 M ; relative max 14 % | `07` §3.1 | recalcul : 0,052 ; 0,107 ; 0,181 et 1,624 ; 13,7 % | ✔ |
| 10 | Exposant du coût en N 0,39–0,87, médiane 0,55 | `07` §3 | calcul à la main sur le tableau profond | ✔ |
| 11 | FX/or/WTI : σ, sauts, ratios | `05` §6 | recalcul depuis `data/ohlc/*.csv` | ✔ |
| 12 | Table d'adjudication : 51 / 40 exécutés / 15 ADOPT / 9 ADAPT / 17 PARK / 10 REJECT ; OSS 21 / 9 exécutés / 5-1-9-6 | `13`, `03` | comptage par script sur les lignes de `13`, lecture de `oss_findings.json` | ✔ |
| 13 | Proxys de spread « ×3 … ×700 » le coté | `00` §3 | recalcul : ×3,4 à ×370 pour CS/AR/Roll/amplitude sur les 9 séries live | ✘ (×700 introuvable) |
| 14 | MAE à 30 s « seulement 7–20 % » au-dessus de 4 s | `07` §3.1, `12` F8 | ratios sur 92 paires : 0,84 à 1,96 (médiane 1,10 ; 21 paires > +20 %) | ✘ (vrai pour la médiane, faux pour SOL gros montants) |
| 15 | Stabilité aux graines « ≤ 0,03 bps sauf taille/profondeur » | `04` §3 | 0,041 pour racine carrée (L1 et OHLCV), 0,039 marche+repli | ✘ (mineur) |
| 16 | σ√L « à ~15 % près à ≥ 4 s » | `00`, `10` | +11 % à +16 % à 4 s (max +16,2 % Kraken ETH) | ✔ (à la marge) |
| 17 | Cohérence entre 03 et 13 : `bidask` ADOPT_REFERENCE (03) / ADAPT_CANDIDATE (13) ; Almgren–Chriss ADAPT_CANDIDATE (03) / PARK (13, avec réserve) | `03`, `13` | lecture croisée | ✘ (contradiction interne, voir 7.5) |
| 18 | Pour `README` : « data/vision NOT committed » | `README.md` | 580 Ko de fichiers `data/vision` sont dans l'arbre (funding + bookDepth) ; seuls aggTrades et klines sont exclus par `.gitignore` | ✘ (mineur) |
| 19 | Complétude des transactions capturées (non discutée par le rapport) | — | ids Coinbase : 0,65 % à 3,4 % manquants ; ids OKX : 5,3 % à 19,6 % de trous | nouveau constat (7.3) |
| 20 | Raw `aggTrades`/`klines` Binance | `06`, `07`, `10` | zips absents du dépôt ; seul le json de résultat est lisible | ? non vérifiable |
| 21 | Corrélation de funding OKX–Binance 0,43/0,49 | `09` | données brutes OKX non enregistrées (seules les statistiques le sont) | ? non vérifiable (json lu, ✔ cohérent avec le rapport) |

---

## 4. Candidats et méthodes évalués un par un

Vocabulaire de verdict de la lane (`13`) : **ADOPT_REFERENCE** = retenu comme référence à évaluer plus tard (pas comme dépendance de production) ; **ADAPT_CANDIDATE** = utile après adaptation ou calibrage propre ; **PARK** = on met de côté (peut revenir avec d'autres données) ; **REJECT** = écarté. Aucun score global n'est donné (`13`). Décompte que j'ai recalculé : 51 modèles/composants, 40 « exécutés », ADOPT 15, ADAPT 9, PARK 17, REJECT 10 ✔.

Dans la colonne « condition de changement », ce qui vient du rapport `14` (« Things that could overturn conclusions ») est marqué (R) ; le reste est mon analyse, marqué (A).

### 4.1 Famille A — Spread

| # | Modèle | Verdict | Justification chiffrée | Condition de changement |
|---|---|---|---|---|
| 1 | Spread coté L1 (distribution + âge de la photo) | ADOPT_REFERENCE | BTC/ETH à 1 tick ; SOL 0,8 bps ; seule mesure défendable du coût de traversée (`06`) | Si les cotes sont absentes (FX/or/matières) : non testable. (R) message-rate à tester |
| 2 | Spread effectif | ADAPT_CANDIDATE | photos REST décalées : 6–55× trop haut sur BTC ; demande un flux L1 à cadence de message, non testé | Un flux WebSocket L1+transactions ; (A) test à faire en priorité |
| 3 | Spread réalisé / marquage post-exécution | ADOPT_REFERENCE (diagnostic) | +0,29…+1,40 bps de sélection adverse à 30 s, IC exclut 0 dans 16/18 ; pas un coût de taker | — |
| 4 | Roll (1984) | REJECT | 4,4–9,2 bps live contre ≤ 1,2 coté | — |
| 5 | Corwin–Schultz (2012) | REJECT | mesure surtout la volatilité ; 0,2 bps vrai → 1,2 à 12,4 synthétique ; BTC Binance 0,8–1,5 bps vs 0,0012 | — |
| 6 | Abdi–Ranaldo (2017) | REJECT | tombe à 0 à forte volatilité ; 1,7–4,5 live | — |
| 7 | Amplitude haut–bas | REJECT | est une mesure de volatilité | — |
| 8 | EDGE (`bidask`, Ardia–Guidotti–Kroencke 2024) | ADAPT_CANDIDATE dans `13` (mais ADOPT_REFERENCE dans `03`) | meilleur estimateur sur bougies synthétiques : 5,04 pour 5 vrai ; 0,06–0,18 bps sur klines Binance vs tick 0,0012/0,037 ; instable sur ~51 bougies (0,09–2,67) | (A) seuil « ≥ 1 000 barres » à justifier par une courbe erreur-vs-n |
| 9 | Retournement de transactions | ADAPT_CANDIDATE | médiane = 1 tick exactement sur Binance BTC/ETH | Nécessite drapeau d'agresseur + horodatage fin |

### 4.2 Familles B et C — Glissement et impact

| # | Modèle | Verdict | Justification chiffrée | Condition de changement |
|---|---|---|---|---|
| 10 | 5 bps par défaut | REJECT | BTC surestimé ≥ 6× ; SOL 1 M sous-estimé de 2–3,5× ; synthétique 4,73 vs 4,00 | — |
| 11 | Table empirique par instrument × taille (constante calibrée) | ADAPT_CANDIDATE | meilleure MAE quand on a l'historique (bat la marche dans 63 % des 92 cellules) mais transporte mal (60–80 %) | Construire par instrument à partir d'historique L2 propre |
| 12 | Demi-spread seul | REJECT | −28,8 bps à 10 M USD (`shallow`) ; sous-facture 75–98 % en transport | — |
| 13 | Proportionnel au spread | REJECT | pas de terme de taille ; Coinbase BTC 100 k : MAE 3,5 vs 0,32 | — |
| 14 | Échelonné à la volatilité | REJECT | pas de taille ; couplage vol–marche live faible | Un monde où le coût ne dépend pas de σ le juge sévèrement ; en monde couplé il fait mieux (A) |
| 15 | Taille/profondeur depuis L1 + 1 bp | REJECT | |biais| TEST 7,05 ; 35,6 bps sur `wall` | — |
| 16 | Loi en racine carrée, Y inter-instruments | ADAPT_CANDIDATE | meilleur transporteur (36–53 %), bande ±50–100 % et queue 3–5× | Si l'exposant réel n'est pas 0,5 (mesure locale live 0,39–0,87, (R) concavité au-delà de 25 niveaux) |
| 17 | **Marche du carnet L2 avec drapeau de profondeur visible et bande de péremption** | **ADOPT_REFERENCE** | pas de biais systématique vs photo suivante (médiane ≤ 3,3 % du coût) ; exact en synthétique quand la profondeur est visible ; défini jusqu'à 3 M USD avec 400 niveaux | (R) des fills réels montrant un biais > le bruit de péremption ; (A) attention : ce biais nul est mécanique (7.1) |
| 18 | zipline `VolumeShareSlippage` / `FixedBasisPointsSlippage` | ADOPT_REFERENCE (oracle de formule) | formules vérifiées en sonde (50,002 et 50,025 sur l'ordre témoin) | — |
| 19 | QuantConnect LEAN (glissement/fill/frais) | ADOPT_REFERENCE (spécification de frais) | non exécuté (.NET) ; Apache-2.0 | — |
| 20 | Almgren–Chriss linéaire | PARK | classe mal les calendriers (regret 0,68 bps, 0 % correct), mais le test est dégénéré (7.1) | (A) test avec un vrai dilemme risque/coût |
| 21 | Propagateur + épuisement | ADAPT_CANDIDATE | utile pour ordres multi-enfants ; calibrage sur ses propres runs, pas sur données gratuites | Runs PAPER propres avec ordres étiquetés |
| 22 | Obizhaeva–Wang | PARK | non exécuté ; paramètres UNKNOWN | — |
| 23 | Contrainte de Gatheral δ+γ ≥ 1 | ADOPT_REFERENCE (comme contrainte) | théorie ; formule `[M]` à re-vérifier | — |
| 24 | Linéarité de l'impact permanent (Huberman–Stanzl) | PARK | théorie | — |
| 25 | Kissell I-Star | PARK | forme UNKNOWN | — |
| 26 | Régression flux–rendement agrégée (Kyle λ / déciles) | PARK | endogène, non métaordre : λ = 2,3–6,6 bps par M USD, R² 0,22–0,34 | Ordres marqués |

### 4.3 Familles D et E — Remplissages

| # | Modèle | Verdict | Justification chiffrée | Condition de changement |
|---|---|---|---|---|
| 27 | « Toujours rempli au touch » (passif) | REJECT | remplissage réel 0,70 en synthétique ; borne haute live 0,79–0,94 | — |
| 28 | Probabilité constante | PARK | égale aux meilleurs modèles synthétiques (MAE 0,21) ; non identifiable en réel | Fills propres |
| 29 | Traversée brownienne | PARK | +0,17 optimiste (18/18) | — |
| 30 | File affichée vs volume | PARK | MAE 0,40 vs 0,21 (constante) | — |
| 31 | Hybride | PARK | +0,25 de biais | — |
| 32 | Fourchette [P_bas(file), P_traversée/P_haut] | ADOPT_REFERENCE | honnête sur la non-identifiabilité (largeur 0,07–0,44) | — |
| 33 | Remplissage plafonné par la profondeur (`filled_fraction`) | ADOPT_REFERENCE | exact partout où la profondeur est visible | — |
| 34 | Cont–Stoikov–Talreja | PARK | exige L3/événements : `MODEL_NOT_EMPIRICALLY_CALIBRATABLE_FROM_FREE_DATA` | Données événementielles |
| 35 | Queue-reactive (Huang–Lehalle–Rosenbaum) | PARK | idem | idem |
| 36 | `hftbacktest` (files/latence) | PARK | exige des flux tick/L2 ; test de fumée : 1 ordre rempli, frais 0,01998 pour 2 bps | Si un flux L2 existe |
| 37 | `nautilus_trader` `FillModel` | PARK | bascule de probabilité (Bernoulli) | — |

### 4.4 Familles F, G, H, I — Sélection adverse, maker/taker, calendrier, latence

| # | Modèle | Verdict | Justification chiffrée | Condition de changement |
|---|---|---|---|---|
| 38 | VPIN | PARK | contesté (Andersen–Bondarenko) ; non exécuté | — |
| 39 | Règle d'équilibre maker/taker `P* = X/(X+2·hs+Δfee)` avec P borné | ADAPT_CANDIDATE | `MAKER_TAKER_UNDECIDABLE` quand la fourchette contient P\* (7/9 séries à Δfee = 2 bps) | Fills propres pour fixer P ; (A) X calculé en tête de file alors que P_bas est en queue de file |
| 40 | Modèles HJB de maker (Avellaneda–Stoikov…) | PARK | exigent des expériences propres de cotation | — |
| 41 | TWAP (enfants égaux) | ADOPT_REFERENCE (comme calendrier de test) | utilisé dans toutes les expériences de découpage | — |
| 42 | VWAP / POV | PARK | profil de volume intraday non étudié | — |
| 43 | Bande de latence σ_L√L (moyenne nulle) | ADOPT_REFERENCE | ±15 % à ≥ 4 s live ; σ doit être estimé à l'horizon de latence | Gaps, régimes de tendance (voir 44) |
| 44 | Complément de dérive conditionnelle au flux | ADAPT_CANDIDATE | +0,6…+1,8 bps après un flux fort (Vision) | Étalonnage sur tape propre |

### 4.5 Familles J, K, L — Détention, fragmentation, comptabilité

| # | Modèle | Verdict | Justification chiffrée | Condition de changement |
|---|---|---|---|---|
| 45 | Funding : taux réglé par bourse × notionnel à l'instant de règlement | ADOPT_REFERENCE | BTC 7 j : 9,35 bps (−0,78 ; 17,26) ; corrélation OKX–Binance 0,43/0,49 | — |
| 46 | Emprunt : taux (bourse+palier+date) sinon `UNKNOWN_COST` | ADOPT_REFERENCE | seul le taux de base est visible ; unité non vérifiée | Relevé de taux par palier |
| 47 | Roll : spread calendaire + 2 demi-spreads | ADOPT_REFERENCE (futures crypto datés) | 34–150 bps par pas | (A) rapprocher du coût de portage (7.3) |
| 48 | Swap FX / financement or / roll COMEX | PARK | aucune source gratuite fiable utilisée | Historiques de courtier |
| 49 | Routage / choix du carnet selon fragmentation | ADAPT_CANDIDATE | ×1,4 à ×3,3 d'erreur si on choisit mal | — |
| 50 | Échelle « implementation shortfall » + contrat d'intégration au prix de remplissage | ADOPT_REFERENCE | résidu 0,0 (tautologique, voir 6.3) ; refus de sur-facturage | (A) test sur un vrai moteur PAPER |
| 51 | Décomposition de Perold | ADOPT_REFERENCE | intégrée à l'échelle | — |

### 4.6 Sonde open source (21 dépôts, `03`)

- **ADOPT_REFERENCE (5)** : `zipline-reloaded` (formules de glissement, Apache-2.0), QuantConnect LEAN (catalogue de frais, Apache-2.0), `bidask` (EDGE, MIT), `freqtrade` (logique de funding, GPL-3.0 : concept seulement), `ccxt` (schéma frais/funding, MIT).
- **ADAPT_CANDIDATE (1)** : notebook Almgren–Chriss (MIT, dernière modif 2022 ; sert d'oracle de trajectoire).
- **PARK (9)** : `hftbacktest`, `nautilus_trader`, `vectorbt`, `mbt_gym`, ABIDES (2), `hummingbot`, `PyLOB`, `vnpy`.
- **REJECT (6)** : `zipline` original, `backtesting.py` (AGPL), `backtrader` (GPL, abandonné), `tick` (fit cassé sous numpy 2.x), `bmoscon/orderbook` (GPL), `pyfolio/quantstats` (n'ont pas d'estimateurs de spread).

Fait notable (OBSERVED par la sonde) : `backtesting.py` applique le paramètre `spread` comme un demi-spread par côté et ne l'applique pas aux sorties forcées en fin de test ; `freqtrade` transforme silencieusement les bougies de funding manquantes (NaN) en 0 frais. Ce sont des exemples réels du « UNKNOWN devient 0 » que le contrat comptable veut interdire.

**Contradictions à corriger** dans les rapports (voir 7.5) : `03` classe `bidask` ADOPT_REFERENCE et Almgren–Chriss ADAPT_CANDIDATE ; `13` classe EDGE ADAPT_CANDIDATE et Almgren–Chriss linéaire PARK (avec la remarque « le notebook est un ADAPT pour les maths de trajectoire »). `13` ajoute d'ailleurs que les verdicts OSS sont « as stated by the probe ». Le décompte final du rapport (`00`, « OSS_COMPONENTS_TESTED=9 ») reste juste.

### 4.7 Ce que la lane recommande comme « pile minimale » par régime de données (`00`)

| régime | spread | glissement / impact | fills | timing | détention | statut |
|---|---|---|---|---|---|---|
| OHLCV seul | UNKNOWN, ou EDGE en borne sur ≥ 1 000 barres | prior racine carrée, Y inter-instruments, bande ±50–100 %, drapeau queue 3–5×, plafond de participation | marché : plafond ; passif : aucun | bande σ√L + drapeau de saut | funding mesuré, borrow UNKNOWN, roll avec courbe | LIMITED (majeures crypto ; rien d'empirique FX/or/matières) |
| L1 | spread coté (+âge) | ordres ≤ taille affichée ; au-delà `INSUFFICIENT_DEPTH` + prior | plafond par la taille affichée ; passif : fourchette | σ_L√L | idem | SUPPORTED (portée limitée) |
| L2 | mesuré | marche plafonnée à la profondeur visible, bande de péremption | `filled_fraction` plafonnée ; fourchette | σ_L√L + bande saut/retrait | idem | SUPPORTED (BTC/ETH/SOL ≤ 3 M USD, 3 bourses, 400 niveaux) |
| Transactions + carnet | + effectif (non testé) | + dérive au flux, marquages | fourchette ouverte sans ordres propres | + momentum de flux | idem | SUPPORTED en diagnostics |

---

## 5. Bloc final complet (reproduit tel quel, `reports/006_execution_cost_intelligence/00_EXECUTIVE_SUMMARY.md`)

```
MODELS_DISCOVERED=51 catalogued models/components (table in 13; plus 21 OSS repositories probed)
MODELS_EXECUTED=40 of 51 (own reference implementations and/or OSS smoke runs, on synthetic and/or public data)
OSS_COMPONENTS_TESTED=9 smoke-executed (of 21 cloned and source-inspected; 5 more used as formula references)

SPREAD_REFERENCE=quoted L1 spread distribution with snapshot age (OHLCV-only: EDGE as a bound on >=1000 bars, never a measurement; candle proxies rejected)
SLIPPAGE_REFERENCE=L2 book walk over visible levels with INSUFFICIENT_VISIBLE_DEPTH flag and empirical staleness band (OHLCV-only: sqrt-law prior with +-50-100% band)
IMPACT_REFERENCE=none beyond the walk for a single child order; depletion+propagator memory (ADAPT_CANDIDATE, own-run calibration) for multi-child/repeated orders
FILL_REFERENCE=depth-capped walk for market orders; explicit [P_lower(queue), P_upper] bracket for passive orders (no point estimate supported)

FUNDING_ACCOUNTING_REFERENCE=settled per-venue funding rate x held notional at settlement instants; ESTIMATED only with a band; ZERO_PROVEN only with evidence
BORROW_ACCOUNTING_REFERENCE=venue+tier+date rate if supplied, otherwise UNKNOWN_COST (never zero)
ROLL_ACCOUNTING_REFERENCE=calendar spread + both legs' half-spreads at the roll; NOT_APPLICABLE for perps/spot; UNKNOWN for continuous series without roll record

OHLCV_ONLY_MODEL_SUPPORTED=LIMITED (crypto majors: sqrt-law band + EDGE bound + participation cap; NO for FX/gold/commodities, NO for passive fills)
L1_MODEL_SUPPORTED=YES_LIMITED (spread, orders within displayed size, fill bracket, timing band)
L2_MODEL_SUPPORTED=YES (depth-capped walk; near-unbiased vs next snapshot on 9 live series, N up to 3M USD with 400 levels; realised slippage unmeasured)

DOUBLE_COUNTING_CONTRACT_PROVEN=PROVEN_ALGEBRAICALLY_AND_TESTED_ON_SYNTHETIC_LADDER (ladder identity residual 0.0; basis invariance abs_err 0.0; overcharge refused); NOT_PROVEN_ON_A_REAL_PAPER_ENGINE (UNKNOWN)

ANY_DROP_IN_EXECUTION_MODEL=NO
ANY_SCIENTIFIC_INVALIDATION=YES (of assumptions/models, not of the reference stack: OHLC spread proxies as quote substitutes; fixed 5 bps default; spread-proportional slippage; effective spread from polled snapshots; Brownian price-through fill; AC-linear schedule ranking; fill-model complexity improving maker/taker decisions; single-venue book as market; cross-venue funding proxy; a single calibrated constant transporting across instruments)

SECOND_SERVICE_REQUIRED=NO (all reference primitives are pure functions of data a PAPER runtime already sees; UNKNOWN whether AurumShift has L2 history)
SECOND_DATASTORE_REQUIRED=NO (optional L2/tape history for calibration is small: the 58-minute capture of 9 series is 8 MB gz; a file/existing store suffices)

FINAL_VERDICT=LIMITED_EXECUTION_MODELS_SUPPORTED
```

### Explication ligne par ligne

| Clé | Ce que ça veut dire | Mon jugement |
|---|---|---|
| `MODELS_DISCOVERED=51` | Nombre de modèles/composants dans le tableau de `13`, plus 21 dépôts sondés (dont une partie est déjà comptée dans les 51) | ✔ 51 comptés. Le « plus 21 » n'est pas additif : plusieurs lignes de `13` (zipline, LEAN, hftbacktest, nautilus) sont des dépôts de la sonde |
| `MODELS_EXECUTED=40 of 51` | Exécutés au moins une fois (code propre ou test de fumée OSS) | ✔ 40 « Yes ». Attention : « exécuté » inclut les tests de fumée sur jouets (`hftbacktest` : 7 événements ; `nautilus` : 10 tirages) qui ne disent rien du coût |
| `OSS_COMPONENTS_TESTED=9` | Neuf dépôts exécutés en test de fumée sur 21 ; « 5 de plus utilisés comme références de formule » | 9 ✔ (zipline-reloaded, hftbacktest, nautilus, vectorbt, backtesting.py, bidask, notebook AC, tick, ccxt). Les « 5 » ne sont pas listés ; je ne peux pas les vérifier (?) |
| `SPREAD_REFERENCE` | Référence de spread = spread coté L1 avec l'âge de la photo ; sans cotes, EDGE seulement comme borne sur ≥ 1 000 barres ; proxys de bougies rejetés | Cohérent avec 3.4 |
| `SLIPPAGE_REFERENCE` | Marche du carnet L2 avec drapeau « profondeur visible insuffisante » et bande de péremption ; sans carnet, prior en racine carrée avec bande ±50–100 % | Bande de péremption chiffrée : 0,1–0,8 bps pour ≤ 100 k USD |
| `IMPACT_REFERENCE=none beyond the walk…` | Pour un ordre unique, pas d'impact au-delà de la marche ; pour plusieurs enfants, épuisement+propagateur (à calibrer sur ses propres runs) | Honnête : rien n'est calibré sur données gratuites |
| `FILL_REFERENCE` | Marché : marche plafonnée. Passif : fourchette [P_bas, P_haut], pas de point | Bien fondé (largeur 0,07–0,44) |
| `FUNDING_ACCOUNTING_REFERENCE` | Taux réglé de la bourse × notionnel détenu aux instants de règlement ; `ESTIMATED` seulement avec bande ; `ZERO_PROVEN` avec preuve | ✔ cohérent avec 3.7 |
| `BORROW_ACCOUNTING_REFERENCE` | Taux (bourse+palier+date) sinon `UNKNOWN_COST`, jamais zéro | — |
| `ROLL_ACCOUNTING_REFERENCE` | Spread calendaire + demi-spreads ; `NOT_APPLICABLE` pour perps/spot ; `UNKNOWN` pour série continue sans trace des rolls | — |
| `OHLCV_ONLY_MODEL_SUPPORTED=LIMITED` | Avec seulement des bougies : possible seulement pour les majeures crypto ; non pour FX/or/matières ; non pour les fills passifs | Avec ce qui a été testé (aucun coût FX n'est calibré), « LIMITED » est plutôt généreux pour OHLCV seul : les seules preuves sont crypto |
| `L1_MODEL_SUPPORTED=YES_LIMITED` | Spread, ordres dans la taille affichée, fourchette de fill, bande de timing | — |
| `L2_MODEL_SUPPORTED=YES` | Marche plafonnée à la profondeur : quasi non biaisée vs photo suivante sur 9 séries, N jusqu'à 3 M USD, 400 niveaux ; slippage réalisé non mesuré | Voir 7.1 : « quasi non biaisé » est vrai mais c'est un test de persistance |
| `DOUBLE_COUNTING_CONTRACT_PROVEN` | Prouvé algébriquement et testé sur une échelle synthétique ; non prouvé sur un vrai moteur PAPER (UNKNOWN) | L'aveu « algébriquement » est exact ; c'est bien de la cohérence interne (6.3) |
| `ANY_DROP_IN_EXECUTION_MODEL=NO` | Aucun modèle clé en main | ✔ F26 |
| `ANY_SCIENTIFIC_INVALIDATION=YES (…)` | Certaines hypothèses courantes sont invalidées (liste de dix) | Liste cohérente avec `12` |
| `SECOND_SERVICE_REQUIRED=NO` | Toutes les primitives sont des fonctions pures de données que le PAPER voit déjà ; on ne sait pas si AurumShift a de l'historique L2 | Correct mais « UNKNOWN » pèse |
| `SECOND_DATASTORE_REQUIRED=NO` | Un fichier suffit pour l'historique de calibrage : 58 minutes de 9 séries = 8 Mo gz | ✔ ordre de grandeur (5,2 + 2,8 Mo pour live+deep) ; mais 58 minutes sont très peu pour calibrer quoi que ce soit (7.1) |
| `FINAL_VERDICT=LIMITED_EXECUTION_MODELS_SUPPORTED` | Verdict unique : un sous-ensemble limité est supporté | Voir 0 pour la force |

---

## 6. Contrôles de validité

### 6.1 Fuite d'information / regard vers le futur (lookahead)

- **Monde synthétique** : le modèle observe une photo prise *avant* la latence (`obs` = carnet au moment de la décision) ; le carnet exécuté est tiré ensuite avec une corrélation 0,7 (`make_book`). Le mid futur n'entre jamais dans un modèle. ✔ pas de fuite structurelle.
- **Live — spread effectif** : la photo utilisée est « la dernière avant la transaction » (`searchsorted − 1`, `empirical_live.py` l.159) ✔. Le décalage d'horloge entre l'horloge locale et les horodatages des bourses est ignoré (`14` §4b) ; j'ai mesuré pour les carnets OKX : `(t0+t1)/2 − ts` = −0,050 s en médiane (5e–95e centile −0,067 à −0,033 s), négligeable devant la cadence de 2 s. Pour Coinbase/Kraken (pas d'horodatage de bourse pour les carnets) : non mesurable (?).
- **Live — modèles de base** : calibrage sur la 1re moitié, test sur la 2e ✔. **Mais** (mon analyse) σ (`sig`) et V_jour (`Vday`) utilisés dans « racine carrée » sont calculés sur **toute** la capture, donc test inclus (`empirical_live.py` l.115–117, 136) : fuite légère et contemporaine. De même le test de transport LOO utilise σ et V_jour contemporains de la série prédite. Impact probablement faible (paramètres d'échelle, pas de niveau de coût) mais non nul, et les rapports ne le disent pas.
- **Test de péremption** : la cible est le coût à t+Δ, prédit avec la photo à t. C'est le protocole voulu, pas une fuite.
- **Fill passif** : les transactions comptées sont celles des instants [t, t+H] après la photo ; le marquage utilise le mid 30 s après le remplissage. Pas de fuite ; en revanche il ne prend pas en compte les transactions manquées (6.5).

### 6.2 Déterminisme

- Toutes les expériences synthétiques sont graine-fixées. **J'ai relancé** `run_synth.py` (62 s sur un cœur), `tests_and_threats.py`, les analyses live/deep (5,8 s pour live+deep+transport) : les fichiers sont identiques à ceux de la branche, colonne de chronométrage exceptée ✔. Cela couvre déterminisme numérique sous numpy 2.4.6, pandas 3.0.6, scipy 1.17.1, Python 3.11.15.
- Les rapports sont régénérés à l'identique par `build_reports.py` sauf la colonne « µs par prédiction » du tableau de `04` ✔. Corollaire : les 72 tableaux des rapports ne peuvent pas contenir d'erreur de recopie ; ils contiennent en revanche les textes rédigés à la main autour, où j'ai trouvé les écarts de la section 3.13.
- Limite : les graines des cinq jeux de « stabilité » se recouvrent partiellement (graine = 1000 + décalage + 10×indice_scénario + log10(N) ; décalage 100 = 10 indices de scénario). Pour un décalage de 100 les scénarios d'entraînement d'indices 0 à 3 réutilisent les graines des scénarios d'indices 10 à 13 du décalage 0. Ce ne sont pas les mêmes scénarios, donc l'effet est mineur (aléas communs), mais les cinq jeux ne sont pas totalement indépendants.

### 6.3 Contrôles positifs et négatifs

- **Contrôles positifs (« ça marche quand ça doit »)** : la marche du carnet est exacte sur un carnet consistant avec la vérité (biais 0,01–0,05 bps) — **rapport `12` F25 : CIRCULAR, pas une preuve** (bien vu). Le contrat accepte l'ajout d'une ligne légitime et refuse un sur-facturage (test négatif ✔ `overcharge_refused: true`). `ZERO_PROVEN` sans source est rejeté ✔.
- **Contrôles négatifs** : BTC-USD sert de témoin dans la table FX ; estimateurs de spread testés sur données synthétiques à spread connu (CS 1,2 à 12,4 pour 0,2 vrai) ; `hl_range_proxy` est dit être une mesure de volatilité ; EDGE testé sur bougies Binance avec vérité (tick) connue par retournement ; identité « annoncé vs réalisé » des taux OKX (écart max 0,0 bps, 277 règlements par symbole) sert de contrôle de cohérence de la source.
- **Identité de l'échelle (résidu 0,0)** : **tautologique** (mon analyse, ✔ lu dans le code). Dans `simulate_market`, `out["IS"][i]` est *défini* comme `drift + half_spread + walk + impact` (`synth.py` l.155). Le « test » de `t_identity` recalcule cette somme et la compare à elle-même ; il ne peut pas échouer. Le résidu 0,0 prouve que le code additionne bien, pas que la décomposition physique est juste.
- **Invariance de base (abs_err 0,0)** : idem, quasi-arithmétique. Pour MID, TOUCH, BOOK_VWAP, le test injecte comme « ligne du contrat » la vérité elle-même (`r["walk"].mean()`, `r["half_spread"].mean()`) puis constate que la somme est égale à la vérité. Ce que le test prouve réellement : le grand livre ne compte pas deux fois un barreau *quand on lui fournit les bons barreaux*. C'est utile (le refus `DOUBLE_COUNT` est réel) mais ce n'est pas une validation de modèle. Le rapport `11` l'admet en toutes lettres (« the proof says the contract is internally consistent »).
- **« Pile naïve ×1,98 »** : la « pile naïve » est un choix de l'auteur (spread entier 1 bp + 1 bp de glissement arbitraire + racine carrée avec Y = 0,117 codé en dur dans `tests_and_threats.py` l.55). Le ×1,98 illustre le risque de double comptage ; il ne mesure pas ce qu'un simulateur réel fait. À citer comme illustration.

### 6.4 Erreurs corrigées en cours de route et écarts déclarés

- `02` « Corrections to the appended notes » : (1) arithmétique de latence corrigée (0,6·√(0,2/31,536×10⁶) ≈ 4,8×10⁻⁵ = **0,48 bps**, pas 0,15 bp ; ✔ je refais le calcul : 0,6 × 7,96×10⁻⁵ = 4,78×10⁻⁵) ; (2) barèmes de frais OKX/Bybit/Coinbase = UNKNOWN (sources secondaires, contradictions internes), donc frais traités comme paramètres (5/2 et 10/8 bps) ; (3) identifiants arXiv « 2026 » non validés ; (4) exposant de la loi en racine carrée sur les places actuelles UNKNOWN.
- Drapeau d'agresseur Coinbase : accord de 25–33 % avec la règle des cotes → interprété comme « côté du maker », utilisé inversé (`s_use = −listed`). L'accord inversé serait 67–75 %, nettement inférieur aux 70–85 % d'OKX/Kraken : la classification Coinbase reste plus bruitée (non quantifié, `14` §5).
- Base USDT/USD (~2 bps) retirée pour les paires OKX dans les tables cross-venue.
- Échecs assumés de la sonde OSS : `tick.fit` cassé, `mbt_gym` non installable, `bmoscon/orderbook` mauvais paquet, ABIDES pins anciens, `bidask` test de fumée sur données grossières (27 bps lu pour 40 bps vrai, présenté comme non probant).
- Écart au protocole : le mandat évoque des catégories (`MODEL_NOT_EMPIRICALLY_CALIBRATABLE_FROM_FREE_DATA`, états `KNOWN_COST` etc.) ; le rapport `09` scinde `KNOWN_COST` en `MEASURED`/`ESTIMATED` — écart déclaré.

### 6.5 Contrôles nouveaux que j'ai ajoutés

1. **Reproduction complète** (section 9) : bit à bit.
2. **Complétude des transactions capturées** (non discutée par le rapport). L'endpoint « transactions récentes » ne renvoie que les 100 dernières transactions à chaque appel (toutes les 3–4 s). Les identifiants de Coinbase sont séquentiels par produit : manquants 137 sur 21 057 (0,65 %) BTC, 318 sur 9 309 (3,4 %) ETH, 164 sur 9 924 (1,7 %) SOL. Pour OKX les identifiants ont des trous : 4 422 sur 22 572 (19,6 %) BTC, 1 519 sur 13 833 (11,0 %) ETH, 1 017 sur 19 233 (5,3 %) SOL (INFERENCE : trous = transactions manquées ; on ne peut pas exclure que les ids OKX ne soient pas strictement contigus). Conséquences possibles : (a) sous-estimation de `P_haut`/`P_bas`/`P_traversée` pour OKX (moins de transactions vues, donc moins de « transaction à ≤ ma limite »), donc peut-être une partie de l'« optimisme » du modèle brownien (+0,17) ; (b) sous-estimation de `Vday_proxy` (OKX BTC 0,564 Md USD/jour proxy) donc de l'échelle de la loi en racine carrée. Effet probablement faible pour (a) — une seule transaction suffit pour marquer une exécution sur 30–60 s — mais à quantifier.
3. **Cohérence des chiffres de prose vs tableaux** : voir 3.13.
4. **Calcul du P\* et de ses cas « à l'intérieur de la fourchette »** : recalculé à la main pour Δfee 2 et 5 bps ✔.

---

## 7. Critique indépendante

Ce qui précède montre une lane sérieuse : elle affiche ses limites (`14`), sépare vérité synthétique et données réelles, marque les résultats circulaires, et ses tableaux sont reproductibles. Le reste de cette section concerne ce qui, à mon avis, mérite d'être relativisé. Étiquettes : (mon analyse) = jugement de ma part ; (vérifié) = recalculé.

### 7.1 Points faibles de méthode

1. **Aucun ordre réel, donc aucun « coût réalisé ».** Tout le « glissement » empirique est le coût *hypothétique* d'un ordre qui marcherait dans une photo publique. Le rapport le dit (`14` §1) ; en revanche l'expression `L2_MODEL_SUPPORTED=YES` dans le bloc final se lit, sans ce contexte, comme une validation d'exécution. Ce qui est supporté : « la photo du carnet est une bonne prévision de la photo suivante ». Pas : « l'ordre aurait obtenu ce prix ».
2. **« Quasi non biaisé » : une propriété mécanique.** (mon analyse) Le test compare le coût calculé sur la photo à *t* et celui calculé sur la photo à *t+4 s ou 30 s*. Pour n'importe quelle série stationnaire, cette différence a une moyenne proche de zéro : on mesure la persistance, pas l'exactitude. Un carnet qui « clignote » autour d'une moyenne donne un biais nul et une MAE non nulle, ce qui est exactement ce que le rapport observe (biais ≤ 0,05 bps, MAE 0,13–1,3 bps). La phrase du résumé « the only slippage primitive that is (near-)unbiased across scenarios and data » est donc trompeuse : *across scenarios*, la marche est fausse de 13,25 bps dans `gap`, 4,27 dans `withdraw`, 1,99 dans `fragmented`, 1,48 dans `trend` (`04`), et son biais moyen en TEST est 2,13 bps. Elle est non biaisée **contre la photo suivante** ; contre les scénarios adverses elle ne l'est pas. Pour être honnête, le rapport `04` dit tout ça ; c'est le résumé `00` qui condense trop.
3. **Cellules non indépendantes.** Les 92 cellules « walk vs constante » mélangent le run 25 niveaux (50 min) et le run profond (8 min) pour les mêmes 9 séries, avec des tailles de 1 k à 3 M : ce sont les mêmes marchés vus deux fois, à des tailles qui se chevauchent. Les pourcentages (37 %, 60 %, 78 %) n'ont pas d'intervalle de confiance et l'effectif effectif est beaucoup plus petit que 92 (au plus 9 séries × 2 fenêtres).
4. **Une seule fenêtre.** 50 minutes plus 8 le 2026-09-29, entre 13:00 et 14:00 UTC. Aucun cycle jour/nuit/week-end, aucun événement de stress ; le rapport le dit. Un point supplémentaire : les deux fenêtres consécutives (live puis deep) ne donnent pas les mêmes coûts pour la même série. Coût de marche 100 k USD, live vs deep (vérifié) : OKX ETH 0,78 vs 1,15 (+47 %), Coinbase SOL 5,24 vs 3,95 (−25 %), Coinbase BTC 0,61 vs 0,77 (+26 %). L'écart mesure la variabilité d'une fenêtre à l'autre, et cette variabilité n'entre dans aucune bande d'incertitude.
5. **Le proxy du volume quotidien est fragile.** `Vday_proxy_usd` extrapole la fenêtre de transactions capturée à 86 400 s. Il varie d'un facteur allant jusqu'à 2,4 entre les deux fenêtres pour la même série (vérifié : Coinbase ETH 0,53 vs 1,25 Md USD/jour ; Coinbase SOL 0,17 vs 0,40 ; OKX ETH 0,28 vs 0,43). Comme la loi en racine carrée utilise V_jour, et que Y est calibré contre ce proxy, les erreurs de transport du prior racine carrée (36–53 %) contiennent une part d'erreur de mesure de V_jour que le rapport ne sépare pas. À cela s'ajoutent les transactions manquées (6.5) qui sous-estiment V pour OKX.
6. **Le modèle est jugé sur sa propre échelle de temps.** L'écart-type de la dérive suit σ√L à ~15 % près pour L ≥ 4 s : c'est un contrôle de cohérence de la marche aléatoire, pas de la latence réelle d'un système (qui inclut le délai de décision, souvent de plusieurs secondes ou minutes ; `02` I).
7. **Statistiques.** Pas d'IC sauf pour la sélection adverse ; pas de correction pour tests multiples ; observations autocorrélées (une photo toutes les 2 s, marquage à 30 s : chevauchement massif). Le rapport avertit qu'il faut traiter comme du bruit les différences < 0,1 bps ; c'est une règle du pouce, pas un test.
8. **Vérité synthétique auto-construite.** Le monde synthétique impose (a) un carnet en loi de puissance avec β = 1,5, plus convexe que les 0,3–0,7 vus près du touch en live, (b) un spread de base de 1 bp, alors que BTC/ETH vivent à ~0,01–0,04 bps, (c) une volatilité de 0,9 bps/√s (BTC-like). Les tailles de biais synthétiques (« 5 bps à 10 M USD ») ne se transposent pas telles quelles. Le rapport le dit pour la convexité et ajoute `concave_book` (ajouté *après* avoir vu le live, donc test non aveugle).

### 7.2 Choix en bord de grille et paramètres discutables

- **Tests de décision par des grilles à 3 niveaux.** Le « maker meilleur dans 61,8 % des cellules » vient de trois valeurs de dérive (0, 0,1, 0,4 bps/s) réparties à parts égales : 100 %, 85 %, 0 % des cellules donnent (100+85+0)/3 ≈ 61,7 %. Les 62 % de précision de tous les modèles « à l'aveugle » sont aussi cet artefact : ils répondent tous « maker ». La grille inclut des dérives (0,4 bps/s = 24 bps par minute, ~5 σ à 60 s de la volatilité de base) qui ne sont pas plausibles en marché réel. Les cellules « probables » sont celles à faible dérive, où le maker gagne toujours en synthétique.
- **Le test de classement de calendriers est dégénéré** (vérifié dans `sliced.json`) : les 60 cas ont la même réponse correcte (20 tranches). Trois modèles « parfaits à 100 % » n'ont fait que répondre « 20 ». La conclusion « AC linéaire est falsifié comme classeur de calendriers » repose sur un test où toute règle « toujours le plus de tranches » gagne. Le rapport reconnaît que la dimension risque/variance qui motive AC n'est pas évaluée (UNKNOWN).
- **Comparaison EDGE vs Corwin–Schultz non homogène.** Le tableau synthétique des estimateurs de `06` moyenne les bougies de 60 s (250 barres) et de 300 s (60 barres) pour Roll/CS/AR, alors que EDGE n'est lancé que sur des bougies de 60 s (`analysis/oss_bidask_test.py`). Exemple (spread vrai 0,2, σ = 0,9, sans tick) : CS = 1,85 à 60 s, 5,73 à 300 s, 3,79 en moyenne (tableau) ; EDGE = 1,10 à 60 s. À conditions égales l'écart EDGE/CS est plus étroit que ce que le tableau suggère, sans inverser la conclusion.
- **Seuils d'usage choisis à la main** : « EDGE sur ≥ 1 000 barres », bande « ±50–100 % » (tirée de 9 séries, médiane des erreurs de transport), « queue 3–5× », couverture ≥ 95 % : plausibles mais non testés par une courbe.
- **Modèle maker/taker et cohérence de la file.** (mon analyse) P\* utilise X = dérive moyenne quand l'ordre n'est **pas** exécuté avec la définition « tête de file » (`P_haut`) : peu de cas de non-exécution (46 à 104 par série) donc les plus adverses. Ce P\* est ensuite comparé à `P_bas` (queue de file). Pour la queue de file, davantage d'ordres ne sont pas exécutés, dont des cas où le prix n'a pas beaucoup monté : X serait plus petit, P\* plus bas, et la zone « maker gagne » plus large. La conclusion `MAKER_TAKER_UNDECIDABLE` est donc biaisée vers l'indécision pour les écarts de frais 1–3 bps.
- **Le pas de grille du carnet synthétique (0,25 bps)** fait qu'un ordre de 1 000 USD affiche déjà un « walk » de 0,125 bps (le milieu du premier niveau), alors que le carnet live BTC coûte 0,01–0,10 bps à 1 k. Sur les petits montants, le synthétique surestime.
- **Gap de 15 bps, `withdraw` ×0,15** : magnitudes choisies à la main, sans étalonnage sur un événement réel.

### 7.3 Hypothèses fragiles côté données réelles

- **Couverture et sélection dans le run 25 niveaux** (vérifié) : le tableau de `07` §3 affiche des coûts à 1 M USD pour des séries dont la couverture est 0,00–0,04 (Coinbase BTC 0,93 à 1 % de couverture, plus bas que la valeur à 300 k, 1,09 ; OKX SOL 14,88 à 0,00). Ce sont des moyennes sur des photos rares et exceptionnellement profondes, pas des coûts typiques. Utiliser le run profond pour ces tailles (ce que fait le résumé).
- **Forme du carnet : deux mesures qui ne se recoupent pas.** (mon analyse) Le tableau de `05` §1 donne β ≈ 0,3–0,7 (concave) pour les 25 premiers niveaux ; le run à 400 niveaux donne β médian 0,6 à 1,17 (OKX BTC 1,00, OKX ETH 1,17, Coinbase BTC 1,10, Coinbase ETH 1,03). Donc la « concavité du top du carnet » disparaît quand on regarde plus loin pour BTC/ETH, ce qui répond en partie à la condition de renversement que `14` formule (« si la concavité persiste au-delà de 25 niveaux… »). Le rapport n'en tire pas la conséquence et ne réconcilie pas cette mesure avec l'exposant *du coût en N* (0,39–0,87, médiane 0,55, qui suggèrerait une profondeur plus convexe). Ces deux exposants ne sont pas le même objet ; sans réconciliation, l'affirmation « le synthétique est trop convexe » (`14` §2) reste incomplète.
- **Complétude des transactions** (6.5) : jusqu'à 19,6 % d'identifiants manquants sur OKX BTC. Les probabilités de remplissage et le V_jour de OKX en sont potentiellement affectés.
- **Drapeau d'agresseur Coinbase** : la règle des cotes ne s'accorde qu'à 25–33 % avec le drapeau ; inversé, 67–75 % : nettement moins bon qu'OKX/Kraken (70–85 %). Le spread réalisé et la sélection adverse Coinbase sont donc plus bruités.
- **Base USDT/USD** retirée comme constante (~2 bps) sur une fenêtre où elle n'est peut-être pas constante ; les tableaux cross-venue en dépendent (les auteurs disent que ce n'est pas de l'arbitrage, correct).
- **Roll = portage.** (mon analyse) La base des futures datés est de 4–5 % par an à toutes les échéances : le « coût de roll » de 34–150 bps par pas est en gros le coût de financement du temps. Il n'est un coût *en plus* dans un PAPER que si le PAPER valorise la position par rapport au spot/indice ; s'il valorise le contrat lui-même, il n'y a pas de perte à rouler (le prix du contrat de premier échéance et celui du suivant sont dans la même unité, la différence est un écart de niveau, pas une perte de valeur de portefeuille). Le rapport le traite comme une friction omise (E10) sans discuter cette dépendance de définition.
- **Funding entre bourses.** La corrélation 0,43/0,49 est calculée sur les niveaux de taux, qui sont beaucoup plus bruités autour de la ligne de base (0,01 % par 8 h = 1 bp) que sur une durée de détention de 7 jours. L'écart absolu moyen est 0,27–0,28 bps par 8 h (contre une moyenne de 0,44 bps sur Binance BTC) et l'écart moyen signé 0,09 : l'erreur cumulée sur une semaine serait de l'ordre de quelques bps, pas dix (non calculée par le rapport ; données OKX brutes non conservées, donc ? non vérifiable de mon côté). Le mot « proxy falsifié » (F20) est légitime pour un usage au règlement près, moins pour un budget hebdomadaire.
- **Funding historique** : 4 mois d'un seul régime (87 % de taux positifs). Les fenêtres glissantes de 30 jours sur 123 jours sont fortement chevauchantes (environ 4 fenêtres indépendantes) : l'intervalle p05–p95 de 20,27–57,75 bps est très mal estimé.
- **Emprunt** : unité du taux OKX non vérifiée ; l'illustration 5–50 % annuel est une hypothèse.
- **Sources non officielles** : chandelles FX/or via un endpoint Yahoo non documenté ; barèmes de frais d'après des agrégateurs secondaires avec contradictions internes.
- **Complétude des sondes OSS** : les clones sont dans `/tmp/oss_clones`, hors dépôt ; les résultats de fumée ne sont donc pas rejouables. Les stars/versions/nombre de mainteneurs sont UNKNOWN (API GitHub inaccessible).

### 7.4 Ce que les chiffres ne prouvent pas

- Que la marche du carnet prédit ce qu'un ordre réel paie (aucun ordre passé).
- Que les coûts de BTC/ETH/SOL sur trois grandes bourses un après-midi de septembre valent pour un autre jour, une autre heure, ou un jour de stress.
- Quoi que ce soit pour FX, or, matières premières côté cotes/carnets : rien n'a été mesuré ; seules la volatilité horaire et les sauts de session le sont.
- Que le simulateur synthétique reflète un marché : il a été écrit par l'auteur.
- Que « P\* dans la fourchette » signifie « indécidable » en général : c'est un cas de données publiques ; avec des ordres propres la fourchette se resserre.
- Que le contrat comptable est correct sur un vrai moteur PAPER (le rapport dit lui-même : non prouvé).
- Que 40 modèles ont été « falsifiés » : 26 lignes de falsification, 15 invalidations. Beaucoup d'« exécutions » sont des tests de fumée d'installation.

### 7.5 Écarts entre rapports, résultats bruts et contradictions internes

Écarts avec les résultats bruts (les seuls que j'ai trouvés, tous mineurs ou de prose) :
1. `00` §3 « ×3 … ×700 » : maximum recalculé ×370 (Roll, OKX BTC) ✘.
2. `07` §3.1/`12` F8 : « MAE à 30 s seulement 7–20 % au-dessus de 4 s » : vrai en médiane (+10 %), faux pour 21 paires sur 92 (> +20 %) dont 4 > +50 % ✘.
3. `04` §3 « ≤ 0,03 bps » pour la stabilité aux graines : 0,039–0,041 pour quatre modèles ✘ (minime).
4. `05` : « Per-venue walk costs differ by ×1.7–1.9 » (100 k USD : BTC 0,34–0,61, ETH 0,78–1,45, SOL 3,1–5,2) : ces plages viennent du run 25 niveaux. Dans le run profond la dispersion BTC 100 k est 0,29–0,77 (×2,65) ; `07` cite d'ailleurs cette plage plus large. Le ×1,7–1,9 sous-estime la dispersion BTC ✘ (mineur).
5. `README` : « data/vision NOT committed » alors que 580 Ko de `data/vision` le sont ✘ (mineur ; précisément : funding et bookDepth committés, aggTrades et klines exclus).
6. `00` : « σ√L à ~15 % près à ≥ 4 s » : ✔ à la marge (11–16 %).

Contradictions internes :
1. `00` (titre 2) « near-unbiased across scenarios and data » contre `04` (biais 13,25 bps en `gap`, 4,27 en `withdraw`, TEST moyen 2,13).
2. `03` vs `13` : `bidask` ADOPT_REFERENCE (03) contre ADAPT_CANDIDATE (13) ; Almgren–Chriss ADAPT_CANDIDATE (03) contre PARK (13). Les deux fichiers ne peuvent pas servir tous deux de référence des verdicts.
3. `00` : « Executed and falsified 40 of 51 » contre `12` (26 lignes, dont 15 invalidations, 1 circulaire, 1 intestable, 1 inconclusive) : « exécutés » n'est pas « falsifiés ».
4. `00` §7 « Timing … ~zero-mean, until flow or a gap says otherwise » est cohérent avec `10`, mais la ligne « σ√L holds within ~15 % at ≥ 4 s » est mesurée sur des photos à 2 s : c'est le régime *minimum* d'échantillonnage.
5. `14` §3 : « Live capture … 3 assets × 3 venues » et `README` : « ~8 min deep » ; le résumé parle de « 58-minute capture ». Cohérent (50+8) mais formulé de trois façons.
6. `06` : « Kraken BTC spread_mean 0,038, p95 0,012 » : possible, mais montre que la moyenne est portée par de rares élargissements ; la conclusion « la moyenne ne suffit pas, utiliser la distribution » (dite en `06` §1) est bien la bonne.

### 7.6 Ce qui est vraiment solide (mon analyse)

- La structure de raisonnement « UNKNOWN ≠ ZERO » et l'interdiction de double comptage sont des idées justes, simples et bon marché.
- Les mesures de coût de marche par taille (0,3–0,8 bps à 100 k USD pour BTC, jusqu'à 60 bps pour SOL à 3 M USD sur OKX) sont dans un ordre de grandeur crédible et recalculables.
- Le constat « le 5 bps par défaut est faux dans les deux sens » est robuste : il tient sur le synthétique et sur le live, sans dépendre d'un modèle.
- Le constat « les proxys de spread par bougies ne sont pas des cotes » est robuste : trois sources indépendantes (live, Vision, synthétique).
- Le constat « on ne peut pas identifier la probabilité d'exécution passive avec des données publiques » est structurel et bien argumenté.
- La reproductibilité mécanique est excellente (section 9).

---

## 8. Comparaison de plusieurs runs

Il n'y a **qu'une branche** (pas de variante « -b » ; `git branch -r` montre `-b` pour d'autres lanes seulement). La comparaison utile est entre les **deux captures** de la lane (run 25 niveaux ≈ 50 min contre run 400 niveaux ≈ 8 min, mêmes séries, fenêtres consécutives), et entre le monde synthétique et le monde réel. Tableau point par point (vérifié, `empirical_live.json` vs `empirical_deep.json`) :

| série | spread moyen live / deep | β médian live / deep | σ (bps/√s) live / deep | marche 100 k live / deep | marche 300 k live / deep | V_jour proxy (Md USD) live / deep |
|---|---|---|---|---|---|---|
| OKX BTC | 0,012 / 0,012 | 0,31 / 1,00 | 0,773 / 0,633 | 0,37 / 0,33 | 0,69 / 1,06 | 0,56 / 0,56 |
| OKX ETH | 0,037 / 0,039 | 0,41 / 1,17 | 1,009 / 0,946 | 0,78 / 1,15 | 1,38 / 2,22 | 0,28 / 0,43 |
| OKX SOL | 0,826 / 0,824 | 0,44 / 0,71 | 1,355 / 1,32 | 3,13 / 2,67 | 7,19 / 6,37 | 0,17 / 0,16 |
| Coinbase BTC | 0,069 / 0,045 | 0,63 / 1,10 | 0,818 / 0,698 | 0,61 / 0,77 | 1,09 / 1,32 | 0,89 / 0,59 |
| Coinbase ETH | 0,287 / 0,312 | 0,55 / 1,03 | 1,024 / 0,965 | 1,44 / 1,46 | 1,96 / 2,31 | 0,53 / 1,25 |
| Coinbase SOL | 1,151 / 1,05 | 0,66 / 0,77 | 1,396 / 1,299 | 5,24 / 3,95 | 9,92 / 7,47 | 0,17 / 0,40 |
| Kraken BTC | 0,038 / 0,018 | 0,58 / 0,77 | 0,754 / 0,68 | 0,34 / 0,29 | 0,42 / 0,41 | 0,24 / 0,18 |
| Kraken ETH | 0,191 / 0,162 | 0,62 / 0,87 | 0,937 / 0,924 | 1,45 / 1,63 | 2,01 / 2,49 | 0,09 / 0,09 |
| Kraken SOL | 0,942 / 1,044 | 0,73 / 0,62 | 1,407 / 1,305 | 3,53 / 3,62 | 5,60 / 5,72 | 0,11 / 0,13 |

Où ils s'accordent : spread (à 0,001–0,1 bps près), σ (à ~10–20 %), ordre des coûts entre actifs (BTC < ETH < SOL), écart de dispersion entre bourses, marche à 100 k (sauf OKX ETH +47 %, Coinbase SOL −25 %).

Où ils divergent et pourquoi (probable) :
- **β** : 0,31–0,73 contre 0,62–1,17. Le run à 25 niveaux ne voit que le tout début du carnet (1,8–3,6 bps sur BTC/ETH), la pente y est forte ; le run à 400 niveaux voit 13–600 bps de profondeur, la pente moyenne se rapproche de 1. C'est de la géométrie de fenêtre, pas un changement de marché (INFERENCE).
- **Marche 300 k** : OKX BTC 0,69 → 1,06 (+54 %), OKX ETH 1,38 → 2,22 (+61 %) : sur le run à 25 niveaux, 300 k n'est couvert que par 72–78 % des photos (moyenne conditionnelle aux photos assez profondes, donc biaisée vers le bas) — cause probable (INFERENCE), en plus de la fluctuation d'une fenêtre à l'autre.
- **V_jour** : divergences jusqu'à ×2,4 (Coinbase ETH), effet d'un échantillon court de trafic ; la loi en racine carrée dépend de V_jour.

Comparaison synthétique / réel (points communs de sens, pas de chiffres) :
| question | synthétique | réel | accord ? |
|---|---|---|---|
| coût croît avec la taille | oui (base 0,65 → 5,60 bps de 10 k à 10 M USD) | oui (BTC 0,01 → 5,25 bps de 1 k à 3 M USD, OKX) | oui, ordre de grandeur cohérent pour BTC ; le synthétique est plus cher à petite taille (0,125 bps de plancher, spread 1 bp) |
| demi-spread seul sous-facture | −5,1 bps à 10 M USD (base) | erreur absolue 5,54 bps à 3 M USD sur OKX BTC contre 0,525 pour la marche (`07` §3.2, run profond) | oui, même sens |
| constante calibrée transporte mal | (non testé) | 60–80 % d'erreur médiane | — |
| sélection adverse du maker | présente en synthétique par construction (couplage flux–prix λ_flow) | +0,29…+1,40 bps, IC exclut 0 dans 16/18 | oui, mais le synthétique la contient par construction |
| latence : bruit σ√L | exact par construction | +11 % à +16 % à 4 s | oui |
| brownien optimiste pour fill passif | MAE 0,21 (égale à la constante) | +0,17 (biais) | le synthétique ne montre pas de biais fort (+0,18), le live +0,17 : similaire |

---

## 9. Reproductibilité

### 9.1 Ce que j'ai relancé, et le résultat

Environnement : Python 3.11.15, numpy 2.4.6, pandas 3.0.6, scipy 1.17.1, `requests` présent ; 4 cœurs. Copie de travail dans mon dossier temporaire (rien dans le dépôt).

| Commande (depuis `bench/execution_cost_v1`) | Durée mesurée | Résultat |
|---|---|---|
| `python3 synthetic/run_synth.py` | 62 s | fichiers identiques à ceux de la branche (`competing`, `fullfill`, `latency_fragmentation`, `limit_fills`, `sliced`, `single_orders.csv`, `truth_decomposition.csv`, `single_seed_stability`, `spread_estimators_synth`) ; seul `single_params_timing.json` diffère (12 valeurs de chronométrage µs/prédiction) |
| `python3 contract/tests_and_threats.py` | 3,5 s | `threat_matrix_and_contract_tests.json` identique |
| `python3 analysis/empirical_live.py data/live live` puis `… data/deep deep` | ≈ 5,8 s (avec les deux LOO) | `empirical_live.json` et `empirical_deep.json` identiques |
| `python3 analysis/transport_loo.py live` / `deep` | inclus | `transport_loo_live.json`, `transport_loo_deep.json` identiques |
| `python3 build_reports.py` | 2 s | 15 rapports identiques aux rapports de la branche, sauf la colonne µs/prédiction du tableau de `04` |

Le README annonce « ≈ 1–2 min, deterministic » pour le banc synthétique : ✔ (62 s + 3,5 s).

### 9.2 Ce que je n'ai pas pu relancer (honnêtement)

- `analysis/funding_borrow_roll.py`, `analysis/fx_gold_ohlc.py` : appellent OKX et Yahoo en direct ; le résultat dépend de l'instant (courbe des futures, taux courants). Je ne les ai pas exécutés (un nouvel appel ne redonnerait de toute façon pas les mêmes chiffres) ; les fichiers de résultats de la branche sont les seuls. J'ai néanmoins recalculé les statistiques de funding Binance depuis les zips committés, et les chiffres FX/or depuis `data/ohlc/*.csv` (mais le script relit Yahoo au lieu d'utiliser les CSV committés : inconvénient).
- `analysis/empirical_vision.py` : a besoin de `data/vision/aggTrades_*.zip` et `klines_*.zip`, exclus par `.gitignore` et absents du dépôt ; `analysis/fetch_vision.sh` les retélécharge depuis `data.binance.vision` (les liens de septembre 2026 pourraient ne plus être là ou être modifiés). Résultat lu dans `empirical_vision.json` (non revérifié depuis les données brutes).
- `analysis/oss_bidask_test.py` : demande un environnement Python avec `bidask` installé (chemin `/tmp/venvs/bidask`, hors dépôt), version non figée (`bidask_version: "?"` dans `oss_bidask_edge.json`) et les klines Binance absents.
- `capture/live_capture.py` : dépend du temps ; les fichiers bruts utilisés sont committés (`data/live`, `data/deep`) ✔ : c'est le bon choix.
- Les sondes OSS (21 dépôts) : clonés dans `/tmp/oss_clones`, hors dépôt ; seuls les comptes rendus (`oss_findings.*`) sont fournis.

### 9.3 Ce qui est fourni / ce qui manque

Fourni : code complet du banc, modèles, contrat, analyses, captures brutes live et deep (10 Mio de données), résultats agrégés, gabarits de rapport + générateur, notes de littérature et de sonde OSS.
Manque : fichier de dépendances (aucun `requirements.txt`/`pyproject`/lock dans la lane) ; versions figées de `bidask` ; données Vision volumineuses ; clones OSS ; historique brut OKX de funding (seules ses statistiques sont dans le JSON) ; scripts de test de la complétude des transactions capturées.

### 9.4 Note sur le déterminisme d'environnement

Les fichiers de résultats produits ici sont identiques sous numpy 2.4.6 / pandas 3.0.6. Rien ne prouve qu'ils le soient sous d'autres versions (par exemple `pd.Series.rolling`, `np.percentile`) ; c'est un risque courant, non testé.

---

## 10. Implications pratiques pour AurumShift (pistes à adjuger plus tard)

Rappel de frontière (`claude.md`) : **rien ci-dessous n'affirme que quoi que ce soit est compatible avec AurumShift.** Je n'ai pas vu le code d'AurumShift. Ce sont des pistes à examiner contre le vrai dépôt local.

1. **Question préalable, à trancher chez AurumShift** : le moteur PAPER remplit-il aujourd'hui à un prix milieu, au prix de la dernière transaction, à la clôture de bougie, ou déjà avec un spread/glissement fixe ? Le contrat de la lane (`11` §3) dépend entièrement de la « base de remplissage » (MID/TOUCH/BOOK_VWAP/BAR_CLOSE/…). C'est la première information à extraire pour savoir quelles lignes de coût existent déjà. (UNKNOWN)
2. **Disposer ou non d'historique L2** : si AurumShift voit déjà des carnets, la marche du carnet (avec drapeau « profondeur insuffisante » et bande de péremption) est la piste la moins chère et la mieux étayée du rapport ; sinon, le rapport ne supporte que le prior en racine carrée avec bande ±50–100 %. (UNKNOWN pour AurumShift)
3. **Contrat « UNKNOWN ≠ 0 »** : idée directement transposable en principe (une ligne de coût inconnue ne doit jamais valoir zéro dans un résultat net ; le net est retenu ou donné comme intervalle). À évaluer : où vit aujourd'hui un « coût inconnu » dans AurumShift, et est-il représentable sans nouveau service ni nouveau stockage (le rapport dit NON pour les deux, mais sans avoir vu AurumShift).
4. **Coûts de détention** : funding par bourse, aux instants de règlement, sur le notionnel réellement détenu ; borrow `UNKNOWN` sauf taux fourni ; roll réservé aux futures datés. Piste à évaluer si AurumShift trade des perpétuels ; attention à la définition de la valorisation avant de rajouter un « coût de roll » (7.3).
5. **Bande de latence σ√L** : cheap à ajouter comme incertitude, pas comme biais ; à condition d'estimer σ à l'horizon de latence (et pas par extrapolation d'un σ à la minute).
6. **Choix du carnet** : quel carnet un PAPER « marche »-t-il (une bourse, agrégé, celui où l'ordre serait réellement routé) — l'erreur est de ×1,4 à ×3,3 en synthétique, ×1,7–2,65 entre bourses en live.
7. **Ce qui doit rester UNKNOWN** dans tout PAPER tant que rien de plus n'est fait : coûts de cotes/carnets pour FX, or, matières premières ; probabilité d'exécution des ordres passifs ; impact d'un ordre multi-enfants ; emprunt ; conditions de stress.
8. **Éviter les faux amis** que la sonde OSS a trouvés : un `spread` en demi-spread par côté (`backtesting.py`), un funding manquant qui devient 0 (`freqtrade`), un glissement constant (`vectorbt`), un modèle de fill Bernoulli (`nautilus`). Si AurumShift utilise un de ces outils, c'est à vérifier. (UNKNOWN)
9. **Aucune dépendance à adopter** : la lane recommande des formules et un schéma, pas d'installer un dépôt.

---

## 11. Questions ouvertes et suites recommandées (classées par valeur)

1. **Mesurer un coût réalisé, même modeste.** Quelques centaines de petits ordres réels ou de testnet pour comparer la marche du carnet au prix obtenu. C'est le seul test qui peut renverser le verdict (`14`) ; sans lui, « supporté » signifie « cohérent avec la photo suivante ». (Hors mandat de cette lane, qui interdit tout ordre.)
2. **Capture longue au débit des messages (WebSocket) sur plusieurs jours, avec jour/nuit/week-end.** Permet le spread effectif correct, la limite Δ→0 de la péremption, les régimes de stress ; à combiner avec des intervalles de confiance et la complétude des transactions vérifiée par identifiants.
3. **Quotes de courtier pour une paire FX et l'or** : c'est le grand trou du domaine cible (`MODEL_NOT_EMPIRICALLY_CALIBRATABLE_FROM_FREE_DATA`).
4. **Réconcilier les deux mesures de forme du carnet** (β par niveaux vs exposant du coût en N) et refaire le synthétique avec un carnet calibré sur le run à 400 niveaux ; puis relancer la comparaison des modèles.
5. **Refaire les tests dégénérés** : classement de calendriers avec un critère risque/coût (variance) et un cas où le meilleur nombre de tranches n'est pas le maximum ; grille maker/taker avec dérives plausibles (≤ 0,1 bps/s) et distributions plutôt que trois niveaux.
6. **Comparer EDGE et Corwin–Schultz à conditions égales** (même durée de barre) et produire une courbe erreur vs nombre de barres pour justifier « ≥ 1 000 ».
7. **Quantifier l'effet des transactions manquantes** sur `P_haut`, `P_bas` et sur le V_jour (par ré-échantillonnage à partir des identifiants), et corriger `Vday_proxy` (durée plus longue, source de volume officielle).
8. **Relier « coût de roll » et « coût de portage »** : dire clairement dans quelle valorisation le roll est un coût additionnel.
9. **Corriger les incohérences de texte** (7.5) : ×700, 7–20 %, ≤ 0,03, cohérence `03`/`13`, README.
10. **Ajouter un `requirements.txt`, figer la version de `bidask`, ajouter les zips Vision ou un hash de contrôle**, et faire lire les CSV de `data/ohlc` par `fx_gold_ohlc.py`.
11. **Valider le contrat sur un vrai moteur PAPER** (phase locale, hors dépôt externe).
12. **Étendre la fenêtre de funding** au-delà de 4 mois et à d'autres bourses avant de chiffrer des budgets de détention ; vérifier l'unité du taux d'emprunt OKX.

---

## 12. Index des fichiers lus

Tous les chemins sont sur la branche `origin/claude/execution-cost-intelligence-v1` (`reports/006_execution_cost_intelligence/` = `R/`, `bench/execution_cost_v1/` = `B/`). « Lu » = lu en entier ; « extrait » = lu partiellement ou par extraction de chiffres.

### Rapports (lus en entier)
- `R/00_EXECUTIVE_SUMMARY.md` — résumé, constats, régimes de données, bloc final.
- `R/01_THREAT_MODEL.md` — matrice de menaces E1–E15, contrat, tests.
- `R/02_MODEL_LANDSCAPE.md` — carte A–L, corrections, annexe de notes sourcées (barèmes de frais, formules `[M]`/`[V]`).
- `R/03_OSS_COMPONENTS.md` — sonde de 21 dépôts, EDGE, annexes par candidat.
- `R/04_SYNTHETIC_BENCH.md` — monde synthétique, modèles, découpage, concurrence, latence, fills.
- `R/05_PUBLIC_DATA_EXPERIMENT.md` — sources, captures, profondeur, cross-venue, FX/or.
- `R/06_SPREAD_MODELS.md` — spread coté, effectif, réalisé, retournement, proxys OHLC, EDGE.
- `R/07_SLIPPAGE_IMPACT.md` — modèles de glissement, marche live, péremption, transport, impact agrégé, comptabilité.
- `R/08_FILL_MODELS.md` — fills au marché et passifs, bornes, brownien.
- `R/09_FUNDING_BORROW_ROLL.md` — funding, emprunt, roll.
- `R/10_MAKER_TAKER_LATENCY.md` — règle maker/taker, sélection adverse, latence.
- `R/11_ACCOUNTING_CONTRACT.md` — échelle de prix, états, bases de remplissage, tests.
- `R/12_FALSIFICATION.md` — F1–F26.
- `R/13_ADJUDICATION.md` — 51 modèles et verdicts.
- `R/14_LIMITATIONS.md` — limites et conditions de renversement.

### Code, README, protocole
- `B/README.md` — plan du banc et commandes.
- `B/.gitignore` — exclut aggTrades et klines Binance.
- `B/synthetic/synth.py` — générateur de vérité (lu en entier).
- `B/synthetic/run_synth.py` — expériences et graines (lu en entier).
- `B/models/models.py` — modèles de coût, remplissage, estimateurs de spread (lu en entier).
- `B/contract/cost_contract.py`, `B/contract/tests_and_threats.py` — contrat et tests (lus en entier).
- `B/analysis/empirical_live.py`, `transport_loo.py`, `funding_borrow_roll.py`, `empirical_vision.py`, `fx_gold_ohlc.py`, `oss_bidask_test.py`, `fetch_vision.sh` — lus en entier.
- `B/capture/live_capture.py` — poller REST (lu en entier).
- `B/build_reports.py` — générateur de tableaux (lu en grande partie : l.1–80, 225–300 ; le reste extrait par grep).
- Il n'existe pas de fichier de protocole/pré-enregistrement dans la lane (constat).

### Résultats
- `B/results/threat_matrix_and_contract_tests.json`, `competing.json`, `single_params_timing.json`, `_table_names.json` — lus (extraits significatifs).
- `B/results/single_orders.csv`, `truth_decomposition.csv` — lus par extraction (en-têtes + recalcul du résumé).
- `B/results/sliced.json`, `limit_fills.json`, `single_seed_stability.json`, `fullfill.json`, `latency_fragmentation.json`, `spread_estimators_synth.json` — analysés par script (agrégats et cellules clés).
- `B/results/empirical_live.json`, `empirical_deep.json`, `transport_loo_live.json`, `transport_loo_deep.json` — analysés par script (tous les champs utilisés dans mes vérifications).
- `B/results/empirical_vision.json`, `funding_borrow_roll.json`, `fx_gold_ohlc.json`, `oss_bidask_edge.json` — lus (chiffres clés).

### Données et sonde OSS
- `B/data/live/*`, `B/data/deep/*` (`jsonl.gz`, 29 + 29 fichiers) — échantillonnés et recalculés par script (spreads, marche du carnet, complétude d'identifiants, décalage d'horloge).
- `B/data/vision/fund_*_2026-0*.zip`, `bookDepth_um_BTCUSDT_2026-09-20.zip` — lus (funding recalculé). `aggTrades`/`klines` : absents du dépôt.
- `B/data/ohlc/*.csv` — recalcul de σ et des sauts.
- `B/oss_probe/oss_findings.json` — lu partiellement (noms, licences, verdicts des 21 dépôts). `B/oss_probe/oss_findings.md` — non lu séparément (son contenu correspond à l'annexe de `R/03`, lue en entier). `B/oss_probe/landscape_notes.md` — comparé par différence à l'annexe de `R/02` : identique, sauf une ligne vide.
- `B/report_templates/*.md` — comparés aux rapports par régénération complète (différences = tableaux substitués) ; `12` et `14` identiques à leur gabarit.

### Fichiers du dépôt hors lane
- `claude.md` (doctrine, contraintes) et `analyses/LANE_004_pit_safe_evidence_replay.md` (format de référence, lu en tête seulement).

### Non lu / non vérifiable
- Les zips Binance `aggTrades`/`klines` (absents), le détail ligne à ligne des `jsonl.gz` (échantillonné), les clones OSS (hors dépôt), les pages officielles de frais des bourses (non consultées par moi), les références bibliographiques (non rouvertes par moi).
