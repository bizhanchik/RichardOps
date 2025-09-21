import React, { useState, useEffect, useRef, forwardRef, useImperativeHandle } from 'react';
import { Search, RefreshCw, Terminal, X } from 'lucide-react';
import { logsDataService, LogsDataService, type LogEntry } from '../../utils/logsDataService';

interface LogsProps {
  searchQuery: string;
  logCount: number;
  viewMode: 'count' | 'hour' | 'search';
  setSearchQuery: (query: string) => void;
  setLogCount: (count: number) => void;
  setViewMode: (mode: 'count' | 'hour' | 'search') => void;
}

interface LogsRef {
  fetchLogs: () => void;
}

const Logs = forwardRef<LogsRef, LogsProps>(({ 
  searchQuery, 
  logCount, 
  viewMode, 
  setSearchQuery, 
  setLogCount, 
  setViewMode 
}, ref) => {
  // State management
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  // Refs
  const logsEndRef = useRef<HTMLDivElement>(null);

  // Scroll to bottom function
  const scrollToBottom = () => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  // Fetch logs based on view mode
  const fetchLogs = async (shouldScroll: boolean = false) => {
    setIsLoading(true);
    setError(null);

    try {
      let response;
      
      if (viewMode === 'search' && searchQuery.trim()) {
        response = await logsDataService.searchLogsWithLimit(searchQuery, 50);
      } else if (viewMode === 'hour') {
        response = await logsDataService.quickSearchLogs({
          hours: 1,
          size: 1000
        });
      } else {
        // Default to count mode - use the new endpoint
        response = await logsDataService.getRecentLogsByCount(logCount);
      }

      // Reverse the logs to show newest at bottom
      const reversedLogs = (response.documents || []).reverse();
      setLogs(reversedLogs);
      setLastUpdated(new Date());
      
      // Always scroll to bottom to show newest logs
      setTimeout(scrollToBottom, 100);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch logs');
      console.error('Error fetching logs:', err);
    } finally {
      setIsLoading(false);
    }
  };

  // Expose fetchLogs function to parent component
  useImperativeHandle(ref, () => ({
    fetchLogs: () => fetchLogs(true) // Always scroll to bottom when refreshing
  }));

  // Initial data fetch and when view mode changes
  useEffect(() => {
    fetchLogs();
  }, [viewMode, viewMode === 'search' ? searchQuery : logCount]);

  // Only scroll to bottom on manual refresh, not on view mode changes
  // Removed auto-scroll to prevent unwanted scrolling when changing count buttons

  return (
    <div className="h-full flex flex-col">
      {/* Terminal Body - Fixed Window Height */}
      <div className="flex-1 overflow-hidden">
        <div className="h-[80vh] bg-white text-gray-800 font-mono text-base border border-gray-300 flex flex-col rounded-lg shadow-2xl">
          {/* Terminal Header - Static */}
          <div className="flex items-center space-x-2 p-6 pb-2 border-b border-gray-300 flex-shrink-0">
            <div className="flex space-x-2">
              <div className="w-3 h-3 bg-red-500 rounded-full"></div>
              <div className="w-3 h-3 bg-yellow-500 rounded-full"></div>
              <div className="w-3 h-3 bg-green-500 rounded-full"></div>
            </div>
            <Terminal className="w-4 h-4 ml-4" />
            <span className="text-gray-700">RichardOps Logs Terminal ({logs.length} entries)</span>
            {isLoading && (
              <div className="ml-3 flex items-center space-x-2">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-500"></div>
                <span className="text-blue-600 text-sm">Loading...</span>
              </div>
            )}
          </div>

          {/* Scrollable Content Area */}
          <div 
            className="flex-1 overflow-y-auto p-6 pt-4 scrollbar-thin scrollbar-track-gray-100 scrollbar-thumb-gray-400 hover:scrollbar-thumb-gray-500"
            style={{
              scrollbarColor: '#9CA3AF #F3F4F6',
              scrollbarWidth: 'thin'
            }}
          >
            {/* Error State */}
            {error && (
              <div className="text-red-700 mb-4 p-3 bg-red-50 border border-red-200 rounded">
                <span className="text-red-600 font-medium">Error: </span>
                {error}
              </div>
            )}



            {/* Empty State */}
            {!isLoading && logs.length === 0 && !error && (
              <div className="text-gray-600 text-center py-8">
                <Terminal className="w-12 h-12 mx-auto mb-4 opacity-50 text-gray-400" />
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
                  <div key={log.id || index} className="mb-2 hover:bg-gray-50 p-2 rounded transition-colors">
                    <div className="flex flex-col lg:flex-row lg:items-start space-y-1 lg:space-y-0 lg:space-x-3">
                      {/* Top row: Timestamp, Level (if available), and Container */}
                      <div className="flex items-center space-x-3 lg:flex-none">
                        {/* Timestamp */}
                        <span className="text-blue-600 text-sm whitespace-nowrap font-medium">
                          <span className="hidden sm:inline">{timestamp.split(' ')[0]} </span>
                          {timestamp.split(' ')[1]} {/* Show only time on mobile, full on desktop */}
                        </span>
                        
                        {/* Level Badge (if available) */}
                        {log.level && (
                          <span className={`px-2 py-1 rounded text-sm font-medium whitespace-nowrap ${
                            log.level === 'ERROR' ? 'bg-red-100 text-red-700 border border-red-200' :
                            log.level === 'WARN' ? 'bg-yellow-100 text-yellow-700 border border-yellow-200' :
                            log.level === 'INFO' ? 'bg-blue-100 text-blue-700 border border-blue-200' :
                            'bg-gray-100 text-gray-700 border border-gray-200'
                          }`}>
                            {log.level}
                          </span>
                        )}

                        {/* Container Info */}
                        {log.container && (
                          <span className="text-purple-700 text-sm whitespace-nowrap font-medium">
                            [{log.container}]
                          </span>
                        )}
                      </div>

                      {/* Message */}
                      <div className="flex-1 min-w-0">
                        <span className="text-green-600 break-words font-mono">
                          {log.message}
                        </span>
                      </div>
                    </div>

                    {/* Additional metadata on second line if available */}
                    {(log.host || log.environment) && (
                      <div className="mt-1 lg:ml-16 text-sm text-gray-700">
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
});

Logs.displayName = 'Logs';

export default Logs;