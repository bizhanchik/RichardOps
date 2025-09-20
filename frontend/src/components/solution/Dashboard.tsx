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