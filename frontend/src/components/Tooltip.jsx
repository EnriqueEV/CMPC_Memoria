import React, { useState } from 'react';

const Tooltip = ({ children, text, position = 'top' }) => {
  const [isVisible, setIsVisible] = useState(false);

  return (
    <div 
      className="tooltip"
      onMouseEnter={() => setIsVisible(true)}
      onMouseLeave={() => setIsVisible(false)}
    >
      {children}
      {isVisible && (
        <div className={`tooltip__bubble tooltip__bubble--${position}`}>
          {text}
        </div>
      )}
    </div>
  );
};

export default Tooltip;
