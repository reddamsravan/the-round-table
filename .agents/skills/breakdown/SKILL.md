---
name: breakdown
description: Decomposes plans into directed acyclic task graphs. Activate on '/breakdown'.
---

The agent SHALL decompose engineering work into directed acyclic task graphs with deterministic acceptance criteria.

## Rules
- Every task breakdown MUST define unique task identifiers, clear titles, explicit dependencies, and concrete acceptance criteria.
- The task dependency graph MUST NOT contain cyclic references or self-dependencies.
- The agent SHALL NOT execute git commits during task breakdown generation.

## Workflow
1. Inspect input requirements, architecture specifications, or implementation plans.
2. Decompose work into atomic task units with explicit scope boundaries.
3. Map prerequisite dependencies across all tasks to form a directed acyclic graph.
4. Author deterministic acceptance criteria for each atomic task.
5. Identify unblocked tasks with satisfied dependencies.
6. IF the user or caller specifies a target file path, THEN execute Procedure A.
7. Deliver the structured task graph and unblocked tasks to the caller.

## Procedures

### Procedure A: Target File Delivery
1. Write the completed task breakdown to the specified target file path.
2. Verify that the written file exists at the specified destination.
3. Confirm file creation and output location to the user.

## Verification Checklist
- [ ] Verify that all task identifiers are unique within the breakdown.
- [ ] Verify that the dependency graph contains no cyclic references or missing prerequisites.
- [ ] Verify that every task defines concrete, testable acceptance criteria.
- [ ] Verify that the task breakdown covers all scope items from the input plan.
- [ ] IF the user or caller specified a target file path, THEN verify that the artifact exists at that path.
