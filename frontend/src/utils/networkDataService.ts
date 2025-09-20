import { timeUtils } from './timeUtils';

export interface NetworkDataPoint {
  timestamp: string;
  cpu_usage: number;
  memory_usage: number;
  disk_usage: number;
  network_rx: number;
  network_tx: number;
  tcp_connections: number;
}

export interface ProcessedNetworkData {
  timestamp: Date;
  usage: number; // bytes/sec
  formattedTime: string;
  formattedUsage: string; // formatted bytes/sec
}

export class NetworkDataService {
  private static instance: NetworkDataService;
  private rxCache: Map<string, ProcessedNetworkData[]> = new Map();
  private txCache: Map<string, ProcessedNetworkData[]> = new Map();
  private lastFetch: Map<string, number> = new Map();
  private readonly CACHE_DURATION = 10 * 1000; // 10 seconds for real-time updates

  static getInstance(): NetworkDataService {
    if (!NetworkDataService.instance) {
      NetworkDataService.instance = new NetworkDataService();
    }
    return NetworkDataService.instance;
  }

  async loadNetworkData(type: 'rx' | 'tx', timeRange: '1h' | '6h' | '12h' = '12h'): Promise<ProcessedNetworkData[]> {
    try {
      console.log(`Fetching fresh ${type} network data from API`);
      const response = await fetch(`http://159.89.104.120:8000/metrics/range?period=${timeRange}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      console.log(`Raw ${type} network API response:`, data);

      // Process the data - API returns array directly, not wrapped in {data: [...]}
      const processedData = this.processRawData(data, type);

      console.log(`Processed ${type} network data:`, processedData.length, 'points for', timeRange);
      return processedData;
    } catch (error) {
      console.error(`Error loading ${type} network data:`, error);
      throw error;
    }
  }

  private processRawData(rawData: NetworkDataPoint[], type: 'rx' | 'tx'): ProcessedNetworkData[] {
    return rawData.map(point => {
      const rawUsage = type === 'rx' ? point.network_rx : point.network_tx;
      // Handle invalid values from API
      const usage = (rawUsage === null || rawUsage === undefined || isNaN(rawUsage)) ? 0 : rawUsage;
      const timestamp = timeUtils.parseTimestamp(point.timestamp);
      
      return {
        timestamp,
        usage: Math.round(usage),
        formattedTime: timeUtils.formatChartTimestamp(timestamp),
        formattedUsage: this.formatBytes(usage)
      };
    });
  }

  private formatBytes(bytes: number): string {
    // Handle invalid values
    if (isNaN(bytes) || bytes === undefined || bytes === null || bytes < 0) {
      return '0 bytes/sec';
    }
    
    if (bytes === 0) return '0 bytes/sec';
    
    const k = 1024;
    const sizes = ['bytes/sec', 'KB/sec', 'MB/sec', 'GB/sec'];
    
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    const value = bytes / Math.pow(k, i);
    
    return `${Math.round(value * 100) / 100} ${sizes[i]}`;
  }

  // Get data for different time ranges
  getDataForRange(data: ProcessedNetworkData[], hours: number): ProcessedNetworkData[] {
    if (data.length === 0) return data;
    
    // Use server-synchronized time range
    const { start } = timeUtils.getTimeRange(hours);
    const filtered = data.filter(point => point.timestamp >= start);
    
    // If no data matches the filter, return the most recent points available
    if (filtered.length === 0) {
      const pointsToShow = Math.min(Math.max(1, Math.ceil(hours)), data.length);
      return data.slice(-pointsToShow);
    }
    
    return filtered;
  }

  // Calculate statistics
  calculateStats(data: ProcessedNetworkData[]) {
    if (data.length === 0) return null;

    const usageValues = data.map(d => d.usage);
    const min = Math.min(...usageValues);
    const max = Math.max(...usageValues);
    const avg = usageValues.reduce((sum, val) => sum + val, 0) / usageValues.length;
    
    return {
      min: this.formatBytes(min),
      max: this.formatBytes(max),
      avg: this.formatBytes(avg),
      current: usageValues[usageValues.length - 1] || 0,
      currentFormatted: this.formatBytes(usageValues[usageValues.length - 1] || 0)
    };
  }

  // Clear cache (no-op since caching is disabled)
  clearCache(): void {
    // No cache to clear - always fetching fresh data
  }
}

export const networkDataService = NetworkDataService.getInstance();