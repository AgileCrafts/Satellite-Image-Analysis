import React from 'react';
import styled from 'styled-components';

// This Wrapper ensures the styles of the button are encapsulated
// const ButtonWrapper = styled.div`
//   display: inline-block;
//   margin: 10px;
// `;

const StyledButton = styled.button`
  position: relative;
  padding: 0.2rem 0.5rem;
  font-size: 0.9rem;
  text-align: center;
  color: #ff0000;
  background: transparent;
  border: 2px solid #ff0000;
  border-radius: 5px;
  cursor: pointer;
  transition: all 0.4s ease-out;
  box-shadow: inset 0 0 0 0 #ff0000;

  &:hover {
    color: white; /* Change color to white on hover */
    background-color: #ff0000;
    box-shadow: inset 0 -100px 0 0 #ff0000;
  }

  &:active {
    transform: scale(0.95); /* Slightly scale down on active */
  }

  &:focus {
    outline: none;
  }
`;

const CustomButton1 = ({ buttonText }) => {
  return (
      <StyledButton type="button">
        {buttonText}
      </StyledButton>
  );
};

export default CustomButton1;
