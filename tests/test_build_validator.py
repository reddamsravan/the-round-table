#!/usr/bin/env python3
"""
Test suite for Build Skill Task and Summary Validator.
"""

import unittest
import os
import sys
import tempfile
import shutil
import subprocess
import importlib.util

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
validator_path = os.path.join(REPO_ROOT, ".agents", "skills", "build", "scripts", "validator.py")

spec = importlib.util.spec_from_file_location("build_validator_mod", validator_path)
build_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build_mod)

BuildValidator = build_mod.BuildValidator


class TestBuildValidator(unittest.TestCase):
    def setUp(self):
        self.validator = BuildValidator()
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    # -------------------------------------------------------------------------
    # Active Task Validation Tests
    # -------------------------------------------------------------------------

    def test_valid_active_task(self):
        content = """### Task: TASK-001 - Create Service Logic
```yaml
id: TASK-001
parent_plan_id: PLAN-001
title: Create Service Logic
status: IN_PROGRESS
effort_hours: 2.5
verify_cmd: python3 -m unittest tests/test_service.py
acceptance_criteria:
  - The service SHALL process records deterministically.
```
"""
        diags, summary = self.validator.validate_active_task(content, "active.md")
        errors = [d for d in diags if d.severity == "ERROR"]
        self.assertEqual(len(errors), 0, f"Expected 0 errors, got: {[e.to_dict() for e in errors]}")
        self.assertEqual(summary["active_task_id"], "TASK-001")
        self.assertEqual(summary["effort_hours"], 2.5)

    def test_effort_exceeded_and_multiple_tasks(self):
        content = """### Task: TASK-001 - First Task
```yaml
id: TASK-001
parent_plan_id: PLAN-001
title: First Task
status: IN_PROGRESS
effort_hours: 8.0
verify_cmd: python3 test.py
acceptance_criteria:
  - The module SHALL run.
```

### Task: TASK-002 - Second Task
```yaml
id: TASK-002
parent_plan_id: PLAN-001
title: Second Task
status: TODO
effort_hours: 2.0
verify_cmd: python3 test.py
acceptance_criteria:
  - The module SHALL run.
```
"""
        diags, summary = self.validator.validate_active_task(content, "active.md")
        error_rules = {d.rule_id for d in diags if d.severity == "ERROR"}
        self.assertIn("MULTIPLE_ACTIVE_TASKS", error_rules)
        self.assertIn("EFFORT_LIMIT_EXCEEDED", error_rules)

    def test_invalid_effort_format_and_missing_keys(self):
        content = """### Task: TASK-001 - Task With Missing Keys
```yaml
id: TASK-001
status: INVALID_STATUS
effort_hours: "not-a-number"
```
"""
        diags, _ = self.validator.validate_active_task(content, "active.md")
        error_rules = {d.rule_id for d in diags if d.severity == "ERROR"}
        self.assertIn("TASK_MISSING_KEY", error_rules)
        self.assertIn("INVALID_EFFORT_FORMAT", error_rules)
        self.assertIn("INVALID_TASK_STATUS", error_rules)

    def test_task_ace_criteria_violations(self):
        content = """### Task: TASK-001 - ACE Violations
```yaml
id: TASK-001
parent_plan_id: PLAN-001
title: ACE Violations
status: IN_PROGRESS
effort_hours: 2.0
verify_cmd: python3 test.py
acceptance_criteria:
  - The component should be fast.
  - The record is saved by the database.
```
"""
        diags, _ = self.validator.validate_active_task(content, "active.md")
        error_rules = {d.rule_id for d in diags if d.severity == "ERROR"}
        self.assertIn("FORBIDDEN_MODAL", error_rules)
        self.assertIn("AMBIGUOUS_WORD", error_rules)
        self.assertIn("PASSIVE_VOICE", error_rules)

    # -------------------------------------------------------------------------
    # Build Summary Validation Tests
    # -------------------------------------------------------------------------

    def test_valid_build_summary(self):
        content = """---
slug: auth-service
status: DRAFT
approved_by: pending
artifacts:
  - docs/.prompts-and-prayers/auth-service/04-build/build-summary.md
---

# Build Summary: Authentication Service

## 1. Execution Overview
Completed token issuance and verification implementation.

## 2. Completed Atomic Tasks
| Task ID | Parent Plan ID | Title | Test Suite | Archive Path |
|---|---|---|---|---|
| TASK-001 | PLAN-001 | Implement Token Logic | tests/test_auth.py | 04-build/archive/TASK-001.md |

## 3. Test Verification Evidence
```text
Ran 5 tests in 0.02s
OK
```

## 4. Modified Components
- `auth/service.py`: Token logic
- `tests/test_auth.py`: Auth unit tests
"""
        diags, summary = self.validator.validate_build_summary(content, "build-summary.md")
        errors = [d for d in diags if d.severity == "ERROR"]
        self.assertEqual(len(errors), 0, f"Expected 0 errors, got: {[e.to_dict() for e in errors]}")
        self.assertEqual(summary["slug"], "auth-service")
        self.assertEqual(summary["status"], "DRAFT")
        self.assertEqual(summary["approved_by"], "pending")
        self.assertEqual(summary["artifacts_count"], 1)

    def test_extra_key_in_frontmatter_ignored(self):
        content = """---
slug: auth-service
persona: developer
status: APPROVED
approved_by: human
artifacts:
  - docs/.prompts-and-prayers/auth-service/04-build/build-summary.md
---

# Build Summary: Authentication Service

## 1. Execution Overview
Overview.

## 2. Completed Atomic Tasks
Tasks.

## 3. Test Verification Evidence
```text
OK
```

## 4. Modified Components
- `auth.py`: Done
"""
        diags, _ = self.validator.validate_build_summary(content, "build-summary.md")
        errors = [d for d in diags if d.severity == "ERROR"]
        self.assertEqual(len(errors), 0)

    def test_frontmatter_missing_and_unclosed(self):
        content_no_frontmatter = """# Build Summary: Auth
## 1. Execution Overview
## 2. Completed Atomic Tasks
## 3. Test Verification Evidence
## 4. Modified Components
"""
        diags, _ = self.validator.validate_build_summary(content_no_frontmatter, "build-summary.md")
        error_rules = {d.rule_id for d in diags if d.severity == "ERROR"}
        self.assertIn("FRONTMATTER_MISSING", error_rules)

        content_unclosed = """---
slug: auth
# Build Summary: Auth
## 1. Execution Overview
## 2. Completed Atomic Tasks
## 3. Test Verification Evidence
## 4. Modified Components
"""
        diags, _ = self.validator.validate_build_summary(content_unclosed, "build-summary.md")
        error_rules = {d.rule_id for d in diags if d.severity == "ERROR"}
        self.assertIn("FRONTMATTER_UNCLOSED", error_rules)

    def test_frontmatter_schema_errors(self):
        content = """---
slug: auth
status: BAD_STATUS
approved_by: robot
artifacts: []
---

# Build Summary: Auth
## 1. Execution Overview
## 2. Completed Atomic Tasks
## 3. Test Verification Evidence
## 4. Modified Components
"""
        diags, _ = self.validator.validate_build_summary(content, "build-summary.md")
        error_rules = {d.rule_id for d in diags if d.severity == "ERROR"}
        self.assertIn("SCHEMA_INVALID_STATUS", error_rules)
        self.assertIn("SCHEMA_INVALID_APPROVED_BY", error_rules)
        self.assertIn("SCHEMA_INVALID_ARTIFACTS", error_rules)

    def test_strict_heading_and_missing_sections(self):
        # Legacy title '# Sprint Implementation Summary:' should fail strict heading requirement
        content = """---
slug: auth
status: DRAFT
approved_by: pending
artifacts:
  - test.md
---

# Sprint Implementation Summary: Auth
## 1. Execution Overview
## 2. Completed Atomic Tasks
"""
        diags, _ = self.validator.validate_build_summary(content, "build-summary.md")
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

# Build Summary: Auth
## 2. Completed Atomic Tasks
## 1. Execution Overview
## 3. Test Verification Evidence
## 4. Modified Components
"""
        diags, _ = self.validator.validate_build_summary(content, "build-summary.md")
        error_rules = {d.rule_id for d in diags if d.severity == "ERROR"}
        self.assertIn("SECTION_ORDER_INVALID", error_rules)

    def test_forbidden_ascii_art(self):
        content = """---
slug: auth
status: DRAFT
approved_by: pending
artifacts:
  - test.md
---

# Build Summary: Auth
+-------------------+
| ASCII Box Diagram |
+-------------------+
## 1. Execution Overview
## 2. Completed Atomic Tasks
## 3. Test Verification Evidence
## 4. Modified Components
"""
        diags, _ = self.validator.validate_build_summary(content, "build-summary.md")
        error_rules = {d.rule_id for d in diags if d.severity == "ERROR"}
        self.assertIn("FORBIDDEN_ASCII_ART", error_rules)

    # -------------------------------------------------------------------------
    # Directory & CLI Execution Tests
    # -------------------------------------------------------------------------

    def test_validate_build_dir(self):
        # Missing summary file
        diags, _ = self.validator.validate_build_dir(self.test_dir)
        error_rules = {d.rule_id for d in diags if d.severity == "ERROR"}
        self.assertIn("BUILD_SUMMARY_NOT_FOUND", error_rules)

        # Valid build directory
        summary_path = os.path.join(self.test_dir, "build-summary.md")
        with open(summary_path, "w", encoding="utf-8") as f:
            f.write("""---
slug: dir-test
status: DRAFT
approved_by: pending
artifacts:
  - build-summary.md
---

# Build Summary: Directory Test
## 1. Execution Overview
## 2. Completed Atomic Tasks
## 3. Test Verification Evidence
## 4. Modified Components
""")

        diags, summary = self.validator.validate_build_dir(self.test_dir)
        errors = [d for d in diags if d.severity == "ERROR"]
        self.assertEqual(len(errors), 0, f"Expected 0 errors, got: {[e.to_dict() for e in errors]}")
        self.assertEqual(summary["slug"], "dir-test")

    def test_cli_execution(self):
        summary_path = os.path.join(self.test_dir, "build-summary.md")
        with open(summary_path, "w", encoding="utf-8") as f:
            f.write("""---
slug: cli-test
status: DRAFT
approved_by: pending
artifacts:
  - build-summary.md
---

# Build Summary: CLI Test
## 1. Execution Overview
## 2. Completed Atomic Tasks
## 3. Test Verification Evidence
## 4. Modified Components
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
