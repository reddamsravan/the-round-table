#!/usr/bin/env python3
"""
Test suite for Define Skill Specification Validator.
"""

import unittest
import os
import sys
import tempfile
import subprocess
import importlib.util

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
validator_path = os.path.join(REPO_ROOT, ".agents", "skills", "define", "scripts", "validator.py")

spec = importlib.util.spec_from_file_location("define_validator_mod", validator_path)
define_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(define_mod)

DefineValidator = define_mod.DefineValidator


class TestDefineValidator(unittest.TestCase):
    def setUp(self):
        self.validator = DefineValidator()

    def test_valid_specification(self):
        content = """---
slug: auth-token-refresh
status: DRAFT
approved_by: pending
artifacts:
  - docs/.prompts-and-prayers/auth-token-refresh/01-define/spec.md
---

# Specification: Auth Token Refresh

## 1. Objective & Value
Provide automated token refresh to prevent session disruption while maintaining security invariants.

## 2. Target Personas
- **Primary Persona**: Registered User accessing web dashboard.
- **Secondary Persona**: Security Auditor monitoring token issuance.

## 3. Scope Boundaries
### In-Scope
- Refresh token issuance and rotation.
### Out-of-Scope
- Multi-factor authentication setup.

## 4. Functional Requirements
### Requirement: REQ-001 - Token Rotation
**Narrative**:
As a registered user,
I want the client to refresh tokens automatically,
So that my active work session continues uninterrupted.

**Acceptance Criteria**:
- GIVEN a valid refresh token
  WHEN the client requests a token exchange
  THEN the server SHALL issue a fresh access token
- INVARIANT the server SHALL invalidate the prior refresh token.

## 5. Success Metrics & Validation
- Token refresh latency remains under 200 milliseconds.
- Session expiration errors drop to zero during continuous usage.
"""
        reqs, diagnostics, summary = self.validator.validate_text(content)
        errors = [d for d in diagnostics if d.severity == "ERROR"]
        self.assertEqual(len(errors), 0, f"Expected 0 errors, got: {[d.to_dict() for d in errors]}")
        self.assertEqual(len(reqs), 1)
        self.assertEqual(summary["slug"], "auth-token-refresh")
        self.assertEqual(summary["status"], "DRAFT")

    def test_extra_key_ignored(self):
        content = """---
slug: auth-token-refresh
persona: define
status: DRAFT
approved_by: pending
artifacts:
  - docs/.prompts-and-prayers/auth-token-refresh/01-define/spec.md
---

# Specification: Auth Token Refresh
## 1. Objective & Value
Valid objective.
## 2. Target Personas
Valid personas.
## 3. Scope Boundaries
Valid boundaries.
## 4. Functional Requirements
### Requirement: REQ-001 - Test
**Narrative**:
As a user,
I want action,
So that value.

**Acceptance Criteria**:
- GIVEN valid state
  WHEN triggered
  THEN the system SHALL proceed.

## 5. Success Metrics & Validation
Metric here.
"""
        _, diagnostics, _ = self.validator.validate_text(content)
        errors = [d for d in diagnostics if d.severity == "ERROR"]
        self.assertEqual(len(errors), 0)

    def test_missing_frontmatter_keys(self):
        content = """---
status: DRAFT
---
# Specification: Test
"""
        _, diagnostics, _ = self.validator.validate_text(content)
        rule_ids = [d.rule_id for d in diagnostics]
        self.assertIn("SCHEMA_MISSING_KEY", rule_ids)

    def test_missing_mandatory_sections(self):
        content = """---
slug: test-work
status: DRAFT
approved_by: pending
artifacts:
  - docs/.prompts-and-prayers/test-work/01-define/spec.md
---

# Specification: Test
## 1. Objective & Value
Valid.
## 2. Target Personas
Valid.
"""
        _, diagnostics, _ = self.validator.validate_text(content)
        rule_ids = [d.rule_id for d in diagnostics]
        self.assertIn("STRUCTURE_MISSING_SECTION", rule_ids)

    def test_invalid_section_order(self):
        content = """---
slug: test-work
status: DRAFT
approved_by: pending
artifacts:
  - docs/.prompts-and-prayers/test-work/01-define/spec.md
---

# Specification: Test
## 2. Target Personas
Valid.
## 1. Objective & Value
Valid.
## 3. Scope Boundaries
Valid.
## 4. Functional Requirements
### Requirement: REQ-001 - Test
**Narrative**:
As a user,
I want action,
So that value.

**Acceptance Criteria**:
- GIVEN valid state
  WHEN triggered
  THEN the system SHALL proceed.

## 5. Success Metrics & Validation
Metric here.
"""
        _, diagnostics, _ = self.validator.validate_text(content)
        rule_ids = [d.rule_id for d in diagnostics]
        self.assertIn("SECTION_ORDER_INVALID", rule_ids)

    def test_invalid_narrative_formula(self):
        content = """---
slug: test-work
status: DRAFT
approved_by: pending
artifacts:
  - docs/.prompts-and-prayers/test-work/01-define/spec.md
---

# Specification: Test
## 1. Objective & Value
Valid.
## 2. Target Personas
Valid.
## 3. Scope Boundaries
Valid.
## 4. Functional Requirements
### Requirement: REQ-001 - Test
**Narrative**:
I want action so that value.

**Acceptance Criteria**:
- GIVEN valid state
  WHEN triggered
  THEN the system SHALL proceed.

## 5. Success Metrics & Validation
Metric here.
"""
        _, diagnostics, _ = self.validator.validate_text(content)
        rule_ids = [d.rule_id for d in diagnostics]
        self.assertIn("INVALID_NARRATIVE_FORMULA", rule_ids)

    def test_forbidden_modal_in_criteria(self):
        content = """---
slug: test-work
status: DRAFT
approved_by: pending
artifacts:
  - docs/.prompts-and-prayers/test-work/01-define/spec.md
---

# Specification: Test
## 1. Objective & Value
Valid.
## 2. Target Personas
Valid.
## 3. Scope Boundaries
Valid.
## 4. Functional Requirements
### Requirement: REQ-001 - Test
**Narrative**:
As a user,
I want action,
So that value.

**Acceptance Criteria**:
- The system should return true.

## 5. Success Metrics & Validation
Metric here.
"""
        _, diagnostics, _ = self.validator.validate_text(content)
        rule_ids = [d.rule_id for d in diagnostics]
        self.assertIn("FORBIDDEN_MODAL_IN_CRITERIA", rule_ids)

    def test_passive_voice_in_criteria(self):
        content = """---
slug: test-work
status: DRAFT
approved_by: pending
artifacts:
  - docs/.prompts-and-prayers/test-work/01-define/spec.md
---

# Specification: Test
## 1. Objective & Value
Valid.
## 2. Target Personas
Valid.
## 3. Scope Boundaries
Valid.
## 4. Functional Requirements
### Requirement: REQ-001 - Test
**Narrative**:
As a user,
I want action,
So that value.

**Acceptance Criteria**:
- GIVEN a request
  WHEN received
  THEN the response is generated by the server.

## 5. Success Metrics & Validation
Metric here.
"""
        _, diagnostics, _ = self.validator.validate_text(content)
        rule_ids = [d.rule_id for d in diagnostics]
        self.assertIn("PASSIVE_VOICE_IN_CRITERIA", rule_ids)

    def test_cli_execution(self):
        doc = """---
slug: cli-test
status: DRAFT
approved_by: pending
artifacts:
  - docs/.prompts-and-prayers/cli-test/01-define/spec.md
---

# Specification: CLI Test

## 1. Objective & Value
Valid objective.

## 2. Target Personas
- **Primary Persona**: Admin

## 3. Scope Boundaries
### In-Scope
- CLI execution test.
### Out-of-Scope
- None.

## 4. Functional Requirements
### Requirement: REQ-001 - CLI Test Requirement
**Narrative**:
As an admin,
I want to execute tests from CLI,
So that automation passes.

**Acceptance Criteria**:
- GIVEN valid CLI input
  WHEN validator runs
  THEN the command SHALL exit with code zero.

## 5. Success Metrics & Validation
- Exit code equals zero.
"""
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as f:
            f.write(doc)
            f_path = f.name

        try:
            res = subprocess.run(
                [sys.executable, validator_path, f_path, "--json"],
                capture_output=True,
                text=True
            )
            self.assertEqual(res.returncode, 0)
            self.assertIn('"valid": true', res.stdout)
        finally:
            if os.path.exists(f_path):
                os.remove(f_path)


if __name__ == "__main__":
    unittest.main()
