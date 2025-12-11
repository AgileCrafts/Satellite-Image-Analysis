import React from "react";
import { Row, Col, Divider, Button } from "antd";
import LogoSection from "./LogoSection";
import MapSettingsPopupButton from "./MapSettingsPopupButton";
import CustomizeSection from "./CustomizeSection";

const Header = ({ onMapTypeChange, onLegendChange }) => {
  return (
    <div
      style={{
        position: "relative",
        top: 0,
        left: 0,
        width: "100%",
        height: "auto",
        // display: "flex",
        // justifyContent: "center", 
        zIndex: 5000,
        padding: "16px 0px",
        background: "transparent",
        // flexWrap:"wrap"
      }}
    >
      <Row
        gutter={16}
        wrap
        // justify="space-between"
        align="middle"
        style={{
          width: "100%"
        }}
      >
        {/* Logo */}
        <Col
          xs={24} sm={8} md={8} lg={7} xl={5} 
          style={{
            display: "flex",
            justifyContent: "flex-start",
            alignItems: "center",
            width:"100%",
            marginBottom:"10px"
          }}
        >
          <LogoSection />
        </Col>

        {/* Date Selection */}
        <Col
          xs={24} sm={8} md={8} lg={10} xl={14} 
          style={{
            display: "flex",
            justifyContent: "center",
            width: "100%",
            marginBottom:"10px",
            minWidth:0,
          }}
        >
          <CustomizeSection />
        </Col>

        {/* Settings */}
        <Col
          xs={24} sm={8} md={8} lg={7} xl={5} 
          style={{
            display: "flex",
            justifyContent: "flex-end",
            alignItems: "center",
            width: "100%",
            marginBottom:"10px"
          }}
        >
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "10px",
              padding: "12px",
              backgroundColor: "white",
              borderRadius: "12px",
              // maxWidth: "100%",
              // width: "100%",
              flex:"0 0 auto"
            }}
          >
            <MapSettingsPopupButton
              onMapTypeChange={onMapTypeChange}
              onLegendChange={onLegendChange}
            />
            <Divider
              type="vertical"
              style={{ height: "40px", borderColor: "lightgrey" }}
            />
            <Button size="small" type="primary" style={{ padding: "20px", fontSize: "clamp(0.75rem, 2.0vw, 0.85rem)"}}>
              Login
            </Button>
          </div>
        </Col>
      </Row>
    </div>
  );
};

export default Header;
