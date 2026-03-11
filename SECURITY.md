# Security Policy

> Security reports belong in private first, public later.

If you believe you found a vulnerability in AmaImagery, report it privately:

`amalsdev367@gmail.com`

Do **not** open a public issue for an unpatched security problem.

---

## What To Send

Include enough detail to reproduce and assess impact:

- affected component, route, or subsystem
- impact summary
- steps to reproduce
- proof of concept, logs, screenshots, or payloads if relevant
- whether you believe the issue is already being exploited

## What Matters Most

Reports are especially valuable when they involve:

- authentication or authorization bypass
- token, cookie, or session handling flaws
- artifact or file exposure bugs
- SSRF, command execution, traversal, or injection paths
- secrets disclosure
- provider abuse or prompt abuse paths with security impact

## Handling Expectations

Best-effort triage usually follows this sequence:

1. Acknowledge receipt
2. Reproduce and validate
3. Prepare a fix or mitigation
4. Coordinate disclosure timing if the report is valid

## Supported Line

Security fixes are prioritized for the active release path leading to `0.1.0`.

If the report is real, actionable, and responsibly disclosed, it will be treated seriously.
