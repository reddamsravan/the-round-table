---
name: learn
description: >-
  Generates and delivers a personalized 30-day curriculum on any topic using active learning pedagogy. Activate on '/learn'.
disable-model-invocation: true
---

The agent SHALL generate and deliver a personalized 30-day curriculum using active learning pedagogy.

## Rules
- The agent SHALL NOT delete or overwrite an existing curriculum directory.
- The agent SHALL NOT mark two curricula as active simultaneously.
- The agent SHALL NOT pre-generate lessons before the user requests them.
- The agent SHALL NOT overwrite an existing notes file.
- The agent SHALL NOT introduce new theoretical concepts on milestone consolidation days.
- The agent SHALL NOT block lesson access due to elapsed time between completions.
- The agent SHALL NOT block day advancement when a learner submits no review artifacts.
- The agent SHALL NOT advance `current_day` without an explicit completion signal from the user.
- The agent SHALL NOT advance `current_day` beyond 30.
- The agent SHALL NOT assume software engineering terminology when the topic is non-technical.
- The agent SHALL NOT embed live external URLs inside generated lessons.
- The agent SHALL NOT compute or display streak counts.
- The agent SHALL NOT implement export commands.

## Workflow
1. Inspect `docs/learn/` for an active `progress.md` file.
2. IF an active curriculum exists or the user requests resuming a curriculum, THEN execute Procedure A.
3. IF no active curriculum exists, THEN execute Procedure B.
4. Execute Procedure C to deliver the lesson for `current_day`.
5. Await user input.
6. IF the user requests lesson regeneration, THEN execute Procedure D.
7. IF the user signals day completion, THEN execute Procedure E.
8. IF `current_day` reaches 31, THEN execute Procedure F.

## Procedures

### Procedure A: Curriculum Resolution and Switching
1. IF the user requests resuming a paused curriculum, THEN scan `docs/learn/` for `progress.md` files with `status: paused`.
2. Display matching paused curricula and prompt the user to select one.
3. Write `status: active` to `progress.md` for the selected curriculum.
4. IF an active curriculum already exists, THEN display the curriculum name and `current_day`.
5. IF the user requests a new topic, THEN prompt the user to choose: `continue current curriculum` or `switch to new topic`.
6. IF the user chooses switch, THEN write `status: paused` to `progress.md` and proceed to Procedure B.
7. IF the user declines both choices, THEN abort the process.

### Procedure B: Intake and Curriculum Setup
1. Collect four fields from the user: topic, level (`beginner`, `intermediate`, or `advanced`), daily time budget in minutes, and primary goal.
2. Convert the topic to lowercase kebab-case to derive the slug.
3. Create directory `docs/learn/<slug>/`.
4. Copy `.agents/skills/learn/assets/lesson.css` to `docs/learn/<slug>/lesson.css`.
5. Generate `docs/learn/<slug>/curriculum.md` containing 30 daily lesson specifications.
6. Designate Days 7, 14, 21, 28, 29, and 30 as milestone consolidation days in `curriculum.md`.
7. Generate `docs/learn/<slug>/progress.md` with this frontmatter:
```yaml
---
curriculum: <slug>
status: active
current_day: 1
started_at: <ISO 8601 timestamp>
completed_days: []
---
```
8. Append a markdown journal section below the frontmatter in `progress.md`.

### Procedure C: Daily Lesson Delivery
1. Read `progress.md` to identify `current_day`.
2. Inspect the last timestamp in `completed_days`.
3. IF the last completion occurred over 24 hours ago, THEN display elapsed days and a brief recap from `curriculum.md`.
4. IF `docs/learn/<slug>/lesson.css` does not exist, THEN copy `.agents/skills/learn/assets/lesson.css` to that path.
5. IF `current_day` matches 7, 14, 21, 28, 29, or 30, THEN generate `day-NN.html` using `.agents/skills/learn/assets/templates/milestone-lesson-template.html`.
6. IF `current_day` does not match a milestone day, THEN generate `day-NN.html` using `.agents/skills/learn/assets/templates/lesson-template.html`.
7. Apply Procedure G to format lesson structure and content.
8. Create `docs/learn/<slug>/day-NN-notes.md` using `.agents/skills/learn/assets/templates/notes-template.md`.
9. Execute Procedure H on `day-NN.html`.
10. Present the lesson link to the user.

### Procedure D: Lesson Regeneration
1. Count existing backup files matching `day-NN-v*.html`.
2. IF the count equals 3, THEN notify the user that the regeneration limit applies.
3. IF the count is less than 3, THEN prompt the user to select an issue: `below my level`, `above my level`, `too long`, `wrong focus`, or `other`.
4. Rename `day-NN.html` to `day-NN-v<K>.html` using the next sequential index.
5. Generate a new `day-NN.html` addressing the feedback.
6. Execute Procedure H on `day-NN.html`.

### Procedure E: Completion and Day Advancement
1. WHEN the user submits work artifacts or reflections, provide coaching feedback covering Core Strengths, Pitfalls, and Next Steps.
2. Inspect `docs/learn/<slug>/day-NN-notes.md` under `## Questions I Still Have`.
3. IF unresolved questions exist and fewer than three sub-lesson files exist, THEN generate `day-NN-V1.M.html` addressing those questions.
4. Execute Procedure H on `day-NN-V1.M.html` and prompt the user to clear questions after review.
5. IF three sub-lesson files already exist, THEN direct the user to external resources.
6. Append a completion record to `completed_days` in `progress.md`:
```yaml
- day: <N>
  completed_at: <ISO 8601 timestamp>
```
7. Increment `current_day` by 1 in `progress.md`.

### Procedure F: Curriculum Completion Ceremony
1. Set `status: completed` in `progress.md`.
2. Generate `docs/learn/<slug>/summary.md` using `.agents/skills/learn/assets/templates/summary-template.md`.
3. Include a 30-row table mapping Day to Objective and Key Takeaway.
4. Include a synthesis narrative of the 30-day learning trajectory.
5. Include three to five recommended next topics.
6. Execute Procedure H on `summary.md`.
7. Present the summary link to the user.

### Procedure G: Lesson Specifications and Formatting
1. Structure standard daily lessons with nine sequential sections:
   a. Header and Metadata Grid
   b. Spaced Retrieval Warm-Up (omit on Day 1; query Day N-1 and Day N-3 or N-7)
   c. Core Mental Model
   d. Predict and Inquire Active Hypothesis Check
   e. Deep Dive and Applied Case Studies
   f. Common Misconceptions and Traps
   g. Comprehension Self-Check with Collapsible Answers
   h. Three-Tiered Practical Tasks
   i. Curated Further Exploration
2. Structure milestone lessons with four sequential sections:
   a. Milestone Banner and Metadata Grid
   b. Diagnostic Self-Audit across preceding days
   c. Integrated Capstone Synthesis Project
   d. Self-Assessment Rubric and Gap Log
3. Structure practical tasks into three tiers:
   a. Tier 1 (Analyze and Critique): 5 to 10 minutes.
   b. Tier 2 (Core Application): 15 to 30 minutes.
   c. Tier 3 (Stretch Transfer): 30 to 60 minutes.
4. Define concrete done-when checklist criteria for each practical task.
5. Enforce a maximum of three practical tasks per daily lesson.
6. IF the topic requires code or formal syntax, THEN render syntax inside `<pre><code>`.
7. IF the topic does not require programming code, THEN use structured tables, comparisons, or case excerpts.

### Procedure H: Readability Validation
1. Extract plain prose from the generated HTML or summary markdown file.
2. Validate readability:
```bash
python3 .agents/skills/prose/scripts/validator.py <prose_file> --json
```
3. Revise text until Flesch Reading Ease reaches 65 or higher and zero errors remain.
4. Re-embed validated prose into the generated document without modifying code, formulas, or commands.
5. Do not apply prose validation to notes files or progress files.

## Verification Checklist
- [ ] Verify that `docs/learn/<slug>/curriculum.md` contains 30 daily lesson specifications.
- [ ] Verify that `docs/learn/<slug>/curriculum.md` designates Days 7, 14, 21, 28, 29, and 30 as milestone consolidation days.
- [ ] Verify that `docs/learn/<slug>/progress.md` contains valid YAML frontmatter with `curriculum`, `status`, `current_day`, and `completed_days`.
- [ ] Verify that `docs/learn/<slug>/lesson.css` exists in the curriculum directory.
- [ ] Verify that generated `day-NN.html` passes prose readability validation with Flesch Reading Ease >= 65.
- [ ] Verify that `docs/learn/<slug>/day-NN-notes.md` exists.
- [ ] Verify that the agent advances `current_day` only after receiving an explicit user completion signal.
- [ ] IF `current_day` reaches 31, THEN verify that `docs/learn/<slug>/summary.md` exists.
