from sqlalchemy import Column, Integer, String, Float, Date, DateTime, Boolean, JSON
from sqlalchemy.sql import func
from .database import Base

class TimeSeriesData(Base):
    __tablename__ = "time_series_data"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, index=True, nullable=False)
    series_type = Column(String, index=True, nullable=False) # "IPCA", "IPCA_12M", "SELIC", "USD_BRL"
    value = Column(Float, nullable=False)

class MacroStatus(Base):
    __tablename__ = "macro_status"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, unique=True, index=True, nullable=False)
    
    # Scores & Indexes
    macro_health_score = Column(Float, nullable=False, default=50.0)
    macro_stress_index = Column(Float, nullable=False)
    fx_stress_index = Column(Float, nullable=False, default=0.0)
    real_interest_rate = Column(Float, nullable=False, default=0.0)
    
    # Regimes and Intelligence
    macro_regime = Column(String, nullable=False, default="Neutro")
    inflation_trend = Column(String, nullable=False) 
    selic_level = Column(String, nullable=False) 
    currency_volatility = Column(String, nullable=False) 
    executive_summary = Column(String, nullable=False)
    
    # Deltas
    ipca_12m_delta = Column(Float, nullable=False, default=0.0)
    selic_delta = Column(Float, nullable=False, default=0.0)
    usd_delta = Column(Float, nullable=False, default=0.0)
    stress_delta = Column(Float, nullable=False, default=0.0)
    
    # Previsões
    predictions_json = Column(JSON, nullable=True) # Guarda dados do ARIMA

    created_at = Column(DateTime(timezone=True), server_default=func.now())
