# Tests Concern

Verify test coverage, correctness, and assertion quality for all code changes.

## Rules

### Test Coverage
- Mark production changes without new or updated tests as `[BLOCKER]`.
- Mark tests that skip changed logic paths as `[BLOCKER]`.

### Test Validity and Logic
- Verify that tests fail when production code breaks.
- Mark tests that cannot catch bugs in changed code as `[BLOCKER]`.
- Mark wrong test logic or bad test checks as `[BLOCKER]`.

### Assertion Quality
- Mark tests with no assertions or trivial checks as `[BLOCKER]`.
- Mark broad assertions that hide bug causes as `[SUGGESTION]`.

### Design and Isolation
- Mark tests tied to internal details rather than outputs as `[SUGGESTION]`.
- Mark single test methods that check multiple unrelated tasks as `[SUGGESTION]`.
- Mark tests that are harder to read than production code as `[SUGGESTION]`.

## Review Standards
- Verify test logic manually. Tests do not test themselves.
- Hold test code to the same high quality bar as production code.
