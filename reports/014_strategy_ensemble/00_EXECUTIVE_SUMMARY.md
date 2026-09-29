# 00 — Résumé exécutif : ensemble de familles de stratégies avec experts « endormis » (V1)

Mode : EXTERNAL_RESEARCH_ONLY · aucun code privé AurumShift · aucune intégration. **Données synthétiques uniquement** : rien ici ne dit qu'une méthode marche sur des marchés réels ni qu'elle est compatible avec AurumShift.
Labels : PROVEN (test reproductible dans le banc synthétique) · OBSERVED · DOCUMENTED_CLAIM · INFERENCE · UNKNOWN.

## Conclusion
**FINAL_VERDICT = NO_ROBUST_ENSEMBLE_METHOD** (règles pré-enregistrées en 03, appliquées sans modification ; 30 graines held-out, 11 scénarios, 17 méthodes exécutées).
Aucune méthode ne franchit toutes les portes (proximité du meilleur par scénario, non-pire-qu'égal, démarrage d'un nouvel expert, spécialiste rare, sous-performance temporaire, dormance). Mais l'échec n'est pas uniforme :

1. **Sémantique des absences** (PROVEN) : ne jamais mettre à jour un expert endormi ni un expert dont le feedback manque. Traiter « inactif » comme négatif fait passer EWMA de 0,55 à 1,16 et le Hedge endormi de 0,73 à 1,35 (nrm ; 1 = poids égaux) ; traiter « preuve manquante » comme négatif ne fait mal que là où elle existe (S1 : +1,55 et +1,21). Conserver la masse du bloc mis à jour (normalisation « spécialiste ») compte : sans elle, S5 +2,03.
2. **Meilleures moyennes** : EG (0,487) et Fixed-share endormi (0,494), devant EWMA (0,548), Hedge endormi simple (0,725) et poids statiques (0,923). Mais l'avantage d'EG sur EWMA (−0,061 en moyenne de nrm) est à peine au-dessus de la marge δ = 0,05, et EG est *significativement pire* qu'EWMA en S2, S4a, S9.
3. **Le Hedge endormi « de référence » tel quel n'est pas le gagnant** : à η optimal sur le tuning (0,03) il ressemble à des poids égaux ; ses poids globaux ne suivent pas les changements de régime.
4. **Famine** (PROVEN, synthétique) : nouvel expert — seuls Fixed-share (part 0,36 vs 0,56 oracle à T/2+250) et MPP passent ; spécialiste de régime rare — tout le monde le laisse à 0,16–0,32 de part (oracle 0,92) sauf le mélange conditionné au contexte (0,63), qui échoue ailleurs (S6 : 1,73, pire qu'égal). Le vainqueur-emporte-tout (WTA) démarre vite mais est 2,4× pire qu'égal en moyenne.
5. **Diversité** : le rabais de redondance réduit bien la masse du cluster corrélé (0,30 vs 0,46) et gagne en S6, mais coûte +0,19 en moyenne ailleurs (pire dans 9 scénarios sur 10 vs Fixed-share). EG seul bat déjà l'oracle « variance inverse indépendante » en S6.
6. **Bandits** (comparaison seule) : 3,4–3,8× pire que poids égaux — choisir un seul expert est inadapté ici.
7. **OSS** : `river.ensemble.EWARegressor` n'a aucune notion d'expert endormi ; avec remplissage forcé il est 1,5–4× pire que poids égaux à son meilleur pas testé (bord de grille : lr→0 tend vers EQUAL).

## Ce que cela ne prouve pas
Sortie synthétique (prévisions de probabilité, perte de Brier, bruit gaussien logit) ; pas de coûts, pas de P&L, pas de dépendance temporelle des erreurs réelle. Les portes sont exigeantes (voir 09/10) ; la conclusion « aucune méthode robuste » signifie *aucune ne passe ces portes*, pas « aucune n'est utile ». En pratique ce banc suggère : EG ou Fixed-share endormis > EWMA > statique, avec garde-fous explicites contre la famine (plancher, contexte) — à réévaluer contre le vrai dépôt.

## Bloc final
METHODS_DISCOVERED=22 (voir 02)
METHODS_EXECUTED=17 méthodes + 6 ablations + 1 sonde OSS (river) + référence ORACLE

STATIC_WEIGHTS_RESULT=nrm 0,92 (≈ poids égaux) ; pire qu'égal en S6 ; échoue toutes les portes de famine
EWMA_RESULT=nrm 0,55, meilleure baseline ; échoue nouvel expert et spécialiste rare (écart pire-cas 0,30)
SLEEPING_EXPERTS_RESULT=Hedge endormi simple 0,73 (faible) ; EG endormi 0,49 et Fixed-share endormi 0,49 (meilleures moyennes) mais aucun robuste

MISSING_EVIDENCE_HANDLED=TRUE (sémantique « ni mise à jour ni pénalité » PROVEN ; les ablations négatives nuisent significativement)
STARVATION_CONTROLLED=FALSE
RECURRING_SPECIALIST_RECOVERY=PARTIAL (ré-entrée de régime OK pour EG/Fixed-share ; spécialiste de régime rare affamé pour toutes les méthodes sauf le mélange contextuel)

COMPLEXITY_JUSTIFIED=FALSE (contexte, diversité, MPP, décote : non justifiés ; EG/Fixed-share : gain sur EWMA ≈ marge δ, non robuste)

FINAL_VERDICT=NO_ROBUST_ENSEMBLE_METHOD
