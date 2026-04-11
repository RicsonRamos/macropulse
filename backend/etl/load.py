import pandas as pd
from typing import List
from sqlalchemy.orm import Session
from ..db.models import TimeSeriesData, MacroStatus
from ..services.insights import generate_executive_insight, analyze_macro_regime
from ..services.prediction import forecast_macro_series
import json

def load_data_to_db(db: Session, df_processed: pd.DataFrame):
    """
    Carrega dados processados e gera as inteliências/predições para o BD.
    """
    if df_processed.empty:
        return
        
    db.query(TimeSeriesData).delete()
    db.query(MacroStatus).delete()
    db.commit()
    
    # 1. Inserindo Time Series
    ts_objects = []

    # Se o DataFrame for o formato genérico (date, value, series_type)
    if 'series_type' in df_processed.columns:
        # ── Drop NaN values before insert — prevents NOT NULL constraint failure ──
        clean_df = df_processed.dropna(subset=['value'])
        dropped = len(df_processed) - len(clean_df)
        if dropped > 0:
            print(f"[load_data_to_db] Dropped {dropped} rows with NaN values before DB insert.")

        for _, row in clean_df.iterrows():
            ts_objects.append(TimeSeriesData(
                date=pd.to_datetime(row['date']).date(),  # datetime.date — required by SQLAlchemy Date column
                series_type=str(row['series_type']),
                value=float(row['value'])
            ))
    else:
        # Fallback para o formato antigo de colunas específicas
        for _, row in df_processed.iterrows():
            if not pd.isna(row.get('ipca_value')):
                ts_objects.append(TimeSeriesData(date=row['date'], series_type='IPCA', value=row['ipca_value']))
            if not pd.isna(row.get('ipca_12m_value')):
                ts_objects.append(TimeSeriesData(date=row['date'], series_type='IPCA_12M', value=row['ipca_12m_value']))
            if not pd.isna(row.get('selic_value')):
                ts_objects.append(TimeSeriesData(date=row['date'], series_type='SELIC', value=row['selic_value']))
            if not pd.isna(row.get('usd_value')):
                ts_objects.append(TimeSeriesData(date=row['date'], series_type='USD_BRL', value=row['usd_value']))

    batch_size = 5000
    for i in range(0, len(ts_objects), batch_size):
        db.bulk_save_objects(ts_objects[i:i+batch_size])
    db.commit()
    
    # 2. Gerando Previsões ARIMA e Status (somente no formato Brasil legado)
    # O formato global (series_type) não possui as colunas específicas necessárias.
    has_legacy_columns = 'ipca_12m_value' in df_processed.columns

    if not has_legacy_columns:
        print("[load_data_to_db] Global format detected — skipping MacroStatus and ARIMA blocks.")
        return

    predictions_json_str = forecast_macro_series(df_processed, steps=90)

    # 3. Inserindo Status com Regimes e Scores
    status_objects = []
    
    for _, row in df_processed.iterrows():
        
        # Apenas processa se tivermos dados suficientes na row para gerar insights
        ipca = row.get('ipca_12m_value', 0)
        selic = row.get('selic_value', 0)
        usd_vol_30d = row.get('usd_vol_30d', 0)
        stress_idx = row.get('macro_stress_index_normalized', 50)
        
        # Trends Simplificados
        if ipca > 6.0: inflation_trend = "Alta"
        elif ipca < 3.5: inflation_trend = "Baixa"
        else: inflation_trend = "Estável"
        
        if selic > 10.0: selic_level = "Restritivo"
        elif selic < 6.0: selic_level = "Estimulativo"
        else: selic_level = "Neutro"
        
        if usd_vol_30d > 15.0: usd_vol = "Alta"
        else: usd_vol = "Baixa"
        
        # Engine Analítica: Regimes
        regime, cause = analyze_macro_regime(
            ipca_12m_delta=row.get('ipca_12m_delta', 0),
            selic_delta=row.get('selic_delta', 0),
            usd_vol=usd_vol_30d,
            ipca_value=ipca
        )
        insight = generate_executive_insight(stress_idx, regime, cause)
        
        # Criação do objeto DB
        status_objects.append(MacroStatus(
            date=row['date'],
            macro_health_score=row.get('macro_health_score', 50),
            macro_stress_index=stress_idx,
            fx_stress_index=row.get('fx_stress_index', 0),
            real_interest_rate=row.get('real_interest_rate', 0),
            macro_regime=regime,
            inflation_trend=inflation_trend,
            selic_level=selic_level,
            currency_volatility=usd_vol,
            executive_summary=insight,
            ipca_12m_delta=row.get('ipca_12m_delta', 0),
            selic_delta=row.get('selic_delta', 0),
            usd_delta=row.get('usd_delta', 0),
            stress_delta=row.get('stress_delta', 0),
            predictions_json=json.loads(predictions_json_str) if predictions_json_str != "{}" else None
        ))

    for i in range(0, len(status_objects), batch_size):
        db.bulk_save_objects(status_objects[i:i+batch_size])
    db.commit()
