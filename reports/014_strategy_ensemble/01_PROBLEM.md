# 01 — Problème

Combiner en ligne des familles de stratégies hétérogènes (tendance, retour à la moyenne, carry, spécialistes de stress ou de régime rare, généralistes, clones) quand **seule une partie** est valide ou disponible à chaque tour. Ne pas supposer que la réponse est un bandit : ici on combine (mélange pondéré), on ne sélectionne pas.

## Sémantique à distinguer (pas seulement à nommer)
| Notion | Définition dans le banc | Effet attendu sur le poids |
|---|---|---|
| Stratégie inactive | structurellement invalide dans le régime, pas encore née, ou retirée | hors mélange ; aucun apprentissage ; poids relatif conservé |
| Preuve manquante | l'expert prévoit (donc pèse dans le mélange) mais son score n'est pas observé | pèse encore ; **aucune** mise à jour |
| Lacune de données | l'entrée manque, l'expert ne peut pas prévoir | comme inactif : endormi, aucun apprentissage |
| Abstention | l'expert valide choisit de ne pas prévoir | endormi ; aucune pénalité (l'abstention pourrait être informative — non exploité ici) |
| Preuve négative | un score observé mauvais sur un tour où l'expert a prévu | mise à jour légitime |
| Mauvaise performance réalisée | perte relative cumulée observée | seule source d'érosion durable du poids |

Règle : **l'absence d'évidence n'est jamais une évidence d'absence de compétence**. Les ablations `*_INACTIVE_NEG` / `*_MISSING_NEG` (pénalité 0,5) mesurent ce que coûte la violation de cette règle.

## Risques de famine testés
Nouvel expert (aucun historique) · spécialiste de régime rare (peu d'occasions d'apprendre) · sous-performance temporaire (le poids s'effondre puis doit revenir) · récupération après dormance (longue lacune de données ou régime absent).

## Non-stationnarité testée
Changement de leadership · récurrence de régimes · arrivée d'un nouvel expert · disparition (puis retour dégradé) · experts corrélés.

## Hors périmètre
Coûts de transaction, taille de position, exécution, optimisation de portefeuille, dépendance à des données de marché réelles. Aucun code AurumShift n'est lu ni supposé.
