from pydantic import BaseModel
from typing import List, Optional
from datetime import date

class GlobalMacroKPIs(BaseModel):
    vix: float
    sp500_daily_change: float
    gold_price: float
    risk_score: float
    regime: str
    regime_color: str
    regime_explanation: str

class NewsItem(BaseModel):
    title: str
    url: str
    source: str
    sentiment: str
    summary: str

class BrasilKPIs(BaseModel):
    selic: Optional[float] = None
    ipca: Optional[float] = None
    ibov_ret: Optional[float] = None
    usdbrl: Optional[float] = None
    btc: Optional[float] = None
    btc_ret: Optional[float] = None
    fng: Optional[float] = None

class RealWorldActivity(BaseModel):
    active_flights: Optional[int] = 0
    active_vessels: Optional[int] = 0
    congestion_status: Optional[str] = "Normal"
    logistics_impact: Optional[str] = "Low"

class GlobalIntelligenceResponse(BaseModel):
    regime: str
    risk_score: float
    color: str
    trend: str
    explanation: str
    brasil: Optional[BrasilKPIs] = None
    kpis: Optional[GlobalMacroKPIs] = None
    news: Optional[List[NewsItem]] = []
    activity: Optional[RealWorldActivity] = None

class TimeSeriesPoint(BaseModel):
    date: date
    series_type: str
    value: float

class TimeSeriesResponse(BaseModel):
    data: List[TimeSeriesPoint]

class ETLRunResponse(BaseModel):
    message: str
