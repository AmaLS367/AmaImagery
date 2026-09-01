import os

# Directories to ignore
IGNORE_DIRS = {
    ".git",
    "__pycache__",
    ".venv",
    "venv",
    "env",
    ".idea",
    ".vscode",
    "node_modules",
    "logs",
    "outputs",
    "models",  # models contains large weight files
    "migrations/__pycache__",
}

# File extensions to include
INCLUDE_EXT = {
    ".py",
    ".ts",
    ".tsx",
    ".json",
    ".md",
    ".yml",
    ".yaml",
    ".toml",
    ".ini",
    ".txt",
    ".sh",
    ".ps1",
    ".conf",
    ".css",
}

# Specific files to ignore
IGNORE_FILES = {
    "desktop.ini",
    "poetry.lock",
    "yarn.lock",
    "package-lock.json",
    # Large model files
    "dreamshaper_6NoVae.safetensors",
}

# Binary / heavy extensions to ignore
IGNORE_EXT = {".safetensors", ".bin", ".pt", ".pth", ".ckpt"}


def should_include_file(file_path: str, file: str) -> bool:
    """Checks whether a file should be included in the context bundle."""
    # Check specific ignored files
    if file in IGNORE_FILES:
        return False

    # Check ignored extensions
    _, ext = os.path.splitext(file)
    if ext in IGNORE_EXT:
        return False

    # Check included extensions
    if ext in INCLUDE_EXT:
        return True

    # Special extensionless configuration files
    if file in ("Dockerfile", "alembic.ini"):
        return True

    return False


def generate_context() -> None:
    """Generates complete project context into a single file."""
    output_file = "full_project_context_amaimagery.txt"

    file_count = 0
    total_size = 0

    with open(output_file, "w", encoding="utf-8") as outfile:
        # Header
        outfile.write("=" * 80 + "\n")
        outfile.write("FULL PROJECT CONTEXT\n")
        outfile.write("=" * 80 + "\n\n")

        # Walk through files
        for root, dirs, files in os.walk("."):
            # Filter directories on the fly
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]

            # Additional filtering for dot-directories
            dirs[:] = [d for d in dirs if not d.startswith(".")]

            for file in files:
                if not should_include_file(os.path.join(root, file), file):
                    continue

                path = os.path.join(root, file)

                # Normalize path for platform consistency
                path = os.path.normpath(path)

                # Skip the output file itself
                if path == output_file or path == os.path.normpath(output_file):
                    continue

                # Write file header
                outfile.write(f"\n{'=' * 80}\n")
                outfile.write(f"FILE: {path}\n")
                outfile.write(f"{'=' * 80}\n\n")

                try:
                    # Check file size (skip files larger than 1MB)
                    file_size = os.path.getsize(path)
                    if file_size > 1_000_000:
                        outfile.write(f"[File too large: {file_size} bytes, skipped]\n")
                        continue

                    with open(path, encoding="utf-8", errors="ignore") as infile:
                        content = infile.read()
                        outfile.write(content)
                        if not content.endswith("\n"):
                            outfile.write("\n")

                    file_count += 1
                    total_size += file_size

                except Exception as e:
                    outfile.write(f"[Error reading file: {e}]\n")

        # Summary statistics
        outfile.write(f"\n\n{'=' * 80}\n")
        outfile.write("STATISTICS\n")
        outfile.write(f"{'=' * 80}\n")
        outfile.write(f"Files processed: {file_count}\n")
        outfile.write(f"Total size: {total_size:,} bytes ({total_size / 1024:.2f} KB)\n")

    print(f"Done. File {output_file} created.")
    print(f"Files processed: {file_count}")
    print(f"Total size: {total_size:,} bytes ({total_size / 1024:.2f} KB)")


if __name__ == "__main__":
    generate_context()
