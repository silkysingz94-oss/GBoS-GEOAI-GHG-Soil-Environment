# 🇬🇲 GBoS GEOAI — Greenhouse Gases & Soil Environment

A VS Code-ready Streamlit dashboard using the Google Earth Engine Python API for selected-area environmental screening in The Gambia.

## Current functions

- National, region and district study-area selection using GAUL boundaries.
- On-demand date range and variable selection.
- Sentinel-5P methane and tropospheric NO₂ composites.
- Sentinel-2 NDVI, CHIRPS rainfall and SMAP surface soil moisture layers.
- An explicitly illustrative nitrate-susceptibility screening score.
- Summary statistics, a persistent map legend, selected-area boundary, and GeoTIFF download link.
- GBoS GEOAI branding and scientific interpretation warnings.

> **Scientific caution:** The nitrate susceptibility layer is an illustrative weighted screening proxy and is not calibrated or validated against groundwater nitrate observations. Do not interpret it as nitrate concentration or a validated risk map. Satellite atmospheric column products are not direct ground-level exposure measurements.

## Requirements

- Windows 10/11, VS Code and Python 3.10–3.12 recommended.
- A Google account with access to Google Earth Engine.
- Internet access for Python packages and Earth Engine datasets.

## 1. Open in VS Code

1. Extract the ZIP file.
2. In VS Code, select **File → Open Folder** and choose `GBoS-GEOAI-GHG-Soil-Environment`.
3. Open **Terminal → New Terminal**.
4. Create a virtual environment:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If PowerShell blocks activation, use Command Prompt in VS Code and run:

```bat
.venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 2. Authenticate Earth Engine

In the VS Code terminal, run:

```powershell
eecli authenticate
```

If `eecli` is not available in your installed Earth Engine package, use Python:

```powershell
python -c "import ee; ee.Authenticate(); ee.Initialize()"
```

Complete the browser authentication and select/confirm your Earth Engine Cloud Project if prompted. If initialization requires a project, edit `app.py` and change `ee.Initialize()` to `ee.Initialize(project="YOUR_EARTH_ENGINE_CLOUD_PROJECT_ID")` using your actual project ID. Do not put private credentials or service-account JSON files in this repository.

## 3. Run the dashboard

```powershell
streamlit run app.py
```

Streamlit will print a local URL, usually `http://localhost:8501`. Open it in your browser. Select a study area, dates and variable, then click **Run analysis**.

## 4. Publish to GitHub

Create a **public or private repository** named `GBoS-GEOAI-GHG-Soil-Environment` on GitHub. Do not initialize it with a README if you plan to push this folder as-is. In the VS Code terminal, from this project folder:

```powershell
git init
git add .
git commit -m "Initial GBoS GEOAI environmental screening dashboard"
git branch -M main
git remote add origin https://github.com/YOUR_GITHUB_USERNAME/GBoS-GEOAI-GHG-Soil-Environment.git
git push -u origin main
```

Replace `YOUR_GITHUB_USERNAME` with your GitHub username. Git may ask you to authenticate in a browser.

## Hosting notes

This project is a Python/Streamlit application; **GitHub Pages cannot run the Python backend**. GitHub stores the source code. To make the live dashboard public, deploy it to a Streamlit-compatible host (for example, Streamlit Community Cloud) and connect the GitHub repository. Earth Engine authentication on a hosted server requires a secure server-side configuration; do not upload your personal Earth Engine credentials. Test locally first.

## Data sources

- Sentinel-5P OFFL CH₄: `COPERNICUS/S5P/OFFL/L3_CH4`
- Sentinel-5P OFFL NO₂: `COPERNICUS/S5P/OFFL/L3_NO2`
- Sentinel-2 SR Harmonized: `COPERNICUS/S2_SR_HARMONIZED`
- CHIRPS Daily: `UCSB-CHG/CHIRPS/DAILY`
- SMAP L4: `NASA/SMAP/SPL4SMGP/007`
- ESA WorldCover v200: `ESA/WorldCover/v200`
- GAUL 2015 administrative boundaries: `FAO/GAUL/2015/level0`, `level1`, `level2`

Dataset availability, band names, permissions and product versions can change. Confirm the current Earth Engine catalog documentation if a layer fails.

## Project structure

```text
GBoS-GEOAI-GHG-Soil-Environment/
├── app.py
├── README.md
├── requirements.txt
├── .gitignore
└── .vscode/
    ├── extensions.json
    └── launch.json
```

## Attribution

Produced by Ansu Singhateh | GIS Analyst, GIS / Cartography Unit, Gambia Bureau of Statistics (GBoS). GBoS GEOAI • Research and educational use.
