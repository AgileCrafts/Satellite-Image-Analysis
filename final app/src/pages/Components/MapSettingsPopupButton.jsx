// MapSettingsPopup.jsx
import React, { useState } from "react";
import { Button, Card, Radio, Checkbox, Divider } from "antd";
import { SettingOutlined, CloseOutlined} from "@ant-design/icons";

export default function MapSettingsPopupButton({ onMapTypeChange, onLegendChange }) {
  const [open, setOpen] = useState(false);

  const handleLegendChange = (e) => {
    onLegendChange({ [e.target.name]: e.target.checked });
  };

  return (
    <>
      {/* BUTTON */}
      <Button
        style={{
          padding:"20px", 
          fontSize:"1rem",
          zIndex:"9999"
        }}
        onClick={() => setOpen(true)}
      >
        <SettingOutlined /> Preferences
      </Button>

      {/* POPUP CARD */}
      {open && (
        <div
          style={{
            // position: "absolute",
            // margin: "0.3rem 0rem 0 0",
            position: "fixed",
            top: "4.5rem",      
            right:"2rem", 
            zIndex: 9999,
            width: "21rem",
            height:"12rem",
            padding: "10px",

          }}
        >
          <Card
            style={{
              width: "22rem",
              height:"17rem",
              borderTopLeftRadius: "12px",
              borderTopRightRadius: "12px",
              padding: "0.5rem 0 0 0.8rem"
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom:"0.2rem" }}>
              <h3 style={{ margin: 0 }}>Map Settings</h3>
              <Button type="text" onClick={() => setOpen(false)}>
                <CloseOutlined />
              </Button>
            </div>

            <Divider style={{margin:"0.2rem"}}/>

            {/* MAP TYPE SECTION */}
            <h4>Map Type</h4>
            <Radio.Group onChange={(e) => onMapTypeChange(e.target.value)} defaultValue="streets-v11">
            <div className="radio-img">
               <input
                type="radio"
                name="mapStyle"
                value="streets-v11"
                id="default"
                className="radio-input"
                defaultChecked
                onChange={(e) => onMapTypeChange(e.target.value)}
              />
                <label htmlFor="default" className="radio-label">
                <div className="image-container">
                    <img
                    src="/src/assets/map_streets.png"
                    alt="Streets"
                    className="radio-image"
                    />
                    <span className="image-text">Default</span>
                </div>
                </label>

                <input
                type="radio"
                name="mapStyle"
                value="satellite-streets-v11"
                id="satellitev11"
                className="radio-input"
                onChange={(e) => onMapTypeChange(e.target.value)}
                />
                <label htmlFor="satellitev11" className="radio-label">
                <div className="image-container">
                    <img
                    src="/src/assets/map_satellite.png"
                    alt="Satellite"
                    className="radio-image"
                    />
                    <span className="image-text" style={{color:"white"}}>Satellite</span>
                </div>
                </label>
            </div>
            </Radio.Group>


            <Divider style={{marginBottom:"0.5rem"}} />

            {/* LEGEND SECTION */}
            <h4>Legend</h4>
            <Checkbox
              name="labels"
              onChange={handleLegendChange}
            >
              Show Labels
            </Checkbox>
            <br />
            <Checkbox
              name="landmarks"
              onChange={handleLegendChange}
            >
              Show Landmarks
            </Checkbox>
          </Card>
        </div>
      )}
    </>
  );
}
