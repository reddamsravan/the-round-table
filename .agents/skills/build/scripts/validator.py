#!/usr/bin/env python3
"""
Build Skill Task and Summary Validator.

Validates:
1. docs/.prompts-and-prayers/{work_slug}/04-build/active.md (or docs/.tasks/active.md)
   for single in-flight atomic task rules (effort <= 4.0h, verify_cmd, ACE criteria).
2. docs/.prompts-and-prayers/{work_slug}/04-build/build-summary.md
   for frontmatter envelope (slug, status, approved_by, artifacts) and mandatory sections.
"""

import sys
import os
import re
import json
import argparse
from typing import List, Dict, Any, Optional, Tuple, Set

try:
    import yaml
except ImportError:
    yaml = None


VALID_STATUSES = {"DRAFT", "PENDING_APPROVAL", "APPROVED", "REJECTED"}
VALID_TASK_STATUSES = {"TODO", "IN_PROGRESS", "VERIFYING", "DONE"}

FORBIDDEN_MODALS = {
    "should": "SHALL or MUST",
    "shouldn't": "SHALL NOT or MUST NOT",
    "should not": "SHALL NOT or MUST NOT",
    "could": "can or SHALL",
    "couldn't": "SHALL NOT or MUST NOT",
    "might": "MAY or explicit conditional",
    "would": "SHALL",
    "may": "is permitted to or explicit conditional",
    "probably": "specify exact condition",
    "possibly": "specify exact condition",
    "maybe": "specify exact condition",
    "perhaps": "specify exact condition",
    "ought": "SHALL or MUST",
}

FORBIDDEN_AMBIGUOUS_WORDS = {
    "appropriate": "specify concrete criteria",
    "various": "specify exact items or count",
    "fast": "specify exact latency threshold",
    "slow": "specify exact latency threshold",
    "user-friendly": "specify exact interface behavior",
    "easy": "specify operational steps",
    "simple": "specify operational steps",
    "complex": "describe specific components",
    "roughly": "specify exact quantity",
    "approximately": "specify exact quantity",
    "basically": "remove filler word",
    "etc": "enumerate all required items",
    "etc.": "enumerate all required items",
    "and so on": "enumerate all required items",
}

IRREGULAR_PAST_PARTICIPLES = {
    "been", "done", "written", "given", "taken", "seen", "made", "built", "sent",
    "run", "read", "set", "cut", "put", "chosen", "drawn", "driven", "eaten",
    "fallen", "found", "gotten", "got", "held", "kept", "known", "led", "left",
    "lost", "paid", "said", "sold", "spent", "told", "understood", "won", "broken",
    "executed", "parsed", "processed", "triggered", "created", "deleted", "modified",
    "invoked", "called", "emitted", "evaluated", "checked", "rendered", "updated"
}


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


class BuildValidator:
    def __init__(self):
        self.diagnostics: List[Diagnostic] = []

    def validate_active_task(self, content: str, path: str = "active.md") -> Tuple[List[Diagnostic], Dict[str, Any]]:
        self.diagnostics = []
        lines = content.splitlines()

        task_headings = [l.strip() for l in lines if re.match(r"^###\s+Task:\s+TASK-\d+", l.strip())]
        if len(task_headings) > 1:
            self.diagnostics.append(
                Diagnostic(
                    1, 1, "MULTIPLE_ACTIVE_TASKS", "ERROR",
                    f"Active task document MUST contain at most one in-flight atomic task. Found {len(task_headings)}.",
                    file_name=path
                )
            )

        task_data = None
        in_yaml = False
        yaml_lines = []
        start_line = 0

        for idx, line in enumerate(lines, start=1):
            s = line.strip()
            if re.match(r"^###\s+Task:\s+(TASK-\d+)", s):
                start_line = idx
                continue
            if s.startswith("```yaml") and not in_yaml:
                in_yaml = True
                continue
            elif s.startswith("```") and in_yaml:
                in_yaml = False
                yaml_text = "\n".join(yaml_lines)
                try:
                    if yaml is not None:
                        task_data = yaml.safe_load(yaml_text) or {}
                    else:
                        task_data = {}
                        for l in yaml_lines:
                            if ":" in l:
                                k, v = l.split(":", 1)
                                task_data[k.strip()] = v.strip().strip('"').strip("'")
                except Exception as e:
                    self.diagnostics.append(
                        Diagnostic(start_line, 1, "YAML_SYNTAX_ERROR", "ERROR", f"Invalid YAML: {e}", file_name=path)
                    )
                break
            if in_yaml:
                yaml_lines.append(line)

        effort_val = None
        if task_data:
            req_keys = ["id", "parent_plan_id", "title", "status", "effort_hours", "verify_cmd", "acceptance_criteria"]
            for rk in req_keys:
                if rk not in task_data:
                    self.diagnostics.append(
                        Diagnostic(start_line, 1, "TASK_MISSING_KEY", "ERROR", f"Atomic task missing mandatory key '{rk}'.", file_name=path)
                    )

            effort = task_data.get("effort_hours")
            try:
                effort_val = float(effort)
                if effort_val > 4.0:
                    self.diagnostics.append(
                        Diagnostic(
                            start_line, 1, "EFFORT_LIMIT_EXCEEDED", "ERROR",
                            f"Atomic task effort ({effort_val}h) MUST NOT exceed 4.0 hours.",
                            file_name=path
                        )
                    )
            except (ValueError, TypeError):
                self.diagnostics.append(
                    Diagnostic(start_line, 1, "INVALID_EFFORT_FORMAT", "ERROR", "Task effort_hours must be a numeric value.", file_name=path)
                )

            status = task_data.get("status")
            if status not in VALID_TASK_STATUSES:
                self.diagnostics.append(
                    Diagnostic(start_line, 1, "INVALID_TASK_STATUS", "ERROR", f"Status must be in {sorted(VALID_TASK_STATUSES)}, found '{status}'.", file_name=path)
                )

            criteria = task_data.get("acceptance_criteria", [])
            if not isinstance(criteria, list) or len(criteria) == 0:
                self.diagnostics.append(
                    Diagnostic(start_line, 1, "TASK_MISSING_CRITERIA", "ERROR", "Atomic task must have non-empty acceptance_criteria list.", file_name=path)
                )
            else:
                for c in criteria:
                    self._check_ace_line(c, start_line, path)

        summary = {
            "active_task_id": task_data.get("id") if task_data else None,
            "status": task_data.get("status") if task_data else None,
            "effort_hours": effort_val if effort_val is not None else (task_data.get("effort_hours") if task_data else None),
        }
        return self.diagnostics, summary

    def validate_build_summary(self, content: str, path: str = "build-summary.md") -> Tuple[List[Diagnostic], Dict[str, Any]]:
        self.diagnostics = []
        lines = content.splitlines()

        # 1. Frontmatter
        if not lines or lines[0].strip() != "---":
            self.diagnostics.append(
                Diagnostic(1, 1, "FRONTMATTER_MISSING", "ERROR", "Document MUST start with YAML frontmatter delimiter '---'.", file_name=path)
            )
            return self.diagnostics, {}

        end_idx = -1
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                end_idx = i
                break

        if end_idx == -1:
            self.diagnostics.append(
                Diagnostic(1, 1, "FRONTMATTER_UNCLOSED", "ERROR", "Frontmatter delimiter '---' is unclosed.", file_name=path)
            )
            return self.diagnostics, {}

        yaml_text = "\n".join(lines[1:end_idx])
        meta: Dict[str, Any] = {}
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

        # Check required frontmatter envelope keys
        req_keys = ["slug", "status", "approved_by", "artifacts"]
        for rk in req_keys:
            if rk not in meta:
                self.diagnostics.append(
                    Diagnostic(1, 1, "SCHEMA_MISSING_KEY", "ERROR", f"Missing mandatory key '{rk}'.", file_name=path)
                )

        status = meta.get("status")
        if status and status not in VALID_STATUSES:
            self.diagnostics.append(
                Diagnostic(1, 1, "SCHEMA_INVALID_STATUS", "ERROR", f"Frontmatter 'status' must be one of {sorted(VALID_STATUSES)}, found '{status}'.", file_name=path)
            )

        approved_by = meta.get("approved_by")
        if approved_by and approved_by not in {"pending", "human"}:
            self.diagnostics.append(
                Diagnostic(1, 1, "SCHEMA_INVALID_APPROVED_BY", "ERROR", f"Frontmatter 'approved_by' must be 'pending' or 'human', found '{approved_by}'.", file_name=path)
            )

        artifacts = meta.get("artifacts")
        if "artifacts" in meta:
            if not isinstance(artifacts, list) or len(artifacts) == 0:
                self.diagnostics.append(
                    Diagnostic(1, 1, "SCHEMA_INVALID_ARTIFACTS", "ERROR", "Frontmatter 'artifacts' must be a non-empty list.", file_name=path)
                )

        # 2. Strict Headings
        required_patterns = [
            (r"^#\s+Build Summary:\s*.+", "Title '# Build Summary: <Title>'"),
            (r"^##\s+1\.\s+Execution Overview", "Section '## 1. Execution Overview'"),
            (r"^##\s+2\.\s+Completed Atomic Tasks", "Section '## 2. Completed Atomic Tasks'"),
            (r"^##\s+3\.\s+Test Verification Evidence", "Section '## 3. Test Verification Evidence'"),
            (r"^##\s+4\.\s+Modified Components", "Section '## 4. Modified Components'"),
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
                    Diagnostic(1, 1, "STRUCTURE_MISSING_SECTION", "ERROR", f"Missing section: {label}.", file_name=path)
                )
            else:
                found_indices.append(matched_line)

        if len(found_indices) == len(required_patterns):
            if found_indices != sorted(found_indices):
                self.diagnostics.append(
                    Diagnostic(1, 1, "SECTION_ORDER_INVALID", "ERROR", "Sections in build-summary.md appear out of sequential order.", file_name=path)
                )

        # 3. Check for ASCII art
        self._check_for_ascii_art(lines, path)

        summary = {
            "slug": meta.get("slug", "unknown"),
            "status": meta.get("status", "unknown"),
            "approved_by": meta.get("approved_by", "unknown"),
            "artifacts_count": len(artifacts) if isinstance(artifacts, list) else 0,
        }
        return self.diagnostics, summary

    def validate_build_dir(self, build_dir: str, check_summary: bool = True, check_active: bool = True) -> Tuple[List[Diagnostic], Dict[str, Any]]:
        self.diagnostics = []
        summary: Dict[str, Any] = {
            "build_dir": build_dir,
            "slug": "unknown",
            "status": "unknown",
            "active_task_id": None,
        }

        if check_summary:
            summary_path = os.path.join(build_dir, "build-summary.md")
            if not os.path.exists(summary_path):
                self.diagnostics.append(
                    Diagnostic(1, 1, "BUILD_SUMMARY_NOT_FOUND", "ERROR", f"File '{summary_path}' does not exist.", file_name=summary_path)
                )
            else:
                with open(summary_path, "r", encoding="utf-8") as f:
                    content = f.read()
                diags, sum_meta = self.validate_build_summary(content, summary_path)
                self.diagnostics.extend(diags)
                summary["slug"] = sum_meta.get("slug", "unknown")
                summary["status"] = sum_meta.get("status", "unknown")

        if check_active:
            active_path = os.path.join(build_dir, "active.md")
            if os.path.exists(active_path):
                with open(active_path, "r", encoding="utf-8") as f:
                    content = f.read()
                diags, act_meta = self.validate_active_task(content, active_path)
                self.diagnostics.extend(diags)
                summary["active_task_id"] = act_meta.get("active_task_id")

        return self.diagnostics, summary

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
                        "ASCII art box diagrams are forbidden. Use Mermaid diagrams and plain text.",
                        snippet=line, file_name=path
                    )
                )

    def _check_ace_line(self, text: str, line: int, path: str):
        words = re.findall(r"\b[A-Za-z0-9'-]+\b", text)
        for w in words:
            wl = w.lower()
            if wl in FORBIDDEN_MODALS:
                self.diagnostics.append(
                    Diagnostic(line, 1, "FORBIDDEN_MODAL", "ERROR", f"Criterion contains forbidden modal '{w}'. Use {FORBIDDEN_MODALS[wl]}.", snippet=text, file_name=path)
                )
            if wl in FORBIDDEN_AMBIGUOUS_WORDS:
                self.diagnostics.append(
                    Diagnostic(line, 1, "AMBIGUOUS_WORD", "ERROR", f"Criterion contains vague term '{w}'. Suggested fix: {FORBIDDEN_AMBIGUOUS_WORDS[wl]}.", snippet=text, file_name=path)
                )

        passive_match = re.search(r"\b(is|are|was|were|be|been|being)\s+([a-z]+ed|[a-z]+en)\b", text, re.IGNORECASE)
        if passive_match:
            verb_part = passive_match.group(2).lower()
            if verb_part in IRREGULAR_PAST_PARTICIPLES or verb_part.endswith("ed"):
                self.diagnostics.append(
                    Diagnostic(line, 1, "PASSIVE_VOICE", "ERROR", f"Criterion contains passive voice '{passive_match.group(0)}'. Use active SVO.", snippet=text, file_name=path)
                )


def format_cli_output(target: str, diagnostics: List[Diagnostic], summary: Dict[str, Any]) -> str:
    errors = [d for d in diagnostics if d.severity == "ERROR"]
    warnings = [d for d in diagnostics if d.severity == "WARNING"]
    lines = []
    lines.append("=" * 70)
    lines.append(f"BUILD TASK & SUMMARY VALIDATOR: {target}")
    lines.append("=" * 70)
    for k, v in summary.items():
        lines.append(f"{k.capitalize():15}: {v}")
    lines.append("-" * 70)

    if errors:
        lines.append(f"ERRORS ({len(errors)}):")
        for e in errors:
            fname = os.path.basename(e.file_name) if e.file_name else "file"
            lines.append(f"  [{fname}:Line {e.line}] {e.rule_id}: {e.message}")
            if e.snippet:
                lines.append(f"    Snippet: {e.snippet}")
    else:
        lines.append("No errors found. Build specification is clean!")

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
    parser = argparse.ArgumentParser(description="Build Task and Summary Validator")
    parser.add_argument("target", nargs="?", default=None, help="Target file (active.md or build-summary.md) or build stage directory")
    parser.add_argument("--slug", "-s", type=str, default=None, help="Work slug identifier")
    parser.add_argument("--check-active", action="store_true", help="Validate active.md only")
    parser.add_argument("--check-summary", action="store_true", help="Validate build-summary.md only")
    parser.add_argument("--all", action="store_true", help="Run all checks (default)")
    parser.add_argument("--json", action="store_true", help="Output machine-readable JSON results")

    args = parser.parse_args()

    run_summary = True
    run_active = True
    if args.check_summary or args.check_active:
        run_summary = args.check_summary
        run_active = args.check_active

    build_dir = None
    target_file = None

    if args.slug:
        cand = os.path.join(os.getcwd(), "docs", ".prompts-and-prayers", args.slug, "04-build")
        if os.path.isdir(cand):
            build_dir = cand

    if args.target and not build_dir:
        target_path = os.path.abspath(args.target)
        if os.path.isdir(target_path):
            build_dir = target_path
        elif os.path.isfile(target_path):
            target_file = target_path
        else:
            sys.stderr.write(f"Error: Target path '{args.target}' does not exist.\n")
            sys.exit(2)

    validator = BuildValidator()

    if target_file:
        with open(target_file, "r", encoding="utf-8") as f:
            content = f.read()
        if "summary" in os.path.basename(target_file):
            diags, summary = validator.validate_build_summary(content, target_file)
        else:
            diags, summary = validator.validate_active_task(content, target_file)

        error_count = len([d for d in diags if d.severity == "ERROR"])
        warn_count = len([d for d in diags if d.severity == "WARNING"])
        if args.json:
            print(json.dumps({
                "target": target_file,
                "valid": error_count == 0,
                "error_count": error_count,
                "warning_count": warn_count,
                "summary": summary,
                "errors": [d.to_dict() for d in diags]
            }, indent=2))
        else:
            print(format_cli_output(target_file, diags, summary))
        sys.exit(1 if error_count > 0 else 0)

    if build_dir is None:
        base_dir = os.path.join(os.getcwd(), "docs", ".prompts-and-prayers")
        if os.path.isdir(base_dir):
            entries = sorted([d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))], reverse=True)
            for entry in entries:
                cand = os.path.join(base_dir, entry, "04-build")
                if os.path.isdir(cand):
                    build_dir = cand
                    break

    if build_dir is None:
        sys.stderr.write("Error: Could not locate build directory.\n")
        sys.exit(2)

    diags, summary = validator.validate_build_dir(build_dir, check_summary=run_summary, check_active=run_active)
    error_count = len([d for d in diags if d.severity == "ERROR"])
    warn_count = len([d for d in diags if d.severity == "WARNING"])

    if args.json:
        print(json.dumps({
            "target": build_dir,
            "valid": error_count == 0,
            "error_count": error_count,
            "warning_count": warn_count,
            "summary": summary,
            "errors": [d.to_dict() for d in diags]
        }, indent=2))
    else:
        print(format_cli_output(build_dir, diags, summary))

    sys.exit(1 if error_count > 0 else 0)


if __name__ == "__main__":
    main()
