#!/usr/bin/env python3
"""
Test suite for Prose Validator (ASD-STE100 and Attempto Controlled English modes).
"""

import unittest
import os
import importlib.util

validator_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".agents", "skills", "prose", "scripts", "validator.py"))
spec = importlib.util.spec_from_file_location("prose_validator_module", validator_path)
prose_validator_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prose_validator_mod)

ProseValidator = prose_validator_mod.ProseValidator
PlainEnglishValidator = prose_validator_mod.PlainEnglishValidator
AceValidator = prose_validator_mod.AceValidator
count_syllables_in_word = prose_validator_mod.count_syllables_in_word


class TestProseValidatorSTE(unittest.TestCase):
    def setUp(self):
        self.validator = ProseValidator(mode="ste")

    def test_clean_plain_english_text(self):
        text = """
# Quick Start Guide

To run the server, add your API key to the environment.
Then start the worker process with `npm start`.
The server listens on port 3000.
The system sends logs to the log directory.
"""
        diagnostics, metrics = self.validator.validate_text(text)
        errors = [d for d in diagnostics if d.severity == "ERROR"]
        self.assertEqual(len(errors), 0, f"Expected 0 errors, got: {[d.to_dict() for d in errors]}")
        self.assertGreaterEqual(metrics["flesch_reading_ease"], 65.0)

    def test_passive_voice_detection(self):
        text = "The log file is written by the server process."
        diagnostics, _ = self.validator.validate_text(text)
        rule_ids = [d.rule_id for d in diagnostics]
        self.assertIn("PASSIVE_VOICE_DISALLOWED", rule_ids)

    def test_complex_word_detection(self):
        text = "The agent will utilize advanced tools in order to terminate the job."
        diagnostics, _ = self.validator.validate_text(text)
        rule_ids = [d.rule_id for d in diagnostics]
        self.assertIn("COMPLEX_WORD_DETECTED", rule_ids)

    def test_nominalization_detection(self):
        text = "The team will make a determination after we conduct an investigation."
        diagnostics, _ = self.validator.validate_text(text)
        rule_ids = [d.rule_id for d in diagnostics]
        self.assertIn("NOMINALIZATION_DETECTED", rule_ids)

    def test_fluff_phrase_detection(self):
        text = "It is important to note that the system runs smoothly."
        diagnostics, _ = self.validator.validate_text(text)
        rule_ids = [d.rule_id for d in diagnostics]
        self.assertIn("FLUFF_PHRASE_DETECTED", rule_ids)

    def test_sentence_length_exceeded(self):
        text = "This is an extremely long sentence that contains far too many words for a plain english sentence because it just keeps going on and on without stopping."
        diagnostics, _ = self.validator.validate_text(text)
        rule_ids = [d.rule_id for d in diagnostics]
        self.assertIn("SENTENCE_LENGTH_EXCEEDED", rule_ids)

    def test_raw_ace_keyword_residue(self):
        text = "GIVEN a clean workspace."
        diagnostics, _ = self.validator.validate_text(text)
        rule_ids = [d.rule_id for d in diagnostics]
        self.assertIn("RAW_ACE_KEYWORD_RESIDUE", rule_ids)

    def test_code_blocks_and_frontmatter_ignored(self):
        text = """---
name: sample
description: The tool should utilize fast methods.
---

# Prose Header

The worker process reads the configuration file.

```python
# In code comments: the file is written by server in order to utilize memory
def process():
    pass
```
"""
        diagnostics, _ = self.validator.validate_text(text)
        errors = [d for d in diagnostics if d.severity == "ERROR"]
        self.assertEqual(len(errors), 0, f"Expected 0 errors in code/frontmatter, got: {[d.to_dict() for d in errors]}")

    def test_em_dash_detection(self):
        text_with_em = "The worker process runs the task — immediately."
        diagnostics, _ = self.validator.validate_text(text_with_em)
        rule_ids = [d.rule_id for d in diagnostics]
        self.assertIn("EM_DASH_DISALLOWED", rule_ids)

        text_with_en = "The worker process executes steps 1 – 5."
        diagnostics, _ = self.validator.validate_text(text_with_en)
        rule_ids = [d.rule_id for d in diagnostics]
        self.assertIn("EM_DASH_DISALLOWED", rule_ids)

        text_with_double_hyphen = "The worker process executes steps 1 -- 5."
        diagnostics, _ = self.validator.validate_text(text_with_double_hyphen)
        rule_ids = [d.rule_id for d in diagnostics]
        self.assertIn("EM_DASH_DISALLOWED", rule_ids)

        text_clean = "The worker process runs the task immediately."
        diagnostics, _ = self.validator.validate_text(text_clean)
        errors = [d for d in diagnostics if d.severity == "ERROR"]
        self.assertEqual(len(errors), 0)

    def test_horizontal_divider_detection(self):
        text_with_divider = """
# Section 1

The worker process runs the task.

---

# Section 2

The worker process logs the result.
"""
        diagnostics, _ = self.validator.validate_text(text_with_divider)
        rule_ids = [d.rule_id for d in diagnostics]
        self.assertIn("HORIZONTAL_DIVIDER_DISALLOWED", rule_ids)

    def test_syllable_counter(self):
        self.assertEqual(count_syllables_in_word("use"), 1)
        self.assertEqual(count_syllables_in_word("help"), 1)
        self.assertEqual(count_syllables_in_word("decide"), 2)
        self.assertEqual(count_syllables_in_word("investigate"), 4)


class TestProseValidatorACE(unittest.TestCase):
    def setUp(self):
        self.validator = ProseValidator(mode="ace")

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
        diagnostics, _ = self.validator.validate_text(text)
        errors = [d for d in diagnostics if d.severity == "ERROR"]
        self.assertEqual(len(errors), 0, f"Expected 0 errors, got: {[d.to_dict() for d in errors]}")

    def test_passive_voice_detection(self):
        text = "The file is processed by the agent."
        diagnostics, _ = self.validator.validate_text(text)
        rule_ids = [d.rule_id for d in diagnostics]
        self.assertIn("PASSIVE_VOICE", rule_ids)

    def test_forbidden_modal_detection(self):
        text = "The agent should run tests before committing."
        diagnostics, _ = self.validator.validate_text(text)
        rule_ids = [d.rule_id for d in diagnostics]
        self.assertIn("FORBIDDEN_MODAL", rule_ids)

    def test_ambiguity_word_detection(self):
        text = "The system SHALL provide a user-friendly interface with fast responses etc."
        diagnostics, _ = self.validator.validate_text(text)
        rule_ids = [d.rule_id for d in diagnostics]
        self.assertIn("AMBIGUOUS_WORD", rule_ids)

    def test_atomic_sentence_length(self):
        text = "The system SHALL execute the command and process every result and deliver data to all callers across all components without any interruption whatsoever and continue indefinitely."
        diagnostics, _ = self.validator.validate_text(text)
        rule_ids = [d.rule_id for d in diagnostics]
        self.assertIn("ATOMIC_SENTENCE", rule_ids)


class TestBackwardCompatibility(unittest.TestCase):
    def test_plain_english_validator_alias(self):
        validator = PlainEnglishValidator()
        text = "The worker process reads the file."
        diagnostics, metrics = validator.validate_text(text)
        self.assertEqual(len(diagnostics), 0)
        self.assertIn("flesch_reading_ease", metrics)

    def test_ace_validator_alias(self):
        validator = AceValidator()
        text = "The agent SHALL execute the task."
        diagnostics = validator.validate_text(text)
        self.assertIsInstance(diagnostics, list)
        self.assertEqual(len(diagnostics), 0)


if __name__ == "__main__":
    unittest.main()
