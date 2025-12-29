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
            "fc_total_asset": asset,
            "monthly_saving": float(monthly_saving),
            "cumulative_saving": cumulative,
        })

    df = pd.DataFrame(rows)
    return df


__all__ = ["calculate_monthly_saving", "generate_plan_projection"]
