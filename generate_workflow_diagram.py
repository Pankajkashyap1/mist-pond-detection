import matplotlib.pyplot as plt
import matplotlib.patches as patches

fig, ax = plt.subplots(figsize=(16, 11), dpi=300)
ax.set_xlim(0, 16)
ax.set_ylim(0, 11)
ax.axis('off')

# Dark background canvas
fig.patch.set_facecolor('#0F172A')
ax.set_facecolor('#0F172A')

# Header Title Block
ax.text(8, 10.4, "MIST POND DETECTION PLATFORM -- DETAILED END-TO-END OPERATIONAL WORKFLOW", 
        ha='center', va='center', color='#FFFFFF', fontsize=15, fontweight='bold', family='sans-serif')
ax.text(8, 10.05, "Sequential Data Pipeline: From Spatial Input & DEM Grid Sampling to D8 BFS Delineation & GIS Render", 
        ha='center', va='center', color='#00E5FF', fontsize=10, fontweight='bold')

def draw_phase_card(x, y, w, h, phase_num, title, subtitle, bullets, bg_color, border_color):
    rect = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.15,rounding_size=0.2",
                                 facecolor=bg_color, edgecolor=border_color, linewidth=2.2)
    ax.add_patch(rect)
    ax.text(x + w/2, y + h - 0.4, f"PHASE {phase_num}: {title}", ha='center', va='center', color='#FFFFFF', fontsize=11, fontweight='bold')
    ax.text(x + w/2, y + h - 0.75, subtitle, ha='center', va='center', color=border_color, fontsize=8.5, fontweight='bold')
    
    start_y = y + h - 1.15
    for i, bullet in enumerate(bullets):
        if bullet.startswith("  "):
            ax.text(x + 0.35, start_y - i*0.36, bullet.strip(), ha='left', va='center', color='#E2E8F0', fontsize=7.8)
        elif ":" in bullet:
            k, v = bullet.split(":", 1)
            ax.text(x + 0.2, start_y - i*0.36, f"{k}:", ha='left', va='center', color=border_color, fontsize=8.0, fontweight='bold')
            ax.text(x + 0.2 + len(k)*0.11, start_y - i*0.36, v, ha='left', va='center', color='#F1F5F9', fontsize=8.0)
        else:
            ax.text(x + 0.2, start_y - i*0.36, bullet, ha='left', va='center', color='#FFFFFF', fontsize=8.0, fontweight='bold')

# Phase 1: User GIS Input
draw_phase_card(0.4, 0.6, 3.6, 9.0, "1", "USER GIS INPUT & MAP SETUP", "Frontend GIS Map Interaction", [
    "Step 1.1: Target Selection",
    "  Planners navigate satellite map",
    "  Location query via Nominatim",
    "Step 1.2: Boundary Definition",
    "  Option A: Draw candidate polygon",
    "  Option B: Upload 1m KML file",
    "Step 1.3: Viewport Customization",
    "  Drag resizer handle (.resize-handle-bar)",
    "  Select preset (30%, 55%, 75%, 88%)",
    "  Trigger Leaflet map.invalidateSize()",
    "Data Payload Formatted:",
    "  GeoJSON FeatureCollection",
    "  Bounding Box [lat_min, lat_max]",
    "  KML 3D Coordinate Tuples (x,y,z)",
    "API Endpoint:",
    "  POST /api/analyze_site",
    "  POST /api/parse_kml"
], "#1E293B", "#00E5FF")

# Phase 2: DEM Grid Interpolation
draw_phase_card(4.3, 0.6, 3.6, 9.0, "2", "DEM SAMPLING & 2D GRID", "Terrain SciPy Grid Interpolation", [
    "Step 2.1: DEM Tile Fetching",
    "  Query SRTM 30m Global DEM",
    "  Parse KML elevation points",
    "Step 2.2: SciPy 2D Interpolation",
    "  Grid shape: N x M matrix Z(x,y)",
    "  SciPy griddata linear method",
    "Step 2.3: IDW Weighting Fallback",
    "  Formula:",
    "    Z(x,y) = Σ(w_k * Z_k) / Σ w_k",
    "    w_k = 1 / (d_k² + ε)",
    "Step 2.4: Topographic Derivatives",
    "  Slope Matrix: S(x,y) = |∇Z|",
    "  Aspect Matrix: Direction of slope",
    "  Iso-Contours: Marching Squares",
    "  Chaikin Line Smoothing algorithm",
    "Output Grid:",
    "  Normalized 2D Matrix Z(i,j)"
], "#1E293B", "#3B82F6")

# Phase 3: D8 Flow Routing & BFS
draw_phase_card(8.2, 0.6, 3.6, 9.0, "3", "D8 FLOW ROUTING & BFS", "Hydrological Catchment Delineation", [
    "Step 3.1: Steepest Gradient",
    "  For each cell (i, j), check 8 neighbors",
    "  Formula:",
    "    ΔZ = (Z_ij - Z_neighbor) / Dist",
    "Step 3.2: D8 Direction Matrix",
    "  Assign 1 of 8 flow codes (1 to 128)",
    "Step 3.3: Flow Accumulation",
    "  Sort cells descending by height",
    "  Accumulate upstream drainage count",
    "Step 3.4: Outlet & Depression",
    "  Identify lowest local valley point",
    "Step 3.5: Reverse BFS Traversal",
    "  Queue starting at outlet node",
    "  Traverse all incoming flow edges",
    "  Extract catchment polygon boundary",
    "Output Vectors:",
    "  Catchment Polygon & Stream Paths"
], "#1E293B", "#10B981")

# Phase 4: Hydro Math & Render
draw_phase_card(12.1, 0.6, 3.5, 9.0, "4", "HYDRO MATH & GIS RENDER", "Volume Estimation & Map Render", [
    "Step 4.1: Climate Data Fetch",
    "  Query Open-Meteo annual rainfall P",
    "Step 4.2: Rational Runoff Volume",
    "  Formula:",
    "    V_runoff = C * (P / 1000) * A",
    "    Runoff Coefficient C = 0.30",
    "Step 4.3: Viability Scoring",
    "  Depression Depth + Slope Score",
    "  Exclusion rules check (0-100)",
    "Step 4.4: Storage & Irrigation",
    "  Net storage volume V (m³)",
    "  Irrigation (ha) = V / 5000",
    "Step 4.5: Frontend GIS Render",
    "  Green Rectangle: Pond Excavation",
    "  Cyan Polygon: Watershed Boundary",
    "  Blue Lines: Stream Channels",
    "  Result Panel Card update"
], "#1E293B", "#F59E0B")

# Sequential Pipeline Flow Arrows
def draw_pipeline_arrow(x1, y1, x2, y2):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="->", color="#00E5FF", lw=3.0, mutation_scale=22))

draw_pipeline_arrow(4.0, 5.1, 4.3, 5.1)
draw_pipeline_arrow(7.9, 5.1, 8.2, 5.1)
draw_pipeline_arrow(11.8, 5.1, 12.1, 5.1)

plt.tight_layout()
plt.savefig("sample_data/workflow_diagram.png", facecolor=fig.get_facecolor(), edgecolor='none', bbox_inches='tight')
print("✔ Detailed Workflow diagram generated at sample_data/workflow_diagram.png")
