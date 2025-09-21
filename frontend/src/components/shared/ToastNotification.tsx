import React, { useState, useEffect } from 'react';
import { AlertCircle, CheckCircle, Info, X, AlertTriangle } from 'lucide-react';

export interface Toast {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message: string;
  duration?: number;
  actions?: Array<{
    label: string;
    onClick: () => void;
    variant?: 'primary' | 'secondary';
  }>;
}

interface ToastNotificationProps {
  toast: Toast;
  onDismiss: (id: string) => void;
}

const ToastNotification: React.FC<ToastNotificationProps> = ({ toast, onDismiss }) => {
  const [isVisible, setIsVisible] = useState(true);
  const [isExiting, setIsExiting] = useState(false);

  useEffect(() => {
    if (toast.duration && toast.duration > 0) {
      const timer = setTimeout(() => {
        handleDismiss();
      }, toast.duration);

      return () => clearTimeout(timer);
    }
  }, [toast.duration]);

  const handleDismiss = () => {
    setIsExiting(true);
    setTimeout(() => {
      onDismiss(toast.id);
    }, 300);
  };

  const getIcon = () => {
    switch (toast.type) {
      case 'success':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'error':
        return <AlertCircle className="w-5 h-5 text-red-500" />;
      case 'warning':
        return <AlertTriangle className="w-5 h-5 text-yellow-500" />;
      case 'info':
        return <Info className="w-5 h-5 text-blue-500" />;
      default:
        return <Info className="w-5 h-5 text-blue-500" />;
    }
  };

  const getBackgroundColor = () => {
    switch (toast.type) {
      case 'success':
        return 'bg-green-50 border-green-200';
      case 'error':
        return 'bg-red-50 border-red-200';
      case 'warning':
        return 'bg-yellow-50 border-yellow-200';
      case 'info':
        return 'bg-blue-50 border-blue-200';
      default:
        return 'bg-blue-50 border-blue-200';
    }
  };

  const getTitleColor = () => {
    switch (toast.type) {
      case 'success':
        return 'text-green-800';
      case 'error':
        return 'text-red-800';
      case 'warning':
        return 'text-yellow-800';
      case 'info':
        return 'text-blue-800';
      default:
        return 'text-blue-800';
    }
  };

  const getMessageColor = () => {
    switch (toast.type) {
      case 'success':
        return 'text-green-700';
      case 'error':
        return 'text-red-700';
      case 'warning':
        return 'text-yellow-700';
      case 'info':
        return 'text-blue-700';
      default:
        return 'text-blue-700';
    }
  };

  if (!isVisible) return null;

  return (
    <div
      className={`
        fixed top-4 right-4 max-w-md w-full border rounded-lg p-4 shadow-lg z-50
        transform transition-all duration-300 ease-in-out
        ${isExiting ? 'translate-x-full opacity-0' : 'translate-x-0 opacity-100'}
        ${getBackgroundColor()}
      `}
    >
      <div className="flex items-start">
        <div className="flex-shrink-0">
          {getIcon()}
        </div>
        <div className="ml-3 flex-1">
          <h3 className={`text-sm font-medium ${getTitleColor()}`}>
            {toast.title}
          </h3>
          <p className={`text-sm mt-1 ${getMessageColor()}`}>
            {toast.message}
          </p>
          
          {toast.actions && toast.actions.length > 0 && (
            <div className="mt-3 flex space-x-2">
              {toast.actions.map((action, index) => (
                <button
                  key={index}
                  onClick={action.onClick}
                  className={`
                    text-xs px-3 py-1 rounded font-medium transition-colors
                    ${action.variant === 'primary' 
                      ? `${toast.type === 'error' ? 'bg-red-100 hover:bg-red-200 text-red-800' :
                          toast.type === 'warning' ? 'bg-yellow-100 hover:bg-yellow-200 text-yellow-800' :
                          toast.type === 'success' ? 'bg-green-100 hover:bg-green-200 text-green-800' :
                          'bg-blue-100 hover:bg-blue-200 text-blue-800'}`
                      : `${getMessageColor()} hover:underline bg-transparent`
                    }
                  `}
                >
                  {action.label}
                </button>
              ))}
            </div>
          )}
        </div>
        <div className="ml-4 flex-shrink-0">
          <button
            onClick={handleDismiss}
            className={`
              inline-flex rounded-md p-1.5 transition-colors
              ${toast.type === 'error' ? 'text-red-400 hover:bg-red-100' :
                toast.type === 'warning' ? 'text-yellow-400 hover:bg-yellow-100' :
                toast.type === 'success' ? 'text-green-400 hover:bg-green-100' :
                'text-blue-400 hover:bg-blue-100'}
            `}
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};

export default ToastNotification;