import pandas as pd
import numpy as np

def calculate_correlations(df_macro: pd.DataFrame):
    """
    Calcula correlações cruzadas entre ativos chave para detectar estresse sistêmico.
    """
    if df_macro.empty or len(df_macro) < 30:
        return []

    # Pivot de dados para formato (Date, Assets...)
    # Precisamos de pelo menos duas séries para correlacionar
    try:
        df_pivot = df_macro.pivot(index='date', columns='series_type', values='value')
        
        # Filtra ativos principais para não poluir o cálculo
        main_assets = ['^GSPC', '^VIX', 'BTC-USD', 'GC=F', 'USDBRL=X', 'T10Y2Y']
        df_pivot = df_pivot[[c for c in main_assets if c in df_pivot.columns]]
        
        # Calcula retornos percentuais para correlação estatística correta
        df_returns = df_pivot.pct_change().dropna()
        
        if df_returns.empty:
            return []
            
        corr_matrix = df_returns.corr()
        
        # Extrai correlações interessantes
        signals = []
        
        # 1. VIX vs S&P 500 (Geralmente negativa alta)
        if '^VIX' in corr_matrix.columns and '^GSPC' in corr_matrix.columns:
            vix_sp = corr_matrix.loc['^VIX', '^GSPC']
            if vix_sp > -0.5: # Anomalia: VIX e Mercado subindo juntos ou correlação fraca
                signals.append({"pair": "VIX vs S&P 500", "corr": round(vix_sp, 2), "status": "Anomaly Detected"})
            else:
                signals.append({"pair": "VIX vs S&P 500", "corr": round(vix_sp, 2), "status": "Standard"})

        # 2. Bitcoin vs USD (Geralmente negativa)
        if 'BTC-USD' in corr_matrix.columns and 'USDBRL=X' in corr_matrix.columns:
            btc_usd = corr_matrix.loc['BTC-USD', 'USDBRL=X']
            signals.append({"pair": "BTC vs USD", "corr": round(btc_usd, 2), "status": "Neutral"})

        return signals
    except Exception as e:
        print(f"Erro no cálculo de correlação: {e}")
        return []
