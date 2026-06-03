import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from shared import DATA_DIR, BASE_LAYOUT, MONTH_LABELS, MONTH_ORDER


def build():
    print("Building Chart 2 — Shore Monthly...")

    monthly_tr_s = pd.read_csv(f"{DATA_DIR}/monthly_traffic_summer_baseline.csv")
    monthly_tr_w = pd.read_csv(f"{DATA_DIR}/monthly_traffic_winter_baseline.csv")
    monthly_aq_s = pd.read_csv(f"{DATA_DIR}/monthly_aq_summer_baseline.csv")
    monthly_aq_w = pd.read_csv(f"{DATA_DIR}/monthly_aq_winter_baseline.csv")

    tr_shore_s = (
        monthly_tr_s[monthly_tr_s["zone"] == "Jersey Shore"]
        .groupby("month", as_index=False)["monthly_adt"].mean()
    )
    tr_shore_w = (
        monthly_tr_w[monthly_tr_w["zone"] == "Jersey Shore"]
        .groupby("month", as_index=False)["monthly_adt"].mean()
    )
    tr_shore = pd.concat([tr_shore_w, tr_shore_s]).sort_values("month")
    tr_shore["month_label"] = tr_shore["month"].map(MONTH_LABELS)
    tr_shore["month_label"] = pd.Categorical(tr_shore["month_label"], MONTH_ORDER, ordered=True)
    tr_shore = tr_shore.sort_values("month_label")

    aq_shore_s = (
        monthly_aq_s[
            (monthly_aq_s["zone"] == "Jersey Shore") &
            (monthly_aq_s["pollutant"] == "Ozone")
        ]
        .groupby("Month", as_index=False)["avg_aqi"].mean()
    )
    aq_shore_w = (
        monthly_aq_w[
            (monthly_aq_w["zone"] == "Jersey Shore") &
            (monthly_aq_w["pollutant"] == "Ozone")
        ]
        .groupby("Month", as_index=False)["avg_aqi"].mean()
    )
    aq_shore = pd.concat([aq_shore_w, aq_shore_s]).sort_values("Month")
    aq_shore["month_label"] = aq_shore["Month"].map(MONTH_LABELS)
    aq_shore["month_label"] = pd.Categorical(aq_shore["month_label"], MONTH_ORDER, ordered=True)
    aq_shore = aq_shore.sort_values("month_label")

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(
        go.Scatter(
            x=aq_shore["month_label"].astype(str),
            y=aq_shore["avg_aqi"],
            name="Ozone AQI (right axis)",
            mode="lines+markers",
            line=dict(color="#d73027", width=3),
            marker=dict(size=9, color="#d73027"),
            hovertemplate="<b>%{x}</b><br>Avg Shore Ozone AQI: %{y:.1f}<extra></extra>",
        ),
        secondary_y=True,
    )

    fig.add_trace(
        go.Scatter(
            x=tr_shore["month_label"].astype(str),
            y=tr_shore["monthly_adt"],
            name="Avg Daily Traffic (left axis)",
            mode="lines+markers",
            line=dict(color="#1f78b4", width=3),
            marker=dict(size=9, color="#1f78b4"),
            hovertemplate="<b>%{x}</b><br>Avg Shore ADT: %{y:,.0f}<extra></extra>",
        ),
        secondary_y=False,
    )

    fig.add_vrect(
        x0="Jun", x1="Aug",
        fillcolor="#fff3cd", opacity=0.4, line_width=0,
        annotation_text="Summer", annotation_position="top left",
        annotation_font_size=11, annotation_font_color="#856404",
    )

    fig.add_hline(
        y=50, line_dash="dash", line_color="#ff7e00", line_width=1.5,
        annotation_text="AQI 50 — Moderate threshold",
        annotation_position="bottom right",
        annotation_font_size=10, annotation_font_color="#ff7e00",
        secondary_y=True,
    )

    fig.update_layout(
        **BASE_LAYOUT,
        title=dict(
            text="<b>Jersey Shore: Monthly Traffic and Ozone AQI Move Together</b><br>"
                 "<sup>Average Daily Traffic (FHWA TMAS) vs Ozone AQI (EPA AQS) · Shore stations · 2023–2025</sup>",
            x=0.01, xanchor="left",
        ),
        legend=dict(orientation="h", y=-0.18, x=0.5, xanchor="center"),
        xaxis=dict(title="Month", gridcolor="#dddddd", categoryorder="array",
                   categoryarray=MONTH_ORDER),
    )
    fig.update_yaxes(
        title_text="Avg Monthly ADT (vehicles/day)",
        tickformat=",", gridcolor="#dddddd",
        secondary_y=False,
    )
    fig.update_yaxes(
        title_text="Avg Monthly Ozone AQI",
        gridcolor="#dddddd",
        secondary_y=True,
    )

    fig.write_html("chart2_shore_monthly.html", include_plotlyjs="cdn")
    print("  Saved chart2_shore_monthly.html")


if __name__ == "__main__":
    build()
