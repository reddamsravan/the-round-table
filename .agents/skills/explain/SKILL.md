---
name: explain
description: Explains code, architecture, errors, and concepts in plain English. Activate on '/explain' or requests to explain.
---

The agent SHALL explain code, architecture, errors, and concepts in a single laconic paragraph.

## Rules
- The explanation MUST NOT exceed one paragraph.

## Workflow
1. Inspect the target code, architecture, error message, or concept.
2. Invoke the `prose` skill to draft an explanation of maximum one paragraph.
3. IF the user specifies a target file path, THEN execute Procedure A.
4. Deliver the explanation to the user.

## Procedures

### Procedure A: Target File Delivery
1. Write the explanation to the specified target file path.
2. Confirm file creation and destination path to the user.

## Verification Checklist
- [ ] Verify that the explanation does not exceed one paragraph.
- [ ] Verify that the explanation passes prose validation.
- [ ] IF the user specified a target file path, THEN verify that the file exists at that destination.
- [ ] Deliver the explanation to the user.
