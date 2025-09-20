import React, { useEffect, useState } from 'react';
import { cpuDataService } from '../../utils/cpuDataService';
import type { ProcessedCPUData } from '../../utils/cpuDataService';
import { memoryDataService } from '../../utils/memoryDataService';
import type { ProcessedMemoryData } from '../../utils/memoryDataService';
import { diskDataService } from '../../utils/diskDataService';
import type { ProcessedDiskData } from '../../utils/diskDataService';
import { networkDataService } from '../../utils/networkDataService';
import type { ProcessedNetworkData } from '../../utils/networkDataService';
import { tcpDataService } from '../../utils/tcpDataService';
import type { ProcessedTCPData } from '../../utils/tcpDataService';
import LoadingAnimation, { ChartSkeleton } from '../LoadingAnimation';
import { timeUtils } from '../../utils/timeUtils';

// Union type for all metric data types
type MetricDataPoint = ProcessedCPUData | ProcessedMemoryData | ProcessedDiskData | ProcessedNetworkData | ProcessedTCPData;

// Helper function to format values based on metric type
const getFormattedValue = (value: number, metricType: string): string => {
  switch (metricType) {
    case 'cpu':
    case 'memory':
    case 'disk':
      // Show exact value with up to 2 decimal places, remove trailing zeros
      return `${parseFloat(value.toFixed(2))}%`;
    case 'network-rx':
    case 'network-tx':
      return formatBytes(value);
    case 'tcp':
      // Show exact value for TCP connections
      return parseFloat(value.toFixed(1)).toString();
    default:
      return `${parseFloat(value.toFixed(2))}%`;
  }
};

// Helper function to format bytes
const formatBytes = (bytes: number): string => {
  // Handle invalid values
  if (isNaN(bytes) || bytes === undefined || bytes === null || bytes < 0) {
    return '0 B';
  }
  
  if (bytes === 0) return '0 B';
  
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  const value = bytes / Math.pow(k, i);
  
  return `${Math.round(value * 100) / 100} ${sizes[i]}`;
};

// Helper function to get metric type from title
const getMetricType = (title: string): string => {
  switch (title) {
    case 'CPU Usage':
      return 'cpu';
    case 'Memory Usage':
      return 'memory';
    case 'Disk Usage':
      return 'disk';
    case 'Network RX':
      return 'network-rx';
    case 'Network TX':
      return 'network-tx';
    case 'TCP Connections':
      return 'tcp';
    default:
      return 'cpu';
  }
};

interface MetricChartProps {
  title: string;
  value: string;
  color: string;
  timeRange: string;
}

// Helper function to get chart colors
const getChartColors = (colorName: string) => {
  const colorMap = {
    emerald: { primary: '#10b981', secondary: '#34d399', tertiary: '#059669' },
    blue: { primary: '#3b82f6', secondary: '#60a5fa', tertiary: '#2563eb' },
    amber: { primary: '#f59e0b', secondary: '#fbbf24', tertiary: '#d97706' },
    purple: { primary: '#8b5cf6', secondary: '#a78bfa', tertiary: '#7c3aed' },
    rose: { primary: '#f43f5e', secondary: '#fb7185', tertiary: '#e11d48' },
    cyan: { primary: '#06b6d4', secondary: '#22d3ee', tertiary: '#0891b2' }
  };
  return colorMap[colorName as keyof typeof colorMap] || colorMap.emerald;
};

const createCPUChart = (
  data: MetricDataPoint[], 
  color: string, 
  chartWidth = 400, 
  chartHeight = 140,
  mousePosition: { x: number; y: number } | null = null,
  hoveredDataPoint: MetricDataPoint | null = null,
  onMouseMove: (position: { x: number; y: number } | null, dataPoint: MetricDataPoint | null) => void = () => {},
  animationState: {
    isAnimating: boolean;
    oldDomain: { start: Date; end: Date } | null;
    newDomain: { start: Date; end: Date } | null;
    progress: number;
  } | null = null,
  metricType: string = 'cpu'
) => {
  if (data.length === 0) return null;
  
  const chartColors = getChartColors(color);
  
  const padding = 35;
  
  // Determine the time domain for rendering
  const getTimeDomain = () => {
    if (animationState?.isAnimating && animationState.oldDomain && animationState.newDomain) {
      // Interpolate between old and new domains
      const { oldDomain, newDomain, progress } = animationState;
      
      // Determine transition direction for adaptive easing
      const oldDuration = oldDomain.end.getTime() - oldDomain.start.getTime();
      const newDuration = newDomain.end.getTime() - newDomain.start.getTime();
      const isContracting = newDuration < oldDuration;
      
      // Use different easing: aggressive for contracting, smooth for expanding
      const eased = isContracting 
        ? 1 - Math.pow(1 - progress, 1.5) // More aggressive for contracting (fast)
        : 1 - Math.pow(1 - progress, 3); // Smooth cubic for expanding (elegant)
      
      const startTime = new Date(
        oldDomain.start.getTime() + 
        (newDomain.start.getTime() - oldDomain.start.getTime()) * eased
      );
      const endTime = new Date(
        oldDomain.end.getTime() + 
        (newDomain.end.getTime() - oldDomain.end.getTime()) * eased
      );
      
      return { start: startTime, end: endTime };
    }
    
    // Default domain: extend to current time so lines reach the end
    const timestamps = data.map(d => d.timestamp);
    const dataStart = new Date(Math.min(...timestamps.map(t => t.getTime())));
    const dataEnd = new Date(Math.max(...timestamps.map(t => t.getTime())));
    const now = new Date(); // Current UTC time
    
    // Extend end time to current time if data is recent
    const timeSinceLastData = now.getTime() - dataEnd.getTime();
    const fiveMinutes = 5 * 60 * 1000;
    
    return {
      start: dataStart,
      end: timeSinceLastData < fiveMinutes ? now : dataEnd
    };
  };

  const timeDomain = getTimeDomain();
  const timeRange = timeDomain.end.getTime() - timeDomain.start.getTime();
  
  // Filter and position data points based on current time domain
  const getVisibleData = () => {
    return data
      .filter(d => d.timestamp >= timeDomain.start && d.timestamp <= timeDomain.end)
      .map(d => {
        const timeFraction = (d.timestamp.getTime() - timeDomain.start.getTime()) / timeRange;
        const x = padding + timeFraction * (chartWidth - 2 * padding);
        return { ...d, x };
      });
  };

  const visibleData = getVisibleData();
  
  if (visibleData.length === 0) return null;
  
  const maxUsage = Math.max(...visibleData.map(d => d.usage));
  const minUsage = Math.min(...visibleData.map(d => d.usage));
  const isFlat = maxUsage === minUsage;
  
  // For flat lines, add artificial range to create a visible curve
  let adjustedMinUsage = minUsage;
  let adjustedMaxUsage = maxUsage;
  let usageRange = maxUsage - minUsage;
  
  if (isFlat) {
    // Add small artificial range around the constant value
    const artificialRange = Math.max(maxUsage * 0.1, 5); // 10% of value or minimum 5
    adjustedMinUsage = maxUsage - artificialRange / 2;
    adjustedMaxUsage = maxUsage + artificialRange / 2;
    usageRange = adjustedMaxUsage - adjustedMinUsage;
  } else {
    usageRange = maxUsage - minUsage || 1;
  }
  
  // Create path for the interpolated line
  const pathData = visibleData.map((d, i) => {
    let y;
    if (isFlat) {
      // For flat lines, place at the center of the artificial range
      y = chartHeight - padding - ((d.usage - adjustedMinUsage) / usageRange) * (chartHeight - 2 * padding);
    } else {
      // Normal scaling for varying data
      y = chartHeight - padding - ((d.usage - minUsage) / usageRange) * (chartHeight - 2 * padding);
    }
    return `${i === 0 ? 'M' : 'L'} ${d.x} ${y}`;
  }).join(' ');
  
  // Create area path
  const areaPath = pathData + 
    ` L ${chartWidth - padding} ${chartHeight - padding}` + 
    ` L ${padding} ${chartHeight - padding} Z`;

  // Helper function to find closest data point to mouse X position
  const findClosestDataPoint = (mouseX: number) => {
    if (!visibleData || visibleData.length === 0) return { data: null, index: -1 };
    
    const closest = visibleData.reduce((prev, curr) => {
      return Math.abs(curr.x - mouseX) < Math.abs(prev.x - mouseX) ? curr : prev;
    });
    
    return { data: closest, index: visibleData.indexOf(closest) };
  };
  
  return (
    <div className="relative w-full h-48">
      <svg
        width="100%"
        height="100%"
        viewBox={`0 0 ${chartWidth} ${chartHeight}`}
        className="overflow-visible cursor-crosshair"
        onMouseMove={(e) => {
          try {
            const rect = e.currentTarget.getBoundingClientRect();
            const scaleX = chartWidth / rect.width;
            const scaleY = chartHeight / rect.height;
            const mouseX = (e.clientX - rect.left) * scaleX;
            const mouseY = (e.clientY - rect.top) * scaleY;
            
            // Only track if within chart bounds
            if (mouseX >= padding && mouseX <= chartWidth - padding) {
              const closest = findClosestDataPoint(mouseX);
              if (closest.data) {
                onMouseMove({ x: mouseX, y: mouseY }, closest.data);
              }
            }
          } catch (error) {
            console.error('Mouse tracking error:', error);
          }
        }}
        onMouseLeave={() => {
          try {
            onMouseMove(null, null);
          } catch (error) {
            console.error('Mouse leave error:', error);
          }
        }}
      >
        {/* Gradient definitions */}
        <defs>
          <pattern id="grid" width="40" height="28" patternUnits="userSpaceOnUse">
            <path d="M 40 0 L 0 0 0 28" fill="none" stroke="#f3f4f6" strokeWidth="1"/>
          </pattern>
          
          <linearGradient id={`gradient-${color}`} x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor={chartColors.primary} stopOpacity="0.3" />
            <stop offset="100%" stopColor={chartColors.primary} stopOpacity="0.05" />
          </linearGradient>
          
          <linearGradient id={`lineGradient-${color}`} x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor={chartColors.secondary} />
            <stop offset="50%" stopColor={chartColors.primary} />
            <stop offset="100%" stopColor={chartColors.tertiary} />
          </linearGradient>
          
          <filter id="glow">
            <feGaussianBlur stdDeviation="2" result="coloredBlur"/>
            <feMerge> 
              <feMergeNode in="coloredBlur"/>
              <feMergeNode in="SourceGraphic"/>
            </feMerge>
          </filter>
        </defs>
        
        <rect width="100%" height="100%" fill="url(#grid)" />
        
        {/* Main line with smooth morphing */}
        <path
          d={pathData}
          fill="none"
          stroke={`url(#lineGradient-${color})`}
          strokeWidth="2.5"
          filter="url(#glow)"
          strokeLinecap="round"
          strokeLinejoin="round"
          style={{
            transition: 'd 0.8s cubic-bezier(0.4, 0, 0.2, 1)',
          }}
          className="animate-draw-line"
        />
        
        {/* Area fill with smooth morphing */}
        <path
          d={areaPath}
          fill={`url(#gradient-${color})`}
          stroke="none"
          style={{
            transition: 'd 0.8s cubic-bezier(0.4, 0, 0.2, 1)',
          }}
        />
        
        {/* Crypto-style vertical line tracker */}
        {mousePosition && hoveredDataPoint && (
          <>
            {/* Vertical line that follows mouse */}
            <line
              x1={mousePosition.x}
              y1={padding}
              x2={mousePosition.x}
              y2={chartHeight - padding}
              stroke={chartColors.primary}
              strokeWidth="1"
              strokeDasharray="4,2"
              opacity="0.8"
            />
            
            {/* Highlight dot on the line */}
            {(() => {
              // Find the hovered data point in the visible data
              const visibleDataPoint = visibleData.find(d => 
                d.timestamp.getTime() === hoveredDataPoint.timestamp.getTime() && 
                d.usage === hoveredDataPoint.usage
              );
              
              if (!visibleDataPoint) return null;
              
              const x = visibleDataPoint.x;
              let y;
              if (isFlat) {
                // For flat lines, use the artificial range positioning
                y = chartHeight - padding - ((hoveredDataPoint.usage - adjustedMinUsage) / usageRange) * (chartHeight - 2 * padding);
              } else {
                // Normal scaling for varying data
                y = chartHeight - padding - ((hoveredDataPoint.usage - minUsage) / usageRange) * (chartHeight - 2 * padding);
              }
              
              return (
                <circle
                  cx={x}
                  cy={y}
                  r="4"
                  fill={chartColors.primary}
                  stroke="white"
                  strokeWidth="2"
                  filter="url(#glow)"
                />
              );
            })()}
          </>
        )}
        
        {/* No individual data points - clean crypto-style chart */}
        
        {/* Y-axis labels with improved spacing */}
        <text x="8" y="20" fontSize="10" fill="#6b7280" textAnchor="start">
          {isFlat ? 
            getFormattedValue(adjustedMaxUsage, metricType) : 
            getFormattedValue(maxUsage, metricType)
          }
        </text>
        <text x="8" y={chartHeight - 15} fontSize="10" fill="#6b7280" textAnchor="start">
          {isFlat ? 
            getFormattedValue(adjustedMinUsage, metricType) : 
            getFormattedValue(minUsage, metricType)
          }
        </text>
        
        {/* Middle Y-axis label for better reference */}
        <text x="8" y={chartHeight / 2 + 3} fontSize="10" fill="#6b7280" textAnchor="start">
          {isFlat ? 
            getFormattedValue(maxUsage, metricType) : 
            getFormattedValue((maxUsage + minUsage) / 2, metricType)
          }
        </text>
      </svg>
      
      {/* Time labels with improved spacing and positioning */}
      <div className="absolute bottom-0 left-0 right-0 flex justify-between px-12 pb-1 text-xs text-gray-400">
        <span className="bg-gray-50 px-1 rounded">{data[0]?.formattedTime}</span>
        <span className="bg-gray-50 px-1 rounded">Now</span>
      </div>
    </div>
  );
};

// Helper function to load data based on metric type
const loadMetricData = async (metricType: string, timeRange: '1h' | '6h' | '12h' = '12h'): Promise<MetricDataPoint[]> => {
  switch (metricType) {
    case 'cpu':
      return await cpuDataService.loadCPUData(timeRange);
    case 'memory':
      return await memoryDataService.loadMemoryData(timeRange);
    case 'disk':
      return await diskDataService.loadDiskData(timeRange);
    case 'network-rx':
      return await networkDataService.loadNetworkData('rx', timeRange);
    case 'network-tx':
      return await networkDataService.loadNetworkData('tx', timeRange);
    case 'tcp':
      return await tcpDataService.loadTCPData(timeRange);
    default:
      return await cpuDataService.loadCPUData(timeRange);
  }
};

// Helper function to get data for range based on metric type
const getDataForRange = (data: MetricDataPoint[], hours: number, metricType: string): MetricDataPoint[] => {
  switch (metricType) {
    case 'cpu':
      return cpuDataService.getDataForRange(data as ProcessedCPUData[], hours);
    case 'memory':
      return memoryDataService.getDataForRange(data as ProcessedMemoryData[], hours);
    case 'disk':
      return diskDataService.getDataForRange(data as ProcessedDiskData[], hours);
    case 'network-rx':
    case 'network-tx':
      return networkDataService.getDataForRange(data as ProcessedNetworkData[], hours);
    case 'tcp':
      return tcpDataService.getDataForRange(data as ProcessedTCPData[], hours);
    default:
      return cpuDataService.getDataForRange(data as ProcessedCPUData[], hours);
  }
};

// Helper function to calculate stats based on metric type
const calculateStats = (data: MetricDataPoint[], metricType: string) => {
  switch (metricType) {
    case 'cpu':
      return cpuDataService.calculateStats(data as ProcessedCPUData[]);
    case 'memory':
      return memoryDataService.calculateStats(data as ProcessedMemoryData[]);
    case 'disk':
      return diskDataService.calculateStats(data as ProcessedDiskData[]);
    case 'network-rx':
    case 'network-tx':
      return networkDataService.calculateStats(data as ProcessedNetworkData[]);
    case 'tcp':
      return tcpDataService.calculateStats(data as ProcessedTCPData[]);
    default:
      return cpuDataService.calculateStats(data as ProcessedCPUData[]);
  }
};

// Helper function to clear cache based on metric type
const clearCache = (metricType: string): void => {
  switch (metricType) {
    case 'cpu':
      cpuDataService.clearCache();
      break;
    case 'memory':
      memoryDataService.clearCache();
      break;
    case 'disk':
      diskDataService.clearCache();
      break;
    case 'network-rx':
    case 'network-tx':
      networkDataService.clearCache();
      break;
    case 'tcp':
      tcpDataService.clearCache();
      break;
    default:
      cpuDataService.clearCache();
      break;
  }
};

const MetricChart: React.FC<MetricChartProps> = ({ title, value, color, timeRange }) => {
  const metricType = getMetricType(title);
  const [metricData, setMetricData] = useState<MetricDataPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [mousePosition, setMousePosition] = useState<{ x: number; y: number } | null>(null);
  const [hoveredDataPoint, setHoveredDataPoint] = useState<MetricDataPoint | null>(null);
  
  // Domain-based animation state
  const [animationState, setAnimationState] = useState<{
    isAnimating: boolean;
    oldDomain: { start: Date; end: Date } | null;
    newDomain: { start: Date; end: Date } | null;
    progress: number;
  } | null>(null);
  
  const [currentTimeRange, setCurrentTimeRange] = useState(timeRange);
  const [timeSyncStatus, setTimeSyncStatus] = useState(timeUtils.getTimeSyncStatus());

  const getColorClasses = (color: string) => {
    const colorMap = {
      emerald: {
        bg: 'bg-emerald-50',
        border: 'border-emerald-200',
        text: 'text-emerald-600',
        icon: 'text-emerald-500',
        chartColor: '#10b981'
      },
      blue: {
        bg: 'bg-blue-50',
        border: 'border-blue-200',
        text: 'text-blue-600',
        icon: 'text-blue-500',
        chartColor: '#3b82f6'
      },
      amber: {
        bg: 'bg-amber-50',
        border: 'border-amber-200',
        text: 'text-amber-600',
        icon: 'text-amber-500',
        chartColor: '#f59e0b'
      },
      purple: {
        bg: 'bg-purple-50',
        border: 'border-purple-200',
        text: 'text-purple-600',
        icon: 'text-purple-500',
        chartColor: '#8b5cf6'
      },
      rose: {
        bg: 'bg-rose-50',
        border: 'border-rose-200',
        text: 'text-rose-600',
        icon: 'text-rose-500',
        chartColor: '#f43f5e'
      },
      cyan: {
        bg: 'bg-cyan-50',
        border: 'border-cyan-200',
        text: 'text-cyan-600',
        icon: 'text-cyan-500',
        chartColor: '#06b6d4'
      }
    };
    return colorMap[color as keyof typeof colorMap] || colorMap.emerald;
  };

  // Domain-based smooth transition system
  const animateDomainTransition = async (newTimeRange: string) => {
    if (metricData.length === 0) return;
    
    // Prevent multiple animations from stacking
    if (animationState?.isAnimating) {
      console.log('Animation already in progress, skipping...');
      return;
    }

    // Set loading state during transition
    setLoading(true);
    setError(null);

    // Calculate current domain from existing data
    const timestamps = metricData.map(d => d.timestamp);
    const oldStart = new Date(Math.min(...timestamps.map(t => t.getTime())));
    const oldEnd = new Date(Math.max(...timestamps.map(t => t.getTime())));
    const oldDuration = oldEnd.getTime() - oldStart.getTime();

    // Determine focus time (hovered timestamp or "now")
    const focusTime = hoveredDataPoint?.timestamp || oldEnd;
    
    // Calculate fraction where focus time sits in current domain
    const fraction = (focusTime.getTime() - oldStart.getTime()) / oldDuration;
    
    // Calculate new duration based on time range
    const newHours = newTimeRange === '1h' ? 1 : newTimeRange === '6h' ? 6 : 12;
    const newDuration = newHours * 60 * 60 * 1000; // Convert to milliseconds
    
    // Calculate new domain keeping focus time anchored
    const newStart = new Date(focusTime.getTime() - fraction * newDuration);
    const newEnd = new Date(newStart.getTime() + newDuration);

    // Set up animation state
    setAnimationState({
      isAnimating: true,
      oldDomain: { start: oldStart, end: oldEnd },
      newDomain: { start: newStart, end: newEnd },
      progress: 0
    });

    // Load new data for the time range while animating
    try {
      const data = await loadMetricData(metricType, newTimeRange as '1h' | '6h' | '12h');
      const filteredData = getDataForRange(data, newHours, metricType);
      const dataToUse = filteredData.length > 0 ? filteredData : data;
      
      // Downsample for performance
      const maxPoints = 50;
      const step = Math.max(1, Math.ceil(dataToUse.length / maxPoints));
      const sampledData = dataToUse.filter((_, i) => i % step === 0);

      // Adaptive animation duration based on transition direction
      const oldDurationHours = oldDuration / (60 * 60 * 1000); // Convert to hours
      const isExpanding = newHours > oldDurationHours; // Low to high (1h → 6h → 12h)
      const isContracting = newHours < oldDurationHours; // High to low (12h → 6h → 1h)
      
      // Instant for contracting, balanced for expanding
      const duration = isContracting ? 0 : isExpanding ? 500 : 400;
      const startTime = Date.now();
      
      const animate = () => {
        const elapsed = Date.now() - startTime;
        const progress = duration === 0 ? 1 : Math.min(elapsed / duration, 1);
        
        setAnimationState(prev => prev ? {
          ...prev,
          progress
        } : null);
        
        if (progress < 1) {
          requestAnimationFrame(animate);
        } else {
          // Animation complete - update time range and data
          setAnimationState(null);
          setCurrentTimeRange(newTimeRange);
          setMetricData(sampledData);
          setLoading(false);
        }
      };
      
      requestAnimationFrame(animate);
    } catch (err) {
      console.error('Error loading data during transition:', err);
      setAnimationState(null);
      setCurrentTimeRange(newTimeRange);
      setLoading(false);
      setError(err instanceof Error ? err.message : `Failed to load ${metricType} data`);
    }
  };

  // Watch for time range changes and trigger domain animation
  useEffect(() => {
    // Prevent multiple animations and ensure we have data
    if (currentTimeRange !== timeRange && metricData.length > 0 && !animationState?.isAnimating) {
      animateDomainTransition(timeRange);
    }
  }, [timeRange]); // Remove metricData.length dependency to prevent multiple triggers

  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        setError(null);
        
        console.log(`Loading ${metricType} data...`);
        const data = await loadMetricData(metricType, timeRange as '1h' | '6h' | '12h');
        console.log('Raw data loaded:', data.length, 'points');
        
        // Get data based on the actual time range
        const hours = timeRange === '1h' ? 1 : timeRange === '6h' ? 6 : 12;
        const filteredData = getDataForRange(data, hours, metricType);
        console.log('Filtered data:', filteredData.length, 'points for', timeRange);
        
        // If no data for the time range, use all available data
        const dataToUse = filteredData.length > 0 ? filteredData : data;
        console.log('Using data:', dataToUse.length, 'points');
        
        // Deterministic sampling to prevent dramatic visual changes
        const maxPoints = 50;
        let sampledData = dataToUse;
        if (dataToUse.length > maxPoints) {
          // Use consistent interval-based sampling instead of modulo
          const interval = (dataToUse.length - 1) / (maxPoints - 1);
          sampledData = [];
          for (let i = 0; i < maxPoints; i++) {
            const index = Math.round(i * interval);
            if (index < dataToUse.length) {
              sampledData.push(dataToUse[index]);
            }
          }
        }
        console.log('Sampled data:', sampledData.length, 'points');
        
        setMetricData(sampledData);
        setCurrentTimeRange(timeRange);
        setLastUpdated(new Date());
        
        // Update time sync status after data load
        setTimeSyncStatus(timeUtils.getTimeSyncStatus());
        
      } catch (err) {
        console.error(`Error loading ${metricType} data:`, err);
        setError(err instanceof Error ? err.message : `Failed to load ${metricType} data`);
      } finally {
        setLoading(false);
      }
    };

    loadData();

    // Refresh data every 10 seconds for real-time updates
    const interval = setInterval(loadData, 10 * 1000);
    return () => clearInterval(interval);
  }, [metricType, timeRange]);

  const colors = getColorClasses(color);
  const chartColors = getChartColors(color);
  const isActiveChart = metricData.length > 0;

  // Calculate current metrics for all chart types
  const stats = calculateStats(metricData, metricType);
  const currentUsage = stats?.current || 0;
  const displayValue = isActiveChart ? getFormattedValue(currentUsage, metricType) : value;

  if (loading) {
    return (
      <div className="bg-white rounded-xl p-6 border border-gray-200 shadow-sm hover:shadow-md transition-shadow duration-200">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-3">
            <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
            <LoadingAnimation size="sm" message="Loading..." />
          </div>
        </div>
        <ChartSkeleton />
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-xl p-6 border border-red-200 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-3">
            <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
            <div className="text-red-600">
              <p className="text-sm">⚠️ {error}</p>
              <button 
                onClick={() => window.location.reload()}
                className="text-xs text-red-500 hover:text-red-700 underline mt-1"
              >
                Retry loading
              </button>
            </div>
          </div>
        </div>
        <div className="flex items-center justify-center h-48 bg-red-50 rounded-lg border border-red-200">
          <div className="text-center">
            <div className="text-red-400 text-4xl mb-2">⚠️</div>
            <p className="text-red-600 font-medium">API Connection Failed</p>
            <p className="text-red-500 text-sm mt-1">Unable to load {title.toLowerCase()} data</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl p-6 border border-gray-200 shadow-sm hover:shadow-md transition-shadow duration-200">
      {/* Chart Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-3">
          <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
          <div className="flex items-center space-x-2">
            <div className={`text-xl font-bold ${colors.text}`}>{displayValue}</div>
            <div className={`px-2 py-1 rounded text-xs font-medium ${colors.bg} ${colors.text}`}>
              {timeRange === '1h' ? '1h' : timeRange === '6h' ? '6h' : '12h'}
            </div>
          </div>
        </div>
        
        {/* Status indicator based on usage */}
        {metricType === 'cpu' && (
          <div className={`px-3 py-1 rounded-full text-xs font-medium ${
            currentUsage < 50 ? 'bg-green-100 text-green-800' :
            currentUsage < 80 ? 'bg-yellow-100 text-yellow-800' :
            'bg-red-100 text-red-800'
          }`}>
            {currentUsage < 50 ? 'Normal' : currentUsage < 80 ? 'Moderate' : 'High'}
          </div>
        )}
      </div>

      {/* Time Sync Warning - Only show critical errors */}
      {timeSyncStatus.status === 'error' && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
          <div className="flex items-center space-x-2 text-red-700 text-sm">
            <span>⚠️</span>
            <span className="font-medium">Clock Sync Issue:</span>
            <span>{timeSyncStatus.message}</span>
          </div>
        </div>
      )}

      {/* Chart Area */}
      {isActiveChart && metricData.length > 0 ? (
        <div className="mb-4 relative">
          
          
          {/* Crypto-style tooltip at the top right */}
          {hoveredDataPoint && !animationState?.isAnimating && (
            <div className="absolute top-2 right-4 bg-gray-900 text-white px-3 py-2 rounded-lg shadow-lg z-10 text-sm">
              <div className="font-semibold" style={{ color: chartColors.primary }}>{getFormattedValue(hoveredDataPoint.usage, metricType)}</div>
              <div className="text-gray-300 text-xs">{hoveredDataPoint.formattedTime}</div>
            </div>
          )}
          
          {createCPUChart(
            metricData,
            color, 
            400, 
            140, 
            mousePosition, 
            hoveredDataPoint,
            (position: { x: number; y: number } | null, dataPoint: MetricDataPoint | null) => {
              setMousePosition(position);
              setHoveredDataPoint(dataPoint);
            },
            animationState,
            metricType
          )}
        </div>
      ) : loading ? (
        <div className="mb-4">
          <div className="text-sm text-gray-500 mb-2">Loading {title} data...</div>
          <LoadingAnimation />
        </div>
      ) : metricData.length === 0 ? (
        <div className="mb-4">
          <div className="text-sm text-red-500 mb-2">No {title} data available (length: {metricData.length})</div>
          <ChartSkeleton />
        </div>
      ) : !isActiveChart ? (
        <div className={`h-48 rounded-lg border-2 border-dashed ${colors.border} ${colors.bg} flex items-center justify-center mb-4`}>
          <div className="text-center">
            <div className={`w-16 h-16 rounded-full ${colors.bg} border-2 ${colors.border} flex items-center justify-center mx-auto mb-3`}>
              <svg className={`w-8 h-8 ${colors.icon}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
            <p className={`text-sm font-medium ${colors.text}`}>No Data Available</p>
            <p className="text-xs text-gray-400 mt-1">Chart will appear here</p>
          </div>
        </div>
      ) : null}

      {/* Statistics for active charts */}
      {isActiveChart && stats && (
        <div className="grid grid-cols-3 gap-4 text-sm mb-4">
          <div>
            <span className="text-gray-500">Min</span>
            <div className="font-semibold text-gray-900">
              {getFormattedValue(Number(stats.min), metricType)}
            </div>
          </div>
          <div>
            <span className="text-gray-500">Avg</span>
            <div className="font-semibold text-gray-900">
              {getFormattedValue(Number(stats.avg), metricType)}
            </div>
          </div>
          <div>
            <span className="text-gray-500">Max</span>
            <div className="font-semibold text-gray-900">
              {getFormattedValue(Number(stats.max), metricType)}
            </div>
          </div>
        </div>
      )}

      {/* Chart Footer */}
      <div className="flex items-center justify-between text-xs text-gray-500">
        <span>
          Last updated: {lastUpdated ? lastUpdated.toLocaleTimeString() : 'Just now'}
        </span>
        <div className="flex items-center space-x-2">
          {/* Update button */}
          <button
            onClick={async () => {
              clearCache(metricType);
              setUpdating(true);
              try {
                console.log(`Manual refresh: Loading ${metricType} data...`);
                const data = await loadMetricData(metricType, timeRange as '1h' | '6h' | '12h');
                console.log('Manual refresh: Raw data loaded:', data.length, 'points');
                
                // Update time range mapping
                const hours = timeRange === '1h' ? 1 : timeRange === '6h' ? 6 : 12;
                const filteredData = getDataForRange(data, hours, metricType);
                console.log('Manual refresh: Filtered data:', filteredData.length, 'points for', timeRange);
                
                // If no data for the time range, use all available data
                const dataToUse = filteredData.length > 0 ? filteredData : data;
                console.log('Manual refresh: Using data:', dataToUse.length, 'points');
                
                // Deterministic sampling to prevent dramatic visual changes
                const maxPoints = 50;
                let sampledData = dataToUse;
                if (dataToUse.length > maxPoints) {
                  // Use consistent interval-based sampling instead of modulo
                  const interval = (dataToUse.length - 1) / (maxPoints - 1);
                  sampledData = [];
                  for (let i = 0; i < maxPoints; i++) {
                    const index = Math.round(i * interval);
                    if (index < dataToUse.length) {
                      sampledData.push(dataToUse[index]);
                    }
                  }
                }
                console.log('Manual refresh: Sampled data:', sampledData.length, 'points');
                
                // Set data directly - domain animations handle transitions
                setMetricData(sampledData);
                setLastUpdated(new Date());
              } catch (err) {
                console.error('Manual refresh error:', err);
                setError(err instanceof Error ? err.message : `Failed to load ${metricType} data`);
              } finally {
                setUpdating(false);
              }
            }}
            className="px-2 py-1 bg-emerald-50 text-emerald-600 rounded text-xs hover:bg-emerald-100 transition-colors"
            disabled={updating}
          >
            {updating ? 'Updating...' : 'Update'}
          </button>
          
          {/* Live indicator - only show when updating */}
          {updating && (
            <div className="flex items-center space-x-1">
              <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse"></div>
              <span>Live</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default MetricChart;