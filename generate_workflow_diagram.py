import matplotlib.pyplot as plt
import matplotlib.patches as patches

fig, ax = plt.subplots(figsize=(15, 8.0), dpi=300)
ax.set_xlim(0, 15)
ax.set_ylim(0, 8.0)
ax.axis('off')

# Background canvas style
fig.patch.set_facecolor('#0F172A')
ax.set_facecolor('#0F172A')

# Header Title
ax.text(7.5, 7.5, "MIST POND DETECTION PLATFORM -- DETAILED END-TO-END WORKFLOW PIPELINE", 
        ha='center', va='center', color='#FFFFFF', fontsize=14, fontweight='bold', family='sans-serif')

def draw_phase(x, y, w, h, phase_num, title, items, bg_color, border_color):
    rect = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.12,rounding_size=0.15",
                                 facecolor=bg_color, edgecolor=border_color, linewidth=2.0)
    ax.add_patch(rect)
    ax.text(x + w/2, y + h - 0.35, f"PHASE {phase_num}: {title}", ha='center', va='center', color='#FFFFFF', fontsize=10.0, fontweight='bold')
    detail_text = "\n".join([f"• {it}" for it in items])
    ax.text(x + 0.25, y + (h - 0.8)/2, detail_text, ha='left', va='center', color='#CBD5E1', fontsize=8.0, multialignment='left')

# Phase 1: User Request & GIS Initialization
draw_phase(0.4, 0.8, 3.3, 6.2, "1", "User Input & Map GIS", [
    "User selects Village / Land Area",
    "Option A: Draw Polygon via Leaflet",
    "Option B: Upload 1m KML/KMZ File",
    "Viewport bounds emitted to REST API",
    "Drag splitter handle (.resize-handle-bar)",
    "Map height preset selected (30%-88%)",
    "Client payload: Lat/Lon GeoJSON"
], "#1E293B", "#00E5FF")

# Phase 2: DEM Grid Interpolation & Sampling
draw_phase(4.0, 0.8, 3.3, 6.2, "2", "Elevation & DEM Grid", [
    "Receive GeoJSON coordinate bounds",
    "Query SRTM 30m elevation DEM tile",
    "Parse KML 3D point cloud (x, y, z)",
    "SciPy 2D griddata interpolation",
    "Inverse Distance Weighting (IDW)",
    "Generate N x M elevation matrix Z",
    "Compute slope & aspect matrices"
], "#1E293B", "#3B82F6")

# Phase 3: D8 Flow & Catchment Delineation
draw_phase(7.6, 0.8, 3.3, 6.2, "3", "D8 Flow Routing & BFS", [
    "Compute 8-neighbor steepest slope",
    "Construct D8 flow direction matrix",
    "Sort elevation cells descending",
    "Accumulate flow count per cell",
    "Identify outlet depression point",
    "Reverse BFS graph traversal",
    "Delineate upstream catchment polygon"
], "#1E293B", "#10B981")

# Phase 4: Hydrology, Suitability & Visual Render
draw_phase(11.2, 0.8, 3.4, 6.2, "4", "Hydro Math & GIS Render", [
    "Fetch Open-Meteo precipitation",
    "Rational runoff V = C * R * A (C=0.30)",
    "Compute net water volume (m³)",
    "Calculate irrigation potential (ha)",
    "Multi-factor site score (0-100)",
    "Render green excavation pond box",
    "Overlay cyan catchment & blue streams"
], "#1E293B", "#F59E0B")

# Arrows helper
def draw_flow_arrow(x1, y1, x2, y2):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="->", color="#00E5FF", lw=2.4, mutation_scale=20))

draw_flow_arrow(3.7, 3.9, 4.0, 3.9)
draw_flow_arrow(7.3, 3.9, 7.6, 3.9)
draw_flow_arrow(10.9, 3.9, 11.2, 3.9)

plt.tight_layout()
plt.savefig("sample_data/workflow_diagram.png", facecolor=fig.get_facecolor(), edgecolor='none', bbox_inches='tight')
print("✔ Detailed Workflow diagram saved to sample_data/workflow_diagram.png")
