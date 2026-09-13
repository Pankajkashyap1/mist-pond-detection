"""
sample_generator.py
-------------------
Generates synthetic high-resolution satellite / drone imagery of rural farmland
containing ponds, agricultural fields, vegetation, and roads for AI model testing.
"""

import cv2
import numpy as np
import os
import random

def generate_synthetic_satellite_image(
    width: int = 1024,
    height: int = 768,
    num_ponds: int = 4,
    seed: int = 42
) -> np.ndarray:
    """
    Synthesizes a realistic aerial satellite view of a village landscape with farm ponds.
    """
    np.random.seed(seed)
    random.seed(seed)

    # 1. Base terrain background (Agricultural soil / dry vegetation green-brown canvas)
    base_color = np.array([55, 110, 70], dtype=np.uint8) # BGR
    img = np.full((height, width, 3), base_color, dtype=np.uint8)

    # Add Perlin-like texture / noise using Perlin/Gaussian blur layers
    noise = np.random.randint(-25, 25, (height, width, 3), dtype=np.int16)
    img = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    img = cv2.GaussianBlur(img, (9, 9), 0)

    # 2. Draw agricultural field patches (polygons with varying crop colors)
    field_colors = [
        (40, 140, 85),   # Bright Green crop field
        (30, 95, 50),    # Dark Green lush crop field
        (70, 160, 175),  # Dry Golden soil field
        (50, 105, 130),  # Terracotta tilled soil
        (45, 125, 95)    # Light Green meadow
    ]

    grid_size = 4
    dx = width // grid_size
    dy = height // grid_size

    for i in range(grid_size):
        for j in range(grid_size):
            pt1 = (i * dx + random.randint(5, 25), j * dy + random.randint(5, 25))
            pt2 = ((i + 1) * dx - random.randint(5, 25), (j + 1) * dy - random.randint(5, 25))
            color = random.choice(field_colors)
            cv2.rectangle(img, pt1, pt2, color, -1)
            # Add field boundary border
            cv2.rectangle(img, pt1, pt2, (30, 70, 40), 2)

    # 3. Draw rural dirt roads / paths connecting fields
    cv2.line(img, (0, height // 3), (width, height // 3 + 40), (100, 140, 165), 8)
    cv2.line(img, (width // 2, 0), (width // 2 - 30, height), (100, 140, 165), 6)

    # 4. Generate distinct Ponds
    pond_specs = [
        {"type": "rectangular_farm", "size": (120, 90), "pos": (width // 5, height // 4), "color": (190, 110, 25)}, # Deep Blue
        {"type": "oval_lake", "size": (180, 130), "pos": (3 * width // 4, height // 3), "color": (150, 130, 30)},   # Cyan-Blue
        {"type": "algae_pond", "size": (110, 110), "pos": (width // 3, 3 * height // 4), "color": (40, 170, 60)},  # Emerald Green Algae
        {"type": "turbid_tank", "size": (140, 95), "pos": (4 * width // 5, 4 * height // 5), "color": (50, 110, 180)} # Muddy Brown
    ]

    for spec in pond_specs[:num_ponds]:
        px, py = spec["pos"]
        w_p, h_p = spec["size"]
        color = spec["color"]

        if spec["type"] == "rectangular_farm":
            # Rectangular farm pond with embankments
            cv2.rectangle(img, (px - 10, py - 10), (px + w_p + 10, py + h_p + 10), (70, 110, 80), -1) # Bank
            cv2.rectangle(img, (px, py), (px + w_p, py + h_p), color, -1)
            # Water texture / ripple lines
            cv2.rectangle(img, (px + 5, py + 5), (px + w_p - 5, py + h_p - 5), 
                          (min(255, color[0] + 30), min(255, color[1] + 30), min(255, color[2] + 30)), 1)
        elif spec["type"] == "oval_lake":
            # Oval natural pond
            cv2.ellipse(img, (px, py), (w_p // 2 + 12, h_p // 2 + 12), 15, 0, 360, (60, 100, 70), -1)
            cv2.ellipse(img, (px, py), (w_p // 2, h_p // 2), 15, 0, 360, color, -1)
        else:
            # Irregular / Algae / Turbid pond shape
            pts = np.array([
                [px, py], [px + w_p, py + 15], [px + w_p - 10, py + h_p], 
                [px + 20, py + h_p + 15], [px - 15, py + h_p // 2]
            ], np.int32)
            pts = pts.reshape((-1, 1, 2))
            cv2.fillPoly(img, [pts], color)

    # 5. Scatter Tree Clusters around ponds and fields
    for _ in range(70):
        tx = random.randint(10, width - 10)
        ty = random.randint(10, height - 10)
        r_tree = random.randint(6, 16)
        # Tree shadow
        cv2.circle(img, (tx + 3, ty + 3), r_tree, (20, 40, 25), -1)
        # Tree canopy
        cv2.circle(img, (tx, ty), r_tree, (random.randint(20, 50), random.randint(120, 180), random.randint(30, 70)), -1)

    return img

def ensure_sample_images_exist(output_dir: str):
    os.makedirs(output_dir, exist_ok=True)
    sample_path = os.path.join(output_dir, "sample_satellite_map.jpg")
    if not os.path.exists(sample_path):
        img = generate_synthetic_satellite_image()
        cv2.imwrite(sample_path, img)
        print(f"Generated sample satellite imagery at: {sample_path}")
    return sample_path

if __name__ == "__main__":
    path = ensure_sample_images_exist("./sample_data")
    print("Sample generation complete:", path)
