# Features Documentation

## Overview

| Symbol | Meaning |
|--------|---------|
| ✅ | Available |
| 🧪 | Provider-dependent or environment-dependent |
| 🚧 | Planned, not yet available |

## Feature Status

| Feature | Status | Notes |
|---------|--------|-------|
| Text-to-image generation | ✅ Live | Public flow via `/api/v1/images/generate` |
| Generation status polling | ✅ Live | `/api/v1/images/status/{task_id}` |
| Generation history | ✅ Live | `/api/v1/users/me/generations` |
| User settings | ✅ Live | `/api/v1/users/me/settings` |
| Hygiene mode | ✅ Live | `/api/v1/users/me/hygiene-mode` |
| NSFW moderation routes | ✅ Live | Under `/api/v1/nsfw/*` |
| Signed file delivery | ✅ Live | Via `/api/v1/file` |
| Admin pages | ✅ Live | Under `/admin/*` |
| Local Diffusers runtime | 🧪 Supported | Environment/provider dependent |
| External ComfyUI runtime | 🧪 Supported | Environment/provider dependent |
| Image editing | 🚧 Planned / not public | Not exposed as a current public API |
| Upscaling | 🚧 Planned / not public | Not exposed as a current public API |
| Resizing | 🚧 Planned / not public | Not exposed as a current public API |

## Core Features

### 🎨 Image Generation
Generate images from text prompts through the async job flow.

**Capabilities:**
- text-to-image generation
- prompt + negative prompt submission
- generation parameters such as width, height, steps, and guidance
- provider-backed execution through `comfyui` or `diffusers`

### 🛡️ Content Moderation
Moderation and hygiene controls.

**Capabilities:**
- NSFW preference toggle
- NSFW rule inspection and reload routes
- prompt hygiene mode support

### 📁 File Management

**Capabilities:**
- signed file access flow
- artifact download path
- persisted output handling through the worker lifecycle

## Planned / Coming Soon Areas

- `Image Editing` — Coming soon
- `Image Upscaling` — Coming soon
- `Image Resizing` — Coming soon
- deeper feature playbooks and walkthroughs — Coming soon

## API Endpoints

- `POST /api/v1/images/generate` - Generate images
- `GET /api/v1/images/status/{task_id}` - Poll status
- `GET /api/v1/users/me/generations` - View generation history
- `GET/PATCH /api/v1/users/me/settings` - Manage saved settings
- `GET/PATCH /api/v1/users/me/hygiene-mode` - Manage hygiene mode
- `PATCH /api/v1/nsfw/users/me/nsfw` - Toggle NSFW preference
- `POST /api/v1/nsfw/check` - Check text against moderation rules
- `GET /api/v1/file` - Download signed artifact

See [Reference](../reference/README.md) for full details.
