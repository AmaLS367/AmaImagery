# Features Documentation

## Overview

Complete documentation of all features available in the AI Image Generator, including image generation, editing, upscaling, resizing, and content moderation.

## Core Features

### 🎨 Image Generation
Generate high-quality images from text prompts using Stable Diffusion models.

**Capabilities:**
- Text-to-image generation
- Custom model selection
- Advanced parameters (steps, guidance, seed)
- Batch generation
- Negative prompts

### ✏️ Image Editing
Edit existing images with AI-powered tools.

**Capabilities:**
- Inpainting (fill masked areas)
- Outpainting (expand images)
- Image-to-image with prompts
- Style transfer with IP-Adapter
- Controlnet guidance

### 🔍 Image Upscaling
Enhance image resolution and quality.

**Capabilities:**
- AI-powered upscaling
- Multiple scaling factors (2x, 4x)
- Detail enhancement
- Artifact reduction

### 📐 Image Resizing
Resize and crop images efficiently.

**Capabilities:**
- Smart cropping
- Aspect ratio maintenance
- Batch resizing
- Quality preservation

### 🛡️ Content Moderation
Ensure safe and appropriate content.

**Capabilities:**
- NSFW detection
- Prompt filtering
- Negative word blocking
- Content safety scoring

### 📁 File Management
Manage generated images and uploads.

**Capabilities:**
- Signed URLs for secure access
- File upload validation
- Storage management
- Automatic cleanup

## Documentation Sections

- [Image Generation](./image-generation.md) - Generation details
- [Image Editing](./image-editing.md) - Editing features
- [Image Upscaling](./image-upscaling.md) - Upscaling guide
- [Image Resizing](./image-resizing.md) - Resizing options
- [Content Moderation](./content-moderation.md) - Moderation system
- [File Management](./file-management.md) - File handling

## Feature Comparison

| Feature | Free Tier | Pro Tier |
|---------|-----------|----------|
| Basic Generation | ✅ Limited | ✅ Unlimited |
| Advanced Editing | ❌ | ✅ |
| Upscaling | ✅ 2x only | ✅ Up to 4x |
| Batch Processing | ❌ | ✅ |
| Priority Queue | ❌ | ✅ |
| API Access | ✅ Limited | ✅ Full |

## API Endpoints

- `POST /api/v1/images/generate` - Generate images
- `POST /api/v1/images/edit` - Edit images
- `POST /api/v1/images/upscale` - Upscale images
- `POST /api/v1/images/resize` - Resize images
- `POST /api/v1/moderation/nsfw` - Check NSFW

See [API Documentation](../backend/api/endpoints/images.md) for details.

