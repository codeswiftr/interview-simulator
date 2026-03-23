---
title: "Platform Security Engineer Interview: Zero Trust, IAM, and Secure Infrastructure"
description: "Prepare for platform security engineer interviews with coverage of zero trust architecture, IAM, secrets management, supply chain security, and 2026 compensation data."
date: "2026-03-20"
category: "Specialty Role Interviews"
---

# Platform Security Engineer Interview: Zero Trust, IAM, and Secure Infrastructure

Platform security engineering is a distinct discipline that often gets conflated with application security or security operations. The role focuses on securing the infrastructure layer — the platforms, pipelines, identity systems, and secrets management that everything else depends on. Getting this layer right is foundational; failures here tend to be catastrophic rather than isolated.

## Role Differentiation

**Platform security engineer vs AppSec:** AppSec focuses on vulnerabilities in application code — SQL injection, XSS, SAST scanning, threat modeling for features. Platform security focuses on the infrastructure that runs the code — Kubernetes RBAC, IAM policies, network segmentation, CI/CD pipeline security.

**Platform security vs SecOps:** SecOps (SOC, SIEM, incident response) is reactive — detecting and responding to attacks in progress. Platform security is proactive — designing systems so that attacks have limited blast radius and detection is built in.

Most organizations of meaningful scale need both functions, but the interview content is quite different.

## Core Domain: Zero Trust Architecture

Zero trust rejects the perimeter security model ("everything inside the network is trusted") in favor of continuous verification. Key principles:

- **Never trust, always verify:** Every request, regardless of network origin, must be authenticated and authorized.
- **Least privilege access:** Users and services receive the minimum permissions necessary for their function.
- **Assume breach:** Design systems so that a compromised identity or service cannot laterally pivot without triggering detection.

In practice, zero trust implementations involve service mesh with mutual TLS (Istio, Linkerd), replacing VPN-based access with identity-aware proxies (Google BeyondCorp, Cloudflare Access, Teleport), and workload identity systems that assign cryptographic identities to services rather than relying on network addresses.

## Core Domain: IAM

Identity and access management is where most platform security work concentrates. Interview expectations include:

**Protocols:** SAML 2.0 for enterprise SSO (XML-based assertions, used with Okta, Azure AD), OAuth 2.0 for authorization delegation, OIDC (OpenID Connect) layered on OAuth for authentication. Know the difference between an authorization code flow and a client credentials flow, and when each is appropriate.

**Okta and IdP architecture:** Configuring applications in Okta, designing group-to-role mappings, setting up MFA policies, and integrating with cloud provider identity (AWS IAM Identity Center, GCP Workload Identity Federation).

**Cloud IAM:** AWS IAM policies — understanding the policy evaluation order (explicit deny → organization SCP → permission boundary → resource policy → identity policy), writing least-privilege IAM policies, detecting overly permissive policies programmatically. GCP IAM roles and bindings. Interviewers frequently present an IAM policy and ask you to identify the security issue.

**Workload identity:** Rather than giving workloads static credentials, modern practice uses short-lived tokens issued by identity systems — AWS instance metadata IMDS tokens, Kubernetes service accounts bound to OIDC providers, or SPIFFE/SPIRE for multi-platform identity.

## Core Domain: Secrets Management

Hardcoded secrets in source code are a perennial failure. Platform security engineers design and operate secrets management systems:

**HashiCorp Vault:** Dynamic secrets (Vault generates short-lived database credentials on demand rather than distributing long-lived passwords), PKI secrets engine for certificate issuance, AppRole and Kubernetes authentication methods. Knowing how to configure a Vault policy and troubleshoot authentication failures is standard.

**Cloud-native secrets:** AWS Secrets Manager and Parameter Store, GCP Secret Manager. Understanding rotation, cross-account access, and integrating with EKS/GKE workloads.

**Secret sprawl detection:** Using tools like GitLeaks, TruffleHog, or cloud-native scanning to detect secrets committed to repositories.

## Core Domain: Supply Chain Security

Post-SolarWinds and XZ Utils, supply chain security has moved from theoretical to critical. Platform security engineers are expected to know:

**SBOM generation and management:** Software Bill of Materials documents what's in a build. Tools like Syft generate SBOMs; Grype or Trivy scan them for known vulnerabilities.

**Container image signing:** Cosign (from the Sigstore project) signs and verifies container images. Policy engines like Kyverno or OPA Gatekeeper enforce that only signed images run in production.

**SLSA framework:** Supply-chain Levels for Software Artifacts provides a graduated framework for build and provenance security. Level 1-4 represent increasing hardening of the build pipeline.

## Sample Interview Questions

**Q: A developer reports that their service can't authenticate to the AWS API from an EC2 instance. They're using an IAM role. How do you debug this?**
A: Check that the instance profile is actually attached to the instance. Verify the IAM role's trust policy allows `ec2.amazonaws.com` to assume it. Review the IAM role's permission policies — use the IAM policy simulator to test the specific action and resource. Check for permission boundaries or SCPs that might deny the action even if the role policy allows it. Inspect CloudTrail for the specific `AccessDenied` event, which will show the exact policy evaluation result.

**Q: How would you prevent secrets from being committed to a GitHub repository at scale?**
A: Multi-layered approach. Pre-commit hooks using detect-secrets or GitLeaks to catch secrets before they're committed. GitHub Advanced Security or a third-party scanner (Trufflesecurity, GitGuardian) to scan all pushes server-side and block or alert. Rotate and revoke any detected secrets immediately. Longer term, migrate to short-lived credentials (workload identity, Vault dynamic secrets) so there are no long-lived secrets to leak.

## Compensation

Platform security engineers are among the highest-compensated individual contributors in infrastructure. Senior levels in San Francisco earn **$180K-$260K base**, with staff and principal roles reaching $300K+ in total compensation. The specialization premium is real — security-focused engineers consistently earn 20-35% above equivalent generalist infrastructure roles.
