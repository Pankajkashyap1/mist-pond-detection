"""
suitability_engine.py
---------------------
AI Suitability Analysis Engine for User-Drawn Pond Locations.

Given a user-drawn polygon on the map, this engine:
1. Fetches elevation data for the drawn area from Open-Elevation API
2. Analyzes terrain slope, depression index, and perimeter-to-area ratio
3. Scores the location on a 0-100 "Pond Suitability" scale
4. If suitable, computes optimal depth, fill volume, and constructon feasibility
5. Returns a rich recommendation report with reasons and suggestions
"""

import requests
import numpy as np
import math
from typing import List, Dict, Any


# ─────────────────────────────────────────────────────────────────────────────
# 1. ELEVATION FETCHING
# ─────────────────────────────────────────────────────────────────────────────

def fetch_elevation_for_polygon(polygon_coords: List[List[float]], grid_samples: int = 12) -> Dict:
    """
    Build a sampling grid INSIDE the user-drawn polygon and query Open-Elevation.

    :param polygon_coords: List of [lat, lon] pairs forming the polygon
    :param grid_samples: Number of sample points per axis (grid_samples x grid_samples)
    :return: Dict with lats, lons, elevations, and stats
    """
    lats = [p[0] for p in polygon_coords]
    lons = [p[1] for p in polygon_coords]

    min_lat, max_lat = min(lats), max(lats)
    min_lon, max_lon = min(lons), max(lons)

    # Build uniform grid inside bounding box
    grid_lats = np.linspace(min_lat, max_lat, grid_samples)
    grid_lons = np.linspace(min_lon, max_lon, grid_samples)

    locations = [
        {"latitude": float(lat), "longitude": float(lon)}
        for lat in grid_lats
        for lon in grid_lons
    ]

    try:
        resp = requests.post(
            "https://api.open-elevation.com/api/v1/lookup",
            json={"locations": locations},
            timeout=20,
            headers={"Accept": "application/json", "Content-Type": "application/json"}
        )
        resp.raise_for_status()
        results = resp.json().get("results", [])
        elevations = [r["elevation"] for r in results]
    except Exception as e:
        # Fallback: simulate gentle slope terrain if API unreachable
        print(f"[Elevation API fallback: {e}]")
        elevations = _simulate_elevation_grid(
            min_lat, max_lat, min_lon, max_lon, grid_samples
        )

    elev_array = np.array(elevations).reshape(grid_samples, grid_samples)
    lat_grid = np.array([p["latitude"] for p in locations]).reshape(grid_samples, grid_samples)
    lon_grid = np.array([p["longitude"] for p in locations]).reshape(grid_samples, grid_samples)

    return {
        "elevations": elev_array,
        "lats": lat_grid,
        "lons": lon_grid,
        "min_lat": min_lat, "max_lat": max_lat,
        "min_lon": min_lon, "max_lon": max_lon,
        "center_lat": (min_lat + max_lat) / 2,
        "center_lon": (min_lon + max_lon) / 2,
    }


def fetch_elevation_for_bbox(min_lat: float, max_lat: float, min_lon: float, max_lon: float, grid_samples: int = 24) -> Dict:
    """Fetch elevation grid across any lat/lon bounding box for whole-map contours."""
    grid_lats = np.linspace(min_lat, max_lat, grid_samples)
    grid_lons = np.linspace(min_lon, max_lon, grid_samples)

    locations = [
        {"latitude": float(lat), "longitude": float(lon)}
        for lat in grid_lats
        for lon in grid_lons
    ]

    try:
        resp = requests.post(
            "https://api.open-elevation.com/api/v1/lookup",
            json={"locations": locations},
            timeout=20,
            headers={"Accept": "application/json", "Content-Type": "application/json"}
        )
        resp.raise_for_status()
        results = resp.json().get("results", [])
        elevations = [r["elevation"] for r in results]
    except Exception as e:
        print(f"[BBox Elevation API fallback: {e}]")
        elevations = _simulate_elevation_grid(min_lat, max_lat, min_lon, max_lon, grid_samples)

    elev_array = np.array(elevations).reshape(grid_samples, grid_samples)
    lat_grid = np.array([p["latitude"] for p in locations]).reshape(grid_samples, grid_samples)
    lon_grid = np.array([p["longitude"] for p in locations]).reshape(grid_samples, grid_samples)

    return {
        "elevations": elev_array,
        "lats": lat_grid,
        "lons": lon_grid,
        "min_lat": min_lat, "max_lat": max_lat,
        "min_lon": min_lon, "max_lon": max_lon,
    }


def _simulate_elevation_grid(min_lat, max_lat, min_lon, max_lon, gs) -> List[float]:
    """Generate a plausible micro-terrain elevation grid for demo/offline use."""
    np.random.seed(int(abs(min_lat * 1000) + abs(min_lon * 1000)) % 999)
    base = 250.0
    elevs = []
    for i, lat in enumerate(np.linspace(min_lat, max_lat, gs)):
        for j, lon in enumerate(np.linspace(min_lon, max_lon, gs)):
            # Gentle bowl depression pattern (ideal pond terrain)
            di = (i - gs / 2) / (gs / 2)
            dj = (j - gs / 2) / (gs / 2)
            bowl = (di ** 2 + dj ** 2) * 3.5        # bowl curvature
            noise = np.random.uniform(-0.8, 0.8)
            elevs.append(round(base + bowl + noise, 2))
    return elevs


# ─────────────────────────────────────────────────────────────────────────────
# 2. POLYGON AREA & PERIMETER CALCULATION (Haversine)
# ─────────────────────────────────────────────────────────────────────────────

def haversine_distance_m(lat1, lon1, lat2, lon2) -> float:
    R = 6_371_000  # Earth radius in metres
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def polygon_area_sqm(coords: List[List[float]]) -> float:
    """
    Shoelace formula adapted for geographic (lat/lon) coordinates using
    local Cartesian approximation in metres.
    """
    if len(coords) < 3:
        return 0.0
    center_lat = sum(c[0] for c in coords) / len(coords)
    lat_to_m = 111_000
    lon_to_m = 111_000 * math.cos(math.radians(center_lat))

    def to_xy(c):
        return c[1] * lon_to_m, c[0] * lat_to_m

    pts = [to_xy(c) for c in coords]
    n = len(pts)
    area = 0.0
    for i in range(n):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % n]
        area += x1 * y2 - x2 * y1
    return abs(area) / 2.0


def polygon_perimeter_m(coords: List[List[float]]) -> float:
    perimeter = 0.0
    n = len(coords)
    for i in range(n):
        lat1, lon1 = coords[i]
        lat2, lon2 = coords[(i + 1) % n]
        perimeter += haversine_distance_m(lat1, lon1, lat2, lon2)
    return perimeter


# ─────────────────────────────────────────────────────────────────────────────
# 3. AI SUITABILITY SCORING
# ─────────────────────────────────────────────────────────────────────────────

def analyze_suitability(
    elevation_data: Dict,
    surface_area_sqm: float,
    perimeter_m: float,
    annual_rainfall_mm: float = 1100.0
) -> Dict[str, Any]:
    """
    Multi-factor AI scoring of the user-drawn pond location.

    Factors scored:
      1. Terrain Slope (gradient) – lower slope = better water retention
      2. Depression Index – bowl/sink shape is ideal
      3. Shape Compactness – compact shapes are cost-efficient to construct
      4. Minimum Size Threshold – area must be viable
      5. Rainfall Adequacy – sufficient rainfall must feed the catchment

    Returns a structured report dict.
    """
    elev = elevation_data["elevations"]
    reasons = []
    penalties = []
    scores = {}

    # ── 1. Slope Analysis (lower is better for water retention)
    gy, gx = np.gradient(elev)
    slope_deg = np.degrees(np.arctan(np.sqrt(gx**2 + gy**2)))
    avg_slope = float(np.mean(slope_deg))
    max_slope = float(np.max(slope_deg))

    if avg_slope < 2.0:
        scores["slope"] = 95
        reasons.append(f"✅ Excellent flat terrain (avg slope {avg_slope:.1f}°) – minimal earthwork required.")
    elif avg_slope < 5.0:
        scores["slope"] = 80
        reasons.append(f"✅ Gentle slope ({avg_slope:.1f}°) – well-suited for a farm pond with minor bunding.")
    elif avg_slope < 10.0:
        scores["slope"] = 55
        reasons.append(f"⚠️ Moderate slope ({avg_slope:.1f}°) – a check dam or contour bund may be needed.")
        penalties.append("Embankment construction cost will be higher due to terrain gradient.")
    else:
        scores["slope"] = 25
        reasons.append(f"❌ Steep terrain ({avg_slope:.1f}°) – not ideal for a gravity-fed surface pond.")
        penalties.append("Steep slope causes rapid runoff overflow; water storage efficiency will be low.")

    # ── 2. Depression Index (bowl-shaped terrain is ideal)
    center_elev = float(elev[elev.shape[0]//2, elev.shape[1]//2])
    rim_elev = float(np.mean([elev[0, :].mean(), elev[-1, :].mean(), elev[:, 0].mean(), elev[:, -1].mean()]))
    depression_m = rim_elev - center_elev

    if depression_m >= 2.0:
        scores["depression"] = 95
        reasons.append(f"✅ Strong natural depression ({depression_m:.1f} m below rim) – acts as a natural water collector.")
    elif depression_m >= 0.5:
        scores["depression"] = 78
        reasons.append(f"✅ Slight natural depression ({depression_m:.1f} m) – moderate excavation needed to deepen.")
    elif depression_m >= -0.5:
        scores["depression"] = 55
        reasons.append(f"⚠️ Flat terrain (elevation difference: {depression_m:.1f} m) – full earthwork excavation needed.")
        penalties.append("No natural depression – manual excavation required for basin formation.")
    else:
        scores["depression"] = 30
        reasons.append(f"❌ Elevated ridge/mound detected ({depression_m:.1f} m above rim) – water will drain away.")
        penalties.append("Terrain is raised; rainwater will flow away from this location.")

    # ── 3. Shape Compactness (compact = lower perimeter-to-area cost)
    compactness = (4 * math.pi * surface_area_sqm) / (perimeter_m ** 2 + 1e-5)
    compactness = max(0, min(1, compactness))

    if compactness >= 0.6:
        scores["compactness"] = 90
        reasons.append(f"✅ Compact shape (index {compactness:.2f}) – efficient perimeter-to-area ratio reduces embankment cost.")
    elif compactness >= 0.35:
        scores["compactness"] = 72
        reasons.append(f"✅ Reasonable shape compactness ({compactness:.2f}) – acceptable for pond construction.")
    else:
        scores["compactness"] = 45
        reasons.append(f"⚠️ Irregular/elongated shape (index {compactness:.2f}) – high embankment perimeter cost.")
        penalties.append("Irregular shape requires more earthwork perimeter lining/compaction.")

    # ── 4. Minimum Area Viability
    if surface_area_sqm < 50:
        scores["area"] = 20
        reasons.append(f"❌ Very small area ({surface_area_sqm:.0f} m²) – below minimum viable pond size (50 m²).")
        penalties.append("Too small to provide meaningful water storage. Extend the drawn area.")
    elif surface_area_sqm < 500:
        scores["area"] = 68
        reasons.append(f"⚠️ Small but viable area ({surface_area_sqm:.0f} m²) – suitable for a household-scale farm pond.")
    elif surface_area_sqm < 50000:
        scores["area"] = 90
        reasons.append(f"✅ Good pond area ({surface_area_sqm:.0f} m² = {surface_area_sqm/10000:.2f} ha) – village/community pond scale.")
    else:
        scores["area"] = 80
        reasons.append(f"✅ Large reservoir scale ({surface_area_sqm/10000:.2f} hectares) – multi-village water storage system.")

    # ── 5. Rainfall Adequacy
    if annual_rainfall_mm >= 900:
        scores["rainfall"] = 92
        reasons.append(f"✅ Annual rainfall {annual_rainfall_mm:.0f} mm – sufficient recharge to fill this pond annually.")
    elif annual_rainfall_mm >= 600:
        scores["rainfall"] = 72
        reasons.append(f"⚠️ Moderate rainfall {annual_rainfall_mm:.0f} mm – supplemental irrigation supply planning advised.")
    else:
        scores["rainfall"] = 42
        reasons.append(f"❌ Low rainfall region ({annual_rainfall_mm:.0f} mm) – pond may not fully recharge every season.")
        penalties.append("Consider groundwater recharge structures or rooftop runoff diversion.")

    # ── Final Weighted Score
    weights = {"slope": 0.28, "depression": 0.30, "compactness": 0.15, "area": 0.18, "rainfall": 0.09}
    final_score = round(sum(scores[k] * weights[k] for k in scores), 1)

    if final_score >= 75:
        verdict = "HIGHLY SUITABLE"
        verdict_color = "green"
        verdict_icon = "✅"
    elif final_score >= 55:
        verdict = "MODERATELY SUITABLE"
        verdict_color = "orange"
        verdict_icon = "⚠️"
    else:
        verdict = "NOT RECOMMENDED"
        verdict_color = "red"
        verdict_icon = "❌"

    return {
        "suitability_score": final_score,
        "verdict": verdict,
        "verdict_color": verdict_color,
        "verdict_icon": verdict_icon,
        "factor_scores": scores,
        "reasons": reasons,
        "penalties": penalties,
        "avg_slope_deg": round(avg_slope, 2),
        "max_slope_deg": round(max_slope, 2),
        "depression_m": round(depression_m, 2),
        "compactness": round(compactness, 3),
        "is_suitable": final_score >= 55,
    }


# ─────────────────────────────────────────────────────────────────────────────
# 4. POND DIMENSION RECOMMENDATION
# ─────────────────────────────────────────────────────────────────────────────

def recommend_pond_specs(
    surface_area_sqm: float,
    depression_m: float,
    avg_slope_deg: float,
    annual_rainfall_mm: float = 1100.0,
    catchment_area_sqm: float = None,
    runoff_coefficient: float = 0.30,
    max_depth_m: float = 4.0,
    evaporation_mm_year: float = 1400.0,
    seepage_mm_day: float = 2.5
) -> Dict[str, Any]:
    """
    Compute recommended depth, volume, and construction specs for the drawn pond.
    """
    # Estimate catchment if not provided (assume 8× pond area for rural flat terrain)
    if not catchment_area_sqm or catchment_area_sqm <= 0:
        catchment_area_sqm = surface_area_sqm * 8.0

    # Annual runoff volume (Rational Method)
    rainfall_m = annual_rainfall_mm / 1000.0
    runoff_m3 = round(runoff_coefficient * rainfall_m * catchment_area_sqm, 2)

    # Account for annual evaporation & seepage losses on the pond surface
    annual_loss_m = (evaporation_mm_year / 1000.0) + (seepage_mm_day * 365.0 / 1000.0)
    loss_volume_m3 = round(annual_loss_m * surface_area_sqm, 2)
    net_storage_needed_m3 = max(runoff_m3, loss_volume_m3 * 1.4)  # store at least 1.4× loss

    # Depth calculation
    # Bonus: if there's a natural depression, we can start from that depth
    natural_depth_bonus = max(0, min(1.5, depression_m))
    raw_depth = net_storage_needed_m3 / surface_area_sqm
    recommended_depth = round(min(max_depth_m, max(1.2, raw_depth + natural_depth_bonus)), 2)

    # Volume with trapezoidal cross-section (0.75 fill factor)
    gross_volume_m3 = round(surface_area_sqm * recommended_depth * 0.75, 2)
    net_usable_volume_m3 = round(max(0, gross_volume_m3 - loss_volume_m3), 2)

    # Earthwork / Excavation volume (volume to be dug in m³)
    existing_depression_vol = round(surface_area_sqm * natural_depth_bonus * 0.5, 2)
    excavation_needed_m3 = round(max(0, gross_volume_m3 - existing_depression_vol), 2)

    # Bund/Embankment height recommendation
    bund_height_m = round(recommended_depth + 0.5, 1)  # Freeboard of 0.5m

    # Irrigation area that can be served per irrigation cycle (paddy needs ~5000m³/ha)
    irrigation_area_ha = round(net_usable_volume_m3 / 5000.0, 2)

    # Drinking water supply (150 liters/person/day × 365 days)
    drinking_days_for_100_people = round(net_usable_volume_m3 * 1000 / (150 * 100), 0)

    # Cost estimate (rough: INR ~350/m³ excavation + compaction in rural India)
    est_cost_inr = round(excavation_needed_m3 * 350, 0)

    return {
        "catchment_area_sqm": round(catchment_area_sqm, 2),
        "annual_runoff_m3": runoff_m3,
        "annual_evaporation_seepage_loss_m3": loss_volume_m3,
        "recommended_depth_m": recommended_depth,
        "gross_storage_volume_m3": gross_volume_m3,
        "net_usable_volume_m3": net_usable_volume_m3,
        "excavation_required_m3": excavation_needed_m3,
        "bund_height_m": bund_height_m,
        "irrigation_potential_ha": irrigation_area_ha,
        "drinking_water_days_100_people": int(drinking_days_for_100_people),
        "estimated_construction_cost_inr": int(est_cost_inr),
        "estimated_construction_cost_display": f"₹{est_cost_inr:,.0f}",
        "surface_area_sqm": round(surface_area_sqm, 2),
        "surface_area_hectares": round(surface_area_sqm / 10000, 4),
        "perimeter_m": 0,  # filled in by caller
    }
