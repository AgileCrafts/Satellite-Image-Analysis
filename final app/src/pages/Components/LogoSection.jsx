import React from "react";

const LogoSection = () => {
  return (
    <div
      style={{
        display: "flex",
        flexDirection:"row",
        alignItems: "center",
        justifyContent:"center",
        width: "18.75rem",
        height: "64px",
        gap: "16px",
        borderRadius: "12px",
        borderWidth: "1px",
        padding: "16px",
        backgroundColor:"white"

      }}
    >
      <img src="src\assets\logo.png" style={{height:"48px", width:"48px"}}></img>
      <h6 style={{fontSize:"0.9rem", margin:0}}>River Encroachment  Monitoring & Simulation System</h6>
    </div>
  );
};

export default LogoSection;
