import React, { useState } from 'react';
import { Collapse, Button, ConfigProvider } from 'antd';
import { DownOutlined, EnvironmentOutlined } from "@ant-design/icons";
import CustomButton1 from './CustomButton1';

const { Panel } = Collapse;

const Enchroachments = ({lostArea, selectedPort}) => {
  const [activeKey, setActiveKey] = useState([]);

  const panels = [];

  // Only add panel 1 IF lostArea exists AND is > 0
  if (lostArea && !isNaN(lostArea)) {
    panels.push({
      key: "1",
      title: `${lostArea} ha Encroached`,
      content:
        " ",
    });

  }

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
                 <Button variant="solid" 
                 onClick={() => {
                        const url = `https://earth.google.com/web/search/${selectedPort.latitude},${selectedPort.longitude}`;
                        window.open(url, '_blank');  
                      }}
                 >
                  
                  <EnvironmentOutlined/></Button>
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
