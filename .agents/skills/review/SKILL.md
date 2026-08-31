---
name: review
description: >-
  The agent SHALL perform structured, concern-driven code reviews on diffs,
  files, or pull requests. The agent SHALL activate on '/review', 'review this',
  'review my changes', or 'do a code review'. The agent SHALL NOT auto-trigger
  on context detection.
---

# Review Skill

The agent SHALL perform structured code reviews by loading concern reference files,
evaluating the diff against each concern, and producing a two-section output report.
The agent SHALL invoke the `write` skill to write the report to a markdown file.

## 1. Severity Level Definitions

The agent SHALL tag every finding with exactly one severity level.

| Severity | Label | Meaning |
|---|---|---|
| BLOCKER | `[BLOCKER]` | The finding MUST be resolved before merge. |
| SUGGESTION | `[SUGGESTION]` | The finding SHOULD be addressed but does not block merge. |
| NIT | `[NIT]` | The finding is optional polish; the author MAY ignore it. |

INVARIANT: The agent SHALL NOT approve a diff that contains unresolved BLOCKER findings.

## 2. Concern Routing Table

The agent SHALL load ALL concern reference files for every review.
The agent SHALL read each file at the path listed below before evaluating the diff.

| Concern | Reference File |
|---|---|
| Design | `references/concerns/design.md` |
| Functionality | `references/concerns/functionality.md` |
| Complexity | `references/concerns/complexity.md` |
| Tests | `references/concerns/tests.md` |
| Naming | `references/concerns/naming.md` |
| Comments | `references/concerns/comments.md` |
| Style | `references/concerns/style.md` |
| Documentation | `references/concerns/documentation.md` |

## 3. Review Execution Procedure

GIVEN the user provides a diff, file, or pull request for review.
WHEN the agent activates this skill.
THEN the agent SHALL execute the following steps in order.

### Step 1: Inspect the Diff
The agent SHALL read the full diff or file contents provided by the user.
The agent SHALL identify which files and logical units the diff modifies.
IF the diff is absent, THEN the agent SHALL request the diff from the user before proceeding.

### Step 2: Load All Concern Reference Files
The agent SHALL read all 8 concern reference files listed in Section 2.
The agent SHALL NOT skip any concern file regardless of diff size or apparent scope.

### Step 3: Evaluate Each Concern
The agent SHALL evaluate the diff against each concern in this order:
1. Design
2. Functionality
3. Complexity
4. Tests
5. Naming
6. Comments
7. Style
8. Documentation

The agent SHALL apply the rules defined in each concern's reference file.
The agent SHALL assign a severity label (BLOCKER, SUGGESTION, or NIT) to each finding.
IF the agent finds no issues for a concern, THEN the agent SHALL record that concern as "No issues found."

### Step 4: Determine Overall Verdict
IF any BLOCKER findings exist, THEN the verdict SHALL be `NEEDS CHANGES`.
IF no BLOCKER findings exist and SUGGESTION or NIT findings exist, THEN the verdict SHALL be `APPROVED WITH SUGGESTIONS`.
IF no findings exist across all concerns, THEN the verdict SHALL be `APPROVED`.

### Step 5: Produce the Review Report
The agent SHALL invoke the `write` skill to produce the output.
The agent SHALL write the report to: `docs/reviews/{YYYY-MM-DD}_{slug}.md`
The agent SHALL replace `{YYYY-MM-DD}` with the current ISO date.
The agent SHALL replace `{slug}` with a concise kebab-case descriptor of the diff.

## 4. Output Format Specification

The review report SHALL contain exactly two sections.

### Section 1: Summary
The agent SHALL write a summary containing:
- Overall verdict: `APPROVED`, `APPROVED WITH SUGGESTIONS`, or `NEEDS CHANGES`.
- Total finding counts by severity: e.g. "2 BLOCKERs, 3 SUGGESTIONs, 1 NIT".
- All BLOCKER findings listed with their concern label and a brief description.

### Section 2: Concern-Grouped Findings
The agent SHALL group all SUGGESTION and NIT findings under their respective concern headings.
The agent SHALL list each finding as a bullet with its severity label prefix.
The agent SHALL include the file name and line reference when available.
IF a concern has no SUGGESTION or NIT findings, THEN the agent SHALL omit that concern heading.

## 5. Review Standard

The agent SHALL apply the following overarching standard when evaluating all concerns.

The agent SHALL approve a diff once it demonstrably improves the overall code health of the system.
The agent SHALL NOT require perfection; the agent SHALL require continuous improvement.
The agent SHALL NOT block a diff based solely on personal style preferences.
IF the diff degrades overall code health, THEN the agent SHALL NOT approve it.
Technical facts and measurable data SHALL override personal opinions in all findings.

## 6. Positive Feedback

The agent SHALL acknowledge correct and well-executed practices observed in the diff.
The agent SHALL include positive observations in the Summary section under a "Strengths" subsection.
INVARIANT: The agent SHALL NOT fabricate praise; the agent SHALL only note real strengths.
