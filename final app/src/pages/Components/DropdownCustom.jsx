import React, { useState, useEffect } from "react";
import { Select, Button } from "antd";

const { Option } = Select;

export default function DropdownCustom({ onPortClick }) {
  const divisions = [
    "Dhaka",
    "Chittagong",
    "Khulna",
    "Rajshahi",
    "Barishal",
    "Sylhet",
    "Rangpur",
    "Mymensingh",
  ];

  const [selectedDivision, setSelectedDivision] = useState(null);
  const [ports, setPorts] = useState([]);

  // 🔥 Fetch ports from backend
  const fetchPorts = async (division) => {
    try {
      const response = await fetch(
        `http://localhost:8000/ports/by-region/${division}`
      );
      const data = await response.json();
      setPorts(data);
    } catch (err) {
      console.error("Error loading ports:", err);
    }
  };

  // When division changes → load ports
  useEffect(() => {
    if (selectedDivision) {
      fetchPorts(selectedDivision);
    }
  }, [selectedDivision]);

  return (
    <div style={{ width: "100%", padding: "10px" }}>
      {/* Division Selector */}
      <Select
        placeholder="Select Division"
        style={{ width: "100%", marginBottom: "10px" }}
        onChange={(value) => setSelectedDivision(value)}
        value={selectedDivision}
        dropdownStyle={{ zIndex: 5000 }}
      >
        {divisions.map((division) => (
          <Option key={division} value={division}>
            {division}
          </Option>
        ))}
      </Select>

      {/* Port Buttons */}
      {selectedDivision && ports.length > 0 && (
        <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
          {ports.map((port) => (
            <Button
              key={port.id}
              className="portBtn"
              style={{ width: "100%" }}
              onClick={() => onPortClick(port)}
            >
              {port.port_name}
            </Button>
          ))}
        </div>
      )}
    </div>
  );
}
