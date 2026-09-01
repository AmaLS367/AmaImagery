"""
Delete all __pycache__ directories and .pyc/.pyo files from the project.

This script recursively walks through the project directory and removes:
- All __pycache__ directories
- All .pyc files
- All .pyo files
- All .pyd files (Windows)

Usage:
    python scripts/python/delete_cache.py
    python -m scripts.python.delete_cache
"""

import os
import shutil
import sys
from pathlib import Path


def find_project_root() -> Path:
    current = Path(__file__).resolve()
    while current.parent != current:
        if (current / "pyproject.toml").exists():
            return current
        current = current.parent
    raise RuntimeError("Could not find project root (pyproject.toml)")


def delete_cache_files(root: Path) -> dict[str, list[str]]:
    deleted = {
        "directories": [],
        "pyc_files": [],
        "pyo_files": [],
        "pyd_files": [],
    }

    skip_dirs = {
        ".git",
        ".venv",
        "venv",
        "env",
        "ENV",
        "node_modules",
        "build",
        "dist",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
    }

    for root_dir, dirs, files in os.walk(root):
        root_path = Path(root_dir)

        dirs[:] = [d for d in dirs if d not in skip_dirs]

        if root_path.name == "__pycache__":
            try:
                shutil.rmtree(root_path)
                deleted["directories"].append(str(root_path))
                print(f"Deleted directory: {root_path}")
            except OSError as e:
                print(f"Error deleting {root_path}: {e}", file=sys.stderr)
            continue

        for file in files:
            file_path = root_path / file
            if file.endswith(".pyc"):
                try:
                    file_path.unlink()
                    deleted["pyc_files"].append(str(file_path))
                    print(f"Deleted file: {file_path}")
                except OSError as e:
                    print(f"Error deleting {file_path}: {e}", file=sys.stderr)
            elif file.endswith(".pyo"):
                try:
                    file_path.unlink()
                    deleted["pyo_files"].append(str(file_path))
                    print(f"Deleted file: {file_path}")
                except OSError as e:
                    print(f"Error deleting {file_path}: {e}", file=sys.stderr)
            elif file.endswith(".pyd"):
                try:
                    file_path.unlink()
                    deleted["pyd_files"].append(str(file_path))
                    print(f"Deleted file: {file_path}")
                except OSError as e:
                    print(f"Error deleting {file_path}: {e}", file=sys.stderr)

    return deleted


def main():
    try:
        project_root = find_project_root()
        print(f"Project root: {project_root}")
        print("Scanning for cache files and directories...\n")

        deleted = delete_cache_files(project_root)

        print("\n" + "=" * 60)
        print("Summary:")
        print(f"  Directories deleted: {len(deleted['directories'])}")
        print(f"  .pyc files deleted: {len(deleted['pyc_files'])}")
        print(f"  .pyo files deleted: {len(deleted['pyo_files'])}")
        print(f"  .pyd files deleted: {len(deleted['pyd_files'])}")

        total = (
            len(deleted["directories"])
            + len(deleted["pyc_files"])
            + len(deleted["pyo_files"])
            + len(deleted["pyd_files"])
        )

        if total == 0:
            print("\nNo cache files found. Project is clean!")
        else:
            print(f"\nTotal items deleted: {total}")
            print("Cache cleanup completed successfully!")

    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
