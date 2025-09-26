import '@ant-design/v5-patch-for-react-19';
import { message, Spin } from 'antd';
import React from "react";
import DatePicker from "react-datepicker";
import "react-datepicker/dist/react-datepicker.css";

export const ChangeMapInputs = ({
  fromDate,
  setFromDate,
  toDate,
  setToDate,
  aois,
  selectedAoi,
  setSelectedAoi,
  selectedDates,
  setSelectedDates,
  setWaterImg,
  setCollageImg,
  setShowTestImage,
  setLoadingMessage,
  setBuiltupAnalysisImg, 
  setBuiltupCollageImg,
  // setWaterChangePercent,
  // setNewReducedCount,
}) => {
  const saveDates = () => {
    if (!fromDate || !toDate) {
      message.error("Please select both dates");
      return;
    }
    if (!selectedAoi) {
      message.error("Please select an AOI");
      return;
    }

    setWaterImg(null);
    setCollageImg(null);
    setShowTestImage(false);
    setLoadingMessage("Results are being generated...");
    setBuiltupAnalysisImg(null); 
    setBuiltupCollageImg(null);

    const payload = {
      aoi_id: selectedAoi,
      from_date: fromDate.toISOString().split("T")[0],
      to_date: toDate.toISOString().split("T")[0],
    };

    setSelectedDates(payload);
    const token = localStorage.getItem("authToken");

    fetch("http://localhost:8000/change_maps", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(payload),
    })
      .then((res) => {
        if (!res.ok) throw new Error(`Failed to save selection: ${res.statusText}`);
        return res.json();
      })
      .then((data) => {
        message.success(`Selection saved! Change Map ID: ${data.change_map_id}`);
        console.log("Change map response:", data);

        /*
        // Fetch water summary
        fetch(`http://localhost:8000/change_maps/${data.change_map_id}/summary`, {
          headers: { Authorization: `Bearer ${token}` },
        })
          .then((res) => {
            if (!res.ok) throw new Error(`Failed to fetch summary: ${res.statusText}`);
            return res.json();
          })
          .then((summary) => {
            setWaterChangePercent(summary.water_area_change);
            setNewReducedCount(summary.new_reduced_water_count);
          })
          .catch((err) => {
            console.error("Summary error:", err);
            message.error("Failed to load summary data");
          });
        */

        // Fetch water analysis image
        fetch(`http://localhost:8000/change_maps/${data.change_map_id}/water_analysis_image`, {
          headers: { Authorization: `Bearer ${token}` },
        })
          .then((res) => {
            if (!res.ok) throw new Error(`Failed to fetch water image: ${res.statusText}`);
            return res.blob();
          })
          .then((blob) => setWaterImg(URL.createObjectURL(blob)))
          .catch((err) => {
            console.error("Water image error:", err);
            message.error("Failed to load water analysis image");
          });

        // Fetch collage image
        fetch(`http://localhost:8000/change_maps/${data.change_map_id}/collage_image`, {
          headers: { Authorization: `Bearer ${token}` },
        })
          .then((res) => {
            if (!res.ok) throw new Error(`Failed to fetch collage image: ${res.statusText}`);
            return res.blob();
          })
          .then((blob) => setCollageImg(URL.createObjectURL(blob)))
          .catch((err) => {
            console.error("Collage image error:", err);
            message.error("Failed to load collage image");
          });

          // Fetch builtup analysis image
        fetch(`http://localhost:8000/change_maps/${data.change_map_id}/builtup_analysis_image`, {
          headers: { Authorization: `Bearer ${token}` },
        })
          .then((res) => {
            if (!res.ok) throw new Error(`Failed to fetch builtup analysis image: ${res.statusText}`);
            return res.blob();
          })
          .then((blob) => setBuiltupAnalysisImg(URL.createObjectURL(blob)))
          .catch((err) => {
            console.error("Builtup analysis image error:", err);
            message.error("Failed to load builtup analysis image");
          });

        // Fetch builtup collage image
        fetch(`http://localhost:8000/change_maps/${data.change_map_id}/builtup_collage_image`, {
          headers: { Authorization: `Bearer ${token}` },
        })
          .then((res) => {
            if (!res.ok) throw new Error(`Failed to fetch builtup collage image: ${res.statusText}`);
            return res.blob();
          })
          .then((blob) => setBuiltupCollageImg(URL.createObjectURL(blob)))
          .catch((err) => {
            console.error("Builtup collage image error:", err);
            message.error("Failed to load builtup collage image");
          });

        setShowTestImage(true);
      })
      .catch((err) => {
        console.error("Save dates error:", err);
        message.error(err.message);
      })
      .finally(() => setLoadingMessage(""));
  };

  return (
    <div>
      <h2>Select Dates to View Change Maps</h2>
      <div style={{ marginBottom: "15px" }}>
        <label htmlFor="from-date" style={{ display: "block", marginBottom: "5px" }}>From:</label>
        <DatePicker
          id="from-date"
          selected={fromDate}
          onChange={setFromDate}
          dateFormat="dd-MM-yyyy"
          placeholderText="Select start date (DD-MM-YYYY)"
          maxDate={toDate || null}
          className="date-picker-input"
        />
      </div>
      <div style={{ marginBottom: "15px" }}>
        <label htmlFor="to-date" style={{ display: "block", marginBottom: "5px" }}>To:</label>
        <DatePicker
          id="to-date"
          selected={toDate}
          onChange={setToDate}
          dateFormat="dd-MM-yyyy"
          placeholderText="Select end date (DD-MM-YYYY)"
          minDate={fromDate || null}
          className="date-picker-input"
        />
      </div>
      <div style={{ marginBottom: "15px" }}>
        <label htmlFor="aoi-select" style={{ display: "block", marginBottom: "5px" }}>Select AOI:</label>
        <select
          id="aoi-select"
          value={selectedAoi || ""}
          onChange={(e) => setSelectedAoi(Number(e.target.value))}
          style={{ width: "100%", padding: "8px", borderRadius: "4px", border: "1px solid #ccc" }}
        >
          <option value="" disabled>
            -- Choose AOI --
          </option>
          {aois.map((aoi) => (
            <option key={aoi.id} value={aoi.id}>
              {`${aoi.label}`}
            </option>
          ))}
        </select>
      </div>
      <button
        onClick={saveDates}
        style={{ width: "100%", padding: "8px", borderRadius: "4px", background: "#1890ff", color: "white", border: "none" }}
      >
        Save & View Details
      </button>
    </div>
  );
};

export default ChangeMapInputs;