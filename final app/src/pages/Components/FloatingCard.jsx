import React, { useState, useEffect, useRef } from 'react';
import { Button, Card, Typography, ConfigProvider } from 'antd';
import { CloseOutlined, EnvironmentOutlined, FullscreenExitOutlined, FullscreenOutlined} from '@ant-design/icons';
import CustomButton1 from './CustomButton1';
import "../css/floatingCard.css";
import Draggable from 'react-draggable';

const { Title, Paragraph } = Typography;

const FloatingCard = ({selectedPort, lostArea}) => {

  const [cardVisible, setCardVisible] = React.useState(false);
  const [cardData, setCardData] = React.useState(null);
  const [isFullscreen, setIsFullscreen] = useState(true);

  const nodeRef = useRef(null);

  const toggleFullscreen = () => {
    setIsFullscreen(!isFullscreen);
  };


  useEffect(() => {
    if (selectedPort && lostArea) {
      const props = selectedPort; 

      setCardData({
        lostArea: lostArea || "Unknown",
        description: "Encroachment detected near the selected port.",
      });
      setCardVisible(true);
    }
  }, [selectedPort, lostArea]);


  const articles=
  ['https://www.thedailystar.net/news/bangladesh/news/blatant-river-grab-3908261',
    'https://www.thedailystar.net/news/bangladesh/crime-justice/news/evict-30-illegal-structures-turags-banks-hc-directs-govt-3812316'
    
  ];

  return (
  <Draggable nodeRef={nodeRef} cancel=".no-drag">
    <div ref={nodeRef} style={{ position: "absolute", top: 100, left: "10%", zIndex: 3000 }}>
    {cardVisible && (
    <Card
            className="encro-card"
            style={{
              // position: "absolute",
              // top: "100px",
              // left: "10%",
              // transform: "translateX(-10%)",
              width: "320px",
              // zIndex: 3000,
            }}
            title="Encroachment Details"
            extra={
            <div>
            <button
                className='no-drag'
                onClick={toggleFullscreen}
                aria-label={isFullscreen ? "Shrink" : "Expand"}
                style={{            
                  border: "none",
                  background: "transparent",
                  cursor: "pointer",
                  padding: "4px 8px",
                  borderRadius: 4,
                  boxShadow: "none",
                  fontSize: 14,
                  color: "white"
                }}
              >
                {isFullscreen ? <FullscreenExitOutlined /> : <FullscreenOutlined />}
              </button>
            
            <CloseOutlined className="no-drag" style={{color: "white"}}onClick={() => setCardVisible(false)} />
              </div>
              }
          >
            { isFullscreen && (
            <div style={{padding: "10px"}}>
              <div className="img-div" style={{ height: "100px", background: "#eee", marginBottom: "10px" }}>
                <iframe
                    src={`https://www.google.com/maps?q=${selectedPort.latitude},${selectedPort.longitude}&hl=en&z=14&output=embed`}
                    width="100%"
                    height="100%"
                    style={{ border: 0 }}
                    allowFullScreen
                    loading="lazy"
                    referrerPolicy="no-referrer-when-downgrade"
                  />
              </div>
              <div className="des-div" style={{display:"flex", justifyContent:"space-between"}}>
                <div>
                    <h3>{selectedPort.port_name}</h3>
                    <p>{lostArea} ha Encroached</p>
                </div>
                
                <div>
                  <ConfigProvider wave={{disabled: true}}>
                 <Button variant="solid" 
                 onClick={() => {
                        const url = `https://www.google.com/maps?q=${selectedPort.latitude},${selectedPort.longitude}&hl=es;z=14&output=embed`;
                        window.open(url, '_blank');  
                      }}
                 >
                  
                  <EnvironmentOutlined/> Open Map</Button>
              </ConfigProvider>
                </div>
                
              </div>
              <div style={{margin:"10px 0px"}}>
                   <Button
                        type="primary"
                        onClick={() => {
                              const articleUrl = articles[selectedPort.id - 1]; // assuming id starts from 1
                              if (articleUrl) {
                                window.open(articleUrl, "_blank");
                                }
                      }}  
                      >
                        Read Article
                      </Button>

                </div>
              <div>
                      <Button  type="primary" style={{marginRight:"10px"}}>Confirm</Button>
                      <CustomButton1 buttonText="Dismiss"/>
              </div>
            </div>
            )}
              
          </Card>
    )}
    </div>

    </Draggable>
  );
};

export default FloatingCard;
