# Interview Simulator - Human Gates

**Updated:** January 6, 2026
**Status:** LIVE (app.codeswiftr.com)

---

## Active Human Gates

### Blocking

| Gate | Impact | Decision Needed |
|------|--------|-----------------|
| Stripe Pricing | Revenue | Configure tier limits in dashboard |
| AI Prompt Changes | Quality | Review feedback prompts before deploy |

### Non-Blocking (Review Before Merge)

| Gate | Impact | Review Type |
|------|--------|-------------|
| Transcription Pipeline | Core feature | Code review |
| Scoring Algorithm | User experience | Manual testing |
| Subscription Logic | Revenue | Integration test |

---

## Autonomous Permissions

### Allowed Without Review

- Add test coverage (any module)
- Fix linting/formatting issues
- Performance optimizations (bundle size, lazy loading)
- Documentation updates (README, API docs)
- OpenAPI docstring improvements
- Bug fixes (non-security)
- Dependency patch updates

### Require Human Review

- `app/ai/` changes (transcription, feedback prompts)
- `app/api/auth.py` changes
- `app/api/subscriptions.py` changes
- Database migration files
- `.env` or secrets changes
- Major dependency updates (e.g., FastAPI 0.x to 1.x)

---

## Current Sprint 5 Tasks

### Autonomous (No Human Gate)

| Task ID | Task | Status |
|---------|------|--------|
| IS-P0-1 | Email service coverage (33% to 70%) | Pending |
| IS-P0-2 | Content sanitizer tests (0% to 80%) | Pending |
| IS-P0-3 | Fix temp file race condition | Pending |
| IS-P0-4 | Password policy tests | Pending |

### Requires Review

| Task | Reviewer | Status |
|------|----------|--------|
| AI prompt modifications | Human | Not started |
| Subscription tier changes | Human | Blocked on Stripe |

---

## Security Audit Summary (Dec 2025)

- **Risk Level:** LOW
- **Critical Issues:** 0
- **Medium Issues:** 2
  1. Password policy (6 char min - weak)
  2. Temp file cleanup race condition
- **Remediation:** P0 tasks address these

---

## Decision History

| Date | Decision | Outcome |
|------|----------|---------|
| Dec 2025 | Production deployment | LIVE on Railway + Cloudflare |
| Dec 2025 | Security audit | Passed with LOW risk |
| Jan 2026 | Sprint 5 focus | Security hardening + coverage |
