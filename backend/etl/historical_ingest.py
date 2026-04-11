"""
backend/etl/historical_ingest.py

Backfills long-run historical data (2005–present) for key macro series.
Includes the 2008 Financial Crisis and 2020 COVID-19 crash windows.

Usage:
    python -m backend.etl.historical_ingest
    # or call ingest_historical_data(db) from a startup script
"""
import logging
from datetime import datetime

import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)

# ─── Series to backfill ─────────────────────────────────────────────────────
HISTORICAL_TICKERS = {
    "^GSPC":    "S&P 500",
    "^VIX":     "VIX Fear Index",
    "GC=F":     "Gold Futures",
    "BTC-USD":  "Bitcoin (from 2014)",
    "^BVSP":    "Ibovespa",
    "USDBRL=X": "USD/BRL",
}

# Full history from 2005 (covers 2008 crisis, 2020 crash, and post-COVID)
START_DATE = "2005-01-01"
END_DATE   = datetime.today().strftime("%Y-%m-%d")


def _fetch_yahoo(ticker: str, start: str, end: str) -> pd.DataFrame:
    """Download daily closing prices from Yahoo Finance."""
    try:
        raw = yf.download(ticker, start=start, end=end, progress=False, auto_adjust=True)
        if raw.empty:
            logger.warning(f"[HistoricalIngest] No data for {ticker}")
            return pd.DataFrame()

        df = raw[["Close"]].reset_index()
        df.columns = ["date", "value"]
        df["series_type"] = ticker
        df["date"] = df["date"].dt.strftime("%Y-%m-%d")
        df = df.dropna(subset=["value"])
        return df[["date", "series_type", "value"]]
    except Exception as e:
        logger.error(f"[HistoricalIngest] Failed to fetch {ticker}: {e}")
        return pd.DataFrame()


def ingest_historical_data(db) -> dict:
    """
    Main entry point — fetches and persists all historical series.
    Returns a summary dict with record counts per ticker.
    """
    from backend.etl.load import load_data_to_db

    summary = {}
    all_frames = []

    for ticker, name in HISTORICAL_TICKERS.items():
        logger.info(f"[HistoricalIngest] Fetching {name} ({ticker})...")
        df = _fetch_yahoo(ticker, START_DATE, END_DATE)
        if not df.empty:
            all_frames.append(df)
            summary[ticker] = len(df)
            logger.info(f"[HistoricalIngest] {ticker}: {len(df)} records ({START_DATE} → {END_DATE})")
        else:
            summary[ticker] = 0

    if all_frames:
        combined = pd.concat(all_frames, ignore_index=True)
        load_data_to_db(db, combined)
        total = len(combined)
        logger.info(f"[HistoricalIngest] ✓ Persisted {total} total historical records.")
    else:
        total = 0
        logger.warning("[HistoricalIngest] No data was fetched. Check connectivity.")

    summary["_total"] = total
    return summary


# ─── CLI entry point ────────────────────────────────────────────────────────
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    from backend.db.database import SessionLocal
    db = SessionLocal()
    try:
        result = ingest_historical_data(db)
        print("\n=== Historical Ingestion Summary ===")
        for k, v in result.items():
            print(f"  {k}: {v} records")
    finally:
        db.close()
