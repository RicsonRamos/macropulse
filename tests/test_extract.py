import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from backend.etl.extract import fetch_sgs_data, fetch_all_macro_series

# Mock raw json response from Banco Central
mock_sgs_response = [
    {"data": "01/01/2023", "valor": "5.20"},
    {"data": "02/01/2023", "valor": "5.30"}
]

@patch("backend.etl.extract.requests.get")
def test_fetch_sgs_data_success(mock_get):
    """Garante que a extração mapeia os tipos corretos para DataFrame usando requests.get mockado"""
    # Moca Response 200 OK
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_sgs_response
    mock_get.return_value = mock_response

    df = fetch_sgs_data(1, "01/01/2023", "02/01/2023")
    
    assert not df.empty, "DataFrame extraído não deve estar vazio"
    assert "date" in df.columns, "Coluna date necessária"
    assert "value" in df.columns, "Coluna value necessária"
    assert pd.api.types.is_datetime64_any_dtype(df["date"]), "A data deve ser formato datetime do pandas"
    assert df.iloc[0]["value"] == 5.20, "O valor numérico (MOCK) de carga inicial deve bater com o primeiro float validado"

@patch("backend.etl.extract.fetch_sgs_data")
def test_fetch_all_macro_series(mock_fetch):
    """Testa o acoplamento do disparador geral, garantindo que as labels 'types' não se percam"""
    df_mock = pd.DataFrame({
        "date": pd.to_datetime(["2023-01-01", "2023-01-02"]),
        "value": [10.0, 11.0]
    })
    # Forçar o mock retornar o nosso dataframe pra qualquer sub-request
    mock_fetch.return_value = df_mock.copy()
    
    df_ipca, df_selic, df_usd = fetch_all_macro_series(lookback_days=30)
    
    assert mock_fetch.call_count == 3, "Deveria solicitar API BCB para as 3 séries (Inflação, Juros e Dólar)"
    assert df_ipca["series_type"].iloc[0] == "IPCA", "O rótulo de inflação se perdeu na extração combinada"
    assert df_selic["series_type"].iloc[0] == "SELIC", "O rótulo de Selic se perdeu"
    assert df_usd["series_type"].iloc[0] == "USD_BRL", "O rótulo de Moeda se perdeu"
