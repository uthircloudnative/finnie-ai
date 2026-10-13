"""
simulations.py — Vectorized Monte Carlo engine for financial Goal Planning
==========================================================================
Uses numpy for high-performance projection of 10,000+ market scenarios.
"""
import numpy as np
from typing import Dict, List, Any, Optional
from langsmith import traceable

@traceable(name="Monte Carlo Engine", run_type="tool")
def run_monte_carlo(
    initial_balance: float,
    target_amount: float,
    monthly_savings: float,
    years: int,
    expected_return: float,
    volatility: float,
    num_simulations: int = 10000
) -> Dict[str, Any]:
    """
    Simulates thousands of potential market paths to calculate the probability
    of hitting a financial goal.
    
    Args:
        initial_balance: Starting portfolio value (USD/INR/etc)
        target_amount: The goal amount to reach
        monthly_savings: Constant monthly contribution
        years: Time horizon in years
        expected_return: Yearly mean return (e.g. 0.08 for 8%)
        volatility: Yearly standard deviation (e.g. 0.18 for 18%)
        num_simulations: Number of paths to simulate (default 10,000)
        
    Returns:
        Dict containing:
            confidence_score: % probability of success
            median_path: Array of median values over time
            p05_path: 5th percentile (Downside case)
            p95_path: 95th percentile (Upside case)
            years_axis: Labels for the X-axis
    """
    months = years * 12
    if months <= 0:
        return {"confidence_score": 0, "error": "Timeline must be > 0 years"}

    # 1. Initialize simulation matrix (Simulations x Months)
    # Start with initial balance for all paths
    paths = np.zeros((num_simulations, months + 1))
    paths[:, 0] = initial_balance

    # 2. Generate random monthly returns
    # Mean: annual_return / 12
    # StdDev: annual_vol / sqrt(12)
    monthly_mean = (1 + expected_return) ** (1/12) - 1
    monthly_vol = volatility / np.sqrt(12)
    
    # Generate all random shocks at once for speed
    # Using Normal Distribution (Gaussian) as is standard for GBM log-returns
    random_returns = np.random.normal(monthly_mean, monthly_vol, (num_simulations, months))

    # 3. Simulate path progression month-by-month
    # We iterate monthly because savings are added every month (Path Dependency)
    current_balances = np.full(num_simulations, initial_balance)
    
    for m in range(months):
        # Apply return + Add monthly savings
        current_balances = (current_balances * (1 + random_returns[:, m])) + monthly_savings
        paths[:, m + 1] = current_balances

    # 4. Calculate Success Metrics
    final_values = paths[:, -1]
    success_count = np.sum(final_values >= target_amount)
    confidence_score = (success_count / num_simulations) * 100

    # 5. Extract Percentiles for Fan Chart (Yearly snapshots to keep data small)
    yearly_indices = np.arange(0, months + 1, 12)
    yearly_paths = paths[:, yearly_indices]
    
    percentiles = np.percentile(yearly_paths, [5, 25, 50, 75, 95], axis=0)
    
    return {
        "confidence_score": float(round(float(confidence_score), 1)),
        "target_amount": float(target_amount),
        "years_axis": [int(y) for y in range(years + 1)],
        "p05_path": [float(x) for x in percentiles[0].tolist()],
        "p25_path": [float(x) for x in percentiles[1].tolist()],
        "median_path": [float(x) for x in percentiles[2].tolist()],
        "p75_path": [float(x) for x in percentiles[3].tolist()],
        "p95_path": [float(x) for x in percentiles[4].tolist()],
        "final_median": float(round(float(percentiles[2][-1]), 2)),
        "num_simulations": int(num_simulations)
    }


def calculate_free_cashflow(
    monthly_take_home: float,
    fixed_living_costs: float,
    monthly_discretionary_spend: float,
    liabilities: List[Dict[str, Any]],
    committed_savings: float = 0.0
) -> Dict[str, Any]:
    """
    Computes net investable cash flow after debt servicing and living expenses.
    SPEC-11 / AC-2
    """
    total_debt_service = sum(float(l.get("monthly_payment", 0.0)) for l in (liabilities or []))
    free_cashflow = float(monthly_take_home) - float(fixed_living_costs) - float(monthly_discretionary_spend) - total_debt_service
    surplus_after_savings = free_cashflow - float(committed_savings)
    solvency_status = "DEFICIT" if (free_cashflow < 0 or surplus_after_savings < 0) else "SOLVENT"

    return {
        "monthly_take_home": float(monthly_take_home),
        "fixed_living_costs": float(fixed_living_costs),
        "monthly_discretionary_spend": float(monthly_discretionary_spend),
        "total_debt_service": float(round(total_debt_service, 2)),
        "free_cashflow": float(round(free_cashflow, 2)),
        "surplus_after_savings": float(round(surplus_after_savings, 2)),
        "solvency_status": solvency_status
    }


def amortize_liabilities(
    liabilities: List[Dict[str, Any]],
    years: int,
    current_year: int = 2026
) -> Dict[str, Any]:
    """
    Simulates month-by-month debt paydown for individual liabilities.
    Returns yearly debt balance curve, freed cash flow per month, and debt-free milestone.
    SPEC-11 / AC-4
    """
    months = max(1, years * 12)
    debt_by_month = np.zeros(months + 1)
    freed_cashflow_by_month = np.zeros(months + 1)

    # Initialize each loan balance
    loans = []
    initial_total_debt = 0.0
    for l in (liabilities or []):
        bal = float(l.get("current_balance", 0.0))
        apr = float(l.get("interest_rate_apr", 0.0))
        pmt = float(l.get("monthly_payment", 0.0))
        rem = int(l.get("remaining_months", months))
        if bal > 0:
            loans.append({
                "balance": bal,
                "monthly_rate": (apr / 100.0) / 12.0,
                "payment": pmt,
                "remaining_months": rem,
                "initial_payment": pmt
            })
            initial_total_debt += bal

    debt_by_month[0] = initial_total_debt
    debt_free_month = None

    for m in range(months):
        month_total = 0.0
        month_freed = 0.0
        for loan in loans:
            if loan["balance"] > 0:
                # Accrue interest, then subtract payment
                interest = loan["balance"] * loan["monthly_rate"]
                payment = min(loan["balance"] + interest, loan["payment"])
                new_balance = max(0.0, loan["balance"] + interest - payment)
                loan["remaining_months"] -= 1

                if new_balance <= 0.0 or loan["remaining_months"] <= 0:
                    loan["balance"] = 0.0
                    month_freed += loan["initial_payment"]
                else:
                    loan["balance"] = new_balance
                month_total += loan["balance"]
            else:
                month_freed += loan["initial_payment"]

        debt_by_month[m + 1] = month_total
        freed_cashflow_by_month[m + 1] = month_freed

        if month_total == 0.0 and debt_free_month is None and initial_total_debt > 0:
            debt_free_month = m + 1

    yearly_indices = np.arange(0, months + 1, 12)
    debt_amortization_path = [float(round(debt_by_month[idx], 2)) for idx in yearly_indices]

    debt_free_year = None
    if debt_free_month is not None:
        debt_free_year = current_year + int(np.ceil(debt_free_month / 12.0))
    elif initial_total_debt == 0:
        debt_free_year = current_year

    return {
        "debt_amortization_path": debt_amortization_path,
        "debt_free_year": debt_free_year,
        "freed_cashflow_by_month": freed_cashflow_by_month.tolist(),
        "initial_total_debt": initial_total_debt,
        "total_interest_saved": float(round(initial_total_debt * 0.12, 2))  # Conservative interest savings estimate
    }


@traceable(name="Cashflow Monte Carlo Engine", run_type="tool")
def run_cashflow_monte_carlo(
    initial_balance: float,
    target_amount: float,
    baseline_monthly_savings: float,
    years: int,
    expected_return: float,
    volatility: float,
    liabilities: Optional[List[Dict[str, Any]]] = None,
    auto_step_up: bool = True,
    num_simulations: int = 10000,
    current_year: int = 2026
) -> Dict[str, Any]:
    """
    Extends standard Monte Carlo with dynamic liability amortization,
    auto-step-up contributions post loan expiration, and net worth trajectory.
    SPEC-11 / AC-4, AC-5
    """
    months = max(1, years * 12)

    # 1. Amortize liabilities
    amort_res = amortize_liabilities(liabilities=liabilities or [], years=years, current_year=current_year)
    debt_path = amort_res["debt_amortization_path"]
    freed_by_month = amort_res["freed_cashflow_by_month"]

    # 2. Vectorized Monthly GBM Returns
    monthly_mean = (1 + expected_return) ** (1/12) - 1
    monthly_vol = volatility / np.sqrt(12)
    random_returns = np.random.normal(monthly_mean, monthly_vol, (num_simulations, months))

    # 3. Simulate Month-by-Month with Dynamic Step-Up
    paths = np.zeros((num_simulations, months + 1))
    paths[:, 0] = initial_balance
    current_balances = np.full(num_simulations, initial_balance)

    for m in range(months):
        step_up = freed_by_month[m + 1] if auto_step_up else 0.0
        eff_savings = baseline_monthly_savings + step_up
        current_balances = (current_balances * (1 + random_returns[:, m])) + eff_savings
        paths[:, m + 1] = current_balances

    # 4. Metrics & Percentiles
    final_values = paths[:, -1]
    success_count = np.sum(final_values >= target_amount)
    confidence_score = (success_count / num_simulations) * 100

    yearly_indices = np.arange(0, months + 1, 12)
    yearly_paths = paths[:, yearly_indices]
    percentiles = np.percentile(yearly_paths, [5, 25, 50, 75, 95], axis=0)

    median_path = [float(x) for x in percentiles[2].tolist()]
    net_worth_median_path = [float(round(median_path[i] - debt_path[i], 2)) for i in range(len(median_path))]

    status = "ON_TRACK" if confidence_score >= 70.0 else ("CAUTION" if confidence_score >= 40.0 else "AT_RISK")
    if initial_balance >= target_amount:
        status = "ACHIEVED"
        confidence_score = 100.0

    return {
        "confidence_score": float(round(float(confidence_score), 1)),
        "status": status,
        "target_amount": float(target_amount),
        "years_axis": [int(y) for y in range(years + 1)],
        "p05_path": [float(x) for x in percentiles[0].tolist()],
        "p25_path": [float(x) for x in percentiles[1].tolist()],
        "median_path": median_path,
        "p75_path": [float(x) for x in percentiles[3].tolist()],
        "p95_path": [float(x) for x in percentiles[4].tolist()],
        "final_median": float(round(float(percentiles[2][-1]), 2)),
        "debt_amortization_path": debt_path,
        "net_worth_median_path": net_worth_median_path,
        "debt_free_year": amort_res["debt_free_year"],
        "total_interest_saved": amort_res["total_interest_saved"],
        "num_simulations": int(num_simulations)
    }
