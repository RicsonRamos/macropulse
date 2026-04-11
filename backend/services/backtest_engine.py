"""
backend/services/backtest_engine.py

Validates the MacroPulse Risk Score against known historical crisis windows.
Zero external dependencies beyond pandas/numpy — runs on the local DB.

Crisis Reference Events:
  - 2008 Financial Crisis: peak stress ~2008-10-10 (VIX > 80)
  - 2020 COVID Crash:      peak stress ~2020-03-23 (VIX > 82)
  - 2022 Rate Shock:       sustained stress March–October 2022
"""
import logging
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

from backend.services.macro_intelligence import (
    detect_market_regime,
    calculate_global_risk_index,
)

logger = logging.getLogger(__name__)

# ─── Known crisis windows for validation ────────────────────────────────────
CRISIS_EVENTS = [
    {
        "name":        "2008 Financial Crisis",
        "start":       "2008-09-01",
        "end":         "2009-03-31",
        "expected_min_risk": 60,      # Risk Score should be >= 60 during this window
        "expected_regime": "Recession",
    },
    {
        "name":        "2020 COVID-19 Crash",
        "start":       "2020-02-20",
        "end":         "2020-04-30",
        "expected_min_risk": 65,
        "expected_regime": "Recession",
    },
    {
        "name":        "2022 Fed Rate Shock",
        "start":       "2022-03-01",
        "end":         "2022-10-31",
        "expected_min_risk": 50,
        "expected_regime": "Overheating",
    },
    {
        "name":        "2019 Bull Market",
        "start":       "2019-01-01",
        "end":         "2019-12-31",
        "expected_max_risk": 35,      # Risk Score should be low in bull market
        "expected_regime": "Expansion",
    },
]


def run_backtest(df_full: pd.DataFrame) -> dict:
    """
    Runs the Risk Engine against all historical windows.
    Returns scored results and a summary pass/fail report.
    
    df_full: full historical DataFrame with columns [date, series_type, value].
    """
    if df_full is None or df_full.empty:
        return {"error": "No historical data available. Run historical_ingest.py first."}

    df = df_full.copy()
    df["date"] = pd.to_datetime(df["date"])

    results = []
    for event in CRISIS_EVENTS:
        result = _evaluate_event(df, event)
        results.append(result)
        logger.info(f"[Backtest] {event['name']}: {result['verdict']}")

    passed = sum(1 for r in results if r["verdict"] == "PASS")
    total  = len(results)

    return {
        "summary": {
            "total_events": total,
            "passed": passed,
            "failed": total - passed,
            "accuracy_pct": round(passed / total * 100, 1),
        },
        "results": results,
        "generated_at": datetime.utcnow().isoformat(),
    }


def _evaluate_event(df: pd.DataFrame, event: dict) -> dict:
    """Simulate daily Risk Scores across a crisis window and evaluate against thresholds."""
    start = pd.Timestamp(event["start"])
    end   = pd.Timestamp(event["end"])

    mask = (df["date"] >= start) & (df["date"] <= end)
    window_df = df[mask]

    if window_df.empty:
        return {
            "event": event["name"],
            "verdict": "NO_DATA",
            "message": f"No data in DB for {event['start']} → {event['end']}. Run historical_ingest.py.",
            "avg_risk_score": None,
            "peak_risk_score": None,
            "detected_regimes": [],
        }

    # Pivot to wide format for day-by-day simulation
    vix_series  = window_df[window_df["series_type"] == "^VIX"].set_index("date")["value"]
    gspc_series = window_df[window_df["series_type"] == "^GSPC"].set_index("date")["value"]
    yld_series  = window_df[window_df["series_type"] == "T10Y2Y"].set_index("date")["value"]

    if vix_series.empty or gspc_series.empty:
        return {
            "event": event["name"],
            "verdict": "NO_DATA",
            "message": "VIX or S&P 500 data missing for this window.",
            "avg_risk_score": None,
            "peak_risk_score": None,
            "detected_regimes": [],
        }

    # Align dates
    dates = sorted(set(vix_series.index) & set(gspc_series.index))

    daily_scores  = []
    daily_regimes = []

    for i, date in enumerate(dates):
        vix   = float(vix_series.get(date, 20))
        yc    = float(yld_series.get(date, 0.5)) if not yld_series.empty else 0.5
        gspc  = float(gspc_series.get(date, 0))
        gspc_prev = float(gspc_series.iloc[i - 1]) if i > 0 else gspc
        sp_ret    = (gspc / gspc_prev - 1) if gspc_prev != 0 else 0

        regime = detect_market_regime(sp_ret, vix)
        risk   = calculate_global_risk_index(
            vix=vix, yield_curve=yc,
            sentiment_score=50, tracking_score=50,
            regime=regime,
        )["score"]

        daily_scores.append(risk)
        daily_regimes.append(regime)

    avg_risk  = round(float(np.mean(daily_scores)), 2)
    peak_risk = round(float(np.max(daily_scores)), 2)
    regimes   = pd.Series(daily_regimes).value_counts().to_dict()

    # ── Verdict logic ────────────────────────────────────────────────────
    verdict = "PASS"
    messages = []

    if "expected_min_risk" in event and avg_risk < event["expected_min_risk"]:
        verdict = "FAIL"
        messages.append(
            f"Avg Risk {avg_risk} below expected minimum {event['expected_min_risk']}"
        )
    if "expected_max_risk" in event and avg_risk > event["expected_max_risk"]:
        verdict = "FAIL"
        messages.append(
            f"Avg Risk {avg_risk} above expected maximum {event['expected_max_risk']} (false alarm)"
        )
    if "expected_regime" in event:
        dominant = max(regimes, key=regimes.get)
        if dominant != event["expected_regime"]:
            messages.append(
                f"Dominant regime '{dominant}' differs from expected '{event['expected_regime']}' (soft miss)"
            )
            # Not a hard FAIL — regime detection is multi-factor

    return {
        "event":            event["name"],
        "window":           f"{event['start']} → {event['end']}",
        "verdict":          verdict,
        "message":          "; ".join(messages) if messages else "All thresholds met.",
        "avg_risk_score":   avg_risk,
        "peak_risk_score":  peak_risk,
        "detected_regimes": regimes,
    }
