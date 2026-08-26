#!/usr/bin/env python3
"""
Task Graph, Schema, and ACE Validator (task skill).

Validates task markdown files (e.g. docs/.tasks/active.md) for:
1. Schema integrity (sections, embedded YAML blocks, required fields, status enums).
2. DAG integrity (acyclicity, known dependencies, prerequisite status satisfaction).
3. ACE specification rules (active voice SVO, permitted modals, no ambiguity words in criteria).
4. Lifecycle status reporting and next ready unblocked task queries.
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


# Permitted lifecycle statuses
VALID_STATUSES = {"TODO", "IN_PROGRESS", "VERIFYING", "DONE", "ABORTED"}

# ACE modal rules
FORBIDDEN_MODALS = {
    "should": "SHALL or MUST",
    "shouldn't": "SHALL NOT or MUST NOT",
    "should not": "SHALL NOT or MUST NOT",
    "could": "can (if capability) or SHALL (if requirement)",
    "couldn't": "SHALL NOT or MUST NOT",
    "might": "MAY or explicit conditional",
    "would": "SHALL or direct active verb",
    "may": "is permitted to or explicit conditional",
    "probably": "specify exact condition",
    "possibly": "specify exact condition",
    "maybe": "specify exact condition",
    "perhaps": "specify exact condition",
    "ought": "SHALL or MUST",
}

# ACE ambiguous terms
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
    "so forth": "enumerate all required items",
    "good": "specify concrete criteria",
    "bad": "specify concrete criteria",
    "sufficient": "specify measurable threshold",
}

# Common past participles for passive voice detection
PASSIVE_PAST_PARTICIPLES = {
    "been", "done", "written", "given", "taken", "seen", "made", "built", "sent",
    "run", "read", "set", "executed", "parsed", "processed", "triggered", "created",
    "deleted", "modified", "invoked", "called", "emitted", "evaluated", "checked",
    "rendered", "updated", "handled", "verified", "tested", "implemented"
}


class Diagnostic:
    def __init__(
        self,
        line: int,
        column: int,
        rule_id: str,
        severity: str,
        message: str,
        snippet: str,
        suggested_fix: str = ""
    ):
        self.line = line
        self.column = column
        self.rule_id = rule_id
        self.severity = severity  # "ERROR" or "WARNING"
        self.message = message
        self.snippet = snippet
        self.suggested_fix = suggested_fix

    def to_dict(self) -> Dict[str, Any]:
        return {
            "line": self.line,
            "column": self.column,
            "rule_id": self.rule_id,
            "severity": self.severity,
            "message": self.message,
            "snippet": self.snippet,
            "suggested_fix": self.suggested_fix,
        }


class TaskItem:
    def __init__(
        self,
        task_id: str,
        title: str,
        status: str,
        assignee: str,
        depends_on: List[str],
        acceptance_criteria: List[str],
        verify_cmd: Optional[str] = None,
        abort_reason: Optional[str] = None,
        line_number: int = 1,
        raw_dict: Optional[Dict[str, Any]] = None
    ):
        self.id = task_id
        self.title = title
        self.status = status
        self.assignee = assignee
        self.depends_on = depends_on
        self.acceptance_criteria = acceptance_criteria
        self.verify_cmd = verify_cmd
        self.abort_reason = abort_reason
        self.line_number = line_number
        self.raw_dict = raw_dict or {}

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "id": self.id,
            "title": self.title,
            "status": self.status,
            "assignee": self.assignee,
            "depends_on": self.depends_on,
            "acceptance_criteria": self.acceptance_criteria,
            "line_number": self.line_number
        }
        if self.verify_cmd is not None:
            result["verify_cmd"] = self.verify_cmd
        if self.abort_reason is not None:
            result["abort_reason"] = self.abort_reason
        return result


class TaskValidator:
    def __init__(self):
        pass

    def parse_document(self, content: str) -> Tuple[List[TaskItem], List[Diagnostic]]:
        """
        Parses Markdown document with embedded YAML blocks under ### Task: <ID> - <Title>.
        """
        tasks: List[TaskItem] = []
        diagnostics: List[Diagnostic] = []

        lines = content.splitlines()
        task_heading_regex = re.compile(r"^(#{2,4})\s+Task:\s*([A-Za-z0-9_-]+)\s*-\s*(.+)$")

        current_task_id: Optional[str] = None
        current_task_title: Optional[str] = None
        current_heading_line = 0
        in_yaml_block = False
        current_yaml_lines: List[str] = []
        current_yaml_start_line = 0

        for i, line in enumerate(lines, start=1):
            heading_match = task_heading_regex.match(line.strip())
            if heading_match:
                # If we had a previous task collecting YAML without closed fence
                if in_yaml_block:
                    diagnostics.append(Diagnostic(
                        line=current_yaml_start_line,
                        column=1,
                        rule_id="UNCLOSED_YAML_BLOCK",
                        severity="ERROR",
                        message=f"Unclosed YAML block before new task heading at line {i}",
                        snippet=lines[current_yaml_start_line - 1],
                        suggested_fix="Close YAML block with ``` before starting a new task."
                    ))
                    in_yaml_block = False
                    current_yaml_lines = []

                current_task_id = heading_match.group(2).strip()
                current_task_title = heading_match.group(3).strip()
                current_heading_line = i
                continue

            if current_task_id is not None:
                stripped = line.strip()
                if stripped.startswith("```yaml") or stripped.startswith("```yml"):
                    in_yaml_block = True
                    current_yaml_lines = []
                    current_yaml_start_line = i
                    continue
                elif in_yaml_block and stripped.startswith("```"):
                    in_yaml_block = False
                    yaml_text = "\n".join(current_yaml_lines)
                    task_item, parse_diags = self._parse_task_yaml(
                        yaml_text,
                        current_task_id,
                        current_task_title,
                        current_heading_line,
                        current_yaml_start_line
                    )
                    diagnostics.extend(parse_diags)
                    if task_item:
                        tasks.append(task_item)
                    current_task_id = None
                    current_task_title = None
                    continue
                elif in_yaml_block:
                    current_yaml_lines.append(line)

        if in_yaml_block:
            diagnostics.append(Diagnostic(
                line=current_yaml_start_line,
                column=1,
                rule_id="UNCLOSED_YAML_BLOCK",
                severity="ERROR",
                message=f"Unclosed YAML block at end of document",
                snippet=lines[current_yaml_start_line - 1] if lines else "",
                suggested_fix="Close YAML block with ```"
            ))

        return tasks, diagnostics

    def _parse_task_yaml(
        self,
        yaml_text: str,
        heading_id: str,
        heading_title: str,
        heading_line: int,
        yaml_line: int
    ) -> Tuple[Optional[TaskItem], List[Diagnostic]]:
        diagnostics: List[Diagnostic] = []
        if yaml is None:
            diagnostics.append(Diagnostic(
                line=yaml_line,
                column=1,
                rule_id="YAML_MODULE_MISSING",
                severity="ERROR",
                message="PyYAML is not installed.",
                snippet="import yaml",
                suggested_fix="Install PyYAML via pip."
            ))
            return None, diagnostics

        try:
            data = yaml.safe_load(yaml_text)
        except Exception as e:
            diagnostics.append(Diagnostic(
                line=yaml_line,
                column=1,
                rule_id="YAML_SYNTAX_ERROR",
                severity="ERROR",
                message=f"YAML parsing failed: {str(e)}",
                snippet=yaml_text.splitlines()[0] if yaml_text else "",
                suggested_fix="Fix YAML syntax error."
            ))
            return None, diagnostics

        if not isinstance(data, dict):
            diagnostics.append(Diagnostic(
                line=yaml_line,
                column=1,
                rule_id="YAML_NOT_DICT",
                severity="ERROR",
                message="Task YAML block must be a mapping/dictionary.",
                snippet=yaml_text.splitlines()[0] if yaml_text else "",
                suggested_fix="Format task metadata as key: value pairs."
            ))
            return None, diagnostics

        task_id = str(data.get("id", heading_id)).strip()
        title = str(data.get("title", heading_title)).strip()
        status = str(data.get("status", "")).strip().upper()
        assignee = str(data.get("assignee", "")).strip()
        depends_on_raw = data.get("depends_on", [])
        acceptance_criteria_raw = data.get("acceptance_criteria", [])
        verify_cmd = data.get("verify_cmd")
        abort_reason = data.get("abort_reason")

        depends_on = [str(d).strip() for d in depends_on_raw] if isinstance(depends_on_raw, list) else []
        acceptance_criteria = [str(c).strip() for c in acceptance_criteria_raw] if isinstance(acceptance_criteria_raw, list) else []

        if verify_cmd is not None:
            verify_cmd = str(verify_cmd).strip()
        if abort_reason is not None:
            abort_reason = str(abort_reason).strip()

        # Check ID match with heading
        if heading_id and task_id != heading_id:
            diagnostics.append(Diagnostic(
                line=heading_line,
                column=1,
                rule_id="TASK_ID_MISMATCH",
                severity="ERROR",
                message=f"Heading task ID '{heading_id}' does not match YAML id '{task_id}'",
                snippet=f"### Task: {heading_id} vs id: {task_id}",
                suggested_fix=f"Align heading and YAML id to '{task_id}'."
            ))

        item = TaskItem(
            task_id=task_id,
            title=title,
            status=status,
            assignee=assignee,
            depends_on=depends_on,
            acceptance_criteria=acceptance_criteria,
            verify_cmd=verify_cmd,
            abort_reason=abort_reason,
            line_number=heading_line,
            raw_dict=data
        )

        return item, diagnostics

    def validate_schema(self, tasks: List[TaskItem], content: str) -> List[Diagnostic]:
        diagnostics: List[Diagnostic] = []

        if not tasks and content.strip():
            diagnostics.append(Diagnostic(
                line=1,
                column=1,
                rule_id="NO_TASKS_FOUND",
                severity="ERROR",
                message="No valid task sections found in document. Expected '### Task: <ID> - <Title>' with embedded ```yaml block.",
                snippet=content.splitlines()[0] if content.splitlines() else "",
                suggested_fix="Define tasks using '### Task: <ID> - <Title>' and embedded ```yaml blocks."
            ))
            return diagnostics

        seen_ids: Set[str] = set()

        for task in tasks:
            # 1. ID checks
            if not task.id:
                diagnostics.append(Diagnostic(
                    line=task.line_number,
                    column=1,
                    rule_id="MISSING_TASK_ID",
                    severity="ERROR",
                    message="Task is missing mandatory 'id' field.",
                    snippet=f"Task at line {task.line_number}",
                    suggested_fix="Provide a unique 'id: TASK-XXX' in the YAML block."
                ))
            elif not re.match(r"^[A-Za-z0-9_-]+$", task.id):
                diagnostics.append(Diagnostic(
                    line=task.line_number,
                    column=1,
                    rule_id="INVALID_TASK_ID",
                    severity="ERROR",
                    message=f"Task ID '{task.id}' contains invalid characters. Use alphanumeric, dash, or underscore.",
                    snippet=f"id: {task.id}",
                    suggested_fix=f"Rename ID '{task.id}' to match ^[A-Za-z0-9_-]+$."
                ))
            elif task.id in seen_ids:
                diagnostics.append(Diagnostic(
                    line=task.line_number,
                    column=1,
                    rule_id="DUPLICATE_TASK_ID",
                    severity="ERROR",
                    message=f"Duplicate task ID '{task.id}' detected.",
                    snippet=f"id: {task.id}",
                    suggested_fix="Ensure each task ID is globally unique across the document."
                ))
            seen_ids.add(task.id)

            # 2. Title check
            if not task.title:
                diagnostics.append(Diagnostic(
                    line=task.line_number,
                    column=1,
                    rule_id="MISSING_TASK_TITLE",
                    severity="ERROR",
                    message=f"Task '{task.id}' is missing a title.",
                    snippet=f"id: {task.id}",
                    suggested_fix="Add 'title: <Description>' to the task YAML."
                ))

            # 3. Status enum check
            if not task.status:
                diagnostics.append(Diagnostic(
                    line=task.line_number,
                    column=1,
                    rule_id="MISSING_STATUS",
                    severity="ERROR",
                    message=f"Task '{task.id}' is missing mandatory 'status' field.",
                    snippet=f"id: {task.id}",
                    suggested_fix=f"Add 'status: TODO' (permitted: {', '.join(sorted(VALID_STATUSES))})."
                ))
            elif task.status not in VALID_STATUSES:
                diagnostics.append(Diagnostic(
                    line=task.line_number,
                    column=1,
                    rule_id="INVALID_STATUS",
                    severity="ERROR",
                    message=f"Task '{task.id}' has invalid status '{task.status}'. Permitted: {', '.join(sorted(VALID_STATUSES))}.",
                    snippet=f"status: {task.status}",
                    suggested_fix=f"Change status to one of {', '.join(sorted(VALID_STATUSES))}."
                ))

            # 4. Assignee check
            if not task.assignee:
                diagnostics.append(Diagnostic(
                    line=task.line_number,
                    column=1,
                    rule_id="MISSING_ASSIGNEE",
                    severity="ERROR",
                    message=f"Task '{task.id}' is missing mandatory 'assignee' field.",
                    snippet=f"id: {task.id}",
                    suggested_fix="Add 'assignee: self' or specify subagent role."
                ))

            # 5. Acceptance criteria checks
            if not task.raw_dict.get("acceptance_criteria"):
                diagnostics.append(Diagnostic(
                    line=task.line_number,
                    column=1,
                    rule_id="MISSING_ACCEPTANCE_CRITERIA",
                    severity="ERROR",
                    message=f"Task '{task.id}' is missing mandatory 'acceptance_criteria' list.",
                    snippet=f"id: {task.id}",
                    suggested_fix="Add 'acceptance_criteria:' with at least one verifiable condition."
                ))
            elif not task.acceptance_criteria:
                diagnostics.append(Diagnostic(
                    line=task.line_number,
                    column=1,
                    rule_id="EMPTY_ACCEPTANCE_CRITERIA",
                    severity="ERROR",
                    message=f"Task '{task.id}' has an empty 'acceptance_criteria' list.",
                    snippet=f"id: {task.id}",
                    suggested_fix="Add at least one concrete ACE acceptance criterion."
                ))

            # 6. Abort reason check
            if task.status == "ABORTED" and not task.abort_reason:
                diagnostics.append(Diagnostic(
                    line=task.line_number,
                    column=1,
                    rule_id="MISSING_ABORT_REASON",
                    severity="ERROR",
                    message=f"Task '{task.id}' is marked ABORTED but lacks mandatory 'abort_reason'.",
                    snippet=f"status: ABORTED",
                    suggested_fix="Add 'abort_reason: <Rationale for terminating task>'."
                ))

        return diagnostics

    def validate_dag(self, tasks: List[TaskItem]) -> List[Diagnostic]:
        diagnostics: List[Diagnostic] = []
        task_map: Dict[str, TaskItem] = {task.id: task for task in tasks if task.id}

        # 1. Dependency existence & self-dependency checks
        for task in tasks:
            if not task.id:
                continue
            for dep_id in task.depends_on:
                if dep_id == task.id:
                    diagnostics.append(Diagnostic(
                        line=task.line_number,
                        column=1,
                        rule_id="SELF_DEPENDENCY",
                        severity="ERROR",
                        message=f"Task '{task.id}' cannot depend on itself.",
                        snippet=f"depends_on: [{dep_id}]",
                        suggested_fix=f"Remove '{dep_id}' from depends_on."
                    ))
                elif dep_id not in task_map:
                    diagnostics.append(Diagnostic(
                        line=task.line_number,
                        column=1,
                        rule_id="UNKNOWN_DEPENDENCY",
                        severity="ERROR",
                        message=f"Task '{task.id}' depends on unknown task ID '{dep_id}'.",
                        snippet=f"depends_on: [{dep_id}]",
                        suggested_fix=f"Ensure '{dep_id}' is defined in the document."
                    ))

        # 2. Cycle detection via DFS
        visited: Dict[str, int] = {}  # 0 = unvisited, 1 = visiting, 2 = visited
        cycle_path: List[str] = []

        def dfs(node_id: str, path: List[str]) -> bool:
            visited[node_id] = 1
            path.append(node_id)

            node_task = task_map.get(node_id)
            if node_task:
                for neighbor_id in node_task.depends_on:
                    if neighbor_id not in task_map:
                        continue
                    if visited.get(neighbor_id, 0) == 1:
                        # Cycle found!
                        cycle_index = path.index(neighbor_id)
                        cycle_path.extend(path[cycle_index:] + [neighbor_id])
                        return True
                    elif visited.get(neighbor_id, 0) == 0:
                        if dfs(neighbor_id, path):
                            return True

            path.pop()
            visited[node_id] = 2
            return False

        for task in tasks:
            if task.id and visited.get(task.id, 0) == 0:
                if dfs(task.id, []):
                    diagnostics.append(Diagnostic(
                        line=task.line_number,
                        column=1,
                        rule_id="CIRCULAR_DEPENDENCY",
                        severity="ERROR",
                        message=f"Circular dependency cycle detected: {' -> '.join(cycle_path)}",
                        snippet=f"Cycle: {' -> '.join(cycle_path)}",
                        suggested_fix="Break the circular dependency cycle in depends_on."
                    ))
                    break

        # 3. State transition validity across dependencies
        for task in tasks:
            if not task.id:
                continue
            if task.status in {"IN_PROGRESS", "VERIFYING", "DONE"}:
                for dep_id in task.depends_on:
                    dep_task = task_map.get(dep_id)
                    if dep_task and dep_task.status != "DONE":
                        diagnostics.append(Diagnostic(
                            line=task.line_number,
                            column=1,
                            rule_id="UNMET_PREREQUISITE_DEPENDENCY",
                            severity="ERROR",
                            message=f"Task '{task.id}' has status '{task.status}' but prerequisite '{dep_id}' has status '{dep_task.status}' (expected 'DONE').",
                            snippet=f"status: {task.status}, depends_on: [{dep_id}]",
                            suggested_fix=f"Complete prerequisite '{dep_id}' or revert '{task.id}' to 'TODO'."
                        ))

        return diagnostics

    def validate_ace(self, tasks: List[TaskItem], content: str) -> List[Diagnostic]:
        diagnostics: List[Diagnostic] = []

        for task in tasks:
            # Check acceptance criteria for ACE rules
            for idx, criterion in enumerate(task.acceptance_criteria, start=1):
                clean_crit = criterion.strip()
                if not clean_crit:
                    continue

                words = re.findall(r"\b[A-Za-z0-9'-]+\b", clean_crit.lower())
                # Sentence length check
                if len(words) > 25:
                    diagnostics.append(Diagnostic(
                        line=task.line_number,
                        column=1,
                        rule_id="ACE_SENTENCE_LENGTH",
                        severity="WARNING",
                        message=f"Task '{task.id}' criterion {idx} exceeds 25 words ({len(words)} words).",
                        snippet=criterion,
                        suggested_fix="Split long criterion into atomic sentences."
                    ))

                # Forbidden modals
                for word in words:
                    if word in FORBIDDEN_MODALS:
                        diagnostics.append(Diagnostic(
                            line=task.line_number,
                            column=1,
                            rule_id="ACE_FORBIDDEN_MODAL",
                            severity="ERROR",
                            message=f"Task '{task.id}' criterion {idx} contains forbidden modal '{word}'.",
                            snippet=criterion,
                            suggested_fix=f"Replace '{word}' with {FORBIDDEN_MODALS[word]}."
                        ))

                # Ambiguous words
                for word in words:
                    if word in FORBIDDEN_AMBIGUOUS_WORDS:
                        diagnostics.append(Diagnostic(
                            line=task.line_number,
                            column=1,
                            rule_id="ACE_AMBIGUOUS_WORD",
                            severity="ERROR",
                            message=f"Task '{task.id}' criterion {idx} contains ambiguous word '{word}'.",
                            snippet=criterion,
                            suggested_fix=f"Replace '{word}' with {FORBIDDEN_AMBIGUOUS_WORDS[word]}."
                        ))

                # Passive voice heuristic (be-verb + past participle)
                for w_idx in range(len(words) - 1):
                    be_verbs = {"is", "are", "was", "were", "be", "being", "been"}
                    if words[w_idx] in be_verbs and words[w_idx + 1] in PASSIVE_PAST_PARTICIPLES:
                        diagnostics.append(Diagnostic(
                            line=task.line_number,
                            column=1,
                            rule_id="ACE_PASSIVE_VOICE",
                            severity="ERROR",
                            message=f"Task '{task.id}' criterion {idx} uses passive voice ('{words[w_idx]} {words[w_idx + 1]}').",
                            snippet=criterion,
                            suggested_fix="Rephrase into active SVO (Subject-Verb-Object)."
                        ))

        return diagnostics

    def get_status_summary(self, tasks: List[TaskItem]) -> Dict[str, Any]:
        task_map = {task.id: task for task in tasks if task.id}
        counts = {status: 0 for status in VALID_STATUSES}
        for task in tasks:
            if task.status in counts:
                counts[task.status] += 1

        ready_tasks: List[str] = []
        blocked_tasks: List[str] = []
        in_progress_tasks: List[str] = []
        completed_tasks: List[str] = []
        aborted_tasks: List[str] = []

        for task in tasks:
            if not task.id:
                continue
            if task.status == "TODO":
                all_deps_done = all(
                    task_map.get(dep_id) and task_map[dep_id].status == "DONE"
                    for dep_id in task.depends_on
                )
                if all_deps_done:
                    ready_tasks.append(task.id)
                else:
                    blocked_tasks.append(task.id)
            elif task.status in {"IN_PROGRESS", "VERIFYING"}:
                in_progress_tasks.append(task.id)
            elif task.status == "DONE":
                completed_tasks.append(task.id)
            elif task.status == "ABORTED":
                aborted_tasks.append(task.id)

        is_terminal = len(tasks) > 0 and (len(completed_tasks) + len(aborted_tasks) == len(tasks))

        return {
            "total_tasks": len(tasks),
            "counts": counts,
            "ready_tasks": ready_tasks,
            "blocked_tasks": blocked_tasks,
            "in_progress_tasks": in_progress_tasks,
            "completed_tasks": completed_tasks,
            "aborted_tasks": aborted_tasks,
            "is_terminal": is_terminal
        }

    def validate_text(
        self,
        content: str,
        check_schema: bool = True,
        check_dag: bool = True,
        check_ace: bool = True
    ) -> Tuple[List[TaskItem], List[Diagnostic], Dict[str, Any]]:
        tasks, parse_diags = self.parse_document(content)
        diagnostics = list(parse_diags)

        if check_schema:
            diagnostics.extend(self.validate_schema(tasks, content))

        if check_dag and not any(d.rule_id == "YAML_SYNTAX_ERROR" for d in diagnostics):
            diagnostics.extend(self.validate_dag(tasks))

        if check_ace:
            diagnostics.extend(self.validate_ace(tasks, content))

        summary = self.get_status_summary(tasks)
        return tasks, diagnostics, summary


def format_cli_output(
    file_label: str,
    tasks: List[TaskItem],
    diagnostics: List[Diagnostic],
    summary: Dict[str, Any],
    show_status: bool = True
) -> str:
    output = []
    error_count = len([d for d in diagnostics if d.severity == "ERROR"])
    warn_count = len([d for d in diagnostics if d.severity == "WARNING"])

    if error_count == 0:
        output.append(f"\033[92m✔ {file_label}: Valid ({len(tasks)} task(s), {warn_count} warning(s))\033[0m")
    else:
        output.append(f"\033[91m✖ {file_label}: {error_count} error(s), {warn_count} warning(s) found:\033[0m\n")
        for d in diagnostics:
            color = "\033[91m" if d.severity == "ERROR" else "\033[93m"
            output.append(f"  {color}[{d.severity}][{d.rule_id}]\033[0m Line {d.line}:{d.column} - {d.message}")
            if d.snippet:
                output.append(f"    \033[90mSnippet:\033[0m {d.snippet}")
            if d.suggested_fix:
                output.append(f"    \033[36mFix:\033[0m     {d.suggested_fix}\n")

    if show_status and summary:
        output.append("\n\033[1mTask Graph Status:\033[0m")
        output.append(f"  Total Tasks: {summary['total_tasks']}")
        output.append(f"  Counts: TODO={summary['counts'].get('TODO', 0)}, "
                      f"IN_PROGRESS={summary['counts'].get('IN_PROGRESS', 0)}, "
                      f"VERIFYING={summary['counts'].get('VERIFYING', 0)}, "
                      f"DONE={summary['counts'].get('DONE', 0)}, "
                      f"ABORTED={summary['counts'].get('ABORTED', 0)}")
        if summary.get("ready_tasks"):
            output.append(f"  \033[92mReady to Execute (Unblocked TODO):\033[0m {', '.join(summary['ready_tasks'])}")
        if summary.get("blocked_tasks"):
            output.append(f"  \033[93mBlocked Tasks:\033[0m {', '.join(summary['blocked_tasks'])}")
        if summary.get("in_progress_tasks"):
            output.append(f"  \033[36mIn Progress / Verifying:\033[0m {', '.join(summary['in_progress_tasks'])}")
        if summary.get("is_terminal"):
            output.append("  \033[92mStatus: All tasks reached terminal state (ready to archive).\033[0m")

    return "\n".join(output)


def main():
    parser = argparse.ArgumentParser(
        description="Task Graph, Schema, and ACE Specification Validator (task skill)"
    )
    parser.add_argument(
        "target",
        nargs="?",
        default=None,
        help="Target task markdown file to validate, or '-' for stdin (default: docs/.tasks/active.md)"
    )
    parser.add_argument("--json", action="store_true", help="Output machine-readable JSON diagnostics")
    parser.add_argument("--check-schema", action="store_true", help="Run schema validation only")
    parser.add_argument("--check-dag", action="store_true", help="Run DAG dependency validation only")
    parser.add_argument("--check-ace", action="store_true", help="Run ACE acceptance criteria linting only")
    parser.add_argument("--status", action="store_true", help="Display task status and unblocked tasks")
    parser.add_argument("--all", action="store_true", help="Run all validation checks (default)")

    args = parser.parse_args()

    # Determine validation modes
    if args.check_schema or args.check_dag or args.check_ace:
        run_schema = args.check_schema
        run_dag = args.check_dag
        run_ace = args.check_ace
    else:
        run_schema = True
        run_dag = True
        run_ace = True

    validator = TaskValidator()

    # Target resolution
    target = args.target
    if target is None:
        default_active = os.path.join(os.getcwd(), "docs", ".tasks", "active.md")
        if os.path.exists(default_active):
            target = default_active
        else:
            target = "-"

    # 1. Stdin mode
    if target == "-":
        content = sys.stdin.read()
        tasks, diagnostics, summary = validator.validate_text(
            content,
            check_schema=run_schema,
            check_dag=run_dag,
            check_ace=run_ace
        )
        error_count = len([d for d in diagnostics if d.severity == "ERROR"])
        warn_count = len([d for d in diagnostics if d.severity == "WARNING"])

        if args.json:
            print(json.dumps({
                "target": "stdin",
                "valid": error_count == 0,
                "error_count": error_count,
                "warning_count": warn_count,
                "status_summary": summary,
                "tasks": [t.to_dict() for t in tasks],
                "errors": [d.to_dict() for d in diagnostics]
            }, indent=2))
        else:
            print(format_cli_output("stdin", tasks, diagnostics, summary, show_status=True))
        sys.exit(1 if error_count > 0 else 0)

    # 2. File mode
    target_path = os.path.abspath(target)
    if not os.path.exists(target_path):
        sys.stderr.write(f"Error: Target task file '{target_path}' does not exist.\n")
        sys.exit(2)

    with open(target_path, "r", encoding="utf-8") as f:
        content = f.read()

    tasks, diagnostics, summary = validator.validate_text(
        content,
        check_schema=run_schema,
        check_dag=run_dag,
        check_ace=run_ace
    )
    error_count = len([d for d in diagnostics if d.severity == "ERROR"])
    warn_count = len([d for d in diagnostics if d.severity == "WARNING"])

    if args.json:
        print(json.dumps({
            "total_files": 1,
            "clean_files": 1 if error_count == 0 else 0,
            "results": [
                {
                    "file": target_path,
                    "valid": error_count == 0,
                    "error_count": error_count,
                    "warning_count": warn_count,
                    "status_summary": summary,
                    "tasks": [t.to_dict() for t in tasks],
                    "errors": [d.to_dict() for d in diagnostics]
                }
            ]
        }, indent=2))
    else:
        print(format_cli_output(os.path.relpath(target_path), tasks, diagnostics, summary, show_status=True))

    sys.exit(1 if error_count > 0 else 0)


if __name__ == "__main__":
    main()
