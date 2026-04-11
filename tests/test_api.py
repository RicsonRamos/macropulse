import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch

from backend.api.main import app
from backend.db.database import get_db

client = TestClient(app)

# Override do Banco de dados com Mock vazio
def override_get_db():
    mock_db = MagicMock()
    # Mockando a chain the sqlalchemy `db.query(Status).order_by().first()`
    mock_status = MagicMock()
    mock_status.date = "2023-01-01"
    mock_status.macro_stress_index = 85.5
    mock_status.executive_summary = "Mocked Instável"
    
    mock_ts = MagicMock()
    mock_ts.value = 13.75
    
    # Criamos um mock chainable limitando o retorno do .first()
    mock_query = MagicMock()
    mock_query.order_by.return_value.first.return_value = mock_status
    mock_query.filter.return_value.first.return_value = mock_ts
    
    mock_db.query.return_value = mock_query
    
    try:
        yield mock_db
    finally:
        pass

app.dependency_overrides[get_db] = override_get_db

@patch("backend.api.main.run_etl_task")
def test_etl_run_endpoint_sync_mocked(mock_etl_task):
    """Garante que a chamada POST chame o serviço interno passando a Session sem de fato fazer HTTP network pra fora"""
    response = client.post("/etl/run")
    assert response.status_code == 200
    assert response.json()["message"] == "Processo de ETL inicializado e concluído com sucesso."
    mock_etl_task.assert_called_once()  # O motor real foi bypassado aqui

def test_get_kpis_mocked():
    """Valida leitura sintática dos schemas da API com banco mockado"""
    response = client.get("/kpis")
    assert response.status_code == 200
    data = response.json()
    assert data["macro_stress_index"] == 85.5
    assert data["selic_latest"] == 13.75 # Pegou do submock TimeSeries
    assert data["executive_summary"] == "Mocked Instável"
