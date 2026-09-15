"""Project constants.

Constants only: no functions, no executable statements at module level.
Every value that might need changing lives here and nowhere else, so that
changing a site or a year is one edit in one place.

Values were chosen on evidence recorded in docs/ASSUMPTIONS.md; the reasoning
behind the choices is in docs/METHODOLOGY.md.
"""

# --- Study site -------------------------------------------------------------
SITE_NAME = 'Puerto de Pajares'
SITE_CONCEJO = 'Lena'          # Pajares is a village inside this concejo
LATITUDE = 43.0000
LONGITUDE = -5.7600
ELEVATION_M = 1370             # approximate, for reference in text only

REGION_ADM1 = 'Principado de Asturias'

# --- Coordinate reference systems -------------------------------------------
# Stated explicitly, never left to automatic selection: Pajares lies 27 km from
# the UTM 29N/30N boundary. See METHODOLOGY section 2.
CRS_MEASURE = 'EPSG:25830'     # ETRS89 / UTM 30N. All area, length, distance.
CRS_DELIVERY = 'EPSG:4326'     # GeoJSON, STAC queries, web display only.

# --- Sentinel-2 -------------------------------------------------------------
S2_CATALOG = 'https://earth-search.aws.element84.com/v1'
S2_COLLECTION = 'sentinel-2-c1-l2a'
S2_SCALE = 0.0001
S2_OFFSET = -0.1               # valid for processing baseline 04.00+ only
S2_RESOLUTION = 10
S2_MAX_CLOUD = 30

# Scene classification classes removed from the data.
# Tutorial material uses [3, 8, 9, 10]; 2 and 11 are added for mountain terrain.
#  2  dark area      -- terrain shadow, 17.1 % of a December scene at Pajares
#  3  cloud shadow
#  8  cloud medium probability
#  9  cloud high probability
# 10  thin cirrus
# 11  snow / ice     -- not vegetation, and confused with cloud in relief
S2_MASK_CLASSES = [2, 3, 8, 9, 10, 11]

# --- Landsat ----------------------------------------------------------------
LS_CATALOG = 'https://planetarycomputer.microsoft.com/api/stac/v1'
LS_COLLECTION = 'landsat-c2-l2'
LS_SCALE = 2.75e-05            # NOT the Sentinel-2 values
LS_OFFSET = -0.2
LS_RESOLUTION = 30
LS_PLATFORM = 'landsat-8'      # single platform for cross-year comparability
LS_TIER = 'T1'                 # geometric RMSE < 12 m, required for time series
LS_MAX_CLOUD = 30

# --- Climate ----------------------------------------------------------------
TERRACLIMATE_URL = 'http://thredds.northwestknowledge.net:8080/thredds/dodsC/'
CLIMATE_START_YEAR = 1970
CLIMATE_END_YEAR = 2025

# --- Time-series processing -------------------------------------------------
RESAMPLE_FREQ = '5d'           # Sentinel-2 revisit with two satellites
SMOOTH_WINDOW = 3              # 3 x 5 days = 15 days
MAX_NDVI_STEP = 0.25           # change impossible for a closed canopy in days
MIN_SUN_ELEVATION = 25         # degrees; below this a ratio index is noise

# --- Visualisation ----------------------------------------------------------
# Fixed, never recomputed per dataset. See METHODOLOGY section 3.
STRETCH_VMIN = 0.0
STRETCH_VMAX = 0.10            # rounded up from the 98th percentile of both years

# --- Quality thresholds -----------------------------------------------------
MIN_SCENES_PER_TILE_PER_YEAR = 4