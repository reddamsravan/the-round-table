#!/usr/bin/env python3
"""
Prose Syntax, Readability & Style Validator.

Provides validation for technical prose across two modes:
1. ASD-STE100 (Simplified Technical English, default): Enforces active voice,
   short sentences (<= 20 words), approved vocabulary, Flesch Reading Ease >= 65,
   and eliminates nominalizations and conversational fluff.
2. Attempto Controlled English (ACE): Enforces deterministic active-voice SVO
   contracts, strict modal verbs (SHALL/MUST), and eliminates ambiguous terms.
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
    "shown", "shut", "spoken", "struck", "taught", "thrown", "worn",
    "executed", "parsed", "processed", "triggered", "created", "deleted", "modified",
    "invoked", "called", "emitted", "evaluated", "checked", "rendered", "updated"
}

# Fallback STE substitutions
DEFAULT_STE_SUBSTITUTIONS = {
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

DEFAULT_STE_NOMINALIZATIONS = {
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

DEFAULT_STE_FLUFF_PHRASES = [
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

# Fallback ACE rules
DEFAULT_ACE_FORBIDDEN_MODALS = {
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

DEFAULT_ACE_AMBIGUOUS_WORDS = {
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

DEFAULT_ACE_CONTRACT_KEYWORDS = {"GIVEN", "WHEN", "THEN", "INVARIANT", "PRECONDITION", "POSTCONDITION"}


def count_syllables_in_word(word: str) -> int:
    """Counts syllables in an English word using phonetic heuristic rules."""
    clean_word = re.sub(r"[^a-zA-Z]", "", word.lower())
    if not clean_word:
        return 0
    if len(clean_word) <= 3:
        return 1

    clean_word = re.sub(r"(?:[^laeiouy]|ed|es|e)$", "", clean_word)
    clean_word = re.sub(r"^y", "", clean_word)

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


class ProseValidator:
    def __init__(self, mode: str = "ste", lexicon_path: Optional[str] = None):
        self.mode = mode.lower()
        self.lexicon = self._load_lexicon(lexicon_path)
        self.ste_substitutions = self._extract_ste_substitutions()
        self.ste_nominalizations = self._extract_ste_nominalizations()
        self.ste_fluff_phrases = self._extract_ste_fluff_phrases()
        self.ace_forbidden_modals = self._extract_ace_modals()
        self.ace_ambiguous_words = self._extract_ace_ambiguous_words()

    def _load_lexicon(self, path: Optional[str]) -> Dict[str, Any]:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        candidates = [
            path,
            os.path.abspath(os.path.join(script_dir, "..", "assets", "lexicon.yaml")),
            os.path.join(os.getcwd(), ".agents", "skills", "prose", "assets", "lexicon.yaml"),
            os.path.join(os.getcwd(), ".agents", "skills", "write", "assets", "lexicon.yaml"),
            os.path.join(os.getcwd(), ".agents", "skills", "ace-write", "assets", "lexicon.yaml"),
        ]
        target_path = next((c for c in candidates if c and os.path.exists(c)), None)

        if target_path and os.path.exists(target_path) and yaml:
            try:
                with open(target_path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                    return data if isinstance(data, dict) else {}
            except Exception:
                return {}
        return {}

    def _extract_ste_substitutions(self) -> Dict[str, str]:
        subs = dict(DEFAULT_STE_SUBSTITUTIONS)
        ste_section = self.lexicon.get("ste", {})
        items = ste_section.get("substitutions", self.lexicon.get("substitutions", []))
        for item in items:
            if isinstance(item, dict) and "term" in item and "replacement" in item:
                subs[item["term"].lower()] = item["replacement"]
        return subs

    def _extract_ste_nominalizations(self) -> Dict[str, str]:
        noms = dict(DEFAULT_STE_NOMINALIZATIONS)
        ste_section = self.lexicon.get("ste", {})
        items = ste_section.get("nominalizations", self.lexicon.get("nominalizations", []))
        for item in items:
            if isinstance(item, dict) and "phrase" in item and "replacement" in item:
                noms[item["phrase"].lower()] = item["replacement"]
        return noms

    def _extract_ste_fluff_phrases(self) -> List[str]:
        fluff = list(DEFAULT_STE_FLUFF_PHRASES)
        ste_section = self.lexicon.get("ste", {})
        items = ste_section.get("fluff_phrases", self.lexicon.get("fluff_phrases", []))
        for item in items:
            if isinstance(item, str) and item.lower() not in fluff:
                fluff.append(item.lower())
        return fluff

    def _extract_ace_modals(self) -> Dict[str, str]:
        modals = dict(DEFAULT_ACE_FORBIDDEN_MODALS)
        ace_section = self.lexicon.get("ace", {})
        modal_keywords = ace_section.get("modal_keywords", self.lexicon.get("modal_keywords", {}))
        disallowed = modal_keywords.get("disallowed", [])
        for item in disallowed:
            if isinstance(item, str) and item.lower() not in modals:
                modals[item.lower()] = "SHALL or MUST"
        return modals

    def _extract_ace_ambiguous_words(self) -> Dict[str, str]:
        ambig = dict(DEFAULT_ACE_AMBIGUOUS_WORDS)
        ace_section = self.lexicon.get("ace", {})
        items = ace_section.get("disallowed_terms", self.lexicon.get("disallowed_terms", []))
        for item in items:
            if isinstance(item, dict) and "term" in item and "replacement" in item:
                ambig[item["term"].lower()] = item["replacement"]
        return ambig

    def extract_prose_lines(self, text: str) -> List[Tuple[int, str]]:
        """Extracts prose lines, filtering out YAML frontmatter, code blocks, tables, and HTML comments."""
        lines = text.splitlines()
        prose_lines: List[Tuple[int, str]] = []

        in_frontmatter = False
        in_code_block = False
        in_html_comment = False

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
                continue
            if in_code_block:
                continue

            if "<!--" in stripped and "-->" not in stripped:
                in_html_comment = True
                continue
            if in_html_comment:
                if "-->" in stripped:
                    in_html_comment = False
                continue

            if not stripped:
                continue
            if stripped.startswith("|") and stripped.endswith("|"):
                continue
            if stripped.startswith("#"):
                prose_lines.append((idx, re.sub(r"^#+\s*", "", stripped)))
                continue

            prose_lines.append((idx, line))

        return prose_lines

    def calculate_readability_metrics(self, prose_lines: List[Tuple[int, str]]) -> Dict[str, Any]:
        """Calculates Flesch Reading Ease and Flesch-Kincaid Grade Level."""
        total_words = 0
        total_syllables = 0
        all_sentences: List[str] = []

        for _, line in prose_lines:
            if re.match(r"^[-=_*]{3,}$", line.strip()):
                continue
            clean_line = re.sub(r"^#+\s*", "", line.strip())
            clean_line = re.sub(r"^\s*([-*+]|\d+\.)\s+", "", clean_line)
            clean_line = re.sub(r"^\s*>\s*", "", clean_line).strip()
            clean_line = re.sub(r"`[^`]+`", "code", clean_line)

            if not clean_line:
                continue

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

        fre = 206.835 - (1.015 * words_per_sentence) - (84.6 * syllables_per_word)
        fre = round(max(0.0, min(100.0, fre)), 2)

        fkgl = (0.39 * words_per_sentence) + (11.8 * syllables_per_word) - 15.59
        fkgl = round(max(0.0, fkgl), 2)

        sentence_lengths = [len(s.split()) for s in all_sentences]
        max_sentence_length = max(sentence_lengths) if sentence_lengths else 0

        return {
            "mode": self.mode,
            "flesch_reading_ease": fre,
            "flesch_kincaid_grade": fkgl,
            "total_words": total_words,
            "total_sentences": num_sentences,
            "avg_sentence_length": round(words_per_sentence, 2),
            "max_sentence_length": max_sentence_length,
            "syllables_per_word": round(syllables_per_word, 2),
        }

    def validate_text(self, text: str) -> Tuple[List[Diagnostic], Dict[str, Any]]:
        """Validates prose text and returns diagnostics and metrics."""
        diagnostics: List[Diagnostic] = []
        prose_lines = self.extract_prose_lines(text)
        metrics = self.calculate_readability_metrics(prose_lines)

        if self.mode == "ste":
            self._validate_ste(prose_lines, metrics, diagnostics)
        else:
            self._validate_ace(prose_lines, metrics, diagnostics)

        return diagnostics, metrics

    def _validate_ste(self, prose_lines: List[Tuple[int, str]], metrics: Dict[str, Any], diagnostics: List[Diagnostic]):
        if metrics["total_words"] >= 15 and metrics["flesch_reading_ease"] < 65.0:
            diagnostics.append(
                Diagnostic(
                    line=1,
                    column=1,
                    rule_id="READABILITY_SCORE_LOW",
                    severity="ERROR",
                    message=f"Flesch Reading Ease score ({metrics['flesch_reading_ease']}) is below 65.0. Grade Level: {metrics['flesch_kincaid_grade']}.",
                    snippet=f"Average sentence length: {metrics['avg_sentence_length']} words, Syllables/word: {metrics['syllables_per_word']}",
                    suggested_fix="Shorten sentences and replace complex words with simpler alternatives."
                )
            )

        for line_num, line in prose_lines:
            clean_line = re.sub(r"^#+\s*", "", line.strip())
            clean_line = re.sub(r"^\s*([-*+]|\d+\.)\s+", "", clean_line)
            clean_line = re.sub(r"^\s*>\s*", "", clean_line).strip()

            if not clean_line:
                continue

            if re.match(r"^[-=_*]{3,}$", line.strip()):
                diagnostics.append(
                    Diagnostic(
                        line=line_num,
                        column=1,
                        rule_id="HORIZONTAL_DIVIDER_DISALLOWED",
                        severity="ERROR",
                        message=f"Horizontal rule divider '{line.strip()}' is prohibited in laconic prose.",
                        snippet=line.strip(),
                        suggested_fix="Remove divider line and use markdown headers."
                    )
                )
                continue

            prose_to_analyze = re.sub(r"`[^`]+`", "TOKEN", clean_line)

            # 1. Sentence length <= 20 words for laconic STE
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
                            message=f"Sentence length ({len(words)} words) exceeds the STE maximum of 20 words.",
                            snippet=snippet_text,
                            suggested_fix="Split into two short sentences or use bullets."
                        )
                    )

            # 2. Passive voice
            passive_regex = re.compile(
                r"\b(am|is|are|was|were|be|been|being)\s+([a-zA-Z]+ed|" + "|".join(IRREGULAR_PAST_PARTICIPLES) + r")\b",
                re.IGNORECASE
            )
            for match in passive_regex.finditer(prose_to_analyze):
                diagnostics.append(
                    Diagnostic(
                        line=line_num,
                        column=match.start() + 1,
                        rule_id="PASSIVE_VOICE_DISALLOWED",
                        severity="ERROR",
                        message=f"Passive voice '{match.group(0)}' detected. Use active voice.",
                        snippet=clean_line,
                        suggested_fix="Rephrase in active voice (Subject + Verb + Object)."
                    )
                )

            # 3. Fluff phrases
            for fluff in self.ste_fluff_phrases:
                pattern = rf"\b{re.escape(fluff)}\b"
                for match in re.finditer(pattern, prose_to_analyze, flags=re.IGNORECASE):
                    diagnostics.append(
                        Diagnostic(
                            line=line_num,
                            column=match.start() + 1,
                            rule_id="FLUFF_PHRASE_DETECTED",
                            severity="ERROR",
                            message=f"Filler phrase '{match.group(0)}' detected.",
                            snippet=clean_line,
                            suggested_fix=f"Delete '{match.group(0)}' and state the point directly."
                        )
                    )

            # 4. Nominalizations
            for nom, replacement in self.ste_nominalizations.items():
                pattern = rf"\b{re.escape(nom)}\b"
                for match in re.finditer(pattern, prose_to_analyze, flags=re.IGNORECASE):
                    diagnostics.append(
                        Diagnostic(
                            line=line_num,
                            column=match.start() + 1,
                            rule_id="NOMINALIZATION_DETECTED",
                            severity="ERROR",
                            message=f"Nominalization '{match.group(0)}' detected.",
                            snippet=clean_line,
                            suggested_fix=f"Replace with direct active verb '{replacement}'."
                        )
                    )

            # 5. Complex words
            for term, replacement in self.ste_substitutions.items():
                pattern = rf"\b{re.escape(term)}\b"
                for match in re.finditer(pattern, prose_to_analyze, flags=re.IGNORECASE):
                    diagnostics.append(
                        Diagnostic(
                            line=line_num,
                            column=match.start() + 1,
                            rule_id="COMPLEX_WORD_DETECTED",
                            severity="ERROR",
                            message=f"Complex term '{match.group(0)}' detected.",
                            snippet=clean_line,
                            suggested_fix=f"Replace '{match.group(0)}' with '{replacement}'."
                        )
                    )

            # 6. Raw ACE keyword residue in pure STE prose
            first_token = clean_line.split()[0].rstrip(":,")
            if first_token in {"GIVEN", "WHEN", "THEN", "INVARIANT", "PRECONDITION", "POSTCONDITION"}:
                diagnostics.append(
                    Diagnostic(
                        line=line_num,
                        column=1,
                        rule_id="RAW_ACE_KEYWORD_RESIDUE",
                        severity="ERROR",
                        message=f"Raw ACE keyword '{first_token}' detected in STE output.",
                        snippet=clean_line,
                        suggested_fix=f"Unwrap '{first_token}' into plain active English, or switch to ACE mode."
                    )
                )

            # 7. Prohibited dashes
            for dash_pattern, name in [(r"—", "Em-dash"), (r"–", "En-dash"), (r"(?<=\S)\s*--\s*(?=\S)", "Double-hyphen dash")]:
                for match in re.finditer(dash_pattern, prose_to_analyze):
                    diagnostics.append(
                        Diagnostic(
                            line=line_num,
                            column=match.start() + 1,
                            rule_id="EM_DASH_DISALLOWED",
                            severity="ERROR",
                            message=f"{name} '{match.group(0)}' is prohibited in laconic prose.",
                            snippet=clean_line,
                            suggested_fix="Delete the dash or replace with a period, comma, or colon."
                        )
                    )

    def _validate_ace(self, prose_lines: List[Tuple[int, str]], metrics: Dict[str, Any], diagnostics: List[Diagnostic]):
        for line_num, line in prose_lines:
            clean_line = re.sub(r"^#+\s*", "", line.strip())
            clean_line = re.sub(r"^\s*([-*+]|\d+\.)\s+", "", clean_line)
            clean_line = re.sub(r"^\s*>\s*", "", clean_line).strip()

            if not clean_line:
                continue

            if re.match(r"^[-=_*]{3,}$", line.strip()):
                diagnostics.append(
                    Diagnostic(
                        line=line_num,
                        column=1,
                        rule_id="HORIZONTAL_DIVIDER_DISALLOWED",
                        severity="ERROR",
                        message=f"Horizontal rule divider '{line.strip()}' is prohibited in Agentic ACE.",
                        snippet=line.strip(),
                        suggested_fix="Remove divider line and use markdown headers."
                    )
                )
                continue

            prose_to_analyze = re.sub(r"`[^`]+`", "TOKEN", clean_line)

            # 1. Check for Forbidden Modals
            for forbidden_word, fix in self.ace_forbidden_modals.items():
                pattern = rf"\b{re.escape(forbidden_word)}\b"
                for match in re.finditer(pattern, prose_to_analyze, flags=re.IGNORECASE):
                    diagnostics.append(
                        Diagnostic(
                            line=line_num,
                            column=match.start() + 1,
                            rule_id="FORBIDDEN_MODAL",
                            severity="ERROR",
                            message=f"Forbidden modal or uncertainty word '{match.group(0)}' detected.",
                            snippet=clean_line,
                            suggested_fix=f"Replace '{match.group(0)}' with {fix}."
                        )
                    )

            # 2. Check for Ambiguous Words
            for vague_word, fix in self.ace_ambiguous_words.items():
                pattern = rf"\b{re.escape(vague_word)}\b"
                for match in re.finditer(pattern, prose_to_analyze, flags=re.IGNORECASE):
                    diagnostics.append(
                        Diagnostic(
                            line=line_num,
                            column=match.start() + 1,
                            rule_id="AMBIGUOUS_WORD",
                            severity="ERROR",
                            message=f"Ambiguous term '{match.group(0)}' detected.",
                            snippet=clean_line,
                            suggested_fix=f"Replace '{match.group(0)}' with {fix}."
                        )
                    )

            # 3. Check for Passive Voice
            passive_regex = re.compile(
                r"\b(am|is|are|was|were|be|been|being)\s+([a-zA-Z]+ed|" + "|".join(IRREGULAR_PAST_PARTICIPLES) + r")\b",
                re.IGNORECASE
            )
            for match in passive_regex.finditer(prose_to_analyze):
                diagnostics.append(
                    Diagnostic(
                        line=line_num,
                        column=match.start() + 1,
                        rule_id="PASSIVE_VOICE",
                        severity="ERROR",
                        message=f"Passive voice construct '{match.group(0)}' detected.",
                        snippet=clean_line,
                        suggested_fix="Rephrase in active SVO voice (Actor + Action + Target)."
                    )
                )

            # 4. Check for Sentence Length (Atomic sentence <= 25 words in ACE)
            sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", prose_to_analyze) if s.strip()]
            for s in sentences:
                words = s.split()
                if len(words) > 25:
                    diagnostics.append(
                        Diagnostic(
                            line=line_num,
                            column=1,
                            rule_id="ATOMIC_SENTENCE",
                            severity="ERROR",
                            message=f"Sentence length ({len(words)} words) exceeds ACE maximum of 25 words.",
                            snippet=s[:60] + "...",
                            suggested_fix="Split compound clauses into separate atomic sentences."
                        )
                    )

            # 5. Prohibited dashes
            for dash_pattern, name in [(r"—", "Em-dash"), (r"–", "En-dash"), (r"(?<=\S)\s*--\s*(?=\S)", "Double-hyphen dash")]:
                for match in re.finditer(dash_pattern, prose_to_analyze):
                    diagnostics.append(
                        Diagnostic(
                            line=line_num,
                            column=match.start() + 1,
                            rule_id="EM_DASH_DISALLOWED",
                            severity="ERROR",
                            message=f"{name} '{match.group(0)}' is prohibited in Agentic ACE.",
                            snippet=clean_line,
                            suggested_fix="Delete the dash or replace with a colon or comma."
                        )
                    )


class PlainEnglishValidator(ProseValidator):
    """Backward compatibility subclass for write skill consumers."""
    def __init__(self, lexicon_path: Optional[str] = None):
        super().__init__(mode="ste", lexicon_path=lexicon_path)


class AceValidator(ProseValidator):
    """Backward compatibility subclass for ace-write skill consumers."""
    def __init__(self, lexicon_path: Optional[str] = None):
        super().__init__(mode="ace", lexicon_path=lexicon_path)

    def validate_text(self, text: str) -> List[Diagnostic]:
        diagnostics, _ = super().validate_text(text)
        return diagnostics


def format_cli_output(file_label: str, diagnostics: List[Diagnostic], metrics: Dict[str, Any]) -> str:
    lines = []
    mode = metrics.get("mode", "ste").upper()
    fre = metrics.get("flesch_reading_ease", 0)
    asl = metrics.get("avg_sentence_length", 0)
    words = metrics.get("total_words", 0)

    score_color = "\033[92m" if fre >= 65.0 else "\033[91m"
    metrics_summary = f"  \033[90mMode={mode} | FRE={score_color}{fre}\033[0m | Words={words} | Avg Sentence={asl}w"

    if not diagnostics:
        lines.append(f"\033[92m✔ {file_label}: 0 violations found ({mode} verified).\033[0m")
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
    parser = argparse.ArgumentParser(description="Prose Readability & Style Validator (ASD-STE100 & ACE)")
    parser.add_argument("target", nargs="?", default="-", help="Path to markdown file or directory, or '-' for stdin")
    parser.add_argument("--mode", choices=["ste", "ace"], default="ste", help="Validation mode: ste (default) or ace")
    parser.add_argument("--json", action="store_true", help="Output machine-readable JSON diagnostics")
    parser.add_argument("--check", action="store_true", help="Stdin check mode")
    parser.add_argument("--lexicon", help="Optional path to custom lexicon.yaml")
    args = parser.parse_args()

    validator = ProseValidator(mode=args.mode, lexicon_path=args.lexicon)

    # Stdin stream processing
    if args.target == "-" or args.check:
        input_text = sys.stdin.read()
        diagnostics, metrics = validator.validate_text(input_text)
        has_errors = any(d.severity == "ERROR" for d in diagnostics)

        if args.json:
            result = {
                "file": "stdin",
                "valid": not has_errors,
                "metrics": metrics,
                "error_count": len([d for d in diagnostics if d.severity == "ERROR"]),
                "warning_count": len([d for d in diagnostics if d.severity == "WARNING"]),
                "diagnostics": [d.to_dict() for d in diagnostics],
            }
            print(json.dumps(result, indent=2))
        else:
            print(format_cli_output("stdin", diagnostics, metrics))

        sys.exit(1 if has_errors else 0)

    target_path = os.path.abspath(args.target)
    if not os.path.exists(target_path):
        sys.stderr.write(f"Error: Target path '{target_path}' does not exist.\n")
        sys.exit(1)

    files_to_check = []
    if os.path.isdir(target_path):
        for root, _, files in os.walk(target_path):
            for file in files:
                if file.endswith((".md", ".markdown")):
                    files_to_check.append(os.path.join(root, file))
    else:
        files_to_check.append(target_path)

    results = []
    total_errors = 0

    for file_path in files_to_check:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        diagnostics, metrics = validator.validate_text(content)
        errors = [d for d in diagnostics if d.severity == "ERROR"]
        warnings = [d for d in diagnostics if d.severity == "WARNING"]
        total_errors += len(errors)

        results.append({
            "file": file_path,
            "valid": len(errors) == 0,
            "metrics": metrics,
            "error_count": len(errors),
            "warning_count": len(warnings),
            "errors": [d.to_dict() for d in errors]
        })

        if not args.json:
            rel_path = os.path.relpath(file_path, os.getcwd())
            print(format_cli_output(rel_path, diagnostics, metrics))

    if args.json:
        print(json.dumps({
            "total_files": len(files_to_check),
            "clean_files": len([r for r in results if r["valid"]]),
            "results": results
        }, indent=2))

    sys.exit(1 if total_errors > 0 else 0)


if __name__ == "__main__":
    main()
