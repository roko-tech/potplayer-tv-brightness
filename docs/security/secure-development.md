# Secure development guide

## Identity and authorization

- Authenticate at a well-defined boundary and fail closed.
- Authorize every protected action and resource server-side; possession of an identifier is not permission.
- Use least-privilege roles, short-lived credentials, secure session/cookie settings, revocation, and audit events for sensitive actions.
- For multi-user systems, include the user/tenant boundary in storage access and negative tests.

## Input, output, and side effects

- Treat request data, files, URLs, provider responses, model output, and persisted legacy data as untrusted.
- Parse into explicit types with size, range, format, and semantic limits.
- Use parameterized queries and context-appropriate output encoding.
- Allowlist destinations and canonicalize paths before file/network access.
- Make externally visible writes idempotent where retries or duplicate delivery are possible.

## Secrets and sensitive data

- Keep secrets in an approved secret manager or GitHub environment, never source, history, logs, issue text, prompts, or fixtures.
- Commit `.env.example` with names and safe documentation only.
- Minimize collected data; document purpose, classification, retention, deletion, export, encryption, and access.
- Redact structured logs at creation. Restrict debug output and production diagnostics.

## Dependencies and build supply chain

- Prefer the standard library or existing dependencies when they satisfy the requirement.
- Review necessity, maintenance, provenance, license, transitive risk, and update policy before adding production dependencies.
- Pin direct dependencies and commit lockfiles. Review automated updates; never auto-merge a breaking or security-sensitive change without tests.
- Pin third-party GitHub Actions to full commit SHAs and annotate the intended release.
- Build with least-privilege tokens on hosted/ephemeral runners for untrusted contributions. Do not execute fork-controlled code with secrets.
- Generate provenance/signatures or attestations when release risk justifies them, and verify the artifact users receive matches the reviewed source/build.

## Errors and availability

- Return safe user errors while preserving correlated internal diagnostics.
- Bound timeouts, retries, payloads, concurrency, memory, and cost. Use jitter and circuit/backpressure behavior where appropriate.
- Define degraded behavior and preserve user data on partial failure.

## Security validation

Maintain tests for authorization, unsafe inputs, sensitive output, dependency boundaries, migrations, and abuse cases. Add static/dependency/secret scanning appropriate to the stack, but validate findings and keep manual threat review for design-level risk.

Report vulnerabilities through [SECURITY.md](../../SECURITY.md).
