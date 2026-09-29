# 04 — Experts endormis / spécialistes

Résultats held-out (30 graines, T=5000). nrm = (mse − oracle)/(égal − oracle) : 0 = oracle, 1 = poids égaux, <0 = bat l'oracle (qui ignore les corrélations). Hyperparamètres choisis sur tuning seul, un jeu par méthode pour tous les scénarios.

| Scénario | STATIC | EWMA | HEDGE_CUM | SLEEP_HEDGE | EG | BMA | FIXED_SHARE | DISC_AWAKE | MPP | CONTEXT | DIVERS. |
|---|---|---|---|---|---|---|---|---|---|---|---|
| S0 base | 0,93 | 0,74 | 0,65 | 0,92 | 0,68 | 0,98 | 0,71 | 0,65 | 0,73 | 0,58 | 0,77 |
| S1 lacunes | 0,91 | 0,98 | 0,99 | 0,87 | 0,74 | 0,88 | 0,79 | 0,74 | 0,83 | 0,67 | 0,82 |
| S2 leadership | 0,94 | 0,35 | 0,43 | 0,40 | 0,41 | 0,39 | 0,33 | 0,38 | 0,39 | 0,66 | 0,64 |
| S3 récurrence | 0,72 | 0,27 | 0,31 | 0,30 | 0,24 | 0,33 | 0,15 | 0,45 | 0,32 | 0,26 | 0,72 |
| S4a nouveau bon | 0,90 | 0,53 | 0,53 | 0,71 | 0,57 | 0,76 | 0,42 | 0,61 | 0,58 | 0,46 | 0,75 |
| S4b nouveau mauvais | 0,94 | 0,76 | 0,76 | 0,92 | 0,71 | 0,99 | 0,72 | 0,63 | 0,74 | 0,61 | 0,82 |
| S5 retrait/retour | 0,90 | 0,71 | 1,68 | 0,84 | 0,62 | 0,91 | 0,66 | 0,64 | 0,75 | 0,90 | 0,78 |
| S6 corrélés | 1,24 | 0,02 | 0,86 | 0,85 | −0,27 | 0,64 | 0,11 | 0,25 | 0,29 | 1,73 | −0,02 |
| S7 sous-perf. | 0,92 | 0,57 | 0,56 | 0,85 | 0,57 | 0,94 | 0,57 | 0,54 | 0,61 | 0,83 | 0,68 |
| S8 rare | 0,90 | 0,73 | 0,66 | 0,89 | 0,68 | 0,94 | 0,68 | 0,66 | 0,70 | 0,58 | 0,76 |
| S9 longue lacune | 0,85 | 0,38 | 0,47 | 0,43 | 0,40 | 0,44 | 0,28 | 0,58 | 0,39 | 0,30 | 0,75 |
| **moyenne** | 0,92 | 0,55 | 0,72 | 0,73 | **0,49** | 0,74 | **0,49** | 0,56 | 0,58 | 0,69 | 0,68 |

Rappel : HEDGE_CUM, WTA, EXP3, EPS_GREEDY et STATIC sont pires qu'égal ou proches ; voir 08 pour WTA (2,42) et bandits (3,4–3,8).

## Lecture (PROVEN dans le banc)
- **Le mécanisme endormi en lui-même (SLEEP_HEDGE) est correct mais insuffisant** : partout mieux que poids égaux (−0,275 en moyenne, meilleur dans les 11 scénarios), mais η optimal = 0,03, quasi-égal, car des poids *globaux* cumulés ne suivent pas des experts dont la qualité dépend du régime. Il est significativement pire qu'EWMA dans 10 scénarios sur 11 (meilleur seulement en S1).
- **EG et Fixed-share** ajoutent le suivi (η plus grand avec ré-injection ou gradient centré) : −0,238 et −0,231 par rapport à SLEEP_HEDGE en moyenne, mieux dans 10–11 scénarios. Vs EWMA : EG mieux dans 7 scénarios, pire dans 3 (S2, S4a, S9) ; Fixed-share mieux dans 9, pire en S6 (+0,095).
- **Effet de la mise à jour uniquement sur observations** : en S1 (preuve manquante à 30 %, lacunes à 12 %), EG (0,74) et Fixed-share (0,79) tiennent, EWMA tombe à 0,98 (presque égal) car son état se périme sans détection.
- **BMA (log-loss, sans oubli)** : température optimale κ=0,01 — c'est du poids quasi-égal ; un vrai postérieur bayésien s'effondre sur une hypothèse dans un environnement non stationnaire (INFERENCE cohérente avec la littérature sur le suivi ; non isolée par test dédié).
- **Corrélation des erreurs** : la mise à jour relative EG (0,1) bat l'oracle indépendant en S6 (nrm −0,27) parce que l'oracle surpondère les clones.

## Portes (03)
| Méthode | écart pire-cas | nouvel expert | rare | sous-perf. | dormance | robuste |
|---|---|---|---|---|---|---|
| EG | 0,149 ✔ | ✘ (0,31) | ✘ | ✔ | ✔ | non |
| FIXED_SHARE | 0,387 ✘ | ✔ (0,64) | ✘ | ✔ | ✘ | non |
| EWMA | 0,304 ✘ | ✘ (0,49) | ✘ | ✔ | ✔ | non |
| MPP | 0,566 ✘ | ✔ (0,58) | ✘ | ✔ | ✔ | non |
| DISC_AWAKE | 0,519 ✘ | ✘ | ✘ | ✔ | ✔ | non |
| CONTEXT_MIX | 1,999 ✘ | ✘ | ✔ | ✘ | ✔ | non (+pire qu'égal en S6) |
Détails : `results/summary_tables.md`, `results/adjudication.json`.
