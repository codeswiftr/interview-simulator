---
title: "Security-Focused Software Engineering Interview Guide"
description: "Complete guide to security engineering interviews — OWASP Top 10 deep dive, threat modeling, cryptography fundamentals, authentication vulnerabilities, secure code review, and interview prep for security-focused roles."
date: "2026-03-20"
category: "Technical Skills Guides"
---

# Security-Focused Software Engineering Interview Guide

Security engineering interviews come in two flavors: pure application security (penetration testing, vulnerability research) and software engineering with security focus (building secure systems, writing secure code, designing authentication). This guide focuses on the latter — what backend and platform engineers need to know when security is a key part of the role.

## OWASP Top 10 Deep Dive for Interviews

The OWASP Top 10 is the starting point for any security engineering discussion. Know these deeply — not just the names, but how they work and how to prevent them.

**Injection (SQL, Command, LDAP):**
The classic vulnerability: untrusted data is interpreted as code. SQL injection example: if an application builds a query as `"SELECT * FROM users WHERE name = '" + username + "'"`, an attacker enters `'; DROP TABLE users; --`. Prevention: parameterized queries/prepared statements. Never concatenate user input into SQL. For ORMs, avoid raw query methods with user input.

**Broken Authentication:**
Weak password requirements, no rate limiting on login (enables brute force), insecure session tokens (short or predictable tokens, HTTP not HTTPS), missing token invalidation on logout, no MFA. Interviewers ask: "How would you implement secure authentication?" — expect: argon2 or bcrypt for password hashing (not SHA-256), secure random session tokens, token expiry, token rotation, rate limiting on auth endpoints.

**Sensitive Data Exposure:**
Transmitting data unencrypted (HTTP instead of HTTPS), storing passwords in plaintext or with weak hashing (MD5), logging sensitive fields (credit card numbers, SSNs), returning more data than needed from APIs (over-fetching). Prevention: TLS everywhere, proper encryption at rest (AES-256 GCM), field-level encryption for sensitive data, audit logging without sensitive values.

**XML External Entities (XXE):**
Malicious XML input that references external entities — can lead to file disclosure, SSRF, or DoS. Prevention: disable external entity processing in XML parsers; use JSON instead of XML when possible.

**Security Misconfiguration:**
Default credentials left unchanged, unnecessary features enabled, directory listing enabled on web servers, verbose error messages that reveal stack traces and internal paths, S3 buckets left public. Prevention: security baseline scanning, IaC (Terraform) with security policies, staging environments that mirror production configuration.

## Cryptography Fundamentals

Interviewers at security-focused companies test applied cryptography knowledge.

**Symmetric vs Asymmetric:**
- **Symmetric** (AES): Same key for encryption and decryption. Fast; key distribution is the problem. Use for bulk data encryption
- **Asymmetric** (RSA, ECDSA): Public/private key pair. Public key encrypts or verifies; private key decrypts or signs. Slower; solves key distribution. Use for TLS handshake, digital signatures, key exchange

**Why not MD5 or SHA-1 for passwords:** MD5 and SHA-1 are fast cryptographic hash functions — designed to be computed quickly. For passwords, fast = bad; it enables brute force and rainbow table attacks. Use **bcrypt** (adaptive, adds salt), **argon2id** (memory-hard, resistant to GPU attacks), or **scrypt**. These are deliberately slow and can be tuned as hardware gets faster.

**TLS handshake overview (critical for system design interviews):**
Client Hello → Server Hello (certificate) → Client verifies certificate chain → Key exchange (ECDHE for forward secrecy) → Derive session keys → Symmetric encryption for all subsequent data. Know what forward secrecy means: even if the server's private key is later compromised, past sessions can't be decrypted.

**JWT security considerations:**
JWTs are frequently discussed. Key issues: `alg: none` attack (don't accept unsigned JWTs), algorithm confusion (RS256 vs HS256 attack), signing key security (don't hardcode in source), appropriate expiry (short for access tokens — 15min), refresh token rotation, token revocation (challenges with stateless JWTs).

## Authentication Architecture Patterns

**OAuth 2.0 flows:**
- Authorization Code + PKCE: For user-facing apps (web, mobile). Most secure
- Client Credentials: Machine-to-machine (M2M) — no user involved
- Never use implicit flow (deprecated; tokens exposed in URL fragment)

**Common interview question:** "How would you implement single sign-on (SSO) for a multi-product SaaS?"
Expected answer covers: SAML 2.0 or OIDC/OAuth 2.0, centralized identity provider, token-based sessions with short expiry, proper redirect validation to prevent open redirects.

**Session fixation attack:** Attacker sets a session ID before login, then waits for the victim to log in with that ID — attacker now has an authenticated session. Prevention: always generate a new session ID after login (session regeneration).

## Threat Modeling

Threat modeling is tested for senior security engineering roles and by companies that take security seriously (Stripe, banks, healthcare tech).

**STRIDE framework:**
- **S**poofing — Can an attacker impersonate a user or service?
- **T**ampering — Can data be modified in transit or storage?
- **R**epudiation — Can users deny performing actions? (requires audit logging)
- **I**nformation Disclosure — Can sensitive data be exposed?
- **D**enial of Service — Can the service be made unavailable?
- **E**levation of Privilege — Can a user gain more permissions than intended?

**Interview scenario:** "Threat model a payment API." Walk through each STRIDE dimension: How does the API authenticate callers (spoofing)? Are amounts validated server-side (tampering)? Is every transaction logged with user identity (repudiation)? What data is returned in error responses (information disclosure)? What happens under high request load (DoS)? What prevents a regular user from accessing another user's payment history (elevation of privilege)?

## Secure Code Review Checklist

When asked to review code for security issues:

1. **Input validation** — Are all inputs validated and sanitized at the entry point?
2. **Output encoding** — Is data encoded before being included in HTML, SQL, or shell commands?
3. **Authentication gates** — Are all endpoints protected? Is there a default-deny access control approach?
4. **Sensitive data handling** — Are passwords/tokens logged? Returned in API responses unnecessarily?
5. **Error handling** — Do error messages reveal internal information (stack traces, database errors)?
6. **Dependency vulnerabilities** — Are dependencies current? Run `npm audit`, `pip audit`, Snyk, or Dependabot

Security interviews reward engineers who think adversarially — who instinctively ask "how would someone abuse this?" when reviewing code or designing systems. Demonstrating that mindset, alongside concrete technical knowledge, is what distinguishes security-conscious engineers.
