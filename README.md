# The Round Table

The Round Table is a home for AI coding tools.
It gives agents simple workflows, exact specs, clear writing, and fast test checks.

## Project Structure

```text
the-round-table/
├── .agents/
│   └── skills/
│       ├── ace-write/     # ACE spec skill and checker
│       ├── agile/         # Agile team orchestrator
│       ├── architect/     # System design and plan checker
│       ├── commit/        # Commit note skill and checker
│       ├── developer/     # Task execution and test checker
│       ├── explain/       # Plain explanation skill and checker
│       ├── grill/         # Design interview skill
│       ├── learn/         # 30-day personalized curriculum skill
│       ├── po/            # Product owner story checker
│       ├── qa/            # Test and code review checker
│       ├── review/        # 8-concern code review skill
│       ├── scrum-master/  # Sprint release and retro checker
│       ├── task/          # Task graph skill and checker
│       ├── ux-designer/   # User flow and wireframe checker
│       └── write/         # Clear text skill and checker
├── docs/
│   └── .prompts-and-prayers/
│       ├── backlog/       # Feature backlog ledger
│       ├── grilling/      # Saved design logs
│       └── sprints/       # Sprint workspaces and artifacts
├── tests/                 # Unit tests for checkers
├── .gitignore
└── README.md
```

## Agile Team Workflow

The repo provides a full agile squad for building software.
The team works through five steps:

1. **Define**: The `po` and `ux-designer` skills draft user stories and screen flows.
2. **Review**: The `architect` skill plans system design and engineering tasks.
3. **Build**: The `developer` skill writes code and runs unit tests.
4. **Verify**: The `qa` skill checks test runs and reviews code changes.
5. **Repeat**: The `scrum-master` skill logs releases and prepares git commits.

The human acts as the leader. The agent stops for your approval at each key step.

### Example Run

Start a full sprint with one command:

```text
/agile
```

You can also run any skill on its own:

```text
/po            # Ask the PO to refine a user story
/ux-designer   # Ask the UX designer for a screen flow
/qa            # Ask QA to review current code changes
```

## Testing & Quality Gates

Run all unit tests to check the skill scripts:

```bash
python3 -m unittest discover tests
```

You can also run each test script by hand:

```bash
# Check text score
python3 .agents/skills/write/scripts/validator.py README.md --json

# Check task graph rules
python3 .agents/skills/task/scripts/validator.py docs/.tasks/active.md --json

# Check ACE spec rules
python3 .agents/skills/ace-write/scripts/validator.py docs/.../artifact.md --json

# Check explanation rules
python3 .agents/skills/explain/scripts/validator.py docs/.../sample.explained.md --json

# Check commit note rules
python3 .agents/skills/commit/scripts/validator.py --check < commit_message.txt
```

## Adding New Skills

Follow these steps to add a new skill to the project:

1. **Make a Skill Folder**: Add a folder under `.agents/skills/<skill-name>/`.
2. **Write the Contract**: Add `SKILL.md` using `ace-write` rules with active voice and clear constraints.
3. **Add a Check Script**: Put your Python script in `.agents/skills/<skill-name>/scripts/validator.py`.
4. **Write Unit Tests**: Add test cases to `tests/test_<skill_name>_validator.py`.
5. **Run the Test Suite**: Run `python3 -m unittest discover tests` and make sure all tests pass.
