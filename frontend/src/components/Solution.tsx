import React, { useState, useEffect } from 'react';
import { PanelRightClose, Trash2 } from 'lucide-react';
import Sidebar from './solution/Sidebar';
import Dashboard from './solution/Dashboard';
import AskAI from './solution/AskAI';
import Logs from './solution/Logs';
import { timeUtils } from '../utils/timeUtils';

const Solution: React.FC = () => {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [timeRange, setTimeRange] = useState('1h');
  const [headerVisible, setHeaderVisible] = useState(false);
  const [activeView, setActiveView] = useState('graphs');
  const [timeSyncStatus, setTimeSyncStatus] = useState(timeUtils.getTimeSyncStatus());

  const timeRangeOptions = [
    { value: '1h', label: '1 Hour' },
    { value: '6h', label: '6 Hours' },
    { value: '12h', label: '12 Hours' }
  ];

  useEffect(() => {
    const handleScroll = () => {
      const scrolled = window.scrollY > 10;
      setHeaderVisible(scrolled);
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  // Update time sync status periodically
  useEffect(() => {
    const updateTimeSyncStatus = () => {
      setTimeSyncStatus(timeUtils.getTimeSyncStatus());
    };

    // Update immediately and then every 30 seconds
    updateTimeSyncStatus();
    const interval = setInterval(updateTimeSyncStatus, 30000);

    return () => clearInterval(interval);
  }, []);

  // Handle view changes and reset scroll
  const handleViewChange = (newView: string) => {
    // Reset header visibility
    setHeaderVisible(false);
    // Change the view
    setActiveView(newView);
    // Only scroll to top when switching TO graphs (not to Ask AI)
    if (newView === 'graphs') {
      setTimeout(() => {
        window.scrollTo({ top: 0, behavior: 'auto' });
      }, 50);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Left Sidebar - Fixed Position */}
      <div className={`fixed left-0 top-0 h-full z-30 transition-transform duration-300 ease-in-out ${
        sidebarOpen ? 'translate-x-0' : '-translate-x-64'
      }`}>
        <Sidebar activeView={activeView} setActiveView={handleViewChange} />
      </div>
      
      {/* Main Content */}
      <div className={`transition-all duration-300 ease-in-out ${
        sidebarOpen ? 'ml-64' : 'ml-0'
      }`}>
        {/* Header with Toggle Button and Time Range */}
        <div className={`sticky top-0 z-20 transition-all duration-300 ease-out ${
          headerVisible 
            ? 'backdrop-blur-md bg-white/30' 
            : 'backdrop-blur-none bg-transparent'
        } p-4`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <button
                onClick={() => setSidebarOpen(!sidebarOpen)}
                className="flex items-center justify-center w-10 h-10 text-gray-600 hover:text-gray-900 hover:bg-white rounded-lg border border-gray-200 transition-all duration-200"
              >
                <PanelRightClose className="w-5 h-5" />
              </button>
              
              {/* Time Sync Status - Only show critical errors */}
              {activeView === 'graphs' && timeSyncStatus.status === 'error' && (
                <div className="px-3 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800">
                  <span className="mr-1">⚠️</span>
                  Clock drift: {Math.abs(timeSyncStatus.offsetHours)}h
                </div>
              )}
            </div>
            
            {/* Time Range Selector - Only show for Graphs */}
            {activeView === 'graphs' && (
              <div className="flex items-center space-x-2">
                <span className="text-sm text-gray-600 mr-2">Time Range:</span>
                {timeRangeOptions.map((option) => (
                  <button
                    key={option.value}
                    onClick={() => setTimeRange(option.value)}
                    className={`px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                      timeRange === option.value
                        ? 'bg-emerald-600 text-white shadow-md'
                        : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50'
                    }`}
                  >
                    {option.label}
                  </button>
                ))}
              </div>
            )}

            {/* Clear Chat Button - Only show for Ask AI */}
            {activeView === 'ask-ai' && (
              <button
                onClick={() => {
                  // TODO: Implement clear chat functionality when message storage is added
                  console.log('Clear chat clicked - functionality to be implemented');
                }}
                className="flex items-center space-x-2 px-4 py-2 bg-white text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50 hover:text-gray-900 transition-all duration-200"
              >
                <Trash2 className="w-4 h-4" />
                <span className="text-sm font-medium">Clear Chat</span>
              </button>
            )}
          </div>
        </div>
        
        {/* Main Content Area */}
        <div className={`px-6 pt-2 pb-6 ${activeView === 'ask-ai' || activeView === 'logs' ? 'overflow-hidden' : ''}`}>
          <div className="transition-all duration-500 ease-in-out">
            {activeView === 'graphs' ? (
              <Dashboard timeRange={timeRange} />
            ) : activeView === 'logs' ? (
              <Logs />
            ) : (
              <AskAI sidebarOpen={sidebarOpen} />
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Solution;