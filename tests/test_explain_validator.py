#!/usr/bin/env python3
"""
Test suite for Explain Skill Composite Validator.
"""

import unittest
import os
import sys
import tempfile
import subprocess
import importlib.util

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
validator_path = os.path.join(REPO_ROOT, ".agents", "skills", "explain", "scripts", "validator.py")

spec = importlib.util.spec_from_file_location("explain_validator_mod", validator_path)
explain_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(explain_mod)

ExplainValidator = explain_mod.ExplainValidator


class TestExplainValidator(unittest.TestCase):
    def setUp(self):
        self.validator = ExplainValidator()

    def test_valid_explanation_clean(self):
        content = """# Token Refresh Mechanism

## Problem & Context
The team needs a clean way to handle token refresh.
Old tokens expire after one hour and cause user requests to fail.
The service must update tokens quietly without user disruption.

## Mental Model & Analogy
Think of a refresh token like a hotel key card receipt.
You use the key card to open your hotel room door each day.
When the card expires, you show your receipt to get a new card.

## How It Works (Mechanics & Anatomy)
The client sends the refresh token to the authentication endpoint.
The server verifies the signature and checks the database record.
Then the server issues a new short-lived access token to the client.

```python
def refresh_token(token: str) -> str:
    return issue_access_token(verify(token))
```

## Pitfalls & Trade-offs
Refresh tokens can leak if clients store them in local storage.
Always store refresh tokens in secure cookies to prevent script theft.
Token rotation adds a small database check on each refresh cycle.
"""
        diagnostics, metrics = self.validator.validate_text(content)
        errors = [d for d in diagnostics if d.severity == "ERROR"]
        self.assertEqual(len(errors), 0, f"Expected 0 errors, got: {[d.to_dict() for d in errors]}")
        self.assertGreaterEqual(metrics["flesch_reading_ease"], 65.0)
        self.assertTrue(metrics["mandatory_sections_present"])
        self.assertEqual(metrics["sections_found_count"], 4)

    def test_missing_section_detection(self):
        content = """# Incomplete Explanation

## Problem & Context
The team needs a clean way to handle token refresh.
Old tokens expire after one hour and cause user requests to fail.
The service must update tokens quietly without user disruption.

## Mental Model & Analogy
Think of a refresh token like a hotel key card receipt.
You use the key card to open your hotel room door each day.
When the card expires, you show your receipt to get a new card.

## Pitfalls & Trade-offs
Refresh tokens can leak if clients store them in local storage.
Always store refresh tokens in secure cookies to prevent script theft.
Token rotation adds a small database check on each refresh cycle.
"""
        diagnostics, metrics = self.validator.validate_text(content)
        rule_ids = [d.rule_id for d in diagnostics]
        self.assertIn("MISSING_SECTION", rule_ids)
        self.assertFalse(metrics["mandatory_sections_present"])

    def test_insufficient_prose_word_count(self):
        content = """# Minimal Section

## Problem & Context
Too short.

## Mental Model & Analogy
Think of a refresh token like a hotel key card receipt.
You use the key card to open your hotel room door each day.
When the card expires, you show your receipt to get a new card.

## How It Works (Mechanics & Anatomy)
The client sends the refresh token to the authentication endpoint.
The server verifies the signature and checks the database record.
Then the server issues a new short-lived access token to the client.

## Pitfalls & Trade-offs
Refresh tokens can leak if clients store them in local storage.
Always store refresh tokens in secure cookies to prevent script theft.
Token rotation adds a small database check on each refresh cycle.
"""
        diagnostics, _ = self.validator.validate_text(content)
        rule_ids = [d.rule_id for d in diagnostics]
        self.assertIn("INSUFFICIENT_PROSE_WORD_COUNT", rule_ids)

    def test_section_order_invalid(self):
        content = """# Out of Order

## Mental Model & Analogy
Think of a refresh token like a hotel key card receipt.
You use the key card to open your hotel room door each day.
When the card expires, you show your receipt to get a new card.

## Problem & Context
The team needs a clean way to handle token refresh.
Old tokens expire after one hour and cause user requests to fail.
The service must update tokens quietly without user disruption.

## How It Works (Mechanics & Anatomy)
The client sends the refresh token to the authentication endpoint.
The server verifies the signature and checks the database record.
Then the server issues a new short-lived access token to the client.

## Pitfalls & Trade-offs
Refresh tokens can leak if clients store them in local storage.
Always store refresh tokens in secure cookies to prevent script theft.
Token rotation adds a small database check on each refresh cycle.
"""
        diagnostics, _ = self.validator.validate_text(content)
        rule_ids = [d.rule_id for d in diagnostics]
        self.assertIn("SECTION_ORDER_INVALID", rule_ids)

    def test_code_blocks_excluded_from_word_count(self):
        content = """# Code Dump Without Prose

## Problem & Context
```python
def foo():
    x = 1
    y = 2
    z = 3
    return x + y + z
```

## Mental Model & Analogy
Think of a refresh token like a hotel key card receipt.
You use the key card to open your hotel room door each day.
When the card expires, you show your receipt to get a new card.

## How It Works (Mechanics & Anatomy)
The client sends the refresh token to the authentication endpoint.
The server verifies the signature and checks the database record.
Then the server issues a new short-lived access token to the client.

## Pitfalls & Trade-offs
Refresh tokens can leak if clients store them in local storage.
Always store refresh tokens in secure cookies to prevent script theft.
Token rotation adds a small database check on each refresh cycle.
"""
        diagnostics, _ = self.validator.validate_text(content)
        rule_ids = [d.rule_id for d in diagnostics]
        self.assertIn("INSUFFICIENT_PROSE_WORD_COUNT", rule_ids)

    def test_write_validator_integration_passive_voice(self):
        content = """# Passive Voice Test

## Problem & Context
The authentication token is processed by the background auth worker.
Old tokens expire after one hour and cause user requests to fail.
The service must update tokens quietly without user disruption.

## Mental Model & Analogy
Think of a refresh token like a hotel key card receipt.
You use the key card to open your hotel room door each day.
When the card expires, you show your receipt to get a new card.

## How It Works (Mechanics & Anatomy)
The client sends the refresh token to the authentication endpoint.
The server verifies the signature and checks the database record.
Then the server issues a new short-lived access token to the client.

## Pitfalls & Trade-offs
Refresh tokens can leak if clients store them in local storage.
Always store refresh tokens in secure cookies to prevent script theft.
Token rotation adds a small database check on each refresh cycle.
"""
        diagnostics, _ = self.validator.validate_text(content)
        rule_ids = [d.rule_id for d in diagnostics]
        self.assertIn("PASSIVE_VOICE_DISALLOWED", rule_ids)

    def test_write_validator_integration_complex_words(self):
        content = """# Complex Words Test

## Problem & Context
The team will utilize modern libraries in order to commence operations.
Old tokens expire after one hour and cause user requests to fail.
The service must update tokens quietly without user disruption.

## Mental Model & Analogy
Think of a refresh token like a hotel key card receipt.
You use the key card to open your hotel room door each day.
When the card expires, you show your receipt to get a new card.

## How It Works (Mechanics & Anatomy)
The client sends the refresh token to the authentication endpoint.
The server verifies the signature and checks the database record.
Then the server issues a new short-lived access token to the client.

## Pitfalls & Trade-offs
Refresh tokens can leak if clients store them in local storage.
Always store refresh tokens in secure cookies to prevent script theft.
Token rotation adds a small database check on each refresh cycle.
"""
        diagnostics, _ = self.validator.validate_text(content)
        rule_ids = [d.rule_id for d in diagnostics]
        self.assertIn("COMPLEX_WORD_DETECTED", rule_ids)

    def test_cli_execution_valid_file(self):
        valid_doc = """# CLI Test Doc

## Problem & Context
The team needs a clean way to handle token refresh.
Old tokens expire after one hour and cause user requests to fail.
The service must update tokens quietly without user disruption.

## Mental Model & Analogy
Think of a refresh token like a hotel key card receipt.
You use the key card to open your hotel room door each day.
When the card expires, you show your receipt to get a new card.

## How It Works (Mechanics & Anatomy)
The client sends the refresh token to the authentication endpoint.
The server verifies the signature and checks the database record.
Then the server issues a new short-lived access token to the client.

## Pitfalls & Trade-offs
Refresh tokens can leak if clients store them in local storage.
Always store refresh tokens in secure cookies to prevent script theft.
Token rotation adds a small database check on each refresh cycle.
"""
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as f:
            f.write(valid_doc)
            f_path = f.name

        try:
            res = subprocess.run(
                [sys.executable, validator_path, f_path, "--json"],
                capture_output=True,
                text=True
            )
            self.assertEqual(res.returncode, 0)
            self.assertIn('"clean_files": 1', res.stdout)
        finally:
            if os.path.exists(f_path):
                os.remove(f_path)


if __name__ == "__main__":
    unittest.main()
