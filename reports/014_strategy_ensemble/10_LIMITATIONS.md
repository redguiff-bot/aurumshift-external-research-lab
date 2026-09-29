# 10 — Limites

1. **Synthétique seulement** : bruit gaussien sur le logit, régime observable à 90 %, erreurs indépendantes sauf clones. Aucune donnée de marché réelle, aucun coût, pas de P&L. (UNKNOWN sur données réelles.)
2. **Perte de prévision** (Brier/log) et non perte de décision : un ensemble de signaux de trading peut se comporter autrement.
3. **Portes exigeantes et partiellement arbitraires** (seuils 0,5 de la part oracle, δ=0,05, δ_R=0,15) ; le verdict « aucune méthode robuste » dépend d'elles (voir sensibilité post-hoc en 09). Elles étaient fixées avant le held-out mais *après* avoir vu un smoke test.
4. **Hyperparamètres** : un jeu par méthode sur tous les scénarios ; certains optimums restent près du bas de grille (MPP `mpp`, FIXED_SHARE α, SLEEP_HEDGE η). Les méthodes à plus de paramètres ont eu plus de degrés de liberté au tuning (Spearman 0,97 rassure sans éliminer le biais).
5. **Oracle non borne** : il ignore les corrélations (EG le bat en S6).
6. **Implémentations simplifiées** : MPP = moyenne uniforme des postérieurs passés (pas le schéma de décroissance de Bousquet–Warmuth) ; « Putting Bayes to sleep » et « growing experts/muting » non exécutés ; pas de coin-betting ni ML-Poly/BOA.
7. **Bandits** : implémentation minimale (EXP3 avec pertes pondérées, ε-greedy) ; pas de bandit endormi optimisé (Kleinberg et al.). La comparaison est indicative.
8. **Sonde river** : un seul mode de remplissage par variante, grille de lr limitée (lr=0,3 = bas de grille) : montre l'absence d'API de sommeil, pas la meilleure performance possible de la bibliothèque.
9. **Un bug corrigé en cours d'étude** (09) : le held-out du run bugué a été vu ; le run final est indépendant du bug mais pas d'un œil informé.
10. **Une seule longueur T=5000, un seul K=10**, dwell de régime fixé ; la sensibilité à K, T, corruption de contexte, bruit d'observation n'est pas explorée.
11. **Littérature** : quatre références vérifiées par recherche web (specialists, Putting Bayes to sleep, growing experts, MPP) ; les autres sont citées de mémoire (DOCUMENTED_CLAIM).
12. **Aucune compatibilité AurumShift affirmée.** L'adjudication finale se fait contre le dépôt réel, plus tard.
