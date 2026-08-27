---
# Derived work from Matt Pocock's grilling skill.
name: grill
description: >-
  The agent SHALL interview the user across a structured design tree to stress-test plans, architectures, and design trade-offs.
  WHEN the user requests plan validation or invokes grill triggers ('grill me', 'stress-test my idea', '/grill', '/grill-me'), THEN the agent SHALL activate this skill.
---

# Grilling: Decision Tree Interview Skill

The agent SHALL interview the user relentlessly until reaching a shared understanding.
The agent SHALL model the exploration space as a **design tree**.
Every core decision branches into dependent downstream decisions.

## 1. The Process

### Step 1: Map the Design Tree
The agent SHALL identify core decisions, prerequisite dependencies, and downstream branches.

### Step 2: Work in Rounds
- The **frontier** comprises all decisions with resolved prerequisites.
- The agent SHALL query the entire frontier in a single round.
- The agent SHALL number each question sequentially.
- The agent SHALL supply a recommended answer and rationale for each question.
- The agent SHALL wait for the user response before opening a subsequent round.
- WHEN the user provides answers, THEN the agent SHALL recompute the active frontier.
- IF a question depends on an open question in the current round, THEN the agent SHALL defer that question to a future round.

## 2. Round Formatting

The agent SHALL format each question within a round using text-based markdown:

```markdown
**Q1**: **<question title>**: <question body, explaining context and listing multiple choices/trade-offs>

Recommendation: <your recommended answer with brief rationale>

**Q2**: **<question title>**: <question body, explaining context and listing multiple choices/trade-offs>

Recommendation: <your recommended answer with brief rationale>
```

## 3. Rules & Principles

### Rule 1: Find Facts First
The agent SHALL discover factual prerequisites autonomously.
WHEN a frontier question requires environment or codebase facts, THEN the agent SHALL inspect the repository or dispatch a research subagent.
The agent SHALL NOT query the user for information discoverable via tool calls.

### Rule 2: Non-Blocking Frontier Queries
A running fact-finding lookup constitutes an unsettled prerequisite.
The agent SHALL query all independent frontier questions immediately without waiting for concurrent fact-finding lookups.
The agent SHALL defer only downstream questions dependent on unsettled facts.

### Rule 3: User Decision Authority
The user retains ultimate authority over trade-offs and architectural preferences.
The agent SHALL present trade-offs clearly.
The agent SHALL wait for explicit user selections before settling decisions.

## 4. Completion & Artifact Generation

WHEN the frontier becomes empty, THEN the grilling session terminates.
The agent SHALL visit every branch of the design tree.
The agent SHALL NOT leave assumptions unvalidated.

GIVEN an empty decision frontier
WHEN the session reaches completion
THEN the agent SHALL execute artifact generation

### Step 1: Generate the Decision Tree Artifact
The agent SHALL use the `ace-write` skill to generate the markdown artifact.
The agent SHALL write the artifact to:
`docs/.prompts-and-prayers/grilling/{SLUG}_{DATE:YYYY-MM-DD}.md`
The agent SHALL replace `{SLUG}` with a concise kebab-case topic descriptor.
The agent SHALL replace `{DATE:YYYY-MM-DD}` with the current ISO date.
The agent SHALL ensure the target directory exists.

### Step 2: Artifact Structure Requirements
The generated artifact SHALL include the following sections:
- **Summary & Context**: High-level problem statement and target objectives.
- **Resolved Decision Tree**: Exhaustive breakdown of questions asked, considered options, chosen decisions, and rationales.
- **Open / Deferred Items**: Edge cases and requirements explicitly deferred to future phases.
- **Next Steps**: Actionable implementation plan derived from settled decisions.

### Step 3: Confirmation Before Implementation
The agent SHALL present the markdown link to the generated artifact.
INVARIANT the agent SHALL NOT execute implementation actions until the user explicitly confirms agreement with the settled design tree.
