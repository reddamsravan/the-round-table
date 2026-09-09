#!/usr/bin/env python3
"""
Plot Skill Technical Specification and Implementation Plan Validator.

Validates plot artifacts (e.g. docs/.prompts-and-prayers/{work_slug}/03-plot/):
1. tech-spec.md for frontmatter envelope (slug, status, approved_by, artifacts),
   mandatory sections, Mermaid diagrams, and ACE technical constraints.
2. plan.md for plan overview, engineering tasks (PLAN-<NNN>), DAG dependencies,
   and ACE acceptance criteria.
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


class PlanTask:
    def __init__(self, task_id: str, title: str, status: str, depends_on: List[str], acceptance_criteria: List[str], line_number: int):
        self.task_id = task_id
        self.title = title
        self.status = status
        self.depends_on = depends_on
        self.acceptance_criteria = acceptance_criteria
        self.line_number = line_number


class PlotValidator:
    def __init__(self):
        self.diagnostics: List[Diagnostic] = []

    def validate_plot_dir(
        self,
        plot_dir: str,
        check_spec: bool = True,
        check_plan: bool = True,
        check_ace: bool = True,
    ) -> Tuple[List[Diagnostic], Dict[str, Any]]:
        self.diagnostics = []

        tech_spec_path = os.path.join(plot_dir, "tech-spec.md")
        plan_path = os.path.join(plot_dir, "plan.md")

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

        summary = {
            "plot_dir": plot_dir,
            "slug": spec_metadata.get("slug", "unknown"),
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
        meta: Dict[str, Any] = {}
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

        required_keys = ["slug", "status", "approved_by", "artifacts"]
        for rk in required_keys:
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

        # 2. Mandatory Headings
        required_patterns = [
            (r"^#\s+(?:Technical(?:\s+Architecture)?|Architecture)\s+Specification:", "Title '# Technical Specification: <Title>'"),
            (r"^##\s+1\.\s+System Overview\s+(?:&|and)\s+Architecture Topology", "Section '## 1. System Overview & Architecture Topology'"),
            (r"^##\s+2\.\s+Architectural Decision Records\s+\(ADRs\)", "Section '## 2. Architectural Decision Records (ADRs)'"),
            (r"^##\s+3\.\s+Component Contracts\s+(?:&|and)\s+Interfaces", "Section '## 3. Component Contracts & Interfaces'"),
            (r"^##\s+4\.\s+Technical Constraints\s+(?:&|and)\s+Invariants", "Section '## 4. Technical Constraints & Invariants'"),
        ]

        found_indices = []
        for pattern, label in required_patterns:
            matched_line = None
            for idx, line in enumerate(lines, start=1):
                if re.search(pattern, line.strip()):
                    matched_line = idx
                    break
            if matched_line is None:
                self.diagnostics.append(
                    Diagnostic(1, 1, "STRUCTURE_MISSING_SECTION", "ERROR", f"Tech spec missing mandatory section: {label}.", file_name=path)
                )
            else:
                found_indices.append(matched_line)

        if len(found_indices) == len(required_patterns):
            if found_indices != sorted(found_indices):
                self.diagnostics.append(
                    Diagnostic(1, 1, "SECTION_ORDER_INVALID", "ERROR", "Sections in tech-spec.md appear out of sequential order.", file_name=path)
                )

        # 3. Mermaid Flowchart
        has_flowchart = False
        in_mermaid = False
        for idx, line in enumerate(lines, start=1):
            s = line.strip()
            if s.startswith("```mermaid"):
                in_mermaid = True
                continue
            elif s.startswith("```") and in_mermaid:
                in_mermaid = False
                continue

            if in_mermaid:
                sl = s.lower()
                if sl.startswith("flowchart") or sl.startswith("graph"):
                    has_flowchart = True

        if not has_flowchart:
            self.diagnostics.append(
                Diagnostic(1, 1, "FLOWCHART_MISSING", "ERROR", "Section 1 MUST contain a Mermaid flowchart ('flowchart TD' or 'flowchart LR').", file_name=path)
            )

        # 4. Check ASCII art
        self._check_for_ascii_art(lines, path)

        # 5. ACE Validation on Section 4
        if check_ace:
            self._validate_constraints_ace(lines, path)

        return data

    def _validate_plan(self, content: str, path: str, check_ace: bool) -> List[PlanTask]:
        lines = content.splitlines()

        # 1. Structure
        required_patterns = [
            (r"^#\s+(?:(?:Sprint\s+)?Implementation Plan|Task Plan):", "Title '# Implementation Plan: <Title>'"),
            (r"^##\s+Plan Overview", "Section '## Plan Overview'"),
            (r"^##\s+Engineering Tasks", "Section '## Engineering Tasks'"),
        ]

        for pattern, label in required_patterns:
            if not any(re.search(pattern, line.strip()) for line in lines):
                self.diagnostics.append(
                    Diagnostic(1, 1, "PLAN_STRUCTURE_MISSING", "ERROR", f"Plan missing mandatory section: {label}.", file_name=path)
                )

        # 2. Extract Tasks
        tasks: List[PlanTask] = []
        task_re = re.compile(r"^###\s+Task:\s+(PLAN-\d{3,})\s+-\s+(.+)$")

        current_id: Optional[str] = None
        current_title: Optional[str] = None
        current_line: int = 0
        in_yaml: bool = False
        yaml_lines: List[str] = []

        for idx, line in enumerate(lines, start=1):
            m = task_re.match(line.strip())
            if m:
                if current_id and yaml_lines:
                    t = self._parse_plan_task_yaml(current_id, current_title or "", current_line, yaml_lines, path, check_ace)
                    if t:
                        tasks.append(t)
                current_id = m.group(1)
                current_title = m.group(2)
                current_line = idx
                yaml_lines = []
                in_yaml = False
                continue

            if current_id:
                s = line.strip()
                if s.startswith("```yaml") or (s.startswith("```") and not in_yaml):
                    in_yaml = True
                    continue
                elif s.startswith("```") and in_yaml:
                    in_yaml = False
                    t = self._parse_plan_task_yaml(current_id, current_title or "", current_line, yaml_lines, path, check_ace)
                    if t:
                        tasks.append(t)
                    current_id = None
                    yaml_lines = []
                    continue

                if in_yaml:
                    yaml_lines.append(line)

        if current_id and yaml_lines:
            t = self._parse_plan_task_yaml(current_id, current_title or "", current_line, yaml_lines, path, check_ace)
            if t:
                tasks.append(t)

        if not tasks:
            self.diagnostics.append(
                Diagnostic(1, 1, "PLAN_NO_TASKS", "ERROR", "Plan contains no valid tasks under '## Engineering Tasks'.", file_name=path)
            )
            return []

        # 3. DAG Dependency Checks
        task_ids = {t.task_id for t in tasks}
        graph: Dict[str, List[str]] = {}

        for t in tasks:
            graph[t.task_id] = []
            for dep in t.depends_on:
                if dep == t.task_id:
                    self.diagnostics.append(
                        Diagnostic(t.line_number, 1, "DAG_SELF_DEPENDENCY", "ERROR", f"Task '{t.task_id}' depends on itself.", file_name=path)
                    )
                elif dep not in task_ids:
                    self.diagnostics.append(
                        Diagnostic(t.line_number, 1, "DAG_UNKNOWN_DEPENDENCY", "ERROR", f"Task '{t.task_id}' depends on non-existent task '{dep}'.", file_name=path)
                    )
                else:
                    graph[t.task_id].append(dep)

        # Cycle detection via DFS
        visited: Dict[str, int] = {}  # 0: unvisited, 1: visiting, 2: visited

        def has_cycle(node: str) -> bool:
            visited[node] = 1
            for neighbor in graph.get(node, []):
                if visited.get(neighbor, 0) == 1:
                    return True
                if visited.get(neighbor, 0) == 0:
                    if has_cycle(neighbor):
                        return True
            visited[node] = 2
            return False

        for tid in task_ids:
            if visited.get(tid, 0) == 0:
                if has_cycle(tid):
                    self.diagnostics.append(
                        Diagnostic(1, 1, "DAG_CYCLE_DETECTED", "ERROR", f"Dependency cycle detected in plan task graph involving '{tid}'.", file_name=path)
                    )
                    break

        return tasks

    def _parse_plan_task_yaml(self, task_id: str, title: str, line_no: int, yaml_lines: List[str], path: str, check_ace: bool) -> Optional[PlanTask]:
        yaml_text = "\n".join(yaml_lines)
        if yaml is None:
            data = {}
            for l in yaml_lines:
                if ":" in l:
                    k, v = l.split(":", 1)
                    data[k.strip()] = v.strip()
        else:
            try:
                data = yaml.safe_load(yaml_text) or {}
            except Exception as e:
                self.diagnostics.append(
                    Diagnostic(line_no, 1, "TASK_YAML_ERROR", "ERROR", f"Task {task_id} has invalid YAML: {e}", file_name=path)
                )
                return None

        status = data.get("status")
        if status not in VALID_TASK_STATUSES:
            self.diagnostics.append(
                Diagnostic(line_no, 1, "TASK_INVALID_STATUS", "ERROR", f"Task {task_id} status '{status}' invalid.", file_name=path)
            )

        deps = data.get("depends_on", [])
        if not isinstance(deps, list):
            deps = []

        criteria = data.get("acceptance_criteria", [])
        if not isinstance(criteria, list) or len(criteria) == 0:
            self.diagnostics.append(
                Diagnostic(line_no, 1, "TASK_MISSING_CRITERIA", "ERROR", f"Task {task_id} must have non-empty acceptance_criteria list.", file_name=path)
            )
            criteria = []
        elif check_ace:
            for crit in criteria:
                self._lint_ace_sentence(crit, line_no, path, f"Task {task_id} acceptance criterion")

        return PlanTask(task_id, title, status or "TODO", deps, criteria, line_no)

    def _check_for_ascii_art(self, lines: List[str], path: str):
        ascii_box_re = re.compile(r"(\+[-=]{3,}\+|\|[-=]{3,}\||\+---+|┌─+┐|└─+┘|├───┤)")
        in_code = False
        for idx, line in enumerate(lines, start=1):
            if line.strip().startswith("```"):
                in_code = not in_code
                continue
            if in_code:
                continue

            if line.strip().startswith("+--") or line.strip().startswith("+==") or ascii_box_re.search(line):
                self.diagnostics.append(
                    Diagnostic(
                        idx, 1, "FORBIDDEN_ASCII_ART", "ERROR",
                        "ASCII art box diagrams are forbidden. Use Mermaid diagrams and plain text.",
                        snippet=line, file_name=path
                    )
                )

    def _validate_constraints_ace(self, lines: List[str], path: str):
        in_constraints = False
        for idx, line in enumerate(lines, start=1):
            s = line.strip()
            if s.startswith("## 4. Technical Constraints"):
                in_constraints = True
                continue
            elif s.startswith("## ") and in_constraints:
                break

            if in_constraints and (s.startswith("- ") or s.startswith("* ")):
                text = s[2:].strip()
                self._lint_ace_sentence(text, idx, path, "Technical constraint")

    def _lint_ace_sentence(self, text: str, line_no: int, path: str, label: str):
        words = re.findall(r"\b[A-Za-z0-9'-]+\b", text)
        for w in words:
            wl = w.lower()
            if wl in FORBIDDEN_MODALS:
                self.diagnostics.append(
                    Diagnostic(
                        line_no, 1, "FORBIDDEN_MODAL", "ERROR",
                        f"{label} contains forbidden modal '{w}'. Use {FORBIDDEN_MODALS[wl]}.",
                        snippet=text, file_name=path
                    )
                )
            if wl in FORBIDDEN_AMBIGUOUS_WORDS:
                self.diagnostics.append(
                    Diagnostic(
                        line_no, 1, "AMBIGUOUS_WORD", "ERROR",
                        f"{label} contains vague term '{w}'. Suggested fix: {FORBIDDEN_AMBIGUOUS_WORDS[wl]}.",
                        snippet=text, file_name=path
                    )
                )

        passive_match = re.search(r"\b(is|are|was|were|be|been|being)\s+([a-z]+ed|[a-z]+en)\b", text, re.IGNORECASE)
        if passive_match:
            verb_part = passive_match.group(2).lower()
            if verb_part in IRREGULAR_PAST_PARTICIPLES or verb_part.endswith("ed"):
                self.diagnostics.append(
                    Diagnostic(
                        line_no, 1, "PASSIVE_VOICE", "ERROR",
                        f"{label} contains passive voice '{passive_match.group(0)}'. Use active SVO.",
                        snippet=text, file_name=path
                    )
                )


def format_cli_output(target: str, diagnostics: List[Diagnostic], summary: Dict[str, Any]) -> str:
    errors = [d for d in diagnostics if d.severity == "ERROR"]
    warnings = [d for d in diagnostics if d.severity == "WARNING"]
    lines = []
    lines.append("=" * 70)
    lines.append(f"PLOT VALIDATOR: {target}")
    lines.append("=" * 70)
    lines.append(f"Slug:             {summary.get('slug', 'unknown')}")
    lines.append(f"Status:           {summary.get('status', 'unknown')}")
    lines.append(f"Total Plan Tasks: {summary.get('total_plan_tasks', 0)}")
    lines.append("-" * 70)

    if errors:
        lines.append(f"ERRORS ({len(errors)}):")
        for e in errors:
            loc = f"[{os.path.basename(e.file_name)}:Line {e.line}]" if e.file_name else f"[Line {e.line}]"
            lines.append(f"  {loc} {e.rule_id}: {e.message}")
            if e.snippet:
                lines.append(f"    Snippet: {e.snippet}")
    else:
        lines.append("No errors found. Plot artifacts are clean!")

    if warnings:
        lines.append(f"WARNINGS ({len(warnings)}):")
        for w in warnings:
            loc = f"[{os.path.basename(w.file_name)}:Line {w.line}]" if w.file_name else f"[Line {w.line}]"
            lines.append(f"  {loc} {w.rule_id}: {w.message}")

    lines.append("=" * 70)
    lines.append("RESULT: " + ("PASS" if len(errors) == 0 else "FAIL"))
    lines.append("=" * 70)
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Plot Skill Specification & Plan Validator")
    parser.add_argument("target", nargs="?", default=None, help="Target plot directory (containing tech-spec.md and plan.md) or markdown file")
    parser.add_argument("--slug", "-s", type=str, default=None, help="Work slug identifier")
    parser.add_argument("--check-spec", action="store_true", help="Run tech-spec checks only")
    parser.add_argument("--check-plan", action="store_true", help="Run plan checks only")
    parser.add_argument("--check-ace", action="store_true", help="Run ACE syntax checks only")
    parser.add_argument("--all", action="store_true", help="Run all checks (default)")
    parser.add_argument("--json", action="store_true", help="Output machine-readable JSON results")

    args = parser.parse_args()

    run_spec = True
    run_plan = True
    run_ace = True

    if args.check_spec or args.check_plan or args.check_ace:
        run_spec = args.check_spec
        run_plan = args.check_plan
        run_ace = args.check_ace

    target = args.target
    if target is None:
        if args.slug:
            candidate = os.path.join(os.getcwd(), "docs", ".prompts-and-prayers", args.slug, "03-plot")
            if os.path.exists(candidate):
                target = candidate
        if target is None:
            base_dir = os.path.join(os.getcwd(), "docs", ".prompts-and-prayers")
            if os.path.isdir(base_dir):
                for entry in sorted(os.listdir(base_dir), reverse=True):
                    candidate = os.path.join(base_dir, entry, "03-plot")
                    if os.path.exists(candidate):
                        target = candidate
                        break
        if target is None:
            sys.stderr.write("Error: No plot target found. Specify directory or file path.\n")
            sys.exit(2)

    target_path = os.path.abspath(target)
    validator = PlotValidator()

    if os.path.isdir(target_path):
        plot_dir = target_path
    elif os.path.isfile(target_path):
        plot_dir = os.path.dirname(target_path)
    else:
        sys.stderr.write(f"Error: Target path '{target_path}' does not exist.\n")
        sys.exit(2)

    diags, summary = validator.validate_plot_dir(
        plot_dir, check_spec=run_spec, check_plan=run_plan, check_ace=run_ace
    )

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
        print(format_cli_output(os.path.relpath(target_path), diags, summary))

    sys.exit(1 if error_count > 0 else 0)


if __name__ == "__main__":
    main()
