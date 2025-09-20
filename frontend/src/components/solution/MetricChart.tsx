import React, { useEffect, useState } from 'react';
import { cpuDataService } from '../../utils/cpuDataService';
import type { ProcessedCPUData } from '../../utils/cpuDataService';
import LoadingAnimation, { ChartSkeleton } from '../LoadingAnimation';

interface MetricChartProps {
  title: string;
  value: string;
  color: string;
  timeRange: string;
}

const createCPUChart = (
  data: ProcessedCPUData[], 
  color: string, 
  chartWidth = 400, 
  chartHeight = 140,
  mousePosition: { x: number; y: number } | null = null,
  hoveredDataPoint: ProcessedCPUData | null = null,
  onMouseMove: (position: { x: number; y: number } | null, dataPoint: ProcessedCPUData | null) => void = () => {}
) => {
  if (data.length === 0) return null;
  
  const padding = 35; // Increased padding for better spacing
  const maxUsage = Math.max(...data.map(d => d.usage));
  const minUsage = Math.min(...data.map(d => d.usage));
  const usageRange = maxUsage - minUsage || 1;
  
  // Create path for the line
  const pathData = data.map((d, i) => {
    const x = padding + (i / (data.length - 1)) * (chartWidth - 2 * padding);
    const y = chartHeight - padding - ((d.usage - minUsage) / usageRange) * (chartHeight - 2 * padding);
    return `${i === 0 ? 'M' : 'L'} ${x} ${y}`;
  }).join(' ');
  
  // Create area path
  const areaPath = pathData + 
    ` L ${chartWidth - padding} ${chartHeight - padding}` + 
    ` L ${padding} ${chartHeight - padding} Z`;

  // Helper function to find closest data point to mouse X position
  const findClosestDataPoint = (mouseX: number) => {
    if (!data || data.length === 0) return { data: null, index: -1 };
    
    const relativeX = mouseX - padding;
    const normalizedX = relativeX / (chartWidth - 2 * padding);
    const index = Math.round(normalizedX * (data.length - 1));
    const clampedIndex = Math.max(0, Math.min(data.length - 1, index));
    return { data: data[clampedIndex], index: clampedIndex };
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
            <stop offset="0%" stopColor="rgb(16, 185, 129)" stopOpacity="0.3" />
            <stop offset="100%" stopColor="rgb(16, 185, 129)" stopOpacity="0.05" />
          </linearGradient>
          
          <linearGradient id="lineGradient" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="rgb(34, 197, 94)" />
            <stop offset="50%" stopColor="rgb(16, 185, 129)" />
            <stop offset="100%" stopColor="rgb(5, 150, 105)" />
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
        
        {/* Area fill */}
        <path
          d={areaPath}
          fill={`url(#gradient-${color})`}
          stroke="none"
        />
        
        {/* Main line */}
        <path
          d={pathData}
          fill="none"
          stroke="url(#lineGradient)"
          strokeWidth="2.5"
          filter="url(#glow)"
          strokeLinecap="round"
          strokeLinejoin="round"
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
              stroke="rgb(16, 185, 129)"
              strokeWidth="1"
              strokeDasharray="4,2"
              opacity="0.8"
            />
            
            {/* Highlight dot on the line */}
            {(() => {
              const dataIndex = data.findIndex(d => d === hoveredDataPoint);
              if (dataIndex === -1) return null;
              
              const x = padding + (dataIndex / (data.length - 1)) * (chartWidth - 2 * padding);
              const y = chartHeight - padding - ((hoveredDataPoint.usage - minUsage) / usageRange) * (chartHeight - 2 * padding);
              
              return (
                <circle
                  cx={x}
                  cy={y}
                  r="4"
                  fill="rgb(16, 185, 129)"
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
          {Math.round(maxUsage)}%
        </text>
        <text x="8" y={chartHeight - 15} fontSize="10" fill="#6b7280" textAnchor="start">
          {Math.round(minUsage)}%
        </text>
        
        {/* Middle Y-axis label for better reference */}
        <text x="8" y={chartHeight / 2 + 3} fontSize="10" fill="#6b7280" textAnchor="start">
          {Math.round((maxUsage + minUsage) / 2)}%
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

const MetricChart: React.FC<MetricChartProps> = ({ title, value, color, timeRange }) => {
  const [cpuData, setCpuData] = useState<ProcessedCPUData[]>([]);
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState(false); // Separate state for manual updates
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [mousePosition, setMousePosition] = useState<{ x: number; y: number } | null>(null);
  const [hoveredDataPoint, setHoveredDataPoint] = useState<ProcessedCPUData | null>(null);

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

  useEffect(() => {
    if (title !== 'CPU Usage') return;

    const loadData = async () => {
      try {
        setLoading(true);
        setError(null);
        
        console.log('Loading CPU data...');
        const data = await cpuDataService.loadCPUData();
        console.log('Raw data loaded:', data.length, 'points');
        
        // Get data based on time range
        const hours = timeRange === '1h' ? 1 : timeRange === '12h' ? 12 : 24;
        const filteredData = cpuDataService.getDataForRange(data, hours);
        console.log('Filtered data:', filteredData.length, 'points for', timeRange);
        
        // If no data for the time range, use all available data
        const dataToUse = filteredData.length > 0 ? filteredData : data;
        console.log('Using data:', dataToUse.length, 'points');
        
        // Downsample for better performance if needed
        const maxPoints = 50;
        const step = Math.max(1, Math.ceil(dataToUse.length / maxPoints));
        const sampledData = dataToUse.filter((_, i) => i % step === 0);
        console.log('Sampled data:', sampledData.length, 'points');
        
        setCpuData(sampledData);
        setLastUpdated(new Date());
      } catch (err) {
        console.error('Error loading CPU data:', err);
        setError(err instanceof Error ? err.message : 'Failed to load CPU data');
      } finally {
        setLoading(false);
      }
    };

    loadData();

    // Refresh data every 5 minutes
    const interval = setInterval(loadData, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, [title, timeRange]);

  const colors = getColorClasses(color);
  const isCPUChart = title === 'CPU Usage';

  // Calculate current metrics for CPU
  const stats = cpuDataService.calculateStats(cpuData);
  const currentUsage = stats?.current || 0;
  const displayValue = isCPUChart ? `${Math.round(currentUsage)}%` : value;

  if (isCPUChart && loading) {
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

  if (isCPUChart && error) {
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
              {timeRange === '1h' ? '1h' : timeRange === '12h' ? '12h' : '24h'}
            </div>
          </div>
        </div>
        
        {/* Status indicator based on CPU usage */}
        {isCPUChart && (
          <div className={`px-3 py-1 rounded-full text-xs font-medium ${
            currentUsage < 50 ? 'bg-green-100 text-green-800' :
            currentUsage < 80 ? 'bg-yellow-100 text-yellow-800' :
            'bg-red-100 text-red-800'
          }`}>
            {currentUsage < 50 ? 'Normal' : currentUsage < 80 ? 'Moderate' : 'High'}
          </div>
        )}
      </div>

      {/* Chart Area */}
      {isCPUChart && cpuData.length > 0 ? (
        <div className="mb-4 relative">
          
          {/* Crypto-style tooltip at the top right */}
          {hoveredDataPoint && (
            <div className="absolute top-2 right-4 bg-gray-900 text-white px-3 py-2 rounded-lg shadow-lg z-10 text-sm">
              <div className="font-semibold text-emerald-400">{hoveredDataPoint.usage}%</div>
              <div className="text-gray-300 text-xs">{hoveredDataPoint.formattedTime}</div>
            </div>
          )}
          
          {createCPUChart(
            cpuData, 
            color, 
            400, 
            140, 
            mousePosition, 
            hoveredDataPoint,
            (position, dataPoint) => {
              setMousePosition(position);
              setHoveredDataPoint(dataPoint);
            }
          )}
        </div>
      ) : isCPUChart && loading ? (
        <div className="mb-4">
          <div className="text-sm text-gray-500 mb-2">Loading CPU data...</div>
          <LoadingAnimation />
        </div>
      ) : isCPUChart && cpuData.length === 0 ? (
        <div className="mb-4">
          <div className="text-sm text-red-500 mb-2">No CPU data available (length: {cpuData.length})</div>
          <ChartSkeleton />
        </div>
      ) : !isCPUChart ? (
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

      {/* Statistics for CPU */}
      {isCPUChart && stats && (
        <div className="grid grid-cols-3 gap-4 text-sm mb-4">
          <div>
            <span className="text-gray-500">Min</span>
            <div className="font-semibold text-gray-900">{stats.min}%</div>
          </div>
          <div>
            <span className="text-gray-500">Avg</span>
            <div className="font-semibold text-gray-900">{stats.avg}%</div>
          </div>
          <div>
            <span className="text-gray-500">Max</span>
            <div className="font-semibold text-gray-900">{stats.max}%</div>
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
              cpuDataService.clearCache();
              setUpdating(true);
              try {
                console.log('Manual refresh: Loading CPU data...');
                const data = await cpuDataService.loadCPUData();
                console.log('Manual refresh: Raw data loaded:', data.length, 'points');
                
                // Update time range mapping
                const hours = timeRange === '1h' ? 1 : timeRange === '12h' ? 12 : 24;
                const filteredData = cpuDataService.getDataForRange(data, hours);
                console.log('Manual refresh: Filtered data:', filteredData.length, 'points for', timeRange);
                
                // If no data for the time range, use all available data
                const dataToUse = filteredData.length > 0 ? filteredData : data;
                console.log('Manual refresh: Using data:', dataToUse.length, 'points');
                
                const maxPoints = 50;
                const step = Math.max(1, Math.ceil(dataToUse.length / maxPoints));
                const sampledData = dataToUse.filter((_, i) => i % step === 0);
                console.log('Manual refresh: Sampled data:', sampledData.length, 'points');
                
                setCpuData(sampledData);
                setLastUpdated(new Date());
              } catch (err) {
                console.error('Manual refresh error:', err);
                setError(err instanceof Error ? err.message : 'Failed to load CPU data');
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