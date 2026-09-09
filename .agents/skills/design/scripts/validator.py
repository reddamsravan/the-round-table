#!/usr/bin/env python3
"""
Design Skill Specification Validator.

Validates design specifications (e.g. docs/.prompts-and-prayers/{work_slug}/02-design/design-spec.md) for:
1. Frontmatter governance envelope (slug, status, approved_by, artifacts).
2. Mandatory section structure:
   - # Design Specification: <Title> (or # UX Design Specification: <Title>)
   - ## 1. User Journey & Interaction Flow
   - ## 2. Screen State Transitions
   - ## 3. UI Layout & Component Specifications
   - ## 4. Accessibility & Responsive Requirements
3. Valid Mermaid code fences (flowcharts in Section 1, state diagrams in Section 2) and no ASCII art boxes.
4. Agentic ACE validation on accessibility requirements.
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


class DesignValidator:
    def __init__(self):
        self.diagnostics: List[Diagnostic] = []

    def validate_text(
        self,
        content: str,
        target_path: Optional[str] = None,
        check_schema: bool = True,
        check_diagrams: bool = True,
        check_ace: bool = True,
    ) -> Tuple[List[Diagnostic], Dict[str, Any]]:
        self.diagnostics = []
        lines = content.splitlines()

        frontmatter, _ = self._parse_frontmatter(lines)
        metadata: Dict[str, Any] = {}

        if check_schema:
            metadata = self._validate_frontmatter(frontmatter)
            self._validate_required_sections(lines)

        mermaid_blocks = self._extract_mermaid_blocks(lines)

        if check_diagrams:
            self._validate_diagrams(lines, mermaid_blocks)
            self._check_for_ascii_art(lines)

        if check_ace:
            self._validate_accessibility_ace(lines)

        summary = {
            "slug": metadata.get("slug", "unknown"),
            "status": metadata.get("status", "unknown"),
            "mermaid_blocks_count": len(mermaid_blocks),
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

    def _validate_frontmatter(self, yaml_text: Optional[str]) -> Dict[str, Any]:
        if not yaml_text:
            return {}

        if yaml is None:
            meta: Dict[str, Any] = {}
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

        required_keys = ["slug", "status", "approved_by", "artifacts"]
        for rk in required_keys:
            if rk not in data:
                self.diagnostics.append(
                    Diagnostic(1, 1, "SCHEMA_MISSING_KEY", "ERROR", f"Frontmatter missing mandatory key '{rk}'.")
                )

        status = data.get("status")
        if status and status not in VALID_STATUSES:
            self.diagnostics.append(
                Diagnostic(1, 1, "SCHEMA_INVALID_STATUS", "ERROR", f"Frontmatter 'status' must be one of {sorted(VALID_STATUSES)}, found '{status}'.")
            )

        approved_by = data.get("approved_by")
        if approved_by and approved_by not in {"pending", "human"}:
            self.diagnostics.append(
                Diagnostic(1, 1, "SCHEMA_INVALID_APPROVED_BY", "ERROR", f"Frontmatter 'approved_by' must be 'pending' or 'human', found '{approved_by}'.")
            )

        artifacts = data.get("artifacts")
        if "artifacts" in data:
            if not isinstance(artifacts, list) or len(artifacts) == 0:
                self.diagnostics.append(
                    Diagnostic(1, 1, "SCHEMA_INVALID_ARTIFACTS", "ERROR", "Frontmatter 'artifacts' must be a non-empty list.")
                )

        return data

    def _validate_required_sections(self, lines: List[str]):
        required_patterns = [
            (r"^#\s+(?:UX\s+)?Design Specification:", "Title '# Design Specification: <Title>'"),
            (r"^##\s+1\.\s+User Journey & Interaction Flow", "Section '## 1. User Journey & Interaction Flow'"),
            (r"^##\s+2\.\s+Screen State Transitions", "Section '## 2. Screen State Transitions'"),
            (r"^##\s+3\.\s+UI Layout & Component Specifications", "Section '## 3. UI Layout & Component Specifications'"),
            (r"^##\s+4\.\s+Accessibility & Responsive Requirements", "Section '## 4. Accessibility & Responsive Requirements'"),
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
                    Diagnostic(1, 1, "STRUCTURE_MISSING_SECTION", "ERROR", f"Document missing mandatory section: {label}.")
                )
            else:
                found_indices.append((matched_line, label))

        if len(found_indices) == len(required_patterns):
            line_numbers = [idx for idx, _ in found_indices]
            if line_numbers != sorted(line_numbers):
                self.diagnostics.append(
                    Diagnostic(
                        1, 1, "SECTION_ORDER_INVALID", "ERROR",
                        "Sections appear out of required sequential order."
                    )
                )

    def _extract_mermaid_blocks(self, lines: List[str]) -> List[Tuple[int, str]]:
        blocks = []
        in_mermaid = False
        current_block = []
        start_line = 0

        for idx, line in enumerate(lines, start=1):
            s = line.strip()
            if s.startswith("```mermaid"):
                in_mermaid = True
                start_line = idx
                current_block = []
                continue
            elif s.startswith("```") and in_mermaid:
                in_mermaid = False
                blocks.append((start_line, "\n".join(current_block)))
                continue

            if in_mermaid:
                current_block.append(line)

        return blocks

    def _validate_diagrams(self, lines: List[str], mermaid_blocks: List[Tuple[int, str]]):
        if not mermaid_blocks:
            self.diagnostics.append(
                Diagnostic(1, 1, "MERMAID_MISSING", "ERROR", "Document MUST contain valid Mermaid code blocks in Sections 1 and 2.")
            )
            return

        has_flowchart = False
        has_statediagram = False

        for start_line, block in mermaid_blocks:
            b_lower = block.lower().strip()
            if b_lower.startswith("flowchart") or b_lower.startswith("graph"):
                has_flowchart = True
            elif b_lower.startswith("statediagram") or b_lower.startswith("statediagram-v2"):
                has_statediagram = True

        if not has_flowchart:
            self.diagnostics.append(
                Diagnostic(1, 1, "FLOWCHART_MISSING", "ERROR", "Section 1 MUST contain a Mermaid flowchart ('flowchart TD' or 'flowchart LR').")
            )

        if not has_statediagram:
            self.diagnostics.append(
                Diagnostic(1, 1, "STATE_DIAGRAM_MISSING", "ERROR", "Section 2 MUST contain a Mermaid state diagram ('stateDiagram-v2').")
            )

    def _check_for_ascii_art(self, lines: List[str]):
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
                        "ASCII art box diagrams are forbidden. Use plain text descriptions and Mermaid diagrams.",
                        line
                    )
                )

    def _validate_accessibility_ace(self, lines: List[str]):
        in_a11y = False
        for idx, line in enumerate(lines, start=1):
            s = line.strip()
            if s.startswith("## 4. Accessibility"):
                in_a11y = True
                continue
            elif s.startswith("## ") and in_a11y:
                break

            if in_a11y and (s.startswith("- ") or s.startswith("* ")):
                text = s[2:].strip()
                words = re.findall(r"\b[A-Za-z0-9'-]+\b", text)
                for w in words:
                    wl = w.lower()
                    if wl in FORBIDDEN_MODALS:
                        self.diagnostics.append(
                            Diagnostic(
                                idx, 1, "FORBIDDEN_MODAL", "ERROR",
                                f"Accessibility criterion contains forbidden modal '{w}'. Use {FORBIDDEN_MODALS[wl]}.",
                                text
                            )
                        )
                    if wl in FORBIDDEN_AMBIGUOUS_WORDS:
                        self.diagnostics.append(
                            Diagnostic(
                                idx, 1, "AMBIGUOUS_WORD", "ERROR",
                                f"Accessibility criterion contains vague term '{w}'. Suggested fix: {FORBIDDEN_AMBIGUOUS_WORDS[wl]}.",
                                text
                            )
                        )

                passive_match = re.search(r"\b(is|are|was|were|be|been|being)\s+([a-z]+ed|[a-z]+en)\b", text, re.IGNORECASE)
                if passive_match:
                    verb_part = passive_match.group(2).lower()
                    if verb_part in IRREGULAR_PAST_PARTICIPLES or verb_part.endswith("ed"):
                        self.diagnostics.append(
                            Diagnostic(
                                idx, 1, "PASSIVE_VOICE", "ERROR",
                                f"Accessibility criterion contains passive voice '{passive_match.group(0)}'. Use active SVO.",
                                text
                            )
                        )


def format_cli_output(target: str, diagnostics: List[Diagnostic], summary: Dict[str, Any]) -> str:
    errors = [d for d in diagnostics if d.severity == "ERROR"]
    warnings = [d for d in diagnostics if d.severity == "WARNING"]
    lines = []
    lines.append("=" * 70)
    lines.append(f"DESIGN SPEC VALIDATOR: {target}")
    lines.append("=" * 70)
    lines.append(f"Slug:           {summary.get('slug', 'unknown')}")
    lines.append(f"Status:         {summary.get('status', 'unknown')}")
    lines.append(f"Mermaid Blocks: {summary.get('mermaid_blocks_count', 0)}")
    lines.append("-" * 70)

    if errors:
        lines.append(f"ERRORS ({len(errors)}):")
        for e in errors:
            lines.append(f"  [Line {e.line}] {e.rule_id}: {e.message}")
            if e.snippet:
                lines.append(f"    Snippet: {e.snippet}")
    else:
        lines.append("No errors found. Design specification is clean!")

    if warnings:
        lines.append(f"WARNINGS ({len(warnings)}):")
        for w in warnings:
            lines.append(f"  [Line {w.line}] {w.rule_id}: {w.message}")

    lines.append("=" * 70)
    lines.append("RESULT: " + ("PASS" if len(errors) == 0 else "FAIL"))
    lines.append("=" * 70)
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Design Skill Specification Validator")
    parser.add_argument("target", nargs="?", default=None, help="Target markdown design spec to validate")
    parser.add_argument("--slug", "-s", type=str, default=None, help="Work slug identifier")
    parser.add_argument("--check-schema", action="store_true", help="Run schema & section checks only")
    parser.add_argument("--check-diagrams", action="store_true", help="Run Mermaid diagram checks only")
    parser.add_argument("--check-ace", action="store_true", help="Run ACE accessibility checks only")
    parser.add_argument("--all", action="store_true", help="Run all checks (default)")
    parser.add_argument("--json", action="store_true", help="Output machine-readable JSON results")

    args = parser.parse_args()

    run_schema = True
    run_diagrams = True
    run_ace = True

    if args.check_schema or args.check_diagrams or args.check_ace:
        run_schema = args.check_schema
        run_diagrams = args.check_diagrams
        run_ace = args.check_ace

    target = args.target
    if target is None:
        if args.slug:
            candidate = os.path.join(os.getcwd(), "docs", ".prompts-and-prayers", args.slug, "02-design", "design-spec.md")
            if os.path.exists(candidate):
                target = candidate
        if target is None:
            base_dir = os.path.join(os.getcwd(), "docs", ".prompts-and-prayers")
            if os.path.isdir(base_dir):
                for entry in sorted(os.listdir(base_dir), reverse=True):
                    candidate = os.path.join(base_dir, entry, "02-design", "design-spec.md")
                    if os.path.exists(candidate):
                        target = candidate
                        break
        if target is None:
            target = "-"

    validator = DesignValidator()

    if target == "-":
        content = sys.stdin.read()
        diags, summary = validator.validate_text(
            content, target_path=None, check_schema=run_schema, check_diagrams=run_diagrams,
            check_ace=run_ace
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
                "errors": [d.to_dict() for d in diags]
            }, indent=2))
        else:
            print(format_cli_output("stdin", diags, summary))
        sys.exit(1 if error_count > 0 else 0)

    target_path = os.path.abspath(target)
    if not os.path.exists(target_path):
        sys.stderr.write(f"Error: Target file '{target_path}' does not exist.\n")
        sys.exit(2)

    with open(target_path, "r", encoding="utf-8") as f:
        content = f.read()

    diags, summary = validator.validate_text(
        content, target_path=target_path, check_schema=run_schema, check_diagrams=run_diagrams,
        check_ace=run_ace
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
                    "errors": [d.to_dict() for d in diags]
                }
            ]
        }, indent=2))
    else:
        print(format_cli_output(os.path.relpath(target_path), diags, summary))

    sys.exit(1 if error_count > 0 else 0)


if __name__ == "__main__":
    main()
