import React, { useState, useEffect, useRef } from 'react';
import { Search, RefreshCw, Terminal, X } from 'lucide-react';
import { logsDataService, LogsDataService, type LogEntry } from '../../utils/logsDataService';

interface LogsProps {
  // Future props can be added here
}

const Logs: React.FC<LogsProps> = () => {
  // State management
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [logCount, setLogCount] = useState(100);
  const [viewMode, setViewMode] = useState<'count' | 'hour' | 'search'>('count');
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  // Refs
  const logsEndRef = useRef<HTMLDivElement>(null);
  const searchInputRef = useRef<HTMLInputElement>(null);

  // Scroll to bottom function
  const scrollToBottom = () => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  // Fetch logs based on view mode
  const fetchLogs = async () => {
    setIsLoading(true);
    setError(null);

    try {
      let response;
      
      if (viewMode === 'search' && searchQuery.trim()) {
        response = await logsDataService.searchLogs(searchQuery, {
          hours: 1,
          size: 1000
        });
      } else if (viewMode === 'hour') {
        response = await logsDataService.quickSearchLogs({
          hours: 1,
          size: 1000
        });
      } else {
        // Default to count mode - use the new endpoint
        response = await logsDataService.getRecentLogsByCount(logCount);
      }

      setLogs(response.documents || []);
      setLastUpdated(new Date());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch logs');
      console.error('Error fetching logs:', err);
    } finally {
      setIsLoading(false);
    }
  };

  // Handle search
  const handleSearch = () => {
    if (searchQuery.trim()) {
      setViewMode('search');
      fetchLogs();
    }
  };

  // Handle key press in search
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  // Handle view mode changes
  const handleViewModeChange = (mode: 'count' | 'hour' | 'search') => {
    setViewMode(mode);
    if (mode === 'search' && !searchQuery.trim()) {
      return; // Don't fetch if search is empty
    }
  };

  // Initial data fetch and when view mode changes
  useEffect(() => {
    fetchLogs();
  }, [viewMode, logCount]);

  // Focus search input when opening
  useEffect(() => {
    if (searchInputRef.current) {
      searchInputRef.current.focus();
    }
  }, []);

  // Scroll to bottom when new logs arrive
  useEffect(() => {
    if (logs.length > 0) {
      setTimeout(scrollToBottom, 100);
    }
  }, [logs]);

  return (
    <div className="h-full flex flex-col">
      {/* Header Controls */}
      <div className="flex-shrink-0 bg-black border-b border-gray-800 p-4 rounded-t-xl">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          {/* Left Side - View Mode Controls */}
          <div className="flex flex-col sm:flex-row items-start sm:items-center space-y-3 sm:space-y-0 sm:space-x-3">
            {/* Search */}
            <div className="flex items-center bg-gray-800 rounded-lg border border-gray-600 px-3 py-2 w-full sm:w-80">
              <Search className="w-4 h-4 text-gray-400 mr-2 flex-shrink-0" />
              <input
                ref={searchInputRef}
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Search logs..."
                className="bg-transparent border-none outline-none flex-1 text-sm placeholder-gray-400 text-white"
              />
              {searchQuery && (
                <button
                  onClick={() => setSearchQuery('')}
                  className="text-gray-400 hover:text-gray-200 ml-2 flex-shrink-0"
                >
                  <X className="w-4 h-4" />
                </button>
              )}
            </div>
            
            <button
              onClick={handleSearch}
              disabled={isLoading || !searchQuery.trim()}
              className="bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors flex items-center space-x-2 disabled:opacity-50"
            >
              <Search className="w-4 h-4" />
              <span>Search</span>
            </button>
          </div>

          {/* Right Side - Controls */}
          <div className="flex flex-wrap items-center gap-2">
            {/* Log Count Buttons */}
            {[25, 50, 100, 200, 500].map((count) => (
              <button
                key={count}
                onClick={() => {
                  setLogCount(count);
                  handleViewModeChange('count');
                }}
                className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  viewMode === 'count' && logCount === count
                    ? 'bg-emerald-600 text-white'
                    : 'bg-gray-700 text-gray-200 border border-gray-600 hover:bg-gray-600'
                }`}
              >
                {count}
              </button>
            ))}

            {/* OR separator */}
            <span className="text-gray-400 text-sm mx-1">or</span>

            {/* Last Hour Button */}
            <button
              onClick={() => handleViewModeChange('hour')}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                viewMode === 'hour'
                  ? 'bg-emerald-600 text-white'
                  : 'bg-gray-700 text-gray-200 border border-gray-600 hover:bg-gray-600'
              }`}
            >
              Last Hour
            </button>

            {/* Refresh Button */}
            <button
              onClick={fetchLogs}
              disabled={isLoading}
              className="bg-gray-700 hover:bg-gray-600 text-gray-200 px-3 py-2 rounded-lg text-sm font-medium transition-colors flex items-center space-x-2 border border-gray-600 disabled:opacity-50 ml-2"
              title="Refresh"
            >
              <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>

        {/* Status Bar */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 text-sm text-gray-300 mt-3">
          <div className="flex flex-col sm:flex-row sm:items-center space-y-1 sm:space-y-0 sm:space-x-4">
            <span>
              Showing {logs.length} logs
              {viewMode === 'search' && searchQuery && ` for "${searchQuery}"`}
              {viewMode === 'hour' && ' from last hour'}
              {viewMode === 'count' && ` (last ${logCount})`}
            </span>
          </div>
          <div className="flex items-center space-x-2">
            <span className="truncate text-xs text-gray-400">
              {lastUpdated ? `Updated: ${lastUpdated.toLocaleTimeString()}` : 'Not updated'}
            </span>
          </div>
        </div>
      </div>

      {/* Logs Display - Terminal Style (Full Height) */}
      <div className="flex-1 overflow-hidden p-4">
        <div className="h-full bg-black text-green-400 font-mono text-sm rounded-xl border border-gray-800 flex flex-col">
          {/* Terminal Header */}
          <div className="flex items-center space-x-2 p-6 pb-2 border-b border-gray-700 flex-shrink-0">
            <Terminal className="w-4 h-4" />
            <span className="text-green-300">RichardOps Logs Terminal</span>
            <span className="text-gray-500">({logs.length} entries)</span>
          </div>

          {/* Scrollable Content Area */}
          <div className="flex-1 overflow-y-auto p-6 pt-4">
            {/* Error State */}
            {error && (
              <div className="text-red-400 mb-4 p-3 bg-red-900/20 border border-red-800 rounded">
                <span className="text-red-300">Error: </span>
                {error}
              </div>
            )}

            {/* Loading State */}
            {isLoading && (
              <div className="text-yellow-400 mb-4 flex items-center space-x-2">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-yellow-400"></div>
                <span>Loading logs...</span>
              </div>
            )}

            {/* Empty State */}
            {!isLoading && logs.length === 0 && !error && (
              <div className="text-gray-500 text-center py-8">
                <Terminal className="w-12 h-12 mx-auto mb-4 opacity-50" />
                <p className="text-lg mb-2">No logs found</p>
                <p className="text-sm">
                  {viewMode === 'search' ? 'Try adjusting your search query' : 'No logs available'}
                </p>
              </div>
            )}

            {/* Log Entries - Scrollable */}
            <div className="space-y-2">
              {logs.map((log, index) => {
                const timestamp = LogsDataService.formatTimestamp(log.timestamp);
                
                return (
                  <div key={log.id || index} className="mb-2 hover:bg-gray-900/50 p-2 rounded transition-colors">
                    <div className="flex flex-col lg:flex-row lg:items-start space-y-1 lg:space-y-0 lg:space-x-3">
                      {/* Top row: Timestamp, Level (if available), and Container */}
                      <div className="flex items-center space-x-3 lg:flex-none">
                        {/* Timestamp */}
                        <span className="text-gray-400 text-xs whitespace-nowrap">
                          <span className="hidden sm:inline">{timestamp.split(' ')[0]} </span>
                          {timestamp.split(' ')[1]} {/* Show only time on mobile, full on desktop */}
                        </span>
                        
                        {/* Level Badge (if available) */}
                        {log.level && (
                          <span className={`px-2 py-1 rounded text-xs font-medium whitespace-nowrap ${
                            log.level === 'ERROR' ? 'bg-red-900 text-red-300' :
                            log.level === 'WARN' ? 'bg-yellow-900 text-yellow-300' :
                            log.level === 'INFO' ? 'bg-blue-900 text-blue-300' :
                            'bg-gray-800 text-gray-300'
                          }`}>
                            {log.level}
                          </span>
                        )}

                        {/* Container Info */}
                        {log.container && (
                          <span className="text-purple-400 text-xs whitespace-nowrap">
                            [{log.container}]
                          </span>
                        )}
                      </div>

                      {/* Message */}
                      <div className="flex-1 min-w-0">
                        <span className="text-green-400 break-words font-mono">
                          {log.message}
                        </span>
                      </div>
                    </div>

                    {/* Additional metadata on second line if available */}
                    {(log.host || log.environment) && (
                      <div className="mt-1 lg:ml-16 text-xs text-gray-500">
                        {log.host && <span>host: {log.host}</span>}
                        {log.host && log.environment && <span className="mx-2">|</span>}
                        {log.environment && <span>env: {log.environment}</span>}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
            
            {/* Scroll anchor */}
            <div ref={logsEndRef} />
          </div>
        </div>
      </div>
    </div>
  );
};

export default Logs;