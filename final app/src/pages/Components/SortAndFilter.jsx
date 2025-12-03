import { useState } from "react";
import { Dropdown, Button } from "antd";
import {DownOutlined } from "@ant-design/icons";

const filterItems = [
  { label: "By Name", key: "name" },
  { label: "By Date", key: "date" },
  { label: "By Type", key: "type" },
];

const SortFilterDropdown = () => {
  const [selected, setSelected] = useState("Filter");

  const handleSelect = (e) => {
    const item = filterItems.find((x) => x.key === e.key);
    setSelected(item?.label || "Filter");
  };

  return (
    <Dropdown
      menu={{ items: filterItems, onClick: handleSelect }}
      placement="bottomLeft"
      trigger={["click"]}
      
    >
     <Button style={{ width: 120 }}>
        Sort & Filter <DownOutlined style={{ marginLeft: 8 }}/>
      </Button> 
    </Dropdown>
  );
};

export default SortFilterDropdown;
