#!/usr/bin/env python3
"""
Test suite for Plot Skill Specification and Plan Validator.
"""

import unittest
import os
import sys
import tempfile
import shutil
import subprocess
import importlib.util

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
validator_path = os.path.join(REPO_ROOT, ".agents", "skills", "plot", "scripts", "validator.py")

spec = importlib.util.spec_from_file_location("plot_validator_mod", validator_path)
plot_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(plot_mod)

PlotValidator = plot_mod.PlotValidator


class TestPlotValidator(unittest.TestCase):
    def setUp(self):
        self.validator = PlotValidator()
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def _write_files(self, spec_content: str, plan_content: str):
        with open(os.path.join(self.test_dir, "tech-spec.md"), "w", encoding="utf-8") as f:
            f.write(spec_content)
        with open(os.path.join(self.test_dir, "plan.md"), "w", encoding="utf-8") as f:
            f.write(plan_content)

    def test_valid_plot_directory(self):
        spec_content = """---
slug: auth-flow
status: DRAFT
approved_by: pending
artifacts:
  - docs/.prompts-and-prayers/auth-flow/03-plot/tech-spec.md
  - docs/.prompts-and-prayers/auth-flow/03-plot/plan.md
---

# Technical Specification: Auth Architecture

## 1. System Overview & Architecture Topology

### System Context
The service coordinates token issuance and validation.

### Architecture Diagram
```mermaid
flowchart TD
    Client --> API
```

## 2. Architectural Decision Records (ADRs)
### ADR-001: JWT Tokens
- Status: Accepted

## 3. Component Contracts & Interfaces
- AuthController

## 4. Technical Constraints & Invariants
- The system SHALL validate all token signatures.
- The service SHALL reject expired credentials.
"""

        plan_content = """# Implementation Plan: Auth Flow

## Plan Overview
Milestones for auth service implementation.

## Engineering Tasks

### Task: PLAN-001 - Implement Token Service
```yaml
id: PLAN-001
title: Implement Token Service
status: TODO
depends_on: []
acceptance_criteria:
  - The service SHALL generate cryptographically signed tokens.
verify_cmd: python3 -m unittest tests/test_token.py
```

### Task: PLAN-002 - Implement Auth Endpoints
```yaml
id: PLAN-002
title: Implement Auth Endpoints
status: TODO
depends_on:
  - PLAN-001
acceptance_criteria:
  - The endpoint SHALL return status 200 on valid credentials.
verify_cmd: python3 -m unittest tests/test_endpoints.py
```
"""
        self._write_files(spec_content, plan_content)
        diags, summary = self.validator.validate_plot_dir(self.test_dir)
        errors = [d for d in diags if d.severity == "ERROR"]
        self.assertEqual(len(errors), 0, f"Expected 0 errors, got: {[e.to_dict() for e in errors]}")
        self.assertEqual(summary["slug"], "auth-flow")
        self.assertEqual(summary["status"], "DRAFT")
        self.assertEqual(summary["total_plan_tasks"], 2)

    def test_extra_key_in_frontmatter_ignored(self):
        spec_content = """---
slug: auth-flow
persona: architect
status: DRAFT
approved_by: pending
artifacts:
  - test.md
---

# Technical Specification: Auth

## 1. System Overview & Architecture Topology
```mermaid
flowchart TD
    A --> B
```

## 2. Architectural Decision Records (ADRs)
ADRs.

## 3. Component Contracts & Interfaces
Contracts.

## 4. Technical Constraints & Invariants
- The system SHALL execute operations.
"""
        plan_content = """# Implementation Plan: Auth
## Plan Overview
Overview.
## Engineering Tasks
### Task: PLAN-001 - Task 1
```yaml
id: PLAN-001
title: Task 1
status: TODO
depends_on: []
acceptance_criteria:
  - The module SHALL run.
```
"""
        self._write_files(spec_content, plan_content)
        diags, _ = self.validator.validate_plot_dir(self.test_dir)
        errors = [d for d in diags if d.severity == "ERROR"]
        self.assertEqual(len(errors), 0)

    def test_missing_tech_spec(self):
        plan_content = """# Implementation Plan: Auth
## Plan Overview
Overview.
## Engineering Tasks
### Task: PLAN-001 - Task 1
```yaml
id: PLAN-001
title: Task 1
status: TODO
depends_on: []
acceptance_criteria:
  - The module SHALL run.
```
"""
        with open(os.path.join(self.test_dir, "plan.md"), "w") as f:
            f.write(plan_content)

        diags, _ = self.validator.validate_plot_dir(self.test_dir)
        rule_ids = [d.rule_id for d in diags if d.severity == "ERROR"]
        self.assertIn("TECH_SPEC_NOT_FOUND", rule_ids)

    def test_missing_plan(self):
        spec_content = """---
slug: auth-flow
status: DRAFT
approved_by: pending
artifacts:
  - test.md
---
# Technical Specification: Auth
## 1. System Overview & Architecture Topology
```mermaid
flowchart TD
    A --> B
```
## 2. Architectural Decision Records (ADRs)
## 3. Component Contracts & Interfaces
## 4. Technical Constraints & Invariants
- The system SHALL run.
"""
        with open(os.path.join(self.test_dir, "tech-spec.md"), "w") as f:
            f.write(spec_content)

        diags, _ = self.validator.validate_plot_dir(self.test_dir)
        rule_ids = [d.rule_id for d in diags if d.severity == "ERROR"]
        self.assertIn("PLAN_NOT_FOUND", rule_ids)

    def test_missing_frontmatter_keys(self):
        spec_content = """---
status: DRAFT
---
# Technical Specification: Auth
## 1. System Overview & Architecture Topology
```mermaid
flowchart TD
    A --> B
```
## 2. Architectural Decision Records (ADRs)
## 3. Component Contracts & Interfaces
## 4. Technical Constraints & Invariants
- The system SHALL run.
"""
        plan_content = """# Implementation Plan: Auth
## Plan Overview
## Engineering Tasks
### Task: PLAN-001 - Task 1
```yaml
id: PLAN-001
title: Task 1
status: TODO
depends_on: []
acceptance_criteria:
  - The module SHALL run.
```
"""
        self._write_files(spec_content, plan_content)
        diags, _ = self.validator.validate_plot_dir(self.test_dir)
        rule_ids = [d.rule_id for d in diags if d.severity == "ERROR"]
        self.assertIn("SCHEMA_MISSING_KEY", rule_ids)

    def test_invalid_status_and_approved_by(self):
        spec_content = """---
slug: auth
status: INVALID_STATUS
approved_by: robot
artifacts: []
---
# Technical Specification: Auth
## 1. System Overview & Architecture Topology
```mermaid
flowchart TD
    A --> B
```
## 2. Architectural Decision Records (ADRs)
## 3. Component Contracts & Interfaces
## 4. Technical Constraints & Invariants
- The system SHALL run.
"""
        plan_content = """# Implementation Plan: Auth
## Plan Overview
## Engineering Tasks
### Task: PLAN-001 - Task 1
```yaml
id: PLAN-001
title: Task 1
status: TODO
depends_on: []
acceptance_criteria:
  - The module SHALL run.
```
"""
        self._write_files(spec_content, plan_content)
        diags, _ = self.validator.validate_plot_dir(self.test_dir)
        rule_ids = [d.rule_id for d in diags if d.severity == "ERROR"]
        self.assertIn("SCHEMA_INVALID_STATUS", rule_ids)
        self.assertIn("SCHEMA_INVALID_APPROVED_BY", rule_ids)
        self.assertIn("SCHEMA_INVALID_ARTIFACTS", rule_ids)

    def test_missing_tech_spec_sections_and_diagram(self):
        spec_content = """---
slug: auth
status: DRAFT
approved_by: pending
artifacts:
  - test.md
---
# Technical Specification: Incomplete
## 1. System Overview & Architecture Topology
No diagram here.
"""
        plan_content = """# Implementation Plan: Auth
## Plan Overview
## Engineering Tasks
### Task: PLAN-001 - Task 1
```yaml
id: PLAN-001
title: Task 1
status: TODO
depends_on: []
acceptance_criteria:
  - The module SHALL run.
```
"""
        self._write_files(spec_content, plan_content)
        diags, _ = self.validator.validate_plot_dir(self.test_dir)
        rule_ids = [d.rule_id for d in diags if d.severity == "ERROR"]
        self.assertIn("STRUCTURE_MISSING_SECTION", rule_ids)
        self.assertIn("FLOWCHART_MISSING", rule_ids)

    def test_forbidden_ascii_art(self):
        spec_content = """---
slug: auth
status: DRAFT
approved_by: pending
artifacts:
  - test.md
---
# Technical Specification: ASCII Box
## 1. System Overview & Architecture Topology
+-------------------+
| ASCII Box Diagram |
+-------------------+
```mermaid
flowchart TD
    A --> B
```
## 2. Architectural Decision Records (ADRs)
## 3. Component Contracts & Interfaces
## 4. Technical Constraints & Invariants
- The system SHALL run.
"""
        plan_content = """# Implementation Plan: Auth
## Plan Overview
## Engineering Tasks
### Task: PLAN-001 - Task 1
```yaml
id: PLAN-001
title: Task 1
status: TODO
depends_on: []
acceptance_criteria:
  - The module SHALL run.
```
"""
        self._write_files(spec_content, plan_content)
        diags, _ = self.validator.validate_plot_dir(self.test_dir)
        rule_ids = [d.rule_id for d in diags if d.severity == "ERROR"]
        self.assertIn("FORBIDDEN_ASCII_ART", rule_ids)

    def test_ace_constraint_violations(self):
        spec_content = """---
slug: auth
status: DRAFT
approved_by: pending
artifacts:
  - test.md
---
# Technical Specification: ACE Errors
## 1. System Overview & Architecture Topology
```mermaid
flowchart TD
    A --> B
```
## 2. Architectural Decision Records (ADRs)
## 3. Component Contracts & Interfaces
## 4. Technical Constraints & Invariants
- The service should validate input.
- The interface SHALL be user-friendly.
- The payload is processed by the server.
"""
        plan_content = """# Implementation Plan: Auth
## Plan Overview
## Engineering Tasks
### Task: PLAN-001 - Task 1
```yaml
id: PLAN-001
title: Task 1
status: TODO
depends_on: []
acceptance_criteria:
  - The module SHALL run.
```
"""
        self._write_files(spec_content, plan_content)
        diags, _ = self.validator.validate_plot_dir(self.test_dir)
        rule_ids = [d.rule_id for d in diags if d.severity == "ERROR"]
        self.assertIn("FORBIDDEN_MODAL", rule_ids)
        self.assertIn("AMBIGUOUS_WORD", rule_ids)
        self.assertIn("PASSIVE_VOICE", rule_ids)

    def test_plan_missing_sections_and_no_tasks(self):
        spec_content = """---
slug: auth
status: DRAFT
approved_by: pending
artifacts:
  - test.md
---
# Technical Specification: Auth
## 1. System Overview & Architecture Topology
```mermaid
flowchart TD
    A --> B
```
## 2. Architectural Decision Records (ADRs)
## 3. Component Contracts & Interfaces
## 4. Technical Constraints & Invariants
- The system SHALL run.
"""
        plan_content = """# Implementation Plan: Empty
No sections here.
"""
        self._write_files(spec_content, plan_content)
        diags, _ = self.validator.validate_plot_dir(self.test_dir)
        rule_ids = [d.rule_id for d in diags if d.severity == "ERROR"]
        self.assertIn("PLAN_STRUCTURE_MISSING", rule_ids)
        self.assertIn("PLAN_NO_TASKS", rule_ids)

    def test_plan_task_schema_errors(self):
        spec_content = """---
slug: auth
status: DRAFT
approved_by: pending
artifacts:
  - test.md
---
# Technical Specification: Auth
## 1. System Overview & Architecture Topology
```mermaid
flowchart TD
    A --> B
```
## 2. Architectural Decision Records (ADRs)
## 3. Component Contracts & Interfaces
## 4. Technical Constraints & Invariants
- The system SHALL run.
"""
        plan_content = """# Implementation Plan: Auth
## Plan Overview
## Engineering Tasks
### Task: PLAN-001 - Bad Status Task
```yaml
id: PLAN-001
title: Bad Task
status: INVALID_STATUS
depends_on: []
acceptance_criteria: []
```
"""
        self._write_files(spec_content, plan_content)
        diags, _ = self.validator.validate_plot_dir(self.test_dir)
        rule_ids = [d.rule_id for d in diags if d.severity == "ERROR"]
        self.assertIn("TASK_INVALID_STATUS", rule_ids)
        self.assertIn("TASK_MISSING_CRITERIA", rule_ids)

    def test_plan_dag_dependencies_and_cycles(self):
        spec_content = """---
slug: auth
status: DRAFT
approved_by: pending
artifacts:
  - test.md
---
# Technical Specification: Auth
## 1. System Overview & Architecture Topology
```mermaid
flowchart TD
    A --> B
```
## 2. Architectural Decision Records (ADRs)
## 3. Component Contracts & Interfaces
## 4. Technical Constraints & Invariants
- The system SHALL run.
"""
        # Cyclic dependency PLAN-001 -> PLAN-002 -> PLAN-001
        plan_content = """# Implementation Plan: Auth
## Plan Overview
## Engineering Tasks
### Task: PLAN-001 - Task 1
```yaml
id: PLAN-001
title: Task 1
status: TODO
depends_on:
  - PLAN-002
acceptance_criteria:
  - The module SHALL run.
```

### Task: PLAN-002 - Task 2
```yaml
id: PLAN-002
title: Task 2
status: TODO
depends_on:
  - PLAN-001
acceptance_criteria:
  - The module SHALL run.
```
"""
        self._write_files(spec_content, plan_content)
        diags, _ = self.validator.validate_plot_dir(self.test_dir)
        rule_ids = [d.rule_id for d in diags if d.severity == "ERROR"]
        self.assertIn("DAG_CYCLE_DETECTED", rule_ids)

    def test_task_self_and_unknown_dependency(self):
        spec_content = """---
slug: auth
status: DRAFT
approved_by: pending
artifacts:
  - test.md
---
# Technical Specification: Auth
## 1. System Overview & Architecture Topology
```mermaid
flowchart TD
    A --> B
```
## 2. Architectural Decision Records (ADRs)
## 3. Component Contracts & Interfaces
## 4. Technical Constraints & Invariants
- The system SHALL run.
"""
        plan_content = """# Implementation Plan: Auth
## Plan Overview
## Engineering Tasks
### Task: PLAN-001 - Task 1
```yaml
id: PLAN-001
title: Task 1
status: TODO
depends_on:
  - PLAN-001
  - PLAN-999
acceptance_criteria:
  - The module SHALL run.
```
"""
        self._write_files(spec_content, plan_content)
        diags, _ = self.validator.validate_plot_dir(self.test_dir)
        rule_ids = [d.rule_id for d in diags if d.severity == "ERROR"]
        self.assertIn("DAG_SELF_DEPENDENCY", rule_ids)
        self.assertIn("DAG_UNKNOWN_DEPENDENCY", rule_ids)

    def test_cli_execution(self):
        spec_content = """---
slug: cli-test
status: DRAFT
approved_by: pending
artifacts:
  - test.md
---
# Technical Specification: Auth
## 1. System Overview & Architecture Topology
```mermaid
flowchart TD
    A --> B
```
## 2. Architectural Decision Records (ADRs)
## 3. Component Contracts & Interfaces
## 4. Technical Constraints & Invariants
- The system SHALL run.
"""
        plan_content = """# Implementation Plan: Auth
## Plan Overview
## Engineering Tasks
### Task: PLAN-001 - Task 1
```yaml
id: PLAN-001
title: Task 1
status: TODO
depends_on: []
acceptance_criteria:
  - The module SHALL run.
```
"""
        self._write_files(spec_content, plan_content)
        res = subprocess.run(
            [sys.executable, validator_path, self.test_dir, "--json"],
            capture_output=True,
            text=True
        )
        self.assertEqual(res.returncode, 0)
        self.assertIn('"valid": true', res.stdout)


if __name__ == "__main__":
    unittest.main()
