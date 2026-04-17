import os

# Use in-memory SQLite so tests can run from root without Docker paths
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
