Repo-wide BugBot Review Rules (Shared)

- Preserve indentation style (spaces vs tabs) and width; do not mix styles.
- Do not introduce unrelated formatting changes in edits. Keep diffs minimal and focused.
- Ensure build/test pipelines remain green after changes; update tests or docs when behavior changes.
- Add or update types and imports as needed; avoid `any` and unsafe casts in TypeScript; avoid untyped APIs in Python.
- No secrets, tokens, or credentials in code or logs; use environment variables and secure stores.
- Follow layered architecture: keep UI/API thin and business logic in services; reuse utilities across layers.
- Input validation everywhere: never trust client input; validate at boundaries.
- Consistent error handling and structured logging across backend and frontend.
- Performance-conscious: paginate, index, memoize, and split where appropriate.
- Documentation: update READMEs/specs when adding significant features or endpoints.
- Clean code ethos: descriptive naming, small functions/modules, modular structure, minimal comments (docstrings where useful), early returns, limited nesting, and explicit error handling.
