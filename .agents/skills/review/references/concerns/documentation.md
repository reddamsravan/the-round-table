---
name: review/concerns/documentation
description: >-
  ACE-spec rules for evaluating the Documentation concern during a code review.
  The agent SHALL read this file as part of Step 2 of the Review Execution Procedure.
---

# Documentation Concern Reference

## 1. Documentation Scope

The agent SHALL evaluate documentation for the following artifact types:
- README files
- Architecture decision records (ADRs)
- API reference documentation
- Setup, build, test, and release guides
- Changelogs

## 2. Documentation Evaluation Rules

### Rule 1: Impact-Triggered Updates
IF the diff changes how users build, test, interact with, or release the system, THEN the agent SHALL verify that associated documentation is also updated.
IF the diff changes a public API and the API reference is not updated, THEN the agent SHALL flag it as BLOCKER.
IF the diff changes a setup or build process and the README is not updated, THEN the agent SHALL flag it as BLOCKER.

### Rule 2: Deprecation and Deletion
IF the diff deletes or deprecates a feature, function, or module, THEN the agent SHALL verify whether associated documentation requires deletion or annotation.
IF documentation for a deleted feature remains without a deprecation notice, THEN the agent SHALL flag it as SUGGESTION.

### Rule 3: Missing Documentation
IF the diff introduces a new public-facing feature or API with no accompanying documentation, THEN the agent SHALL flag it as SUGGESTION.
IF the diff introduces an internal module with non-trivial, multi-step behavior and no documentation, THEN the agent SHALL flag it as NIT.

### Rule 4: Documentation Accuracy
IF existing documentation referenced by the diff contains inaccurate information after the change, THEN the agent SHALL flag it as BLOCKER.
IF documentation is technically accurate but unclear or incomplete, THEN the agent SHALL flag it as SUGGESTION.

### Rule 5: Documentation Scope Separation
The agent SHALL NOT conflate inline code comments with external documentation.
Inline comments (covered in comments.md) SHALL NOT substitute for README or API reference updates.
External documentation SHALL describe user-facing behavior; inline comments SHALL describe implementation rationale.

## 3. Documentation Standard

The agent SHALL request documentation updates, not author them.
IF the system requires documentation that the diff omits, THEN the agent SHALL flag the gap with a description of the missing documentation.
The agent SHALL NOT silently skip the documentation concern on the grounds that the diff is "small" or "internal".
