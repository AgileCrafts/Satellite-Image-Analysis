import { Button, Divider, Select } from "antd";
import React from "react";
import CustomSearch from "./CustomSearch";
import RangeSelector from "./RangeSelector";
import SortFilterDropdown from "./SortAndFilter";



export default function CustomizeSection(){
    return(
        <div 
        style={{
            display: "flex",
            flexDirection:"row",
            alignItems: "center",
            justifyContent:"center",
            width:"100%",
            maxWidth: "44rem",
            height: "64px",
            gap: "0.5rem",
            borderRadius: "12px",
            borderWidth: "1px",
            // padding: "16px",
            // marginLeft:"5rem",
            backgroundColor:"white",
            // zIndex: "9999"
        }}>
            <div>
                <CustomSearch/>
            </div>
            {/* <Divider type="vertical" style={{height:"40px", borderColor:"lightgrey"}}/>

            <div>
                <SortFilterDropdown/>
                <RangeSelector/>
            </div>
            <Divider type="vertical" style={{height:"40px", borderColor:"lightgrey"}}/>
            <div  style={{display:"flex", justifyContent:"space-between"}}>
                <Button style={{marginRight:"5px"}}>Select Area</Button>
                <Button>Markdown</Button>

            </div> */}
        </div>
    );
}

