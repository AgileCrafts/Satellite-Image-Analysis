import React, { useRef, useEffect } from "react";
import Map, { NavigationControl, Marker, Source, Layer } from "react-map-gl";
import "mapbox-gl/dist/mapbox-gl.css";
import { ZoomInOutlined, ZoomOutOutlined, CloseOutlined, EnvironmentOutlined } from "@ant-design/icons";
import { Card, Typography, ConfigProvider, Button } from "antd";
import FloatingCard from "./FloatingCard";
import CustomButton1 from "./CustomButton1";


import "/src/pages/css/mapPage.css";


export default function MapPage({ mapStyle, legend, selectedPort, waterChangeData, lostArea}) {
  const [viewState, setViewState] = React.useState({
    longitude: 90.50,
    latitude: 23.56,
    zoom: 12,
    bearing: 0,
    pitch: 0,
    zIndex: 1,
  });

  

  const mapRef = useRef();

  useEffect(() => {
  if (!selectedPort) return;

  const lon = Number(selectedPort.longitude);
  const lat = Number(selectedPort.latitude);

  if (!isNaN(lon) && !isNaN(lat)) {
    setViewState((prev) => ({
      ...prev,
      longitude: lon,
      latitude: lat,
      zoom: 14,
    }));

    
  }
}, [selectedPort]);





  // Example red mask polygon (you can replace with your bbox later)
  // const maskGeoJSON = {
  //   type: "Feature",
  //   geometry: {
  //     type: "Polygon",
  //     coordinates: [
  //       [
  //         [90.530, 23.560],
  //         [90.540, 23.560],
  //         [90.540, 23.570],
  //         [90.530, 23.570],
  //         [90.530, 23.560]
  //       ]
  //     ]
  //   }
  // };

    useEffect(() => {
    if (!waterChangeData || !mapRef.current) return;
    const map = mapRef.current.getMap();

    if (!waterChangeData.features || waterChangeData.features.length === 0) return;

    // Flatten coordinates for bounding box
    const allCoords = waterChangeData.features.flatMap(feature => {
      const coords = feature.geometry.coordinates;
      // Handles Polygon and MultiPolygon
      if (feature.geometry.type === "Polygon") return coords.flat();
      if (feature.geometry.type === "MultiPolygon") return coords.flat(2);
      return [];
    });

    if (allCoords.length === 0) return;

    const lons = allCoords.map(c => c[0]);
    const lats = allCoords.map(c => c[1]);

    const minLon = Math.min(...lons);
    const maxLon = Math.max(...lons);
    const minLat = Math.min(...lats);
    const maxLat = Math.max(...lats);

    // Fit map to bounds with some padding
    map.fitBounds([[minLon, minLat], [maxLon, maxLat]], { padding: 50, duration: 1000 });
  }, [waterChangeData]);

  

  const maskGeoJSON = waterChangeData || null;

  // Zoom In
  const zoomIn = () => {
    setViewState((prev) => ({ ...prev, zoom: prev.zoom + 1 }));
  };

  // Zoom Out
  const zoomOut = () => {
    setViewState((prev) => ({ ...prev, zoom: prev.zoom - 1 }));
  };

  React.useEffect(() => {
    const map = mapRef.current?.getMap();
    if (!map) return;

    const updateLayerVisibility = () => {
      if (map.getLayer("place-name")) {
        map.setLayoutProperty(
          "place-name",
          "visibility",
          legend.labels ? "visible" : "none"
        );
      }
      if (map.getLayer("poi-label")) {
        map.setLayoutProperty(
          "poi-label",
          "visibility",
          legend.landmarks ? "visible" : "none"
        );
      }
    };

    if (map.loaded()) {
      updateLayerVisibility();
    } else {
      map.on("load", updateLayerVisibility);
    }

    return () => {
      map.off("load", updateLayerVisibility);
    };
  }, [legend, mapStyle]);




  return (
    <div style={{ height: "100%", width: "100%", position: "fixed" }}>
      <Map
        ref={mapRef}
        {...viewState}
        onMove={(evt) => setViewState(evt.viewState)}
        mapStyle={mapStyle}
        mapboxAccessToken="pk.eyJ1IjoicnViYXlldHJhaXNhIiwiYSI6ImNtZmYxNjVyNzBkY3cya29hd3JwcHgxem8ifQ.9EWRZl8FOkbvcz5aVBDOpg"
        style={{ width: "100%", height: "100%" }}


        // onClick={(e) => {
        //   const map = mapRef.current?.getMap();
        //   if (!map) return;

        //   // Detect if clicked feature belongs to encroachment layer
        //   const features = map.queryRenderedFeatures(e.point, {
        //     layers: ["mask-layer"],
        //   });

        //   if (features.length > 0) {
        //     const props = features[0].properties;

        //     // Open card with properties of encroachment
        //     setCardData({
        //       lostArea: lostArea || "Unknown",
        //       description: props?.description || "Encroachment detected."
        //     });

        //     setCardVisible(true);
        //   }
        //}}

        
      >

        {/* Red Mask Overlay */}
       {waterChangeData && (
          <Source id="mask-source" type="geojson" data={waterChangeData}>
            <Layer
              id="mask-layer"
              type="fill"
              paint={{
                "fill-color": "rgba(255, 0, 0, 0.3)",
                "fill-outline-color": "red",
              }}
            />
          </Source>
          
        )}

        {/* <Marker longitude={90.5356} latitude={23.5657} /> */}
        
      </Map>

      
      <FloatingCard selectedPort={selectedPort} lostArea={lostArea}/>
        



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
          zIndex: 2000
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
