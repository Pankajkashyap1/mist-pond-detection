"""
test_api_execution.py
---------------------
Tests the live POST /analyzeContour API endpoint with a sample KML file 
and prints the structured JSON response.
"""

import sys
import json
import requests

API_URL = "http://localhost:5000/analyzeContour"

# Sample KML content for dynamic testing
SAMPLE_KML = """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>Sample Contours</name>
    <Placemark>
      <name>Contour 310m</name>
      <LineString>
        <coordinates>
          81.2857,21.2458,310.0
          81.2880,21.2455,310.0
          81.2910,21.2450,310.0
        </coordinates>
      </LineString>
    </Placemark>
    <Placemark>
      <name>Contour 300m</name>
      <LineString>
        <coordinates>
          81.2860,21.2440,300.0
          81.2890,21.2435,300.0
          81.2915,21.2430,300.0
        </coordinates>
      </LineString>
    </Placemark>
    <Placemark>
      <name>Contour 290m</name>
      <LineString>
        <coordinates>
          81.2865,21.2420,290.0
          81.2895,21.2415,290.0
          81.2920,21.2410,290.0
        </coordinates>
      </LineString>
    </Placemark>
  </Document>
</kml>"""

def run_test():
    print(f"📡 Sending POST request to {API_URL}...")
    files = {"file": ("test_contours.kml", SAMPLE_KML, "application/vnd.google-earth.kml+xml")}
    try:
        response = requests.post(API_URL, files=files, timeout=10)
        print(f"HTTP Status Code: {response.status_code}")
        print("JSON Response:")
        print(json.dumps(response.json(), indent=2))
    except Exception as e:
        print(f"Error executing API test: {e}")

if __name__ == "__main__":
    run_test()
