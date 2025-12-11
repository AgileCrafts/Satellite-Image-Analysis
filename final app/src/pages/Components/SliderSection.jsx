import React, { useState } from "react";
import '@ant-design/v5-patch-for-react-19';
import { Segmented, DatePicker, Space, Button, Row, Col, Modal } from "antd";
import { PlaySquareFilled, FullscreenOutlined, FullscreenExitOutlined } from "@ant-design/icons";

import TimeSlider from "./CustomSlider";
const { RangePicker } = DatePicker;

const SliderSection = ({onDatesChange, selectedPort}) => {
  const [selectedOption, setSelectedOption] = useState("Weekly");
  const [dateRange, setDateRange] = useState(null);
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false); //for modal expansion


  const handleSegmentChange = (value) => {
    setSelectedOption(value);

    // Reset date when switching options
    if (value !== "Custom") {
      setDateRange(null);
    }
  };

  const handleRangeChange = (value) => {
    setDateRange(value); 
  };


  const handleModalClose = () => {
    setIsModalVisible(false); // Close the modal
    setIsFullscreen(false);
  };

  const handleModalOpen = () => {
    setIsModalVisible(true); // Open the modal
  };

  //for modal expansion
   const toggleFullscreen = () => {
    setIsFullscreen(!isFullscreen);
  };

  return (
    <div
      style={{
        position: "fixed", 
        bottom: "1rem",        
        left: 0,          
        zIndex: 1000,
        background: "transparent",
        padding: "10px",  
        width: "100%",    
        display: "flex",
        flexDirection: "column", 
      }}
    >
      {/* Upper portion with Segmented and RangePicker aligned to the left */}
      <Row
        gutter={[16, 16]} 
        justify="start"  
        style={{ display: "flex", alignItems: "center", width: "100%", background:"transparent", pointerEvents: "auto" }}
      >
        {/* Segmented selection */}
        <Col
          xs={24} sm={8} md={6} lg={6} xl={5}
          style={{
            display: "flex",
            justifyContent: "flex-start", 
            padding: "5px",
          }}
        >
          <Segmented
            options={["Weekly", "Monthly", "Yearly", "Custom"]}
            value={selectedOption}
            onChange={handleSegmentChange}
            style={{
              width: "100%",
              backgroundColor: "lightgrey",
              borderRadius: "8px",
            }}
          />
        </Col>

        {/* Show RangePicker only for Custom */}
        {selectedOption === "Custom" && (
          <Col
            xs={24} sm={16} md={12} lg={10} xl={8}
            style={{
              display: "flex",
              justifyContent: "flex-start", 
              padding: "5px",
            }}
          >
            <Space direction="vertical" size={20}>
              <RangePicker
                format="YYYY-MM-DD"
                value={dateRange}
                onChange={handleRangeChange}
                style={{ width: "100%" }}
              />
            </Space>
          </Col>
        )}
      </Row>

      

      {/* Play Button and TimeSlider */}
      <div
        style={{
          display: "flex",
          justifyContent: "center", 
          alignItems: "center",
          width: "100%",
          height: "64px",
          backgroundColor: "white",
          padding: "0 16px", 
          marginTop: "16px", 
        }}
      >
        <Button
          style={{
            width: "45px",
            height: "45px",
            padding: "0",
            marginRight: "10px", 
          }}
          onClick={handleModalOpen}
        >
          <PlaySquareFilled style={{ fontSize: "45px", color: "blue" }} />
        </Button>
        <TimeSlider onDatesChange={onDatesChange} selectedPort={selectedPort}/>
      </div>


        {/* GIF Modal */}
      {/* <Modal
        title="GIF on changes over time"
        open={isModalVisible}
        onCancel={handleModalClose}
        footer={null} 
        width={800} 
        zIndex={9999999}
      >
        <img
          src="backend\output.gif" 
          alt="GIF"
          style={{ width: "100%" }}
        />
      </Modal> */}
      <Modal

          title={
            <div
              style={{
                position: "relative",          // allow absolute child inside header
                display: "flex",
                alignItems: "center",
                width: "100%",
                paddingRight: "64px",          // give space for our button + built-in close icon
              }}
            >
              <span style={{ fontWeight: 600 }}>GIF on changes over time</span>

              {/* Expand / Shrink Button placed absolutely so it lines up with the Close button */}
              <button
                onClick={toggleFullscreen}
                aria-label={isFullscreen ? "Shrink" : "Expand"}
                style={{
                  position: "absolute",
                  right: "15px",              // distance from right edge — tuned to align with close button
                  top: "30%",
                  transform: "translateY(-50%)",
                  border: "none",
                  background: "transparent",
                  cursor: "pointer",
                  padding: "4px 8px",
                  borderRadius: 4,
                  boxShadow: "none",
                  fontSize: 14,
                }}
              >
                {isFullscreen ? <FullscreenExitOutlined /> : <FullscreenOutlined />}
              </button>
            </div>
          }

          open={isModalVisible}
          onCancel={handleModalClose}
          footer={null}
          width={isFullscreen ? "100%" : 800}
          zIndex={9999999}
          bodyStyle={{ padding: 0 }}
          style={{ top: 0, padding:0 }}
        >
          {/* modal body: remove the previous Expand/Shrink button from body */}
          <div style={{ textAlign: "center" }}>
            {selectedPort?.id ? (
              <img
                src={`backend/${selectedPort.id}_output.gif`}
                alt="GIF"
                style={{ width: isFullscreen ? "1350px" : "100%", height: isFullscreen ? "650px" : "auto"}}
              />
            ) : (
              <p>No ports selected</p> // Placeholder text or fallback when no port is selected
            )}
          </div>



        {/* Fullscreen Toggle Button */}
        {/* <div style={{ marginTop: 16, textAlign: "center"}}>
          <Button onClick={toggleFullscreen} style={{ marginRight: 10 }}>
            {isFullscreen ? "Shrink" : "Expand"}
          </Button>
        </div> */}
      </Modal>

    </div>
  );
};

export default SliderSection;
