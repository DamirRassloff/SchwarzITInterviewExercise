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
        
        html.Label("Anzahl Kategorien, Filialen & Artikel:"),
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

    # KPI-Leiste (NEU)
    html.Div(id="kpi-bar", style={"display": "flex", "gap": "16px", "marginBottom": "16px"}),

    # Charts
    dcc.Graph(id="sales-by-category"),
    dcc.Graph(id="sales-by-category-pie"),
    dcc.Graph(id="sales-over-time"),
    dcc.Graph(id="sales-by-store"),
    dcc.Graph(id="sales-by-store-pie"),
    dcc.Graph(id="sales-by-article"),
    dcc.Graph(id="sales-by-article-pie"),
    dcc.Graph(id="predicted-over-time"),
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
    Output("sales-by-category-pie", "figure"),
    Output("sales-over-time", "figure"),
    Output("sales-by-store", "figure"),
    Output("sales-by-store-pie", "figure"),
    Output("sales-by-article", "figure"),
    Output("sales-by-article-pie", "figure"),
    Output("kpi-bar", "children"),
    Output("predicted-over-time", "figure"), 
    Input("date-range", "start_date"),
    Input("date-range", "end_date"),
    Input("top-n", "value"),
)
def update_graphs(start_date, end_date, top_n):
    params = {}
    if start_date: params["start"] = start_date
    if end_date:   params["end"] = end_date
    if top_n is not None:
        params["top"] = top_n

    try:
        resp = requests.get(f"{API_BASE}/metrics", params=params, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        rows_cat   = data.get("sales_by_category", [])
        rows_time  = data.get("sales_over_time", [])
        rows_store = data.get("sales_by_store", [])
        rows_article = data.get("sales_by_article", [])
        rows_pred = data.get("predicted_over_time", [])
    except Exception:
        data = {}
        rows_cat, rows_time, rows_store = [], [], []

    # ---- KPI-Bar (NEU) ----
    total_sales = data.get("total_sales", 0)
    total_rows = data.get("total_rows", 0)
    avg_per_day = data.get("avg_sales_per_day", 0)
    distinct_articles = data.get("distinct_articles", None)

    def kpi_card(label, value):
        return html.Div([
            html.Div(label, style={"fontSize": "12px", "color": "#555"}),
            html.Div(value, style={"fontSize": "20px", "fontWeight": 700})
        ], style={"border": "1px solid #eee",
                  "borderRadius": "10px",
                  "padding": "10px",
                  "background": "#fafafa",
                  "minWidth": "180px"})

    kpis = [
        kpi_card("Gesamtverkäufe (Stück)", f"{int(total_sales):,}".replace(",", ".")),
        kpi_card("Datensätze im Zeitraum", f"{int(total_rows):,}".replace(",", ".")),
        kpi_card("Ø Verkäufe pro Tag", f"{avg_per_day:.2f}"),
    ]
 
    # Nur anhängen, wenn vorhanden
    if distinct_articles is not None:
        kpis.append(kpi_card("Anzahl Artikel", f"{int(distinct_articles):,}".replace(",", ".")))

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

        fig_cat_pie = px.pie(title="Verkäufe pro Kategorie (Anteile)")
        fig_cat_pie.add_annotation(
            text="Keine Daten vorhanden", 
            xref="paper", yref="paper", 
            x=0.5, y=0.5, 
            showarrow=False, font=dict(size=16))
    else:
        df_cat = df_cat.sort_values("sales", ascending=False)
        fig_cat = px.bar(df_cat, x="Kategorie", y="sales", title="Verkäufe pro Kategorie")
        fig_cat_pie = px.pie(df_cat, names="Kategorie", values="sales", 
                        title="Verkäufe pro Kategorie (Anteile)")

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

        fig_store_pie = px.pie(title="Verkäufe pro Filiale (Anteile)")
        fig_store_pie.add_annotation(text="Keine Daten vorhanden", xref="paper", yref="paper", 
                                     x=0.5, y=0.5, showarrow=False, font=dict(size=16))
    else:
        # Top-N analog anwenden
        df_store = df_store.sort_values("sales", ascending=False)
        fig_store = px.bar(df_store, x="Filialnummer", y="sales", title="Verkäufe pro Filiale")
        fig_store_pie = px.pie(df_store, names="Filialnummer", values="sales", 
                               title="Verkäufe pro Filiale (Anteile)")
        
    # --- Verkäufe pro Artikel ---
    df_article = pd.DataFrame(rows_article)
    if df_article.empty:
        fig_article = px.bar(title="Verkäufe pro Artikel")
        fig_article.add_annotation(
            text="Keine Daten vorhanden", xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False, font=dict(size=16)
        )
        fig_article.update_xaxes(visible=False)
        fig_article.update_yaxes(visible=False)

        fig_article_pie = px.pie(title="Verkäufe pro Artikel")
        fig_article_pie.add_annotation(
            text="Keine Daten vorhanden", xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False, font=dict(size=16)
        )
    else:
        df_article = df_article.sort_values("sales", ascending=False)

        fig_article = px.bar(
            df_article, x="Artikelname", y="sales", title="Verkäufe pro Artikel"
        )
        fig_article_pie = px.pie(
            df_article, names="Artikelname", values="sales", title="Verkäufe pro Artikel (Anteil)"
        )
        fig_article_pie.update_traces(textinfo="none",
                              hovertemplate="%{label}<br>%{percent:.2%} (%{value:.0f})<extra></extra>")
        fig_article_pie.update_layout(showlegend=False)

    # --- Vorhergesagter Verkaufswert über Zeit ---
    df_pred = pd.DataFrame(rows_pred)
    if df_pred.empty:
        fig_pred = px.line(title="Vorhergesagter Verkaufswert über Zeit")
        fig_pred.add_annotation(
            text="Keine Daten vorhanden",
            xref="paper", yref="paper", x=0.5, y=0.5,
            showarrow=False, font=dict(size=16)
        )
        fig_pred.update_xaxes(visible=False)
        fig_pred.update_yaxes(visible=False)
    else:
        fig_pred = px.line(
            df_pred, x="Verkaufsdatum", y="predicted",
            title="Vorhergesagter Verkaufswert über Zeit"
        )
    

    return fig_cat, fig_cat_pie, fig_time, fig_store, fig_store_pie, fig_article, fig_article_pie, kpis, fig_pred


if __name__ == "__main__":
    app.run_server(debug=True, host="0.0.0.0", port=8050)


