---
name: verify
description: Verifies criteria against the workspace. Activate on '/verify'.
disable-model-invocation: true
---

The agent SHALL evaluate criteria against the workspace and report verification outcomes.

## Rules
- The agent SHALL NOT mark a criterion as passed without verifiable evidence from tool calls or command execution.
- IF any criterion fails verification, THEN the agent SHALL report failure details to the user.

## Workflow
1. Inspect input prompt arguments, criteria files, or query the user for criteria.
2. Evaluate each criterion individually against the workspace using tool calls and commands.
3. Record deterministic pass or fail status and concrete evidence for each criterion.
4. IF the user specifies a target file path, THEN execute Procedure A.
5. Deliver the criteria verification summary and overall verdict to the user.

## Procedures

### Procedure A: Target File Delivery
1. Write the completed verification report to the specified target file path.
2. Verify that the written file exists at the specified destination.
3. Confirm file creation and output location to the user.

## Verification Checklist
- [ ] Verify that the agent evaluated all criteria individually.
- [ ] Verify that every passed criterion records concrete verification evidence.
- [ ] Verify that every failed criterion records failure details.
- [ ] IF the user specified a target file path, THEN verify that the artifact exists at that path.
