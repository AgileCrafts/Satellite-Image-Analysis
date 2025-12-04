import React, { useState } from "react";
import { Segmented, DatePicker, Space, Slider, Button } from "antd";
import {PlaySquareFilled } from "@ant-design/icons";
import CustomSlider from "./CustomSlider";
import TimeSlider from "./CustomSlider";
const { RangePicker } = DatePicker;

const SliderSection = () => {
  const [selectedOption, setSelectedOption] = useState("Weekly");
  const [dateRange, setDateRange] = useState(null);

  const handleSegmentChange = (value) => {
    setSelectedOption(value);

    // Reset date when switching options
    if (value !== "Custom") {
      setDateRange(null);
    }
  };

  const handleRangeChange = (value) => {
    setDateRange(value); // value = [startDayjs, endDayjs]
  };

  return (
    <div
       style={{
              display:"flex",
              flexDirection:"column",
              position: 'absolute',
              bottom: '5.6rem',
              left: '1rem',
              zIndex: 1000,
              background: 'transparent',
              // padding: '5px',
              borderRadius: '6px',
              width: '1500px',
              height:"2rem"
        }}
    >
        <div 
        style={{
          display:"flex",
          width:"300px",
          height:"2rem",
        }}>
          {/* Segmented selection */}
          <Segmented
            options={["Weekly", "Monthly", "Yearly", "Custom"]}
            value={selectedOption}
            onChange={handleSegmentChange}
            style={{ marginBottom: 20, backgroundColor:"lightgrey",height:"2rem", }}
          />

          {/* Show RangePicker only for Custom */}
          {selectedOption === "Custom" && (
            <Space direction="vertical" size={20}>
              <RangePicker
                format="YYYY-MM-DD"
                value={dateRange}
                onChange={handleRangeChange}
                style={{ width: "250px" }}
              />
            </Space>
          )}
          </div>
          <div style={{
            display:"flex",
            justifyContent:"center",
            alignItems:"center",
            width:"1500px",
            height:"64px",
            backgroundColor:"white",
          }}>
            <Button style={{ width: "45px", height:"45px", padding: "0" }}>
                <PlaySquareFilled style={{ fontSize:"45px",color: "blue" }} />
            </Button>
            <TimeSlider/>
          </div>
    </div>
  );
};

export default SliderSection;
