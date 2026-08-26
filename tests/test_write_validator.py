#!/usr/bin/env python3
"""
Test suite for Plain English Validator (write skill).
"""

import unittest
import os
import importlib.util

validator_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".agents", "skills", "write", "scripts", "validator.py"))
spec = importlib.util.spec_from_file_location("plain_english_validator_module", validator_path)
plain_validator_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(plain_validator_mod)

PlainEnglishValidator = plain_validator_mod.PlainEnglishValidator
count_syllables_in_word = plain_validator_mod.count_syllables_in_word


class TestPlainEnglishValidator(unittest.TestCase):
    def setUp(self):
        self.validator = PlainEnglishValidator()

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

    def test_syllable_counter(self):
        self.assertEqual(count_syllables_in_word("use"), 1)
        self.assertEqual(count_syllables_in_word("help"), 1)
        self.assertEqual(count_syllables_in_word("decide"), 2)
        self.assertEqual(count_syllables_in_word("investigate"), 4)


if __name__ == "__main__":
    unittest.main()
