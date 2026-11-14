"""
AstroHealth Statistical Health Trend Forecasting Module
Provides short-term forward trajectory extrapolation using polynomial regression
and empirical confidence intervals, strictly distinguishing estimates from measured data.
"""
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
import numpy as np
import pandas as pd
import logging

logger = logging.getLogger("astrohealth.ai.forecaster")


class HealthTrendForecaster:
    """
    Fits trend models to time-series biometrics and projects short-term trajectory.
    Clearly marks all forecasted data points as estimates.
    """

    @staticmethod
    def forecast_biometric_indicator(
        readings: List[Dict[str, Any]],
        metric_key: str = "heart_rate",
        horizon_steps: int = 12,
        step_interval_seconds: int = 120
    ) -> Dict[str, Any]:
        """
        Extrapolates metric_key for horizon_steps into the future.
        """
        if not readings or len(readings) < 5:
            return {
                "status": "insufficient_data",
                "message": "At least 5 historical readings required for forecasting.",
                "metric_key": metric_key
            }

        df = pd.DataFrame(readings)
        if metric_key not in df.columns:
            return {"status": "metric_not_found", "metric_key": metric_key}

        df[metric_key] = pd.to_numeric(df[metric_key], errors="coerce")
        df = df.dropna(subset=[metric_key])

        y = df[metric_key].values
        n = len(y)
        x = np.arange(n)

        # Fit linear/quadratic polynomial
        degree = 1 if n < 10 else 2
        poly_coeffs = np.polyfit(x, y, deg=degree)
        poly_func = np.poly1d(poly_coeffs)

        # Estimate residual standard error for empirical 95% confidence interval
        fitted_vals = poly_func(x)
        residuals = y - fitted_vals
        residual_std = float(np.std(residuals)) if len(residuals) > 1 else 1.0

        # Last known timestamp
        last_ts_str = df.iloc[-1].get("timestamp")
        if isinstance(last_ts_str, str):
            try:
                last_time = datetime.fromisoformat(last_ts_str.replace("Z", "+00:00"))
            except Exception:
                last_time = datetime.now(timezone.utc)
        elif isinstance(last_ts_str, datetime):
            last_time = last_ts_str
        else:
            last_time = datetime.now(timezone.utc)

        # Generate forecast trajectory
        future_x = np.arange(n, n + horizon_steps)
        forecast_points = []

        for i, fx in enumerate(future_x):
            est_val = float(poly_func(fx))
            # Bound realistic values (e.g. SpO2 <= 100)
            if metric_key == "spo2":
                est_val = min(100.0, max(50.0, est_val))
            elif metric_key == "heart_rate":
                est_val = max(30.0, min(220.0, est_val))
            elif metric_key == "body_temp":
                est_val = max(33.0, min(42.0, est_val))

            # Expanding uncertainty cone
            uncertainty_growth = 1.0 + (i * 0.15)
            margin = 1.96 * residual_std * uncertainty_growth

            step_time = last_time + timedelta(seconds=(i + 1) * step_interval_seconds)

            forecast_points.append({
                "step": i + 1,
                "timestamp": step_time.isoformat(),
                "estimated_value": round(est_val, 2),
                "lower_bound_95": round(est_val - margin, 2),
                "upper_bound_95": round(est_val + margin, 2),
                "is_forecast": True,
                "is_measured": False
            })

        slope = float(poly_coeffs[0] if degree == 1 else poly_coeffs[1])
        trajectory = "climbing" if slope > 0.15 else ("declining" if slope < -0.15 else "stable")

        return {
            "status": "forecast_generated",
            "metric_key": metric_key,
            "historical_sample_count": n,
            "forecast_horizon_steps": horizon_steps,
            "step_interval_seconds": step_interval_seconds,
            "trajectory_direction": trajectory,
            "trend_slope": round(slope, 3),
            "forecast_points": forecast_points,
            "disclaimer": "Statistically estimated trend projection. Not guaranteed prediction."
        }


forecaster = HealthTrendForecaster()

