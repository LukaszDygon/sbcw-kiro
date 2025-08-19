Frontend BugBot Review Rules

- Scope: TypeScript React app (`/frontend`) using Vite, TailwindCSS, RTL/Jest, Playwright.
- Architecture: components → hooks → contexts → services → utils; keep views dumb, logic in hooks/services.

Security & Privacy
- Never store secrets or tokens in localStorage; prefer httpOnly cookies + server validation.
- Sanitize and escape any user-provided content; prevent XSS and injection.
- Enforce role-based UI hiding and guard routes with `AuthGuard`; never rely on UI-only checks for authorization.
- Avoid leaking PII in logs or error messages. Do not expose stack traces in production.

UX & Accessibility
- Follow `ACCESSIBILITY.md`; ensure keyboard navigation, focus management, aria attributes.
- Ensure color contrast, proper labels, and semantic HTML. Avoid tabindex > 0.
- All interactive elements must be reachable and operable via keyboard.

Performance
- Code-split large routes; lazy-load rarely used views.
- Memoize expensive computations; avoid unnecessary re-renders (`React.memo`, `useMemo`, `useCallback`).
- Keep bundle size in check; tree-shake and avoid heavy dependencies.

State & Data Flow
- Use contexts for cross-cutting concerns (auth, accessibility, notifications); keep local state local.
- Co-locate data-fetching in services; components call services and handle UI states (loading/error/empty).
- Handle loading, error, empty states explicitly; never leave UI in limbo.

API Contracts
- Use typed service clients in `src/services`; define request/response types in `src/types`.
- Validate inputs before calling backend APIs; enforce length/range constraints consistent with backend.
- Handle HTTP errors with user-friendly messages; no raw error objects to the UI.

Testing
- Unit: components with RTL; hooks in isolation. Integration: flows with MSW. E2E: Playwright for core journeys.
- Accessibility tests in Jest where practical. Deterministic tests; avoid real network.
- Keep tests colocated under `__tests__` and integration under `tests/integration`.

Clean code rules
- Naming: descriptive, no cryptic abbreviations. Components PascalCase; hooks use `useX`.
- Size: small, focused components (~≤200 lines). Extract subcomponents and hooks.
- Structure: early returns; avoid deep nesting; split logic from presentation.
- Comments: avoid gratuitous comments. Document non-trivial hooks/components with concise docblocks.
- Style: consistent formatting; no drive-by reformatting; keep lines readable; avoid long JSX expressions.
- Error boundaries for top-level routes to contain failures.

PR checklists
- Security: no secrets in code; inputs sanitized; guarded routes; PII not leaked.
- Accessibility: keyboard, aria, contrast, labels verified.
- Performance: code-splitting/memoization appropriate; bundle size considered.
- Testing: units for new logic; integration for flows; E2E for critical paths.
