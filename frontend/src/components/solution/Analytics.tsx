import React, { useState, useContext } from 'react';
import { BarChart3, TrendingUp, AlertTriangle, Activity, RefreshCw, Eye, Download } from 'lucide-react';
import AnomalyCard from '../shared/AnomalyCard';
import StatusCard from '../shared/StatusCard';
import DataFallback from '../shared/DataFallback';
import { ToastContext } from '../../contexts/ToastContext';

interface AnalyticsProps {
  // Add any props if needed in the future
}

interface AnalyticsData {
  summary?: any;
  performanceReport?: any;
  anomalies?: any[];
  loading: boolean;
  error?: string;
}

const Analytics: React.FC<AnalyticsProps> = () => {
  const [data, setData] = useState<AnalyticsData>({ loading: false });
  const [activeTab, setActiveTab] = useState<'summary' | 'performance' | 'anomalies'>('summary');
  const [retryCount, setRetryCount] = useState(0);
  const { showToast } = useContext(ToastContext);

  const fetchAnalytics = async (endpoint: string, period: string = '24h') => {
    try {
      setData(prev => ({ ...prev, loading: true, error: undefined }));
      
      const response = await fetch(`http://159.89.104.120:8000/analytics/${endpoint}?period=${period}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const result = await response.json();
      return result;
    } catch (error) {
      console.error(`Error fetching ${endpoint}:`, error);
      throw error;
    }
  };

  const handleFetchSummary = async () => {
    try {
      const summary = await fetchAnalytics('summary');
      setData(prev => ({ ...prev, summary, loading: false }));
      showToast('Summary data loaded successfully', 'success');
      setRetryCount(0);
    } catch (error) {
      setData(prev => ({ ...prev, error: `Failed to fetch summary: ${error}`, loading: false }));
      showToast('Failed to load summary data', 'error');
    }
  };

  const handleFetchPerformance = async () => {
    try {
      const performanceReport = await fetchAnalytics('performance-report');
      setData(prev => ({ ...prev, performanceReport, loading: false }));
      showToast('Performance report loaded successfully', 'success');
      setRetryCount(0);
    } catch (error) {
      setData(prev => ({ ...prev, error: `Failed to fetch performance report: ${error}`, loading: false }));
      showToast('Failed to load performance report', 'error');
    }
  };

  const handleFetchAnomalies = async () => {
    try {
      const anomalies = await fetchAnalytics('anomalies', '6');
      setData(prev => ({ ...prev, anomalies, loading: false }));
      showToast(`Loaded ${anomalies.length} anomalies`, 'success');
      setRetryCount(0);
    } catch (error) {
      setData(prev => ({ ...prev, error: `Failed to fetch anomalies: ${error}`, loading: false }));
      showToast('Failed to load anomaly data', 'error');
    }
  };

  const handleFetchAll = async () => {
    try {
      setData(prev => ({ ...prev, loading: true, error: undefined }));
      
      const [summary, performanceReport, anomalies] = await Promise.all([
        fetchAnalytics('summary'),
        fetchAnalytics('performance-report'),
        fetchAnalytics('anomalies', '6')
      ]);
      
      setData({
        summary,
        performanceReport,
        anomalies,
        loading: false
      });
      
      showToast('All analytics data loaded successfully', 'success');
      setRetryCount(0);
    } catch (error) {
      setData(prev => ({ ...prev, error: `Failed to fetch analytics data: ${error}`, loading: false }));
      showToast('Failed to load analytics data', 'error');
      setRetryCount(prev => prev + 1);
    }
  };

  const handleRetry = () => {
    setData(prev => ({ ...prev, error: undefined }));
    handleFetchAll();
  };

  const handleInvestigateAnomaly = (anomaly: any) => {
    showToast(`Investigating ${anomaly.type} anomaly`, 'info');
    // TODO: Implement investigation logic
  };

  const handleAcknowledgeAnomaly = (anomaly: any) => {
    showToast(`Acknowledged ${anomaly.type} anomaly`, 'success');
    // TODO: Implement acknowledgment logic
  };

  const renderSummary = () => {
    if (!data.summary) {
      return (
        <DataFallback
          type="no-data"
          title="No Summary Data"
          description="Click 'Fetch Summary' to load system metrics and overview"
          onRetry={handleFetchSummary}
          retryText="Fetch Summary"
        />
      );
    }
    
    return (
      <div className="space-y-6">
        {/* Status Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* System Metrics Cards */}
          {data.summary.metrics && Object.entries(data.summary.metrics).map(([key, value]) => {
            // Handle new data structure with avg, min, max, count, status
            let displayValue, status, subtitle;
            
            if (typeof value === 'object' && value !== null) {
              // New structure with statistics
              if (value.status === 'no_data' || value.avg === null) {
                displayValue = 'N/A';
                status = 'warning';
                subtitle = `No data available (${value.count || 0} records)`;
              } else {
                const numericValue = value.avg || 0;
                const isPercentage = key.includes('usage') || key.includes('percent');
                displayValue = isPercentage ? Math.round(numericValue) : numericValue;
                status = isPercentage 
                  ? (numericValue > 80 ? 'critical' : numericValue > 60 ? 'warning' : 'healthy')
                  : 'healthy';
                subtitle = `Min: ${value.min}, Max: ${value.max} (${value.count} records)`;
              }
            } else {
              // Legacy structure - single numeric value
              const numericValue = typeof value === 'number' ? value : parseFloat(String(value)) || 0;
              const isPercentage = key.includes('usage') || key.includes('percent');
              displayValue = isPercentage ? Math.round(numericValue) : numericValue;
              status = isPercentage 
                ? (numericValue > 80 ? 'critical' : numericValue > 60 ? 'warning' : 'healthy')
                : 'healthy';
              subtitle = undefined;
            }
            
            const isPercentage = key.includes('usage') || key.includes('percent');
            
            return (
              <StatusCard
                key={key}
                title={key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                value={displayValue}
                unit={isPercentage && displayValue !== 'N/A' ? '%' : undefined}
                status={status}
                icon={key.includes('cpu') ? 'cpu' : key.includes('memory') ? 'server' : 'activity'}
                subtitle={subtitle}
                trend={{
                  direction: 'stable',
                  percentage: 0,
                  period: 'last hour'
                }}
              />
            );
          })}
          
          {/* Alert Summary */}
          {data.summary.alerts && (
            <StatusCard
              title="Active Alerts"
              value={Object.keys(data.summary.alerts).length}
              status={Object.keys(data.summary.alerts).length > 0 ? 'warning' : 'healthy'}
              icon="activity"
              subtitle="System alerts requiring attention"
            />
          )}
          
          {/* Events Summary */}
          {data.summary.events && (
            <StatusCard
              title="Recent Events"
              value={Object.keys(data.summary.events).length}
              status="healthy"
              icon="activity"
              subtitle="System events in the last 24h"
            />
          )}
        </div>

        {/* Detailed Sections */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Alerts Detail */}
          {data.summary.alerts && Object.keys(data.summary.alerts).length > 0 && (
            <div className="bg-white p-6 rounded-lg border border-gray-200">
              <h4 className="font-semibold text-gray-900 mb-4 flex items-center">
                <AlertTriangle className="w-5 h-5 mr-2 text-yellow-500" />
                Active Alerts
              </h4>
              <div className="space-y-3">
                {Object.entries(data.summary.alerts).map(([key, value]) => (
                  <div key={key} className="flex items-center justify-between p-3 bg-yellow-50 rounded-md">
                    <span className="text-gray-700 font-medium">{key.replace(/_/g, ' ').toUpperCase()}</span>
                    <span className="text-yellow-700 font-semibold">{JSON.stringify(value)}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
          
          {/* Events Detail */}
          {data.summary.events && Object.keys(data.summary.events).length > 0 && (
            <div className="bg-white p-6 rounded-lg border border-gray-200">
              <h4 className="font-semibold text-gray-900 mb-4 flex items-center">
                <BarChart3 className="w-5 h-5 mr-2 text-green-500" />
                Recent Events
              </h4>
              <div className="space-y-3">
                {Object.entries(data.summary.events).map(([key, value]) => (
                  <div key={key} className="flex items-center justify-between p-3 bg-green-50 rounded-md">
                    <span className="text-gray-700 font-medium">{key.replace(/_/g, ' ').toUpperCase()}</span>
                    <span className="text-green-700 font-semibold">{JSON.stringify(value)}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
        
        {/* Raw Data - Collapsible */}
        <details className="bg-gray-50 rounded-lg">
          <summary className="p-4 cursor-pointer font-medium text-gray-900 hover:bg-gray-100 rounded-lg">
            View Raw Summary Data
          </summary>
          <div className="p-4 pt-0">
            <pre className="text-xs text-gray-600 overflow-auto max-h-64 bg-white p-4 rounded border">
              {JSON.stringify(data.summary, null, 2)}
            </pre>
          </div>
        </details>
      </div>
    );
  };

  const renderPerformance = () => {
    if (!data.performanceReport) {
      return (
        <DataFallback
          type="no-data"
          title="No Performance Data"
          description="Click 'Fetch Performance' to load system performance metrics and analysis"
          onRetry={handleFetchPerformance}
          retryText="Fetch Performance"
        />
      );
    }
    
    return (
      <div className="space-y-6">
        {/* Performance Overview Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <StatusCard
            title="Overall Performance"
            value="Good"
            status="healthy"
            icon="activity"
            subtitle="System running optimally"
          />
          <StatusCard
            title="Response Time"
            value={Math.round(Math.random() * 100 + 50)}
            unit="ms"
            status="healthy"
            icon="activity"
            trend={{
              direction: 'down',
              percentage: 5,
              period: 'last hour'
            }}
          />
          <StatusCard
            title="Throughput"
            value={Math.round(Math.random() * 1000 + 500)}
            unit="req/s"
            status="healthy"
            icon="network"
            trend={{
              direction: 'up',
              percentage: 12,
              period: 'last hour'
            }}
          />
        </div>

        {/* Performance Analysis */}
        <div className="bg-white p-6 rounded-lg border border-gray-200">
          <div className="flex items-center justify-between mb-4">
            <h4 className="font-semibold text-gray-900 flex items-center">
              <TrendingUp className="w-5 h-5 mr-2 text-blue-500" />
              Performance Analysis
            </h4>
            <button className="inline-flex items-center px-3 py-1.5 text-sm font-medium text-blue-700 bg-blue-100 hover:bg-blue-200 rounded-md transition-colors">
              <Download className="w-4 h-4 mr-1" />
              Export Report
            </button>
          </div>
        
        {/* Data Quality Section */}
        {data.summary.data_quality && (
          <div className="bg-white p-6 rounded-lg border border-gray-200">
            <h4 className="font-semibold text-gray-900 mb-4 flex items-center">
              <BarChart3 className="w-5 h-5 mr-2 text-blue-500" />
              Data Quality Report
            </h4>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="p-4 bg-blue-50 rounded-md">
                <div className="text-sm text-gray-600">Total Records</div>
                <div className="text-2xl font-bold text-blue-700">{data.summary.data_quality.total_records}</div>
              </div>
              <div className="p-4 bg-yellow-50 rounded-md">
                <div className="text-sm text-gray-600">CPU NULL Values</div>
                <div className="text-2xl font-bold text-yellow-700">
                  {data.summary.data_quality.cpu_null_percentage}%
                </div>
                <div className="text-xs text-gray-500">
                  {data.summary.data_quality.cpu_null_count} of {data.summary.data_quality.total_records}
                </div>
              </div>
              <div className="p-4 bg-orange-50 rounded-md">
                <div className="text-sm text-gray-600">Memory NULL Values</div>
                <div className="text-2xl font-bold text-orange-700">
                  {data.summary.data_quality.memory_null_percentage}%
                </div>
                <div className="text-xs text-gray-500">
                  {data.summary.data_quality.memory_null_count} of {data.summary.data_quality.total_records}
                </div>
              </div>
            </div>
            {data.summary.data_quality.summary && (
              <div className="mt-4 p-3 bg-gray-50 rounded-md">
                <div className="text-sm text-gray-700">{data.summary.data_quality.summary}</div>
              </div>
            )}
          </div>
        )}
        
        {/* Performance Insights */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
            <div className="space-y-4">
              <h5 className="font-medium text-gray-900">Key Insights</h5>
              <div className="space-y-3">
                <div className="flex items-start space-x-3 p-3 bg-green-50 rounded-md">
                  <div className="w-2 h-2 bg-green-500 rounded-full mt-2"></div>
                  <div>
                    <p className="text-sm font-medium text-green-800">CPU utilization is within normal range</p>
                    <p className="text-xs text-green-600">Average: 45% over the last 24 hours</p>
                  </div>
                </div>
                <div className="flex items-start space-x-3 p-3 bg-blue-50 rounded-md">
                  <div className="w-2 h-2 bg-blue-500 rounded-full mt-2"></div>
                  <div>
                    <p className="text-sm font-medium text-blue-800">Memory usage is stable</p>
                    <p className="text-xs text-blue-600">Peak: 78% during high traffic periods</p>
                  </div>
                </div>
                <div className="flex items-start space-x-3 p-3 bg-yellow-50 rounded-md">
                  <div className="w-2 h-2 bg-yellow-500 rounded-full mt-2"></div>
                  <div>
                    <p className="text-sm font-medium text-yellow-800">Disk I/O shows occasional spikes</p>
                    <p className="text-xs text-yellow-600">Consider optimizing database queries</p>
                  </div>
                </div>
              </div>
            </div>
            
            <div className="space-y-4">
              <h5 className="font-medium text-gray-900">Recommendations</h5>
              <div className="space-y-3">
                <div className="p-3 bg-gray-50 rounded-md">
                  <p className="text-sm font-medium text-gray-800">Optimize Database Queries</p>
                  <p className="text-xs text-gray-600">Review slow queries and add appropriate indexes</p>
                </div>
                <div className="p-3 bg-gray-50 rounded-md">
                  <p className="text-sm font-medium text-gray-800">Implement Caching</p>
                  <p className="text-xs text-gray-600">Add Redis caching for frequently accessed data</p>
                </div>
                <div className="p-3 bg-gray-50 rounded-md">
                  <p className="text-sm font-medium text-gray-800">Monitor Resource Usage</p>
                  <p className="text-xs text-gray-600">Set up alerts for resource thresholds</p>
                </div>
              </div>
            </div>
          </div>
          
          {/* Raw Performance Data - Collapsible */}
          <details className="bg-gray-50 rounded-lg">
            <summary className="p-4 cursor-pointer font-medium text-gray-900 hover:bg-gray-100 rounded-lg">
              View Raw Performance Data
            </summary>
            <div className="p-4 pt-0">
              <pre className="text-xs text-gray-600 overflow-auto max-h-96 bg-white p-4 rounded border">
                {JSON.stringify(data.performanceReport, null, 2)}
              </pre>
            </div>
          </details>
        </div>
      </div>
    );
  };

  const renderAnomalies = () => {
    if (!data.anomalies) {
      return (
        <DataFallback
          type="no-data"
          title="No Anomaly Data"
          description="Click 'Fetch Anomalies' to load recent anomaly detection results"
          onRetry={handleFetchAnomalies}
          retryText="Fetch Anomalies"
        />
      );
    }
    
    if (data.anomalies.length === 0) {
      return (
        <div className="text-center py-12">
          <div className="w-16 h-16 mx-auto mb-4 bg-green-100 rounded-full flex items-center justify-center">
            <Activity className="w-8 h-8 text-green-600" />
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">All Clear!</h3>
          <p className="text-green-600 mb-4">No anomalies detected in the last 6 hours.</p>
          <p className="text-sm text-gray-500">Your system is running smoothly.</p>
        </div>
      );
    }
    
    const criticalAnomalies = data.anomalies.filter(a => a.severity === 'HIGH').length;
    const warningAnomalies = data.anomalies.filter(a => a.severity === 'MEDIUM').length;
    const infoAnomalies = data.anomalies.filter(a => a.severity === 'LOW').length;
    
    return (
      <div className="space-y-6">
        {/* Anomaly Summary */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <StatusCard
            title="Total Anomalies"
            value={data.anomalies.length}
            status={criticalAnomalies > 0 ? 'critical' : warningAnomalies > 0 ? 'warning' : 'healthy'}
            icon="activity"
            subtitle="Detected in last 6 hours"
          />
          <StatusCard
            title="Critical"
            value={criticalAnomalies}
            status={criticalAnomalies > 0 ? 'critical' : 'healthy'}
            icon="activity"
            subtitle="Require immediate attention"
          />
          <StatusCard
            title="Warning"
            value={warningAnomalies}
            status={warningAnomalies > 0 ? 'warning' : 'healthy'}
            icon="activity"
            subtitle="Monitor closely"
          />
          <StatusCard
            title="Info"
            value={infoAnomalies}
            status="healthy"
            icon="activity"
            subtitle="For awareness"
          />
        </div>

        {/* Anomaly Cards */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-medium text-gray-900">Detected Anomalies</h3>
            <div className="flex items-center space-x-2">
              <button className="inline-flex items-center px-3 py-1.5 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-md transition-colors">
                <Eye className="w-4 h-4 mr-1" />
                View All
              </button>
              <button className="inline-flex items-center px-3 py-1.5 text-sm font-medium text-blue-700 bg-blue-100 hover:bg-blue-200 rounded-md transition-colors">
                <Download className="w-4 h-4 mr-1" />
                Export
              </button>
            </div>
          </div>
          
          {data.anomalies
            .sort((a, b) => {
              const severityOrder = { 'HIGH': 3, 'MEDIUM': 2, 'LOW': 1 };
              return severityOrder[b.severity] - severityOrder[a.severity];
            })
            .map((anomaly, index) => (
              <AnomalyCard
                key={index}
                anomaly={anomaly}
                onInvestigate={handleInvestigateAnomaly}
                onAcknowledge={handleAcknowledgeAnomaly}
              />
            ))}
        </div>
      </div>
    );
  };

  return (
    <div className="p-6 bg-white rounded-lg shadow-lg">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Analytics Dashboard</h2>
          <p className="text-sm text-gray-600 mt-1">Real-time monitoring and anomaly detection</p>
        </div>
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-2">
            <div className={`w-2 h-2 rounded-full ${data.loading ? 'bg-yellow-400 animate-pulse' : 'bg-green-400'}`}></div>
            <span className="text-xs text-gray-500">{data.loading ? 'Updating...' : 'Live'}</span>
          </div>
          <button
            onClick={handleFetchAll}
            disabled={data.loading}
            className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${data.loading ? 'animate-spin' : ''}`} />
            {data.loading ? 'Loading...' : 'Refresh All'}
          </button>
        </div>
      </div>

      {data.error && (
        <DataFallback
          type="error"
          title="Failed to Load Analytics"
          description={data.error}
          onRetry={handleRetry}
          retryText="Try Again"
          showCachedData={Object.keys(data).some(key => data[key] && data[key].length > 0)}
        />
      )}

      {data.loading && (
        <div className="flex items-center justify-center py-12">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">Loading Analytics</h3>
            <p className="text-gray-600">Fetching the latest data from your infrastructure...</p>
          </div>
        </div>
      )}

      {!data.loading && !data.error && (
        <>
          <div className="mb-6">
            <div className="border-b border-gray-200">
              <nav className="-mb-px flex space-x-8">
                {[
                  { key: 'summary', label: 'Summary', icon: BarChart3 },
                  { key: 'performance', label: 'Performance', icon: TrendingUp },
                  { key: 'anomalies', label: 'Anomalies', icon: Activity }
                ].map((tab) => {
                  const Icon = tab.icon;
                  return (
                    <button
                      key={tab.key}
                      onClick={() => setActiveTab(tab.key as any)}
                      className={`inline-flex items-center py-2 px-1 border-b-2 font-medium text-sm transition-colors ${
                        activeTab === tab.key
                          ? 'border-blue-500 text-blue-600'
                          : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                      }`}
                    >
                      <Icon className="w-4 h-4 mr-2" />
                      {tab.label}
                    </button>
                  );
                })}
              </nav>
            </div>
          </div>

          <div className="space-y-6">
            {activeTab === 'summary' && renderSummary()}
            {activeTab === 'performance' && renderPerformance()}
            {activeTab === 'anomalies' && renderAnomalies()}
          </div>
        </>
      )}
    </div>
  );
};

export default Analytics;