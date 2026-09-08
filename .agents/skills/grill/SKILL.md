---
# Derived work from Matt Pocock's grilling skill.
name: grill
description: Stress-test plans, architectures, and trade-offs via a structured design tree interview. Activate on 'grill me', 'stress-test my idea', '/grill', '/grill-me'.
---

## Process

### Step 1: Map the Design Tree
Identify core decisions, prerequisite dependencies, and downstream branches.

### Step 2: Work in Rounds
- The **frontier** comprises all decisions with resolved prerequisites.
- Query the entire frontier in one round; number each question sequentially.
- Supply a recommended answer and rationale for each question.
- Wait for the user's response, then recompute the frontier.
- Defer questions that depend on open questions in the current round.

## Round Format

```markdown
**Q1**: **<question title>**: <question body, explaining context and listing multiple choices/trade-offs>

Recommendation: <your recommended answer with brief rationale>

**Q2**: **<question title>**: <question body, explaining context and listing multiple choices/trade-offs>

Recommendation: <your recommended answer with brief rationale>
```

## Rules

1. **Find Facts First**: Discover factual prerequisites autonomously via tool calls or a research subagent. Do NOT query the user for discoverable information.
2. **Non-Blocking Frontier**: Query all independent frontier questions immediately. Defer only downstream questions dependent on unsettled facts.
3. **User Decision Authority**: Present trade-offs clearly; wait for explicit user selections before settling decisions.

## Completion & Artifact Generation

WHEN the frontier is empty, the session terminates. Visit every branch; leave no assumptions unvalidated.

INVARIANT: do NOT execute implementation actions until the user explicitly confirms the settled design tree.

### Step 1: Generate Decision Tree Artifact
Use the `ace-write` skill. Write to:
`docs/.prompts-and-prayers/grilling/{SLUG}_{DATE:YYYY-MM-DD}.md`

### Step 2: Artifact Structure
- **Summary & Context**: Problem statement and objectives.
- **Resolved Decision Tree**: Questions, options, decisions, and rationales.
- **Open / Deferred Items**: Edge cases deferred to future phases.

### Step 3: Present the artifact link to the user.
