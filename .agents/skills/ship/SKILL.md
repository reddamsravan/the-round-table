---
name: ship
description: Commits changes and authors retrospectives. Activate on '/ship'.
disable-model-invocation: true
---

The agent SHALL commit changes and author retrospectives.

## Rules
- IF commit execution fails, THEN the agent SHALL halt execution.

## Workflow
1. Activate the `commit` skill to stage and commit target modifications.
2. Execute Procedure A to author and validate the sprint retrospective.
3. Deliver the completion summary and retrospective path to the user.

## Procedures

### Procedure A: Retrospective Authoring
1. Copy `.agents/skills/ship/assets/retrospective_template.md` to `docs/.prompts-and-prayers/{work_slug}/06-ship/retrospective.md`.
2. Populate start, stop, and continue items adhering to [assets/retrospective_template.md](assets/retrospective_template.md).
3. Validate retrospective prose using the `prose` skill.
4. Present the retrospective artifact link to the user.

## Verification Checklist
- [ ] Verify that the agent committed all target modifications using the `commit` skill.
- [ ] Verify that `docs/.prompts-and-prayers/{work_slug}/06-ship/retrospective.md` exists.
- [ ] Verify that the retrospective contains all mandatory sections per [assets/retrospective_template.md](assets/retrospective_template.md).
- [ ] Verify that the retrospective passes prose validation.
