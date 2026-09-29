# 02 — Revue de `typesafe-ai/system-one-adapter-python` comme couche d'abstraction

Code cloné et lu (v0.2.1, 2026-09-22, ~2 100 lignes `src/`, MIT, 6 commits « Release » par bot). Étiquettes : PROVEN = exécuté/lu par nous.

## 1. Ce que c'est (PROVEN)
Un client `SystemOneAdapterClient.system_one(state, questions, provider, model)` qui imite `TypeSafeClient.system_one` mais s'appuie sur des LLM (OpenAI Responses/Chat Completions, Anthropic, Gemini Interactions) ou sur un fournisseur personnalisé. Retourne une sous-classe de `typesafe_sdk.SystemOneResponse` (mêmes `answers`, `nouls/choices/scores`) + `usage` (tokens cumulés, retries, latence) + `debug` (`llm_attempts`, raisons de retry, diagnostics de normalisation).

## 2. Ce qu'il permet de mutualiser (state / question / output)
| Élément | Mutualisé ? | Détail (PROVEN) |
|---|---|---|
| Schéma de questions | Oui | `Noul | Choice | Score` (typesafe_sdk), validés strictement, ≥ 2 critères pour Choice/Score |
| Schéma de sortie | Oui | modèle pydantic généré **par requête** (`create_llm_output_model`) → JSON Schema natif ou JSON « prompted » validé côté client |
| State | Oui, mais **JSON opaque** | sérialisé dans `<document>…</document>`, `<`/`>` échappés, consigne système « traiter comme donnée non fiable » |
| Providers | Oui | `openai`, `anthropic`, `gemini`, fournisseur perso (`SyncProvider`/`AsyncProvider`) |
| Instructions par provider | Générées | descriptions de champs et prompt système construits à partir du QuestionSet (pas de prompt par provider à écrire) |

## 3. Expérience (PROVEN) — `evidence/exp_custom_provider_seam.py`
Une baseline **déterministe** (`RuleProvider`, sans réseau) branchée via `model=RuleProvider()` a produit une `SystemOneResponse` valide pour un QuestionSet Noul+Choice+Score. Conséquence : le même QuestionSet peut servir un `RuleSensor`, un `LLMSensor` et (via `TypeSafeClient`) Jev. Les 424 tests de l'adapter passent hors ligne (cassettes, `--block-network`).

Effet de bord observé : en cas d'égalité parfaite de probabilités, `choice` prend le premier label et `confidence` vaut 0. **Toute consommation doit lire `probabilities`/`confidence`, pas seulement `choice`.**

## 4. Limites structurelles pour AurumShift (PROVEN dans le code sauf mention)
1. **Un seul appel LLM pour toutes les questions d'un state.** Pour Jev les questions sont évaluées « en parallèle et isolément » (doc, DOCUMENTED_CLAIM) ; pour un LLM elles sont corrélées (effet d'ordre, contamination entre réponses). Les comparaisons B2/B3 vs Jev ne sont donc **pas** iso-processus ; à mesurer (K répétitions, permutation d'ordre des questions).
2. **Aucune température, seed, top_p** (recherche `grep` vide) : sorties LLM non déterministes ; à fixer dans un provider personnalisé ou par options du SDK provider.
3. **Probabilités LLM = verbalisées** (le modèle écrit des nombres) ; `normalize_probabilities` les rescale à 1. La `confidence` est **recalculée par l'adapter** avec la formule de Jev `(N·p_max−1)/(N−1)` : comparable en forme, pas en nature. Carte tout à zéro ⇒ uniforme (`rescale`) ; issue #45 rapporte des cartes à zéro renvoyées comme réponses valides (option 1 choisie) : DOCUMENTED_CLAIM d'un tiers.
4. **Pas de notion PIT** : `state` est un JSON quelconque ; `as_of`, hash, provenance sont à notre charge.
5. **Pas de persistance** : `debug.llm_attempts` est un bon matériau de rejeu, mais en mémoire seulement.
6. **Alias de modèle non épinglé par défaut** côté SDK (`jev-latest`).
7. **Couplage au vendeur** : dépend de `typesafe-sdk>=0.7.0` (types Question/Answer, `RetryPolicy`, `TypeSafeError`), pydantic ≥ 2.12, tenacity, SDK providers optionnels (openai ≥ 2.53, anthropic ≥ 0.121, google-genai ≥ 2.24).

## 5. Maturité et breaking changes
- v0.1.3 (2026-09-15) → v0.2.1 (2026-09-22) : 5 versions en 7 jours. **Breaking** : v0.2.0 (msgspec → pydantic, suit typesafe-sdk 0.7.0) ; v0.1.5 a dû borner `typesafe-sdk<0.7`. Issue #37 (OBSERVED) : installation fraîche cassée par cette migration (borne haute absente).
- Trois renommages publics de la classe en 2 semaines (OBSERVED via liste de PR) ; le SDK Python a aussi eu un breaking (0.6.0 : `Score.criteria` dict → séquence ; 0.7.0 : pydantic).
- Issues ouvertes (5) : timeouts par provider absents (#48), `choices` vide → IndexError (#47), refus Chat Completions (#46), cartes nulles (#45), tests Windows (#44). Fermées : `finish_reason="length"` accepté (#38), refus retentés (#43), usage absent (#39).
- Contributions : quasi uniquement les mainteneurs ; 0 dépendant GitHub ; 54 forks surtout « pour patcher » (SynthLuvr : port JS + Gemini natif).
- `Development Status :: 5 - Production/Stable` dans le classifieur PyPI alors que le projet a 2 semaines (INFERENCE : étiquette marketing).

## 6. Conclusion architecture
- **REUSE** : compilation QuestionSet → schémas providers, décodage/validation/retries, journal de tentatives, point d'extension Provider.
- **DO NOT REUSE comme contrat** : `AurumStateV1`, `QuestionSetV1`, `EpistemicSensor`, `JudgmentObservationV1` restent définis chez nous (vendor-neutres, PIT, append-only). L'adapter est un **détail d'implémentation d'un `LLMSensor`** ; `TypeSafeClient` celui d'un `JevSensor`.
- Recommandation : **ADAPT** — épingler `system-one-adapter==0.2.1` et `typesafe-sdk==0.7.2` (ou vendoring), ajouter timeout/température par provider personnalisé, journaliser en append-only, tests de contrat sur nos QuestionSets. Effort estimé : faible (INFERENCE) ; exit cost : faible tant que le contrat canonique est le nôtre.
- Alternatives sans lock-in vendeur pour la couche « schéma partagé » (comparaison seulement, ne fournissent pas de probabilités calibrées par option) : instructor, pydantic-ai, BAML, outlines, DSPy, LiteLLM.
