---
# Derived from the grilling skill in mattpocock/skills (https://github.com/mattpocock/skills)
name: interview
description: Stress-tests plans and decisions through design tree interviews. Activate on '/interview'.
---

The agent SHALL interview the user across a design tree.

## Rules
- The agent SHALL NOT query the user for information discoverable via environment inspection or tool calls.
- IF a question depends on open decisions, THEN the agent SHALL defer that question to a subsequent round.
- The session is complete only WHEN the decision frontier is empty, no branches remain unvisited, with nothing left silently assumed.

## Workflow
1. Map the initial design tree and identify open decisions.
2. IF any frontier decision requires facts from the environment, THEN execute Procedure A.
3. Execute Procedure B to query the frontier in iterative rounds until the frontier is empty.
4. Confirm the settled design tree and shared understanding with the user.
5. IF the user requests an artifact, THEN execute Procedure C.

## Procedures

### Procedure A: Non-Blocking Fact Discovery
1. Dispatch a research subagent to discover required facts.
2. Mark questions downstream of running explorations as waiting on unresolved facts.
3. Advance all remaining unblocked frontier questions immediately without waiting for the subagent.
4. Upon subagent completion, incorporate discovered facts to satisfy prerequisites.

### Procedure B: Iterative Round Execution Loop
1. Identify all decisions with satisfied prerequisites to form the active frontier.
2. Number each frontier question sequentially and provide a recommended answer with rationale.
3. Format each question:
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
4. Present the entire active frontier in one round and await user response.
5. Reshape the design tree using user answers and push the frontier outward.
6. Recompute the active frontier to unblock dependent questions.
7. Repeat steps 1 through 6 until the decision frontier is empty.

### Procedure C: Artifact Generation (Optional)
1. Write the settled design tree to `docs/.prompts-and-prayers/interviews/{SLUG}_{DATE:YYYY-MM-DD}.md`.
2. Include sections: `# Interview: <Title>`, `## Summary & Context`, `## Resolved Decision Tree`, and `## Open / Deferred Items`.
3. Validate the artifact:
   ```bash
   python3 .agents/skills/prose/scripts/validator.py docs/.prompts-and-prayers/interviews/{SLUG}_{DATE:YYYY-MM-DD}.md --mode ace --json
   ```
4. Present the artifact link to the user.

## Verification Checklist
- [ ] Verify that the agent looked up discoverable environment facts autonomously.
- [ ] Verify that running fact explorations did not block independent frontier questions.
- [ ] Verify that each round queried the entire active frontier with numbered questions and recommendations.
- [ ] Verify that no questions depended on open decisions from the same round.
- [ ] Verify that the agent recomputed the frontier iteratively until empty.
- [ ] Obtain explicit user confirmation of shared understanding before any implementation.
- [ ] IF the user requested an artifact, THEN verify that the interview artifact exists and passes ACE validation.
