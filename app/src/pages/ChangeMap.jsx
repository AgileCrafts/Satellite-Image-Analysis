import '@ant-design/v5-patch-for-react-19';
import { message } from 'antd';

import React, { useState , useEffect} from "react";
import DatePicker from "react-datepicker";
import "react-datepicker/dist/react-datepicker.css";
import axios from "axios";

function ChangeMap() {
  const [fromDate, setFromDate] = useState(null);
  const [toDate, setToDate] = useState(null);
  const [aois, setAois] = useState([]);      // list of AOIs from backend
  const [selectedAoi, setSelectedAoi] = useState(""); // selected AOI id
  const [selectedDates, setSelectedDates] = useState(null);

  // Fetch AOIs from backend on component mount
    useEffect(() => {
    const fetchAois = async () => {
      try {
        const token = localStorage.getItem("authToken"); 
        if (!token) {
        console.error("No auth token found in localStorage");
        setAois([]);
        return;
      }
        const res =await axios.get("http://127.0.0.1:8000/aois", {
        headers: { Authorization: `Bearer ${token}` }
        });


        console.log("Full response from /aois:", res); 
        // Make sure it's an array
        if (Array.isArray(res.data)) {
          setAois(res.data);
        } else {
          console.error("AOI response is not an array:", res.data);
          setAois([]);
        }
      } catch (err) {
        console.error("Failed to fetch AOIs:", err);
        setAois([]);
      }
    };

    fetchAois();
  }, []);


  const saveDates = () => {
  if (!fromDate || !toDate) {
    alert("Please select both dates");
    return;
  }
  if (!selectedAoi) {
    alert("Please select an AOI");
    return;
  }

  // Prepare the selected dates and AOI payload
  const payload = {
    aoi_id: selectedAoi,
    from_date: fromDate.toISOString().split("T")[0],
    to_date: toDate.toISOString().split("T")[0],
};

  // Save in frontend state
  setSelectedDates(payload);
  const token = localStorage.getItem("authToken");

fetch("http://localhost:8000/change_maps", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    "Authorization": `Bearer ${token}`
  },
  body: JSON.stringify(payload),
})
  
  .then((res) => {
      if (!res.ok) throw new Error("Failed to save selection");
      return res.json();
    })
    .then((data) => {
      message.success(`Selection saved! Change Map ID: ${data.change_map_id}`);
      console.log(data);
    })
    .catch((err) => message.error(err.message));

  
};


  return (
    <div className="change-map-container">
      <h2>Select Dates to View Change Maps</h2>

      <div className="date-picker-row">
        <label htmlFor="from-date">From:</label>
        <DatePicker
          id="from-date"
          selected={fromDate}
          onChange={setFromDate}
          dateFormat="dd-MM-yyyy"
          placeholderText="Select start date(DD-MM-YYYY)"
          maxDate={toDate || null}
          onChangeRaw={(e) => {
            const value = e.target.value;
            const date = new Date(value);
            if (!isNaN(date)) setFromDate(date);
          }}
        />
      {/* </div>

      <div className="date-picker-row"> */}
        <label htmlFor="to-date">To:</label>
        <DatePicker
          id="to-date"
          selected={toDate}
          onChange={setToDate}
          dateFormat="dd-MM-yyyy"
          placeholderText="Select end date(DD-MM-YYYY)"
        //   minDate={fromDate || null}
          onChangeRaw={(e) => {
            const value = e.target.value;
            const date = new Date(value);
            if (!isNaN(date)) setToDate(date);
          }}
        />
      </div>

      <div className="aoi-dropdown-row" style={{ marginTop: "15px" }}>
        <label htmlFor="aoi-select">Select AOI:</label>
        <select
          id="aoi-select"
          value={selectedAoi || ""}
          onChange={(e) => setSelectedAoi(Number(e.target.value))}
        >
          <option value="" disabled>
            -- Choose AOI --
          </option>
          {aois.map((aoi) => (
            <option key={aoi.id} value={aoi.id}>
              {`${aoi.label} - Centroid: (${aoi.centroid ? `${aoi.centroid.lat.toFixed(3)}, ${aoi.centroid.lon.toFixed(3)}` : 'N/A'})`}
            </option>
          ))}
        </select>
      </div>

      <button className="save-btn" style={{ marginTop: "20px" }} onClick={saveDates}>
        Save Dates & AOI
      </button>

      

    </div>
    
  );
}

export default ChangeMap;
