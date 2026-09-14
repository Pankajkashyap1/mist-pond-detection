"""
contour_engine.py
-----------------
Core Engine for KML/KMZ Contour Processing, DEM Generation, D8 Hydrological Terrain Analysis,
Optimal Pond Location Discovery, and Automated Catchment Delineation.

Author: Pankaj Kashyap
Project: Mist Pond Detection System
"""

import io
import math
import re
import time
import zipfile
import xml.etree.ElementTree as ET
import numpy as np
import scipy.ndimage
from scipy.interpolate import griddata

try:
    from shapely.geometry import MultiPoint, Polygon, mapping
    SHAPELY_AVAILABLE = True
except ImportError:
    SHAPELY_AVAILABLE = False


class ContourParser:
    """Parses KML and KMZ contour map files and extracts 3D spatial geometries."""

    @staticmethod
    def parse_file(file_bytes: bytes, filename: str) -> dict:
        """
        Parses KML or KMZ file bytes and extracts point cloud and line geometries.
        """
        filename_lower = filename.lower()
        if filename_lower.endswith(".kmz") or file_bytes[:4] == b"PK\x03\x04":
            with zipfile.ZipFile(io.BytesIO(file_bytes), "r") as z:
                kml_files = [f for f in z.namelist() if f.lower().endswith(".kml")]
                if not kml_files:
                    raise ValueError("No valid KML file found inside the uploaded KMZ archive.")
                kml_content = z.read(kml_files[0])
                root = ET.fromstring(kml_content)
        else:
            root = ET.fromstring(file_bytes.decode("utf-8", errors="replace"))

        def get_tag_name(el):
            return el.tag.split("}")[-1] if "}" in el.tag else el.tag

        all_points = []
        contour_lines = []

        # Find all placemarks
        placemarks = [el for el in root.findall(".//") if get_tag_name(el) == "Placemark"]

        for pm in placemarks:
            elev = None
            # 1. Parse elevation from <name>
            name_el = None
            for child in pm:
                if get_tag_name(child) == "name":
                    name_el = child
                    break
            if name_el is not None and name_el.text:
                txt = name_el.text.strip()
                try:
                    elev = float(txt)
                except ValueError:
                    match = re.search(r"[-+]?\d*\.\d+|\d+", txt)
                    if match:
                        elev = float(match.group())

            # 2. Check ExtendedData / SimpleData if elev not found
            if elev is None:
                for sd in pm.findall(".//"):
                    if get_tag_name(sd) == "SimpleData" and sd.text:
                        sd_name = sd.attrib.get("name", "").lower()
                        if sd_name in ("id", "elevation", "elev", "level", "contour", "z"):
                            try:
                                elev = float(sd.text.strip())
                                break
                            except ValueError:
                                pass

            # 3. Check Description regex if elev still None
            if elev is None:
                for child in pm:
                    if get_tag_name(child) == "description" and child.text:
                        match = re.search(r"(?:elevation|contour|alt|z)\s*[:=]?\s*([-+]?\d+\.?\d*)", child.text, re.IGNORECASE)
                        if match:
                            elev = float(match.group(1))
                            break

            # Parse line coordinates
            coords_str = ""
            for child in pm.findall(".//"):
                if get_tag_name(child) in ("LineString", "Polygon", "Point"):
                    for c_el in child.findall(".//"):
                        if get_tag_name(c_el) == "coordinates" and c_el.text:
                            coords_str = c_el.text.strip()
                            break

            if not coords_str:
                continue

            line_pts = []
            for tuple_str in coords_str.split():
                parts = tuple_str.split(",")
                if len(parts) >= 2:
                    try:
                        lon = float(parts[0])
                        lat = float(parts[1])
                        pt_elev = elev
                        # Use 3rd coordinate only if elev was not found in metadata
                        if pt_elev is None and len(parts) >= 3:
                            try:
                                candidate_z = float(parts[2])
                                if candidate_z != 0:
                                    pt_elev = candidate_z
                            except ValueError:
                                pass

                        if pt_elev is not None:
                            all_points.append((lon, lat, pt_elev))
                            line_pts.append((lon, lat, pt_elev))
                    except ValueError:
                        pass

            if line_pts and elev is not None:
                contour_lines.append({
                    "elevation": elev,
                    "points": line_pts,
                    "point_count": len(line_pts)
                })

        if not all_points:
            raise ValueError("No valid geographic 3D contour points could be extracted from the file.")

        # Outlier filtering using Interquartile Range (IQR) to remove dummy boundary points
        elev_vals = np.array([p[2] for p in all_points])
        q25, q75 = np.percentile(elev_vals, [25, 75])
        iqr = q75 - q25
        valid_mask = (elev_vals >= q25 - 3.0 * iqr) & (elev_vals <= q75 + 3.0 * iqr)

        filtered_points = [all_points[i] for i in range(len(all_points)) if valid_mask[i]]
        if not filtered_points:
            filtered_points = all_points

        lons = [p[0] for p in filtered_points]
        lats = [p[1] for p in filtered_points]
        elevs = [p[2] for p in filtered_points]

        # Calculate contour interval
        unique_elevs = sorted(list(set(elevs)))
        if len(unique_elevs) > 1:
            diffs = np.diff(unique_elevs)
            contour_interval = float(np.min(diffs[diffs > 0])) if np.any(diffs > 0) else 1.0
        else:
            contour_interval = 1.0

        return {
            "total_points": len(filtered_points),
            "total_contours": len(contour_lines),
            "min_elevation": float(np.min(elevs)),
            "max_elevation": float(np.max(elevs)),
            "contour_interval": float(contour_interval),
            "bounding_box": {
                "min_lat": float(np.min(lats)),
                "max_lat": float(np.max(lats)),
                "min_lon": float(np.min(lons)),
                "max_lon": float(np.max(lons))
            },
            "points": filtered_points,
            "contour_lines": contour_lines
        }


class ContourAnalysisEngine:
    """Core Engine for DEM Interpolation, D8 Hydrology Routing, Pond Location & Catchment Estimation."""

    @staticmethod
    def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        R = 6371000.0  # Earth radius in metres
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlam = math.radians(lon2 - lon1)
        a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2.0) ** 2
        return 2.0 * R * math.asin(math.sqrt(a))

    @classmethod
    def analyze_terrain(
        cls,
        parsed_kml: dict,
        annual_rainfall_mm: float = 1100.0,
        runoff_coefficient: float = 0.30,
        grid_resolution: int = 80
    ) -> dict:
        """
        Executes full hydrological analysis:
        1. Interpolates 3D contour points onto a Digital Elevation Model (DEM) grid.
        2. Computes terrain slope, aspect, and D8 flow directions.
        3. Computes D8 Flow Accumulation matrix to identify natural streams.
        4. Finds the optimal pond location (local elevation minimum with high drainage).
        5. Performs reverse D8 flow tracing to delineate the exact catchment area.
        6. Computes catchment metrics and water harvesting potential.
        """
        start_time = time.time()

        points = parsed_kml["points"]
        bbox = parsed_kml["bounding_box"]
        min_lat, max_lat = bbox["min_lat"], bbox["max_lat"]
        min_lon, max_lon = bbox["min_lon"], bbox["max_lon"]

        lons = np.array([p[0] for p in points])
        lats = np.array([p[1] for p in points])
        elevs = np.array([p[2] for p in points])

        # ── 1. Create Regular Grid DEM
        GRID_N = grid_resolution
        grid_lons = np.linspace(min_lon, max_lon, GRID_N)
        grid_lats = np.linspace(min_lat, max_lat, GRID_N)
        mesh_lon, mesh_lat = np.meshgrid(grid_lons, grid_lats)

        # Downsample points for fast cubic/linear interpolation if dataset is huge
        if len(points) > 15000:
            sub_idx = np.random.choice(len(points), size=15000, replace=False)
            s_lons, s_lats, s_elevs = lons[sub_idx], lats[sub_idx], elevs[sub_idx]
        else:
            s_lons, s_lats, s_elevs = lons, lats, elevs

        dem = griddata((s_lons, s_lats), s_elevs, (mesh_lon, mesh_lat), method="linear")

        # Fill boundary NaNs with nearest neighbor interpolation
        nan_mask = np.isnan(dem)
        if np.any(nan_mask):
            dem_nearest = griddata((s_lons, s_lats), s_elevs, (mesh_lon, mesh_lat), method="nearest")
            dem[nan_mask] = dem_nearest[nan_mask]

        # Smooth DEM slightly to eliminate noise artifacts
        dem = scipy.ndimage.gaussian_filter(dem, sigma=1.0)

        # Compute cell dimensions in meters
        dy = cls.haversine_m(min_lat, min_lon, max_lat, min_lon) / (GRID_N - 1)
        dx = cls.haversine_m(min_lat, min_lon, min_lat, max_lon) / (GRID_N - 1)
        cell_area_sqm = dx * dy

        # ── 2. Slope & Aspect Calculations
        gy, gx = np.gradient(dem, dy, dx)
        slope_rad = np.arctan(np.sqrt(gx ** 2 + gy ** 2))
        slope_deg = np.degrees(slope_rad)
        aspect_deg = (np.degrees(np.arctan2(-gx, gy)) + 360) % 360

        # ── 3. D8 Flow Direction & Flow Accumulation
        rows, cols = dem.shape
        flow_dir = np.full((rows, cols), -1, dtype=int)
        d8_offsets = [(-1, 0), (-1, 1), (0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1)]
        d8_distances = [dy, math.sqrt(dx**2 + dy**2), dx, math.sqrt(dx**2 + dy**2),
                        dy, math.sqrt(dx**2 + dy**2), dx, math.sqrt(dx**2 + dy**2)]

        for r in range(rows):
            for c in range(cols):
                z_curr = dem[r, c]
                max_slope = 0.0
                best_dir = -1
                for idx, ((dr, dc), dist) in enumerate(zip(d8_offsets, d8_distances)):
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < rows and 0 <= nc < cols:
                        dz = z_curr - dem[nr, nc]
                        if dz > 0:
                            s = dz / dist
                            if s > max_slope:
                                max_slope = s
                                best_dir = idx
                flow_dir[r, c] = best_dir

        # Flow Accumulation Engine
        flow_acc = np.ones((rows, cols), dtype=float)
        sorted_indices = np.argsort(dem.ravel())[::-1]  # Highest to lowest elevation

        for idx in sorted_indices:
            r = idx // cols
            c = idx % cols
            fdir = flow_dir[r, c]
            if fdir != -1:
                dr, dc = d8_offsets[fdir]
                nr, nc = r + dr, c + dc
                if 0 <= nr < rows and 0 <= nc < cols:
                    flow_acc[nr, nc] += flow_acc[r, c]

        # ── 4. Identify Optimal Pond Location
        min_elev = float(dem.min())
        elev_range = max(1.0, float(dem.max()) - min_elev)
        norm_elev = (dem - min_elev) / elev_range

        # Suitability Score Grid: High Flow Acc, Low Elevation, Gentle Slope
        score_grid = (flow_acc / flow_acc.max()) * 0.5 + (1.0 - norm_elev) * 0.35 + (1.0 / (slope_deg + 1.0)) * 0.15

        # Ignore outer grid border cells for pond placement
        border_margin = max(2, GRID_N // 15)
        score_grid[:border_margin, :] = 0
        score_grid[-border_margin:, :] = 0
        score_grid[:, :border_margin] = 0
        score_grid[:, -border_margin:] = 0

        opt_idx = int(np.argmax(score_grid))
        opt_r, opt_c = opt_idx // cols, opt_idx % cols
        opt_lat = float(grid_lats[opt_r])
        opt_lon = float(grid_lons[opt_c])
        opt_elev = float(dem[opt_r, opt_c])
        opt_slope = float(slope_deg[opt_r, opt_c])

        # ── 5. Reverse D8 Tracing for Catchment Delineation
        upstream_cells = set()
        queue = [(opt_r, opt_c)]
        upstream_cells.add((opt_r, opt_c))

        while queue:
            curr_r, curr_c = queue.pop(0)
            for idx, (dr, dc) in enumerate(d8_offsets):
                nr, nc = curr_r - dr, curr_c - dc
                if 0 <= nr < rows and 0 <= nc < cols and (nr, nc) not in upstream_cells:
                    if flow_dir[nr, nc] == idx:  # Neighbor flows into curr
                        upstream_cells.add((nr, nc))
                        queue.append((nr, nc))

        # Catchment Metrics
        catchment_cell_count = len(upstream_cells)
        catchment_area_sqm = round(catchment_cell_count * cell_area_sqm, 2)
        catchment_area_ha = round(catchment_area_sqm / 10000.0, 4)

        upstream_coords = [(float(grid_lons[c]), float(grid_lats[r])) for (r, c) in upstream_cells]
        upstream_elevs = [float(dem[r, c]) for (r, c) in upstream_cells]
        upstream_slopes = [float(slope_deg[r, c]) for (r, c) in upstream_cells]

        catchment_min_elev = round(float(np.min(upstream_elevs)), 2)
        catchment_max_elev = round(float(np.max(upstream_elevs)), 2)
        catchment_avg_slope = round(float(np.mean(upstream_slopes)), 2)

        # Build Catchment Boundary Polygon GeoJSON
        catchment_polygon_geojson = cls._generate_polygon_geojson(upstream_coords)

        # Recommended Pond Dimensions
        rec_pond_surface_sqm = round(min(12000.0, max(1200.0, catchment_area_sqm * 0.04)), 2)
        rec_pond_depth_m = round(min(3.5, max(1.8, 1.5 + (catchment_max_elev - opt_elev) * 0.08)), 2)
        rec_pond_volume_m3 = round(rec_pond_surface_sqm * rec_pond_depth_m * 0.75, 2)
        pond_polygon_geojson = cls._generate_pond_boundary_geojson(opt_lat, opt_lon, rec_pond_surface_sqm)

        # ── 6. Hydrology & Water Harvesting Estimation
        rainfall_m = annual_rainfall_mm / 1000.0
        annual_runoff_m3 = round(runoff_coefficient * rainfall_m * catchment_area_sqm, 2)
        irrigation_support_ha = round(annual_runoff_m3 / 5000.0, 2)
        excavation_m3 = round(rec_pond_volume_m3 * 0.85, 2)
        est_cost_inr = round(excavation_m3 * 350, 0)
        drought_resilience_score = min(100, max(30, int((annual_runoff_m3 / (rec_pond_volume_m3 + 1e-5)) * 40)))

        # Stream / Drainage Network GeoJSON
        stream_threshold = float(np.percentile(flow_acc, 92))
        stream_lines_geojson = cls._extract_stream_lines_geojson(flow_acc, flow_dir, grid_lats, grid_lons, stream_threshold, d8_offsets)

        exec_time_sec = round(time.time() - start_time, 3)

        return {
            "status": "success",
            "execution_time_seconds": exec_time_sec,
            "contour_summary": {
                "total_contours": parsed_kml["total_contours"],
                "total_points_parsed": parsed_kml["total_points"],
                "min_elevation_m": parsed_kml["min_elevation"],
                "max_elevation_m": parsed_kml["max_elevation"],
                "contour_interval_m": parsed_kml["contour_interval"],
                "bounding_box": parsed_kml["bounding_box"]
            },
            "suitable_pond_location": {
                "latitude": round(opt_lat, 6),
                "longitude": round(opt_lon, 6),
                "elevation_m": round(opt_elev, 2),
                "slope_deg": round(opt_slope, 2),
                "recommended_surface_area_sqm": rec_pond_surface_sqm,
                "recommended_depth_m": rec_pond_depth_m,
                "gross_storage_capacity_m3": rec_pond_volume_m3,
                "suitability_score": min(98.5, round(75.0 + (10.0 / (opt_slope + 0.5)) + (catchment_area_ha * 0.5), 1)),
                "pond_boundary_geojson": pond_polygon_geojson
            },
            "catchment_information": {
                "catchment_area_sqm": catchment_area_sqm,
                "catchment_area_hectares": catchment_area_ha,
                "min_elevation_m": catchment_min_elev,
                "max_elevation_m": catchment_max_elev,
                "avg_slope_deg": catchment_avg_slope,
                "catchment_cell_count": catchment_cell_count,
                "catchment_boundary_geojson": catchment_polygon_geojson
            },
            "hydrology_metrics": {
                "annual_rainfall_mm": annual_rainfall_mm,
                "runoff_coefficient": runoff_coefficient,
                "estimated_annual_runoff_m3": annual_runoff_m3,
                "irrigation_support_potential_ha": irrigation_support_ha,
                "excavation_required_m3": excavation_m3,
                "estimated_cost_inr": int(est_cost_inr),
                "drought_resilience_score": drought_resilience_score
            },
            "visualization": {
                "streams_geojson": stream_lines_geojson,
                "dem_grid_resolution": [GRID_N, GRID_N]
            }
        }

    @staticmethod
    def _generate_polygon_geojson(points: list) -> dict:
        """Generates GeoJSON polygon from point set using Convex Hull or bounding polygon."""
        if not points:
            return None
        if SHAPELY_AVAILABLE and len(points) >= 3:
            try:
                hull = MultiPoint(points).convex_hull
                if isinstance(hull, Polygon):
                    return mapping(hull)
            except Exception:
                pass

        # Fallback Bounding Box Polygon
        lons = [p[0] for p in points]
        lats = [p[1] for p in points]
        min_lo, max_lo = min(lons), max(lons)
        min_la, max_la = min(lats), max(lats)
        return {
            "type": "Polygon",
            "coordinates": [[
                [min_lo, min_la], [max_lo, min_la],
                [max_lo, max_la], [min_lo, max_la],
                [min_lo, min_la]
            ]]
        }

    @staticmethod
    def _generate_pond_boundary_geojson(lat: float, lon: float, surface_area_sqm: float) -> dict:
        """Generates a rectangular GeoJSON polygon around the target lat/lon centroid."""
        side_length_m = math.sqrt(surface_area_sqm)
        half_m = side_length_m / 2.0
        lat_offset = half_m / 111000.0
        lon_offset = half_m / (111000.0 * math.cos(math.radians(lat)))

        return {
            "type": "Polygon",
            "coordinates": [[
                [round(lon - lon_offset, 6), round(lat - lat_offset, 6)],
                [round(lon + lon_offset, 6), round(lat - lat_offset, 6)],
                [round(lon + lon_offset, 6), round(lat + lat_offset, 6)],
                [round(lon - lon_offset, 6), round(lat + lat_offset, 6)],
                [round(lon - lon_offset, 6), round(lat - lat_offset, 6)]
            ]]
        }

    @staticmethod
    def _extract_stream_lines_geojson(flow_acc: np.ndarray, flow_dir: np.ndarray, grid_lats: np.ndarray, grid_lons: np.ndarray, threshold: float, d8_offsets: list) -> dict:
        """Extracts high flow accumulation drainage stream channels as GeoJSON LineStrings."""
        rows, cols = flow_acc.shape
        features = []

        for r in range(rows):
            for c in range(cols):
                if flow_acc[r, c] >= threshold:
                    fdir = flow_dir[r, c]
                    if fdir != -1:
                        dr, dc = d8_offsets[fdir]
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < rows and 0 <= nc < cols:
                            features.append({
                                "type": "Feature",
                                "geometry": {
                                    "type": "LineString",
                                    "coordinates": [
                                        [float(grid_lons[c]), float(grid_lats[r])],
                                        [float(grid_lons[nc]), float(grid_lats[nr])]
                                    ]
                                },
                                "properties": {"flow_accumulation": float(flow_acc[r, c])}
                            })
        return {
            "type": "FeatureCollection",
            "features": features[:150]  # Limit top 150 stream segments for fast map rendering
        }
