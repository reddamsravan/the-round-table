# The Round Table

The Round Table is a home for AI coding tools.
It gives agents simple workflows, exact specs, clear writing, and fast test checks.

## Skills Catalog

The project provides four core agent skills:

### 1. ace-write
Turns raw text into exact specs.
It removes doubt, sets strict rules, and builds clean agent contracts.
- **Skill File**: [.agents/skills/ace-write/SKILL.md](.agents/skills/ace-write/SKILL.md)
- **Check Script**:
  ```bash
  python3 .agents/skills/ace-write/scripts/validator.py <file> --json
  ```

### 2. commit
Guides git staging, splits big diffs into clean batches, and writes standard commit notes.
It keeps subject lines short, active, and clear.
- **Slash Command**: `/commit`
- **Skill File**: [.agents/skills/commit/SKILL.md](.agents/skills/commit/SKILL.md)
- **Check Script**:
  ```bash
  python3 .agents/skills/commit/scripts/validator.py <file> --json
  ```

### 3. grill
Asks users clear questions to test plans, ideas, and system design.
It asks questions in rounds, tracks choices, and saves decision logs.
- **Slash Command**: `/grill`
- **Skill File**: [.agents/skills/grill/SKILL.md](.agents/skills/grill/SKILL.md)
- **Log Path**: `docs/.prompts-and-prayers/grilling/`

### 4. write
Turns dry technical notes into clear text.
It uses active voice, simple words, and keeps reading scores high.
- **Skill File**: [.agents/skills/write/SKILL.md](.agents/skills/write/SKILL.md)
- **Check Script**:
  ```bash
  python3 .agents/skills/write/scripts/validator.py <file> --json
  ```

## Project Structure

```text
the-round-table/
├── .agents/
│   └── skills/
│       ├── ace-write/     # ACE spec skill and checker
│       ├── commit/        # Commit note skill and checker
│       ├── grill/         # Design interview skill
│       └── write/         # Clear text skill and checker
├── docs/
│   └── .prompts-and-prayers/
│       └── grilling/      # Saved design logs
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
