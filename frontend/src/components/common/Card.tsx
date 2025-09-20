import React from 'react';

interface CardProps {
  children: React.ReactNode;
  className?: string;
  hover?: boolean;
  glow?: boolean;
}

const Card: React.FC<CardProps> = ({
  children,
  className = '',
  hover = true,
  glow = false,
}) => {
  const baseStyles = 'bg-gray-800/50 border border-gray-700 rounded-2xl p-6 transition-all duration-300';
  const hoverStyles = hover ? 'hover:shadow-lg hover:scale-105 hover:border-purple-500' : '';
  const glowStyles = glow ? 'shadow-purple-500/50 shadow-lg animate-pulse' : 'shadow-lg shadow-gray-900/50';
  
  return (
    <div className={`${baseStyles} ${hoverStyles} ${glowStyles} ${className}`}>
      {children}
    </div>
  );
};

export default Card;