import pandas as pd
from statsmodels.tsa.arima.model import ARIMA
import warnings
import json

warnings.filterwarnings("ignore")

def forecast_macro_series(df: pd.DataFrame, steps: int = 90) -> str:
    """
    Treina um modelo ARIMA muito rápido para prever 90 dias a frente as variáveis chave.
    Retorna um JSON string estruturado.
    """
    if df.empty or len(df) < 100:
        return "{}"
        
    predictions = {}
    
    # Vamos prever IPCA 12m, USD e SELIC
    targets = {
        'ipca_12m_value': (1,0,0), # AR1 Simples
        'usd_value': (1,1,0),      # Random walk with drift approx
        'selic_value': (1,0,0)     # Alta persistencia
    }
    
    for col, order in targets.items():
        if col in df.columns:
            try:
                # Pega ultimos 500 dias para o treino ser rápido
                series = df[col].dropna().tail(500).values
                model = ARIMA(series, order=order)
                fitted = model.fit()
                forecasts = fitted.forecast(steps=steps)
                
                predictions[col] = list(forecasts)
            except Exception as e:
                print(f"Erro no ARIMA para {col}: {e}")
                predictions[col] = []
                
    return json.dumps(predictions)
