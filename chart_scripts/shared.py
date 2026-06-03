import plotly.graph_objects as go
from plotly.subplots import make_subplots

DATA_DIR = "data"

ZONE_COLORS = {
    "Transit Corridor": "#e31a1c",
    "Jersey Shore":     "#1f78b4",
    "Newark Gateway":   "#ff7f00",
    "Statewide":        "#6a3d9a",
}

BASE_LAYOUT = dict(
    font=dict(family="Courier New, monospace", size=12, color="#1a1a1a"),
    paper_bgcolor="#ffffff",
    plot_bgcolor="#f8f8f8",
    hoverlabel=dict(font_family="Courier New, monospace", bgcolor="white"),
    margin=dict(t=80, b=60, l=60, r=40),
)

MONTH_LABELS = {6: "Jun", 7: "Jul", 8: "Aug", 11: "Nov", 12: "Dec"}
MONTH_ORDER  = ["Nov", "Dec", "Jun", "Jul", "Aug"]
DAY_ORDER    = ["Friday", "Saturday", "Sunday"]
