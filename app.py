"""GBoS GEOAI — Greenhouse Gas & Environmental Screening Dashboard.
Run locally with: streamlit run app.py

Earth Engine authentication is performed locally; never commit credentials.
All composite indices are screening proxies, not direct groundwater nitrate measurements.
"""
from datetime import date, timedelta
import streamlit as st
import ee
import geemap.foliumap as geemap

APP_TITLE = "GBoS GEOAI | Environmental Intelligence"
COUNTRY = "The Gambia"
GAUL0 = "FAO/GAUL/2015/level0"
GAUL1 = "FAO/GAUL/2015/level1"
GAUL2 = "FAO/GAUL/2015/level2"

st.set_page_config(page_title=APP_TITLE, page_icon="🇬🇲", layout="wide")
st.markdown("""
<style>
.block-container{padding-top:1rem;max-width:100%}
.gbos-header{background:#062b45;color:white;padding:1rem 1.25rem;border-radius:12px;margin-bottom:1rem}
.gbos-header h1{margin:0;color:white;font-size:1.7rem}
.gbos-header p{margin:.35rem 0 0;color:#d9f2ff}
[data-testid="stMetric"]{background:#f4f8fb;padding:.8rem;border-radius:10px;border:1px solid #d4dee6}
</style>
<div class="gbos-header"><h1>🇬🇲 GBoS GEOAI</h1><p>Greenhouse Gases • Vegetation • Rainfall • Soil Environment • Groundwater Nitrate Susceptibility</p></div>
""", unsafe_allow_html=True)

@st.cache_resource(show_spinner="Connecting to Google Earth Engine…")
def init_ee():
    try:
        ee.Initialize()
    except Exception:
        ee.Authenticate()
        ee.Initialize()
    return True

@st.cache_data(ttl=3600, show_spinner=False)
def admin_names(level):
    asset = GAUL1 if level == "Region" else GAUL2
    field = "ADM1_NAME" if level == "Region" else "ADM2_NAME"
    fc = ee.FeatureCollection(asset).filter(ee.Filter.eq("ADM0_NAME", "Gambia"))
    return sorted(fc.aggregate_array(field).distinct().getInfo())

def country_geometry():
    return ee.FeatureCollection(GAUL0).filter(ee.Filter.eq("ADM0_NAME", "Gambia")).geometry()

def get_aoi(level, selected):
    if level == "National":
        return country_geometry()
    if level == "Region":
        return ee.FeatureCollection(GAUL1).filter(ee.Filter.eq("ADM0_NAME", "Gambia")).filter(ee.Filter.eq("ADM1_NAME", selected)).geometry()
    return ee.FeatureCollection(GAUL2).filter(ee.Filter.eq("ADM0_NAME", "Gambia")).filter(ee.Filter.eq("ADM2_NAME", selected)).geometry()

def collection_mean(collection_id, band, start, end, aoi, scale_factor=1.0):
    col = ee.ImageCollection(collection_id).filterDate(start, end).filterBounds(aoi).select(band)
    count = col.size()
    image = col.mean().multiply(scale_factor).clip(aoi).rename("value")
    return col, image, count

try:
    init_ee()
    ee_ready = True
except Exception as exc:
    ee_ready = False
    st.error("Google Earth Engine could not initialize. Follow the setup instructions in README.md, then restart the app.")
    st.code(str(exc))

with st.sidebar:
    st.header("Analysis controls")
    admin_level = st.selectbox("Study area level", ["National", "Region", "District"])
    selected_admin = "The Gambia"
    if ee_ready and admin_level != "National":
        try:
            names = admin_names(admin_level)
            selected_admin = st.selectbox(f"Select {admin_level.lower()}", names)
        except Exception as exc:
            st.warning(f"Could not load administrative names: {exc}")
            selected_admin = ""
    today = date.today()
    default_start = today - timedelta(days=90)
    date_range = st.date_input("Date range", value=(default_start, today), max_value=today)
    metric = st.selectbox("Environmental variable", [
        "Methane (CH₄)", "Nitrogen dioxide (NO₂)", "Vegetation (NDVI)",
        "Rainfall", "Surface soil moisture", "Groundwater nitrate susceptibility (screening)"
    ])
    run = st.button("Run analysis", type="primary", use_container_width=True)
    st.caption("Processing starts only when you click Run.")

st.info("**Interpretation:** satellite-derived layers describe environmental patterns. A nitrate susceptibility index is not a measured nitrate concentration and must be validated against groundwater samples.")

if not ee_ready:
    st.stop()
if not run:
    st.markdown("### Ready to analyse The Gambia")
    st.write("Choose an area, date range and variable in the sidebar, then click **Run analysis**. The map and summary are generated on demand to reduce unnecessary Earth Engine requests.")
    st.stop()
if not isinstance(date_range, (tuple, list)) or len(date_range) != 2:
    st.error("Please choose both a start and end date.")
    st.stop()
start_date, end_date = date_range
if start_date >= end_date:
    st.error("The start date must be earlier than the end date.")
    st.stop()

with st.spinner("Preparing selected-area analysis…"):
    aoi = get_aoi(admin_level, selected_admin)
    start = start_date.isoformat()
    end = (end_date + timedelta(days=1)).isoformat()
    if metric == "Methane (CH₄)":
        col, image, count = collection_mean("COPERNICUS/S5P/OFFL/L3_CH4", "CH4_column_volume_mixing_ratio_dry_air", start, end, aoi)
        palette = ["#233b8b", "#20b8d5", "#62c370", "#ffe45e", "#e85d3f"]
        vis = {"min": 1750, "max": 1950, "palette": palette}
        units = "ppb (column mixing ratio product)"
    elif metric == "Nitrogen dioxide (NO₂)":
        col, image, count = collection_mean("COPERNICUS/S5P/OFFL/L3_NO2", "tropospheric_NO2_column_number_density", start, end, aoi)
        palette = ["#233b8b", "#20b8d5", "#62c370", "#ffe45e", "#e85d3f"]
        vis = {"min": 0, "max": 0.0002, "palette": palette}
        units = "mol/m² (tropospheric column)"
    elif metric == "Vegetation (NDVI)":
        s2 = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED").filterDate(start, end).filterBounds(aoi).filter(ee.Filter.lte("CLOUDY_PIXEL_PERCENTAGE", 40))
        def add_ndvi(img):
            return img.normalizedDifference(["B8", "B4"]).rename("value")
        col = s2.map(add_ndvi)
        image = col.median().clip(aoi)
        count = col.size()
        palette = ["#8c2d04", "#d94801", "#fee08b", "#a6d96a", "#1a9850"]
        vis = {"min": -0.2, "max": 0.9, "palette": palette}
        units = "NDVI (unitless)"
    elif metric == "Rainfall":
        col, image, count = collection_mean("UCSB-CHG/CHIRPS/DAILY", "precipitation", start, end, aoi)
        # Daily mean is displayed; total-period rainfall is computed separately for summary.
        image = ee.ImageCollection("UCSB-CHG/CHIRPS/DAILY").filterDate(start, end).filterBounds(aoi).select("precipitation").sum().clip(aoi).rename("value")
        palette = ["#fff7bc", "#fec44f", "#fe9929", "#ec7014", "#662506"]
        vis = {"min": 0, "max": 500, "palette": palette}
        units = "mm total over selected period"
    elif metric == "Surface soil moisture":
        col, image, count = collection_mean("NASA/SMAP/SPL4SMGP/007", "sm_surface", start, end, aoi)
        palette = ["#a6611a", "#dfc27d", "#f5f5f5", "#80cdc1", "#018571"]
        vis = {"min": 0, "max": 0.5, "palette": palette}
        units = "m³/m³ (model-assimilated surface soil moisture)"
    else:
        # Relative screening index using rainfall, vegetation and soil/land cover context.
        # This is explicitly not a measured nitrate layer.
        rain = ee.ImageCollection("UCSB-CHG/CHIRPS/DAILY").filterDate(start, end).filterBounds(aoi).select("precipitation").mean().unitScale(0, 15).clamp(0, 1).rename("rain_norm")
        s2 = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED").filterDate(start, end).filterBounds(aoi).filter(ee.Filter.lte("CLOUDY_PIXEL_PERCENTAGE", 40))
        ndvi = s2.map(lambda im: im.normalizedDifference(["B8", "B4"]).rename("ndvi")).median().unitScale(-0.2, 0.9).clamp(0, 1)
        wc = ee.ImageCollection("ESA/WorldCover/v200").first().select("Map").clip(aoi)
        # Transparent proxy weights; land-cover contribution is only a broad context proxy.
        built = wc.eq(50).rename("built_context")
        image = rain.multiply(0.45).add(ndvi.multiply(0.35)).add(built.multiply(0.20)).multiply(100).clip(aoi).rename("value")
        col = ee.ImageCollection([])
        count = ee.Number(0)
        palette = ["#1a9850", "#91cf60", "#fee08b", "#fc8d59", "#d73027"]
        vis = {"min": 0, "max": 100, "palette": palette}
        units = "relative screening score (0–100; not nitrate concentration)"

    scene_count = count.getInfo()
    area_km2 = aoi.area(1).divide(1e6).getInfo()
    stats = image.reduceRegion(reducer=ee.Reducer.mean().combine(ee.Reducer.minMax(), sharedInputs=True), geometry=aoi, scale=10000, bestEffort=True, maxPixels=1e7, tileScale=4).getInfo()
    mean_value = stats.get("value_mean") if stats else None
    min_value = stats.get("value_min") if stats else None
    max_value = stats.get("value_max") if stats else None

c1, c2, c3, c4 = st.columns(4)
c1.metric("Study area", selected_admin)
c2.metric("Area (km²)", f"{area_km2:,.1f}" if area_km2 else "N/A")
c3.metric("Images / scenes", f"{scene_count:,}" if scene_count is not None else "N/A")
c4.metric("Mean value", f"{mean_value:,.5g}" if mean_value is not None else "No data")

left, right = st.columns([1.7, 1])
with left:
    st.subheader(f"Map — {metric}")
    m = geemap.Map(center=[13.45, -15.5], zoom=7, basemap="HYBRID")
    m.addLayer(image, vis, metric)
    boundary = ee.FeatureCollection([ee.Feature(aoi)])
    m.addLayer(boundary.style(color="00FFFF", fillColor="00000000", width=2), {}, "Selected area boundary")
    m.add_colorbar(vis_params=vis, label=units, orientation="horizontal", layer_name=metric)
    m.to_streamlit(height=620)
with right:
    st.subheader("Summary statistics")
    st.write(f"**Variable:** {metric}")
    st.write(f"**Period:** {start_date} to {end_date}")
    st.write(f"**Units / interpretation:** {units}")
    st.metric("Minimum", f"{min_value:,.5g}" if min_value is not None else "N/A")
    st.metric("Maximum", f"{max_value:,.5g}" if max_value is not None else "N/A")
    st.markdown("#### Legend")
    st.markdown("🟦 Low / lower relative values  →  🟨 Intermediate  →  🟥 High / higher relative values")
    st.markdown("#### Data and limitations")
    st.write("Cloud cover, retrieval quality, sensor resolution, seasonality and data gaps can influence the results. Satellite products measure different physical quantities and should not be treated as interchangeable.")
    if metric == "Groundwater nitrate susceptibility (screening)":
        st.warning("This is an illustrative, weighted environmental screening score. The weights are not calibrated to field nitrate observations. Do not report it as groundwater nitrate concentration or validated risk without local groundwater data and validation.")

st.subheader("Export")
try:
    export_url = image.getDownloadURL({"scale": 10000, "region": aoi, "format": "GEO_TIFF", "maxPixels": 1e8})
    st.link_button("Download current raster (GeoTIFF)", export_url)
except Exception as exc:
    st.caption(f"Raster download link could not be prepared for this selection: {exc}")

st.caption("Produced by Ansu Singhateh | GIS Analyst, GIS / Cartography Unit, GBoS | GBoS GEOAI • Research and educational use")
