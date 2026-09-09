---
name: explain
description: Explains code, architecture, errors, and concepts in plain English. Integrates strictly with write skill.
---

The agent SHALL explain code, architecture, stack traces, and specifications in plain English.
The agent SHALL structure every explanation into four sequential sections:
1. `## Problem & Context`
2. `## Mental Model & Analogy`
3. `## How It Works (Mechanics & Anatomy)`
4. `## Pitfalls & Trade-offs`

INVARIANT: every section MUST contain at least 15 words of plain prose.
INVARIANT: the agent SHALL NOT omit mandatory section headings.

## Procedures

### A: Inline or Stdin
1. The agent SHALL draft the explanation across the four mandatory sections.
2. The agent SHALL validate via Procedure E and return the verified text.

### B: Single File Companion
1. The agent SHALL read the source file and draft the 4-section explanation.
2. The agent SHALL determine destination:
   - User `--out <path>`: write to `<path>`.
   - Existing code file: write to `{dir}/{stem}.explained.md`.
   - Conceptual document: write to `docs/explanations/{slug}.md`.
3. The agent SHALL validate via Procedure E and write the verified file.

### C: Directory Batch
1. The agent SHALL run Procedure B for each source file in the directory.
2. The agent SHALL validate all files via Procedure E.

### D: Dry-Run Lint
The agent SHALL run `python3 .agents/skills/explain/scripts/validator.py <path> --json` and report diagnostics.

### E: Validation and Readability Gate
1. The agent SHALL execute `python3 .agents/skills/explain/scripts/validator.py <path-or-stdin> --json`.
2. IF errors exist, THEN the agent SHALL execute up to 3 automated refinement passes.
3. In each pass, the agent SHALL eliminate passive voice, shorten sentences, and replace multi-syllable jargon.
4. IF errors persist after 3 passes, THEN the agent SHALL report diagnostics to the user.

INVARIANT: the agent SHALL NOT deliver explanations that fail validation.
INVARIANT: all explanation prose MUST satisfy write skill quality gates with Flesch score of 65 or higher.
