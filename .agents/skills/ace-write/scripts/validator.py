#!/usr/bin/env python3
"""
Agentic ACE Syntax & Style Validator.

Enforces deterministic active-voice SVO sentences, strict modal verbs (SHALL/MUST),
contract blocks (GIVEN/WHEN/THEN/INVARIANT), and eliminates ambiguous terms and passive voice.
Provides human-readable CLI formatting and structured JSON output for automated agent repair loops.
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


# Common irregular past participles for passive voice detection
IRREGULAR_PAST_PARTICIPLES = {
    "been", "done", "written", "given", "taken", "seen", "made", "built", "sent",
    "run", "read", "set", "cut", "put", "chosen", "drawn", "driven", "eaten",
    "fallen", "found", "gotten", "got", "held", "kept", "known", "led", "left",
    "lost", "paid", "said", "sold", "spent", "told", "understood", "won", "broken",
    "brought", "bought", "caught", "frozen", "hidden", "laid", "meant", "met",
    "shown", "shut", "spoken", "struck", "taught", "thrown", "worn", "written",
    "executed", "parsed", "processed", "triggered", "created", "deleted", "modified",
    "invoked", "called", "emitted", "evaluated", "checked", "rendered", "updated"
}

# Forbidden modal and uncertainty words
FORBIDDEN_MODALS = {
    "should": "SHALL or MUST",
    "shouldn't": "SHALL NOT or MUST NOT",
    "should not": "SHALL NOT or MUST NOT",
    "could": "can (if capability) or SHALL (if requirement)",
    "couldn't": "SHALL NOT or MUST NOT",
    "might": "MAY (if permitted) or explicit conditional IF/THEN",
    "would": "SHALL or direct active verb",
    "may": "is permitted to (if capability) or explicit conditional",
    "probably": "remove uncertainty; specify exact condition",
    "possibly": "remove uncertainty; specify exact condition",
    "maybe": "remove uncertainty; specify exact condition",
    "perhaps": "remove uncertainty; specify exact condition",
    "ought": "SHALL or MUST",
}

# Forbidden vague adjectives, adverbs, and open-ended fillers
FORBIDDEN_AMBIGUOUS_WORDS = {
    "appropriate": "specify exact criteria or name",
    "various": "specify exact items or count",
    "fast": "specify exact time limit in seconds/ms",
    "slow": "specify exact latency threshold",
    "user-friendly": "specify exact interface behavior",
    "easy": "specify exact operational steps",
    "simple": "specify exact operational steps",
    "complex": "describe the specific components",
    "roughly": "specify exact quantity or range",
    "approximately": "specify exact quantity or range",
    "basically": "remove filler word",
    "etc": "enumerate all required items explicitly",
    "etc.": "enumerate all required items explicitly",
    "and so on": "enumerate all required items explicitly",
    "so forth": "enumerate all required items explicitly",
    "nice": "specify concrete requirement",
    "good": "specify concrete criteria",
    "bad": "specify concrete criteria",
    "frequent": "specify exact frequency / interval",
    "often": "specify exact frequency / interval",
    "seldom": "specify exact frequency / interval",
    "sometimes": "specify explicit triggering condition",
    "regularly": "specify exact cron or interval",
    "adequate": "specify measurable threshold",
    "reasonable": "specify measurable threshold",
    "sufficient": "specify measurable threshold",
    "as needed": "specify triggering condition (IF ... THEN ...)",
    "if necessary": "specify triggering condition (IF ... THEN ...)",
}

# Contract block prefixes
CONTRACT_KEYWORDS = {"GIVEN", "WHEN", "THEN", "INVARIANT", "PRECONDITION", "POSTCONDITION"}


class Diagnostic:
    def __init__(self, line: int, column: int, rule_id: str, severity: str, message: str, snippet: str, suggested_fix: str):
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


class AceValidator:
    def __init__(self, lexicon_path: Optional[str] = None):
        self.lexicon = self._load_lexicon(lexicon_path)

    def _load_lexicon(self, path: Optional[str]) -> Dict[str, Any]:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        skill_asset_path = os.path.abspath(os.path.join(script_dir, "..", "assets", "lexicon.yaml"))
        workspace_asset_path = os.path.join(os.getcwd(), ".agents", "skills", "ace-write", "assets", "lexicon.yaml")
        fallback_path = os.path.join(os.getcwd(), ".agents", "lexicon.yaml")

        candidates = [path, skill_asset_path, workspace_asset_path, fallback_path]
        target_path = next((c for c in candidates if c and os.path.exists(c)), None)

        if target_path and os.path.exists(target_path) and yaml:
            try:
                with open(target_path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                    return data if isinstance(data, dict) else {}
            except Exception:
                return {}
        return {}

    def extract_prose_lines(self, text: str) -> List[Tuple[int, str]]:
        """
        Extracts prose lines, filtering out YAML frontmatter, code blocks, tables, and HTML comments.
        Returns a list of (1-indexed line_number, line_content).
        """
        lines = text.splitlines()
        prose_lines: List[Tuple[int, str]] = []

        in_frontmatter = False
        in_code_block = False
        in_html_comment = False

        for idx, line in enumerate(lines, start=1):
            stripped = line.strip()

            # Frontmatter detection (at the top of file)
            if idx == 1 and stripped.startswith("---"):
                in_frontmatter = True
                continue
            if in_frontmatter:
                if stripped.startswith("---"):
                    in_frontmatter = False
                continue

            # Code fence detection
            if stripped.startswith("```"):
                in_code_block = not in_code_block
                continue
            if in_code_block:
                continue

            # HTML Comment detection
            if "<!--" in stripped and "-->" not in stripped:
                in_html_comment = True
                continue
            if in_html_comment:
                if "-->" in stripped:
                    in_html_comment = False
                continue

            # Skip empty lines and table rows
            if not stripped:
                continue
            if stripped.startswith("|") and stripped.endswith("|"):
                continue
            if stripped.startswith("#"):
                # Check headers for prohibited words, but skip structural validation
                prose_lines.append((idx, re.sub(r"^#+\s*", "", stripped)))
                continue

            prose_lines.append((idx, line))

        return prose_lines

    def validate_text(self, text: str) -> List[Diagnostic]:
        """
        Validates prose text against Agentic ACE rules and returns diagnostics.
        """
        diagnostics: List[Diagnostic] = []
        prose_lines = self.extract_prose_lines(text)

        for line_num, line_content in prose_lines:
            self._check_line(line_num, line_content, diagnostics)

        return diagnostics

    def _check_line(self, line_num: int, line: str, diagnostics: List[Diagnostic]):
        is_header = line.strip().startswith("#")
        clean_line = re.sub(r"^#+\s*", "", line.strip())
        # Strip list markers and blockquote symbols for linguistic analysis
        clean_line = re.sub(r"^\s*([-*+]|\d+\.)\s+", "", clean_line)
        clean_line = re.sub(r"^\s*>\s*", "", clean_line).strip()

        if not clean_line:
            return

        # Check for Horizontal Dividers (Rule E009)
        if re.match(r"^[-=_*]{3,}$", line.strip()):
            diagnostics.append(
                Diagnostic(
                    line=line_num,
                    column=1,
                    rule_id="HORIZONTAL_DIVIDER_DISALLOWED",
                    severity="ERROR",
                    message=f"Horizontal rule divider '{line.strip()}' is prohibited in Agentic ACE.",
                    snippet=line.strip(),
                    suggested_fix="Remove divider line and use markdown headers for section separation."
                )
            )
            return

        # Mask inline code spans (e.g. `foo`) to avoid false positives on code literals and metareferences
        prose_to_analyze = re.sub(r"`[^`]+`", "TOKEN", clean_line)

        # 1. Check for Forbidden Modals & Uncertainty Words (Rule E002)
        for forbidden_word, fix in FORBIDDEN_MODALS.items():
            pattern = rf"\b{re.escape(forbidden_word)}\b"
            for match in re.finditer(pattern, prose_to_analyze, flags=re.IGNORECASE):
                col = match.start() + 1
                matched_text = match.group(0)
                diagnostics.append(
                    Diagnostic(
                        line=line_num,
                        column=col,
                        rule_id="FORBIDDEN_MODAL",
                        severity="ERROR",
                        message=f"Forbidden modal or uncertainty word '{matched_text}' detected.",
                        snippet=clean_line,
                        suggested_fix=f"Replace '{matched_text}' with {fix}."
                    )
                )

        # 2. Check for Forbidden Ambiguity Words (Rule E003)
        for vague_word, fix in FORBIDDEN_AMBIGUOUS_WORDS.items():
            pattern = rf"\b{re.escape(vague_word)}\b"
            for match in re.finditer(pattern, prose_to_analyze, flags=re.IGNORECASE):
                col = match.start() + 1
                matched_text = match.group(0)
                diagnostics.append(
                    Diagnostic(
                        line=line_num,
                        column=col,
                        rule_id="AMBIGUOUS_WORD",
                        severity="ERROR",
                        message=f"Ambiguous or vague term '{matched_text}' detected.",
                        snippet=clean_line,
                        suggested_fix=f"{fix}."
                    )
                )

        # 3. Check for Passive Voice (Rule E001)
        # Patterns like: is/are/was/were/be/been/being + [verb-ed or irregular participle]
        passive_regex = re.compile(
            r"\b(am|is|are|was|were|be|been|being)\s+([a-zA-Z]+ed|" + "|".join(IRREGULAR_PAST_PARTICIPLES) + r")\b",
            re.IGNORECASE
        )
        for match in passive_regex.finditer(prose_to_analyze):
            col = match.start() + 1
            snippet_match = match.group(0)
            diagnostics.append(
                Diagnostic(
                    line=line_num,
                    column=col,
                    rule_id="PASSIVE_VOICE",
                    severity="ERROR",
                    message=f"Passive voice construct '{snippet_match}' detected. Use active SVO structure.",
                    snippet=clean_line,
                    suggested_fix=f"Rephrase in active voice: [Subject] [Verb] [Object]."
                )
            )

        # 4. Check Sentence Length & Complexity (Rule E004)
        words = clean_line.split()
        if len(words) > 35:
            diagnostics.append(
                Diagnostic(
                    line=line_num,
                    column=1,
                    rule_id="SENTENCE_LENGTH",
                    severity="WARNING",
                    message=f"Sentence length ({len(words)} words) exceeds atomic maximum.",
                    snippet=clean_line[:60] + "...",
                    suggested_fix="Split into multiple atomic SVO sentences."
                )
            )

        # 5. Check Contract Block Formatting (Rule E006)
        first_token = clean_line.split()[0].rstrip(":,")
        if first_token.upper() in CONTRACT_KEYWORDS:
            if first_token != first_token.upper():
                diagnostics.append(
                    Diagnostic(
                        line=line_num,
                        column=1,
                        rule_id="CONTRACT_KEYWORD_CASE",
                        severity="ERROR",
                        message=f"Contract keyword '{first_token}' MUST be uppercase '{first_token.upper()}'.",
                        snippet=clean_line,
                        suggested_fix=f"Capitalize to '{first_token.upper()}'."
                    )
                )

        # 6. Check Conditionals (Rule E005)
        if clean_line.upper().startswith("IF "):
            if not re.search(r"\bTHEN\b", clean_line, flags=re.IGNORECASE):
                diagnostics.append(
                    Diagnostic(
                        line=line_num,
                        column=1,
                        rule_id="CONDITIONAL_THEN_MISSING",
                        severity="ERROR",
                        message="Conditional statement is missing required 'THEN' clause.",
                        snippet=clean_line,
                        suggested_fix="Use format: IF <condition>, THEN <action/state>."
                    )
                )

        # 7. Check Custom Lexicon Disallowed Words (Rule E007)
        disallowed_lexicon = self.lexicon.get("disallowed_terms", [])
        if isinstance(disallowed_lexicon, list):
            for item in disallowed_lexicon:
                if isinstance(item, str):
                    term = item
                    replacement = "defined domain term"
                elif isinstance(item, dict):
                    term = item.get("term", "")
                    replacement = item.get("replacement", "defined domain term")
                else:
                    continue

                if term:
                    pattern = rf"\b{re.escape(term)}\b"
                    for match in re.finditer(pattern, clean_line, flags=re.IGNORECASE):
                        col = match.start() + 1
                        diagnostics.append(
                            Diagnostic(
                                line=line_num,
                                column=col,
                                rule_id="LEXICON_DISALLOWED",
                                severity="ERROR",
                                message=f"Term '{match.group(0)}' is disallowed by project lexicon.",
                                snippet=clean_line,
                                suggested_fix=f"Use '{replacement}'."
                            )
                        )

        # 8. Check for Prohibited Em-Dashes and En-Dashes (Rule E008)
        for dash_pattern, name in [(r"—", "Em-dash"), (r"–", "En-dash"), (r"(?<=\S)\s*--\s*(?=\S)", "Double-hyphen dash")]:
            for match in re.finditer(dash_pattern, prose_to_analyze):
                col = match.start() + 1
                matched_char = match.group(0)
                diagnostics.append(
                    Diagnostic(
                        line=line_num,
                        column=col,
                        rule_id="EM_DASH_DISALLOWED",
                        severity="ERROR",
                        message=f"{name} '{matched_char}' is prohibited in Agentic ACE.",
                        snippet=clean_line,
                        suggested_fix="Delete the dash or replace with a period, colon, comma, or parentheses."
                    )
                )


def format_cli_output(file_label: str, diagnostics: List[Diagnostic]) -> str:
    if not diagnostics:
        return f"\033[92m✔ {file_label}: 0 violations found. Strict conformance verified.\033[0m"

    output = [f"\033[91m✖ {file_label}: {len(diagnostics)} violation(s) found:\033[0m\n"]
    for d in diagnostics:
        color = "\033[91m" if d.severity == "ERROR" else "\033[93m"
        output.append(f"  {color}[{d.severity}][{d.rule_id}]\033[0m Line {d.line}:{d.column} - {d.message}")
        output.append(f"    \033[90mSnippet:\033[0m {d.snippet}")
        output.append(f"    \033[36mFix:\033[0m     {d.suggested_fix}\n")
    return "\n".join(output)


def main():
    parser = argparse.ArgumentParser(
        description="Agentic ACE Syntax, Style & Contract Validator"
    )
    parser.add_argument("target", nargs="?", default="-", help="Target file or directory to validate, or '-' for stdin")
    parser.add_argument("--json", action="store_true", help="Output machine-readable JSON diagnostics")
    parser.add_argument("--check", action="store_true", help="Perform check only without modifying files")
    parser.add_argument("--lexicon", type=str, default=None, help="Path to custom lexicon YAML file")
    parser.add_argument("--in-place", "-i", action="store_true", help="Permit in-place modification when paired with transforms")
    parser.add_argument("--output", "-o", type=str, default=None, help="Output file path")

    args = parser.parse_args()
    validator = AceValidator(lexicon_path=args.lexicon)

    # 1. Stdin mode
    if args.target == "-":
        content = sys.stdin.read()
        diagnostics = validator.validate_text(content)
        if args.json:
            print(json.dumps({
                "target": "stdin",
                "valid": len([d for d in diagnostics if d.severity == "ERROR"]) == 0,
                "error_count": len([d for d in diagnostics if d.severity == "ERROR"]),
                "warning_count": len([d for d in diagnostics if d.severity == "WARNING"]),
                "errors": [d.to_dict() for d in diagnostics]
            }, indent=2))
        else:
            print(format_cli_output("stdin", diagnostics))
        sys.exit(1 if any(d.severity == "ERROR" for d in diagnostics) else 0)

    # 2. File or Directory mode
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
        diagnostics = validator.validate_text(content)
        err_count = len([d for d in diagnostics if d.severity == "ERROR"])
        warn_count = len([d for d in diagnostics if d.severity == "WARNING"])
        if err_count > 0:
            has_errors = True

        all_results.append({
            "file": file_path,
            "valid": err_count == 0,
            "error_count": err_count,
            "warning_count": warn_count,
            "errors": [d.to_dict() for d in diagnostics]
        })

        if not args.json:
            print(format_cli_output(os.path.relpath(file_path), diagnostics))

    if args.json:
        print(json.dumps({
            "total_files": len(files_to_check),
            "clean_files": len([r for r in all_results if r["valid"]]),
            "results": all_results
        }, indent=2))

    sys.exit(1 if has_errors else 0)


if __name__ == "__main__":
    main()
