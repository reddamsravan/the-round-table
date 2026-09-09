---
name: plot
description: Plans technical architecture, component contracts, and implementation milestones.
---

The agent SHALL formulate technical architecture in `docs/.prompts-and-prayers/{work_slug}/03-plot/tech-spec.md` and implementation plans in `docs/.prompts-and-prayers/{work_slug}/03-plot/plan.md`.

## Specification Invariants

Every plot artifact set MUST satisfy these rules:

1. **Frontmatter Envelope**:
   - `slug`: Work slug identifier.
   - `status`: One of `DRAFT`, `PENDING_APPROVAL`, `APPROVED`, `REJECTED`.
   - `approved_by`: `pending` or `human`.
   - `artifacts`: List containing paths for `tech-spec.md` and `plan.md`.
2. **Technical Specification Structure**:
   - `# Technical Specification: <Title>`
   - `## 1. System Overview & Architecture Topology`
   - `## 2. Architectural Decision Records (ADRs)`
   - `## 3. Component Contracts & Interfaces`
   - `## 4. Technical Constraints & Invariants`
3. **Visualizations**: Section 1 of `tech-spec.md` MUST contain a Mermaid flowchart.
4. **Implementation Plan Structure**:
   - `# Implementation Plan: <Title>`
   - `## Plan Overview`
   - `## Engineering Tasks`
   - Tasks formatted as `### Task: PLAN-<NNN> - <Title>` with YAML `id`, `title`, `status`, `depends_on`, and `acceptance_criteria`.
5. **Deterministic Criteria**: active SVO items in constraints and criteria using `SHALL` or `MUST`.
   INVARIANT: criteria SHALL NOT use passive voice or ambiguous words.

## Execution Procedure

GIVEN approved definitions and designs.
WHEN the agent activates the plot skill:
1. Intake: the agent SHALL inspect definitions and designs in `01-define/` and `02-design/`.
2. Trade-offs: IF open trade-offs exist, THEN the agent SHALL activate the `grill` skill.
3. Generate: the agent SHALL fill `.agents/skills/plot/assets/tech_spec_template.md` and `.agents/skills/plot/assets/plan_template.md` under `docs/.prompts-and-prayers/{work_slug}/03-plot/`.
4. Validate: the agent SHALL run:
   ```bash
   python3 .agents/skills/plot/scripts/validator.py docs/.prompts-and-prayers/{work_slug}/03-plot/ --json
   ```
   The agent SHALL fix errors iteratively until zero remain.
5. Stakeholder Gate: the agent SHALL set `status: PENDING_APPROVAL` and present artifact links to stakeholder.
   INVARIANT: the agent SHALL NOT proceed to downstream phases without explicit human approval.
6. Handoff: on confirmation, the agent SHALL set `status: APPROVED`, set `approved_by: human`, and prompt the next phase.
