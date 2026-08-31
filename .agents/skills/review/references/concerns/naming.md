---
name: review/concerns/naming
description: >-
  ACE-spec rules for evaluating the Naming concern during a code review.
  The agent SHALL read this file as part of Step 2 of the Review Execution Procedure.
---

# Naming Concern Reference

## 1. Naming Standard

The agent SHALL evaluate names for all introduced or modified identifiers.
The agent SHALL evaluate: variables, functions, methods, classes, modules, files, constants, and type aliases.

## 2. Naming Evaluation Rules

### Rule 1: Communicative Completeness
The agent SHALL verify that each name fully communicates what the item is or does.
IF a name requires additional context to understand its purpose, THEN the agent SHALL flag it as SUGGESTION with a proposed alternative.
IF a name is a single letter or generic placeholder (e.g., `x`, `temp`, `data`, `obj`) outside of a conventional loop counter, THEN the agent SHALL flag it as SUGGESTION.

### Rule 2: Length Calibration
The agent SHALL verify that names are neither too short nor too long.
IF a name is so long it impedes readability, THEN the agent SHALL flag it as NIT with a proposed shorter alternative.
IF a name is so short it fails to communicate its purpose, THEN the agent SHALL flag it as SUGGESTION.

### Rule 3: Boolean Naming
IF a boolean variable or function name does not form a clear predicate (e.g., `is_valid`, `has_errors`, `can_retry`), THEN the agent SHALL flag it as SUGGESTION.

### Rule 4: Function Naming
IF a function name does not describe its action as a verb phrase (e.g., `calculate_total`, `fetch_user`, `validate_schema`), THEN the agent SHALL flag it as SUGGESTION.

### Rule 5: Consistency
The agent SHALL verify that naming follows existing conventions in the surrounding codebase.
IF a new name contradicts the established naming convention of adjacent code, THEN the agent SHALL flag it as SUGGESTION.
IF no convention exists, THEN the agent SHALL accept the author's naming choice without flagging.

## 3. Naming Standard Principle

Clear names reduce the need for explanatory comments.
IF fixing a name eliminates the need for an associated comment, THEN the agent SHALL prefer recommending the name fix over accepting the comment.
