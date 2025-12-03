import React, { useState } from 'react';
import { Button, Card, Divider } from 'antd';

// Custom Collapsible Card Component
const CollapsibleCard = ({ title, children, style }) => {
  const [isCollapsed, setIsCollapsed] = useState(true);

  // Toggle collapse state
  const handleToggle = () => {
    setIsCollapsed(!isCollapsed);
  };

  

  return (
    <Card style={{ 
      ...style }}>
      {/* Custom Header with the Toggle Button */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginLeft:"2px", padding:"5px 10px 0px 10px" }}>
        <p style={{marginTop:"15px"}}>{title}</p>
        <button
          onClick={handleToggle}
          style={{
            border: 'none',
            background: 'white',
            fontSize: '20px',
            cursor: 'pointer',
            outline: 'none',
            boxShadow: 'none', 
            // padding: '5px'
          }}
        >
          {isCollapsed ? '+' : '-'}
        </button>
      </div>
      
      {/* Content that shows based on collapse state */}
      {!isCollapsed && (
        
        <div> 
          <Divider style={{ margin: '0px 0px 15px 0px', borderColor: '#ddd', padding:"0" }} />
          {children}</div>
      )}
    </Card>
  );
};

export default CollapsibleCard;
