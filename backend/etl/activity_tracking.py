import os
import requests
from pyopensky.rest import REST
from dotenv import load_dotenv

load_dotenv()

OS_USER = os.getenv("OPENSKY_USERNAME")
OS_PASS = os.getenv("OPENSKY_PASSWORD")

def get_flight_states_count():
    """
    Retorna o total de vôos ativos no mundo agora via OpenSky Network.
    Utiliza autenticação para maiores limites de requisição.
    """
    try:
        # pyopensky REST client
        # As credenciais são lidas automaticamente das variáveis de ambiente:
        # OPENSKY_USERNAME e OPENSKY_PASSWORD (para Trino) 
        # ou config file (para REST API)
        rest = REST()
            
        states = rest.states()
        if states is not None and not states.empty:
            return len(states)
        return 0
    except Exception as e:
        print(f"Erro ao acessar OpenSky: {e}")
        return 0

def get_ship_activity_status():
    """
    Simulação de atividade de logística via AIS (devido à complexidade de WebSockets).
    Em produção, conectaria a stream.aisstream.io.
    """
    # Exemplo de payload simulado baseado em regiões de alto tráfego
    return {
        "active_vessels_monitored": 12540,
        "key_ports_congestion": "Medium",
        "global_logistics_index": 78.5
    }

def get_real_world_activity():
    """
    Consolida indicadores de aviões e navios.
    """
    flights = get_flight_states_count()
    ships = get_ship_activity_status()
    
    return {
        "active_flights": flights,
        "active_vessels": ships["active_vessels_monitored"],
        "congestion_status": ships["key_ports_congestion"],
        "logistics_impact": "High" if flights > 10000 else "Low"
    }
