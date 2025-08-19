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
    Input("date-range", "start_date"),
    Input("date-range", "end_date"),
    Input("top-n", "value"),
)
def update_graph(start_date, end_date, top_n):
    params = {}
    if start_date: params["start"] = start_date
    if end_date:   params["end"] = end_date

    try:
        resp = requests.get(f"{API_BASE}/metrics", params=params, timeout=20)
        resp.raise_for_status()
        rows = resp.json().get("sales_by_category", [])
    except Exception:
        rows = []

    df = pd.DataFrame(rows)

    if df.empty:
        fig = px.bar(title="Verkäufe pro Kategorie")
        fig.add_annotation(
            text="Keine Daten vorhanden",
            xref="paper", yref="paper", x=0.5, y=0.5,
            showarrow=False, font=dict(size=16)
        )
        fig.update_xaxes(visible=False)
        fig.update_yaxes(visible=False)
        return fig

    # Sortieren nach Umsatz
    df = df.sort_values("sales", ascending=False)

    # Top N anwenden (0 = Alle)
    if top_n and top_n > 0:
        df = df.head(top_n)

    fig = px.bar(df, x="Kategorie", y="sales", title="Verkäufe pro Kategorie")
    return fig


if __name__ == "__main__":
    app.run_server(debug=True, host="0.0.0.0", port=8050)

