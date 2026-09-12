# Complexity Concern

Check changed code for excess complexity. Code must be easy to read and safe to change.

## Rules

### Line Complexity
- Mark lines with more than two nested calls as `[SUGGESTION]`.
- Mark lines that require re-reading to parse as `[SUGGESTION]`.

### Function Complexity
- Mark functions that do more than one task as `[SUGGESTION]`. Ask to split them.
- Mark functions with more than three nesting levels as `[SUGGESTION]`.

### Class Complexity
- Mark classes that hold more than one main duty as `[SUGGESTION]`. Split by single duty.

### Over-Engineering
- Mark extra layers, interfaces, or hooks not needed today as `[SUGGESTION]`.
- Solve current problems now. Address future needs when they arrive.
- Mark unused code that harms system health as `[BLOCKER]`.
- Mark unused neutral code as `[SUGGESTION]`.

## Review Standards
- Prefer simple code over code that needs a comment to explain it.
- Ask authors to simplify hard code rather than explain it in chat.
