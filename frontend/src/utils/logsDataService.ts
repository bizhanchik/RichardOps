/**
 * Logs Data Service
 * 
 * Service for fetching log data from the backend API.
 * Provides methods for searching logs, getting recent logs, and retrieving filter options.
 */

// Types for log-related data structures
export interface LogEntry {
  id: string | number;
  timestamp: string;
  level?: 'ERROR' | 'WARN' | 'INFO' | 'DEBUG';
  message: string;
  container?: string;
  host?: string;
  environment?: string;
  source?: string;
  metadata?: Record<string, any>;
}

export interface LogSearchResponse {
  total: number;
  total_relation: string;
  max_score?: number;
  documents: LogEntry[];
  took: number;
  fallback: boolean;
}

export interface LogFilterOptions {
  containers: string[];
  hosts: string[];
  environments: string[];
  log_levels: string[];
  severities: string[];
}

export interface LogSearchParams {
  query?: string;
  hours?: number;
  level?: string;
  container?: string;
  size?: number;
  from?: number;
}

export interface LogAnalytics {
  total_logs?: number;
  aggregations: Record<string, any>;
}

class LogsDataService {
  private apiUrl: string;

  constructor() {
    this.apiUrl = 'http://159.89.104.120:8000';
  }

  /**
   * Quick search for logs with basic filtering
   */
  async quickSearchLogs(params: LogSearchParams = {}): Promise<LogSearchResponse> {
    try {
      const searchParams = new URLSearchParams();
      
      if (params.query) searchParams.append('q', params.query);
      if (params.hours) searchParams.append('hours', params.hours.toString());
      if (params.level) searchParams.append('level', params.level);
      if (params.container) searchParams.append('container', params.container);
      if (params.size) searchParams.append('size', params.size.toString());

      const response = await fetch(`${this.apiUrl}/api/logs/search/quick?${searchParams}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error fetching logs:', error);
      throw error;
    }
  }

  /**
   * Get recent logs without search query
   */
  async getRecentLogs(count: number = 50, hours: number = 24): Promise<LogSearchResponse> {
    return this.quickSearchLogs({ size: count, hours });
  }

  /**
   * Get recent logs by count using the /logs/recent endpoint
   */
  async getRecentLogsByCount(limit: number = 50): Promise<LogSearchResponse> {
    try {
      const response = await fetch(`${this.apiUrl}/logs/recent?limit=${limit}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const logs = await response.json();
      
      // Convert the direct array response to the expected LogSearchResponse format
      return {
        total: logs.length,
        total_relation: "eq",
        documents: logs,
        took: 0,
        fallback: false
      };
    } catch (error) {
      console.error('Error fetching recent logs:', error);
      throw error;
    }
  }

  /**
   * Search logs with query
   */
  async searchLogs(query: string, params: Omit<LogSearchParams, 'query'> = {}): Promise<LogSearchResponse> {
    return this.quickSearchLogs({ query, ...params });
  }

  /**
   * Get available filter options for dropdowns
   */
  async getFilterOptions(): Promise<LogFilterOptions> {
    try {
      const response = await fetch(`${this.apiUrl}/api/logs/filters`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching filter options:', error);
      // Return default options on error
      return {
        containers: [],
        hosts: [],
        environments: ['production', 'staging', 'development'],
        log_levels: ['ERROR', 'WARN', 'INFO', 'DEBUG'],
        severities: ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']
      };
    }
  }

  /**
   * Get log analytics data
   */
  async getLogAnalytics(hours: number = 24): Promise<LogAnalytics> {
    try {
      const response = await fetch(`${this.apiUrl}/api/logs/analytics/logs?hours=${hours}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching log analytics:', error);
      throw error;
    }
  }

  /**
   * Check if the logs service is available
   */
  async healthCheck(): Promise<{ status: string; available: boolean }> {
    try {
      const response = await fetch(`${this.apiUrl}/api/logs/health`);
      const data = await response.json();
      
      return {
        status: data.status || 'unknown',
        available: response.ok && data.status === 'healthy'
      };
    } catch (error) {
      console.error('Logs service health check failed:', error);
      return {
        status: 'unhealthy',
        available: false
      };
    }
  }

  /**
   * Format log level for display
   */
  static formatLogLevel(level: string): { color: string; icon: string } {
    switch (level.toUpperCase()) {
      case 'ERROR':
        return { color: 'text-red-600 bg-red-50', icon: '❌' };
      case 'WARN':
        return { color: 'text-yellow-600 bg-yellow-50', icon: '⚠️' };
      case 'INFO':
        return { color: 'text-blue-600 bg-blue-50', icon: 'ℹ️' };
      case 'DEBUG':
        return { color: 'text-gray-600 bg-gray-50', icon: '🔍' };
      default:
        return { color: 'text-gray-600 bg-gray-50', icon: '📝' };
    }
  }

  /**
   * Format timestamp for display
   */
  static formatTimestamp(timestamp: string): string {
    try {
      const date = new Date(timestamp);
      return date.toLocaleString();
    } catch (error) {
      return timestamp;
    }
  }

  /**
   * Get time range options for the UI
   */
  static getTimeRangeOptions() {
    return [
      { value: 1, label: '1 Hour' },
      { value: 6, label: '6 Hours' },
      { value: 12, label: '12 Hours' },
      { value: 24, label: '24 Hours' },
      { value: 72, label: '3 Days' },
      { value: 168, label: '1 Week' }
    ];
  }

  /**
   * Get log count options for the UI
   */
  static getLogCountOptions() {
    return [
      { value: 25, label: '25 logs' },
      { value: 50, label: '50 logs' },
      { value: 100, label: '100 logs' },
      { value: 200, label: '200 logs' },
      { value: 500, label: '500 logs' }
    ];
  }
}

// Export singleton instance and class for static methods
export { LogsDataService };
export const logsDataService = new LogsDataService();
export default logsDataService;