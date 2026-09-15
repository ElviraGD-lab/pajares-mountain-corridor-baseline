# ASSUMPTIONS

Every assumption in this project is recorded here: what was assumed, why, which way it
biases the result, and how it was checked. An assumption that is not written down is
indistinguishable from an error.

**Scope.** This file holds working assumptions about data and method. Reasoning behind
architectural choices belongs in `METHODOLOGY.md`; actions belong in the master plan at
the phase where they are executed.

**Maintenance.** An entry is added at the moment the assumption is made, not afterwards.
When an assumption is replaced, the entry is marked superseded and kept — the history of
what was believed is part of the method.

**Status legend.** `verified` — checked against data. `accepted` — taken on documented
external authority. `open` — not yet checked, flagged as a risk.

---

## A-01. Pajares is represented by the concejo of Lena

**Status:** verified

**Assumed.** The study site "Pajares" is analysed within the administrative boundary of
the concejo of Lena.

**Why.** Pajares is a village (*parroquia*) inside Lena, not a municipality. It does not
exist at adm3 level in any global boundary dataset. Parish-level boundaries for Asturias
would have to be sourced separately from regional Spanish portals.

**Bias.** The analysed area is substantially larger than the village and its immediate
corridor. Any per-area statistic — risk density, vegetation fraction, incident rate — is
diluted relative to the site as understood colloquially.

**Check.** Queried adm3 for `Principado de Asturias`: 78 features returned, `Lena`
present, `Pajares` absent. If a tighter boundary becomes necessary, the parish polygon can
replace it — the pipeline takes the boundary as an input and does not depend on its extent.

---

## A-02. Administrative boundaries come from geoBoundaries only

**Status:** verified

**Assumed.** All administrative polygons come from geoBoundaries via FieldMaps
edge-matched ADM3. No other boundary source is mixed in.

**Why.** Queryable in place over HTTP without download, internally edge-matched so
adjacent polygons share exact borders, ODbL licensed. See `METHODOLOGY.md` §13.

**Bias.** Boundaries differ from the legally authoritative IGN and catastro polygons by
tens of metres in places. Areas and per-unit aggregates carry that error. For a corridor
buffer of 30 m the discrepancy is of the same order as the buffer itself, so results near
a municipal boundary must not be attributed to one side with confidence.

**Check.** Total area of the 78 concejos, computed in EPSG:25830, came to 10 601 km²
against a published figure of approximately 10 600 km² for Asturias. Consistent at the
level of the whole region; not verified per concejo.

---

## A-03. Sentinel-2 reflectance offset assumes processing baseline 04.00 or later

**Status:** verified

**Assumed.** Sentinel-2 L2A integers are converted as `DN * 0.0001 - 0.1`.

**Why.** ESA introduced a −1000 DN offset with processing baseline 04.00 (January 2022).
Scenes processed under earlier baselines carry no offset and require `offset = 0`.

**Bias.** Applying the offset to a pre-04.00 scene shifts all reflectance down by 0.1 — an
error larger than the reflectance of most vegetation, silently corrupting every derived
index. Acquisition date is not a reliable guide: archived scenes are reprocessed under
newer baselines. One Asturias scene acquired in September 2023 was processed in August
2025 and carries baseline 05.11.

**Check.** Baseline read from `s2:product_uri` (the `N05xx` field) for every scene entering
a composite. Value range of the result asserted to fall within approximately 0 to 1 before
the composite is written.

---

## A-04. Landsat reflectance uses mission-specific scale and offset

**Status:** verified

**Assumed.** Landsat Collection 2 Level-2 integers are converted as
`DN * 0.0000275 - 0.2`.

**Why.** Read from `raster:bands` in the STAC item assets, not carried over from another
mission. Sentinel-2 uses `0.0001` and `-0.1` — entirely different numbers for the same
physical quantity.

**Bias.** Applying Sentinel-2 constants to Landsat data produces values near −0.09 across
the entire image. This is physically meaningless but renders as a plausible picture under
automatic contrast stretching, so it is not detectable by eye.

**Check.** The Collection 2 valid DN range of 7273–43636 maps to 0.0000 and 0.9999 under
these constants, confirming they are the intended ones. Composite range verified after
computation: min −0.06 to −0.10, max 0.70 to 0.77, mean 0.032 — consistent with a heavily
vegetated region.

**Generalisation.** No raster source is assumed to carry physical units. For every new
source, the encoding is read from metadata and the resulting range is checked against
physical plausibility before the data is used.

---

## A-05. Slightly out-of-range reflectance values are accepted as normal

**Status:** verified

**Assumed.** Individual pixels with surface reflectance slightly below 0 or above 1 are
retained rather than clipped or masked.

**Why.** Atmospheric correction subtracts a modelled atmospheric contribution, which can
overshoot over very dark surfaces — deep water, terrain shadow. Specular returns from
water and snow can exceed 1. These are correction artefacts on real measurements, not
errors.

**Bias.** Negligible for aggregate statistics; relevant if a threshold is applied near 0.

**Check.** The diagnostic is the distinction between isolated outliers and a uniform
displacement. Asturias composites show minima of −0.06 and −0.10 at the 0th percentile
while the 1st percentile sits at 0.011 — isolated, as expected. A whole image displaced
into a narrow band outside the range indicates a processing error instead.

---

## A-06. Scene-level cloud cover is a cost filter, not a quality guarantee

**Status:** accepted

**Assumed.** Scenes are filtered by `eo:cloud_cover` below a fixed threshold, applied
identically to every year and site.

**Why.** The metadata filter is free and removes unusable acquisitions before any pixel is
read.

**Bias.** `eo:cloud_cover` describes a full granule — 110 × 110 km for Sentinel-2,
185 × 180 km for Landsat — while the areas of interest are a small fraction of it. A scene
at 25 % cloud may be entirely clear over the corridor or entirely obscured; the filter
neither guarantees nor excludes either. Per-pixel masking from the SCL band (Sentinel-2) or
`qa_pixel` band (Landsat) is the actual quality control and is not yet implemented.

**Check.** Threshold held constant across all years and sites so composites remain
comparable. Number of scenes and number of unique solar days recorded per composite.

---

## A-07. Median compositing assumes cloud affects a minority of observations per pixel

**Status:** open

**Assumed.** A per-pixel median over the compositing window returns a cloud-free surface
value.

**Why.** The median is unaffected by outliers as long as they are fewer than half the
sample. Cloud and shadow are outliers with respect to surface reflectance.

**Bias.** Where more than half the observations for a pixel are cloudy, the median returns
cloud, and does so without any error or warning. Asturias is among the cloudiest regions of
Spain and the mountain sites are the worst case. Contamination raises apparent reflectance,
which biases vegetation indices downward.

**Check.** Partially checked only. Observation counts are recorded per composite, but a
per-pixel validity count raster (`ds.notnull().sum(dim='time')`) is not yet produced. Until
it is, composite reliability is assumed uniform across the area, which it is not — see A-08.

---

## A-08. Observation density is uneven across the study area

**Status:** verified

**Assumed.** Every pixel of a composite is treated as equally reliable.

**Why.** Simplification. Tracking per-pixel observation counts through the pipeline adds a
parallel data product.

**Bias.** The assumption is false, and measurably so. Asturias is covered by five Landsat
WRS-2 tiles (202/030, 203/029, 203/030, 204/029, 204/030) with 4 to 8 Tier 1 scenes each
per year — a factor of two between best and worst. Areas in the sidelap between adjacent
orbital paths are observed roughly twice as often as areas within a single path; at 43° N
the sidelap is about a third of the swath width. The same applies to Sentinel-2 where an
area of interest straddles MGRS tiles.

Consequence: a composite is more reliable in some parts of the region than others, and
this is invisible in the image. Visible gaps at the eastern edge of the 2020 composite mark
pixels with too few valid observations; gaps are the extreme case of a gradient that exists
everywhere.

**Check.** Scene counts tabulated per tile per year before loading. Minimum accepted
threshold: 4 scenes per tile per year. Where a configuration falls below it, the filter is
loosened rather than the shortfall accepted silently.

---

## A-09. Landsat Tier 1 only, at a cost in seasonal balance

**Status:** verified

**Assumed.** Only Landsat scenes with `landsat:collection_category == 'T1'` enter a
composite.

**Why.** Tier 1 scenes passed geometric validation with registration error below 12 m.
USGS specifies Tier 1 as the requirement for time-series analysis. At 30 m pixel size, a
Tier 2 registration error of tens of metres is on the order of a whole pixel, and change
between two dates would be partly displacement rather than change on the ground.

**Bias.** Tier 2 rejections are not randomly distributed — they concentrate where ground
control points are scarce, which means winter scenes and mountainous terrain. Excluding
them therefore removes winter observations preferentially, and unequally between years.
For Asturias 2020 vs 2025 the mean sun elevation moved from 46.2° / 46.0° (both tiers) to
48.6° / 46.9° (Tier 1 only) — the inter-year difference grew from 0.2° to 1.7°.

This is an accepted trade: geometric precision bought at the price of a small loss of
seasonal comparability.

**Check.** Both tier configurations inventoried and compared before choosing. Tier 1 alone
satisfied the 4-scenes-per-tile minimum in every tile and year (4 to 8 scenes), so no
further compromise was needed.

---

## A-10. Multi-sensor missions are restricted to a single platform

**Status:** verified

**Assumed.** Comparisons across years use one satellite platform only — Landsat 8, not
Landsat 8 and 9 together.

**Why.** The `landsat-c2-l2` collection holds all Landsat missions. Landsat 5 (TM), 7
(ETM+) and 8/9 (OLI) carry different sensors with different spectral response. Landsat 7
additionally suffers scan line corrector failure since 2003, producing striped imagery
with about a quarter of each scene missing.

Landsat 9 is excluded although OLI-2 is cross-calibrated with OLI and would add
observations: it did not exist in 2020, so including it would make the two years unequal
in sensor composition. Comparability is the purpose of the exercise.

**Bias.** Fewer observations in the later year — 26 Tier 1 scenes in 2025 against 32 in
2020, giving 20 solar days against 24. The 2025 composite is built on a smaller sample and
is correspondingly less robust to cloud.

**Check.** Platform filter applied in the STAC query, not after loading. Scene and solar-day
counts printed per year.

---

## A-11. The compositing window is validated on metadata, not assumed

**Status:** verified

**Assumed.** A full calendar year is used as the compositing window for both years, rather
than a fixed seasonal window.

**Why.** A fixed seasonal window was the initial choice, on the reasoning that an annual
median mixes leaf-on and leaf-off states and widely differing sun elevations, in
proportions set by which months happened to be clear. Metadata inventory rejected this:
at < 30 % cloud, a June–September window left as few as 1 Tier 1 scene on one tile in
2025, which makes a median meaningless.

The full year was then tested for the bias the seasonal window was meant to prevent, and
the two years proved balanced:

| Check | 2020 | 2025 |
|---|---|---|
| Tier 1 scenes | 32 | 26 |
| Scenes per tile | 4–8 | 4–6 |
| Mean sun elevation | 48.6° | 46.9° |
| Sun elevation std | 14.3 | 14.4 |
| Sun elevation range | 19.9–64.3° | 20.3–64.3° |
| Leaf-off share (Nov–Apr) | 35.0 % | 38.2 % |

**Bias.** Composites describe typical annual condition and mix leaf-on with leaf-off
observations. Nothing season-specific can be read from them. The balance verified here
holds for Asturias 2020 vs 2025 and must be re-checked for any other pair of years or any
other area — it is a property of the weather in those years, not of the method.

**Check.** Distribution of scenes by month, leaf-off share, and sun elevation min/mean/max/std
compared between years before any pixel was loaded. Cost: a few seconds of metadata queries.

---

## A-12. Coordinate reference systems are declared, never auto-selected

**Status:** verified

**Assumed.** `crs='EPSG:25830'` (ETRS89 / UTM 30N) is stated explicitly at load time
rather than using `crs='utm'`.

**Why.** Asturias straddles the boundary between UTM zones 29N and 30N at 6° W, which runs
near Gijón. Landsat scenes are projected into the zone containing their own centre, so
scenes covering the same region arrive in different zones — verified: one probe scene
returned EPSG:32630 while western-path scenes return EPSG:32629. An automatic choice would
resolve to a single zone selected from whichever data happened to be loaded.

All measurement — area, length, distance, buffer width, clearance — is performed in
EPSG:25830. EPSG:4326 is used only for delivery formats that require it. See
`METHODOLOGY.md` §15.

**Bias.** None, provided the declaration is present. Its absence produces silent error:
geometric operations in geographic coordinates return numbers without raising an
exception, and those numbers are in square or linear degrees, which are not convertible to
metric units.

**Check.** Output grid dimensions identical across years (3150 × 7328 px before clipping,
58.2 % of cells holding data after), confirming the two composites share one grid pixel for
pixel.

---

## A-13. Visualisation stretch is fixed and recorded

**Status:** verified

**Assumed.** Published rasters use explicit `vmin` and `vmax` applied unchanged to every
year. For the Asturias Landsat composites: 0.0 and 0.10.

**Why.** Percentile stretching computes display limits from the data being displayed. Two
composites of the same place in different years would each occupy the full brightness
range regardless of what changed on the ground: real change is absorbed into the scale and
becomes invisible, while differences caused by the stretch itself become visible. The
failure is silent — both images look correct. See `METHODOLOGY.md` §14.

The value 0.10 was chosen once, by rounding up the 98th percentile of both composites
(0.0948 and 0.0968), and then frozen as a constant. Data may inform the value; data must
not recompute it per dataset.

**Bias.** About 2 % of pixels — snow on the Picos de Europa, bare limestone, urban
surfaces — are clipped to white. Accepted so that the vegetated majority of the region
receives full contrast.

**Check.** Percentiles of both composites compared before fixing the value:

| | p1 | p50 | p95 | p98 |
|---|---|---|---|---|
| 2020 | 0.0109 | 0.0361 | 0.0780 | 0.0948 |
| 2025 | 0.0127 | 0.0385 | 0.0791 | 0.0968 |

---

## A-14. Physical data and display products are separate artefacts

**Status:** verified

**Assumed.** Every raster output is written twice: physical values as float COG, and a
display version as 8-bit RGBA COG with the stretch baked in.

**Why.** The display product can be regenerated from the physical product at any time. The
reverse is impossible: the stretch clips everything above the upper limit to one value and
everything below the lower limit to another, destroying information irreversibly.

**Bias.** Storage cost roughly doubles. Accepted.

**Check.** Both files present in the output folder with the stretch parameters recorded in
the accompanying source passport.

---

## A-15. RGB composites cannot separate brightness shift from surface change

**Status:** verified

**Assumed.** Visual comparison of RGB composites is used for orientation and sanity
checking only, never as evidence of change.

**Why.** Three distinct causes produce the same visual effect: a uniform radiometric shift
between years, a difference in the number of observations entering each median, and actual
change in surface cover. They are not separable in a three-band visible-light image.

Asturias 2025 is uniformly brighter than 2020 by about 0.002 across the entire
distribution, from the 1st to the 98th percentile. A uniform shift of this kind is not how
a change in surface cover would present — that would move the tails in different
directions. The most likely cause is the differing observation count (24 solar days against
20).

**Bias.** Reading change off an RGB pair would attribute this artefact to the ground.

**Check.** Quantitative change detection requires a band ratio — NDVI from the red and
near-infrared bands — computed per year and differenced. Being a ratio, it partially
cancels uniform illumination differences that affect both bands. Not yet implemented; the
`nir08` asset is available in the same Landsat items and was deliberately not loaded for
the RGB task.

---

## A-16. Overture Maps release version is pinned per download

**Status:** accepted

**Assumed.** The Overture release used for infrastructure and building extraction is
recorded at download time and treated as fixed for that run.

**Why.** Overture publishes monthly. Resolving "latest" at query time makes two runs of the
same code return different data, which breaks reproducibility of any figure derived from it.

**Bias.** None on the result itself, provided the version is recorded. Unrecorded, every
figure derived from Overture becomes unreproducible, and a reviewer cannot distinguish a
change in the data from a change in the method.

**Check.** Release identifier written to the source passport in the data folder alongside
the extracted files.

---

## A-17. Overture division subtypes are not equivalent to administrative levels

**Status:** accepted

**Assumed.** Where Overture is used for boundaries, its `subtype` values (`locality`,
`county`, `localadmin`, `region`) are treated as a separate classification from the
adm0–adm3 hierarchy, not as a mapping onto it.

**Why.** Neither system corresponds exactly to the Spanish *municipio*. Overture subtypes
are applied unevenly across countries: a settlement classified `locality` in Spain may be
`localadmin` elsewhere. Administrative levels adm0–adm3 are ordinal positions within each
country's own hierarchy and likewise do not carry a fixed meaning across borders.

**Bias.** A boundary retrieved from Overture will not match the same-named boundary from
geoBoundaries. Differences are of the order of tens of metres and would appear as change
if the two were mixed within one analysis.

**Check.** One source is used throughout for boundaries (A-02). Overture is used for
infrastructure and buildings only, where it has no open competitor.

---

## Pending

Assumptions required by the master plan but not yet made, listed so their absence is
visible:

- Conductor type (ACSR assumed where PNOA does not supply it) — Phase 1
- Conductor operating temperature for sag calculation — Phase 3
- LiDAR point density adequacy for crown detection — Phase 2
- Model transfer between study sites (Cabrales trained, Lena applied, or vice versa) — Phase 7