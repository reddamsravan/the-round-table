# The Round Table

The Round Table is a home for AI coding tools.
It gives agents simple workflows, exact specs, clear writing, and fast test checks.

## Project Structure

```text
the-round-table/
├── .agents/
│   └── skills/
│       ├── ace-write/     # ACE spec skill and checker
│       ├── commit/        # Commit note skill and checker
│       ├── grill/         # Design interview skill
│       ├── task/          # Task graph skill and checker
│       └── write/         # Clear text skill and checker
├── docs/
│   ├── .prompts-and-prayers/
│   │   └── grilling/      # Saved design logs
│   └── .tasks/            # Active and archived task graphs
├── tests/                 # Unit tests for checkers
├── .gitignore
└── README.md
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
