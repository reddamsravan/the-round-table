#!/usr/bin/env python3
"""
Architect Technical Specification and Plan Validator.

Validates:
1. docs/.prompts-and-prayers/sprints/sprint-{N}/03-architecture/tech-spec.md for schema, ADRs, and diagrams.
2. docs/.prompts-and-prayers/sprints/sprint-{N}/04-tasks/plan.md for task graph schema, dependencies, and ACE criteria.
3. End-to-end traceability of User Stories from 01-stories/spec.md to 04-tasks/plan.md.
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
VALID_TASK_STATUSES = {"TODO", "IN_PROGRESS", "VERIFYING", "DONE", "ABORTED"}

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


class ArchitectValidator:
    def __init__(self):
        self.diagnostics: List[Diagnostic] = []

    def validate_sprint(
        self,
        sprint_dir: str,
        check_spec: bool = True,
        check_plan: bool = True,
        check_traceability: bool = True,
        check_ace: bool = True,
    ) -> Tuple[List[Diagnostic], Dict[str, Any]]:
        self.diagnostics = []

        tech_spec_path = os.path.join(sprint_dir, "03-architecture", "tech-spec.md")
        plan_path = os.path.join(sprint_dir, "04-tasks", "plan.md")
        stories_path = os.path.join(sprint_dir, "01-stories", "spec.md")

        spec_metadata = {}
        plan_tasks = []

        if check_spec:
            if not os.path.exists(tech_spec_path):
                self.diagnostics.append(
                    Diagnostic(1, 1, "TECH_SPEC_NOT_FOUND", "ERROR", f"File '{tech_spec_path}' does not exist.", file_name=tech_spec_path)
                )
            else:
                with open(tech_spec_path, "r", encoding="utf-8") as f:
                    spec_content = f.read()
                spec_metadata = self._validate_tech_spec(spec_content, tech_spec_path, check_ace)

        if check_plan:
            if not os.path.exists(plan_path):
                self.diagnostics.append(
                    Diagnostic(1, 1, "PLAN_NOT_FOUND", "ERROR", f"File '{plan_path}' does not exist.", file_name=plan_path)
                )
            else:
                with open(plan_path, "r", encoding="utf-8") as f:
                    plan_content = f.read()
                plan_tasks = self._validate_plan(plan_content, plan_path, check_ace)

        if check_traceability and os.path.exists(stories_path) and os.path.exists(plan_path):
            with open(stories_path, "r", encoding="utf-8") as f:
                stories_content = f.read()
            with open(plan_path, "r", encoding="utf-8") as f:
                plan_content = f.read()
            self._validate_traceability(stories_content, plan_content, plan_tasks, stories_path, plan_path)

        summary = {
            "sprint_dir": sprint_dir,
            "sprint": spec_metadata.get("sprint", "unknown"),
            "status": spec_metadata.get("status", "unknown"),
            "total_plan_tasks": len(plan_tasks),
        }

        return self.diagnostics, summary

    def _validate_tech_spec(self, content: str, path: str, check_ace: bool) -> Dict[str, Any]:
        lines = content.splitlines()

        # 1. Frontmatter
        if not lines or lines[0].strip() != "---":
            self.diagnostics.append(
                Diagnostic(1, 1, "FRONTMATTER_MISSING", "ERROR", "Document MUST start with YAML frontmatter '---'.", file_name=path)
            )
            return {}

        end_idx = -1
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                end_idx = i
                break

        if end_idx == -1:
            self.diagnostics.append(
                Diagnostic(1, 1, "FRONTMATTER_UNCLOSED", "ERROR", "Frontmatter delimiter '---' is unclosed.", file_name=path)
            )
            return {}

        yaml_text = "\n".join(lines[1:end_idx])
        meta = {}
        if yaml is None:
            for line in yaml_text.splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    meta[k.strip()] = v.strip().strip('"').strip("'")
            data = meta
        else:
            try:
                data = yaml.safe_load(yaml_text) or {}
            except Exception as e:
                self.diagnostics.append(
                    Diagnostic(1, 1, "YAML_SYNTAX_ERROR", "ERROR", f"Invalid YAML: {e}", file_name=path)
                )
                return {}

        required_keys = ["sprint", "persona", "status", "handoff_to", "artifacts"]
        for rk in required_keys:
            if rk not in data:
                self.diagnostics.append(
                    Diagnostic(1, 1, "SCHEMA_MISSING_KEY", "ERROR", f"Missing mandatory key '{rk}'.", file_name=path)
                )

        if data.get("persona") != "architect":
            self.diagnostics.append(
                Diagnostic(1, 1, "SCHEMA_INVALID_PERSONA", "ERROR", f"Persona must be 'architect', found '{data.get('persona')}'.", file_name=path)
            )

        if data.get("status") not in VALID_STATUSES:
            self.diagnostics.append(
                Diagnostic(1, 1, "SCHEMA_INVALID_STATUS", "ERROR", f"Status must be in {sorted(VALID_STATUSES)}, found '{data.get('status')}'.", file_name=path)
            )

        if data.get("handoff_to") != "developer":
            self.diagnostics.append(
                Diagnostic(1, 1, "SCHEMA_INVALID_HANDOFF", "ERROR", f"Handoff must be 'developer', found '{data.get('handoff_to')}'.", file_name=path)
            )

        # 2. Headings
        headings = [l.strip() for l in lines if l.startswith("#")]
        required_patterns = [
            (r"^#\s+Technical Architecture Specification:", "Title '# Technical Architecture Specification: <Title>'"),
            (r"^##\s+1\.\s+System Overview & Architecture Topology", "Section '## 1. System Overview & Architecture Topology'"),
            (r"^##\s+2\.\s+Architectural Decision Records", "Section '## 2. Architectural Decision Records (ADRs)'"),
            (r"^##\s+3\.\s+Component Contracts & Interfaces", "Section '## 3. Component Contracts & Interfaces'"),
            (r"^##\s+4\.\s+Technical Constraints & Invariants", "Section '## 4. Technical Constraints & Invariants'"),
        ]
        for pat, label in required_patterns:
            if not any(re.search(pat, h) for h in headings):
                self.diagnostics.append(
                    Diagnostic(1, 1, "STRUCTURE_MISSING_SECTION", "ERROR", f"Tech spec missing section: {label}.", file_name=path)
                )

        # 3. Mermaid block in Section 1
        if not re.search(r"```mermaid\s+(flowchart|graph)", content, re.IGNORECASE):
            self.diagnostics.append(
                Diagnostic(1, 1, "MERMAID_MISSING", "ERROR", "Section 1 MUST contain a Mermaid architecture flowchart.", file_name=path)
            )

        # 4. ACE constraints
        if check_ace:
            in_sec4 = False
            for idx, line in enumerate(lines, start=1):
                s = line.strip()
                if s.startswith("## 4. Technical"):
                    in_sec4 = True
                    continue
                elif s.startswith("## ") and in_sec4:
                    break
                if in_sec4 and (s.startswith("- ") or s.startswith("* ")):
                    self._check_ace_line(s[2:].strip(), idx, path)

        return data

    def _validate_plan(self, content: str, path: str, check_ace: bool) -> List[Dict[str, Any]]:
        lines = content.splitlines()
        headings = [l.strip() for l in lines if l.startswith("#")]

        required_patterns = [
            (r"^#\s+Sprint Implementation Plan:", "Title '# Sprint Implementation Plan: <Title>'"),
            (r"^##\s+Plan Overview", "Section '## Plan Overview'"),
            (r"^##\s+Traceability Matrix", "Section '## Traceability Matrix'"),
            (r"^##\s+Engineering Tasks", "Section '## Engineering Tasks'"),
        ]
        for pat, label in required_patterns:
            if not any(re.search(pat, h) for h in headings):
                self.diagnostics.append(
                    Diagnostic(1, 1, "STRUCTURE_MISSING_SECTION", "ERROR", f"Plan missing section: {label}.", file_name=path)
                )

        # Extract tasks: ### Task: PLAN-<NNN> - <Title>
        task_re = re.compile(r"^###\s+Task:\s+(PLAN-\d+)\s+-\s+(.+)$")
        tasks = []
        current_id = None
        current_title = None
        current_yaml = []
        in_yaml = False
        start_line = 0

        for idx, line in enumerate(lines, start=1):
            s = line.strip()
            m = task_re.match(s)
            if m:
                current_id = m.group(1)
                current_title = m.group(2).strip()
                start_line = idx
                current_yaml = []
                in_yaml = False
                continue

            if current_id:
                if s.startswith("```yaml") and not in_yaml:
                    in_yaml = True
                    continue
                elif s.startswith("```") and in_yaml:
                    in_yaml = False
                    # Parse task YAML
                    yaml_text = "\n".join(current_yaml)
                    task_data = self._parse_task_yaml(yaml_text, current_id, start_line, path)
                    if task_data:
                        tasks.append(task_data)
                    current_id = None
                    continue

                if in_yaml:
                    current_yaml.append(line)

        if not tasks:
            self.diagnostics.append(
                Diagnostic(1, 1, "TASKS_EMPTY", "ERROR", "Plan MUST define at least one task matching '### Task: PLAN-<NNN> - <Title>'.", file_name=path)
            )

        if check_ace:
            for t in tasks:
                for c in t.get("acceptance_criteria", []):
                    self._check_ace_line(c, t.get("line_number", 1), path)

        return tasks

    def _parse_task_yaml(self, text: str, task_id: str, line: int, path: str) -> Optional[Dict[str, Any]]:
        try:
            if yaml is not None:
                data = yaml.safe_load(text) or {}
            else:
                data = {}
                for l in text.splitlines():
                    if ":" in l:
                        k, v = l.split(":", 1)
                        data[k.strip()] = v.strip().strip('"').strip("'")
        except Exception as e:
            self.diagnostics.append(
                Diagnostic(line, 1, "TASK_YAML_INVALID", "ERROR", f"Task '{task_id}' has invalid YAML: {e}", file_name=path)
            )
            return None

        data["line_number"] = line
        req_keys = ["id", "title", "status", "depends_on", "acceptance_criteria"]
        for rk in req_keys:
            if rk not in data:
                self.diagnostics.append(
                    Diagnostic(line, 1, "TASK_MISSING_KEY", "ERROR", f"Task '{task_id}' missing mandatory field '{rk}'.", file_name=path)
                )

        if data.get("status") not in VALID_TASK_STATUSES:
            self.diagnostics.append(
                Diagnostic(line, 1, "TASK_INVALID_STATUS", "ERROR", f"Task '{task_id}' status '{data.get('status')}' must be in {sorted(VALID_TASK_STATUSES)}.", file_name=path)
            )

        return data

    def _validate_traceability(
        self, stories_content: str, plan_content: str, plan_tasks: List[Dict[str, Any]], stories_path: str, plan_path: str
    ):
        story_ids = set(re.findall(r"###\s+Story:\s+(US-\d+)", stories_content))
        if not story_ids:
            return

        covered_stories = set()
        for t in plan_tasks:
            us_list = t.get("user_stories", [])
            if isinstance(us_list, list):
                for us in us_list:
                    covered_stories.add(str(us).strip())

        # Also search in the Traceability Matrix table in plan.md
        for sid in story_ids:
            if sid in plan_content:
                covered_stories.add(sid)

        uncovered = story_ids - covered_stories
        if uncovered:
            for u in sorted(uncovered):
                self.diagnostics.append(
                    Diagnostic(
                        1, 1, "UNCOVERED_USER_STORY", "ERROR",
                        f"User story '{u}' from 01-stories/spec.md is not mapped in 04-tasks/plan.md.",
                        file_name=plan_path,
                    )
                )

    def _check_ace_line(self, text: str, line: int, path: str):
        words = re.findall(r"\b[A-Za-z0-9'-]+\b", text)
        for w in words:
            wl = w.lower()
            if wl in FORBIDDEN_MODALS:
                self.diagnostics.append(
                    Diagnostic(
                        line, 1, "FORBIDDEN_MODAL", "ERROR",
                        f"Statement contains forbidden modal '{w}'. Use {FORBIDDEN_MODALS[wl]}.",
                        snippet=text, file_name=path
                    )
                )
            if wl in FORBIDDEN_AMBIGUOUS_WORDS:
                self.diagnostics.append(
                    Diagnostic(
                        line, 1, "AMBIGUOUS_WORD", "ERROR",
                        f"Statement contains vague term '{w}'. Suggested fix: {FORBIDDEN_AMBIGUOUS_WORDS[wl]}.",
                        snippet=text, file_name=path
                    )
                )

        passive_match = re.search(r"\b(is|are|was|were|be|been|being)\s+([a-z]+ed|[a-z]+en)\b", text, re.IGNORECASE)
        if passive_match:
            verb_part = passive_match.group(2).lower()
            if verb_part in IRREGULAR_PAST_PARTICIPLES or verb_part.endswith("ed"):
                self.diagnostics.append(
                    Diagnostic(
                        line, 1, "PASSIVE_VOICE", "ERROR",
                        f"Statement contains passive voice '{passive_match.group(0)}'. Use active SVO.",
                        snippet=text, file_name=path
                    )
                )


def format_cli_output(sprint_dir: str, diagnostics: List[Diagnostic], summary: Dict[str, Any]) -> str:
    errors = [d for d in diagnostics if d.severity == "ERROR"]
    warnings = [d for d in diagnostics if d.severity == "WARNING"]
    lines = []
    lines.append("=" * 70)
    lines.append(f"ARCHITECT SPEC & PLAN VALIDATOR: {sprint_dir}")
    lines.append("=" * 70)
    lines.append(f"Sprint:      {summary.get('sprint', 'unknown')}")
    lines.append(f"Status:      {summary.get('status', 'unknown')}")
    lines.append(f"Plan Tasks:  {summary.get('total_plan_tasks', 0)}")
    lines.append("-" * 70)

    if errors:
        lines.append(f"ERRORS ({len(errors)}):")
        for e in errors:
            fname = os.path.basename(e.file_name) if e.file_name else "spec"
            lines.append(f"  [{fname}:Line {e.line}] {e.rule_id}: {e.message}")
            if e.snippet:
                lines.append(f"    Snippet: {e.snippet}")
    else:
        lines.append("No errors found. Technical spec and implementation plan are clean!")

    if warnings:
        lines.append(f"WARNINGS ({len(warnings)}):")
        for w in warnings:
            fname = os.path.basename(w.file_name) if w.file_name else "spec"
            lines.append(f"  [{fname}:Line {w.line}] {w.rule_id}: {w.message}")

    lines.append("=" * 70)
    lines.append("RESULT: " + ("PASS" if len(errors) == 0 else "FAIL"))
    lines.append("=" * 70)
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Architect Technical Spec and Plan Validator")
    parser.add_argument("target", nargs="?", default=None, help="Target sprint directory or file")
    parser.add_argument("--sprint", "-s", type=str, default=None, help="Sprint identifier (e.g. sprint-1)")
    parser.add_argument("--check-spec", action="store_true", help="Validate tech-spec.md only")
    parser.add_argument("--check-plan", action="store_true", help="Validate plan.md only")
    parser.add_argument("--check-traceability", action="store_true", help="Validate user story traceability only")
    parser.add_argument("--check-ace", action="store_true", help="Validate ACE criteria syntax only")
    parser.add_argument("--all", action="store_true", help="Run all checks (default)")
    parser.add_argument("--json", action="store_true", help="Output machine-readable JSON results")

    args = parser.parse_args()

    run_spec = True
    run_plan = True
    run_trace = True
    run_ace = True

    if args.check_spec or args.check_plan or args.check_traceability or args.check_ace:
        run_spec = args.check_spec
        run_plan = args.check_plan
        run_trace = args.check_traceability
        run_ace = args.check_ace

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
            # Resolve sprint root directory from file path
            p = cand
            while p and os.path.dirname(p) != p:
                if os.path.basename(os.path.dirname(p)) == "sprints":
                    sprint_dir = p
                    break
                p = os.path.dirname(p)

    if sprint_dir is None:
        sprints_root = os.path.join(os.getcwd(), "docs", ".prompts-and-prayers", "sprints")
        if os.path.isdir(sprints_root):
            entries = sorted(
                [d for d in os.listdir(sprints_root) if os.path.isdir(os.path.join(sprints_root, d))],
                reverse=True
            )
            for sp in entries:
                sprint_dir = os.path.join(sprints_root, sp)
                break

    if sprint_dir is None or not os.path.exists(sprint_dir):
        sys.stderr.write(f"Error: Unable to locate active sprint directory.\n")
        sys.exit(2)

    validator = ArchitectValidator()
    diags, summary = validator.validate_sprint(
        sprint_dir, check_spec=run_spec, check_plan=run_plan, check_traceability=run_trace, check_ace=run_ace
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
