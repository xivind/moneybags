"""Database manager for all CRUD operations using PeeWee ORM."""
from typing import List, Optional
from datetime import date, datetime
from app.database_model import (
    Post, Tag, PostTag, BudgetEntry, ActualEntry, UserPreference
)


# ============================================================================
# POST OPERATIONS
# ============================================================================

def create_post(post_id: str, name: str, post_type: str) -> Post:
    """
    Create a new post.

    Args:
        post_id: Unique identifier
        name: Post name (e.g., "Rent", "Salary")
        post_type: Either 'income' or 'expense'

    Returns:
        Post: Created post object
    """
    return Post.create(
        id=post_id,
        name=name,
        type=post_type
    )


def get_post(post_id: str) -> Optional[Post]:
    """
    Retrieve a post by ID.

    Args:
        post_id: Post identifier

    Returns:
        Post or None if not found
    """
    try:
        return Post.get_by_id(post_id)
    except Post.DoesNotExist:
        return None


def get_all_posts() -> List[Post]:
    """
    Retrieve all posts.

    Returns:
        List of Post objects
    """
    return list(Post.select())


def update_post(post_id: str, name: Optional[str] = None) -> Post:
    """
    Update a post's name.

    Args:
        post_id: Post identifier
        name: New name (optional)

    Returns:
        Updated Post object
    """
    post = Post.get_by_id(post_id)
    if name is not None:
        post.name = name
        post.updated_at = datetime.now()
        post.save()
    return post


def delete_post(post_id: str) -> None:
    """
    Delete a post and all related data.

    WARNING: This cascades to delete all associated:
    - Post-Tag relationships
    - Budget entries
    - Actual entries

    Args:
        post_id: Post identifier
    """
    # Delete related records first
    PostTag.delete().where(PostTag.post == post_id).execute()
    BudgetEntry.delete().where(BudgetEntry.post == post_id).execute()
    ActualEntry.delete().where(ActualEntry.post == post_id).execute()

    # Then delete the post
    post = Post.get_by_id(post_id)
    post.delete_instance()


# ============================================================================
# TAG OPERATIONS
# ============================================================================

def create_tag(tag_id: str, name: str) -> Tag:
    """
    Create a new tag.

    Args:
        tag_id: Unique identifier
        name: Tag name (e.g., "Housing", "Fixed")

    Returns:
        Tag: Created tag object
    """
    return Tag.create(id=tag_id, name=name)


def get_tag_by_name(name: str) -> Optional[Tag]:
    """
    Retrieve a tag by name.

    Args:
        name: Tag name

    Returns:
        Tag or None if not found
    """
    try:
        return Tag.get(Tag.name == name)
    except Tag.DoesNotExist:
        return None


def get_all_tags() -> List[Tag]:
    """
    Retrieve all tags.

    Returns:
        List of Tag objects
    """
    return list(Tag.select())


# ============================================================================
# POST-TAG RELATIONSHIP OPERATIONS
# ============================================================================

def add_tag_to_post(post_id: str, tag_id: str) -> PostTag:
    """
    Link a tag to a post.

    Args:
        post_id: Post identifier
        tag_id: Tag identifier

    Returns:
        PostTag: Created relationship
    """
    return PostTag.create(post=post_id, tag=tag_id)


def get_post_tags(post_id: str) -> List[Tag]:
    """
    Get all tags for a post.

    Args:
        post_id: Post identifier

    Returns:
        List of Tag objects
    """
    post_tags = PostTag.select().where(PostTag.post == post_id)
    return [pt.tag for pt in post_tags]


def remove_tag_from_post(post_id: str, tag_id: str) -> None:
    """
    Remove tag from post.

    Args:
        post_id: Post identifier
        tag_id: Tag identifier
    """
    PostTag.delete().where(
        (PostTag.post == post_id) & (PostTag.tag == tag_id)
    ).execute()


# ============================================================================
# BUDGET ENTRY OPERATIONS
# ============================================================================

def create_budget_entry(
    entry_id: str,
    post_id: str,
    year: int,
    month: int,
    amount: float
) -> BudgetEntry:
    """
    Create a budget entry.

    Args:
        entry_id: Unique identifier
        post_id: Post identifier
        year: Budget year (e.g., 2024)
        month: Budget month (1-12)
        amount: Budgeted amount

    Returns:
        BudgetEntry: Created entry
    """
    return BudgetEntry.create(
        id=entry_id,
        post=post_id,
        year=year,
        month=month,
        amount=amount
    )


def get_budget_entries(post_id: str, year: int) -> List[BudgetEntry]:
    """
    Get all budget entries for a post and year.

    Args:
        post_id: Post identifier
        year: Budget year

    Returns:
        List of BudgetEntry objects
    """
    return list(
        BudgetEntry.select().where(
            (BudgetEntry.post == post_id) & (BudgetEntry.year == year)
        ).order_by(BudgetEntry.month)
    )


def update_budget_entry(
    entry_id: str,
    amount: Optional[float] = None
) -> BudgetEntry:
    """
    Update a budget entry.

    Args:
        entry_id: Entry identifier
        amount: New amount (optional)

    Returns:
        Updated BudgetEntry object
    """
    entry = BudgetEntry.get_by_id(entry_id)
    if amount is not None:
        entry.amount = amount
        entry.updated_at = datetime.now()
        entry.save()
    return entry


# ============================================================================
# ACTUAL ENTRY OPERATIONS
# ============================================================================

def create_actual_entry(
    entry_id: str,
    post_id: str,
    entry_date: date,
    amount: float,
    comment: str = ''
) -> ActualEntry:
    """
    Create an actual entry.

    Args:
        entry_id: Unique identifier
        post_id: Post identifier
        entry_date: Date of transaction
        amount: Actual amount
        comment: Optional comment

    Returns:
        ActualEntry: Created entry
    """
    return ActualEntry.create(
        id=entry_id,
        post=post_id,
        date=entry_date,
        amount=amount,
        comment=comment if comment else None
    )


def get_actual_entries(
    post_id: str,
    start_date: date,
    end_date: date
) -> List[ActualEntry]:
    """
    Get actual entries for a post within date range.

    Args:
        post_id: Post identifier
        start_date: Start of date range (inclusive)
        end_date: End of date range (inclusive)

    Returns:
        List of ActualEntry objects
    """
    return list(
        ActualEntry.select().where(
            (ActualEntry.post == post_id) &
            (ActualEntry.date >= start_date) &
            (ActualEntry.date <= end_date)
        ).order_by(ActualEntry.date.desc())
    )


def update_actual_entry(
    entry_id: str,
    amount: Optional[float] = None,
    comment: Optional[str] = None
) -> ActualEntry:
    """
    Update an actual entry.

    Args:
        entry_id: Entry identifier
        amount: New amount (optional)
        comment: New comment (optional)

    Returns:
        Updated ActualEntry object
    """
    entry = ActualEntry.get_by_id(entry_id)
    if amount is not None:
        entry.amount = amount
    if comment is not None:
        entry.comment = comment
    entry.updated_at = datetime.now()
    entry.save()
    return entry


def delete_actual_entry(entry_id: str) -> None:
    """
    Delete an actual entry.

    Args:
        entry_id: Entry identifier
    """
    entry = ActualEntry.get_by_id(entry_id)
    entry.delete_instance()


# ============================================================================
# USER PREFERENCE OPERATIONS
# ============================================================================

def get_or_create_preference(key: str, default_value: str) -> UserPreference:
    """
    Get existing preference or create with default.

    Args:
        key: Preference key
        default_value: Default value if not exists

    Returns:
        UserPreference object
    """
    try:
        return UserPreference.get(UserPreference.key == key)
    except UserPreference.DoesNotExist:
        from app.utils import generate_uuid
        return UserPreference.create(
            id=generate_uuid(),
            key=key,
            value=default_value
        )


def update_preference(key: str, value: str) -> UserPreference:
    """
    Update a preference value.

    Args:
        key: Preference key
        value: New value

    Returns:
        Updated UserPreference object
    """
    pref = UserPreference.get(UserPreference.key == key)
    pref.value = value
    pref.save()
    return pref
