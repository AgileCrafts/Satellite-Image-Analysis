import React, { useState } from 'react';
import { Button, Card, Typography, Space } from 'antd';
import { CloseOutlined } from '@ant-design/icons';

const { Title, Paragraph } = Typography;

const FloatingCardWithCloseButton = () => {
  const [visible, setVisible] = useState(false);

  // Show the floating card
  const showCard = () => {
    setVisible(true);
  };

  // Hide the floating card
  const hideCard = () => {
    setVisible(false);
  };

  return (
    <div style={{ padding: 20 }}>
      {/* Button to show the floating card */}
      <Button type="primary" onClick={showCard}>
        Show Floating Card
      </Button>

      {/* Floating Card with Close Button */}
      {visible && (
        <Card
          style={{
            position: 'absolute',
            top: '100px', 
            left: '50%',
            transform: 'translateX(-50%)',
            width: '300px',
            zIndex: 1000, 
          }}
          title="Floating Card"
          extra={<CloseOutlined onClick={hideCard} />}
        >
          <Title level={4}>Title</Title>
          <Paragraph>Content</Paragraph>
        </Card>
      )}
    </div>
  );
};

export default FloatingCardWithCloseButton;
