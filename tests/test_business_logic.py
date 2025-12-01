import pytest
from datetime import date
from decimal import Decimal
from peewee import SqliteDatabase
from app.database_model import db, Post, Tag, PostTag, BudgetEntry, ActualEntry
from app.database_manager import (
    create_post, create_tag, add_tag_to_post,
    create_budget_entry, create_actual_entry
)
from app.business_logic import (
    create_post_with_tags,
    get_monthly_variance,
    get_year_overview,
    get_posts_by_type,
    calculate_post_total_actual
)


@pytest.fixture(autouse=True)
def test_db():
    """Setup test database."""
    test_database = SqliteDatabase(':memory:')
    models = [Post, Tag, PostTag, BudgetEntry, ActualEntry]
    test_database.bind(models)
    test_database.create_tables(models)
    yield
    test_database.close()


def test_create_post_with_tags():
    """Should create post and link tags in one operation."""
    from app.utils import generate_uuid

    tag1_id = generate_uuid()
    tag2_id = generate_uuid()
    create_tag(tag1_id, 'Housing')
    create_tag(tag2_id, 'Fixed')

    post = create_post_with_tags('Rent', 'expense', [tag1_id, tag2_id])

    assert post.name == 'Rent'
    assert post.type == 'expense'
    # Verify tags are linked (check via database_manager)
    from app.database_manager import get_post_tags
    tags = get_post_tags(post.id)
    assert len(tags) == 2


def test_get_monthly_variance():
    """Should calculate budget vs actual variance for a month."""
    from app.utils import generate_uuid

    post_id = generate_uuid()
    create_post(post_id, 'Groceries', 'expense')

    # Budget: 500
    budget_id = generate_uuid()
    create_budget_entry(budget_id, post_id, 2024, 1, 500.00)

    # Actuals: 120 + 130 = 250
    create_actual_entry(generate_uuid(), post_id, date(2024, 1, 5), 120.00)
    create_actual_entry(generate_uuid(), post_id, date(2024, 1, 15), 130.00)

    variance = get_monthly_variance(post_id, 2024, 1)

    assert variance['budget'] == Decimal('500.00')
    assert variance['actual'] == Decimal('250.00')
    assert variance['difference'] == Decimal('250.00')  # Under budget
    assert variance['percentage'] == 50.0


def test_get_year_overview():
    """Should aggregate income and expenses for entire year."""
    from app.utils import generate_uuid

    # Create income post
    income_id = generate_uuid()
    create_post(income_id, 'Salary', 'income')
    create_actual_entry(generate_uuid(), income_id, date(2024, 1, 1), 5000.00)
    create_actual_entry(generate_uuid(), income_id, date(2024, 2, 1), 5000.00)

    # Create expense post
    expense_id = generate_uuid()
    create_post(expense_id, 'Rent', 'expense')
    create_actual_entry(generate_uuid(), expense_id, date(2024, 1, 1), 1500.00)
    create_actual_entry(generate_uuid(), expense_id, date(2024, 2, 1), 1500.00)

    overview = get_year_overview(2024)

    assert overview['total_income'] == Decimal('10000.00')
    assert overview['total_expenses'] == Decimal('3000.00')
    assert overview['net_savings'] == Decimal('7000.00')


def test_get_posts_by_type():
    """Should filter posts by income or expense type."""
    from app.utils import generate_uuid

    create_post(generate_uuid(), 'Salary', 'income')
    create_post(generate_uuid(), 'Bonus', 'income')
    create_post(generate_uuid(), 'Rent', 'expense')

    income_posts = get_posts_by_type('income')
    expense_posts = get_posts_by_type('expense')

    assert len(income_posts) == 2
    assert len(expense_posts) == 1


def test_calculate_post_total_actual():
    """Should sum all actuals for a post in date range."""
    from app.utils import generate_uuid

    post_id = generate_uuid()
    create_post(post_id, 'Groceries', 'expense')

    create_actual_entry(generate_uuid(), post_id, date(2024, 1, 5), 100.00)
    create_actual_entry(generate_uuid(), post_id, date(2024, 1, 15), 150.00)
    create_actual_entry(generate_uuid(), post_id, date(2024, 2, 5), 120.00)

    total = calculate_post_total_actual(
        post_id,
        date(2024, 1, 1),
        date(2024, 1, 31)
    )

    assert total == Decimal('250.00')
