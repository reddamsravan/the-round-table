#!/usr/bin/env python3
"""
Test suite for Agent Skill Validator (write-a-skill skill).
"""

import unittest
import os
import tempfile
import importlib.util

validator_path = os.path.abspath(os.path.join(
    os.path.dirname(__file__), "..", ".agents", "skills", "write-a-skill", "scripts", "validator.py"
))
spec = importlib.util.spec_from_file_location("write_a_skill_validator_mod", validator_path)
validator_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator_mod)

SkillValidator = validator_mod.SkillValidator
validate_skill_frontmatter = validator_mod.validate_skill_frontmatter
parse_frontmatter = validator_mod.parse_frontmatter


class TestSkillFrontmatterValidation(unittest.TestCase):
    def setUp(self):
        self.validator = SkillValidator()

    def test_valid_minimal_frontmatter(self):
        content = """---
name: sample-skill
description: A clear description explaining what this skill does and when to use it.
---

# Sample Skill Content
"""
        diagnostics = self.validator.validate_content(content, expected_dir_name="sample-skill")
        errors = [d for d in diagnostics if d.severity == "ERROR"]
        self.assertEqual(len(errors), 0, f"Expected 0 errors, got: {[d.to_dict() for d in errors]}")

    def test_valid_full_frontmatter(self):
        content = """---
name: pdf-tools
description: Extracts text from PDFs. Use when handling PDF documents.
compatibility: Requires Python 3.10+ and pypdf
license: Apache-2.0
metadata:
  version: "1.0.0"
  category: "utility"
allowed-tools: Bash Read Write
---

# PDF Tools
"""
        diagnostics = self.validator.validate_content(content, expected_dir_name="pdf-tools")
        errors = [d for d in diagnostics if d.severity == "ERROR"]
        self.assertEqual(len(errors), 0, f"Expected 0 errors, got: {[d.to_dict() for d in errors]}")

    def test_missing_name_and_description(self):
        content = """---
compatibility: Python 3
---
"""
        diagnostics = self.validator.validate_content(content)
        rule_ids = [d.rule_id for d in diagnostics]
        self.assertIn("MISSING_NAME", rule_ids)
        self.assertIn("MISSING_DESCRIPTION", rule_ids)

    def test_invalid_name_formats(self):
        # Uppercase
        diags = self.validator.validate_content("---\nname: Sample-Skill\ndescription: Test\n---\n")
        self.assertIn("NAME_FORMAT_INVALID", [d.rule_id for d in diags])

        # Leading hyphen
        diags = self.validator.validate_content("---\nname: -sample\ndescription: Test\n---\n")
        self.assertIn("NAME_FORMAT_INVALID", [d.rule_id for d in diags])

        # Trailing hyphen
        diags = self.validator.validate_content("---\nname: sample-\ndescription: Test\n---\n")
        self.assertIn("NAME_FORMAT_INVALID", [d.rule_id for d in diags])

        # Consecutive hyphens
        diags = self.validator.validate_content("---\nname: sample--skill\ndescription: Test\n---\n")
        self.assertIn("NAME_FORMAT_INVALID", [d.rule_id for d in diags])

        # Name too long (>64 chars)
        long_name = "a" * 65
        diags = self.validator.validate_content(f"---\nname: {long_name}\ndescription: Test\n---\n")
        self.assertIn("NAME_LENGTH_INVALID", [d.rule_id for d in diags])

    def test_name_directory_mismatch(self):
        content = """---
name: actual-name
description: Test description
---
"""
        diagnostics = self.validator.validate_content(content, expected_dir_name="different-name")
        rule_ids = [d.rule_id for d in diagnostics]
        self.assertIn("NAME_DIRECTORY_MISMATCH", rule_ids)

    def test_invalid_descriptions(self):
        # Empty description
        diags = self.validator.validate_content("---\nname: sample\ndescription: ''\n---\n")
        self.assertIn("EMPTY_DESCRIPTION", [d.rule_id for d in diags])

        # Description too long (> 1024 chars)
        long_desc = "d" * 1025
        diags = self.validator.validate_content(f"---\nname: sample\ndescription: {long_desc}\n---\n")
        self.assertIn("DESCRIPTION_TOO_LONG", [d.rule_id for d in diags])

    def test_optional_fields_constraints(self):
        # Compatibility too long (> 500 chars)
        long_comp = "c" * 501
        content = f"""---
name: sample
description: Valid description
compatibility: {long_comp}
---
"""
        diags = self.validator.validate_content(content)
        self.assertIn("COMPATIBILITY_TOO_LONG", [d.rule_id for d in diags])

        # Metadata with non-string values
        content_invalid_meta = """---
name: sample
description: Valid description
metadata:
  numeric_val: 123
---
"""
        diags = self.validator.validate_content(content_invalid_meta)
        self.assertIn("INVALID_METADATA_ENTRY", [d.rule_id for d in diags])

        # Valid disable-model-invocation
        content_valid_dmi = """---
name: sample
description: Valid description
disable-model-invocation: true
---
"""
        diags = self.validator.validate_content(content_valid_dmi)
        errors = [d for d in diags if d.severity == "ERROR"]
        self.assertEqual(len(errors), 0)

        # Invalid disable-model-invocation type
        content_invalid_dmi = """---
name: sample
description: Valid description
disable-model-invocation: "yes"
---
"""
        diags = self.validator.validate_content(content_invalid_dmi)
        self.assertIn("INVALID_DISABLE_MODEL_INVOCATION_TYPE", [d.rule_id for d in diags])

    def test_missing_frontmatter_delimiters(self):
        content_no_delimiters = "# Pure Markdown without frontmatter\n"
        diags = self.validator.validate_content(content_no_delimiters)
        self.assertIn("FRONTMATTER_PARSE_ERROR", [d.rule_id for d in diags])

        content_unclosed = "---\nname: sample\ndescription: unclosed\n"
        diags = self.validator.validate_content(content_unclosed)
        self.assertIn("FRONTMATTER_PARSE_ERROR", [d.rule_id for d in diags])

    def test_validate_path_file_and_dir(self):
        repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        skill_dir = os.path.join(repo_root, ".agents", "skills", "write-a-skill")

        # Validate directory
        diags, path = self.validator.validate_path(skill_dir)
        errors = [d for d in diags if d.severity == "ERROR"]
        self.assertEqual(len(errors), 0)
        self.assertTrue(path.endswith("SKILL.md"))

        # Validate missing path
        diags, _ = self.validator.validate_path(os.path.join(repo_root, "non_existent_dir"))
        self.assertIn("FILE_NOT_FOUND", [d.rule_id for d in diags])

        # Validate directory missing SKILL.md
        with tempfile.TemporaryDirectory() as tmp_dir:
            diags, _ = self.validator.validate_path(tmp_dir)
            self.assertIn("MISSING_SKILL_MD", [d.rule_id for d in diags])


if __name__ == "__main__":
    unittest.main()
