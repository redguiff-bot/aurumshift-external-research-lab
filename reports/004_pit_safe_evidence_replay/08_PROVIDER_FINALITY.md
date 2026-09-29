# 08 — Finalité fournisseur

Modèle interne : PRELIMINARY / FINAL / CORRECTED / UNKNOWN + `finality_basis` (PROVEN côté modèle : filtre après sélection). Le **mapping fournisseur est un adaptateur séparé**.

| Fournisseur | Constat | Label |
|---|---|---|
| Binance kline stream | champ `x` = « Is this kline closed? » ; poussé toutes les 1000 ms (1s) / 2000 ms (autres) | DOCUMENTED_CLAIM (page web-socket-streams récupérée 2026-09-29) |
| OKX candlesticks | champ `confirm` : texte de la doc non obtenu (page tronquée à la récupération) | UNKNOWN |
| Coinbase Exchange candles | granularités {60,300,900,3600,21600,86400} ; **aucune déclaration** de finalité/révision trouvée | DOCUMENTED_CLAIM (absence) → UNKNOWN pour la finalité |

Règle : toute finalité non prouvée est stockée UNKNOWN et exclue de `asof_final` (fail-closed). Une clôture `x=true` n'exclut pas une correction ultérieure du fournisseur : détectée seulement par `silent_restatements`/`provider_disagreement` (INFERENCE).
