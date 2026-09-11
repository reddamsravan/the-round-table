# The Round Table

The Round Table is a home for AI coding tools.
It gives agents simple workflows, exact specs, clear writing, and fast test checks.

## Project Structure

```text
the-round-table/
├── .agents/
│   └── skills/
│       ├── breakdown/     # Task graph decomposition skill
│       ├── build/         # Task implementation skill
│       ├── commit/        # Commit staging and message drafting skill
│       ├── define/        # Requirements specification checker
│       ├── design/        # User flow and wireframe checker
│       ├── explain/       # Plain explanation skill and checker
│       ├── interview/     # Design interview skill
│       ├── learn/         # 30-day personalized curriculum skill
│       ├── plot/          # Technical spec and plan checker
│       ├── prose/         # STE and ACE prose checker
│       ├── review/        # 8-concern code review skill
│       ├── ship/          # Release notes and commit coordinator
│       ├── verify/        # Test and code review checker
│       └── write-a-skill/ # Skill authoring and schema checker
├── docs/
│   └── .prompts-and-prayers/
│       ├── backlog/       # Feature backlog ledger
│       ├── interviews/    # Saved design logs
│       └── sprints/       # Sprint workspaces and artifacts
├── tests/                 # Unit tests for checkers
├── .gitignore
└── README.md
```

## Team Workflow

The repo provides skills for building software.
The skills cover each step:

1. **Define**: The `define` and `design` skills draft requirements and screen flows.
2. **Plan**: The `plot` skill plans system design and engineering tasks.
3. **Build**: The `build` skill writes code and runs unit tests.
4. **Verify**: The `verify` skill checks test runs and reviews code changes.
5. **Ship**: The `ship` skill logs releases and prepares git commits.

The human acts as the leader. The agent stops for your approval at each key step.

### Example Run

Run any skill on its own:

```text
/define        # Ask the define skill for a requirements spec
/design        # Ask the design skill for a screen flow
/plot          # Ask the plot skill for a system plan
/build         # Ask the build skill to write code and tests
/verify        # Ask the verify skill to check tests and diffs
/ship          # Ask the ship skill to draft release notes
```

## Testing & Quality Gates

Run all unit tests to check the skill scripts:

```bash
python3 -m unittest discover tests
```

You can also run each test script by hand:

```bash
# Check prose score (ASD-STE100)
python3 .agents/skills/prose/scripts/validator.py README.md --json

# Check ACE contract rules
python3 .agents/skills/prose/scripts/validator.py docs/.../artifact.md --mode ace --json

# Check requirement spec rules
python3 .agents/skills/define/scripts/validator.py docs/.../01-define/spec.md --json

# Check design spec rules
python3 .agents/skills/design/scripts/validator.py docs/.../02-design/design-spec.md --json

# Check plot spec rules
python3 .agents/skills/plot/scripts/validator.py docs/.../03-plot/ --json

# Check verify rules
python3 .agents/skills/verify/scripts/validator.py docs/.../05-verify/ --json

# Check explanation rules
python3 .agents/skills/explain/scripts/validator.py docs/.../sample.explained.md --json

# Check skill frontmatter rules
python3 .agents/skills/write-a-skill/scripts/validator.py .agents/skills/.../ --json
```

## Adding New Skills

Run `/write-a-skill` to create a new skill following the [Agent Skills standard](.agents/skills/write-a-skill/references/specification.md).
Follow these manual steps to add a skill:

1. **Make a Skill Folder**: Add a folder under `.agents/skills/<skill-name>/`.
2. **Write the Contract**: Add `SKILL.md` and check prose with `prose` using `--mode ace`.
3. **Add a Check Script**: If you need exact math or transforms, add a script in `.agents/skills/<skill-name>/scripts/validator.py`.
4. **Write Unit Tests**: If you added a script, add test cases to `tests/test_<skill_name>_validator.py`.
5. **Run the Test Suite**: Run `python3 -m unittest discover tests` and make sure all tests pass.
