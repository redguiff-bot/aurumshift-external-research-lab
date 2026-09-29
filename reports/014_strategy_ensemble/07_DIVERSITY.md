# 07 — Diversité et experts corrélés (S6 : 4 clones, ρ = 0,95, bons puis mauvais ; 3 experts indépendants)

| Méthode | nrm S6 | part du cluster corrélé | n effectif 1/Σw² |
|---|---|---|---|
| EQUAL | 1,00 | 0,57 | 7,0 |
| SLEEP_HEDGE | 0,85 | 0,58 | 6,0 |
| CONTEXT_MIX | 1,73 | 0,58 | 3,9 |
| FIXED_SHARE | 0,11 | 0,46 | 4,7 |
| EWMA | 0,02 | 0,44 | 4,9 |
| **DIVERSITY** | −0,02 | **0,30** | 4,8 |
| **EG** | **−0,27** | 0,33 | 5,2 |
| ORACLE (indépendance supposée) | (0) | 0,51 | 5,7 |

- Les poids égaux et le Hedge quasi-égal donnent aux 4 clones 57–58 % de la masse : ils comptent quatre fois la même erreur. PROVEN (synthétique).
- Le **rabais de redondance** réduit la masse du cluster (0,30) et gagne face à Fixed-share en S6 (significatif) — mais **coûte partout ailleurs** (DIVERSITY − FIXED_SHARE : +0,186 en moyenne sur les 11 scénarios ; significativement pire dans 9 des 10 autres scénarios) car il retire du poids à des experts légitimement similaires (nb : les experts de S0 partagent le signal latent).
- **EG seul** bat même le rabais dédié (−0,27 en S6) sans terme de diversité : sa mise à jour centrée sur le mélange pénalise les clones dès que leur erreur commune devient mauvaise (le cluster est éteint en un seul bloc). Le rabais n'apporte donc pas de gain démontré contre EG.
- CONTEXT_MIX est significativement pire qu'égal en S6 : il apprend un décalage par contexte sur un cluster qui devient mauvais partout.
- Limite : la diversité est mesurée sur les résidus de *prévision* (corrélation observable sans étiquettes) ; en pratique les corrélations d'erreur changent selon le régime. UNKNOWN sur données réelles.
Verdict diversité : la concentration sur des clones est un risque réel et mesurable ; une méthode à mise à jour relative (EG) le traite mieux que l'ajout d'un terme explicite. COMPLEXITY_JUSTIFIED pour DIVERSITY = FALSE.
