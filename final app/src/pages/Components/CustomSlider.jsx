import React, { useState } from "react";
import { Slider } from "antd";
import "antd/dist/reset.css";

const TimeSlider = () => {
  // Define marks as month + year strings
  const marks = {
    0: "Jan 2019",
    1: "Mar",
    2: "Jun",
    3: "Sep",
    4: "Jan 2020",
    5: "Mar 2020",
    6: "Jun 2020",
    7: "Sep 2020",
    8: "Jan 2021",
    9: "Mar 2021",
    10: "Jun 2021",
    11: "Sep 2021",
    12: "Jan 2022",
    13: "Mar 2022",
    14: "Jun 2022",
    15: "Sep 2022",
    16: "Jan 2023",
    17: "Mar 2023",
    18: "Jun 2023",
    19: "Sep 2023",
    20: "Jan 2024",
    21: "Mar 2024",
    22: "Jun 2024",
    23: "Sep 2024",
    24: "Jan 2025",
    25: "Mar 2025",
    26: "Jun 2025",
    27: "Sep 2025",
  };

  const [range, setRange] = useState([4, 16]); // default selection

  const onChange = (value) => {
    setRange(value);
    console.log("Selected range:", value.map(v => marks[v]));
  };

  return (
    <div style={{ width: "1400px", margin: "50px auto" }}>
      <Slider
        range
        min={0}
        max={27}
        step={null} 
        marks={marks}
        defaultValue={range}
        onChange={onChange}
        tooltip={{
          formatter: (value) => marks[value],
        }}
      />
    </div>
  );
};

export default TimeSlider;
