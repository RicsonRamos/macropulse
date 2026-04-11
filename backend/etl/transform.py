import pandas as pd
import numpy as np

def transform_data(df_ipca: pd.DataFrame, df_ipca_12m: pd.DataFrame, df_selic: pd.DataFrame, df_usd: pd.DataFrame):
    """
    Mescla e interpola as séries temporais. 
    Retorna o DataFrame limpo contendo informações padronizadas para análise diária.
    """
    if df_selic.empty or df_usd.empty:
        return pd.DataFrame()
        
    # Renomeando colunas
    if not df_ipca.empty:
        df_ipca = df_ipca.rename(columns={'value': 'ipca_value'})[['date', 'ipca_value']]
    if not df_ipca_12m.empty:
        df_ipca_12m = df_ipca_12m.rename(columns={'value': 'ipca_12m_value'})[['date', 'ipca_12m_value']]
        
    df_selic = df_selic.rename(columns={'value': 'selic_value'})[['date', 'selic_value']]
    df_usd = df_usd.rename(columns={'value': 'usd_value'})[['date', 'usd_value']]
    
    min_date = min([df['date'].min() for df in [df_ipca, df_ipca_12m, df_selic, df_usd] if not df.empty])
    max_date = max([df['date'].max() for df in [df_ipca, df_ipca_12m, df_selic, df_usd] if not df.empty])
    
    df_dates = pd.DataFrame({'date': pd.date_range(min_date, max_date, freq='D')})
    
    df_merged = df_dates
    for df in [df_ipca, df_ipca_12m, df_selic, df_usd]:
        if not df.empty:
            df_merged = pd.merge(df_merged, df, on='date', how='left')
            
    # Forward fill preenche os buracos de finais de semana ou meses incompletos
    for col in df_merged.columns:
        if col != 'date':
            df_merged[col] = df_merged[col].ffill()
            
    df_merged = df_merged.dropna().reset_index(drop=True)
    return df_merged

def calculate_kpis_and_index(df_merged: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula variações (trend), volatilidade, e os Core Scores.
    """
    if df_merged.empty:
        return df_merged
        
    df = df_merged.copy()
    
    # 1. Juro Real (Selic Nível - IPCA 12M Acumulado Nível)
    if 'selic_value' in df.columns and 'ipca_12m_value' in df.columns:
        df['real_interest_rate'] = df['selic_value'] - df['ipca_12m_value']
    else:
        df['real_interest_rate'] = 0.0

    # 2. FX Stress Index e Volatilidade
    df['usd_returns'] = df['usd_value'].pct_change()
    df['usd_vol_30d'] = df['usd_returns'].rolling(window=30).std() * np.sqrt(252)
    # FX Stress usa usd nominais normais misturado com volatilidade para gerar panico.
    df['fx_stress_index'] = (df['usd_value'] / df['usd_value'].rolling(window=252).mean()) * (1 + df['usd_vol_30d'])

    # 3. Deltas / Momentum (Comparação com 30 dias atrás)
    df['ipca_12m_delta'] = df['ipca_12m_value'] - df['ipca_12m_value'].shift(30)
    df['selic_delta'] = df['selic_value'] - df['selic_value'].shift(30)
    df['usd_delta'] = df['usd_value'] - df['usd_value'].shift(30)
    df['stress_delta'] = 0.0 # Placeholder it gets defined later
    
    # 4. Z-scores dinâmicos para Macro Stress
    window = 252
    for col in ['ipca_12m_value', 'selic_value', 'usd_value']:
        if col in df.columns:
            mean_col = df[col].rolling(window=window, min_periods=30).mean()
            std_col = df[col].rolling(window=window, min_periods=30).std()
            df[f'{col}_zscore'] = (df[col] - mean_col) / (std_col + 1e-6)
    
    mean_vol = df['usd_vol_30d'].rolling(window=window, min_periods=30).mean()
    std_vol = df['usd_vol_30d'].rolling(window=window, min_periods=30).std()
    df['usd_vol_zscore'] = (df['usd_vol_30d'] - mean_vol) / (std_vol + 1e-6)
    
    # MSI Ponderado
    df['macro_stress_index'] = (
        (df.get('ipca_12m_value_zscore', 0).clip(lower=0) * 0.35) + 
        (df.get('selic_value_zscore', 0).clip(lower=0) * 0.35) + 
        (df.get('usd_vol_zscore', 0).clip(lower=0) * 0.30)
    )
    
    rolling_min = df['macro_stress_index'].rolling(window=504, min_periods=30).min()
    rolling_max = df['macro_stress_index'].rolling(window=504, min_periods=30).max()
    df['macro_stress_index_normalized'] = 100 * (df['macro_stress_index'] - rolling_min) / (rolling_max - rolling_min + 1e-6)
    
    df['stress_delta'] = df['macro_stress_index_normalized'] - df['macro_stress_index_normalized'].shift(30)

    # 5. Macro Health Score (Inverso do Stress com buffer de liquidez ideal)
    # Ex: Um score próximo de 100 significa excelência Macro.
    df['macro_health_score'] = 100 - df['macro_stress_index_normalized']
    
    df = df.dropna()
    return df
