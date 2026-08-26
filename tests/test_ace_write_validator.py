#!/usr/bin/env python3
"""
Test suite for Agentic ACE Validator (ace-write skill).
"""

import unittest
import os
import importlib.util

validator_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".agents", "skills", "ace-write", "scripts", "validator.py"))
spec = importlib.util.spec_from_file_location("ace_validator_module", validator_path)
ace_validator_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ace_validator_mod)

AceValidator = ace_validator_mod.AceValidator


class TestAceValidator(unittest.TestCase):
    def setUp(self):
        self.validator = AceValidator()

    def test_clean_svo_text(self):
        text = """
# Test Skill

The agent SHALL execute the specified command.
The system MUST return a JSON response.
IF the command fails, THEN the agent SHALL log the error.

GIVEN a valid file path.
WHEN the user invokes the tool.
THEN the tool SHALL output the file contents.
INVARIANT the tool SHALL NOT modify the source file.
"""
        diagnostics = self.validator.validate_text(text)
        errors = [d for d in diagnostics if d.severity == "ERROR"]
        self.assertEqual(len(errors), 0, f"Expected 0 errors, got: {[d.to_dict() for d in errors]}")

    def test_passive_voice_detection(self):
        text = "The file is processed by the agent."
        diagnostics = self.validator.validate_text(text)
        rule_ids = [d.rule_id for d in diagnostics]
        self.assertIn("PASSIVE_VOICE", rule_ids)

    def test_forbidden_modal_detection(self):
        text = "The agent should run tests before committing."
        diagnostics = self.validator.validate_text(text)
        rule_ids = [d.rule_id for d in diagnostics]
        self.assertIn("FORBIDDEN_MODAL", rule_ids)

    def test_ambiguity_word_detection(self):
        text = "The system SHALL provide a user-friendly interface with fast responses etc."
        diagnostics = self.validator.validate_text(text)
        rule_ids = [d.rule_id for d in diagnostics]
        self.assertIn("AMBIGUOUS_WORD", rule_ids)

    def test_code_blocks_and_frontmatter_ignored(self):
        text = """---
name: sample
description: The tool should be fast etc.
---

# Prose Header

The agent SHALL read the configuration file.

```python
# In code comments: this should be fast etc.
def process():
    pass
```
"""
        diagnostics = self.validator.validate_text(text)
        errors = [d for d in diagnostics if d.severity == "ERROR"]
        self.assertEqual(len(errors), 0, f"Expected 0 errors in code/frontmatter, got: {[d.to_dict() for d in errors]}")

    def test_em_dash_detection(self):
        text_with_em = "The agent SHALL execute the command — immediately."
        diagnostics = self.validator.validate_text(text_with_em)
        rule_ids = [d.rule_id for d in diagnostics]
        self.assertIn("EM_DASH_DISALLOWED", rule_ids)

        text_with_en = "The agent SHALL execute steps 1 – 5."
        diagnostics = self.validator.validate_text(text_with_en)
        rule_ids = [d.rule_id for d in diagnostics]
        self.assertIn("EM_DASH_DISALLOWED", rule_ids)

        text_clean = "The agent SHALL execute the command immediately."
        diagnostics = self.validator.validate_text(text_clean)
        errors = [d for d in diagnostics if d.severity == "ERROR"]
        self.assertEqual(len(errors), 0)

    def test_horizontal_divider_detection(self):
        text_with_divider = """
# Section 1

The agent SHALL execute the command.

---

# Section 2

The agent SHALL output the result.
"""
        diagnostics = self.validator.validate_text(text_with_divider)
        rule_ids = [d.rule_id for d in diagnostics]
        self.assertIn("HORIZONTAL_DIVIDER_DISALLOWED", rule_ids)


if __name__ == "__main__":
    unittest.main()
