import matplotlib.pyplot as plt
import matplotlib.patches as patches

fig, ax = plt.subplots(figsize=(16, 11), dpi=300)
ax.set_xlim(0, 16)
ax.set_ylim(0, 11)
ax.axis('off')

# Dark background canvas
fig.patch.set_facecolor('#0B0F19')
ax.set_facecolor('#0B0F19')

# Header Title Block
ax.text(8, 10.45, "MIST POND DETECTION PLATFORM -- SYSTEM ARCHITECTURE & HIGH LEVEL DESIGN (HLD)", 
        ha='center', va='center', color='#FFFFFF', fontsize=14, fontweight='bold', family='sans-serif')
ax.text(8, 10.12, "Multi-Tier Stateless Micro-Architecture with Distributed Load Balancing & Hydrological Computation", 
        ha='center', va='center', color='#38BDF8', fontsize=9.5, fontweight='bold')

def draw_card(x, y, w, h, title, subtitle, bullets, bg_color, border_color, title_color="#FFFFFF"):
    rect = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.15,rounding_size=0.18",
                                 facecolor=bg_color, edgecolor=border_color, linewidth=2.0)
    ax.add_patch(rect)
    ax.text(x + w/2, y + h - 0.3, title, ha='center', va='center', color=title_color, fontsize=10, fontweight='bold')
    if subtitle:
        ax.text(x + w/2, y + h - 0.62, subtitle, ha='center', va='center', color='#94A3B8', fontsize=8.0, fontweight='bold')
    
    start_y = y + h - 0.95
    for i, bullet in enumerate(bullets):
        line_y = start_y - i*0.31
        if bullet.startswith("  "):
            ax.text(x + 0.35, line_y, f"• {bullet.strip()}", ha='left', va='center', color='#CBD5E1', fontsize=7.5)
        elif ":" in bullet and not bullet.startswith("Formula"):
            k, v = bullet.split(":", 1)
            ax.text(x + 0.2, line_y, f"{k}:", ha='left', va='center', color='#38BDF8', fontsize=7.8, fontweight='bold')
            ax.text(x + 0.2 + len(k)*0.10, line_y, v, ha='left', va='center', color='#E2E8F0', fontsize=7.8)
        else:
            ax.text(x + 0.2, line_y, bullet, ha='left', va='center', color='#F1F5F9', fontsize=7.8, fontweight='bold')

# Layer 1: Client GIS Presentation Layer
draw_card(0.4, 6.2, 4.8, 3.6, "TIER 1: CLIENT GIS PRESENTATION LAYER", "Frontend Web User Interface (Browser)", [
    "GIS Engine: Leaflet.js v1.9 + Leaflet.draw",
    "Interactive UI: Dynamic Resizer (.resize-handle-bar)",
    "Viewport Presets: 30%, 55%, 75%, 88%",
    "Layer Controls: Rainbow Iso-Contours & Heat-Dots",
    "Visual Overlays:",
    "  Green Rectangle: Optimal Excavation Site",
    "  Cyan Polygon: Upstream Watershed Catchment",
    "  Blue Lines: Natural Drainage Stream Paths"
], "#1E293B", "#00E5FF", "#00E5FF")

# Layer 2: Load Balancer & API Gateway Layer
draw_card(5.6, 6.2, 4.8, 3.6, "TIER 2: API GATEWAY & LOAD BALANCER", "Reverse Proxy Router (cluster_load_balancer.py)", [
    "Load Balancer: Flask Round-Robin Scheduler",
    "Security: Encrypted TLS/HTTPS SSH Tunnel",
    "Tunnel Protocol: localhost.run / Reverse Proxy",
    "Worker Pool: 4 Distributed Clusters",
    "  Worker Node 1: Port 2257 (Active)",
    "  Worker Node 2: Port 2258 (Active)",
    "  Worker Node 3: Port 2259 (Active)",
    "  Worker Node 4: Port 2260 (Active)",
    "Reliability: Health-Check & Auto-Failover"
], "#1E293B", "#3B82F6", "#3B82F6")

# Layer 3: External Data Providers
draw_card(10.8, 6.2, 4.8, 3.6, "TIER 3: EXTERNAL DATA PROVIDERS", "Remote REST APIs & Geo-Spatial Archives", [
    "Climate Data: Open-Meteo Historical Archive",
    "  Parameters: Daily Precipitation (P_annual mm)",
    "Geocoding API: OpenStreetMap Nominatim",
    "  Reverse Geocoding: Village / District Bounds",
    "Elevation Data: SRTM 30m Global DEM Tiles",
    "Caching Layer: In-Memory Spatial Grid Cache",
    "Data Protocols: Asynchronous JSON / GeoJSON"
], "#1E293B", "#A855F7", "#A855F7")

# Layer 4: Hydro-Geological Calculation Engines
draw_card(0.4, 0.4, 4.8, 5.4, "ENGINE 4A: CONTOUR & D8 FLOW", "contour_engine.py", [
    "Input: 3D Point Cloud (x, y, z) / KML Upload",
    "2D Grid Math: SciPy griddata Interpolation",
    "Fallback Math: Inverse Distance Weighting (IDW)",
    "  Z(x,y) = Σ(w_k * Z_k) / Σ w_k",
    "Contour Gen: Marching Squares + Chaikin Smooth",
    "D8 Direction: 8-Neighbor Slope Gradient",
    "  ΔZ = (Z_center - Z_neighbor) / Distance",
    "Graph Algorithm: Reverse BFS Traversal",
    "  Extracts upstream contributing watershed",
    "Output: Catchment GeoJSON & Stream Vectors"
], "#0F172A", "#10B981", "#10B981")

draw_card(5.6, 0.4, 4.8, 5.4, "ENGINE 4B: SUITABILITY SCORING", "suitability_engine.py", [
    "Multi-Factor Scoring Matrix (0 - 100 Score):",
    "  1. Depression Depth: ΔZ_min valley detection",
    "  2. Slope Score: Terrain gradient analysis",
    "  3. Exclusion Rules: Water/road buffers",
    "Depression Finder: Min local elevation point",
    "Excavation Geometry:",
    "  Optimal Center: Lat/Lon coordinate pair",
    "  Recommended Excavation Depth: 2.0m - 5.0m",
    "  Recommended Surface Area: Calculated m²",
    "Output: Viability Score & Excavation Box"
], "#0F172A", "#F59E0B", "#F59E0B")

draw_card(10.8, 0.4, 4.8, 5.4, "ENGINE 4C: HYDROLOGY & STORAGE", "hydrology_engine.py", [
    "Precipitation Aggregation: Annual rainfall P",
    "Runoff Formula: Rational Method",
    "  V_runoff = C * (P_annual / 1000) * A_catchment",
    "Runoff Coefficient: C = 0.30 (Semi-arid soil)",
    "Storage Capacity: Net volume V (m³)",
    "Crop Potential: Farmland irrigation area",
    "  Irrigation (ha) = V_storage / 5000 m³/ha",
    "Loss Models: Seepage & Evaporation Factor",
    "Output: Hydrological Metrics Payload"
], "#0F172A", "#EC4899", "#EC4899")

# Connective Flow Arrows
def draw_flow_arrow(x1, y1, x2, y2, label=""):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="->", color="#00E5FF", lw=2.2, mutation_scale=16))
    if label:
        ax.text((x1+x2)/2, (y1+y2)/2 + 0.15, label, ha='center', va='center', color='#00E5FF', fontsize=7.8, fontweight='bold')

draw_flow_arrow(5.2, 8.0, 5.6, 8.0, "REST Payload")
draw_flow_arrow(10.4, 8.0, 10.8, 8.0, "Async Query")

draw_flow_arrow(6.4, 6.2, 2.8, 5.8, "Dispatch")
draw_flow_arrow(8.0, 6.2, 8.0, 5.8, "Dispatch")
draw_flow_arrow(9.6, 6.2, 13.2, 5.8, "Dispatch")

plt.tight_layout()
plt.savefig("sample_data/high_level_architecture.png", facecolor=fig.get_facecolor(), edgecolor='none', bbox_inches='tight')
print("✔ Refined High-Level Design diagram generated at sample_data/high_level_architecture.png")
