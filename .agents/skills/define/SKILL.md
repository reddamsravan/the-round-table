---
name: define
description: Defines problem statements, functional requirements, and acceptance criteria.
---

The agent SHALL formulate problem statements, target personas, functional requirements, and acceptance criteria in `docs/.prompts-and-prayers/{work_slug}/01-define/spec.md`.

## Specification Invariants

Every specification document MUST satisfy these rules:

1. **Frontmatter Envelope**:
   - `slug`: Work slug identifier.
   - `status`: One of `DRAFT`, `PENDING_APPROVAL`, `APPROVED`, `REJECTED`.
   - `approved_by`: `pending` or `human`.
   - `artifacts`: List of generated specification paths.
2. **Mandatory Sections**:
   - `# Specification: <Title>`
   - `## 1. Objective & Value`
   - `## 2. Target Personas`
   - `## 3. Scope Boundaries`
   - `## 4. Functional Requirements`
   - `## 5. Success Metrics & Validation`
3. **Requirement Format**: `### Requirement: REQ-<NNN> - <Title>` containing the narrative:
   - `As a <role>,`
   - `I want <action>,`
   - `So that <value>.`
4. **Acceptance Criteria**: one or more active SVO bullet items using `SHALL` or `MUST`.
   INVARIANT: criteria SHALL NOT use passive voice or ambiguous words.

## Execution Procedure

GIVEN a problem statement or feature request.
WHEN the agent activates the define skill:
1. Intake: the agent SHALL clarify missing boundaries, personas, or outcomes, and inspect codebase for context.
2. Generate: the agent SHALL fill `.agents/skills/define/assets/spec_template.md` and write to `docs/.prompts-and-prayers/{work_slug}/01-define/spec.md`.
3. Validate: the agent SHALL run:
   ```bash
   python3 .agents/skills/define/scripts/validator.py docs/.prompts-and-prayers/{work_slug}/01-define/spec.md --json
   ```
   The agent SHALL fix errors iteratively until zero remain.
4. Stakeholder Gate: the agent SHALL set `status: PENDING_APPROVAL` and present artifact link to stakeholder.
   INVARIANT: the agent SHALL NOT proceed to downstream phases without explicit human approval.
5. Handoff: on confirmation, the agent SHALL set `status: APPROVED`, set `approved_by: human`, and prompt the next phase.
