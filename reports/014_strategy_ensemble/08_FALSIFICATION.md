# 08 — Falsification

Hypothèses testées par des scénarios qui pouvaient les réfuter, et résultat (held-out, 30 graines, IC 95 % appariés).

| # | Hypothèse | Test | Résultat |
|---|---|---|---|
| H1 | Les poids statiques suffisent | STATIC vs EQUAL/EWMA | **Réfutée pour la robustesse** : 0,92 ≈ égal ; pire qu'égal en S6 (1,24, IC>0) ; échoue nouvel expert/rare/dormance. |
| H2 | Un EWMA de performance récente suffit | EWMA vs tous | **Partiellement réfutée** : meilleure baseline (0,55), EWMA bat SLEEP_HEDGE dans 10/11 scénarios ; mais pire qu'EG/Fixed-share en moyenne (−0,06/−0,05, ≈ δ), pire qu'égal-proche en S1 (0,98), écart pire-cas 0,30, échoue nouvel expert et rare. |
| H3 | Le Hedge endormi simple est la référence | SLEEP_HEDGE | **Réfutée comme méthode gagnante** : η optimal ≈ égal (0,73). Le *mécanisme* (aucune mise à jour au repos, masse conservée) est en revanche nécessaire (ablations ci-dessous). |
| H4 | « Inactif » peut être traité comme mauvais sans conséquence | `*_INACTIVE_NEG` | **Réfutée (PROVEN)** : EWMA 0,55→1,16 ; SLEEP_HEDGE 0,73→1,35 ; pire qu'égal dans 6 et 9 scénarios respectivement. |
| H5 | « Preuve manquante » peut être traitée comme mauvaise | `*_MISSING_NEG` | **Réfutée là où la preuve manque** (S1 seulement : +1,55 EWMA, +1,21 SLEEP) ; sans effet ailleurs (attendu). |
| H6 | La conservation de masse du bloc endormi compte | `*_NOMASS` | **Confirmée** : SLEEP_NOMASS pire de +2,03 en S5, +1,11 en S1, +0,60 en S4b ; EG_NOMASS +0,25 en S1 (mais SLEEP_NOMASS est *meilleur* de 0,05–0,24 dans cinq scénarios (S0, S2, S4a, S7, S8) : sans conservation le Hedge s'ancre plus vite sur le spécialiste — gain local, danger global). |
| H7 | Un bandit suffit | EXP3, ε-greedy | **Réfutée** : 3,84 et 3,36 (3–4× pire qu'égal). Sélectionner un seul expert avec retour partiel jette la moyenne d'erreurs. |
| H8 | Le winner-take-all suffit | WTA | **Réfutée** : 2,42 ; pire qu'égal dans 9 scénarios. Meilleur en famine (nouvel expert 0,76 de part, rare 0,94) mais catastrophique en bruit. |
| H9 | La diversité explicite aide | DIVERSITY | **Réfutée en général** (+0,19 vs Fixed-share) ; vraie en S6 seulement ; EG fait mieux sans terme dédié. |
| H10 | Le contexte règle la famine du spécialiste rare | CONTEXT_MIX | **Confirmée pour S8 uniquement** (part 0,63) ; **réfutée globalement** (S6 1,73, S5 0,90, S7 0,83). |
| H11 | La décote « horloge » oublie les dormants | DISC_CLOCK vs DISC_AWAKE | **Non démontrée** (S9 : pas de différence de récupération ; en moyenne 0,65 vs 0,56 en faveur de DISC_AWAKE). |
| H12 | Une bibliothèque OSS d'ensemble gère les experts endormis | river EWARegressor | **Réfutée** : API sans masque ; remplissage forcé ⇒ 1,5–4× pire qu'égal à ses meilleurs pas testés. |

## Ce qui réfuterait nos conclusions
Si les erreurs des experts réels sont fortement autocorrélées ou hétéroscédastiques d'une façon absente du banc ; si la perte utile est un P&L net de coûts plutôt qu'un Brier ; si les régimes réels ne sont pas observables au contexte donné (ici étiquette à 10 % de bruit). Rien de cela n'est testé.
