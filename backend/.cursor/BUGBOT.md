Backend BugBot Review Rules

- Scope: Python Flask + SQLAlchemy backend only (`/backend`).
- Architecture: API → middleware → services → models → utils. Keep controllers thin; put business logic in services.

Security
- Require auth on protected routes; enforce roles (EMPLOYEE, ADMIN, FINANCE). Validate resource ownership.
- Validate and sanitize all inputs (types, ranges, lengths). Reject SQLi/XSS; sanitize free text (note, category).
- CSRF protection for state-changing endpoints when cookies are used. Rate limit per-user/IP; expose limit headers.
- No secrets/PII in logs or responses. Mask sensitive data. Use short-lived JWTs; refresh rotation; session timeout.
- Audit sensitive actions (transactions, role/admin actions, system events) with timestamps and minimal context.

API behavior
- Strict request validation. On error return JSON: { "error": { "code": STRING, "message": STRING, "details": {} } }.
- Enforce pagination and limits; validate dates and ranges. Idempotency for financial actions; prevent replay/double spend.
- Structured logging; include correlation metadata if available.

Models and constraints (align with design)
- User: unique `microsoft_id`, role, account_status, timestamps.
- Account: `balance` Decimal(10,2), default currency 'GBP'; enforce min/max limits and overdraft rules.
- Transaction: sender, recipient, amount > 0, type {TRANSFER, EVENT_CONTRIBUTION}, optional category/note, status lifecycle.
- EventAccount: name, description, optional positive target_amount, future deadline, ACTIVE/CLOSED/CANCELLED.
- MoneyRequest: requester, recipient, amount > 0, note optional, PENDING→APPROVED/DECLINED/EXPIRED with responded_at.
- AuditLog: optional user_id, action_type, entity_type/id, old/new values JSON, ip_address, user_agent, created_at.

Services
- AccountService: balances, available balance, overdraft checks, history with filters, safe updates with audit logging.
- TransactionService: validate amounts/self-transfer/limits/user status; atomic balance updates; audit + notifications; bulk limits.
- EventService: create/validate, contributions only when ACTIVE, close with auth.
- MoneyRequestService: prevent self/dupes; proper state transitions; expire/cleanup; notify + audit.
- AuditService: centralized logging and retrieval with filtering/pagination; retention policies.

Retention & compliance
- Enforce retention for audit logs, expired requests, old notifications. Verify audit integrity in scheduled jobs.

Performance
- Use defined indexes; avoid N+1; paginate queries; bound limits. Keep transactions short; SQLite WAL assumed in dev/test.

Error handling & observability
- Never swallow exceptions; convert to typed errors and return consistent JSON. Roll back DB on errors.
- Structured logs without sensitive values.

Python & SQLAlchemy
- Prefer timezone-aware datetimes (`datetime.now(datetime.UTC)`) over `utcnow()`.
- Use SQLAlchemy 2.x patterns; `Session.get()` over legacy `Query.get()`; explicit sessions/transactions.

Clean code rules
- Naming: descriptive, no single-letter or unclear abbreviations. Functions as verbs; variables as nouns.
- Size: small, focused functions (~≤30-40 lines). Split files/modules when > ~300-400 lines unless justified.
- Structure: use guard clauses; avoid deep nesting (>2-3). Handle edge cases first. No gratuitous comments.
- Docs: concise docstrings for non-trivial functions/classes (intent and invariants), not line-by-line narration.
- Style: consistent formatting; no drive-by reformatting; wrap long expressions for readability.
- Exceptions: do not catch broad exceptions unless re-raising with added context; never ignore exceptions.

PR checklists
- API security: roles enforced; inputs validated; CSRF/rate limits applied; no sensitive data in logs; audit events emitted.
- Data integrity: financial ops are atomic/idempotent-safe; invariants and DB constraints preserved.
- Performance: indexed queries; no N+1; pagination + bounded limits.
- Testing: new logic covered (unit/integration); negative cases; deterministic tests; mocks for external services.
