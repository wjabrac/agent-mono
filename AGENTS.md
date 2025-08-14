# AGENTS instructions

These guidelines apply to the entire repository.

## Development workflow

- Prefer `rg` for searching within the repo; avoid `ls -R` or `grep -R`.
- Install the project in editable mode without dependency resolution:
  
  ```bash
  pip install --no-deps -e .
  ```
- Ensure the CLI loads:
  
  ```bash
  agent --help
  ```
- For any modified Python files, verify they compile:
  
  ```bash
  python -m py_compile <paths>
  ```

## Documentation

- Update `README.md` and `docs/quickstart.md` whenever user-facing commands change.
- Reference this `AGENTS.md` for contributor guidelines.

## Commit style

- Use imperative mood in commit messages.
- Leave the worktree clean before finalizing (`git status` should show no changes).
