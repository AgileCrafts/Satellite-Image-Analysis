import React, { useEffect, useState, useRef, useCallback } from "react";
import Map, { useMap, NavigationControl } from "react-map-gl";
import MapboxDraw from "@mapbox/mapbox-gl-draw";
import * as MapboxDrawGeodesic from "mapbox-gl-draw-geodesic";
import * as turf from "@turf/turf";
import "@mapbox/mapbox-gl-draw/dist/mapbox-gl-draw.css";

const DRAW_MODES = {
  ...MapboxDraw.modes,
  ...MapboxDrawGeodesic.modes,
};

const DRAW_STYLES = [
  // Base styles from Mapbox Draw
  ...MapboxDraw.styles,
  // Override / extend with circle mode styles, if provided
  ...circleDrawStyles,
  // Custom style for rectangle
  {
    id: "gl-draw-polygon-fill-rectangle",
    type: "fill",
    filter: ["all", ["==", ["get", "mode"], "draw_rectangle"], ["==", ["geometry", "type"], "Polygon"]],
    paint: { "fill-color": "#f00", "fill-opacity": 0.3 },
  },
  {
    id: "gl-draw-polygon-stroke-rectangle",
    type: "line",
    filter: ["all", ["==", ["get", "mode"], "draw_rectangle"], ["==", ["geometry", "type"], "Polygon"]],
    paint: { "line-color": "#f00", "line-width": 2 },
  },
];

export function DrawControl({ onAoiChange, drawRef }) {
  const { current: map } = useMap();
  const drawInstanceRef = useRef(null);

  const handleCreateUpdateDelete = useCallback(
    (e) => {
      const all = drawInstanceRef.current.getAll();
      const feature = all.features[0] || null;
      if (feature) {
        // attach shape property (rectangle or circle) if needed
        // feature.properties.shape = ... 
      }
      onAoiChange(feature);
    },
    [onAoiChange]
  );

  useEffect(() => {
    if (!map) return;

    const draw = new MapboxDraw({
    displayControlsDefault: false,
    modes: DRAW_MODES,
    styles: [
      ...MapboxDraw.styles,
      ...MapboxDrawGeodesic.styles, // optional, adds circle/rectangle styling
    ],
    userProperties: true,
  });

    drawRef.current = draw;
    drawInstanceRef.current = draw;
    map.addControl(draw, "top-right");

    map.on("draw.create", handleCreateUpdateDelete);
    map.on("draw.update", handleCreateUpdateDelete);
    map.on("draw.delete", handleCreateUpdateDelete);

    return () => {
      map.off("draw.create", handleCreateUpdateDelete);
      map.off("draw.update", handleCreateUpdateDelete);
      map.off("draw.delete", handleCreateUpdateDelete);

      map.removeControl(draw);
      drawRef.current = null;
      drawInstanceRef.current = null;
    };
  }, [map, handleCreateUpdateDelete, drawRef]);

  return null;
}

export function MapPage({
  aoi,
  setAoi,
  coords,
  setCoords,
  setSearchCoords,
  drawRef,
  setAois,
  setSelectedAoi,
}) {
  const { current: map } = useMap(); // or useMap inside Map component

  const handleSearch = () => {
    const lat = parseFloat(coords.lat);
    const lng = parseFloat(coords.lng);
    if (isNaN(lat) || isNaN(lng)) {
      // you can show a message
      return;
    }
    setSearchCoords({ lat, lng });
    map.flyTo({ center: [lng, lat], zoom: 12, essential: true });
  };

  const handleModeChange = (mode) => {
    if (drawRef.current) {
      drawRef.current.changeMode(mode);
    }
  };

  const handleSave = async () => {
    if (!aoi) return;
    try {
      const token = localStorage.getItem("authToken");
      if (!token) {
        // show error
        return;
      }
      const response = await fetch("/aoi", {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify(aoi),
      });
      if (!response.ok) throw new Error("Save failed");
      const data = await response.json();
      const newAoi = { id: data.aoi_id, geometry: aoi.geometry, properties: aoi.properties };
      setAois((prev) => [...prev, newAoi]);
      setSelectedAoi(data.aoi_id);
    } catch (err) {
      console.error(err);
      // show error to user
    }
  };

  return (
    <div style={{ position: "relative", width: "100%", height: "100%" }}>
      <Map
        initialViewState={{ latitude: 23.5657, longitude: 90.5356, zoom: 12 }}
        mapStyle="mapbox://styles/mapbox/satellite-streets-v12"
        mapboxAccessToken={process.env.REACT_APP_MAPBOX_TOKEN}
        style={{ width: "100%", height: "100%" }}
      >
        <DrawControl onAoiChange={setAoi} drawRef={drawRef} />
        <NavigationControl position="top-left" />

        {/* Controls */}
        <div className="map-controls" style={{ position: "absolute", top: 10, left: 10, zIndex: 10 }}>
          <button onClick={() => drawRef.current.changeMode("draw_rectangle")}>Rectangle</button>
          <button onClick={() => drawRef.current.changeMode("draw_circle")}>Circle</button>

          <button onClick={() => drawRef.current?.deleteAll()}>Clear</button>

          <div style={{ marginTop: 10 }}>
            <input
              type="text"
              placeholder="Latitude"
              value={coords.lat}
              onChange={(e) => setCoords({ ...coords, lat: e.target.value })}
            />
            <input
              type="text"
              placeholder="Longitude"
              value={coords.lng}
              onChange={(e) => setCoords({ ...coords, lng: e.target.value })}
            />
            <button onClick={handleSearch}>Go</button>
          </div>

          {aoi && (
            <div style={{ marginTop: 10 }}>
              <button onClick={handleSave}>Save AOI</button>
            </div>
          )}
        </div>

        <div
          className="aoi-display"
          style={{ position: "absolute", bottom: 10, left: 10, background: "white", padding: 10, maxWidth: "300px", maxHeight: "200px", overflow: "auto" }}
        >
          <h4>AOI GeoJSON:</h4>
          <pre>{aoi ? JSON.stringify(aoi, null, 2) : "No AOI selected"}</pre>
        </div>
      </Map>
    </div>
  );
}
