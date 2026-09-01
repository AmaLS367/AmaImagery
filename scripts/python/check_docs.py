from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOC_ROOTS = [
    ROOT / "README.md",
    ROOT / "docs" / "README.md",
    ROOT / "docs" / "en",
    ROOT / "docs" / "ru",
]

BANNED_TOKENS = [
    "AI Image Generator",
    "python run_dev.py",
    "/api/v1/images/edit",
    "/api/v1/images/upscale",
    "/api/v1/images/resize",
]

MARKDOWN_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
HTML_HREF_RE = re.compile(r'href="([^"]+)"')


def iter_markdown_files() -> list[Path]:
    files: list[Path] = []
    for entry in DOC_ROOTS:
        if entry.is_file():
            files.append(entry)
            continue
        files.extend(sorted(entry.rglob("*.md")))
    return files


def normalize_target(raw_target: str) -> str | None:
    target = raw_target.strip()
    if not target:
        return None
    if target.startswith(("http://", "https://", "mailto:", "#")):
        return None
    if target.startswith("<") and target.endswith(">"):
        target = target[1:-1].strip()
    if "#" in target:
        target = target.split("#", 1)[0]
    if not target:
        return None
    return target


def check_links(files: list[Path]) -> list[str]:
    errors: list[str] = []
    for path in files:
        text = path.read_text(encoding="utf-8")
        targets = MARKDOWN_LINK_RE.findall(text) + HTML_HREF_RE.findall(text)
        for raw_target in targets:
            target = normalize_target(raw_target)
            if target is None:
                continue
            resolved = (path.parent / target).resolve()
            if not resolved.exists():
                errors.append(f"{path.relative_to(ROOT)} -> missing link target: {raw_target}")
    return errors


def check_banned_tokens(files: list[Path]) -> list[str]:
    errors: list[str] = []
    for path in files:
        text = path.read_text(encoding="utf-8")
        for token in BANNED_TOKENS:
            if token in text:
                errors.append(f"{path.relative_to(ROOT)} -> banned token: {token}")
    return errors


def main() -> int:
    files = iter_markdown_files()
    errors = check_links(files)
    errors.extend(check_banned_tokens(files))

    if errors:
        print("Documentation check failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"Documentation check passed for {len(files)} markdown files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
