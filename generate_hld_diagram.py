import matplotlib.pyplot as plt
import matplotlib.patches as patches

fig, ax = plt.subplots(figsize=(12, 7), dpi=300)
ax.set_xlim(0, 12)
ax.set_ylim(0, 7)
ax.axis('off')

# Background canvas style
fig.patch.set_facecolor('#0B0F19')
ax.set_facecolor('#0B0F19')

# Header Title
ax.text(6, 6.5, "MIST POND DETECTION PLATFORM -- HIGH-LEVEL SYSTEM ARCHITECTURE", 
        ha='center', va='center', color='#FFFFFF', fontsize=13, fontweight='bold', family='sans-serif')

def draw_box(x, y, w, h, title, subtitle, bg_color, border_color, title_color='#FFFFFF'):
    rect = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.1,rounding_size=0.15",
                                 facecolor=bg_color, edgecolor=border_color, linewidth=1.8)
    ax.add_patch(rect)
    ax.text(x + w/2, y + h - 0.35, title, ha='center', va='center', color=title_color, fontsize=10, fontweight='bold')
    ax.text(x + w/2, y + 0.35, subtitle, ha='center', va='center', color='#94A3B8', fontsize=8, multialignment='center')

# Layer 1: Client Frontend Layer
draw_box(0.5, 4.5, 3.2, 1.6, "1. Client GIS Interface", "Leaflet.js v1.9 | Leaflet.draw\nDrag Resizer | Visual Overlays\n(Green Pond, Cyan Catchment)", "#1E293B", "#00E5FF")

# Layer 2: Load Balancer & Gateway Layer
draw_box(4.4, 4.5, 3.2, 1.6, "2. Gateway & Load Balancer", "Flask Gateway | SSH Tunnel\nRound-Robin Node Selector\nPublic HTTPS: localhost.run", "#1E293B", "#3B82F6")

# Layer 3: External APIs
draw_box(8.3, 4.5, 3.2, 1.6, "3. External API Services", "Open-Meteo Historical Climate API\nOpenStreetMap Nominatim API\nSRTM DEM Elevation Data", "#1E293B", "#A855F7")

# Layer 4: Hydrological Core Engines
draw_box(0.5, 1.0, 3.2, 2.4, "Contour & D8 Engine\n(contour_engine.py)", "• KML/KMZ 3D Point Cloud Parsing\n• 2D DEM Grid Interpolation\n• D8 Single-Flow Direction Model\n• Upstream Catchment BFS Traversal", "#0F172A", "#10B981")

draw_box(4.4, 1.0, 3.2, 2.4, "Suitability Engine\n(suitability_engine.py)", "• Multi-Factor Terrain Scoring\n• Elevation Depression Detection\n• Water Body Exclusion Rules\n• Recommended Pond Depth & Size", "#0F172A", "#F59E0B")

draw_box(8.3, 1.0, 3.2, 2.4, "Hydrology Engine\n(hydrology_engine.py)", "• Historical Precipitation Query\n• Rational Method Runoff (V=C*I*A)\n• Storage Capacity (m³) Estimation\n• Irrigation Potential (Hectares)", "#0F172A", "#EC4899")

# Arrows connection helper
def draw_arrow(x1, y1, x2, y2, label=""):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="->", color="#00E5FF", lw=1.8, mutation_scale=15))
    if label:
        ax.text((x1+x2)/2, (y1+y2)/2 + 0.15, label, ha='center', va='center', color='#00E5FF', fontsize=7.5, fontweight='bold')

# Connect Client to Gateway
draw_arrow(3.7, 5.3, 4.4, 5.3, "HTTPS Request")

# Connect Gateway to External APIs
draw_arrow(7.6, 5.3, 8.3, 5.3, "REST Calls")

# Connect Gateway to Worker Engines
draw_arrow(5.0, 4.5, 2.1, 3.4, "Dispatch")
draw_arrow(6.0, 4.5, 6.0, 3.4, "Dispatch")
draw_arrow(7.0, 4.5, 9.9, 3.4, "Dispatch")

plt.tight_layout()
plt.savefig("sample_data/high_level_architecture.png", facecolor=fig.get_facecolor(), edgecolor='none', bbox_inches='tight')
print("✔ High Level Architecture diagram saved to sample_data/high_level_architecture.png")
