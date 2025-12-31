"""
Supersaver business logic.

Validation, business rules, and data preparation for supersaver entries.
Follows same patterns as business_logic.py but in separate module.

Key responsibilities:
- Validate all inputs before passing to database
- Generate UUIDs and timestamps
- Convert empty strings to NULL
- Calculate balances and summaries
- Format data for API responses
"""

import logging
from datetime import datetime, date
from typing import Optional
from utils import generate_uid, empty_to_none, validate_date_format
import supersaver_database_manager as ssdb

logger = logging.getLogger(__name__)


# ==================== SUPERSAVER CATEGORY LOGIC ====================

def create_supersaver_category(name: str) -> dict:
    """
    Create new supersaver category.

    Business logic:
    - Validate name not empty
    - Check uniqueness (case-insensitive)
    - Generate UUID and timestamp
    """
    try:
        if not name or not name.strip():
            raise ValueError("Category name is required")

        name = name.strip()

        # Check uniqueness
        if ssdb.supersaver_category_exists_by_name(name):
            raise ValueError(f"Supersaver category '{name}' already exists")

        category_data = {
            'id': generate_uid(),
            'name': name,
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }

        category = ssdb.create_supersaver_category(category_data)
        logger.info(f"Business logic: Created supersaver category {name}")

        return {
            'id': category.id,
            'name': category.name
        }
    except Exception as e:
        logger.error(f"Failed to create supersaver category: {e}")
        raise


def get_all_supersaver_categories() -> list:
    """Get all supersaver categories with balance and usage stats."""
    try:
        categories = ssdb.get_all_supersaver_categories()
        result = []

        for cat in categories:
            entry_count = ssdb.supersaver_entry_count_by_category(cat.id)
            balance = ssdb.get_supersaver_balance(cat.id)

            result.append({
                'id': cat.id,
                'name': cat.name,
                'entry_count': entry_count,
                'balance': balance
            })

        return result
    except Exception as e:
        logger.error(f"Failed to get supersaver categories: {e}")
        raise


def update_supersaver_category(category_id: str, name: str) -> dict:
    """
    Update supersaver category (rename only).

    Business logic:
    - Validate category exists
    - Validate new name not empty
    - Check uniqueness (unless name unchanged)
    """
    try:
        category = ssdb.get_supersaver_category_by_id(category_id)
        if not category:
            raise ValueError(f"Supersaver category {category_id} not found")

        if not name or not name.strip():
            raise ValueError("Category name is required")

        name = name.strip()

        # Check uniqueness (skip if name unchanged)
        if name.lower() != category.name.lower():
            if ssdb.supersaver_category_exists_by_name(name):
                raise ValueError(f"Supersaver category '{name}' already exists")

        updated_category = ssdb.update_supersaver_category(
            category_id,
            {'name': name, 'updated_at': datetime.now()}
        )
        logger.info(f"Business logic: Updated supersaver category {category_id}")

        return {
            'id': updated_category.id,
            'name': updated_category.name
        }
    except Exception as e:
        logger.error(f"Failed to update supersaver category: {e}")
        raise


def delete_supersaver_category(category_id: str) -> None:
    """
    Delete supersaver category.

    Business logic:
    - Validate category exists
    - Check NOT in use (no entries reference it)
    """
    try:
        category = ssdb.get_supersaver_category_by_id(category_id)
        if not category:
            raise ValueError(f"Supersaver category {category_id} not found")

        # Check usage
        if ssdb.supersaver_category_has_entries(category_id):
            raise ValueError(
                f"Cannot delete category '{category.name}' - it has supersaver entries"
            )

        ssdb.delete_supersaver_category(category_id)
        logger.info(f"Business logic: Deleted supersaver category {category_id}")
    except Exception as e:
        logger.error(f"Failed to delete supersaver category: {e}")
        raise


# ==================== SUPERSAVER ENTRY LOGIC ====================

def create_supersaver_entry(
    category_id: str,
    amount: int,
    date_str: str,
    comment: Optional[str] = None
) -> dict:
    """
    Create supersaver entry (savings deposit).

    Business logic:
    - Validate category exists
    - Validate amount >= 0
    - Validate date format
    - Convert empty comment to NULL
    - Generate UUID and timestamp
    """
    try:
        # Validate category
        category = ssdb.get_supersaver_category_by_id(category_id)
        if not category:
            raise ValueError(f"Supersaver category {category_id} not found")

        # Validate amount
        if not isinstance(amount, int) or amount < 0:
            raise ValueError("Amount must be a non-negative integer")

        # Validate date
        if not validate_date_format(date_str):
            raise ValueError("Date must be in YYYY-MM-DD format")

        # Convert empty comment to NULL
        comment = empty_to_none(comment)

        entry_data = {
            'id': generate_uid(),
            'category_id': category_id,
            'amount': amount,
            'date': date_str,
            'comment': comment,
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }

        entry = ssdb.create_supersaver_entry(entry_data)
        logger.info(f"Business logic: Created supersaver entry {amount} to {category.name}")

        return {
            'id': entry.id,
            'category_id': entry.category_id,
            'category_name': category.name,
            'amount': entry.amount,
            'date': str(entry.date),
            'comment': entry.comment
        }
    except Exception as e:
        logger.error(f"Failed to create supersaver entry: {e}")
        raise


def update_supersaver_entry(
    entry_id: str,
    category_id: str,
    amount: int,
    date_str: str,
    comment: Optional[str] = None
) -> dict:
    """Update supersaver entry."""
    try:
        entry = ssdb.get_supersaver_entry_by_id(entry_id)
        if not entry:
            raise ValueError(f"Supersaver entry {entry_id} not found")

        # Validate category
        category = ssdb.get_supersaver_category_by_id(category_id)
        if not category:
            raise ValueError(f"Supersaver category {category_id} not found")

        # Validate amount
        if not isinstance(amount, int) or amount < 0:
            raise ValueError("Amount must be a non-negative integer")

        # Validate date
        if not validate_date_format(date_str):
            raise ValueError("Date must be in YYYY-MM-DD format")

        comment = empty_to_none(comment)

        update_data = {
            'category_id': category_id,
            'amount': amount,
            'date': date_str,
            'comment': comment,
            'updated_at': datetime.now()
        }

        updated_entry = ssdb.update_supersaver_entry(entry_id, update_data)
        logger.info(f"Business logic: Updated supersaver entry {entry_id}")

        return {
            'id': updated_entry.id,
            'category_id': updated_entry.category_id,
            'category_name': category.name,
            'amount': updated_entry.amount,
            'date': str(updated_entry.date),
            'comment': updated_entry.comment
        }
    except Exception as e:
        logger.error(f"Failed to update supersaver entry: {e}")
        raise


def delete_supersaver_entry(entry_id: str) -> None:
    """Delete supersaver entry."""
    try:
        entry = ssdb.get_supersaver_entry_by_id(entry_id)
        if not entry:
            raise ValueError(f"Supersaver entry {entry_id} not found")

        ssdb.delete_supersaver_entry(entry_id)
        logger.info(f"Business logic: Deleted supersaver entry {entry_id}")
    except Exception as e:
        logger.error(f"Failed to delete supersaver entry: {e}")
        raise


def get_supersaver_entries_for_month(
    category_id: str,
    year: int,
    month: int
) -> list:
    """
    Get all supersaver entries for category/year/month.

    Returns list organized by entry with type and amount.
    """
    try:
        category = ssdb.get_supersaver_category_by_id(category_id)
        if not category:
            raise ValueError(f"Supersaver category {category_id} not found")

        entries = ssdb.get_supersaver_entries_by_category_month(
            category_id, year, month
        )

        result = []
        for e in entries:
            result.append({
                'id': e.id,
                'category_id': e.category_id,
                'category_name': category.name,
                'amount': e.amount,
                'date': str(e.date),
                'comment': e.comment
            })

        return result
    except Exception as e:
        logger.error(f"Failed to get supersaver entries for month: {e}")
        raise


def get_supersaver_heatmap_year(year: int) -> dict:
    """
    Get daily heatmap data for entire year (all categories, deposits only).

    Returns deposits aggregated by date.
    Format:
    {
        'year': 2025,
        'days': {
            '2025-01-15': 50000,
            '2025-01-16': 125000,
            ...
        },
        'total_saved': 500000
    }
    """
    try:
        # Get all entries for the year (all categories)
        all_entries = ssdb.get_all_supersaver_entries_for_year(year)

        # Aggregate deposits by date
        days = {}
        total_saved = 0

        for entry in all_entries:
            date_str = str(entry.date)
            if date_str not in days:
                days[date_str] = 0
            days[date_str] += entry.amount
            total_saved += entry.amount

        return {
            'year': year,
            'days': days,
            'total_saved': total_saved
        }
    except Exception as e:
        logger.error(f"Failed to get supersaver heatmap: {e}")
        raise


def get_supersaver_dashboard_summary(year: int = None) -> dict:
    """
    Get supersaver summary for dashboard widget.

    Returns aggregated data across all categories for current month and year.
    Includes trend comparison with previous month.
    """
    try:
        if year is None:
            year = datetime.now().year

        current_month = datetime.now().month
        current_year = datetime.now().year

        # Get all entries for current year
        all_entries_current_year = ssdb.get_all_supersaver_entries_for_year(current_year)

        # Calculate this month savings (deposits only, no withdrawals)
        this_month_deposits = 0
        this_year_deposits = 0

        for entry in all_entries_current_year:
            this_year_deposits += entry.amount
            if entry.date.month == current_month:
                this_month_deposits += entry.amount

        # Calculate previous month for trend
        if current_month == 1:
            prev_month = 12
            prev_year = current_year - 1
        else:
            prev_month = current_month - 1
            prev_year = current_year

        all_entries_prev_year = ssdb.get_all_supersaver_entries_for_year(prev_year)
        prev_month_deposits = 0

        for entry in all_entries_prev_year:
            if entry.date.month == prev_month:
                prev_month_deposits += entry.amount

        # Determine trend
        if this_month_deposits > prev_month_deposits:
            month_trend = 'up'
        elif this_month_deposits < prev_month_deposits:
            month_trend = 'down'
        else:
            month_trend = 'same'

        return {
            'saved_this_month': this_month_deposits,
            'saved_this_year': this_year_deposits,
            'month_trend': month_trend
        }
    except Exception as e:
        logger.error(f"Failed to get supersaver dashboard summary: {e}")
        raise
