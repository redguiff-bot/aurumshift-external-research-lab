# 06 — Stabilité (seeds × marchés × temps × held-out)

## Entre seeds
Consolidation des familles de candidats par corrélation de rang ≥ 0.85 sur validation ; garde ≥ 60 % des seeds (3/5).
`y_ret` : 11 familles → 1 gardée (`ret_24h × wknd`, 3/5 seeds). `y_vol` : 9 familles → 1 gardée (`ret_72h × sgn(mag_168)`, 5/5 seeds). Détail : tableau seeds dans `03_SYMBOLIC.md` ; la seed 37 de `y_ret` n'a trouvé aucune interaction.

## Entre marchés et périodes (train + val)
Environnements = 4 marchés × années civiles (16) ; invariance des pentes (Cochran-Q, erreurs HAC lag 48) :

{{invariance}}

- `y_vol / C01` : Q **rejette** l'homogénéité sur train+val (p = 0.0004) bien que le signe soit identique partout : la pente varie en amplitude (0.011–0.113 selon environnement). Sur les 9 marchés held-out, Q ne rejette pas (p = 0.86), signe 9/9 → **association d'un signe stable, d'amplitude variable** ; classée `PREDICTIVE`, pas `INVARIANT_ASSOCIATION` (la classe exige les deux Q ≥ 0.05).
- `y_ret / C01` : signes 10/16 puis 5/9 → pas de signe cohérent (cohérent avec IC ≈ 0).

## Held-out
Une seule lecture (verrou `results/heldout_lock.json`), 9 marchés dont 5 jamais vus. Voir 05. Placebo réel : la cible held-out est décalée circulairement (même décalage pour tous les marchés), 20 fois ; taux de « p<0.05 » :

{{placebo}}

Taux observé 0 % et 5 % (1/20) : compatible avec le niveau nominal (INFERENCE ; 20 tirages = faible résolution).

## Ce qui a été *volontairement pas fait*
Aucune sélection de formule sur le held-out, aucun re-run, aucun ajustement de seuil après lecture. Le script `05_heldout_once.py` refuse de se relancer.
