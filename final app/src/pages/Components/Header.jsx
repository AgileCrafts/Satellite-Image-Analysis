import React from "react";
import '@ant-design/v5-patch-for-react-19';
import { Card, Divider, Button, Row, Col } from "antd";
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
        height: "auto",
        // display: "grid",
        // gridTemplateColumns: "repeat(12, 1fr)", 
        gap: "16px",
        padding: "16px",
        background:"transparent",
        zIndex:1000,
        width:"100%",
        marginBottom:"200px"
      }}
    >
      <Row
        gutter={[16, 16]} 
        align="middle"
        style={{ height: "100%", pointerEvents: "auto" }}  
      ></Row>

      {/* Logo goes here */}
      <Col xs={24} sm={24} md={8} lg={6} xl={4}>
          <LogoSection/>
      </Col>

      {/* Date Selection goes here */}
      <Col xs={24} sm={24} md={8} lg={12} xl={16} style={{display:"flex", justifyContent:"center", width:"100%"}}>
          <CustomizeSection/>
      </Col>

      {/* Settings goes here */}
      <Col xs={24} sm={24} md={8} lg={6} xl={4}>
      <div style=
      {{
        
        display: "flex",
        flexDirection:"row",
        alignItems: "center",
        justifyContent:"center",
        width: "100%",
        height: "64px",
        gap: "10px",
        borderRadius: "12px",
        borderWidth: "1px",
        padding: "16px",
        backgroundColor:"white",
        // marginLeft:"5rem"
      }}>
            {/* <Button style={{padding:"20px", fontSize:"1rem"}}><SettingOutlined/> Preferences </Button> */}
            <MapSettingsPopupButton onMapTypeChange={onMapTypeChange} onLegendChange={onLegendChange}/>
            <Divider type="vertical" style={{height:"40px", borderColor:"lightgrey"}}/>
            <Button type="primary" style={{padding:"20px", fontSize:"1rem"}}>Login</Button>
      </div>
      </Col>

    </div>
  );
};

export default Header;