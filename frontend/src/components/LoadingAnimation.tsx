import React from 'react';

interface LoadingAnimationProps {
  size?: 'sm' | 'md' | 'lg';
  message?: string;
}

export const LoadingAnimation: React.FC<LoadingAnimationProps> = ({ 
  size = 'md', 
  message = 'Loading...'
}) => {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-6 h-6',
    lg: 'w-8 h-8'
  };

  return (
    <div className="flex items-center space-x-2">
      {/* Simple spinner */}
      <div className={`${sizeClasses[size]} border-2 border-gray-300 border-t-emerald-500 rounded-full animate-spin`}></div>
      
      {message && (
        <span className="text-sm text-gray-600">{message}</span>
      )}
    </div>
  );
};

export const ChartSkeleton: React.FC = () => (
  <div className="animate-pulse space-y-4">
    {/* Simple skeleton bars */}
    <div className="h-32 bg-gray-200 rounded-lg flex items-end justify-between p-4 space-x-1">
      {[...Array(8)].map((_, i) => (
        <div
          key={i}
          className="bg-gray-300 rounded-sm w-8"
          style={{ height: `${30 + (i % 3) * 20}%` }}
        />
      ))}
    </div>
    
    {/* Simple text skeleton */}
    <div className="flex justify-between">
      <div className="h-3 bg-gray-200 rounded w-16"></div>
      <div className="h-3 bg-gray-200 rounded w-12"></div>
    </div>
  </div>
);

export default LoadingAnimation;