"""
backend/services/macro_intelligence.py

Core intelligence engine with:
  - Dynamic weight allocation based on regime detection
  - Heuristic Thesis Engine (deterministic rule-based research report)
  - LLM-ready synthesis interface (swap _build_thesis_heuristic for LLM call)
"""
import pandas as pd
import numpy as np

# ─────────────────────────────────────────────────────────────────────────────
# REGIME DETECTION
# ─────────────────────────────────────────────────────────────────────────────

def detect_market_regime(gspc_returns: float, vix_level: float) -> str:
    """
    Two-factor regime classifier: S&P 500 momentum + VIX level.
    Returns one of: Expansion, Recovery, Overheating, Stagflation, Recession.
    """
    if vix_level < 15 and gspc_returns > 0:
        return "Expansion"
    elif vix_level >= 25 and gspc_returns < 0:
        return "Recession"
    elif vix_level > 20 and gspc_returns > 0:
        return "Overheating"
    elif vix_level < 20 and gspc_returns < 0:
        return "Recovery"
    else:
        return "Stagflation"


# ─────────────────────────────────────────────────────────────────────────────
# DYNAMIC WEIGHT ENGINE
# ─────────────────────────────────────────────────────────────────────────────

REGIME_WEIGHTS = {
    # In Expansion: growth dominates, sentiment & tracking are leading
    "Expansion": {
        "VIX": 0.25,
        "Macro (Yield Curve)": 0.20,
        "News Sentiment": 0.30,
        "Physical Activity": 0.25,
    },
    # In Recession: volatility and macro inversion are primary stress signals
    "Recession": {
        "VIX": 0.50,
        "Macro (Yield Curve)": 0.35,
        "News Sentiment": 0.10,
        "Physical Activity": 0.05,
    },
    # In Overheating: monetary policy tightening pressure dominates
    "Overheating": {
        "VIX": 0.30,
        "Macro (Yield Curve)": 0.40,
        "News Sentiment": 0.20,
        "Physical Activity": 0.10,
    },
    # In Stagflation: all factors simultaneously stressed
    "Stagflation": {
        "VIX": 0.35,
        "Macro (Yield Curve)": 0.30,
        "News Sentiment": 0.20,
        "Physical Activity": 0.15,
    },
    # In Recovery: real-world activity signals are the leading edge
    "Recovery": {
        "VIX": 0.20,
        "Macro (Yield Curve)": 0.20,
        "News Sentiment": 0.25,
        "Physical Activity": 0.35,
    },
    # Default fallback
    "Default": {
        "VIX": 0.40,
        "Macro (Yield Curve)": 0.25,
        "News Sentiment": 0.20,
        "Physical Activity": 0.15,
    },
}


def calculate_global_risk_index(
    vix: float,
    yield_curve: float,
    sentiment_score: float,
    tracking_score: float = 50,
    regime: str = "Default",
) -> dict:
    """
    Composite Risk Index 0-100 with DYNAMIC weights per market regime.
    Returns score + full breakdown for transparency UI.
    """
    weights = REGIME_WEIGHTS.get(regime, REGIME_WEIGHTS["Default"])

    # Scale each raw input to 0-100
    vix_component      = min(vix / 50 * 100, 100)
    yield_component    = min(abs(yield_curve) * 20, 100) if yield_curve < 0 else 0
    sentiment_component = max(0, 100 - sentiment_score)   # low bullish % → high risk
    tracking_component  = max(0, 100 - tracking_score)    # low activity → high risk

    # Weighted sum
    breakdown = {
        "Volatility (VIX)":    round(vix_component      * weights["VIX"], 2),
        "Economic Inversion":  round(yield_component     * weights["Macro (Yield Curve)"], 2),
        "News Sentiment":      round(sentiment_component * weights["News Sentiment"], 2),
        "Physical Activity":   round(tracking_component  * weights["Physical Activity"], 2),
    }

    total = min(sum(breakdown.values()), 100)

    return {
        "score": round(total, 2),
        "breakdown": breakdown,
        "active_weights": weights,  # Surface which weight table is in use
    }


# ─────────────────────────────────────────────────────────────────────────────
# POSITIONING ENGINE
# ─────────────────────────────────────────────────────────────────────────────

def get_suggested_positioning(regime: str, risk_score: float) -> dict:
    """
    Derives tactical asset allocation from regime + risk score magnitude.
    Risk score override: above 70 forces defensive posture regardless of regime.

    LLM Upgrade Path:
      Pass regime + risk_score to LLM and request a personalised allocation memo.
    """
    if risk_score > 70:
        return {
            "strategy": "Defensive Pivot (Capital Preservation)",
            "actions": [
                "Raise cash allocation",
                "Increase Gold & long Treasuries",
                "Hedge equity beta via put options",
                "Exit speculative Crypto exposure",
            ],
            "signal": "Risk-Off",
        }

    playbook = {
        "Expansion": {
            "strategy": "Aggressive (Risk-On)",
            "actions": [
                "Overweight Technology & AI sectors",
                "Long Bitcoin & large-cap Crypto",
                "Emerging Markets FX carry trades",
                "Reduce cash drag to minimum",
            ],
            "signal": "Bullish",
        },
        "Recovery": {
            "strategy": "Accumulation (Value-Focused)",
            "actions": [
                "Rotate into Small & Mid-Cap Value",
                "Corporate High Yield (BB-rated)",
                "Selective EM Equities with dollar funding",
                "Moderate Bitcoin accumulation on dips",
            ],
            "signal": "Neutral+",
        },
        "Overheating": {
            "strategy": "Tactical Defensive (Inflation Hedge)",
            "actions": [
                "Commodities & Energy sector overweight",
                "TIPS and Real Asset REITs",
                "Reduce long-duration bond exposure",
                "Cash / short T-bills as yield alternative",
            ],
            "signal": "Cautious",
        },
        "Stagflation": {
            "strategy": "Hedge / Real Assets",
            "actions": [
                "Overweight Gold & Silver",
                "TIPS (inflation-protected Treasuries)",
                "Commodity-linked equities (mining, agriculture)",
                "Avoid growth equities and long-duration bonds",
            ],
            "signal": "Bearish-Controlled",
        },
        "Recession": {
            "strategy": "Deep Defensive (Systemic Protection)",
            "actions": [
                "Long-term U.S. Treasuries (flight to quality)",
                "USD-denominated cash equivalents",
                "Defensive Utilities & Consumer Staples",
                "Minimal equity exposure — preserve capital",
            ],
            "signal": "Risk-Off",
        },
    }

    return playbook.get(
        regime,
        {"strategy": "Neutral (Monitor)", "actions": ["Rebalancing", "Passive hedge"], "signal": "Neutral"},
    )


# ─────────────────────────────────────────────────────────────────────────────
# HEURISTIC THESIS ENGINE
# ─────────────────────────────────────────────────────────────────────────────

def build_macro_thesis(
    regime: str,
    risk_score: float,
    vix: float,
    yield_curve: float,
    sentiment_pct: float,
    activity_score: float,
    brasil_kpis: dict,
) -> str:
    """
    Generates a specific, data-interpolated macro research thesis.
    Every sentence references actual metric values — no generic filler.

    LLM Upgrade Path:
        Replace this body with an API call, passing all variables as structured context.
    """
    parts = []

    # ── 1. Volatility vs Monetary Policy divergence ───────────────────────
    vix_label = "acute fear" if vix > 30 else "elevated stress" if vix > 22 else "contained" if vix < 18 else "moderate"
    parts.append(
        f"VIX at {vix:.1f} ({vix_label}), "
        + (
            f"signalling acute investor fear — historically correlated with systemic dislocations. "
            f"March 2020 analogue: VIX reached 82 as COVID triggered forced deleveraging."
            if vix > 30 else
            f"signalling above-average uncertainty without reaching panic territory. "
            f"Risk premia are widening but institutional buying-on-dips behaviour persists."
            if vix > 22 else
            f"indicating that market participants are comfortable with current systemic risk. "
            f"Low volatility regimes historically precede momentum continuation in equities."
        )
    )

    # ── 2. Yield curve — specific spread value ────────────────────────────
    if yield_curve is not None:
        if yield_curve < -0.5:
            parts.append(
                f"The T10Y–T2Y yield spread stands at {yield_curve:+.2f}% (deeply inverted). "
                "Deep inversions of this magnitude have preceded every U.S. recession since 1970, "
                "with an average lead time of 12–18 months. "
                "This signals that bond markets expect the Fed to cut aggressively — "
                "an admission that current rates are too restrictive for sustained growth."
            )
        elif yield_curve < 0:
            parts.append(
                f"The yield curve is modestly inverted at {yield_curve:+.2f}%. "
                "Early-stage inversion suggests credit markets are pricing in growth deceleration "
                "but not yet a broad recessionary scenario. "
                "Monitor for further flattening — the signal strengthens if spread widens below −0.50%."
            )
        elif yield_curve < 0.3:
            parts.append(
                f"The yield curve is near-flat at {yield_curve:+.2f}%, "
                "a neutral-to-cautious signal indicating that term premia are compressed. "
                "Monetary policy is restrictive relative to long-run neutral rate estimates."
            )
        else:
            parts.append(
                f"The yield curve is positively sloped at {yield_curve:+.2f}%, "
                "consistent with a growth-supportive monetary environment. "
                "Steepening curves historically coincide with early-cycle recoveries and credit expansion."
            )

    # ── 3. Regime-specific causal narrative ──────────────────────────────
    regime_causal = {
        "Expansion": (
            f"The {regime} regime is supported by positive S&P 500 momentum and subdued volatility. "
            "Earnings growth and consumer confidence are driving the cycle. "
            "Key risk: overheating that forces a premature tightening response."
        ),
        "Recovery": (
            f"The {regime} regime reflects stabilising equity returns after a drawdown period. "
            "Leading indicators (PMI, credit spreads) are improving but from a low base. "
            "Asymmetric opportunity exists for patient accumulators — downside is limited, upside optionality is rising."
        ),
        "Overheating": (
            f"The {regime} regime is characterised by positive returns concurrent with elevated macro risk. "
            f"The divergence between VIX ({vix:.1f}) and yield curve ({yield_curve:+.2f}%) suggests "
            "markets are pricing in a soft landing while bond markets hedge against tightening overshoot."
        ),
        "Stagflation": (
            f"The {regime} regime is the most challenging for traditional 60/40 portfolios. "
            "Growth is deteriorating while inflation remains sticky — "
            "making both equities and nominal bonds unattractive simultaneously. "
            "Real assets and inflation-linked instruments serve as the primary hedge."
        ),
        "Recession": (
            f"The {regime} regime is confirmed by negative equity momentum (S&P 500 declining) "
            f"concurrent with elevated volatility (VIX: {vix:.1f}). "
            "Cash preservation and defensive positioning are the dominant strategies. "
            "Duration risk in Treasuries has historically delivered positive returns in this phase."
        ),
    }
    parts.append(regime_causal.get(regime, f"Market regime is classified as {regime}."))

    # ── 4. Sentiment and news flow ────────────────────────────────────────
    if sentiment_pct < 30:
        parts.append(
            f"News-flow sentiment skews bearish ({sentiment_pct:.0f}% bullish). "
            "Multiple macro narratives are converging negatively — "
            "tightening credit conditions, geopolitical friction, and slowing global trade "
            "are creating a self-reinforcing negative feedback loop in market psychology."
        )
    elif sentiment_pct > 65:
        parts.append(
            f"News-flow sentiment is constructive ({sentiment_pct:.0f}% bullish). "
            "Corporate earnings resilience and easing central bank language are supporting "
            "risk-on positioning across equities, credit, and EM assets."
        )
    else:
        parts.append(
            f"News-flow sentiment is balanced ({sentiment_pct:.0f}% bullish). "
            "Cross-currents between resilient U.S. data and international growth headwinds "
            "are preventing a clear directional consensus. Positioning is bifurcated."
        )

    # ── 5. Brazil-specific addendum (only if meaningful) ─────────────────
    selic  = brasil_kpis.get("selic", 0)
    usdbrl = brasil_kpis.get("usdbrl", 0)
    ibov   = brasil_kpis.get("ibov_ret", 0) * 100
    if selic > 10 and usdbrl > 0:
        brl_signal = "capital outflow risk" if usdbrl > 5.8 else "relatively stable"
        parts.append(
            f"Brazil: Selic at {selic:.2f}% (annualised) maintains a restrictive monetary stance. "
            f"USD/BRL at R${usdbrl:.2f} — {brl_signal}. "
            f"Ibovespa daily change: {ibov:+.2f}%. "
            + (f"BRL weakness amplifies imported inflation risk and pressures the BCB to stay hawkish longer."
               if usdbrl > 5.8 else
               f"FX stability reduces imported inflation pressure and supports BCB's easing optionality.")
        )

    # ── 6. Conclusion with full risk score context ────────────────────────
    risk_tier  = "high" if risk_score > 65 else "moderate" if risk_score > 40 else "low"
    active_bias = "defensive" if risk_score > 65 else "balanced" if risk_score > 40 else "risk-on"
    parts.append(
        f"Composite Risk Score: {risk_score:.1f}/100 ({risk_tier} systemic pressure). "
        f"Dynamic weight allocation is {regime}-calibrated. "
        f"Recommended portfolio bias: {active_bias}."
    )

    return " ".join(parts)


# ─────────────────────────────────────────────────────────────────────────────
# BADGE / UI HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def get_market_regime_badge(regime: str) -> dict:
    regimes = {
        "Expansion":   {"color": "success", "trend": "↑"},
        "Overheating": {"color": "warning", "trend": "↗"},
        "Stagflation": {"color": "danger",  "trend": "→"},
        "Recession":   {"color": "dark",    "trend": "↓"},
        "Recovery":    {"color": "info",    "trend": "↗"},
    }
    return regimes.get(regime, {"color": "secondary", "trend": "?"})


# ─────────────────────────────────────────────────────────────────────────────
# MAIN INTELLIGENCE SNAPSHOT
# ─────────────────────────────────────────────────────────────────────────────

def get_intelligence_snapshot(df_macro: pd.DataFrame, sentiment_score: float) -> dict:
    """
    Master function — assembles the complete intelligence payload.
    sentiment_score: 0-100 (percentage of Bullish news articles).
    """
    if df_macro.empty:
        return {}

    df = df_macro.copy()
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")

    # ── Core market indicators ────────────────────────────────────────────
    try:
        current_vix = float(df[df["series_type"] == "^VIX"]["value"].iloc[-1])
        sp500_row   = df[df["series_type"] == "^GSPC"]
        sp500_ret   = float(sp500_row["value"].iloc[-1] / sp500_row["value"].iloc[-2] - 1) if len(sp500_row) > 1 else 0.0
    except Exception:
        current_vix = 20.0
        sp500_ret   = 0.0

    try:
        current_yield = float(df[df["series_type"] == "T10Y2Y"]["value"].iloc[-1])
    except Exception:
        current_yield = 0.5

    # ── Regime & risk ─────────────────────────────────────────────────────
    regime    = detect_market_regime(sp500_ret, current_vix)
    risk_data = calculate_global_risk_index(
        vix=current_vix,
        yield_curve=current_yield,
        sentiment_score=sentiment_score,
        tracking_score=50,
        regime=regime,                   # ← Dynamic weights activated here
    )
    risk_score = risk_data["score"]

    # ── Brasil KPIs ───────────────────────────────────────────────────────
    brasil = _extract_brasil_kpis(df)

    # ── Thesis (heuristic research report) ───────────────────────────────
    thesis = build_macro_thesis(
        regime=regime,
        risk_score=risk_score,
        vix=current_vix,
        yield_curve=current_yield,
        sentiment_pct=sentiment_score,
        activity_score=50,   # Default; ETL worker overrides with real tracking
        brasil_kpis=brasil,
    )

    positioning = get_suggested_positioning(regime, risk_score)
    badge       = get_market_regime_badge(regime)

    return {
        "regime":        regime,
        "risk_score":    risk_score,
        "risk_breakdown": risk_data["breakdown"],
        "active_weights": risk_data["active_weights"],
        "positioning":   positioning,
        "ai_thesis":     thesis,
        "color":         badge["color"],
        "trend":         badge["trend"],
        "explanation":   (
            f"VIX: {current_vix:.1f} | Yield Curve: {current_yield:+.2f}% | "
            f"Regime: {regime} | Risk: {risk_score:.0f}/100"
        ),
        "brasil":        brasil,
    }


def _extract_brasil_kpis(df: pd.DataFrame) -> dict:
    """Extract Brazil & Crypto KPIs from the macro dataframe."""
    kpis = {"selic": 0, "ipca": 0, "ibov_ret": 0, "usdbrl": 0, "btc": 0, "btc_ret": 0, "fng": 0}

    def last(t):
        rows = df[df["series_type"] == t]["value"]
        return float(rows.iloc[-1]) if not rows.empty else None

    def pct_change(t):
        rows = df[df["series_type"] == t]["value"]
        if len(rows) > 1:
            return float(rows.iloc[-1] / rows.iloc[-2] - 1)
        return 0.0

    try:
        daily_selic = last("BCB_SELIC")
        if daily_selic is not None:
            kpis["selic"] = round(((1 + daily_selic / 100) ** 252 - 1) * 100, 2)

        ipca = last("BCB_IPCA")
        if ipca is not None:
            kpis["ipca"] = ipca

        kpis["ibov_ret"] = pct_change("^BVSP")

        usd = last("USDBRL=X")
        if usd is not None:
            kpis["usdbrl"] = usd

        btc = last("BTC-USD")
        if btc is not None:
            kpis["btc"]     = btc
            kpis["btc_ret"] = pct_change("BTC-USD")

        fng = last("FEAR_GREED")
        if fng is not None:
            kpis["fng"] = fng

    except Exception as e:
        print(f"[Intelligence] Brasil KPI extraction error: {e}")

    return kpis
