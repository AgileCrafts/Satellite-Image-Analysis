// Dashboard.jsx
import React, { useEffect, useState } from "react";
import { Card, Row, Col, Spin, Button } from "antd";
import { useNavigate } from 'react-router-dom';

const Dashboard = () => {
  const [data, setData] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    fetch("http://localhost:8000/dashboard")
      .then((res) => res.json())
      .then((res) => setData(res));
  }, []);

  if (!data) return <Spin size="large" />;

  return (
    <div style={{ padding: 10 }}>
      {/* Banner / Hero Section */}
      <Card
        style={{
          marginBottom: 10,
          textAlign: "center",
          background: "#e7edf4ff",
          borderRadius: 1,
        }}
      >
        <h2>Welcome to the Satellite Image Analysis Dashboard!</h2>
        <h4>Quick summary of your AOIs and analyses</h4>
        <Button 
          type="primary" 
          size="large" 
          onClick={() => navigate('/map')} 
          style={{ marginTop: 20 }}
        >
          Go to Map
        </Button>
      </Card>

      {/* Stats Cards */}
      <Row gutter={24}>
        <Col span={8}>
          <Card title="Total AOIs" varient="borderless" className="floating-card" style={{ textAlign: "center" }}>
            <h4>{data.total_aois}</h4>
          </Card>
        </Col>
        <Col span={8}>
          <Card title="Total Change Maps" varient="borderless" className="floating-card" style={{ textAlign: "center" }}>
            <h4>{data.total_change_maps}</h4>
          </Card>
        </Col>
        <Col span={8}>
          <Card title="Last Analysis Date" varient="borderless" className="floating-card" style={{ textAlign: "center" }}>
            <h4>{data.last_analysis_date}</h4>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default Dashboard;
