import matplotlib.pyplot as plt
import matplotlib.patches as patches

fig, ax = plt.subplots(figsize=(13, 6.5), dpi=300)
ax.set_xlim(0, 13)
ax.set_ylim(0, 6.5)
ax.axis('off')

# Background canvas style
fig.patch.set_facecolor('#0F172A')
ax.set_facecolor('#0F172A')

# Header Title
ax.text(6.5, 6.0, "MIST POND DETECTION PLATFORM -- END-TO-END WORKFLOW & DATA PIPELINE", 
        ha='center', va='center', color='#FFFFFF', fontsize=13, fontweight='bold', family='sans-serif')

def draw_step(x, y, w, h, step_num, title, items, bg_color, border_color):
    rect = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.1,rounding_size=0.15",
                                 facecolor=bg_color, edgecolor=border_color, linewidth=1.8)
    ax.add_patch(rect)
    # Step header tag
    ax.text(x + w/2, y + h - 0.3, f"STEP {step_num}: {title}", ha='center', va='center', color='#FFFFFF', fontsize=9.5, fontweight='bold')
    # Details bullet points
    detail_text = "\n".join([f"• {it}" for it in items])
    ax.text(x + 0.2, y + h/2 - 0.2, detail_text, ha='left', va='center', color='#CBD5E1', fontsize=7.5, multialignment='left')

# Step 1: User Input
draw_step(0.4, 1.2, 2.7, 4.2, "1", "User GIS Input", [
    "Select region on map",
    "Draw custom polygon",
    "Or upload 1m KML/KMZ",
    "Drag resizer handle bar",
    "Pick height preset"
], "#1E293B", "#00E5FF")

# Step 2: DEM Grid Interpolation
draw_step(3.5, 1.2, 2.7, 4.2, "2", "Terrain DEM Sampling", [
    "Query SRTM DEM API",
    "Parse KML 3D point cloud",
    "SciPy 2D griddata math",
    "IDW fallback weighting",
    "Compute slope & aspect"
], "#1E293B", "#3B82F6")

# Step 3: D8 Catchment Routing
draw_step(6.6, 1.2, 2.7, 4.2, "3", "D8 Flow Accumulation", [
    "8-neighbor steepest slope",
    "D8 flow direction matrix",
    "Sort cells by elevation",
    "Reverse BFS watershed",
    "Extract catchment boundary"
], "#1E293B", "#10B981")

# Step 4: Hydro & Suitability Scoring
draw_step(9.7, 1.2, 2.8, 4.2, "4", "Hydro & Results Render", [
    "Fetch Open-Meteo rainfall",
    "Rational runoff V=C*R*A",
    "Depression & depth score",
    "Green pond excavation box",
    "Cyan watershed & blue streams"
], "#1E293B", "#F59E0B")

# Arrows helper
def draw_flow_arrow(x1, y1, x2, y2):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="->", color="#00E5FF", lw=2.2, mutation_scale=18))

draw_flow_arrow(3.1, 3.3, 3.5, 3.3)
draw_flow_arrow(6.2, 3.3, 6.6, 3.3)
draw_flow_arrow(9.3, 3.3, 9.7, 3.3)

plt.tight_layout()
plt.savefig("sample_data/workflow_diagram.png", facecolor=fig.get_facecolor(), edgecolor='none', bbox_inches='tight')
print("✔ End-to-End Workflow diagram saved to sample_data/workflow_diagram.png")
