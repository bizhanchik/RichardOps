import React, { useState } from 'react';
import { 
  AlertTriangle, 
  AlertCircle, 
  Info, 
  ChevronDown, 
  ChevronUp, 
  Eye, 
  Check, 
  Clock,
  Server,
  Activity,
  TrendingUp
} from 'lucide-react';

interface AnomalyCardProps {
  anomaly: {
    type: string;
    severity: 'LOW' | 'MEDIUM' | 'HIGH';
    timestamp: string;
    description: string;
    details: Record<string, any>;
    affected_resource?: string;
    confidence: number;
  };
  onInvestigate?: (anomaly: any) => void;
  onAcknowledge?: (anomaly: any) => void;
  className?: string;
}

const AnomalyCard: React.FC<AnomalyCardProps> = ({
  anomaly,
  onInvestigate,
  onAcknowledge,
  className = ''
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [isAcknowledged, setIsAcknowledged] = useState(false);

  const getSeverityConfig = () => {
    switch (anomaly.severity) {
      case 'HIGH':
        return {
          borderColor: 'border-red-500',
          bgColor: 'bg-red-50',
          textColor: 'text-red-800',
          badgeColor: 'bg-red-100 text-red-700 border-red-200',
          icon: <AlertCircle className="w-5 h-5 text-red-500" />
        };
      case 'MEDIUM':
        return {
          borderColor: 'border-yellow-500',
          bgColor: 'bg-yellow-50',
          textColor: 'text-yellow-800',
          badgeColor: 'bg-yellow-100 text-yellow-700 border-yellow-200',
          icon: <AlertTriangle className="w-5 h-5 text-yellow-500" />
        };
      case 'LOW':
        return {
          borderColor: 'border-blue-500',
          bgColor: 'bg-blue-50',
          textColor: 'text-blue-800',
          badgeColor: 'bg-blue-100 text-blue-700 border-blue-200',
          icon: <Info className="w-5 h-5 text-blue-500" />
        };
      default:
        return {
          borderColor: 'border-gray-500',
          bgColor: 'bg-gray-50',
          textColor: 'text-gray-800',
          badgeColor: 'bg-gray-100 text-gray-700 border-gray-200',
          icon: <Info className="w-5 h-5 text-gray-500" />
        };
    }
  };

  const getTypeIcon = () => {
    const type = anomaly.type.toLowerCase();
    if (type.includes('cpu') || type.includes('memory') || type.includes('disk')) {
      return <Activity className="w-4 h-4" />;
    }
    if (type.includes('container') || type.includes('restart')) {
      return <Server className="w-4 h-4" />;
    }
    if (type.includes('spike') || type.includes('request')) {
      return <TrendingUp className="w-4 h-4" />;
    }
    return <AlertTriangle className="w-4 h-4" />;
  };

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    return date.toLocaleDateString();
  };

  const handleAcknowledge = () => {
    setIsAcknowledged(true);
    if (onAcknowledge) {
      onAcknowledge(anomaly);
    }
  };

  const handleInvestigate = () => {
    if (onInvestigate) {
      onInvestigate(anomaly);
    }
  };

  const config = getSeverityConfig();

  return (
    <div className={`
      bg-white border-l-4 ${config.borderColor} rounded-r-lg shadow-lg hover:shadow-xl 
      transition-all duration-200 ${isAcknowledged ? 'opacity-75' : ''} ${className}
    `}>
      <div className="p-4">
        {/* Header */}
        <div className="flex justify-between items-start mb-3">
          <div className="flex items-start space-x-3 flex-1">
            <div className="flex-shrink-0 mt-0.5">
              {config.icon}
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center space-x-2 mb-1">
                <h3 className="font-semibold text-gray-900 truncate">
                  {anomaly.type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                </h3>
                {isAcknowledged && (
                  <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-700">
                    <Check className="w-3 h-3 mr-1" />
                    Acknowledged
                  </span>
                )}
              </div>
              <p className="text-sm text-gray-600 mb-2">
                {anomaly.description}
              </p>
              <div className="flex items-center space-x-3 text-xs text-gray-500">
                <span className={`inline-flex items-center px-2 py-1 rounded-full font-medium border ${config.badgeColor}`}>
                  {anomaly.severity}
                </span>
                <span className="flex items-center">
                  <Clock className="w-3 h-3 mr-1" />
                  {formatTimestamp(anomaly.timestamp)}
                </span>
                <span>Confidence: {Math.round(anomaly.confidence * 100)}%</span>
              </div>
            </div>
          </div>
          
          {/* Actions */}
          <div className="flex items-center space-x-2 ml-4">
            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className="p-1.5 text-gray-400 hover:text-gray-600 rounded-md hover:bg-gray-100 transition-colors"
            >
              {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
            </button>
          </div>
        </div>

        {/* Expandable Details */}
        {isExpanded && (
          <div className="mt-4 pt-4 border-t border-gray-200">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Affected Resources */}
              {anomaly.affected_resource && (
                <div>
                  <h4 className="text-sm font-medium text-gray-900 mb-2">Affected Resource</h4>
                  <div className="bg-gray-50 p-3 rounded-md">
                    <span className="text-sm text-gray-700 font-mono">
                      {anomaly.affected_resource}
                    </span>
                  </div>
                </div>
              )}

              {/* Technical Details */}
              <div>
                <h4 className="text-sm font-medium text-gray-900 mb-2">Technical Details</h4>
                <div className="bg-gray-50 p-3 rounded-md">
                  <div className="space-y-1 text-sm text-gray-700">
                    {Object.entries(anomaly.details).map(([key, value]) => (
                      <div key={key} className="flex justify-between">
                        <span className="font-medium">{key.replace(/_/g, ' ')}:</span>
                        <span className="font-mono text-gray-600">
                          {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* Recommendations */}
            <div className="mt-4">
              <h4 className="text-sm font-medium text-gray-900 mb-2">Recommended Actions</h4>
              <div className="bg-blue-50 p-3 rounded-md">
                <ul className="text-sm text-blue-800 space-y-1">
                  {anomaly.type.includes('cpu') && (
                    <li>• Check for resource-intensive processes</li>
                  )}
                  {anomaly.type.includes('memory') && (
                    <li>• Review memory usage patterns and potential leaks</li>
                  )}
                  {anomaly.type.includes('disk') && (
                    <li>• Monitor disk I/O and storage capacity</li>
                  )}
                  {anomaly.type.includes('request') && (
                    <li>• Investigate potential DDoS or unusual traffic patterns</li>
                  )}
                  {anomaly.type.includes('restart') && (
                    <li>• Check container logs for crash reasons</li>
                  )}
                  <li>• Monitor the situation for recurring patterns</li>
                </ul>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default AnomalyCard;