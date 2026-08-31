---
name: review/concerns/style
description: >-
  ACE-spec rules for evaluating the Style concern during a code review.
  The agent SHALL read this file as part of Step 2 of the Review Execution Procedure.
---

# Style Concern Reference

## 1. Style Authority

The agent SHALL treat the project's style guide as the absolute authority on style.
IF the project specifies a style guide, THEN the agent SHALL verify the diff follows it.
IF a style guide is not specified, THEN the agent SHALL accept the author's style without flagging deviations.
INVARIANT: The agent SHALL NOT block a diff based solely on personal style preferences not grounded in a style guide.

## 2. Style Evaluation Rules

### Rule 1: Style Guide Compliance
IF the diff violates a rule explicitly stated in the style guide, THEN the agent SHALL flag it as SUGGESTION.
IF the diff violates a formatting rule (whitespace, indentation, import ordering), THEN the agent SHALL flag it as NIT.

### Rule 2: Nitpick Labeling
IF a style finding is a minor preference point not mandated by the style guide, THEN the agent SHALL flag it as NIT.
The agent SHALL prefix such comments with "Nit:" to signal optionality to the author.

### Rule 3: Mixed Style Changes
IF the diff combines major style changes (e.g., file-wide reformatting) with functional changes, THEN the agent SHALL flag it as BLOCKER.
The agent SHALL request the author separate the reformatting into a dedicated diff.
Mixing style and logic changes obscures the functional diff, complicates merges, and impedes rollbacks.

### Rule 4: Consistency with Surrounding Code
IF no style guide rule applies to a specific pattern, THEN the agent SHALL verify the new code is consistent with the surrounding existing code.
IF the new code is inconsistent with surrounding code, THEN the agent SHALL flag it as NIT.
IF existing surrounding code violates the style guide, THEN the agent SHALL accept the author's style guide-compliant choice over the surrounding inconsistency.

### Rule 5: Existing Code Inconsistency
IF the diff introduces style-guide-compliant code into a file that itself is inconsistent with the style guide, THEN the agent SHALL accept the diff.
The agent SHALL optionally note the broader inconsistency as NIT and suggest the author file a cleanup task.

## 3. Style Standard Principle

Style disagreements SHALL NOT delay the merge of a functionally correct diff.
The agent SHALL NOT escalate style SUGGESTIONs to BLOCKERs unless the style issue creates ambiguity, a functional defect, or directly violates a mandatory style guide rule.
