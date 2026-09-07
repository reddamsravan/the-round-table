#!/usr/bin/env python3
"""
PO Story Specification Validator.

Validates sprint story specifications (e.g. docs/.prompts-and-prayers/sprints/sprint-1/01-stories/spec.md) for:
1. Frontmatter handover schema (sprint, persona: po, status, handoff_to: ux-designer, artifacts).
2. Document structure (Sprint Goal, Target Personas, Scope Boundaries, User Stories).
3. Story narrative formula (As a... I want... So that...).
4. Agentic ACE acceptance criteria (SVO active voice, permitted modals SHALL/MUST, no forbidden terms).
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


class StoryItem:
    def __init__(self, story_id: str, title: str, narrative: str, criteria: List[str], line_number: int):
        self.story_id = story_id
        self.title = title
        self.narrative = narrative
        self.criteria = criteria
        self.line_number = line_number

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.story_id,
            "title": self.title,
            "narrative": self.narrative,
            "criteria": self.criteria,
            "line_number": self.line_number,
        }


class POValidator:
    def __init__(self):
        self.diagnostics: List[Diagnostic] = []

    def validate_text(
        self,
        content: str,
        check_schema: bool = True,
        check_invest: bool = True,
        check_ace: bool = True,
    ) -> Tuple[List[StoryItem], List[Diagnostic], Dict[str, Any]]:
        self.diagnostics = []
        lines = content.splitlines()

        frontmatter, body_start_idx = self._parse_frontmatter(lines)
        metadata = {}

        if check_schema:
            metadata = self._validate_frontmatter(frontmatter)
            self._validate_required_sections(lines)

        stories = self._extract_stories(lines)

        if check_invest:
            self._validate_invest_narratives(stories, lines)

        if check_ace:
            self._validate_ace_criteria(stories, lines)

        summary = {
            "sprint": metadata.get("sprint", "unknown"),
            "status": metadata.get("status", "unknown"),
            "persona": metadata.get("persona", "unknown"),
            "total_stories": len(stories),
            "story_ids": [s.story_id for s in stories],
        }

        return stories, self.diagnostics, summary

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

    def _validate_frontmatter(self, yaml_text: Optional[str]) -> Dict[str, Any]:
        if not yaml_text:
            return {}

        if yaml is None:
            # Basic fallback parser if pyyaml is missing
            meta = {}
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
                    Diagnostic(1, 1, "YAML_SYNTAX_ERROR", "ERROR", f"Invalid YAML frontmatter: {e}")
                )
                return {}

        # Required keys
        required_keys = ["sprint", "persona", "status", "handoff_to", "artifacts"]
        for rk in required_keys:
            if rk not in data:
                self.diagnostics.append(
                    Diagnostic(1, 1, "SCHEMA_MISSING_KEY", "ERROR", f"Frontmatter missing mandatory key '{rk}'.")
                )

        if data.get("persona") != "po":
            self.diagnostics.append(
                Diagnostic(1, 1, "SCHEMA_INVALID_PERSONA", "ERROR", f"Frontmatter 'persona' must be 'po', found '{data.get('persona')}'.")
            )

        status = data.get("status")
        if status not in VALID_STATUSES:
            self.diagnostics.append(
                Diagnostic(1, 1, "SCHEMA_INVALID_STATUS", "ERROR", f"Frontmatter 'status' must be one of {sorted(VALID_STATUSES)}, found '{status}'.")
            )

        if data.get("handoff_to") != "ux-designer":
            self.diagnostics.append(
                Diagnostic(1, 1, "SCHEMA_INVALID_HANDOFF", "ERROR", f"Frontmatter 'handoff_to' must be 'ux-designer', found '{data.get('handoff_to')}'.")
            )

        artifacts = data.get("artifacts")
        if not isinstance(artifacts, list) or len(artifacts) == 0:
            self.diagnostics.append(
                Diagnostic(1, 1, "SCHEMA_INVALID_ARTIFACTS", "ERROR", "Frontmatter 'artifacts' must be a non-empty list.")
            )

        return data

    def _validate_required_sections(self, lines: List[str]):
        headings = [line.strip() for line in lines if line.startswith("#")]
        required_patterns = [
            (r"^#\s+Sprint Specification:", "Title '# Sprint Specification: <Title>'"),
            (r"^##\s+1\.\s+Sprint Goal", "Section '## 1. Sprint Goal'"),
            (r"^##\s+2\.\s+Target Personas", "Section '## 2. Target Personas'"),
            (r"^##\s+3\.\s+Scope Boundaries", "Section '## 3. Scope Boundaries'"),
            (r"^##\s+4\.\s+User Stories", "Section '## 4. User Stories'"),
        ]

        for pattern, label in required_patterns:
            if not any(re.search(pattern, h) for h in headings):
                self.diagnostics.append(
                    Diagnostic(1, 1, "STRUCTURE_MISSING_SECTION", "ERROR", f"Document missing mandatory section: {label}.")
                )

    def _extract_stories(self, lines: List[str]) -> List[StoryItem]:
        stories = []
        current_id = None
        current_title = None
        current_narrative = []
        current_criteria = []
        start_line = 0
        in_criteria = False

        story_header_re = re.compile(r"^###\s+Story:\s+(US-\d+)\s+-\s+(.+)$")

        for idx, raw_line in enumerate(lines, start=1):
            line = raw_line.strip()
            m = story_header_re.match(line)
            if m:
                if current_id:
                    stories.append(StoryItem(
                        current_id, current_title, " ".join(current_narrative).strip(), current_criteria, start_line
                    ))
                current_id = m.group(1)
                current_title = m.group(2).strip()
                current_narrative = []
                current_criteria = []
                start_line = idx
                in_criteria = False
                continue

            if current_id:
                if line.startswith("### ") or (line.startswith("## ") and not line.startswith("## 4.")):
                    # Next section
                    stories.append(StoryItem(
                        current_id, current_title, " ".join(current_narrative).strip(), current_criteria, start_line
                    ))
                    current_id = None
                    continue

                if "Acceptance Criteria" in line:
                    in_criteria = True
                    continue

                if in_criteria:
                    if line.startswith("- ") or line.startswith("* "):
                        current_criteria.append(line[2:].strip())
                    elif line.startswith("GIVEN ") or line.startswith("WHEN ") or line.startswith("THEN ") or line.startswith("INVARIANT "):
                        current_criteria.append(line)
                else:
                    if line and not line.startswith("**Narrative**"):
                        current_narrative.append(line)

        if current_id:
            stories.append(StoryItem(
                current_id, current_title, " ".join(current_narrative).strip(), current_criteria, start_line
            ))

        return stories

    def _validate_invest_narratives(self, stories: List[StoryItem], lines: List[str]):
        if not stories:
            self.diagnostics.append(
                Diagnostic(1, 1, "STORIES_EMPTY", "ERROR", "Document MUST contain at least one user story under '## 4. User Stories'.")
            )
            return

        for story in stories:
            narrative = story.narrative.lower()
            if "as a" not in narrative or "i want" not in narrative or "so that" not in narrative:
                self.diagnostics.append(
                    Diagnostic(
                        story.line_number,
                        1,
                        "INVEST_FORMULA_VIOLATION",
                        "ERROR",
                        f"Story '{story.story_id}' narrative MUST adhere to formula: 'As a... I want... So that...'",
                        story.narrative,
                    )
                )

            if not story.criteria:
                self.diagnostics.append(
                    Diagnostic(
                        story.line_number,
                        1,
                        "CRITERIA_EMPTY",
                        "ERROR",
                        f"Story '{story.story_id}' MUST define at least one acceptance criterion.",
                    )
                )

    def _validate_ace_criteria(self, stories: List[StoryItem], lines: List[str]):
        for story in stories:
            for c_idx, criterion in enumerate(story.criteria, start=1):
                # Check modal verbs
                words = re.findall(r"\b[A-Za-z0-9'-]+\b", criterion)
                for w in words:
                    wl = w.lower()
                    if wl in FORBIDDEN_MODALS:
                        self.diagnostics.append(
                            Diagnostic(
                                story.line_number,
                                1,
                                "FORBIDDEN_MODAL",
                                "ERROR",
                                f"Criterion {c_idx} in '{story.story_id}' contains forbidden modal '{w}'. Use {FORBIDDEN_MODALS[wl]}.",
                                criterion,
                            )
                        )
                    if wl in FORBIDDEN_AMBIGUOUS_WORDS:
                        self.diagnostics.append(
                            Diagnostic(
                                story.line_number,
                                1,
                                "AMBIGUOUS_WORD",
                                "ERROR",
                                f"Criterion {c_idx} in '{story.story_id}' contains vague term '{w}'. Suggested fix: {FORBIDDEN_AMBIGUOUS_WORDS[wl]}.",
                                criterion,
                            )
                        )

                # Check passive voice (e.g. "is done", "be resolved", "was created")
                passive_match = re.search(r"\b(is|are|was|were|be|been|being)\s+([a-z]+ed|[a-z]+en)\b", criterion, re.IGNORECASE)
                if passive_match:
                    verb_part = passive_match.group(2).lower()
                    if verb_part in IRREGULAR_PAST_PARTICIPLES or verb_part.endswith("ed"):
                        self.diagnostics.append(
                            Diagnostic(
                                story.line_number,
                                1,
                                "PASSIVE_VOICE",
                                "ERROR",
                                f"Criterion {c_idx} in '{story.story_id}' contains passive voice '{passive_match.group(0)}'. Use active SVO.",
                                criterion,
                            )
                        )


def format_cli_output(target: str, stories: List[StoryItem], diagnostics: List[Diagnostic], summary: Dict[str, Any]) -> str:
    errors = [d for d in diagnostics if d.severity == "ERROR"]
    warnings = [d for d in diagnostics if d.severity == "WARNING"]
    lines = []
    lines.append("=" * 70)
    lines.append(f"PO STORY VALIDATOR: {target}")
    lines.append("=" * 70)
    lines.append(f"Sprint:  {summary.get('sprint', 'unknown')}")
    lines.append(f"Status:  {summary.get('status', 'unknown')}")
    lines.append(f"Stories: {summary.get('total_stories', 0)} ({', '.join(summary.get('story_ids', []))})")
    lines.append("-" * 70)

    if errors:
        lines.append(f"ERRORS ({len(errors)}):")
        for e in errors:
            lines.append(f"  [Line {e.line}] {e.rule_id}: {e.message}")
            if e.snippet:
                lines.append(f"    Snippet: {e.snippet}")
    else:
        lines.append("No errors found. Specification is clean!")

    if warnings:
        lines.append(f"WARNINGS ({len(warnings)}):")
        for w in warnings:
            lines.append(f"  [Line {w.line}] {w.rule_id}: {w.message}")

    lines.append("=" * 70)
    lines.append("RESULT: " + ("PASS" if len(errors) == 0 else "FAIL"))
    lines.append("=" * 70)
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="PO Story Specification Validator")
    parser.add_argument("target", nargs="?", default=None, help="Target markdown story spec to validate")
    parser.add_argument("--sprint", "-s", type=str, default=None, help="Sprint identifier (e.g. sprint-1)")
    parser.add_argument("--check-schema", action="store_true", help="Run schema & section checks only")
    parser.add_argument("--check-invest", action="store_true", help="Run INVEST story checks only")
    parser.add_argument("--check-ace", action="store_true", help="Run ACE linguistic linting only")
    parser.add_argument("--all", action="store_true", help="Run all checks (default)")
    parser.add_argument("--json", action="store_true", help="Output JSON results")

    args = parser.parse_args()

    run_schema = True
    run_invest = True
    run_ace = True

    if args.check_schema or args.check_invest or args.check_ace:
        run_schema = args.check_schema
        run_invest = args.check_invest
        run_ace = args.check_ace

    target = args.target
    if target is None:
        if args.sprint:
            candidate = os.path.join(os.getcwd(), "docs", ".prompts-and-prayers", "sprints", args.sprint, "01-stories", "spec.md")
            if os.path.exists(candidate):
                target = candidate
        if target is None:
            # Auto-detect latest sprint
            sprints_dir = os.path.join(os.getcwd(), "docs", ".prompts-and-prayers", "sprints")
            if os.path.isdir(sprints_dir):
                sprint_entries = sorted(
                    [d for d in os.listdir(sprints_dir) if os.path.isdir(os.path.join(sprints_dir, d))],
                    reverse=True
                )
                for sp in sprint_entries:
                    candidate = os.path.join(sprints_dir, sp, "01-stories", "spec.md")
                    if os.path.exists(candidate):
                        target = candidate
                        break
        if target is None:
            target = "-"

    validator = POValidator()

    if target == "-":
        content = sys.stdin.read()
        stories, diags, summary = validator.validate_text(
            content, check_schema=run_schema, check_invest=run_invest, check_ace=run_ace
        )
        error_count = len([d for d in diags if d.severity == "ERROR"])
        warn_count = len([d for d in diags if d.severity == "WARNING"])

        if args.json:
            print(json.dumps({
                "target": "stdin",
                "valid": error_count == 0,
                "error_count": error_count,
                "warning_count": warn_count,
                "summary": summary,
                "stories": [s.to_dict() for s in stories],
                "errors": [d.to_dict() for d in diags]
            }, indent=2))
        else:
            print(format_cli_output("stdin", stories, diags, summary))
        sys.exit(1 if error_count > 0 else 0)

    target_path = os.path.abspath(target)
    if not os.path.exists(target_path):
        sys.stderr.write(f"Error: Target file '{target_path}' does not exist.\n")
        sys.exit(2)

    with open(target_path, "r", encoding="utf-8") as f:
        content = f.read()

    stories, diags, summary = validator.validate_text(
        content, check_schema=run_schema, check_invest=run_invest, check_ace=run_ace
    )
    error_count = len([d for d in diags if d.severity == "ERROR"])
    warn_count = len([d for d in diags if d.severity == "WARNING"])

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
                    "summary": summary,
                    "stories": [s.to_dict() for s in stories],
                    "errors": [d.to_dict() for d in diags]
                }
            ]
        }, indent=2))
    else:
        print(format_cli_output(os.path.relpath(target_path), stories, diags, summary))

    sys.exit(1 if error_count > 0 else 0)


if __name__ == "__main__":
    main()
