---
name: write
description: Turns specs and docs into plain English (Flesch >= 65). Use ace-write for skills and agent contracts.
---

## Linguistic Rules

1. **Active SVO voice**: every sentence names an actor performing an action. No passive voice.
2. **Common vocabulary**: replace Latinate or bureaucratic terms with everyday words (`assets/lexicon.yaml`).
3. **De-nominalize**: convert smothered nouns back to verbs (decide, not "make a determination").
4. **Short sentences**: max 20 words; target 10-15. Split compound sentences into bullets.
5. **Unwrap ACE blocks**: rewrite `GIVEN/WHEN/THEN/INVARIANT` and `SHALL/MUST` as plain active prose.
6. **No filler**: delete preambles, throat-clearing, and redundant modifiers.
7. **Bullet lists**: use markdown bullets for multi-item lists, conditions, and procedures.
8. **No dashes**: delete em-dashes, en-dashes, and `---` dividers. Use `##` headers instead.

## Procedures

### A: Inline / Stdin
1. Isolate code snippets, URLs, and structured data.
2. Rephrase prose using the rules above.
3. Validate: `echo "<text>" | python3 .agents/skills/write/scripts/validator.py --json`
4. Fix errors until validator exits 0 and Flesch >= 65.
5. Return the verified text.

### B: Single File
1. Read the file. Preserve YAML frontmatter, code fences, and tables verbatim.
2. Rephrase headers, paragraphs, and list items.
3. Output: overwrite with `--in-place`, else write to `{dir}/{stem}.plain.md`.
4. Validate: `python3 .agents/skills/write/scripts/validator.py <path> --json`
5. Fix until 0 errors remain.

### C: Directory Batch
1. Find all markdown files in the directory.
2. Run Procedure B on each file.
3. Validate: `python3 .agents/skills/write/scripts/validator.py <dir>`

### D: Dry-Run Lint
Run `python3 .agents/skills/write/scripts/validator.py <path>` and report violations.

After each run: validate with the validator script; fix until it exits 0.
