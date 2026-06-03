import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import plotly.graph_objects as go
from shared import DATA_DIR, BASE_LAYOUT, DAY_ORDER

YEAR_COLORS = {2023: "#74add1", 2024: "#1f78b4", 2025: "#4575b4"}


def build():
    print("Building Chart 5 — July 4th Saturation...")

    j4_tr    = pd.read_csv(f"{DATA_DIR}/july4_weekend_traffic.csv")
    july_tr  = pd.read_csv(f"{DATA_DIR}/july_weekend_baseline_traffic.csv")

    shore_j4 = (
        j4_tr[j4_tr["zone"] == "Jersey Shore"]
        .groupby(["year", "day_of_weekend"], as_index=False)["daily_vehicle_count"]
        .mean()
        .round(0)
    )
    shore_j4["day_of_weekend"] = pd.Categorical(
        shore_j4["day_of_weekend"], DAY_ORDER, ordered=True
    )
    shore_j4 = shore_j4.sort_values("day_of_weekend")

    shore_jbase = (
        july_tr[july_tr["zone"] == "Jersey Shore"]
        .groupby("day_of_weekend", as_index=False)["avg_daily_vehicle_count"]
        .mean()
        .round(0)
    )
    shore_jbase["day_of_weekend"] = pd.Categorical(
        shore_jbase["day_of_weekend"], DAY_ORDER, ordered=True
    )
    shore_jbase = shore_jbase.sort_values("day_of_weekend")

    fig = go.Figure()
    for year in [2023, 2024, 2025]:
        sub = shore_j4[shore_j4["year"] == year]
        fig.add_trace(go.Bar(
            x=sub["day_of_weekend"].astype(str),
            y=sub["daily_vehicle_count"],
            name=f"July 4th Weekend {year}",
            marker_color=YEAR_COLORS[year],
            marker_line_color="white",
            marker_line_width=1,
            hovertemplate=f"<b>{year} July 4th %{{x}}</b><br>Shore ADT: %{{y:,.0f}}<extra></extra>",
        ))

    fig.add_trace(go.Scatter(
        x=shore_jbase["day_of_weekend"].astype(str),
        y=shore_jbase["avg_daily_vehicle_count"],
        name="Typical July Weekend Baseline",
        mode="lines+markers",
        line=dict(color="#d73027", width=2.5, dash="dot"),
        marker=dict(size=9, color="#d73027", symbol="diamond"),
        hovertemplate="<b>July Baseline %{x}</b><br>Avg Shore ADT: %{y:,.0f}<extra></extra>",
    ))

    fig.update_layout(
        **BASE_LAYOUT,
        title=dict(
            text="<b>July 4th Weekend: Shore Roads Already at Capacity</b><br>"
                 "<sup>Jersey Shore traffic on July 4th weekend vs avg non-holiday July weekends · "
                 "2023–2025</sup>",
            x=0.01, xanchor="left",
        ),
        xaxis=dict(title="Day of Weekend", gridcolor="#dddddd",
                   categoryorder="array", categoryarray=DAY_ORDER),
        yaxis=dict(title="Avg Daily Traffic (vehicles/day)",
                   tickformat=",", gridcolor="#dddddd"),
        barmode="group",
        legend=dict(orientation="h", y=-0.18, x=0.5, xanchor="center"),
    )

    fig.write_html("chart5_july4_capacity.html", include_plotlyjs="cdn")
    print("  Saved chart5_july4_capacity.html")


if __name__ == "__main__":
    build()
