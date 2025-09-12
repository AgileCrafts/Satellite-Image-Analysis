// Dashboard.jsx
import React ,{useState , useEffect} from "react";
import { Card, Row, Col , List, Spin } from "antd";

function Dashboard() {

  const [activity, setActivity] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);


   useEffect(() => {
    async function fetchData() {
      try {
        const [activityRes, notificationsRes] = await Promise.all([
          fetch("http://127.0.0.1:8000/activity"),
          fetch("http://127.0.0.1:8000/notifications"),
        ]);

        const activityData = await activityRes.json();
        const notificationsData = await notificationsRes.json();

        setActivity(activityData.logs || []);
        setNotifications(notificationsData.messages || []);
      } catch (error) {
        console.error("Error fetching data:", error);
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, []);

  return (
    <div>
      <Row gutter={[16, 16]} style={{ marginTop: "24px" }}>
        <Col span={12}>
          <Card title="Recent Activity">
            {loading ? (
              <Spin />
            ) : (
              <List
                dataSource={activity}
                renderItem={(item) => <List.Item>{item}</List.Item>}
              />
            )}
          </Card>
        </Col>
        <Col span={12}>
          <Card title="Notifications">

            {loading ? (
              <Spin />
            ) : (
              <List
                dataSource={notifications}
                renderItem={(item) => <List.Item>{item}</List.Item>}
              />
            )}

          </Card>
        </Col>
      </Row>
    </div>
  );
}

export default Dashboard;
