import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useApiConnectivity } from '../../utils/apiConnectivity';

interface SidebarProps {
  activeView: string;
  setActiveView: (view: string) => void;
}

const Sidebar: React.FC<SidebarProps> = ({ activeView, setActiveView }) => {
  const navigate = useNavigate();
  const { status } = useApiConnectivity();

  const menuItems = [
    {
      id: 'graphs',
      name: 'Graphs',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
        </svg>
      )
    },
    {
      id: 'logs',
      name: 'Logs',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
      )
    },
    {
      id: 'ask-ai',
      name: 'Ask AI',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
        </svg>
      )
    }
  ];

  return (
    <div className="w-64 bg-white border-r border-gray-200 shadow-sm flex flex-col h-screen">
      {/* Sidebar Header */}
      <div className="p-6 border-b border-gray-200 flex-shrink-0">
        <button 
          onClick={() => navigate('/')}
          className="text-left hover:opacity-80 transition-opacity"
        >
          <h2 className="text-xl font-bold text-gray-900">
            <span>Team </span>
            <span className="text-emerald-600">Richards</span>
          </h2>
          <p className="text-sm text-gray-600 mt-1">AI Security Dashboard</p>
        </button>
      </div>

      {/* Navigation Menu */}
      <nav className="p-4 flex-1">
        <ul className="space-y-2">
          {menuItems.map((item) => (
            <li key={item.id}>
              <button
                onClick={() => setActiveView(item.id)}
                className={`w-full flex items-center px-4 py-3 text-left rounded-lg transition-all duration-300 ease-in-out transform hover:scale-105 ${
                  activeView === item.id
                    ? 'bg-emerald-50 text-emerald-700 border border-emerald-200 shadow-md'
                    : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900 border border-transparent'
                }`}
              >
                <span className={`mr-3 transition-colors duration-300 ${
                  activeView === item.id ? 'text-emerald-600' : 'text-gray-400'
                }`}>
                  {item.icon}
                </span>
                <span className="font-medium">{item.name}</span>
              </button>
            </li>
          ))}
        </ul>
      </nav>

      {/* Footer - Dynamic API Status */}
      <div className="p-4 flex-shrink-0">
        <div className={`rounded-lg p-3 border transition-colors duration-300 ${
          status.isOnline 
            ? 'bg-emerald-50 border-emerald-200' 
            : 'bg-red-50 border-red-200'
        }`}>
          <div className="flex items-center mb-1">
            <div className={`w-2 h-2 rounded-full mr-2 ${
              status.isOnline 
                ? 'bg-emerald-500 animate-pulse' 
                : 'bg-red-500'
            }`}></div>
            <span className="text-sm font-medium text-gray-700">
              {status.isOnline ? 'API Online' : 'API Offline'}
            </span>
            {status.responseTime && (
              <span className="ml-auto text-xs text-gray-500">
                {status.responseTime}ms
              </span>
            )}
          </div>
          <p className="text-xs text-gray-500">
            {status.isOnline 
              ? 'All services operational' 
              : (status.error || 'Connection failed')
            }
          </p>
          <p className="text-xs text-gray-400 mt-1">
            Last: {status.lastCheck.toLocaleTimeString()}
          </p>
        </div>
      </div>
    </div>
  );
};

export default Sidebar;