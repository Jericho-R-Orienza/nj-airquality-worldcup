import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import plotly.graph_objects as go
from shared import DATA_DIR, ZONE_COLORS, BASE_LAYOUT

CURATED_IDS = {
    "00003R", "0080DL", "E02132", "00003C", "E02111", "N00440",
    "0001CX", "000280", "N31025",
    "CO0563", "00040B", "00322H", "N06120", "N06114",
    "00034B", "CO0539", "E06108",
}

def shorten(loc):
    loc = str(loc).strip()
    replacements = {
        "NJ-3, MP 6.0,Rutherford Twp.,Bergen  Co.":   "NJ-3 Rutherford",
        "I-80 Local, MP 66.2, South Hackensack, Bergen Co.": "I-80 S. Hackensack",
        "Bet GSP Entrance & NJ 17":                    "GSP / NJ-17 Bergen",
        "NJ-3, MP 4.3, Clifton Twp.Passaic Co.":      "NJ-3 Clifton",
        "PASSAIC EXPRESSWAY AT MINNISINK ROAD OVERPASS": "Passaic Expressway",
        "BET PROSPECT AVE & PULASKI ST":               "NJ-440 Bayonne",
        "MP48.1, Newark City, Essex Co.":              "NJ Tpke Newark MP48",
        "JUST BEFORE INTERCHANGE 5":                   "I-280 Essex",
        "North of Roanoke Avenue":                     "Doremus Ave Newark",
        "Co-563,MP8.8,Egg harborTwp,Atlantic Co":      "Co-563 Egg Harbor",
        "JUST WEST OF DIVIDED ROADWAY":                "NJ-40 Egg Harbor",
        "Bet Skip Morgan Dr & High Bank Rd":           "NJ-322 Atlantic",
        "JUST NORTH OF RUMSON RD":                     "Rumson Rd Monmouth",
        "OLD MILL ROAD BET OCEAN AVE AND WARREN AVE":  "Ocean Ave Wall Twp",
        "MP 5.7 Wall Twp., Monmouth County":           "Wall Twp Monmouth",
        "BET SUNSET DR ON PELICAN ISLAND & B":         "Pelican Island Ocean",
    }
    for k, v in replacements.items():
        if k in loc:
            return v
    return loc[:22].strip()


def build():
    print("Building Chart 1 — Bottleneck...")

    adt = pd.read_csv(f"{DATA_DIR}/nj_traffic_adt_master.csv")
    adt["station_id_str"] = adt["station_id"].astype(str).str.strip()
    c17 = adt[adt["station_id_str"].isin(CURATED_IDS)].copy()

    c17["label"] = c17["station_location"].apply(shorten)
    c17_sorted   = c17.dropna(subset=["pct_change"]).sort_values("pct_change")

    fig = go.Figure()
    for zone in ["Transit Corridor", "Newark Gateway", "Jersey Shore"]:
        sub = c17_sorted[c17_sorted["zone"] == zone]
        if sub.empty:
            continue
        fig.add_trace(go.Bar(
            x=sub["label"],
            y=sub["pct_change"],
            name=zone,
            marker_color=ZONE_COLORS[zone],
            marker_line_color="white",
            marker_line_width=1,
            hovertemplate=(
                "<b>%{x}</b><br>"
                "Zone: " + zone + "<br>"
                "Summer change: %{y:+.1f}%<extra></extra>"
            ),
        ))

    fig.add_hline(y=0, line_color="#333333", line_width=1.5)

    fig.update_layout(
        **BASE_LAYOUT,
        title=dict(
            text="<b>The Shore Bottleneck: Summer Traffic Change by Station</b><br>"
                 "<sup>17 curated TMAS monitoring stations · summer vs winter Average Daily Traffic</sup>",
            x=0.01, xanchor="left",
        ),
        xaxis=dict(
            title="Monitoring Station",
            tickangle=-38,
            tickfont=dict(size=10),
            gridcolor="#eeeeee",
        ),
        yaxis=dict(
            title="Summer % Change vs Winter Baseline",
            ticksuffix="%",
            gridcolor="#dddddd",
            zeroline=True,
            zerolinecolor="#333333",
            zerolinewidth=1.5,
        ),
        legend=dict(title="Zone", orientation="h", y=1.02, x=1, xanchor="right"),
        barmode="group",
        annotations=[
            dict(
                text="Transit Corridor roads: flat year-round<br>Shore barrier island roads: up to +119% in summer",
                xref="paper", yref="paper", x=0.01, y=0.97,
                showarrow=False,
                font=dict(size=11, color="#444444"),
                bgcolor="rgba(255,255,255,0.8)",
                bordercolor="#cccccc", borderwidth=1,
                align="left",
            )
        ],
    )

    fig.write_html("chart1_bottleneck.html", include_plotlyjs="cdn")
    print("  Saved chart1_bottleneck.html")


if __name__ == "__main__":
    build()
