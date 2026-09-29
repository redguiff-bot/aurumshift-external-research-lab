# 05 — Famine

Toutes valeurs held-out ; « part » = part de poids normalisée sur les experts éveillés ; référence = ORACLE.

## Nouvel expert (S4a : excellent à T/2 ; S4b : mauvais)
| Méthode | part à T/2+250 | part à T/2+450 |
|---|---|---|
| ORACLE | 0,56 | 0,55 |
| WTA | 0,76 | 0,84 |
| FIXED_SHARE | 0,36 | 0,49 |
| MPP | 0,32 | 0,34 |
| EWMA | 0,28 | 0,40 |
| DISC_AWAKE | 0,23 | 0,23 |
| CONTEXT_MIX | 0,17 | 0,23 |
| EG | 0,17 | 0,20 |
| SLEEP_HEDGE | 0,15 | 0,18 |
| EQUAL | 0,14 | 0,14 |
Porte (part ≥ 50 % oracle) : seuls **FIXED_SHARE** et **MPP** passent (WTA passe mais échoue partout ailleurs). Le nouvel expert entre à la moyenne géométrique des poids connus ; sans ré-injection (SLEEP_HEDGE, EG) il ne monte que lentement. **Coût du faux départ (S4b, expert mauvais)** : aucun candidat n'est pire qu'égal ; FIXED_SHARE 0,72, EG 0,71, EWMA 0,76 : la ré-injection ne coûte pas cher ici. WTA 3,26 (PROVEN pire).

## Spécialiste de régime rare (S8, occurrences ≥ 3)
| Méthode | part du spécialiste | mse (rare, tardif) |
|---|---|---|
| ORACLE | 0,92 | 0,0009 |
| WTA | 0,94 | 0,0028 |
| CONTEXT_MIX | 0,63 | 0,0036 |
| DISC_AWAKE | 0,32 | 0,0075 |
| FIXED_SHARE | 0,27 | 0,0100 |
| MPP | 0,24 | 0,0130 |
| EG | 0,21 | 0,0084 |
| SLEEP_HEDGE | 0,20 | 0,0097 |
| EWMA | 0,16 | 0,0135 |
| EQUAL | 0,14 | 0,0111 |
**Famine avérée** pour tout méthode à poids global : le spécialiste (sd 0,15) n'est éveillé que ~2 % du temps ; en dehors de ces bouffées il n'accumule aucune preuve et le mélange de ces poids à part de tout le monde le dilue. EWMA fait *pire* qu'égal dans ce régime (0,0135 vs 0,0111). Seul le poids conditionné au contexte (`lw_global + lw_ctx[c]`, contexte corrompu à 10 %) le retrouve (0,63), au prix d'échecs ailleurs. WTA le retrouve par accident (il suit le seul expert éveillé le meilleur) mais détruit le reste. Porte échouée par tous sauf CONTEXT_MIX et WTA.

## Sous-performance temporaire (S7 : l'expert trend/clone souffle de sd 0,4 à 2,2 sur 1000 tours)
Toutes les méthodes candidates récupèrent après la fenêtre (post − pré ≤ 0,15 en nrm, porte G_under ✔ sauf BMA et CONTEXT_MIX). La métrique « temps de récupération » (`extras.json`) est **non informative** ici (médiane 0 : la tolérance est atteinte dès le premier bloc lissé) ; je ne la cite pas.

## Récupération après dormance (S9 : étoile en lacune de données 1250 tours ; S3 : spécialistes dormants 2/3 du temps)
- S9 (nrm post-lacune moins pré-lacune) : EG 0,33 → 0,21 ; EWMA 0,58 → 0,63 ; DISC_AWAKE 0,53 → 0,59 ; **FIXED_SHARE 0,09 → 0,43** (la ré-injection uniforme sur les experts connus dilue l'étoile après un long sommeil : retour en ~200 tours) ; MPP 0,23 → 0,36. DISC_CLOCK (décote à chaque tour même endormi) n'est pas pire que DISC_AWAKE ici (0,65 vs 0,56 en moyenne) mais ne « perd » pas non plus la dormance en S9 — l'hypothèse « la décote horloge oublie les dormants » n'est **pas** démontrée par ce banc (UNKNOWN).
- S3 (ré-entrée de régime, 50 premiers tours) : FIXED_SHARE 0,15, EG 0,25, CONTEXT_MIX 0,26, EWMA 0,27 ✔ ; DIVERSITY 0,72 et STATIC 0,72 ✘.

## Verdict famine
STARVATION_CONTROLLED=FALSE : nouvel expert contrôlé seulement par ré-injection (Fixed-share/MPP) ; spécialiste rare non contrôlé sans contexte ; dormance longue contrôlée par EG mais dégradée par Fixed-share. Aucune méthode ne réussit les quatre à la fois.
