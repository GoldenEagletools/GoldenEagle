# GoldenEagle 0.3.0 (Beta) — اكستنشن مجاني للعمارة البيئية والمستدامة

**EN** — A free extension for environmental and sustainable architecture (Syria and the world) for Rhino/Grasshopper.
Designed for Rhino 6 and later; **tested so far only on Rhino 6** (with Ladybug Tools 1.10.0). Developer: Eng. Mohammad Ghazi Al-Hussami.
**AR** — اكستنشن مجاني للعمارة البيئية والمستدامة (لسوريا والعالم) لـ Rhino/Grasshopper. مصمم لـ Rhino 6 فما فوق، ومُختبر حتى الآن على Rhino 6 فقط.

License / الترخيص: GPL-3.0-or-later. Put the full text from https://www.gnu.org/licenses/gpl-3.0.txt in a file named `LICENSE`. NASA POWER data are not covered by this license.

## 1) Install (development setup) / التركيب (إعداد التطوير)
1. Copy `goldeneagle_core.py` to `%APPDATA%\GoldenEagle\lib\` (create the folders). Every tool adds this folder to Python's path.
2. For each tool file: add a **GhPython Script** component, set the inputs/outputs named in its header (type hints below, all *Item Access*), paste the code.
3. Optional — reusable tool: right-click the component → **Create User Object**: Name = the full English name, Category = `GoldenEagle`, Sub-Category as in the table (the numeric prefix keeps the panel order; this behaviour is untested), Icon = the 24x24 PNG listed.
4. Grasshopper's solver must be enabled (Solution → Enable Solver).
5. For Ladybug integration, Ladybug Tools must be installed with its Python path set (`set_python_path.bat` with Rhino closed).
(A one-click installer is planned: tools will be self-contained so users type nothing.)

## 2) Tools / الأدوات
| Sub-Category | Tool (file) | Nickname | Icon | Inputs (type hint, all Item Access) | Outputs |
|---|---|---|---|---|---|
| 1 :: Information | GE About (`GE_01_About.py`) | GE About | `ge_about_24.png` | — | version, info_en, info_ar |
| 2 :: Study | GE Location (`GE_02_Location.py`) | GE Location | `ge_location_24.png` | idx int, lat float, lon float, tz float, name str, run bool | loc, names, report_en, report_ar |
| 2 :: Study | GE Standard Average (`GE_03_StandardAverage.py`) | Std Average | `ge_standard_24.png` | loc str, date str, run bool, update bool | name, elev, T, Tmax, Tmin, RH, WS, GHI, DNI, DHI, P, daily, report_en, report_ar |
| 2 :: Study | GE General Average (`GE_04_GeneralAverage.py`) | Gen Average | `ge_general_24.png` | same as Standard Average | same |
| 2 :: Study | GE Custom Average (`GE_05_CustomAverage.py`) | Cust Average | `ge_custom_24.png` | loc str, y1 int, m1 int, y2 int, m2 int, date str, run bool, update bool | same |
| 3 :: Engineering Disciplines | GE Architecture (`GE_08_Architecture.py`) | Architecture | `ge_architecture_24.png` | loc str, y_from int, y_to int, wind_years int, overhang_depth float, window_height float, run bool, update bool | qibla_deg, qibla_km, qibla_vec, noon_alt, wind_dir, wind_dir_name, wind_rose, facades, facade_kwh, best_facade, sunny_pct, report_en, report_ar |
| 3 :: Engineering Disciplines | GE Civil (`GE_09_Civil.py`) | Civil | `ge_civil_24.png` | loc str, y_from int, y_to int, soil bool, run bool, update bool | elev, wind_mean, wind_max, tmax_rec, tmin_rec, range_mean, rain_year, rain_max_day, frost_days, freeze_thaw, rh_mean, soil_info, report_en, report_ar |
| 3 :: Engineering Disciplines | GE Mechanical (`GE_10_Mechanical.py`) | Mechanical | `ge_mechanical_24.png` | loc str, y_from int, y_to int, base_heat float, base_cool float, hourly_years int, run bool, update bool | hdd, cdd, hdd_m, cdd_m, heat_design_daily, cool_design_daily, heat_design_hourly, cool_design_hourly, mcwb, wbt_m, wbd_m, report_en, report_ar |
| 3 :: Engineering Disciplines | GE Electrical (`GE_11_Electrical.py`) | Electrical | `ge_electrical_24.png` | loc str, y_from int, y_to int, noct float, tcoef float, run bool, update bool | psh, psh_m, best_tilt, tilt_winter, tilt_summer, yield_opt, gain_vs_horizontal, derate_hot, temp_factor_m, voc_tmin, autonomy_days, wind50, report_en, report_ar |
| 3 :: Engineering Disciplines | GE Agricultural (`GE_12_Agricultural.py`) | Agricultural | `ge_agricultural_24.png` | loc str, y_from int, y_to int, kc float, base_gdd float, run bool, update bool | et0_m, et0_year, rain_year, deficit_m, aridity, frost_last, frost_first, frost_days, gdd_year, hot_days, report_en, report_ar |
| 4 :: Ladybug Integration | GE AMY Export to EPW (`GE_06_AMY_ExportToEPW.py`) | AMY to EPW | `ge_amy_24.png` | loc str, year int, city str, out_dir str, run bool, site_elev float | epw_path, lat_o, lon_o, tz_o, elev_o, city_o, T_m, GHI_m, report_en, report_ar |
| 4 :: Ladybug Integration | GE TMY Export to EPW (`GE_07_TMY_ExportToEPW.py`) | TMY to EPW | `ge_tmy_24.png` | loc str, y_from int, y_to int, city str, out_dir str, site_elev float, run bool | epw_path, lat_o, lon_o, tz_o, elev_o, city_o, T_m, GHI_m, years, report_en, report_ar |

Icons: `GoldenEagle_icons/tools/` (24, 48 and 256 px) and `GoldenEagle_icons/` (eagle logo and badge variants).

## 3) Typical flow / سير العمل
- `GE Location` (idx from `names`, or lat/lon with optional name and tz) → any tool, with `loc` wired and `run = True`.
- Engineering Disciplines tools use the daily cache and the period 1991-2020 by default (`y_from`/`y_to` to change; complete years only). Options that download HOURLY data (`wind_years`, `hourly_years`) are large on first use.
- Ladybug: `GE Location` → `GE AMY Export to EPW` (year) or `GE TMY Export to EPW` → `epw_path` → `_epw_file` of Ladybug's *Import EPW*. Free coordinates need `tz` set in `GE Location` for EPW export.

## 4) Things to know / ملاحظات
- Data: NASA POWER (reanalysis; weather ~0.5x0.625 deg, solar ~1x1 deg cells). Not station measurements; locations in the same cell get the same weather values. Compared so far with one reference file only (Homs): our air was drier and windier, minimum temperatures colder (partly cell elevation), direct/diffuse split different. Treat as preliminary; check humidity-sensitive work against station data.
- The discipline tools give INDICATORS and screening values, not design loads or official design conditions (wind loads, drainage, ASHRAE design conditions, soil/geotechnical reports, bankable PV yield need the applicable codes and specialist tools). Each report lists its method and simplifications.
- Everything is cached in `%APPDATA%\GoldenEagle\cache`; requests identify the app with a `GoldenEagle-Grasshopper` User-Agent.
- Ladybug reads the EPW *missing* codes (e.g. 999999) as ordinary numbers: avoid illuminance, visibility, ceiling, weather, snow, aerosol, opaque sky cover and night albedo fields.
- `site_elev` (EPW tools) applies a simple, unvalidated elevation correction to temperature, pressure and dew point.
