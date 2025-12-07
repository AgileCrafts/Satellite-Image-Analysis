// import React from "react";
// import "@ant-design/v5-patch-for-react-19";
// import { Divider, Button } from "antd";
// import LogoSection from "./LogoSection";
// import MapSettingsPopupButton from "./MapSettingsPopupButton";
// import CustomizeSection from "./CustomizeSection";

// const Header = ({ onMapTypeChange, onLegendChange }) => {
//   return (
//     <div
//       style={{
//         position: "absolute",
//         top: 0,
//         left: 0,
//         width: "100%",
//         height: "auto",
//         display: "grid",
//         gridTemplateColumns: "2fr 8fr 2fr",
//         alignItems: "center",
//         gap: "16px",
//         padding: "16px",
//         background: "transparent",
//         zIndex: 5000,
//       }}
//     >
//       {/* Logo */}
//       <div style={{ display: "flex", alignItems: "center" }}>
//         <LogoSection />
//       </div>

//       {/* Date Selection */}
//       <div
//         style={{
//           display: "flex",
//           justifyContent: "center",
//           width: "100%",
//         }}
//       >
//         <CustomizeSection />
//       </div>

//       {/* Settings */}
//       <div
//         style={{
//           display: "flex",
//           alignItems: "center",
//           justifyContent: "center",
//           width: "100%",
//         }}
//       >
//         <div
//           style={{
//             display: "flex",
//             alignItems: "center",
//             gap: "10px",
//             height: "auto",
//             padding: "12px",
//             backgroundColor: "white",
//             borderRadius: "12px",
//             width: "100%",
//             maxWidth: "300px",
//           }}
//         >
//           <MapSettingsPopupButton
//             onMapTypeChange={onMapTypeChange}
//             onLegendChange={onLegendChange}
//           />
//           <Divider
//             type="vertical"
//             style={{ height: "40px", borderColor: "lightgrey" }}
//           />
//           <Button type="primary" style={{ padding: "20px", fontSize: "1rem" }}>
//             Login
//           </Button>
//         </div>
//       </div>
//     </div>
//   );
// };

// export default Header;

import React from "react";
import { Row, Col, Divider, Button } from "antd";
import LogoSection from "./LogoSection";
import MapSettingsPopupButton from "./MapSettingsPopupButton";
import CustomizeSection from "./CustomizeSection";

const Header = ({ onMapTypeChange, onLegendChange }) => {
  return (
    <div
      style={{
        position: "absolute",
        top: 0,
        left: 0,
        width: "100%",
        height: "auto",
        display: "flex",
        justifyContent: "center", 
        zIndex: 5000,
        padding: "16px",
        background: "transparent",
        flexWrap:"wrap"
      }}
    >
      <Row
        justify="space-between"
        align="middle"
        style={{
          width: "100%"
        }}
      >
        {/* Logo */}
        <Col
          xs={24} sm={6} md={6} lg={5} xl={5} 
          style={{
            display: "flex",
            justifyContent: "flex-start",
            alignItems: "center",
          }}
        >
          <LogoSection />
        </Col>

        {/* Date Selection */}
        <Col
          xs={24} sm={12} md={12} lg={14} xl={14} 
          style={{
            display: "flex",
            justifyContent: "center",
            width: "100%",
          }}
        >
          <CustomizeSection />
        </Col>

        {/* Settings */}
        <Col
          xs={24} sm={6} md={6} lg={5} xl={5} 
          style={{
            display: "flex",
            justifyContent: "flex-end",
            alignItems: "center",
            width: "100%",
          }}
        >
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "10px",
              padding: "12px",
              backgroundColor: "white",
              borderRadius: "12px",
              width: "100%",
              maxWidth: "300px", 
            }}
          >
            <MapSettingsPopupButton
              onMapTypeChange={onMapTypeChange}
              onLegendChange={onLegendChange}
            />
            <Divider
              type="vertical"
              style={{ height: "40px", borderColor: "lightgrey" }}
            />
            <Button type="primary" style={{ padding: "20px", fontSize: "1rem" }}>
              Login
            </Button>
          </div>
        </Col>
      </Row>
    </div>
  );
};

export default Header;
