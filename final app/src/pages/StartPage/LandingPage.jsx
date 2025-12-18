import React, { useState } from "react";
import MagPage from "../Components/MapPage.jsx";
import CollapsibleCard from "../Components/CollapsibleCard.jsx";
import Header from "../Components/Header2.jsx";
import { Button ,Row,Col} from 'antd';
import DropdownCustom from "../Components/DropdownCustom.jsx";
import Enchroachments from "../Components/Enchroachments.jsx";
import SliderSection from "../Components/SliderSection.jsx";
import "../css/landingPage.css";

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

    <div  className="landing-container">

      <MagPage mapStyle={mapStyle} legend={legend} selectedPort={selectedPort} waterChangeData={waterChangeData} lostArea={lostArea}/>


      
      <div>
        <Header onMapTypeChange={handleMapTypeChange}
                onLegendChange={handleLegendChange}
        />
      </div>
      
      <div className="landing-sub-container">
      <div className="collapseCard-container" style={{zIndex:2000}}>
        <div className="landing-card-wrapper">
          {/* PORTS Card*/}
          <CollapsibleCard
            title="PORTS"
            className="ports-card"
            style={{zIndex:3000}}
          >
            <DropdownCustom onPortClick={handlePortClick} />
          </CollapsibleCard>

          {/* ENCROACHMENT LIST Card */}
          <div className="encroachment-container" style={{zIndex:2500}}>
            <CollapsibleCard
              title="ENCROACHMENT LIST"
              className="encroachment-card"
            >
              <Enchroachments lostArea={lostArea} selectedPort={selectedPort} />
            </CollapsibleCard>
          </div>
        </div>
      </div>
  
      </div>
        
        <div className="landing-slider"
            style={{
              zIndex: 1  
            }}
          >
            <SliderSection onDatesChange={handleSliderDates} selectedPort={selectedPort}/>
        </div>
        
        

    </div>
   
  );
}