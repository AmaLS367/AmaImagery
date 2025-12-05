# Shared Resources

This directory contains resources shared across all language versions of the documentation.

## Directory Structure

```
_shared/
├── images/          # Screenshots, diagrams, illustrations
├── diagrams/        # Architecture and technical diagrams
├── videos/          # Video links and metadata
└── assets/          # Other shared resources
```

## Usage Guidelines

### Images

Place all images here to avoid duplication across language directories.

**Naming convention:**
- Use descriptive names: `architecture-overview.png`
- Include version if needed: `api-flow-v2.png`
- Use lowercase with hyphens

**Supported formats:**
- PNG (preferred for screenshots and diagrams)
- JPG (for photos)
- SVG (for vector graphics)
- WebP (for optimized web images)

**Reference from docs:**
```markdown
![Alt text](../_shared/images/filename.png)
```

### Diagrams

Store architecture diagrams, flowcharts, and technical diagrams here.

**Tools:**
- PlantUML (`.puml` files)
- Mermaid (`.mmd` files)
- Draw.io (`.drawio` files)
- Export to PNG/SVG for use in docs

**Example reference:**
```markdown
![System Architecture](../_shared/diagrams/system-architecture.png)
```

### Videos

Store video metadata and links (not the actual video files).

**Format:**
```json
{
  "id": "video-001",
  "title": "Getting Started Tutorial",
  "url": "https://example.com/video",
  "duration": "10:30",
  "language": "en",
  "subtitles": ["en", "ru"]
}
```

### Assets

Other shared resources like:
- Icons
- Logos
- Fonts (if needed)
- Data files for examples

## Best Practices

1. **Optimize images:** Compress before committing
2. **Use descriptive names:** Make names self-explanatory
3. **Keep organized:** Use subdirectories for different types
4. **Document sources:** Add attribution in comments if needed
5. **Update references:** When moving/renaming, update all docs

## Contributing

When adding new shared resources:
1. Place in appropriate subdirectory
2. Use proper naming convention
3. Update this README if adding new categories
4. Verify all language docs can access the resource

