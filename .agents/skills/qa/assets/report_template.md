---
sprint: {SPRINT_ID}
persona: qa
status: DRAFT
approved_by: pending
handoff_to: scrum-master
artifacts:
  - docs/.prompts-and-prayers/sprints/{SPRINT_ID}/05-reviews/{DATE}_{SLUG}.md
---

# QA Verification & Code Review Report: {SPRINT_TITLE}

## 1. Automated Test Execution Evidence

### Test Command
```bash
python3 -m unittest discover tests
```

### Execution Output
```text
{Paste of test command execution output}
```

### Test Metrics
- **Total Tests Executed**: {N}
- **Passed**: {N}
- **Failed**: 0
- **Errors**: 0

## 2. 8-Concern Code Review Summary

- **Overall Verdict**: {APPROVED | APPROVED WITH SUGGESTIONS | NEEDS CHANGES}
- **Severity Totals**: 0 BLOCKERs, {N} SUGGESTIONs, {N} NITs

### Verdict Criteria
- `APPROVED`: 0 BLOCKERs, 0 SUGGESTIONs, 0 NITs.
- `APPROVED WITH SUGGESTIONS`: 0 BLOCKERs, one or more SUGGESTIONs or NITs.
- `NEEDS CHANGES`: One or more BLOCKER findings.

## 3. Detailed Findings

### Design
- No issues found.

### Functionality
- No issues found.

### Complexity
- No issues found.

### Tests
- No issues found.

### Naming
- No issues found.

### Comments
- No issues found.

### Style
- No issues found.

### Documentation
- No issues found.

## 4. Strengths & Positive Observations

- {Observed engineering strengths and clean patterns}
