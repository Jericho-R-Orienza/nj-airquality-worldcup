import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import plotly.graph_objects as go
from shared import DATA_DIR, BASE_LAYOUT, ZONE_COLORS

ZONE_ORDER = ["Transit Corridor", "Jersey Shore", "Statewide"]
ZONE_MAP = {
    "Bergen": "Transit Corridor", "Hudson": "Transit Corridor",
    "Passaic": "Transit Corridor", "Atlantic": "Jersey Shore",
    "Monmouth": "Jersey Shore", "Ocean": "Jersey Shore",
}
MONTH_NAMES = {
    1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun",
    7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec",
}


def build():
    print("Building Chart 3A — Monthly PM2.5 Trend...")

    ap = pd.read_csv(f"{DATA_DIR}/all_pollutants_daily_clean_2023-2025.csv", low_memory=False)
    ap["Date Local"] = pd.to_datetime(ap["Date Local"])
    ap["Month"] = ap["Date Local"].dt.month
    ap["zone"]  = ap["County Name"].map(lambda c: ZONE_MAP.get(c, "Statewide"))

    monthly_trend = (
        ap[ap["pollutant"] == "PM2.5"]
        .groupby(["zone", "Month"])["daily_max_aqi"]
        .mean()
        .reset_index()
        .rename(columns={"daily_max_aqi": "avg_aqi"})
    )

    months       = list(range(1, 13))
    month_labels = [MONTH_NAMES[m] for m in months]

    fig = go.Figure()

    for zone in ZONE_ORDER:
        sub   = monthly_trend[monthly_trend["zone"] == zone].set_index("Month").reindex(months)
        vals  = sub["avg_aqi"].tolist()
        color = ZONE_COLORS.get(zone, "#888888")
        r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)

        fig.add_trace(go.Scatter(
            x=month_labels,
            y=vals,
            name=zone,
            mode="lines+markers",
            line=dict(color=color, width=2.6),
            marker=dict(size=5, color=color),
            fill="tozeroy",
            fillcolor=f"rgba({r},{g},{b},0.07)",
            hovertemplate=f"<b>{zone}</b><br>%{{x}}: %{{y:.1f}} AQI<extra></extra>",
        ))

    fig.add_vrect(x0="Jun", x1="Aug", fillcolor="#e07b00", opacity=0.06, layer="below", line_width=0)
    fig.add_vrect(x0="Nov", x1="Dec", fillcolor="#2166ac", opacity=0.06, layer="below", line_width=0)

    fig.add_annotation(
        x="Jun", y=52.8,
        text="June 2023<br>Canadian wildfire<br>smoke event",
        showarrow=True, arrowhead=2,
        ax=80, ay=-40,
        font=dict(size=9, color="#666666"),
        arrowcolor="#888888",
        bgcolor="rgba(255,255,255,0.7)",
    )

    fig.update_layout(
        **BASE_LAYOUT,
        title=dict(
            text="<b>Monthly Average PM2.5 AQI by Zone (2023–2025)</b><br>"
                 "<sup>EPA AQS monitoring stations · Summer = Jun–Aug · Winter = Nov–Dec</sup>",
            x=0.01, xanchor="left",
        ),
        xaxis=dict(
            title="Month",
            categoryorder="array",
            categoryarray=month_labels,
            gridcolor="#dddddd",
        ),
        yaxis=dict(title="Average PM2.5 AQI", gridcolor="#dddddd", rangemode="tozero"),
        legend=dict(orientation="h", y=-0.15, x=0.5, xanchor="center"),
    )

    fig.write_html("chart3a_pm25_monthly_trend.html", include_plotlyjs="cdn")
    print("  Saved chart3a_pm25_monthly_trend.html")


if __name__ == "__main__":
    build()
