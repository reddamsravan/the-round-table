#!/usr/bin/env python3
"""
Test suite for Conventional Commit Validator (commit skill).
"""

import unittest
import os
import importlib.util
import json

validator_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", ".agents", "skills", "commit", "scripts", "validator.py")
)
spec = importlib.util.spec_from_file_location("commit_validator_module", validator_path)
commit_validator_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(commit_validator_mod)

CommitValidator = commit_validator_mod.CommitValidator


class TestCommitValidator(unittest.TestCase):
    def setUp(self):
        self.validator = CommitValidator()

    def test_valid_simple_commit(self):
        text = "feat(auth): add token refresh endpoint"
        diagnostics = self.validator.validate_text(text)
        errors = [d for d in diagnostics if d.severity == "ERROR"]
        self.assertEqual(len(errors), 0, f"Expected 0 errors, got: {[d.to_dict() for d in errors]}")

    def test_valid_commit_without_scope(self):
        text = "fix: resolve memory leak on shutdown"
        diagnostics = self.validator.validate_text(text)
        errors = [d for d in diagnostics if d.severity == "ERROR"]
        self.assertEqual(len(errors), 0)

    def test_valid_breaking_header(self):
        text = "refactor(api)!: drop deprecated v1 endpoints"
        diagnostics = self.validator.validate_text(text)
        errors = [d for d in diagnostics if d.severity == "ERROR"]
        self.assertEqual(len(errors), 0)

    def test_valid_multi_line_commit_with_body_and_footer(self):
        text = (
            "fix(parser): handle empty input lines\n"
            "\n"
            "The parser crashed on empty lines in input.\n"
            "This update checks line bounds before indexing.\n"
            "\n"
            "BREAKING CHANGE: parse_tokens returns None instead of error\n"
            "Fixes #42"
        )
        diagnostics = self.validator.validate_text(text)
        errors = [d for d in diagnostics if d.severity == "ERROR"]
        self.assertEqual(len(errors), 0, f"Expected 0 errors, got: {[d.to_dict() for d in errors]}")

    def test_invalid_type(self):
        text = "unknown(core): add something"
        diagnostics = self.validator.validate_text(text)
        rule_ids = [d.rule_id for d in diagnostics]
        self.assertIn("INVALID_TYPE", rule_ids)

    def test_invalid_scope_casing_and_chars(self):
        text_upper = "feat(Core): add feature"
        diags_upper = self.validator.validate_text(text_upper)
        self.assertIn("SCOPE_LOWERCASE", [d.rule_id for d in diags_upper])

        text_chars = "feat(core$): add feature"
        diags_chars = self.validator.validate_text(text_chars)
        self.assertIn("SCOPE_INVALID_CHARS", [d.rule_id for d in diags_chars])

    def test_subject_capitalization(self):
        text = "feat(core): Add new feature"
        diagnostics = self.validator.validate_text(text)
        rule_ids = [d.rule_id for d in diagnostics]
        self.assertIn("SUBJECT_LOWERCASE", rule_ids)

    def test_subject_trailing_period(self):
        text = "feat(core): add new feature."
        diagnostics = self.validator.validate_text(text)
        rule_ids = [d.rule_id for d in diagnostics]
        self.assertIn("SUBJECT_TRAILING_PERIOD", rule_ids)

    def test_subject_imperative_mood(self):
        past_tense = "feat(core): added new feature"
        diags_past = self.validator.validate_text(past_tense)
        self.assertIn("SUBJECT_IMPERATIVE_MOOD", [d.rule_id for d in diags_past])

        continuous = "fix(core): fixing memory leak"
        diags_cont = self.validator.validate_text(continuous)
        self.assertIn("SUBJECT_IMPERATIVE_MOOD", [d.rule_id for d in diags_cont])

        third_person = "refactor(core): refactors cache engine"
        diags_third = self.validator.validate_text(third_person)
        self.assertIn("SUBJECT_IMPERATIVE_MOOD", [d.rule_id for d in diags_third])

    def test_missing_blank_line_after_header(self):
        text = "feat: add feature\nThis is the body text without blank line."
        diagnostics = self.validator.validate_text(text)
        rule_ids = [d.rule_id for d in diagnostics]
        self.assertIn("BLANK_LINE_AFTER_HEADER", rule_ids)

    def test_subject_length_limits(self):
        # 55 chars header -> warns recommended length
        header_55 = "feat(core): implement very comprehensive authentication"
        diags_55 = self.validator.validate_text(header_55)
        self.assertIn("HEADER_LENGTH_RECOMMENDED", [d.rule_id for d in diags_55])
        self.assertEqual(len([d for d in diags_55 if d.severity == "ERROR"]), 0)

        # 75 chars header -> hard error
        header_75 = "feat(core): implement extremely long header text that exceeds seventy two characters"
        diags_75 = self.validator.validate_text(header_75)
        self.assertIn("HEADER_LENGTH_HARD_LIMIT", [d.rule_id for d in diags_75])

    def test_body_line_length_check(self):
        long_line = "a" * 80
        text = f"feat(core): add feature\n\n{long_line}"
        diagnostics = self.validator.validate_text(text)
        rule_ids = [d.rule_id for d in diagnostics]
        self.assertIn("BODY_LINE_LENGTH", rule_ids)

    def test_code_block_and_url_ignored_in_body_length(self):
        url = "https://example.com/very/long/path/to/resource/with/many/parameters/and/tokens/that/exceeds/seventy/two/characters"
        text = f"feat(core): add feature\n\nReference URL:\n{url}\n\n```json\n{{\"very_long_json_key_that_exceeds_limits\": 12345678901234567890}}\n```"
        diagnostics = self.validator.validate_text(text)
        errors = [d for d in diagnostics if d.severity == "ERROR"]
        self.assertEqual(len(errors), 0)

    def test_autofix_header_and_body(self):
        input_text = (
            "feat(CORE): Added new user authentication model.\n"
            "This is a very long body description that should be wrapped automatically by the autofix feature because it clearly exceeds the standard seventy two character line width limit for git commit messages.\n"
            "Fixes #100"
        )
        fixed = self.validator.autofix(input_text)
        fixed_diags = self.validator.validate_text(fixed)
        errors = [d for d in fixed_diags if d.severity == "ERROR"]
        self.assertEqual(len(errors), 0, f"Autofixed text had errors: {fixed}\nErrors: {[d.to_dict() for d in errors]}")
        self.assertTrue(fixed.startswith("feat(core): add new user authentication model"))

    def test_local_task_reference_rejected(self):
        text_footer = "feat(core): add feature\n\nCloses TASK-001"
        diags_footer = self.validator.validate_text(text_footer)
        self.assertIn("LOCAL_TASK_REFERENCE", [d.rule_id for d in diags_footer])

        text_header = "feat(core): add feature (TASK-001)"
        diags_header = self.validator.validate_text(text_header)
        self.assertIn("LOCAL_TASK_REFERENCE", [d.rule_id for d in diags_header])

    def test_autofix_removes_local_task_footer(self):
        input_text = "feat(core): add feature (TASK-001)\n\nImplementation details.\n\nCloses TASK-001"
        fixed = self.validator.autofix(input_text)
        diags = self.validator.validate_text(fixed)
        errors = [d for d in diags if d.severity == "ERROR"]
        self.assertEqual(len(errors), 0, f"Errors in autofixed text: {fixed}")
        self.assertNotIn("TASK-001", fixed)


if __name__ == "__main__":
    unittest.main()
