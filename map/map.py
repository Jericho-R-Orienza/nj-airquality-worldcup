"""
World Cup Transit Corridor Air Quality & Environmental Justice Analysis
NJ DEP Job Fair Project

Generates an interactive Folium map saved as nj_worldcup_map.html.
Embed in a GitHub Pages site using:
    <iframe src="nj_worldcup_map.html" width="100%" height="600px" frameborder="0"></iframe>

Dependencies:
    pip install folium pandas geopandas branca requests

Usage:
    python nj_worldcup_map.py

Output:
    nj_worldcup_map.html  (open in any browser or upload to GitHub Pages)
"""

import math
import folium
import pandas as pd
import geopandas as gpd
from folium import FeatureGroup, LayerControl
from branca.element import Template, MacroElement


# CONFIG — update DATA_DIR to wherever your CSV files live
DATA_DIR    = "data"
OUTPUT_FILE = "nj_worldcup_map.html"


# LOAD DATA
print("Loading data files...")

adt       = pd.read_csv(f"{DATA_DIR}/nj_traffic_adt_master.csv")
aq_long   = pd.read_csv(f"{DATA_DIR}/aq_station_summary_long.csv")
aq_wide   = pd.read_csv(f"{DATA_DIR}/aq_station_summary_wide.csv")
county_aq = pd.read_csv(f"{DATA_DIR}/county_aqi_seasonal_comparison.csv")

print(f"  Traffic stations : {len(adt)}")
print(f"  AQ station rows  : {len(aq_long)}")
print(f"  Counties in AQ   : {county_aq['County Name'].nunique()}")


# COMPUTE AQ PCT CHANGE
# Triangle fill color encodes how much worse summer AQI is vs winter baseline.
# This is the primary visual argument: summer stress, not just absolute level.
# We compute it from the wide file and merge into the summer baseline subset.
aq_wide["aq_pct_change"] = (
    (aq_wide["avg_aqi_Summer_Baseline"] - aq_wide["avg_aqi_Winter_Baseline"])
    / aq_wide["avg_aqi_Winter_Baseline"] * 100
).round(1)

# Pre-build summer baseline subset with pct_change and summer AQI merged in
aq_summer = aq_long[aq_long["group"] == "Summer Baseline"].copy()
aq_summer = aq_summer.merge(
    aq_wide[["Local Site Name", "pollutant", "aq_pct_change",
             "avg_aqi_Summer_Baseline"]],
    on=["Local Site Name", "pollutant"],
    how="left",
)

print(f"  AQ summer markers: {len(aq_summer)} ({aq_summer['Local Site Name'].nunique()} stations)")


# NJ COUNTY SHAPEFILE
# Downloads NJ county boundaries from Census TIGER/Line (requires internet).
# If the download fails, choropleth is skipped — all other layers unaffected.
print("Downloading NJ county shapefile...")

NJ_COUNTIES_URL = (
    "https://www2.census.gov/geo/tiger/TIGER2023/COUNTY/tl_2023_34_county.zip"
)

CHOROPLETH_ENABLED = True
nj_counties = None

try:
    nj_counties = gpd.read_file(NJ_COUNTIES_URL)
    nj_counties["NAME"] = nj_counties["NAME"].str.strip()
    print(f"  Loaded {len(nj_counties)} NJ counties")
except Exception as e:
    print(f"  WARNING: Could not download county shapefile: {e}")
    print("  Choropleth layer will be skipped — all other layers unaffected.")
    CHOROPLETH_ENABLED = False


# CHOROPLETH DATA
ozone_delta = (
    county_aq[county_aq["pollutant"] == "Ozone"]
    .groupby("County Name", as_index=False)["aqi_delta"]
    .mean()
    .rename(columns={"aqi_delta": "avg_ozone_delta"})
)

if CHOROPLETH_ENABLED:
    nj_map_data = nj_counties.merge(
        ozone_delta,
        left_on="NAME",
        right_on="County Name",
        how="left",
    )


# COLOR & STYLE HELPERS

# Zone border colors for traffic circles
ZONE_COLORS = {
    "Transit Corridor": "#e31a1c",
    "Jersey Shore":     "#1f78b4",
    "Newark Gateway":   "#ff7f00",
    "Statewide":        "#6a3d9a",
}


def pct_to_fill(pct):
    """
    Traffic circles: diverging scale for summer % ADT change.
    Red = large spike (bottleneck). Blue = seasonal decline.
    """
    if pd.isna(pct):
        return "#aaaaaa"
    if pct > 80:
        return "#d73027"
    if pct > 50:
        return "#f46d43"
    if pct > 25:
        return "#fdae61"
    if pct > 10:
        return "#fee090"
    if pct >= 0:
        return "#ffffbf"
    return "#abd9e9"


def aq_pct_to_fill(pct):
    """
    AQ triangles: unified % change fill scale.
    Warm  = summer AQI increase (ozone, PM2.5).
    Cool  = summer AQI decrease (NO2 — chemically expected as NOx converts
            to ozone in heat; declining NO2 is a known atmospheric signal).
    """
    if pd.isna(pct):
        return "#aaaaaa"
    if pct > 100:
        return "#d73027"    # dark red   — extreme summer increase
    if pct > 75:
        return "#f46d43"    # orange-red
    if pct > 50:
        return "#fdae61"    # orange
    if pct > 25:
        return "#fee090"    # light amber
    if pct >= 0:
        return "#ffffbf"    # pale yellow — minimal increase
    if pct >= -25:
        return "#e0f3f8"    # very light blue — slight decline
    return "#74add1"        # medium blue  — large decline (NO2)


def aqi_to_border_style(aqi):
    """
    AQ triangles: border encodes absolute summer AQI level (3 tiers).
    Returns (color, width, dash).

    Good (<45)              thin dark border — no concern
    Approaching Moderate    amber dashed    — within 5 points of EPA threshold
    (45–50)
    Moderate (51+)          thick solid     — at or above EPA Moderate threshold
    """
    if pd.isna(aqi):
        return "#888888", 1.5, False
    if aqi > 50:
        return "#e65c00", 3.0, False    # thick solid orange — Moderate
    if aqi >= 45:
        return "#f0ad4e", 2.0, True     # amber dashed — approaching Moderate
    return "#444444", 1.5, False        # thin dark — Good


def make_aq_triangle(fill_color, border_color, border_width, dash=False):
    """
    Returns a Folium DivIcon rendered as an upward-pointing SVG triangle.
    Anchor is set to the bottom center so the point aligns to the lat/lon.
    """
    w, h = 20, 18
    points = "10,1 19,17 1,17"         # 1px inset so stroke doesn't clip
    dash_attr = 'stroke-dasharray="4,2"' if dash else ""

    svg = (
        f'<svg width="{w}" height="{h}" '
        f'xmlns="http://www.w3.org/2000/svg" overflow="visible">'
        f'<polygon points="{points}" '
        f'fill="{fill_color}" '
        f'stroke="{border_color}" '
        f'stroke-width="{border_width}" '
        f'{dash_attr}/>'
        f"</svg>"
    )

    return folium.DivIcon(
        html=svg,
        icon_size=(w, h),
        icon_anchor=(w // 2, h),    # bottom center
    )


def adt_to_radius(adt, min_r=5, max_r=22):
    """Log-scale ADT to circle radius for traffic stations."""
    if pd.isna(adt) or adt <= 0:
        return min_r
    log_min = math.log10(300)
    log_max = math.log10(175_000)
    log_val = math.log10(max(float(adt), 300))
    return round(min_r + (max_r - min_r) * (log_val - log_min) / (log_max - log_min), 1)


# CURATED TRAFFIC STATION IDs (thicker border ring)
CURATED_IDS = {
    "00003R", "0080DL", "E02132", "00003C", "E02111", "N00440",
    "0001CX", "000280", "N31025",
    "CO0563", "00040B", "00322H", "N06120", "N06114",
    "00034B", "CO0539", "E06108",
}


# WORLD CUP LOCATIONS
WORLDCUP_LOCATIONS = [
    {
        "name": "MetLife Stadium",
        "lat":  40.8135, "lon": -74.0745,
        "note": "8 FIFA matches · Final July 19, 2026 · 82,500 capacity",
    },
    {
        "name": "Secaucus Junction",
        "lat":  40.7547, "lon": -74.0538,
        "note": "Primary fan transfer hub · 40,000 rail tickets/matchday · "
                "Commuter trains rerouted 4 hrs pre-match",
    },
    {
        "name": "Penn Station NYC",
        "lat":  40.7506, "lon": -73.9971,
        "note": "Fan departure point · Restricted to World Cup ticketholders "
                "4 hrs before kickoff",
    },
    {
        "name": "Newark Penn Station",
        "lat":  40.7347, "lon": -74.1741,
        "note": "Commuter overflow hub · Receives displaced commuters "
                "during matchday blackout windows",
    },
    {
        "name": "Jersey Fan Hub (SI Stadium, Harrison)",
        "lat":  40.7480, "lon": -74.1503,
        "note": "Official FIFA fan hub · Harrison, NJ · 16 match dates "
                "(Jun 14 - Jul 15)",
    },
    {
        "name": "American Dream Fan Fest",
        "lat":  40.8133, "lon": -74.0680,
        "note": "39-day continuous fan festival · Jun 11 - Jul 19",
    },
    {
        "name": "Liberty State Park Fan Village",
        "lat":  40.7017, "lon": -74.0443,
        "note": "Official fan village · Jersey City · Knockout stage events",
    },
]


# BUILD MAP
print("Building map...")

m = folium.Map(
    location=[40.15, -74.50],
    zoom_start=8,
    tiles="CartoDB positron",
    prefer_canvas=True,
)

# Title
title_html = """
{% macro html(this, kwargs) %}
<div style="
    position: fixed; top: 12px; left: 60px; z-index: 9999;
    background: rgba(255,255,255,0.95);
    border-left: 5px solid #e31a1c;
    border-radius: 0 6px 6px 0;
    padding: 10px 16px 8px 12px;
    font-family: monospace;
    box-shadow: 2px 2px 8px rgba(0,0,0,0.15);
    max-width: 340px;">
  <div style="font-size:14px; font-weight:bold; color:#1a1a1a;">
    NJ World Cup Air Quality Analysis
  </div>
  <div style="font-size:11px; color:#555; margin-top:3px;">
    Traffic bottleneck &middot; AQI burden &middot; Environmental justice<br>
    EPA AQS 2023&ndash;2025 &middot; FHWA TMAS &middot; FIFA World Cup 2026
  </div>
</div>
{% endmacro %}
"""
title_el = MacroElement()
title_el._template = Template(title_html)
m.get_root().add_child(title_el)


#  LAYER 1: County Choropleth 
if CHOROPLETH_ENABLED:
    print("  Adding choropleth...")
    folium.Choropleth(
        geo_data=nj_map_data.__geo_interface__,
        name="County Ozone Burden (Summer vs Winter Delta)",
        data=ozone_delta,
        columns=["County Name", "avg_ozone_delta"],
        key_on="feature.properties.NAME",
        fill_color="YlOrRd",
        fill_opacity=0.30,
        line_opacity=0.5,
        line_color="#777777",
        legend_name="Avg Summer Ozone AQI Increase vs Winter Baseline",
        nan_fill_color="#eeeeee",
        nan_fill_opacity=0.4,
    ).add_to(m)
else:
    print("  Skipping choropleth (shapefile unavailable)")


#  LAYER 2: Traffic Station Circles 
# Fill  = summer % ADT change vs winter (bottleneck signal)
# Size  = summer ADT on log scale
# Border color = zone
# Border width = 3px if curated focus station, else 1px
print("  Adding traffic stations...")

traffic_group = FeatureGroup(name="Traffic Stations — Summer % Change", show=True)

for _, row in adt.iterrows():
    is_curated = str(row["station_id"]).strip() in CURATED_IDS
    fill_color = pct_to_fill(row["pct_change"])
    zone_color = ZONE_COLORS.get(row["zone"], "#888888")
    radius     = adt_to_radius(row["summer_adt"])
    weight     = 3 if is_curated else 1

    pct_str   = f"{row['pct_change']:+.1f}%" if pd.notna(row["pct_change"]) else "N/A"
    w_adt_str = f"{int(row['winter_adt']):,}" if pd.notna(row["winter_adt"]) else "N/A"
    s_adt_str = f"{int(row['summer_adt']):,}"

    spike_label = ""
    if pd.notna(row["pct_change"]) and row["pct_change"] > 80:
        spike_label = " | BOTTLENECK"
    elif pd.notna(row["pct_change"]) and row["pct_change"] > 50:
        spike_label = " | High spike"

    curated_badge = " [FOCUS]" if is_curated else ""
    delta_color   = "#c00000" if pd.notna(row["pct_change"]) and row["pct_change"] > 25 else "#333333"

    popup_html = f"""
    <div style="font-family: monospace; font-size: 12px; min-width: 230px;">
      <b style="font-size: 13px;">{row['station_location']}{spike_label}{curated_badge}</b>
      <br><span style="color: #666;">Zone: {row['zone']}</span>
      <hr style="margin: 5px 0;">
      <table style="width: 100%; border-collapse: collapse;">
        <tr><td>Summer ADT</td><td><b>{s_adt_str}</b></td></tr>
        <tr><td>Winter ADT</td><td><b>{w_adt_str}</b></td></tr>
        <tr><td>Summer change</td>
            <td><b style="color: {delta_color};">{pct_str}</b></td></tr>
      </table>
      <div style="font-size: 10px; color: #888; margin-top: 4px;">
        Circle size = Summer ADT &middot; Border color = Zone
      </div>
    </div>
    """

    folium.CircleMarker(
        location=[row["latitude"], row["longitude"]],
        radius=radius,
        color=zone_color,
        weight=weight,
        fill=True,
        fill_color=fill_color,
        fill_opacity=0.82,
        popup=folium.Popup(popup_html, max_width=270),
        tooltip=f"{row['station_location']} | {pct_str} summer change",
    ).add_to(traffic_group)

traffic_group.add_to(m)


#  LAYER 3: AQ Station Triangles 
# Shape  = upward-pointing triangle (distinct from traffic circles)
# Fill   = summer vs winter AQI % change (the seasonal burden story)
# Border = absolute summer AQI level:
#           thin dark   = Good (<45)
#           amber dashed = Approaching Moderate (45–50)
#           thick orange = Moderate (51+)
print("  Adding AQ station layers...")

aq_wide_idx = aq_wide.set_index(["Local Site Name", "pollutant"])

# AQI label lookup for popup
def aqi_label(aqi):
    if pd.isna(aqi):
        return "N/A"
    if aqi > 50:
        return "Moderate"
    if aqi >= 45:
        return "Approaching Moderate"
    return "Good"

for pollutant in ["Ozone", "PM2.5", "NO2"]:
    show_default = (pollutant == "Ozone")
    fg = FeatureGroup(
        name=f"AQ Stations — {pollutant} (Summer vs Winter % Change)",
        show=show_default,
    )

    subset = aq_summer[aq_summer["pollutant"] == pollutant]

    for _, row in subset.iterrows():
        station    = row["Local Site Name"]
        pct        = row["aq_pct_change"]
        summer_aqi = row["avg_aqi_Summer_Baseline"]

        fill_color                    = aq_pct_to_fill(pct)
        border_color, border_w, dash  = aqi_to_border_style(summer_aqi)
        icon                          = make_aq_triangle(fill_color, border_color, border_w, dash)

        pct_str = f"{pct:+.1f}%" if pd.notna(pct) else "N/A"

        # Pull comparison values from wide file for popup table
        try:
            w = aq_wide_idx.loc[(station, pollutant)]
            s_aqi    = f"{w['avg_aqi_Summer_Baseline']:.1f}"
            wi_aqi   = f"{w['avg_aqi_Winter_Baseline']:.1f}"
            nfl_aqi  = f"{w['avg_aqi_NFL_Game_Day']:.1f}"
            delta    = w["summer_vs_winter_delta"]
            delta_str = f"{delta:+.1f}"
        except KeyError:
            s_aqi = wi_aqi = nfl_aqi = delta_str = "N/A"

        pct_color  = "#c00000" if pd.notna(pct) and pct > 50 else "#333333"
        status     = aqi_label(summer_aqi)
        status_color = (
            "#e65c00" if summer_aqi > 50
            else "#c47f00" if summer_aqi >= 45
            else "#336600"
        ) if pd.notna(summer_aqi) else "#333333"

        popup_html = f"""
        <div style="font-family: monospace; font-size: 12px; min-width: 255px;">
          <b style="font-size: 13px;">{station}</b>
          <br><span style="color: #666;">{row['County Name']} County &middot; {pollutant}</span>
          <hr style="margin: 5px 0;">
          <table style="width: 100%; border-collapse: collapse;">
            <tr>
              <td>Summer vs Winter</td>
              <td><b style="color: {pct_color};">{pct_str}</b></td>
            </tr>
            <tr><td>Summer AQI</td><td><b>{s_aqi}</b></td></tr>
            <tr><td>Winter AQI</td><td><b>{wi_aqi}</b></td></tr>
            <tr><td>NFL Game Day AQI</td><td><b>{nfl_aqi}</b></td></tr>
            <tr><td>AQI Status</td>
                <td><b style="color: {status_color};">{status}</b></td></tr>
          </table>
          <div style="font-size: 10px; color: #888; margin-top: 4px;">
            Fill = seasonal % change &middot; Border = AQI level<br>
            NFL = matched control comparison (2023&ndash;2024 seasons)
          </div>
        </div>
        """

        folium.Marker(
            location=[row["Latitude"], row["Longitude"]],
            icon=icon,
            popup=folium.Popup(popup_html, max_width=290),
            tooltip=f"{station} | {pollutant} {pct_str} summer change | {status}",
        ).add_to(fg)

    fg.add_to(m)


#  LAYER 4: World Cup Locations 
print("  Adding World Cup markers...")

wc_group = FeatureGroup(name="FIFA World Cup 2026 Locations", show=True)

for loc in WORLDCUP_LOCATIONS:
    popup_html = f"""
    <div style="font-family: monospace; font-size: 12px; min-width: 220px;">
      <b style="font-size: 13px; color: #8B0000;">{loc['name']}</b>
      <hr style="margin: 5px 0;">
      {loc['note']}
    </div>
    """
    folium.Marker(
        location=[loc["lat"], loc["lon"]],
        icon=folium.Icon(color="darkred", icon="star", prefix="fa"),
        popup=folium.Popup(popup_html, max_width=260),
        tooltip=loc["name"],
    ).add_to(wc_group)

wc_group.add_to(m)


#  LAYER 5: Essex County Monitoring Gap 
print("  Adding Essex County annotation...")

essex_group = FeatureGroup(name="Essex County — AQ Monitoring Gap", show=True)

essex_popup = """
<div style="font-family: monospace; font-size: 12px; max-width: 270px;">
  <b>Essex County - No AQ Monitor (2023-2025)</b>
  <hr style="margin: 5px 0;">
  Essex County (Newark) has <b>no PM2.5, NO2, or ozone monitoring station</b>
  in the federal EPA AQS dataset for 2023&ndash;2025.<br><br>
  Newark sits adjacent to:
  <ul style="margin: 4px 0; padding-left: 16px;">
    <li>I-95 / NJ Turnpike</li>
    <li>Newark Liberty Airport</li>
    <li>Port Newark</li>
    <li>Five active Superfund sites</li>
  </ul>
  <b style="color: #856404;">
    The communities most likely to absorb the environmental cost of the
    World Cup are the least measured in this dataset. That gap is itself
    an environmental justice finding.
  </b>
</div>
"""

folium.Marker(
    location=[40.7957, -74.2444],
    icon=folium.DivIcon(
        html="""
        <div style="
            background: #fff3cd;
            border: 2px solid #f0ad4e;
            border-radius: 6px;
            padding: 5px 9px;
            font-family: monospace;
            font-size: 11px;
            font-weight: bold;
            color: #856404;
            white-space: nowrap;
            box-shadow: 2px 2px 5px rgba(0,0,0,0.2);">
          Essex Co.<br>No AQ Monitor
        </div>""",
        icon_size=(112, 38),
        icon_anchor=(56, 19),
    ),
    popup=folium.Popup(essex_popup, max_width=290),
    tooltip="Essex County: No Federal AQ Monitor (2023-2025) — click for details",
).add_to(essex_group)

essex_group.add_to(m)


#  LEGEND 
legend_html = """
{% macro html(this, kwargs) %}
<div style="
    position: fixed;
    bottom: 40px;
    left: 20px;
    z-index: 9999;
    background: rgba(255,255,255,0.96);
    border: 1px solid #cccccc;
    border-radius: 8px;
    padding: 14px 16px;
    font-family: monospace;
    font-size: 12px;
    box-shadow: 3px 3px 8px rgba(0,0,0,0.15);
    max-width: 225px;
    line-height: 1.7;">

  <div style="font-weight:bold; font-size:13px; margin-bottom:4px;">
    &#9711; Traffic: Summer % Change
  </div>
  <div><span style="background:#d73027;display:inline-block;width:13px;height:13px;border-radius:50%;vertical-align:middle;margin-right:5px;"></span>&gt; 80% &mdash; Bottleneck</div>
  <div><span style="background:#f46d43;display:inline-block;width:13px;height:13px;border-radius:50%;vertical-align:middle;margin-right:5px;"></span>50&ndash;80%</div>
  <div><span style="background:#fdae61;display:inline-block;width:13px;height:13px;border-radius:50%;vertical-align:middle;margin-right:5px;"></span>25&ndash;50%</div>
  <div><span style="background:#fee090;display:inline-block;width:13px;height:13px;border-radius:50%;vertical-align:middle;margin-right:5px;"></span>10&ndash;25%</div>
  <div><span style="background:#ffffbf;display:inline-block;width:13px;height:13px;border-radius:50%;border:1px solid #ccc;vertical-align:middle;margin-right:5px;"></span>0&ndash;10% (flat)</div>
  <div><span style="background:#abd9e9;display:inline-block;width:13px;height:13px;border-radius:50%;vertical-align:middle;margin-right:5px;"></span>Declining</div>
  <div style="font-size:10px;color:#777;margin-top:2px;">Circle size = Summer ADT volume</div>

  <hr style="margin:8px 0;border-color:#ddd;">

  <div style="font-weight:bold;margin-bottom:3px;">Zone Borders</div>
  <div><span style="background:#e31a1c;display:inline-block;width:13px;height:5px;vertical-align:middle;border-radius:2px;margin-right:5px;"></span>Transit Corridor</div>
  <div><span style="background:#1f78b4;display:inline-block;width:13px;height:5px;vertical-align:middle;border-radius:2px;margin-right:5px;"></span>Jersey Shore</div>
  <div><span style="background:#ff7f00;display:inline-block;width:13px;height:5px;vertical-align:middle;border-radius:2px;margin-right:5px;"></span>Newark Gateway</div>
  <div><span style="background:#6a3d9a;display:inline-block;width:13px;height:5px;vertical-align:middle;border-radius:2px;margin-right:5px;"></span>Statewide</div>
  <div style="font-size:10px;color:#777;margin-top:2px;">Thick border = curated focus station</div>

  <hr style="margin:8px 0;border-color:#ddd;">

  <div style="font-weight:bold; font-size:13px; margin-bottom:4px;">
    &#9651; AQ Stations: Fill = Summer % Change
  </div>
  <div><span style="background:#d73027;display:inline-block;width:13px;height:13px;vertical-align:middle;margin-right:5px;"></span>&gt; 100%</div>
  <div><span style="background:#f46d43;display:inline-block;width:13px;height:13px;vertical-align:middle;margin-right:5px;"></span>75&ndash;100%</div>
  <div><span style="background:#fdae61;display:inline-block;width:13px;height:13px;vertical-align:middle;margin-right:5px;"></span>50&ndash;75%</div>
  <div><span style="background:#fee090;display:inline-block;width:13px;height:13px;vertical-align:middle;margin-right:5px;"></span>25&ndash;50%</div>
  <div><span style="background:#ffffbf;display:inline-block;width:13px;height:13px;border:1px solid #ccc;vertical-align:middle;margin-right:5px;"></span>0&ndash;25%</div>
  <div><span style="background:#e0f3f8;display:inline-block;width:13px;height:13px;vertical-align:middle;margin-right:5px;"></span>&minus;25&ndash;0% (slight decline)</div>
  <div><span style="background:#74add1;display:inline-block;width:13px;height:13px;vertical-align:middle;margin-right:5px;"></span>&lt; &minus;25% (NO2 summer decline)</div>

  <hr style="margin:8px 0;border-color:#ddd;">

  <div style="font-weight:bold;margin-bottom:3px;">&#9651; AQ Border: Summer AQI Level</div>
  <div>
    <svg width="14" height="12" style="vertical-align:middle;margin-right:5px;">
      <polygon points="7,1 13,11 1,11" fill="#fee090" stroke="#444" stroke-width="1.5"/>
    </svg>
    Good (AQI &lt; 45)
  </div>
  <div>
    <svg width="14" height="12" style="vertical-align:middle;margin-right:5px;">
      <polygon points="7,1 13,11 1,11" fill="#fee090" stroke="#f0ad4e" stroke-width="2" stroke-dasharray="3,2"/>
    </svg>
    Approaching Moderate (45&ndash;50)
  </div>
  <div>
    <svg width="14" height="12" style="vertical-align:middle;margin-right:5px;">
      <polygon points="7,1 13,11 1,11" fill="#fdae61" stroke="#e65c00" stroke-width="3"/>
    </svg>
    Moderate (AQI &gt; 50)
  </div>

  <hr style="margin:8px 0;border-color:#ddd;">

  <div style="font-weight:bold;color:#8B0000;margin-bottom:2px;">FIFA World Cup 2026</div>
  <div style="font-size:11px;color:#555;">Click star markers for venue details</div>

  <hr style="margin:8px 0;border-color:#ddd;">

  <div style="font-size:10px;color:#888;">
    Sources: EPA AQS 2023&ndash;2025<br>
    FHWA TMAS &middot; NJ DEP &middot; US Census<br>
    Use layer panel (top right) to toggle
  </div>

</div>
{% endmacro %}
"""

legend_el = MacroElement()
legend_el._template = Template(legend_html)
m.get_root().add_child(legend_el)


#  LAYER CONTROL 
LayerControl(collapsed=False, position="topright").add_to(m)


# SAVE
m.save(OUTPUT_FILE)
print(f"\n  Map saved to {OUTPUT_FILE}")
print(f"  Open in any browser to preview.")
print(f'  Embed with: <iframe src="{OUTPUT_FILE}" width="100%" height="600px" frameborder="0"></iframe>')