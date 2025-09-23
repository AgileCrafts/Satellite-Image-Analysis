import '@ant-design/v5-patch-for-react-19';
import { message } from 'antd';
import React, { useEffect, useState, useRef } from "react";
import Map, { useMap, NavigationControl } from "react-map-gl";
import MapboxDraw from "@mapbox/mapbox-gl-draw";
import * as turf from "@turf/turf";
import "mapbox-gl/dist/mapbox-gl.css";
import "@mapbox/mapbox-gl-draw/dist/mapbox-gl-draw.css";

// Custom Rectangle Mode
export const RectangleMode = {
  onSetup() {
    const rect = this.newFeature({
      type: "Feature",
      properties: { shape: "rectangle" },
      geometry: {
        type: "Polygon",
        coordinates: [[]],
      },
    });
    this.addFeature(rect);
    this.clearSelectedFeatures();
    this.updateUIClasses({ mouse: "add" });
    this.setActionableState({ trash: true });
    return { rect, startPos: null };
  },

  clickAnywhere(state, e) {
    if (state.startPos === null) {
      state.startPos = [e.lngLat.lng, e.lngLat.lat];
    } else {
      this.updateRectangle(state, [e.lngLat.lng, e.lngLat.lat]);
      this.updateUIClasses({ mouse: "pointer" });
      this.changeMode("simple_select", { featureIds: [state.rect.id] });
      this.map.fire('draw.create', { features: [state.rect.toGeoJSON()] });
    }
    this.updateRectangle(state, [e.lngLat.lng, e.lngLat.lat]);
  },

  onMouseMove(state, e) {
    if (state.startPos) {
      this.updateRectangle(state, [e.lngLat.lng, e.lngLat.lat]);
    }
  },

  updateRectangle(state, endPos) {
    const start = state.startPos;
    const end = endPos;
    const minX = Math.min(start[0], end[0]);
    const maxX = Math.max(start[0], end[0]);
    const minY = Math.min(start[1], end[1]);
    const maxY = Math.max(start[1], end[1]);
    const coords = [
      [minX, minY],
      [maxX, minY],
      [maxX, maxY],
      [minX, maxY],
      [minX, minY],
    ];
    state.rect.setCoordinates([coords]);
  },

  onTap(state, e) {
    this.clickAnywhere(state, e);
  },

  onClick(state, e) {
    this.clickAnywhere(state, e);
  },

  toDisplayFeatures(state, geojson, display) {
    display(geojson);
  },
};

// Custom Circle Mode
export const CircleMode = {
  onSetup() {
    const circle = this.newFeature({
      type: "Feature",
      properties: { shape: "circle" },
      geometry: {
        type: "Polygon",
        coordinates: [[]],
      },
    });
    this.addFeature(circle);
    this.clearSelectedFeatures();
    this.updateUIClasses({ mouse: "add" });
    this.setActionableState({ trash: true });
    return { circle, center: null, radius: 0 };
  },

  clickAnywhere(state, e) {
    if (state.center === null) {
      state.center = [e.lngLat.lng, e.lngLat.lat];
    } else {
      this.updateCircle(state, [e.lngLat.lng, e.lngLat.lat]);
      this.updateUIClasses({ mouse: "pointer" });
      this.changeMode("simple_select", { featureIds: [state.circle.id] });
      this.map.fire('draw.create', { features: [state.circle.toGeoJSON()] });
    }
    this.updateCircle(state, [e.lngLat.lng, e.lngLat.lat]);
  },

  onMouseMove(state, e) {
    if (state.center) {
      this.updateCircle(state, [e.lngLat.lng, e.lngLat.lat]);
    }
  },

  updateCircle(state, endPos) {
    if (!state.center) return;
    const distance = turf.distance(state.center, endPos, { units: "meters" });
    state.radius = distance;
    const circleGeo = turf.circle(state.center, state.radius / 1000, {
      steps: 64,
      units: "kilometers",
    });
    state.circle.setCoordinates(circleGeo.geometry.coordinates);
  },

  onTap(state, e) {
    this.clickAnywhere(state, e);
  },

  onClick(state, e) {
    this.clickAnywhere(state, e);
  },

  toDisplayFeatures(state, geojson, display) {
    display(geojson);
  },
};

// DrawControl component
export const DrawControl = ({ position, onAoiChange, drawRef }) => {
  const [selectedFeatureId, setSelectedFeatureId] = useState(null);
  const [buttonPosition, setButtonPosition] = useState(null);
  const { current: map } = useMap();

  useEffect(() => {
    if (!map) return;

    const draw = new MapboxDraw({
      displayControlsDefault: false,
      controls: { polygon: true, line_string: true },
      modes: {
        ...MapboxDraw.modes,
        draw_rectangle: RectangleMode,
        draw_circle: CircleMode,
      },
      styles: [
        {
          id: "gl-draw-polygon-fill",
          type: "fill",
          paint: {
            "fill-color": [
              "case",
              ["==", ["get", "shape"], "rectangle"], "red",
              ["==", ["get", "shape"], "circle"], "green",
              "blue",
            ],
            "fill-opacity": 0.3,
          },
        },
        {
          id: "gl-draw-polygon-stroke",
          type: "line",
          paint: {
            "line-color": [
              "case",
              ["==", ["get", "shape"], "rectangle"], "red",
              ["==", ["get", "shape"], "circle"], "green",
              "blue",
            ],
            "line-width": 2,
          },
        },
      ],
    });

    drawRef.current = draw;
    map.addControl(draw, position);

    const updateAoi = (e) => {
      let data = draw.getAll();
      if (e.type === "draw.create" && data.features.length > 1) {
        const idsToDelete = data.features.slice(0, -1).map((f) => f.id);
        draw.delete(idsToDelete);
        data = draw.getAll();
      }
      const feature = data.features[0] || null;
      if (feature) {
        const shape = e.mode
          ? e.mode.replace("draw_", "")
          : feature.properties.shape || "polygon";
        feature.properties = { ...feature.properties, shape };
      }
      onAoiChange(feature);
    };

    map.on("draw.create", updateAoi);
    map.on("draw.update", updateAoi);
    map.on("draw.delete", updateAoi);

    map.on("draw.selectionchange", (e) => {
      if (e.features.length > 0) {
        const feature = e.features[0];
        setSelectedFeatureId(feature.id);
        const [minX, minY, maxX, maxY] = turf.bbox(feature);
        const corner = [maxX, maxY];
        const pixel = map.project(corner);
        setButtonPosition({ x: pixel.x, y: pixel.y });
      } else {
        setSelectedFeatureId(null);
        setButtonPosition(null);
      }
    });

    map.on("move", () => {
      if (selectedFeatureId) {
        const feature = drawRef.current.get(selectedFeatureId);
        if (feature) {
          const [minX, minY, maxX, maxY] = turf.bbox(feature);
          const corner = [maxX, maxY];
          const pixel = map.project(corner);
          setButtonPosition({ x: pixel.x, y: pixel.y });
        }
      }
    });

    return () => {
      console.log("DrawControl: Cleaning up, map exists:", !!map, "draw exists:", !!drawRef.current);
      try {
        if (map) {
          console.log("DrawControl: Removing event listeners");
          map.off("draw.create", updateAoi);
          map.off("draw.update", updateAoi);
          map.off("draw.delete", updateAoi);
          map.off("draw.selectionchange");
          map.off("move");
          if (drawRef.current) {
            console.log("DrawControl: Removing draw control");
            map.removeControl(drawRef.current);
          }
        }
      } catch (error) {
        console.error("DrawControl: Cleanup error:", error);
      }
      drawRef.current = null;
    };
  }, [map, position, onAoiChange, drawRef]);

  return (
    <>
      {selectedFeatureId && buttonPosition && (
        <button
          style={{
            position: "absolute",
            left: `${buttonPosition.x}px`,
            top: `${buttonPosition.y}px`,
            transform: "translate(10%, -50%)",
            zIndex: 1000,
            padding: "2px 6px",
            background: "red",
            color: "white",
            border: "none",
            borderRadius: "4px",
            cursor: "pointer",
            fontSize: "12px",
          }}
          onClick={() => {
            if (window.confirm("Delete this AOI?")) {
              drawRef.current?.delete(selectedFeatureId);
              setSelectedFeatureId(null);
              setButtonPosition(null);
              onAoiChange(null);
            }
          }}
        >
          ✖
        </button>
      )}
    </>
  );
};

// MapMover component
export const MapMover = ({ searchCoords }) => {
  const { current: map } = useMap();

  useEffect(() => {
    if (!map || !searchCoords) return;
    const { lat, lng } = searchCoords;
    if (!isNaN(lat) && !isNaN(lng)) {
      setTimeout(() => {
        map.flyTo({ center: [lng, lat], zoom: 12, essential: true });
        console.log("Map moved to:", { lat, lng });
      }, 100);
    } else {
      console.log("Invalid coordinates:", { lat, lng });
    }
  }, [searchCoords, map]);

  return null;
};

const MapPage = ({ aoi, setAoi, coords, setCoords, searchCoords, setSearchCoords, drawRef }) => {
  const handleSearch = () => {
    const lat = parseFloat(coords.lat.trim());
    const lng = parseFloat(coords.lng.trim());
    if (isNaN(lat) || isNaN(lng)) {
      console.log("Invalid coordinates:", coords);
      return;
    }
    setSearchCoords({ lat, lng });
  };

  const handleDrawMode = (mode) => {
    if (drawRef.current) {
      drawRef.current.changeMode(mode);
    }
  };

  return (
    <div style={{ height: "100%", width: "100%", position: "relative" }}>
      <Map
        id="myMap"
        initialViewState={{
          latitude: 23.5657,
          longitude: 90.5356,
          zoom: 12,
        }}
        style={{ width: "100%", height: "100%" }}
        mapStyle="mapbox://styles/mapbox/satellite-streets-v12"
        mapboxAccessToken="pk.eyJ1IjoicnViYXlldHJhaXNhIiwiYSI6ImNtZmYxNjVyNzBkY3cya29hd3JwcHgxem8ifQ.9EWRZl8FOkbvcz5aVBDOpg"
      >
        <DrawControl position="top-right" onAoiChange={setAoi} drawRef={drawRef} />
        <MapMover searchCoords={searchCoords} />
        <NavigationControl position="top-left" />
        {/* Search Bar */}
        <div
          className="map-search-bar"
          style={{
            position: "absolute",
            top: 10,
            left: "50%",
            transform: "translateX(-50%)",
            zIndex: 1000,
            display: "flex",
            gap: "6px",
          }}
        >
          <input
            type="text"
            placeholder="Latitude"
            value={coords.lat}
            onChange={(e) => setCoords({ ...coords, lat: e.target.value })}
            className="map-search-input"
          />
          <input
            type="text"
            placeholder="Longitude"
            value={coords.lng}
            onChange={(e) => setCoords({ ...coords, lng: e.target.value })}
            className="map-search-input"
          />
          <button onClick={handleSearch} className="save-btn map-search-button">
            Go
          </button>
        </div>
        {/* Custom Draw Buttons */}
        <div
          style={{
            position: "absolute",
            top: 68,
            right: 10,
            zIndex: 1000,
            border: 0,
          }}
        >
          <div className="mapboxgl-ctrl mapboxgl-ctrl-group">
            <button
              className="mapbox-gl-draw_ctrl-draw-btn mapbox-gl-draw_rectangle"
              title="Draw rectangle"
              onClick={() => handleDrawMode("draw_rectangle")}
            >
              <svg viewBox="0 0 24 24" width="20" height="20">
                <rect
                  x="4"
                  y="4"
                  width="16"
                  height="12"
                  fill="none"
                  stroke="black"
                  strokeWidth="2"
                />
              </svg>
            </button>
            <button
              className="mapbox-gl-draw_ctrl-draw-btn mapbox-gl-draw_circle"
              title="Draw circle"
              onClick={() => handleDrawMode("draw_circle")}
            >
              <svg viewBox="0 0 24 24" width="20" height="20">
                <circle
                  cx="12"
                  cy="12"
                  r="8"
                  fill="none"
                  stroke="black"
                  strokeWidth="2"
                />
              </svg>
            </button>
          </div>
        </div>
        {/* AOI Display */}
        <div
          className="floating-card"
          style={{
            position: "absolute",
            bottom: 10,
            left: "10px",
            zIndex: 1000,
            padding: "10px",
            maxWidth: "400px",
            maxHeight: "400px",
            overflowY: "auto",
          }}
        >
          <h4>AOI GeoJSON:</h4>
          <pre>{aoi ? JSON.stringify(aoi, null, 2) : "No AOI selected"}</pre>
          {aoi && (
            <>
              <button
                onClick={() => {
                  const geojsonStr = JSON.stringify(aoi, null, 2);
                  const blob = new Blob([geojsonStr], { type: "application/json" });
                  const url = URL.createObjectURL(blob);
                  const a = document.createElement("a");
                  a.href = url;
                  a.download="aoi.geojson";
                  a.click();
                  URL.revokeObjectURL(url);
                }}
                className="save-btn"
              >
                Download AOI
              </button>
              <button
                onClick={async () => {
                  try {
                    const token = localStorage.getItem("authToken");
                    if (!token) {
                      message.error("No auth token found. Please log in.");
                      return;
                    }
                    const response = await fetch("http://localhost:8000/aoi", {
                      method: "POST",
                      headers: {
                        "Content-Type": "application/json",
                        Authorization: `Bearer ${token}`,
                      },
                      body: JSON.stringify(aoi),
                    });
                    if (!response.ok) {
                      const errorData = await response.json();
                      throw new Error(errorData.detail || "Failed to save AOI");
                    }
                    const data = await response.json();
                    console.log("AOI saved:", data);
                    message.success(`AOI saved successfully! AOI ID: ${data.aoi_id}`);
                  } catch (err) {
                    console.error(err);
                    message.error(err.message || "Failed to save AOI");
                  }
                }}
                className="save-btn"
              >
                Save
              </button>
            </>
          )}
        </div>
      </Map>
    </div>
  );
};

export default MapPage;