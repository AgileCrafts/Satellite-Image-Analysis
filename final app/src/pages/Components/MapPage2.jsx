import React, { useRef, useEffect, useState } from "react";
import { MapContainer, TileLayer, Marker, Popup, GeoJSON, useMap } from "react-leaflet";
import { ZoomInOutlined, ZoomOutOutlined } from "@ant-design/icons";
import { Card, Typography, ConfigProvider, Button } from "antd";
import FloatingCard from "./FloatingCard";
import CustomButton1 from "./CustomButton1";
import L from "leaflet";  // Import Leaflet directly
import "/src/pages/css/mapPage.css";
import 'leaflet/dist/leaflet.css';

// Leaflet Map Setup
export default function MapPage({ mapStyle, legend, selectedPort, waterChangeData, lostArea }) {
  const [viewState, setViewState] = useState({
    latitude: 23.56,
    longitude: 90.50,
    zoom: 12,
  });

  const mapRef = useRef();

  // Adjust map view based on selected port
  useEffect(() => {
    if (!selectedPort) return;

    const lon = Number(selectedPort.longitude);
    const lat = Number(selectedPort.latitude);

    if (!isNaN(lon) && !isNaN(lat)) {
      setViewState({
        latitude: lat,
        longitude: lon,
        zoom: 14,
      });
    }
  }, [selectedPort]);

  // Handle zoom in
  const zoomIn = () => {
    setViewState((prev) => ({ ...prev, zoom: prev.zoom + 1 }));
  };

  // Handle zoom out
  const zoomOut = () => {
    setViewState((prev) => ({ ...prev, zoom: prev.zoom - 1 }));
  };

  // Handle the update of the mask layer when waterChangeData updates
  useEffect(() => {
    if (!waterChangeData) return;
    console.log(waterChangeData);
  }, [waterChangeData]);

  return (
    <div style={{ height: "100%", width: "100%", position: "fixed" }}>
      {/* Leaflet Map */}
      <MapContainer
        center={[viewState.latitude, viewState.longitude]}
        zoom={viewState.zoom}
        style={{ width: "100%", height: "100%" }}
        whenCreated={(mapInstance) => { mapRef.current = mapInstance; }}
      >
        {/* TileLayer */}
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        />

        {/* Mask Layer - Water Change Data (GeoJSON) */}
        {waterChangeData && (
          <GeoJSON data={waterChangeData} 
            style={{
              fillColor: "red",
              weight: 2,
              opacity: 1,
              color: "red",
              fillOpacity: 0.3,
            }}
          />
        )}

        {/* Custom Marker for Selected Port */}
        {selectedPort && (
          <Marker position={[selectedPort.latitude, selectedPort.longitude]}>
            <Popup>{selectedPort.name}</Popup>
          </Marker>
        )}

      </MapContainer>

      {/* Floating Card */}
      <FloatingCard selectedPort={selectedPort} lostArea={lostArea} />

      {/* Custom Navigation Controls */}
      <div
        style={{
          position: "absolute",
          top: "100px",
          left: "20px",
          display: "flex",
          flexDirection: "column",
          background: "transparent",
          borderRadius: "6px",
          boxShadow: "0 2px 8px rgba(0,0,0,0.15)",
          overflow: "hidden",
          zIndex: 2000,
        }}
      >
        <button onClick={zoomIn} className="mapNav">
          <ZoomInOutlined />
        </button>

        <button onClick={zoomOut} className="mapNav">
          <ZoomOutOutlined />
        </button>
      </div>
    </div>
  );
}
