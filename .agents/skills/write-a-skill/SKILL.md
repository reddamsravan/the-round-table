---
name: write-a-skill
description: >-
  Authors and verifies standard agent skills. Activate on '/write-a-skill' or requests to author skills.
---

The agent SHALL guide the user to author reliable agent skills adhering to [references/specification.md](references/specification.md).

## Rules
- The agent SHALL match the frontmatter `name` to the parent directory name.
- The agent SHALL invoke the `prose` skill with `--mode ace` to write and validate all skill prose.
- The agent SHALL recommend `scripts/` only when the skill requires exact computation, static AST parsing, or binary transforms.
- The agent SHALL NOT add `scripts/` for procedural workflows, document authoring, or review skills.
- IF a workflow has conditional paths or repeated steps, THEN the agent SHALL author separate procedures referenced by the workflow.
- The agent SHALL NOT duplicate statements across Rules, Workflow, and Procedures.
- Rules MUST define behavioral invariants and constraints only.
- Workflow MUST define sequential execution steps only.
- Procedures MUST define execution details for conditional or repeated steps only.
- The agent SHALL author a Verification Checklist unique to the execution outputs of the target skill.
- The agent SHALL NOT copy the skill authoring checklist into the target skill.

## Workflow
1. Execute Procedure A to interview the user and discover requirements.
2. Scaffold the skill directory structure per [references/specification.md](references/specification.md).
3. Copy `assets/skill_template.md` to `<skill-name>/SKILL.md` and populate frontmatter.
4. Author the sequential `Workflow` and conditional `Procedures`.
5. Scaffold required assets in `assets/` and reference guides in `references/`.
6. IF the skill requires deterministic computation, THEN execute Procedure B.
7. Execute all steps in the Verification Checklist.

## Procedures

### Procedure A: Discovery and Requirements
1. The agent SHALL activate the `interview` skill to map the design tree for the target skill.
2. The interview SHALL extract the skill name, slash command trigger, user intent keywords, inputs, outputs, and behavioral invariants.
3. The agent SHALL verify that the skill name consists of lowercase alphanumeric characters and single hyphens without edge hyphens.

### Procedure B: Script Scaffolding
1. The agent SHALL author self-contained helper code in `scripts/`.
2. The agent SHALL author unit tests in `tests/test_<skill_name>_validator.py`.
3. The agent SHALL run the test suite to verify that all unit tests pass.

## Verification Checklist
- [ ] Validate frontmatter schema:
  ```bash
  python3 .agents/skills/write-a-skill/scripts/validator.py .agents/skills/<skill-name>/ --json
  ```
- [ ] Validate skill prose:
  ```bash
  python3 .agents/skills/prose/scripts/validator.py .agents/skills/<skill-name>/SKILL.md --mode ace --json
  ```
- [ ] Run unit tests if scripts exist:
  ```bash
  python3 -m unittest discover tests
  ```
- [ ] Register the new skill in `README.md` under Project Structure.
