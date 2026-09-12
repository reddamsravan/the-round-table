# Documentation Concern

Check documentation updates across guides, README files, and API references.

## Rules

### Build and API Changes
- Mark public API changes without updated API guides as `[BLOCKER]`.
- Mark build, test, or setup changes without updated README files as `[BLOCKER]`.

### New and Deleted Features
- Mark new public features without user guides as `[SUGGESTION]`.
- Mark complex internal modules without guides as `[NIT]`.
- Mark deleted features that still appear in docs without notes as `[SUGGESTION]`.

### Accuracy and Clarity
- Mark wrong or misleading documentation as `[BLOCKER]`.
- Mark unclear or incomplete text as `[SUGGESTION]`.

### Scope
- Do not treat code comments as user documentation.
- External guides explain user steps; code comments explain why code exists.

## Review Standards
- Request missing documentation from the author.
- Do not skip doc checks for small code diffs.
