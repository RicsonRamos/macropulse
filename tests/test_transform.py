import pytest
import pandas as pd
from backend.etl.transform import transform_data, calculate_kpis_and_index

def test_transform_data_forward_fill():
    """Valida a capacidade do Transform de alinhar as datas e aplicar FFill no IPCA"""
    df_ipca = pd.DataFrame({
        "date": pd.to_datetime(["2023-01-01"]),
        "value": [0.5]
    })
    # Selic tem dado todo dia
    df_selic = pd.DataFrame({
        "date": pd.to_datetime(["2023-01-01", "2023-01-02", "2023-01-03"]),
        "value": [13.75, 13.75, 13.75]
    })
    # Dolar também
    df_usd = pd.DataFrame({
        "date": pd.to_datetime(["2023-01-01", "2023-01-02", "2023-01-03"]),
        "value": [5.10, 5.15, 5.20]
    })
    
    merged = transform_data(df_ipca, df_selic, df_usd)
    
    assert len(merged) == 3, "Deveria ter explodido os 3 dias do IPCA mensal preenchendo as colunas vazias"
    assert "ipca_value" in merged.columns
    # Verifica Forward Fill
    assert merged[merged["date"] == "2023-01-02"]["ipca_value"].iloc[0] == 0.5, "O valor do IPCA referente a janeiro não populou ffill pro dia 2."

def test_calculate_kpis_index():
    """Valida o preenchimento estatístico do score macro de Z-Score limitando 0 a 100"""
    # Precisamos de 30+ registros pro rolling do pandas disparar senao volta NaN.
    dates = pd.date_range("2023-01-01", periods=40, freq="D")
    df_merged = pd.DataFrame({
        "date": dates,
        "ipca_value": [0.5] * 40,
        "selic_value": [13.75] * 40,
        "usd_value": [5.0 + (i * 0.01) for i in range(40)]  # dólar subindo lento
    })
    
    result = calculate_kpis_and_index(df_merged)
    
    # Ele clipa nan em calculo de std desvio mas deve voltar algo
    assert "macro_stress_index" in result.columns
    assert "macro_stress_index_normalized" in result.columns
    
    # As the window is 252 but min_periods is 30, we should have results for the last 10 rows
    assert not result.empty, "Rolling calculations failed or dropped everything"
    
    normalized_val = result["macro_stress_index_normalized"].iloc[-1]
    assert 0 <= normalized_val <= 100, f"Score Macros precisa estar base 100! Retornou: {normalized_val}"
