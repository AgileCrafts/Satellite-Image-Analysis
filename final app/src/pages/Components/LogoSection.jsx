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
        maxWidth:"100%",
        height: "64px",
        gap: "16px",
        borderRadius: "12px",
        borderWidth: "1px",
        padding: "16px",
        backgroundColor:"white",
        flexShrink:1,
        marginLeft:"5px"
      }}
    >
      <img src="images\logo.png" style={{height:"48px", width:"48px", flexShrink:0}}></img>
      <h6 
      style={{
        margin:0,
        flex:1,
        fontSize: "clamp(0.65rem, 1.2vw, 0.9rem)"
        }}>River Encroachment  Monitoring & Simulation System</h6>
    </div>
  );
};

export default LogoSection;
