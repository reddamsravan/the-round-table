# Naming Concern

Check all names in changed code. Names must communicate intent with precision.

## Rules

### Clarity and Intent
- Mark names that need extra context to understand as `[SUGGESTION]`. Suggest a clear name.
- Mark single letters or generic words like `data` or `temp` as `[SUGGESTION]`. Allow loop indexes.

### Structure
- Mark boolean names that lack clear predicates like `is_valid` as `[SUGGESTION]`.
- Mark function names that lack action verbs as `[SUGGESTION]`.

### Length
- Mark names that are too short to explain their purpose as `[SUGGESTION]`.
- Mark overly long names that hurt reading flow as `[NIT]` with a shorter name.

### Consistency
- Follow naming conventions used in surrounding code.
- Mark names that clash with project style as `[SUGGESTION]`.
- Accept author names when no clear convention exists.

## Review Standards
- Prefer clean names over comments that explain poor names.
