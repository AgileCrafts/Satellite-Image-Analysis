import React, { useEffect, useState, useRef } from "react";
import { MapContainer, TileLayer, FeatureGroup, useMap } from "react-leaflet";
import L from "leaflet";
import "leaflet-draw";
import "leaflet/dist/leaflet.css";
import "leaflet-draw/dist/leaflet.draw.css";

// DrawControls component (unchanged)
const DrawControls = ({ onAoiChange }) => {
  const map = useMap();

  useEffect(() => {
    if (!map) return;

    const drawnItems = new L.FeatureGroup();
    map.addLayer(drawnItems);

    const drawControl = new L.Control.Draw({
      position: "topright",
      draw: {
        rectangle: {
          shapeOptions: { color: "red" },
          showArea: false,
          repeatMode: false
        },
        polygon: { allowIntersection: false, shapeOptions: { color: "blue" } },
        polyline: true,
        circle: { shapeOptions: { color: "green" } },
        circlemarker: false,
        marker: false,
      },
      edit: {
        featureGroup: drawnItems,
        remove: true,
        edit: {
          selectedPathOptions: {
            maintainColor: true,
            opacity: 0.6
          }
        }
      },
    });

    map.addControl(drawControl);

    map.on(L.Draw.Event.CREATED, function (e) {
      const layer = e.layer;
      let geojson;
      let finalLayer = layer;

      if (layer instanceof L.Rectangle) {
        geojson = layer.toGeoJSON();
      } else if (layer instanceof L.Circle) {
        const latlng = layer.getLatLng();
        const radius = layer.getRadius();

        function circleToPolygon(center, radius, sides = 64) {
          const coords = [];
          const R = 6378137;
          const latRad = (center.lat * Math.PI) / 180;

          for (let i = 0; i < sides; i++) {
            const angle = (i * 2 * Math.PI) / sides;
            const dx = radius * Math.cos(angle);
            const dy = radius * Math.sin(angle);

            const dLat = (dy / R) * (180 / Math.PI);
            const dLng = (dx / (R * Math.cos(latRad))) * (180 / Math.PI);

            coords.push([center.lat + dLat, center.lng + dLng]);
          }
          coords.push(coords[0]);
          return coords;
        }

        const polygonCoords = circleToPolygon(latlng, radius);
        const polygon = L.polygon(polygonCoords, { color: "green" });

        geojson = polygon.toGeoJSON();
        finalLayer = polygon;
      } else {
        geojson = layer.toGeoJSON();
      }

      drawnItems.addLayer(finalLayer);
      onAoiChange(geojson);
    });

    map.on(L.Draw.Event.EDITED, function (e) {
      e.layers.eachLayer((layer) => {
        onAoiChange(layer.toGeoJSON());
      });
    });

    map.on(L.Draw.Event.DELETED, function () {
      onAoiChange(null);
    });

    return () => {
      map.removeControl(drawControl);
      map.removeLayer(drawnItems);
    };
  }, [map, onAoiChange]);

  return null;
};

// Updated MapMover component
const MapMover = ({ searchCoords }) => {
  const map = useMap();

  console.log("MapMover mounted"); // Debug to confirm rendering

  useEffect(() => {
    if (!searchCoords) return;
    console.log("MapMover received coords:", searchCoords);
    const { lat, lng } = searchCoords;
    if (!isNaN(lat) && !isNaN(lng)) {
      setTimeout(() => {
        map.flyTo([lat, lng], 14, { animate: false });
        console.log("Map moved to:", { lat, lng });
      }, 100);
    } else {
      console.log("Invalid coordinates in MapMover:", { lat, lng });
    }
  }, [searchCoords, map]);

  return null;
};

const MapPage = () => {
  const [aoi, setAoi] = useState(null);
  const [coords, setCoords] = useState({ lat: "", lng: "" });
  const [searchCoords, setSearchCoords] = useState(null); // Define searchCoords state
  const mapRef = useRef(null);

  const handleSearch = () => {
    const lat = parseFloat(coords.lat.trim());
    const lng = parseFloat(coords.lng.trim());
    if (isNaN(lat) || isNaN(lng)) {
      console.log("Invalid coordinates:", { lat: coords.lat, lng: coords.lng });
      return;
    }
    setSearchCoords({ lat, lng });
    console.log("Search triggered:", { lat, lng });
  };

  console.log("Current coords:", coords); // Debug state updates
  console.log("Leaflet version:", L.version); // Debug library version

  return (
    <div style={{ height: "100vh", width: "100vw" }}>
      {/* Search Bar */}
      <div
        style={{
          position: "absolute",
          top: 10,
          left: "50%",
          transform: "translateX(-50%)",
          zIndex: 1000,
          background: "white",
          padding: "8px 12px",
          borderRadius: "8px",
          display: "flex",
          gap: "8px",
        }}
      >
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

      <MapContainer
        center={[23.5657, 90.5356]}
        zoom={12}
        style={{ height: "100%", width: "100%" }}
        whenCreated={(mapInstance) => {
          mapRef.current = mapInstance;
          console.log("Map instance created:", mapRef.current);
        }}
      >
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution="&copy; OpenStreetMap contributors"
        />
        <FeatureGroup>
          <DrawControls onAoiChange={setAoi} />
        </FeatureGroup>
        <MapMover searchCoords={searchCoords} /> {/* Use searchCoords */}
      </MapContainer>

      {/* AOI GeoJSON display & save */}
      <div
        style={{
          position: "absolute",
          bottom: 10,
          left: "10px",
          zIndex: 1000,
          background: "white",
          padding: "10px",
          borderRadius: "8px",
          maxWidth: "400px",
          overflowWrap: "break-word",
        }}
      >
        <h4>AOI GeoJSON:</h4>
        <pre>{aoi ? JSON.stringify(aoi, null, 2) : "No AOI selected"}</pre>
        {aoi && (
          <button
            onClick={() => {
              const geojsonStr = JSON.stringify(aoi, null, 2);
              const blob = new Blob([geojsonStr], { type: "application/json" });
              const url = URL.createObjectURL(blob);
              const a = document.createElement("a");
              a.href = url;
              a.download = "aoi.geojson";
              a.click();
              URL.revokeObjectURL(url);
            }}
            style={{ marginTop: "10px", padding: "5px 10px" }}
          >
            Save AOI
          </button>
        )}
      </div>
    </div>
  );
};

export default MapPage;