#!/usr/bin/env python3
"""
Plain English Readability & Style Validator.

Enforces Plain English guidelines (Plain Writing Act & Federal Plain Language Guidelines),
measuring readability (Flesch Reading Ease >= 65, Flesch-Kincaid Grade Level <= 8),
sentence length limits (<= 20 words), active voice, and eliminating bureaucratic jargon,
throat-clearing filler, and nominalizations.
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

# Fallback substitutions if YAML is unavailable
DEFAULT_SUBSTITUTIONS = {
    "utilize": "use",
    "utilization": "use",
    "commence": "start",
    "terminate": "end",
    "facilitate": "help",
    "implement": "build",
    "implementation": "setup",
    "demonstrate": "show",
    "transmit": "send",
    "ascertain": "find out",
    "discontinue": "stop",
    "endeavor": "try",
    "expedite": "speed up",
    "furnish": "give",
    "initiate": "start",
    "modify": "change",
    "modification": "change",
    "obtain": "get",
    "procure": "buy",
    "prior to": "before",
    "subsequent to": "after",
    "in order to": "to",
    "in the event that": "if",
    "at this point in time": "now",
    "due to the fact that": "because",
    "in light of the fact that": "because",
    "with regard to": "about",
    "with respect to": "about",
    "for the purpose of": "to",
    "in accordance with": "following",
    "is able to": "can",
    "has the ability to": "can",
    "shall be responsible for": "handles",
    "a number of": "many",
    "a majority of": "most",
    "at an early date": "soon",
    "by means of": "by",
}

DEFAULT_NOMINALIZATIONS = {
    "make a determination": "decide",
    "conduct an investigation": "investigate",
    "give consideration to": "consider",
    "reach a conclusion": "conclude",
    "perform an analysis": "analyze",
    "provide assistance to": "help",
    "make an assumption": "assume",
    "bring about a reduction": "reduce",
    "make an examination of": "examine",
    "take action": "act",
    "provide a description of": "describe",
    "give an explanation of": "explain",
    "make a recommendation": "recommend",
    "reach an agreement": "agree",
}

DEFAULT_FLUFF_PHRASES = [
    "it is important to note that",
    "it should be noted that",
    "please be advised that",
    "it is interesting to note that",
    "it goes without saying that",
    "as a matter of fact",
    "for all intents and purposes",
    "in the final analysis",
    "needless to say",
    "all things being equal",
]


def count_syllables_in_word(word: str) -> int:
    """
    Counts syllables in an English word using phonetic heuristic rules.
    """
    clean_word = re.sub(r"[^a-zA-Z]", "", word.lower())
    if not clean_word:
        return 0
    if len(clean_word) <= 3:
        return 1

    # Exceptions and specific prefixes/suffixes
    clean_word = re.sub(r"(?:[^laeiouy]|ed|es|e)$", "", clean_word)
    clean_word = re.sub(r"^y", "", clean_word)

    # Count vowel groups
    vowel_groups = re.findall(r"[aeiouy]{1,2}", clean_word)
    count = len(vowel_groups)
    return max(1, count)


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


class PlainEnglishValidator:
    def __init__(self, lexicon_path: Optional[str] = None):
        self.lexicon = self._load_lexicon(lexicon_path)
        self.substitutions = self._extract_substitutions()
        self.nominalizations = self._extract_nominalizations()
        self.fluff_phrases = self._extract_fluff_phrases()

    def _load_lexicon(self, path: Optional[str]) -> Dict[str, Any]:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        skill_asset_path = os.path.abspath(os.path.join(script_dir, "..", "assets", "lexicon.yaml"))
        workspace_asset_path = os.path.join(os.getcwd(), ".agents", "skills", "write", "assets", "lexicon.yaml")

        candidates = [path, skill_asset_path, workspace_asset_path]
        target_path = next((c for c in candidates if c and os.path.exists(c)), None)

        if target_path and os.path.exists(target_path) and yaml:
            try:
                with open(target_path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                    return data if isinstance(data, dict) else {}
            except Exception:
                return {}
        return {}

    def _extract_substitutions(self) -> Dict[str, str]:
        subs = dict(DEFAULT_SUBSTITUTIONS)
        entries = self.lexicon.get("substitutions", [])
        if isinstance(entries, list):
            for item in entries:
                if isinstance(item, dict) and "term" in item and "replacement" in item:
                    subs[item["term"].lower()] = item["replacement"]
        return subs

    def _extract_nominalizations(self) -> Dict[str, str]:
        noms = dict(DEFAULT_NOMINALIZATIONS)
        entries = self.lexicon.get("nominalizations", [])
        if isinstance(entries, list):
            for item in entries:
                if isinstance(item, dict) and "phrase" in item and "replacement" in item:
                    noms[item["phrase"].lower()] = item["replacement"]
        return noms

    def _extract_fluff_phrases(self) -> List[str]:
        fluff = list(DEFAULT_FLUFF_PHRASES)
        entries = self.lexicon.get("fluff_phrases", [])
        if isinstance(entries, list):
            for item in entries:
                if isinstance(item, str) and item.lower() not in fluff:
                    fluff.append(item.lower())
        return fluff

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

            # Frontmatter detection
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
                # Analyze header text without structural constraints
                prose_lines.append((idx, re.sub(r"^#+\s*", "", stripped)))
                continue

            prose_lines.append((idx, line))

        return prose_lines

    def calculate_readability_metrics(self, prose_lines: List[Tuple[int, str]]) -> Dict[str, Any]:
        """
        Calculates Flesch Reading Ease and Flesch-Kincaid Grade Level over all prose text.
        """
        total_words = 0
        total_syllables = 0
        all_sentences: List[str] = []

        for _, line in prose_lines:
            if re.match(r"^[-=_*]{3,}$", line.strip()):
                continue
            clean_line = re.sub(r"^#+\s*", "", line.strip())
            clean_line = re.sub(r"^\s*([-*+]|\d+\.)\s+", "", clean_line)
            clean_line = re.sub(r"^\s*>\s*", "", clean_line).strip()
            # Mask inline code
            clean_line = re.sub(r"`[^`]+`", "code", clean_line)

            if not clean_line:
                continue

            # Split line into sentences (by period, exclamation, question mark, or list marker)
            sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", clean_line) if s.strip()]
            if not sentences:
                sentences = [clean_line]

            all_sentences.extend(sentences)

            for sentence in sentences:
                words = [re.sub(r"[^\w\'-]", "", w) for w in sentence.split() if re.sub(r"[^\w\'-]", "", w)]
                total_words += len(words)
                for w in words:
                    total_syllables += count_syllables_in_word(w)

        num_sentences = max(1, len(all_sentences))
        num_words = max(1, total_words)
        num_syllables = max(1, total_syllables)

        words_per_sentence = num_words / num_sentences
        syllables_per_word = num_syllables / num_words

        # Flesch Reading Ease = 206.835 - (1.015 * ASL) - (84.6 * ASW)
        fre = 206.835 - (1.015 * words_per_sentence) - (84.6 * syllables_per_word)
        fre = round(max(0.0, min(100.0, fre)), 2)

        # Flesch-Kincaid Grade Level = (0.39 * ASL) + (11.8 * ASW) - 15.59
        fkgl = (0.39 * words_per_sentence) + (11.8 * syllables_per_word) - 15.59
        fkgl = round(max(0.0, fkgl), 2)

        sentence_lengths = [len(s.split()) for s in all_sentences]
        max_sentence_length = max(sentence_lengths) if sentence_lengths else 0

        return {
            "flesch_reading_ease": fre,
            "flesch_kincaid_grade": fkgl,
            "total_words": total_words,
            "total_sentences": num_sentences,
            "avg_sentence_length": round(words_per_sentence, 2),
            "max_sentence_length": max_sentence_length,
            "syllables_per_word": round(syllables_per_word, 2),
        }

    def validate_text(self, text: str) -> Tuple[List[Diagnostic], Dict[str, Any]]:
        """
        Validates prose text against Plain English rules and returns diagnostics and metrics.
        """
        diagnostics: List[Diagnostic] = []
        prose_lines = self.extract_prose_lines(text)
        metrics = self.calculate_readability_metrics(prose_lines)

        # Overall Readability Diagnostic (Rule P001)
        if metrics["total_words"] >= 15 and metrics["flesch_reading_ease"] < 65.0:
            diagnostics.append(
                Diagnostic(
                    line=1,
                    column=1,
                    rule_id="READABILITY_SCORE_LOW",
                    severity="ERROR",
                    message=f"Flesch Reading Ease score ({metrics['flesch_reading_ease']}) is below target threshold (>= 65.0). Grade Level: {metrics['flesch_kincaid_grade']}.",
                    snippet=f"Average sentence length: {metrics['avg_sentence_length']} words, Syllables/word: {metrics['syllables_per_word']}",
                    suggested_fix="Shorten sentences, split clauses, and replace multi-syllable jargon with simpler everyday words."
                )
            )

        for line_num, line_content in prose_lines:
            self._check_line(line_num, line_content, diagnostics)

        return diagnostics, metrics

    def _check_line(self, line_num: int, line: str, diagnostics: List[Diagnostic]):
        clean_line = re.sub(r"^#+\s*", "", line.strip())
        clean_line = re.sub(r"^\s*([-*+]|\d+\.)\s+", "", clean_line)
        clean_line = re.sub(r"^\s*>\s*", "", clean_line).strip()

        if not clean_line:
            return

        # Check for Horizontal Dividers (Rule P008)
        if re.match(r"^[-=_*]{3,}$", line.strip()):
            diagnostics.append(
                Diagnostic(
                    line=line_num,
                    column=1,
                    rule_id="HORIZONTAL_DIVIDER_DISALLOWED",
                    severity="ERROR",
                    message=f"Horizontal rule divider '{line.strip()}' is prohibited in Plain English.",
                    snippet=line.strip(),
                    suggested_fix="Remove divider line and use markdown headers for section separation."
                )
            )
            return

        # Mask inline code spans to prevent false positives
        prose_to_analyze = re.sub(r"`[^`]+`", "TOKEN", clean_line)

        # 1. Check for Sentence Length exceeding 20 words (Rule P002)
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", prose_to_analyze) if s.strip()]
        for s in sentences:
            words = s.split()
            if len(words) > 20:
                snippet_text = s[:60] + "..." if len(s) > 60 else s
                diagnostics.append(
                    Diagnostic(
                        line=line_num,
                        column=1,
                        rule_id="SENTENCE_LENGTH_EXCEEDED",
                        severity="ERROR",
                        message=f"Sentence length ({len(words)} words) exceeds the Plain English maximum of 20 words.",
                        snippet=snippet_text,
                        suggested_fix="Split into two or more short, direct sentences or use bullet points."
                    )
                )

        # 2. Check for Passive Voice (Rule P003)
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
                    rule_id="PASSIVE_VOICE_DISALLOWED",
                    severity="ERROR",
                    message=f"Passive voice construct '{snippet_match}' detected. Use active voice (Subject + Verb + Object).",
                    snippet=clean_line,
                    suggested_fix="Rephrase in active voice: identify the actor and put them before the action verb."
                )
            )

        # 3. Check for Fluff / Throat-Clearing Phrases (Rule P004)
        for fluff in self.fluff_phrases:
            pattern = rf"\b{re.escape(fluff)}\b"
            for match in re.finditer(pattern, prose_to_analyze, flags=re.IGNORECASE):
                col = match.start() + 1
                matched_text = match.group(0)
                diagnostics.append(
                    Diagnostic(
                        line=line_num,
                        column=col,
                        rule_id="FLUFF_PHRASE_DETECTED",
                        severity="ERROR",
                        message=f"Throat-clearing filler phrase '{matched_text}' detected.",
                        snippet=clean_line,
                        suggested_fix=f"Delete '{matched_text}' and state the key point directly."
                    )
                )

        # 4. Check for Nominalizations (Rule P005)
        for nom, replacement in self.nominalizations.items():
            pattern = rf"\b{re.escape(nom)}\b"
            for match in re.finditer(pattern, prose_to_analyze, flags=re.IGNORECASE):
                col = match.start() + 1
                matched_text = match.group(0)
                diagnostics.append(
                    Diagnostic(
                        line=line_num,
                        column=col,
                        rule_id="NOMINALIZATION_DETECTED",
                        severity="ERROR",
                        message=f"Smothered verb / nominalization '{matched_text}' detected.",
                        snippet=clean_line,
                        suggested_fix=f"Replace with direct active verb '{replacement}'."
                    )
                )

        # 5. Check for Complex / Bureaucratic Substitutions (Rule P006)
        for term, replacement in self.substitutions.items():
            pattern = rf"\b{re.escape(term)}\b"
            for match in re.finditer(pattern, prose_to_analyze, flags=re.IGNORECASE):
                col = match.start() + 1
                matched_text = match.group(0)
                diagnostics.append(
                    Diagnostic(
                        line=line_num,
                        column=col,
                        rule_id="COMPLEX_WORD_DETECTED",
                        severity="ERROR",
                        message=f"Complex/bureaucratic term '{matched_text}' detected.",
                        snippet=clean_line,
                        suggested_fix=f"Replace '{matched_text}' with simpler word '{replacement}'."
                    )
                )

        # 6. Check for Raw Agentic ACE Contract Residue (Rule P007)
        first_token = clean_line.split()[0].rstrip(":,")
        if first_token in {"GIVEN", "WHEN", "THEN", "INVARIANT", "PRECONDITION", "POSTCONDITION"}:
            diagnostics.append(
                Diagnostic(
                    line=line_num,
                    column=1,
                    rule_id="RAW_ACE_KEYWORD_RESIDUE",
                    severity="ERROR",
                    message=f"Raw Agentic ACE keyword '{first_token}' detected in Plain English output.",
                    snippet=clean_line,
                    suggested_fix=f"Unwrap '{first_token}' into natural plain language (e.g. 'If...', 'Then...', 'Rule: ...')."
                )
            )

        # 7. Check for Prohibited Em-Dashes and En-Dashes (Rule P009)
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
                        message=f"{name} '{matched_char}' is prohibited in Plain English.",
                        snippet=clean_line,
                        suggested_fix="Delete the dash or replace with a period, colon, comma, or parentheses."
                    )
                )


def format_cli_output(file_label: str, diagnostics: List[Diagnostic], metrics: Dict[str, Any]) -> str:
    lines = []
    fre = metrics.get("flesch_reading_ease", 0)
    fkgl = metrics.get("flesch_kincaid_grade", 0)
    asl = metrics.get("avg_sentence_length", 0)
    words = metrics.get("total_words", 0)

    score_color = "\033[92m" if fre >= 65.0 else "\033[91m"
    metrics_summary = f"  \033[90mMetrics:\033[0m FRE={score_color}{fre}\033[0m (Grade {fkgl}), Words={words}, Avg Sentence={asl}w"

    if not diagnostics:
        lines.append(f"\033[92m✔ {file_label}: 0 violations found. Strict Plain English verified.\033[0m")
        lines.append(metrics_summary)
        return "\n".join(lines)

    lines.append(f"\033[91m✖ {file_label}: {len(diagnostics)} violation(s) found:\033[0m")
    lines.append(metrics_summary + "\n")

    for d in diagnostics:
        color = "\033[91m" if d.severity == "ERROR" else "\033[93m"
        lines.append(f"  {color}[{d.severity}][{d.rule_id}]\033[0m Line {d.line}:{d.column} - {d.message}")
        lines.append(f"    \033[90mSnippet:\033[0m {d.snippet}")
        lines.append(f"    \033[36mFix:\033[0m     {d.suggested_fix}\n")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Plain English Readability & Style Validator"
    )
    parser.add_argument("target", nargs="?", default="-", help="Target file or directory to validate, or '-' for stdin")
    parser.add_argument("--json", action="store_true", help="Output machine-readable JSON diagnostics")
    parser.add_argument("--check", action="store_true", help="Perform check only without modifying files")
    parser.add_argument("--lexicon", type=str, default=None, help="Path to custom lexicon YAML file")
    parser.add_argument("--in-place", "-i", action="store_true", help="Permit in-place modification")
    parser.add_argument("--output", "-o", type=str, default=None, help="Output file path")

    args = parser.parse_args()
    validator = PlainEnglishValidator(lexicon_path=args.lexicon)

    # 1. Stdin mode
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
