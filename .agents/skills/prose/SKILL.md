---
name: prose
description: >-
  Writes and validates laconic text using ASD-STE100 and ACE. Activate on '/prose'.
---

The agent SHALL write laconic technical text.

## Rules
- All created or generated prose MUST be laconic.
- The agent SHALL apply ASD-STE100 rules by default.
- The agent SHALL apply Attempto Controlled English (ACE) rules for contracts, specifications, invariants, and disambiguation.
- The agent SHALL NOT use passive voice.
- The agent SHALL NOT use filler words, padding phrases, or em-dashes.
- The agent SHALL overwrite target files in place.

## Procedures

### Procedure A: Inline Text Processing
1. Read input text.
2. Select mode: ASD-STE100 (default) or ACE (contracts and disambiguation).
3. Draft laconic text following the mode rules.
4. Validate: `echo "<text>" | python3 .agents/skills/prose/scripts/validator.py [--mode ace] --json`
5. Fix violations until validator exits 0.

### Procedure B: Document File Processing
1. Read target file. Preserve frontmatter, code blocks, and tables verbatim.
2. Rewrite prose to satisfy mode rules.
3. Overwrite the target file in place.
4. Validate: `python3 .agents/skills/prose/scripts/validator.py <path> [--mode ace] --json`
5. Fix violations until validator exits 0.

### Procedure C: Mode Reference Specifications

#### ASD-STE100 Rules (Default)

| Rule | Requirement |
| :--- | :--- |
| **Sentence Length** | Max 20 words for procedural steps. Max 25 words for descriptions. |
| **Voice** | Imperative for instructions. Active SVO for descriptions. No passive voice. |
| **Vocabulary** | Use everyday words from `assets/lexicon.yaml`. De-nominalize verbs. |
| **Density** | Delete filler, throat-clearing, and padding. No em-dashes or horizontal dividers. |
| **Readability** | Maintain Flesch Reading Ease >= 65. |

#### Attempto Controlled English Rules (Disambiguation)

| Rule | Requirement |
| :--- | :--- |
| **Modals** | Use `SHALL`, `SHALL NOT`, `MUST`, `MUST NOT` only. Never use `should`, `may`, `could`. |
| **Structure** | Use `GIVEN / WHEN / THEN / INVARIANT` blocks or `IF ... THEN` clauses. |
| **Precision** | Replace vague terms (`etc.`, `fast`, `user-friendly`) with exact thresholds. |
| **Voice** | Active SVO only. Every clause names an explicit actor and action. |

## Verification Checklist
- [ ] Validate frontmatter schema:
  ```bash
  python3 .agents/skills/write-a-skill/scripts/validator.py .agents/skills/prose/ --json
  ```
- [ ] Validate skill prose:
  ```bash
  python3 .agents/skills/prose/scripts/validator.py .agents/skills/prose/SKILL.md --mode ace --json
  ```
- [ ] Run unit tests:
  ```bash
  python3 -m unittest discover tests -k test_prose_validator
  ```
- [ ] Verify skill registration in `README.md` under Project Structure.
