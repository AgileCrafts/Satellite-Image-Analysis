import React from 'react';
import { Breadcrumb, Layout, Menu, theme, Input } from 'antd';
import { UserOutlined, LaptopOutlined, NotificationOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';

const Dashboard = () => {
    const { Search } = Input;
    const { Header, Content, Sider } = Layout;
    const items1 = [{
    key: 'nav1',
    // icon: <UserOutlined />,
    label: 'About',
    
    }
    ];
    const items2 = [
    {
    key: 'sub1',
    // icon: <UserOutlined />,
    label: 'Dashboard',
    
    } ,

    {
    key: 'sub2',
    // icon: <UserOutlined />,
    label: 'Map',
    children: [
      { key: '1', label: 'opt1' },
      { key: '2', label: 'opt2' },
      { key: '3', label: 'opt3' },
    ],
    } 
    ];
    const {
    token: { colorBgContainer, borderRadiusLG },
  } = theme.useToken();



  return (
    <Layout className='dashboard'>
      <Header style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        {/* Logo */}
        <div className="demo-logo" style={{ color: 'white', fontWeight: 'bold' }}>
            MyApp
        </div>

        {/* Search bar in the center */}
        <div style={{ flex: 1, display: 'flex', justifyContent: 'center' }}>
            <Search
            placeholder="Search..."
            onSearch={value => console.log(value)}
            style={{ maxWidth: 400 }}
            />
        </div>

        {/* Menu aligned to the right */}
        <Menu
            theme="dark"
            mode="horizontal"
            defaultSelectedKeys={['2']}
            items={items1}
            style={{ minWidth: 200 }}
        />
        </Header>

      <Layout>
        <Sider width={200} style={{ background: colorBgContainer }}>
          <Menu
            mode="inline"
            defaultSelectedKeys={['1']}
            defaultOpenKeys={['sub1']}
            style={{ height: '100%', borderInlineEnd: 0 }}
            items={items2}
          />
        </Sider>
        <Layout style={{ padding: '0 24px 24px' }}>
          {/* <Breadcrumb
            items={[{ title: 'Home' }, { title: 'List' }, { title: 'App' }]}
            style={{ margin: '16px 0' }}
          /> */}
          <Content
            style={{
              padding: 24,
              margin: 0,
              minHeight: 280,
              background: colorBgContainer,
              borderRadius: borderRadiusLG,
            }}
          >
            Content
          </Content>
        </Layout>
      </Layout>
    </Layout>
  );

};

export default Dashboard;
