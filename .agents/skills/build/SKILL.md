---
name: build
description: Implements tasks using breakdown, subagents, and interviews. Activate on '/build'.
---

The agent SHALL implement engineering tasks in `docs/.prompts-and-prayers/{work_slug}/04-build/task.md` using task decomposition, unblocked execution, and criteria verification.

## Rules
- The agent SHALL NOT mark a task complete without passing all defined verification criteria.

## Workflow
1. Inspect the implementation ask and domain constraints.
2. IF the ask contains ambiguities, THEN execute Procedure A.
3. Invoke the `breakdown` skill to write the task graph to `docs/.prompts-and-prayers/{work_slug}/04-build/task.md`.
4. Present the task graph to the user and await explicit confirmation before starting execution.
5. Execute Procedure B to process all tasks in `docs/.prompts-and-prayers/{work_slug}/04-build/task.md`.
6. Present the execution summary and verification outcomes to the user.

## Procedures

### Procedure A: Ambiguity and Escalation Handling
1. Pause execution and invoke the `interview` skill to formulate structured questions.
2. Present options, trade-offs, and recommendations to the user.
3. Await user confirmation on settled decisions before resuming work.

### Procedure B: Task Graph Execution Loop
1. Read `docs/.prompts-and-prayers/{work_slug}/04-build/task.md` and identify unblocked tasks with satisfied prerequisites.
2. IF two or more independent tasks have satisfied prerequisites, THEN execute Procedure C.
3. IF one task has satisfied prerequisites, THEN execute the task in the workspace.
4. IF ambiguity arises during task execution, THEN execute Procedure A.
5. Execute verification commands and evaluate each acceptance criterion.
6. IF any criterion is not met or fails verification, THEN complete the required work and re-verify.
7. Mark each verified criterion checkbox as done in `docs/.prompts-and-prayers/{work_slug}/04-build/task.md`.
8. Mark the task complete in `docs/.prompts-and-prayers/{work_slug}/04-build/task.md` when all criteria pass.
9. Repeat steps 1 through 8 until all tasks reach completion.

### Procedure C: Concurrent Subagent Execution
1. Dispatch parallel subagents using `invoke_subagent` for each unblocked task.
2. Assign each subagent its task scope, file targets, and verification criteria.
3. Await completion notifications from all dispatched subagents.
4. Verify that each subagent satisfied all task acceptance criteria.
5. IF any criterion is not met or fails verification, THEN complete the required work and re-verify.
6. Mark each verified criterion checkbox and task complete in `docs/.prompts-and-prayers/{work_slug}/04-build/task.md`.

## Verification Checklist
- [ ] Verify that `docs/.prompts-and-prayers/{work_slug}/04-build/task.md` exists and contains a valid task graph.
- [ ] Verify that the user confirmed the task graph before execution started.
- [ ] Resolve all ambiguities and trade-offs using the `interview` skill.
- [ ] Dispatch concurrent subagents for independent unblocked tasks.
- [ ] Verify that each task passes all defined verification commands with zero exit code.
- [ ] Verify that all tasks in `docs/.prompts-and-prayers/{work_slug}/04-build/task.md` reach completed status.

