import React from 'react';
import { X, Calendar, Clock, Server, Tag, AlertCircle } from 'lucide-react';

interface LogFilters {
  levels: string[];
  containers: string[];
  hosts: string[];
  environments: string[];
  timeRange: {
    start: string;
    end: string;
  };
  searchTerm: string;
}

interface LogFilterPanelProps {
  filters: LogFilters;
  onFiltersChange: (filters: LogFilters) => void;
  onClearFilters: () => void;
  availableContainers: string[];
  availableHosts: string[];
  availableEnvironments: string[];
}

const LOG_LEVELS = [
  { value: 'ERROR', label: 'Error', color: 'bg-red-100 text-red-800 border-red-200' },
  { value: 'WARN', label: 'Warning', color: 'bg-yellow-100 text-yellow-800 border-yellow-200' },
  { value: 'INFO', label: 'Info', color: 'bg-blue-100 text-blue-800 border-blue-200' },
  { value: 'DEBUG', label: 'Debug', color: 'bg-gray-100 text-gray-800 border-gray-200' },
  { value: 'TRACE', label: 'Trace', color: 'bg-purple-100 text-purple-800 border-purple-200' }
];

const LogFilterPanel: React.FC<LogFilterPanelProps> = ({
  filters,
  onFiltersChange,
  onClearFilters,
  availableContainers,
  availableHosts,
  availableEnvironments
}) => {
  const updateFilters = (updates: Partial<LogFilters>) => {
    onFiltersChange({ ...filters, ...updates });
  };

  const toggleLevel = (level: string) => {
    const newLevels = filters.levels.includes(level)
      ? filters.levels.filter(l => l !== level)
      : [...filters.levels, level];
    updateFilters({ levels: newLevels });
  };

  const toggleContainer = (container: string) => {
    const newContainers = filters.containers.includes(container)
      ? filters.containers.filter(c => c !== container)
      : [...filters.containers, container];
    updateFilters({ containers: newContainers });
  };

  const toggleHost = (host: string) => {
    const newHosts = filters.hosts.includes(host)
      ? filters.hosts.filter(h => h !== host)
      : [...filters.hosts, host];
    updateFilters({ hosts: newHosts });
  };

  const toggleEnvironment = (environment: string) => {
    const newEnvironments = filters.environments.includes(environment)
      ? filters.environments.filter(e => e !== environment)
      : [...filters.environments, environment];
    updateFilters({ environments: newEnvironments });
  };

  const hasActiveFilters = filters.levels.length > 0 || 
                          filters.containers.length > 0 || 
                          filters.hosts.length > 0 || 
                          filters.environments.length > 0 || 
                          filters.timeRange.start || 
                          filters.searchTerm;

  return (
    <div className="p-3 sm:p-4 space-y-3 sm:space-y-4">
      {/* Search */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center space-y-2 sm:space-y-0 sm:space-x-4">
        <div className="flex-1 w-full">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Search Logs
          </label>
          <input
            type="text"
            value={filters.searchTerm}
            onChange={(e) => updateFilters({ searchTerm: e.target.value })}
            placeholder="Search in log messages..."
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
          />
        </div>
        {hasActiveFilters && (
          <button
            onClick={onClearFilters}
            className="inline-flex items-center px-3 py-2 text-xs sm:text-sm font-medium text-red-700 bg-red-100 hover:bg-red-200 rounded-md transition-colors flex-shrink-0"
          >
            <X className="w-4 h-4 mr-1" />
            Clear All
          </button>
        )}
      </div>

      {/* Time Range */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            <Calendar className="w-4 h-4 inline mr-1" />
            Start Time
          </label>
          <input
            type="datetime-local"
            value={filters.timeRange.start}
            onChange={(e) => updateFilters({ 
              timeRange: { ...filters.timeRange, start: e.target.value }
            })}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            <Clock className="w-4 h-4 inline mr-1" />
            End Time
          </label>
          <input
            type="datetime-local"
            value={filters.timeRange.end}
            onChange={(e) => updateFilters({ 
              timeRange: { ...filters.timeRange, end: e.target.value }
            })}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
          />
        </div>
      </div>

      {/* Log Levels */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          <AlertCircle className="w-4 h-4 inline mr-1" />
          Log Levels
        </label>
        <div className="flex flex-wrap gap-1 sm:gap-2">
          {LOG_LEVELS.map((level) => (
            <button
              key={level.value}
              onClick={() => toggleLevel(level.value)}
              className={`px-2 sm:px-3 py-1 text-xs sm:text-sm font-medium border rounded-full transition-all ${
                filters.levels.includes(level.value)
                  ? level.color + ' ring-2 ring-offset-1 ring-blue-500'
                  : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
              }`}
            >
              {level.label}
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
          <div className="flex flex-wrap gap-1 sm:gap-2">
            {availableContainers.map((container) => (
              <button
                key={container}
                onClick={() => toggleContainer(container)}
                className={`px-2 sm:px-3 py-1 text-xs sm:text-sm font-medium border rounded-full transition-all ${
                  filters.containers.includes(container)
                    ? 'bg-green-100 text-green-800 border-green-200 ring-2 ring-offset-1 ring-green-500'
                    : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                }`}
              >
                {container}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Hosts */}
      {availableHosts.length > 0 && (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            <Server className="w-4 h-4 inline mr-1" />
            Hosts
          </label>
          <div className="flex flex-wrap gap-1 sm:gap-2">
            {availableHosts.map((host) => (
              <button
                key={host}
                onClick={() => toggleHost(host)}
                className={`px-2 sm:px-3 py-1 text-xs sm:text-sm font-medium border rounded-full transition-all ${
                  filters.hosts.includes(host)
                    ? 'bg-purple-100 text-purple-800 border-purple-200 ring-2 ring-offset-1 ring-purple-500'
                    : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                }`}
              >
                {host}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Environments */}
      {availableEnvironments.length > 0 && (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            <Tag className="w-4 h-4 inline mr-1" />
            Environments
          </label>
          <div className="flex flex-wrap gap-1 sm:gap-2">
            {availableEnvironments.map((environment) => (
              <button
                key={environment}
                onClick={() => toggleEnvironment(environment)}
                className={`px-2 sm:px-3 py-1 text-xs sm:text-sm font-medium border rounded-full transition-all ${
                  filters.environments.includes(environment)
                    ? 'bg-orange-100 text-orange-800 border-orange-200 ring-2 ring-offset-1 ring-orange-500'
                    : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                }`}
              >
                {environment}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Active Filters Summary */}
      {hasActiveFilters && (
        <div className="pt-2 border-t border-gray-200">
          <div className="text-xs sm:text-sm text-gray-600 space-y-1">
            <div className="font-medium">Active filters:</div>
            <div className="flex flex-wrap gap-1 text-xs">
              {filters.levels.length > 0 && (
                <span className="bg-gray-100 px-2 py-1 rounded">Levels: {filters.levels.join(', ')}</span>
              )}
              {filters.containers.length > 0 && (
                <span className="bg-gray-100 px-2 py-1 rounded">Containers: {filters.containers.join(', ')}</span>
              )}
              {filters.hosts.length > 0 && (
                <span className="bg-gray-100 px-2 py-1 rounded">Hosts: {filters.hosts.join(', ')}</span>
              )}
              {filters.environments.length > 0 && (
                <span className="bg-gray-100 px-2 py-1 rounded">Environments: {filters.environments.join(', ')}</span>
              )}
              {filters.timeRange.start && (
                <span className="bg-gray-100 px-2 py-1 rounded">Time range applied</span>
              )}
              {filters.searchTerm && (
                <span className="bg-gray-100 px-2 py-1 rounded">Search: "{filters.searchTerm}"</span>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default LogFilterPanel;