---
name: ace-write
description: Rewrites prose into deterministic Agentic ACE specs. Use for skills, agent contracts, system prompts, and inter-agent communication.
---

## Linguistic Rules

1. **Active SVO voice**: every sentence names an explicit subject performing an action. No passive voice.
2. **Strict modals**: use `SHALL`, `SHALL NOT`, `MUST`, `MUST NOT` only.
   Forbidden: `should`, `could`, `might`, `would`, `may`, `probably`, `possibly`, `maybe`, `ought`.
3. **Deterministic conditionals**: use `IF ... THEN` or `WHEN ... THEN` syntax. No implicit conditionals.
4. **Contract blocks**: structure requirements as `GIVEN / WHEN / THEN / INVARIANT` blocks.
5. **Atomic sentences**: max 25 words. Split compound clauses into separate sentences.
6. **No vague qualifiers**: replace open-ended terms with numeric thresholds or concrete identifiers.
7. **No dashes**: delete em-dashes, en-dashes, and `---` dividers. Use `##` headers instead.

## Procedures

### A: Inline / Prompt
1. Isolate code snippets and structured data.
2. Rephrase all prose into active SVO and ACE contract blocks.
3. Validate: `echo "<text>" | python3 .agents/skills/ace-write/scripts/validator.py --json`
4. Fix until validator exits 0.
5. Return the verified text.

### B: Single File
1. Read the file. Preserve YAML frontmatter, code fences, and tables verbatim.
2. Rephrase headers, instructions, list items, and paragraphs into Agentic ACE.
3. Output: overwrite with `--in-place`, else write to `{dir}/{stem}.ace.md`.
4. Validate: `python3 .agents/skills/ace-write/scripts/validator.py <path> --json`
5. Fix until 0 errors remain.

### C: Directory Batch
1. Find all markdown files in the directory.
2. Run Procedure B on each file.
3. Validate: `python3 .agents/skills/ace-write/scripts/validator.py <dir>`

### D: Dry-Run Lint
Run `python3 .agents/skills/ace-write/scripts/validator.py <path>` and report violations.

After each run: validate with the validator script; fix until it exits 0.
