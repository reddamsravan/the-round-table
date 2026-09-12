# Design Concern

Check the overall system design first. Ensure changes fit the architecture and improve code health.

## Rules

### Primary Check
- Check design before inspecting small code details.
- Mark core design flaws as `[BLOCKER]`. Report them right away.

### System Fit
- Verify the change belongs in this project.
- Mark code that rebuilds existing library tools as `[SUGGESTION]`.

### Integration
- Verify that components work cleanly together.
- Mark broken component links or mismatched architecture as `[BLOCKER]`.

### Code Health
- Verify that the change improves overall code health.
- Mark changes that degrade code health as `[BLOCKER]`.
- Accept changes that improve code health even if not perfect.
- Do not demand perfect design; demand steady improvement.

### Context and Scope
- Read full files to understand context beyond the diff.
- Mark small edits in methods longer than thirty lines as `[SUGGESTION]` to split the method.

## Review Standards
- Rely on facts and data over personal opinion.
- Accept the author choice when two paths show equal merit.
