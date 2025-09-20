export interface NetworkDataPoint {
  timestamp: string;
  usage: number;
}

export interface NetworkMetricsResponse {
  metadata: {
    generated: string;
    server: string;
    metric: string;
    interval: string;
    total_points: number;
  };
  data: NetworkDataPoint[];
}

export interface ProcessedNetworkData {
  timestamp: Date;
  usage: number; // bytes/sec
  formattedTime: string;
  formattedUsage: string; // formatted bytes/sec
}

export class NetworkDataService {
  private static instance: NetworkDataService;
  private rxCache: ProcessedNetworkData[] | null = null;
  private txCache: ProcessedNetworkData[] | null = null;
  private lastFetch: number = 0;
  private readonly CACHE_DURATION = 5 * 60 * 1000; // 5 minutes

  static getInstance(): NetworkDataService {
    if (!NetworkDataService.instance) {
      NetworkDataService.instance = new NetworkDataService();
    }
    return NetworkDataService.instance;
  }

  async loadNetworkData(type: 'rx' | 'tx'): Promise<ProcessedNetworkData[]> {
    const now = Date.now();
    const cache = type === 'rx' ? this.rxCache : this.txCache;
    
    // Return cached data if it's still fresh
    if (cache && (now - this.lastFetch) < this.CACHE_DURATION) {
      console.log(`Returning cached ${type} network data:`, cache.length, 'points');
      return cache;
    }

    try {
      console.log(`Fetching ${type.toUpperCase()} network data from /data/cpu-metrics.json (temporary)`);
      const response = await fetch('/data/cpu-metrics.json');
      
      if (!response.ok) {
        throw new Error(`Failed to fetch ${type.toUpperCase()} network data: ${response.status} ${response.statusText}`);
      }

      const data: NetworkMetricsResponse = await response.json();
      console.log(`Raw ${type.toUpperCase()} network JSON data:`, data);
      
      // Process and cache the data - simulate network usage pattern
      const processedData = this.processRawData(data.data, type);
      
      if (type === 'rx') {
        this.rxCache = processedData;
      } else {
        this.txCache = processedData;
      }
      
      this.lastFetch = now;
      
      console.log(`Processed ${type} network data:`, processedData.length, 'points');
      return processedData;
    } catch (error) {
      console.error(`Error loading ${type.toUpperCase()} network data:`, error);
      
      // Return fallback data if fetch fails
      console.log(`Using fallback ${type} network data`);
      return this.generateFallbackData(type);
    }
  }

  private processRawData(rawData: NetworkDataPoint[], type: 'rx' | 'tx'): ProcessedNetworkData[] {
    return rawData.map((point, index) => {
      // Simulate network usage in bytes/sec
      let simulatedUsage: number;
      
      if (type === 'rx') {
        // RX typically lower than TX, around 10KB-50KB/sec
        simulatedUsage = Math.max(5000, Math.min(80000, point.usage * 800 + 15000 + Math.sin(index * 0.2) * 8000));
      } else {
        // TX typically higher than RX, around 20KB-80KB/sec
        simulatedUsage = Math.max(10000, Math.min(120000, point.usage * 1200 + 25000 + Math.cos(index * 0.15) * 12000));
      }
      
      return {
        timestamp: new Date(point.timestamp),
        usage: Math.round(simulatedUsage),
        formattedTime: this.formatTimestamp(new Date(point.timestamp)),
        formattedUsage: this.formatBytes(simulatedUsage)
      };
    });
  }

  private formatBytes(bytes: number): string {
    if (bytes === 0) return '0 bytes/sec';
    
    const k = 1024;
    const sizes = ['bytes/sec', 'KB/sec', 'MB/sec', 'GB/sec'];
    
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    const value = bytes / Math.pow(k, i);
    
    return `${Math.round(value * 100) / 100} ${sizes[i]}`;
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

  private generateFallbackData(type: 'rx' | 'tx'): ProcessedNetworkData[] {
    const fallbackData: ProcessedNetworkData[] = [];
    const now = new Date();
    
    // Generate 12 hours of fallback data
    for (let i = 0; i < 12; i++) {
      const timestamp = new Date(now.getTime() - (i * 60 * 60 * 1000));
      
      let usage: number;
      if (type === 'rx') {
        usage = Math.random() * 40000 + 10000; // 10KB-50KB/sec
      } else {
        usage = Math.random() * 60000 + 20000; // 20KB-80KB/sec
      }
      
      fallbackData.unshift({
        timestamp,
        usage: Math.round(usage),
        formattedTime: this.formatTimestamp(timestamp),
        formattedUsage: this.formatBytes(usage)
      });
    }
    
    return fallbackData;
  }

  // Get data for different time ranges
  getDataForRange(data: ProcessedNetworkData[], hours: number): ProcessedNetworkData[] {
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
    this.rxCache = null;
    this.txCache = null;
    this.lastFetch = 0;
  }
}

export const networkDataService = NetworkDataService.getInstance();