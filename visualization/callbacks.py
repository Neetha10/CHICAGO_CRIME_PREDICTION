from dash.dependencies import Input, Output, State
from app import app
import requests
import json
import folium
import sys
sys.path.append("../notebooks")

from week4 import predict_crime

@app.callback(
    Output("summary-table", "data"),
    Output("overview-stats-chart", "figure"),
    Output("crime-trend-chart", "figure"),
    Input("apply-filters-btn", "n_clicks"),
    State("filter-crime-type", "value"),
    State("filter-date-range", "start_date"),
    State("filter-date-range", "end_date"),
)
def update_overview(n, crime_type, start, end):
    return [], {}, {}


FOLIUM_PATH = "../outputs/chicago_crime_heatmap.html"

@app.callback(
    Output("folium-map", "srcDoc"),
    Input("refresh-map-btn", "n_clicks")
)
# @app.callback(
#     Output("hotspot-map", "srcDoc"),
#     Output("hotspot-cluster-chart", "figure"),
#     Input("apply-filters-btn", "n_clicks"),
#     State("filter-crime-type", "value"),
#     State("filter-date-range", "start_date"),
#     State("filter-date-range", "end_date"),
# )
def update_hotspots(n, crime_type, start, end):
    m = folium.Map(location=[41.8781, -87.6298], zoom_start=11, max_bounds=True )

    from folium.plugins import HeatMap
    example_data = [
        [41.8781, -87.6298],
        [41.8794, -87.6200],
    ]
    HeatMap(example_data).add_to(m)

    m.save(FOLIUM_PATH)

    return open(FOLIUM_PATH, "r").read()

@app.callback(
    Output("forecast-7day-chart", "figure"),
    Output("forecast-30day-chart", "figure"),
    Input("apply-filters-btn", "n_clicks"),
)
def update_forecast(n):
    # forecast API
    return {}, {}
