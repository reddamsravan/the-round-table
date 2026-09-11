# Conventional Commits Reference Guide

This reference defines specifications for Conventional Commits 1.0.0 messages.

## Message Syntax

The commit header MUST follow this structure:
`<type>(<scope>): <subject>` or `<type>: <subject>`

IF breaking changes exist, THEN the header MUST prepend `!` before the colon:
`<type>(<scope>)!: <subject>` or `<type>!: <subject>`

## Allowed Types

- `feat`: Adds a new feature to the codebase.
- `fix`: Patches a bug or defect in the codebase.
- `docs`: Updates documentation only.
- `style`: Changes code formatting without altering meaning.
- `refactor`: Alters code structure without adding features or fixing bugs.
- `perf`: Improves system performance or resource consumption.
- `test`: Adds missing tests or modifies existing tests.
- `build`: Changes build tooling or external dependencies.
- `ci`: Changes continuous integration scripts or workflows.
- `chore`: Maintains auxiliary tasks and repository maintenance.
- `revert`: Reverts a previous commit.

## Scope Invariants

- The scope MUST be optional.
- WHEN present, the scope MUST consist of a single lowercase noun.
- The scope MUST describe a general area of the codebase.
- Examples of valid scopes include `auth`, `parser`, `api`, `cli`, `config`, and `rules`.
- The scope MUST NOT contain file paths, slashes, backslashes, or directory names.
- The scope MUST NOT contain file names or file extensions like `.py`, `.ts`, or `.md`.

## Subject Guidelines

- The subject description MUST use the imperative mood.
- The subject description MUST begin with a lowercase letter.
- The subject description MUST NOT end with a period.
- The subject description target length MUST be 50 characters or fewer.
- The subject description hard ceiling MUST be 72 characters.

## Body and Footer Guidelines

- The agent SHALL omit the commit body for self-explanatory changes.
- IF a body exists, THEN each line MUST NOT exceed 72 characters.
- IF a body exists, THEN the body MUST explain the rationale without reciting diff details.
- IF a breaking change footer exists, THEN the footer MUST start with `BREAKING CHANGE: ` followed by a description.
- Footers MUST format issue tracker references as `Fixes #<id>` or `Closes #<id>`.
