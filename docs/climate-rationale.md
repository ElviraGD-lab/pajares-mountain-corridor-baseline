# Climate rationale for `asturias-grid-risk-ai`

Why this project exists, what its own data show, and — equally important — what those
data do not support.

Intended as source material for the repository README and for presentation. Written to
survive a reader who knows the field.

---

## 1. The question

**Is the clearance between overhead conductors and vegetation in Asturias shrinking, and
can that be measured from open data?**

Not "are there trees near power lines". That is an inventory question, answered by
inspection. The question above is about change over time, and it has two components that
move in opposite directions.

---

## 2. The two-sided mechanism

Clearance between a conductor and the canopy below it is reduced by two independent
processes.

**Vegetation rises.** Growth adds height to the canopy. In Asturias the growing season is
long and the climate is Atlantic-wet; beech, oak and chestnut on the slopes below
transmission corridors gain height every year unless cut back.

**The conductor descends.** An overhead conductor hangs as a catenary between towers. Its
length depends on temperature: metal expands when heated. A longer conductor in the same
span has a lower low point, so sag increases and clearance falls.

Conductor temperature is not air temperature. The conductor is heated by three sources:
ambient air, solar radiation, and Joule heating from the load current. On a hot, still day
under heavy load a conductor can run tens of degrees above ambient. Maximum operating
temperature for ACSR is typically 75–85 °C. **Air temperature is a necessary input to
conductor temperature, not a substitute for it.**

The worst case is a coincidence: hot summer day at peak load. In Spain that is also peak
air-conditioning demand and peak canopy density.

---

## 3. What this project's own data show

All figures below were measured in the course of this work and are reproducible from the
notebooks. Sources, parameters and limitations are recorded in
`cloud-native-remote-sensing-notes.md` and `ASSUMPTIONS.md`.

### 3.1 Maximum temperature is rising at Puerto de Pajares

TerraClimate monthly maximum 2-m temperature, 1970–2025, 672 monthly values, nearest grid
cell to the pass (42.9792 N, 5.7708 W):

| | value |
|---|---|
| Mean of monthly maxima | 12.32 °C |
| Trend | **+0.48 °C per decade** |
| Total change 1970–2025 | **+2.66 °C** |

The trend exceeds the Spanish national average of roughly 0.3–0.4 °C per decade, which is
consistent with the known pattern of faster warming at altitude.

### 3.2 The trend is robust to grid-cell choice; the absolute value is not

TerraClimate resolves 1/24° (~4.6 km). Two adjacent cells straddling the watershed at
Pajares were compared:

| | South cell (42.9792) | North cell (43.0625) | difference |
|---|---|---|---|
| Mean | 12.32 °C | 15.60 °C | **3.28 °C** |
| Trend | +0.48 °C/decade | +0.45 °C/decade | **0.03 °C/decade** |

The two cells are 4.6 km apart and differ in mean temperature by more than the entire
century-scale European warming signal — because they differ in mean elevation. Their
trends agree to within 0.03 °C per decade, and their annual series run parallel across all
55 years.

**Conclusion, verified rather than assumed: absolute temperatures from a 4-km climate grid
cannot be attached to a specific point in mountainous terrain; changes over time can.**

### 3.3 Vegetation at the same location is dense and seasonally active

Sentinel-2 NDVI at the same coordinates, 2023, after cloud masking, spike rejection and a
minimum sun-elevation filter (48 acquisitions → 28 usable):

- February minimum around 0.49 — deciduous canopy leaf-off over an evergreen understorey
- May rise from 0.59 to 0.87 in a single month — leaf-out
- June–October plateau at 0.85–0.90 — **closed canopy, NDVI saturated**

The saturation is itself a finding: above roughly 0.85 the index stops discriminating
density. **NDVI establishes that closed forest is present; it cannot measure how tall it
is.** Height requires LiDAR.

### 3.4 The regional picture is consistent

Landsat 8 annual median composites over the whole of Asturias, 2020 and 2025, Tier 1 only,
identical processing and identical display scale: distributions matched to within 0.002 at
every percentile. The 2025 composite is uniformly brighter by that amount — a uniform
shift, which is not how a change in surface cover would present, and is most plausibly an
artefact of differing observation counts (24 vs 20 solar days).

Recorded here because it is a **negative result and belongs in the record**: RGB composites
of two years cannot separate a radiometric shift from real change. Quantitative change
detection requires an index, not an image.

---

## 4. What is already known and documented

This section exists so the project is not presented as a discovery of something already
established. Everything below is external to this work.

**The mechanism is codified in standards.** NERC FAC-003 (Transmission Vegetation
Management) requires that assessment of clearance account for conductor sag and movement
across the operating range from no-load to maximum, and distinguishes "grow-in" from
"fall-in" threats.

**Climate-aware vegetation management is an established research topic.** Reviews of grid
adaptation identify sag under heat plus heavy loading as a clearance risk and call for
vegetation management policy that accounts for temperature, wind speed and growing-season
length.

**Remote sensing for vegetation management is commercial.** Utilities and vendors are
actively moving from cyclical manual inspection toward predictive management using
satellite and UAV data.

**Spatial climate-risk assessment of transmission corridors has been published** — for
example a GIS risk assessment covering forest fire, winter storm and technical failure
risks for transmission lines in the Cologne district, Germany.

**Spain has national climate adaptation policy covering energy infrastructure.** The
national adaptation plan includes reinforcement of energy infrastructure and protection of
the electrical system against storms. Large companies additionally face EU climate-risk
disclosure requirements.

**Grid resilience is high on the Spanish agenda.** A major blackout affected the Iberian
peninsula in April 2025; its causes are a separate matter and are not claimed here to be
vegetation-related, but grid reliability has had sustained political and public attention
in Spain since.

---

## 5. What is actually missing

Given section 4, the contribution of this project is not the mechanism. It is the
following, and the claim should be made in these terms:

**No open, local, quantified evidence exists for Asturias.** The published work is
national, European or North American. Nobody has put a number on how much the maximum
temperature above a specific Asturian pass has risen, alongside a measurement of the
vegetation along the specific corridors that cross it.

**The two components are rarely combined in open work.** Vegetation encroachment studies
measure the canopy. Grid climate-adaptation studies model the conductor. Studies treating
both as one shrinking clearance, on the same territory, with reproducible open data, are
scarce.

**Reproducibility.** Commercial solutions exist but are proprietary. A pipeline built
entirely on open data (Sentinel-2, Landsat, TerraClimate, geoBoundaries, PNOA LiDAR) with
its assumptions recorded can be inspected, criticised and repeated by anyone.

**Asturias is a demanding case and therefore a useful one.** Steep relief, high cloud
cover, low winter sun, snow — every condition under which standard remote-sensing
workflows degrade. A method that works here is unlikely to be over-fitted to easy terrain.

---

## 6. Limits of this evidence

Stated explicitly, because the argument is stronger for containing them.

**A temperature trend is not a sag calculation.** Converting +2.66 °C into a change in
clearance requires conductor type, span geometry, tension at installation, load profile and
a thermal model. None of that has been done here. Nothing in this document supports a
statement of the form "clearance has decreased by N centimetres".

**Absolute temperatures from TerraClimate are not usable at a point.** Section 3.2
demonstrates a 3.28 °C discrepancy between adjacent cells. Conductor temperature modelling
requires station data corrected for elevation, not a 4-km grid.

**TerraClimate is a modelled product, not a measurement.** It combines WorldClim
climatology with ERA5 anomalies by climatically aided interpolation. Its complete absence
of gaps reflects the method, not the reliability of any individual value.

**NDVI saturates.** It establishes presence and seasonal behaviour of closed canopy; it
does not measure height, and height is what determines clearance.

**One year, one point, one site.** The NDVI series covers 2023 at Pajares. Multi-year
series and the Cabrales site are not yet done. Transferability between the two sites is
untested and is listed as a pending assumption.

**Cloud masking is imperfect in this terrain, and imperfect in a biased direction.** The
SCL mask over-flags cloud on steep slopes at low sun, so the number of valid observations
is systematically lower exactly where the corridors run.

---

## 7. Further climate analyses worth adding

TerraClimate carries other variables on the same grid, accessible by changing one string in
the code already written. Each has a defensible connection to grid risk — and each has a
limitation that must be stated with it.

**Snow water equivalent (`swe`).** Ice and snow loading is a design case for conductors and
towers in mountain terrain: accumulated load increases sag and can bring down spans. A
declining SWE trend would be a genuine finding for Pajares at 1370 m. *Limit:* monthly
means say nothing about individual loading events.

**Wind speed (`ws`).** Wind causes conductor swing, reducing lateral clearance, and fells
trees into corridors. *Limit, and it is severe:* TerraClimate `ws` is a monthly mean at
10 m. Storm damage is caused by gusts lasting seconds. **Monthly mean wind speed cannot
support any statement about storms.** For that, station or reanalysis data at hourly
resolution is required. Do not use this variable to argue about storm frequency.

**Vapour pressure deficit (`vpd`) and Palmer Drought Severity Index (`pdsi`).** Drought
stresses trees; stressed trees die; dead trees fall. Both also relate to fire danger, and
vegetation contact is a recognised ignition source. A drought trend would connect the
vegetation and ignition strands of the project. *Limit:* these are indices, not direct
observations of tree mortality.

**Precipitation (`ppt`).** Growing-season water availability drives growth rate and thus how
fast the canopy rises.

**Minimum temperature (`tmin`).** A rising winter minimum lengthens the growing season,
which increases annual height increment. Arguably more directly connected to the
vegetation side of the mechanism than `tmax` is.

**Recommended order:** `swe` first — it is the most specific to mountain grid infrastructure
and the least likely to be already documented for this area. Then `tmin`, for the
growing-season argument. `ws` only with the gust caveat stated in the same sentence as the
result.

---

## 8. How to present this

**Lead with the measurement, not the concern.** "Maximum temperature above Puerto de
Pajares has risen 2.66 °C since 1970, and I verified that figure is robust to grid-cell
choice" is a stronger opening than "climate change threatens the grid."

**State the known state of the art before the contribution.** Section 4 before section 5.
An interviewer who knows FAC-003 will test whether you do.

**Volunteer the limits.** Section 6 is the part that distinguishes an engineer from an
enthusiast. Saying "this trend does not yet support a sag figure, and here is what would be
needed" demonstrates more competence than any result.

**Do not claim novelty of the mechanism.** Claim locality, openness and reproducibility.

**On the sector.** Observations about how slowly utilities change, or how they hire, may be
accurate but do not belong in a technical document. They weaken it: a reader who disagrees
with the characterisation discounts the measurements too. Keep this file to what can be
checked.