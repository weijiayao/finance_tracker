from datetime import datetime
from typing import Tuple
import pandas as pd


def _months_between(start: datetime, end: datetime) -> int:
    return (end.year - start.year) * 12 + (end.month - start.month)

def calculate_suggested_monthly_saving(
    initial_asset: float,
    initial_time: datetime,
    target_asset_value: float,
    target_time: datetime,
    annual_return_rate_percent: float = 5.0,
) -> Tuple[float, float]:
    """
    Calculate required monthly saving to reach `target_asset_value`.

    Returns:
        (suggested_monthly_saving, suggested_monthly_expense_budget)
    """

    months = _months_between(initial_time, target_time)
    if months <= 0:
        raise ValueError("`target_time` must be after `initial_time`")

    A = float(initial_asset)
    target = float(target_asset_value)

    # error reminder
    if A >= target:
        raise ValueError("Initial asset already meets or exceeds target asset value.")
    if annual_return_rate_percent < 0:
        raise ValueError("Annual return rate percent cannot be negative.")

    # Convert annual return to effective monthly rate
    r_annual = annual_return_rate_percent / 100.0
    if r_annual == 0:
        monthly_rate = 0.0
    else:
        monthly_rate = (1 + r_annual) ** (1 / 12) - 1

    n = months

    # Solve for monthly saving (PMT)
    # assumed formula: target = A*(1+monthly_rate)**n + suggested_monthly_saving * [((1+monthly_rate)**n - 1) / monthly_rate]
    if monthly_rate == 0:
        # Linear saving, no investment growth
        suggested_monthly_saving = (target - A) / n
    else:
        factor = (1 + monthly_rate) ** n
        denom = (factor - 1) / monthly_rate
        suggested_monthly_saving = (target - A * factor) / denom

    suggested_monthly_saving = max(0.0, float(suggested_monthly_saving))

    return suggested_monthly_saving


def generate_plan_projection(
    initial_asset: float,
    initial_time: datetime,
    suggested_monthly_saving: float,
    target_time: datetime,
    monthly_earned_income: float,
    annual_return_rate_percent: float = 5.0,
    annual_income_increase_rate_percent: float = 0.0,
) -> pd.DataFrame:
    """
    Generate a monthly projection DataFrame from `initial_time` up to `target_time`.

    Assumptions:
    - Investment grows at a fixed monthly rate derived from `annual_return_rate_percent`
    - Monthly contributions occur at the end of each month
    - Monthly earned income increases annually at `annual_income_increase_rate_percent` (applied in Jan each year)
    
    Returns DataFrame with columns:
    - `month` (Timestamp first day of month)
    - `total_asset_plan` (planned total asset for that month)
    - `cumulative_saving_plan` (sum of contributions so far)
    - `monthly_income` (income for that month after annual increase)
    - `suggested_monthly_expense` (income minus saving)
    """
    months = _months_between(initial_time, target_time)
    if months <= 0:
        raise ValueError("`target_time` must be after `initial_time` and at least one month later")

    r_annual = float(annual_return_rate_percent) / 100.0
    monthly_rate = (1 + r_annual) ** (1 / 12) - 1

    income_increase_rate = float(annual_income_increase_rate_percent) / 100.0
    current_income = float(monthly_earned_income)

    rows = []
    asset = float(initial_asset)
    cumulative = 0.0

    start_year = initial_time.year

    for i in range(1, months + 1):
        # advance one month
        month = (initial_time.replace(day=1) + pd.DateOffset(months=i))

        # check if it is a new year (Jan), then increase income
        if month.month == 1 and month.year > start_year:
            current_income *= (1 + income_increase_rate)
            start_year = month.year

        # asset grows during month
        asset = asset * (1 + monthly_rate)
        # contribution at end of month
        asset += float(suggested_monthly_saving)
        cumulative += float(suggested_monthly_saving)

        # planed expense budget is what's left from salary after saving
        expense_plan = current_income - suggested_monthly_saving
        if expense_plan < 0:
            # Not enough salary to cover suggested saving; clamp expense at zero.
            raise ValueError("Current monthly salary is insufficient to meet the saving goal.")
    
        rows.append({
            "month": month.to_pydatetime(),
            "total_asset_plan": asset,
            "cumulative_saving_plan": cumulative,
            "earned_income_plan": current_income,
            "expense_plan": expense_plan,
            "suggested_monthly_saving": suggested_monthly_saving,
        })

    df = pd.DataFrame(rows)
    return df

def generate_planned_finance(
    current_monthly_earned_income: float,
    initial_asset: float,
    initial_time: datetime,
    target_asset_value: float,
    target_time: datetime,
    annual_return_rate_percent: float,
    annual_income_increase_rate_percent: float,
) -> pd.DataFrame:
    """Return a DataFrame with planned monthly projection from initial_time to target_time.

    Columns: `month`, `fc_total_asset`, `suggested_monthly_saving`, `cumulative_saving`, `suggested_monthly_expense`.
    If `generate` is False, returns an empty DataFrame.
    """
    
    # Calculate required monthly saving and suggested expense
    suggested_monthly_saving = calculate_suggested_monthly_saving(
        initial_asset=initial_asset,
        initial_time=initial_time,
        target_asset_value=target_asset_value,
        target_time=target_time,
        annual_return_rate_percent=annual_return_rate_percent,
    )

    plan_df = generate_plan_projection(
        initial_asset=initial_asset,
        initial_time=initial_time,
        suggested_monthly_saving=suggested_monthly_saving,
        target_time=target_time,
        annual_return_rate_percent=annual_return_rate_percent,
        monthly_earned_income=current_monthly_earned_income,
        annual_income_increase_rate_percent=annual_income_increase_rate_percent,
    )
    
    return plan_df, suggested_monthly_saving

