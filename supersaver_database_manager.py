"""
Supersaver database CRUD operations.

Pure CRUD functions - no validation or business logic.
All validation happens in supersaver_business_logic.py.

Follows same patterns as database_manager.py:
- Uses @with_transaction for write operations
- Uses @with_retry for read operations
- Raises exceptions on errors (handled by business logic layer)
"""

import logging
from datetime import date
from peewee import DoesNotExist, fn
from database_model import SupersaverCategory, Supersaver
import database_manager as db

logger = logging.getLogger(__name__)


# ==================== SUPERSAVER CATEGORY CRUD ====================

@db.with_transaction
def create_supersaver_category(data: dict) -> SupersaverCategory:
    """Create supersaver category with provided data dict."""
    category = SupersaverCategory(**data)
    category.save(force_insert=True)
    logger.info(f"Created supersaver category: {category.name} ({category.id})")
    return category


@db.with_retry
def get_supersaver_category_by_id(category_id: str) -> SupersaverCategory:
    """Get supersaver category by ID. Returns None if not found."""
    try:
        return SupersaverCategory.get(SupersaverCategory.id == category_id)
    except DoesNotExist:
        return None


@db.with_retry
def get_all_supersaver_categories() -> list:
    """Get all supersaver categories ordered by name."""
    return list(SupersaverCategory.select().order_by(SupersaverCategory.name))


@db.with_retry
def supersaver_category_exists_by_name(name: str) -> bool:
    """Check if supersaver category with name exists (case-insensitive)."""
    return SupersaverCategory.select().where(
        SupersaverCategory.name.ilike(name)
    ).exists()


@db.with_transaction
def update_supersaver_category(category_id: str, data: dict) -> SupersaverCategory:
    """Update supersaver category fields."""
    category = SupersaverCategory.get(SupersaverCategory.id == category_id)
    for key, value in data.items():
        setattr(category, key, value)
    category.save()
    logger.info(f"Updated supersaver category: {category.name} ({category.id})")
    return category


@db.with_transaction
def delete_supersaver_category(category_id: str) -> None:
    """Delete supersaver category by ID."""
    category = SupersaverCategory.get(SupersaverCategory.id == category_id)
    category_name = category.name
    category.delete_instance()
    logger.info(f"Deleted supersaver category: {category_name} ({category_id})")


@db.with_retry
def supersaver_category_has_entries(category_id: str) -> bool:
    """Check if category has any supersaver entries."""
    return Supersaver.select().where(
        Supersaver.category_id == category_id
    ).exists()


# ==================== SUPERSAVER ENTRY CRUD ====================

@db.with_transaction
def create_supersaver_entry(data: dict) -> Supersaver:
    """Create supersaver entry with provided data dict."""
    entry = Supersaver(**data)
    entry.save(force_insert=True)
    logger.info(f"Created supersaver entry: {entry.amount} ({entry.id})")
    return entry


@db.with_retry
def get_supersaver_entry_by_id(entry_id: str) -> Supersaver:
    """Get supersaver entry by ID. Returns None if not found."""
    try:
        return Supersaver.get(Supersaver.id == entry_id)
    except DoesNotExist:
        return None


@db.with_retry
def get_supersaver_entries_by_category_month(
    category_id: str,
    year: int,
    month: int
) -> list:
    """Get supersaver entries for category/year/month."""
    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1)
    else:
        end_date = date(year, month + 1, 1)

    return list(Supersaver.select().where(
        (Supersaver.category_id == category_id) &
        (Supersaver.date >= start_date) &
        (Supersaver.date < end_date)
    ).order_by(Supersaver.date.desc()))


@db.with_transaction
def update_supersaver_entry(entry_id: str, data: dict) -> Supersaver:
    """Update supersaver entry fields."""
    entry = Supersaver.get(Supersaver.id == entry_id)
    for key, value in data.items():
        setattr(entry, key, value)
    entry.save()
    logger.info(f"Updated supersaver entry: {entry_id}")
    return entry


@db.with_transaction
def delete_supersaver_entry(entry_id: str) -> None:
    """Delete supersaver entry by ID."""
    entry = Supersaver.get(Supersaver.id == entry_id)
    entry.delete_instance()
    logger.info(f"Deleted supersaver entry: {entry_id}")


@db.with_retry
def supersaver_entry_count_by_category(category_id: str) -> int:
    """Count entries for supersaver category."""
    return Supersaver.select().where(
        Supersaver.category_id == category_id
    ).count()


@db.with_retry
def get_supersaver_balance(category_id: str) -> int:
    """
    Get current balance for category (total deposits).

    Returns 0 if no entries exist.
    """
    total = (Supersaver
             .select(fn.SUM(Supersaver.amount))
             .where(Supersaver.category_id == category_id)
             .scalar()) or 0

    return total


@db.with_retry
def get_all_supersaver_entries_for_year(year: int) -> list:
    """Get all supersaver entries across all categories for a given year."""
    start_date = date(year, 1, 1)
    end_date = date(year + 1, 1, 1)

    return list(Supersaver.select().where(
        (Supersaver.date >= start_date) &
        (Supersaver.date < end_date)
    ).order_by(Supersaver.date.desc()))
