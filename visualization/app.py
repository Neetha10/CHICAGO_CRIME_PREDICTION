from dash import Dash, html, dcc, dash_table
import dash_bootstrap_components as dbc
import pandas as pd
app = Dash(__name__, suppress_callback_exceptions=True, external_stylesheets=[dbc.themes.FLATLY])
server = app.server
from dash import Input, Output, State, callback
import plotly.express as px

# from app import app

import requests
import json
import folium
import sys
sys.path.append("../notebooks")

from week4 import predict_crime
df = pd.read_parquet("../data/crime_clean.parquet", columns=["date", "primary_type", "arrest", "district", "block", "latitude", "longitude"])

# filter_panel = dbc.Card(
#     [
#         html.H5("Filters", className="card-title"),
#         dbc.Row([
#             dbc.Col([
#                 html.Label("Crime Type"),
#                 dcc.Dropdown(
#                     id="filter-crime-type",
#                     options=[],
#                     multi=True,
#                 )
#             ], width=6),

#             dbc.Col([
#                 html.Label("Date Range"),
#                 dcc.DatePickerRange(
#                     id="filter-date-range",
#                     min_date_allowed="2001-01-01",
#                     max_date_allowed="2024-12-31"
#                 )
#             ], width=6),
#         ]),
#         html.Br(),
#         dbc.Button("Apply Filters", id="apply-filters-btn", color="primary", className="w-100"),
#     ],
#     body=True,
#     className="mb-3 shadow-sm"
# )

# 1. OVERVIEW TAB
# overview_tab = dbc.Container([
#     html.H3("Chicago Crime Overview"),
#     html.Br(),

#     dbc.Row([
#         dbc.Col(dcc.Graph(id="overview-stats-chart"), width=6),
#         dbc.Col(dcc.Graph(id="crime-trend-chart"), width=6),
#     ]),

#     html.Br(),

#     dash_table.DataTable(
#         id="summary-table",
#         page_size=10,
#         style_table={"overflowX": "auto"},
#         style_cell={"textAlign": "left"},
#     ),
# ])

crime_options = [{"label": crime, "value": crime} for crime in sorted(df["primary_type"].unique())]

overview_tab = dbc.Container([
    html.H3("Chicago Crime Overview", className="mt-3 mb-4"),

    dbc.Row([
        dbc.Col([
            html.Label("Date Range"),
            html.Br(),
            dcc.DatePickerRange(
                id="overview-date-range",
                start_date=df["date"].min(),
                end_date=df["date"].max(),
                display_format="YYYY-MM-DD",
                clearable=True
            )
        ], width=3),
        dbc.Col([
                html.Label("Crime Type"),
                dcc.Dropdown(
                    id="filter-crime-type",
                    options=crime_options,
                    multi=True,
                )
            ], width=6),
        dbc.Col([
            html.Br(),
            dbc.Button("Refresh", id="overview-refresh-btn", color="primary", className="mt-1")
        ], width=3),
    ], className="mb-4"),

    dbc.Row([
        dbc.Col(dbc.Card(dbc.CardBody([html.H6("Total Crimes"), html.H3(id="kpi-total-crimes")])), width=3),
        dbc.Col(dbc.Card(dbc.CardBody([html.H6("YoY Change"), html.H3(id="kpi-yoy-change")])), width=3),
        dbc.Col(dbc.Card(dbc.CardBody([html.H6("Most Common Crime"), html.H3(id="kpi-common-crime")])), width=3),
        dbc.Col(dbc.Card(dbc.CardBody([html.H6("Arrest Rate"), html.H3(id="kpi-arrest-rate")])), width=3),
    ], className="mb-5"),

    # Charts
    dbc.Row([
        dbc.Col([html.H5("Crime Trend Over Time"), dcc.Graph(id="crime-trend-chart", style={"height": "400px"})], width=7),
        dbc.Col([html.H5("Top Crime Types"), dcc.Graph(id="top-crime-types-chart", style={"height": "400px"})], width=5),
    ], className="mb-5"),

    # Heatmap & Hotspots
    # dbc.Row([
    #     dbc.Col([html.H5("Heatmap Snapshot"), dcc.Graph(id="overview-heatmap", style={"height": "400px"})], width=7),
    #     dbc.Col([html.H5("Current Hotspots"), html.Ul(id="hotspot-list", children=[html.Li("—")], className="mt-2")], width=5),
    # ], className="mb-5"),

    # Summary Table
    # html.H5("Summary Table"),
    # dash_table.DataTable(
    #     id="summary-table",
    #     page_size=10,
    #     style_table={"overflowX": "auto"},
    #     style_cell={"textAlign": "left"},
    #     style_header={"fontWeight": "bold"},
    #     style_data={"whiteSpace": "normal", "height": "auto"}
    # ),
], fluid=True)


# FILTER FUNCTION
def filter_df(df, start=None, end=None, crime=None):
    temp = df.copy()
    
    if start:
        temp = temp[temp["date"] >= pd.to_datetime(start)]
    if end:
        temp = temp[temp["date"] <= pd.to_datetime(end)]
    if crime:
        temp = temp[temp["primary_type"].isin(crime)]
    
    return temp

# KPI CALLBACK
@callback(
    Output("kpi-total-crimes", "children"),
    Output("kpi-yoy-change", "children"),
    Output("kpi-common-crime", "children"),
    Output("kpi-arrest-rate", "children"),
    Input("overview-date-range", "start_date"),
    Input("overview-date-range", "end_date"),
    Input("filter-crime-type", "value"),
    # Input("overview-refresh-btn", "n_clicks"),
)
def update_kpis(start, end, crime):
    filt = filter_df(df, start, end, crime)
    if len(filt) == 0:
        filt = df.copy()

    total = len(filt)
    common = filt["primary_type"].mode()[0] if len(filt) else "—"
    arrest_rate = round(filt["arrest"].mean() * 100, 2) if len(filt) else 0

    filt["year"] = filt["date"].dt.year
    curr = filt[filt["year"] == filt["year"].max()]
    prev = filt[filt["year"] == filt["year"].max() - 1]
    yoy = round(((len(curr) - len(prev)) / len(prev)) * 100, 2) if len(prev) else 0

    return total, f"{yoy}%", common, f"{arrest_rate}%"


# CRIME TREND CALLBACK
@callback(
    Output("crime-trend-chart", "figure"),
    Input("overview-date-range", "start_date"),
    Input("overview-date-range", "end_date"),
    Input("filter-crime-type", "value"),
    # Input("overview-refresh-btn", "n_clicks"),
)
def update_trend(start, end, crime):
    filt = filter_df(df, start, end, crime)
    if len(filt) == 0:
        filt = df.copy()
    filt["month"] = filt["date"].dt.to_period("M").astype(str)
    trend = filt.groupby("month").size().reset_index(name="count")
    return px.line(trend, x="month", y="count", title="Crime Trend Over Time")


# TOP CRIME TYPES CALLBACK
@callback(
    Output("top-crime-types-chart", "figure"),
    Input("overview-date-range", "start_date"),
    Input("overview-date-range", "end_date"),
    Input("filter-crime-type", "value"),
    # Input("overview-refresh-btn", "n_clicks"),
)
def update_top_crimes(start, end, crime):
    filt = filter_df(df, start, end, crime)
    if len(filt) == 0:
        filt = df.copy()
    top = filt["primary_type"].value_counts().head(10)
    
    return px.bar(top, x=top.values, y=top.index, orientation="h", title="Top 10 Crime Types",
        color_discrete_sequence=px.colors.qualitative.Vivid)


# HEATMAP CALLBACK
# @callback(
#     Output("overview-heatmap", "figure"),
#     Input("overview-date-range", "start_date"),
#     Input("overview-date-range", "end_date")
# )
# def update_heatmap(start, end):
#     filt = filter_df(df, start, end)
#     if len(filt) == 0:
#         filt = df.copy()
#     return px.density_mapbox(
#         filt, lat="latitude", lon="longitude", radius=8,
#         center=dict(lat=41.8781, lon=-87.6298),
#         zoom=10, mapbox_style="carto-positron"
    # )

# 2) CRIME TREND CHART
# @callback(
#     Output("crime-trend-chart", "figure"),
#     Input("overview-refresh-btn", "n_clicks"),
#     State("overview-date-range", "start_date"),
#     State("overview-date-range", "end_date"),
#     State("overview-crime-type", "value"),
#     State("overview-district", "value")
# )
# def update_trend(n, start, end, crime, district):
#     if not n:
#         return {}

#     filt = filter_df(df, start, end, crime, district)
#     if len(filt) == 0:
#         return px.line()

#     filt["month"] = pd.to_datetime(filt["date"]).dt.to_period("M").astype(str)
#     trend = filt.groupby("month").size().reset_index(name="count")

#     return px.line(trend, x="month", y="count", title="Crime Trend")


# 3) TOP CRIME TYPES BAR CHART
# @callback(
#     Output("top-crime-types-chart", "figure"),
#     Input("overview-refresh-btn", "n_clicks"),
#     State("overview-date-range", "start_date"),
#     State("overview-date-range", "end_date"),
#     State("overview-crime-type", "value"),
#     State("overview-district", "value")
# )
# def update_top_crimes(n, start, end, crime, district):
#     if not n:
#         return {}

#     filt = filter_df(df, start, end, crime, district)
#     top = filt["primary_type"].value_counts().head(10)

#     return px.bar(
#         top,
#         x=top.values,
#         y=top.index,
#         orientation="h",
#         title="Top 10 Crime Types"
#     )


# 4) HEATMAP
# @callback(
#     Output("overview-heatmap", "figure"),
#     Input("overview-refresh-btn", "n_clicks"),
#     State("overview-date-range", "start_date"),
#     State("overview-date-range", "end_date"),
#     State("overview-crime-type", "value"),
#     State("overview-district", "value")
# )
# def update_heatmap(n, start, end, crime, district):
#     if not n:
#         return {}

#     filt = filter_df(df, start, end, crime, district)

#     fig = px.density_mapbox(
#         filt,
#         lat="latitude",
#         lon="longitude",
#         radius=8,
#         center=dict(lat=41.8781, lon=-87.6298),
#         zoom=9,
#         mapbox_style="carto-positron"
#     )
#     return fig


# 5) HOTSPOT LIST
# @callback(
#     Output("hotspot-list", "children"),
#     Input("overview-refresh-btn", "n_clicks"),
#     State("overview-date-range", "start_date"),
#     State("overview-date-range", "end_date"),
#     State("overview-crime-type", "value"),
#     State("overview-district", "value")
# )
# def update_hotspot_list(n, start, end, crime, district):
#     if not n:
#         return [html.Li("—")]

#     filt = filter_df(df, start, end, crime, district)

#     # Example: group by street / block
#     top_locs = filt["block"].value_counts().head(5)

#     return [html.Li(f"{loc}: {count} crimes") for loc, count in top_locs.items()]


# 6) SUMMARY TABLE
# @callback(
#     Output("summary-table", "data"),
#     Output("summary-table", "columns"),
#     Input("overview-date-range", "start_date"),
#     Input("overview-date-range", "end_date"),
#     Input("filter-crime-type", "value"),
# )
# def update_summary_table(start, end, crime):
#     filt = filter_df(df, start, end, crime)
#     cols = [{"name": c, "id": c} for c in filt.columns]
#     data = filt.to_dict("records")
#     return data, cols



# 2. HOTSPOT MAP TAB
hotspot_tab = dbc.Container([
    html.H3("Hotspot Analysis"),
    html.Br(),

    dbc.Row([
        dbc.Col([
            # html.H5("Hotspot Map (DBSCAN / KDE / H3)"),
            html.Iframe(
                id="folium-map",
                srcDoc=open("../outputs/h3_hex_hotspots.html", "r").read(),
                width="100%",
                height="600"
            ),
            # html.Button("Refresh Map", id="refresh-map-btn")
        ])
    ]),

    # html.Br(),
    # dcc.Graph(id="hotspot-cluster-chart", style={"height": "400px"}),
])

# 3. ML PREDICTION TAB
prediction_tab = dbc.Container([
    html.H3("Crime Risk Prediction (ML Models)"),
    html.Br(),

    dbc.Row([
        dbc.Col([
            html.Label("Select Date & Time"),
            # html.Br(),
            # dcc.DatePickerSingle(id="pred-date", style={"margin-left": "20px"}),
            # html.Br(),
            html.Br(),
            dcc.Input(id="pred-hour", type="number", min=0, max=23, placeholder="Hour", style={"margin-left": "153px"}),

            html.Br(), html.Br(),

            html.Label("Location (Lat, Lng)"),
            dcc.Input(id="pred-lat", type="number", placeholder="Latitude", style={"margin-left": "20px"}),
            dcc.Input(id="pred-lng", type="number", placeholder="Longitude", style={"margin-left": "147px"}),

            html.Br(), html.Br(),

            dbc.Button("Predict Crime Probability", id="predict-btn", color="primary"),
            html.Br(), html.Br(),

            html.Div(id="prediction-output", className="p-3 bg-light border rounded")
        ], width=4),

        dbc.Col([
            dcc.Graph(id="feature-importance-chart", style={"height": "400px"})
        ], width=8),
    ])
])

@app.callback(
    Output("prediction-output", "children"),
    Input("predict-btn", "n_clicks"),
    # State("pred-date", "date"),
    State("pred-hour", "value"),
    State("pred-lat", "value"),
    State("pred-lng", "value")
)
def predict_callback(n_clicks, hour, lat, lng):

    if n_clicks is None:
        return "Please enter something"

    if None in [hour, lat, lng]:
        return "Please provide all inputs."

    # import pandas as pd
    # day_of_week = pd.to_datetime(date).weekday() if date else 0

    prob = predict_crime(hour, lat, lng)
    print(prob)
    return f"Predicted Crime : {prob}"

# 4. TIME SERIES FORECAST TAB
forecast_tab = dbc.Container([
    html.H3("Crime Forecasting (7-day & 30-day)"),
    html.Br(),

    dbc.Row([
        dbc.Col(dcc.Graph(id="forecast-7day-chart"), width=6),
        dbc.Col(dcc.Graph(id="forecast-30day-chart"), width=6),
    ]),
])

app.layout = dbc.Container([
    html.H1("Chicago Crime Analytics Dashboard", className="text-center my-4"),

    dbc.Tabs([
        dbc.Tab(overview_tab, label="Overview"),
        dbc.Tab(hotspot_tab, label="Hotspots"),
        dbc.Tab(prediction_tab, label="ML Prediction"),
        dbc.Tab(forecast_tab, label="Forecasts"),
    ])
], fluid=True)


if __name__ == "__main__":
    app.run(debug=True)