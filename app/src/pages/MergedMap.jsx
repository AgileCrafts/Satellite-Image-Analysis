import '@ant-design/v5-patch-for-react-19';
import { message, Card, Row, Col, Spin, Alert } from 'antd';
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
  const [areaStats, setAreaStats] = useState(null);
  const [waterAreaStats, setWaterAreaStats] = useState(null);
  const [changeMapId, setChangeMapId] = useState(null);
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

  useEffect(() => {
    if (changeMapId) {
      const token = localStorage.getItem("authToken");
      fetch(`http://localhost:8000/change_maps/${changeMapId}/builtup_collage_image`, {
        headers: { Authorization: `Bearer ${token}` },
      })
        .then((res) => {
          if (!res.ok) throw new Error(`Failed to fetch builtup collage image: ${res.statusText}`);
          const builtupAreaStatsHeader = res.headers.get('X-Builtup-Area-Stats');
          console.log("X-Builtup-Area-Stats header:", builtupAreaStatsHeader);
          if (builtupAreaStatsHeader) {
            try {
              setAreaStats(JSON.parse(builtupAreaStatsHeader));
            } catch (e) {
              console.error("Failed to parse X-Builtup-Area-Stats:", e, "Raw header:", builtupAreaStatsHeader);
              setAreaStats(null);
            }
          } else {
            setAreaStats(null);
            console.warn("X-Builtup-Area-Stats header not found");
          }
          return res.blob();
        })
        .then((blob) => setBuiltupCollageImg(URL.createObjectURL(blob)))
        .catch((err) => {
          console.error("Builtup collage image error:", err);
          message.error("Failed to load builtup collage image");
        });


        // Fetch water analysis image and water area stats
      fetch(`http://localhost:8000/change_maps/${changeMapId}/water_analysis_image`, {
        headers: { Authorization: `Bearer ${token}` },
      })
        .then((res) => {
          if (!res.ok) throw new Error(`Failed to fetch water image: ${res.statusText}`);
          const waterAreaStatsHeader = res.headers.get('X-Water-Area-Stats');
          console.log("X-Water-Area-Stats header:", waterAreaStatsHeader);
          if (waterAreaStatsHeader) {
            try {
              setWaterAreaStats(JSON.parse(waterAreaStatsHeader));
            } catch (e) {
              console.error("Failed to parse X-Water-Area-Stats:", e, "Raw header:", waterAreaStatsHeader);
              setWaterAreaStats(null);
            }
          } else {
            setWaterAreaStats(null);
            console.warn("X-Water-Area-Stats header not found");
          }
          
        })
        .catch((err) => {
          console.error("Water image error:", err);
          message.error("Failed to load water analysis image");
        });

    }
  }, [changeMapId]);


  const openLightbox = (imgSrc) => {
    setLightboxSlides([{ src: imgSrc }]);
    setLightboxOpen(true);
  };

  const columns = [
    {
      title: 'Category',
      dataIndex: 'category',
      key: 'category',
    },
    {
      title: 'Area (Hectares)',
      dataIndex: 'area',
      key: 'area',
      render: (text) => Number(text).toFixed(2),
    },
    {
      title: 'Color Indicator',
      dataIndex: 'color',
      key: 'color',
      render: (color) => (
        <span style={{
          display: 'inline-block',
          width: '20px',
          height: '20px',
          backgroundColor: `rgb(${color[0]}, ${color[1]}, ${color[2]})`,
          borderRadius: '4px',
          border: '1px solid #333',
        }}></span>
      ),
    },
  ];

  const areaData = areaStats
    ? Object.entries(areaStats).map(([category, { area_ha, color }]) => {
        console.log(`Processing category: ${category}, Data:`, { area_ha, color });
        if (!area_ha || !color || !Array.isArray(color) || color.length !== 3) {
          console.error(`Invalid data for category ${category}:`, { area_ha, color });
          return null;
        }
        return {
          key: category,
          category,
          area: area_ha,
          color,
        };
      }).filter(item => item !== null)
    : [];


    const waterAreaData = waterAreaStats
    ? Object.entries(waterAreaStats).map(([category, { area_ha, color }]) => {
        console.log(`Processing water category: ${category}, Data:`, { area_ha, color });
        if (!area_ha || !color || !Array.isArray(color) || color.length !== 3) {
          console.error(`Invalid data for water category ${category}:`, { area_ha, color });
          return null;
        }
        return {
          key: category,
          category,
          area: area_ha,
          color,
        };
      }).filter(item => item !== null)
    : [];

  const handleSave = (newChangeMapId) => {
    setChangeMapId(newChangeMapId);
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
            setAreaStats={setAreaStats}
            setWaterAreaStats={setWaterAreaStats}
            handleSave={handleSave}
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




                    {waterAreaStats && (
                        <div style={{ marginTop: '24px', lineHeight: 1.6 }}>
                          <h3 style={{ fontSize: '18px', fontWeight: '700', color: '#333' }}>
                            Water Analysis Summary
                          </h3>
                          <ul
                            style={{
                              marginLeft: '20px',
                              color: '#0c0b0b',
                              fontSize: '14px',
                              listStyle: 'none',
                              padding: 0,
                              marginTop: '12px',
                            }}
                          >
                            {Object.entries(waterAreaStats).map(([key, value]) => (
                              <li key={key} style={{ marginBottom: '10px' }}>
                                <strong>{key}:</strong> {value.area_ha?.toFixed(2) ?? 'N/A'} ha
                              </li>
                            ))}
                            <li style={{ marginTop: '16px' }}>
                              <strong>Total Water Area:</strong>{' '}
                              {(() => {
                                console.log('waterAreaStats:', waterAreaStats);
                                const waterValues = Object.entries(waterAreaStats)
                                  .filter(([key]) => ['Persistent Water', 'New Water'].includes(key)) // Match with your data keys
                                  .map(([, value]) => Number(value.area_ha) || 0);
                                console.log('Water values:', waterValues);
                                const total = waterValues.reduce((sum, area) => sum + area, 0).toFixed(2);
                                console.log('Calculated water total:', total);
                                return total || '0.00';
                              })()}{' '}
                              ha
                          </li>
                          </ul>
                          {(() => {
                            const totalWaterArea = Object.entries(waterAreaStats)
                              .reduce((sum, [, value]) => sum + (Number(value.area_ha) || 0), 0);
                            const significantLossThreshold = Math.max(totalWaterArea * 0.05, 1); // 10% of total, minimum 1 ha
                            const rapidExpansionThreshold = 0.05; // 5% of relevant area
                            const relevantWaterArea = Object.entries(waterAreaStats)
                              .filter(([key]) => ['Persistent Water', 'New Water'].includes(key))
                              .reduce((sum, [, value]) => sum + (Number(value.area_ha) || 0), 0);

                            return (
                              <>
                                {waterAreaStats['Lost Water']?.area_ha > significantLossThreshold && (
                                  <p
                                    style={{
                                      display: 'flex',
                                      alignItems: 'center',
                                      backgroundColor: '#fdecea',
                                      color: '#611a15',
                                      border: '1px solid #f5c6cb',
                                      borderRadius: '6px',
                                      padding: '10px 12px',
                                      fontWeight: 500,
                                      fontSize: '14px',
                                      marginTop: '12px',
                                      boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
                                    }}
                                  >
                                    <span style={{ fontSize: '18px', marginRight: '8px' }}>⚠️</span>
                                    <b>Significant water loss detected</b> — possible drought or human intervention.
                                  </p>
                                )}
                                {/* {waterAreaStats['New Water']?.area_ha / relevantWaterArea > rapidExpansionThreshold && (
                                  <p
                                    style={{
                                      display: 'flex',
                                      alignItems: 'center',
                                      backgroundColor: '#fdecea',
                                      color: '#95170eff',
                                      border: '1px solid #f5c6cb',
                                      borderRadius: '6px',
                                      padding: '10px 12px',
                                      fontWeight: 500,
                                      fontSize: '14px',
                                      marginTop: '12px',
                                      boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
                                    }}
                                  >
                                    <span style={{ fontSize: '18px', marginRight: '8px' }}>⚠️</span>
                                    <b>Rapid water expansion detected</b>  — consider reviewing water management plans.
                                  </p>
                                )} */}
                              </>
                            );
                          })()}
                          <p style={{ marginTop: '16px', color: '#000' }}>
                            These insights aid in water resource management and environmental planning.
                          </p>
                        </div>
                      )}


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




                    {areaStats && (
                      <div style={{ marginTop: '24px', lineHeight: 1.6 }}>
                        <h3 style={{ fontSize: '18px', fontWeight: '700', color: '#333' }}>
                          Built-up Analysis Summary
                        </h3>
                        <ul
                          style={{
                            marginLeft: '20px',
                            color: '#0c0b0b',
                            fontSize: '14px',
                            listStyle: 'none',
                            padding: 0,
                            marginTop: '12px',
                          }}
                        >
                          {Object.entries(areaStats).map(([key, value]) => (
                            <li key={key} style={{ marginBottom: '10px' }}>
                              <strong>{key}:</strong> {value.area_ha?.toFixed(2) ?? 'N/A'} ha
                            </li>
                          ))}
                          <li style={{ marginTop: '16px' }}>
                            <strong>Total Built-up Area:</strong>{' '}
                            {(() => {
                              console.log('areaStats:', areaStats);
                              const builtupValues = Object.entries(areaStats)
                                .filter(([key]) => ['New Built-up', 'Persistent Built-up'].includes(key))
                                .map(([, value]) => Number(value.area_ha) || 0);
                              console.log('Built-up values:', builtupValues);
                              const total = builtupValues.reduce((sum, area) => sum + area, 0).toFixed(2);
                              console.log('Calculated total built-up area:', total);
                              return total || '0.00';
                            })()}{' '}
                            ha
                          </li>
                        </ul>
                        {(() => {
                          const totalBuiltupArea = Object.entries(areaStats)
                            .reduce((sum, [, value]) => sum + (Number(value.area_ha) || 0), 0);
                          const significantLossThreshold = Math.max(totalBuiltupArea * 0.10, 1); // 10% of total, minimum 1 ha
                          const rapidExpansionThreshold = 0.05; // 5% of relevant area
                          const relevantBuiltupArea = Object.entries(areaStats)
                            .filter(([key]) => ['New Built-up', 'Persistent Built-up'].includes(key))
                            .reduce((sum, [, value]) => sum + (Number(value.area_ha) || 0), 0);

                          return (
                            <>
                              {areaStats['Reduced Built-up']?.area_ha > significantLossThreshold && (
                                <p
                                  style={{
                                    display: 'flex',
                                    alignItems: 'center',
                                    backgroundColor: '#fdecea',
                                    color: '#f89538ff',
                                    border: '1px solid #f5c6cb',
                                    borderRadius: '6px',
                                    padding: '10px 12px',
                                    fontWeight: 500,
                                    fontSize: '14px',
                                    marginTop: '12px',
                                    boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
                                  }}
                                >
                                  <span style={{ fontSize: '18px', marginRight: '8px' }}>⚠️</span>
                                  <b>Significant loss in built-up areas</b> — possible redevelopment or flood impact.
                                </p>
                              )}
                              {areaStats['New Built-up']?.area_ha / relevantBuiltupArea > rapidExpansionThreshold && (
                                <p
                                  style={{
                                    display: 'flex',
                                    alignItems: 'center',
                                    backgroundColor: '#fdecea',
                                    color: '#95170eff',
                                    border: '1px solid #f5c6cb',
                                    borderRadius: '6px',
                                    padding: '10px 12px',
                                    fontWeight: 500,
                                    fontSize: '14px',
                                    marginTop: '12px',
                                    boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
                                  }}
                                >
                                  <span style={{ fontSize: '18px', marginRight: '8px' }}>⚠️</span>
                                  <b>Rapid urban expansion detected</b> — consider reviewing land-use zoning and infrastructure plans.
                                </p>
                              )}

                              
                            </>
                          );
                        })()}
                        <p style={{ marginTop: '16px', color: '#000' }}>
                          These insights help inform strategic planning, infrastructure management, and sustainable development.
                        </p>
                      </div>
                    )}
              




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