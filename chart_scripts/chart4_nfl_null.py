import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import plotly.graph_objects as go
from shared import DATA_DIR, BASE_LAYOUT

CORRIDOR_COUNTIES = ["Bergen", "Hudson", "Passaic"]
POLLUTANT_COLORS  = {"PM2.5": "#d73027", "Ozone": "#f46d43", "NO2": "#74add1"}


def build():
    print("Building Chart 4 — NFL Null Finding...")

    aq_long = pd.read_csv(f"{DATA_DIR}/aq_station_summary_long.csv")

    nfl_groups = (
        aq_long[
            (aq_long["group"].isin(["NFL Game Day", "NFL Control"])) &
            (aq_long["County Name"].isin(CORRIDOR_COUNTIES))
        ]
        .groupby(["group", "pollutant"], as_index=False)["avg_aqi"].mean()
        .round(2)
    )

    fig = go.Figure()
    for group, label, opacity in [("NFL Game Day", "Game Day", 1.0),
                                   ("NFL Control", "Control Sunday", 0.65)]:
        sub = nfl_groups[nfl_groups["group"] == group]
        for _, row in sub.iterrows():
            fig.add_trace(go.Bar(
                x=[f"{row['pollutant']} — {label}"],
                y=[row["avg_aqi"]],
                name=f"{row['pollutant']} {label}",
                marker_color=POLLUTANT_COLORS[row["pollutant"]],
                opacity=opacity,
                marker_line_color="white",
                marker_line_width=1,
                showlegend=False,
                hovertemplate=(
                    f"<b>{row['pollutant']} — {label}</b><br>"
                    f"Avg AQI: {row['avg_aqi']:.2f}<extra></extra>"
                ),
            ))

    for p, c in POLLUTANT_COLORS.items():
        fig.add_trace(go.Bar(
            x=[None], y=[None], name=p,
            marker_color=c, showlegend=True,
        ))

    fig.update_layout(
        **BASE_LAYOUT,
        title=dict(
            text="<b>NFL Game Days: No Detectable AQI Spike in the Transit Corridor</b><br>"
                 "<sup>Bergen, Hudson, Passaic counties · NFL Game Day vs matched control Sundays · 2023–2024 seasons</sup>",
            x=0.01, xanchor="left",
        ),
        xaxis=dict(
            title="",
            tickangle=-20,
            gridcolor="#dddddd",
        ),
        yaxis=dict(title="Avg AQI", gridcolor="#dddddd"),
        barmode="group",
        legend=dict(title="Pollutant", orientation="h", y=-0.18, x=0.5, xanchor="center"),
    )

    fig.write_html("chart4_nfl_null.html", include_plotlyjs="cdn")
    print("  Saved chart4_nfl_null.html")


if __name__ == "__main__":
    build()
