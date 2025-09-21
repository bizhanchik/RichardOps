import React from 'react';
import { 
  TrendingUp, 
  TrendingDown, 
  Minus, 
  Activity, 
  Server, 
  Database, 
  Cpu, 
  HardDrive, 
  Network,
  AlertTriangle,
  CheckCircle,
  Clock
} from 'lucide-react';

interface StatusCardProps {
  title: string;
  value: string | number;
  unit?: string;
  trend?: {
    direction: 'up' | 'down' | 'stable';
    percentage: number;
    period: string;
  };
  status?: 'healthy' | 'warning' | 'critical' | 'unknown';
  icon?: 'activity' | 'server' | 'database' | 'cpu' | 'harddrive' | 'network' | 'custom';
  customIcon?: React.ReactNode;
  subtitle?: string;
  onClick?: () => void;
  className?: string;
  size?: 'sm' | 'md' | 'lg';
}

const StatusCard: React.FC<StatusCardProps> = ({
  title,
  value,
  unit,
  trend,
  status = 'unknown',
  icon = 'activity',
  customIcon,
  subtitle,
  onClick,
  className = '',
  size = 'md'
}) => {
  const getStatusConfig = () => {
    switch (status) {
      case 'healthy':
        return {
          borderColor: 'border-green-200',
          bgColor: 'bg-green-50',
          statusColor: 'text-green-600',
          statusIcon: <CheckCircle className="w-4 h-4" />
        };
      case 'warning':
        return {
          borderColor: 'border-yellow-200',
          bgColor: 'bg-yellow-50',
          statusColor: 'text-yellow-600',
          statusIcon: <AlertTriangle className="w-4 h-4" />
        };
      case 'critical':
        return {
          borderColor: 'border-red-200',
          bgColor: 'bg-red-50',
          statusColor: 'text-red-600',
          statusIcon: <AlertTriangle className="w-4 h-4" />
        };
      default:
        return {
          borderColor: 'border-gray-200',
          bgColor: 'bg-gray-50',
          statusColor: 'text-gray-600',
          statusIcon: <Clock className="w-4 h-4" />
        };
    }
  };

  const getIcon = () => {
    if (customIcon) return customIcon;
    
    const iconClass = size === 'sm' ? 'w-5 h-5' : size === 'lg' ? 'w-7 h-7' : 'w-6 h-6';
    
    switch (icon) {
      case 'server':
        return <Server className={iconClass} />;
      case 'database':
        return <Database className={iconClass} />;
      case 'cpu':
        return <Cpu className={iconClass} />;
      case 'harddrive':
        return <HardDrive className={iconClass} />;
      case 'network':
        return <Network className={iconClass} />;
      default:
        return <Activity className={iconClass} />;
    }
  };

  const getTrendIcon = () => {
    if (!trend) return null;
    
    const iconClass = 'w-4 h-4';
    switch (trend.direction) {
      case 'up':
        return <TrendingUp className={`${iconClass} text-green-500`} />;
      case 'down':
        return <TrendingDown className={`${iconClass} text-red-500`} />;
      case 'stable':
        return <Minus className={`${iconClass} text-gray-500`} />;
      default:
        return null;
    }
  };

  const getTrendColor = () => {
    if (!trend) return 'text-gray-500';
    
    switch (trend.direction) {
      case 'up':
        return 'text-green-600';
      case 'down':
        return 'text-red-600';
      case 'stable':
        return 'text-gray-600';
      default:
        return 'text-gray-500';
    }
  };

  const getSizeClasses = () => {
    switch (size) {
      case 'sm':
        return {
          padding: 'p-4',
          titleSize: 'text-sm',
          valueSize: 'text-xl',
          subtitleSize: 'text-xs'
        };
      case 'lg':
        return {
          padding: 'p-6',
          titleSize: 'text-lg',
          valueSize: 'text-4xl',
          subtitleSize: 'text-sm'
        };
      default:
        return {
          padding: 'p-5',
          titleSize: 'text-base',
          valueSize: 'text-3xl',
          subtitleSize: 'text-sm'
        };
    }
  };

  const statusConfig = getStatusConfig();
  const sizeClasses = getSizeClasses();

  return (
    <div 
      className={`
        bg-white border ${statusConfig.borderColor} rounded-lg shadow-sm hover:shadow-md 
        transition-all duration-200 ${onClick ? 'cursor-pointer hover:scale-105' : ''} 
        ${className}
      `}
      onClick={onClick}
    >
      <div className={sizeClasses.padding}>
        {/* Header */}
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center space-x-2">
            <div className="text-gray-600">
              {getIcon()}
            </div>
            <h3 className={`font-medium text-gray-900 ${sizeClasses.titleSize}`}>
              {title}
            </h3>
          </div>
          <div className={`flex items-center ${statusConfig.statusColor}`}>
            {statusConfig.statusIcon}
          </div>
        </div>

        {/* Value */}
        <div className="mb-2">
          <div className="flex items-baseline space-x-1">
            <span className={`font-bold text-gray-900 ${sizeClasses.valueSize}`}>
              {typeof value === 'number' ? value.toLocaleString() : value}
            </span>
            {unit && (
              <span className="text-gray-500 text-sm font-medium">
                {unit}
              </span>
            )}
          </div>
        </div>

        {/* Subtitle */}
        {subtitle && (
          <p className={`text-gray-600 mb-2 ${sizeClasses.subtitleSize}`}>
            {subtitle}
          </p>
        )}

        {/* Trend */}
        {trend && (
          <div className="flex items-center space-x-1">
            {getTrendIcon()}
            <span className={`${sizeClasses.subtitleSize} font-medium ${getTrendColor()}`}>
              {trend.percentage > 0 ? '+' : ''}{trend.percentage}%
            </span>
            <span className={`${sizeClasses.subtitleSize} text-gray-500`}>
              vs {trend.period}
            </span>
          </div>
        )}
      </div>
    </div>
  );
};

export default StatusCard;