#!/usr/bin/env python3
"""
Test suite for Verify Skill Verification and Review Report Validator.
"""

import unittest
import os
import sys
import tempfile
import shutil
import subprocess
import importlib.util

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
validator_path = os.path.join(REPO_ROOT, ".agents", "skills", "verify", "scripts", "validator.py")

spec = importlib.util.spec_from_file_location("verify_validator_mod", validator_path)
verify_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verify_mod)

VerifyValidator = verify_mod.VerifyValidator


class TestVerifyValidator(unittest.TestCase):
    def setUp(self):
        self.validator = VerifyValidator()
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_valid_verification_report(self):
        content = """---
slug: auth-feature
status: APPROVED
approved_by: human
artifacts:
  - docs/.prompts-and-prayers/auth-feature/05-verify/verification-report.md
---

# Verification Report: Authentication Feature

## 1. Automated Test Execution Evidence

### Test Command
```bash
python3 -m unittest discover tests
```

### Execution Output
```text
Ran 12 tests in 0.05s
OK
```

### Test Metrics
- **Total Tests Executed**: 12
- **Passed**: 12
- **Failed**: 0
- **Errors**: 0

## 2. 8-Concern Code Review Summary

- **Overall Verdict**: APPROVED
- **Severity Totals**: 0 BLOCKERs, 0 SUGGESTIONs, 0 NITs

## 3. Detailed Findings

### Design
- Clean service separation.

### Functionality
- All scenarios covered.

### Complexity
- Linear complexity.

### Tests
- Full test coverage.

### Naming
- Intuitive names.

### Comments
- Clear docstrings.

### Style
- Conforms to PEP 8.

### Documentation
- Updated guide.

## 4. Strengths & Positive Observations

- Solid test coverage and modular architecture.
"""
        diags, summary = self.validator.validate_text(content, "verification-report.md")
        errors = [d for d in diags if d.severity == "ERROR"]
        self.assertEqual(len(errors), 0, f"Expected 0 errors, got: {[e.to_dict() for e in errors]}")
        self.assertEqual(summary["slug"], "auth-feature")
        self.assertEqual(summary["status"], "APPROVED")
        self.assertTrue(summary["approved"])
        self.assertEqual(summary["blockers_found"], 0)

    def test_extra_key_in_frontmatter_ignored(self):
        content = """---
slug: auth-feature
persona: qa
status: DRAFT
approved_by: pending
artifacts:
  - verification-report.md
---

# Verification Report: Authentication Feature

## 1. Automated Test Execution Evidence
OK

## 2. 8-Concern Code Review Summary
Approved.

## 3. Detailed Findings
### Design
- Clean.
### Functionality
- Clean.
### Complexity
- Clean.
### Tests
- Clean.
### Naming
- Clean.
### Comments
- Clean.
### Style
- Clean.
### Documentation
- Clean.

## 4. Strengths & Positive Observations
- None.
"""
        diags, _ = self.validator.validate_text(content, "verification-report.md")
        errors = [d for d in diags if d.severity == "ERROR"]
        self.assertEqual(len(errors), 0)

    def test_frontmatter_missing_and_unclosed(self):
        content_no_fm = """# Verification Report: Auth
## 1. Automated Test Execution Evidence
## 2. 8-Concern Code Review Summary
## 3. Detailed Findings
## 4. Strengths & Positive Observations
"""
        diags, _ = self.validator.validate_text(content_no_fm, "verification-report.md")
        error_rules = {d.rule_id for d in diags if d.severity == "ERROR"}
        self.assertIn("FRONTMATTER_MISSING", error_rules)

        content_unclosed = """---
slug: auth
# Verification Report: Auth
## 1. Automated Test Execution Evidence
## 2. 8-Concern Code Review Summary
## 3. Detailed Findings
## 4. Strengths & Positive Observations
"""
        diags, _ = self.validator.validate_text(content_unclosed, "verification-report.md")
        error_rules = {d.rule_id for d in diags if d.severity == "ERROR"}
        self.assertIn("FRONTMATTER_UNCLOSED", error_rules)

    def test_frontmatter_schema_errors(self):
        content = """---
slug: auth
status: INVALID_STATUS
approved_by: machine
artifacts: []
---

# Verification Report: Auth
## 1. Automated Test Execution Evidence
## 2. 8-Concern Code Review Summary
## 3. Detailed Findings
### Design
### Functionality
### Complexity
### Tests
### Naming
### Comments
### Style
### Documentation
## 4. Strengths & Positive Observations
"""
        diags, _ = self.validator.validate_text(content, "verification-report.md")
        error_rules = {d.rule_id for d in diags if d.severity == "ERROR"}
        self.assertIn("SCHEMA_INVALID_STATUS", error_rules)
        self.assertIn("SCHEMA_INVALID_APPROVED_BY", error_rules)
        self.assertIn("SCHEMA_INVALID_ARTIFACTS", error_rules)

    def test_strict_heading_and_missing_sections(self):
        # Legacy QA title should fail strict heading requirement
        content = """---
slug: auth
status: DRAFT
approved_by: pending
artifacts:
  - test.md
---

# QA Verification & Code Review Report: Auth
## 1. Automated Test Execution Evidence
## 2. 8-Concern Code Review Summary
## 3. Detailed Findings
### Design
### Functionality
### Complexity
### Tests
### Naming
### Comments
### Style
### Documentation
## 4. Strengths & Positive Observations
"""
        diags, _ = self.validator.validate_text(content, "verification-report.md")
        error_rules = {d.rule_id for d in diags if d.severity == "ERROR"}
        self.assertIn("STRUCTURE_MISSING_SECTION", error_rules)

    def test_section_order_invalid(self):
        content = """---
slug: auth
status: DRAFT
approved_by: pending
artifacts:
  - test.md
---

# Verification Report: Auth
## 2. 8-Concern Code Review Summary
## 1. Automated Test Execution Evidence
## 3. Detailed Findings
### Design
### Functionality
### Complexity
### Tests
### Naming
### Comments
### Style
### Documentation
## 4. Strengths & Positive Observations
"""
        diags, _ = self.validator.validate_text(content, "verification-report.md")
        error_rules = {d.rule_id for d in diags if d.severity == "ERROR"}
        self.assertIn("SECTION_ORDER_INVALID", error_rules)

    def test_missing_concern_headings(self):
        content = """---
slug: auth
status: DRAFT
approved_by: pending
artifacts:
  - test.md
---

# Verification Report: Auth
## 1. Automated Test Execution Evidence
## 2. 8-Concern Code Review Summary
## 3. Detailed Findings
### Design
- Good.
### Functionality
- Good.
## 4. Strengths & Positive Observations
"""
        diags, _ = self.validator.validate_text(content, "verification-report.md")
        error_rules = {d.rule_id for d in diags if d.severity == "ERROR"}
        self.assertIn("MISSING_CONCERN_HEADING", error_rules)

    def test_blockers_in_approved_report(self):
        content = """---
slug: auth
status: APPROVED
approved_by: human
artifacts:
  - test.md
---

# Verification Report: Auth
## 1. Automated Test Execution Evidence
## 2. 8-Concern Code Review Summary
Overall Verdict: NEEDS CHANGES
## 3. Detailed Findings
### Design
- [BLOCKER] Critical architectural flaw.
### Functionality
- Good.
### Complexity
- Good.
### Tests
- Good.
### Naming
- Good.
### Comments
- Good.
### Style
- Good.
### Documentation
- Good.
## 4. Strengths & Positive Observations
"""
        diags, _ = self.validator.validate_text(content, "verification-report.md")
        error_rules = {d.rule_id for d in diags if d.severity == "ERROR"}
        self.assertIn("UNRESOLVED_BLOCKERS_PRESENT", error_rules)
        self.assertIn("INVALID_APPROVED_VERDICT", error_rules)

    def test_forbidden_ascii_art(self):
        content = """---
slug: auth
status: DRAFT
approved_by: pending
artifacts:
  - test.md
---

# Verification Report: Auth
+-------------------+
| ASCII Box Diagram |
+-------------------+
## 1. Automated Test Execution Evidence
## 2. 8-Concern Code Review Summary
## 3. Detailed Findings
### Design
### Functionality
### Complexity
### Tests
### Naming
### Comments
### Style
### Documentation
## 4. Strengths & Positive Observations
"""
        diags, _ = self.validator.validate_text(content, "verification-report.md")
        error_rules = {d.rule_id for d in diags if d.severity == "ERROR"}
        self.assertIn("FORBIDDEN_ASCII_ART", error_rules)

    def test_validate_verify_dir(self):
        # Missing report
        diags, _ = self.validator.validate_verify_dir(self.test_dir)
        error_rules = {d.rule_id for d in diags if d.severity == "ERROR"}
        self.assertIn("VERIFICATION_REPORT_NOT_FOUND", error_rules)

        # Valid report
        report_path = os.path.join(self.test_dir, "verification-report.md")
        with open(report_path, "w", encoding="utf-8") as f:
            f.write("""---
slug: dir-test
status: DRAFT
approved_by: pending
artifacts:
  - verification-report.md
---

# Verification Report: Directory Test
## 1. Automated Test Execution Evidence
## 2. 8-Concern Code Review Summary
## 3. Detailed Findings
### Design
### Functionality
### Complexity
### Tests
### Naming
### Comments
### Style
### Documentation
## 4. Strengths & Positive Observations
""")

        diags, summary = self.validator.validate_verify_dir(self.test_dir)
        errors = [d for d in diags if d.severity == "ERROR"]
        self.assertEqual(len(errors), 0, f"Expected 0 errors, got: {[e.to_dict() for e in errors]}")
        self.assertEqual(summary["slug"], "dir-test")

    def test_cli_execution(self):
        report_path = os.path.join(self.test_dir, "verification-report.md")
        with open(report_path, "w", encoding="utf-8") as f:
            f.write("""---
slug: cli-test
status: DRAFT
approved_by: pending
artifacts:
  - verification-report.md
---

# Verification Report: CLI Test
## 1. Automated Test Execution Evidence
## 2. 8-Concern Code Review Summary
## 3. Detailed Findings
### Design
### Functionality
### Complexity
### Tests
### Naming
### Comments
### Style
### Documentation
## 4. Strengths & Positive Observations
""")

        res = subprocess.run(
            [sys.executable, validator_path, self.test_dir, "--json"],
            capture_output=True,
            text=True
        )
        self.assertEqual(res.returncode, 0)
        self.assertIn('"valid": true', res.stdout)


if __name__ == "__main__":
    unittest.main()
