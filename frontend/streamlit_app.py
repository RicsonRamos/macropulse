import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from sqlalchemy import desc
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.db.database import SessionLocal, engine, Base
from backend.db.models import TimeSeriesData, MacroStatus
from backend.etl.extract import fetch_all_macro_series
from backend.etl.transform import transform_data, calculate_kpis_and_index
from backend.etl.load import load_data_to_db

# Criação do banco caso não exista
Base.metadata.create_all(bind=engine)

st.set_page_config(page_title="MacroPulse Intelligence", page_icon="🧠", layout="wide")

@st.cache_data(ttl=3600)
def fetch_status():
    db = SessionLocal()
    try:
        # Pega a última análise macro gerada
        status = db.query(MacroStatus).order_by(desc(MacroStatus.date)).first()
        if not status: return None
        
        return {
            "date": status.date.strftime("%Y-%m-%d"),
            "macro_health_score": status.macro_health_score,
            "macro_stress_index": status.macro_stress_index,
            "fx_stress_index": status.fx_stress_index,
            "real_interest_rate": status.real_interest_rate,
            "macro_regime": status.macro_regime,
            "inflation_trend": status.inflation_trend,
            "selic_level": status.selic_level,
            "executive_summary": status.executive_summary,
            "ipca_12m_delta": status.ipca_12m_delta,
            "selic_delta": status.selic_delta,
            "usd_delta": status.usd_delta,
            "stress_delta": status.stress_delta,
            "predictions": status.predictions_json
        }
    except Exception as e:
        return None
    finally:
        db.close()

@st.cache_data(ttl=3600)
def fetch_timeseries():
    db = SessionLocal()
    try:
        records = db.query(TimeSeriesData).order_by(TimeSeriesData.date).all()
        data = [{"date": r.date, "series_type": r.series_type, "value": r.value} for r in records]
        return pd.DataFrame(data)
    except:
        return pd.DataFrame()
    finally:
        db.close()

def trigger_etl():
    try:
        with st.spinner("🧠 Rodando Engine ETL, calculando Regimes e Previsões (ARIMA)..."):
            db = SessionLocal()
            try:
                df_ipca, df_ipca_12m, df_selic, df_usd = fetch_all_macro_series(lookback_days=365*3)
                df_merged = transform_data(df_ipca, df_ipca_12m, df_selic, df_usd)
                df_processed = calculate_kpis_and_index(df_merged)
                load_data_to_db(db, df_processed)
                
                st.success("Inteligência Macro atualizada com sucesso.")
                st.cache_data.clear()
                st.rerun()
            except Exception as e:
                st.error(f"Erro no pipeline analítico: {e}")
            finally:
                db.close()
    except Exception as e:
        pass

# ==========================================
# HEADER E SETUP
# ==========================================
cols = st.columns([8, 2])
with cols[0]:
    st.title("🧠 MacroPulse Intelligence Engine")
with cols[1]:
    if st.button("🔄 Otimizar Engine (ETL)"):
        trigger_etl()

status = fetch_status()

if not status:
    st.info("Plataforma aguardando inicialização. Clique em Otimizar Engine (ETL).")
    st.stop()

# Busca timeseries para os gráficos
df_ts = fetch_timeseries()
if not df_ts.empty:
    df_ts['date'] = pd.to_datetime(df_ts['date'])

# Último valor nominal de IPCA e USD da série pura para simplificar o card
ipca_latest = df_ts[df_ts['series_type'] == 'IPCA_12M'].tail(1)['value'].values[0] if not df_ts[df_ts['series_type'] == 'IPCA_12M'].empty else 0.0
usd_latest = df_ts[df_ts['series_type'] == 'USD_BRL'].tail(1)['value'].values[0] if not df_ts[df_ts['series_type'] == 'USD_BRL'].empty else 0.0

# Define cor do risco
risk_color = "red" if status["macro_stress_index"] > 60 else "orange" if status["macro_stress_index"] > 40 else "green"

st.markdown(f"""
<div style="background-color: #1e1e1e; padding: 1rem; border-radius: 10px; margin-bottom: 2rem;">
    <h3 style="margin:0;">🧭 Regime Atual: <span style="color: #64B5F6;">{status['macro_regime']}</span> | Risco: <span style="color: {risk_color};">{status['macro_stress_index']:.1f}/100</span> | Trend Inflação: {status['inflation_trend']}</h3>
</div>
""", unsafe_allow_html=True)


# ==========================================
# ROW 1 - INDICADORES CORE
# ==========================================
st.markdown("### 📊 Indicadores Core (Momentum 30d)")
c1, c2, c3, c4, c5 = st.columns(5)

c1.metric(label="IPCA 12M", value=f"{ipca_latest:.2f}%", delta=f"{status['ipca_12m_delta']:.2f} bps", delta_color="inverse")
c2.metric(label="Juro Real (Ex-ante aprox)", value=f"{status['real_interest_rate']:.2f}%", delta=f"{status['selic_delta'] - status['ipca_12m_delta']:.2f} bps")
c3.metric(label="Dólar Nominal", value=f"R$ {usd_latest:.3f}", delta=f"{status['usd_delta']:.3f}", delta_color="inverse")
c4.metric(label="FX Stress Index", value=f"{status['fx_stress_index']:.2f}")
c5.metric(label="Macro Health Score", value=f"{status['macro_health_score']:.1f}/100", delta=f"{-status['stress_delta']:.1f}")

st.divider()

# ==========================================
# ROW 2 - GRÁFICOS
# ==========================================
if not df_ts.empty:
    st.markdown("### 📈 Painel Analítico de Séries")
    
    t1, t2, t3 = st.tabs(["IPCA vs Selic", "USD Dinâmico & FX Stress", "Forecast (ARIMA)"])
    
    with t1:
        # Multi-axis plot for Selic and IPCA
        hist_ipca = df_ts[df_ts['series_type'] == 'IPCA_12M'].copy()
        hist_selic = df_ts[df_ts['series_type'] == 'SELIC'].copy()
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=hist_ipca['date'], y=hist_ipca['value'], name='IPCA 12M', fill='tozeroy', line=dict(color='#ff4b4b')))
        fig.add_trace(go.Scatter(x=hist_selic['date'], y=hist_selic['value'], name='Selic Target', line=dict(color='#64B5F6', dash='dot')))
        fig.update_layout(template="plotly_dark", title="Dinâmica: Inflação Histórica x Taxa de Juros Base", hovermode="x unified", width=1200, height=400)
        st.plotly_chart(fig, use_container_width=True)
        
    with t2:
        # USD and Moving Averages
        hist_usd = df_ts[df_ts['series_type'] == 'USD_BRL'].copy()
        hist_usd['MA30'] = hist_usd['value'].rolling(30).mean()
        hist_usd['MA90'] = hist_usd['value'].rolling(90).mean()
        
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(x=hist_usd['date'], y=hist_usd['value'], name='Câmbio Spot', line=dict(color='#00E676')))
        fig2.add_trace(go.Scatter(x=hist_usd['date'], y=hist_usd['MA30'], name='Média 30d', line=dict(color='yellow', dash='dot')))
        fig2.add_trace(go.Scatter(x=hist_usd['date'], y=hist_usd['MA90'], name='Média 90d', line=dict(color='orange', dash='dot')))
        fig2.update_layout(template="plotly_dark", title="Pressão Cambial (Médias Móveis 30-90 dias)", hovermode="x unified", width=1200, height=400)
        st.plotly_chart(fig2, use_container_width=True)

    with t3:
        preds = status.get("predictions", {})
        if preds and "ipca_12m_value" in preds:
            st.info("Projeção Estocástica a termo (90 dias à frente usando ARIMA puro base).")
            # Construct synthetic forward dates
            last_date = hist_ipca['date'].max()
            future_dates = pd.date_range(last_date + pd.Timedelta(days=1), periods=len(preds["ipca_12m_value"]), freq='D')
            
            fig3 = go.Figure()
            # Mostra passado (limitado a 300 dias pra dar zoom)
            ipca_zoom = hist_ipca.tail(300)
            fig3.add_trace(go.Scatter(x=ipca_zoom['date'], y=ipca_zoom['value'], name='IPCA 12m (Real)', line=dict(color='darkgray')))
            fig3.add_trace(go.Scatter(x=future_dates, y=preds["ipca_12m_value"], name='IPCA 12m (Forward/ARIMA)', line=dict(color='#ff4b4b', dash='dash')))
            fig3.update_layout(template="plotly_dark", title="Curva Futura Projetada da Inflação - ARIMA", width=1200, height=400)
            st.plotly_chart(fig3, use_container_width=True)
            
            # Curva Selic Forward
            future_selic = preds.get('selic_value', [])
            if len(future_selic) > 0:
                fig4 = go.Figure()
                selic_zoom = hist_selic.tail(300)
                fig4.add_trace(go.Scatter(x=selic_zoom['date'], y=selic_zoom['value'], name='Selic (Real)', line=dict(color='darkgray')))
                fig4.add_trace(go.Scatter(x=future_dates, y=future_selic, name='Selic (Forward/ARIMA)', line=dict(color='#64B5F6', dash='dash')))
                fig4.update_layout(template="plotly_dark", title="Trajetória Estatística Inercial da Selic", width=1200, height=400)
                st.plotly_chart(fig4, use_container_width=True)
        else:
            st.warning("Previsões ainda não foram geradas no último cruzamento. Recarregue a Engine ETL.")

st.divider()

# ==========================================
# ROW 3 - INSIGHT IA
# ==========================================
st.markdown("### 🧠 Insight Macro Assistido")
insight_lines = status['executive_summary'].split(". ")

st.error(f"**Análise Computacional**: {insight_lines[0]}")
if len(insight_lines) > 1:
    st.warning("⚠️ **Sinais de Atenção Identificados:**\n" + "\n".join([f"- {line}" for line in insight_lines[1:] if line]))
else:
    st.success("✅ O cenário navega sob âncoras da normalidade estatística. Nenhuma divergência severa mapeada algorítmicamente.")

# ==========================================
# ROW 4 - HEATMAP / STRESS BOARD
# ==========================================
st.markdown("### 📉 Stress Board / Macro Health Heatmap")

# Lógica de Heatmap Baseada em Limiares Simples
heat_ipca = "Alta" if status['ipca_12m_delta'] > 0 else "Estável/Baixa"
heat_selic = "Alta/Restritiva" if status['selic_level'] == "Restritivo" else "Neutra/Dovish"
heat_usd = "Volátil" if status['usd_delta'] > 0 or status['fx_stress_index'] > 1.2 else "Calmo"
liquidez = "Apertada" if status['real_interest_rate'] > 4.5 else "Ampla"

df_heat = pd.DataFrame({
    'Indicador': ['Pressão Inflacionária', 'Liquidez Sistêmica', 'Stress Cambial', 'Aperto Monetário'],
    'Status Corrente': [heat_ipca, liquidez, heat_usd, heat_selic],
    'Score de Stress (0-100)': [
        min(100, max(0, 50 + status['ipca_12m_delta']*100)),
        min(100, max(0, status['real_interest_rate'] * 10)),
        min(100, max(0, status['fx_stress_index'] * 50)),
        min(100, max(0, status['selic_delta'] * 10 + 50))
    ]
})

fig_heat = px.density_heatmap(df_heat, y="Indicador", x="Status Corrente", z="Score de Stress (0-100)", 
                              color_continuous_scale="Reds", title="Liquidity & Risk Heatmap Proxy")
fig_heat.update_layout(template="plotly_dark", height=300)
st.plotly_chart(fig_heat, use_container_width=True)
