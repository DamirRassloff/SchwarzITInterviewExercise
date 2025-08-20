import requests
import dash
from dash import dcc, html, Input, Output
import plotly.express as px
import pandas as pd

API_BASE = "http://api:8000"

app = dash.Dash(__name__)
server = app.server

app.layout = html.Div([
    html.H1("Sales Dashboard (Schwarz IT Exercise)"),
    
    # Filterbereich
    html.Div([
        dcc.DatePickerRange(id="date-range"),
        html.Button("Reset Date Filter", id="reset-btn", style={"marginLeft": "10px"}),
        
        html.Br(), html.Br(),
        
        html.Label("Anzahl Kategorien:"),
        dcc.Dropdown(
            id="top-n",
            options=[
                {"label": "Top 3", "value": 3},
                {"label": "Top 5", "value": 5},
                {"label": "Top 10", "value": 10},
                {"label": "Alle", "value": 0},
            ],
            value=5,  # Default
            clearable=False,
            style={"width": "200px"}
        ),
    ], style={"marginBottom": "20px"}),
    
    dcc.Graph(id="sales-by-category"),
    dcc.Graph(id="sales-over-time"),
    dcc.Graph(id="sales-by-store"),
])

# Reset-Callback
@app.callback(
    Output("date-range", "start_date"),
    Output("date-range", "end_date"),
    Input("reset-btn", "n_clicks"),
    prevent_initial_call=True
)
def reset_dates(n_clicks):
    return None, None


# Automatisches Update bei Änderung
@app.callback(
    Output("sales-by-category", "figure"),
    Output("sales-over-time", "figure"),
    Output("sales-by-store", "figure"),
    Input("date-range", "start_date"),
    Input("date-range", "end_date"),
    Input("top-n", "value"),
)
def update_graphs(start_date, end_date, top_n):
    params = {}
    if start_date: params["start"] = start_date
    if end_date:   params["end"] = end_date

    try:
        resp = requests.get(f"{API_BASE}/metrics", params=params, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        rows_cat = data.get("sales_by_category", [])
        rows_time = data.get("sales_over_time", [])
        rows_store = data.get("sales_by_store", []) 
    except Exception:
        rows_cat, rows_time = [], []

    # --- Verkäufe pro Kategorie ---
    df_cat = pd.DataFrame(rows_cat)
    if df_cat.empty:
        fig_cat = px.bar(title="Verkäufe pro Kategorie")
        fig_cat.add_annotation(
            text="Keine Daten vorhanden",
            xref="paper", yref="paper", x=0.5, y=0.5,
            showarrow=False, font=dict(size=16)
        )
        fig_cat.update_xaxes(visible=False)
        fig_cat.update_yaxes(visible=False)
    else:
        df_cat = df_cat.sort_values("sales", ascending=False)
        if top_n and top_n > 0:
            df_cat = df_cat.head(top_n)
        fig_cat = px.bar(df_cat, x="Kategorie", y="sales", title="Verkäufe pro Kategorie")

    # --- Verkäufe über Zeit ---
    df_time = pd.DataFrame(rows_time)
    if df_time.empty:
        fig_time = px.line(title="Verkäufe über Zeit")
        fig_time.add_annotation(
            text="Keine Daten vorhanden",
            xref="paper", yref="paper", x=0.5, y=0.5,
            showarrow=False, font=dict(size=16)
        )
        fig_time.update_xaxes(visible=False)
        fig_time.update_yaxes(visible=False)
    else:
        fig_time = px.line(df_time, x="Verkaufsdatum", y="sales", title="Verkäufe über Zeit")

    # --- Verkäufe pro Filiale ---
    df_store = pd.DataFrame(rows_store)
    if df_store.empty:
        fig_store = px.bar(title="Verkäufe pro Filiale")
        fig_store.add_annotation(text="Keine Daten vorhanden", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False, font=dict(size=16))
        fig_store.update_xaxes(visible=False); fig_store.update_yaxes(visible=False)
    else:
        # Top-N analog anwenden
        df_store = df_store.sort_values("sales", ascending=False)
        if top_n and top_n > 0:
            df_store = df_store.head(top_n)
        fig_store = px.bar(df_store, x="Filialnummer", y="sales", title="Verkäufe pro Filiale")

    return fig_cat, fig_time, fig_store


if __name__ == "__main__":
    app.run_server(debug=True, host="0.0.0.0", port=8050)


