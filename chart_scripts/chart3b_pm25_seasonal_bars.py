import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import plotly.graph_objects as go
from shared import DATA_DIR, BASE_LAYOUT

ZONE_ORDER = ["Transit Corridor", "Jersey Shore", "Statewide"]
SUM_C = "#e07b00"
WIN_C = "#2166ac"


def build():
    print("Building Chart 3B — PM2.5 Seasonal Bars...")

    aq_s = pd.read_csv(f"{DATA_DIR}/monthly_aq_summer_baseline.csv")
    aq_w = pd.read_csv(f"{DATA_DIR}/monthly_aq_winter_baseline.csv")

    summer_aqi = (
        aq_s[aq_s["pollutant"] == "PM2.5"]
        .groupby("zone")["avg_aqi"].mean()
        .rename("summer_aqi")
    )
    winter_aqi = (
        aq_w[aq_w["pollutant"] == "PM2.5"]
        .groupby("zone")["avg_aqi"].mean()
        .rename("winter_aqi")
    )
    aq_seasonal = (
        pd.concat([summer_aqi, winter_aqi], axis=1)
        .reindex(ZONE_ORDER)
        .dropna(how="all")
    )
    aq_seasonal["pct_change"] = (
        (aq_seasonal["summer_aqi"] - aq_seasonal["winter_aqi"])
        / aq_seasonal["winter_aqi"] * 100
    )

    zones = [
        z for z in ZONE_ORDER
        if z in aq_seasonal.index and not pd.isna(aq_seasonal.loc[z, "summer_aqi"])
    ]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=zones,
        y=[aq_seasonal.loc[z, "summer_aqi"] for z in zones],
        name="Summer (Jun–Aug)",
        marker_color=SUM_C,
        marker_line_color="white",
        marker_line_width=0.8,
        opacity=0.82,
        hovertemplate="<b>%{x} — Summer</b><br>PM2.5 AQI: %{y:.1f}<extra></extra>",
    ))

    fig.add_trace(go.Bar(
        x=zones,
        y=[aq_seasonal.loc[z, "winter_aqi"] for z in zones],
        name="Winter (Nov–Dec)",
        marker_color=WIN_C,
        marker_line_color="white",
        marker_line_width=0.8,
        opacity=0.82,
        hovertemplate="<b>%{x} — Winter</b><br>PM2.5 AQI: %{y:.1f}<extra></extra>",
    ))

    annotations = []
    for z in zones:
        row    = aq_seasonal.loc[z]
        pct    = row["pct_change"]
        y_pos  = max(row["summer_aqi"], row["winter_aqi"]) + 4.5
        symbol = "▲" if pct > 0 else "▼"
        color  = "#c0392b" if pct > 0 else "#27ae60"
        annotations.append(dict(
            x=z, y=y_pos,
            text=f"<b>{symbol} {abs(pct):.0f}%</b>",
            showarrow=False,
            font=dict(size=10, color=color),
        ))

    fig.update_layout(
        **BASE_LAYOUT,
        title=dict(
            text="<b>PM2.5 AQI — Summer vs. Winter by Zone</b><br>"
                 "<sup>EPA AQS monitoring stations · 2023–2025</sup>",
            x=0.01, xanchor="left",
        ),
        xaxis=dict(title="Zone", gridcolor="#dddddd"),
        yaxis=dict(title="Average PM2.5 AQI", gridcolor="#dddddd"),
        barmode="group",
        legend=dict(orientation="h", y=-0.15, x=0.5, xanchor="center"),
        annotations=annotations,
    )

    fig.write_html("chart3b_pm25_seasonal_bars.html", include_plotlyjs="cdn")
    print("  Saved chart3b_pm25_seasonal_bars.html")


if __name__ == "__main__":
    build()
