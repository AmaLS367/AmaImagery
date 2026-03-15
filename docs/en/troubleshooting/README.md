# Troubleshooting Documentation

## Overview

Current issues, debugging paths, and operational notes for **AmaImagery**.

## Quick Links

| Topic | Status |
|------|--------|
| Common issues page | 🚧 Coming soon |
| Error code reference | 🚧 Coming soon |
| GPU-specific page | 🚧 Coming soon |
| Memory issues page | 🚧 Coming soon |
| Performance issues page | 🚧 Coming soon |

## Common Issues

### Installation Problems

#### Issue: local ML runtime cannot start
**Symptoms:** provider boot failures, missing models, missing CUDA, or unsupported dtype

**Checks:**
1. verify model files and cache paths
2. verify GPU/CUDA only if you are actually using local Diffusers
3. verify provider env config

#### Issue: frontend runs but generation never completes
**Checks:**
1. confirm the worker process is running
2. confirm PostgreSQL is reachable
3. confirm the selected provider is usable

### Runtime Errors

#### Issue: ComfyUI flow does not connect
**Checks:**
1. verify `COMFYUI_BASE_URL`
2. verify `COMFYUI_WEBSOCKET_URL`
3. verify the external ComfyUI service is reachable

#### Issue: signed file access fails
**Checks:**
1. verify artifact exists
2. verify signing/TTL settings
3. verify URL rewriting is not breaking the download path

### Docker Issues

#### Issue: container exits immediately
**Checks:**
1. inspect `docker compose logs`
2. verify env files
3. verify ports/volumes

## Getting Help

1. Check the relevant section README
2. Capture logs and exact commands
3. Record env/runtime/provider context
4. Reproduce with the simplest supported flow
