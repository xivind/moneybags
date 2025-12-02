"""Business logic layer for Moneybags application."""
from typing import List, Dict, Any
from datetime import date, datetime
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


def get_monthly_chart_data(year: int) -> Dict[str, List[float]]:
    """
    Get monthly income and expense totals for chart.

    Returns dict with 'income' and 'expenses' lists (12 values each).
    """
    posts = get_all_posts()

    income_by_month = [Decimal('0')] * 12
    expenses_by_month = [Decimal('0')] * 12

    for post in posts:
        for month in range(1, 13):
            start_date = date(year, month, 1)
            if month == 12:
                end_date = date(year, 12, 31)
            else:
                from calendar import monthrange
                last_day = monthrange(year, month)[1]
                end_date = date(year, month, last_day)

            actuals = get_actual_entries(post.id, start_date, end_date)
            total = sum(Decimal(str(a.amount)) for a in actuals)

            if post.type == 'income':
                income_by_month[month - 1] += total
            else:
                expenses_by_month[month - 1] += total

    return {
        'income': [float(v) for v in income_by_month],
        'expenses': [float(v) for v in expenses_by_month]
    }


def get_yoy_comparison_data(years: List[int]) -> Dict[str, Any]:
    """
    Get year-over-year comparison data for multiple years.

    Args:
        years: List of years to compare (e.g., [2023, 2024, 2025])

    Returns:
        Dict with years, income_data, expense_data, and growth_rates
    """
    years_sorted = sorted(years)
    income_totals = []
    expense_totals = []
    net_totals = []

    for year in years_sorted:
        overview = get_year_overview(year)
        income_totals.append(float(overview['total_income']))
        expense_totals.append(float(overview['total_expenses']))
        net_totals.append(float(overview['net_savings']))

    # Calculate growth rates (year-over-year change percentages)
    income_growth = []
    expense_growth = []
    net_growth = []

    for i in range(1, len(years_sorted)):
        if income_totals[i-1] > 0:
            income_growth.append(((income_totals[i] - income_totals[i-1]) / income_totals[i-1]) * 100)
        else:
            income_growth.append(0.0)

        if expense_totals[i-1] > 0:
            expense_growth.append(((expense_totals[i] - expense_totals[i-1]) / expense_totals[i-1]) * 100)
        else:
            expense_growth.append(0.0)

        if abs(net_totals[i-1]) > 0:
            net_growth.append(((net_totals[i] - net_totals[i-1]) / abs(net_totals[i-1])) * 100)
        else:
            net_growth.append(0.0)

    return {
        'years': years_sorted,
        'income': income_totals,
        'expenses': expense_totals,
        'net': net_totals,
        'income_growth': income_growth,
        'expense_growth': expense_growth,
        'net_growth': net_growth
    }


def get_tag_analysis_data() -> List[Dict[str, Any]]:
    """
    Aggregate all posts by tag across all years.

    Returns:
        List of dicts with tag_name, total_income, total_expense, post_count
    """
    from app.database_manager import get_all_tags
    from app.database_model import PostTag, ActualEntry

    tags = get_all_tags()
    results = []

    # Get all posts once before the loop for performance
    posts = get_all_posts()

    for tag in tags:
        # Find all posts with this tag using PostTag relationship
        post_tags = PostTag.select().where(PostTag.tag == tag.id)
        tagged_post_ids = [pt.post_id for pt in post_tags]

        # Get the actual post objects
        tagged_posts = [p for p in posts if p.id in tagged_post_ids]

        total_income = Decimal('0')
        total_expense = Decimal('0')

        for post in tagged_posts:
            # Get all actuals across all time (no date filtering)
            actuals = ActualEntry.select().where(ActualEntry.post == post.id)
            total = sum(Decimal(str(a.amount)) for a in actuals)

            if post.type == 'income':
                total_income += total
            else:
                total_expense += total

        results.append({
            'tag_name': tag.name,
            'total_income': float(total_income),
            'total_expense': float(total_expense),
            'post_count': len(tagged_posts)
        })

    # Sort by total expense (descending) for better visibility
    results.sort(key=lambda x: x['total_expense'], reverse=True)
    return results


def get_time_series_data(year: int) -> Dict[str, Any]:
    """
    Get time-series data showing actual entries over time with patterns.

    Args:
        year: Year to analyze

    Returns:
        Dict with monthly_income, monthly_expenses, trends, and patterns
    """
    from calendar import monthrange

    posts = get_all_posts()
    income_by_month = [Decimal('0')] * 12
    expenses_by_month = [Decimal('0')] * 12
    monthly_labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                      'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

    for post in posts:
        for month in range(1, 13):
            start_date = date(year, month, 1)
            last_day = monthrange(year, month)[1]
            end_date = date(year, month, last_day)

            actuals = get_actual_entries(post.id, start_date, end_date)
            total = sum(Decimal(str(a.amount)) for a in actuals)

            if post.type == 'income':
                income_by_month[month - 1] += total
            else:
                expenses_by_month[month - 1] += total

    # Calculate simple trends (average per month, highest, lowest)
    income_values = [float(v) for v in income_by_month]
    expense_values = [float(v) for v in expenses_by_month]

    income_avg = sum(income_values) / 12 if income_values else 0
    expense_avg = sum(expense_values) / 12 if expense_values else 0

    # Find peak months
    max_income_month = monthly_labels[income_values.index(max(income_values))] if max(income_values) > 0 else 'N/A'
    max_expense_month = monthly_labels[expense_values.index(max(expense_values))] if max(expense_values) > 0 else 'N/A'

    return {
        'labels': monthly_labels,
        'income_data': income_values,
        'expense_data': expense_values,
        'income_avg': income_avg,
        'expense_avg': expense_avg,
        'max_income_month': max_income_month,
        'max_expense_month': max_expense_month,
        'max_income_value': max(income_values),
        'max_expense_value': max(expense_values)
    }
