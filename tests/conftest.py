"""
Test configuration and fixtures.
"""
from uuid import UUID
from typing import Optional


class MockUser:
    """Mock user for testing."""

    def __init__(self, id: UUID, is_superuser: bool = False, email: Optional[str] = None):
        self.id = id
        self.is_superuser = is_superuser
        self.email = email or f"user_{id}@test.com"
