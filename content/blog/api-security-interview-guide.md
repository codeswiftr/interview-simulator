---
title: "API Security Interview Guide"
description: "Security questions in backend and platform interviews: authentication vs. authorization, OAuth 2.0 flows, JWT pitfalls, rate limiting, and common API vulnerabilities from OWASP API Top 10."
date: "2026-03-19"
category: "Technical Skills"
---

# API Security Interview Guide

API security questions appear in backend, platform, and full-stack interviews at companies where the API is the product — Stripe, Twilio, Okta, GitHub — and increasingly at any company where engineers own their own services end-to-end. This isn't a security specialist role topic; it's baseline engineering knowledge that senior interviews now test. This guide covers the concepts that appear most frequently.

## Authentication vs. Authorization

This is the most common security interview question, and the answer requires more than a one-line definition.

**Authentication**: Proving who you are. Mechanisms: passwords, API keys, OAuth tokens, JWTs, certificates. The system answers "is this really user X?"

**Authorization**: Proving what you're allowed to do. Mechanisms: RBAC (role-based access control), ABAC (attribute-based), ACLs, scopes on OAuth tokens. The system answers "is user X allowed to do this?"

The failure mode interviewers probe: treating these as a single step. An API that correctly identifies a user (authentication passes) but doesn't check whether that user can access the requested resource (authorization skipped) leaks data.

A common interview question: "Walk me through how you'd implement authorization for a multi-tenant SaaS API where users can only see their own organization's data." Strong answers include: resource ownership checks in every query (not just at the route level), how to prevent horizontal privilege escalation (accessing another org's data by changing an ID in the request), and testing strategy for authorization rules.

## JWT Security Pitfalls

JWTs are ubiquitous in API authentication, and interviewers at companies using them probe specific pitfalls:

**The `none` algorithm attack**: Some early JWT libraries accepted `alg: none` in the header, meaning no signature was required. Always verify the algorithm before validating — don't trust the `alg` field in the token header.

**Weak signing secrets**: JWTs signed with HMAC are only as secure as the secret. Short or guessable secrets can be brute-forced offline. Use 256+ bit secrets generated from a CSPRNG.

**`exp` claim not checked**: Tokens without expiration or with unchecked expiration are effectively permanent credentials. Always validate `exp` and set short lifetimes (15 minutes for access tokens, longer for refresh tokens with rotation).

**Storing JWTs in localStorage**: XSS attacks can steal tokens from localStorage. httpOnly cookies protect against XSS (JavaScript can't read them). The tradeoff: cookies are vulnerable to CSRF, which requires its own mitigation (SameSite=Strict or CSRF tokens).

Interview question: "What are the security considerations for implementing a 'remember me' feature?" Involves refresh token rotation, secure storage, token revocation on logout, and binding tokens to device fingerprints.

## OAuth 2.0 Flows

OAuth is tested in interviews at API platform companies and anywhere third-party integrations exist. The key flows:

**Authorization Code Flow**: For server-side apps. User authorizes at the provider, provider redirects with an authorization code, server exchanges code for tokens. Tokens never exposed in the URL or browser history. Add PKCE (Proof Key for Code Exchange) to prevent authorization code interception.

**Client Credentials Flow**: For machine-to-machine authentication. No user involved — a service authenticates with its own credentials to get a token. Used for backend service-to-service calls.

**Implicit Flow**: Deprecated. Exposed tokens in URL fragments, no refresh tokens. Don't use — replace with Authorization Code + PKCE.

The PKCE question comes up often: "Why is PKCE necessary even for server-side apps?" Answer: it prevents authorization code interception attacks in environments where redirect URIs can be intercepted, adding a verifier that only the original requester can provide.

## OWASP API Top 10: What Interviews Test

The OWASP API Security Top 10 is the interview reference for API vulnerabilities. High-frequency items:

**Broken Object Level Authorization (BOLA/IDOR)**: Most common API vulnerability. Accessing resources by changing object IDs in the request (`/api/orders/12345` → `/api/orders/12346`). Mitigation: check ownership for every resource access, never trust client-provided IDs alone.

**Excessive Data Exposure**: APIs returning full data objects when the client only needs a subset. A `/api/users/me` endpoint returning password hash, internal IDs, and private fields that the UI doesn't display. Mitigation: explicit field selection or separate response DTOs.

**Rate Limiting and Resource Consumption**: Endpoints without rate limits enable credential stuffing, scraping, and DoS. Implementation: rate limit by IP, user, and API key with appropriate limits per tier. Return 429 with `Retry-After` header.

**Security Misconfiguration**: Debug endpoints exposed in production, CORS set to `*`, verbose error messages exposing stack traces. Mitigation: environment-specific configuration, security headers, structured error responses that don't leak internals.

## Practical Security Patterns for Interviews

When asked to design an API in an interview, incorporating security patterns unprompted signals maturity:

- **Defense in depth for authorization**: Check permissions at the route level AND the data layer — don't assume middleware covers everything
- **Input validation**: Validate and sanitize at the boundary. Use parameterized queries — never string interpolation for SQL
- **Secure defaults**: Default to deny, not allow. New features should require explicit permission grants, not implicit access
- **Audit logging**: Log authentication events (login, token exchange, failed attempts) and significant authorization decisions. Not for debugging — for incident response

The security question interviewers ask most to distinguish senior candidates: "How would you test the authorization logic in this API?" Strong answer: explicit test cases for each authorization rule, including tests that verify a user in role X cannot access resource Y even if they manipulate the request. Not just "the happy path works" but "the attack paths are blocked."

API security is no longer a specialist domain. It's a baseline expectation for engineers who own production services — and interviews at companies with that ownership model reflect it.
