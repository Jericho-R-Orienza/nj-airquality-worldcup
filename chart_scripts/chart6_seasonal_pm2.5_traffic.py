"""
seasonal_comparison_chart.py

Three-panel figure:
  Panel A (top, full width) — Monthly PM2.5 AQI trend by zone, full year
  Panel B (bottom-left)     — PM2.5 AQI seasonal bars, zone-level
  Panel C (bottom-right)    — Traffic % change per station, with PM2.5
                              reference lines showing where air quality
                              sits relative to each zone's traffic shift

Data sources:
  all_pollutants_daily_clean_2023-2025.csv  → full-year PM2.5 monthly trend
  monthly_aq_summer_baseline.csv            → summer AQI averages by station
  monthly_aq_winter_baseline.csv            → winter AQI averages by station
  nj_traffic_adt_master.csv                 → curated station ADT + pct_change

Run from the project root:
    python seasonal_comparison_chart.py
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.ticker as mticker
from matplotlib.gridspec import GridSpec

#  Data directory
DATA_DIR = "data"

def load(filename):
    return pd.read_csv(os.path.join(DATA_DIR, filename), low_memory=False)

#  Zone configuration 
ZONE_MAP = {
    "Bergen":   "Transit Corridor",
    "Hudson":   "Transit Corridor",
    "Passaic":  "Transit Corridor",
    "Atlantic": "Jersey Shore",
    "Monmouth": "Jersey Shore",
    "Ocean":    "Jersey Shore",
}
ZONE_ORDER = ["Transit Corridor", "Jersey Shore", "Statewide"]

ZONE_COLORS = {
    "Transit Corridor": "#e31a1c",
    "Jersey Shore":     "#1f78b4",
    "Statewide":        "#6a3d9a",
}

MONTH_NAMES = {
    1:"Jan", 2:"Feb", 3:"Mar", 4:"Apr", 5:"May",  6:"Jun",
    7:"Jul", 8:"Aug", 9:"Sep", 10:"Oct", 11:"Nov", 12:"Dec"
}

SUM_C = "#e07b00"
WIN_C = "#2166ac"

#  Curated station set — 13 stations (CO0539 excluded: summer-only reporter)
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

# 1.  Monthly PM2.5 trend — all 12 months for Panel A
print("Loading all_pollutants_daily_clean_2023-2025.csv ...")
ap = load("all_pollutants_daily_clean_2023-2025.csv")
ap["Date Local"] = pd.to_datetime(ap["Date Local"])
ap["Month"]      = ap["Date Local"].dt.month
ap["zone"]       = ap["County Name"].map(lambda c: ZONE_MAP.get(c, "Statewide"))

monthly_trend = (
    ap[ap["pollutant"] == "PM2.5"]
    .groupby(["zone", "Month"])["daily_max_aqi"]
    .mean()
    .reset_index()
    .rename(columns={"daily_max_aqi": "avg_aqi"})
)

# 2.  PM2.5 seasonal averages — zone level for Panel B
print("Loading monthly AQ baselines ...")
aq_s = load("monthly_aq_summer_baseline.csv")
aq_w = load("monthly_aq_winter_baseline.csv")

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

# PM2.5 % change per zone — used as reference lines in Panel C
pm25_pct = {
    "Transit Corridor": aq_seasonal.loc["Transit Corridor", "pct_change"],
    "Jersey Shore":     aq_seasonal.loc["Jersey Shore",     "pct_change"],
}

print("PM2.5 seasonal summary:")
print(aq_seasonal.round(1).to_string())

# 3.  Curated station traffic data for Panel C
print("\nLoading nj_traffic_adt_master.csv ...")
master = load("nj_traffic_adt_master.csv")
master["station_id"] = master["station_id"].astype(str).str.strip()

stations = master[master["station_id"].isin(CURATED_IDS)].copy()
stations["label"] = stations["station_id"].map(SHORT_NAMES)

# Sort so Transit Corridor ends up at the TOP of the chart and Jersey Shore below.
# In matplotlib barh, higher y-position = higher on the plot.
# Assigning Shore zone_ord=0 means it goes first in the loop gets lower y values → bottom.
# Assigning Corridor zone_ord=1 means it goes second gets higher y values → top.
# Within each zone, sort ascending so the highest pct_change gets the highest y in its group.
zone_ord_map = {"Jersey Shore": 0, "Transit Corridor": 1}
stations["zone_ord"] = stations["zone"].map(zone_ord_map)
stations = stations.sort_values(
    ["zone_ord", "pct_change"], ascending=[True, True]
).reset_index(drop=True)

# Assign y positions — Transit Corridor gets higher y values (appears at top)
# Build positions from top down, then flip so top = highest y
n = len(stations)
gap_size  = 1.8    # extra vertical space between zone groups
y_cur     = 0
positions = []
prev_zone = None

for _, row in stations.iterrows():
    if prev_zone is not None and row["zone"] != prev_zone:
        y_cur += gap_size
    positions.append(y_cur)
    y_cur += 1
    prev_zone = row["zone"]

stations["ypos"] = positions
print(f"\n{len(stations)} stations loaded:")
print(stations[["label", "zone", "pct_change", "ypos"]].to_string())

# 4.  Build figure
plt.rcParams.update({
    "font.family":       "DejaVu Sans",
    "axes.spines.top":   False,
    "axes.spines.right": False,
    "axes.grid":         True,
    "grid.color":        "#e8e8e8",
    "grid.linewidth":    0.6,
    "grid.alpha":        0.8,
    "axes.axisbelow":    True,
})

fig = plt.figure(figsize=(16, 13), facecolor="white")
gs  = GridSpec(
    2, 2, figure=fig,
    top=0.88, bottom=0.07, left=0.07, right=0.97,
    hspace=0.55, wspace=0.30,
    height_ratios=[1.0, 1.3],     # give bottom panels more room for stations
)
ax_trend = fig.add_subplot(gs[0, :])
ax_aq    = fig.add_subplot(gs[1, 0])
ax_tr    = fig.add_subplot(gs[1, 1])

#  Figure titles 
fig.text(
    0.5, 0.955,
    "NJ Air Quality & Traffic — Seasonal Comparison (2023–2025)",
    ha="center", fontsize=16, fontweight="bold", color="#1a1a2e",
)
fig.text(
    0.5, 0.924,
    "PM2.5 AQI from EPA AQS monitoring stations  ·  "
    "Traffic from FHWA TMAS monthly station counts  ·  "
    "Summer = Jun–Aug  ·  Winter = Nov–Dec",
    ha="center", fontsize=9.5, color="#555555",
)

# 
# PANEL A — Full-year monthly PM2.5 trend lines
# 
ax = ax_trend
months       = list(range(1, 13))
month_labels = [MONTH_NAMES[m] for m in months]

for zone in ZONE_ORDER:
    sub   = monthly_trend[monthly_trend["zone"] == zone].set_index("Month").reindex(months)
    vals  = sub["avg_aqi"].values
    color = ZONE_COLORS[zone]
    ax.plot(months, vals, color=color, linewidth=2.6, marker="o",
            markersize=5, label=zone, zorder=3)
    ax.fill_between(months, vals, alpha=0.08, color=color)

ax.axvspan(5.5, 8.5,   alpha=0.06, color="#e07b00", zorder=0)
ax.axvspan(10.5, 12.5, alpha=0.06, color="#2166ac", zorder=0)
y_top = ax.get_ylim()[1]
ax.text(7,    y_top * 0.96, "SUMMER", fontsize=8, color="#e07b00",
        ha="center", fontweight="bold", alpha=0.85)
ax.text(11.5, y_top * 0.96, "WINTER", fontsize=8, color="#2166ac",
        ha="center", fontweight="bold", alpha=0.85)
ax.annotate(
    "June 2023\nCanadian wildfire\nsmoke event",
    xy=(6, 52.8), xytext=(7.8, 58),
    arrowprops=dict(arrowstyle="->", color="#888", lw=1.2),
    fontsize=8, color="#666", ha="left",
)
ax.set_xticks(months)
ax.set_xticklabels(month_labels, fontsize=10)
ax.set_ylabel("Average PM2.5 AQI", fontsize=10)
ax.set_title("Monthly Average PM2.5 AQI by Zone  (2023–2025 combined)",
             fontsize=11, fontweight="semibold", pad=8, loc="left")
ax.set_xlim(0.5, 12.5)
ax.set_ylim(bottom=15)
ax.legend(loc="upper right", fontsize=9, framealpha=0.85, edgecolor="#ddd")

# 
# PANEL B — Summer vs Winter PM2.5 AQI bars (zone level)
# 
ax    = ax_aq
zones = [z for z in ZONE_ORDER if z in aq_seasonal.index
         and not pd.isna(aq_seasonal.loc[z, "summer_aqi"])]
x     = np.arange(len(zones))
bar_w = 0.35

bars_s = ax.bar(x - bar_w/2, aq_seasonal.loc[zones, "summer_aqi"],
                bar_w, label="Summer (Jun–Aug)", color=SUM_C,
                alpha=0.82, edgecolor="white", linewidth=0.8, zorder=3)
bars_w = ax.bar(x + bar_w/2, aq_seasonal.loc[zones, "winter_aqi"],
                bar_w, label="Winter (Nov–Dec)", color=WIN_C,
                alpha=0.82, edgecolor="white", linewidth=0.8, zorder=3)

def label_bars(bars, ax, fmt="{:.1f}"):
    for bar in bars:
        h = bar.get_height()
        if not np.isnan(h):
            ax.text(bar.get_x() + bar.get_width() / 2, h + 0.5,
                    fmt.format(h), ha="center", va="bottom",
                    fontsize=9, fontweight="bold", color="#333")

label_bars(bars_s, ax)
label_bars(bars_w, ax)

for i, zone in enumerate(zones):
    row    = aq_seasonal.loc[zone]
    pct    = row["pct_change"]
    y      = max(row["summer_aqi"], row["winter_aqi"]) + 4.5
    color  = "#c0392b" if pct > 0 else "#27ae60"
    symbol = "▲" if pct > 0 else "▼"
    ax.annotate(f"{symbol} {abs(pct):.0f}%", xy=(i, y),
                ha="center", va="bottom",
                fontsize=9.5, fontweight="bold", color=color)

ax.set_xticks(x)
ax.set_xticklabels(zones, fontsize=9.5)
for tick, zone in zip(ax.get_xticklabels(), zones):
    tick.set_color(ZONE_COLORS[zone])
    tick.set_fontweight("bold")

ax.set_ylabel("Average PM2.5 AQI", fontsize=10)
ax.set_title("PM2.5 AQI — Summer vs. Winter by Zone",
             fontsize=11, fontweight="semibold", pad=8, loc="left")
ax.legend(fontsize=9, loc="upper right", framealpha=0.85, edgecolor="#ddd")
ax.set_ylim(0, ax.get_ylim()[1] * 1.28)

# 
# PANEL C — Per-station traffic % change with PM2.5 reference lines
# 
ax = ax_tr

#  Draw bars 
for _, row in stations.iterrows():
    color = ZONE_COLORS[row["zone"]]
    ax.barh(row["ypos"], row["pct_change"], height=0.65,
            color=color, alpha=0.80, edgecolor="white", linewidth=0.5, zorder=3)

    # Value label — right of positive bars, left of negative
    pct    = row["pct_change"]
    offset = 1.8 if pct >= 0 else -1.8
    ha     = "left" if pct >= 0 else "right"
    ax.text(pct + offset, row["ypos"], f"{pct:+.1f}%",
            va="center", ha=ha, fontsize=8, color="#222", zorder=4)

#  Zero reference line 
ax.axvline(0, color="#555", linewidth=0.9, zorder=5)

#  Zone group geometry 
corr_rows  = stations[stations["zone"] == "Transit Corridor"]
shore_rows = stations[stations["zone"] == "Jersey Shore"]
corr_ymin  = corr_rows["ypos"].min()  - 0.45
corr_ymax  = corr_rows["ypos"].max()  + 0.45
shore_ymin = shore_rows["ypos"].min() - 0.45
shore_ymax = shore_rows["ypos"].max() + 0.45
gap_mid    = (corr_ymin + shore_ymax) / 2

#  Subtle background bands per zone 
ax.axhspan(corr_ymin,  corr_ymax,  facecolor=ZONE_COLORS["Transit Corridor"],
           alpha=0.04, zorder=0)
ax.axhspan(shore_ymin, shore_ymax, facecolor=ZONE_COLORS["Jersey Shore"],
           alpha=0.04, zorder=0)

#  Separator line between zones 
ax.axhline(gap_mid, color="#bbb", linewidth=0.8, linestyle="--", zorder=2)

#  PM2.5 % change reference lines per zone 
for zone, (ymin, ymax) in [
    ("Transit Corridor", (corr_ymin,  corr_ymax)),
    ("Jersey Shore",     (shore_ymin, shore_ymax)),
]:
    ref_x = pm25_pct[zone]
    color = ZONE_COLORS[zone]
    ax.vlines(ref_x, ymin, ymax,
              color=color, linewidth=1.8, linestyle=":", alpha=0.85, zorder=4)
    ax.text(ref_x, ymax + 0.15,
            f"PM2.5\n{ref_x:+.0f}%",
            ha="center", va="bottom",
            fontsize=7.5, color=color, fontweight="bold")

#  Zone header labels (as extra y-ticks above each group) 
corr_header_y  = corr_ymax  + 0.85
shore_header_y = shore_ymax + 0.85

all_yticks  = list(stations["ypos"]) + [corr_header_y, shore_header_y]
all_labels  = list(stations["label"]) + ["TRANSIT CORRIDOR", "JERSEY SHORE"]
all_colors  = (
    [ZONE_COLORS[r["zone"]] for _, r in stations.iterrows()]
    + [ZONE_COLORS["Transit Corridor"], ZONE_COLORS["Jersey Shore"]]
)
all_weights = ["normal"] * len(stations) + ["bold", "bold"]
all_sizes   = [8.5]     * len(stations) + [9.5,  9.5]

ax.set_yticks(all_yticks)
ax.set_yticklabels(all_labels)
for tick, col, wt, sz in zip(ax.get_yticklabels(), all_colors, all_weights, all_sizes):
    tick.set_color(col)
    tick.set_fontweight(wt)
    tick.set_fontsize(sz)

ax.set_xlabel("% Change in ADT — Summer vs. Winter", fontsize=9.5)
ax.set_title("Traffic Volume Change by Station",
             fontsize=11, fontweight="semibold", pad=8, loc="left")
ax.set_ylim(shore_ymin - 0.8, corr_header_y + 0.5)

# x-axis: leave enough room for the +119% bar label
ax.set_xlim(left=min(stations["pct_change"].min() - 12, -28))
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:+.0f}%"))
ax.tick_params(axis="x", labelsize=8.5)

# Turn off horizontal grid — it clutters the station chart
ax.yaxis.grid(False)
ax.xaxis.grid(True)

#  Clifton footnote 
ax.text(
    0.01, -0.07,
    "† NJ-3 Clifton: active construction detours rerouted traffic to parallel roads "
    "during the study period — does not reflect a reduction in regional VMT.",
    transform=ax.transAxes, fontsize=7, color="#777", style="italic",
    va="top", wrap=True
)

#  Source footnote 
fig.text(
    0.5, 0.015,
    "Sources: EPA Air Quality System (AQS) — NJ daily readings 2023–2025  ·  "
    "FHWA Travel Monitoring Analysis System (TMAS) — NJ monthly traffic counts 2023–2025",
    ha="center", fontsize=7.5, color="#888888", style="italic",
)

#  Save 
out_path = "/charts/seasonal_traffic_pm25_comparison.png"
os.makedirs(os.path.dirname(out_path), exist_ok=True)
fig.savefig(out_path, dpi=160, bbox_inches="tight", facecolor="white")
print(f"\nSaved → {out_path}")
plt.close()