---
name: review
description: Performs structured, concern-driven code reviews on diffs and pull requests. Activate on '/review'.
disable-model-invocation: true
---

The agent SHALL evaluate code changes against quality concern guides and author structured review reports.

## Rules
- The agent SHALL NOT modify application source code during review.

## Workflow
1. Inspect target modifications from user input or the git working tree.
2. Read all concern guides located in `references/concerns/`.
3. Execute Procedure A to evaluate all concerns concurrently using parallel subagents.
4. Consolidate findings and identify real strengths from subagent outputs.
5. Determine the overall verdict based on finding severity.
6. Author the review report adhering to [assets/review_template.md](assets/review_template.md).
7. IF the user or caller specifies a target file path, THEN execute Procedure B.
8. Deliver the review report to the caller.

## Procedures

### Procedure A: Concurrent Subagent Evaluation
1. Dispatch parallel subagents for each concern guide in `references/concerns/`.
2. Assign each subagent its concern guide and the target modifications.
3. Instruct each subagent to evaluate changes against its assigned concern guide.
4. Instruct each subagent to tag findings with `[BLOCKER]`, `[SUGGESTION]`, or `[NIT]`.
5. Await completion notifications from all dispatched subagents.
6. Collect findings and positive observations from all subagents.

### Procedure B: Target File Delivery
1. Write the completed review report to the specified target file path.
2. Verify that the written file exists at the specified destination.
3. Confirm file creation and output location to the user.

## Verification Checklist
- [ ] Dispatch parallel subagents for each concern guide in `references/concerns/`.
- [ ] Await completion from all dispatched subagents.
- [ ] Verify that every finding assigns an explicit severity label.
- [ ] Verify that the overall verdict matches finding severities.
- [ ] Verify that the review report contains all sections per [assets/review_template.md](assets/review_template.md).
- [ ] IF the user or caller specified a target file path, THEN verify that the artifact exists at that path.
