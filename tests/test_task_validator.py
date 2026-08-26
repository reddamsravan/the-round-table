#!/usr/bin/env python3
"""
Test suite for Task Validator (task skill).
"""

import unittest
import os
import importlib.util

validator_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", ".agents", "skills", "task", "scripts", "validator.py")
)
spec = importlib.util.spec_from_file_location("task_validator_module", validator_path)
task_validator_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(task_validator_mod)

TaskValidator = task_validator_mod.TaskValidator
TaskItem = task_validator_mod.TaskItem


class TestTaskValidator(unittest.TestCase):
    def setUp(self):
        self.validator = TaskValidator()

    def test_valid_task_document(self):
        content = """# Active Tasks

### Task: TASK-001 - First Task

```yaml
id: TASK-001
title: First Task
status: DONE
assignee: self
depends_on: []
verify_cmd: "pytest tests/test_first.py"
acceptance_criteria:
  - The module SHALL process input records.
  - The module SHALL return structured JSON output.
```

### Task: TASK-002 - Second Task

```yaml
id: TASK-002
title: Second Task
status: TODO
assignee: self
depends_on:
  - TASK-001
acceptance_criteria:
  - The CLI SHALL display task status summary.
```
"""
        tasks, diagnostics, summary = self.validator.validate_text(content)
        errors = [d for d in diagnostics if d.severity == "ERROR"]
        self.assertEqual(len(errors), 0, f"Expected 0 errors, got: {[d.to_dict() for d in errors]}")
        self.assertEqual(len(tasks), 2)
        self.assertEqual(summary["total_tasks"], 2)
        self.assertEqual(summary["ready_tasks"], ["TASK-002"])

    def test_missing_tasks_error(self):
        content = "# Active Tasks\n\nNo task headings here."
        tasks, diagnostics, summary = self.validator.validate_text(content)
        rule_ids = [d.rule_id for d in diagnostics]
        self.assertIn("NO_TASKS_FOUND", rule_ids)

    def test_unclosed_yaml_block(self):
        content = """### Task: TASK-001 - Broken Block

```yaml
id: TASK-001
title: Broken Block
status: TODO
assignee: self
depends_on: []
acceptance_criteria:
  - The agent SHALL close yaml fences.
"""
        tasks, diagnostics, _ = self.validator.validate_text(content)
        rule_ids = [d.rule_id for d in diagnostics]
        self.assertIn("UNCLOSED_YAML_BLOCK", rule_ids)

    def test_missing_mandatory_fields(self):
        content = """### Task: TASK-001 - Incomplete Task

```yaml
id: TASK-001
title: Incomplete Task
depends_on: []
```
"""
        tasks, diagnostics, _ = self.validator.validate_text(content)
        rule_ids = [d.rule_id for d in diagnostics]
        self.assertIn("MISSING_STATUS", rule_ids)
        self.assertIn("MISSING_ASSIGNEE", rule_ids)
        self.assertIn("MISSING_ACCEPTANCE_CRITERIA", rule_ids)

    def test_invalid_status_enum(self):
        content = """### Task: TASK-001 - Invalid Status

```yaml
id: TASK-001
title: Invalid Status
status: COMPLETED
assignee: self
depends_on: []
acceptance_criteria:
  - The status SHALL be valid.
```
"""
        tasks, diagnostics, _ = self.validator.validate_text(content)
        rule_ids = [d.rule_id for d in diagnostics]
        self.assertIn("INVALID_STATUS", rule_ids)

    def test_duplicate_task_id(self):
        content = """### Task: TASK-001 - First Task

```yaml
id: TASK-001
title: First Task
status: DONE
assignee: self
depends_on: []
acceptance_criteria:
  - The first task SHALL execute.
```

### Task: TASK-001 - Duplicate Task

```yaml
id: TASK-001
title: Duplicate Task
status: TODO
assignee: self
depends_on: []
acceptance_criteria:
  - The second task SHALL execute.
```
"""
        tasks, diagnostics, _ = self.validator.validate_text(content)
        rule_ids = [d.rule_id for d in diagnostics]
        self.assertIn("DUPLICATE_TASK_ID", rule_ids)

    def test_self_dependency(self):
        content = """### Task: TASK-001 - Self Dependent Task

```yaml
id: TASK-001
title: Self Dependent Task
status: TODO
assignee: self
depends_on:
  - TASK-001
acceptance_criteria:
  - The task SHALL not depend on itself.
```
"""
        tasks, diagnostics, _ = self.validator.validate_text(content)
        rule_ids = [d.rule_id for d in diagnostics]
        self.assertIn("SELF_DEPENDENCY", rule_ids)

    def test_unknown_dependency(self):
        content = """### Task: TASK-001 - Dangling Dependency Task

```yaml
id: TASK-001
title: Dangling Dependency Task
status: TODO
assignee: self
depends_on:
  - TASK-999
acceptance_criteria:
  - The task SHALL depend on existing IDs.
```
"""
        tasks, diagnostics, _ = self.validator.validate_text(content)
        rule_ids = [d.rule_id for d in diagnostics]
        self.assertIn("UNKNOWN_DEPENDENCY", rule_ids)

    def test_circular_dependency(self):
        content = """### Task: TASK-001 - Cycle Node 1

```yaml
id: TASK-001
title: Cycle Node 1
status: TODO
assignee: self
depends_on:
  - TASK-002
acceptance_criteria:
  - Node 1 SHALL execute.
```

### Task: TASK-002 - Cycle Node 2

```yaml
id: TASK-002
title: Cycle Node 2
status: TODO
assignee: self
depends_on:
  - TASK-001
acceptance_criteria:
  - Node 2 SHALL execute.
```
"""
        tasks, diagnostics, _ = self.validator.validate_text(content)
        rule_ids = [d.rule_id for d in diagnostics]
        self.assertIn("CIRCULAR_DEPENDENCY", rule_ids)

    def test_unmet_prerequisite_dependency(self):
        content = """### Task: TASK-001 - Prerequisite Task

```yaml
id: TASK-001
title: Prerequisite Task
status: IN_PROGRESS
assignee: self
depends_on: []
acceptance_criteria:
  - The prerequisite task SHALL complete.
```

### Task: TASK-002 - Premature Task

```yaml
id: TASK-002
title: Premature Task
status: IN_PROGRESS
assignee: self
depends_on:
  - TASK-001
acceptance_criteria:
  - The downstream task SHALL wait for prerequisite.
```
"""
        tasks, diagnostics, _ = self.validator.validate_text(content)
        rule_ids = [d.rule_id for d in diagnostics]
        self.assertIn("UNMET_PREREQUISITE_DEPENDENCY", rule_ids)

    def test_aborted_status_with_and_without_reason(self):
        content_with_reason = """### Task: TASK-001 - Aborted Task

```yaml
id: TASK-001
title: Aborted Task
status: ABORTED
assignee: self
depends_on: []
abort_reason: Feature requirement was cancelled by user.
acceptance_criteria:
  - The task SHALL record reason.
```
"""
        tasks, diags_valid, _ = self.validator.validate_text(content_with_reason)
        errors_valid = [d for d in diags_valid if d.severity == "ERROR"]
        self.assertEqual(len(errors_valid), 0)

        content_without_reason = """### Task: TASK-001 - Aborted Task

```yaml
id: TASK-001
title: Aborted Task
status: ABORTED
assignee: self
depends_on: []
acceptance_criteria:
  - The task SHALL record reason.
```
"""
        tasks, diags_invalid, _ = self.validator.validate_text(content_without_reason)
        rule_ids = [d.rule_id for d in diags_invalid]
        self.assertIn("MISSING_ABORT_REASON", rule_ids)

    def test_ace_linting_forbidden_modals(self):
        content = """### Task: TASK-001 - Modal Violation

```yaml
id: TASK-001
title: Modal Violation
status: TODO
assignee: self
depends_on: []
acceptance_criteria:
  - The system should return JSON output.
```
"""
        tasks, diagnostics, _ = self.validator.validate_text(content)
        rule_ids = [d.rule_id for d in diagnostics]
        self.assertIn("ACE_FORBIDDEN_MODAL", rule_ids)

    def test_ace_linting_ambiguous_words(self):
        content = """### Task: TASK-001 - Ambiguous Words Violation

```yaml
id: TASK-001
title: Ambiguous Words Violation
status: TODO
assignee: self
depends_on: []
acceptance_criteria:
  - The system SHALL return fast responses etc.
```
"""
        tasks, diagnostics, _ = self.validator.validate_text(content)
        rule_ids = [d.rule_id for d in diagnostics]
        self.assertIn("ACE_AMBIGUOUS_WORD", rule_ids)

    def test_ace_linting_passive_voice(self):
        content = """### Task: TASK-001 - Passive Voice Violation

```yaml
id: TASK-001
title: Passive Voice Violation
status: TODO
assignee: self
depends_on: []
acceptance_criteria:
  - The file is executed by the test runner.
```
"""
        tasks, diagnostics, _ = self.validator.validate_text(content)
        rule_ids = [d.rule_id for d in diagnostics]
        self.assertIn("ACE_PASSIVE_VOICE", rule_ids)

    def test_status_summary_logic(self):
        content = """### Task: TASK-001 - Prereq 1

```yaml
id: TASK-001
title: Prereq 1
status: DONE
assignee: self
depends_on: []
acceptance_criteria:
  - Task 1 SHALL complete.
```

### Task: TASK-002 - Prereq 2

```yaml
id: TASK-002
title: Prereq 2
status: DONE
assignee: self
depends_on: []
acceptance_criteria:
  - Task 2 SHALL complete.
```

### Task: TASK-003 - Unblocked Ready Task

```yaml
id: TASK-003
title: Unblocked Ready Task
status: TODO
assignee: self
depends_on:
  - TASK-001
  - TASK-002
acceptance_criteria:
  - Task 3 SHALL execute.
```

### Task: TASK-004 - Blocked Task

```yaml
id: TASK-004
title: Blocked Task
status: TODO
assignee: self
depends_on:
  - TASK-003
acceptance_criteria:
  - Task 4 SHALL wait.
```
"""
        tasks, diagnostics, summary = self.validator.validate_text(content)
        errors = [d for d in diagnostics if d.severity == "ERROR"]
        self.assertEqual(len(errors), 0)
        self.assertEqual(summary["total_tasks"], 4)
        self.assertEqual(summary["counts"]["DONE"], 2)
        self.assertEqual(summary["counts"]["TODO"], 2)
        self.assertEqual(summary["ready_tasks"], ["TASK-003"])
        self.assertEqual(summary["blocked_tasks"], ["TASK-004"])
        self.assertFalse(summary["is_terminal"])


if __name__ == "__main__":
    unittest.main()
