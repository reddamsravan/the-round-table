#!/usr/bin/env python3
"""
Agent Skill Frontmatter & Specification Validator.

Validates skill directories and SKILL.md frontmatter against the standard
Agent Skills specification (references/specification.md).
"""

import sys
import os
import re
import json
import argparse
from typing import List, Dict, Any, Optional

try:
    import yaml
except ImportError:
    yaml = None


NAME_REGEX = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


class Diagnostic:
    def __init__(self, rule_id: str, severity: str, message: str, field: Optional[str] = None):
        self.rule_id = rule_id
        self.severity = severity  # "ERROR" or "WARNING"
        self.message = message
        self.field = field

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "severity": self.severity,
            "field": self.field,
            "message": self.message,
        }


def parse_frontmatter(content: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Extracts YAML frontmatter from markdown content."""
    lines = content.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, "Missing opening '---' frontmatter delimiter at line 1."

    closing_idx = -1
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            closing_idx = i
            break

    if closing_idx == -1:
        return None, "Missing closing '---' frontmatter delimiter."

    fm_text = "\n".join(lines[1:closing_idx])
    if yaml:
        try:
            parsed = yaml.safe_load(fm_text)
            if parsed is None:
                return {}, None
            if not isinstance(parsed, dict):
                return None, f"Frontmatter must parse to a mapping/dictionary, got {type(parsed).__name__}."
            return parsed, None
        except Exception as e:
            return None, f"YAML parse error in frontmatter: {str(e)}"
    else:
        # Simple fallback parser if PyYAML is unavailable
        parsed = {}
        for line in lines[1:closing_idx]:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if ":" in line:
                k, v = line.split(":", 1)
                parsed[k.strip()] = v.strip().strip("\"'")
        return parsed, None


def validate_skill_frontmatter(frontmatter: Dict[str, Any], expected_dir_name: Optional[str] = None) -> List[Diagnostic]:
    """Validates frontmatter against the standard Agent Skills specification."""
    diagnostics: List[Diagnostic] = []

    # 1. Validate 'name'
    if "name" not in frontmatter:
        diagnostics.append(Diagnostic("MISSING_NAME", "ERROR", "The 'name' field is required in frontmatter.", "name"))
    else:
        name_val = frontmatter["name"]
        if not isinstance(name_val, str):
            diagnostics.append(Diagnostic("INVALID_NAME_TYPE", "ERROR", f"'name' must be a string, got {type(name_val).__name__}.", "name"))
        else:
            name_str = name_val.strip()
            if len(name_str) < 1 or len(name_str) > 64:
                diagnostics.append(Diagnostic("NAME_LENGTH_INVALID", "ERROR", f"'name' length ({len(name_str)}) must be between 1 and 64 characters.", "name"))

            if not NAME_REGEX.match(name_str):
                diagnostics.append(Diagnostic(
                    "NAME_FORMAT_INVALID",
                    "ERROR",
                    f"'name' ('{name_str}') must consist of lowercase letters, digits, and hyphens without consecutive or edge hyphens.",
                    "name"
                ))

            if expected_dir_name and name_str != expected_dir_name:
                diagnostics.append(Diagnostic(
                    "NAME_DIRECTORY_MISMATCH",
                    "ERROR",
                    f"'name' ('{name_str}') does not match parent directory name ('{expected_dir_name}').",
                    "name"
                ))

    # 2. Validate 'description'
    if "description" not in frontmatter:
        diagnostics.append(Diagnostic("MISSING_DESCRIPTION", "ERROR", "The 'description' field is required in frontmatter.", "description"))
    else:
        desc_val = frontmatter["description"]
        if not isinstance(desc_val, str):
            diagnostics.append(Diagnostic("INVALID_DESCRIPTION_TYPE", "ERROR", f"'description' must be a string, got {type(desc_val).__name__}.", "description"))
        else:
            desc_str = desc_val.strip()
            if len(desc_str) < 1:
                diagnostics.append(Diagnostic("EMPTY_DESCRIPTION", "ERROR", "'description' must not be empty.", "description"))
            elif len(desc_str) > 1024:
                diagnostics.append(Diagnostic("DESCRIPTION_TOO_LONG", "ERROR", f"'description' length ({len(desc_str)}) exceeds maximum of 1024 characters.", "description"))

    # 3. Validate optional 'compatibility'
    if "compatibility" in frontmatter and frontmatter["compatibility"] is not None:
        comp_val = frontmatter["compatibility"]
        if not isinstance(comp_val, str):
            diagnostics.append(Diagnostic("INVALID_COMPATIBILITY_TYPE", "ERROR", f"'compatibility' must be a string, got {type(comp_val).__name__}.", "compatibility"))
        elif len(comp_val) > 500:
            diagnostics.append(Diagnostic("COMPATIBILITY_TOO_LONG", "ERROR", f"'compatibility' length ({len(comp_val)}) exceeds maximum of 500 characters.", "compatibility"))

    # 4. Validate optional 'metadata'
    if "metadata" in frontmatter and frontmatter["metadata"] is not None:
        meta_val = frontmatter["metadata"]
        if not isinstance(meta_val, dict):
            diagnostics.append(Diagnostic("INVALID_METADATA_TYPE", "ERROR", f"'metadata' must be a key-value mapping, got {type(meta_val).__name__}.", "metadata"))
        else:
            for k, v in meta_val.items():
                if not isinstance(k, str) or not isinstance(v, str):
                    diagnostics.append(Diagnostic("INVALID_METADATA_ENTRY", "ERROR", f"'metadata' entries must map string keys to string values; found {k}: {v}.", "metadata"))

    # 5. Validate optional 'allowed-tools'
    if "allowed-tools" in frontmatter and frontmatter["allowed-tools"] is not None:
        tools_val = frontmatter["allowed-tools"]
        if not isinstance(tools_val, str):
            diagnostics.append(Diagnostic("INVALID_ALLOWED_TOOLS_TYPE", "ERROR", f"'allowed-tools' must be a space-separated string, got {type(tools_val).__name__}.", "allowed-tools"))

    # 6. Validate optional 'license'
    if "license" in frontmatter and frontmatter["license"] is not None:
        lic_val = frontmatter["license"]
        if not isinstance(lic_val, str):
            diagnostics.append(Diagnostic("INVALID_LICENSE_TYPE", "ERROR", f"'license' must be a string, got {type(lic_val).__name__}.", "license"))

    # 7. Validate optional 'disable-model-invocation'
    if "disable-model-invocation" in frontmatter and frontmatter["disable-model-invocation"] is not None:
        dmi_val = frontmatter["disable-model-invocation"]
        if not isinstance(dmi_val, bool):
            diagnostics.append(Diagnostic("INVALID_DISABLE_MODEL_INVOCATION_TYPE", "ERROR", f"'disable-model-invocation' must be a boolean, got {type(dmi_val).__name__}.", "disable-model-invocation"))

    return diagnostics


class SkillValidator:
    """Validates an Agent Skill directory or SKILL.md file."""
    def validate_content(self, content: str, expected_dir_name: Optional[str] = None) -> List[Diagnostic]:
        frontmatter, err = parse_frontmatter(content)
        if err:
            return [Diagnostic("FRONTMATTER_PARSE_ERROR", "ERROR", err)]
        if frontmatter is None:
            return [Diagnostic("NO_FRONTMATTER", "ERROR", "No frontmatter found in file.")]
        return validate_skill_frontmatter(frontmatter, expected_dir_name=expected_dir_name)

    def validate_path(self, target_path: str) -> Tuple[List[Diagnostic], str]:
        resolved = os.path.abspath(target_path)
        if not os.path.exists(resolved):
            return [Diagnostic("FILE_NOT_FOUND", "ERROR", f"Target path '{target_path}' does not exist.")], resolved

        if os.path.isdir(resolved):
            skill_md = os.path.join(resolved, "SKILL.md")
            if not os.path.exists(skill_md):
                return [Diagnostic("MISSING_SKILL_MD", "ERROR", f"Required 'SKILL.md' not found in '{target_path}'.")], resolved
            expected_dir = os.path.basename(resolved)
            target_file = skill_md
        else:
            if not resolved.endswith(".md"):
                return [Diagnostic("INVALID_FILE_TYPE", "ERROR", f"Target file '{target_path}' must be a markdown file.")], resolved
            expected_dir = os.path.basename(os.path.dirname(resolved))
            target_file = resolved

        with open(target_file, "r", encoding="utf-8") as f:
            content = f.read()

        diagnostics = self.validate_content(content, expected_dir_name=expected_dir)
        return diagnostics, target_file


def format_cli_output(label: str, diagnostics: List[Diagnostic]) -> str:
    errors = [d for d in diagnostics if d.severity == "ERROR"]
    warnings = [d for d in diagnostics if d.severity == "WARNING"]

    if not errors and not warnings:
        return f"\033[92m✔ {label}: 0 violations found (standard frontmatter specification verified).\033[0m"

    lines = [f"\033[91m✖ {label}: {len(errors)} error(s), {len(warnings)} warning(s) found:\033[0m"]
    for d in diagnostics:
        color = "\033[91m" if d.severity == "ERROR" else "\033[93m"
        field_str = f" [{d.field}]" if d.field else ""
        lines.append(f"  {color}[{d.severity}][{d.rule_id}]{field_str}\033[0m {d.message}")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Agent Skill Frontmatter Validator")
    parser.add_argument("target", nargs="?", default="-", help="Path to skill directory, SKILL.md, or '-' for stdin")
    parser.add_argument("--json", action="store_true", help="Output machine-readable JSON diagnostics")
    parser.add_argument("--check", action="store_true", help="Stdin check mode")
    args = parser.parse_args()

    validator = SkillValidator()

    if args.target == "-" or args.check:
        content = sys.stdin.read()
        diagnostics = validator.validate_content(content)
        has_errors = any(d.severity == "ERROR" for d in diagnostics)

        if args.json:
            result = {
                "target": "stdin",
                "valid": not has_errors,
                "error_count": len([d for d in diagnostics if d.severity == "ERROR"]),
                "warning_count": len([d for d in diagnostics if d.severity == "WARNING"]),
                "diagnostics": [d.to_dict() for d in diagnostics],
            }
            print(json.dumps(result, indent=2))
        else:
            print(format_cli_output("stdin", diagnostics))

        sys.exit(1 if has_errors else 0)

    diagnostics, target_file = validator.validate_path(args.target)
    has_errors = any(d.severity == "ERROR" for d in diagnostics)

    if args.json:
        result = {
            "target": target_file,
            "valid": not has_errors,
            "error_count": len([d for d in diagnostics if d.severity == "ERROR"]),
            "warning_count": len([d for d in diagnostics if d.severity == "WARNING"]),
            "diagnostics": [d.to_dict() for d in diagnostics],
        }
        print(json.dumps(result, indent=2))
    else:
        rel_path = os.path.relpath(target_file, os.getcwd())
        print(format_cli_output(rel_path, diagnostics))

    sys.exit(1 if has_errors else 0)


if __name__ == "__main__":
    main()
