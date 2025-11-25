import React from "react";
import '@ant-design/v5-patch-for-react-19';
import { Card, Divider, DatePicker,Button } from "antd";
const { Meta } = Card;

const Dashboard = () => {
  return (
    <div
      style={{
        minHeight: "100vh",
        display: "grid",
        gridTemplateColumns: "repeat(12, 1fr)",  // 12-column system (like Antd!)
        gap: "16px",
        padding: "16px",
        gridAutoRows: "minmax(120px, auto)",
      }}
      className="card-grid"
    >
      {/* Card 1 - 6 columns wide */}
      <Card
        style={{ gridColumn: "span 6" }}
        className="dash-card"
        
        
      >
        <Meta description={
        <div style={{display:"flex", flexDirection: "column", padding:"10px"}}>
          <div style={{display:"flex", flexDirection: "row", padding:"10px"}}>
            <div style={{padding: "10px 5px 0px 5px"}}>
                <h3>Total Port Numbers</h3>
                <p>21 ports</p>
                

            </div>
            <Divider type="vertical" style={{marginTop: "2px", height:"60px", borderColor:"lightgrey"}}/>
            <div style={{padding: "10px 5px 0px 5px"}}>
                <h3>Total Port Numbers</h3>
                <p>21 ports</p>

            </div>
            <Divider type="vertical" style={{marginTop: "2px", height:"60px", borderColor:"lightgrey"}}/>
            <div style={{padding: "10px 5px 0px 5px"}}>
                <h3>Numbers</h3>
                <p>21 ports</p>
            </div>
          </div>
          <div style={{display:"flex", flexDirection: "row", justifyContent:"space-between"}}>
            <div style={{display:"flex", flexDirection: "row"}}>
              <div style={{ margin: "20px 0px 0px 20px" }}>
                      {/* <label htmlFor="from-date" style={{ display: "block"}}>From:</label> */}
                      <DatePicker
                        id="from-date"
                        // selected={fromDate}
                        // onChange={setFromDate}
                        dateFormat="DD-MM-YYYY"
                        placeholder="Start Date"
                        // maxDate={toDate || null}
                        className="date-picker-input"
                      />
              </div>
              <div style={{ margin: "20px 0px 0px 20px" }}>
                      {/* <label htmlFor="to-date" style={{ display: "block" }}>To:</label> */}
                      <DatePicker
                        id="to-date"
                        // selected={toDate}
                        // onChange={setToDate}
                        format="DD-MM-YYYY"
                        placeholder="Select end date"
                        // minDate={fromDate || null}
                        className="date-picker-input"
                        
                      />
                </div>
              </div>
              <div> 
                <button className="launch-button">
                  <svg
                    height="20"
                    width="20"
                    viewBox="0 0 24 24"
                    xmlns="http://www.w3.org/2000/svg"
                  >
                    <path d="M0 0h24v24H0z" fill="none"></path>
                    <path
                      d="M5 13c0-5.088 2.903-9.436 7-11.182C16.097 3.564 19 7.912 19 13c0 .823-.076 1.626-.22 2.403l1.94 1.832a.5.5 0 0 1 .095.603l-2.495 4.575a.5.5 0 0 1-.793.114l-2.234-2.234a1 1 0 0 0-.707-.293H9.414a1 1 0 0 0-.707.293l-2.234 2.234a.5.5 0 0 1-.793-.114l-2.495-4.575a.5.5 0 0 1 .095-.603l1.94-1.832C5.077 14.626 5 13.823 5 13zm1.476 6.696l.817-.817A3 3 0 0 1 9.414 18h5.172a3 3 0 0 1 2.121.879l.817.817.982-1.8-1.1-1.04a2 2 0 0 1-.593-1.82c.124-.664.187-1.345.187-2.036 0-3.87-1.995-7.3-5-8.96C8.995 5.7 7 9.13 7 13c0 .691.063 1.372.187 2.037a2 2 0 0 1-.593 1.82l-1.1 1.039.982 1.8zM12 13a2 2 0 1 1 0-4 2 2 0 0 1 0 4z"
                      fill="currentColor"
                    ></path>
                  </svg>
                  <span>Launch</span>
                </button>

              </div>
          </div>
          
        </div> 
        }
        />
      </Card>

      {/* Card 2 - tall, 6 columns wide, spans 2 rows */}
      <Card
        title="Card 2"
        style={{ gridColumn: "span 6", gridRow: "span 2" }}
        className="dash-card"
      >
        <Meta description="Content for Card 2" />
      </Card>

      {/* Card 3 - sits neatly below Card 1 */}
      <Card
        title="Card 3"
        style={{ gridColumn: "span 3" }}
        className="dash-card"
      >
        <Meta description="Content for Card 3" />
      </Card>
      <Card
        title="Card 4"
        style={{ gridColumn: "span 3" }}
        className="dash-card"
      >
        <Meta description="Content for Card 4" />
      </Card>

      {/* Card 5 (4 columns) */}
      <Card
        title="Card 5"
        style={{ gridColumn: "span 4" }}
        className="dash-card"
      >
        <Meta description="Content for card 4" />
      </Card>

      {/* Card 6 & 7(4 columns each) */}
      <Card
        title="Card 6"
        style={{ gridColumn: "span 4" }}
        className="dash-card"
      >
        <Meta description="Content for Card 6" />
      </Card>

      <Card
        title="Card 7"
        style={{ gridColumn: "span 4" }}
        className="dash-card"
      >
        <Meta description="Content for Card 7" />
      </Card>

      {/* Card 8 & 9 - full width or half width */}
      <Card
        title="Recent Analysis & Report"
        style={{ gridColumn: "span 7" }}   
        className="dash-card"
      >
        <Meta description={
          <table className="report-table">
            <thead>
              <tr>
                  <th>Port/Area</th>
                  <th>Type</th>
                  <th>Status</th>
                  <th>Action</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
              </tr>
            </tbody>
          </table>
        } />
      </Card>

      <Card
        title="Recent Analysis Deption"
        style={{ gridColumn: "span 5" }}
        className="dash-card"
      >
        <Meta description=
        {
          <table  className="report-table">
            <thead>
              <tr>
                  <th>Port/Area</th>
                  <th>Type</th>
                  <th>Status</th>
                  <th>Action</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
              </tr>
            </tbody>
          </table>
        }
        />
      </Card>
    </div>
  );
};

export default Dashboard;