export interface CPUDataPoint {
  timestamp: string;
  usage: number;
}

export interface CPUMetricsResponse {
  metadata: {
    generated: string;
    server: string;
    metric: string;
    interval: string;
    total_points: number;
  };
  data: CPUDataPoint[];
}

export interface ProcessedCPUData {
  timestamp: Date;
  usage: number;
  formattedTime: string;
}

export class CPUDataService {
  private static instance: CPUDataService;
  private cache: ProcessedCPUData[] | null = null;
  private lastFetch: number = 0;
  private readonly CACHE_DURATION = 5 * 60 * 1000; // 5 minutes

  static getInstance(): CPUDataService {
    if (!CPUDataService.instance) {
      CPUDataService.instance = new CPUDataService();
    }
    return CPUDataService.instance;
  }

  async loadCPUData(): Promise<ProcessedCPUData[]> {
    const now = Date.now();
    
    // Return cached data if it's still fresh
    if (this.cache && (now - this.lastFetch) < this.CACHE_DURATION) {
      console.log('Returning cached data:', this.cache.length, 'points');
      return this.cache;
    }

    try {
      console.log('Fetching CPU data from /data/cpu-metrics.json');
      const response = await fetch('/data/cpu-metrics.json');
      
      if (!response.ok) {
        throw new Error(`Failed to fetch CPU data: ${response.status} ${response.statusText}`);
      }

      const data: CPUMetricsResponse = await response.json();
      console.log('Raw JSON data:', data);
      
      // Process and cache the data
      this.cache = this.processRawData(data.data);
      this.lastFetch = now;
      
      console.log('Processed data:', this.cache.length, 'points');
      return this.cache;
    } catch (error) {
      console.error('Error loading CPU data:', error);
      
      // Return fallback data if fetch fails
      console.log('Using fallback data');
      return this.generateFallbackData();
    }
  }

  private processRawData(rawData: CPUDataPoint[]): ProcessedCPUData[] {
    return rawData.map(point => ({
      timestamp: new Date(point.timestamp),
      usage: Math.round(point.usage * 10) / 10, // Round to 1 decimal place
      formattedTime: this.formatTimestamp(new Date(point.timestamp))
    }));
  }

  private formatTimestamp(date: Date): string {
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffHours / 24);

    if (diffDays === 0) {
      return date.toLocaleTimeString('en-US', { 
        hour: '2-digit', 
        minute: '2-digit',
        hour12: false 
      });
    } else if (diffDays < 7) {
      return `${diffDays}d ago`;
    } else {
      return date.toLocaleDateString('en-US', { 
        month: 'short', 
        day: 'numeric' 
      });
    }
  }

  private generateFallbackData(): ProcessedCPUData[] {
    const fallbackData: ProcessedCPUData[] = [];
    const now = new Date();
    
    // Generate 24 hours of fallback data
    for (let i = 0; i < 24; i++) {
      const timestamp = new Date(now.getTime() - (i * 60 * 60 * 1000));
      const usage = Math.random() * 80 + 10; // 10-90% usage
      
      fallbackData.unshift({
        timestamp,
        usage: Math.round(usage * 10) / 10,
        formattedTime: this.formatTimestamp(timestamp)
      });
    }
    
    return fallbackData;
  }

  // Get data for different time ranges
  getDataForRange(data: ProcessedCPUData[], hours: number): ProcessedCPUData[] {
    if (data.length === 0) return data;
    
    // Instead of using current time, use the latest data point as reference
    const latestDataPoint = data[data.length - 1];
    const cutoff = new Date(latestDataPoint.timestamp.getTime() - (hours * 60 * 60 * 1000));
    
    const filtered = data.filter(point => point.timestamp >= cutoff);
    
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

  // Clear cache (useful for testing or forced refresh)
  clearCache(): void {
    this.cache = null;
    this.lastFetch = 0;
  }
}

export const cpuDataService = CPUDataService.getInstance();