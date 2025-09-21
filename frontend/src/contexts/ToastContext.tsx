import React, { createContext, useContext, useState, useCallback } from 'react';
import ToastNotification, { Toast } from '../components/shared/ToastNotification';

interface ToastContextType {
  showToast: (toast: Omit<Toast, 'id'>) => void;
  showSuccess: (title: string, message: string, actions?: Toast['actions']) => void;
  showError: (title: string, message: string, actions?: Toast['actions']) => void;
  showWarning: (title: string, message: string, actions?: Toast['actions']) => void;
  showInfo: (title: string, message: string, actions?: Toast['actions']) => void;
  dismissToast: (id: string) => void;
  clearAllToasts: () => void;
}

export const ToastContext = createContext<ToastContextType | undefined>(undefined);

export const useToast = () => {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToast must be used within a ToastProvider');
  }
  return context;
};

interface ToastProviderProps {
  children: React.ReactNode;
}

export const ToastProvider: React.FC<ToastProviderProps> = ({ children }) => {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const generateId = () => {
    return `toast-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  };

  const showToast = useCallback((toastData: Omit<Toast, 'id'>) => {
    const toast: Toast = {
      ...toastData,
      id: generateId(),
      duration: toastData.duration ?? 5000, // Default 5 seconds
    };

    setToasts(prev => [...prev, toast]);
  }, []);

  const showSuccess = useCallback((title: string, message: string, actions?: Toast['actions']) => {
    showToast({ type: 'success', title, message, actions });
  }, [showToast]);

  const showError = useCallback((title: string, message: string, actions?: Toast['actions']) => {
    showToast({ type: 'error', title, message, actions, duration: 8000 }); // Longer duration for errors
  }, [showToast]);

  const showWarning = useCallback((title: string, message: string, actions?: Toast['actions']) => {
    showToast({ type: 'warning', title, message, actions });
  }, [showToast]);

  const showInfo = useCallback((title: string, message: string, actions?: Toast['actions']) => {
    showToast({ type: 'info', title, message, actions });
  }, [showToast]);

  const dismissToast = useCallback((id: string) => {
    setToasts(prev => prev.filter(toast => toast.id !== id));
  }, []);

  const clearAllToasts = useCallback(() => {
    setToasts([]);
  }, []);

  const value: ToastContextType = {
    showToast,
    showSuccess,
    showError,
    showWarning,
    showInfo,
    dismissToast,
    clearAllToasts,
  };

  return (
    <ToastContext.Provider value={value}>
      {children}
      
      {/* Toast Container */}
      <div className="fixed top-4 right-4 z-50 space-y-2">
        {toasts.map((toast) => (
          <ToastNotification
            key={toast.id}
            toast={toast}
            onDismiss={dismissToast}
          />
        ))}
      </div>
    </ToastContext.Provider>
  );
};

export default ToastProvider;