import { timeUtils } from './timeUtils';

export interface MemoryDataPoint {
  timestamp: string;
  cpu_usage: number;
  memory_usage: number;
  disk_usage: number;
  network_rx: number;
  network_tx: number;
  tcp_connections: number;
}

export interface ProcessedMemoryData {
  timestamp: Date;
  usage: number;
  formattedTime: string;
}

export class MemoryDataService {
  private static instance: MemoryDataService;
  private cache: Map<string, ProcessedMemoryData[]> = new Map();
  private lastFetch: Map<string, number> = new Map();
  private readonly CACHE_DURATION = 10 * 1000; // 10 seconds for real-time updates

  static getInstance(): MemoryDataService {
    if (!MemoryDataService.instance) {
      MemoryDataService.instance = new MemoryDataService();
    }
    return MemoryDataService.instance;
  }

  async loadMemoryData(timeRange: '1h' | '6h' | '12h' = '12h'): Promise<ProcessedMemoryData[]> {
    const cacheKey = `memory-${timeRange}`;
    const now = Date.now();
    
    // Check if we have cached data that's still fresh
    const cachedData = this.cache.get(cacheKey);
    const lastFetchTime = this.lastFetch.get(cacheKey) || 0;
    
    if (cachedData && (now - lastFetchTime) < this.CACHE_DURATION) {
      console.log('Using cached memory data for', timeRange);
      return cachedData;
    }

    try {
      console.log('Fetching fresh memory data from API');
      const response = await fetch(`http://159.89.104.120:8000/metrics/range?period=${timeRange}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      console.log('Raw memory API response:', data);

      // Process the data - API returns array directly, not wrapped in {data: [...]}
      const processedData = this.processRawData(data);

      // Cache the processed data
      this.cache.set(cacheKey, processedData);
      this.lastFetch.set(cacheKey, now);

      console.log('Processed memory data:', processedData.length, 'points for', timeRange);
      return processedData;
    } catch (error) {
      console.error('Error loading memory data:', error);
      throw error;
    }
  }

  private processRawData(rawData: MemoryDataPoint[]): ProcessedMemoryData[] {
    return rawData.map(point => ({
      timestamp: timeUtils.parseTimestamp(point.timestamp),
      usage: Math.round(point.memory_usage * 10) / 10, // Round to 1 decimal place
      formattedTime: timeUtils.formatChartTimestamp(timeUtils.parseTimestamp(point.timestamp))
    }));
  }

  // Get data for different time ranges
  getDataForRange(data: ProcessedMemoryData[], hours: number): ProcessedMemoryData[] {
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
  calculateStats(data: ProcessedMemoryData[]) {
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

  // Clear cache (no-op since caching is disabled)
  clearCache(): void {
    // No cache to clear - always fetching fresh data
  }
}

export const memoryDataService = MemoryDataService.getInstance();