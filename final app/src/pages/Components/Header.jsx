import React from "react";
import '@ant-design/v5-patch-for-react-19';
import { Card, Divider, Button } from "antd";
const { Meta } = Card;
import LogoSection from "./LogoSection";
import CollapsibleCard from "./CollapsibleCard";
import MapSettingsPopupButton from "./MapSettingsPopupButton";
import {SettingOutlined } from "@ant-design/icons";
import CustomizeSection from "./CustomizeSection";

const Header = ({ onMapTypeChange, onLegendChange }) => {
  return (
    // Card Starts from here
    <div
      style={{
        position:"fixed",
        height: "108px",
        display: "grid",
        gridTemplateColumns: "repeat(12, 1fr)", 
        gap: "16px",
        padding: "16px",
        background:"transparent",
        zIndex:5000,
        width:"100%"
      }}
      className="card-grid"
    >
      {/* Logo goes here */}
      <div style={{ gridColumn: "span 2" }}>
          <LogoSection/>
      </div>

      {/* Date Selection goes here */}
      <div style={{gridColumn: "span 7", display:"flex", justifyContent:"center", width:"100%"}}>
          <CustomizeSection/>
      </div>

      {/* Settings goes here */}
      <div style={{gridColumn: "span 3",
        display: "flex",
        flexDirection:"row",
        alignItems: "center",
        justifyContent:"center",
        width: "18.75rem",
        height: "64px",
        gap: "10px",
        borderRadius: "12px",
        borderWidth: "1px",
        padding: "16px",
        backgroundColor:"white",
        marginLeft:"5rem"
      }}>
            {/* <Button style={{padding:"20px", fontSize:"1rem"}}><SettingOutlined/> Preferences </Button> */}
            <MapSettingsPopupButton onMapTypeChange={onMapTypeChange} onLegendChange={onLegendChange}/>
            <Divider type="vertical" style={{height:"40px", borderColor:"lightgrey"}}/>
            <Button type="primary" style={{padding:"20px", fontSize:"1rem"}}>Login</Button>
      </div>


    </div>
  );
};

export default Header;