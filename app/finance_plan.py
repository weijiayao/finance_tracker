from datetime import datetime
from typing import Tuple
import pandas as pd


def _months_between(start: datetime, end: datetime) -> int:
    return (end.year - start.year) * 12 + (end.month - start.month)

def calculate_suggested_monthly_saving(
    current_monthly_earned_income: float,
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

    # Suggested expense budget is what's left from salary after saving
    suggested_monthly_expense = float(current_monthly_earned_income) - suggested_monthly_saving
    if suggested_monthly_expense < 0:
        # Not enough salary to cover suggested saving; clamp expense at zero.
        raise ValueError("Current monthly salary is insufficient to meet the saving goal.")

    return suggested_monthly_saving, suggested_monthly_expense


def generate_plan_projection(
    initial_asset: float,
    initial_time: datetime,
    suggested_monthly_saving: float,
    target_time: datetime,
    annual_return_rate_percent: float = 5.0,
) -> pd.DataFrame:
    """Generate a monthly projection DataFrame from `initial_time` up to `target_time`.

    The returned DataFrame has columns:
    - `month` (Timestamp first day of month)
    - `fc_total_asset` (planned total asset for that month)
    - `suggested_monthly_saving` (same value each month)
    - `cumulative_saving` (sum of contributions so far)
    """
    months = _months_between(initial_time, target_time)
    if months <= 0:
        raise ValueError("`target_time` must be after `initial_time` and at least one month later")

    r_annual = float(annual_return_rate_percent) / 100.0
    monthly_rate = (1 + r_annual) ** (1 / 12) - 1

    rows = []
    asset = float(initial_asset)
    cumulative = 0.0
    # Build months as first day timestamps
    for i in range(1, months + 1):
        # advance one month
        month = (initial_time.replace(day=1) + pd.DateOffset(months=i))
        # asset grows during month
        asset = asset * (1 + monthly_rate)
        # contribution at end of month
        asset += float(suggested_monthly_saving)
        cumulative += float(suggested_monthly_saving)

        rows.append({
            "month": month.to_pydatetime(),
            "total_asset_plan": asset,
            "cumulative_saving_plan": cumulative,
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
    generate: bool,
) -> pd.DataFrame:
    """Return a DataFrame with planned monthly projection from initial_time to target_time.

    Columns: `month`, `fc_total_asset`, `suggested_monthly_saving`, `cumulative_saving`, `suggested_monthly_expense`.
    If `generate` is False, returns an empty DataFrame.
    """
    if not generate:
        return pd.DataFrame(columns=["month", "total_asset_plan", "suggested_monthly_saving_plan", "cumulative_saving_plan", "suggested_monthly_expense_plan"]) 

    # Calculate required monthly saving and suggested expense
    suggested_monthly_saving, suggested_monthly_expense = calculate_suggested_monthly_saving(
        current_monthly_earned_income=current_monthly_earned_income,
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
    )

    # Add suggested_monthly_expense and suggested_monthly_saving_plan as constant column and rename plan columns with suffix
    if not plan_df.empty:
        plan_df = plan_df.copy()
        plan_df["suggested_monthly_expense"] = float(suggested_monthly_expense)
        plan_df["suggested_suggested_monthly_saving"] = float(suggested_monthly_saving)
    
    return plan_df, suggested_monthly_expense

