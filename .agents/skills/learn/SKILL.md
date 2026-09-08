---
name: learn
description: Generate and deliver a personalized 30-day curriculum on any topic using active learning pedagogy.
---

## Invocation

### Procedure A: Start or Switch Curriculum

1. The agent SHALL scan `docs/learn/` for a `progress.md` file with `status: active`.
2. IF an active curriculum exists, THEN the agent SHALL execute Procedure B.
3. IF no active curriculum exists, THEN the agent SHALL execute Procedure C.

### Procedure B: Active Curriculum Check and Continuation

1. The agent SHALL display the active curriculum name and `current_day`.
2. IF the user requested the next lesson or continuation, THEN the agent SHALL execute Procedure E.
3. IF the user requested a new topic, THEN the agent SHALL prompt the user to choose: `continue current curriculum | switch to new topic`.
4. IF the user chooses to continue, THEN the agent SHALL execute Procedure E.
5. IF the user chooses to switch, THEN the agent SHALL write `status: paused` to `progress.md` and execute Procedure C.
6. IF the user declines both choices, THEN the agent SHALL abort the intake process.

INVARIANT: the agent SHALL NOT delete or overwrite an existing curriculum directory.

### Procedure C: Intake Wizard

The agent SHALL collect four fields from the user:
- Topic (free text)
- Current level (`beginner`, `intermediate`, or `advanced`)
- Daily time budget in minutes
- Primary goal (free text)

The agent SHALL derive the slug by converting the topic to lowercase kebab-case.

INVARIANT: the agent SHALL NOT generate curriculum files until the user supplies all four fields.

## Curriculum Generation

### Procedure D: Generate Curriculum and Progress Files

1. The agent SHALL create `docs/learn/<slug>/`.
2. The agent SHALL copy `.agents/skills/learn/assets/lesson.css` to `docs/learn/<slug>/lesson.css`.
3. The agent SHALL generate `docs/learn/<slug>/curriculum.md` containing 30 daily lesson specifications.
4. The agent SHALL designate Days 7, 14, 21, 28, 29, and 30 as Milestone Consolidation Days.
5. The agent SHALL generate `docs/learn/<slug>/progress.md` with this YAML frontmatter:

```yaml
---
curriculum: <slug>
status: active
current_day: 1
started_at: <ISO 8601 timestamp>
completed_days: []
---
```

6. The agent SHALL write a markdown journal section below the frontmatter.

INVARIANT: the agent SHALL NOT mark two curricula as active simultaneously.

## Lesson Delivery

### Procedure E: Deliver a Lesson

1. The agent SHALL read `progress.md` to determine `current_day`.
2. The agent SHALL inspect the `completed_at` timestamp of the last entry in `completed_days`.
3. IF the last completion occurred over 24 hours ago, THEN the agent SHALL execute Procedure F first.
4. IF `docs/learn/<slug>/lesson.css` is missing, THEN the agent SHALL copy `.agents/skills/learn/assets/lesson.css` to that path.
5. IF `current_day` matches 7, 14, 21, 28, 29, or 30, THEN the agent SHALL generate `day-NN.html` using `.agents/skills/learn/assets/milestone-lesson.md`.
6. IF `current_day` does not match a milestone day, THEN the agent SHALL generate `day-NN.html` using `.agents/skills/learn/assets/lesson.md`.
7. The agent SHALL create `docs/learn/<slug>/day-NN-notes.md` using `.agents/skills/learn/assets/notes.md`.
8. The agent SHALL execute Procedure M on `day-NN.html`.

INVARIANT: the agent SHALL NOT pre-generate lessons before the user requests them.
INVARIANT: the agent SHALL NOT overwrite an existing `day-NN-notes.md` file.
INVARIANT: the agent SHALL NOT introduce new theoretical concepts on milestone consolidation days.

### Procedure F: Gap Handling

1. The agent SHALL compute and display the elapsed day count since the last completed lesson.
2. The agent SHALL extract and display a brief recap of Day N from `curriculum.md`.
3. The agent SHALL proceed directly to lesson delivery.

INVARIANT: the agent SHALL NOT block lesson access due to time gaps.

## Completion Signal Handling

### Procedure G: Process Completion Signal

Triggers: the user submits "done", "mark day complete", or equivalent wording.

1. WHEN the user submits work artifacts or reflection summaries, THEN the agent SHALL provide coaching feedback covering Core Strengths, Pitfalls, and Next Steps.
2. The agent SHALL read `docs/learn/<slug>/day-NN-notes.md` and inspect content under `## Questions I Still Have`.
3. IF `## Questions I Still Have` contains unresolved questions, THEN the agent SHALL execute Procedure H.
4. IF `## Questions I Still Have` is empty, THEN the agent SHALL execute Procedure I.

INVARIANT: the agent SHALL NOT advance `current_day` without an explicit completion signal from the user.
INVARIANT: the agent SHALL NOT block day advancement when a learner submits no review artifacts.

### Procedure H: Sub-Lesson Generation and Chaining

1. The agent SHALL count existing files matching `day-NN-V1.*.html` in the curriculum directory.
2. IF the count is less than 3, THEN the agent SHALL:
   a. Set M = count + 1.
   b. Generate `docs/learn/<slug>/day-NN-V1.M.html` addressing unresolved questions.
   c. Execute Procedure M on `day-NN-V1.M.html`.
   d. Direct the user to clear `## Questions I Still Have` after review.
3. IF the count equals 3, THEN the agent SHALL direct the user to external resources and execute Procedure I.

INVARIANT: the agent SHALL NOT generate `day-NN-V1.4.html` or higher versions.

### Procedure I: Advance Day

1. The agent SHALL append a completion record to `completed_days` in `progress.md`:
   ```yaml
   - day: <N>
     completed_at: <ISO 8601 timestamp>
   ```
2. The agent SHALL increment `current_day` by 1.
3. IF `current_day` reaches 31, THEN the agent SHALL set `status: completed` and execute Procedure J.

## Day 30 Completion Ceremony

### Procedure J: Generate Summary Artifact

The agent SHALL generate `docs/learn/<slug>/summary.md` using `.agents/skills/learn/assets/summary.md`.
The summary SHALL contain:
1. A 30-row table mapping Day to Objective and Key Takeaway.
2. A synthesis narrative summarizing the full learning trajectory.
3. A forward-looking section providing 3 to 5 adjacent topic recommendations.

The agent SHALL execute Procedure M on `summary.md`.

## Resume and Regeneration Flows

### Procedure K: Resume a Paused Curriculum

1. The agent SHALL scan `docs/learn/` for `progress.md` files with `status: paused`.
2. The agent SHALL match the user topic to a paused curriculum slug.
3. IF a match exists, THEN the agent SHALL write `status: active` to that `progress.md`.
4. IF no match exists, THEN the agent SHALL list paused curricula and prompt the user to choose one.

INVARIANT: the agent SHALL NOT run the intake wizard for a resume request.

### Procedure L: Regenerate a Lesson

1. The agent SHALL count existing backup files matching `day-NN-v*.html`.
2. IF the count equals 3, THEN the agent SHALL inform the user that the regeneration limit applies.
3. IF the count is less than 3, THEN the agent SHALL:
   a. Prompt the user to select an issue: `below my level | above my level | too long | wrong focus | other`.
   b. Rename `day-NN.html` to `day-NN-v<K>.html` using the next sequential index.
   c. Generate a new `day-NN.html` tailored to the stated issue.
   d. Execute Procedure M on the regenerated `day-NN.html`.

INVARIANT: the agent SHALL NOT delete existing backup lesson files.

## Lesson Specifications and Invariants

### Standard Active Learning Lesson Flow
The agent SHALL structure standard daily lessons with nine sequential sections:
1. Header and Metadata Grid
2. Spaced Retrieval Warm-Up (omitted on Day 1; queries Day N-1 and Day N-3 or N-7)
3. Core Mental Model
4. Predict and Inquire Active Hypothesis Check
5. Deep Dive and Applied Case Studies
6. Common Misconceptions and Traps
7. Comprehension Self-Check with Collapsible Answers
8. Three-Tiered Practical Tasks
9. Curated Further Exploration

### Milestone Consolidation Lesson Flow
The agent SHALL structure milestone lessons with four sequential sections:
1. Milestone Banner and Metadata Grid
2. Diagnostic Self-Audit across preceding days
3. Integrated Capstone Synthesis Project
4. Self-Assessment Rubric and Gap Log

### Three-Tiered Practical Tasks
1. Tier 1 (Analyze and Critique): 5 to 10 minutes. Requires spotting flaws, analyzing partial models, or debugging.
2. Tier 2 (Core Application): 15 to 30 minutes. Requires building, solving, or creating an independent artifact.
3. Tier 3 (Stretch Transfer): 30 to 60 minutes. Requires extending the core skill to an edge case or novel domain.

INVARIANT: each practical task SHALL define concrete done-when checklist criteria.
INVARIANT: the agent SHALL NOT exceed three practical tasks per daily lesson.

### Topic-Adaptive Media Rules
IF the topic requires software code, commands, or formal syntax, THEN the agent SHALL render syntax inside `<pre><code>`.
IF the topic does not require programming code, THEN the agent SHALL use structured tables, comparisons, or case excerpts.

INVARIANT: the agent SHALL NOT assume software engineering terminology when the topic is non-technical.
INVARIANT: the agent SHALL NOT embed live external URLs inside generated lessons.

## Readability Pass

### Procedure M: Apply Write Skill

The agent SHALL apply the `write` skill to all generated lesson and summary files:
1. The agent SHALL extract plain prose by stripping HTML tags.
2. The agent SHALL validate readability:
   ```bash
   python3 .agents/skills/write/scripts/validator.py <prose_file> --json
   ```
3. The agent SHALL iterate until Flesch Reading Ease reaches 65 or higher and zero violations remain.
4. The agent SHALL re-embed validated prose into the HTML file.

INVARIANT: the agent SHALL NOT alter code, formulas, or commands during readability revisions.
INVARIANT: the agent SHALL NOT apply Procedure M to `day-NN-notes.md` or `progress.md`.

## Global Invariants

- The agent SHALL NOT generate curriculum content before completing the intake wizard.
- The agent SHALL NOT advance `current_day` beyond 30.
- The agent SHALL NOT compute or display streak counts.
- The agent SHALL NOT implement export commands.
- The agent SHALL keep notes files in markdown format.
