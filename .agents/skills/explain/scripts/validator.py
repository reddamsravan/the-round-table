#!/usr/bin/env python3
"""
Explain Skill Composite Validator.

Validates explanation documents against:
1. Four mandatory structural sections in required sequence:
   - ## Problem & Context
   - ## Mental Model & Analogy
   - ## How It Works (Mechanics & Anatomy)
   - ## Pitfalls & Trade-offs
2. Per-section prose minimum quota (>= 15 words of plain prose per section).
3. Integration with PlainEnglishValidator (write skill):
   - Flesch Reading Ease >= 65.0
   - Active SVO voice (no passive voice)
   - No nominalizations, throat-clearing fluff, or forbidden complex words
   - Max 20 words per sentence
   - No em-dashes or horizontal dividers
"""

import sys
import os
import re
import json
import argparse
import importlib.util
from typing import List, Dict, Any, Optional, Tuple


def _load_write_validator():
    """Locates and loads PlainEnglishValidator from the write skill."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.abspath(os.path.join(script_dir, "..", "..", "write", "scripts", "validator.py")),
        os.path.abspath(os.path.join(os.getcwd(), ".agents", "skills", "write", "scripts", "validator.py")),
    ]
    for candidate in candidates:
        if os.path.exists(candidate):
            spec = importlib.util.spec_from_file_location("write_validator_module", candidate)
            if spec and spec.loader:
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                return mod.PlainEnglishValidator, mod.Diagnostic
    raise ImportError("Could not locate PlainEnglishValidator at write skill scripts/validator.py")


try:
    PlainEnglishValidator, BaseDiagnostic = _load_write_validator()
except Exception as e:
    PlainEnglishValidator = None
    BaseDiagnostic = None


class Diagnostic:
    def __init__(
        self,
        line: int,
        column: int,
        rule_id: str,
        severity: str,
        message: str,
        snippet: str = "",
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
            "suggested_fix": self.suggested_fix
        }


MANDATORY_SECTIONS = [
    {
        "id": "problem_and_context",
        "title": "Problem & Context",
        "pattern": re.compile(r"^##\s+(?:\d+\.\s*)?Problem\s*(?:&|and)\s*Context\b", re.IGNORECASE)
    },
    {
        "id": "mental_model_and_analogy",
        "title": "Mental Model & Analogy",
        "pattern": re.compile(r"^##\s+(?:\d+\.\s*)?Mental\s*Model\s*(?:&|and)\s*Analogy\b", re.IGNORECASE)
    },
    {
        "id": "mechanics_and_anatomy",
        "title": "How It Works (Mechanics & Anatomy)",
        "pattern": re.compile(
            r"^##\s+(?:\d+\.\s*)?How\s*It\s*Works(?:\s*[\(:—\-]?\s*Mechanics\s*(?:&|and)\s*Anatomy\)?|\s*\(\s*Mechanics\s*(?:&|and)\s*Anatomy\s*\))?\b",
            re.IGNORECASE
        )
    },
    {
        "id": "pitfalls_and_tradeoffs",
        "title": "Pitfalls & Trade-offs",
        "pattern": re.compile(r"^##\s+(?:\d+\.\s*)?Pitfalls\s*(?:&|and)\s*Trade[\s\-]?offs\b", re.IGNORECASE)
    }
]

MIN_SECTION_PROSE_WORDS = 15


class ExplainValidator:
    def __init__(self, lexicon_path: Optional[str] = None):
        if PlainEnglishValidator:
            self.plain_validator = PlainEnglishValidator(lexicon_path=lexicon_path)
        else:
            self.plain_validator = None

    def validate_text(self, text: str) -> Tuple[List[Diagnostic], Dict[str, Any]]:
        diagnostics: List[Diagnostic] = []

        # 1. Structural and section quota checks
        section_diags, section_metrics = self._validate_structure_and_quotas(text)
        diagnostics.extend(section_diags)

        # 2. Plain English checks via write skill
        write_metrics: Dict[str, Any] = {}
        if self.plain_validator:
            write_diags, write_metrics = self.plain_validator.validate_text(text)
            for d in write_diags:
                diagnostics.append(
                    Diagnostic(
                        line=d.line,
                        column=d.column,
                        rule_id=d.rule_id,
                        severity=d.severity,
                        message=d.message,
                        snippet=d.snippet,
                        suggested_fix=d.suggested_fix
                    )
                )

        combined_metrics = {
            **write_metrics,
            "sections": section_metrics.get("sections", {}),
            "sections_found_count": section_metrics.get("sections_found_count", 0),
            "mandatory_sections_present": section_metrics.get("all_sections_present", False)
        }

        return diagnostics, combined_metrics

    def _validate_structure_and_quotas(self, text: str) -> Tuple[List[Diagnostic], Dict[str, Any]]:
        diagnostics: List[Diagnostic] = []
        lines = text.splitlines()

        # Extract sections
        parsed_sections: List[Dict[str, Any]] = []
        current_section: Optional[Dict[str, Any]] = None

        in_frontmatter = False
        in_code_block = False

        for idx, line in enumerate(lines, start=1):
            stripped = line.strip()

            if idx == 1 and stripped.startswith("---"):
                in_frontmatter = True
                continue
            if in_frontmatter:
                if stripped.startswith("---"):
                    in_frontmatter = False
                continue

            if stripped.startswith("```"):
                in_code_block = not in_code_block
                if current_section:
                    current_section["raw_lines"].append((idx, line, True))
                continue

            if in_code_block:
                if current_section:
                    current_section["raw_lines"].append((idx, line, True))
                continue

            # Check for top-level H2 header
            if stripped.startswith("## ") and not stripped.startswith("###"):
                matched_def = None
                for sec_def in MANDATORY_SECTIONS:
                    if sec_def["pattern"].search(stripped):
                        matched_def = sec_def
                        break

                if current_section:
                    parsed_sections.append(current_section)

                current_section = {
                    "line": idx,
                    "header_text": stripped,
                    "matched_def": matched_def,
                    "raw_lines": []
                }
                continue

            if current_section:
                current_section["raw_lines"].append((idx, line, False))

        if current_section:
            parsed_sections.append(current_section)

        # Check for mandatory sections presence and order
        found_section_ids = []
        sections_dict: Dict[str, Any] = {}

        for parsed in parsed_sections:
            m_def = parsed["matched_def"]
            if m_def:
                s_id = m_def["id"]
                s_title = m_def["title"]
                found_section_ids.append(s_id)

                # Compute prose words in this section
                prose_words = self._count_prose_words(parsed["raw_lines"])
                sections_dict[s_title] = {
                    "line": parsed["line"],
                    "prose_words": prose_words,
                    "header": parsed["header_text"]
                }

                if prose_words < MIN_SECTION_PROSE_WORDS:
                    diagnostics.append(
                        Diagnostic(
                            line=parsed["line"],
                            column=1,
                            rule_id="INSUFFICIENT_PROSE_WORD_COUNT",
                            severity="ERROR",
                            message=(
                                f"Section '{s_title}' contains only {prose_words} words of plain prose "
                                f"(minimum required is {MIN_SECTION_PROSE_WORDS})."
                            ),
                            snippet=parsed["header_text"],
                            suggested_fix="Add explanatory plain English prose to explain concepts clearly."
                        )
                    )

        # Check for missing mandatory sections
        all_present = True
        for sec_def in MANDATORY_SECTIONS:
            s_id = sec_def["id"]
            s_title = sec_def["title"]
            if s_id not in found_section_ids:
                all_present = False
                diagnostics.append(
                    Diagnostic(
                        line=1,
                        column=1,
                        rule_id="MISSING_SECTION",
                        severity="ERROR",
                        message=f"Mandatory section '{s_title}' is missing.",
                        snippet="",
                        suggested_fix=f"Add mandatory header '## {s_title}' with at least {MIN_SECTION_PROSE_WORDS} prose words."
                    )
                )

        # Check section sequence order
        if all_present:
            expected_order = [s["id"] for s in MANDATORY_SECTIONS]
            actual_order = [s_id for s_id in found_section_ids if s_id in expected_order]
            if actual_order != expected_order:
                diagnostics.append(
                    Diagnostic(
                        line=1,
                        column=1,
                        rule_id="SECTION_ORDER_INVALID",
                        severity="ERROR",
                        message=(
                            "Mandatory sections appear out of sequence. Required order: "
                            + ", ".join([s["title"] for s in MANDATORY_SECTIONS])
                        ),
                        snippet="",
                        suggested_fix="Reorder section headings to match the mandatory sequence."
                    )
                )

        metrics = {
            "sections": sections_dict,
            "sections_found_count": len(found_section_ids),
            "all_sections_present": all_present
        }

        return diagnostics, metrics

    def _count_prose_words(self, raw_lines: List[Tuple[int, str, bool]]) -> int:
        words_count = 0
        for _, line, is_code in raw_lines:
            if is_code:
                continue
            stripped = line.strip()
            if not stripped:
                continue
            # Skip tables
            if stripped.startswith("|") and stripped.endswith("|"):
                continue
            # Skip divider
            if re.match(r"^[-=_*]{3,}$", stripped):
                continue
            # Clean markdown formatting: bullets, subheaders, quotes
            clean = re.sub(r"^#+\s*", "", stripped)
            clean = re.sub(r"^\s*([-*+]|\d+\.)\s+", "", clean)
            clean = re.sub(r"^\s*>\s*", "", clean)
            # Remove inline code spans
            clean = re.sub(r"`[^`]+`", " ", clean)
            tokens = [w for w in re.findall(r"\b[a-zA-Z0-9_\-\./']+\b", clean) if len(w) > 0]
            words_count += len(tokens)
        return words_count


def format_cli_output(file_label: str, diagnostics: List[Diagnostic], metrics: Dict[str, Any]) -> str:
    lines = []
    fre = metrics.get("flesch_reading_ease", 0.0)
    fkgl = metrics.get("flesch_kincaid_grade", 0.0)
    sections = metrics.get("sections", {})

    status_icon = "PASS" if not any(d.severity == "ERROR" for d in diagnostics) else "FAIL"
    lines.append(f"=== [{status_icon}] {file_label} ===")
    lines.append(f"Readability: Flesch Reading Ease {fre:.1f} (Grade {fkgl:.1f})")
    lines.append("Sections:")
    for s_def in MANDATORY_SECTIONS:
        title = s_def["title"]
        if title in sections:
            words = sections[title]["prose_words"]
            ok_str = "OK" if words >= MIN_SECTION_PROSE_WORDS else f"TOO SHORT ({words}/{MIN_SECTION_PROSE_WORDS})"
            lines.append(f"  - {title}: {words} prose words [{ok_str}]")
        else:
            lines.append(f"  - {title}: MISSING")

    errors = [d for d in diagnostics if d.severity == "ERROR"]
    warnings = [d for d in diagnostics if d.severity == "WARNING"]

    if errors:
        lines.append(f"\nDiagnostics ({len(errors)} errors, {len(warnings)} warnings):")
        for d in errors:
            lines.append(f"  ERROR [{d.rule_id}] Line {d.line}:{d.column} - {d.message}")
            if d.snippet:
                lines.append(f"    Snippet: \"{d.snippet}\"")
            if d.suggested_fix:
                lines.append(f"    Fix: {d.suggested_fix}")

    for d in warnings:
        lines.append(f"  WARNING [{d.rule_id}] Line {d.line}:{d.column} - {d.message}")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Explain Skill Composite Validator (Structure + Readability)"
    )
    parser.add_argument("target", nargs="?", default="-", help="Target file or directory to validate, or '-' for stdin")
    parser.add_argument("--json", action="store_true", help="Output machine-readable JSON diagnostics")
    parser.add_argument("--check", action="store_true", help="Perform check only")
    parser.add_argument("--lexicon", type=str, default=None, help="Path to custom lexicon YAML file")

    args = parser.parse_args()
    validator = ExplainValidator(lexicon_path=args.lexicon)

    # Stdin mode
    if args.target == "-":
        content = sys.stdin.read()
        diagnostics, metrics = validator.validate_text(content)
        has_errors = any(d.severity == "ERROR" for d in diagnostics)
        if args.json:
            print(json.dumps({
                "target": "stdin",
                "valid": not has_errors,
                "metrics": metrics,
                "error_count": len([d for d in diagnostics if d.severity == "ERROR"]),
                "warning_count": len([d for d in diagnostics if d.severity == "WARNING"]),
                "errors": [d.to_dict() for d in diagnostics]
            }, indent=2))
        else:
            print(format_cli_output("stdin", diagnostics, metrics))
        sys.exit(1 if has_errors else 0)

    # File / Directory mode
    target_path = os.path.abspath(args.target)
    if not os.path.exists(target_path):
        sys.stderr.write(f"Error: Target path '{target_path}' does not exist.\n")
        sys.exit(2)

    files_to_check = []
    if os.path.isdir(target_path):
        for root, _, files in os.walk(target_path):
            for file in files:
                if file.endswith((".md", ".txt")):
                    files_to_check.append(os.path.join(root, file))
    else:
        files_to_check.append(target_path)

    all_results = []
    has_errors = False

    for file_path in files_to_check:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        diagnostics, metrics = validator.validate_text(content)
        err_count = len([d for d in diagnostics if d.severity == "ERROR"])
        warn_count = len([d for d in diagnostics if d.severity == "WARNING"])
        if err_count > 0:
            has_errors = True

        all_results.append({
            "file": file_path,
            "valid": err_count == 0,
            "metrics": metrics,
            "error_count": err_count,
            "warning_count": warn_count,
            "errors": [d.to_dict() for d in diagnostics]
        })

        if not args.json:
            print(format_cli_output(os.path.relpath(file_path), diagnostics, metrics))

    if args.json:
        print(json.dumps({
            "total_files": len(files_to_check),
            "clean_files": len([r for r in all_results if r["valid"]]),
            "results": all_results
        }, indent=2))

    sys.exit(1 if has_errors else 0)


if __name__ == "__main__":
    main()
