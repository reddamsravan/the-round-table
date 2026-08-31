---
name: review/concerns/functionality
description: >-
  ACE-spec rules for evaluating the Functionality concern during a code review.
  The agent SHALL read this file as part of Step 2 of the Review Execution Procedure.
---

# Functionality Concern Reference

## 1. Primary Goal

The agent SHALL verify that the code does what the author intended.
The agent SHALL verify that the intended behavior is correct for both end-users and future developers.

## 2. Functionality Evaluation Rules

### Rule 1: Intent Verification
The agent SHALL determine the author's stated intent from the diff description, commit message, or comments.
The agent SHALL verify that the code logically achieves that intent.
IF the code does not achieve the stated intent, THEN the agent SHALL flag it as BLOCKER.

### Rule 2: Edge Case Analysis
The agent SHALL identify edge cases not handled by the diff.
IF an unhandled edge case will cause incorrect behavior or data loss, THEN the agent SHALL flag it as BLOCKER.
IF an unhandled edge case causes degraded but recoverable behavior, THEN the agent SHALL flag it as SUGGESTION.

### Rule 3: Concurrency and Race Conditions
IF the diff introduces parallel execution, threading, async patterns, or shared mutable state, THEN the agent SHALL evaluate for race conditions and deadlocks.
IF the agent identifies a plausible race condition or deadlock, THEN the agent SHALL flag it as BLOCKER.
The agent SHALL NOT approve concurrency code whose correctness the agent cannot verify through static analysis.

### Rule 4: User-Facing Impact
IF the diff alters user-facing behavior, THEN the agent SHALL evaluate whether the behavioral change benefits the target users.
IF the user-facing impact is adverse and unintentional, THEN the agent SHALL flag it as BLOCKER.
IF the user-facing impact is adverse and intentional, THEN the agent SHALL flag it as SUGGESTION and request justification.

### Rule 5: Bug Detection
The agent SHALL read the code to identify observable bugs without executing it.
IF the agent identifies a bug visible from static reading, THEN the agent SHALL flag it as BLOCKER with the specific line reference.

## 3. Verification Standard

The agent SHALL assume the author tested the code before review.
The agent SHALL NOT re-test the code unless explicitly requested.
The agent SHALL focus functionality review on edge cases, concurrency, and user impact.
