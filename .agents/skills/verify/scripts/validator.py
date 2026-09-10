#!/usr/bin/env python3
"""
Verify Skill Verification and Review Report Validator.

Validates verification reports (e.g. docs/.prompts-and-prayers/{work_slug}/05-verify/verification-report.md) for:
1. Frontmatter envelope (slug, status, approved_by, artifacts).
2. Strict document heading '# Verification Report: <Title>'.
3. Mandatory section structure in sequential order.
4. Mandatory inclusion of all eight review concerns under Detailed Findings.
5. Deterministic zero-blocker and passing verdict invariants for APPROVED status.
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
    def __init__(self, line: int, column: int, rule_id: str, severity: str, message: str, snippet: str = "", file_name: str = ""):
        self.line = line
        self.column = column
        self.rule_id = rule_id
        self.severity = severity
        self.message = message
        self.snippet = snippet
        self.file_name = file_name

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file": self.file_name,
            "line": self.line,
            "column": self.column,
            "rule_id": self.rule_id,
            "severity": self.severity,
            "message": self.message,
            "snippet": self.snippet,
        }


class VerifyValidator:
    def __init__(self):
        self.diagnostics: List[Diagnostic] = []

    def validate_text(self, content: str, path: str = "verification-report.md") -> Tuple[List[Diagnostic], Dict[str, Any]]:
        self.diagnostics = []
        lines = content.splitlines()

        # 1. Frontmatter
        frontmatter, _ = self._parse_frontmatter(lines, path)
        metadata = self._validate_frontmatter(frontmatter, path)

        # 2. Structure & Sections
        self._validate_required_sections(lines, path)

        # 3. 8 Review Concerns
        self._validate_concerns(content, path)

        # 4. Check ASCII art
        self._check_for_ascii_art(lines, path)

        # 5. Zero-Blocker & Verdict Invariants
        blocker_count = len(re.findall(r"\[BLOCKER\]", content, re.IGNORECASE))
        has_needs_changes = "NEEDS CHANGES" in content

        if metadata.get("status") == "APPROVED":
            if blocker_count > 0:
                self.diagnostics.append(
                    Diagnostic(
                        1, 1, "UNRESOLVED_BLOCKERS_PRESENT", "ERROR",
                        f"Report cannot have status 'APPROVED' with {blocker_count} unresolved [BLOCKER] findings.",
                        file_name=path
                    )
                )
            if has_needs_changes:
                self.diagnostics.append(
                    Diagnostic(
                        1, 1, "INVALID_APPROVED_VERDICT", "ERROR",
                        "Report cannot have status 'APPROVED' while verdict is 'NEEDS CHANGES'.",
                        file_name=path
                    )
                )

        summary = {
            "slug": metadata.get("slug", "unknown"),
            "status": metadata.get("status", "unknown"),
            "approved_by": metadata.get("approved_by", "unknown"),
            "blockers_found": blocker_count,
            "approved": metadata.get("status") == "APPROVED" and blocker_count == 0 and not has_needs_changes,
        }

        return self.diagnostics, summary

    def validate_verify_dir(self, verify_dir: str) -> Tuple[List[Diagnostic], Dict[str, Any]]:
        self.diagnostics = []
        summary: Dict[str, Any] = {
            "verify_dir": verify_dir,
            "slug": "unknown",
            "status": "unknown",
            "approved_by": "unknown",
            "blockers_found": 0,
            "approved": False,
        }

        target_path = os.path.join(verify_dir, "verification-report.md")
        if not os.path.exists(target_path):
            fallback = os.path.join(verify_dir, "report.md")
            if os.path.exists(fallback):
                target_path = fallback
            else:
                self.diagnostics.append(
                    Diagnostic(1, 1, "VERIFICATION_REPORT_NOT_FOUND", "ERROR", f"File '{target_path}' does not exist.", file_name=target_path)
                )
                return self.diagnostics, summary

        with open(target_path, "r", encoding="utf-8") as f:
            content = f.read()

        return self.validate_text(content, target_path)

    def _parse_frontmatter(self, lines: List[str], path: str) -> Tuple[Optional[str], int]:
        if not lines or lines[0].strip() != "---":
            self.diagnostics.append(
                Diagnostic(1, 1, "FRONTMATTER_MISSING", "ERROR", "Document MUST start with YAML frontmatter delimiter '---'.", file_name=path)
            )
            return None, 0

        end_idx = -1
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                end_idx = i
                break

        if end_idx == -1:
            self.diagnostics.append(
                Diagnostic(1, 1, "FRONTMATTER_UNCLOSED", "ERROR", "Frontmatter delimiter '---' is unclosed.", file_name=path)
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
                    Diagnostic(1, 1, "YAML_SYNTAX_ERROR", "ERROR", f"Invalid YAML: {e}", file_name=path)
                )
        else:
            for l in yaml_text.splitlines():
                if ":" in l:
                    k, v = l.split(":", 1)
                    data[k.strip()] = v.strip().strip('"').strip("'")

        req_keys = ["slug", "status", "approved_by", "artifacts"]
        for rk in req_keys:
            if rk not in data:
                self.diagnostics.append(
                    Diagnostic(1, 1, "SCHEMA_MISSING_KEY", "ERROR", f"Missing mandatory key '{rk}'.", file_name=path)
                )

        status = data.get("status")
        if status and status not in VALID_STATUSES:
            self.diagnostics.append(
                Diagnostic(1, 1, "SCHEMA_INVALID_STATUS", "ERROR", f"Frontmatter 'status' must be one of {sorted(VALID_STATUSES)}, found '{status}'.", file_name=path)
            )

        approved_by = data.get("approved_by")
        if approved_by and approved_by not in {"pending", "human"}:
            self.diagnostics.append(
                Diagnostic(1, 1, "SCHEMA_INVALID_APPROVED_BY", "ERROR", f"Frontmatter 'approved_by' must be 'pending' or 'human', found '{approved_by}'.", file_name=path)
            )

        artifacts = data.get("artifacts")
        if "artifacts" in data:
            if not isinstance(artifacts, list) or len(artifacts) == 0:
                self.diagnostics.append(
                    Diagnostic(1, 1, "SCHEMA_INVALID_ARTIFACTS", "ERROR", "Frontmatter 'artifacts' must be a non-empty list.", file_name=path)
                )

        return data

    def _validate_required_sections(self, lines: List[str], path: str):
        required_patterns = [
            (r"^#\s+Verification Report:\s*.+", "Title '# Verification Report: <Title>'"),
            (r"^##\s+1\.\s+Automated Test Execution Evidence", "Section '## 1. Automated Test Execution Evidence'"),
            (r"^##\s+2\.\s+8-Concern Code Review Summary", "Section '## 2. 8-Concern Code Review Summary'"),
            (r"^##\s+3\.\s+Detailed Findings", "Section '## 3. Detailed Findings'"),
            (r"^##\s+4\.\s+Strengths & Positive Observations", "Section '## 4. Strengths & Positive Observations'"),
        ]

        found_indices = []
        for pat, label in required_patterns:
            matched_line = None
            for idx, line in enumerate(lines, start=1):
                if re.search(pat, line.strip()):
                    matched_line = idx
                    break
            if matched_line is None:
                self.diagnostics.append(
                    Diagnostic(1, 1, "STRUCTURE_MISSING_SECTION", "ERROR", f"Report missing section: {label}.", file_name=path)
                )
            else:
                found_indices.append(matched_line)

        if len(found_indices) == len(required_patterns):
            if found_indices != sorted(found_indices):
                self.diagnostics.append(
                    Diagnostic(1, 1, "SECTION_ORDER_INVALID", "ERROR", "Sections in verification-report.md appear out of sequential order.", file_name=path)
                )

    def _validate_concerns(self, content: str, path: str):
        for c in MANDATORY_CONCERNS:
            pattern = rf"^###\s+{c}\b"
            if not re.search(pattern, content, re.MULTILINE):
                self.diagnostics.append(
                    Diagnostic(1, 1, "MISSING_CONCERN_HEADING", "ERROR", f"Section 3 missing concern heading: '### {c}'.", file_name=path)
                )

    def _check_for_ascii_art(self, lines: List[str], path: str):
        ascii_box_re = re.compile(r"(\+[-=]{3,}\+|\|={3,}\||\+---+|┌─+┐|└─+┘|├───┤)")
        in_code = False
        for idx, line in enumerate(lines, start=1):
            s = line.strip()
            if s.startswith("```"):
                in_code = not in_code
                continue
            if in_code:
                continue

            # Skip standard markdown table row delimiters like |---|---|
            if re.match(r"^\|?(\s*:?-+:?\s*\|)+\s*:?-+:?\s*\|?$", s):
                continue

            if s.startswith("+--") or s.startswith("+==") or ascii_box_re.search(line):
                self.diagnostics.append(
                    Diagnostic(
                        idx, 1, "FORBIDDEN_ASCII_ART", "ERROR",
                        "ASCII art box diagrams are forbidden. Use plain text descriptions and Mermaid diagrams.",
                        snippet=line, file_name=path
                    )
                )


def format_cli_output(target: str, diagnostics: List[Diagnostic], summary: Dict[str, Any]) -> str:
    errors = [d for d in diagnostics if d.severity == "ERROR"]
    warnings = [d for d in diagnostics if d.severity == "WARNING"]
    lines = []
    lines.append("=" * 70)
    lines.append(f"VERIFY REPORT VALIDATOR: {target}")
    lines.append("=" * 70)
    for k, v in summary.items():
        lines.append(f"{k.capitalize():18}: {v}")
    lines.append("-" * 70)

    if errors:
        lines.append(f"ERRORS ({len(errors)}):")
        for e in errors:
            fname = os.path.basename(e.file_name) if e.file_name else "file"
            lines.append(f"  [{fname}:Line {e.line}] {e.rule_id}: {e.message}")
            if e.snippet:
                lines.append(f"    Snippet: {e.snippet}")
    else:
        lines.append("No errors found. Verification report is clean!")

    if warnings:
        lines.append(f"WARNINGS ({len(warnings)}):")
        for w in warnings:
            fname = os.path.basename(w.file_name) if w.file_name else "file"
            lines.append(f"  [{fname}:Line {w.line}] {w.rule_id}: {w.message}")

    lines.append("=" * 70)
    lines.append("RESULT: " + ("PASS" if len(errors) == 0 else "FAIL"))
    lines.append("=" * 70)
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Verify Verification and Review Report Validator")
    parser.add_argument("target", nargs="?", default=None, help="Target verification report file or 05-verify directory")
    parser.add_argument("--slug", "-s", type=str, default=None, help="Work slug identifier")
    parser.add_argument("--all", action="store_true", help="Run all checks (default)")
    parser.add_argument("--json", action="store_true", help="Output machine-readable JSON results")

    args = parser.parse_args()

    target_path = None
    target_dir = None

    if args.slug:
        cand = os.path.join(os.getcwd(), "docs", ".prompts-and-prayers", args.slug, "05-verify")
        if os.path.isdir(cand):
            target_dir = cand

    if args.target and not target_dir:
        resolved = os.path.abspath(args.target)
        if os.path.isdir(resolved):
            target_dir = resolved
        elif os.path.isfile(resolved):
            target_path = resolved
        elif args.target == "-":
            target_path = "-"
        else:
            sys.stderr.write(f"Error: Target '{args.target}' does not exist.\n")
            sys.exit(2)

    validator = VerifyValidator()

    if target_path == "-":
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

    if target_path:
        with open(target_path, "r", encoding="utf-8") as f:
            content = f.read()
        diags, summary = validator.validate_text(content, target_path)
        error_count = len([d for d in diags if d.severity == "ERROR"])
        warn_count = len([d for d in diags if d.severity == "WARNING"])
        if args.json:
            print(json.dumps({
                "target": target_path,
                "valid": error_count == 0,
                "error_count": error_count,
                "warning_count": warn_count,
                "summary": summary,
                "errors": [d.to_dict() for d in diags]
            }, indent=2))
        else:
            print(format_cli_output(target_path, diags, summary))
        sys.exit(1 if error_count > 0 else 0)

    if target_dir is None:
        base_dir = os.path.join(os.getcwd(), "docs", ".prompts-and-prayers")
        if os.path.isdir(base_dir):
            entries = sorted([d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))], reverse=True)
            for entry in entries:
                cand = os.path.join(base_dir, entry, "05-verify")
                if os.path.isdir(cand):
                    target_dir = cand
                    break

    if target_dir is None:
        sys.stderr.write("Error: Could not locate 05-verify directory.\n")
        sys.exit(2)

    diags, summary = validator.validate_verify_dir(target_dir)
    error_count = len([d for d in diags if d.severity == "ERROR"])
    warn_count = len([d for d in diags if d.severity == "WARNING"])

    if args.json:
        print(json.dumps({
            "target": target_dir,
            "valid": error_count == 0,
            "error_count": error_count,
            "warning_count": warn_count,
            "summary": summary,
            "errors": [d.to_dict() for d in diags]
        }, indent=2))
    else:
        print(format_cli_output(target_dir, diags, summary))

    sys.exit(1 if error_count > 0 else 0)


if __name__ == "__main__":
    main()
