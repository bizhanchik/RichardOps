import React, { useState } from 'react';
import { BarChart3, TrendingUp, AlertTriangle, Activity, RefreshCw } from 'lucide-react';

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
    } catch (error) {
      setData(prev => ({ ...prev, error: `Failed to fetch summary: ${error}`, loading: false }));
    }
  };

  const handleFetchPerformance = async () => {
    try {
      const performanceReport = await fetchAnalytics('performance-report');
      setData(prev => ({ ...prev, performanceReport, loading: false }));
    } catch (error) {
      setData(prev => ({ ...prev, error: `Failed to fetch performance report: ${error}`, loading: false }));
    }
  };

  const handleFetchAnomalies = async () => {
    try {
      const anomalies = await fetchAnalytics('anomalies', '6');
      setData(prev => ({ ...prev, anomalies, loading: false }));
    } catch (error) {
      setData(prev => ({ ...prev, error: `Failed to fetch anomalies: ${error}`, loading: false }));
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
    } catch (error) {
      setData(prev => ({ ...prev, error: `Failed to fetch analytics data: ${error}`, loading: false }));
    }
  };

  const renderSummary = () => {
    if (!data.summary) return <div className="text-gray-500">No summary data available. Click "Fetch Summary" to load data.</div>;
    
    return (
      <div className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {/* Metrics */}
          {data.summary.metrics && (
            <div className="bg-white p-4 rounded-lg border border-gray-200">
              <h4 className="font-semibold text-gray-900 mb-2 flex items-center">
                <Activity className="w-4 h-4 mr-2 text-blue-500" />
                System Metrics
              </h4>
              <div className="space-y-2 text-sm">
                {Object.entries(data.summary.metrics).map(([key, value]) => (
                  <div key={key} className="flex justify-between">
                    <span className="text-gray-600">{key.replace(/_/g, ' ').toUpperCase()}:</span>
                    <span className="font-medium">{JSON.stringify(value)}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
          
          {/* Alerts */}
          {data.summary.alerts && (
            <div className="bg-white p-4 rounded-lg border border-gray-200">
              <h4 className="font-semibold text-gray-900 mb-2 flex items-center">
                <AlertTriangle className="w-4 h-4 mr-2 text-yellow-500" />
                Alerts
              </h4>
              <div className="space-y-2 text-sm">
                {Object.entries(data.summary.alerts).map(([key, value]) => (
                  <div key={key} className="flex justify-between">
                    <span className="text-gray-600">{key.replace(/_/g, ' ').toUpperCase()}:</span>
                    <span className="font-medium">{JSON.stringify(value)}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
          
          {/* Events */}
          {data.summary.events && (
            <div className="bg-white p-4 rounded-lg border border-gray-200">
              <h4 className="font-semibold text-gray-900 mb-2 flex items-center">
                <BarChart3 className="w-4 h-4 mr-2 text-green-500" />
                Events
              </h4>
              <div className="space-y-2 text-sm">
                {Object.entries(data.summary.events).map(([key, value]) => (
                  <div key={key} className="flex justify-between">
                    <span className="text-gray-600">{key.replace(/_/g, ' ').toUpperCase()}:</span>
                    <span className="font-medium">{JSON.stringify(value)}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
        
        {/* Raw Data */}
        <div className="bg-gray-50 p-4 rounded-lg">
          <h4 className="font-semibold text-gray-900 mb-2">Raw Summary Data</h4>
          <pre className="text-xs text-gray-600 overflow-auto max-h-64">
            {JSON.stringify(data.summary, null, 2)}
          </pre>
        </div>
      </div>
    );
  };

  const renderPerformance = () => {
    if (!data.performanceReport) return <div className="text-gray-500">No performance data available. Click "Fetch Performance" to load data.</div>;
    
    return (
      <div className="space-y-4">
        <div className="bg-white p-4 rounded-lg border border-gray-200">
          <h4 className="font-semibold text-gray-900 mb-2 flex items-center">
            <TrendingUp className="w-4 h-4 mr-2 text-blue-500" />
            Performance Analysis
          </h4>
          <pre className="text-xs text-gray-600 overflow-auto max-h-96">
            {JSON.stringify(data.performanceReport, null, 2)}
          </pre>
        </div>
      </div>
    );
  };

  const renderAnomalies = () => {
    if (!data.anomalies) return <div className="text-gray-500">No anomaly data available. Click "Fetch Anomalies" to load data.</div>;
    
    if (data.anomalies.length === 0) {
      return <div className="text-green-600">No anomalies detected in the last 6 hours.</div>;
    }
    
    return (
      <div className="space-y-4">
        {data.anomalies.map((anomaly, index) => (
          <div key={index} className={`p-4 rounded-lg border ${
            anomaly.severity === 'HIGH' ? 'bg-red-50 border-red-200' :
            anomaly.severity === 'MEDIUM' ? 'bg-yellow-50 border-yellow-200' :
            'bg-blue-50 border-blue-200'
          }`}>
            <div className="flex items-center justify-between mb-2">
              <h4 className="font-semibold text-gray-900">{anomaly.type}</h4>
              <span className={`px-2 py-1 rounded text-xs font-medium ${
                anomaly.severity === 'HIGH' ? 'bg-red-100 text-red-800' :
                anomaly.severity === 'MEDIUM' ? 'bg-yellow-100 text-yellow-800' :
                'bg-blue-100 text-blue-800'
              }`}>
                {anomaly.severity}
              </span>
            </div>
            <p className="text-gray-700 text-sm mb-2">{anomaly.description}</p>
            <div className="text-xs text-gray-500">
              <div>Timestamp: {anomaly.timestamp}</div>
              <div>Confidence: {anomaly.confidence}%</div>
              {anomaly.affected_resource && <div>Resource: {anomaly.affected_resource}</div>}
            </div>
          </div>
        ))}
      </div>
    );
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Analytics Dashboard</h1>
        <button
          onClick={handleFetchAll}
          disabled={data.loading}
          className="flex items-center space-x-2 px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          <RefreshCw className={`w-4 h-4 ${data.loading ? 'animate-spin' : ''}`} />
          <span>Fetch All Data</span>
        </button>
      </div>

      {/* Error Display */}
      {data.error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center">
            <AlertTriangle className="w-5 h-5 text-red-500 mr-2" />
            <span className="text-red-700">{data.error}</span>
          </div>
        </div>
      )}

      {/* Loading Indicator */}
      {data.loading && (
        <div className="flex items-center justify-center py-8">
          <RefreshCw className="w-6 h-6 animate-spin text-emerald-600 mr-2" />
          <span className="text-gray-600">Loading analytics data...</span>
        </div>
      )}

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {[
            { id: 'summary', name: 'System Summary', action: handleFetchSummary },
            { id: 'performance', name: 'Performance Report', action: handleFetchPerformance },
            { id: 'anomalies', name: 'Anomaly Detection', action: handleFetchAnomalies }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => {
                setActiveTab(tab.id as any);
                tab.action();
              }}
              className={`py-2 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === tab.id
                  ? 'border-emerald-500 text-emerald-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              {tab.name}
            </button>
          ))}
        </nav>
      </div>

      {/* Content */}
      <div className="min-h-96">
        {activeTab === 'summary' && renderSummary()}
        {activeTab === 'performance' && renderPerformance()}
        {activeTab === 'anomalies' && renderAnomalies()}
      </div>
    </div>
  );
};

export default Analytics;