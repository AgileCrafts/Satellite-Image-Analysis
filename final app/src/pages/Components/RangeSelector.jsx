import React, { useState } from 'react';
import { Select } from 'antd';

const { Option } = Select;

const RangeSelector = () => {
  const [selectedRange, setSelectedRange] = useState(null);

  const handleChange = (value) => {
    setSelectedRange(value);
    console.log('Selected Range:', value);
  };

  return (
    <Select
      showSearch
      placeholder="Date range"
      style={{ width: 120, marginLeft:"10px"}}
      onChange={handleChange}
      getPopupContainer={(triggerNode) => triggerNode.parentNode}
    >
      <Option value="10">10</Option>
      <Option value="20">20</Option>
      <Option value="30">30</Option>
      <Option value="40">40</Option>
      <Option value="50">50</Option>
    </Select>
  );
};

export default RangeSelector;
