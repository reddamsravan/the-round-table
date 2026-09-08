---
name: commit
description: Guides git staging, decomposes multi-concern changes, and drafts Conventional Commit messages.
---

INVARIANT: obtain explicit user confirmation before any `git commit`.

## Message Rules

1. **Header syntax**: `<type>(<scope>): <subject>` or `<type>: <subject>`.
   Valid types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`.
   Scope: lowercase alphanumeric with hyphens or slashes.
2. **Length**: header target <= 50 chars; hard ceiling 72. Body lines <= 72 chars.
   Blank line required between header and body/footers.
3. **Subject**: lowercase imperative verb, no trailing period, no past tense.
4. **Breaking changes**: add `!` before colon or append `BREAKING CHANGE: <description>` footer.
5. **No local task IDs**: reserve `Fixes #<id>` / `Closes #<id>` for external trackers only.
6. **Diff-only content**: derive all message content strictly from `git diff`. The agent SHALL NOT inject context, assumptions, or knowledge from outside the diff.

## Procedures

### A: Inspect and Stage
1. Run `git status --short`.
2. IF staging area is empty, THEN inspect with `git diff`; else inspect with `git diff --cached`.
3. IF the diff has multiple independent concerns, THEN propose atomic commit splits.
4. Stage with `git add <paths>`.

### B: Draft Message
1. Identify the change intent, affected component, type, and scope.
2. Draft subject and body using the `write` skill; validate with
   `python3 .agents/skills/write/scripts/validator.py --json`; fix until Flesch >= 65 and 0 errors.
3. Form header: prepend `<type>(<scope>): ` to the validated subject.
4. Apply footers per rules 4 and 5 if needed.

### C: Validate
1. Validate: `echo "<message>" | python3 .agents/skills/commit/scripts/validator.py --json`
2. IF errors exist, THEN autofix and re-validate until 0 errors remain.

### D: Present and Execute
1. Show staged file list and full commit message; wait for explicit confirmation.
2. On confirm: `git commit -m "<header>" -m "<body>"`
3. On reject: revise message or staging.
