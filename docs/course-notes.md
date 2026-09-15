# Cloud Native Remote Sensing — working notes for `asturias-grid-risk-ai`

Everything from the Spatial Thoughts course *Cloud Native Remote Sensing with Python*
that carries over into the project, with the real numbers obtained on Asturias data
rather than the course defaults.

**This file is a working reference, not a project record.** Causes belong in
`METHODOLOGY.md`, actions in the master plan, assumptions in `ASSUMPTIONS.md`. Section 8
maps every finding here to its destination. Entries stay here as well because the code
patterns and the numbers are needed while working, not only while documenting.

Course covered so far: Module 1 (notebooks 00–04, Assignment 1) and Module 2.1
(notebooks 01–03). Roughly half the course.

---

## 1. Settled parameters

Paste as a configuration block. Every value below was chosen on evidence recorded in
section 5, not taken from the course defaults.

```python
# --- Study area -------------------------------------------------------------
SITES = {
    'pajares':  {'concejo': 'Lena',     'lat': 43.0000, 'lon': -5.7600},
    'cabrales': {'concejo': 'Cabrales', 'lat': 43.2800, 'lon': -4.8300},
}
# Sites are processed separately, never merged: different geology, different
# vegetation, different UTM zone of origin. Separation also allows model
# transferability between them to be measured.

# --- Coordinate reference systems -------------------------------------------
CRS_MEASURE  = 'EPSG:25830'   # ETRS89 / UTM 30N. All area, length, distance.
CRS_DELIVERY = 'EPSG:4326'    # GeoJSON, STAC queries, web display only.
# Never crs='utm'. Asturias straddles the 29N/30N boundary at 6 W; Pajares sits
# in tile 29TQH (native 32629) while Cabrales falls in zone 30.

# --- Sentinel-2 -------------------------------------------------------------
S2_COLLECTION = 'sentinel-2-c1-l2a'
S2_CATALOG    = 'https://earth-search.aws.element84.com/v1'
S2_SCALE      = 0.0001
S2_OFFSET     = -0.1          # valid for processing baseline 04.00+ only
S2_RESOLUTION = 10
S2_MAX_CLOUD  = 30

# SCL classes removed. Course uses [3, 8, 9, 10]; 2 and 11 added for mountains.
#  2  dark area      -- terrain shadow, 17.1 % of a December scene over Pajares
#  3  cloud shadow
#  8  cloud medium probability
#  9  cloud high probability
# 10  thin cirrus
# 11  snow / ice     -- not vegetation; Sen2Cor confuses it with cloud in relief
S2_MASK_CLASSES = [2, 3, 8, 9, 10, 11]

# --- Landsat ----------------------------------------------------------------
LS_COLLECTION = 'landsat-c2-l2'
LS_CATALOG    = 'https://planetarycomputer.microsoft.com/api/stac/v1'
LS_SCALE      = 2.75e-05      # NOT the Sentinel-2 values
LS_OFFSET     = -0.2
LS_RESOLUTION = 30
LS_PLATFORM   = 'landsat-8'   # single platform for cross-year comparability
LS_TIER       = 'T1'          # geometric RMSE < 12 m, required for time series
LS_MAX_CLOUD  = 30

# --- Time-series processing -------------------------------------------------
RESAMPLE_FREQ      = '5d'     # Sentinel-2 revisit with two satellites
SMOOTH_WINDOW      = 3        # 3 x 5 days = 15 days
MAX_STEP           = 0.25     # NDVI change impossible for a closed canopy
MIN_SUN_ELEVATION  = 25       # degrees; below this, ratio indices are noise

# --- Visualisation ----------------------------------------------------------
STRETCH_VMIN = 0.0
STRETCH_VMAX = 0.10           # Asturias, Landsat RGB; 98th pct of both years
# Fixed, never recomputed per dataset. See METHODOLOGY section 14.

# --- Quality thresholds -----------------------------------------------------
MIN_SCENES_PER_TILE_PER_YEAR = 4   # below this a median is not meaningful
```

---

## 2. The processing order

The course order is standard and correct as far as it goes. Steps 3 and 7 are additions
required by mountainous terrain at 43 N; step 6 replaces the course version.

```
1. Search STAC, inventory metadata, decide parameters on the counts
2. Load, mask NoData, convert to reflectance
3. Quality mask — clouds AND terrain shadow AND snow          [addition]
4. Compute the index
5. Extract the point or the area
6. Reject implausible values                                  [addition]
7. Resample to a regular grid
8. Interpolate INSIDE the series only — never bfill/ffill      [changed]
9. Smooth
10. Leave gaps where no data exists                            [changed]
```

**Rule behind steps 6 and 9.** A smoother does not remove an error; it spreads the error
across the neighbours and makes it invisible. A wrong value that looked obviously wrong
becomes a plausible curve. Quality control always precedes smoothing.

**Rule behind step 8.** Interpolation estimates between known points and its error is
bounded by the neighbours. `bfill` and `ffill` copy a value into a period where nothing
was observed — extrapolation disguised as data. In the Pajares 2023 series the first
valid value was an artefact of division by near-zero; `bfill` would have replicated it
across the whole of January.

**Rule behind step 1.** Metadata queries cost seconds and read no pixels. Decisions about
window, threshold and platform are made on the counts, before anything is loaded. This
changed the temporal window decision for the Landsat assignment: a summer window was
rejected because it left 1 scene on one tile, and a full year was adopted only after
verifying the two years were seasonally balanced.

---

## 3. Reusable code

### 3.1 Scene inventory before loading

```python
def scene_inventory(catalog, collection, year, bbox, query, extra_fields=None):
    """Return a DataFrame of scene metadata. Reads no pixels.

    Run this before deciding the compositing window, the cloud threshold or the
    platform. The decision belongs on the counts, not on a default.
    """
    items = catalog.search(
        collections=[collection],
        bbox=bbox,
        datetime=f'{year}-01-01/{year}-12-31',
        query=query,
    ).item_collection()

    rows = []
    for item in items:
        row = {
            'date': pd.to_datetime(item.properties['datetime']).tz_localize(None),
            'cloud': item.properties.get('eo:cloud_cover'),
            'sun_elevation': item.properties.get('view:sun_elevation'),
            'platform': item.properties.get('platform'),
            'proj_code': item.properties.get('proj:code'),
        }
        for field in (extra_fields or []):
            row[field.split(':')[-1]] = item.properties.get(field)
        rows.append(row)

    df = pd.DataFrame(rows)
    df['month'] = df['date'].dt.month
    df['year'] = year
    return df
```

Landsat: `extra_fields=['landsat:wrs_path', 'landsat:wrs_row',
'landsat:collection_category']`.
Sentinel-2: `extra_fields=['grid:code', 's2:product_uri']`.

### 3.2 Reading units from the data, never from memory

```python
def band_encoding(item, bands):
    """Read scale, offset and nodata from STAC item assets.

    No raster source is assumed to carry physical units. Sentinel-2 uses
    0.0001 / -0.1; Landsat Collection 2 uses 0.0000275 / -0.2. Carrying one
    mission's constants to another produces values near -0.09 across the whole
    image, which renders as a plausible picture under automatic stretching and
    is therefore invisible to the eye.
    """
    return {b: item.assets[b].extra_fields.get('raster:bands') for b in bands}
```

Fallback check that works on any source:

```python
print(f'{name}: min={float(arr.min()):.4f} max={float(arr.max()):.4f}')
# Reflectance: roughly 0 to 1. Integers in the thousands: not converted.
# Uniformly near -0.1 or -0.2: converted twice, or the wrong constants.
```

### 3.3 Never overwrite with a non-idempotent operation

```python
# Wrong: re-running the cell applies the offset again, silently.
ds = ds * scale + offset

# Right: a new name at every step. `ds` is never modified.
masked = ds.where(ds != 0)
reflectance = masked * scale + offset
```

The test is not "am I overwriting" but "would applying this twice give the same result".
`load()` and `where()` are idempotent; multiplication with an offset is not.

### 3.4 Composite builder

```python
def build_composite(year, geometry, aoi_gdf, output_folder, **kw):
    """Build a median composite for one year and write physical values to disk.

    Inside a function every variable is local and created fresh on each call,
    so scale and offset cannot be applied twice however the cell is run.
    Visualisation is left to the caller so that several years can share one
    stretch.
    """
    items = catalog.search(...).item_collection()
    if len(items) == 0:
        raise ValueError(f'No scenes for {year}. Widen the window or the '
                         f'threshold -- but change it for ALL years.')
    print(f'{year}: {len(items)} scenes')

    ds = load(items, bbox=geometry.bounds, crs=CRS_MEASURE, ...)
    print(f'{year}: {ds.sizes["time"]} solar days')

    masked = ds.where(ds != 0)
    reflectance = masked * scale + offset
    composite = reflectance.median(dim='time').compute()

    composite_da = composite.to_array('band')
    aoi_in_crs = aoi_gdf.to_crs(composite_da.rio.crs)
    clipped = composite_da.rio.clip(aoi_in_crs.geometry)

    clipped.rio.to_raster(
        os.path.join(output_folder, f'composite_{year}.tif'), driver='COG')
    return clipped
```

Always print the number of unique solar days, not only the number of scenes. A granule
count overstates the observation count wherever the area of interest straddles tiles:
Landsat over Asturias returned 32 scenes for 24 solar days, Sentinel-2 over Oviedo
returned 20 scenes for 14 days.

### 3.5 Cloud mask with morphology

```python
cloud_mask = ds['scl'].isin(S2_MASK_CLASSES)

# Radius is in PIXELS. Think in metres, convert, and verify the conversion:
# int(60 / 100) evaluates to 0 and silently disables the dilation.
radius_px = max(1, round(BUFFER_M / resolution))
print(f'Buffer {BUFFER_M} m at {resolution} m/px -> {radius_px} px '
      f'(actual {radius_px * resolution} m)')

# Closing before dilation. Err on the side of masking too much: a missed cloud
# pixel enters the composite at reflectance ~0.7 instead of ~0.04, while an
# over-masked pixel costs one observation out of many.
cleaned = mask_cleanup(cloud_mask, [('closing', 2), ('dilation', radius_px)])

clean = ds[spectral].where(~cleaned)   # the mask flags BAD pixels: note the ~
```

Measured on a December scene over Pajares at 100 m: original mask 622 786 px,
opening −5.1 %, closing +9.0 %, closing + 1 px dilation +11.1 %. The choice of operation
changes the volume of discarded data by more than a tenth.

### 3.6 Index with guards, in the right order

```python
ndvi = (nir - red) / (nir + red)
ndvi = ndvi.where(np.isfinite(ndvi))   # inf -> NaN, honest no-data
ndvi = ndvi.clip(-1, 1)                # enforce the physical range
```

**The order is not arbitrary.** `clip` treats infinity as greater than 1 and returns 1.0 —
a flawless-looking value meaning perfect vegetation, produced by a division by zero.
Reversing these two lines puts false maxima wherever water or deep shadow sits.

`clip` makes data processable; it does not make data correct. In the course version of
the Pajares series it converted a raw NDVI of about 3.7 into exactly 1.00, which then
propagated through the smoother as a plausible winter decline.

### 3.7 Outlier rejection

```python
def reject_outliers(series, max_step=MAX_STEP):
    """Remove points that depart from both neighbours in the same direction.

    A closed deciduous canopy cannot gain or lose a quarter of its NDVI in
    days. Such a point is residual cloud, shadow or haze the SCL mask missed.
    A real change moves in one direction, so it sits above one neighbour and
    below the other; a spike departs from both and returns.
    """
    values = series.values.copy()
    flagged = 0
    for i in range(1, len(values) - 1):
        prev_v, this_v, next_v = values[i - 1], values[i], values[i + 1]
        if np.isnan([prev_v, this_v, next_v]).any():
            continue
        if (abs(this_v - prev_v) > max_step
                and abs(this_v - next_v) > max_step
                and np.sign(this_v - prev_v) == np.sign(this_v - next_v)):
            values[i] = np.nan
            flagged += 1
    print(f'Rejected {flagged} spike(s)')
    return series.copy(data=values)
```

### 3.8 Sun elevation filter

```python
sun = {pd.to_datetime(i.properties['datetime']).tz_localize(None).normalize():
       i.properties.get('view:sun_elevation') for i in items}

dates = pd.to_datetime(series.time.values).normalize()

missing = [d for d in dates if d not in sun]
if missing:
    print(f'WARNING: no sun elevation for {len(missing)} date(s)')

low_sun = np.array([sun.get(d) is not None and sun[d] < MIN_SUN_ELEVATION
                    for d in dates])
filtered = series.where(~xr.DataArray(low_sun, dims='time'))
```

Note the explicit `missing` check. Using `.get()` alone means an unmatched date silently
passes the filter as "sun high enough".

### 3.9 NaN in comparisons

```python
# NaN > threshold evaluates to False, so no-data pixels are classified as the
# negative class. Restore them explicitly.
water = xr.where(mndwi > threshold, 1, 0).where(mndwi.notnull())
```

Without the second `where`, the empty corners of a scene are counted as land and the
denominator of any percentage is inflated.

### 3.10 Quality-control figure

```python
# One figure showing the fate of every observation. Without it, an empty
# period cannot be distinguished from a period with no valid data.
ax.plot(raw.time, raw.values, marker='o', markersize=9, linestyle='none',
        markerfacecolor='none', markeredgecolor='#999999', label='after mask')
ax.plot(kept.time, kept.values, marker='o', markersize=6, linestyle='none',
        color='#238b45', label='kept')
ax.plot(spikes.time, spikes.values, marker='x', markersize=11, linestyle='none',
        color='#d7301f', markeredgewidth=2, label='rejected as spike')
ax.plot(lowsun.time, lowsun.values, marker='s', markersize=8, linestyle='none',
        color='#fe9929', label='rejected: low sun')
```

Layers must not fully overlap. Drawing the raw series as small filled markers under the
kept series as larger filled markers makes the raw series invisible — the two differ by
only a few points.

---

## 4. Physics worth keeping

**The red edge.** Chlorophyll absorbs red (665 nm) so a leaf reflects 3–5 % there, while
the spongy mesophyll scatters near-infrared (833 nm) up to 45–55 %. The jump is the
sharpest contrast in the spectral signature of living matter and every vegetation index
rests on it. The jump collapses when leaf structure breaks down — **a stressed tree is
visible in the infrared before it turns brown in the visible.** Directly useful for
detecting dying trees near a conductor.

**Why a ratio and not a band.** Illumination, haze and slope act multiplicatively on the
whole spectrum. In `(A − B)/(A + B)` a common factor cancels. Absolute brightness depends
on the conditions of observation; the ratio depends on the surface. This is exactly why
two RGB composites of different years cannot be compared but their NDVI can.

**NDVI saturation.** Above roughly 0.85 the index stops discriminating. In the Pajares
2023 series the summer plateau sat at 0.85–0.90 and the histogram of the August scene
peaked sharply at 0.90. **NDVI states that forest is present; it does not state how tall
or how dense.** Height comes only from LiDAR.

**Median compositing.** Robust while cloudy observations are a minority for that pixel;
returns cloud, silently, when they are not. Observation counts per pixel are therefore a
quality figure, not a detail.

**Sun-synchronous orbit.** Every acquisition of a given point happens at the same local
solar time — Sentinel-2 at about 11:29 over Pajares, 10:38 over the course default further
east. Solar elevation then varies only with season: 21° in late December, 64° in June at
43 N. Level-2A corrects the atmosphere, **not the geometry of illumination**. On steep
relief this leaves a systematic residual, which is what topographic correction addresses.

**Acquisition geometry.** All 20 Landsat scenes over Asturias came from path R037 and all
Sentinel-2 scenes over Pajares from tile 29TQH, so viewing geometry was constant across
the series. Worth verifying rather than assuming: mixed paths would mean mixed view angles
and mixed shadow lengths.

---

## 5. Pitfalls, with the numbers that exposed them

| # | Symptom | Cause | Detection |
|---|---|---|---|
| 1 | All values ≈ −0.0999 | scale/offset applied twice | value range check before any plot |
| 2 | Values in the thousands | scale/offset not applied | same |
| 3 | Uniform −0.09 on Landsat | Sentinel-2 constants used | read `raster:bands` |
| 4 | NDVI exactly 1.00 | division by near-zero, clipped | physically impossible; check sun elevation |
| 5 | Composite over the wrong city | dropped minus on longitude | `spatial_ref` returned 32631 not 32630 |
| 6 | One feature where 78 expected | adm2 is provincia, not municipio | print names and area, not only count |
| 7 | Both comparison plots identical | cell executed out of order | separate variable names per result |
| 8 | Dilation had no effect | `int(60 / 100)` = 0 | print the actual buffer in metres |
| 9 | Plausible picture, corrupt data | `robust=True` fits scale to content | verify numerically before plotting |
| 10 | Real change invisible between years | percentile stretch computed per year | fix `vmin`/`vmax` once |
| 11 | Scene rotated on screen | tile reprojected across UTM zones | `grid:code` 29TQH, output 32630 |
| 12 | Snow reported as 289 px | Sen2Cor classifies mountain snow as cloud | mask outline follows contours, not cloud shapes |

### Measured values, Asturias

**Boundaries.** 78 concejos, 10 601 km² in EPSG:25830 against a reference of about
10 600 km². Spain: adm1 = comunidad autónoma, adm2 = provincia, adm3 = municipio
(*concejo* in Asturias). Asturias is uniprovincial, so adm1 and adm2 cover the same
territory and an adm2 query returns exactly one feature.

**Landsat 8, Asturias, Tier 1 only.** 2020: 32 scenes, 24 solar days. 2025: 26 scenes,
20 days. Five WRS-2 tiles with 4–8 scenes each per year, a factor of two between best and
worst. Output grid identical both years: 3150 × 7328 px, 58.2 % of cells holding data
after clipping. Distributions matched to within 0.002 at every percentile.

**Tier 1 filtering cost.** Mean sun elevation moved from 46.2 / 46.0 (both tiers) to
48.6 / 46.9 (T1 only). Tier 2 rejections concentrate in winter and in relief, so excluding
them removes winter observations preferentially and unequally between years.

**SCL class distribution, Pajares, 30 December 2023, at 100 m.**

```
 2  dark area            17.1 %     terrain shadow, sun at 21 deg
 3  cloud shadow          3.5 %
 4  vegetation           22.1 %
 5  not vegetated         8.1 %
 6  water                 0.1 %
 7  unclassified          0.8 %
 8  cloud medium          7.3 %
 9  cloud high           39.9 %
10  thin cirrus           0.9 %
11  snow / ice            0.02 %    implausibly low for a snow-covered pass
```

Course mask `[3, 8, 9, 10]` removes 51.6 %. Project mask `[2, 3, 8, 9, 10, 11]` removes
more and is correct for this terrain.

**Sentinel-2 NDVI series, Pajares, 2023.** 48 acquisitions → 31 after the extended mask →
30 after spike rejection → 28 after the sun filter. Resampled to 72 five-day cells, 47
filled, 25 left as honest gaps. Usable range February to October; November to January hold
no reliable observations.

**MNDWI, Pajares tile, August 2023, at 20 m.** 78 704 water pixels of 30 133 170 valid,
0.261 %, 31.5 km². Consistent with the reservoirs present (Barrios de Luna and others).
Land and water populations separated by a clean gap, so the threshold of 0 sits in empty
space and is stable.

---

## 6. Data produced so far

```
asturias-grid-risk-ai/data/
├── boundaries/
│   ├── asturias_concejos.gpkg        78 concejos, geoBoundaries ADM3, EPSG:4326
│   ├── study_sites_concejos.gpkg     Cabrales and Lena only
│   └── README.md                     source passport  [NOT YET WRITTEN]
└── landsat/
    ├── landsat_composite_2020.tif    surface reflectance, COG
    ├── landsat_composite_2025.tif
    ├── landsat_visual_2020.tif       RGBA, stretch 0.0-0.10 baked in
    ├── landsat_visual_2025.tif
    └── README.md                     source passport
```

**Two files per raster product, always.** Physical values as float COG, display version
as 8-bit RGBA with the stretch applied. The display version can be regenerated from the
physical one at any time; the reverse is impossible, because the stretch clips both tails
irreversibly.

**Outstanding.** The boundaries source passport was not written. Ten lines, `scripts/
source_passport.py`, run once.

---

## 7. Remaining course modules

Not yet covered. Expected to bear on the project:

- **Zonal statistics** — aggregating raster values inside polygons. Directly applicable to
  per-concejo and per-corridor summaries.
- **Exporting and publication formats** — COG and PMTiles, already the chosen formats for
  Phase 9.
- **Larger-scale Dask processing** — the composites so far were single points or single
  regions; corridor-wide processing needs chunking along space with time held whole.

Carry forward into every remaining notebook: the parameters in section 1, the order in
section 2, and the value-range check before any figure.

---

## 8. Where each finding belongs

**To `METHODOLOGY.md`** — the reasoning, one section each:

- Single boundary source, and why sources must not be mixed (§13)
- Fixed visualisation stretch (§14)
- Measurement CRS separate from delivery CRS (§15)
- Composite as background rather than snapshot (§16)
- *New:* quality control precedes smoothing, because a smoother spreads an error rather
  than removing it
- *New:* interpolation inside a series is permitted, extrapolation beyond its ends is not

**To `ASSUMPTIONS.md`** — entries A-01 to A-17 already filed. To add:

- SCL classes 2 and 11 included in the mask, with the 17.1 % cost recorded
- Cloud-mask morphology parameters expressed in metres and converted per resolution
- Minimum sun elevation of 25° for ratio indices, and the winter data it removes
- Spike rejection threshold of 0.25 NDVI between consecutive observations
- Pajares lies wholly in MGRS tile 29TQH and is reprojected; Cabrales falls in zone 30

**To the master plan** — actions:

- Phase 0: write the boundaries source passport
- Phase 1: read band encoding from STAC metadata for every source before use
- Phase 1: record scenes, solar days and value range for every composite
- Phase 2: per-pixel validity count raster as a companion to every composite
- Phase 2: topographic correction for the mountain sites, or class 2 masked and the loss
  quantified

**Nowhere** — engineering habits, caught in code when they appear rather than studied as a
list: new variable name per transformation step, verify numerically before plotting,
inspect the full query result before applying `LIMIT`, stop on a source error instead of
writing a corrupt file.