#!/usr/bin/env python3
"""
Test suite for Persona Validators (qa, scrum-master).
"""

import unittest
import os
import sys
import tempfile
import shutil
import importlib.util

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def load_module(name: str, rel_path: str):
    full_path = os.path.join(REPO_ROOT, rel_path)
    spec = importlib.util.spec_from_file_location(name, full_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


qa_mod = load_module("qa_validator", ".agents/skills/qa/scripts/validator.py")
sm_mod = load_module("sm_validator", ".agents/skills/scrum-master/scripts/validator.py")


class TestQAValidator(unittest.TestCase):
    def setUp(self):
        self.validator = qa_mod.QAValidator()

    def test_valid_qa_report(self):
        content = """---
sprint: sprint-1
persona: qa
status: APPROVED
approved_by: pending
handoff_to: scrum-master
artifacts:
  - 05-reviews/report.md
---

# QA Verification & Code Review Report: Auth Module

## 1. Automated Test Execution Evidence
```text
Ran 10 tests in 0.05s
OK
```

## 2. 8-Concern Code Review Summary
- Verdict: APPROVED
- Total Blockers: 0

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
- Clean test structure.
"""
        diags, summary = self.validator.validate_text(content, "report.md")
        errors = [d for d in diags if d.severity == "ERROR"]
        self.assertEqual(len(errors), 0, f"Expected 0 errors, got: {[e.to_dict() for e in errors]}")
        self.assertTrue(summary["approved"])

    def test_blockers_in_approved_report(self):
        content = """---
sprint: sprint-1
persona: qa
status: APPROVED
approved_by: pending
handoff_to: scrum-master
artifacts:
  - 05-reviews/report.md
---

# QA Verification & Code Review Report: Auth Module

## 1. Automated Test Execution Evidence
```text
FAILED (failures=1)
```

## 2. 8-Concern Code Review Summary
Verdict: NEEDS CHANGES

## 3. Detailed Findings
### Design
- [BLOCKER] Critical interface flaw.
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
- None.
"""
        diags, summary = self.validator.validate_text(content, "report.md")
        error_rules = {d.rule_id for d in diags if d.severity == "ERROR"}
        self.assertIn("UNRESOLVED_BLOCKERS_PRESENT", error_rules)
        self.assertIn("INVALID_APPROVED_VERDICT", error_rules)


class TestScrumMasterValidator(unittest.TestCase):
    def setUp(self):
        self.validator = sm_mod.ScrumMasterValidator()
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_valid_scrum_master_release(self):
        os.makedirs(os.path.join(self.test_dir, "04-tasks"))
        os.makedirs(os.path.join(self.test_dir, "05-reviews"))
        os.makedirs(os.path.join(self.test_dir, "06-release"))

        with open(os.path.join(self.test_dir, "04-tasks", "plan.md"), "w") as f:
            f.write("### Task: PLAN-001\nstatus: DONE\n")

        with open(os.path.join(self.test_dir, "05-reviews", "2026-09-07_review.md"), "w") as f:
            f.write("---\nstatus: APPROVED\n---\n")

        with open(os.path.join(self.test_dir, "06-release", "release-notes.md"), "w") as f:
            f.write("""---
sprint: sprint-1
persona: scrum-master
status: DRAFT
approved_by: pending
handoff_to: po
artifacts:
  - 06-release/release-notes.md
---

# Sprint Release Notes: Auth Release

## 1. Release Summary
Summary of release.

## 2. Delivered Features & User Stories
| US-001 | Auth | Delivered |

## 3. Conventional Commit Log
- feat(auth): add email login

## 4. Verification Signoff
Approved.
""")

        with open(os.path.join(self.test_dir, "06-release", "retrospective.md"), "w") as f:
            f.write("""# Sprint Retrospective: Auth Release

## 1. Sprint Execution Metrics
Metrics.

## 2. What Went Well
Good tests.

## 3. Opportunities for Improvement
None.

## 4. Action Items for Next Sprint
- Action item.
""")

        diags, summary = self.validator.validate_sprint(self.test_dir)
        errors = [d for d in diags if d.severity == "ERROR"]
        self.assertEqual(len(errors), 0, f"Expected 0 errors, got: {[e.to_dict() for e in errors]}")


if __name__ == "__main__":
    unittest.main()
