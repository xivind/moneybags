# Helpers for Moneybags application

import uuid
from datetime import datetime, date


def generate_uid():
    """
    Generate unique record ID using UUID + timestamp.
    """
    uuid_part = uuid.uuid4().hex[:6]
    timestamp_part = str(int(datetime.now().timestamp()))[-4:]
    return f"{uuid_part}{timestamp_part}"


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


def validate_date_format(date_str: str) -> bool:
    """
    Validate date string is in YYYY-MM-DD format.

    Returns True if valid, False otherwise.
    """
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
        return True
    except (ValueError, TypeError):
        return False


def validate_month(month: int) -> bool:
    """Validate month is 1-12."""
    return isinstance(month, int) and 1 <= month <= 12


def validate_year(year: int) -> bool:
    """Validate year is reasonable (1900-2100)."""
    return isinstance(year, int) and 1900 <= year <= 2100


def get_month_date_range(year: int, month: int) -> tuple:
    """
    Get start and end dates for a month.

    Returns (start_date, end_date) as date objects.
    """
    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1)
    else:
        end_date = date(year, month + 1, 1)
    return (start_date, end_date)
