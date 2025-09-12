import React, { useState } from "react";
import DatePicker from "react-datepicker";
import "react-datepicker/dist/react-datepicker.css";

function ChangeMap() {
  const [fromDate, setFromDate] = useState(null);
  const [toDate, setToDate] = useState(null);

  const saveDates = () => {
    if (!fromDate || !toDate) {
      alert("Please select both dates");
      return;
    }
    const payload = {
      from: fromDate.toISOString().split("T")[0],
      to: toDate.toISOString().split("T")[0],
    };
    console.log("Data to save:", payload);
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

      <button className="save-btn" onClick={saveDates}>Save Dates</button>
    </div>
  );
}

export default ChangeMap;
