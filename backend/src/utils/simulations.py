"""
simulations.py — Vectorized Monte Carlo engine for financial Goal Planning
==========================================================================
Uses numpy for high-performance projection of 10,000+ market scenarios.
"""
import numpy as np
from typing import Dict, List, Any
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
        "confidence_score": round(confidence_score, 1),
        "target_amount": target_amount,
        "years_axis": [int(y) for y in range(years + 1)],
        "p05_path": percentiles[0].tolist(),
        "p25_path": percentiles[1].tolist(),
        "median_path": percentiles[2].tolist(),
        "p75_path": percentiles[3].tolist(),
        "p95_path": percentiles[4].tolist(),
        "final_median": round(percentiles[2][-1], 2),
        "num_simulations": num_simulations
    }
