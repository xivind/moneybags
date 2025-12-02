# Helpers for gas gauge application

import uuid
from datetime import datetime


def generate_canister_id():
    """
    Generate unique canister ID using UUID + timestamp.
    Format: GC-{uuid[:6]}{timestamp[-4:]}
    Example: GC-a3f8e52468
    """
    uuid_part = uuid.uuid4().hex[:6]
    timestamp_part = str(int(datetime.now().timestamp()))[-4:]
    return f"GC-{uuid_part}{timestamp_part}"

def empty_to_none(value):
    """Convert empty string or whitespace-only string to None.

    This ensures we store NULL in the database instead of empty strings,
    maintaining data integrity and query consistency.

    Args:
        value: Any value, typically a string from form input

    Returns:
        None if value is empty/whitespace/None, otherwise the value
    """
    if value is None:
        return None
    if isinstance(value, str) and not value.strip():
        return None
    return value
