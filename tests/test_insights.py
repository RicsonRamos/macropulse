from backend.services.insights import generate_executive_insight

def test_generate_executive_insight_stable():
    """Valida se uma economia perfeita com juros baixos retorna o insight natural esperado"""
    insight = generate_executive_insight(
        stress_index=20.0, 
        inflation_trend="Baixa", 
        selic_level="Estimulativo", 
        usd_vol="Baixa"
    )
    
    assert "Ambiente estável com baixa volatilidade sistêmica." in insight
    assert "Espaço para expansão com juros estimulativos e inflação controlada." in insight

def test_generate_executive_insight_chaos():
    """Valida se o ambiente de stress máximo puxa os alertas corretos"""
    insight = generate_executive_insight(
        stress_index=90.0, 
        inflation_trend="Alta", 
        selic_level="Restritivo", 
        usd_vol="Alta"
    )
    
    assert "Ambiente macroeconômico instável." in insight
    assert "Pressão inflacionária crescente mantendo o cenário de juros restritivos." in insight
    assert "Atenção: Alta volatilidade cambial observada recentemente." in insight
