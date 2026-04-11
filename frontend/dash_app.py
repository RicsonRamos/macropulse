import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
import pandas as pd
import requests
import os
from datetime import datetime

# Configurações
API_URL = os.getenv("API_URL", "http://localhost:8000")

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.CYBORG],
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}]
)

app.title = "MacroPulse Global Intelligence"

# --- LAYOUT COMPONENTS ---

def create_header():
    return dbc.NavbarSimple(
        children=[
            dbc.Badge("GLOBAL TERMINAL", color="info", className="ms-2 me-4"),
            dbc.NavItem(dbc.NavLink("Macro", href="#")),
            dbc.NavItem(dbc.NavLink("Markets", href="#")),
            dbc.NavItem(dbc.NavLink("News", href="#")),
            dbc.Button("🔄 Update Database (ETL)", id="btn-etl", color="primary", size="sm", className="ms-3")
        ],
        brand="📊 MacroPulse Global Professional",
        brand_href="#",
        color="dark",
        dark=True,
        className="mb-4"
    )

def create_status_bar():
    return dbc.Row([
        dbc.Col(dbc.Card([
            dbc.CardBody([
                html.H6("Current Market Regime", className="text-muted"),
                html.H3(id="regime-text", children="Loading..."),
                html.P(id="regime-subtext", className="small")
            ])
        ], color="secondary", outline=True), width=8),
        dbc.Col(dbc.Card([
            dbc.CardBody([
                html.H6("Global Risk Score", className="text-muted"),
                html.H2(id="risk-score", children="--"),
                dbc.Progress(id="risk-progress", value=50, color="danger")
            ])
        ], color="secondary", outline=True), width=4),
    ], className="mb-4")

def create_kpi_cards():
    return dbc.Row([
        dbc.Col(dbc.Card(dbc.CardBody([
            html.H6("S&P 500 Change", className="text-muted"),
            html.H4(id="kpi-sp500", children="0.00%")
        ])), width=3),
        dbc.Col(dbc.Card(dbc.CardBody([
            html.H6("VIX Index", className="text-muted"),
            html.H4(id="kpi-vix", children="0.00")
        ])), width=3),
        dbc.Col(dbc.Card(dbc.CardBody([
            html.H6("Gold (Ounce)", className="text-muted"),
            html.H4(id="kpi-gold", children="$0.00")
        ])), width=3),
        dbc.Col(dbc.Card(dbc.CardBody([
            html.H6("Active Flights", className="text-muted"),
            html.H4(id="kpi-flights", children="0")
        ])), width=3),
    ], className="mb-4")

def create_main_content():
    return dbc.Row([
        dbc.Col([
            dbc.Tabs([
                dbc.Tab(label="Markets Overview", children=[
                    dcc.Graph(id="main-graph", style={"height": "500px"})
                ]),
                dbc.Tab(label="Real World Activity", children=[
                    dbc.Row([
                        dbc.Col(dcc.Graph(id="flights-graph"), width=6),
                        dbc.Col(dcc.Graph(id="ships-logistics"), width=6),
                    ])
                ]),
            ])
        ], width=8),
        dbc.Col([
            html.H5("News Intelligence Feed", className="mb-3"),
            html.Div(id="news-feed", style={"height": "600px", "overflowY": "scroll"})
        ], width=4)
    ])

app.layout = dbc.Container([
    create_header(),
    dbc.Alert("Bases não carregadas. Por favor, clique no botão 'Update Database (ETL)' no topo para iniciar.", 
              id="alert-no-data", color="warning", is_open=True, className="mb-4"),
    create_status_bar(),
    create_kpi_cards(),
    create_main_content(),
    
    dcc.Interval(id="interval-update", interval=60*1000, n_intervals=0), # Refresh a cada 1m
    dcc.Store(id="global-data-store"),
    html.Div(id="etl-status-output", className="d-none")
], fluid=True)

# --- CALLBACKS ---

@app.callback(
    Output("global-data-store", "data"),
    Input("interval-update", "n_intervals")
)
def update_store(n):
    try:
        r = requests.get(f"{API_URL}/intelligence/global")
        if r.status_code == 200:
            return r.json()
    except:
        return None

@app.callback(
    [Output("regime-text", "children"),
     Output("regime-text", "style"),
     Output("regime-subtext", "children"),
     Output("risk-score", "children"),
     Output("risk-progress", "value"),
     Output("kpi-sp500", "children"),
     Output("kpi-vix", "children"),
     Output("kpi-gold", "children"),
     Output("kpi-flights", "children"),
     Output("alert-no-data", "is_open")],
    Input("global-data-store", "data")
)
def update_kpis(data):
    if not data:
        return [dash.no_update] * 9 + [True]
    
    kpis = data["kpis"]
    act = data["activity"]
    
    color_map = {"success": "#00ff00", "warning": "#ffa500", "danger": "#ff0000", "info": "#00ffff", "dark": "#888888"}
    reg_color = color_map.get(kpis["regime_color"], "white")
    
    return [
        kpis["regime"],
        {"color": reg_color},
        kpis["regime_explanation"],
        f"{kpis['risk_score']}",
        kpis["risk_score"],
        f"{kpis['sp500_daily_change']}%",
        f"{kpis['vix']:.2f}",
        f"${kpis['gold_price']:.2f}",
        f"{act['active_flights']:,}",
        False # Fecha o alerta
    ]

@app.callback(
    Output("news-feed", "children"),
    Input("global-data-store", "data")
)
def update_news(data):
    if not data:
        return "No news available."
    
    items = []
    for article in data["news"]:
        badge_color = "success" if article["sentiment"] == "Bullish" else "danger" if article["sentiment"] == "Bearish" else "secondary"
        items.append(dbc.Card([
            dbc.CardBody([
                dbc.Badge(article["sentiment"], color=badge_color, className="mb-2"),
                html.H6(article["title"]),
                html.P(article["summary"], className="small text-muted"),
                html.A("Read More", href=article["url"], target="_blank", className="small")
            ])
        ], className="mb-2"))
    return items

@app.callback(
    Output("main-graph", "figure"),
    Input("interval-update", "n_intervals")
)
def update_graph(n):
    try:
        r = requests.get(f"{API_URL}/timeseries/global")
        if r.status_code == 200:
            df = pd.DataFrame(r.json()["data"])
            if df.empty: return go.Figure()
            
            fig = go.Figure()
            # Mostra S&P 500 e VIX em eixos diferentes
            for ticker in ["^GSPC", "^VIX"]:
                dff = df[df['series_type'] == ticker]
                fig.add_trace(go.Scatter(x=dff['date'], y=dff['value'], name=ticker))
            
            fig.update_layout(template="plotly_dark", margin=dict(l=20, r=20, t=20, b=20))
            return fig
    except:
        return go.Figure()

@app.callback(
    Output("etl-status-output", "children"),
    Input("btn-etl", "n_clicks"),
    prevent_initial_call=True
)
def trigger_etl(n):
    if n:
        try:
            requests.post(f"{API_URL}/etl/run")
            return "ETL Triggered"
        except:
            return "Error Triggering ETL"
    return ""

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8050, debug=False)
