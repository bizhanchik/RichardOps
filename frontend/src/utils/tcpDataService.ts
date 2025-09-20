import { timeUtils } from './timeUtils';

export interface TCPDataPoint {
  timestamp: string;
  cpu_usage: number;
  memory_usage: number;
  disk_usage: number;
  network_rx: number;
  network_tx: number;
  tcp_connections: number;
}

export interface ProcessedTCPData {
  timestamp: Date;
  usage: number; // connection count
  formattedTime: string;
}

export class TCPDataService {
  private static instance: TCPDataService;
  private cache: Map<string, ProcessedTCPData[]> = new Map();
  private lastFetch: Map<string, number> = new Map();
  private readonly CACHE_DURATION = 5 * 60 * 1000; // 5 minutes

  static getInstance(): TCPDataService {
    if (!TCPDataService.instance) {
      TCPDataService.instance = new TCPDataService();
    }
    return TCPDataService.instance;
  }

  async loadTCPData(timeRange: '1h' | '6h' | '12h' = '12h'): Promise<ProcessedTCPData[]> {
    const now = Date.now();
    const cacheKey = `tcp_${timeRange}`;
    
    // Return cached data if it's still fresh for this specific time range
    const cachedData = this.cache.get(cacheKey);
    const lastFetchTime = this.lastFetch.get(cacheKey) || 0;
    
    if (cachedData && (now - lastFetchTime) < this.CACHE_DURATION) {
      console.log('Returning cached TCP data:', cachedData.length, 'points for', timeRange);
      return cachedData;
    }

    try {
      console.log('Fetching TCP data from API');
      const response = await fetch(`http://159.89.104.120:8000/metrics/range?time_range=${timeRange}`);
      
      if (!response.ok) {
        throw new Error(`Failed to fetch TCP data: ${response.status} ${response.statusText}`);
      }

      const data: TCPDataPoint[] = await response.json();
      console.log('Raw TCP API data:', data);
      
      // Calibrate time sync with server data
      timeUtils.calibrateTimeSync(data);
      
      // Process and cache the data for this specific time range
      const processedData = this.processRawData(data);
      this.cache.set(cacheKey, processedData);
      this.lastFetch.set(cacheKey, now);
      
      console.log('Processed TCP data:', processedData.length, 'points for', timeRange);
      return processedData;
    } catch (error) {
      console.error('Error loading TCP data:', error);
      
      // Clear cache for this time range on error and rethrow to let component handle
      this.cache.delete(cacheKey);
      this.lastFetch.delete(cacheKey);
      throw error;
    }
  }

  private processRawData(rawData: TCPDataPoint[]): ProcessedTCPData[] {
    return rawData.map(point => {
      const timestamp = timeUtils.parseTimestamp(point.timestamp);
      return {
        timestamp,
        usage: Math.round(point.tcp_connections), // TCP connections are whole numbers
        formattedTime: timeUtils.formatTimestamp(timestamp)
      };
    });
  }

  // Get data for different time ranges
  getDataForRange(data: ProcessedTCPData[], hours: number): ProcessedTCPData[] {
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
  calculateStats(data: ProcessedTCPData[]) {
    if (data.length === 0) return null;

    const usageValues = data.map(d => d.usage);
    const min = Math.min(...usageValues);
    const max = Math.max(...usageValues);
    const avg = usageValues.reduce((sum, val) => sum + val, 0) / usageValues.length;
    
    return {
      min: Math.round(min),
      max: Math.round(max),
      avg: Math.round(avg),
      current: usageValues[usageValues.length - 1] || 0
    };
  }

  // Clear cache (useful for testing or forced refresh)
  clearCache(): void {
    this.cache.clear();
    this.lastFetch.clear();
  }
}

export const tcpDataService = TCPDataService.getInstance();