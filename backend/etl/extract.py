import requests
import pandas as pd
from datetime import datetime, timedelta
import time

def fetch_sgs_data(serie_codigo: int, data_inicial: str, data_final: str, retries: int = 3) -> pd.DataFrame:
    """
    Busca dados da API SGS do Banco Central do Brasil com Retry e Backoff Exponencial.
    Retorna um pandas DataFrame com colunas 'date' (datetime) e 'value' (float).
    """
    url = f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{serie_codigo}/dados?formato=json&dataInicial={data_inicial}&dataFinal={data_final}"
    
    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=20)
            
            # Se for 502, estourar exception pro fallback
            if response.status_code == 502:
                print(f"BCB 502 Bad Gateway na série {serie_codigo}. Tentativa {attempt + 1}/{retries}")
                response.raise_for_status()
                
            response.raise_for_status()
            data = response.json()
            
            if not data:
                return pd.DataFrame(columns=['date', 'value'])
                
            df = pd.DataFrame(data)
            df['date'] = pd.to_datetime(df['data'], format='%d/%m/%Y')
            df['value'] = pd.to_numeric(df['valor'])
            df = df.drop(columns=['data', 'valor']).sort_values('date')
            
            return df
            
        except requests.exceptions.RequestException as e:
            if attempt < retries - 1:
                sleep_time = 2 ** attempt  # 1s, 2s, 4s...
                time.sleep(sleep_time)
            else:
                print(f"Falha definitiva ao buscar série {serie_codigo} no BCB: {e}")
                return pd.DataFrame(columns=['date', 'value'])

def fetch_all_macro_series(lookback_days: int = 365 * 3):
    """
    Busca as séries solicitadas:
    - IPCA Mensal (433)
    - IPCA 12 Meses Acumulado (13522)
    - Selic (11) - Diário
    - USD_BRL (1) - Diário
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=lookback_days)
    
    start_str = start_date.strftime("%d/%m/%Y")
    end_str = end_date.strftime("%d/%m/%Y")
    
    df_ipca = fetch_sgs_data(433, start_str, end_str)
    if not df_ipca.empty:
        df_ipca['series_type'] = "IPCA"
        
    df_ipca_12m = fetch_sgs_data(13522, start_str, end_str)
    if not df_ipca_12m.empty:
        df_ipca_12m['series_type'] = "IPCA_12M"
        
    df_selic = fetch_sgs_data(11, start_str, end_str)
    if not df_selic.empty:
        df_selic['series_type'] = "SELIC"
        
    df_usd = fetch_sgs_data(1, start_str, end_str)
    if not df_usd.empty:
        df_usd['series_type'] = "USD_BRL"
        
    return df_ipca, df_ipca_12m, df_selic, df_usd
