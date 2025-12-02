"""Business logic layer for Moneybags application."""
from typing import List, Dict, Any
from datetime import date
from decimal import Decimal
from app.utils import generate_uuid
from app.database_manager import (
    create_post, get_all_posts, get_post,
    add_tag_to_post, get_budget_entries, get_actual_entries
)
from app.database_model import Post


def create_post_with_tags(
    name: str,
    post_type: str,
    tag_ids: List[str]
) -> Post:
    """
    Create a post and link tags in one operation.

    Args:
        name: Post name
        post_type: 'income' or 'expense'
        tag_ids: List of tag IDs to link

    Returns:
        Post: Created post
    """
    post_id = generate_uuid()
    post = create_post(post_id, name, post_type)

    for tag_id in tag_ids:
        add_tag_to_post(post.id, tag_id)

    return post


def get_monthly_variance(post_id: str, year: int, month: int) -> Dict[str, Any]:
    """
    Calculate budget vs actual variance for a specific month.

    Args:
        post_id: Post identifier
        year: Year
        month: Month (1-12)

    Returns:
        Dict with budget, actual, difference, and percentage
    """
    # Get budget entry for the month
    budget_entries = get_budget_entries(post_id, year)
    budget_entry = next((e for e in budget_entries if e.month == month), None)
    budget_amount = Decimal(str(budget_entry.amount)) if budget_entry else Decimal('0')

    # Get actual entries for the month
    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year, 12, 31)
    else:
        from calendar import monthrange
        last_day = monthrange(year, month)[1]
        end_date = date(year, month, last_day)

    actual_entries = get_actual_entries(post_id, start_date, end_date)
    actual_amount = sum(Decimal(str(e.amount)) for e in actual_entries)

    difference = budget_amount - actual_amount
    percentage = float((actual_amount / budget_amount * 100)) if budget_amount > 0 else 0.0

    return {
        'budget': budget_amount,
        'actual': actual_amount,
        'difference': difference,
        'percentage': percentage
    }


def get_year_overview(year: int) -> Dict[str, Decimal]:
    """
    Aggregate all income and expenses for a year.

    Args:
        year: Year to analyze

    Returns:
        Dict with total_income, total_expenses, net_savings
    """
    start_date = date(year, 1, 1)
    end_date = date(year, 12, 31)

    total_income = Decimal('0')
    total_expenses = Decimal('0')

    posts = get_all_posts()
    for post in posts:
        actuals = get_actual_entries(post.id, start_date, end_date)
        total = sum(Decimal(str(e.amount)) for e in actuals)

        if post.type == 'income':
            total_income += total
        else:
            total_expenses += total

    return {
        'total_income': total_income,
        'total_expenses': total_expenses,
        'net_savings': total_income - total_expenses
    }


def get_posts_by_type(post_type: str) -> List[Post]:
    """
    Filter posts by type.

    Args:
        post_type: 'income' or 'expense'

    Returns:
        List of Post objects
    """
    all_posts = get_all_posts()
    return [p for p in all_posts if p.type == post_type]


def calculate_post_total_actual(
    post_id: str,
    start_date: date,
    end_date: date
) -> Decimal:
    """
    Sum all actual entries for a post in date range.

    Args:
        post_id: Post identifier
        start_date: Start of range
        end_date: End of range

    Returns:
        Total amount as Decimal
    """
    actuals = get_actual_entries(post_id, start_date, end_date)
    return sum(Decimal(str(e.amount)) for e in actuals)


def get_dashboard_data(year: int, current_month: int) -> Dict[str, Any]:
    """
    Get all data needed for dashboard.

    Args:
        year: Current year
        current_month: Current month (1-12)

    Returns:
        Dict with year overview, monthly data, recent entries
    """
    overview = get_year_overview(year)

    # Get current month variance for all posts
    posts = get_all_posts()
    monthly_variances = []
    for post in posts:
        variance = get_monthly_variance(post.id, year, current_month)
        monthly_variances.append({
            'post_name': post.name,
            'post_type': post.type,
            **variance
        })

    # Get recent actual entries (last 10)
    from datetime import datetime
    all_recent = []
    for post in posts:
        actuals = get_actual_entries(
            post.id,
            date(year, 1, 1),
            date.today()
        )
        for actual in actuals[:10]:  # Limit per post
            all_recent.append({
                'post_name': post.name,
                'date': actual.date,
                'amount': actual.amount,
                'comment': actual.comment
            })

    # Sort by date descending and take top 10
    all_recent.sort(key=lambda x: x['date'], reverse=True)
    recent_entries = all_recent[:10]

    return {
        'overview': overview,
        'monthly_variances': monthly_variances,
        'recent_entries': recent_entries,
        'year': year,
        'month': current_month
    }
