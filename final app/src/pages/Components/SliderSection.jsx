import React, { useState } from "react";
import '@ant-design/v5-patch-for-react-19';
import { Segmented, DatePicker, Space, Button, Row, Col, Modal } from "antd";
import { PlaySquareFilled } from "@ant-design/icons";

import TimeSlider from "./CustomSlider";
const { RangePicker } = DatePicker;

const SliderSection = () => {
  const [selectedOption, setSelectedOption] = useState("Weekly");
  const [dateRange, setDateRange] = useState(null);
  const [isModalVisible, setIsModalVisible] = useState(false);


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
  };

  const handleModalOpen = () => {
    setIsModalVisible(true); // Open the modal
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
        style={{ display: "flex", alignItems: "center", width: "100%" }}
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
        <TimeSlider />
      </div>


        {/* GIF Modal */}
      <Modal
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
      </Modal>

    </div>
  );
};

export default SliderSection;
