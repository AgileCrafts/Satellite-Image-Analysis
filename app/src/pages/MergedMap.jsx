import '@ant-design/v5-patch-for-react-19';
import { message, Card, Row, Col, Spin } from 'antd';
import React, { useState, useEffect, useRef } from "react";
import Lightbox from "yet-another-react-lightbox";
import "yet-another-react-lightbox/styles.css";
import axios from "axios";
import MapPage from './MapPage'; 
import { ChangeMapInputs } from './ChangeMap'; 

const LEGENDS = [
  { color: '#0000FF', label: 'Stable Water (water → water)' },
  { color: '#FF0000', label: 'Water Receded (water → land)' },
  { color: '#00FF00', label: 'New Water (land → water)' },
  { color: '#808080', label: 'Stable Land (land → land)' },
];

const BUILTUP_LEGENDS = [
  { color: '#C800C8', label: 'New Built-up Area (growth)' },
  { color: '#FFA500', label: 'Stable Built-up Area' },
  { color: '#00FFFF', label: 'Reduced Built-up Area' },
  { color: '#808080', label: 'Non-Built-up Area' },
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
  const [builtupAnalysisImg, setBuiltupAnalysisImg] = useState(null);
  const [builtupCollageImg, setBuiltupCollageImg] = useState(null);
  const [extraImage, setExtraImage] = useState("/annotated_mapbox.png");
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

  const openLightbox = (imgSrc) => {
    setLightboxSlides([{ src: imgSrc }]);
    setLightboxOpen(true);
  };

  return (
    <div className="dashboard" style={{ display: "flex", flexDirection: "column", minHeight: "100vh" }}>
      {/* First Row: Map and Input Fields */}
      <div style={{ display: "flex", minHeight: "500px", flexShrink: 0 }}>
        {/* Map Section */}
        <div style={{ flex: 1, position: "relative" }}>
          <MapPage
            aoi={aoi}
            setAoi={setAoi}
            coords={coords}
            setCoords={setCoords}
            searchCoords={searchCoords}
            setSearchCoords={setSearchCoords}
            drawRef={drawRef}
            setAois={setAois}
          />
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
            setBuiltupAnalysisImg={setBuiltupAnalysisImg}
            setBuiltupCollageImg={setBuiltupCollageImg}
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
                    <p style={{ marginBottom: '12px', color: '#050505ff', fontSize: '14px' }}>
                      Analysis of water body changes between {selectedDates?.from_date} and {selectedDates?.to_date}. Red areas can be marked for water loss and can be checked for any issues. Green areas are a good sign that water has been increased in those places.
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
                        <p style={{ marginBottom: '12px', color: '#0c0a0aff', fontSize: '14px', textAlign: 'right' }}>
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
            {builtupAnalysisImg && (
              <Row gutter={[16, 16]} style={{ marginBottom: '16px' }}>
                <Col xs={24}>
                  <Card
                    title="Built-up Area Analysis"
                    hoverable
                    className="summary-card"
                    onClick={() => openLightbox(builtupAnalysisImg)}
                  >
                    <p style={{ marginBottom: '12px', color: '#050505ff', fontSize: '14px' }}>
                      Analysis of built-up area changes between {selectedDates?.from_date} and {selectedDates?.to_date}. Purple areas should be checked for new infrastructures.
                    </p>
                    <div className="image-legend-container">
                      <img
                      src={builtupAnalysisImg}
                      alt="Built-up Analysis"
                      className="thumbnail"
                      style={{ width: '400px', height: '200px', borderRadius: '6px', cursor: 'pointer' }}
                    />
                      <div className="legend-container">
                        {BUILTUP_LEGENDS.map((legend) => (
                          <LegendItem key={legend.color} {...legend} />
                        ))}
                      </div>
                    </div>
                  </Card>
                </Col>
              </Row>
            )}
            {builtupCollageImg && (
              <Row gutter={[16, 16]} style={{ marginBottom: '16px' }}>
                <Col xs={24}>
                  <Card
                    title="Built-up Image Comparison"
                    hoverable
                    className="summary-card"
                    onClick={() => openLightbox(builtupCollageImg)}
                    headStyle={{ textAlign: 'right' }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                      <div style={{ maxWidth: '600px' }}>
                        <p style={{ marginBottom: '12px', color: '#000000ff', fontSize: '14px', textAlign: 'right' }}>
                          Composite view of built-up area imagery from the selected period.
                        </p>
                        <img
                          src={builtupCollageImg}
                          alt="Built-up Collage"
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
                    <p style={{ marginBottom: '12px', color: '#000000ff', fontSize: '14px' }}>
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

            {(waterImg && collageImg && builtupAnalysisImg && showTestImage) && (
              <Row gutter={[16, 16]} style={{ marginBottom: '16px' }}>
                <Col xs={24}>
                  <Card
                    title="Detected Brick Kilns"
                    hoverable
                    className="summary-card"
                    onClick={() => openLightbox(extraImage)}
                  >
                    <p style={{ marginBottom: '12px', color: '#000000ff', fontSize: '14px' }}>
                      Annotated image highlighting detected brick kilns near the area of interest.
                    </p>
                    <img
                      src={extraImage}
                      alt="Brick Kiln"
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