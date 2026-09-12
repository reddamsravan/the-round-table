# Style Concern

Check code style against the project style guide. Do not block merges over personal preferences.

## Rules

### Style Guide Authority
- Follow the official project style guide when one exists.
- Mark style guide rule violations as `[SUGGESTION]`.
- Mark minor format issues like spaces or import order as `[NIT]`.
- Accept author style choices when no project guide exists.

### Mixed Changes
- Mark large reformatting mixed with logic changes as `[BLOCKER]`.
- Ask authors to put file-wide format changes in a separate commit.

### Code Consistency
- Match style in surrounding code when no guide rule applies.
- Mark code that clashes with local patterns as `[NIT]`.
- Prefer style guide rules when surrounding code breaks them.

## Review Standards
- Do not let style debates block clean, working code.
- Never escalate style findings to `[BLOCKER]` unless logic breaks.
