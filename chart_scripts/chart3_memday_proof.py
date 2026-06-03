import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import plotly.graph_objects as go
from shared import DATA_DIR, BASE_LAYOUT, DAY_ORDER

SHORE_COUNTIES = ["Atlantic", "Monmouth", "Ocean"]
YEAR_COLORS    = {2023: "#74add1", 2024: "#d73027", 2025: "#6a3d9a"}


def build():
    print("Building Chart 3 — Memorial Day Proof Case...")

    mem_aqi      = pd.read_csv(f"{DATA_DIR}/memorial_day_weekend_aqi.csv")
    mem_base_aqi = pd.read_csv(f"{DATA_DIR}/may_weekend_baseline_aqi.csv")

    mem_shore = (
        mem_aqi[
            (mem_aqi["County Name"].isin(SHORE_COUNTIES)) &
            (mem_aqi["pollutant"] == "Ozone")
        ]
        .groupby(["year", "day_of_weekend"], as_index=False)["aqi"].mean()
        .round(1)
    )

    base_shore = (
        mem_base_aqi[
            (mem_base_aqi["County Name"].isin(SHORE_COUNTIES)) &
            (mem_base_aqi["pollutant"] == "Ozone")
        ]
        .groupby("day_of_weekend", as_index=False)["avg_aqi"].mean()
        .round(1)
    )

    fig = go.Figure()

    for year in [2023, 2024, 2025]:
        sub = mem_shore[mem_shore["year"] == year].copy()
        sub["day_of_weekend"] = pd.Categorical(sub["day_of_weekend"], DAY_ORDER, ordered=True)
        sub = sub.sort_values("day_of_weekend")
        fig.add_trace(go.Bar(
            x=sub["day_of_weekend"].astype(str),
            y=sub["aqi"],
            name=str(year),
            marker_color=YEAR_COLORS[year],
            marker_line_color="white",
            marker_line_width=1,
            hovertemplate=f"<b>{year} %{{x}}</b><br>Shore Ozone AQI: %{{y:.1f}}<extra></extra>",
        ))

    base_shore["day_of_weekend"] = pd.Categorical(base_shore["day_of_weekend"], DAY_ORDER, ordered=True)
    base_shore = base_shore.sort_values("day_of_weekend")
    fig.add_trace(go.Scatter(
        x=base_shore["day_of_weekend"].astype(str),
        y=base_shore["avg_aqi"],
        name="May Baseline (avg non-holiday weekends)",
        mode="lines+markers",
        line=dict(color="#333333", width=2.5, dash="dot"),
        marker=dict(size=8, color="#333333"),
        hovertemplate="<b>May Baseline %{x}</b><br>Avg Shore Ozone AQI: %{y:.1f}<extra></extra>",
    ))

    fig.add_hline(
        y=50, line_dash="dash", line_color="#ff7e00", line_width=1.5,
        annotation_text="AQI 50 — EPA Moderate threshold",
        annotation_position="top right",
        annotation_font_size=10, annotation_font_color="#ff7e00",
    )

    fig.update_layout(
        **BASE_LAYOUT,
        title=dict(
            text="<b>Memorial Day Proof Case: Shore Ozone Spikes on Holiday Weekends</b><br>"
                 "<sup>Jersey Shore counties (Atlantic, Monmouth, Ocean) · Ozone AQI · "
                 "vs May non-holiday weekend baseline</sup>",
            x=0.01, xanchor="left",
        ),
        xaxis=dict(title="Day of Weekend", gridcolor="#dddddd",
                   categoryorder="array", categoryarray=DAY_ORDER),
        yaxis=dict(title="Avg Shore Ozone AQI", gridcolor="#dddddd"),
        barmode="group",
        legend=dict(orientation="h", y=-0.18, x=0.5, xanchor="center"),
        # annotations=[
        #     dict(
        #         text="2024 Friday: AQI 92 vs May baseline 40 — a 130% spike<br>"
        #              "2025: traffic and AQI both suppressed — weather-driven, no surge",
        #         xref="paper", yref="paper", x=0.01, y=0.97,
        #         showarrow=False, font=dict(size=10, color="#444"),
        #         bgcolor="rgba(255,255,255,0.85)", bordercolor="#ccc",
        #         borderwidth=1, align="left",
        #     )
        # ],
    )

    fig.write_html("chart3_memday_proof.html", include_plotlyjs="cdn")
    print("  Saved chart3_memday_proof.html")


if __name__ == "__main__":
    build()
