"""Test bootstrap — allow the app to import without a live MySQL instance."""

import os

os.environ.setdefault("ALLOW_DB_FAILURE", "true")
os.environ.setdefault("DEBUG", "true")
