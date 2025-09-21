import React, { useState, useEffect } from 'react';
import { 
  Filter, 
  Calendar, 
  Clock, 
  Server, 
  AlertCircle, 
  Search, 
  X, 
  ChevronDown,
  Download,
  RefreshCw
} from 'lucide-react';

interface LogFilter {
  timeRange: {
    start: string;
    end: string;
    preset?: 'last-hour' | 'last-4-hours' | 'last-24-hours' | 'last-7-days' | 'custom';
  };
  levels: string[];
  containers: string[];
  searchTerm: string;
  severity?: string[];
}

interface LogFilterPanelProps {
  onFilterChange: (filters: LogFilter) => void;
  onExport?: (format: 'csv' | 'json') => void;
  onRefresh?: () => void;
  availableContainers?: string[];
  isLoading?: boolean;
  className?: string;
}

const LogFilterPanel: React.FC<LogFilterPanelProps> = ({
  onFilterChange,
  onExport,
  onRefresh,
  availableContainers = [],
  isLoading = false,
  className = ''
}) => {
  const [filters, setFilters] = useState<LogFilter>({
    timeRange: {
      start: '',
      end: '',
      preset: 'last-24-hours'
    },
    levels: [],
    containers: [],
    searchTerm: '',
    severity: []
  });

  const [isExpanded, setIsExpanded] = useState(false);
  const [showExportMenu, setShowExportMenu] = useState(false);

  const logLevels = ['DEBUG', 'INFO', 'WARN', 'ERROR', 'FATAL'];
  const severityLevels = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'];

  const timePresets = [
    { value: 'last-hour', label: 'Last Hour' },
    { value: 'last-4-hours', label: 'Last 4 Hours' },
    { value: 'last-24-hours', label: 'Last 24 Hours' },
    { value: 'last-7-days', label: 'Last 7 Days' },
    { value: 'custom', label: 'Custom Range' }
  ];

  useEffect(() => {
    // Set default time range based on preset
    if (filters.timeRange.preset && filters.timeRange.preset !== 'custom') {
      const now = new Date();
      const start = new Date();
      
      switch (filters.timeRange.preset) {
        case 'last-hour':
          start.setHours(now.getHours() - 1);
          break;
        case 'last-4-hours':
          start.setHours(now.getHours() - 4);
          break;
        case 'last-24-hours':
          start.setDate(now.getDate() - 1);
          break;
        case 'last-7-days':
          start.setDate(now.getDate() - 7);
          break;
      }

      setFilters(prev => ({
        ...prev,
        timeRange: {
          ...prev.timeRange,
          start: start.toISOString().slice(0, 16),
          end: now.toISOString().slice(0, 16)
        }
      }));
    }
  }, [filters.timeRange.preset]);

  useEffect(() => {
    onFilterChange(filters);
  }, [filters, onFilterChange]);

  const handleTimePresetChange = (preset: string) => {
    setFilters(prev => ({
      ...prev,
      timeRange: {
        ...prev.timeRange,
        preset: preset as any
      }
    }));
  };

  const handleTimeRangeChange = (field: 'start' | 'end', value: string) => {
    setFilters(prev => ({
      ...prev,
      timeRange: {
        ...prev.timeRange,
        [field]: value,
        preset: 'custom'
      }
    }));
  };

  const handleLevelToggle = (level: string) => {
    setFilters(prev => ({
      ...prev,
      levels: prev.levels.includes(level)
        ? prev.levels.filter(l => l !== level)
        : [...prev.levels, level]
    }));
  };

  const handleContainerToggle = (container: string) => {
    setFilters(prev => ({
      ...prev,
      containers: prev.containers.includes(container)
        ? prev.containers.filter(c => c !== container)
        : [...prev.containers, container]
    }));
  };

  const handleSeverityToggle = (severity: string) => {
    setFilters(prev => ({
      ...prev,
      severity: prev.severity?.includes(severity)
        ? prev.severity.filter(s => s !== severity)
        : [...(prev.severity || []), severity]
    }));
  };

  const clearFilters = () => {
    setFilters({
      timeRange: {
        start: '',
        end: '',
        preset: 'last-24-hours'
      },
      levels: [],
      containers: [],
      searchTerm: '',
      severity: []
    });
  };

  const getLevelColor = (level: string) => {
    switch (level) {
      case 'DEBUG': return 'bg-gray-100 text-gray-700 border-gray-200';
      case 'INFO': return 'bg-blue-100 text-blue-700 border-blue-200';
      case 'WARN': return 'bg-yellow-100 text-yellow-700 border-yellow-200';
      case 'ERROR': return 'bg-red-100 text-red-700 border-red-200';
      case 'FATAL': return 'bg-purple-100 text-purple-700 border-purple-200';
      default: return 'bg-gray-100 text-gray-700 border-gray-200';
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'LOW': return 'bg-green-100 text-green-700 border-green-200';
      case 'MEDIUM': return 'bg-yellow-100 text-yellow-700 border-yellow-200';
      case 'HIGH': return 'bg-orange-100 text-orange-700 border-orange-200';
      case 'CRITICAL': return 'bg-red-100 text-red-700 border-red-200';
      default: return 'bg-gray-100 text-gray-700 border-gray-200';
    }
  };

  return (
    <div className={`bg-white border border-gray-200 rounded-lg shadow-sm ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200">
        <div className="flex items-center space-x-3">
          <Filter className="w-5 h-5 text-gray-600" />
          <h3 className="font-medium text-gray-900">Log Filters</h3>
          {(filters.levels.length > 0 || filters.containers.length > 0 || filters.searchTerm || filters.severity?.length) && (
            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-700">
              {filters.levels.length + filters.containers.length + (filters.searchTerm ? 1 : 0) + (filters.severity?.length || 0)} active
            </span>
          )}
        </div>
        
        <div className="flex items-center space-x-2">
          {onRefresh && (
            <button
              onClick={onRefresh}
              disabled={isLoading}
              className="p-2 text-gray-400 hover:text-gray-600 rounded-md hover:bg-gray-100 transition-colors disabled:opacity-50"
            >
              <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
            </button>
          )}
          
          {onExport && (
            <div className="relative">
              <button
                onClick={() => setShowExportMenu(!showExportMenu)}
                className="inline-flex items-center px-3 py-1.5 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-md transition-colors"
              >
                <Download className="w-4 h-4 mr-1" />
                Export
              </button>
              
              {showExportMenu && (
                <div className="absolute right-0 mt-2 w-32 bg-white border border-gray-200 rounded-md shadow-lg z-10">
                  <button
                    onClick={() => {
                      onExport('csv');
                      setShowExportMenu(false);
                    }}
                    className="block w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 text-left"
                  >
                    Export CSV
                  </button>
                  <button
                    onClick={() => {
                      onExport('json');
                      setShowExportMenu(false);
                    }}
                    className="block w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 text-left"
                  >
                    Export JSON
                  </button>
                </div>
              )}
            </div>
          )}
          
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="p-2 text-gray-400 hover:text-gray-600 rounded-md hover:bg-gray-100 transition-colors"
          >
            <ChevronDown className={`w-4 h-4 transform transition-transform ${isExpanded ? 'rotate-180' : ''}`} />
          </button>
        </div>
      </div>

      {/* Quick Filters */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex flex-wrap items-center gap-3">
          {/* Search */}
          <div className="flex-1 min-w-64">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search logs..."
                value={filters.searchTerm}
                onChange={(e) => setFilters(prev => ({ ...prev, searchTerm: e.target.value }))}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
          </div>

          {/* Time Preset */}
          <select
            value={filters.timeRange.preset || 'custom'}
            onChange={(e) => handleTimePresetChange(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            {timePresets.map(preset => (
              <option key={preset.value} value={preset.value}>
                {preset.label}
              </option>
            ))}
          </select>

          {/* Clear Filters */}
          <button
            onClick={clearFilters}
            className="inline-flex items-center px-3 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-md transition-colors"
          >
            <X className="w-4 h-4 mr-1" />
            Clear
          </button>
        </div>
      </div>

      {/* Expanded Filters */}
      {isExpanded && (
        <div className="p-4 space-y-6">
          {/* Time Range */}
          {filters.timeRange.preset === 'custom' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                <Calendar className="w-4 h-4 inline mr-1" />
                Time Range
              </label>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs text-gray-500 mb-1">Start Time</label>
                  <input
                    type="datetime-local"
                    value={filters.timeRange.start}
                    onChange={(e) => handleTimeRangeChange('start', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-1">End Time</label>
                  <input
                    type="datetime-local"
                    value={filters.timeRange.end}
                    onChange={(e) => handleTimeRangeChange('end', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
              </div>
            </div>
          )}

          {/* Log Levels */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              <AlertCircle className="w-4 h-4 inline mr-1" />
              Log Levels
            </label>
            <div className="flex flex-wrap gap-2">
              {logLevels.map(level => (
                <button
                  key={level}
                  onClick={() => handleLevelToggle(level)}
                  className={`
                    px-3 py-1.5 text-sm font-medium border rounded-md transition-colors
                    ${filters.levels.includes(level) 
                      ? getLevelColor(level) 
                      : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                    }
                  `}
                >
                  {level}
                </button>
              ))}
            </div>
          </div>

          {/* Severity Levels */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              <AlertCircle className="w-4 h-4 inline mr-1" />
              Severity Levels
            </label>
            <div className="flex flex-wrap gap-2">
              {severityLevels.map(severity => (
                <button
                  key={severity}
                  onClick={() => handleSeverityToggle(severity)}
                  className={`
                    px-3 py-1.5 text-sm font-medium border rounded-md transition-colors
                    ${filters.severity?.includes(severity) 
                      ? getSeverityColor(severity) 
                      : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                    }
                  `}
                >
                  {severity}
                </button>
              ))}
            </div>
          </div>

          {/* Containers */}
          {availableContainers.length > 0 && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                <Server className="w-4 h-4 inline mr-1" />
                Containers
              </label>
              <div className="flex flex-wrap gap-2">
                {availableContainers.map(container => (
                  <button
                    key={container}
                    onClick={() => handleContainerToggle(container)}
                    className={`
                      px-3 py-1.5 text-sm font-medium border rounded-md transition-colors
                      ${filters.containers.includes(container) 
                        ? 'bg-blue-100 text-blue-700 border-blue-200' 
                        : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                      }
                    `}
                  >
                    {container}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default LogFilterPanel;