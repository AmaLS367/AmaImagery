"""
Test configuration for repository integration tests.

Sets up SQLite database before models are imported.
"""

import os

# Set SQLite before any model imports
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

