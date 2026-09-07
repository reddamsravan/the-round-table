#!/usr/bin/env python3
"""
QA Verification and Review Report Validator.

Validates QA review reports (e.g. docs/.prompts-and-prayers/sprints/sprint-1/05-reviews/{YYYY-MM-DD}_{slug}.md) for:
1. Frontmatter handover schema (sprint, persona: qa, status, handoff_to: scrum-master, artifacts).
2. Mandatory section structure (Test Evidence, 8-Concern Review Summary, Detailed Findings, Strengths).
3. Inclusion of all 8 concerns under Detailed Findings.
4. Deterministic zero-blocker invariant for APPROVED status.
"""

import sys
import os
import re
import json
import argparse
from typing import List, Dict, Any, Optional, Tuple

try:
    import yaml
except ImportError:
    yaml = None


VALID_STATUSES = {"DRAFT", "PENDING_APPROVAL", "APPROVED", "REJECTED"}

MANDATORY_CONCERNS = [
    "Design",
    "Functionality",
    "Complexity",
    "Tests",
    "Naming",
    "Comments",
    "Style",
    "Documentation",
]


class Diagnostic:
    def __init__(self, line: int, column: int, rule_id: str, severity: str, message: str, snippet: str = ""):
        self.line = line
        self.column = column
        self.rule_id = rule_id
        self.severity = severity
        self.message = message
        self.snippet = snippet

    def to_dict(self) -> Dict[str, Any]:
        return {
            "line": self.line,
            "column": self.column,
            "rule_id": self.rule_id,
            "severity": self.severity,
            "message": self.message,
            "snippet": self.snippet,
        }


class QAValidator:
    def __init__(self):
        self.diagnostics: List[Diagnostic] = []

    def validate_text(self, content: str, path: str) -> Tuple[List[Diagnostic], Dict[str, Any]]:
        self.diagnostics = []
        lines = content.splitlines()

        frontmatter, body_start_idx = self._parse_frontmatter(lines)
        metadata = self._validate_frontmatter(frontmatter, path)
        self._validate_required_sections(lines, path)
        self._validate_concerns(content, path)

        # Blocker check
        blocker_count = len(re.findall(r"\[BLOCKER\]", content, re.IGNORECASE))
        has_needs_changes = "NEEDS CHANGES" in content

        if metadata.get("status") == "APPROVED":
            if blocker_count > 0:
                self.diagnostics.append(
                    Diagnostic(
                        1, 1, "UNRESOLVED_BLOCKERS_PRESENT", "ERROR",
                        f"Report cannot have status 'APPROVED' with {blocker_count} unresolved [BLOCKER] findings."
                    )
                )
            if has_needs_changes:
                self.diagnostics.append(
                    Diagnostic(
                        1, 1, "INVALID_APPROVED_VERDICT", "ERROR",
                        "Report cannot have status 'APPROVED' while verdict is 'NEEDS CHANGES'."
                    )
                )

        summary = {
            "sprint": metadata.get("sprint", "unknown"),
            "status": metadata.get("status", "unknown"),
            "persona": metadata.get("persona", "unknown"),
            "blockers_found": blocker_count,
            "approved": metadata.get("status") == "APPROVED" and blocker_count == 0,
        }

        return self.diagnostics, summary

    def _parse_frontmatter(self, lines: List[str]) -> Tuple[Optional[str], int]:
        if not lines or lines[0].strip() != "---":
            self.diagnostics.append(
                Diagnostic(1, 1, "FRONTMATTER_MISSING", "ERROR", "Document MUST start with YAML frontmatter delimiter '---'.")
            )
            return None, 0

        end_idx = -1
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                end_idx = i
                break

        if end_idx == -1:
            self.diagnostics.append(
                Diagnostic(1, 1, "FRONTMATTER_UNCLOSED", "ERROR", "Frontmatter delimiter '---' is unclosed.")
            )
            return None, 0

        yaml_text = "\n".join(lines[1:end_idx])
        return yaml_text, end_idx + 1

    def _validate_frontmatter(self, yaml_text: Optional[str], path: str) -> Dict[str, Any]:
        if not yaml_text:
            return {}

        data = {}
        if yaml is not None:
            try:
                data = yaml.safe_load(yaml_text) or {}
            except Exception as e:
                self.diagnostics.append(
                    Diagnostic(1, 1, "YAML_SYNTAX_ERROR", "ERROR", f"Invalid YAML: {e}")
                )
        else:
            for l in yaml_text.splitlines():
                if ":" in l:
                    k, v = l.split(":", 1)
                    data[k.strip()] = v.strip().strip('"').strip("'")

        req_keys = ["sprint", "persona", "status", "handoff_to", "artifacts"]
        for rk in req_keys:
            if rk not in data:
                self.diagnostics.append(
                    Diagnostic(1, 1, "SCHEMA_MISSING_KEY", "ERROR", f"Missing mandatory key '{rk}'.")
                )

        if data.get("persona") != "qa":
            self.diagnostics.append(
                Diagnostic(1, 1, "SCHEMA_INVALID_PERSONA", "ERROR", f"Persona must be 'qa', found '{data.get('persona')}'.")
            )

        status = data.get("status")
        if status not in VALID_STATUSES:
            self.diagnostics.append(
                Diagnostic(1, 1, "SCHEMA_INVALID_STATUS", "ERROR", f"Status must be in {sorted(VALID_STATUSES)}, found '{status}'.")
            )

        if data.get("handoff_to") != "scrum-master":
            self.diagnostics.append(
                Diagnostic(1, 1, "SCHEMA_INVALID_HANDOFF", "ERROR", f"Handoff must be 'scrum-master', found '{data.get('handoff_to')}'.")
            )

        return data

    def _validate_required_sections(self, lines: List[str], path: str):
        headings = [l.strip() for l in lines if l.startswith("#")]
        required_patterns = [
            (r"^#\s+QA Verification & Code Review Report:", "Title '# QA Verification & Code Review Report: <Title>'"),
            (r"^##\s+1\.\s+Automated Test Execution Evidence", "Section '## 1. Automated Test Execution Evidence'"),
            (r"^##\s+2\.\s+8-Concern Code Review Summary", "Section '## 2. 8-Concern Code Review Summary'"),
            (r"^##\s+3\.\s+Detailed Findings", "Section '## 3. Detailed Findings'"),
            (r"^##\s+4\.\s+Strengths & Positive Observations", "Section '## 4. Strengths & Positive Observations'"),
        ]
        for pat, label in required_patterns:
            if not any(re.search(pat, h) for h in headings):
                self.diagnostics.append(
                    Diagnostic(1, 1, "STRUCTURE_MISSING_SECTION", "ERROR", f"Report missing section: {label}.")
                )

    def _validate_concerns(self, content: str, path: str):
        for c in MANDATORY_CONCERNS:
            pattern = rf"^###\s+{c}\b"
            if not re.search(pattern, content, re.MULTILINE):
                self.diagnostics.append(
                    Diagnostic(1, 1, "MISSING_CONCERN_HEADING", "ERROR", f"Section 3 missing concern heading: '### {c}'.")
                )


def format_cli_output(target: str, diagnostics: List[Diagnostic], summary: Dict[str, Any]) -> str:
    errors = [d for d in diagnostics if d.severity == "ERROR"]
    warnings = [d for d in diagnostics if d.severity == "WARNING"]
    lines = []
    lines.append("=" * 70)
    lines.append(f"QA VERIFICATION & REVIEW VALIDATOR: {target}")
    lines.append("=" * 70)
    for k, v in summary.items():
        lines.append(f"{k.capitalize():18}: {v}")
    lines.append("-" * 70)

    if errors:
        lines.append(f"ERRORS ({len(errors)}):")
        for e in errors:
            lines.append(f"  [Line {e.line}] {e.rule_id}: {e.message}")
            if e.snippet:
                lines.append(f"    Snippet: {e.snippet}")
    else:
        lines.append("No errors found. QA report specification is clean!")

    if warnings:
        lines.append(f"WARNINGS ({len(warnings)}):")
        for w in warnings:
            lines.append(f"  [Line {w.line}] {w.rule_id}: {w.message}")

    lines.append("=" * 70)
    lines.append("RESULT: " + ("PASS" if len(errors) == 0 else "FAIL"))
    lines.append("=" * 70)
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="QA Verification and Review Report Validator")
    parser.add_argument("target", nargs="?", default=None, help="Target QA report file to validate")
    parser.add_argument("--sprint", "-s", type=str, default=None, help="Sprint identifier (e.g. sprint-1)")
    parser.add_argument("--all", action="store_true", help="Run all checks (default)")
    parser.add_argument("--json", action="store_true", help="Output machine-readable JSON results")

    args = parser.parse_args()

    target_file = None
    if args.target:
        cand = os.path.abspath(args.target)
        if os.path.isfile(cand):
            target_file = cand
        elif os.path.isdir(cand):
            reviews_dir = os.path.join(cand, "05-reviews")
            if os.path.isdir(reviews_dir):
                files = sorted([f for f in os.listdir(reviews_dir) if f.endswith(".md")], reverse=True)
                if files:
                    target_file = os.path.join(reviews_dir, files[0])

    if target_file is None:
        sprint = args.sprint
        if not sprint:
            sprints_root = os.path.join(os.getcwd(), "docs", ".prompts-and-prayers", "sprints")
            if os.path.isdir(sprints_root):
                entries = sorted([d for d in os.listdir(sprints_root) if os.path.isdir(os.path.join(sprints_root, d))], reverse=True)
                if entries:
                    sprint = entries[0]
        if sprint:
            reviews_dir = os.path.join(os.getcwd(), "docs", ".prompts-and-prayers", "sprints", sprint, "05-reviews")
            if os.path.isdir(reviews_dir):
                files = sorted([f for f in os.listdir(reviews_dir) if f.endswith(".md")], reverse=True)
                if files:
                    target_file = os.path.join(reviews_dir, files[0])

    if target_file is None:
        target_file = "-"

    validator = QAValidator()

    if target_file == "-":
        content = sys.stdin.read()
        diags, summary = validator.validate_text(content, "stdin")
        error_count = len([d for d in diags if d.severity == "ERROR"])
        warn_count = len([d for d in diags if d.severity == "WARNING"])
        if args.json:
            print(json.dumps({
                "target": "stdin",
                "valid": error_count == 0,
                "error_count": error_count,
                "warning_count": warn_count,
                "summary": summary,
                "errors": [d.to_dict() for d in diags]
            }, indent=2))
        else:
            print(format_cli_output("stdin", diags, summary))
        sys.exit(1 if error_count > 0 else 0)

    if not os.path.exists(target_file):
        sys.stderr.write(f"Error: Target file '{target_file}' does not exist.\n")
        sys.exit(2)

    with open(target_file, "r", encoding="utf-8") as f:
        content = f.read()

    diags, summary = validator.validate_text(content, target_file)
    error_count = len([d for d in diags if d.severity == "ERROR"])
    warn_count = len([d for d in diags if d.severity == "WARNING"])

    if args.json:
        print(json.dumps({
            "total_files": 1,
            "clean_files": 1 if error_count == 0 else 0,
            "results": [
                {
                    "file": target_file,
                    "valid": error_count == 0,
                    "error_count": error_count,
                    "warning_count": warn_count,
                    "summary": summary,
                    "errors": [d.to_dict() for d in diags]
                }
            ]
        }, indent=2))
    else:
        print(format_cli_output(os.path.relpath(target_file), diags, summary))

    sys.exit(1 if error_count > 0 else 0)


if __name__ == "__main__":
    main()
