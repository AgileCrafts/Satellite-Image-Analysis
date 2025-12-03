import React, { useState } from "react";
import { Segmented, DatePicker, Space, Slider } from "antd";
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
              bottom: '8rem',
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
          height:"4px",
          marginBottom:"40px",
          backgroundColor:"white"
        }}>
          {/* Segmented selection */}
          <Segmented
            options={["Weekly", "Monthly", "Yearly", "Custom"]}
            value={selectedOption}
            onChange={handleSegmentChange}
            style={{ marginBottom: 20 }}
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
            height:"60px",
            backgroundColor:"white"
          }}>
            <PlaySquareFilled style={{fontSize:"45px", color:"blue"}}/>
            <TimeSlider/>
          </div>
    </div>
  );
};

export default SliderSection;
