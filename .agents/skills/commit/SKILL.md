---
name: commit
description: Stages git changes, splits multi-concern diffs, and drafts concise Conventional Commit messages. Activate on '/commit'.
---

The agent SHALL stage git changes, split multi-concern diffs, and draft Conventional Commit messages.

## Rules
- INVARIANT: The agent SHALL obtain explicit user confirmation before running `git commit`.
- The agent SHALL format commit messages adhering to [references/conventional_commits.md](references/conventional_commits.md).
- The agent SHALL derive all commit message content strictly from `git diff`.
- The agent SHALL invoke the `prose` skill to prepare the commit message subject and body.

## Workflow
1. Inspect working tree status using `git status --short`.
2. Inspect modifications using `git diff` or `git diff --cached`.
3. IF the diff contains multiple independent concerns, THEN execute Procedure A.
4. Stage target modifications using `git add <paths>`.
5. Execute Procedure B to draft the Conventional Commit message.
6. Present staged modifications and the draft commit message to the user for explicit confirmation.
7. Execute Procedure C upon user confirmation.

## Procedures

### Procedure A: Multi-Concern Splitting
1. Identify independent concerns across modified files.
2. Group related file modifications into atomic patch sets.
3. Stage each patch set sequentially for distinct commits.

### Procedure B: Message Preparation
1. Identify the primary change intent and select the commit type adhering to [references/conventional_commits.md](references/conventional_commits.md).
2. Identify the codebase subsystem to select an optional single-word noun scope.
3. Invoke the `prose` skill to prepare the concise imperative subject line.
4. IF the modification requires explanation, THEN invoke the `prose` skill to prepare the rationale body.
5. IF breaking changes exist, THEN apply the breaking change format adhering to [references/conventional_commits.md](references/conventional_commits.md).

### Procedure C: Commit Execution
1. Run `git commit -m "<header>"` or `git commit -m "<header>" -m "<body>"`.
2. Confirm commit creation using `git status --short`.
3. Display the generated commit SHA and summary to the user.

## Verification Checklist
- [ ] Verify that staged modifications belong to a single atomic concern.
- [ ] Verify that the commit header follows Conventional Commits syntax per [references/conventional_commits.md](references/conventional_commits.md).
- [ ] Verify that the prose skill prepared the commit message subject and body.
- [ ] Obtain explicit user confirmation before executing `git commit`.
- [ ] Confirm commit creation with `git status --short`.
