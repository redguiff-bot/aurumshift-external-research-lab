# 10 — Limites

1. **Univers étroit (OBSERVED)** : 9 paires crypto spot d'un seul exchange, fortement corrélées ; « multi-marchés » ≠ 9 preuves indépendantes (le bootstrap partage le temps pour en tenir compte). PAXG est le seul actif non purement crypto. Aucun autre venue, aucun autre actif (actions, FX, futures).
2. **Un seul régime temporel** 2021-2026 ; held-out 20 mois (2025-01 → 2026-08).
3. **Primitives limitées** : OHLCV + trades + taker-buy. Pas d'order-book, funding, OI, données on-chain ou macro (voir `reports/005_data_feed_resilience`).
4. **Cibles** : `y_vol` est dominé par la persistance de la volatilité (IC ridge 0.585) ; c'est un test de puissance, pas une découverte économique. `y_ret` est quasi non prédictible : un résultat nul y est le résultat attendu, pas la preuve d'un pipeline sourd (l'arène couvre cette question).
5. **Pas de coûts ni d'exécution** : IC/R² uniquement ; aucun PnL, aucun seuil de rentabilité (UNKNOWN).
6. **Gaps de données** : 7 trous d'1 h par paire (maintenance) ; les lookbacks « N barres » les traversent ; les 9 marchés partagent la même grille (intersection).
7. **Espace de features/formules restreint** : GP à 10 générations/300 individus, 5 seeds, fonctions usuelles ; PySR non exécuté (Julia). Un GP plus lourd pourrait trouver plus, avec plus de coût de multiplicité.
8. **Puissance GP faible** (27.5 % sur non-linéarité pure synthétique) : « GP n'a rien trouvé » ne prouve pas « rien à trouver ».
9. **Stability selection** : borne E[V] théorique supposant des conditions non vérifiées sous dépendance temporelle ; 15 % de faux mains sous NULL.
10. **Deviations du protocole** : listées en 02 §12 (filtre trivial après un premier passage train/val ; arène : puissance linéaire mesurée par mains ; démo causale durcie ; pas de gate de nouveauté). Aucune n'a touché au held-out.
11. **Références** citées de mémoire, non re-vérifiées en ligne (DOCUMENTED_CLAIM).
12. **Arène synthétique** : bruit hétéroscédastique gaussien, features AR(1) — plus simple que le marché réel ; le FWER mesuré (0/40) n'est pas une garantie sur données réelles (mais complété par les placebos réels 0/20 et 1/20).
13. **Aucune conclusion sur AurumShift** : mission NO_INTEGRATION ; l'adjudication d'intégration reste à faire contre le dépôt local.
