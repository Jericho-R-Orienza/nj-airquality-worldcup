# NJ World Cup Traffic and Air Quality Analysis

A GIS and data analysis project examining air quality and environmental justice impacts of the 2026 FIFA World Cup on NJ Transit corridor communities. Built for the NJ Department of Environmental Protection Job Fair.

## What It Is

Eight World Cup matches are scheduled at MetLife Stadium in East Rutherford, NJ during peak ozone season (June and July 2026). This project maps where the environmental cost of hosting those games lands, and who bears it.

The analysis combines EPA air quality data, FHWA traffic monitoring data, and NJ Transit ridership information to answer three questions:

1. How does seasonal traffic differ between the MetLife transit corridor and the Jersey Shore?
2. How elevated is the summer air quality baseline before a single fan arrives?
3. What do historical events (NFL games, Memorial Day, July 4th) tell us about how the system responds to additional pressure?

## Key Findings

- **Shore roads spike, corridor roads do not.** Jersey Shore highway approach roads average +39% higher traffic in summer vs. winter. The MetLife corridor (Bergen, Hudson, Passaic counties) shows essentially no seasonal change (+0.1%).
- **Summer ozone is 82% higher before any World Cup traffic.** Heat and photochemical reactions drive this gap independent of event activity.
- **NFL game days leave no detectable AQI fingerprint.** A single well-managed transit event at MetLife does not produce a measurable county-level air quality spike. The World Cup risk is different: 8 games across 5 weeks, 4 on weekdays overlapping rush hour, with transit capped at 40,000 fans while the stadium holds 82,500.
- **Essex County has no federal air quality monitor (2023-2025).** The communities most likely to absorb the environmental cost of the tournament are the ones for which we have the least data.

## Data Sources

| Source | Coverage |
|---|---|
| EPA Air Quality System (AQS) | PM2.5, Ozone, NO2 daily readings, 28 NJ stations, 2023-2025 |
| FHWA Travel Monitoring Analysis System (TMAS) | Hourly traffic volumes, 181 permanent stations, 2023-2025 |
| NJ Transit | Matchday transportation plan and fare structure |
| NJDEP Open Data Portal | Contaminated sites, environmental justice layers |
| US Census Bureau | Demographic data by census tract |
| FIFA / NY-NJ Host Committee | Tourism volume projections |

## Tech Stack

- Python (data processing and chart generation)
- GeoPandas (spatial analysis)
- Folium (interactive map)
- Plotly (interactive charts)
- HTML/CSS (report layout)

## Project Structure

```
data/               cleaned CSVs for air quality, traffic, and seasonal baselines
chart_scripts/      Python scripts that generate each Plotly chart
charts/             rendered HTML charts embedded in the report
map/                Folium interactive map
index.html          main report page
```

## Charts

| Chart | What It Shows |
|---|---|
| chart1_bottleneck | Summer vs. winter traffic percent change by TMAS station |
| chart1b_seasonal_baseline | Side-by-side seasonal change in traffic and ozone by zone |
| chart2_shore_monthly | Jersey Shore monthly traffic and ozone on a dual axis |
| chart3a_pm25_monthly_trend | Monthly average PM2.5 AQI by zone across 12 months |
| chart3b_pm25_seasonal_bars | Summer vs. winter PM2.5 AQI by zone |
| chart3c_traffic_pct_change | Traffic percent change by station with PM2.5 reference lines |
| chart4_nfl_null | NFL game day AQI vs. matched control Sundays |
| chart5_july4_capacity | July 4th Shore traffic vs. typical July weekend baseline |
| chart6_memday_proof | Memorial Day ozone AQI vs. May baseline, 2023-2025 |

## Policy Recommendations

1. **Transit fare parity on matchdays** to reduce car spillover (supported by FIFA's own COO warning on elevated fares)
2. **Temporary air quality sensor deployment** in Essex and Hudson County transit corridors during the tournament
3. **Diesel idle enforcement** at shuttle staging areas near Secaucus Junction and Harrison Fan Hub
4. **Allocate EV buses** to World Cup matchday shuttle routes
5. **Long-term NJ Transit expansion** to close coverage gaps that force car dependency in underserved corridors

---

Data from EPA AQS, FHWA TMAS, and NJ Transit. Analysis conducted for educational and portfolio purposes.
