"""Test fixtures and configuration."""

import os

# Set test environment BEFORE importing any app modules
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")
os.environ.setdefault("VOYAGE_API_KEY", "test-key")
os.environ.setdefault("SUPABASE_URL", "http://test")
os.environ.setdefault("SUPABASE_ANON_KEY", "test-anon")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "test-service")
os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/test")
os.environ.setdefault("JWT_SECRET", "test-jwt-secret-min-32-chars-for-tests")
