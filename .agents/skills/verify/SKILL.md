---
name: verify
description: Executes automated tests, performs 8-concern code reviews on diffs, and authors verification reports.
---

The agent SHALL verify uncommitted code modifications against automated test suites and architectural quality criteria in `docs/.prompts-and-prayers/{work_slug}/05-verify/verification-report.md`.

## Specification Invariants

Every verification artifact set MUST satisfy these rules:

1. **Frontmatter Envelope**:
   - `slug`: Work slug identifier.
   - `status`: One of `DRAFT`, `PENDING_APPROVAL`, `APPROVED`, `REJECTED`.
   - `approved_by`: `pending` or `human`.
   - `artifacts`: List containing paths for `verification-report.md`.
2. **Report Document Structure**:
   - `# Verification Report: <Title>`
   - `## 1. Automated Test Execution Evidence`
   - `## 2. 8-Concern Code Review Summary`
   - `## 3. Detailed Findings`
   - `## 4. Strengths & Positive Observations`
3. **Mandatory Review Concerns**:
   Section 3 MUST include subheadings for all eight review concerns: `### Design`, `### Functionality`, `### Complexity`, `### Tests`, `### Naming`, `### Comments`, `### Style`, and `### Documentation`.
4. **Verification Gates & Quality Standards**:
   - Section 1 MUST record command, output, and pass/fail metrics.
   - Findings MUST declare severity: `[BLOCKER]`, `[SUGGESTION]`, or `[NIT]`.
   - INVARIANT: the agent SHALL NOT approve reports with test failures, unresolved `[BLOCKER]` items, or `NEEDS CHANGES` verdicts.
   - WHEN tests fail or review detects blockers, THEN the agent SHALL escalate diagnostics to the stakeholder immediately.

## Execution Procedure

GIVEN uncommitted code modifications and build artifacts in `04-build/build-summary.md`.
WHEN the agent activates the verify skill:
1. Test: the agent SHALL execute:
   ```bash
   python3 -m unittest discover tests
   ```
   IF tests fail, THEN the agent SHALL report diagnostics to the stakeholder.
2. Diff: the agent SHALL inspect uncommitted changes using `git diff`.
3. Review: the agent SHALL evaluate the diff against each of the eight concerns using `.agents/skills/review/references/concerns/`.
4. Report: the agent SHALL compile findings into `.agents/skills/verify/assets/verification_report_template.md` under `05-verify/verification-report.md`.
5. Validate: the agent SHALL run:
   ```bash
   python3 .agents/skills/verify/scripts/validator.py docs/.prompts-and-prayers/{work_slug}/05-verify/ --json
   ```
   The agent SHALL fix errors iteratively until zero remain.
6. Stakeholder Gate: the agent SHALL set `status: PENDING_APPROVAL` and present the report link to the stakeholder.
   INVARIANT: the agent SHALL NOT proceed to downstream phases without explicit human approval.
7. Handoff: on confirmation, the agent SHALL set `status: APPROVED`, set `approved_by: human`, and prompt the next phase.
