"""Utility functions for Moneybags application."""
import uuid


def generate_uuid() -> str:
    """
    Generate a unique UUID string.

    Returns:
        str: UUID in string format (e.g., "a1b2c3d4-e5f6-7890-abcd-ef1234567890")
    """
    return str(uuid.uuid4())
