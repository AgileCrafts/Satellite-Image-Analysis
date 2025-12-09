import React, { useRef, useEffect } from "react";
import Map, { NavigationControl, Marker, Source, Layer } from "react-map-gl";
import "mapbox-gl/dist/mapbox-gl.css";
import { ZoomInOutlined, ZoomOutOutlined, CloseOutlined, EnvironmentOutlined } from "@ant-design/icons";
import { Card, Typography, ConfigProvider, Button } from "antd";

import CustomButton1 from "./CustomButton1";

export default function MapPage({ mapStyle, legend, selectedPort, waterChangeData, lostArea}) {
  const [viewState, setViewState] = React.useState({
    longitude: 90.50,
    latitude: 23.56,
    zoom: 12,
    bearing: 0,
    pitch: 0,
    zIndex: 1,
  });

  const articles=
  ['https://www.thedailystar.net/news/bangladesh/news/blatant-river-grab-3908261',
    'https://www.thedailystar.net/news/bangladesh/crime-justice/news/evict-30-illegal-structures-turags-banks-hc-directs-govt-3812316'
    
  ];

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

    console.log(waterChangeData);

    const map = mapRef.current?.getMap();
    if (!map || !waterChangeData) return;

    if (map.getSource("mask-source")) {
      map.getSource("mask-source").setData(waterChangeData);

    }

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


  const [cardVisible, setCardVisible] = React.useState(false);
  const [cardData, setCardData] = React.useState(null);

  


  return (
    <div style={{ height: "100%", width: "100%", position: "absolute" }}>
      <Map
        ref={mapRef}
        {...viewState}
        onMove={(evt) => setViewState(evt.viewState)}
        mapStyle={mapStyle}
        mapboxAccessToken="pk.eyJ1IjoicnViYXlldHJhaXNhIiwiYSI6ImNtZmYxNjVyNzBkY3cya29hd3JwcHgxem8ifQ.9EWRZl8FOkbvcz5aVBDOpg"
        style={{ width: "100%", height: "100%" }}


        onClick={(e) => {
          const map = mapRef.current?.getMap();
          if (!map) return;

          // Detect if clicked feature belongs to encroachment layer
          const features = map.queryRenderedFeatures(e.point, {
            layers: ["mask-layer"],
          });

          if (features.length > 0) {
            const props = features[0].properties;

            // Open card with properties of encroachment
            setCardData({
              lostArea: lostArea || "Unknown",
              description: props?.description || "Encroachment detected."
            });

            setCardVisible(true);
          }
        }}

        
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

      {cardVisible && (
          <Card
            style={{
              position: "absolute",
              top: "100px",
              left: "10%",
              transform: "translateX(-10%)",
              width: "320px",
              zIndex: 3000,
            }}
            title="Encroachment Details"
            extra={<CloseOutlined onClick={() => setCardVisible(false)} />}
          >
            
            <div style={{padding: "10px"}}>
              <div className="img-div" style={{ height: "100px", background: "#eee", marginBottom: "10px" }}>
                <iframe
                    src={`https://www.google.com/maps?q=${selectedPort.latitude},${selectedPort.longitude}&hl=en&z=14&output=embed`}
                    width="100%"
                    height="100%"
                    style={{ border: 0 }}
                    allowFullScreen
                    loading="lazy"
                    referrerPolicy="no-referrer-when-downgrade"
                  />
              </div>
              <div className="des-div" style={{display:"flex", justifyContent:"space-between"}}>
                <div>
                    <h3>{selectedPort.port_name}</h3>
                    <p>{lostArea} ha Encroached</p>
                </div>
                
                <div>
                  <ConfigProvider wave={{disabled: true}}>
                 <Button variant="solid" 
                 onClick={() => {
                        const url = `https://www.google.com/maps?q=${selectedPort.latitude},${selectedPort.longitude}&hl=es;z=14&output=embed`;
                        window.open(url, '_blank');  
                      }}
                 >
                  
                  <EnvironmentOutlined/> Open Map</Button>
              </ConfigProvider>
                </div>
                
              </div>
              <div style={{margin:"10px 0px"}}>
                   <Button
                        type="primary"
                        onClick={() => {
                              const articleUrl = articles[selectedPort.id - 1]; // assuming id starts from 1
                              if (articleUrl) {
                                window.open(articleUrl, "_blank");
                                }
                      }}  
                      >
                        Read Article
                      </Button>

                </div>
              <div>
                      <Button  type="primary" style={{marginRight:"10px"}}>Confirm</Button>
                      <CustomButton1 buttonText="Dismiss"/>
              </div>
            </div>
              
          </Card>
        )}



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
