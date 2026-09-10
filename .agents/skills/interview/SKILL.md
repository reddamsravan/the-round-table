---
name: interview
description: Stress-tests plans and decisions through design tree interviews. Activate on '/interview'.
---

The agent SHALL interview the user across a structured design tree to stress-test plans, architectures, and decisions.

## Rules
- The agent SHALL NOT query the user for information discoverable via codebase inspection or tool calls.
- IF a question depends on open decisions, THEN the agent SHALL defer that question to a subsequent round.
- The agent SHALL NOT execute implementation actions until the user confirms the settled design tree.
- The agent SHALL NOT generate an artifact unless the user explicitly requests one.
- IF generating an artifact, THEN the agent SHALL apply the `prose` skill in ACE mode.

## Workflow
1. Execute Procedure A to discover factual prerequisites autonomously.
2. Map the initial design tree and identify independent frontier questions.
3. Execute Procedure B in iterative rounds until the decision frontier is empty.
4. Confirm the settled design tree with the user.
5. IF the user requests an artifact, THEN execute Procedure C.

## Procedures

### Procedure A: Autonomous Fact Discovery
1. Inspect the codebase, file system, and environment using tool calls.
2. IF investigations require deep research, THEN dispatch a research subagent.
3. Resolve all factual prerequisites before formulating interview questions.

### Procedure B: Round Execution
1. Query the entire active frontier in one round; number each question sequentially.
2. Provide up to four lettered choices for multiple-choice questions.
3. Designate open questions with an explicit `[Free-form text]` indicator.
4. Format each question:
   ```markdown
   **Q<N>**: **<question title>**: <question body explaining context and trade-offs>
   - Choices:
     - **A)** <choice 1>
     - **B)** <choice 2>
     - **C)** <choice 3>
     - **D)** <choice 4>
     - **[Free-form text]** (if open response required)
   - Recommendation: <recommended answer with rationale>
   ```
5. Await user response before opening a subsequent round.
6. Recompute the active frontier and advance unblocked questions.

### Procedure C: Artifact Generation (Optional)
1. Write the decision tree to `docs/.prompts-and-prayers/interviews/{SLUG}_{DATE:YYYY-MM-DD}.md`.
2. Include sections: `# Interview: <Title>`, `## Summary & Context`, `## Resolved Decision Tree`, and `## Open / Deferred Items`.
3. Validate the artifact:
   ```bash
   python3 .agents/skills/prose/scripts/validator.py docs/.prompts-and-prayers/interviews/{SLUG}_{DATE:YYYY-MM-DD}.md --mode ace --json
   ```
4. Present the artifact link to the user.

## Verification Checklist
- [ ] Execute autonomous discovery before querying the user.
- [ ] Verify that no questions within the active round depend on unresolved decisions.
- [ ] Query every frontier question with choices or a free-form indicator, trade-offs, and a recommended answer.
- [ ] Verify that all frontier branches are empty before ending the interview.
- [ ] Obtain explicit user confirmation on the settled design tree.
- [ ] IF the user requested an artifact, THEN verify that the artifact at `docs/.prompts-and-prayers/interviews/{SLUG}_{DATE:YYYY-MM-DD}.md` passes ACE validation.
