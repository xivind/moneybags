import pytest
from datetime import date
from peewee import SqliteDatabase
from app.database_model import (
    Post, Tag, PostTag, BudgetEntry, ActualEntry, UserPreference,
    db
)
from app.database_manager import (
    create_post, get_post, get_all_posts, update_post, delete_post,
    create_tag, get_tag_by_name, get_all_tags,
    add_tag_to_post, get_post_tags, remove_tag_from_post,
    create_budget_entry, get_budget_entries, update_budget_entry,
    create_actual_entry, get_actual_entries, update_actual_entry, delete_actual_entry,
    get_or_create_preference, update_preference
)


@pytest.fixture(autouse=True)
def test_db():
    """Setup test database before each test."""
    test_database = SqliteDatabase(':memory:')
    models = [Post, Tag, PostTag, BudgetEntry, ActualEntry, UserPreference]
    test_database.bind(models)
    test_database.create_tables(models)
    yield
    test_database.close()


class TestPostOperations:
    def test_create_post(self):
        """Should create a new post."""
        post_id = 'test-post-1'
        post = create_post(post_id, 'Rent', 'expense')

        assert post.id == post_id
        assert post.name == 'Rent'
        assert post.type == 'expense'

    def test_get_post(self):
        """Should retrieve existing post."""
        post_id = 'test-post-1'
        create_post(post_id, 'Salary', 'income')

        post = get_post(post_id)
        assert post is not None
        assert post.name == 'Salary'

    def test_get_all_posts(self):
        """Should retrieve all posts."""
        create_post('post-1', 'Rent', 'expense')
        create_post('post-2', 'Salary', 'income')

        posts = get_all_posts()
        assert len(posts) == 2

    def test_update_post(self):
        """Should update post name."""
        post_id = 'test-post-1'
        create_post(post_id, 'Netflix', 'expense')

        updated = update_post(post_id, name='Netflix + Disney+')
        assert updated.name == 'Netflix + Disney+'

    def test_delete_post(self):
        """Should delete post."""
        post_id = 'test-post-1'
        create_post(post_id, 'Old Post', 'expense')

        delete_post(post_id)
        post = get_post(post_id)
        assert post is None


class TestTagOperations:
    def test_create_tag(self):
        """Should create a new tag."""
        tag_id = 'tag-1'
        tag = create_tag(tag_id, 'Housing')

        assert tag.id == tag_id
        assert tag.name == 'Housing'

    def test_get_tag_by_name(self):
        """Should retrieve tag by name."""
        create_tag('tag-1', 'Streaming')

        tag = get_tag_by_name('Streaming')
        assert tag is not None
        assert tag.name == 'Streaming'

    def test_get_all_tags(self):
        """Should retrieve all tags."""
        create_tag('tag-1', 'Housing')
        create_tag('tag-2', 'Food')

        tags = get_all_tags()
        assert len(tags) == 2


class TestPostTagRelationship:
    def test_add_tag_to_post(self):
        """Should link tag to post."""
        post = create_post('post-1', 'Rent', 'expense')
        tag = create_tag('tag-1', 'Housing')

        add_tag_to_post(post.id, tag.id)

        post_tags = get_post_tags(post.id)
        assert len(post_tags) == 1
        assert post_tags[0].name == 'Housing'

    def test_remove_tag_from_post(self):
        """Should unlink tag from post."""
        post = create_post('post-1', 'Rent', 'expense')
        tag = create_tag('tag-1', 'Housing')
        add_tag_to_post(post.id, tag.id)

        remove_tag_from_post(post.id, tag.id)

        post_tags = get_post_tags(post.id)
        assert len(post_tags) == 0


class TestBudgetEntryOperations:
    def test_create_budget_entry(self):
        """Should create budget entry."""
        post = create_post('post-1', 'Rent', 'expense')
        entry_id = 'budget-1'

        entry = create_budget_entry(entry_id, post.id, 2024, 1, 1500.00)

        assert entry.year == 2024
        assert entry.month == 1
        assert float(entry.amount) == 1500.00

    def test_get_budget_entries(self):
        """Should retrieve budget entries for post and year."""
        post = create_post('post-1', 'Rent', 'expense')
        create_budget_entry('b1', post.id, 2024, 1, 1500.00)
        create_budget_entry('b2', post.id, 2024, 2, 1500.00)
        create_budget_entry('b3', post.id, 2025, 1, 1600.00)

        entries = get_budget_entries(post.id, 2024)
        assert len(entries) == 2

    def test_update_budget_entry(self):
        """Should update budget amount."""
        post = create_post('post-1', 'Rent', 'expense')
        entry = create_budget_entry('b1', post.id, 2024, 1, 1500.00)

        updated = update_budget_entry(entry.id, amount=1600.00)
        assert float(updated.amount) == 1600.00


class TestActualEntryOperations:
    def test_create_actual_entry(self):
        """Should create actual entry with date and comment."""
        post = create_post('post-1', 'Rent', 'expense')
        entry_id = 'actual-1'
        entry_date = date(2024, 1, 15)

        entry = create_actual_entry(
            entry_id, post.id, entry_date, 1500.00, 'January rent'
        )

        assert entry.date == entry_date
        assert float(entry.amount) == 1500.00
        assert entry.comment == 'January rent'

    def test_get_actual_entries(self):
        """Should retrieve actual entries for post and date range."""
        post = create_post('post-1', 'Groceries', 'expense')
        create_actual_entry('a1', post.id, date(2024, 1, 5), 100.00, '')
        create_actual_entry('a2', post.id, date(2024, 1, 15), 120.00, '')
        create_actual_entry('a3', post.id, date(2024, 2, 5), 110.00, '')

        entries = get_actual_entries(
            post.id,
            date(2024, 1, 1),
            date(2024, 1, 31)
        )
        assert len(entries) == 2

    def test_update_actual_entry(self):
        """Should update actual entry amount and comment."""
        post = create_post('post-1', 'Groceries', 'expense')
        entry = create_actual_entry('a1', post.id, date(2024, 1, 5), 100.00, '')

        updated = update_actual_entry(entry.id, amount=105.00, comment='Updated')
        assert float(updated.amount) == 105.00
        assert updated.comment == 'Updated'

    def test_delete_actual_entry(self):
        """Should delete actual entry."""
        post = create_post('post-1', 'Groceries', 'expense')
        entry = create_actual_entry('a1', post.id, date(2024, 1, 5), 100.00, '')

        delete_actual_entry(entry.id)

        entries = get_actual_entries(post.id, date(2024, 1, 1), date(2024, 12, 31))
        assert len(entries) == 0


class TestUserPreferenceOperations:
    def test_get_or_create_preference(self):
        """Should create preference if not exists."""
        pref = get_or_create_preference('currency_notation', 'USD')

        assert pref.key == 'currency_notation'
        assert pref.value == 'USD'

    def test_update_preference(self):
        """Should update existing preference."""
        get_or_create_preference('currency_notation', 'USD')

        updated = update_preference('currency_notation', 'NOK')
        assert updated.value == 'NOK'
