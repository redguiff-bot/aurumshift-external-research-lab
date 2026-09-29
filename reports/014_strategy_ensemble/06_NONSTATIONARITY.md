# 06 — Non-stationnarité (held-out, nrm ; voir tableau 04)

- **Changements de leadership (S2)** : EWMA 0,35, Fixed-share 0,33, DISC_AWAKE 0,38, SLEEP_HEDGE 0,40, EG 0,41. Fixed-share (ré-injection) mieux qu'EWMA (−0,015, faible). CONTEXT_MIX (0,66) et DIVERSITY (0,64) traînent : un contexte de régime ne dit rien d'un changement de leadership *hors régime*. STATIC 0,94.
- **Récurrence de régimes (S3)** : les méthodes à mémoire longue gagnent (Fixed-share 0,15 ; EG 0,25 ; CONTEXT_MIX 0,26). DISC_* (0,45–0,51) oublient. WTA (0,47) et STATIC (0,72) ne profitent pas.
- **Nouvel expert (S4)** : voir 05. Le nouveau bon expert est mieux exploité par Fixed-share (0,42) et CONTEXT_MIX (0,46) que par EWMA (0,53) ; EG et DISC sont plus lents (0,57–0,61) ; SLEEP_HEDGE/BMA (0,71–0,76) quasi-égal.
- **Expert qui disparaît puis revient dégradé (S5)** : pas de mécanisme spécial ; les poids rendent bien : EG 0,62 ; DISC_AWAKE 0,64 ; EWMA 0,71 ; **HEDGE_CUM 1,68 (significativement pire qu'égal)** — la perte cumulée observée d'un expert retiré reste figée basse et il revient avec un avantage indu. CONTEXT_MIX 0,90.
- **Experts corrélés (S6)** : voir 07.

## Stabilité tuning → held-out
Spearman des nrm moyens par méthode (tuning vs held-out) = 0,97 (règle de stabilité ≥ 0,6 ✔). Le tuning a été fait en deux tours, dont le second pour élargir des optimums en bord de grille. Restent en bord de grille (LIMITATION) : MPP `mpp`=0,005 (plus petit testé) au tuning, STATIC κ=10 après extension partielle, `SLEEP_HEDGE` η=0,03 et FIXED_SHARE α=0,003 près du bas de grille (η/α intérieurs, mais plage basse).
