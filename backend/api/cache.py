"""
backend/api/cache.py

Shared in-memory cache for the API serving layer.
In production (with Celery + Redis), replace this module with a Redis client.

Migration Path:
  import redis, json
  r = redis.Redis(host='localhost', port=6379, db=0)
  
  # Write: r.set('global_cache', json.dumps(global_cache))
  # Read:  global_cache = json.loads(r.get('global_cache'))
"""
import pandas as pd

global_cache: dict = {
    "snapshot": None,       # pd.DataFrame — latest market data
    "news": [],             # list[dict] — processed news articles
    "activity": {           # dict — aviation/maritime activity
        "active_flights": 0,
        "active_vessels": 0,
        "congestion_status": "Unknown",
        "logistics_impact": "Unknown"
    },
    "intelligence": None,   # dict — full intelligence snapshot
}
