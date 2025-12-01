import pytest
from peewee import SqliteDatabase
from app.database_model import (
    Post, Tag, PostTag, BudgetEntry, ActualEntry, UserPreference,
    initialize_database
)


@pytest.fixture
def test_db():
    """Create in-memory test database."""
    test_database = SqliteDatabase(':memory:')
    models = [Post, Tag, PostTag, BudgetEntry, ActualEntry, UserPreference]
    test_database.bind(models)
    test_database.create_tables(models)
    yield test_database
    test_database.close()


def test_post_model_creation(test_db):
    """Post model should create and retrieve records."""
    post = Post.create(
        id='test-uuid-1',
        name='Test Post',
        type='expense'
    )
    assert post.id == 'test-uuid-1'
    assert post.name == 'Test Post'
    assert post.type == 'expense'


def test_tag_model_creation(test_db):
    """Tag model should create and retrieve records."""
    tag = Tag.create(
        id='tag-uuid-1',
        name='Housing'
    )
    assert tag.id == 'tag-uuid-1'
    assert tag.name == 'Housing'


def test_post_tag_relationship(test_db):
    """PostTag should link posts and tags."""
    post = Post.create(id='post-1', name='Rent', type='expense')
    tag = Tag.create(id='tag-1', name='Housing')
    post_tag = PostTag.create(post=post, tag=tag)

    assert post_tag.post_id == 'post-1'
    assert post_tag.tag_id == 'tag-1'


def test_budget_entry_model(test_db):
    """BudgetEntry should store monthly budget values."""
    post = Post.create(id='post-1', name='Rent', type='expense')
    entry = BudgetEntry.create(
        id='budget-1',
        post=post,
        year=2024,
        month=1,
        amount=1500.00
    )

    assert entry.year == 2024
    assert entry.month == 1
    assert float(entry.amount) == 1500.00


def test_actual_entry_model(test_db):
    """ActualEntry should store dated transactions with comments."""
    from datetime import date

    post = Post.create(id='post-1', name='Rent', type='expense')
    entry = ActualEntry.create(
        id='actual-1',
        post=post,
        date=date(2024, 1, 15),
        amount=1500.00,
        comment='January rent payment'
    )

    assert entry.date == date(2024, 1, 15)
    assert float(entry.amount) == 1500.00
    assert entry.comment == 'January rent payment'


def test_user_preference_model(test_db):
    """UserPreference should store key-value configuration."""
    pref = UserPreference.create(
        id='pref-1',
        key='currency_notation',
        value='NOK'
    )

    assert pref.key == 'currency_notation'
    assert pref.value == 'NOK'
