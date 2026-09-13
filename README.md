# 💧 Mist Pond Detection

**Smart AI-Based Pond Suitability & Hydrology System**

Draw any polygon on the map, and Mist Pond Detection instantly tells you:
- ✅ Whether that location is **suitable for a pond**
- 📐 The recommended **depth and surface area**
- 💧 The estimated **storage volume** (m³ & Liters)
- 🌾 How many **hectares of cropland** it can irrigate

---

## 🚀 Quick Start

```bash
# Install dependencies
pip install flask requests numpy

# Run the app
python3 web_app.py
```

Open `http://localhost:5000` in your browser.

---

## 🗺️ How It Works

1. **Search** for any village or location using the search bar
2. **Draw a polygon** on the map using the polygon tool
3. Click **"Analyze This Site"**
4. The AI fetches real elevation data and scores your location on:
   - Terrain Slope
   - Natural Depression (bowl shape)
   - Shape Compactness
   - Area Viability
   - Rainfall Adequacy

---

## 📁 Project Structure

```
smart_pond_detection/
├── web_app.py              # Flask web server
├── suitability_engine.py   # AI suitability scoring engine
├── hydrology_engine.py     # Runoff & depth calculation engine
├── ai_pond_detector.py     # Computer vision pond detector
├── sample_generator.py     # Synthetic satellite image generator
├── detect_ponds_cli.py     # CLI batch processing tool
├── templates/
│   └── index.html          # Web UI (Leaflet.js + draw tools)
└── static/
    ├── style.css           # Dark glassmorphism stylesheet
    └── app.js              # Frontend JavaScript
```

---

## 🛠️ Tech Stack

- **Backend**: Python + Flask
- **AI Engine**: NumPy terrain analysis + Open-Elevation API
- **Hydrology**: Rational Method (Q = C × P × A)
- **Frontend**: Vanilla JS + Leaflet.js + Leaflet.draw
- **Map Data**: OpenStreetMap + Esri Satellite
