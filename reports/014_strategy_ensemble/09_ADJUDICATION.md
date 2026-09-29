# 09 — Adjudication

## Application des règles pré-enregistrées (03)
1. Stabilité tuning→held-out : Spearman 0,97 ≥ 0,6 ✔ (pas d'INCONCLUSIVE).
2. Ensemble robuste (baselines + candidats) : **vide**. Aucune méthode ne passe toutes les portes.
   - Plus proche : **EG** (écart pire-cas 0,149 ≤ 0,15 ✔ de justesse ; échoue *nouvel expert* et *spécialiste rare*).
   - **Fixed-share** : meilleure moyenne ex æquo (0,494) mais écart pire-cas 0,387 (S6) et dormance dégradée (S9).
   - **EWMA** : écart 0,304, échoue nouvel expert et rare.
3. ⇒ **NO_ROBUST_ENSEMBLE_METHOD**.
4. Familles « nécessaires » (bat toutes les autres familles de > δ) : cœur (S6, via EG), tracking (S3, via Fixed-share). Contexte et diversité : aucune.

## Journal des écarts
1. **Bug de conservation de masse (détecté avant adjudication finale, corrigé, tuning et held-out relancés).** La première version rétablissait la masse du bloc mis à jour de façon seulement approchée (une translation logarithmique qui ne préserve pas la masse quand le dénominateur change). Découvert car l'ablation `SLEEP_UNCENTRED` (qui devait être mathématiquement identique) donnait des résultats différents (−0,18 vs SLEEP_HEDGE en S0). Correction exacte `e^c = m0(1−m1)/((1−m0)m1)` + test unitaire d'invariance. Les résultats du run bugué sont archivés dans `bench/ensemble_v1/results/buggy_mass_fix/` ; **le verdict était déjà NO_ROBUST_ENSEMBLE_METHOD** et les moyennes proches (EG 0,498 vs 0,487 ; Fixed-share 0,516 vs 0,494). Le held-out du run bugué a été *vu* avant la correction ; la correction n'a pas modifié les règles ni les portes.
2. Tuning en deux tours (grilles élargies après optimums en bord de grille) — sur graines de tuning seulement ; documenté.
3. Métrique « temps de récupération » (extras.json) jugée non informative et non utilisée.
4. Aucun seuil de porte modifié après le held-out.

## Sensibilité POST-HOC (ne modifie pas le verdict)
- Avec un écart pire-cas toléré de 0,40 au lieu de 0,15, EG et Fixed-share passeraient cette porte-là ; EG échoue toujours nouvel expert et rare ; Fixed-share échoue rare et dormance ; personne ne passe les quatre portes de famine.
- Portes de famine jugées **très** exigeantes : la part de l'oracle (0,92 pour le spécialiste rare) suppose la connaissance parfaite de l'écart-type ; un seuil à 25 % de l'oracle ne changerait que quelques méthodes (le maximum observé hors WTA/CONTEXT_MIX est 0,35 de la part oracle pour DISC_AWAKE).
- Sur la moyenne seule, EG (0,487) ≈ Fixed-share (0,494) < EWMA (0,548) : différence à la limite de δ. Un lecteur préférant la moyenne classerait EG/Fixed-share devant EWMA ; le protocole demandait la robustesse.

## Recommandations (candidats ADOPT/ADAPT/PARK/REJECT — externes, à réévaluer contre le dépôt réel)
| Candidat | Décision | Raison |
|---|---|---|
| Sémantique « endormi ≠ mauvais » + mise à jour sur observés uniquement | **ADOPT** (principe) | PROVEN : ne pas l'appliquer coûte jusqu'à > 1 span égal→oracle. |
| Conservation de masse du bloc mis à jour (normalisation spécialiste) | **ADOPT** (principe) | Nécessaire à la stabilité (S5/S1). |
| EG endormi (η≈0,1) | **ADAPT** | Meilleure moyenne + meilleur écart pire-cas ; ajouter garde-fou nouvel expert. |
| Fixed-share endormi (α≈0,003–0,01) | **ADAPT** | Seul à bien traiter nouvel expert + récurrence ; attention dormance longue et clones. |
| EWMA | **ADAPT (baseline)** | Simple, compétitif ; garder comme référence et repli. |
| MPP, DISC_AWAKE | **PARK** | Complexité sans gain net robuste. |
| CONTEXT_MIX | **PARK** | Seul remède du spécialiste rare mais dégâts ailleurs ; nécessite un contexte fiable. |
| DIVERSITY | **REJECT** (en l'état) | Coût > gain ; traiter les clones par EG ou par regroupement en amont. |
| BMA sans oubli, HEDGE_CUM, WTA, EXP3, ε-greedy | **REJECT** | Voir 08. |
| river EWARegressor | **REJECT** pour ce cas | Pas de masque de sommeil. |
Intégration et compatibilité : hors périmètre.
