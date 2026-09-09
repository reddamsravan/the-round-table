---
name: design
description: Designs user journeys, screen state transitions, UI layouts, and accessibility criteria.
---

The agent SHALL formulate user journeys, screen state transitions, UI layouts, and accessibility criteria in `docs/.prompts-and-prayers/{work_slug}/02-design/design-spec.md`.

## Specification Invariants

Every design specification document MUST satisfy these rules:

1. **Frontmatter Envelope**:
   - `slug`: Work slug identifier.
   - `status`: One of `DRAFT`, `PENDING_APPROVAL`, `APPROVED`, `REJECTED`.
   - `approved_by`: `pending` or `human`.
   - `artifacts`: List of generated design specification paths.
2. **Mandatory Sections**:
   - `# Design Specification: <Title>`
   - `## 1. User Journey & Interaction Flow`
   - `## 2. Screen State Transitions`
   - `## 3. UI Layout & Component Specifications`
   - `## 4. Accessibility & Responsive Requirements`
3. **Visualizations**:
   - Section 1 MUST contain a Mermaid flowchart.
   - Section 2 MUST contain a Mermaid state diagram.
   INVARIANT: specifications SHALL NOT use ASCII art box drawings.
4. **Accessibility Criteria**: active SVO items in Section 4 using `SHALL` or `MUST`.
   INVARIANT: criteria SHALL NOT use passive voice or ambiguous words.

## Execution Procedure

GIVEN a feature request or upstream definition.
WHEN the agent activates the design skill:
1. Intake: the agent SHALL clarify missing viewports, journeys, or interactions, and inspect upstream definitions.
2. Generate: the agent SHALL fill `.agents/skills/design/assets/design_template.md` and write to `docs/.prompts-and-prayers/{work_slug}/02-design/design-spec.md`.
3. Validate: the agent SHALL run:
   ```bash
   python3 .agents/skills/design/scripts/validator.py docs/.prompts-and-prayers/{work_slug}/02-design/design-spec.md --json
   ```
   The agent SHALL fix errors iteratively until zero remain.
4. Stakeholder Gate: the agent SHALL set `status: PENDING_APPROVAL` and present artifact link to stakeholder.
   INVARIANT: the agent SHALL NOT proceed to downstream phases without explicit human approval.
5. Handoff: on confirmation, the agent SHALL set `status: APPROVED`, set `approved_by: human`, and prompt the next phase.
