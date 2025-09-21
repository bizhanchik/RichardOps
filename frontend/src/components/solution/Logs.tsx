import React, { useState, useEffect, useRef, forwardRef, useImperativeHandle, useContext } from 'react';
import { Search, RefreshCw, Terminal, X, Filter, Download, Eye, Settings } from 'lucide-react';
import { logsDataService, LogsDataService, type LogEntry } from '../../utils/logsDataService';
import LogFilterPanel from '../shared/LogFilterPanel';
import { ToastContext } from '../../contexts/ToastContext';

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
  const [showFilters, setShowFilters] = useState(false);
  const [filters, setFilters] = useState({
    timeRange: { start: '', end: '' },
    levels: [] as string[],
    containers: [] as string[],
    hosts: [] as string[],
    environments: [] as string[]
  });
  
  // Toast context
  const { showToast } = useContext(ToastContext);

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
      
      // Build search parameters with filters
      const searchParams: any = {
        size: logCount
      };
      
      // Apply filters
      if (filters.levels.length > 0) {
        searchParams.level = filters.levels.join(',');
      }
      if (filters.containers.length > 0) {
        searchParams.container = filters.containers.join(',');
      }
      if (filters.timeRange.start && filters.timeRange.end) {
        searchParams.start_time = filters.timeRange.start;
        searchParams.end_time = filters.timeRange.end;
      }
      
      if (viewMode === 'search' && searchQuery.trim()) {
        searchParams.query = searchQuery;
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

      if (response.fallback) {
        setError('Using fallback data - some logs may be missing');
        showToast('warning', 'Using cached data', 'Some logs may be missing due to connection issues');
      } else {
        showToast('success', 'Logs loaded', `Successfully loaded ${response.documents?.length || 0} log entries`);
      }

      // Reverse the logs to show newest at bottom
      const reversedLogs = (response.documents || []).reverse();
      setLogs(reversedLogs);
      setLastUpdated(new Date());
      
      // Always scroll to bottom to show newest logs
      setTimeout(scrollToBottom, 100);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch logs';
      setError(errorMessage);
      showToast('error', 'Failed to load logs', errorMessage);
      console.error('Error fetching logs:', err);
    } finally {
      setIsLoading(false);
    }
  };

  // Expose fetchLogs function to parent component
  useImperativeHandle(ref, () => ({
    fetchLogs: () => fetchLogs(true) // Always scroll to bottom when refreshing
  }));

  // Export logs functionality
  const exportLogs = (format: 'csv' | 'json') => {
    try {
      let content: string;
      let filename: string;
      let mimeType: string;

      if (format === 'csv') {
        const headers = ['Timestamp', 'Level', 'Container', 'Host', 'Environment', 'Message'];
        const csvContent = [
          headers.join(','),
          ...logs.map(log => [
            log.timestamp,
            log.level || '',
            log.container || '',
            log.host || '',
            log.environment || '',
            `"${log.message.replace(/"/g, '""')}"` // Escape quotes in CSV
          ].join(','))
        ].join('\n');
        
        content = csvContent;
        filename = `logs-${new Date().toISOString().split('T')[0]}.csv`;
        mimeType = 'text/csv';
      } else {
        content = JSON.stringify(logs, null, 2);
        filename = `logs-${new Date().toISOString().split('T')[0]}.json`;
        mimeType = 'application/json';
      }

      const blob = new Blob([content], { type: mimeType });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);

      showToast('success', 'Export completed', `Logs exported as ${filename}`);
    } catch (err) {
      showToast('error', 'Export failed', 'Failed to export logs');
      console.error('Export error:', err);
    }
  };

  // Filter handlers
  const handleFilterChange = (newFilters: typeof filters) => {
    setFilters(newFilters);
    // Refetch logs with new filters
    fetchLogs();
  };

  const clearFilters = () => {
    setFilters({
      timeRange: { start: '', end: '' },
      levels: [],
      containers: [],
      hosts: [],
      environments: []
    });
    fetchLogs();
  };

  // Initial data fetch and when view mode changes
  useEffect(() => {
    fetchLogs();
  }, [viewMode, viewMode === 'search' ? searchQuery : logCount, filters]);

  // Only scroll to bottom on manual refresh, not on view mode changes
  // Removed auto-scroll to prevent unwanted scrolling when changing count buttons

  return (
    <div className="h-full flex flex-col">
      {/* Terminal Body - Fixed Window Height */}
      <div className="flex-1 overflow-hidden">
        <div className="h-[80vh] bg-white text-gray-800 font-mono text-sm sm:text-base border border-gray-300 flex flex-col rounded-lg shadow-2xl">
          {/* Terminal Header - Enhanced */}
          <div className="flex items-center justify-between p-3 sm:p-6 pb-2 sm:pb-4 border-b border-gray-300 flex-shrink-0 flex-wrap gap-2">
            <div className="flex items-center space-x-2 sm:space-x-4 flex-wrap min-w-0">
              <div className="flex space-x-2 flex-shrink-0">
                <div className="w-3 h-3 bg-red-500 rounded-full"></div>
                <div className="w-3 h-3 bg-yellow-500 rounded-full"></div>
                <div className="w-3 h-3 bg-green-500 rounded-full"></div>
              </div>
              <div className="flex items-center space-x-2 min-w-0">
                <Terminal className="w-4 h-4 flex-shrink-0" />
                <span className="text-gray-700 font-medium text-sm sm:text-base truncate">RichardOps Logs Terminal</span>
              </div>
              <div className="flex items-center space-x-2 text-xs sm:text-sm text-gray-600 flex-wrap">
                <span>({logs.length} entries)</span>
                {lastUpdated && (
                  <span className="text-xs hidden sm:inline">
                    • Updated {lastUpdated.toLocaleTimeString()}
                  </span>
                )}
              </div>
              {isLoading && (
                <div className="flex items-center space-x-2 flex-shrink-0">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-500"></div>
                  <span className="text-blue-600 text-xs sm:text-sm">Loading...</span>
                </div>
              )}
            </div>
            
            {/* Action Controls */}
            <div className="flex items-center space-x-1 sm:space-x-2 flex-shrink-0">
              <button
                onClick={() => setShowFilters(!showFilters)}
                className={`inline-flex items-center px-2 sm:px-3 py-1.5 text-xs sm:text-sm font-medium rounded-md transition-colors ${
                  showFilters 
                    ? 'bg-blue-100 text-blue-700 hover:bg-blue-200' 
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
                title="Toggle filters"
              >
                <Filter className="w-4 h-4 mr-1" />
                <span className="hidden sm:inline">Filters</span>
                <span className="sm:hidden">F</span>
                {(filters.levels.length > 0 || filters.containers.length > 0 || filters.timeRange.start) && (
                  <span className="ml-1 px-1.5 py-0.5 bg-blue-500 text-white text-xs rounded-full">
                    {filters.levels.length + filters.containers.length + (filters.timeRange.start ? 1 : 0)}
                  </span>
                )}
              </button>
              
              <div className="relative group">
                <button className="inline-flex items-center px-2 sm:px-3 py-1.5 text-xs sm:text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-md transition-colors">
                  <Download className="w-4 h-4 mr-1" />
                  <span className="hidden sm:inline">Export</span>
                  <span className="sm:hidden">E</span>
                </button>
                <div className="absolute right-0 top-full mt-1 w-32 bg-white border border-gray-200 rounded-md shadow-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-10">
                  <button
                    onClick={() => exportLogs('csv')}
                    className="w-full px-3 py-2 text-left text-sm text-gray-700 hover:bg-gray-50 transition-colors"
                  >
                    Export CSV
                  </button>
                  <button
                    onClick={() => exportLogs('json')}
                    className="w-full px-3 py-2 text-left text-sm text-gray-700 hover:bg-gray-50 transition-colors"
                  >
                    Export JSON
                  </button>
                </div>
              </div>
              
              <button
                onClick={() => fetchLogs(true)}
                disabled={isLoading}
                className="inline-flex items-center px-2 sm:px-3 py-1.5 text-xs sm:text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed rounded-md transition-colors"
                title="Refresh logs"
              >
                <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
              </button>
            </div>
          </div>
          
          {/* Filter Panel */}
          {showFilters && (
            <div className="border-b border-gray-300 bg-gray-50">
              <LogFilterPanel
                filters={filters}
                onFiltersChange={handleFilterChange}
                onClearFilters={clearFilters}
                availableContainers={Array.from(new Set(logs.map(log => log.container).filter(Boolean)))}
                availableHosts={Array.from(new Set(logs.map(log => log.host).filter(Boolean)))}
                availableEnvironments={Array.from(new Set(logs.map(log => log.environment).filter(Boolean)))}
              />
            </div>
          )}

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