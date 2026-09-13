"""
hydrology_engine.py
-------------------
Hydrological Modeling & Water Management Engine for Pond Planning.

Implements:
- Rational Method Runoff Computation: Q = C * P * A
- Crop Water Requirement & Irrigation Supply Sizing
- Evaporation & Seepage Loss Calculation
- Recommended Pond Depth and Footprint Optimization
- Annual Water Harvesting Potential & Drought Resilience Score
"""

import math
from typing import Dict, Any

class HydrologyEngine:
    # Typical Runoff Coefficients (C) for different terrain types
    RUNOFF_COEFFICIENTS = {
        "Agricultural Land (Loam/Clay)": 0.30,
        "Sandy Soil Field": 0.15,
        "Hilly / Rocky Catchment": 0.55,
        "Urban / Impervious Area": 0.80,
        "Forest / Dense Vegetation": 0.20
    }

    @staticmethod
    def calculate_runoff(
        catchment_area_sqm: float,
        annual_rainfall_mm: float,
        terrain_type: str = "Agricultural Land (Loam/Clay)",
        custom_c: float = None
    ) -> float:
        """
        Calculate annual runoff volume using the Rational Method:
        Q = C * (P / 1000) * A
        :return: Runoff volume in cubic meters (m³)
        """
        c = custom_c if custom_c is not None else HydrologyEngine.RUNOFF_COEFFICIENTS.get(terrain_type, 0.30)
        rainfall_m = annual_rainfall_mm / 1000.0
        runoff_m3 = c * rainfall_m * catchment_area_sqm
        return round(runoff_m3, 2)

    @staticmethod
    def plan_optimal_pond(
        target_water_volume_m3: float,
        available_surface_area_sqm: float = None,
        max_safe_depth_m: float = 3.5,
        avg_evaporation_mm_year: float = 1400.0,
        avg_seepage_mm_day: float = 3.0
    ) -> Dict[str, Any]:
        """
        Compute optimal depth, dimensions, and net water availability taking losses into account.
        """
        # Account for annual evaporation and seepage losses
        # Annual loss (meters) = (evaporation_mm + seepage_mm_day * 365) / 1000
        annual_loss_m = (avg_evaporation_mm_year + avg_seepage_mm_day * 365.0) / 1000.0
        
        # Gross water required to deliver net volume target
        # Gross = Target / (1 - Loss Factor)
        loss_factor = min(0.35, annual_loss_m * 0.12)
        gross_volume_m3 = target_water_volume_m3 * (1.0 + loss_factor)

        if available_surface_area_sqm and available_surface_area_sqm > 0:
            req_depth = gross_volume_m3 / available_surface_area_sqm
            depth = min(max_safe_depth_m, max(1.2, req_depth))
            surface_area = max(available_surface_area_sqm, gross_volume_m3 / depth)
        else:
            depth = min(max_safe_depth_m, max(2.0, gross_volume_m3 / 5000.0))
            surface_area = gross_volume_m3 / depth

        # Rectangular aspect ratio (3:2 length to width)
        width = math.sqrt(surface_area / 1.5)
        length = 1.5 * width

        # Irrigation potential (1 hectare of paddy/wheat requires ~5,000 m³ water per season)
        irrigation_hectares = round(target_water_volume_m3 / 5000.0, 2)

        # Resilience score (0-100)
        resilience_score = min(100, max(20, int((target_water_volume_m3 / (gross_volume_m3 + 1e-5)) * 100)))

        return {
            "target_water_volume_m3": round(target_water_volume_m3, 2),
            "gross_required_volume_m3": round(gross_volume_m3, 2),
            "recommended_depth_m": round(depth, 2),
            "recommended_surface_area_sqm": round(surface_area, 2),
            "recommended_length_m": round(length, 2),
            "recommended_width_m": round(width, 2),
            "estimated_annual_loss_m3": round(gross_volume_m3 - target_water_volume_m3, 2),
            "irrigation_support_hectares": irrigation_hectares,
            "drought_resilience_score": resilience_score
        }

if __name__ == "__main__":
    eng = HydrologyEngine()
    print("Runoff test:", eng.calculate_runoff(50000, 1100))
