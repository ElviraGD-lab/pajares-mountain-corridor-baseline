# Methodology

Why this work is done the way it is. Decisions and their reasoning; the working
assumptions they produce are recorded separately in `ASSUMPTIONS.md`, and the
reusable procedures in `course-notes.md`.

---

## 0. Scope and position

This repository measures climate and vegetation conditions at Puerto de Pajares, a
mountain pass in the Cantabrian range through which a transport and energy corridor
passes — the AP-66 motorway, a railway, and high-voltage transmission lines.

**What this work does:** quantify, from open data, how maximum temperature and
vegetation cover have changed at a specific mountain location, and establish a
reproducible method for doing so.

**What it does not do:** assess risk to any transmission line. No conductor
geometry, no span data, no clearance calculation. That is the subject of a
separate project; the connection between the two is set out in
`climate-rationale.md`.

**Why mountains specifically.** Standard remote-sensing workflows are developed and
demonstrated on flat terrain, and they degrade in relief in ways that are
predictable but rarely handled in tutorial material. Every methodological decision
below exists because a default that works on a plain fails at 1370 m on a
watershed at 43° N. The degradation is measurable, and measuring it is part of the
result:

- 17.1 % of a December scene classified as terrain shadow, where any ratio index is
  dominated by noise
- 3.28 °C difference in mean maximum temperature between adjacent 4.6 km climate
  grid cells, driven by elevation alone
- a cloud mask that flags snow as cloud and over-flags steep slopes at low sun,
  biasing data loss toward exactly the slopes the corridor crosses

Terrain is not a complication to be worked around here. It is the subject.

---

## 1. Why administrative boundaries come from a single source

Three open sources were available: geoBoundaries via FieldMaps, Overture Maps, and
the Spanish IGN.

**geoBoundaries via FieldMaps** is used throughout. It is queryable in place over
HTTP without download, internally edge-matched so adjacent polygons share exact
borders, and ODbL licensed.

**Overture Maps** was evaluated and rejected as the boundary source: its division
subtypes (`locality`, `county`, `localadmin`, `region`) are not applied uniformly
across countries, so a query that finds a Spanish municipality will not find its
equivalent elsewhere without modification.

**IGN and the Spanish cadastre** are legally authoritative and would be preferred
if a result had to stand against an official boundary. They are not used here
because they require per-dataset download rather than remote query.

The decisive point is not which source is best in isolation. **Boundaries from
different providers differ by tens of metres.** That is immaterial for the area of
a concejo and material for a narrow corridor. One source is used throughout, and it
is named in every output.

Administrative levels are not universal categories. In Spain adm1 is the comunidad
autónoma, adm2 the provincia, adm3 the municipio — called *concejo* in Asturias.
Asturias is uniprovincial, so the same territory appears at both adm1 and adm2 and
an adm2 query returns exactly one feature. Treating adm2 as "municipality" would be
wrong by two administrative levels and by a factor of 78 in feature count.

---

## 2. Why measurement and delivery use different coordinate systems

Two coordinate reference systems are used deliberately, and the distinction is
enforced in code rather than left to habit.

**EPSG:25830 (ETRS89 / UTM zone 30N)** for anything measured: area, length,
distance, buffer width. Geometric operations in geographic coordinates return
numbers without raising an exception, and those numbers are in square or linear
degrees, which are not convertible to metric units. The failure is silent.

**EPSG:4326** for delivery only: GeoJSON outputs, STAC queries, web display.

The target CRS is stated explicitly at load time rather than left to automatic
selection. Pajares lies 27 km from the boundary between UTM zones 29N and 30N:
its Sentinel-2 tile (`29TQH`) is native to zone 29 and is reprojected on load,
while sites further east fall in zone 30. An automatic choice resolves to whichever
zone the data happens to suggest, which differs between sites and makes them
non-comparable.

When a raster and a vector must be brought together, **the vector is reprojected.**
Reprojecting a polygon recomputes vertex coordinates exactly; reprojecting a raster
resamples pixel values.

---

## 3. Why visualisation scale is fixed rather than derived from the data

Any raster shown as an image requires a rule mapping data values to screen
brightness, defined by a minimum and a maximum.

Percentile stretching computes those limits **from the data being displayed**. It
produces the best-looking single image, because the scale is fitted to the content.

**For any output that will be compared — across years, across sites, or against
another study — the limits must be fixed and stated.** Under percentile stretching,
two composites of the same place in different years both occupy the full brightness
range regardless of what changed on the ground. Real change is absorbed into the
scale and becomes invisible; a difference caused solely by the stretch becomes
visible. The failure is silent: both images look correct.

Data may inform the value. Data must not recompute it per dataset. The limits used
here were chosen once from the 98th percentile of both composites and then frozen
as a constant.

The same reasoning applies to any parameter computed from data and then used to
compare datasets.

---

## 4. Why a median composite is a background, not a snapshot

Both single scenes and median composites are used, for different questions, and
conflating them would misstate what the results describe.

A **single scene** is a moment. Every pixel was acquired within the same few
seconds, so shadow, water level and post-event condition are internally consistent
and can be measured. Its weakness is cloud: over Asturias a fully clear scene over
a given location is rare.

A **median composite** is a background. Each pixel is the middle value of its own
time series, so adjacent pixels may originate from different dates. Nothing that
depends on a specific instant may be measured on it. In exchange, cloud is removed
statistically rather than by waiting for a clear day.

The median is robust only while cloudy observations are a minority **for that
pixel**. Asturias is among the cloudiest regions of Spain, so the number of valid
observations entering each composite is recorded as a quality figure rather than
assumed adequate, and composites built from few dates are treated as less reliable
rather than as equivalent.

---

## 5. Why quality control precedes smoothing

A smoothing filter does not distinguish signal from error. It reduces variability,
whatever the source of that variability.

An implausible value that survives into a smoothed series is not removed. It is
distributed across its neighbours and made invisible: an obvious spike becomes a
plausible curve. Smoothness is persuasive, which makes an undetected error more
dangerous after smoothing than before it.

Quality control therefore runs before any filter, in three stages:

**Per-pixel masking** of cloud, cloud shadow, terrain shadow and snow, using the
scene classification layer. Classes for terrain shadow and snow are included, which
tutorial material generally omits: at 43° N in December the sun reaches 21°, and
north-facing slopes fall into their own shadow with near-zero reflectance in every
band, where a ratio index is dominated by noise.

**Plausibility rejection** of values that depart from both temporal neighbours in
the same direction by more than a physically possible amount. A closed deciduous
canopy cannot gain or lose a quarter of its NDVI in days; such a point is residual
cloud or haze the mask missed.

**Illumination rejection** of observations acquired below a minimum solar
elevation, read from scene metadata. This addresses the cause rather than the
symptom: clipping an index to its valid range afterwards converts an obviously
impossible value into a plausible one, which is worse than leaving it visible.

---

## 6. Why interpolation is permitted inside a series and extrapolation is not

Interpolation estimates a value between known observations. Its error is bounded by
its neighbours.

Forward and backward filling copy a value into a period where nothing was observed.
That is extrapolation presented as data, and its error is unbounded.

Gaps at the ends of a series are therefore left as gaps. A break in a plotted line
is information: it states that no reliable observation exists for that period. A
line drawn through it states the opposite, and states it without evidence.

For the Pajares 2023 NDVI series this leaves the period from November to January
empty. Winter observations are removed simultaneously by cloud cover, terrain
shadow and low sun — the three filters concentrate their losses in the same
months. That is a real limitation of optical remote sensing in mountain winter, and
it is reported rather than filled.

---

## 7. Why every result is verified against external knowledge

Internal consistency is not correctness. Code that runs without error can produce
values that are physically impossible, and a stretched image will render them
convincingly.

Each result is therefore checked against something known independently of the
computation:

| Result | Check |
|---|---|
| 78 concejos of Asturias | total area 10 601 km² against a published ~10 600 km² |
| Reflectance after conversion | range approximately 0 to 1 |
| Water mask | 31.5 km², consistent with the reservoirs present |
| Clipped composite | 58.2 % of the grid holds data, consistent with land area over bounding box |
| Temperature trend | +0.48 °C/decade against a Spanish average of 0.3–0.4 |

Numbers are inspected before images, in every case. A contrast stretch fitted to
the data will render a corrupted array as a plausible landscape.

---

## 8. Rejected options

Recorded so that the choices above are visible as choices.

**A fixed summer compositing window** was the initial preference for comparing
years, on the reasoning that an annual median mixes leaf-on and leaf-off states in
proportions set by which months happened to be clear. It was rejected on the data:
at the chosen cloud threshold a June–September window left as few as one Tier 1
scene on one WRS-2 tile. The full year was then tested for the bias the seasonal
window was meant to prevent, and the two years proved balanced — mean sun elevation
within 0.2°, leaf-off share within 3.2 percentage points. The decision was made on
metadata counts obtained in seconds, before any pixel was loaded.

**Combining Landsat 8 and 9** in the later year would have added observations but
made the two years unequal in sensor composition, since Landsat 9 did not exist in
the earlier year. Comparability was preferred over sample size.

**Merging the two study sites** into one analysis was rejected. They differ in
geology, vegetation and native UTM zone. Processing them separately also allows
transferability between them to be measured rather than assumed.

**Filling winter gaps by extrapolation** was rejected for the reason given in
section 6.

---

## 9. Relationship to further work

This repository establishes conditions. A separate project assesses what those
conditions mean for the transmission infrastructure that crosses the pass, which
requires conductor specifications, span geometry and a thermal model — none of
which are present here.

The two are bound by a common subject: **transmission corridors in mountainous
terrain, where relief and climate depart far enough from the conditions standard
methods assume that the methods themselves must be adapted.** The measurements in
this repository are the first half of that argument; the second half is not claimed
here.