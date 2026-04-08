import React from 'react';
import { useTimeGradient } from '../../hooks/useTimeGradient';

export const SkyBackground: React.FC = () => {
  const { gradient } = useTimeGradient();

  return (
    <div 
      className="sky-background"
      style={{ backgroundImage: gradient }}
    />
  );
};
