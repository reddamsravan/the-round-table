---
name: review/concerns/complexity
description: >-
  ACE-spec rules for evaluating the Complexity concern during a code review.
  The agent SHALL read this file as part of Step 2 of the Review Execution Procedure.
---

# Complexity Concern Reference

## 1. Definition of Excessive Complexity

The agent SHALL define "exceeds cognitive readability" as code that satisfies at least one of these conditions:
- A typical code reader cannot understand the code in a single read-through.
- A developer will likely introduce bugs when calling or modifying the code.

## 2. Complexity Evaluation Rules

### Rule 1: Line-Level Complexity
The agent SHALL evaluate each changed line for individual complexity.
IF a single line contains more than 2 nested operations or requires re-reading to parse, THEN the agent SHALL flag it as SUGGESTION.

### Rule 2: Function-Level Complexity
The agent SHALL evaluate each changed or introduced function for complexity.
IF a function performs more than one distinct logical operation, THEN the agent SHALL flag it as SUGGESTION with a recommendation to decompose it.
IF a function contains more than 3 levels of nesting, THEN the agent SHALL flag it as SUGGESTION.

### Rule 3: Class-Level Complexity
The agent SHALL evaluate each changed or introduced class for complexity.
IF a class encapsulates more than one distinct responsibility, THEN the agent SHALL flag it as SUGGESTION with a recommendation to apply single-responsibility decomposition.

### Rule 4: Over-Engineering Detection
The agent SHALL identify over-engineering, defined as code made more generic than the current system requires.
IF the diff introduces abstractions, interfaces, or extension points for requirements not present in the current system, THEN the agent SHALL flag it as SUGGESTION.
The agent SHALL direct the author to solve the problem known to exist now, NOT the problem speculated to exist later.
INVARIANT: The agent SHALL address future problems when they arrive with their actual shape and requirements visible.

### Rule 5: Speculative Functionality
IF the diff adds functionality that no current requirement references, THEN the agent SHALL flag it as BLOCKER if it degrades code health, or SUGGESTION if it adds neutral unused code.

## 3. Complexity Standard

The agent SHALL encourage authors to simplify code rather than explain it in review comments.
IF the agent requests clarification about hard-to-read code and the author provides only a verbal explanation, THEN the agent SHALL request that the author rewrite the code to be self-explanatory.
IF the code requires a comment to become understandable, THEN the agent SHALL assess whether simplification is feasible before accepting the comment.
