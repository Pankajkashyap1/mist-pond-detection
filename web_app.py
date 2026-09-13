"""
web_app.py
----------
Flask Web Application — Smart AI Pond Suitability & Hydrology System.
This version has a draw-on-map feature for users to mark proposed pond sites.
"""

import os
import requests as req_lib
import numpy as np
from flask import Flask, render_template, request, jsonify

from suitability_engine import (
    fetch_elevation_for_polygon,
    fetch_elevation_for_bbox,
    polygon_area_sqm,
    polygon_perimeter_m,
    analyze_suitability,
    recommend_pond_specs,
)
from hydrology_engine import HydrologyEngine

app = Flask(__name__, template_folder="templates", static_folder="static")


# ─────────────────────────────────────────────────────────────────────────────
# 1.  HOME
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


# ─────────────────────────────────────────────────────────────────────────────
# 2.  ANALYZE DRAWN POLYGON
#     POST /api/analyze_polygon
#     Body: { coordinates: [[lat,lon],...], annual_rainfall_mm: 1100, catchment_area_sqm: null }
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/api/analyze_polygon", methods=["POST"])
def analyze_polygon():
    try:
        data = request.json or {}
        coords = data.get("coordinates", [])           # [[lat, lon], ...]
        rainfall_mm = float(data.get("annual_rainfall_mm", 1100.0))
        custom_catchment = data.get("catchment_area_sqm", None)
        if custom_catchment:
            custom_catchment = float(custom_catchment)

        if len(coords) < 3:
            return jsonify({"status": "error", "message": "Please draw a polygon with at least 3 points."}), 400

        # ── Step 1: Geometry
        area_sqm = polygon_area_sqm(coords)
        perimeter_m = polygon_perimeter_m(coords)
        center_lat = sum(c[0] for c in coords) / len(coords)
        center_lon = sum(c[1] for c in coords) / len(coords)

        # ── Step 2: Elevation Data (32x32 grid for ultra-smooth contours)
        GRID_SIZE = 32
        elevation_data = fetch_elevation_for_polygon(coords, grid_samples=GRID_SIZE)

        # ── Step 3: AI Suitability Analysis
        suitability = analyze_suitability(
            elevation_data=elevation_data,
            surface_area_sqm=area_sqm,
            perimeter_m=perimeter_m,
            annual_rainfall_mm=rainfall_mm,
        )

        # ── Step 4: Pond Specs (only if suitable)
        specs = None
        if suitability["is_suitable"]:
            specs = recommend_pond_specs(
                surface_area_sqm=area_sqm,
                depression_m=suitability["depression_m"],
                avg_slope_deg=suitability["avg_slope_deg"],
                annual_rainfall_mm=rainfall_mm,
                catchment_area_sqm=custom_catchment,
            )
            specs["perimeter_m"] = round(perimeter_m, 2)

        # ── Step 5: Elevation Profile for chart (perimeter ring values)
        elev_profile = _extract_perimeter_profile(elevation_data)
        elev_heatmap_data = _build_heatmap_data(elevation_data)

        return jsonify({
            "status": "success",
            "geometry": {
                "surface_area_sqm": round(area_sqm, 2),
                "surface_area_hectares": round(area_sqm / 10000, 4),
                "perimeter_m": round(perimeter_m, 2),
                "center_lat": round(center_lat, 6),
                "center_lon": round(center_lon, 6),
            },
            "elevation_stats": {
                "min_m": round(float(elevation_data["elevations"].min()), 2),
                "max_m": round(float(elevation_data["elevations"].max()), 2),
                "mean_m": round(float(elevation_data["elevations"].mean()), 2),
                "depression_m": suitability["depression_m"],
                "avg_slope_deg": suitability["avg_slope_deg"],
                "max_slope_deg": suitability["max_slope_deg"],
            },
            "suitability": suitability,
            "pond_specs": specs,
            "elevation_profile": elev_profile,
            "elevation_heatmap": elev_heatmap_data,
            "elevation_grid": {
                "grid_size": GRID_SIZE,
                "values": elevation_data["elevations"].tolist(),
                "lats":    elevation_data["lats"].tolist(),
                "lons":    elevation_data["lons"].tolist(),
                "min_lat": elevation_data["min_lat"],
                "max_lat": elevation_data["max_lat"],
                "min_lon": elevation_data["min_lon"],
                "max_lon": elevation_data["max_lon"],
            },
        })

    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500


# ─────────────────────────────────────────────────────────────────────────────
# 3.  SEARCH / GEOCODE LOCATION
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/api/geocode", methods=["GET"])
def geocode():
    query = request.args.get("q", "")
    if not query:
        return jsonify({"status": "error"}), 400
    try:
        resp = req_lib.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": query, "format": "json", "limit": 5},
            headers={"User-Agent": "AquaVisionPondPlanner/2.0"},
            timeout=8,
        )
        resp.raise_for_status()
        return jsonify({"status": "success", "results": resp.json()})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# ─────────────────────────────────────────────────────────────────────────────
# 4.  MAP VIEWPORT CONTOURS (FULL SCREEN CONTOURS)
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/api/map_contours", methods=["POST"])
def map_contours():
    """Fetch elevation grid for the visible map bounding box to display full-map contours."""
    try:
        data = request.json or {}
        min_lat = float(data.get("min_lat"))
        max_lat = float(data.get("max_lat"))
        min_lon = float(data.get("min_lon"))
        max_lon = float(data.get("max_lon"))

        GRID_SIZE = 28
        elevation_data = fetch_elevation_for_bbox(min_lat, max_lat, min_lon, max_lon, grid_samples=GRID_SIZE)

        return jsonify({
            "status": "success",
            "elevation_grid": {
                "grid_size": GRID_SIZE,
                "values": elevation_data["elevations"].tolist(),
                "lats":    elevation_data["lats"].tolist(),
                "lons":    elevation_data["lons"].tolist(),
                "min_lat": elevation_data["min_lat"],
                "max_lat": elevation_data["max_lat"],
                "min_lon": elevation_data["min_lon"],
                "max_lon": elevation_data["max_lon"],
            }
        })
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500


# ─────────────────────────────────────────────────────────────────────────────
# 4.  HELPER: elevation profile & heatmap
# ─────────────────────────────────────────────────────────────────────────────

def _extract_perimeter_profile(elevation_data: dict) -> list:
    """Return a ring of elevation values around the grid perimeter for the chart."""
    e = elevation_data["elevations"]
    r, c = e.shape
    top    = list(e[0, :])
    right  = list(e[1:, -1])
    bottom = list(e[-1, ::-1][1:])
    left   = list(e[-1:0:-1, 0][:-1])
    ring   = top + right + bottom + left
    return [round(float(v), 2) for v in ring]


def _build_heatmap_data(elevation_data: dict) -> list:
    """Return flat list of {lat, lon, elevation} dicts for the Leaflet heatmap."""
    e = elevation_data["elevations"]
    lats = elevation_data["lats"]
    lons = elevation_data["lons"]
    result = []
    for i in range(e.shape[0]):
        for j in range(e.shape[1]):
            result.append({
                "lat": round(float(lats[i, j]), 6),
                "lon": round(float(lons[i, j]), 6),
                "elev": round(float(e[i, j]), 2),
            })
    return result


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
