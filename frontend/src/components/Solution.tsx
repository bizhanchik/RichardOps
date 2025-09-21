import React, { useState, useEffect, useRef } from 'react';
import { PanelRightClose, Trash2, Search, RefreshCw, X } from 'lucide-react';
import Sidebar from './solution/Sidebar';
import Dashboard from './solution/Dashboard';
import AskAI from './solution/AskAI';
import Logs from './solution/Logs';
import Analytics from './solution/Analytics';
import { timeUtils } from '../utils/timeUtils';

const Solution: React.FC = () => {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [timeRange, setTimeRange] = useState('1h');
  const [headerVisible, setHeaderVisible] = useState(false);
  const [headerOverTerminal, setHeaderOverTerminal] = useState(false);
  const [activeView, setActiveView] = useState('graphs');
  const [timeSyncStatus, setTimeSyncStatus] = useState(timeUtils.getTimeSyncStatus());
  
  // Logs state
  const [searchQuery, setSearchQuery] = useState('');
  const [logCount, setLogCount] = useState(100);
  const [viewMode, setViewMode] = useState<'count' | 'hour' | 'search'>('count');
  const logsRef = useRef<{ fetchLogs: () => void }>(null);

  // Handle logs refresh
  const handleLogsRefresh = () => {
    if (logsRef.current) {
      logsRef.current.fetchLogs();
    }
  };

  const timeRangeOptions = [
    { value: '1h', label: '1 Hour' },
    { value: '6h', label: '6 Hours' },
    { value: '12h', label: '12 Hours' }
  ];

  useEffect(() => {
    const handleScroll = () => {
      const scrolled = window.scrollY > 10;
      setHeaderVisible(scrolled);
      
      // Check if header is over terminal (for logs view)
      if (activeView === 'logs') {
        // Estimate when header starts overlapping terminal content
        // Terminal typically starts around 200px from top
        const terminalOverlap = window.scrollY > 0;
        setHeaderOverTerminal(terminalOverlap);
      } else {
        setHeaderOverTerminal(false);
      }
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, [activeView]);

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
            ? headerOverTerminal 
              ? 'backdrop-blur-md bg-black/30' 
              : 'backdrop-blur-md bg-white/30'
            : 'backdrop-blur-none bg-transparent'
        } p-4`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <button
                onClick={() => setSidebarOpen(!sidebarOpen)}
                className={`flex items-center justify-center w-10 h-10 rounded-lg border transition-all duration-300 ${
                  headerOverTerminal 
                    ? 'text-gray-300 hover:text-white hover:bg-gray-800 border-gray-600' 
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100 border-gray-200'
                }`}
              >
                <PanelRightClose className="w-5 h-5" />
              </button>
              
              {/* Logs Search Controls - Only show for Logs */}
              {activeView === 'logs' && (
                <div className="flex items-center space-x-3">
                  {/* Search */}
                  <div className={`flex items-center border rounded-lg px-3 py-2 transition-colors duration-300 ${
                    headerOverTerminal 
                      ? 'bg-gray-800 border-gray-600' 
                      : 'bg-white border-gray-200'
                  }`}>
                    <Search className={`w-4 h-4 mr-2 flex-shrink-0 ${
                      headerOverTerminal ? 'text-gray-400' : 'text-gray-400'
                    }`} />
                    <input
                      type="text"
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      placeholder="Search logs..."
                      className={`bg-transparent border-none outline-none flex-1 text-sm transition-colors duration-300 ${
                        headerOverTerminal 
                          ? 'text-gray-200 placeholder-gray-400' 
                          : 'text-gray-900 placeholder-gray-500'
                      }`}
                    />
                    {searchQuery && (
                      <button
                        onClick={() => setSearchQuery('')}
                        className={`ml-2 flex-shrink-0 transition-colors duration-300 ${
                          headerOverTerminal 
                            ? 'text-gray-400 hover:text-gray-200' 
                            : 'text-gray-400 hover:text-gray-600'
                        }`}
                      >
                        <X className="w-4 h-4" />
                      </button>
                    )}
                  </div>
                  
                  <button
                    onClick={() => setViewMode('search')}
                    disabled={!searchQuery.trim()}
                    className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors duration-300 flex items-center space-x-2 disabled:opacity-50 ${
                      headerOverTerminal 
                        ? 'bg-emerald-700 hover:bg-emerald-600 text-white' 
                        : 'bg-emerald-600 hover:bg-emerald-700 text-white'
                    }`}
                  >
                    <Search className="w-4 h-4" />
                    <span>Search</span>
                  </button>
                </div>
              )}
              
              {/* Time Sync Status - Only show critical errors */}
              {activeView === 'graphs' && timeSyncStatus.status === 'error' && (
                <div className="px-3 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800">
                  <span className="mr-1">⚠️</span>
                  Clock drift: {Math.abs(timeSyncStatus.offsetHours)}h
                </div>
              )}
            </div>

            {/* Right Side Controls */}
            <div className="flex items-center space-x-3">
              {/* Logs Count Controls - Only show for Logs */}
              {activeView === 'logs' && (
                <>
                  {/* Log Count Buttons */}
                  {[25, 50, 100, 200, 500].map((count) => (
                    <button
                      key={count}
                      onClick={() => {
                        setLogCount(count);
                        setViewMode('count');
                      }}
                      className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors duration-300 ${
                        viewMode === 'count' && logCount === count
                          ? headerOverTerminal 
                            ? 'bg-emerald-700 text-white' 
                            : 'bg-emerald-600 text-white'
                          : headerOverTerminal 
                            ? 'bg-gray-800 text-gray-200 border border-gray-600 hover:bg-gray-700' 
                            : 'bg-white text-gray-700 border border-gray-200 hover:bg-gray-50'
                      }`}
                    >
                      {count}
                    </button>
                  ))}



                  {/* Refresh Button */}
                  <button
                    onClick={handleLogsRefresh}
                    className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors duration-300 flex items-center space-x-2 border ${
                      headerOverTerminal 
                        ? 'bg-gray-800 hover:bg-gray-700 text-gray-200 border-gray-600' 
                        : 'bg-white hover:bg-gray-50 text-gray-700 border-gray-200'
                    }`}
                    title="Refresh"
                  >
                    <RefreshCw className="w-4 h-4" />
                  </button>
                </>
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
        <div className={`${activeView === 'logs' ? 'p-6' : 'px-6 pt-2 pb-6'} ${activeView === 'ask-ai' || activeView === 'logs' ? 'overflow-hidden' : ''}`}>
          <div className="transition-all duration-500 ease-in-out">
            {activeView === 'graphs' ? (
              <Dashboard timeRange={timeRange} />
            ) : activeView === 'logs' ? (
              <Logs   
                ref={logsRef}
                searchQuery={searchQuery}
                logCount={logCount}
                viewMode={viewMode}
                setSearchQuery={setSearchQuery}
                setLogCount={setLogCount}
                setViewMode={setViewMode}
              />
            ) : activeView === 'analytics' ? (
              <Analytics />
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