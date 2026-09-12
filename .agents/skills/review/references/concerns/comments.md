# Comments Concern

Check comments in changed code. Comments must explain why code exists, not what it does.

## Rules

### Inline Comments
- Mark comments that explain what code does as `[SUGGESTION]`. Ask for clear code instead.
- Mark comments that state obvious code facts as `[NIT]` for removal.
- Accept comments that explain business rules or math steps.
- Mark wrong or misleading comments as `[BLOCKER]`.
- Mark stale comments that no longer match the code as `[BLOCKER]`.
- Mark resolved TODO comments as `[NIT]` for removal.

### Doc Comments
- Mark public classes, functions, or modules without docstrings as `[SUGGESTION]`.
- Mark complex private functions without docstrings as `[NIT]`.
- Mark wrong docstrings that misstate inputs or outputs as `[BLOCKER]`.
- Mark incomplete docstrings on public tools as `[SUGGESTION]`.

## Review Standards
- Review the code, not the author.
- Give the reason for each finding.
- Ask for clean code instead of chat explanations.
