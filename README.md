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
│       ├── define/        # Requirements specification and criteria skill
│       ├── design/        # Interface and flow design skill
│       ├── explain/       # Laconic plain-English explanation skill
│       ├── interview/     # Design interview skill
│       ├── learn/         # 30-day personalized curriculum skill
│       ├── plot/          # Technical architecture and plan skill
│       ├── prose/         # STE and ACE prose checker
│       ├── review/        # Concern-driven code review skill
│       ├── ship/          # Commit and retrospective skill
│       ├── verify/        # Criteria verification skill
│       └── write-a-skill/ # Skill authoring and schema checker
├── docs/
│   └── .prompts-and-prayers/
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
4. **Verify**: The `verify` skill evaluates acceptance criteria against the workspace.
5. **Ship**: The `ship` skill prepares git commits and authors retrospectives.

The human acts as the leader. The agent stops for your approval at each key step.

### Example Run

Run any skill on its own:

```text
/define        # Ask the define skill for a requirements spec
/design        # Ask the design skill for a screen flow
/plot          # Ask the plot skill for a system plan
/build         # Ask the build skill to write code and tests
/verify        # Ask the verify skill to check acceptance criteria
/ship          # Ask the ship skill to commit changes and record retrospectives
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
