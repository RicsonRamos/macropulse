"""
backend/api/main.py

Pure API serving layer — READ ONLY.
All data mutations happen in backend/workers/etl_worker.py (APScheduler).

Architecture:
  ┌─────────────────┐      ┌──────────────────────┐
  │  APScheduler    │ ───> │  global_cache / DB   │
  │  (ETL Worker)   │      └──────────┬───────────┘
  └─────────────────┘                 │
                                      ▼
                          ┌──────────────────────┐
                          │  FastAPI (read-only)  │
                          │  /intelligence/global │
                          │  /timeseries/global   │
                          │  /backtest            │
                          └──────────────────────┘

Production Migration: replace global_cache with Redis reads.
"""
import logging
import pandas as pd
from fastapi import FastAPI, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from . import schemas
from ..db.database import engine, Base, get_db
from ..db.models import TimeSeriesData
from .cache import global_cache
from ..services.macro_intelligence import get_intelligence_snapshot
from ..services.correlation import calculate_correlations
from ..services.alert_engine import evaluate_alerts
from ..workers.etl_worker import start_scheduler, stop_scheduler, run_etl_job

logger = logging.getLogger(__name__)

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="MacroPulse Global API",
    description="Professional Macro Intelligence Terminal — Read-only API layer.",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─────────────────────────────────────────────────────────────────────────────
# STARTUP / SHUTDOWN
# ─────────────────────────────────────────────────────────────────────────────

@app.on_event("startup")
def startup_event():
    """Load last known state from DB, then start the background ETL scheduler."""
    _warm_cache_from_db()
    start_scheduler(interval_minutes=30)   # ETL runs every 30 min automatically
    logger.info("[API] MacroPulse API started. ETL scheduler active.")


@app.on_event("shutdown")
def shutdown_event():
    stop_scheduler()
    logger.info("[API] MacroPulse API stopped. Scheduler halted.")


def _warm_cache_from_db():
    """
    On startup, hydrate the in-memory cache from the last persisted DB state.
    This ensures the API can serve data immediately even before the first ETL run.
    """
    from backend.db.database import SessionLocal
    db = SessionLocal()
    try:
        records = db.query(TimeSeriesData).all()
        if not records:
            logger.warning("[API] Database is empty — cache not warmed. Trigger ETL manually.")
            return

        df = pd.DataFrame([
            {"date": r.date, "value": r.value, "series_type": r.series_type}
            for r in records
        ])
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date")

        intelligence = get_intelligence_snapshot(df, sentiment_score=50)
        intelligence["correlations"] = calculate_correlations(df)
        intelligence["alerts"]       = evaluate_alerts(intelligence, df)

        global_cache["snapshot"]     = df
        global_cache["intelligence"] = intelligence

        logger.info(f"[API] Cache warmed: {len(records)} records | "
                    f"Regime={intelligence.get('regime')} | Risk={intelligence.get('risk_score')}")
    except Exception as e:
        logger.error(f"[API] Cache warm failed: {e}", exc_info=True)
    finally:
        db.close()


# ─────────────────────────────────────────────────────────────────────────────
# ETL TRIGGER (manual override — doesn't block the HTTP response)
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/etl/run", tags=["ETL"])
def trigger_etl(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    Manually trigger the ETL pipeline. Runs in the background (non-blocking).
    Normally the scheduler runs this automatically every 30 minutes.
    """
    background_tasks.add_task(run_etl_job)
    return {"message": "ETL job queued in background.", "status": "accepted"}


# ─────────────────────────────────────────────────────────────────────────────
# INTELLIGENCE ENDPOINTS (read-only)
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/intelligence/global", tags=["Intelligence"])
def get_global_intelligence():
    """
    Returns the latest consolidated macro intelligence snapshot from cache.
    Updated automatically every 30 minutes by the ETL scheduler.
    """
    intell = global_cache.get("intelligence")
    df     = global_cache.get("snapshot")

    if intell is None or df is None or df.empty:
        return {"message": "Cache is empty. ETL may not have run yet.", "data": None}

    def _safe_last(series_type: str):
        rows = df[df["series_type"] == series_type]["value"]
        return float(rows.iloc[-1]) if not rows.empty else 0.0

    sp500_change = df[df["series_type"] == "^GSPC"]["value"].pct_change().iloc[-1] if not df.empty else 0.0
    vix   = _safe_last("^VIX")
    gold  = _safe_last("GC=F")

    return {
        # Intelligence
        "regime":          intell.get("regime"),
        "risk_score":      intell.get("risk_score"),
        "risk_breakdown":  intell.get("risk_breakdown"),
        "active_weights":  intell.get("active_weights"),     # New: shows dynamic weights
        "positioning":     intell.get("positioning"),
        "ai_thesis":       intell.get("ai_thesis"),
        "correlations":    intell.get("correlations"),
        "alerts":          intell.get("alerts", []),          # New: proactive alert list
        "brasil":          intell.get("brasil"),
        # KPIs
        "kpis": {
            "vix":               vix,
            "sp500_daily_change": round(float(sp500_change) * 100, 2),
            "gold_price":        gold,
            "risk_score":        intell.get("risk_score"),
            "regime":            intell.get("regime"),
            "regime_explanation": intell.get("explanation"),
            "regime_color":      intell.get("color"),
            "regime_trend":      intell.get("trend"),
        },
        "news":     global_cache.get("news", [])[:10],
        "activity": global_cache.get("activity", {}),
    }


@app.get("/timeseries/global", response_model=schemas.TimeSeriesResponse, tags=["Data"])
def get_global_timeseries():
    """Returns the full time-series dataset from cache."""
    df = global_cache.get("snapshot")
    if df is None or df.empty:
        return {"data": []}
    return {"data": df.to_dict("records")}


# ─────────────────────────────────────────────────────────────────────────────
# BACKTESTING ENDPOINT
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/backtest", tags=["Validation"])
def run_backtest_endpoint():
    """
    Validate the Risk Engine against historical crisis events.
    Requires historical data — run /etl/historical-ingest first.
    """
    from ..services.backtest_engine import run_backtest
    df = global_cache.get("snapshot")
    return run_backtest(df)


@app.post("/etl/historical-ingest", tags=["ETL"])
def trigger_historical_ingest(db: Session = Depends(get_db)):
    """
    Backfill long-run historical data (2005–present).
    Covers 2008 Financial Crisis and 2020 COVID-19 crash windows.
    This is a long-running operation — may take 1-2 minutes.
    """
    from ..etl.historical_ingest import ingest_historical_data
    summary = ingest_historical_data(db)
    # Refresh cache with the new extended dataset
    _warm_cache_from_db()
    return {"message": "Historical ingestion complete.", "summary": summary}
