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
  private readonly CACHE_DURATION = 5 * 60 * 1000; // 5 minutes

  static getInstance(): NetworkDataService {
    if (!NetworkDataService.instance) {
      NetworkDataService.instance = new NetworkDataService();
    }
    return NetworkDataService.instance;
  }

  async loadNetworkData(type: 'rx' | 'tx', timeRange: '1h' | '6h' | '12h' = '12h'): Promise<ProcessedNetworkData[]> {
    const now = Date.now();
    const cacheKey = `${type}_${timeRange}`;
    const cache = type === 'rx' ? this.rxCache : this.txCache;
    
    // Return cached data if it's still fresh for this specific time range
    const cachedData = cache.get(cacheKey);
    const lastFetchTime = this.lastFetch.get(cacheKey) || 0;
    
    if (cachedData && (now - lastFetchTime) < this.CACHE_DURATION) {
      console.log(`Returning cached ${type} network data:`, cachedData.length, 'points for', timeRange);
      return cachedData;
    }

    try {
      console.log(`Fetching ${type.toUpperCase()} network data from API`);
      const response = await fetch(`http://159.89.104.120:8000/metrics/range?time_range=${timeRange}`);
      
      if (!response.ok) {
        throw new Error(`Failed to fetch ${type.toUpperCase()} network data: ${response.status} ${response.statusText}`);
      }

      const data: NetworkDataPoint[] = await response.json();
      console.log(`Raw ${type.toUpperCase()} network API data:`, data);
      
      // Calibrate time sync with server data
      timeUtils.calibrateTimeSync(data);
      
      // Process and cache the data for this specific time range
      const processedData = this.processRawData(data, type);
      
      if (type === 'rx') {
        this.rxCache.set(cacheKey, processedData);
      } else {
        this.txCache.set(cacheKey, processedData);
      }
      
      this.lastFetch.set(cacheKey, now);
      
      console.log(`Processed ${type} network data:`, processedData.length, 'points for', timeRange);
      return processedData;
    } catch (error) {
      console.error(`Error loading ${type.toUpperCase()} network data:`, error);
      
      // Clear cache for this time range on error and rethrow to let component handle
      if (type === 'rx') {
        this.rxCache.delete(cacheKey);
      } else {
        this.txCache.delete(cacheKey);
      }
      this.lastFetch.delete(cacheKey);
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
        formattedTime: timeUtils.formatTimestamp(timestamp),
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

  // Clear cache (useful for testing or forced refresh)
  clearCache(): void {
    this.rxCache.clear();
    this.txCache.clear();
    this.lastFetch.clear();
  }
}

export const networkDataService = NetworkDataService.getInstance();