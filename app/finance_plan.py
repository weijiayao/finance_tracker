from datetime import datetime
from typing import Tuple
import pandas as pd


def _months_between(start: datetime, end: datetime) -> int:
    return (end.year - start.year) * 12 + (end.month - start.month)


def calculate_monthly_saving(
    current_monthly_salary: float,
    initial_asset: float,
    initial_time: datetime,
    target_asset_value: float,
    target_time: datetime,
    annual_return_rate_percent: float = 5.0,
) -> Tuple[float, float]:
    """Calculate required monthly saving to reach `target_asset_value`.

    Returns a tuple: (monthly_saving, suggested_monthly_expense_budget).

    Calculation assumptions:
    - Monthly contributions occur at the end of each month.
    - Investment grows at a fixed monthly rate derived from the annual rate.
    - If `annual_return_rate_percent` is zero, a simple linear split is used.
    - If the target is already met, monthly saving is 0.
    """
    months = _months_between(initial_time, target_time)
    if months <= 0:
        raise ValueError("`target_time` must be after `initial_time` and at least one month later")

    target = float(target_asset_value)
    A = float(initial_asset)
    r = float(annual_return_rate_percent) / 100.0
    m = 12
    monthly_rate = r / m

    # If already at or above target, no saving needed.
    if A >= target:
        return 0.0, max(0.0, float(current_monthly_salary))

    # Solve future value formula for PMT (end-of-period contributions):
    # target = A*(1+monthly_rate)**n + PMT * [((1+monthly_rate)**n - 1) / monthly_rate]
    n = months
    if monthly_rate == 0:
        pmt = (target - A) / n
    else:
        factor = (1 + monthly_rate) ** n
        denom = (factor - 1) / monthly_rate
        pmt = (target - A * factor) / denom

    # Ensure PMT is not negative
    pmt = max(0.0, float(pmt))

    # Suggested expense budget is what's left from salary after saving
    suggested_expense = float(current_monthly_salary) - pmt
    if suggested_expense < 0:
        # Not enough salary to cover suggested saving; clamp expense at zero.
        suggested_expense = 0.0

    return pmt, suggested_expense


def generate_plan_projection(
    initial_asset: float,
    initial_time: datetime,
    monthly_saving: float,
    target_time: datetime,
    annual_return_rate_percent: float = 5.0,
) -> pd.DataFrame:
    """Generate a monthly projection DataFrame from `initial_time` up to `target_time`.

    The returned DataFrame has columns:
    - `month` (Timestamp first day of month)
    - `fc_total_asset` (planned total asset for that month)
    - `monthly_saving` (same value each month)
    - `cumulative_saving` (sum of contributions so far)
    """
    months = _months_between(initial_time, target_time)
    if months <= 0:
        raise ValueError("`target_time` must be after `initial_time` and at least one month later")

    r = float(annual_return_rate_percent) / 100.0
    monthly_rate = r / 12.0

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
        asset += float(monthly_saving)
        cumulative += float(monthly_saving)

        rows.append({
            "month": month.to_pydatetime(),
            "total_asset_plan": asset,
            "monthly_saving_plan": float(monthly_saving),
            "cumulative_saving_plan": cumulative,
        })

    df = pd.DataFrame(rows)
    return df

def generate_planned_finance(
    current_monthly_salary: float,
    initial_asset: float,
    initial_time: datetime,
    target_asset_value: float,
    target_time: datetime,
    annual_return_rate_percent: float,
    generate: bool,
) -> pd.DataFrame:
    """Return a DataFrame with planned monthly projection from initial_time to target_time.

    Columns: `month`, `fc_total_asset`, `monthly_saving`, `cumulative_saving`, `suggested_expense`.
    If `generate` is False, returns an empty DataFrame.
    """
    if not generate:
        return pd.DataFrame(columns=["month", "total_asset_plan", "monthly_saving_plan", "cumulative_saving_plan", "suggested_expense_plan"]) 

    # Calculate required monthly saving and suggested expense
    pmt, suggested_expense = calculate_monthly_saving(
        current_monthly_salary=current_monthly_salary,
        initial_asset=initial_asset,
        initial_time=initial_time,
        target_asset_value=target_asset_value,
        target_time=target_time,
        annual_return_rate_percent=annual_return_rate_percent,
    )

    plan_df = generate_plan_projection(
        initial_asset=initial_asset,
        initial_time=initial_time,
        monthly_saving=pmt,
        target_time=target_time,
        annual_return_rate_percent=annual_return_rate_percent,
    )

    # Add suggested_expense as constant column and rename plan columns with suffix
    if not plan_df.empty:
        plan_df = plan_df.copy()
        plan_df["suggested_expense"] = float(suggested_expense)
    return plan_df

