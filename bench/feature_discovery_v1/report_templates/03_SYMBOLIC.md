# 03 — Régression symbolique (GP)

Configuration (OBSERVED, `fd/symbolic.py`) : gplearn 0.4.3, population 300, 10 générations, tournoi 15, parcimonie 0.004, fonctions {add, sub, mul, div protégée, abs, neg, max, min, tanh}, profondeur init 2–4, constantes ∈ [−1, 1], 5 seeds (11, 23, 37, 41, 59), 20 000 lignes échantillonnées par seed, top-6 programmes de la dernière génération (≤ 15 nœuds), puis simplification gloutonne sur le score de validation pénalisé, puis gate.

## Résultats par seed (les deux cibles)

{{seeds}}

Constats (OBSERVED) :
- Après filtre « primitive triviale » (protocole §12.2) et gate, **0–3 programmes GP par seed** survivent ; aucune famille GP n'est retrouvée dans ≥ 60 % des seeds → **aucune expression symbolique gelée** (`SYMBOLIC_EXPRESSIONS_STABLE = 0`).
- `y_vol` : les meilleurs programmes GP (IC val 0.40–0.50) sont `sub(lvol_24, sub(lsz_1, lrv_24))`, `sub(neg(wknd), lrv_24)`, `sub(lnt_1, add(lvol_1, lrv_24))` : combinaisons **linéaires** de primitives, dont l'essentiel est `−lrv_24` (retour à la moyenne de la vol). Leur corrélation partielle vs ridge de mains est faible (0.004–0.155) et leurs formes changent d'une seed à l'autre → non consolidées. C'est le comportement attendu : un ridge sur primitives brutes contient déjà ces combinaisons.
- `y_ret` : les programmes (`add(dhi_72, ret_1h)`, `min(mag_168, hod_sin)`, …) ont un IC val de 0.025–0.05 mais ne se retrouvent pas d'une seed à l'autre.
- La simplification gloutonne (remplacement de sous-arbres par un enfant/0 si le score pénalisé ne baisse pas) vise les « hitchhikers » du GP ; son effet propre n'a pas été isolé par une ablation dédiée (UNKNOWN).

## Puissance du GP dans l'arène (vérité connue, PROVEN sur synthétique)

Composante non-linéaire pure `(z3² − 1)` : retrouvée dans **27.5 %** des réplications MIXED. Le GP est donc le maillon faible du pipeline : il peut *rater* du signal non linéaire. Il n'a jamais produit de faux positif stable sous H0 (voir 08).

## Cartes d'interprétabilité

Aucune expression symbolique n'est retenue ; les cartes des deux formules gelées (issues de la recherche d'interactions) sont dans `05_INTERACTIONS.md`.

## Verdict (INFERENCE)

Sur ces primitives et cet horizon, le GP **ne trouve rien qu'un lasso n'ait déjà** ; son coût (instabilité inter-seeds, temps, besoin de simplification/pénalités) n'est pas justifié. → **PARK**.
