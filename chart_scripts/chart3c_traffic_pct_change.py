import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import plotly.graph_objects as go
from shared import DATA_DIR, BASE_LAYOUT, ZONE_COLORS

CURATED_IDS = [
    "00003C", "00003R", "00034B", "00040B", "00322H",
    "0080DL", "CO0563", "E02111", "E02132", "E06108",
    "N00440", "N06114", "N06120",
]

SHORT_NAMES = {
    "00003C": "NJ-3 Clifton †",
    "00003R": "NJ-3 Rutherford",
    "00034B": "Wall Twp, Monmouth",
    "00040B": "NJ-40 Egg Harbor",
    "00322H": "NJ-322 Atlantic",
    "0080DL": "I-80 S. Hackensack",
    "CO0563": "Co-563 Egg Harbor",
    "E02111": "Passaic Expressway",
    "E02132": "GSP / NJ-17 Bergen",
    "E06108": "Pelican Island, Ocean",
    "N00440": "NJ-440 Bayonne",
    "N06114": "Ocean Ave, Wall Twp",
    "N06120": "Rumson Rd, Monmouth",
}


def build():
    print("Building Chart 3C — Traffic % Change by Station...")

    aq_s = pd.read_csv(f"{DATA_DIR}/monthly_aq_summer_baseline.csv")
    aq_w = pd.read_csv(f"{DATA_DIR}/monthly_aq_winter_baseline.csv")

    summer_pm = aq_s[aq_s["pollutant"] == "PM2.5"].groupby("zone")["avg_aqi"].mean()
    winter_pm = aq_w[aq_w["pollutant"] == "PM2.5"].groupby("zone")["avg_aqi"].mean()
    pm25_pct = {
        z: (summer_pm[z] - winter_pm[z]) / winter_pm[z] * 100
        for z in ["Transit Corridor", "Jersey Shore"]
        if z in summer_pm.index and z in winter_pm.index
    }

    master = pd.read_csv(f"{DATA_DIR}/nj_traffic_adt_master.csv")
    master["station_id"] = master["station_id"].astype(str).str.strip()
    stations = master[master["station_id"].isin(CURATED_IDS)].copy()
    stations["label"] = stations["station_id"].map(SHORT_NAMES)

    stations["zone_ord"] = stations["zone"].map({"Jersey Shore": 0, "Transit Corridor": 1})
    stations = stations.sort_values(
        ["zone_ord", "pct_change"], ascending=[True, True]
    ).reset_index(drop=True)

    category_order = list(stations["label"])
    shore_labels   = stations[stations["zone"] == "Jersey Shore"]["label"].tolist()
    corr_labels    = stations[stations["zone"] == "Transit Corridor"]["label"].tolist()

    fig = go.Figure()

    for zone in ["Jersey Shore", "Transit Corridor"]:
        sub   = stations[stations["zone"] == zone]
        color = ZONE_COLORS[zone]
        fig.add_trace(go.Bar(
            x=sub["pct_change"],
            y=sub["label"],
            orientation="h",
            name=zone,
            marker_color=color,
            marker_line_color="white",
            marker_line_width=0.5,
            opacity=0.80,
            hovertemplate="<b>%{y}</b><br>Traffic change: %{x:+.1f}%<extra></extra>",
        ))

    fig.add_hrect(
        y0=shore_labels[0], y1=shore_labels[-1],
        fillcolor=ZONE_COLORS["Jersey Shore"], opacity=0.04, layer="below", line_width=0,
    )
    fig.add_hrect(
        y0=corr_labels[0], y1=corr_labels[-1],
        fillcolor=ZONE_COLORS["Transit Corridor"], opacity=0.04, layer="below", line_width=0,
    )

    fig.add_vline(x=0, line_color="#555555", line_width=0.9)

    for zone, ref_x in pm25_pct.items():
        color = ZONE_COLORS[zone]
        fig.add_vline(
            x=ref_x,
            line_color=color, line_width=1.8, line_dash="dot",
            annotation_text=f"PM2.5 {ref_x:+.0f}%",
            annotation_position="top",
            annotation_font=dict(size=8, color=color),
        )

    fig.update_layout(
        **BASE_LAYOUT,
        title=dict(
            text="<b>Traffic Volume Change by Station</b><br>"
                 "<sup>% change Summer vs. Winter ADT · Transit Corridor & Jersey Shore · 2023–2025</sup>",
            x=0.01, xanchor="left",
        ),
        xaxis=dict(
            title="% Change in ADT — Summer vs. Winter",
            gridcolor="#dddddd",
            tickformat="+.0f",
            ticksuffix="%",
        ),
        yaxis=dict(
            title="",
            categoryorder="array",
            categoryarray=category_order,
            gridcolor="#dddddd",
        ),
        legend=dict(orientation="h", y=-0.18, x=0.5, xanchor="center")
    )

    fig.write_html("chart3c_traffic_pct_change.html", include_plotlyjs="cdn")
    print("  Saved chart3c_traffic_pct_change.html")


if __name__ == "__main__":
    build()
