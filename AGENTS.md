# Development guide for TokenTally

This repository contains a Python backend and a small Next.js frontend. Tests live in `receipt_processor/tests`. Follow the guidelines below for any contribution.

## General expectations
- Maintain a clean and easy-to-read code base. Prefer clarity over cleverness.
- Split work into small commits so changes are easy to review.
- Keep cross-platform compatibility in mind (Linux/macOS).
- Avoid introducing network calls in tests or build steps unless already mocked.
- Python code should target **Python 3.11**.

## Code style
- Format all Python with **Black** (`black .`).
- Type annotate new functions and use docstrings for public APIs.
- Follow `snake_case` for variables/functions and `PascalCase` for classes.
- Use absolute imports within the project (`from token_tally.module import X`).
- Keep functions short and refactor duplicated logic into helpers.
- Prefer built-in dataclasses for simple data containers.

## Commit messages
- Begin with a short summary line (< 72 characters).
- Optionally add a body explaining *why* the change is needed.
- Group related changes into a single commit and do not rewrite history once pushed.

## Required checks
- Run `pytest -q` from the repository root. All tests must pass.
- If Node dependencies are installed, run `npm run build` in `frontend/` to ensure the UI builds (skip if offline).
- Format code before committing so CI does not fail.

## Testing guidelines
- Use `pytest` fixtures to set up data; avoid external network calls in tests.
- Keep test names descriptive. Every new feature should come with corresponding tests.
- Place reusable fixtures under `receipt_processor/tests/` if needed.

## Pull request process
- Open PRs against the default `work` branch.
- Include a brief **Summary** of changes and a **Testing** section describing commands executed.
- Mention any follow-up work or TODOs in a **Notes** section.
- Reviewers should verify that tests pass, code follows these guidelines, and documentation is updated.

## Documentation
- Update `README.md` and any relevant docs when behaviour changes or new features are added.
- Document new configuration options or environment variables.
- Keep code comments and docstrings up to date with implementation behaviour.

Adhering to these rules keeps the project maintainable and reviewable for everyone.
