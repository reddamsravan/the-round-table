---
name: plot
description: Plans technical architecture, subsystem boundaries, and implementation milestones. Activate on '/plot'.
disable-model-invocation: true
---

The agent SHALL formulate technical architecture and high-level implementation plans.

## Rules
- The agent SHALL NOT modify application source code during technical planning.
- The agent SHALL NOT include file implementation code, method signatures, or parameter types in architecture specifications.

## Workflow
1. Inspect the definitions and designs provided by the user.
2. IF the input contains ambiguities or unresolved trade-offs, THEN execute Procedure A.
3. Copy `.agents/skills/plot/assets/tech_spec_template.md` to `docs/.prompts-and-prayers/{work_slug}/03-plot/tech-spec.md`.
4. Draft the technical specification adhering to [assets/tech_spec_template.md](assets/tech_spec_template.md).
5. Invoke the `breakdown` skill to generate the high-level plan in `docs/.prompts-and-prayers/{work_slug}/03-plot/plan.md` adhering to [assets/plan_template.md](assets/plan_template.md).
6. Validate the technical specification and plan using the `prose` skill with `--mode ace`.
7. Execute Procedure B to complete the stakeholder approval gate.
8. Deliver the approved artifact paths to the caller.

## Procedures

### Procedure A: Ambiguity Resolution
1. Activate the `interview` skill to resolve open trade-offs and ambiguities.
2. Incorporate settled decisions before drafting the technical specification.

### Procedure B: Stakeholder Approval Gate
1. Set frontmatter status to `DRAFT` in `docs/.prompts-and-prayers/{work_slug}/03-plot/tech-spec.md`.
2. Present the artifact links and summary to the user.
3. Await explicit human confirmation.
4. IF the user approves the artifacts, THEN set `status: APPROVED`.
5. IF the user requests revisions, THEN revise the artifacts and re-execute Procedure B.

## Verification Checklist
- [ ] Verify that `docs/.prompts-and-prayers/{work_slug}/03-plot/tech-spec.md` exists.
- [ ] Verify that `docs/.prompts-and-prayers/{work_slug}/03-plot/plan.md` exists.
- [ ] Verify that the technical specification contains all mandatory sections per [assets/tech_spec_template.md](assets/tech_spec_template.md).
- [ ] Verify that the implementation plan contains all mandatory sections per [assets/plan_template.md](assets/plan_template.md).
- [ ] Verify that the technical specification and plan pass prose validation with `--mode ace`.
- [ ] Verify that frontmatter status is `APPROVED`.
- [ ] Obtain explicit user confirmation before downstream handoff.
