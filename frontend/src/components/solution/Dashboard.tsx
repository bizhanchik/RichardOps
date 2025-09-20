import React from 'react';
import MetricChart from './MetricChart';

interface DashboardProps {
  timeRange: string;
}

const Dashboard: React.FC<DashboardProps> = ({ timeRange }) => {

  const metrics = [
    {
      id: 'cpu',
      title: 'CPU Usage',
      value: '16.2%',
      color: 'emerald'
    },
    {
      id: 'memory',
      title: 'Memory Usage',
      value: '75.3%',
      color: 'blue'
    },
    {
      id: 'disk',
      title: 'Disk Usage',
      value: '76.4%',
      color: 'amber'
    },
    {
      id: 'network-rx',
      title: 'Network RX',
      value: '17,627 bytes/sec',
      color: 'purple'
    },
    {
      id: 'network-tx',
      title: 'Network TX',
      value: '31,698 bytes/sec',
      color: 'rose'
    },
    {
      id: 'tcp',
      title: 'TCP Connections',
      value: '76',
      color: 'cyan'
    }
  ];

  return (
    <div className="max-w-7xl mx-auto pt-6">
      {/* Header */}
      <div className="mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">System Metrics</h1>
          <p className="text-gray-600 mt-1">Real-time monitoring dashboard</p>
        </div>
      </div>

      {/* Status Cards */}
      <div className="mb-8 grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white rounded-xl p-6 border border-gray-200 shadow-sm">
          <div className="flex items-center">
            <div className="w-12 h-12 bg-emerald-100 rounded-lg flex items-center justify-center">
              <svg className="w-6 h-6 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div className="ml-4">
              <h3 className="text-lg font-semibold text-gray-900">System Status</h3>
              <p className="text-emerald-600 font-medium">All Systems Operational</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl p-6 border border-gray-200 shadow-sm">
          <div className="flex items-center">
            <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
              <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <div className="ml-4">
              <h3 className="text-lg font-semibold text-gray-900">Performance</h3>
              <p className="text-blue-600 font-medium">Optimal</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl p-6 border border-gray-200 shadow-sm">
          <div className="flex items-center">
            <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
              <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
            </div>
            <div className="ml-4">
              <h3 className="text-lg font-semibold text-gray-900">Security</h3>
              <p className="text-purple-600 font-medium">Protected</p>
            </div>
          </div>
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {metrics.map((metric) => (
          <MetricChart
            key={metric.id}
            title={metric.title}
            value={metric.value}
            color={metric.color}
            timeRange={timeRange}
          />
        ))}
      </div>
    </div>
  );
};

export default Dashboard;