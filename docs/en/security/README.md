# Security Documentation

## Overview

Security notes for the current **AmaImagery** runtime: auth, file delivery, rate limiting, moderation, and operational safeguards.

## Security Features

### 🔐 Authentication
- JWT-based auth flows
- password hashing
- refresh token flow
- session/cookie related config

### 🛡️ Authorization
- authenticated route protection
- superuser-only admin access

### 🚦 Rate Limiting
- per-user and per-IP controls
- Redis-backed where enabled

### ✅ Input Validation
- Pydantic validation
- request size limits
- file validation on the delivery side

### 🔍 Content Filtering
- NSFW rules
- prompt hygiene
- user NSFW preferences

### 🌐 Network / Runtime Safety
- network guard options
- host/origin related config
- security headers and cookie settings

## Documentation Sections

| Topic | Status |
|------|--------|
| Authentication deep-dive | 🚧 Coming soon |
| Authorization deep-dive | 🚧 Coming soon |
| Rate limiting deep-dive | 🚧 Coming soon |
| Input validation deep-dive | 🚧 Coming soon |
| Content filtering deep-dive | 🚧 Coming soon |
| Network security deep-dive | 🚧 Coming soon |
| Data protection deep-dive | 🚧 Coming soon |
| Security best practices page | 🚧 Coming soon |

## Reporting Security Issues

If you discover a security vulnerability, email `ama@amadev.tech`. Do not open a public issue for an unpatched security problem.

See the repository-level [SECURITY.md](../../SECURITY.md) for the current disclosure policy.
