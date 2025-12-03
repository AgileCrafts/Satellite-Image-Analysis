import React, { useRef } from "react";
import Map, { NavigationControl, Marker } from "react-map-gl";
import "mapbox-gl/dist/mapbox-gl.css";

import {ZoomInOutlined, ZoomOutOutlined, ReloadOutlined } from "@ant-design/icons";
import { Divider } from 'antd';

export default function MapPage({ mapStyle, legend }) {
  const [viewState, setViewState] = React.useState({
    longitude: 90.5356,
    latitude: 23.5657,
    zoom: 12,
    bearing: 0,
    pitch: 0,
    zIndex: 1,
  });


  // Zoom In
  const zoomIn = () => {
    setViewState((prev) => ({ ...prev, zoom: prev.zoom + 1 }));
  };

  // Zoom Out
  const zoomOut = () => {
    setViewState((prev) => ({ ...prev, zoom: prev.zoom - 1 }));
  };


  const mapRef = React.useRef();

  React.useEffect(() => {
    const map = mapRef.current?.getMap();
    if (!map) return;

    const updateLayerVisibility = () => {
      if (map.getLayer('place-name')) {
        map.setLayoutProperty('place-name', 'visibility', legend.labels ? 'visible' : 'none');
      }
      if (map.getLayer('poi-label')) {  // landmarks layer
        map.setLayoutProperty('poi-label', 'visibility', legend.landmarks ? 'visible' : 'none');
      }
    };

    if (map.loaded()) {
      updateLayerVisibility();
    } else {
      map.on('load', updateLayerVisibility);
    }

    return () => {
      map.off('load', updateLayerVisibility);
    };
  }, [legend, mapStyle]);

  return (
    <div style={{ height: "100%", width: "100%", position: "relative" }}>
      <Map
        ref={mapRef}
        {...viewState}
        onMove={(evt) => setViewState(evt.viewState)}
        mapStyle={ mapStyle }
        mapboxAccessToken="pk.eyJ1IjoicnViYXlldHJhaXNhIiwiYSI6ImNtZmYxNjVyNzBkY3cya29hd3JwcHgxem8ifQ.9EWRZl8FOkbvcz5aVBDOpg"
        style={{ width: "100%", height: "100%" }}
      >
        <Marker longitude={90.5356} latitude={23.5657} />
      </Map>

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
        <button
          onClick={zoomIn}
          className="mapNav"
        >
          <ZoomInOutlined />
        </button>

        

        <button
          onClick={zoomOut}
          className="mapNav"
        >
          <ZoomOutOutlined />
        </button>

      </div>
    </div>
  );
}

