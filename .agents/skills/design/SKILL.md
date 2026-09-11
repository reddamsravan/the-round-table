---
name: design
description: Designs flows, interface contracts, state models, and requirements. Activate on '/design'.
disable-model-invocation: true
---

The agent SHALL formulate flows, interface contracts, state models, and requirements.

## Rules
- All design documents MUST adhere to [assets/design_template.md](assets/design_template.md).

## Workflow
1. Inspect input problem statements, requirements specifications, and codebase context.
2. IF the input contains ambiguities or missing interface details, THEN execute Procedure A.
3. Copy `.agents/skills/design/assets/design_template.md` to `docs/.prompts-and-prayers/{work_slug}/02-design/design-spec.md`.
4. Draft the design specification adhering to [assets/design_template.md](assets/design_template.md).
5. Validate the design specification using the `prose` skill with `--mode ace`.
6. Execute Procedure B to complete the stakeholder approval gate.
7. Deliver the approved design specification path to the caller.

## Procedures

### Procedure A: Ambiguity Resolution
1. Activate the `interview` skill to resolve ambiguities.
2. Incorporate settled decisions before drafting the design specification.

### Procedure B: Stakeholder Approval Gate
1. Set frontmatter status to `DRAFT` in `docs/.prompts-and-prayers/{work_slug}/02-design/design-spec.md`.
2. Present the design specification artifact link and summary to the user.
3. Await explicit human confirmation.
4. IF the user approves the design specification, THEN set `status: APPROVED`.
5. IF the user requests revisions, THEN revise the design specification and re-execute Procedure B.

## Verification Checklist
- [ ] Verify that `docs/.prompts-and-prayers/{work_slug}/02-design/design-spec.md` exists.
- [ ] Verify that the document contains all mandatory sections per [assets/design_template.md](assets/design_template.md).
- [ ] Verify that the design specification passes prose validation with `--mode ace`.
- [ ] Verify that frontmatter status is `APPROVED`.
- [ ] Obtain explicit user confirmation before downstream handoff.
