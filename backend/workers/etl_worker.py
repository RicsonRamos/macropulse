"""
backend/workers/etl_worker.py

Dedicated ETL background worker using APScheduler.
Architecture is modular: swap BackgroundScheduler → Celery task in production.

Production Migration Path:
  1. Install: pip install celery redis
  2. Replace run_etl_job() with @celery_app.task decorator
  3. Replace scheduler.start() with: celery -A backend.workers.celery_worker worker
"""
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)

# Singleton scheduler — importado pelo main.py na startup
scheduler = BackgroundScheduler(timezone="UTC")


def run_etl_job():
    """
    Core ETL job. Runs on schedule. Fully decoupled from the API serving layer.
    Import happens inside to avoid circular dependencies at import time.
    """
    logger.info("[ETL Worker] Starting scheduled ETL run...")
    try:
        from backend.db.database import SessionLocal
        from backend.etl.global_macro import get_global_macro_snapshot
        from backend.etl.news_engine import get_news_intelligence
        from backend.etl.activity_tracking import get_real_world_activity
        from backend.etl.load import load_data_to_db
        from backend.services.macro_intelligence import get_intelligence_snapshot
        from backend.services.correlation import calculate_correlations
        from backend.services.alert_engine import evaluate_alerts
        from backend.api.cache import global_cache

        db = SessionLocal()
        try:
            # 1. Fetch all data sources
            df_macro = get_global_macro_snapshot()
            news_data = get_news_intelligence()
            activity = get_real_world_activity()

            # 2. Build intelligence snapshot
            intelligence = get_intelligence_snapshot(df_macro, news_data["sentiment_score"])
            intelligence["ai_thesis"] = news_data["ai_thesis"]
            intelligence["correlations"] = calculate_correlations(df_macro)

            # 3. Evaluate proactive alerts
            intelligence["alerts"] = evaluate_alerts(intelligence, df_macro)

            # 4. Persist to DB
            load_data_to_db(db, df_macro)
            logger.info(f"[ETL Worker] Persisted {len(df_macro)} records to DB.")

            # 5. Update shared cache (in production: write to Redis)
            global_cache["snapshot"] = df_macro
            global_cache["news"] = news_data["articles"]
            global_cache["activity"] = activity
            global_cache["intelligence"] = intelligence

            logger.info(f"[ETL Worker] ETL complete. Regime={intelligence.get('regime')} RiskScore={intelligence.get('risk_score')}")
        finally:
            db.close()

    except Exception as e:
        logger.error(f"[ETL Worker] ETL job failed: {e}", exc_info=True)


def start_scheduler(interval_minutes: int = 30):
    """
    Start the APScheduler background scheduler.
    interval_minutes: how often the ETL runs (default: 30 min).
    """
    if scheduler.running:
        logger.warning("[ETL Worker] Scheduler already running. Skipping start.")
        return

    scheduler.add_job(
        run_etl_job,
        trigger=IntervalTrigger(minutes=interval_minutes),
        id="etl_global",
        name="MacroPulse Global ETL",
        replace_existing=True,
        max_instances=1,       # Prevent overlapping runs
        coalesce=True,         # If missed, run once (not multiple times)
    )
    scheduler.start()
    logger.info(f"[ETL Worker] Scheduler started. ETL interval: every {interval_minutes} min.")


def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("[ETL Worker] Scheduler stopped.")
