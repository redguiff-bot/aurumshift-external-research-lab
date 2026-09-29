# 02 — Méthodes

Statut : **DOCUMENTED_CLAIM** = lu/recherché mais non revérifié dans le texte ; **VERIFIED_SEARCH** = existence et objet confirmés par recherche web dans cette session (titre, auteurs, résumé) ; **EXECUTED** = implémenté et exécuté dans `bench/ensemble_v1`.

## Découvertes (22)
| # | Méthode / source | Statut |
|---|---|---|
| 1 | Hedge / Exponentially Weighted Average (Littlestone–Warmuth 1994 ; Freund–Schapire 1997) | DOCUMENTED_CLAIM ; EXECUTED (HEDGE_CUM, SLEEP_HEDGE) |
| 2 | Exponentiated Gradient (Kivinen–Warmuth 1997) | DOCUMENTED_CLAIM ; EXECUTED (EG) |
| 3 | Specialists / abstention trick (Freund, Schapire, Singer, Warmuth, STOC 1997) | VERIFIED_SEARCH ; EXECUTED |
| 4 | Sleeping experts, régret de sommeil (Blum 1997 ; Blum–Mansour 2007 ; Kleinberg–Niculescu-Mizil–Sharma 2010) | DOCUMENTED_CLAIM ; référence conceptuelle |
| 5 | Fixed-share (Herbster–Warmuth 1998) | DOCUMENTED_CLAIM ; EXECUTED |
| 6 | Mixing past posteriors (Bousquet–Warmuth, JMLR 2002) | VERIFIED_SEARCH ; EXECUTED (version simplifiée : moyenne des postérieurs passés) |
| 7 | Putting Bayes to sleep (Koolen, Adamskiy, Warmuth, NIPS 2012) ; Freezing and sleeping (Adamskiy et al.) | VERIFIED_SEARCH ; non exécuté tel quel (approché par 5+6) |
| 8 | Growing number of experts : abstention + « muting trick » (Mourtada–Maillard, ALT 2017) | VERIFIED_SEARCH ; non exécuté (entrée à la moyenne géométrique des poids à la place) |
| 9 | Adaptation forte / décote (Hazan–Seshadhri ; Daniely et al. 2015 ; coin-betting, Jun et al. 2017) | DOCUMENTED_CLAIM ; décote EXECUTED (DISC_*), pas de coin-betting |
| 10 | Model averaging bayésien / algorithme d'agrégation (Vovk 1990 ; Hoeting et al. 1999) | DOCUMENTED_CLAIM ; EXECUTED (BMA, log-loss tempérée) |
| 11 | Mélange conditionné au contexte, EXP4 (Auer et al. 2002) | DOCUMENTED_CLAIM ; EXECUTED (CONTEXT_MIX, produit de poids global × contexte) |
| 12 | Pondération sensible à la diversité (décomposition d'ambiguïté Krogh–Vedelsby 1995 ; diversité effective de Leinster–Cobbold) | DOCUMENTED_CLAIM ; EXECUTED (DIVERSITY, rabais de similarité) |
| 13 | EXP3 (Auer et al. 2002) | DOCUMENTED_CLAIM ; EXECUTED (bandit, comparaison) |
| 14 | ε-greedy / UCB | DOCUMENTED_CLAIM ; ε-greedy EXECUTED |
| 15 | Thompson sampling | DOCUMENTED_CLAIM ; non exécuté |
| 16 | ML-Poly / BOA / paquet R `opera` ; `pyopera` (PyPI) | DOCUMENTED_CLAIM ; non exécuté |
| 17 | `river.ensemble.EWARegressor` (river 0.26.1) | OBSERVED (code lu) ; EXECUTED (sonde) |
| 18 | `river.model_selection.SuccessiveHalving*`, `river.bandit.*` | OBSERVED (existence) ; non exécuté |
| 19 | `mabwiser` | OBSERVED (installable) ; non exécuté |
| 20 | Follow-the-leader / winner-take-all | EXECUTED (WTA) |
| 21 | EWMA de performance récente | EXECUTED |
| 22 | Poids fixes / 1/N | EXECUTED (EQUAL, STATIC) |

## Exécutées (17 + ablations)
Baselines : EQUAL, STATIC, WTA, EWMA. Candidats : HEDGE_CUM (Hedge naïf sur perte cumulée observée), SLEEP_HEDGE, EG, FIXED_SHARE, DISC_AWAKE (décote seulement quand l'expert est mis à jour), DISC_CLOCK (décote à chaque tour, même endormi), BMA, MPP, SLEEP_FLOOR (poids plancher = pondération bornée), CONTEXT_MIX, DIVERSITY. Bandits : EXP3, EPS_GREEDY. Référence non candidate : ORACLE (variance inverse connue, ignore les corrélations, donc pas une borne stricte). Ablations : EWMA/SLEEP × {INACTIVE_NEG, MISSING_NEG}, EG_NOMASS, SLEEP_NOMASS.

## Cœur endormi (implémentation)
Log-poids persistants ; un expert dort ⇒ aucun changement. Sur les experts *observés* U : `lw_i −= η(ℓ_i − ℓ̂)` avec ℓ̂ moyenne des pertes de U sous les poids courants ; puis translation constante du bloc U qui **rétablit exactement sa masse postérieure** (normalisation spécialiste). Avec cette conservation, centrer ou non ne change rien (test unitaire) — un premier essai avec une conservation approchée était biaisé (voir 09, journal des écarts). Nouvel expert : entrée à la moyenne géométrique des log-poids connus. Perte : Brier (BMA : log-loss). Prévision : `ŷ = Σ w_i p_i` sur les experts éveillés ; si aucun n'est éveillé, 0,5.
Extensions : Fixed-share `v ← (1−α)v + α/K_connus` ; MPP `v ← (1−m)v + m·v̄_passé` (+ α = 0,01) ; décote `lw ← c + γ(lw − c)` ; plancher `w ← (1−f)w + f/n_éveillés` ; contexte `lw = lw_global + lw_ctx[c]` ; diversité `w_i ∝ w_i / n_i^θ`, `n_i = Σ_j sim_ij` (corrélation des résidus de logit de prévision, sans étiquettes).

## Tests unitaires (PROVEN, `results/unit_tests.json`)
η→0 ≡ EQUAL ; centrage sans effet avec conservation de masse ; poids relatifs des experts au repos gelés ; masse du bloc conservée ; tous les apprenants : poids ≥ 0, nuls sur endormis, somme 1 ; ORACLE meilleur qu'EQUAL ; aucune fuite du futur par construction (y_t n'est lu qu'après `weights()`).
