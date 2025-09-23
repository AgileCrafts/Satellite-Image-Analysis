import '@ant-design/v5-patch-for-react-19';
import { message, Card, Row, Col, Spin } from 'antd';
import React, { useState, useEffect, useRef } from "react";
import Map, { NavigationControl } from "react-map-gl";
import MapboxDraw from "@mapbox/mapbox-gl-draw";
import "mapbox-gl/dist/mapbox-gl.css";
import "@mapbox/mapbox-gl-draw/dist/mapbox-gl-draw.css";
import Lightbox from "yet-another-react-lightbox";
import "yet-another-react-lightbox/styles.css";
import axios from "axios";
import { DrawControl, MapMover } from './MapPage'; // Adjust path as needed
import { ChangeMapInputs } from './ChangeMap'; // Adjust path as needed

const LEGENDS = [
  { color: '#0000FF', label: 'Stable Water (water → water)' },
  { color: '#FF0000', label: 'Water Receded (water → land)' },
  { color: '#00FF00', label: 'New Water (land → water)' },
  { color: '#808080', label: 'Stable Land (land → land)' },
];

const LegendItem = ({ color, label }) => (
  <div style={{ display: 'flex', alignItems: 'center', marginBottom: '8px' }}>
    <span style={{
      display: 'inline-block',
      width: '20px',
      height: '20px',
      backgroundColor: color,
      marginRight: '10px',
      borderRadius: '4px',
      border: '1px solid #333',
      boxShadow: '0 2px 4px rgba(0, 0, 0, 0.1)'
    }}></span>
    <span style={{ fontSize: '14px', color: '#333' }}>{label}</span>
  </div>
);

const MergedMapPage = () => {
  const [aoi, setAoi] = useState(null);
  const [coords, setCoords] = useState({ lat: "", lng: "" });
  const [searchCoords, setSearchCoords] = useState(null);
  const [fromDate, setFromDate] = useState(null);
  const [toDate, setToDate] = useState(null);
  const [aois, setAois] = useState([]);
  const [selectedAoi, setSelectedAoi] = useState("");
  const [selectedDates, setSelectedDates] = useState(null);
  const [waterImg, setWaterImg] = useState(null);
  const [collageImg, setCollageImg] = useState(null);
  const [showTestImage, setShowTestImage] = useState(false);
  const [loadingMessage, setLoadingMessage] = useState("");
  const [lightboxOpen, setLightboxOpen] = useState(false);
  const [lightboxSlides, setLightboxSlides] = useState([]);
  const drawRef = useRef(null);

  useEffect(() => {
    const fetchAois = async () => {
      try {
        const token = localStorage.getItem("authToken");
        if (!token) {
          console.error("No auth token found in localStorage");
          setAois([]);
          return;
        }
        const res = await axios.get("http://127.0.0.1:8000/aois", {
          headers: { Authorization: `Bearer ${token}` },
        });
        console.log("Full response from /aois:", res);
        if (Array.isArray(res.data)) {
          setAois(res.data);
        } else {
          console.error("AOI response is not an array:", res.data);
          setAois([]);
        }
      } catch (err) {
        console.error("Failed to fetch AOIs:", err);
        setAois([]);
      }
    };
    fetchAois();
  }, []);

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

  const openLightbox = (imgSrc) => {
    setLightboxSlides([{ src: imgSrc }]);
    setLightboxOpen(true);
  }


  return (
    <div className="dashboard" style={{ display: "flex", flexDirection: "column", minHeight: "100vh" }}>
      {/* First Row: Map and Input Fields */}
      <div style={{ display: "flex", minHeight: "500px", flexShrink: 0 }}>
        {/* Map Section */}
        <div style={{ flex: 1, position: "relative" }}>
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
            {/* AOI display */}
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
                      a.download = "aoi.geojson";
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
                        const res = await axios.get("http://127.0.0.1:8000/aois", {
                          headers: { Authorization: `Bearer ${token}` },
                        });
                        if (Array.isArray(res.data)) {
                          setAois(res.data);
                        }
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
        {/* Input Fields Section */}
        <div className="change-map-container">
          <ChangeMapInputs
            fromDate={fromDate}
            setFromDate={setFromDate}
            toDate={toDate}
            setToDate={setToDate}
            aois={aois}
            selectedAoi={selectedAoi}
            setSelectedAoi={setSelectedAoi}
            selectedDates={selectedDates}
            setSelectedDates={setSelectedDates}
            setWaterImg={setWaterImg}
            setCollageImg={setCollageImg}
            setShowTestImage={setShowTestImage}
            setLoadingMessage={setLoadingMessage}
          />
        </div>
      </div>
      {/* Second Row: Summary Section */}
      <div style={{ padding: "20px", flexShrink: 0, background: "#f0f4f8" }}>
        {loadingMessage && (
          <div style={{ textAlign: 'center', marginBottom: '24px' }}>
            <Spin size="large" />
            <p style={{ fontWeight: '600', marginTop: '12px', color: '#333' }}>{loadingMessage}</p>
          </div>
        )}
        {(waterImg || collageImg || showTestImage) && (
          <div className="summary-container">
            {waterImg && (
              <Row gutter={[16, 16]} style={{ marginBottom: '16px' }}>
                <Col xs={24}>
                  <Card
                    title="Water Change Analysis"
                    hoverable
                    className="summary-card"
                    onClick={() => openLightbox(waterImg)}
                  >
                    <p style={{ marginBottom: '12px', color: '#555', fontSize: '14px' }}>
                      Analysis of water body changes between {selectedDates?.from_date} and {selectedDates?.to_date}.
                    </p>
                    <div className="image-legend-container">
                      <img
                        src={waterImg}
                        alt="Water Analysis"
                        className="thumbnail"
                        style={{ width: '400px', height: '200px', borderRadius: '6px', cursor: 'pointer' }}
                      />
                      <div className="legend-container">
                        {LEGENDS.map((legend) => (
                          <LegendItem key={legend.color} {...legend} />
                        ))}
                      </div>
                    </div>
                  </Card>
                </Col>
              </Row>
            )}
            {collageImg && (
              <Row gutter={[16, 16]} style={{ marginBottom: '16px' }}>
                <Col xs={24}>
                  <Card
                    title="Satellite Image Comparison"
                    hoverable
                    className="summary-card"
                    onClick={() => openLightbox(collageImg)}
                    headStyle={{ textAlign: 'right' }}
                    
                  >
                    <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                      <div style={{ maxWidth: '600px' }}>
                        <p style={{ marginBottom: '12px', color: '#555', fontSize: '14px', display: 'flex', justifyContent: 'flex-end' }}>
                          Composite view of satellite imagery from the selected period.
                        </p>
                        <img
                          src={collageImg}
                          alt="Collage"
                          className="thumbnail"
                          style={{ width: '100%', borderRadius: '6px', cursor: 'pointer' }}
                        />
                      </div>
                    </div>
                  </Card>
                </Col>
              </Row>
            )}
            {showTestImage && (
              <Row gutter={[16, 16]} style={{ marginBottom: '16px' }}>
                <Col xs={24}>
                  <Card
                    title="Detected Boats"
                    hoverable
                    className="summary-card"
                    onClick={() => openLightbox("/annotated_test5.png")}
                  >
                    <p style={{ marginBottom: '12px', color: '#555', fontSize: '14px' }}>
                      Annotated image highlighting detected boats in the area of interest.
                    </p>
                    <img
                      src="/annotated_test5.png"
                      alt="Test5"
                      className="thumbnail"
                      style={{ width: '400px', height: '200px', borderRadius: '6px', cursor: 'pointer' }}
                    />
                  </Card>
                </Col>
              </Row>
            )}
          </div>
        )}
        <Lightbox
          open={lightboxOpen}
          close={() => setLightboxOpen(false)}
          slides={lightboxSlides}
          carousel={{ finite: true }}
          controller={{ showNavigation: false, closeOnBackdropClick: true }}
          animation={{ swipe: 0 }}
        />
      </div>
    </div>
  );
};

export default MergedMapPage;