#!/usr/bin/env python3
"""
Conventional Commit Validator and Formatter.

Enforces Conventional Commits 1.0.0 syntax, strict 50/72 formatting rules,
imperative mood subjects, and plain English body line-wrapping.
Provides structured JSON output for automated agent repair loops and an --autofix mode.
"""

import sys
import os
import re
import json
import argparse
import textwrap
from typing import List, Dict, Any, Optional, Tuple

ALLOWED_TYPES = {
    "feat",
    "fix",
    "docs",
    "style",
    "refactor",
    "perf",
    "test",
    "build",
    "ci",
    "chore",
    "revert"
}

# Common past tense or continuous verb replacements for imperative mood auto-fix / diagnostics
NON_IMPERATIVE_VERBS = {
    "added": "add",
    "adding": "add",
    "adds": "add",
    "fixed": "fix",
    "fixing": "fix",
    "fixes": "fix",
    "updated": "update",
    "updating": "update",
    "updates": "update",
    "removed": "remove",
    "removing": "remove",
    "removes": "remove",
    "created": "create",
    "creating": "create",
    "creates": "create",
    "deleted": "delete",
    "deleting": "delete",
    "deletes": "delete",
    "changed": "change",
    "changing": "change",
    "changes": "change",
    "refactored": "refactor",
    "refactoring": "refactor",
    "refactors": "refactor",
    "implemented": "implement",
    "implementing": "implement",
    "implements": "implement",
    "improved": "improve",
    "improving": "improve",
    "improves": "improve",
    "handled": "handle",
    "handling": "handle",
    "handles": "handle",
    "resolved": "resolve",
    "resolving": "resolve",
    "resolves": "resolve",
    "configured": "configure",
    "configuring": "configure",
    "configures": "configure",
    "cleaned": "clean",
    "cleaning": "clean",
    "cleans": "clean",
    "moved": "move",
    "moving": "move",
    "moves": "move",
    "simplified": "simplify",
    "simplifying": "simplify",
    "simplifies": "simplify",
    "supported": "support",
    "supporting": "support",
    "supports": "support",
    "prevented": "prevent",
    "preventing": "prevent",
    "prevents": "prevent",
    "allowed": "allow",
    "allowing": "allow",
    "allows": "allow",
    "ensured": "ensure",
    "ensuring": "ensure",
    "ensures": "ensure",
    "deprecated": "deprecate",
    "deprecating": "deprecate",
    "deprecates": "deprecate",
    "reverted": "revert",
    "reverting": "revert",
    "reverts": "revert",
    "documented": "document",
    "documenting": "document",
    "documents": "document"
}

# Regex to match Conventional Commit header:
# <type>[(<scope>)][!]: <subject>
HEADER_PATTERN = re.compile(
    r"^(?P<type>[a-zA-Z0-9_\-]+)(?:\((?P<scope>[^\)]+)\))?(?P<breaking>!)?:\s+(?P<subject>.+)$"
)

# Regex to detect footer patterns (BREAKING CHANGE: ... or Token: value or Token #123)
FOOTER_PATTERN = re.compile(
    r"^(BREAKING[\s-]CHANGE:\s+.+|[a-zA-Z0-9_\-]+(?:\s*#\d+|:\s+.+))$"
)


class Diagnostic:
    def __init__(
        self,
        line: int,
        column: int,
        rule_id: str,
        severity: str,
        message: str,
        snippet: str,
        suggested_fix: str
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


class CommitValidator:
    def __init__(
        self,
        max_subject_length: int = 50,
        hard_max_subject_length: int = 72,
        max_body_line_length: int = 72,
        allowed_types: Optional[set] = None
    ):
        self.max_subject_length = max_subject_length
        self.hard_max_subject_length = hard_max_subject_length
        self.max_body_line_length = max_body_line_length
        self.allowed_types = allowed_types or ALLOWED_TYPES

    def validate_text(self, text: str) -> List[Diagnostic]:
        diagnostics: List[Diagnostic] = []
        raw_lines = text.split("\n")
        
        # Remove trailing empty lines for analysis
        while raw_lines and raw_lines[-1] == "":
            raw_lines.pop()

        if not raw_lines or not raw_lines[0].strip():
            diagnostics.append(
                Diagnostic(
                    line=1,
                    column=1,
                    rule_id="EMPTY_COMMIT_MESSAGE",
                    severity="ERROR",
                    message="Commit message is empty.",
                    snippet="",
                    suggested_fix="Provide a Conventional Commit message in format '<type>(<scope>): <subject>'."
                )
            )
            return diagnostics

        header = raw_lines[0]

        # 1. Header syntax validation
        match = HEADER_PATTERN.match(header)
        if not match:
            diagnostics.append(
                Diagnostic(
                    line=1,
                    column=1,
                    rule_id="HEADER_SYNTAX",
                    severity="ERROR",
                    message="Header does not conform to '<type>(<scope>): <subject>' or '<type>: <subject>'.",
                    snippet=header,
                    suggested_fix="Format header as '<type>(<scope>): <subject>' with a colon and space."
                )
            )
            # If header regex failed, we still inspect other lines if present
            self._validate_body_and_footers(raw_lines, diagnostics)
            return diagnostics

        commit_type = match.group("type")
        scope = match.group("scope")
        subject = match.group("subject")

        # 2. Type validation
        if commit_type not in self.allowed_types:
            diagnostics.append(
                Diagnostic(
                    line=1,
                    column=1,
                    rule_id="INVALID_TYPE",
                    severity="ERROR",
                    message=f"Commit type '{commit_type}' is not recognized.",
                    snippet=commit_type,
                    suggested_fix=f"Use one of allowed types: {', '.join(sorted(self.allowed_types))}."
                )
            )

        # 3. Scope validation
        if scope is not None:
            if scope != scope.lower():
                diagnostics.append(
                    Diagnostic(
                        line=1,
                        column=header.find(f"({scope})") + 2,
                        rule_id="SCOPE_LOWERCASE",
                        severity="ERROR",
                        message=f"Scope '{scope}' must be lowercase.",
                        snippet=scope,
                        suggested_fix=f"Change scope to '{scope.lower()}'."
                    )
                )
            if not re.match(r"^[a-z0-9_\-\/]+$", scope):
                diagnostics.append(
                    Diagnostic(
                        line=1,
                        column=header.find(f"({scope})") + 2,
                        rule_id="SCOPE_INVALID_CHARS",
                        severity="ERROR",
                        message=f"Scope '{scope}' contains invalid characters.",
                        snippet=scope,
                        suggested_fix="Use alphanumeric characters, hyphens, underscores, or slashes."
                    )
                )

        # 4. Subject capitalization
        first_char = subject[0] if subject else ""
        if first_char.isalpha() and first_char.isupper():
            diagnostics.append(
                Diagnostic(
                    line=1,
                    column=header.rfind(subject) + 1,
                    rule_id="SUBJECT_LOWERCASE",
                    severity="ERROR",
                    message="Subject must begin with a lowercase letter.",
                    snippet=subject,
                    suggested_fix=f"Change '{subject}' to '{first_char.lower() + subject[1:]}'."
                )
            )

        # 5. Subject trailing period
        if subject.endswith("."):
            diagnostics.append(
                Diagnostic(
                    line=1,
                    column=len(header),
                    rule_id="SUBJECT_TRAILING_PERIOD",
                    severity="ERROR",
                    message="Subject must not end with a period.",
                    snippet=subject,
                    suggested_fix=f"Remove the trailing period: '{subject.rstrip('.')}'."
                )
            )

        # 6. Subject imperative mood check
        first_word = re.split(r"\s+", subject.strip())[0].lower()
        if first_word in NON_IMPERATIVE_VERBS:
            recommended_verb = NON_IMPERATIVE_VERBS[first_word]
            diagnostics.append(
                Diagnostic(
                    line=1,
                    column=header.rfind(subject) + 1,
                    rule_id="SUBJECT_IMPERATIVE_MOOD",
                    severity="ERROR",
                    message=f"Subject should use imperative mood ('{recommended_verb}') instead of '{first_word}'.",
                    snippet=first_word,
                    suggested_fix=f"Replace '{first_word}' with imperative verb '{recommended_verb}'."
                )
            )

        # 7. Header length check
        header_len = len(header)
        if header_len > self.hard_max_subject_length:
            diagnostics.append(
                Diagnostic(
                    line=1,
                    column=self.hard_max_subject_length + 1,
                    rule_id="HEADER_LENGTH_HARD_LIMIT",
                    severity="ERROR",
                    message=f"Header length ({header_len} chars) exceeds hard limit of {self.hard_max_subject_length} characters.",
                    snippet=header,
                    suggested_fix=f"Shorten header to {self.hard_max_subject_length} characters or fewer."
                )
            )
        elif header_len > self.max_subject_length:
            diagnostics.append(
                Diagnostic(
                    line=1,
                    column=self.max_subject_length + 1,
                    rule_id="HEADER_LENGTH_RECOMMENDED",
                    severity="WARNING",
                    message=f"Header length ({header_len} chars) exceeds recommended {self.max_subject_length} characters.",
                    snippet=header,
                    suggested_fix=f"Shorten header to {self.max_subject_length} characters or fewer for optimal display."
                )
            )

        # 8. Body and footers validation
        self._validate_body_and_footers(raw_lines, diagnostics)

        return diagnostics

    def _validate_body_and_footers(self, raw_lines: List[str], diagnostics: List[Diagnostic]) -> None:
        if len(raw_lines) <= 1:
            return

        # Blank line check between header and body/footers
        if raw_lines[1].strip() != "":
            diagnostics.append(
                Diagnostic(
                    line=2,
                    column=1,
                    rule_id="BLANK_LINE_AFTER_HEADER",
                    severity="ERROR",
                    message="A blank line is required between the header and the body/footers.",
                    snippet=raw_lines[1],
                    suggested_fix="Insert an empty line after the first line."
                )
            )

        # Check subsequent lines for length violations
        in_code_block = False
        for idx in range(2, len(raw_lines)):
            line_num = idx + 1
            line = raw_lines[idx]

            if line.strip().startswith("```"):
                in_code_block = not in_code_block
                continue

            if in_code_block:
                continue

            # Ignore lines containing unbroken URLs
            if "http://" in line or "https://" in line or "file://" in line:
                words = line.split()
                if any(w.startswith(("http://", "https://", "file://")) and len(w) > 40 for w in words):
                    continue

            if len(line) > self.max_body_line_length:
                diagnostics.append(
                    Diagnostic(
                        line=line_num,
                        column=self.max_body_line_length + 1,
                        rule_id="BODY_LINE_LENGTH",
                        severity="ERROR",
                        message=f"Body line exceeds maximum width of {self.max_body_line_length} characters ({len(line)} chars).",
                        snippet=line,
                        suggested_fix=f"Wrap line at {self.max_body_line_length} characters."
                    )
                )

    def autofix(self, text: str) -> str:
        raw_lines = text.split("\n")
        while raw_lines and raw_lines[-1] == "":
            raw_lines.pop()

        if not raw_lines or not raw_lines[0].strip():
            return text

        header = raw_lines[0].strip()
        match = HEADER_PATTERN.match(header)

        if match:
            commit_type = match.group("type").lower()
            scope = match.group("scope")
            breaking = match.group("breaking") or ""
            subject = match.group("subject").strip()

            if scope:
                scope = scope.lower()

            # Fix subject lowercase start
            if subject and subject[0].isupper():
                subject = subject[0].lower() + subject[1:]

            # Fix subject trailing period
            subject = subject.rstrip(".")

            # Fix non-imperative starting verb
            words = subject.split(" ")
            if words and words[0].lower() in NON_IMPERATIVE_VERBS:
                words[0] = NON_IMPERATIVE_VERBS[words[0].lower()]
                subject = " ".join(words)

            if scope:
                fixed_header = f"{commit_type}({scope}){breaking}: {subject}"
            else:
                fixed_header = f"{commit_type}{breaking}: {subject}"
        else:
            fixed_header = header

        if len(raw_lines) == 1:
            return fixed_header

        # Process body and footers
        remaining_lines = raw_lines[1:]
        # Ensure first line after header was empty or skip leading blank lines
        while remaining_lines and remaining_lines[0].strip() == "":
            remaining_lines.pop(0)

        if not remaining_lines:
            return fixed_header

        # Group paragraphs and wrap lines at 72 chars, preserving code blocks
        paragraphs: List[List[str]] = []
        current_para: List[str] = []
        in_code_block = False

        for line in remaining_lines:
            if line.strip().startswith("```"):
                in_code_block = not in_code_block
                if current_para:
                    paragraphs.append(current_para)
                    current_para = []
                paragraphs.append([line])
                continue

            if in_code_block:
                paragraphs.append([line])
                continue

            if not line.strip():
                if current_para:
                    paragraphs.append(current_para)
                    current_para = []
            else:
                current_para.append(line)

        if current_para:
            paragraphs.append(current_para)

        formatted_paragraphs: List[str] = []
        for para in paragraphs:
            if len(para) == 1 and (para[0].strip().startswith("```") or para[0].startswith(" ")):
                formatted_paragraphs.append(para[0])
                continue
            
            # Check if paragraph is a bullet list or footer
            text_block = " ".join(l.strip() for l in para)
            # Wrap text at max_body_line_length
            wrapped = textwrap.fill(
                text_block,
                width=self.max_body_line_length,
                break_long_words=False,
                break_on_hyphens=False
            )
            formatted_paragraphs.append(wrapped)

        body_text = "\n\n".join(formatted_paragraphs)
        return f"{fixed_header}\n\n{body_text}"


def parse_args():
    parser = argparse.ArgumentParser(
        description="Validate and format Conventional Commit messages."
    )
    parser.add_argument(
        "target",
        nargs="?",
        default=None,
        help="Target file path containing commit message, or omit to read from stdin."
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output diagnostics in structured JSON format."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Return exit code 1 on errors without modifying files."
    )
    parser.add_argument(
        "--autofix",
        action="store_true",
        help="Automatically correct lowercase headers, trailing periods, imperative mood, and line wrapping."
    )
    parser.add_argument(
        "--in-place",
        action="store_true",
        help="Write autofixed content directly back to target file (requires target file)."
    )
    parser.add_argument(
        "--max-subject-length",
        type=int,
        default=50,
        help="Recommended max length for commit subject (default: 50)."
    )
    return parser.parse_args()


def main():
    args = parse_args()

    if args.target:
        if not os.path.exists(args.target):
            print(f"Error: Target path '{args.target}' does not exist.", file=sys.stderr)
            sys.exit(2)
        with open(args.target, "r", encoding="utf-8") as f:
            content = f.read()
        target_name = os.path.abspath(args.target)
    else:
        content = sys.stdin.read()
        target_name = "stdin"

    validator = CommitValidator(max_subject_length=args.max_subject_length)
    diagnostics = validator.validate_text(content)

    errors = [d for d in diagnostics if d.severity == "ERROR"]
    warnings = [d for d in diagnostics if d.severity == "WARNING"]
    is_valid = len(errors) == 0

    if args.autofix:
        fixed_text = validator.autofix(content)
        if args.in_place and args.target:
            with open(args.target, "w", encoding="utf-8") as f:
                f.write(fixed_text)
        elif not args.json:
            sys.stdout.write(fixed_text + ("\n" if not fixed_text.endswith("\n") else ""))

    if args.json:
        result = {
            "target": target_name,
            "valid": is_valid,
            "error_count": len(errors),
            "warning_count": len(warnings),
            "errors": [d.to_dict() for d in diagnostics],
        }
        if args.autofix:
            result["fixed_text"] = validator.autofix(content)
        print(json.dumps(result, indent=2))
    elif not args.autofix:
        if is_valid and not warnings:
            print(f"✓ Commit message is valid Conventional Commit 1.0.0 ({target_name})")
        else:
            for d in diagnostics:
                prefix = "✖ ERROR" if d.severity == "ERROR" else "⚠ WARNING"
                print(f"{prefix} [{d.rule_id}] Line {d.line}:{d.column} - {d.message}")
                if d.snippet:
                    print(f"  Snippet: {d.snippet}")
                if d.suggested_fix:
                    print(f"  Fix:     {d.suggested_fix}")

    if args.check and not is_valid:
        sys.exit(1)
    elif not is_valid and not args.autofix:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
