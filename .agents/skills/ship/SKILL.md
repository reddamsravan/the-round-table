---
name: ship
description: Coordinates release closures, authors release notes and retrospectives, governs git commits, and updates backlogs.
---

The agent SHALL coordinate release procedures, author release notes and retrospectives in `docs/.prompts-and-prayers/{work_slug}/06-ship/`, orchestrate Conventional Commits via the `commit` skill, and update product backlogs in `docs/.prompts-and-prayers/backlog/backlog.md`.

## Specification Invariants

Every ship artifact set MUST satisfy these rules:

1. **Frontmatter Envelope**:
   - `slug`: Work slug identifier.
   - `status`: One of `DRAFT`, `PENDING_APPROVAL`, `APPROVED`, `REJECTED`.
   - `approved_by`: `pending` or `human`.
   - `artifacts`: List containing paths for `release-notes.md` and `retrospective.md`.
2. **Release Document Structures**:
   - `06-ship/release-notes.md` MUST contain in sequential order: `# Release Notes: <Title>`, `## 1. Release Summary`, `## 2. Delivered Features & User Stories`, `## 3. Conventional Commit Log`, and `## 4. Verification Signoff`.
   - `06-ship/retrospective.md` MUST contain in sequential order: `# Retrospective: <Title>`, `## 1. Execution Metrics`, `## 2. What Went Well`, `## 3. Opportunities for Improvement`, and `## 4. Action Items for Next Iteration`.
3. **Gate 4 Commit & Backlog Invariants**:
   - The agent SHALL invoke the `commit` skill to stage target files and generate Conventional Commit messages.
   - INVARIANT: the agent SHALL NOT execute `git commit` commands without explicit human authorization.
   - WHEN the user authorizes the release commit, THEN the agent SHALL update `docs/.prompts-and-prayers/backlog/backlog.md` and set the work item status to `DONE`.

## Execution Procedure

GIVEN an approved verification report from `05-verify/`.
WHEN the agent activates the ship skill:
1. Document: the agent SHALL author `06-ship/release-notes.md` and `06-ship/retrospective.md` using templates in `.agents/skills/ship/assets/`.
2. Stage: the agent SHALL activate the `commit` skill to stage modifications and draft Conventional Commit messages.
3. Gate 4: the agent SHALL present staged diffs and drafted commit messages to the stakeholder.
   INVARIANT: the agent SHALL NOT execute `git commit` without explicit human approval.
4. Commit: WHEN the stakeholder authorizes the release, THEN the agent SHALL run `git commit`.
5. Backlog: the agent SHALL update `docs/.prompts-and-prayers/backlog/backlog.md` to transition the item to `DONE`.
6. Handoff: the agent SHALL display a release completion summary and prompt the next cycle.
