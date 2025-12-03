import React, { useState } from 'react';
import { Collapse, Button, ConfigProvider } from 'antd';
import { DownOutlined, EnvironmentOutlined } from "@ant-design/icons";
import CustomButton1 from './CustomButton1';

const { Panel } = Collapse;

const Enchroachments = () => {
  const [activeKey, setActiveKey] = useState([]);

  const panels = [
    { key: '1', title: '20sqkm Encroached', content: 'FHRR+5J Paira, Patuakhali District, Barisal Division, Bangladesh' },
    { key: '2', title: 'Panel 2', content: 'Content for panel 2' },
    { key: '3', title: 'Panel 3', content: 'Content for panel 3' },
  ];

  return (
    <Collapse
      activeKey={activeKey}
      onChange={(keys) => setActiveKey(keys)}
      bordered={false}
      expandIcon={({ isActive }) => <DownOutlined rotate={isActive ? 180 : 0} />}
      expandIconPosition="end"
    >
      {panels.map(({ key, title, content }, index) => {
        const isActive = activeKey.includes(key);
        return (
          <Panel
            key={key}
            header={
             <div style={{ display: 'flex', alignItems: 'center' }}>
                <div
                  style={{
                    backgroundColor: isActive ? 'white' : '#fadada', 
                    color: isActive ? 'red' : 'red',            
                    borderRadius: '5px',
                    width: '28px',
                    height: '24px',
                    display: 'flex',
                    justifyContent: 'center',
                    alignItems: 'center',
                    marginRight: '8px',
                  }}
                >
                  {index + 1} 
                </div>
                <span style={{fontWeight:'bold'}}>{title}</span>
              </div>
      }
            style={{
              // borderRadius: '6px',
              // marginBottom: '8px',
              backgroundColor: isActive ? '#F2F4F5' : 'white',
            }}
          >
            <div style={{padding:"1rem"}}>
            {content}
            <div style={{ display: 'flex', gap: '0.5rem', marginTop: '1rem' }}>

              <Button  type="primary">Confirm</Button>
              <CustomButton1 buttonText="Dismiss"/>
              <ConfigProvider wave={{disabled: true}}>
                 <Button variant="solid"><EnvironmentOutlined/></Button>
              </ConfigProvider>
                
                
            </div>
            </div>
          </Panel>
        );
      })}
    </Collapse>
  );
};

export default Enchroachments;
