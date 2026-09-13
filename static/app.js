/* ==========================================================================
   AquaVision AI – Draw & Analyze Pond System
   Frontend Application Logic  v2.0
   ========================================================================== */

'use strict';

// ── State ──────────────────────────────────────────────────────────────────
const state = {
    drawnLayer: null,
    lastResult: null,
    contoursVisible: true,
    dotsVisible: true,
};

// ── DOM references ─────────────────────────────────────────────────────────
const $ = (id) => document.getElementById(id);
const DOM = {
    searchInput:    $('searchInput'),
    btnSearch:      $('btnSearch'),
    searchResults:  $('searchResults'),
    sliderRainfall: $('sliderRainfall'),
    labelRainfall:  $('labelRainfall'),
    inputCatchment: $('inputCatchment'),
    btnAnalyze:     $('btnAnalyze'),
    btnClearDraw:   $('btnClearDraw'),
    drawHint:       $('drawHint'),
    drawStats:      $('drawStats'),
    statArea:       $('statArea'),
    statPerimeter:  $('statPerimeter'),
    statCenter:     $('statCenter'),
    mapLoading:     $('mapLoading'),
    resultPanel:    $('resultPanel'),

    verdictBanner:  $('verdictBanner'),
    verdictIcon:    $('verdictIcon'),
    verdictTitle:   $('verdictTitle'),
    verdictSubtitle:$('verdictSubtitle'),
    scoreArc:       $('scoreArc'),
    scoreNum:       $('scoreNum'),

    kpiArea:        $('kpiArea'),
    kpiAreaHa:      $('kpiAreaHa'),
    kpiDepth:       $('kpiDepth'),
    kpiBundHeight:  $('kpiBundHeight'),
    kpiVolume:      $('kpiVolume'),
    kpiVolumeLiters:$('kpiVolumeLiters'),
    kpiIrrigation:  $('kpiIrrigation'),

    factorGrid:     $('factorGrid'),
    reasonsList:    $('reasonsList'),
    specsGrid:      $('specsGrid'),
    mapControls:    $('mapControls'),
    btnToggleContour: $('btnToggleContour'),
    btnToggleHeatDots: $('btnToggleHeatDots'),
};

// ── Leaflet Map Setup ──────────────────────────────────────────────────────
const map = L.map('mainMap', {
    center: [22.5, 80.0],
    zoom: 6,
    zoomControl: true,
});

// OpenStreetMap base tile (no API key required)
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors',
    maxZoom: 19,
}).addTo(map);

// Satellite tile option via Esri
const esriSat = L.tileLayer(
    'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    { attribution: 'Tiles © Esri', maxZoom: 19 }
);

// Layer switcher
const baseMaps = {
    '🗺 Street Map': L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19 }),
    '🛰 Satellite':  esriSat,
};
L.control.layers(baseMaps).addTo(map);

// Leaflet.Draw setup
const drawnItems = new L.FeatureGroup().addTo(map);
const drawControl = new L.Control.Draw({
    draw: {
        polygon: {
            shapeOptions: {
                color: '#00d4ff',
                fillColor: '#00d4ff',
                fillOpacity: 0.18,
                weight: 2.5,
            },
            showArea: true,
            guideLayers: [],
            snapDistance: 15,
        },
        rectangle: {
            shapeOptions: {
                color: '#00d4ff',
                fillColor: '#00d4ff',
                fillOpacity: 0.18,
                weight: 2.5,
            },
        },
        circle:   false,
        marker:   false,
        polyline: false,
        circlemarker: false,
    },
    edit: {
        featureGroup: drawnItems,
        edit: true,
        remove: true,
    },
});
map.addControl(drawControl);

// ── Draw Events ───────────────────────────────────────────────────────────
map.on(L.Draw.Event.CREATED, (e) => {
    clearDrawing(false);
    state.drawnLayer = e.layer;
    drawnItems.addLayer(state.drawnLayer);
    onDrawingUpdated();
});

map.on(L.Draw.Event.EDITED, () => onDrawingUpdated());
map.on(L.Draw.Event.DELETED, () => {
    state.drawnLayer = null;
    DOM.btnAnalyze.disabled = true;
    DOM.drawStats.style.display = 'none';
    DOM.resultPanel.classList.add('hidden');
});

function onDrawingUpdated() {
    if (!state.drawnLayer) return;

    const coords = getPolygonCoords(state.drawnLayer);
    const areaSqm = computeAreaFromCoords(coords);
    const perimM  = computePerimeterFromCoords(coords);
    const center  = state.drawnLayer.getBounds().getCenter();

    DOM.statArea.textContent      = `${areaSqm.toLocaleString(undefined, {maximumFractionDigits:1})} m² (${(areaSqm/10000).toFixed(4)} ha)`;
    DOM.statPerimeter.textContent = `${perimM.toFixed(1)} m`;
    DOM.statCenter.textContent    = `${center.lat.toFixed(5)}°, ${center.lng.toFixed(5)}°`;

    DOM.drawStats.style.display = 'block';
    DOM.btnAnalyze.disabled = false;
    DOM.drawHint.innerHTML = '<i class="fa-solid fa-check-circle" style="color:var(--teal)"></i> Polygon drawn. Click Analyze to run AI.';
}

// ── Utility: extract polygon lat/lon coords ──────────────────────────────
function getPolygonCoords(layer) {
    const ll = layer.getLatLngs ? layer.getLatLngs() : [];
    const flat = ll.flat ? ll.flat(Infinity) : flatDeep(ll);
    return flat.map(p => [p.lat, p.lng]);
}
function flatDeep(arr) {
    return arr.reduce((acc, val) => Array.isArray(val) ? acc.concat(flatDeep(val)) : acc.concat(val), []);
}

// Haversine distance
function haversineM(lat1, lon1, lat2, lon2) {
    const R = 6371000;
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLon = (lon2 - lon1) * Math.PI / 180;
    const a = Math.sin(dLat/2)**2 + Math.cos(lat1*Math.PI/180)*Math.cos(lat2*Math.PI/180)*Math.sin(dLon/2)**2;
    return 2 * R * Math.asin(Math.sqrt(a));
}
function computeAreaFromCoords(coords) {
    if (coords.length < 3) return 0;
    const clat = coords.reduce((s,c)=>s+c[0],0)/coords.length;
    const lat2m = 111000;
    const lon2m = 111000 * Math.cos(clat * Math.PI/180);
    const pts = coords.map(c => [c[1]*lon2m, c[0]*lat2m]);
    let area = 0;
    for (let i=0; i<pts.length; i++) {
        const j = (i+1) % pts.length;
        area += pts[i][0]*pts[j][1] - pts[j][0]*pts[i][1];
    }
    return Math.abs(area)/2;
}
function computePerimeterFromCoords(coords) {
    let p = 0;
    for (let i=0; i<coords.length; i++) {
        const j = (i+1)%coords.length;
        p += haversineM(coords[i][0],coords[i][1],coords[j][0],coords[j][1]);
    }
    return p;
}

// ── Clear Drawing ─────────────────────────────────────────────────────────
function clearDrawing(clearResults = true) {
    drawnItems.clearLayers();
    state.drawnLayer = null;
    DOM.btnAnalyze.disabled = true;
    DOM.drawStats.style.display = 'none';
    DOM.drawHint.innerHTML = '<i class="fa-solid fa-info-circle"></i> Draw a polygon on the map first, then click Analyze.';
    if (clearResults) {
        DOM.resultPanel.classList.add('hidden');
        state.lastResult = null;
    }
}

// ── ANALYZE BUTTON ────────────────────────────────────────────────────────
DOM.btnAnalyze.addEventListener('click', runAnalysis);
DOM.btnClearDraw.addEventListener('click', () => clearDrawing(true));

async function runAnalysis() {
    if (!state.drawnLayer) return;

    const coords = getPolygonCoords(state.drawnLayer);
    if (coords.length < 3) {
        alert('Draw a polygon on the map first.');
        return;
    }

    const rainfall = parseInt(DOM.sliderRainfall.value, 10);
    const catchment = parseFloat(DOM.inputCatchment.value) || null;

    DOM.mapLoading.classList.remove('hidden');
    DOM.resultPanel.classList.add('hidden');

    try {
        const resp = await fetch('/api/analyze_polygon', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                coordinates:          coords,
                annual_rainfall_mm:   rainfall,
                catchment_area_sqm:   catchment,
            }),
        });
        const data = await resp.json();

        if (data.status !== 'success') {
            alert(`Error: ${data.message}`);
            return;
        }

        state.lastResult = data;
        renderResults(data);
        DOM.resultPanel.classList.remove('hidden');

    } catch (err) {
        console.error(err);
        alert('Failed to connect to AI analysis server.');
    } finally {
        DOM.mapLoading.classList.add('hidden');
    }
}

// ── RENDER RESULTS ────────────────────────────────────────────────────────
function renderResults(data) {
    const { geometry, elevation_stats, suitability, pond_specs, elevation_heatmap, elevation_grid } = data;

    renderVerdictBanner(suitability, geometry);
    renderKPIs(geometry, pond_specs);
    renderFactorGrid(suitability);
    renderReasons(suitability);
    renderSpecsGrid(geometry, pond_specs);

    // Elevation dots + contour lines on map
    renderElevationHeatmap(elevation_heatmap, elevation_stats);
    renderContourLines(elevation_grid);

    // Show map control bar
    DOM.mapControls.style.display = 'flex';

    // Activate first tab
    switchTab('reasons');
}

// ── Verdict Banner ────────────────────────────────────────────────────────
function renderVerdictBanner(s, g) {
    const colorMap = { green: 'green-verdict', orange: 'orange-verdict', red: 'red-verdict' };
    DOM.verdictBanner.className = `verdict-banner ${colorMap[s.verdict_color] || ''}`;

    const emojiMap = { green: '✅', orange: '⚠️', red: '❌' };
    DOM.verdictIcon.textContent = emojiMap[s.verdict_color] || '📍';

    DOM.verdictTitle.textContent = s.verdict;
    DOM.verdictSubtitle.textContent = `AI Suitability Score: ${s.suitability_score}/100 | Area: ${g.surface_area_sqm.toLocaleString()} m² (${g.surface_area_hectares} ha)`;

    // Animate score ring
    const circumference = 2 * Math.PI * 26;   // r=26
    const offset = circumference * (1 - s.suitability_score / 100);
    const arcColors = { green: '#00e676', orange: '#ff9f00', red: '#ff4d4d' };
    DOM.scoreArc.style.stroke = arcColors[s.verdict_color] || '#00d4ff';
    DOM.scoreArc.style.strokeDasharray = `${circumference}`;
    setTimeout(() => { DOM.scoreArc.style.strokeDashoffset = offset; }, 50);

    DOM.scoreNum.textContent = s.suitability_score;
    const numColors = { green: '#00e676', orange: '#ff9f00', red: '#ff4d4d' };
    DOM.scoreNum.style.color = numColors[s.verdict_color] || '#00d4ff';
}

// ── KPI Cards ─────────────────────────────────────────────────────────────
function renderKPIs(g, specs) {
    DOM.kpiArea.textContent    = `${g.surface_area_sqm.toLocaleString()} m²`;
    DOM.kpiAreaHa.textContent  = `${g.surface_area_hectares} Hectares`;

    if (specs) {
        DOM.kpiDepth.textContent       = `${specs.recommended_depth_m} m`;
        DOM.kpiBundHeight.textContent  = `Bund height: ${specs.bund_height_m} m`;
        DOM.kpiVolume.textContent      = `${specs.net_usable_volume_m3.toLocaleString()} m³`;
        DOM.kpiVolumeLiters.textContent= `${(specs.net_usable_volume_m3 * 1000).toLocaleString()} Liters`;
        DOM.kpiIrrigation.textContent  = `${specs.irrigation_potential_ha} ha`;
    } else {
        ['kpiDepth','kpiBundHeight','kpiVolume','kpiVolumeLiters','kpiIrrigation'].forEach(k => {
            DOM[k].textContent = 'N/A (not suitable)';
        });
    }
}

// ── Factor Grid ───────────────────────────────────────────────────────────
function renderFactorGrid(s) {
    const labels = {
        slope: 'Terrain Slope', depression: 'Natural Depression',
        compactness: 'Shape Compactness', area: 'Area Viability', rainfall: 'Rainfall Adequacy'
    };
    DOM.factorGrid.innerHTML = Object.entries(s.factor_scores).map(([k, v]) => {
        const color = v >= 75 ? '#00e676' : v >= 50 ? '#ff9f00' : '#ff4d4d';
        return `
        <div class="factor-card">
            <div class="factor-label">${labels[k] || k}</div>
            <div class="factor-score" style="color:${color}">${v}</div>
            <div class="factor-bar"><div class="factor-fill" style="width:${v}%;background:${color}"></div></div>
        </div>`;
    }).join('');
}

// ── Reasons ───────────────────────────────────────────────────────────────
function renderReasons(s) {
    const rows = [
        ...s.reasons.map(r => `<div class="reason-item">${r}</div>`),
        ...s.penalties.map(r => `<div class="reason-item penalty">⚠️ ${r}</div>`),
    ];
    DOM.reasonsList.innerHTML = rows.join('');
}

// ── Specs Grid ────────────────────────────────────────────────────────────
function renderSpecsGrid(g, specs) {
    if (!specs) {
        DOM.specsGrid.innerHTML = `<p style="color:var(--text-2);font-size:13px;padding:12px">Location not suitable – pond construction not recommended here. Consider redrawing in a lower-lying area.</p>`;
        return;
    }
    const items = [
        { label: 'Surface Area',             val: `${specs.surface_area_sqm.toLocaleString()} m²`,       unit: `${specs.surface_area_hectares} ha` },
        { label: 'Perimeter',                val: `${g.perimeter_m} m`,                                   unit: 'boundary length' },
        { label: 'Recommended Depth',        val: `${specs.recommended_depth_m} m`,                       unit: 'below ground level' },
        { label: 'Bund / Embankment Height', val: `${specs.bund_height_m} m`,                             unit: '0.5m freeboard included' },
        { label: 'Gross Storage Volume',     val: `${specs.gross_storage_volume_m3.toLocaleString()} m³`, unit: 'total capacity' },
        { label: 'Net Usable Volume',        val: `${specs.net_usable_volume_m3.toLocaleString()} m³`,    unit: 'after evap & seepage loss' },
        { label: 'Annual Runoff Inflow',     val: `${specs.annual_runoff_m3.toLocaleString()} m³`,        unit: 'from catchment area' },
        { label: 'Annual Loss (Evap+Seep)',  val: `${specs.annual_evaporation_seepage_loss_m3.toLocaleString()} m³`, unit: 'expected annual loss' },
        { label: 'Excavation Required',      val: `${specs.excavation_required_m3.toLocaleString()} m³`,  unit: 'earth to remove' },
        { label: 'Catchment Area',           val: `${specs.catchment_area_sqm.toLocaleString()} m²`,      unit: 'feeder area assumed' },
    ];
    DOM.specsGrid.innerHTML = items.map(i => `
        <div class="spec-item">
            <div class="spec-label">${i.label}</div>
            <div class="spec-val">${i.val}</div>
            <div class="spec-unit">${i.unit}</div>
        </div>`).join('');
}



// ═══════════════════════════════════════════════════════════════════════════
// CONTOUR MAP ENGINE
// ═══════════════════════════════════════════════════════════════════════════

// ── Color scale: Blue (low) → Cyan → Green → Yellow → Orange → Red (high)
function elevationColor(t) {
    // t ∈ [0,1], 0=lowest, 1=highest
    const stops = [
        [0.00, [30, 136, 229]],   // #1e88e5 deep blue
        [0.15, [0,  172, 193]],   // #00acc1 cyan
        [0.35, [67, 160,  71]],   // #43a047 green
        [0.55, [253, 216,  53]],  // #fdd835 yellow
        [0.75, [251, 140,   0]],  // #fb8c00 orange
        [1.00, [229,  57,  53]],  // #e53935 red
    ];
    for (let i = 1; i < stops.length; i++) {
        if (t <= stops[i][0]) {
            const [t0, c0] = stops[i-1];
            const [t1, c1] = stops[i];
            const f = (t - t0) / (t1 - t0);
            const r = Math.round(c0[0] + f*(c1[0]-c0[0]));
            const g = Math.round(c0[1] + f*(c1[1]-c0[1]));
            const b = Math.round(c0[2] + f*(c1[2]-c0[2]));
            return `rgb(${r},${g},${b})`;
        }
    }
    return '#e53935';
}

// ── Elevation dot markers ─────────────────────────────────────────────────
let heatmapMarkers = [];
function renderElevationHeatmap(heatData, stats) {
    heatmapMarkers.forEach(m => map.removeLayer(m));
    heatmapMarkers = [];

    const minE = stats.min_m, maxE = stats.max_m;
    const range = maxE - minE || 1;

    heatData.forEach(pt => {
        const t = (pt.elev - minE) / range;
        const color = elevationColor(t);
        const circle = L.circleMarker([pt.lat, pt.lon], {
            radius: 5, color: 'transparent',
            fillColor: color, fillOpacity: 0.72, weight: 0,
        });
        circle.bindTooltip(`${pt.elev} m ASL`, { permanent: false, opacity: .9 });
        circle.addTo(map);
        heatmapMarkers.push(circle);
    });

    if (!state.dotsVisible) heatmapMarkers.forEach(m => map.removeLayer(m));
}

// ── Marching Squares Contour Line Generator ───────────────────────────────
let contourLayers = [];

function renderContourLines(grid) {
    // Clear previous
    contourLayers.forEach(l => map.removeLayer(l));
    contourLayers = [];

    const values = grid.values;           // 2D array [row][col]
    const lats   = grid.lats;
    const lons   = grid.lons;
    const rows   = grid.grid_size;
    const cols   = grid.grid_size;

    // Find min / max elevation
    let minE = Infinity, maxE = -Infinity;
    for (let r = 0; r < rows; r++)
        for (let c = 0; c < cols; c++) {
            if (values[r][c] < minE) minE = values[r][c];
            if (values[r][c] > maxE) maxE = values[r][c];
        }
    if (maxE === minE) return;

    // Generate NUM_LEVELS iso-contour levels
    const NUM_LEVELS = 10;
    const levels = [];
    for (let i = 0; i <= NUM_LEVELS; i++)
        levels.push(minE + (i / NUM_LEVELS) * (maxE - minE));

    // For each iso-level, run a simple marching-squares variant
    levels.forEach((threshold, li) => {
        const t = li / NUM_LEVELS;
        const color = elevationColor(t);
        const segments = marchingSquares(values, lats, lons, rows, cols, threshold);

        segments.forEach(seg => {
            const poly = L.polyline(seg, {
                color,
                weight: li % 3 === 0 ? 2.2 : 1.2,   // thicker every 3rd line
                opacity: 0.82,
                smoothFactor: 1.2,
            });
            poly.bindTooltip(`${threshold.toFixed(1)} m`, { sticky: true, opacity: .85 });
            poly.addTo(map);
            contourLayers.push(poly);
        });
    });

    if (!state.contoursVisible) contourLayers.forEach(l => map.removeLayer(l));
}

/**
 * Simplified Marching Squares — returns an array of LatLng pair arrays
 * representing iso-contour line segments at `threshold` elevation.
 */
function marchingSquares(values, lats, lons, rows, cols, threshold) {
    const segments = [];

    // Linear interpolation helper along a cell edge
    function interp(v0, v1, lat0, lon0, lat1, lon1) {
        const t = (threshold - v0) / (v1 - v0 + 1e-12);
        return [lat0 + t*(lat1 - lat0), lon0 + t*(lon1 - lon0)];
    }

    for (let r = 0; r < rows - 1; r++) {
        for (let c = 0; c < cols - 1; c++) {
            // Four corners of the cell
            const v00 = values[r][c],     v01 = values[r][c+1];
            const v10 = values[r+1][c],   v11 = values[r+1][c+1];

            const lat00 = lats[r][c],     lon00 = lons[r][c];
            const lat01 = lats[r][c+1],   lon01 = lons[r][c+1];
            const lat10 = lats[r+1][c],   lon10 = lons[r+1][c];
            const lat11 = lats[r+1][c+1], lon11 = lons[r+1][c+1];

            // Binary code for which corners are above threshold
            const code =
                (v00 >= threshold ? 8 : 0) |
                (v01 >= threshold ? 4 : 0) |
                (v11 >= threshold ? 2 : 0) |
                (v10 >= threshold ? 1 : 0);

            if (code === 0 || code === 15) continue; // all below or all above

            // Pre-compute the four edge midpoints (only needed ones)
            const top    = () => interp(v00, v01, lat00, lon00, lat01, lon01);
            const right  = () => interp(v01, v11, lat01, lon01, lat11, lon11);
            const bottom = () => interp(v10, v11, lat10, lon10, lat11, lon11);
            const left   = () => interp(v00, v10, lat00, lon00, lat10, lon10);

            // Marching Squares lookup table → pairs of edges to connect
            const table = {
                1:  [left, bottom],  2:  [bottom, right], 3:  [left, right],
                4:  [right, top],    5:  [left, top, right, bottom], // saddle
                6:  [bottom, top],   7:  [left, top],
                8:  [top, left],     9:  [top, bottom],
                10: [right, left, bottom, top], // saddle
                11: [top, right],    12: [right, left],
                13: [bottom, left],  14: [bottom, top],  // redundant but safe
            };

            const edges = table[code];
            if (!edges) continue;

            // Emit as pairs of [pt1, pt2]
            for (let i = 0; i < edges.length; i += 2) {
                if (edges[i+1]) {
                    segments.push([edges[i](), edges[i+1]()]);
                }
            }
        }
    }
    return segments;
}

// ── Toggle Contour Button ─────────────────────────────────────────────────
DOM.btnToggleContour.addEventListener('click', () => {
    state.contoursVisible = !state.contoursVisible;
    DOM.btnToggleContour.classList.toggle('active', state.contoursVisible);
    contourLayers.forEach(l => {
        state.contoursVisible ? l.addTo(map) : map.removeLayer(l);
    });
});

// ── Toggle Elevation Dots Button ──────────────────────────────────────────
DOM.btnToggleHeatDots.addEventListener('click', () => {
    state.dotsVisible = !state.dotsVisible;
    DOM.btnToggleHeatDots.classList.toggle('active', state.dotsVisible);
    heatmapMarkers.forEach(m => {
        state.dotsVisible ? m.addTo(map) : map.removeLayer(m);
    });
});

// ── Tab Switching ─────────────────────────────────────────────────────────
document.querySelectorAll('.tab').forEach(btn => {
    btn.addEventListener('click', () => switchTab(btn.dataset.tab));
});

function switchTab(tabId) {
    document.querySelectorAll('.tab').forEach(t => t.classList.toggle('active', t.dataset.tab === tabId));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.toggle('active', c.id === `tab-${tabId}`));
    if (tabId === 'terrain' && state.elevChart) state.elevChart.resize();
}

// ── Rainfall Slider ───────────────────────────────────────────────────────
DOM.sliderRainfall.addEventListener('input', (e) => {
    DOM.labelRainfall.textContent = `${e.target.value} mm`;
});

// ── Location Search ───────────────────────────────────────────────────────
DOM.btnSearch.addEventListener('click', doSearch);
DOM.searchInput.addEventListener('keydown', (e) => { if (e.key === 'Enter') doSearch(); });

async function doSearch() {
    const q = DOM.searchInput.value.trim();
    if (!q) return;

    try {
        const resp = await fetch(`/api/geocode?q=${encodeURIComponent(q)}`);
        const data = await resp.json();
        if (data.results && data.results.length) {
            renderSearchResults(data.results);
        } else {
            DOM.searchResults.innerHTML = '<li style="color:var(--text-3)">No results found.</li>';
            DOM.searchResults.classList.remove('hidden');
        }
    } catch (err) {
        console.error(err);
    }
}

function renderSearchResults(results) {
    DOM.searchResults.innerHTML = results.slice(0, 5).map(r => `
        <li data-lat="${r.lat}" data-lon="${r.lon}">${r.display_name}</li>
    `).join('');
    DOM.searchResults.classList.remove('hidden');

    DOM.searchResults.querySelectorAll('li').forEach(li => {
        li.addEventListener('click', () => {
            const lat = parseFloat(li.dataset.lat);
            const lon = parseFloat(li.dataset.lon);
            map.setView([lat, lon], 15);
            DOM.searchResults.classList.add('hidden');
        });
    });
}

// Hide search results on outside click
document.addEventListener('click', (e) => {
    if (!DOM.searchResults.contains(e.target) && e.target !== DOM.searchInput) {
        DOM.searchResults.classList.add('hidden');
    }
});
