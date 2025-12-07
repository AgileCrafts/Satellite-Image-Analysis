import React, { useState } from "react";
import MagPage from "../Components/MapPage.jsx";
import CollapsibleCard from "../Components/CollapsibleCard.jsx";
import Header from "../Components/Header2.jsx";
import { Button } from 'antd';
import DropwdownCustom from "../Components/DropdownCustom.jsx";
import Enchroachments from "../Components/Encroachments.jsx";
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
  pre_date: "2020-01-17",
  post_date: "2024-01-06"
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

      <div>
        <CollapsibleCard title="PORTS" style={{
          position: 'absolute',
          marginTop: '8%',
          right: '1%',
          zIndex: 2000,
          background: 'white',
          // padding: '10px',
          borderRadius: '6px',
          width: '20%',
          boxShadow: '0px 4px 6px rgba(0, 0, 0, 0.1)',
        }}>
        <DropwdownCustom onPortClick={handlePortClick}/>
        </CollapsibleCard>
    
     
        <CollapsibleCard title="ENCROACHMENT LIST" 
        style={{
          position: 'absolute',
          marginTop: '18%',
          right: '1%',
          zIndex: 1000,
          background: 'white',
          // padding: '5px',
          borderRadius: '6px',
          width: '20%',
          boxShadow: '0px 4px 6px rgba(0, 0, 0, 0.1)',
        }}>

        <Enchroachments lostArea={lostArea} selectedPort={selectedPort}/>
        </CollapsibleCard>
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