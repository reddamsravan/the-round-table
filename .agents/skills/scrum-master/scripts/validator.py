#!/usr/bin/env python3
"""
Scrum Master Release and Retrospective Validator.

Validates:
1. docs/.prompts-and-prayers/sprints/sprint-{N}/06-release/release-notes.md (frontmatter schema, sections, commit log).
2. docs/.prompts-and-prayers/sprints/sprint-{N}/06-release/retrospective.md (metrics, retrospectives, action items).
3. Pre-release sprint integrity (all tasks in 04-tasks/plan.md are terminal DONE/ABORTED, QA report is APPROVED).
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


class ScrumMasterValidator:
    def __init__(self):
        self.diagnostics: List[Diagnostic] = []

    def validate_sprint(
        self,
        sprint_dir: str,
        check_release: bool = True,
        check_retro: bool = True,
        check_prereqs: bool = True,
    ) -> Tuple[List[Diagnostic], Dict[str, Any]]:
        self.diagnostics = []

        release_file = os.path.join(sprint_dir, "06-release", "release-notes.md")
        retro_file = os.path.join(sprint_dir, "06-release", "retrospective.md")
        plan_file = os.path.join(sprint_dir, "04-tasks", "plan.md")
        reviews_dir = os.path.join(sprint_dir, "05-reviews")

        meta = {}
        if check_release:
            if not os.path.exists(release_file):
                self.diagnostics.append(
                    Diagnostic(1, 1, "RELEASE_NOTES_MISSING", "ERROR", f"File '{release_file}' does not exist.", file_name=release_file)
                )
            else:
                with open(release_file, "r", encoding="utf-8") as f:
                    content = f.read()
                meta = self._validate_release_notes(content, release_file)

        if check_retro:
            if not os.path.exists(retro_file):
                self.diagnostics.append(
                    Diagnostic(1, 1, "RETROSPECTIVE_MISSING", "ERROR", f"File '{retro_file}' does not exist.", file_name=retro_file)
                )
            else:
                with open(retro_file, "r", encoding="utf-8") as f:
                    content = f.read()
                self._validate_retrospective(content, retro_file)

        if check_prereqs:
            self._validate_prerequisites(plan_file, reviews_dir)

        summary = {
            "sprint_dir": sprint_dir,
            "sprint": meta.get("sprint", "unknown"),
            "status": meta.get("status", "unknown"),
            "persona": meta.get("persona", "unknown"),
        }
        return self.diagnostics, summary

    def _validate_release_notes(self, content: str, path: str) -> Dict[str, Any]:
        lines = content.splitlines()

        # Frontmatter
        if not lines or lines[0].strip() != "---":
            self.diagnostics.append(
                Diagnostic(1, 1, "FRONTMATTER_MISSING", "ERROR", "Release notes MUST start with '---'.", file_name=path)
            )
            return {}

        end_idx = -1
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                end_idx = i
                break

        if end_idx == -1:
            self.diagnostics.append(
                Diagnostic(1, 1, "FRONTMATTER_UNCLOSED", "ERROR", "Frontmatter delimiter is unclosed.", file_name=path)
            )
            return {}

        yaml_text = "\n".join(lines[1:end_idx])
        meta = {}
        if yaml is not None:
            try:
                meta = yaml.safe_load(yaml_text) or {}
            except Exception as e:
                self.diagnostics.append(
                    Diagnostic(1, 1, "YAML_SYNTAX_ERROR", "ERROR", f"Invalid YAML: {e}", file_name=path)
                )
        else:
            for l in yaml_text.splitlines():
                if ":" in l:
                    k, v = l.split(":", 1)
                    meta[k.strip()] = v.strip().strip('"').strip("'")

        req_keys = ["sprint", "persona", "status", "handoff_to", "artifacts"]
        for rk in req_keys:
            if rk not in meta:
                self.diagnostics.append(
                    Diagnostic(1, 1, "SCHEMA_MISSING_KEY", "ERROR", f"Missing key '{rk}'.", file_name=path)
                )

        if meta.get("persona") != "scrum-master":
            self.diagnostics.append(
                Diagnostic(1, 1, "SCHEMA_INVALID_PERSONA", "ERROR", f"Persona must be 'scrum-master', found '{meta.get('persona')}'.", file_name=path)
            )

        headings = [l.strip() for l in lines if l.startswith("#")]
        required_patterns = [
            (r"^#\s+Sprint Release Notes:", "Title '# Sprint Release Notes: <Title>'"),
            (r"^##\s+1\.\s+Release Summary", "Section '## 1. Release Summary'"),
            (r"^##\s+2\.\s+Delivered Features & User Stories", "Section '## 2. Delivered Features & User Stories'"),
            (r"^##\s+3\.\s+Conventional Commit Log", "Section '## 3. Conventional Commit Log'"),
            (r"^##\s+4\.\s+Verification Signoff", "Section '## 4. Verification Signoff'"),
        ]
        for pat, label in required_patterns:
            if not any(re.search(pat, h) for h in headings):
                self.diagnostics.append(
                    Diagnostic(1, 1, "STRUCTURE_MISSING_SECTION", "ERROR", f"Release notes missing section: {label}.", file_name=path)
                )

        return meta

    def _validate_retrospective(self, content: str, path: str):
        lines = content.splitlines()
        headings = [l.strip() for l in lines if l.startswith("#")]
        required_patterns = [
            (r"^#\s+Sprint Retrospective:", "Title '# Sprint Retrospective: <Title>'"),
            (r"^##\s+1\.\s+Sprint Execution Metrics", "Section '## 1. Sprint Execution Metrics'"),
            (r"^##\s+2\.\s+What Went Well", "Section '## 2. What Went Well'"),
            (r"^##\s+3\.\s+Opportunities for Improvement", "Section '## 3. Opportunities for Improvement'"),
            (r"^##\s+4\.\s+Action Items for Next Sprint", "Section '## 4. Action Items for Next Sprint'"),
        ]
        for pat, label in required_patterns:
            if not any(re.search(pat, h) for h in headings):
                self.diagnostics.append(
                    Diagnostic(1, 1, "STRUCTURE_MISSING_SECTION", "ERROR", f"Retrospective missing section: {label}.", file_name=path)
                )

    def _validate_prerequisites(self, plan_file: str, reviews_dir: str):
        # 1. Plan tasks completion
        if os.path.exists(plan_file):
            with open(plan_file, "r", encoding="utf-8") as f:
                content = f.read()
            # Find all task statuses in plan.md
            statuses = re.findall(r"status:\s*([A-Za-z_]+)", content)
            non_terminal = [s for s in statuses if s not in ("DONE", "ABORTED")]
            if non_terminal:
                self.diagnostics.append(
                    Diagnostic(
                        1, 1, "UNFINISHED_PLAN_TASKS", "ERROR",
                        f"Cannot release sprint: {len(non_terminal)} plan tasks are not DONE ({', '.join(non_terminal)}).",
                        file_name=plan_file
                    )
                )

        # 2. QA review report approval
        if os.path.isdir(reviews_dir):
            files = sorted([f for f in os.listdir(reviews_dir) if f.endswith(".md")], reverse=True)
            if not files:
                self.diagnostics.append(
                    Diagnostic(1, 1, "QA_REPORT_MISSING", "ERROR", "No QA review reports found in 05-reviews/.")
                )
            else:
                latest_report = os.path.join(reviews_dir, files[0])
                with open(latest_report, "r", encoding="utf-8") as f:
                    rep_content = f.read()
                if "status: APPROVED" not in rep_content:
                    self.diagnostics.append(
                        Diagnostic(
                            1, 1, "QA_NOT_APPROVED", "ERROR",
                            f"Latest QA report '{files[0]}' does not have status: APPROVED.",
                            file_name=latest_report
                        )
                    )


def format_cli_output(sprint_dir: str, diagnostics: List[Diagnostic], summary: Dict[str, Any]) -> str:
    errors = [d for d in diagnostics if d.severity == "ERROR"]
    warnings = [d for d in diagnostics if d.severity == "WARNING"]
    lines = []
    lines.append("=" * 70)
    lines.append(f"SCRUM MASTER RELEASE VALIDATOR: {sprint_dir}")
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
        lines.append("No errors found. Sprint release artifacts and prerequisites are clean!")

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
    parser = argparse.ArgumentParser(description="Scrum Master Release and Retrospective Validator")
    parser.add_argument("target", nargs="?", default=None, help="Target sprint directory or file")
    parser.add_argument("--sprint", "-s", type=str, default=None, help="Sprint identifier (e.g. sprint-1)")
    parser.add_argument("--check-release", action="store_true", help="Validate release-notes.md only")
    parser.add_argument("--check-retro", action="store_true", help="Validate retrospective.md only")
    parser.add_argument("--check-prereqs", action="store_true", help="Validate plan completion and QA approval only")
    parser.add_argument("--all", action="store_true", help="Run all checks (default)")
    parser.add_argument("--json", action="store_true", help="Output machine-readable JSON results")

    args = parser.parse_args()

    run_release = True
    run_retro = True
    run_prereqs = True

    if args.check_release or args.check_retro or args.check_prereqs:
        run_release = args.check_release
        run_retro = args.check_retro
        run_prereqs = args.check_prereqs

    sprint_dir = None
    if args.sprint:
        cand = os.path.join(os.getcwd(), "docs", ".prompts-and-prayers", "sprints", args.sprint)
        if os.path.isdir(cand):
            sprint_dir = cand
    elif args.target:
        cand = os.path.abspath(args.target)
        if os.path.isdir(cand):
            sprint_dir = cand
        elif os.path.isfile(cand):
            p = cand
            while p and os.path.dirname(p) != p:
                if os.path.basename(os.path.dirname(p)) == "sprints":
                    sprint_dir = p
                    break
                p = os.path.dirname(p)

    if sprint_dir is None:
        sprints_root = os.path.join(os.getcwd(), "docs", ".prompts-and-prayers", "sprints")
        if os.path.isdir(sprints_root):
            entries = sorted([d for d in os.listdir(sprints_root) if os.path.isdir(os.path.join(sprints_root, d))], reverse=True)
            for sp in entries:
                sprint_dir = os.path.join(sprints_root, sp)
                break

    if sprint_dir is None:
        sys.stderr.write("Error: Could not locate active sprint directory.\n")
        sys.exit(2)

    validator = ScrumMasterValidator()
    diags, summary = validator.validate_sprint(
        sprint_dir, check_release=run_release, check_retro=run_retro, check_prereqs=run_prereqs
    )

    error_count = len([d for d in diags if d.severity == "ERROR"])
    warn_count = len([d for d in diags if d.severity == "WARNING"])

    if args.json:
        print(json.dumps({
            "target": sprint_dir,
            "valid": error_count == 0,
            "error_count": error_count,
            "warning_count": warn_count,
            "summary": summary,
            "errors": [d.to_dict() for d in diags]
        }, indent=2))
    else:
        print(format_cli_output(os.path.relpath(sprint_dir), diags, summary))

    sys.exit(1 if error_count > 0 else 0)


if __name__ == "__main__":
    main()
