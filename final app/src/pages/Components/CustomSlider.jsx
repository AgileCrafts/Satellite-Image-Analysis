import React, { useState, useRef } from "react";
import { Slider, Button } from "antd";
import "antd/dist/reset.css";

const TimeSlider = ({onDatesChange, selectedPort}) => {

  const marks = {
//   0: "2015",
//   1: "Jan 2015",
//   2: "Feb 2015",
//   3: "Mar 2015",
//   4: "Apr 2015",
//   5: "May 2015",
//   6: "Jun 2015",
//   7: "Jul 2015",
//   8: "Aug 2015",
//   9: "Sep 2015",
//   10: "Oct 2015",
//   11: "Nov 2015",
//   12: "Dec 2015",
  
//   13: "2016",
//   14: "Jan 2016",
//   15: "Feb 2016",
//   16: "Mar 2016",
//   17: "Apr 2016",
//   18: "May 2016",
//   19: "Jun 2016",
//   20: "Jul 2016",
//   21: "Aug 2016",
//   22: "Sep 2016",
//   23: "Oct 2016",
//   24: "Nov 2016",
//   25: "Dec 2016",

//   26: "2017",
//   27: "Jan 2017",
//   28: "Feb 2017",
//   29: "Mar 2017",
//   30: "Apr 2017",
//   31: "May 2017",
//   32: "Jun 2017",
//   33: "Jul 2017",
//   34: "Aug 2017",
//   35: "Sep 2017",
//   36: "Oct 2017",
//   37: "Nov 2017",
//   38: "Dec 2017",

//   39: "2018",
//   40: "Jan 2018",
//   41: "Feb 2018",
//   42: "Mar 2018",
//   43: "Apr 2018",
//   44: "May 2018",
//   45: "Jun 2018",
//   46: "Jul 2018",
//   47: "Aug 2018",
//   48: "Sep 2018",
//   49: "Oct 2018",
//   50: "Nov 2018",
//   51: "Dec 2018",

//   52: "2019",
//   53: "Jan 2019",
//   54: "Feb 2019",
//   55: "Mar 2019",
//   56: "Apr 2019",
//   57: "May 2019",
//   58: "Jun 2019",
//   59: "Jul 2019",
//   60: "Aug 2019",
//   61: "Sep 2019",
//   62: "Oct 2019",
//   63: "Nov 2019",
//   64: "Dec 2019",

//   65: "2020",
//   66: "Jan 2020",
//   67: "Feb 2020",
//   68: "Mar 2020",
//   69: "Apr 2020",
//   70: "May 2020",
//   71: "Jun 2020",
//   72: "Jul 2020",
//   73: "Aug 2020",
//   74: "Sep 2020",
//   75: "Oct 2020",
//   76: "Nov 2020",
//   77: "Dec 2020",

//   78: "2021",
//   79: "Jan 2021",
//   80: "Feb 2021",
//   81: "Mar 2021",
//   82: "Apr 2021",
//   83: "May 2021",
//   84: "Jun 2021",
//   85: "Jul 2021",
//   86: "Aug 2021",
//   87: "Sep 2021",
//   88: "Oct 2021",
//   89: "Nov 2021",
//   90: "Dec 2021",

//   91: "2022",
//   92: "Jan 2022",
//   93: "Feb 2022",
//   94: "Mar 2022",
//   95: "Apr 2022",
//   96: "May 2022",
//   97: "Jun 2022",
//   98: "Jul 2022",
//   99: "Aug 2022",
//   100: "Sep 2022",
//   101: "Oct 2022",
//   102: "Nov 2022",
//   103: "Dec 2022",

//   104: "2023",
//   105: "Jan 2023",
//   106: "Feb 2023",
//   107: "Mar 2023",
//   108: "Apr 2023",
//   109: "May 2023",
//   110: "Jun 2023",
//   111: "Jul 2023",
//   112: "Aug 2023",
//   113: "Sep 2023",
//   114: "Oct 2023",
//   115: "Nov 2023",
//   116: "Dec 2023",

//   117: "2024",
//   118: "Jan 2024",
//   119: "Feb 2024",
//   120: "Mar 2024",
//   121: "Apr 2024",
//   122: "May 2024",
//   123: "Jun 2024",
//   124: "Jul 2024",
//   125: "Aug 2024",
//   126: "Sep 2024",
//   127: "Oct 2024",
//   128: "Nov 2024",
//   129: "Dec 2024",

//   130: "2025",
//   131: "Jan 2025",
//   132: "Feb 2025",
//   133: "Mar 2025",
//   134: "Apr 2025",
//   135: "May 2025",
//   136: "Jun 2025",
//   137: "Jul 2025",
//   138: "Aug 2025",
//   139: "Sep 2025",
//   140: "Oct 2025",
//   141: "Nov 2025",
//   142: "Dec 2025",
  0: "2016",
  1: "mid 2016",
  2: "2017",
  3: "mid 2017",
  4: "2018",
  5: "mid 2018",
  6: "2019",
  7: "mid 2019",
  8: "2020",
  9: "mid 2020",
  10: "2021",
  11: "mid 2021",
  12: "2022",
  13: "mid 2022",
  14: "2023",
  15: "mid 2023",
  16: "2024",
  17: "mid 2024",
  18: "2025",
  19: "mid 2025"

 };


 const sliderDates = [
  
  selectedPort?.id === 1
        ?
  {
    0: "2016-02-17",
    1: "2016-11-13",
    2: "2017-01-02",
    3: "2017-05-02",
    4: "2018-02-01",
    5: "2018-11-18",
    6: "2019-01-02",
    7: "2019-11-13",
    8: "2020-01-17",
    9: "2020-11-22",
    10: "2021-01-06",
    11: "2021-05-01",
    12: "2022-01-01",
    13: "2022-12-12",
    14: "2023-01-11",
    15: "2023-11-02",
    16: "2024-02-10",
    17: "2024-05-25",
    18: "2025-01-30",
    19: "2025-11-11"
  } : {

    0: "2016-02-17",
    1: "2016-12-23",
    2: "2017-01-02",
    3: "2017-12-23",
    4: "2018-03-08",
    5: "2018-11-18",
    6: "2019-01-02",
    7: "2019-11-28",
    8: "2020-02-11",
    9: "2020-11-22",
    10: "2021-01-06",
    11: "2021-05-01",
    12: "2022-01-16", //2022-01-16    "2022-01-06"
    13: "2022-11-12", //2022-11-12    "2022-11-22"
    14: "2023-01-11",
    15: "2023-11-02",
    16: "2024-01-06",
    17: "2024-11-16", //2022-11-16    "2024-11-26"
    18: "2025-03-01", //2025-03-01    "2025-03-11"
    19: "2025-10-27"  //2025-10-27    "2025-10-22"

  }
]
  ;

  const [range, setRange] = useState([0, 14]);

  // Create a reference for the slider wrapper (this will help us control scroll position)
  const sliderWrapperRef = useRef(null);

  const onChange = (value) => {
    setRange(value);
    console.log("Selected range:", value.map((v) => marks[v]));
  };


  const getSelectedDatesFromSlider = (range) => {
    const dates = sliderDates[0];
    
    return {
      pre_date: dates[range[0]],
      post_date: dates[range[1]]
    };
  };

  const sendDatesToParent = () => {
    const { pre_date, post_date } = getSelectedDatesFromSlider(range);
    
    console.log(pre_date);
    console.log(post_date);

    onDatesChange(pre_date, post_date);
  };


  // Scroll the slider to the left
  const scrollLeft = () => {
    if (sliderWrapperRef.current) {
      sliderWrapperRef.current.scrollLeft -= 200; // Adjust scroll distance as needed
    }
  };

  // Scroll the slider to the right
  const scrollRight = () => {
    if (sliderWrapperRef.current) {
      sliderWrapperRef.current.scrollLeft += 200; // Adjust scroll distance as needed
    }
  };

  const tooltipFormatter = (value) => {
    
      return marks[value]; // Show year marks (divisible by 5)
   
  };

  // Custom marks function to only show text below year marks divisible by 5
  const customMarks = Object.keys(marks).reduce((acc, key) => {
    const index = parseInt(key);

    if (index % 2 === 0) {
      // Show text below year marks divisible by 5 (like 2015, 2020, etc.)
      acc[index] = marks[key];
    } else {
      // For month marks, we set `label` to null so the text does not appear below
      acc[index] = "  ";
    }
    return acc;
  }, {});

  return (
    <div style={{ position: "relative", width: "100%",  display:"flex", justifyContent:"center", margin:"0 !important", padding:0}}>
      {/* Left Button */}
      {/* <Button
        style={{
          position: "absolute",
          left: 0,
          top: "50%",
          // transform: "translateY(-50%)",
          zIndex: 10,
        }}
        onClick={scrollLeft}
      >
        ←
      </Button> */}

      {/* Right Button */}
      {/* <Button
        style={{
          position: "absolute",
          right: 0,
          top: "50%",
          // transform: "translateY(-50%)",
          zIndex: 10,
        }}
        onClick={scrollRight}
      >
        →
      </Button> */}


      {/* Slider Container */}
      <div
        ref={sliderWrapperRef}
        style={{
          overflowX: "auto", 
          whiteSpace: "nowrap", 
          width: "90%", 
          padding: "20px 20px", 
        }}
      >
        
        <Slider
          range
          min={0}
          max={19}
          step={null}
          marks={customMarks}
          defaultValue={range}
          onChange={onChange}
          onChangeComplete={() => sendDatesToParent()}
          tooltip={{
            visible: true,
            formatter: tooltipFormatter,
          }}
          style={{
            // width: "5000px", // Make the slider's width large enough to fit all marks
            width:"100%",
            minWidth:"600px",
            display: "inline-block",
            margin:"0 auto",
          }}
        />
      </div>
      </div>

  );
};

export default TimeSlider;

