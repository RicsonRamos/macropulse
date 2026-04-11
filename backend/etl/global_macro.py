import os
import yfinance as yf
from fredapi import Fred
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

FRED_KEY = os.getenv("FRED_API_KEY")

def fetch_yfinance_data(tickers: list, period="1y"):
    """
    Busca dados de mercados globais via Yahoo Finance.
    Tickers sugeridos: ^GSPC (S&P 500), ^VIX (Volatilidade), EURUSD=X (Moeda).
    """
    data_dict = {}
    for ticker in tickers:
        try:
            ticker_obj = yf.Ticker(ticker)
            df = ticker_obj.history(period=period)
            if not df.empty:
                # Normaliza para colunas date e value
                df = df.reset_index()
                df = df.rename(columns={'Date': 'date', 'Close': 'value'})
                df['date'] = df['date'].dt.date
                df['series_type'] = ticker
                data_dict[ticker] = df[['date', 'value', 'series_type']]
        except Exception as e:
            print(f"Erro ao buscar ticker {ticker}: {e}")
    return data_dict

def fetch_fred_data(series_ids: list, lookback_days=365):
    """
    Busca dados macro via FRED (St. Louis Fed).
    IDs sugeridos: T10Y2Y (Curva de juros), UNRATE (Desemprego EUA), CPIAUCSL (Inflação EUA).
    """
    if not FRED_KEY:
        print("FRED_API_KEY não configurada.")
        return {}

    fred = Fred(api_key=FRED_KEY)
    data_dict = {}
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=lookback_days)

    for s_id in series_ids:
        try:
            series = fred.get_series(s_id, observation_start=start_date, observation_end=end_date)
            if not series.empty:
                df = series.reset_index()
                df.columns = ['date', 'value']
                df['date'] = df['date'].dt.date
                df['series_type'] = s_id
                data_dict[s_id] = df
        except Exception as e:
            print(f"Erro ao buscar série FRED {s_id}: {e}")
    return data_dict

import requests

def fetch_bcb_data(series_ids: dict):
    """
    Busca dados do Banco Central do Brasil (SGS).
    Ex: 11 (Selic), 433 (IPCA).
    """
    data_dict = {}
    for label, s_id in series_ids.items():
        try:
            url = f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{s_id}/dados/ultimos/1?formato=json"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                json_data = response.json()
                if json_data:
                    last_point = json_data[0]
                    # Formato do BCB: {'data': 'dd/mm/aaaa', 'valor': 'val'}
                    date_obj = datetime.strptime(last_point['data'], '%d/%m/%Y').date()
                    value = float(last_point['valor'])
                    
                    df = pd.DataFrame([{
                        'date': date_obj,
                        'value': value,
                        'series_type': f"BCB_{label}"
                    }])
                    data_dict[label] = df
        except Exception as e:
            print(f"Erro ao buscar série BCB {label}: {e}")
    return data_dict

def fetch_fear_greed_index():
    """
    Busca o Crypto Fear & Greed Index da Alternative.me.
    Retorna um valor de 0 a 100.
    """
    try:
        url = "https://api.alternative.me/fng/"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data['data']:
                val = float(data['data'][0]['value'])
                ts = datetime.fromtimestamp(int(data['data'][0]['timestamp'])).date()
                return pd.DataFrame([{
                    'date': ts,
                    'value': val,
                    'series_type': 'FEAR_GREED'
                }])
    except Exception as e:
        print(f"Erro ao buscar Fear & Greed: {e}")
    return pd.DataFrame()

def get_global_macro_snapshot():
    """
    Gera um DataFrame consolidado com indicadores globais, brasileiros e cripto.
    """
    # Mercados: S&P 500, VIX, Ouro, EUR/USD, IBOVESPA, USD/BRL, BITCOIN
    market_tickers = ["^GSPC", "^VIX", "GC=F", "EURUSD=X", "^BVSP", "USDBRL=X", "BTC-USD"]
    # FRED: 10Y-2Y Spread, Fed Funds Rate, US Inflation
    fred_ids = ["T10Y2Y", "FEDFUNDS", "CPIAUCSL"]
    # BCB (Brasil): Selic (11), IPCA (433)
    bcb_ids = {"SELIC": 11, "IPCA": 433}
    
    markets = fetch_yfinance_data(market_tickers)
    macros = fetch_fred_data(fred_ids)
    brasil = fetch_bcb_data(bcb_ids)
    fng = fetch_fear_greed_index()
    
    all_dfs = list(markets.values()) + list(macros.values()) + list(brasil.values())
    if not fng.empty:
        all_dfs.append(fng)
    
    if not all_dfs:
        return pd.DataFrame()
        
    return pd.concat(all_dfs, ignore_index=True)
