import React, { useState } from "react";
import MagPage from "../Components/MapPage.jsx";
import CollapsibleCard from "../Components/CollapsibleCard.jsx";
import Header from "../Components/Header.jsx";
import { Button } from 'antd';
import DropwdownCustom from "../Components/DropdownCustom.jsx";
import Enchroachments from "../Components/Encroachments.jsx";
import SliderSection from "../Components/SliderSection.jsx";

export default function LandingPage() {
  const [mapStyle, setMapStyle] = useState("mapbox://styles/mapbox/streets-v11");

  const [legend, setLegend] = useState({
  labels: false,
  landmarks: false
  });

  // handler to update legend from Header
  const handleLegendChange = (changes) => {
    setLegend((prev) => ({ ...prev, ...changes }));
  };

  // function to pass down to Header and MapSettingsPopupButton
  const handleMapTypeChange = (styleKey) => {
    setMapStyle(`mapbox://styles/mapbox/${styleKey}`);
  };

  return (

    <div
    style={{
        height:"100vh",
        width:"100vw",
        position: "relative"
    }}>

        <Header onMapTypeChange={handleMapTypeChange}
                onLegendChange={handleLegendChange}
        />

        <CollapsibleCard title="PORTS" style={{
          position: 'absolute',
          top: '15%',
          right: '1rem',
          zIndex: 2000,
          background: 'white',
          // padding: '10px',
          borderRadius: '6px',
          width: '300px',
          boxShadow: '0px 4px 6px rgba(0, 0, 0, 0.1)',
        }}>
        <DropwdownCustom/>
        </CollapsibleCard>
    
     
        <CollapsibleCard title="ENCROACHMENT LIST" 
        style={{
          position: 'absolute',
          top: '40%',
          right: '1rem',
          zIndex: 1000,
          background: 'white',
          // padding: '5px',
          borderRadius: '6px',
          width: '300px',
          boxShadow: '0px 4px 6px rgba(0, 0, 0, 0.1)',
        }}>

        <Enchroachments/>
        </CollapsibleCard>

        <SliderSection/>
        <MagPage mapStyle={mapStyle} legend={legend}/>
        

    </div>
   
  );
}