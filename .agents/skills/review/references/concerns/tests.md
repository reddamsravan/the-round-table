---
name: review/concerns/tests
description: >-
  ACE-spec rules for evaluating the Tests concern during a code review.
  The agent SHALL read this file as part of Step 2 of the Review Execution Procedure.
---

# Tests Concern Reference

## 1. Test Coverage Requirement

The agent SHALL verify that the diff includes tests matching the scope of the change.
The agent SHALL determine whether unit tests, integration tests, or end-to-end tests match the scope of the change.
IF the diff modifies production logic and includes no new or updated tests, THEN the agent SHALL flag it as BLOCKER.
IF tests exist but do not cover the changed logic paths, THEN the agent SHALL flag the gap as BLOCKER.

## 2. Test Quality Rules

### Rule 1: Test Validity
The agent SHALL verify that each test will actually fail when a developer breaks the production code.
IF a test asserts a condition that cannot detect a regression in the changed code, THEN the agent SHALL flag it as BLOCKER.

### Rule 2: False Positive Risk
The agent SHALL assess whether tests will produce false positives if the underlying code changes.
IF a test is tightly coupled to implementation details rather than observable behavior, THEN the agent SHALL flag it as SUGGESTION.

### Rule 3: Assertion Quality
The agent SHALL verify that each test makes focused, precise, and useful assertions.
IF a test makes no assertions or asserts only trivially true conditions, THEN the agent SHALL flag it as BLOCKER.
IF a test makes overly broad assertions that reduce its diagnostic value, THEN the agent SHALL flag it as SUGGESTION.

### Rule 4: Test Isolation
The agent SHALL verify that tests separate each behavior into a distinct test method.
IF a single test method covers multiple unrelated behaviors, THEN the agent SHALL flag it as SUGGESTION.

### Rule 5: Test Complexity
The agent SHALL apply the same complexity standards to test code as to production code.
INVARIANT: Developers MUST maintain test code with the same rigor as production code.
IF a test is harder to understand than the code it tests, THEN the agent SHALL flag it as SUGGESTION.
The agent SHALL NOT accept test complexity on the grounds that tests are non-production code.

## 3. Test Correctness Standard

The agent SHALL verify test correctness manually; tests do not test themselves.
The agent SHALL evaluate whether test assertions correctly capture the intended behavior of the production code.
The agent SHALL flag incorrect test logic as BLOCKER, not as SUGGESTION.
