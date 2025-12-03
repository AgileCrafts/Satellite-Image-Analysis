import React, { useState } from 'react';
import { Input } from 'antd';

const { Search } = Input;

const CustomSearch = () => {
  const [value, setValue] = useState('');

  const handleSearch = (value) => {
    console.log('Search Query:', value);
   //code goes here
  };

  return (
    <Search
      placeholder="Search Port"
      value={value}
      onChange={(e) => setValue(e.target.value)}
      onSearch={handleSearch}  
      style={{width:"150px"}}
    />
  );
};

export default CustomSearch;
