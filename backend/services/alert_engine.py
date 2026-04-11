"""
backend/services/alert_engine.py

Proactive alert monitor for critical macro signal combinations.
Designed for extensibility — add new alert rules as simple dict entries.

LLM Integration Path:
  Future version can pass triggered alerts to an LLM to generate
  a natural-language explanation of why the alert matters right now.
"""
from dataclasses import dataclass
from typing import Optional
import pandas as pd

# ─────────────────────────────────────────────
# Alert Severity Levels
# ─────────────────────────────────────────────
CRITICAL = "CRITICAL"
WARNING  = "WARNING"
INFO     = "INFO"


@dataclass
class Alert:
    level: str          # CRITICAL / WARNING / INFO
    code: str           # Machine-readable id
    title: str          # Short display title
    message: str        # Full explanatory message
    implication: str    # What this means for positioning


def evaluate_alerts(intelligence: dict, df_macro: pd.DataFrame) -> list[dict]:
    """
    Evaluate all alert rules against current market intelligence.
    Returns a list of triggered Alert objects serialized as dicts.
    """
    triggered = []
    risk_score = intelligence.get("risk_score", 0)
    regime     = intelligence.get("regime", "")
    brasil     = intelligence.get("brasil", {})

    # ── Helper: safe series getter ──────────────────────────────────────────
    def last(series_type: str) -> Optional[float]:
        rows = df_macro[df_macro["series_type"] == series_type]["value"]
        return float(rows.iloc[-1]) if not rows.empty else None

    vix         = last("^VIX")
    yield_curve = last("T10Y2Y")
    btc         = last("BTC-USD")
    sp500       = last("^GSPC")
    usdbrl      = last("USDBRL=X")

    # ── RULE 1: Critical — VIX spike + Yield curve inversion ───────────────
    if vix and yield_curve is not None:
        if vix > 30 and yield_curve < 0:
            triggered.append(Alert(
                level=CRITICAL,
                code="SYSTEMIC_STRESS",
                title="⚠️ Systemic Stress Detected",
                message=(
                    f"VIX at {vix:.1f} (fear spike) combined with an inverted yield curve "
                    f"({yield_curve:.2f}%) historically precedes recessionary shocks "
                    "(e.g., 2008, COVID-19 crash)."
                ),
                implication="Immediate defensive repositioning advised. Reduce risk exposure."
            ).__dict__)

    # ── RULE 2: Warning — Risk Score crosses high threshold ─────────────────
    if risk_score > 65:
        triggered.append(Alert(
            level=WARNING,
            code="HIGH_RISK_SCORE",
            title="📊 Risk Score Elevated",
            message=(
                f"The composite Risk Score has reached {risk_score:.1f}/100. "
                "Multiple components are signalling above-average systemic pressure."
            ),
            implication="Consider reducing leveraged positions and adding hedges (Gold, Bonds)."
        ).__dict__)

    # ── RULE 3: Warning — Regime is Recession ───────────────────────────────
    if regime == "Recession":
        triggered.append(Alert(
            level=WARNING,
            code="RECESSION_REGIME",
            title="📉 Recession Regime Active",
            message=(
                "Market signals classify current conditions as a Recession regime. "
                "Equity momentum is negative while volatility remains elevated."
            ),
            implication="Defensive assets (Treasuries, Gold, USD) historically outperform in this phase."
        ).__dict__)

    # ── RULE 4: Warning — Yield curve inversion alone ───────────────────────
    if yield_curve is not None and yield_curve < -0.5:
        triggered.append(Alert(
            level=WARNING,
            code="YIELD_INVERSION",
            title="💹 Deep Yield Curve Inversion",
            message=(
                f"T10Y-T2Y spread at {yield_curve:.2f}%. "
                "A sustained inversion of this magnitude has preceded every U.S. recession in the past 50 years."
            ),
            implication="Increase allocation to short-duration fixed income and defensive sectors."
        ).__dict__)

    # ── RULE 5: Info — BRL weakness ─────────────────────────────────────────
    if usdbrl and usdbrl > 5.8:
        triggered.append(Alert(
            level=INFO,
            code="BRL_STRESS",
            title="🇧🇷 BRL Weakness Alert",
            message=(
                f"USD/BRL rate at R${usdbrl:.2f}. "
                "A weak Real signals capital flight from EM Brazil assets and inflationary pressure on imported goods."
            ),
            implication="Monitor Ibovespa exposure and consider USD-denominated hedge."
        ).__dict__)

    # ── RULE 6: Info — Stagflation regime ───────────────────────────────────
    if regime == "Stagflation":
        triggered.append(Alert(
            level=INFO,
            code="STAGFLATION_DETECTED",
            title="🔥 Stagflationary Pressures",
            message=(
                "Simultaneous elevation of volatility and deteriorating growth signals suggest "
                "stagflationary conditions — a challenging environment where neither stocks nor bonds perform well."
            ),
            implication="Real assets (Gold, Commodities, TIPS) are the primary hedge."
        ).__dict__)

    return triggered
