export interface TCPDataPoint {
  timestamp: string;
  usage: number;
}

export interface TCPMetricsResponse {
  metadata: {
    generated: string;
    server: string;
    metric: string;
    interval: string;
    total_points: number;
  };
  data: TCPDataPoint[];
}

export interface ProcessedTCPData {
  timestamp: Date;
  usage: number; // connection count
  formattedTime: string;
}

export class TCPDataService {
  private static instance: TCPDataService;
  private cache: ProcessedTCPData[] | null = null;
  private lastFetch: number = 0;
  private readonly CACHE_DURATION = 5 * 60 * 1000; // 5 minutes

  static getInstance(): TCPDataService {
    if (!TCPDataService.instance) {
      TCPDataService.instance = new TCPDataService();
    }
    return TCPDataService.instance;
  }

  async loadTCPData(): Promise<ProcessedTCPData[]> {
    const now = Date.now();
    
    // Return cached data if it's still fresh
    if (this.cache && (now - this.lastFetch) < this.CACHE_DURATION) {
      console.log('Returning cached TCP data:', this.cache.length, 'points');
      return this.cache;
    }

    try {
      console.log('Fetching TCP data from /data/cpu-metrics.json (temporary)');
      const response = await fetch('/data/cpu-metrics.json');
      
      if (!response.ok) {
        throw new Error(`Failed to fetch TCP data: ${response.status} ${response.statusText}`);
      }

      const data: TCPMetricsResponse = await response.json();
      console.log('Raw TCP JSON data:', data);
      
      // Process and cache the data - simulate TCP connections pattern
      this.cache = this.processRawData(data.data);
      this.lastFetch = now;
      
      console.log('Processed TCP data:', this.cache.length, 'points');
      return this.cache;
    } catch (error) {
      console.error('Error loading TCP data:', error);
      
      // Return fallback data if fetch fails
      console.log('Using fallback TCP data');
      return this.generateFallbackData();
    }
  }

  private processRawData(rawData: TCPDataPoint[]): ProcessedTCPData[] {
    return rawData.map((point, index) => {
      // Simulate TCP connections - typically 50-150 connections
      const simulatedUsage = Math.max(30, Math.min(200, point.usage * 3 + 60 + Math.sin(index * 0.3) * 20));
      
      return {
        timestamp: new Date(point.timestamp),
        usage: Math.round(simulatedUsage), // TCP connections are whole numbers
        formattedTime: this.formatTimestamp(new Date(point.timestamp))
      };
    });
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

  private generateFallbackData(): ProcessedTCPData[] {
    const fallbackData: ProcessedTCPData[] = [];
    const now = new Date();
    
    // Generate 12 hours of fallback data
    for (let i = 0; i < 12; i++) {
      const timestamp = new Date(now.getTime() - (i * 60 * 60 * 1000));
      const usage = Math.round(Math.random() * 100 + 50); // 50-150 connections
      
      fallbackData.unshift({
        timestamp,
        usage,
        formattedTime: this.formatTimestamp(timestamp)
      });
    }
    
    return fallbackData;
  }

  // Get data for different time ranges
  getDataForRange(data: ProcessedTCPData[], hours: number): ProcessedTCPData[] {
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
    this.cache = null;
    this.lastFetch = 0;
  }
}

export const tcpDataService = TCPDataService.getInstance();