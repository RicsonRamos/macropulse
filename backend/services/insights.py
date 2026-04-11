def analyze_macro_regime(ipca_12m_delta: float, selic_delta: float, usd_vol: float, ipca_value: float) -> tuple[str, str]:
    """
    Business Logic function that classifies the macro regime based on momentum and deltas.
    Returns: (regime, cause_insight)
    """
    # Regime Logic Based on Growth proxy (Selic delta as tightness) and Inflation delta
    # Se juros descem rapido e inflacao sobe = Expansion/Overheating
    # Se juros sobem e inflacao sobe = Stagflation / Tightening
    # Se juros sobem/estaveis e inflacao desce = Recovery / Cool down
    # Se juros descem e inflacao desce = Recession
    
    if ipca_12m_delta > 0.05 and selic_delta >= 0:
        regime = "Stagflation"
        cause = "Inflação acelerando mesmo com política monetária restritiva."
    elif ipca_12m_delta > 0.05 and selic_delta < 0:
        regime = "Overheating"
        cause = "Aceleração inflacionária puxada pelo ciclo de corte de juros."
    elif ipca_12m_delta < -0.05 and selic_delta < 0:
        regime = "Recession"
        cause = "Desaceleração global: inflação e juros perdendo força simultaneamente."
    elif ipca_12m_delta < -0.05 and selic_delta >= 0:
        regime = "Recovery"
        cause = "Ciclo de recuperação ancorado: Juros controlam a inflação com sucesso."
    else:
        regime = "Neutral"
        cause = "Ambiente macroeconômico lateralizado sem fortes guinadas direcionais."
        
    # Adicionais (Causas cruzadas)
    if usd_vol > 30.0:  # proxy para alta vol cambial
        cause += " Atenção: Choque externo/cambial sendo repassado aos preços."
        
    return regime, cause

def generate_executive_insight(stress_index: float, regime: str, cause: str) -> str:
    """
    Gera o texto executivo Row 3.
    """
    messages = []
    
    # Avaliação do Stress Index
    if stress_index > 75:
        messages.append(f"⚠️ {regime} Crítico.")
    elif stress_index < 30:
        messages.append(f"✅ {regime} Saudável.")
    else:
        messages.append(f"📊 {regime} Moderado.")
        
    messages.append(cause)
        
    return " ".join(messages)
