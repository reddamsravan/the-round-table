#!/usr/bin/env python3
"""
Define Skill Specification Validator.

Validates definition specifications (e.g. docs/.prompts-and-prayers/{work_slug}/01-define/spec.md) for:
1. Frontmatter governance envelope (slug, status, approved_by, artifacts - no persona field).
2. Document structure (5 mandatory section headings in order):
   - # Specification: <Title>
   - ## 1. Objective & Value
   - ## 2. Target Personas
   - ## 3. Scope Boundaries
   - ## 4. Functional Requirements
   - ## 5. Success Metrics & Validation
3. Requirement narrative formula:
   - As a / As an <role>,
   - I want <action>,
   - So that <value>.
4. Agentic ACE acceptance criteria:
   - SVO active voice (no passive voice)
   - Permitted modals (SHALL, MUST only)
   - No ambiguous terms or filler words
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


class RequirementItem:
    def __init__(self, req_id: str, title: str, narrative: str, criteria: List[str], line_number: int):
        self.req_id = req_id
        self.title = title
        self.narrative = narrative
        self.criteria = criteria
        self.line_number = line_number

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.req_id,
            "title": self.title,
            "narrative": self.narrative,
            "criteria": self.criteria,
            "line_number": self.line_number,
        }


class DefineValidator:
    def __init__(self):
        self.diagnostics: List[Diagnostic] = []

    def validate_text(
        self,
        content: str,
        check_schema: bool = True,
        check_narrative: bool = True,
        check_ace: bool = True,
    ) -> Tuple[List[RequirementItem], List[Diagnostic], Dict[str, Any]]:
        self.diagnostics = []
        lines = content.splitlines()

        frontmatter, body_start_idx = self._parse_frontmatter(lines)
        metadata = {}

        if check_schema:
            metadata = self._validate_frontmatter(frontmatter)
            self._validate_required_sections(lines)

        requirements = self._extract_requirements(lines)

        if check_narrative:
            self._validate_narratives(requirements, lines)

        if check_ace:
            self._validate_ace_criteria(requirements, lines)

        summary = {
            "slug": metadata.get("slug", "unknown"),
            "status": metadata.get("status", "unknown"),
            "total_requirements": len(requirements),
            "requirement_ids": [r.req_id for r in requirements],
        }

        return requirements, self.diagnostics, summary

    def _parse_frontmatter(self, lines: List[str]) -> Tuple[Optional[str], int]:
        if not lines or lines[0].strip() != "---":
            self.diagnostics.append(
                Diagnostic(1, 1, "FRONTMATTER_MISSING", "ERROR", "Document MUST start with YAML frontmatter delimiter '---'.")
            )
            return None, 0

        end_idx = -1
        for idx in range(1, len(lines)):
            if lines[idx].strip() == "---":
                end_idx = idx
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

        # Disallow persona key
        if "persona" in data:
            self.diagnostics.append(
                Diagnostic(1, 1, "SCHEMA_FORBIDDEN_KEY", "ERROR", "Frontmatter SHALL NOT contain 'persona' key; define is a verb.")
            )

        # Required keys
        required_keys = ["slug", "status", "approved_by", "artifacts"]
        for rk in required_keys:
            if rk not in data:
                self.diagnostics.append(
                    Diagnostic(1, 1, "SCHEMA_MISSING_KEY", "ERROR", f"Frontmatter missing mandatory key '{rk}'.")
                )

        status = data.get("status")
        if status and status not in VALID_STATUSES:
            self.diagnostics.append(
                Diagnostic(
                    1, 1, "SCHEMA_INVALID_STATUS", "ERROR",
                    f"Invalid status '{status}'. Must be one of: {sorted(list(VALID_STATUSES))}."
                )
            )

        approved_by = data.get("approved_by")
        if approved_by and approved_by not in {"pending", "human"}:
            self.diagnostics.append(
                Diagnostic(1, 1, "SCHEMA_INVALID_APPROVED_BY", "ERROR", f"Invalid approved_by '{approved_by}'. Must be 'pending' or 'human'.")
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
            (r"^#\s+Specification:", "Title '# Specification: <Title>'"),
            (r"^##\s+1\.\s+Objective\s+(?:&|and)\s+Value", "Section '## 1. Objective & Value'"),
            (r"^##\s+2\.\s+Target Personas", "Section '## 2. Target Personas'"),
            (r"^##\s+3\.\s+Scope Boundaries", "Section '## 3. Scope Boundaries'"),
            (r"^##\s+4\.\s+Functional Requirements", "Section '## 4. Functional Requirements'"),
            (r"^##\s+5\.\s+Success Metrics\s+(?:&|and)\s+Validation", "Section '## 5. Success Metrics & Validation'"),
        ]

        found_indices = []
        for pattern, label in required_patterns:
            matched_idx = -1
            for idx, h in enumerate(headings):
                if re.search(pattern, h, re.IGNORECASE):
                    matched_idx = idx
                    break
            if matched_idx == -1:
                self.diagnostics.append(
                    Diagnostic(1, 1, "STRUCTURE_MISSING_SECTION", "ERROR", f"Document missing mandatory section: {label}.")
                )
            else:
                found_indices.append(matched_idx)

        # Check section sequence
        if len(found_indices) == len(required_patterns):
            if found_indices != sorted(found_indices):
                self.diagnostics.append(
                    Diagnostic(
                        1, 1, "SECTION_ORDER_INVALID", "ERROR",
                        "Mandatory sections appear out of sequence. Required order: Title, 1. Objective & Value, 2. Target Personas, 3. Scope Boundaries, 4. Functional Requirements, 5. Success Metrics & Validation."
                    )
                )

    def _extract_requirements(self, lines: List[str]) -> List[RequirementItem]:
        requirements = []
        current_id = None
        current_title = None
        current_narrative = []
        current_criteria = []
        start_line = 0
        in_criteria = False

        req_header_re = re.compile(r"^###\s+Requirement:\s+(REQ-\d+)\s+-\s+(.+)$")

        for idx, raw_line in enumerate(lines, start=1):
            line = raw_line.strip()

            match = req_header_re.match(line)
            if match:
                if current_id:
                    requirements.append(
                        RequirementItem(
                            current_id, current_title, " ".join(current_narrative).strip(),
                            current_criteria, start_line
                        )
                    )
                current_id = match.group(1)
                current_title = match.group(2)
                current_narrative = []
                current_criteria = []
                start_line = idx
                in_criteria = False
                continue

            # Stop extracting at next H2 section
            if line.startswith("## ") and current_id:
                requirements.append(
                    RequirementItem(
                        current_id, current_title, " ".join(current_narrative).strip(),
                        current_criteria, start_line
                    )
                )
                current_id = None
                in_criteria = False
                continue

            if current_id:
                if "Acceptance Criteria" in line:
                    in_criteria = True
                    continue
                if in_criteria:
                    if line.startswith("- ") or line.startswith("* "):
                        current_criteria.append(line[2:].strip())
                    elif current_criteria and line and not line.startswith("### "):
                        current_criteria[-1] += " " + line
                else:
                    if line and not line.startswith("**Narrative**"):
                        current_narrative.append(line)

        if current_id:
            requirements.append(
                RequirementItem(
                    current_id, current_title, " ".join(current_narrative).strip(),
                    current_criteria, start_line
                )
            )

        if not requirements:
            self.diagnostics.append(
                Diagnostic(1, 1, "NO_REQUIREMENTS_FOUND", "ERROR", "Section 4 MUST define at least one requirement with '### Requirement: REQ-<NNN> - <Title>'.")
            )

        return requirements

    def _validate_narratives(self, requirements: List[RequirementItem], lines: List[str]):
        for req in requirements:
            narrative = req.narrative
            has_as_a = bool(re.search(r"\bAs an?\b", narrative, re.IGNORECASE))
            has_i_want = bool(re.search(r"\bI want\b", narrative, re.IGNORECASE))
            has_so_that = bool(re.search(r"\bSo that\b", narrative, re.IGNORECASE))

            if not (has_as_a and has_i_want and has_so_that):
                missing = []
                if not has_as_a:
                    missing.append("'As a <role>'")
                if not has_i_want:
                    missing.append("'I want <action>'")
                if not has_so_that:
                    missing.append("'So that <value>'")
                self.diagnostics.append(
                    Diagnostic(
                        req.line_number, 1, "INVALID_NARRATIVE_FORMULA", "ERROR",
                        f"Requirement {req.req_id} narrative is missing formula components: {', '.join(missing)}.",
                        snippet=narrative[:80]
                    )
                )

    def _validate_ace_criteria(self, requirements: List[RequirementItem], lines: List[str]):
        for req in requirements:
            if not req.criteria:
                self.diagnostics.append(
                    Diagnostic(
                        req.line_number, 1, "EMPTY_ACCEPTANCE_CRITERIA", "ERROR",
                        f"Requirement {req.req_id} must have at least one acceptance criterion bullet under '**Acceptance Criteria**:'."
                    )
                )
                continue

            for crit in req.criteria:
                crit_text = re.sub(r"^[-*]\s*", "", crit).strip()

                # Check for forbidden modals
                for modal, fix in FORBIDDEN_MODALS.items():
                    pattern = rf"\b{re.escape(modal)}\b"
                    if re.search(pattern, crit_text, re.IGNORECASE):
                        self.diagnostics.append(
                            Diagnostic(
                                req.line_number, 1, "FORBIDDEN_MODAL_IN_CRITERIA", "ERROR",
                                f"Forbidden modal '{modal}' in criterion. Use {fix}.",
                                snippet=crit_text
                            )
                        )

                # Check for ambiguous terms
                for term, fix in FORBIDDEN_AMBIGUOUS_WORDS.items():
                    pattern = rf"\b{re.escape(term)}\b"
                    if re.search(pattern, crit_text, re.IGNORECASE):
                        self.diagnostics.append(
                            Diagnostic(
                                req.line_number, 1, "AMBIGUOUS_WORD_IN_CRITERIA", "ERROR",
                                f"Ambiguous term '{term}' in criterion. {fix}.",
                                snippet=crit_text
                            )
                        )

                # Check for passive voice
                passive_re = re.compile(
                    r"\b(is|are|was|were|be|been|being)\s+([a-zA-Z]+ed|"
                    + "|".join(IRREGULAR_PAST_PARTICIPLES)
                    + r")\b",
                    re.IGNORECASE,
                )
                match = passive_re.search(crit_text)
                if match:
                    self.diagnostics.append(
                        Diagnostic(
                            req.line_number, 1, "PASSIVE_VOICE_IN_CRITERIA", "ERROR",
                            f"Passive voice '{match.group(0)}' detected in criterion. Use active SVO voice.",
                            snippet=crit_text
                        )
                    )


def format_cli_output(file_label: str, diagnostics: List[Diagnostic], summary: Dict[str, Any]) -> str:
    lines = []
    errors = [d for d in diagnostics if d.severity == "ERROR"]
    warnings = [d for d in diagnostics if d.severity == "WARNING"]
    status_icon = "PASS" if len(errors) == 0 else "FAIL"

    lines.append(f"=== [{status_icon}] {file_label} ===")
    lines.append(f"Slug: {summary.get('slug', 'unknown')}, Status: {summary.get('status', 'unknown')}, Requirements: {summary.get('total_requirements', 0)}")
    if summary.get("requirement_ids"):
        lines.append(f"IDs: {', '.join(summary['requirement_ids'])}")

    if errors:
        lines.append(f"\nErrors ({len(errors)}):")
        for d in errors:
            lines.append(f"  [{d.rule_id}] Line {d.line}:{d.column} - {d.message}")
            if d.snippet:
                lines.append(f"    Snippet: \"{d.snippet}\"")

    if warnings:
        lines.append(f"\nWarnings ({len(warnings)}):")
        for d in warnings:
            lines.append(f"  [{d.rule_id}] Line {d.line}:{d.column} - {d.message}")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Define Skill Specification Validator")
    parser.add_argument("target", nargs="?", default="-", help="Target spec file, or '-' for stdin")
    parser.add_argument("--json", action="store_true", help="Output machine-readable JSON diagnostics")
    parser.add_argument("--check", action="store_true", help="Perform check only")

    args = parser.parse_args()
    validator = DefineValidator()

    if args.target == "-":
        content = sys.stdin.read()
        requirements, diagnostics, summary = validator.validate_text(content)
        has_errors = any(d.severity == "ERROR" for d in diagnostics)
        if args.json:
            print(json.dumps({
                "target": "stdin",
                "valid": not has_errors,
                "summary": summary,
                "error_count": len([d for d in diagnostics if d.severity == "ERROR"]),
                "warning_count": len([d for d in diagnostics if d.severity == "WARNING"]),
                "errors": [d.to_dict() for d in diagnostics]
            }, indent=2))
        else:
            print(format_cli_output("stdin", diagnostics, summary))
        sys.exit(1 if has_errors else 0)

    target_path = os.path.abspath(args.target)
    if not os.path.exists(target_path):
        sys.stderr.write(f"Error: Target path '{target_path}' does not exist.\n")
        sys.exit(2)

    with open(target_path, "r", encoding="utf-8") as f:
        content = f.read()

    requirements, diagnostics, summary = validator.validate_text(content)
    has_errors = any(d.severity == "ERROR" for d in diagnostics)

    if args.json:
        print(json.dumps({
            "target": target_path,
            "valid": not has_errors,
            "summary": summary,
            "error_count": len([d for d in diagnostics if d.severity == "ERROR"]),
            "warning_count": len([d for d in diagnostics if d.severity == "WARNING"]),
            "errors": [d.to_dict() for d in diagnostics]
        }, indent=2))
    else:
        print(format_cli_output(os.path.relpath(target_path), diagnostics, summary))

    sys.exit(1 if has_errors else 0)


if __name__ == "__main__":
    main()
