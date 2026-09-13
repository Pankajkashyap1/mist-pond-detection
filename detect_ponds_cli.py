"""
detect_ponds_cli.py
-------------------
Command-line interface (CLI) tool for Smart AI-Based Pond Detection.

Usage:
  python3 detect_ponds_cli.py --input sample_data/sample_satellite_map.jpg --output_dir results/
"""

import argparse
import cv2
import json
import csv
import os
from ai_pond_detector import AIPondDetector
from hydrology_engine import HydrologyEngine
from sample_generator import ensure_sample_images_exist

def main():
    parser = argparse.ArgumentParser(description="Smart AI-Based Pond Detection CLI Tool")
    parser.add_argument("--input", type=str, default=None, help="Path to input satellite/drone image")
    parser.add_argument("--output_dir", type=str, default="results", help="Directory to save output files")
    parser.add_argument("--mpp", type=float, default=0.5, help="Scale in meters per pixel (default: 0.5)")
    parser.add_argument("--sensitivity", type=float, default=0.55, help="Water detection sensitivity (0.1 to 1.0)")
    parser.add_argument("--min_area", type=float, default=20.0, help="Min pond surface area in sq meters")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    input_path = args.input
    if not input_path or not os.path.exists(input_path):
        print("Input path not provided or found. Generating synthetic satellite map...")
        input_path = ensure_sample_images_exist(os.path.join(args.output_dir, "sample_data"))

    print(f"Loading input image: {input_path}")
    image = cv2.imread(input_path)
    if image is None:
        print(f"Error: Unable to load image at {input_path}")
        return

    # Run AI Detection Engine
    detector = AIPondDetector(meters_per_pixel=args.mpp)
    res = detector.detect_ponds(
        image,
        sensitivity=args.sensitivity,
        min_area_sqm=args.min_area
    )

    print("\n==================================================")
    print("      SMART AI POND DETECTION ANALYSIS REPORT     ")
    print("==================================================")
    print(f"Image Source          : {input_path}")
    print(f"Meters per Pixel      : {args.mpp} m/px")
    print(f"Ponds Detected        : {res['total_ponds_detected']}")
    print(f"Total Surface Area    : {res['total_surface_area_sqm']} m² ({res['total_surface_area_hectares']} Hectares)")
    print(f"Total Storage Capacity: {res['total_storage_volume_m3']} m³ ({int(res['total_storage_volume_liters']):,} Liters)")
    print("--------------------------------------------------")

    for pond in res["detected_ponds"]:
        print(f"Pond #{pond['pond_id']} | Type: {pond['pond_type']:<32} | Area: {pond['surface_area_sqm']:>8.1f} m² | Vol: {pond['estimated_volume_m3']:>8.1f} m³ | Quality: {pond['water_quality']}")

    # Save output images
    annotated_path = os.path.join(args.output_dir, "annotated_ponds.jpg")
    mask_path = os.path.join(args.output_dir, "water_mask.png")
    ndwi_path = os.path.join(args.output_dir, "ndwi_map.png")

    cv2.imwrite(annotated_path, res["annotated_image"])
    cv2.imwrite(mask_path, res["water_mask"])
    cv2.imwrite(ndwi_path, res["ndwi_map"])

    print("--------------------------------------------------")
    print(f"Saved annotated result map to : {annotated_path}")
    print(f"Saved water binary mask to    : {mask_path}")
    print(f"Saved NDWI index map to       : {ndwi_path}")

    # Export CSV summary
    csv_path = os.path.join(args.output_dir, "pond_detection_summary.csv")
    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Pond ID", "Type", "Surface Area (sqm)", "Perimeter (m)", "Compactness", "Water Quality", "Est Depth (m)", "Est Volume (m3)", "Confidence"])
        for p in res["detected_ponds"]:
            writer.writerow([
                p["pond_id"], p["pond_type"], p["surface_area_sqm"],
                p["perimeter_m"], p["compactness"], p["water_quality"],
                p["estimated_depth_m"], p["estimated_volume_m3"], p["confidence_score"]
            ])

    print(f"Saved tabular report to       : {csv_path}")
    print("==================================================\n")

if __name__ == "__main__":
    main()
