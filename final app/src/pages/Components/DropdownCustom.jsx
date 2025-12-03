import React, { useState } from "react";
import { Select, Button } from "antd";

const { Option } = Select;

export default function DropdownCustom({ onPortClick }) {

  // 8 Divisions with ports inside them
  const divisions = {
    "Dhaka": [ "Ashuganj Port"],
    "Chittagong": ["Chittagong Port", "Karnaphuli Terminal"],
    "Khulna": ["Mongla Port"],
    "Rajshahi": ["Godagari Dry Port"],
    "Barishal": ["Payra Port"],
    "Sylhet": [""],
    "Rangpur": [""],
    "Mymensingh": [""],
    
  };

  const [selectedDivision, setSelectedDivision] = useState(null);

  return (
    <div style={{ width: "100%",padding:"10px" }}>
      
      {/* Dropdown */}
      <Select
        placeholder="Select Division"
        style={{ width: "100%", marginBottom: "10px" }}
        onChange={(value) => setSelectedDivision(value)}
        value={selectedDivision}
        dropdownStyle={{ zIndex: 5000 }}
      >
        {Object.keys(divisions).map((division) => (
          <Option key={division} value={division}>
            {division}
          </Option>
        ))}
      </Select>

      {/* Ports (appear only after selecting district) */}
      {selectedDivision && (
        <div style={{ display: "flex", flexDirection: "column", gap: "8px"}}>
          {divisions[selectedDivision].map((port) => (
            <Button
              key={port}
              className="portBtn"
              style={{ width: "100%" }}
              onClick={() => onPortClick(port)}
            >
              {port}
            </Button>
          ))}
        </div>
      )}
    </div>
  );
}
