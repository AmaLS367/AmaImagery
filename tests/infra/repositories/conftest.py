"""Repository test configuration.

Repository tests use the dedicated ``test_db_session`` fixture from the root
test harness, so this module intentionally avoids mutating process-wide
database settings during collection.
"""

