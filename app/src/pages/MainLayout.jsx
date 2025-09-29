import React from "react";
import { Layout, Menu, Input, theme } from "antd";
import { Outlet, useNavigate, useLocation } from "react-router-dom";
import { radiansToLength } from "@turf/turf";

const { Header, Content } = Layout;
const { Search } = Input;

const MainLayout = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const {
    token: { colorBgContainer, borderRadiusLG },
  } = theme.useToken();

  const topMenu = [
    {
      key: "/dashboard",
      label: "Dashboard",
    },
    {
      key: "/map",
      label: "Map",
    },
  ];

  const searchMap = {
    dashboard: "/dashboard",
    map: "/map",
    about: "/about",
  };

  return (
    <Layout style={{ minHeight: "100vh", width: "100vw" }}>
      {/* HEADER */}
      <Header
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
        }}
      >
        <div style={{ color: "white", fontWeight: "bold" }}>LOGO</div>

        <div style={{ flex: 1, display: "flex", justifyContent: "center" }}>
          <Search
            placeholder="Search..."
            enterButton
            style={{ maxWidth: 400 }}
            onSearch={(value) => {
              if (!value.trim()) return;

              const key = value.toLowerCase();
              const route = searchMap[key];

              if (route) {
                navigate(route);
              } else {
                alert("No matching page found!");
              }
            }}
          />
        </div>

        <Menu
          theme="dark"
          mode="horizontal"
          items={topMenu}
          style={{ minWidth: 300 }}
          onClick={(e) => navigate(e.key)}
          selectedKeys={[location.pathname]}
        />
      </Header>

      {/* CONTENT */}
      <Layout>
        <Content
          style={{
            margin: 0,
            background: colorBgContainer,
            borderRadius: borderRadiusLG,
            height: "100%",
          }}
        >
          {/* Renders Dashboard / Map (MergedMapPage) / About */}
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
};

export default MainLayout;