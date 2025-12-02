import pytest
from app.utils import generate_uuid


def test_generate_uuid_returns_string():
    """UUID should be returned as string."""
    uuid = generate_uuid()
    assert isinstance(uuid, str)


def test_generate_uuid_is_unique():
    """Each call should generate unique UUID."""
    uuid1 = generate_uuid()
    uuid2 = generate_uuid()
    assert uuid1 != uuid2


def test_generate_uuid_format():
    """UUID should be in correct format (8-4-4-4-12 hex)."""
    uuid = generate_uuid()
    parts = uuid.split('-')
    assert len(parts) == 5
    assert len(parts[0]) == 8
    assert len(parts[1]) == 4
    assert len(parts[2]) == 4
    assert len(parts[3]) == 4
    assert len(parts[4]) == 12
