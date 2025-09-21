import { timeUtils } from './timeUtils';

export interface CPUDataPoint {
  timestamp: string;
  cpu_usage: number;
  memory_usage: number;
  disk_usage: number;
  network_rx: number;
  network_tx: number;
  tcp_connections: number;
}

export interface ProcessedCPUData {
  timestamp: Date;
  usage: number;
  formattedTime: string;
}

export class CPUDataService {
  private static instance: CPUDataService;
  private cache: Map<string, ProcessedCPUData[]> = new Map();
  private lastFetch: Map<string, number> = new Map();
  private readonly CACHE_DURATION = 10 * 1000; // 10 seconds for real-time updates

  static getInstance(): CPUDataService {
    if (!CPUDataService.instance) {
      CPUDataService.instance = new CPUDataService();
    }
    return CPUDataService.instance;
  }

  async loadCPUData(timeRange: '1h' | '6h' | '12h' = '12h'): Promise<ProcessedCPUData[]> {
    const cacheKey = `cpu-${timeRange}`;
    const now = Date.now();
    
    // Check if we have cached data that's still fresh
    const cachedData = this.cache.get(cacheKey);
    const lastFetchTime = this.lastFetch.get(cacheKey) || 0;
    
    if (cachedData && (now - lastFetchTime) < this.CACHE_DURATION) {
      console.log('Using cached CPU data for', timeRange);
      return cachedData;
    }

    try {
      console.log('Fetching fresh CPU data from API');
      const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/metrics/range?period=${timeRange}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      console.log('Raw CPU API response:', data);

      // Process the data - API returns array directly, not wrapped in {data: [...]}
      const processedData = this.processRawData(data);

      // Cache the processed data
      this.cache.set(cacheKey, processedData);
      this.lastFetch.set(cacheKey, now);

      console.log('Processed CPU data:', processedData.length, 'points for', timeRange);
      return processedData;
    } catch (error) {
      console.error('Error loading CPU data:', error);
      throw error;
    }
  }

  private processRawData(rawData: CPUDataPoint[]): ProcessedCPUData[] {
    return rawData.map(point => ({
      timestamp: timeUtils.parseTimestamp(point.timestamp),
      usage: Math.round(point.cpu_usage * 10) / 10, // Round to 1 decimal place
      formattedTime: timeUtils.formatChartTimestamp(timeUtils.parseTimestamp(point.timestamp))
    }));
  }

  // Get data for different time ranges
  getDataForRange(data: ProcessedCPUData[], hours: number): ProcessedCPUData[] {
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
  calculateStats(data: ProcessedCPUData[]) {
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

export const cpuDataService = CPUDataService.getInstance();