---
name: define
description: Defines objectives, scope boundaries, functional requirements, and acceptance criteria. Activate on '/define'.
disable-model-invocation: true
---

The agent SHALL formulate objectives, scope boundaries, functional requirements, and acceptance criteria.

## Rules
- All specification documents MUST adhere to [assets/spec_template.md](assets/spec_template.md).

## Workflow
1. Inspect the input problem statement, feature request, and codebase context.
2. IF the input contains ambiguities or missing boundaries, THEN execute Procedure A.
3. Copy `.agents/skills/define/assets/spec_template.md` to `docs/.prompts-and-prayers/{work_slug}/01-define/spec.md`.
4. Draft the specification adhering to [assets/spec_template.md](assets/spec_template.md).
5. Validate the specification using the `prose` skill with `--mode ace`.
6. Execute Procedure B to complete the stakeholder approval gate.
7. Deliver the approved specification path to the caller.

## Procedures

### Procedure A: Ambiguity Resolution
1. Activate the `interview` skill to formulate structured questions.
2. Present options, trade-offs, and recommendations to the user.
3. Await user confirmation on settled decisions before drafting the specification.

### Procedure B: Stakeholder Approval Gate
1. Set frontmatter status to `DRAFT` in `docs/.prompts-and-prayers/{work_slug}/01-define/spec.md`.
2. Present the specification artifact link and summary to the user.
3. Await explicit human confirmation.
4. IF the user approves the specification, THEN set `status: APPROVED`.
5. IF the user requests revisions, THEN revise the specification and re-execute Procedure B.

## Verification Checklist
- [ ] Verify that `docs/.prompts-and-prayers/{work_slug}/01-define/spec.md` exists.
- [ ] Verify that the document contains all mandatory sections per [assets/spec_template.md](assets/spec_template.md).
- [ ] Verify that the specification passes prose validation with `--mode ace`.
- [ ] Verify that frontmatter status is `APPROVED`.
- [ ] Obtain explicit user confirmation before downstream handoff.
