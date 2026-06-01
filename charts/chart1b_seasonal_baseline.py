import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from shared import DATA_DIR, ZONE_COLORS, BASE_LAYOUT


def build():
    print("Building Chart 1b — Seasonal Baseline...")

    adt       = pd.read_csv(f"{DATA_DIR}/nj_traffic_adt_master.csv")
    county_aq = pd.read_csv(f"{DATA_DIR}/county_aqi_seasonal_comparison.csv")

    zones_plot = ["Transit Corridor", "Jersey Shore"]

    tr_zone = (
        adt[adt["zone"].isin(zones_plot)]
        .dropna(subset=["pct_change", "winter_adt"])
        .groupby("zone", as_index=False)["pct_change"]
        .mean()
        .round(1)
    )
    tr_zone = tr_zone[tr_zone["zone"].isin(zones_plot)].sort_values("pct_change")

    ozone_zone = (
        county_aq[
            (county_aq["pollutant"] == "Ozone") &
            (county_aq["zone"].isin(zones_plot))
        ]
        .groupby("zone", as_index=False)["aqi_pct_change"]
        .mean()
        .round(1)
    )
    ozone_zone = ozone_zone[ozone_zone["zone"].isin(zones_plot)]

    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=(
            "Traffic: Avg Summer % Change vs Winter",
            "Ozone AQI: Avg Summer % Change vs Winter",
        ),
        horizontal_spacing=0.12,
    )

    ZONE_ORDER = ["Transit Corridor", "Jersey Shore"]

    tr_indexed = tr_zone.set_index("zone")
    for zone in ZONE_ORDER:
        val = tr_indexed.loc[zone, "pct_change"]
        fig.add_trace(go.Bar(
            x=[zone],
            y=[val],
            name=zone,
            marker_color=ZONE_COLORS[zone],
            showlegend=True,
            hovertemplate=f"<b>{zone}</b><br>Traffic change: {val:+.1f}%<extra></extra>",
    ), row=1, col=1)

    oz_indexed = ozone_zone.set_index("zone")
    for zone in ZONE_ORDER:
        val = oz_indexed.loc[zone, "aqi_pct_change"]
        fig.add_trace(go.Bar(
            x=[zone],
            y=[val],
            name=zone,
            marker_color=ZONE_COLORS[zone],
            showlegend=False,
            hovertemplate=f"<b>{zone}</b><br>Ozone AQI change: {val:+.1f}%<extra></extra>",
    ), row=1, col=2)

    fig.update_layout(
        **BASE_LAYOUT,
        title=dict(
            text="<b>Summer vs Winter Baseline: Traffic and Ozone AQI by Zone</b><br>",
            x=0.5, xanchor="center",
        ),
        # legend=dict(title="Zone", orientation="h", y=-0.18, x=0.5, xanchor="center"),
        # # annotations=[
        # #     dict(
        # #         text="Jersey Shore: traffic +40% AND ozone +55%<br>"
        # #              "Transit Corridor: traffic flat — ozone rises from chemistry alone",
        # #         xref="paper", yref="paper", x=0.5, y=0.98,
        # #         showarrow=False, font=dict(size=10, color="#444"),
        # #         bgcolor="rgba(255,255,255,0.8)", bordercolor="#ccc",
        # #         borderwidth=1, xanchor="center",
        # #     )
        # # ] + list(fig.layout.annotations),
    )
    fig.update_yaxes(ticksuffix="%", gridcolor="#dddddd", row=1, col=1)
    fig.update_yaxes(ticksuffix="%", gridcolor="#dddddd", row=1, col=2)
    fig.update_xaxes(tickangle=-20, row=1, col=1)
    fig.update_xaxes(tickangle=-20, row=1, col=2)

    fig.write_html("chart1b_seasonal_baseline.html", include_plotlyjs="cdn")
    print("  Saved chart1b_seasonal_baseline.html")


if __name__ == "__main__":
    build()
