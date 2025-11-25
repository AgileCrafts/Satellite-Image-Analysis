import React, { useState } from "react";
import { Layout, Menu, Input, Button, Avatar, Dropdown, theme, Grid, Drawer } from "antd";
import { Outlet, useNavigate, useLocation } from "react-router-dom";
import { UserOutlined, HomeFilled, FlagFilled, LogoutOutlined, ProfileOutlined, MenuOutlined } from "@ant-design/icons";
import ShipIcon from '/src/assets/Ship-Fill.svg';

const { Header, Sider, Content } = Layout;
const { useBreakpoint } = Grid;

const MainLayout = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const screens = useBreakpoint();
  const isMobile = !screens.lg; 

  const [drawerOpen, setDrawerOpen] = useState(false);

  const sideMenu = [
    { key: "/dashboard", icon: <HomeFilled />, label: "Dashboard" },
    { key: "/ports", icon: <img src={ShipIcon} />, label: "Ports" },
    { key: "/encroachments", icon: <FlagFilled />, label: "Encroachments" }
  ];

  const profileMenu = {
    items: [
      { key: "1", label: "Profile", icon: <ProfileOutlined /> },
      { key: "2", label: "Logout", icon: <LogoutOutlined /> }
    ]
  };

  return (
    <Layout style={{ minHeight: "100vh", width: "100vw" }}>
      <Header
        style={{
          backgroundColor: "white",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "0 20px",
          border: "1px",
          flexWrap: "wrap",
          gap: "10px",
          height: "100%"
        }}
      >
        {/* Mobile Hamburger Button */}
        {isMobile && (
          <MenuOutlined
            style={{ fontSize: 24, cursor: "pointer" }}
            onClick={() => setDrawerOpen(true)}
          />
        )}

        <div style={{ display: "flex", alignItems: "center", paddingLeft: "0px", flexWrap: "wrap", gap: "20px", flex: "1 1 300px" }}>
          <h2 style={{ color: "#0c06ac", paddingLeft: "55px" }}>BIWTA</h2>
          <h2 style={{ color: "black", paddingLeft: "25px" }}> Temporal Change Detection </h2>
        </div>

        <div style={{ display: "flex", alignItems: "center", flexWrap: "wrap", gap: 20, flexShrink: 0, marginLeft: "auto", maxWidth: "fit-content" }}>
          <button className="new-analysis-btn">Run Analysis</button>

          <Dropdown menu={profileMenu} placement="bottomRight" trigger={["hover"]}>
            <Avatar style={{ cursor: "pointer", backgroundColor: "#0486ffff" }} icon={<UserOutlined />} />
          </Dropdown>
        </div>
      </Header>

      <Layout>
        {/* Desktop Sider */}
        {!isMobile && (
          <Sider theme="light" width={200} style={{ background: "transparent" }}>
            <Menu
              mode="inline"
              selectedKeys={[location.pathname]}
              items={sideMenu}
              onClick={(e) => navigate(e.key)}
              style={{ height: "100%", borderRight: 0, background: "none", color: "black", fontSize: "14px", fontStyle: "bold" }}
            />
          </Sider>
        )}

        {/* Mobile Drawer */}
        {isMobile && (
          <Drawer
            placement="left"
            open={drawerOpen}
            onClose={() => setDrawerOpen(false)}
            closable={true}
          >
            <Menu
              mode="inline"
              selectedKeys={[location.pathname]}
              items={sideMenu}
              onClick={(e) => {
                navigate(e.key);
                setDrawerOpen(false);
              }}
              style={{ height: "100%", borderRight: 0 }}
            />
          </Drawer>
        )}

        <Layout style={{ padding: "0" }}>
          <Content
            style={{
              margin: 0,
              padding: 0,
              borderRadius: theme.useToken().token.borderRadiusLG,
              height: "100%"
            }}
          >
            <Outlet />
          </Content>
        </Layout>
      </Layout>
    </Layout>
  );
};

export default MainLayout;
