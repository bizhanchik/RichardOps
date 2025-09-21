import React from 'react';
import { CloudOff, RefreshCw, AlertCircle, Database, Wifi } from 'lucide-react';

interface DataFallbackProps {
  error?: Error | string;
  onRetry?: () => void;
  onViewCached?: () => void;
  type?: 'connection' | 'data' | 'server' | 'generic';
  title?: string;
  description?: string;
  showCachedOption?: boolean;
  className?: string;
}

const DataFallback: React.FC<DataFallbackProps> = ({
  error,
  onRetry,
  onViewCached,
  type = 'generic',
  title,
  description,
  showCachedOption = false,
  className = ''
}) => {
  const getIcon = () => {
    switch (type) {
      case 'connection':
        return <Wifi className="w-12 h-12 text-gray-400 mx-auto mb-4" />;
      case 'data':
        return <Database className="w-12 h-12 text-gray-400 mx-auto mb-4" />;
      case 'server':
        return <AlertCircle className="w-12 h-12 text-gray-400 mx-auto mb-4" />;
      default:
        return <CloudOff className="w-12 h-12 text-gray-400 mx-auto mb-4" />;
    }
  };

  const getDefaultTitle = () => {
    if (title) return title;
    
    switch (type) {
      case 'connection':
        return 'Connection Failed';
      case 'data':
        return 'Unable to Load Data';
      case 'server':
        return 'Server Error';
      default:
        return 'Something Went Wrong';
    }
  };

  const getDefaultDescription = () => {
    if (description) return description;
    
    switch (type) {
      case 'connection':
        return 'We\'re having trouble connecting to the monitoring service. Please check your internet connection.';
      case 'data':
        return 'The requested data could not be loaded. This might be a temporary issue.';
      case 'server':
        return 'The server encountered an error while processing your request.';
      default:
        return 'An unexpected error occurred. Please try again.';
    }
  };

  const getErrorMessage = () => {
    if (!error) return null;
    
    const errorMessage = typeof error === 'string' ? error : error.message;
    return errorMessage;
  };

  return (
    <div className={`text-center py-12 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300 ${className}`}>
      {getIcon()}
      
      <h3 className="text-lg font-medium text-gray-900 mb-2">
        {getDefaultTitle()}
      </h3>
      
      <p className="text-gray-600 mb-4 max-w-md mx-auto">
        {getDefaultDescription()}
      </p>
      
      {getErrorMessage() && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md max-w-md mx-auto">
          <p className="text-sm text-red-700 font-mono">
            {getErrorMessage()}
          </p>
        </div>
      )}
      
      <div className="flex flex-col sm:flex-row gap-3 justify-center items-center">
        {onRetry && (
          <button
            onClick={onRetry}
            className="inline-flex items-center px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
          >
            <RefreshCw className="w-4 h-4 mr-2" />
            Try Again
          </button>
        )}
        
        {showCachedOption && onViewCached && (
          <button
            onClick={onViewCached}
            className="inline-flex items-center px-4 py-2 bg-gray-200 text-gray-700 text-sm font-medium rounded-md hover:bg-gray-300 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500 transition-colors"
          >
            <Database className="w-4 h-4 mr-2" />
            View Cached Data
          </button>
        )}
      </div>
      
      <div className="mt-6 text-xs text-gray-500">
        <p>If this problem persists, please contact support.</p>
      </div>
    </div>
  );
};

export default DataFallback;