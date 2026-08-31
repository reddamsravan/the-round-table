---
name: review/concerns/design
description: >-
  ACE-spec rules for evaluating the Design concern during a code review.
  The agent SHALL read this file as part of Step 2 of the Review Execution Procedure.
---

# Design Concern Reference

## 1. Primary Standard

The agent SHALL prioritize design evaluation above all other concerns.
The agent SHALL evaluate overall design before examining line-level details.
IF the agent identifies a fundamental design flaw, THEN the agent SHALL flag it as BLOCKER.
IF a BLOCKER design flaw exists, THEN the agent SHALL skip detailed review of affected code and report the BLOCKER immediately.

## 2. Design Evaluation Rules

### Rule 1: System Fit
The agent SHALL verify that the change belongs in the target codebase.
The agent SHALL verify that the change does not duplicate functionality available in libraries.
IF the change introduces functionality better served by an existing library, THEN the agent SHALL flag it as SUGGESTION.

### Rule 2: Integration Coherence
The agent SHALL verify that all components in the diff interact coherently.
The agent SHALL verify that the change integrates well with the existing system architecture.
IF component interactions are incoherent or architecturally inconsistent, THEN the agent SHALL flag the finding as BLOCKER.

### Rule 3: Timing and Scope
The agent SHALL assess whether the current system roadmap justifies this change at this time.
IF the change introduces premature abstractions not yet required by the system, THEN the agent SHALL flag it as SUGGESTION.
IF the change adds functionality the system demonstrably does not need now, THEN the agent SHALL flag it as SUGGESTION and reference the over-engineering rule in complexity.md.

### Rule 4: Code Health Direction
The agent SHALL assess whether the change improves or degrades overall code health.
IF the change degrades overall code health, THEN the agent SHALL flag it as BLOCKER.
IF the change improves overall code health even if imperfect, THEN the agent SHALL recommend approval.
INVARIANT: The agent SHALL NOT require a perfect design; the agent SHALL require improvement.

### Rule 5: Review Scope Breadth
The agent SHALL examine the change in the context of the surrounding system.
The agent SHALL inspect the full file when the diff shows only partial context.
IF 4 or fewer changed lines reside inside a method exceeding 30 lines, THEN the agent SHALL flag the containing method for potential decomposition as SUGGESTION.

## 3. Design Principles

The agent SHALL apply these principles when evaluating trade-offs.

Technical facts and measurable data SHALL override personal opinions.
The agent SHALL NOT dismiss aspects of software design as mere style preferences.
IF the author demonstrates via data or solid engineering principles that multiple approaches are equally valid, THEN the agent SHALL accept the author's preference.
IF the author demonstrates no such equivalence, THEN the agent SHALL apply standard software design principles to determine the correct approach.
