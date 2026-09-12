# Functionality Concern

Verify that changed code works as intended and handles edge cases safely.

## Rules

### Intent and Correctness
- Read the author stated goal in the diff description.
- Mark code that fails to achieve the stated goal as `[BLOCKER]`.
- Mark bugs found during code reading as `[BLOCKER]` with exact line numbers.

### Edge Cases
- Mark unhandled edge cases that cause data loss or crashes as `[BLOCKER]`.
- Mark edge cases with safe recovery paths as `[SUGGESTION]`.

### Concurrency
- Check shared state, async calls, and locks for race conditions or deadlocks.
- Mark possible race conditions or deadlocks as `[BLOCKER]`.
- Do not approve concurrent code unless static logic proves it safe.

### User Impact
- Mark harmful, unplanned changes to user flow as `[BLOCKER]`.
- Mark planned negative impacts as `[SUGGESTION]` and ask for reasons.

## Review Standards
- Assume the author tested normal paths.
- Focus review on edge cases, race conditions, and user impact.
