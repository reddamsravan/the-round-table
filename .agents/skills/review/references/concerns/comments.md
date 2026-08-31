---
name: review/concerns/comments
description: >-
  ACE-spec rules for evaluating the Comments concern during a code review.
  The agent SHALL read this file as part of Step 2 of the Review Execution Procedure.
---

# Comments Concern Reference

## 1. Comment Purpose Standard

The agent SHALL distinguish between inline comments and documentation comments.
Inline comments SHALL explain WHY code exists, not WHAT the code does.
Documentation comments (docstrings, JSDoc, KDoc, Rustdoc) SHALL express the purpose, expected usage, and behavior of a function, class, or module.
The agent SHALL apply the rules below to each category separately.

## 2. Inline Comment Rules

### Rule 1: Why vs. What
IF an inline comment explains what the code does rather than why it exists, THEN the agent SHALL flag it as SUGGESTION.
The agent SHALL recommend deleting the comment or rewriting the code to be self-explanatory.

### Rule 2: Comment Necessity
IF an inline comment describes something already obvious from the code, THEN the agent SHALL flag it as NIT for removal.
IF an inline comment provides information the code cannot express (e.g., business reasoning, legal constraints, algorithm citations), THEN the agent SHALL accept it without flagging.

### Rule 3: Exceptions for Non-Obvious Algorithms
The agent SHALL accept inline comments that explain regular expressions, non-trivial algorithms, or mathematical derivations.
IF such a comment exists but the explanation is incorrect or misleading, THEN the agent SHALL flag it as BLOCKER.

### Rule 4: Stale Comments
The agent SHALL check whether pre-existing comments in modified code remain accurate after the change.
IF a comment no longer accurately describes the surrounding code, THEN the agent SHALL flag it as BLOCKER.
IF the current diff resolves a TODO comment and the comment remains, THEN the agent SHALL flag its retention as NIT.

## 3. Documentation Comment Rules

### Rule 5: Presence
IF a public function, class, or module introduced in the diff lacks a documentation comment, THEN the agent SHALL flag it as SUGGESTION.
IF a private function performs a non-obvious operation and lacks a documentation comment, THEN the agent SHALL flag it as NIT.

### Rule 6: Accuracy
IF a documentation comment inaccurately describes the function's behavior, parameters, or return value, THEN the agent SHALL flag it as BLOCKER.
IF a documentation comment is incomplete (e.g., missing parameter descriptions for public APIs), THEN the agent SHALL flag it as SUGGESTION.

## 4. Review Authoring Standard

The agent SHALL produce review comments about the code, NOT about the author.
The agent SHALL explain the reasoning behind each finding.
The agent SHALL balance pointing out problems with providing direct guidance.
IF the agent requests clarification about code it does not understand, THEN the agent SHALL expect the author to rewrite the code more clearly, not just explain it verbally.
INVARIANT: Explanations provided only in the review tool and not reflected in code or comments are NOT acceptable as a permanent resolution.
