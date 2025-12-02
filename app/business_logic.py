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


def get_budget_vs_actual_analysis(year: int) -> List[Dict[str, Any]]:
    """
    Calculate budget vs actual for all posts in a year.

    Args:
        year: Year to analyze

    Returns:
        List of dicts with post_name, post_type, budget, actual, variance, percentage
    """
    posts = get_all_posts()
    results = []

    for post in posts:
        # Get all 12 months of budget
        budgets = get_budget_entries(post.id, year)
        budget_total = sum(Decimal(str(b.amount)) for b in budgets)

        # Get all actuals for the year
        actuals = get_actual_entries(post.id, date(year, 1, 1), date(year, 12, 31))
        actual_total = sum(Decimal(str(a.amount)) for a in actuals)

        variance = budget_total - actual_total
        percentage = float((actual_total / budget_total * 100)) if budget_total > 0 else 0.0

        results.append({
            'post_name': post.name,
            'post_type': post.type,
            'budget': budget_total,
            'actual': actual_total,
            'variance': variance,
            'percentage': percentage
        })

    return results


def get_year_over_year_comparison(year1: int, year2: int) -> Dict[str, Any]:
    """
    Compare two years' income and expenses.

    Args:
        year1: First year
        year2: Second year

    Returns:
        Dict with year1, year2, year1_data, year2_data, income_change, expense_change
    """
    overview1 = get_year_overview(year1)
    overview2 = get_year_overview(year2)

    income_change = overview2['total_income'] - overview1['total_income']
    expense_change = overview2['total_expenses'] - overview1['total_expenses']

    return {
        'year1': year1,
        'year2': year2,
        'year1_data': overview1,
        'year2_data': overview2,
        'income_change': income_change,
        'expense_change': expense_change
    }
