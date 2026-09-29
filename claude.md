# AurumShift External Research Lab

## Purpose

This repository is a research laboratory for evaluating external technologies,
algorithms, scientific work, open-source projects and engineering techniques
that may improve AurumShift.

It does NOT contain AurumShift source code and must never pretend to know the
current private AurumShift implementation.

## Research doctrine

Priority:

REUSE → ADAPT → WRAP → COMPOSE → CUSTOM LAST

For every significant candidate:

1. Prefer primary sources:
   - actual repositories
   - official documentation
   - scientific papers
   - upstream issues/releases

2. Do not trust README claims blindly.
   Inspect actual source code.

3. Clone and execute candidates whenever feasible.

4. Inspect:
   - architecture
   - core algorithms
   - maintenance activity
   - recent commits/releases
   - open issues
   - dependencies
   - persistence model
   - operational complexity
   - failure modes
   - license
   - reproducibility

5. Distinguish all findings using:

   PROVEN
   OBSERVED
   DOCUMENTED_CLAIM
   INFERENCE
   UNKNOWN

6. Do not rank projects from GitHub stars alone.

7. Do not fabricate benchmark results.

8. Prefer components that are:
   - modular
   - replaceable
   - composable
   - operationally simple
   - realistically maintainable

9. Reject or PARK technology requiring excessive tuning unless the measured
   benefit is exceptional.

## AurumShift constraints relevant to external evaluation

- research-only / paper-only
- no live capital
- PostgreSQL-first where appropriate
- PIT / provenance / no-lookahead are critical
- event-driven / intraday rather than HFT
- one authoritative source per concern
- missing evidence is not negative evidence
- realistic market costs matter
- low operator relay is preferred
- scientific reproducibility matters
- infrastructure complexity must justify itself

## Important boundary

Never claim that a candidate is compatible with current AurumShift merely from
this repository.

External research produces:
ADOPT / ADAPT / PARK / REJECT candidates.

Final integration adjudication happens later against the real local AurumShift
repository.
