---
name: prose
description: Laconic technical prose engine. Uses ASD-STE100 by default for documentation and Attempto Controlled English (ACE) to eliminate ambiguity in contracts.
---

The agent SHALL write laconic technical text with zero filler.
The agent SHALL apply ASD-STE100 by default.
The agent SHALL apply Attempto Controlled English (ACE) for contracts, invariants, and disambiguation.

## ASD-STE100 Rules (Default)

| Rule | Requirement |
| :--- | :--- |
| **Sentence Length** | Max 20 words for procedural steps. Max 25 words for descriptions. |
| **Voice** | Imperative for instructions. Active SVO for descriptions. No passive voice. |
| **Vocabulary** | Use everyday words from `assets/lexicon.yaml`. De-nominalize verbs. |
| **Density** | Delete filler, throat-clearing, and padding. No em-dashes or horizontal dividers. |
| **Readability** | Maintain Flesch Reading Ease >= 65. |

## Attempto Controlled English Rules (Disambiguation)

| Rule | Requirement |
| :--- | :--- |
| **Modals** | Use `SHALL`, `SHALL NOT`, `MUST`, `MUST NOT` only. Never use `should`, `may`, `could`. |
| **Structure** | Use `GIVEN / WHEN / THEN / INVARIANT` blocks or `IF ... THEN` clauses. |
| **Precision** | Replace vague terms (`etc.`, `fast`, `user-friendly`) with exact thresholds. |
| **Voice** | Active SVO only. Every clause names an explicit actor and action. |

## Procedures

### Inline Text
1. Read input text.
2. Select mode: ASD-STE100 (default) or ACE (contracts and disambiguation).
3. Draft laconic text following the mode rules.
4. Validate: `echo "<text>" | python3 .agents/skills/prose/scripts/validator.py [--mode ace] --json`
5. Fix violations until validator exits 0.

### Document File
1. Read target file. Preserve frontmatter, code blocks, and tables verbatim.
2. Rewrite prose to satisfy mode rules.
3. Output to `{dir}/{stem}.prose.md` or overwrite in place.
4. Validate: `python3 .agents/skills/prose/scripts/validator.py <path> [--mode ace] --json`
5. Fix violations until validator exits 0.
