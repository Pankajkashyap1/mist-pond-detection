import matplotlib.pyplot as plt
import matplotlib.patches as patches

fig, ax = plt.subplots(figsize=(14, 8.5), dpi=300)
ax.set_xlim(0, 14)
ax.set_ylim(0, 8.5)
ax.axis('off')

# Background canvas style
fig.patch.set_facecolor('#0B0F19')
ax.set_facecolor('#0B0F19')

# Header Title
ax.text(7, 8.0, "MIST POND DETECTION PLATFORM -- DETAILED HIGH-LEVEL DESIGN (HLD)", 
        ha='center', va='center', color='#FFFFFF', fontsize=14, fontweight='bold', family='sans-serif')

def draw_box(x, y, w, h, title, subtitle, items, bg_color, border_color):
    rect = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.1,rounding_size=0.15",
                                 facecolor=bg_color, edgecolor=border_color, linewidth=2.0)
    ax.add_patch(rect)
    ax.text(x + w/2, y + h - 0.35, title, ha='center', va='center', color='#FFFFFF', fontsize=10.5, fontweight='bold')
    if subtitle:
        ax.text(x + w/2, y + h - 0.75, subtitle, ha='center', va='center', color='#38BDF8', fontsize=8.5, fontweight='bold')
    detail_text = "\n".join([f"• {it}" for it in items])
    ax.text(x + 0.2, y + (h - 1.0)/2, detail_text, ha='left', va='center', color='#94A3B8', fontsize=8.0, multialignment='left')

# Layer 1: Client GIS Interface Layer
draw_box(0.5, 5.0, 4.0, 2.5, "1. Client GIS Interface Layer", "Frontend UI (Browser)", [
    "Leaflet.js v1.9 GIS Map Engine",
    "Leaflet.draw Polygon Tool",
    "Dynamic Splitter Handle (.resize-handle-bar)",
    "4 Layout Presets (30%, 55%, 75%, 88%)",
    "Visual Overlays: Pond (Green), Catchment (Cyan)"
], "#1E293B", "#00E5FF")

# Layer 2: Load Balancer & Gateway Layer
draw_box(5.0, 5.0, 4.0, 2.5, "2. Gateway & Load Balancer", "Reverse Proxy & Router", [
    "Flask Load Balancer (cluster_load_balancer.py)",
    "Round-Robin Worker Dispatcher",
    "TLS/HTTPS Encrypted SSH Tunnel (localhost.run)",
    "4 Active Worker Clusters (Ports 2257-2260)",
    "Health-Check Monitoring & Auto-Failover"
], "#1E293B", "#3B82F6")

# Layer 3: External API Services
draw_box(9.5, 5.0, 4.0, 2.5, "3. External Data Providers", "Remote REST APIs", [
    "Open-Meteo Historical Climate API (Precipitation)",
    "OpenStreetMap Nominatim Geocoding API",
    "SRTM 30m Global DEM Elevation Tiles",
    "In-Memory Tile & Grid Cache"
], "#1E293B", "#A855F7")

# Layer 4: Hydro-Geological Calculation Engines
draw_box(0.5, 0.8, 4.0, 3.8, "4A. Contour & D8 Engine", "contour_engine.py", [
    "KML/KMZ 3D Point Cloud Parsing",
    "SciPy 2D Grid Interpolation (IDW Fallback)",
    "Chaikin Iso-Contour Line Smoothing",
    "8-Neighbor Steepest Gradient Matrix",
    "D8 Single-Flow Direction Model",
    "Reverse BFS Upstream Catchment Traversal",
    "Drainage Stream Path Generation"
], "#0F172A", "#10B981")

draw_box(5.0, 0.8, 4.0, 3.8, "4B. Suitability Scoring Engine", "suitability_engine.py", [
    "Terrain Elevation Depression Detection",
    "Multi-Factor Scoring Matrix (0-100)",
    "Slope & Gradient Analysis",
    "Water Body & Built-up Area Exclusion Rules",
    "Optimal Pond Center (Lat/Lon) Location",
    "Recommended Excavation Depth (m)",
    "Recommended Surface Area (m²)"
], "#0F172A", "#F59E0B")

draw_box(9.5, 0.8, 4.0, 3.8, "4C. Hydrology & Volume Engine", "hydrology_engine.py", [
    "Historical Rainfall Query & Aggregation",
    "Rational Method Runoff Volume (V = C * R * A)",
    "Runoff Coefficient Assignment (C = 0.30)",
    "Net Water Storage Capacity (m³)",
    "Cropland Irrigation Potential (Hectares)",
    "Evaporation Loss & Seepage Estimation",
    "GeoJSON Payload Formatter"
], "#0F172A", "#EC4899")

# Flow Arrows
def draw_arrow(x1, y1, x2, y2, label=""):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="->", color="#00E5FF", lw=2.0, mutation_scale=16))
    if label:
        ax.text((x1+x2)/2, (y1+y2)/2 + 0.15, label, ha='center', va='center', color='#00E5FF', fontsize=7.5, fontweight='bold')

draw_arrow(4.5, 6.25, 5.0, 6.25, "HTTPS REST")
draw_arrow(9.0, 6.25, 9.5, 6.25, "Async Query")

draw_arrow(5.8, 5.0, 2.5, 4.6, "Dispatch")
draw_arrow(7.0, 5.0, 7.0, 4.6, "Dispatch")
draw_arrow(8.2, 5.0, 11.5, 4.6, "Dispatch")

plt.tight_layout()
plt.savefig("sample_data/high_level_architecture.png", facecolor=fig.get_facecolor(), edgecolor='none', bbox_inches='tight')
print("✔ Detailed High-Level Design diagram saved to sample_data/high_level_architecture.png")
