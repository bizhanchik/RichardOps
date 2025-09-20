import { timeUtils } from './timeUtils';

export interface DiskDataPoint {
  timestamp: string;
  cpu_usage: number;
  memory_usage: number;
  disk_usage: number;
  network_rx: number;
  network_tx: number;
  tcp_connections: number;
}

export interface ProcessedDiskData {
  timestamp: Date;
  usage: number;
  formattedTime: string;
}

export class DiskDataService {
  private static instance: DiskDataService;
  private cache: Map<string, ProcessedDiskData[]> = new Map();
  private lastFetch: Map<string, number> = new Map();
  private readonly CACHE_DURATION = 5 * 60 * 1000; // 5 minutes

  static getInstance(): DiskDataService {
    if (!DiskDataService.instance) {
      DiskDataService.instance = new DiskDataService();
    }
    return DiskDataService.instance;
  }

  async loadDiskData(timeRange: string = '1h'): Promise<ProcessedDiskData[]> {
    const now = Date.now();
    const cacheKey = `disk_${timeRange}`;
    
    // Return cached data if it's still fresh for this specific time range
    const cachedData = this.cache.get(cacheKey);
    const lastFetchTime = this.lastFetch.get(cacheKey) || 0;
    
    if (cachedData && (now - lastFetchTime) < this.CACHE_DURATION) {
      console.log('Returning cached disk data:', cachedData.length, 'points for', timeRange);
      return cachedData;
    }

    try {
      console.log(`Fetching Disk data from metrics/range?time_range=${timeRange}`);
      const response = await fetch(`http://159.89.104.120:8000/metrics/range?time_range=${timeRange}`);
      
      if (!response.ok) {
        throw new Error(`Failed to fetch Disk data: ${response.status} ${response.statusText}`);
      }

      const data: DiskDataPoint[] = await response.json();
      console.log('Raw Disk JSON data:', data);
      
      // Calibrate time sync with server data
      timeUtils.calibrateTimeSync(data);
      
      // Process and cache the data for this specific time range
      const processedData = this.processRawData(data);
      this.cache.set(cacheKey, processedData);
      this.lastFetch.set(cacheKey, now);
      
      console.log('Processed disk data:', processedData.length, 'points for', timeRange);
      return processedData;
    } catch (error) {
      console.error('Error loading Disk data:', error);
      
      // Clear cache for this time range on error and rethrow to let component handle
      this.cache.delete(cacheKey);
      this.lastFetch.delete(cacheKey);
      throw error;
    }
  }

  private processRawData(rawData: DiskDataPoint[]): ProcessedDiskData[] {
    return rawData.map(point => ({
      timestamp: timeUtils.parseTimestamp(point.timestamp),
      usage: Math.round(point.disk_usage * 10) / 10, // Round to 1 decimal place
      formattedTime: timeUtils.formatTimestamp(timeUtils.parseTimestamp(point.timestamp))
    }));
  }

  // Get data for different time ranges
  getDataForRange(data: ProcessedDiskData[], hours: number): ProcessedDiskData[] {
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
  calculateStats(data: ProcessedDiskData[]) {
    if (data.length === 0) return null;

    const usageValues = data.map(d => d.usage);
    const min = Math.min(...usageValues);
    const max = Math.max(...usageValues);
    const avg = usageValues.reduce((sum, val) => sum + val, 0) / usageValues.length;
    
    return {
      min: Math.round(min * 10) / 10,
      max: Math.round(max * 10) / 10,
      avg: Math.round(avg * 10) / 10,
      current: usageValues[usageValues.length - 1] || 0
    };
  }

  // Clear cache (useful for testing or forced refresh)
  clearCache(): void {
    this.cache.clear();
    this.lastFetch.clear();
  }
}

export const diskDataService = DiskDataService.getInstance();