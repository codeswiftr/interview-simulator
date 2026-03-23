---
title: "Security Engineer Advanced Interview: Threat Modeling, Cryptography, and Secure Design"
description: "A technical deep-dive into security engineering interviews covering threat modeling with STRIDE, cryptography fundamentals, AppSec vs infrastructure security roles, and sample Q&A."
date: "2026-03-20"
category: "Specialty Role Interviews"
---

# Security Engineer Advanced Interview: Threat Modeling, Cryptography, and Secure Design

Security engineering interviews are among the most varied in software. An AppSec engineer at a fintech startup and a detection engineer at a cloud provider will face entirely different questions. Before you prep, identify which security discipline the role requires—the frameworks and technical vocabulary differ substantially.

## Security Engineering Disciplines and What Each Tests

**Application Security (AppSec)** engineers embed into product teams and review code, architecture, and design. Interviews focus on OWASP Top 10, code review techniques (finding SQLi, XSS, IDOR), security testing pipelines (SAST/DAST), and threat modeling new features.

**Infrastructure Security** engineers protect cloud environments, networks, and identity systems. Expect questions on IAM policies, VPC segmentation, secrets management (Vault, AWS KMS), TLS configuration, and hardening runbooks.

**Detection Engineering** roles at security operations centers or product security teams focus on writing detection rules (Sigma, Yara, Splunk SPL), understanding attacker TTPs (MITRE ATT&CK), reducing false positive rates, and log pipeline architecture.

Know which track you are interviewing for. Most job postings will signal this in the required skills section.

## Threat Modeling with STRIDE

Threat modeling is a near-universal topic in security interviews, especially at companies with mature security organizations. STRIDE is the most commonly referenced framework.

STRIDE stands for: **Spoofing**, **Tampering**, **Repudiation**, **Information Disclosure**, **Denial of Service**, **Elevation of Privilege**.

A practical interview question: "Walk me through threat modeling a password reset flow." A strong answer applies STRIDE systematically:

- Spoofing: Can an attacker initiate a reset for another user's email?
- Tampering: Is the reset token validated server-side, or can the token be modified?
- Repudiation: Are reset attempts logged with enough detail to audit abuse?
- Information Disclosure: Does the response reveal whether an email exists in the system (user enumeration)?
- Denial of Service: Can an attacker spam reset requests to lock out a user or abuse email rate limits?
- Elevation of Privilege: Does the reset flow bypass MFA, granting access without the second factor?

Interviewers are not looking for you to recite definitions—they want to see you apply the framework fluently to a concrete system.

## Cryptography Fundamentals Interviewers Actually Test

You do not need to implement RSA from scratch. You do need to know when and why to use different cryptographic primitives.

**Hashing**: SHA-256 and SHA-3 are collision-resistant and one-way. They are not encryption. For password storage, use a memory-hard KDF—bcrypt, scrypt, or Argon2. A candidate who suggests SHA-256 for password hashing will not pass this question.

**Symmetric encryption**: AES-GCM is the standard for bulk data encryption. It provides authenticated encryption (confidentiality + integrity). Never use AES-ECB—it leaks patterns in ciphertext. Know that GCM nonce reuse is catastrophic.

**Asymmetric encryption**: RSA and ECC (ECDSA, ECDH) are used for key exchange and digital signatures, not bulk encryption. RSA-OAEP is the correct padding scheme—never PKCS#1 v1.5 for new systems.

**TLS**: Know the TLS 1.3 handshake at a high level—client hello, server hello, certificate, key exchange (ECDHE), session keys derived via HKDF. Know why TLS 1.0/1.1 are deprecated (BEAST, POODLE attacks). Know what certificate pinning is and its tradeoffs.

Common interview question: "Explain the difference between signing and encryption." Signing uses a private key to produce a signature; anyone with the public key can verify it. Encryption uses a public key to encrypt; only the private key holder can decrypt. Many candidates conflate these.

## Secure Design Patterns Worth Knowing

**Principle of least privilege**: Every component should have only the permissions it needs. Applied to IAM: Lambda functions should have execution roles scoped to the exact resources they access—not wildcard policies.

**Defense in depth**: Multiple independent security controls. If one fails, others remain. Relevant in system design interviews: a web app with a WAF, parameterized queries, and output encoding is more defensible than one relying on a WAF alone.

**Secure defaults**: Systems should be secure out of the box. S3 buckets should be private by default. APIs should require authentication by default. Interviewers ask: "What is a secure default you would enforce in a new microservices deployment?"

**Separation of duties**: No single entity should be able to both create and approve a critical action. Relevant for deployment pipelines and financial transaction systems.

## Sample Q&A

**Q: A developer asks you to review a new API endpoint. What do you check first?**

A: Authentication and authorization—is the endpoint protected, and does it enforce ownership checks (not just login checks)? Then input validation—are all parameters validated server-side? Then output—does the response leak sensitive fields? Finally, logging—are access and errors logged without including sensitive data?

**Q: How would you detect credential stuffing against a login endpoint?**

A: Monitor for high volume of login attempts from distributed IPs with low success rates. Correlate against known breached credential lists using HaveIBeenPwned-style checks. Implement progressive delays, CAPTCHA triggers on anomalous patterns, and alert on geographic velocity anomalies (same user logging in from two countries minutes apart).

**Q: Explain a time you found a security vulnerability in a design, not in code.**

Use this to demonstrate threat modeling in practice. Walk through the system, the threat you identified, what the impact would have been, and what design change you recommended. Concrete specifics—data type, attack vector, business impact—make this answer stand out.

Security engineering interviews reward candidates who think adversarially and communicate risk in business terms. Pair your technical depth with clear explanations of impact, and you will distinguish yourself from candidates who only recite framework names.
