#!/usr/bin/env python3
"""
Test suite for Persona Validators (po, ux-designer, architect, developer, qa, scrum-master).
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


po_mod = load_module("po_validator", ".agents/skills/po/scripts/validator.py")
ux_mod = load_module("ux_validator", ".agents/skills/ux-designer/scripts/validator.py")
arch_mod = load_module("arch_validator", ".agents/skills/architect/scripts/validator.py")
dev_mod = load_module("dev_validator", ".agents/skills/developer/scripts/validator.py")
qa_mod = load_module("qa_validator", ".agents/skills/qa/scripts/validator.py")
sm_mod = load_module("sm_validator", ".agents/skills/scrum-master/scripts/validator.py")


class TestPOValidator(unittest.TestCase):
    def setUp(self):
        self.validator = po_mod.POValidator()

    def test_valid_po_story_spec(self):
        content = """---
sprint: sprint-1
persona: po
status: DRAFT
approved_by: pending
handoff_to: ux-designer
artifacts:
  - docs/.prompts-and-prayers/sprints/sprint-1/01-stories/spec.md
---

# Sprint Specification: Core Auth

## 1. Sprint Goal
Deliver user authentication.

## 2. Target Personas
- **Primary Persona**: End User

## 3. Scope Boundaries
### In-Scope
- Email login
### Out-of-Scope
- Social login

## 4. User Stories

### Story: US-001 - User Login

**Narrative**:
As an end user,
I want to log in with email and password,
So that I access my account securely.

**Acceptance Criteria**:
- The system SHALL validate user credentials.
- The system MUST return an auth token upon successful login.
"""
        stories, diags, summary = self.validator.validate_text(content)
        errors = [d for d in diags if d.severity == "ERROR"]
        self.assertEqual(len(errors), 0, f"Expected 0 errors, got: {[e.to_dict() for e in errors]}")
        self.assertEqual(len(stories), 1)
        self.assertEqual(summary["sprint"], "sprint-1")

    def test_invalid_po_frontmatter_and_ace(self):
        content = """---
sprint: sprint-1
persona: developer
status: UNKNOWN
handoff_to: qa
artifacts: []
---

# Sprint Specification: Incomplete Spec

## 4. User Stories

### Story: US-001 - Broken Story
The user can login.
"""
        stories, diags, summary = self.validator.validate_text(content)
        error_rules = {d.rule_id for d in diags if d.severity == "ERROR"}
        self.assertIn("SCHEMA_INVALID_PERSONA", error_rules)
        self.assertIn("SCHEMA_INVALID_STATUS", error_rules)
        self.assertIn("SCHEMA_INVALID_HANDOFF", error_rules)
        self.assertIn("INVEST_FORMULA_VIOLATION", error_rules)


class TestUXValidator(unittest.TestCase):
    def setUp(self):
        self.validator = ux_mod.UXValidator()

    def test_valid_ux_spec(self):
        content = """---
sprint: sprint-1
persona: ux-designer
status: DRAFT
approved_by: pending
handoff_to: architect
artifacts:
  - docs/.prompts-and-prayers/sprints/sprint-1/02-design/design-spec.md
---

# UX Design Specification: Auth Flow

## 1. User Journey & Interaction Flow
Ref: US-001
```mermaid
flowchart TD
    A["Enter Email"] --> B["Submit"]
```

## 2. Screen State Transitions
```mermaid
stateDiagram-v2
    [*] --> Idle
    Idle --> Done
```

## 3. UI Layout & Component Specifications
The view contains an email input field and a submit button.

## 4. Accessibility & Responsive Requirements
- The interface SHALL support full keyboard navigation.
- The interface SHALL provide accessible label attributes.
"""
        diags, summary = self.validator.validate_text(content)
        errors = [d for d in diags if d.severity == "ERROR"]
        self.assertEqual(len(errors), 0, f"Expected 0 errors, got: {[e.to_dict() for e in errors]}")
        self.assertEqual(summary["mermaid_blocks_count"], 2)

    def test_missing_mermaid_and_forbidden_ascii(self):
        content = """---
sprint: sprint-1
persona: ux-designer
status: DRAFT
approved_by: pending
handoff_to: architect
artifacts:
  - test.md
---

# UX Design Specification: Bad Spec

## 1. User Journey & Interaction Flow
+-------------------+
| ASCII Box Diagram |
+-------------------+

## 2. Screen State Transitions
No diagrams.

## 3. UI Layout & Component Specifications
Text.

## 4. Accessibility & Responsive Requirements
Text.
"""
        diags, summary = self.validator.validate_text(content)
        error_rules = {d.rule_id for d in diags if d.severity == "ERROR"}
        self.assertIn("MERMAID_MISSING", error_rules)
        self.assertIn("FORBIDDEN_ASCII_ART", error_rules)


class TestArchitectValidator(unittest.TestCase):
    def setUp(self):
        self.validator = arch_mod.ArchitectValidator()
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_valid_architect_sprint(self):
        os.makedirs(os.path.join(self.test_dir, "01-stories"))
        os.makedirs(os.path.join(self.test_dir, "03-architecture"))
        os.makedirs(os.path.join(self.test_dir, "04-tasks"))

        with open(os.path.join(self.test_dir, "01-stories", "spec.md"), "w") as f:
            f.write("### Story: US-001 - Login Feature\n")

        with open(os.path.join(self.test_dir, "03-architecture", "tech-spec.md"), "w") as f:
            f.write("""---
sprint: sprint-1
persona: architect
status: DRAFT
approved_by: pending
handoff_to: developer
artifacts:
  - 03-architecture/tech-spec.md
  - 04-tasks/plan.md
---

# Technical Architecture Specification: Auth Service

## 1. System Overview & Architecture Topology
```mermaid
flowchart TD
    Client --> API
```

## 2. Architectural Decision Records (ADRs)
### ADR-001: JWT Auth

## 3. Component Contracts & Interfaces
- AuthController

## 4. Technical Constraints & Invariants
- The system SHALL validate all token signatures.
""")

        with open(os.path.join(self.test_dir, "04-tasks", "plan.md"), "w") as f:
            f.write("""# Sprint Implementation Plan: Auth Service

## Plan Overview
Architecture tasks.

## Traceability Matrix
| PLAN-001 | US-001 | Auth |

## Engineering Tasks

### Task: PLAN-001 - Implement Controller
```yaml
id: PLAN-001
title: Implement Controller
status: TODO
depends_on: []
user_stories:
  - US-001
acceptance_criteria:
  - The module SHALL return valid responses.
```
""")

        diags, summary = self.validator.validate_sprint(self.test_dir)
        errors = [d for d in diags if d.severity == "ERROR"]
        self.assertEqual(len(errors), 0, f"Expected 0 errors, got: {[e.to_dict() for e in errors]}")
        self.assertEqual(summary["total_plan_tasks"], 1)


class TestDeveloperValidator(unittest.TestCase):
    def setUp(self):
        self.validator = dev_mod.DeveloperValidator()

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
