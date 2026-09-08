---
name: compact
description: >-
  Simplifies and reduces code and prose to achieve optimal clarity
  while preserving behavioral invariants and test guarantees.
---

The agent SHALL simplify code and prose to optimal clarity, maintain behavioral equivalence, and prune low-value verbosity.
The agent SHALL apply DRY: merge overlapping rules, procedures, and prose into single authoritative statements.

## Code Workflow
1. Execute pre-flight tests. INVARIANT: abort if any fail; MUST NOT proceed on untested code without explicit user consent.
2. Refactor toward idiomatic clarity; eliminate boilerplate, dead code, and redundant indirection.
   MUST NOT collapse multiple statements onto one line or sacrifice legibility.
   MUST preserve public APIs, exported symbols, and type annotations.
3. Re-execute tests. INVARIANT: all must pass without regressions.
4. Present diff preview with optimization metrics. INVARIANT: MUST NOT overwrite without explicit user approval.

## Prose Workflow
1. Preserve YAML frontmatter, code blocks, and tables verbatim.
2. Condense prose; delete padding; retain all decisions, constraints, and commands.
3. Present diff preview with optimization metrics. INVARIANT: MUST NOT overwrite without explicit user approval.
