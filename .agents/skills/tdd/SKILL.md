---
# tdd skill in mattpocock/skills (https://github.com/mattpocock/skills/tree/main/skills/engineering/tdd)
name: tdd
description: >-
  Test-driven development. Activate on '/tdd', when the user wants to build features or fix bugs test-first, or mentions "red-green" or "integration tests".
---

The agent SHALL drive feature development and bug fixes through the red-green TDD loop.

## Rules

- The agent SHALL NOT write any test before confirming seams with the user.
- IF the test runner is not specified, THEN the agent SHALL detect it from the project configuration files.

## Workflow

1. Read [references/tests.md](references/tests.md) and [references/mocking.md](references/mocking.md).
2. Execute Procedure A to confirm seams with the user.
3. Execute Procedure B: the red-green loop, once per confirmed seam and target behavior.
4. Deliver the completed test file and production code to the user.

## Procedures

### Procedure A: Seam Confirmation

1. Identify all candidate seams for the feature or bug under test.
2. For each candidate seam, invoke the `explain` skill to describe the seam and the behaviors observable from it.
3. Ask the user: "Confirm this seam for testing?"
4. Record only confirmed seams.

### Procedure B: Red-Green Loop

Repeat for each confirmed seam and target behavior:

1. **Red**: Write one failing test that describes the target behavior through the confirmed seam. Run the test suite and confirm the new test fails.
2. **Green**: Write the minimum production code to pass the failing test. Run the test suite and confirm all tests pass.
3. IF more behaviors remain for this seam, THEN return to step 1.

## Verification Checklist

- [ ] Verify that the agent explained each seam via the `explain` skill before asking for confirmation.
- [ ] Verify that no test targets an unconfirmed seam.
- [ ] Verify that the agent wrote each test before the production code that satisfies it.
- [ ] Verify that each new test failed before the agent wrote the production code (red phase confirmed).
- [ ] Verify that all tests pass after the green phase.
- [ ] Confirm with the user that the delivered tests read as specifications.
