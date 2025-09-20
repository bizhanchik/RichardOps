import { useState, useEffect } from 'react';

export interface ApiStatus {
  isOnline: boolean;
  lastCheck: Date;
  responseTime: number | null;
  error: string | null;
}

export const useApiConnectivity = (checkInterval: number = 30000) => {
  const [status, setStatus] = useState<ApiStatus>({
    isOnline: false,
    lastCheck: new Date(),
    responseTime: null,
    error: null
  });

  const checkConnectivity = async () => {
    const startTime = Date.now();
    try {
      const response = await fetch('http://159.89.104.120:8000/metrics/range?metric=cpu&range=1h', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        signal: AbortSignal.timeout(10000) // 10 second timeout
      });

      const responseTime = Date.now() - startTime;

      if (response.ok) {
        setStatus({
          isOnline: true,
          lastCheck: new Date(),
          responseTime,
          error: null
        });
      } else {
        setStatus({
          isOnline: false,
          lastCheck: new Date(),
          responseTime,
          error: `HTTP ${response.status}: ${response.statusText}`
        });
      }
    } catch (error) {
      const responseTime = Date.now() - startTime;
      setStatus({
        isOnline: false,
        lastCheck: new Date(),
        responseTime,
        error: error instanceof Error ? error.message : 'Unknown error'
      });
    }
  };

  useEffect(() => {
    // Check immediately on mount
    checkConnectivity();

    // Set up interval for periodic checks
    const interval = setInterval(checkConnectivity, checkInterval);

    return () => clearInterval(interval);
  }, [checkInterval]);

  return { status, checkConnectivity };
};