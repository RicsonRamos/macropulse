"""
backend/etl/news_engine.py — upgraded with impact scoring and causal classification.
"""
import os
import time
import requests

NEWS_KEY = os.getenv("NEWS_API_KEY")

# ── Sentiment keywords ───────────────────────────────────────────────────────
BULLISH_KEYWORDS = [
    "recovery", "growth", "expansion", "profit", "surplus", "easing",
    "bullish", "upgrade", "stability", "rate cut", "stimulus", "gdp beat",
]
BEARISH_KEYWORDS = [
    "recession", "inflation", "crisis", "decline", "deficit", "tightening",
    "bearish", "downgrade", "instability", "shock", "stagflation", "default",
    "debt ceiling", "bank failure", "rate hike", "layoffs", "contraction",
]

# ── High-impact macro topics → these trigger HIGH impact label ───────────────
HIGH_IMPACT_TRIGGERS = [
    "federal reserve", "fed", "ecb", "central bank", "rate hike", "rate cut",
    "recession", "inflation", "war", "sanctions", "oil price", "credit suisse",
    "debt", "default", "gdp", "cpi", "unemployment", "yield curve",
    "china", "us china", "geopolit", "nato", "nuclear",
]
MEDIUM_IMPACT_TRIGGERS = [
    "earnings", "ipo", "merger", "acquisition", "trade", "export", "import",
    "currency", "forex", "bitcoin", "crypto", "emerging market", "em risk",
    "elections", "political", "brazil", "europe", "asia",
]


def fetch_gdelt_news(query="macroeconomics", timespan="24h"):
    url = "https://api.gdeltproject.org/api/v2/doc/doc"
    params = {"query": query, "mode": "artlist", "format": "json",
              "timespan": timespan, "maxrecords": 50}
    for attempt in range(3):
        try:
            r = requests.get(url, params=params, timeout=15)
            if r.status_code == 429:
                wait = (attempt + 1) * 5
                print(f"GDELT Rate Limit (429). Aguardando {wait}s... (Tentativa {attempt+1}/3)")
                time.sleep(wait)
                continue
            r.raise_for_status()
            return r.json().get("articles", [])
        except Exception as e:
            print(f"Erro ao buscar notícias GDELT (Tentativa {attempt+1}): {e}")
            if attempt < 2:
                time.sleep(2)
    return []


def fetch_newsapi_news(query="macroeconomics"):
    if not NEWS_KEY:
        return []
    try:
        r = requests.get("https://newsapi.org/v2/everything", timeout=10, params={
            "q": query, "sortBy": "publishedAt", "pageSize": 20,
            "apiKey": NEWS_KEY, "language": "en",
        })
        if r.status_code == 200:
            return [
                {"title": a.get("title"), "url": a.get("url"),
                 "source": a.get("source", {}).get("name", "NewsAPI"),
                 "seendate": a.get("publishedAt")}
                for a in r.json().get("articles", [])
            ]
    except Exception as e:
        print(f"Erro NewsAPI: {e}")
    return []


def analyze_sentiment(text: str) -> str:
    if not text:
        return "Neutral"
    t = text.lower()
    bull = sum(1 for w in BULLISH_KEYWORDS if w in t)
    bear = sum(1 for w in BEARISH_KEYWORDS if w in t)
    if bull > bear:
        return "Bullish"
    elif bear > bull:
        return "Bearish"
    return "Neutral"


def assess_impact(text: str) -> str:
    """Return HIGH / MEDIUM / LOW based on topic relevance to macro market moves."""
    if not text:
        return "LOW"
    t = text.lower()
    if any(trigger in t for trigger in HIGH_IMPACT_TRIGGERS):
        return "HIGH"
    if any(trigger in t for trigger in MEDIUM_IMPACT_TRIGGERS):
        return "MEDIUM"
    return "LOW"


def derive_macro_implication(title: str, sentiment: str, impact: str) -> str:
    """
    Generate a short causal implication string tied to the article topic.
    More specific than 'sentiment classified as bearish'.
    """
    t = title.lower()

    if "inflation" in t or "cpi" in t:
        if sentiment == "Bearish":
            return "Rising inflation pressure increases probability of central bank tightening → bearish for growth equities and long bonds"
        return "Inflation cooling → supports rate cut expectations → bullish for risk assets"

    if "recession" in t or "contraction" in t or "gdp" in t:
        return "Growth deterioration signal → increases defensive allocation probability → bearish for cyclicals"

    if "fed" in t or "federal reserve" in t or "rate" in t:
        if sentiment == "Bearish":
            return "Hawkish Fed signal → tightening financial conditions → bearish for equities and crypto"
        return "Dovish pivot signal → liquidity expansion → bullish for risk assets"

    if "oil" in t or "energy" in t or "opec" in t:
        return "Energy price move feeds directly into CPI → inflation risk premium increases"

    if "china" in t or "trade" in t or "tariff" in t:
        return "Trade friction impacts global supply chains and EM risk premium"

    if "bank" in t or "credit" in t or "default" in t:
        return "Credit stress signal → systemic risk premium elevated → Risk-Off positioning indicated"

    if "election" in t or "political" in t:
        return "Political uncertainty impacts EM risk premium and capital flows"

    if "bitcoin" in t or "crypto" in t:
        return "Crypto volatility reflects broader liquidity and risk appetite conditions"

    # Generic fallback — still better than "classified as bearish"
    direction = "downward" if sentiment == "Bearish" else "upward" if sentiment == "Bullish" else "neutral"
    return f"Macro narrative directional bias: {direction} pressure on risk assets"


def synthesize_macro_thesis(processed_news: list) -> str:
    """Aggregate all articles into a cohesive thesis. Falls back gracefully."""
    if not processed_news:
        return "No live news signals detected in the last 24h. Thesis based on quantitative indicators only."

    sentiments = [n["sentiment"] for n in processed_news]
    bullish_pct = sentiments.count("Bullish") / len(sentiments) * 100
    bearish_pct = sentiments.count("Bearish") / len(sentiments) * 100

    high_impact = [n for n in processed_news if n.get("impact") == "HIGH"]
    high_titles = "; ".join(n["title"][:60] for n in high_impact[:3]) if high_impact else ""

    if bearish_pct > 60:
        base = (
            f"Multiple high-conviction bearish signals detected ({bearish_pct:.0f}% of sources). "
            "Cross-asset narrative points to tightening financial conditions and rising risk aversion. "
        )
        if high_titles:
            base += f"Key macro triggers: {high_titles}. "
        base += "Systematic reduction of equity beta and credit exposure is warranted."
        return base

    if bullish_pct > 60:
        base = (
            f"News flow is predominantly bullish ({bullish_pct:.0f}% of sources), "
            "supporting a risk-on macro backdrop. Liquidity indicators and earnings expectations are constructive. "
        )
        if high_titles:
            base += f"Primary catalysts: {high_titles}."
        return base

    # Mixed — more analytical
    return (
        f"Sentiment is balanced ({bullish_pct:.0f}% bullish / {bearish_pct:.0f}% bearish), "
        "indicating a market at an inflection point. Geopolitical risk and monetary policy cross-currents "
        "are creating an uncertain macro narrative. "
        + (f"High-impact events to monitor: {high_titles}." if high_titles else
           "No single dominant macro catalyst — watch for regime shift signals.")
    )


def get_news_intelligence() -> dict:
    print("Buscando notícias GDELT...")
    raw = fetch_gdelt_news()

    if not raw and NEWS_KEY:
        print("GDELT falhou ou retornou vazio. Acionando Fallback: NewsAPI.org...")
        raw = fetch_newsapi_news()

    processed = []
    for art in raw:
        title     = art.get("title", "")
        sentiment = analyze_sentiment(title)
        impact    = assess_impact(title)
        processed.append({
            "title":      title,
            "url":        art.get("url", "#"),
            "source":     art.get("source", art.get("sourcecountry", "Global")),
            "published":  art.get("seendate", ""),
            "sentiment":  sentiment,
            "impact":     impact,
            "implication": derive_macro_implication(title, sentiment, impact),
        })

    # Sort: HIGH impact first, then by sentiment strength
    impact_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    processed.sort(key=lambda x: impact_order.get(x["impact"], 2))

    thesis = synthesize_macro_thesis(processed)
    bullish_count = sum(1 for n in processed if n["sentiment"] == "Bullish")
    sentiment_score = (bullish_count / len(processed) * 100) if processed else 50

    return {
        "articles":       processed,
        "ai_thesis":      thesis,
        "sentiment_score": sentiment_score,
    }
