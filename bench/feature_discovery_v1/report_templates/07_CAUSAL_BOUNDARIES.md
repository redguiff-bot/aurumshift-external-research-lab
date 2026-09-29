# 07 — Frontières causales

Règle : une association prédictive n'est **jamais** appelée causale sans design identifié. Classes : `PREDICTIVE` → `INVARIANT_ASSOCIATION` → `CAUSAL_HYPOTHESIS` → `CAUSAL_IDENTIFIED` (`fd/causal.py`). `CAUSAL_IDENTIFIED` exige un objet *design* explicite (intervention randomisée, expérience naturelle, instrument valide) avec p < 0.01 et réplication ; les données réelles de ce dépôt (klines observationnelles) n'en fournissent aucun.

## Classification des formules gelées (données réelles)

{{classes}}

Aucune formule n'atteint `INVARIANT_ASSOCIATION` : `y_vol/C01` échoue sur Q train+val (amplitude), `y_ret/C01` n'est pas stable. ICP-lite n'accepte **aucun** sous-ensemble (0/8 et 0/42) : la volatilité et les rendements ne vérifient pas « moyenne et variance des résidus égales entre environnements » — les hypothèses d'ICP (interventions sur les causes, pas de confondant changeant) sont violées, et l'intersection est indéfinie. `CAUSAL_HYPOTHESIS` exigerait aussi un mécanisme documenté ; aucun n'est revendiqué (`mechanism_documented=False`). **CAUSAL_IDENTIFIED_COUNT = 0.**

## Pourquoi l'invariance ne suffit pas (structures simulées à DAG connu, PROVEN sur synthétique)

{{causal}}

Lecture :
- **A** (X→Y, environnements qui décalent le bruit de X) : pente invariante, ICP retrouve `X`, l'intervention randomisée confirme. Seul ce cas atteint `CAUSAL_IDENTIFIED`, *uniquement* avec le design.
- **B décalé** (confondant U→X, U→Y) : le décalage du bruit de X **casse** l'invariance → Q rejette ; c'est le cas où ICP est utile.
- **B échangeable** : sans hétérogénéité informative entre environnements, la feature confondue est **invariante et prédictive exactement comme A** (IC 0.19, Q p = 0.69) : l'observation ne distingue pas A de B ; seule l'intervention (effet ≈ 0, p = 0.95) le fait. Or c'est la situation des marchés crypto (cross-sections échangeables et corrélées).
- **C** (Y→X, causalité inverse) : IC 0.66, invariant, mais X ne cause pas Y (do(X) ≈ 0).
- **D** (signe du confondant qui bascule) : Q et le signe (0.5) le détectent.

Conclusion (INFERENCE) : l'invariance inter-marchés observée en crypto est un critère de **robustesse prédictive**, pas d'identification. Toute mention de causalité pour une feature de marché exige un design (p. ex. expérience naturelle d'exécution ou intervention en paper trading randomisée) qui n'existe pas ici.
