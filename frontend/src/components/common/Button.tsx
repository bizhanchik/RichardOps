import React from 'react';

interface ButtonProps {
  variant?: 'primary' | 'secondary' | 'outline';
  size?: 'sm' | 'md' | 'lg';
  children: React.ReactNode;
  onClick?: () => void;
  className?: string;
  disabled?: boolean;
}

const Button: React.FC<ButtonProps> = ({
  variant = 'primary',
  size = 'md',
  children,
  onClick,
  className = '',
  disabled = false,
}) => {
  const baseStyles = 'font-semibold rounded-xl transition-all duration-300 transform hover:scale-105 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none';
  
  const variants = {
    primary: 'bg-gradient-to-r from-purple-500 to-green-500 text-white shadow-lg hover:shadow-purple-500/25',
    secondary: 'bg-gray-800 text-white border border-gray-700 hover:border-purple-500 hover:shadow-purple-500/25',
    outline: 'bg-transparent text-purple-500 border-2 border-purple-500 hover:bg-purple-500 hover:text-white',
  };
  
  const sizes = {
    sm: 'px-4 py-2 text-sm',
    md: 'px-6 py-3 text-base',
    lg: 'px-8 py-4 text-lg',
  };
  
  return (
    <button
      className={`${baseStyles} ${variants[variant]} ${sizes[size]} ${className}`}
      onClick={onClick}
      disabled={disabled}
    >
      {children}
    </button>
  );
};

export default Button;