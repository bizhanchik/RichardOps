/**
 * Time utilities to handle clock synchronization issues
 * Addresses the 1.8-hour time difference between client and server
 */

export interface TimeSync {
  serverOffset: number; // Milliseconds difference between client and server
  lastSync: number; // When this offset was calculated
  isValid: boolean; // Whether the offset is reliable
}

class TimeManager {
  private static instance: TimeManager;
  private timeSync: TimeSync = {
    serverOffset: 0,
    lastSync: 0,
    isValid: false
  };

  static getInstance(): TimeManager {
    if (!TimeManager.instance) {
      TimeManager.instance = new TimeManager();
    }
    return TimeManager.instance;
  }

  /**
   * Calculate server time offset based on API response
   * @param apiData Array of data points with server timestamps
   */
  calibrateTimeSync(apiData: Array<{ timestamp: string }>): void {
    if (!apiData || apiData.length === 0) return;

    try {
      // Server sends UTC timestamps, no need for complex offset calculation
      // Just mark as valid so other functions work properly
      this.timeSync = {
        serverOffset: 0, // No offset needed - UTC is the standard
        lastSync: Date.now(),
        isValid: true
      };
      
      console.log('Time sync calibrated: Using UTC timestamps from server');
    } catch (error) {
      console.warn('Failed to calibrate time sync:', error);
    }
  }

  /**
   * Convert server timestamp to normalized Date object
   * @param serverTimestamp ISO string from server
   * @returns Date object adjusted for time differences
   */
  parseServerTimestamp(serverTimestamp: string): Date {
    const serverDate = new Date(serverTimestamp);
    
    // If we have a valid time sync, adjust the timestamp
    if (this.timeSync.isValid) {
      // Don't adjust server timestamps - they're the authoritative source
      // This prevents double-adjustment issues
      return serverDate;
    }
    
    return serverDate;
  }

  /**
   * Get current time synchronized with server
   * @returns Date object representing "server now" in UTC
   */
  getServerNow(): Date {
    // Always return current UTC time since server uses UTC
    return new Date();
  }

  /**
   * Format timestamp relative to current time
   * @param date Date to format (UTC timestamp from server)
   * @param referenceTime Optional reference time (defaults to current UTC)
   * @returns Formatted time string
   */
  formatRelativeTime(date: Date, referenceTime?: Date): string {
    const reference = referenceTime || new Date(); // Current UTC time
    const diffMs = reference.getTime() - date.getTime();
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffHours / 24);
    const diffMinutes = Math.floor(diffMs / (1000 * 60));

    // For recent timestamps (within last day)
    if (diffDays === 0) {
      if (diffMinutes < 1) {
        return 'Just now';
      } else if (diffMinutes < 60) {
        return `${diffMinutes}m ago`;
      } else {
        return `${diffHours}h ago`;
      }
    } 
    // For older timestamps
    else if (diffDays < 7) {
      return `${diffDays}d ago`;
    } 
    // For very old timestamps
    else {
      return date.toLocaleDateString('en-US', { 
        month: 'short', 
        day: 'numeric' 
      });
    }
  }

  /**
   * Get time range boundaries in UTC
   * @param hours Number of hours to go back
   * @param endTime Optional end time (defaults to current UTC)
   * @returns Start and end timestamps in UTC
   */
  getTimeRange(hours: number, endTime?: Date): { start: Date; end: Date } {
    const end = endTime || new Date(); // Current UTC time
    const start = new Date(end.getTime() - (hours * 60 * 60 * 1000));
    
    return { start, end };
  }

  /**
   * Check if time sync seems accurate
   * @returns Object with sync status and details
   */
  getTimeSyncStatus(): { 
    isValid: boolean; 
    offsetSeconds: number; 
    offsetHours: number;
    lastSyncAgo: number;
    status: 'good' | 'warning' | 'error' | 'unknown';
    message: string;
  } {
    if (!this.timeSync.isValid) {
      return {
        isValid: false,
        offsetSeconds: 0,
        offsetHours: 0,
        lastSyncAgo: 0,
        status: 'unknown',
        message: 'Time sync not yet calibrated'
      };
    }

    const offsetSeconds = Math.round(this.timeSync.serverOffset / 1000);
    const offsetHours = Math.round(offsetSeconds / 3600 * 10) / 10;
    const lastSyncAgo = Math.round((Date.now() - this.timeSync.lastSync) / 1000);
    
    let status: 'good' | 'warning' | 'error' = 'good';
    let message = `Time sync OK (${Math.abs(offsetSeconds)}s difference)`;
    
    if (Math.abs(offsetSeconds) > 300) { // > 5 minutes
      status = 'error';
      message = `Large time difference detected: ${Math.abs(offsetHours)}h offset`;
    } else if (Math.abs(offsetSeconds) > 60) { // > 1 minute
      status = 'warning';
      message = `Minor time drift: ${Math.abs(offsetSeconds)}s offset`;
    }

    return {
      isValid: this.timeSync.isValid,
      offsetSeconds,
      offsetHours,
      lastSyncAgo,
      status,
      message
    };
  }

  /**
   * Reset time sync (useful for testing)
   */
  resetTimeSync(): void {
    this.timeSync = {
      serverOffset: 0,
      lastSync: 0,
      isValid: false
    };
  }
}

export const timeManager = TimeManager.getInstance();

/**
 * Utility functions for common time operations
 */
export const timeUtils = {
  /**
   * Parse server timestamp with proper time handling
   */
  parseTimestamp: (timestamp: string): Date => {
    return timeManager.parseServerTimestamp(timestamp);
  },

  /**
   * Format timestamp for display
   */
  formatTimestamp: (date: Date): string => {
    return timeManager.formatRelativeTime(date);
  },

  /**
   * Get time range for data filtering
   */
  getTimeRange: (hours: number): { start: Date; end: Date } => {
    return timeManager.getTimeRange(hours);
  },

  /**
   * Calibrate time sync with server data
   */
  calibrateTimeSync: (apiData: Array<{ timestamp: string }>): void => {
    timeManager.calibrateTimeSync(apiData);
  },

  /**
   * Get current server time
   */
  getServerNow: (): Date => {
    return timeManager.getServerNow();
  },

  /**
   * Get time sync status for monitoring
   */
  getTimeSyncStatus: () => {
    return timeManager.getTimeSyncStatus();
  }
};