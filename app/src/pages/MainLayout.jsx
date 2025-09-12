import React from "react";
import { Layout, Menu, Input, theme } from "antd";
import { Outlet, useNavigate } from "react-router-dom";

const { Header, Content, Sider } = Layout;
const { Search } = Input;

const MainLayout = () => {
  const navigate = useNavigate();
  const {
    token: { colorBgContainer, borderRadiusLG },
  } = theme.useToken();

  const topMenu = [
    {
      key: "/about",
      label: "About",
    },
  ];

  const sideMenu = [
    {
      key: "/dashboard",
      label: "Dashboard",
    },
    {
      key: "map",
      label: "Map",
      children: [
        { key: "/map/view", label: "View" },
        { key: "/map/changemap", label: "Change Map" },
        { key: "3", label: "Opt 3" },
      ],
    },
  ];
  const searchMap = {
  dashboard: "/dashboard",
  map: "/map/view",
  "change map": "/map/changemap",
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
                navigate(route); // Navigate to the matched page
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
          style={{ minWidth: 200 }}
        />
      </Header>

      {/* BODY */}
      <Layout>
        {/* SIDEBAR */}
        <Sider width={200} style={{ background: colorBgContainer }}>
          <Menu
            mode="inline"
            defaultOpenKeys={["/map"]}
            style={{ height: "100%", borderInlineEnd: 0 }}
            items={sideMenu}
            onClick={(e) => navigate(e.key)}
          />
        </Sider>

        {/* CONTENT */}
        <Layout style={{ padding: "0px" }}>
          <Content
            style={{
              margin: 0,
              background: colorBgContainer,
              borderRadius: borderRadiusLG,
              height: "100%",
            }}
          >
            {/* Renders Dashboard / MapPage */}
            <Outlet />
          </Content>
        </Layout>
      </Layout>
    </Layout>
  );
};

export default MainLayout;
