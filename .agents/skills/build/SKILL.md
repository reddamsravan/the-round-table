---
name: build
description: Decomposes engineering plans into atomic tasks, implements code and unit tests, and records build summaries.
---

The agent SHALL transform engineering task plans into verified executable code, unit tests, and build summaries in `docs/.prompts-and-prayers/{work_slug}/04-build/build-summary.md`.

## Specification Invariants

Every build artifact set MUST satisfy these rules:

1. **Frontmatter Envelope**:
   - `slug`: Work slug identifier.
   - `status`: One of `DRAFT`, `PENDING_APPROVAL`, `APPROVED`, `REJECTED`.
   - `approved_by`: `pending` or `human`.
   - `artifacts`: List containing paths for `build-summary.md`.
2. **Summary Document Structure**:
   - `# Build Summary: <Title>`
   - `## 1. Execution Overview`
   - `## 2. Completed Atomic Tasks`
   - `## 3. Test Verification Evidence`
   - `## 4. Modified Components`
3. **Atomic Task Constraints**:
   - Single in-flight task in `04-build/active.md` (fallback `docs/.tasks/active.md`) under `### Task: TASK-<NNN> - <Title>`.
   - Task YAML fields: `id`, `parent_plan_id`, `title`, `status`, `effort_hours` (<= 4.0), `verify_cmd`, and `acceptance_criteria`.
   - Deterministic criteria: active SVO items using `SHALL` or `MUST`.
4. **Verification & Quality**:
   - Every task modifying code MUST update unit tests in `tests/`.
   - The task `verify_cmd` MUST execute unit tests.
   - INVARIANT: the agent SHALL NOT mark tasks `DONE` on non-zero exit codes.
   - IF verification fails, THEN the agent SHALL attempt up to three repairs before escalating to stakeholder.
5. **Archival & Handover**:
   - The agent SHALL archive completed tasks to `04-build/archive/{task-id}.md`.
   - INVARIANT: the agent SHALL NOT execute `git commit` commands during the build phase.

## Execution Procedure

GIVEN approved implementation plans from `03-plot/plan.md`.
WHEN the agent activates the build skill:
1. Intake: the agent SHALL decompose plan items into atomic tasks (<= 4.0h effort) in `04-build/active.md`.
2. Implement: the agent SHALL write code and unit tests in `tests/`.
3. Verify: the agent SHALL execute `verify_cmd`. IF verification fails, THEN the agent SHALL run up to three repair attempts.
4. Archive: WHEN tests pass, THEN the agent SHALL mark `status: DONE` and archive to `04-build/archive/{task-id}.md`.
5. Summarize: WHEN all plan items finish, THEN the agent SHALL fill `.agents/skills/build/assets/build_summary_template.md` under `04-build/build-summary.md`.
6. Validate: the agent SHALL run:
   ```bash
   python3 .agents/skills/build/scripts/validator.py docs/.prompts-and-prayers/{work_slug}/04-build/ --json
   ```
   The agent SHALL fix errors iteratively until zero remain.
7. Stakeholder Gate: the agent SHALL set `status: PENDING_APPROVAL` and present artifact links to the stakeholder.
   INVARIANT: the agent SHALL NOT proceed to downstream phases without explicit human approval.
8. Handoff: on confirmation, the agent SHALL set `status: APPROVED`, set `approved_by: human`, and prompt the next phase.
