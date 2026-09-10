---
name: interview
description: >-
  Stress-tests plans and decisions through design tree interviews. Activate on '/interview'.
---

The agent SHALL interview the user across a structured design tree to stress-test plans, architectures, and decisions.

## Rules
- The agent SHALL NOT query the user for information discoverable via codebase inspection or tool calls.
- The agent SHALL NOT execute implementation actions until the user confirms the settled design tree.
- The agent SHALL NOT generate an artifact unless the user explicitly requests one.
- IF generating an artifact, THEN the agent SHALL apply the `prose` skill in ACE mode.

## Workflow
1. Discover factual prerequisites autonomously and map the initial design tree.
2. Execute Procedure A in iterative rounds until the decision frontier is empty.
3. Confirm the settled design tree with the user.
4. IF the user requests an artifact, THEN execute Procedure B.

## Procedures

### Procedure A: Round Execution
1. Query the entire active frontier in one round; number each question sequentially.
2. Format each question:
   ```markdown
   **Q<N>**: **<question title>**: <question body explaining context and trade-offs>

   Recommendation: <recommended answer with rationale>
   ```
3. Await user response before opening a subsequent round.
4. Recompute the active frontier and defer questions dependent on unresolved decisions.

### Procedure B: Artifact Generation (Optional)
1. Write the decision tree to `docs/.prompts-and-prayers/interviews/{SLUG}_{DATE:YYYY-MM-DD}.md`.
2. Include sections: `# Interview: <Title>`, `## Summary & Context`, `## Resolved Decision Tree`, and `## Open / Deferred Items`.
3. Validate the artifact:
   ```bash
   python3 .agents/skills/prose/scripts/validator.py docs/.prompts-and-prayers/interviews/{SLUG}_{DATE:YYYY-MM-DD}.md --mode ace --json
   ```
4. Present the artifact link to the user.

## Verification Checklist
- [ ] Discover all codebase prerequisites autonomously before querying the user.
- [ ] Query every frontier question with context, trade-offs, and a recommended answer.
- [ ] Verify that all frontier branches are empty before ending the interview.
- [ ] Obtain explicit user confirmation on the settled design tree.
- [ ] IF the user requested an artifact, THEN verify that the artifact at `docs/.prompts-and-prayers/interviews/{SLUG}_{DATE:YYYY-MM-DD}.md` passes ACE validation.
