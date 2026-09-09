#!/usr/bin/env python3
"""
Test suite for Design Skill Specification Validator.
"""

import unittest
import os
import sys
import tempfile
import subprocess
import importlib.util

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
validator_path = os.path.join(REPO_ROOT, ".agents", "skills", "design", "scripts", "validator.py")

spec = importlib.util.spec_from_file_location("design_validator_mod", validator_path)
design_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(design_mod)

DesignValidator = design_mod.DesignValidator


class TestDesignValidator(unittest.TestCase):
    def setUp(self):
        self.validator = DesignValidator()

    def test_valid_specification(self):
        content = """---
slug: auth-token-refresh
status: DRAFT
approved_by: pending
artifacts:
  - docs/.prompts-and-prayers/auth-token-refresh/02-design/design-spec.md
---

# Design Specification: Auth Flow

## 1. User Journey & Interaction Flow

### Overview
User initiates login and receives an active authenticated session.

### Interaction Flowchart
```mermaid
flowchart TD
    A["Enter Email"] --> B["Submit Credentials"]
    B --> C["Dashboard Displayed"]
```

## 2. Screen State Transitions

```mermaid
stateDiagram-v2
    [*] --> Idle
    Idle --> Loading: Submit
    Loading --> Success: Auth Valid
    Loading --> Error: Auth Invalid
    Success --> [*]
    Error --> Idle: Retry
```

## 3. UI Layout & Component Specifications

### Layout Structure
- **Header**: Contains application logo and status indicator.
- **Main Viewport**: Contains email and password input fields with submit button.
- **Action Controls**: Primary login button and reset link.

### Component Specifications
- **LoginForm**: Manages form validation state and submit action.

## 4. Accessibility & Responsive Requirements

- The interface SHALL support full keyboard navigation for all controls.
- The interface SHALL provide explicit aria-label attributes on icon buttons.
- The layout SHALL adapt responsively across mobile and desktop viewports.
- The system SHALL maintain a minimum color contrast ratio of 4.5 to 1.
"""
        diags, summary = self.validator.validate_text(content)
        errors = [d for d in diags if d.severity == "ERROR"]
        self.assertEqual(len(errors), 0, f"Expected 0 errors, got: {[d.to_dict() for d in errors]}")
        self.assertEqual(summary["slug"], "auth-token-refresh")
        self.assertEqual(summary["status"], "DRAFT")
        self.assertEqual(summary["mermaid_blocks_count"], 2)

    def test_valid_ux_specification_title_backwards_compatible(self):
        content = """---
slug: legacy-ux
status: DRAFT
approved_by: pending
artifacts:
  - test.md
---

# UX Design Specification: Legacy Screen

## 1. User Journey & Interaction Flow
```mermaid
flowchart LR
    A --> B
```

## 2. Screen State Transitions
```mermaid
stateDiagram-v2
    [*] --> Active
```

## 3. UI Layout & Component Specifications
Layout description.

## 4. Accessibility & Responsive Requirements
- The system SHALL support keyboard navigation.
"""
        diags, _ = self.validator.validate_text(content)
        errors = [d for d in diags if d.severity == "ERROR"]
        self.assertEqual(len(errors), 0)

    def test_extra_key_in_frontmatter_ignored(self):
        content = """---
slug: auth-flow
persona: design
status: DRAFT
approved_by: pending
artifacts:
  - test.md
---

# Design Specification: Auth Flow

## 1. User Journey & Interaction Flow
```mermaid
flowchart TD
    A --> B
```

## 2. Screen State Transitions
```mermaid
stateDiagram-v2
    [*] --> Active
```

## 3. UI Layout & Component Specifications
Layout.

## 4. Accessibility & Responsive Requirements
- The system SHALL support tab navigation.
"""
        diags, _ = self.validator.validate_text(content)
        errors = [d for d in diags if d.severity == "ERROR"]
        self.assertEqual(len(errors), 0)

    def test_missing_frontmatter_delimiter(self):
        content = """# Design Specification: Missing Frontmatter
## 1. User Journey & Interaction Flow
"""
        diags, _ = self.validator.validate_text(content)
        rule_ids = [d.rule_id for d in diags]
        self.assertIn("FRONTMATTER_MISSING", rule_ids)

    def test_unclosed_frontmatter(self):
        content = """---
slug: bad-fm
status: DRAFT
# Design Specification: Unclosed
"""
        diags, _ = self.validator.validate_text(content)
        rule_ids = [d.rule_id for d in diags]
        self.assertIn("FRONTMATTER_UNCLOSED", rule_ids)

    def test_missing_mandatory_frontmatter_keys(self):
        content = """---
status: DRAFT
---
# Design Specification: Test
"""
        diags, _ = self.validator.validate_text(content)
        rule_ids = [d.rule_id for d in diags]
        self.assertIn("SCHEMA_MISSING_KEY", rule_ids)

    def test_invalid_status(self):
        content = """---
slug: test-slug
status: UNKNOWN_STATUS
approved_by: pending
artifacts:
  - test.md
---
# Design Specification: Test
"""
        diags, _ = self.validator.validate_text(content)
        rule_ids = [d.rule_id for d in diagnostics_errors(diags)]
        self.assertIn("SCHEMA_INVALID_STATUS", rule_ids)

    def test_invalid_approved_by(self):
        content = """---
slug: test-slug
status: DRAFT
approved_by: robot
artifacts:
  - test.md
---
# Design Specification: Test
"""
        diags, _ = self.validator.validate_text(content)
        rule_ids = [d.rule_id for d in diagnostics_errors(diags)]
        self.assertIn("SCHEMA_INVALID_APPROVED_BY", rule_ids)

    def test_invalid_artifacts(self):
        content = """---
slug: test-slug
status: DRAFT
approved_by: pending
artifacts: []
---
# Design Specification: Test
"""
        diags, _ = self.validator.validate_text(content)
        rule_ids = [d.rule_id for d in diagnostics_errors(diags)]
        self.assertIn("SCHEMA_INVALID_ARTIFACTS", rule_ids)

    def test_missing_mandatory_sections(self):
        content = """---
slug: test-slug
status: DRAFT
approved_by: pending
artifacts:
  - test.md
---

# Design Specification: Incomplete Spec

## 1. User Journey & Interaction Flow
```mermaid
flowchart TD
    A --> B
```
"""
        diags, _ = self.validator.validate_text(content)
        rule_ids = [d.rule_id for d in diagnostics_errors(diags)]
        self.assertIn("STRUCTURE_MISSING_SECTION", rule_ids)

    def test_invalid_section_order(self):
        content = """---
slug: test-slug
status: DRAFT
approved_by: pending
artifacts:
  - test.md
---

# Design Specification: Bad Order

## 2. Screen State Transitions
```mermaid
stateDiagram-v2
    [*] --> Active
```

## 1. User Journey & Interaction Flow
```mermaid
flowchart TD
    A --> B
```

## 3. UI Layout & Component Specifications
Layout.

## 4. Accessibility & Responsive Requirements
- The system SHALL support tab navigation.
"""
        diags, _ = self.validator.validate_text(content)
        rule_ids = [d.rule_id for d in diagnostics_errors(diags)]
        self.assertIn("SECTION_ORDER_INVALID", rule_ids)

    def test_missing_mermaid_blocks(self):
        content = """---
slug: test-slug
status: DRAFT
approved_by: pending
artifacts:
  - test.md
---

# Design Specification: No Diagrams

## 1. User Journey & Interaction Flow
No diagram here.

## 2. Screen State Transitions
No diagram here.

## 3. UI Layout & Component Specifications
Layout.

## 4. Accessibility & Responsive Requirements
- The system SHALL support tab navigation.
"""
        diags, _ = self.validator.validate_text(content)
        rule_ids = [d.rule_id for d in diagnostics_errors(diags)]
        self.assertIn("MERMAID_MISSING", rule_ids)

    def test_missing_flowchart(self):
        content = """---
slug: test-slug
status: DRAFT
approved_by: pending
artifacts:
  - test.md
---

# Design Specification: Missing Flowchart

## 1. User Journey & Interaction Flow
No flowchart.

## 2. Screen State Transitions
```mermaid
stateDiagram-v2
    [*] --> Active
```

## 3. UI Layout & Component Specifications
Layout.

## 4. Accessibility & Responsive Requirements
- The system SHALL support tab navigation.
"""
        diags, _ = self.validator.validate_text(content)
        rule_ids = [d.rule_id for d in diagnostics_errors(diags)]
        self.assertIn("FLOWCHART_MISSING", rule_ids)

    def test_missing_state_diagram(self):
        content = """---
slug: test-slug
status: DRAFT
approved_by: pending
artifacts:
  - test.md
---

# Design Specification: Missing State Diagram

## 1. User Journey & Interaction Flow
```mermaid
flowchart TD
    A --> B
```

## 2. Screen State Transitions
No state diagram.

## 3. UI Layout & Component Specifications
Layout.

## 4. Accessibility & Responsive Requirements
- The system SHALL support tab navigation.
"""
        diags, _ = self.validator.validate_text(content)
        rule_ids = [d.rule_id for d in diagnostics_errors(diags)]
        self.assertIn("STATE_DIAGRAM_MISSING", rule_ids)

    def test_forbidden_ascii_art(self):
        content = """---
slug: test-slug
status: DRAFT
approved_by: pending
artifacts:
  - test.md
---

# Design Specification: ASCII Box

## 1. User Journey & Interaction Flow
+-------------------+
| ASCII Box Diagram |
+-------------------+

```mermaid
flowchart TD
    A --> B
```

## 2. Screen State Transitions
```mermaid
stateDiagram-v2
    [*] --> Active
```

## 3. UI Layout & Component Specifications
Layout.

## 4. Accessibility & Responsive Requirements
- The system SHALL support tab navigation.
"""
        diags, _ = self.validator.validate_text(content)
        rule_ids = [d.rule_id for d in diagnostics_errors(diags)]
        self.assertIn("FORBIDDEN_ASCII_ART", rule_ids)

    def test_forbidden_modal_in_accessibility(self):
        content = """---
slug: test-slug
status: DRAFT
approved_by: pending
artifacts:
  - test.md
---

# Design Specification: Modal Violation

## 1. User Journey & Interaction Flow
```mermaid
flowchart TD
    A --> B
```

## 2. Screen State Transitions
```mermaid
stateDiagram-v2
    [*] --> Active
```

## 3. UI Layout & Component Specifications
Layout.

## 4. Accessibility & Responsive Requirements
- The system should support keyboard navigation.
"""
        diags, _ = self.validator.validate_text(content)
        rule_ids = [d.rule_id for d in diagnostics_errors(diags)]
        self.assertIn("FORBIDDEN_MODAL", rule_ids)

    def test_ambiguous_word_in_accessibility(self):
        content = """---
slug: test-slug
status: DRAFT
approved_by: pending
artifacts:
  - test.md
---

# Design Specification: Ambiguous Word

## 1. User Journey & Interaction Flow
```mermaid
flowchart TD
    A --> B
```

## 2. Screen State Transitions
```mermaid
stateDiagram-v2
    [*] --> Active
```

## 3. UI Layout & Component Specifications
Layout.

## 4. Accessibility & Responsive Requirements
- The layout SHALL provide a user-friendly experience.
"""
        diags, _ = self.validator.validate_text(content)
        rule_ids = [d.rule_id for d in diagnostics_errors(diags)]
        self.assertIn("AMBIGUOUS_WORD", rule_ids)

    def test_passive_voice_in_accessibility(self):
        content = """---
slug: test-slug
status: DRAFT
approved_by: pending
artifacts:
  - test.md
---

# Design Specification: Passive Voice

## 1. User Journey & Interaction Flow
```mermaid
flowchart TD
    A --> B
```

## 2. Screen State Transitions
```mermaid
stateDiagram-v2
    [*] --> Active
```

## 3. UI Layout & Component Specifications
Layout.

## 4. Accessibility & Responsive Requirements
- The icon button is rendered by the framework with an aria-label.
"""
        diags, _ = self.validator.validate_text(content)
        rule_ids = [d.rule_id for d in diagnostics_errors(diags)]
        self.assertIn("PASSIVE_VOICE", rule_ids)

    def test_cli_execution(self):
        doc = """---
slug: cli-test
status: DRAFT
approved_by: pending
artifacts:
  - docs/.prompts-and-prayers/cli-test/02-design/design-spec.md
---

# Design Specification: CLI Flow

## 1. User Journey & Interaction Flow
```mermaid
flowchart TD
    A --> B
```

## 2. Screen State Transitions
```mermaid
stateDiagram-v2
    [*] --> Done
```

## 3. UI Layout & Component Specifications
Standard layout.

## 4. Accessibility & Responsive Requirements
- The interface SHALL support keyboard navigation.
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

    def test_cli_stdin_execution(self):
        doc = """---
slug: stdin-test
status: DRAFT
approved_by: pending
artifacts:
  - stdin.md
---

# Design Specification: Stdin Flow

## 1. User Journey & Interaction Flow
```mermaid
flowchart TD
    A --> B
```

## 2. Screen State Transitions
```mermaid
stateDiagram-v2
    [*] --> Done
```

## 3. UI Layout & Component Specifications
Standard layout.

## 4. Accessibility & Responsive Requirements
- The interface SHALL support keyboard navigation.
"""
        res = subprocess.run(
            [sys.executable, validator_path, "-", "--json"],
            input=doc,
            capture_output=True,
            text=True
        )
        self.assertEqual(res.returncode, 0)
        self.assertIn('"valid": true', res.stdout)


def diagnostics_errors(diags):
    return [d for d in diags if d.severity == "ERROR"]


if __name__ == "__main__":
    unittest.main()
