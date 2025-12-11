import React, { useState } from "react";
import MagPage from "../Components/MapPage.jsx";
import CollapsibleCard from "../Components/CollapsibleCard.jsx";
import Header from "../Components/Header2.jsx";
import { Button } from 'antd';
import DropdownCustom from "../Components/DropdownCustom.jsx";
import Enchroachments from "../Components/Enchroachments.jsx";
import SliderSection from "../Components/SliderSection.jsx";

export default function LandingPage() {
  const [mapStyle, setMapStyle] = useState("mapbox://styles/mapbox/streets-v11");
  const [selectedPort, setSelectedPort] = useState(null);
  const [waterChangeData, setWaterChangeData] = useState(null);
  const [lostArea, setLostArea] = useState(null);

  const [legend, setLegend] = useState({
  labels: false,
  landmarks: false
  });

  const [sliderDates, setSliderDates] = useState({
  pre_date: "2016-02-17",
  post_date: "2023-01-11"
});

  // handler to update legend from Header
  const handleLegendChange = (changes) => {
    setLegend((prev) => ({ ...prev, ...changes }));
  };

  // function to pass down to Header and MapSettingsPopupButton
  const handleMapTypeChange = (styleKey) => {
    setMapStyle(`mapbox://styles/mapbox/${styleKey}`);
  };

  const handleSliderDates = async (pre_date, post_date) => {

  setSliderDates({ pre_date, post_date });

  if (selectedPort) {
    const url = `http://localhost:8000/analyze-water-change/${selectedPort.id}?pre_date=${pre_date}&post_date=${post_date}`;

    const res = await fetch(url);
    const data = await res.json();

    if (!data.error) {
      setWaterChangeData(data.lost_water_geojson);
      setLostArea(data.lost_area_ha);
    }
  }
};


  const handlePortClick = async (port) => {
    setSelectedPort(port); // keep map centered on port
    setWaterChangeData(null); // reset previous data
    setLostArea(null);
    const { pre_date, post_date } = sliderDates;

    try {
      const res = await fetch(
    `http://localhost:8000/analyze-water-change/${port.id}?pre_date=${pre_date}&post_date=${post_date}`
  );

  const data = await res.json();

      if (data.error) {
        console.error(data.error);
        setWaterChangeData(null);
        setLostArea(null);
      } else {
        setWaterChangeData(data.lost_water_geojson);
        setLostArea(data.lost_area_ha);
      }
    } catch (err) {
      console.error("Failed to fetch water change analysis:", err);
      setWaterChangeData(null);
      setLostArea(null);
    }
  };


  return (

    <div
    style={{
        height:"100vh",
        width:"100vw",
        position: "relative"
    }}>

      <MagPage mapStyle={mapStyle} legend={legend} selectedPort={selectedPort} waterChangeData={waterChangeData} lostArea={lostArea}/>


      <div>
        <Header onMapTypeChange={handleMapTypeChange}
                onLegendChange={handleLegendChange}
        />
      </div>


      <div
        style={{
          position: "absolute",
          top: "240px",
          right: "16px",
          marginLeft:"16px",
          width: "300px",
          maxWidth: "calc(100% - 32px)",
          zIndex: 2000,
          pointerEvents: "none",  
          margin:"0 auto"
          // marginTop:"300px"
        }}
      >
        <div style={{ position: "relative", pointerEvents: "auto", width:"100%"}}>
          {/* PORTS Card – stays in flow, expands freely */}
          <CollapsibleCard
            title="PORTS"
            style={{
              background: "white",
              borderRadius: "6px",
              width: "100%",
              boxShadow: "0px 4px 6px rgba(0, 0, 0, 0.1)",
              position: "relative",
              zIndex: 3000,  
            }}
          >
            <DropdownCustom onPortClick={handlePortClick} />
          </CollapsibleCard>

          {/* ENCROACHMENT LIST Card – taken out of flow, fixed offset */}
          <div style={{ position: "absolute", top: "150px", width: "100%", zIndex: 2500 }}>
            <CollapsibleCard
              title="ENCROACHMENT LIST"
              style={{
                background: "white",
                borderRadius: "6px",
                width: "100%",
                boxShadow: "0px 4px 6px rgba(0, 0, 0, 0.1)",
              }}
            >
              <Enchroachments lostArea={lostArea} selectedPort={selectedPort} />
            </CollapsibleCard>
          </div>
        </div>
      </div>


      
        
        <div
            style={{
              position: "absolute",
              bottom: "2%",
              zIndex: 1,
              width: "98%",   
            }}
          >
            <SliderSection onDatesChange={handleSliderDates} selectedPort={selectedPort}/>
        </div>
        
        

    </div>
   
  );
}