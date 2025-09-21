import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Database, Clock, Container, AlertCircle, CheckCircle, Code, Terminal, TrendingUp, TrendingDown, Activity, Zap, Shield, Eye, BarChart3, PieChart, LineChart, AlertTriangle, Info, Lightbulb, Target, Cpu, HardDrive, Wifi, Server, Search, Filter, Download, Copy, ExternalLink } from 'lucide-react';

interface LogEntry {
  id: string;
  timestamp: string;
  container: string;
  message: string;
  level?: string;
}

interface AnomalyData {
  type: 'cpu' | 'memory' | 'disk' | 'network';
  severity: 'low' | 'medium' | 'high' | 'critical';
  value: number;
  threshold: number;
  timestamp: string;
  description: string;
  recommendation?: string;
}



interface QueryResult {
  success: boolean;
  intent: string;
  confidence: number;
  results?: any[];
  count?: number;
  processing_time_ms?: number;
  error?: string;
  metadata?: {
    intent: string;
    confidence: number;
    query_processed_at: string;
    entities_found: number;
    processing_time_ms: number;
  };
  query_info?: {
    query_type: string;
    method_called?: string;
    parameters?: Record<string, any>;
  };
  anomalies?: AnomalyData[];
  insights?: string[];
  recommendations?: string[];
}

interface Message {
  id: string;
  type: 'user' | 'ai' | 'system';
  content: string;
  timestamp: Date;
  queryResult?: QueryResult;
  messageType?: 'normal' | 'anomaly' | 'insight' | 'recommendation';
}

interface AskAIProps {
  sidebarOpen?: boolean;
}

const AskAI: React.FC<AskAIProps> = ({ sidebarOpen = true }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [recentAnomalies, setRecentAnomalies] = useState<AnomalyData[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Improved suggested queries with better categorization and validated mappings
  // Categorized suggestions for better organization - REDUCED SET
  const suggestedQueries = [
    {
      category: "📋 Log Analysis",
      queries: [
        "🔍 Show me recent logs",
        "📋 Find error logs",
        "🔧 Show system logs"
      ]
    }
  ];
  
  // Flatten all queries for backward compatibility
  const allSuggestedQueries = suggestedQueries.flatMap(category => category.queries);
  
  // Deterministic mapping of suggestions to specific backend functions - validated mappings only
  const suggestionMapping = {
    "🔍 Show me recent logs": {
      endpoint: "/api/nlp/query",
      method: "POST",
      payload: { query: "show me recent logs" },
      intent: "search_logs"
    },
    "📋 Find error logs": {
      endpoint: "/api/nlp/query",
      method: "POST",
      payload: { query: "find error logs" },
      intent: "search_logs"
    },
    "🔧 Show system logs": {
      endpoint: "/api/nlp/query",
      method: "POST",
      payload: { query: "show system logs" },
      intent: "search_logs"
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);



  const handleSendMessage = async () => {
    if (!inputValue.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      content: inputValue.trim(),
      sender: 'user',
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    const currentInput = inputValue;
    setInputValue('');

    try {
      const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
      const response = await fetch(`${apiBaseUrl}/api/nlp/query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query: currentInput }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      console.log('Backend response:', result); // Debug log
      
      // Handle the new direct mapping system response format
      let queryResult: QueryResult;
      let formattedContent: string;
      
      if (result.success && result.data) {
        // New direct mapping system response structure
        queryResult = {
          success: result.success,
          intent: result.data.function_used || 'unknown',
          confidence: result.data.metadata?.confidence || 1.0,
          results: result.data.results || [],
          count: result.data.count || result.data.results?.length || 0,
          processing_time_ms: result.processing_time_ms || result.data.processing_time_ms || 0,
          metadata: result.data.metadata,
          query_info: {
            query_type: result.data.function_used || 'unknown',
            method_called: result.data.function_used,
            parameters: result.data.parameters || {}
          }
        };
        
        formattedContent = formatAIResponseForDirectMapping(result.data, currentInput);
      } else {
        // Fallback for other response formats
        queryResult = result.result || result;
        formattedContent = formatAIResponse(result);
      }
      
      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'ai',
        content: formattedContent,
        timestamp: new Date(),
        queryResult: queryResult,
      };

      setMessages(prev => [...prev, aiMessage]);
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'ai',
        content: 'Sorry, I encountered an error while processing your request. Please try again.',
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const generateEnhancedResponse = (result: QueryResult, userQuery: string): string => {
    try {
      // Handle low confidence responses with helpful suggestions
      if (result.confidence < 0.3) {
        const suggestions = [
          "Try being more specific about what you're looking for",
          "Include keywords like 'logs', 'alerts', 'performance', or 'metrics'",
          "Ask questions like 'show me recent logs' or 'what alerts are active'",
          "Use time-specific queries like 'logs from last hour' or 'today's errors'"
        ];
        
        return `I'm not entirely sure what you're looking for (confidence: ${(result.confidence * 100).toFixed(1)}%). 

Here are some suggestions to help me understand better:
${suggestions.map(s => `• ${s}`).join('\n')}

You can also try one of the suggested queries below.`;
      }

      // Handle unknown intent with better guidance
      if (result.intent === 'unknown') {
        return `I didn't understand your request. Here are some things I can help you with:

**📋 View Logs**: "show me recent logs", "get error logs", "display container logs"
**🚨 Check Alerts**: "show current alerts", "any critical issues", "what's broken"
**📊 Performance**: "system performance", "CPU usage", "memory metrics"
**🔍 Investigate**: "what caused this error", "debug the issue", "why is it slow"
**📈 Analytics**: "system summary", "detect anomalies", "show trends"
**📄 Reports**: "generate report", "create summary", "export analytics"

Try rephrasing your question using these examples as a guide.`;
      }

      // Enhanced responses based on intent and confidence
      if (result.intent === 'search_logs') {
        if (result.results && result.results.length > 0) {
          const errorCount = result.results.filter(r => r.level === 'ERROR').length;
          const warningCount = result.results.filter(r => r.level === 'WARN').length;
          
          let summary = `Found ${result.results.length} log entries`;
          if (errorCount > 0 || warningCount > 0) {
            summary += ` (${errorCount} errors, ${warningCount} warnings)`;
          }
          summary += `. Here are the most relevant entries:`;
          
          return summary;
        } else {
          return `No log entries found matching your criteria. Try:
• Expanding the time range
• Using different keywords
• Checking if the service is running
• Looking for logs in a different container`;
        }
      }

      if (result.intent === 'show_alerts') {
        if (result.results && result.results.length > 0) {
          const criticalCount = result.results.filter(r => r.severity === 'critical').length;
          const highCount = result.results.filter(r => r.severity === 'high').length;
          
          return `Found ${result.results.length} active alerts. ${criticalCount > 0 ? `⚠️ ${criticalCount} critical alerts require immediate attention!` : ''} ${highCount > 0 ? `🔶 ${highCount} high priority alerts.` : ''}`;
        } else {
          return `✅ No active alerts found. Your system appears to be running smoothly!`;
        }
      }

      if (result.intent === 'investigate') {
        return `🔍 Investigation Results:

I've analyzed the available data to help understand the issue. The information below shows relevant logs, metrics, and patterns that might explain what happened.

${result.confidence < 0.6 ? '💡 **Tip**: For more accurate investigations, try including specific error messages, timestamps, or component names in your query.' : ''}`;
      }

      if (result.intent === 'analytics_performance') {
        return `📊 System Performance Analysis:

Here's a comprehensive view of your system's current performance metrics and trends. Pay attention to any values that appear highlighted in red or yellow.`;
      }

      if (result.intent === 'analytics_anomalies') {
        if (result.results && result.results.length > 0) {
          return `🚨 Anomaly Detection Results:

Found ${result.results.length} potential anomalies in your system. These patterns deviate from normal behavior and may require investigation.`;
        } else {
          return `✅ No significant anomalies detected. Your system metrics are within normal ranges.`;
        }
      }

      if (result.intent === 'generate_report') {
        return `📄 Report Generated:

I've compiled a comprehensive report based on your request. The report includes relevant metrics, trends, and insights from the specified time period.`;
      }

      if (result.intent === 'analytics_summary') {
        return `📋 System Summary:

Here's a high-level overview of your system's current status, including key metrics, recent activity, and any items that need attention.`;
      }

      if (result.intent === 'analyze_trends') {
        return `📈 Trend Analysis:

I've analyzed historical data to identify patterns and trends. Look for any significant changes or unusual patterns in the visualizations below.`;
      }

      if (result.intent === 'analytics_metrics') {
        return `📊 System Metrics:

Current system metrics and key performance indicators. Values are updated in real-time and color-coded based on thresholds.`;
      }

      // Default response for other intents
      return `I found ${result.results?.length || 0} results for your query. ${result.confidence < 0.6 ? 'The results may not be exactly what you were looking for - try being more specific for better results.' : ''}`;
      
    } catch (error) {
      console.error('Error generating enhanced response:', error);
      return `I found some results for your query, but had trouble formatting the response. Please try rephrasing your question.`;
    }
  };

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const formatLogLevel = (level?: string) => {
    if (!level) return null;
    
    const levelColors = {
      'ERROR': 'bg-red-100 text-red-800 border-red-200',
      'WARN': 'bg-yellow-100 text-yellow-800 border-yellow-200',
      'INFO': 'bg-blue-100 text-blue-800 border-blue-200',
      'DEBUG': 'bg-gray-100 text-gray-800 border-gray-200',
    };
    
    const colorClass = levelColors[level.toUpperCase() as keyof typeof levelColors] || 'bg-gray-100 text-gray-800 border-gray-200';
    
    return (
      <span className={`inline-flex items-center px-2 py-1 rounded-md text-xs font-medium border ${colorClass}`}>
        {level.toUpperCase()}
      </span>
    );
  };

  const extractLogLevel = (message: string): string => {
    const levelMatch = message.match(/\[(ERROR|WARN|WARNING|INFO|DEBUG)\]/i);
    return levelMatch ? levelMatch[1].toUpperCase() : 'INFO';
  };

  const formatLogTimestamp = (timestamp: string): string => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false
    });
  };

  const formatTimestamp = (timestamp: string): string => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      hour12: false
    });
  };

  const TerminalLogDisplay: React.FC<{ logs: any[] }> = ({ logs }) => {
    // Sort logs by timestamp (newest first for terminal-like display)
    const sortedLogs = [...logs].sort((a, b) => 
      new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
    );

    const getLogLevelColor = (level: string) => {
      const levelColors = {
        'ERROR': 'text-red-400',
        'WARN': 'text-yellow-400',
        'WARNING': 'text-yellow-400',
        'INFO': 'text-blue-400',
        'DEBUG': 'text-gray-400',
      };
      return levelColors[level as keyof typeof levelColors] || 'text-gray-400';
    };

    const getLogLevelBg = (level: string) => {
      const levelBgs = {
        'ERROR': 'bg-red-500/20 border border-red-500/30',
        'WARN': 'bg-yellow-500/20 border border-yellow-500/30',
        'WARNING': 'bg-yellow-500/20 border border-yellow-500/30',
        'INFO': 'bg-blue-500/20 border border-blue-500/30',
        'DEBUG': 'bg-gray-500/20 border border-gray-500/30',
      };
      return levelBgs[level as keyof typeof levelBgs] || 'bg-gray-500/20 border border-gray-500/30';
    };

    const highlightLogMessage = (message: string) => {
      // Clean up timestamp prefixes
      const cleanMessage = message.replace(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z\s+/, '').replace(/^\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\s+/, '');
      return cleanMessage;
    };

    return (
      <div className="bg-dark-bg rounded-xl border border-gray-700 overflow-hidden shadow-lg">
        <div className="bg-gradient-to-r from-dark-surface to-dark-card px-4 py-3 border-b border-gray-700">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="p-1.5 bg-neon-green-500/20 rounded-lg">
                <Terminal className="w-4 h-4 text-neon-green-500" />
              </div>
              <div>
                <span className="text-neon-green-500 font-mono text-sm font-medium">Container Logs</span>
                <span className="text-text-muted text-xs ml-2">({logs.length} entries)</span>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <button className="p-1.5 hover:bg-dark-card rounded-lg transition-colors">
                <Copy className="w-3 h-3 text-text-muted" />
              </button>
              <button className="p-1.5 hover:bg-dark-card rounded-lg transition-colors">
                <Download className="w-3 h-3 text-text-muted" />
              </button>
              <button className="p-1.5 hover:bg-dark-card rounded-lg transition-colors">
                <Filter className="w-3 h-3 text-text-muted" />
              </button>
            </div>
          </div>
        </div>
        
        <div className="max-h-96 overflow-y-auto">
          <div className="p-2 space-y-0.5 font-mono text-sm">
            {sortedLogs.map((log, index) => {
              const logLevel = extractLogLevel(log.message);
              const levelColor = getLogLevelColor(logLevel);
              const levelBg = getLogLevelBg(logLevel);
              
              return (
                <div 
                  key={log.id || index} 
                  className="group flex items-start space-x-3 hover:bg-dark-surface/50 px-3 py-2 rounded-lg transition-colors cursor-pointer border-l-2 border-transparent hover:border-neon-purple-500/30"
                >
                  <span className="text-text-muted text-xs w-20 flex-shrink-0 font-medium">
                    {formatLogTimestamp(log.timestamp)}
                  </span>
                  <span className={`text-xs w-16 flex-shrink-0 font-bold px-2 py-0.5 rounded ${levelColor} ${levelBg}`}>
                    {logLevel}
                  </span>
                  <span className="text-neon-purple-500 text-xs w-28 flex-shrink-0 truncate font-medium bg-neon-purple-500/10 px-2 py-0.5 rounded">
                    {log.container.replace('/repathon-', '').replace('-1', '')}
                  </span>
                  <span className="text-text-primary flex-1 break-words group-hover:text-white transition-colors">
                    {highlightLogMessage(log.message)}
                  </span>
                  <button className="opacity-0 group-hover:opacity-100 p-1 hover:bg-dark-card rounded transition-all">
                    <ExternalLink className="w-3 h-3 text-text-muted" />
                  </button>
                </div>
              );
            })}
          </div>
        </div>
        
        <div className="bg-dark-surface px-4 py-2 border-t border-gray-700">
          <div className="flex items-center justify-between text-xs">
            <div className="flex items-center space-x-4">
              <span className="text-text-muted">
                Showing {logs.length} of {logs.length} entries
              </span>
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-neon-green-500 rounded-full animate-pulse"></div>
                <span className="text-neon-green-500 font-medium">Live</span>
              </div>
            </div>
            <button className="text-neon-purple-500 hover:text-neon-purple-400 transition-colors">
              View Full Logs →
            </button>
          </div>
        </div>
      </div>
    );
  };

  const LogEntryComponent: React.FC<{ log: LogEntry; index: number }> = ({ log, index }) => (
    <div className="bg-gray-50 border border-gray-200 rounded-lg p-3 mb-2 font-mono text-xs">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center space-x-2">
          <span className="text-gray-500">#{index + 1}</span>
          <Container className="w-3 h-3 text-blue-500" />
          <span className="font-semibold text-blue-700">{log.container}</span>
          {log.level && formatLogLevel(log.level)}
        </div>
        <div className="flex items-center space-x-1 text-gray-500">
          <Clock className="w-3 h-3" />
          <span>{new Date(log.timestamp).toLocaleString()}</span>
        </div>
      </div>
      <div className="bg-white border border-gray-100 rounded p-2 text-gray-800 leading-relaxed">
        {log.message}
      </div>
    </div>
  );

  const getMessageIcon = (message: Message) => {
    if (message.sender === 'user') {
      return <User className="w-6 h-6 text-black" />;
    }
    
    if (message.isError) {
      return <AlertTriangle className="w-6 h-6 text-red-500" />;
    }
    
    return <Bot className="w-6 h-6 text-neon-purple-500" />;
  };



  const renderQueryResult = (result: QueryResult) => {
    if (!result.success) return null;

    return (
      <div className="mt-4 space-y-4">
        {/* Anomalies Section */}
        {result.anomalies && result.anomalies.length > 0 && (
          <div className="bg-gradient-to-r from-red-50 to-red-100 rounded-xl p-6 border-l-4 border-red-500 shadow-sm">
            <h4 className="font-bold text-red-800 mb-4 flex items-center gap-3 text-lg">
              <div className="p-2 bg-red-500 rounded-lg">
                <AlertTriangle className="w-5 h-5 text-white" />
              </div>
              Critical Anomalies Detected
              <span className="bg-red-500 text-white px-3 py-1 rounded-full text-sm font-medium">
                {result.anomalies.length}
              </span>
            </h4>
            <div className="grid gap-4">
              {result.anomalies.map((anomaly, index) => (
                <div key={index} className="bg-white rounded-lg p-4 border border-red-200 shadow-sm hover:shadow-md transition-shadow">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <div className={`w-3 h-3 rounded-full ${
                        anomaly.severity === 'critical' ? 'bg-red-500 animate-pulse' :
                        anomaly.severity === 'high' ? 'bg-orange-500' :
                        anomaly.severity === 'medium' ? 'bg-yellow-500' : 'bg-blue-500'
                      }`} />
                      <span className="font-semibold text-gray-800 capitalize text-lg">{anomaly.type}</span>
                      <span className={`px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wide ${
                        anomaly.severity === 'critical' ? 'bg-red-100 text-red-800 border border-red-300' :
                        anomaly.severity === 'high' ? 'bg-orange-100 text-orange-800 border border-orange-300' :
                        anomaly.severity === 'medium' ? 'bg-yellow-100 text-yellow-800 border border-yellow-300' : 
                        'bg-blue-100 text-blue-800 border border-blue-300'
                      }`}>
                        {anomaly.severity}
                      </span>
                    </div>
                    <div className="text-right">
                      <div className="text-sm text-gray-500">Current / Threshold</div>
                      <div className="font-bold text-gray-800">{anomaly.value} / {anomaly.threshold}</div>
                    </div>
                  </div>
                  <p className="text-gray-700 mb-3 leading-relaxed">{anomaly.description}</p>
                  {anomaly.recommendation && (
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                      <div className="flex items-start gap-2">
                        <Lightbulb className="w-4 h-4 text-blue-600 mt-0.5 flex-shrink-0" />
                        <div>
                          <div className="font-medium text-blue-800 text-sm">Recommendation</div>
                          <div className="text-blue-700 text-sm">{anomaly.recommendation}</div>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Regular Results */}
        {result.results && result.results.length > 0 && (
          <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl p-6 border-l-4 border-blue-500 shadow-sm">
            <div className="flex items-center justify-between mb-4">
              <h4 className="font-bold text-blue-800 flex items-center gap-3 text-lg">
                <div className="p-2 bg-blue-500 rounded-lg">
                  <Database className="w-5 h-5 text-white" />
                </div>
                Query Results
                <span className="bg-blue-500 text-white px-3 py-1 rounded-full text-sm font-medium">
                  {result.count || result.results.length}
                </span>
              </h4>
              {result.metadata && (
                <div className="bg-white rounded-lg px-4 py-2 border border-blue-200">
                  <div className="text-xs text-blue-600 font-medium">
                    ⚡ {result.metadata.processing_time_ms}ms • 
                    🎯 {(result.metadata.confidence * 100).toFixed(1)}% confidence
                  </div>
                </div>
              )}
            </div>
            
            <div className="max-h-80 overflow-y-auto space-y-3 pr-2">
              {result.results.slice(0, 10).map((item: any, index: number) => (
                <div key={index} className="bg-white rounded-lg p-4 border border-blue-200 shadow-sm hover:shadow-md transition-all hover:border-blue-300">
                  {typeof item === 'object' ? (
                    <div className="space-y-2">
                      {Object.entries(item).map(([key, value]) => (
                        <div key={key} className="flex justify-between items-center py-1">
                          <span className="text-gray-600 capitalize font-medium text-sm">{key.replace(/_/g, ' ')}:</span>
                          <span className="font-mono text-sm bg-gray-100 px-2 py-2 rounded text-gray-800 max-w-xs truncate">
                            {String(value)}
                          </span>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="font-mono text-sm bg-gray-100 p-3 rounded border text-gray-800">
                      {String(item)}
                    </div>
                  )}
                </div>
              ))}
            </div>
            
            {result.results.length > 10 && (
              <div className="mt-4 text-center">
                <div className="inline-flex items-center gap-2 bg-white border border-blue-200 rounded-lg px-4 py-2 text-blue-700">
                  <Eye className="w-4 h-4" />
                  <span className="text-sm font-medium">
                    Showing 10 of {result.results.length} results
                  </span>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Insights Section */}
        {result.insights && result.insights.length > 0 && (
          <div className="bg-gradient-to-r from-yellow-50 to-amber-50 rounded-xl p-6 border-l-4 border-yellow-500 shadow-sm">
            <h4 className="font-bold text-yellow-800 mb-4 flex items-center gap-3 text-lg">
              <div className="p-2 bg-yellow-500 rounded-lg">
                <Lightbulb className="w-5 h-5 text-white" />
              </div>
              AI Insights
              <span className="bg-yellow-500 text-white px-3 py-1 rounded-full text-sm font-medium">
                {result.insights.length}
              </span>
            </h4>
            <div className="space-y-3">
              {result.insights.map((insight, index) => (
                <div key={index} className="bg-white rounded-lg p-4 border border-yellow-200 shadow-sm">
                  <div className="flex items-start gap-3">
                    <div className="w-2 h-2 bg-yellow-500 rounded-full mt-2 flex-shrink-0"></div>
                    <p className="text-yellow-800 leading-relaxed">{insight}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Recommendations Section */}
        {result.recommendations && result.recommendations.length > 0 && (
          <div className="bg-gradient-to-r from-green-50 to-emerald-50 rounded-xl p-6 border-l-4 border-green-500 shadow-sm">
            <h4 className="font-bold text-green-800 mb-4 flex items-center gap-3 text-lg">
              <div className="p-2 bg-green-500 rounded-lg">
                <Target className="w-5 h-5 text-white" />
              </div>
              Recommendations
              <span className="bg-green-500 text-white px-3 py-1 rounded-full text-sm font-medium">
                {result.recommendations.length}
              </span>
            </h4>
            <div className="space-y-3">
              {result.recommendations.map((rec, index) => (
                <div key={index} className="bg-white rounded-lg p-4 border border-green-200 shadow-sm">
                  <div className="flex items-start gap-3">
                    <div className="w-2 h-2 bg-green-500 rounded-full mt-2 flex-shrink-0"></div>
                    <p className="text-green-800 leading-relaxed">{rec}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  };

  const MethodCallComponent: React.FC<{ queryResult: QueryResult }> = ({ queryResult }) => {
    const methodCalled = queryResult.query_info?.method_called || 'process_query';
    const queryType = queryResult.metadata?.intent || queryResult.intent || 'unknown';
    const executionTime = queryResult.processing_time_ms || 0;
    const totalResults = queryResult.count || queryResult.results?.length || 0;
  
    return (
      <div className="bg-blue-50 border border-blue-200 rounded p-3 mb-3 text-sm">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <span className="text-blue-700 flex items-center gap-1">
              <Code className="w-4 h-4" />
              <span className="font-medium">{methodCalled}</span>
            </span>
            <span className="text-gray-700">
              Intent: <span className="font-semibold text-purple-700">{queryType}</span>
            </span>
          </div>
          <div className="flex items-center gap-4 text-gray-600">
            <span className="flex items-center gap-1">
              <Clock className="w-3 h-3" />
              {executionTime.toFixed(0)}ms
            </span>
            <span className="font-medium text-green-700">{totalResults} results</span>
          </div>
        </div>
      </div>
    );
  };

  const handleSuggestedQuery = async (query: string) => {
    // Get the mapping for this specific suggestion
    const mapping = suggestionMapping[query as keyof typeof suggestionMapping];
    
    if (!mapping) {
      // Fallback to original behavior if no mapping found
      setInputValue(query);
      return;
    }

    // Create user message
    const userMessage: Message = {
      id: Date.now().toString(),
      content: query,
      type: 'user',
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    try {
      const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
      let response: Response;

      // Call the specific endpoint based on mapping
      if (mapping.method === 'GET') {
        const params = new URLSearchParams(mapping.params || {});
        const url = `${apiBaseUrl}${mapping.endpoint}${params.toString() ? `?${params.toString()}` : ''}`;
        response = await fetch(url, {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
        });
      } else {
        // POST request
        response = await fetch(`${apiBaseUrl}${mapping.endpoint}`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(mapping.payload || {}),
        });
      }

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      console.log('Backend response:', result); // Debug log
      
      // Extract the actual data from the response
      let queryResult: QueryResult;
      let formattedContent: string;
      
      if (result.success && result.result) {
        // NLP endpoint response structure
        queryResult = {
          success: result.success,
          intent: result.result.metadata?.intent || mapping.intent,
          confidence: result.result.metadata?.confidence || 1.0,
          results: result.result.results || [],
          count: result.result.count || result.result.results?.length || 0,
          processing_time_ms: result.processing_time_ms || result.result.metadata?.processing_time_ms || 0,
          metadata: result.result.metadata,
          query_info: {
            query_type: mapping.intent,
            method_called: 'process_query',
            parameters: mapping.payload || mapping.params || {}
          },
          anomalies: result.result.anomalies,
          insights: result.result.insights,
          recommendations: result.result.recommendations
        };
        
        formattedContent = formatAIResponse(result.result, mapping.intent);
      } else if (result.anomalies || result.metrics || result.summary) {
        // Analytics endpoint response structure
        queryResult = {
          success: true,
          intent: mapping.intent,
          confidence: 1.0,
          results: result.anomalies || result.metrics || [result.summary],
          count: result.anomalies?.length || result.metrics?.length || (result.summary ? 1 : 0),
          processing_time_ms: 0,
          anomalies: result.anomalies,
          insights: result.insights,
          recommendations: result.recommendations
        };
        
        formattedContent = formatAIResponse(result, mapping.intent);
      } else {
        // Fallback for other response structures
        queryResult = {
          success: result.success || true,
          intent: mapping.intent,
          confidence: 1.0,
          results: Array.isArray(result) ? result : [result],
          count: Array.isArray(result) ? result.length : 1,
          processing_time_ms: 0
        };
        
        formattedContent = formatAIResponse(result, mapping.intent);
      }
      
      // Create AI response message
      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'ai',
        content: formattedContent,
        timestamp: new Date(),
        queryResult: queryResult,
      };

      setMessages(prev => [...prev, aiMessage]);
    } catch (error) {
      console.error('Error calling specific function:', error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'ai',
        content: `Sorry, I encountered an error while processing "${query}". Please try again.`,
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  // Helper function to format AI response for the new direct mapping system
  const formatAIResponseForDirectMapping = (data: any, userQuery: string): string => {
    const functionUsed = data.function_used || 'unknown';
    const count = data.count || data.results?.length || 0;
    const totalCount = data.total_count || count;
    const hasMore = data.has_more || false;
    
    // Format response based on the function that was called
    switch (functionUsed) {
      case 'fetch_latest_logs':
        if (count > 0) {
          return `🔍 Found ${count} recent log entries${totalCount > count ? ` (showing ${count} of ${totalCount} total)` : ''}. Here are the latest logs:`;
        } else {
          return '🔍 No recent log entries found. The system may not have generated any logs recently.';
        }
        
      case 'search_logs':
        if (count > 0) {
          return `🔍 Found ${count} log entries matching your search${totalCount > count ? ` (showing ${count} of ${totalCount} total)` : ''}. Here are the results:`;
        } else {
          return '🔍 No log entries found matching your search criteria. Try adjusting your search terms.';
        }
        
      case 'get_alerts':
        if (count > 0) {
          return `🚨 Found ${count} active alerts${hasMore ? ' (showing recent alerts)' : ''}. Here are the current system alerts:`;
        } else {
          return '✅ No active alerts found. Your system is running smoothly!';
        }
        
      case 'get_metrics':
        if (count > 0) {
          return `📊 Retrieved ${count} performance metrics. Here's your system performance overview:`;
        } else {
          return '📊 No performance metrics available at the moment.';
        }
        
      case 'get_docker_events':
        if (count > 0) {
          return `🐳 Found ${count} Docker events${hasMore ? ' (showing recent events)' : ''}. Here are the container activities:`;
        } else {
          return '🐳 No recent Docker events found. Container activity is quiet.';
        }
        
      case 'get_container_status':
        if (count > 0) {
          return `🐳 Retrieved status for ${count} containers. Here's your container overview:`;
        } else {
          return '🐳 No container information available.';
        }
        
      default:
        if (count > 0) {
          return `✅ Successfully processed your query "${userQuery}". Found ${count} results:`;
        } else {
          return `✅ Processed your query "${userQuery}" but no results were found.`;
        }
    }
  };

  // Helper function to format AI response based on intent
  const formatAIResponse = (result: any, intent: string): string => {
    if (intent === 'analytics_anomalies') {
      const anomalies = result.anomalies || [];
      return anomalies.length > 0 
        ? `🚨 Found ${anomalies.length} anomalies that require attention. Check the details below for specific issues and recommendations.`
        : '✅ No significant anomalies detected in your system. All metrics are within normal ranges.';
    }
    
    if (intent === 'analytics_performance') {
      const metrics = result.metrics || result.performance_metrics || [];
      return metrics.length > 0
        ? `📊 Performance metrics retrieved successfully. Found ${metrics.length} performance indicators. Here's your system performance overview:`
        : '📊 Performance metrics retrieved. System performance data is available below.';
    }
    
    if (intent === 'analytics_summary') {
      return '📋 System summary generated successfully. Here\'s a comprehensive overview of your current system status and key metrics:';
    }
    
    if (intent === 'analytics_metrics') {
      const containers = result.containers || result.metrics || [];
      return containers.length > 0
        ? `🐳 Container analysis complete. Found ${containers.length} containers. Here are the current container metrics and health status:`
        : '🐳 Container analysis complete. Container metrics and health status are available below.';
    }
    
    if (intent === 'search_logs') {
      const count = result.results?.length || result.count || 0;
      if (count > 0) {
        return `🔍 Found ${count} relevant log entries matching your search criteria. Here are the results:`;
      } else {
        return '🔍 No matching log entries found for your query. Try adjusting your search terms or time range.';
      }
    }
    
    if (intent === 'investigate') {
      const findings = result.findings || result.investigation_results || [];
      return findings.length > 0
        ? `🛡️ Security investigation complete. Found ${findings.length} findings that require attention. Here are the investigation results:`
        : '🛡️ Security investigation complete. No significant security issues detected in the specified timeframe.';
    }
    
    if (intent === 'analyze_trends') {
      return '🌐 Network analysis complete. Here are the connectivity patterns, latency insights, and trend analysis:';
    }
    
    // Default response
    return 'Analysis complete. Here are the results:';
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="flex flex-col h-full bg-dark-bg text-text-primary">
      {/* Header with System Health */}
      <div className="bg-dark-surface border-b border-gray-800 p-4">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-gradient-neon rounded-lg">
              <Terminal className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-text-primary">Log Analysis Assistant</h1>
              <p className="text-sm text-text-muted">AI-powered monitoring and log analysis</p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <button className="p-2 hover:bg-dark-card rounded-lg transition-colors">
              <Filter className="w-5 h-5 text-text-muted" />
            </button>
            <button className="p-2 hover:bg-dark-card rounded-lg transition-colors">
              <Download className="w-5 h-5 text-text-muted" />
            </button>
          </div>
        </div>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {/* Initial welcome screen with improved categorized suggestions */}
        {messages.length === 0 ? (
          <div className="text-center py-16">
            <Bot className="w-16 h-16 text-neon-purple-500 mx-auto mb-6" />
            <h2 className="text-2xl font-bold text-text-primary mb-2">Welcome to AI Assistant</h2>
            <p className="text-text-muted mb-8 max-w-md mx-auto">
              Ask me anything about your system logs, performance metrics, or anomalies. 
              I'll help you analyze and understand your monitoring data.
            </p>
            
            {/* Categorized Quick Actions */}
            <div className="max-w-6xl mx-auto space-y-6">
              {suggestedQueries.map((category, categoryIndex) => (
                <div key={categoryIndex} className="text-left">
                  <h3 className="text-lg font-semibold text-text-primary mb-4 text-center">{category.category}</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {category.queries.map((query, queryIndex) => (
                      <button
                        key={queryIndex}
                        onClick={() => handleSuggestedQuery(query)}
                        className="group p-4 bg-dark-surface hover:bg-dark-card border border-gray-700 hover:border-neon-purple-500 rounded-xl transition-all duration-200 text-left"
                      >
                        <div className="flex items-start space-x-3">
                          <div className="text-2xl">{query.split(' ')[0]}</div>
                          <div>
                            <div className="text-text-primary font-medium group-hover:text-neon-purple-500 transition-colors">
                              {query.substring(2)}
                            </div>
                          </div>
                        </div>
                      </button>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        ) : (
          messages.map((message) => (
            <div key={message.id} className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-[85%] ${
                message.sender === 'user' 
                  ? 'bg-gradient-purple text-white shadow-purple-500/20' 
                  : 'bg-dark-surface border border-gray-700'
              } rounded-xl p-5 shadow-lg`}>
                <div className="flex items-start space-x-4">
                  <div className="flex-shrink-0">
                    <div className={`p-2 rounded-lg ${
                      message.sender === 'user' 
                        ? 'bg-white/90' 
                        : 'bg-neon-purple-500/20'
                    }`}>
                      {getMessageIcon(message)}
                    </div>
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between mb-3">
                      <div className={`text-sm font-medium ${
                        message.sender === 'user' ? 'text-black/80' : 'text-text-muted'
                      }`}>
                        {message.sender === 'user' ? 'You' : 'AI Assistant'}
                      </div>
                      <div className={`text-xs ${
                        message.sender === 'user' ? 'text-black/60' : 'text-text-muted'
                      }`}>
                        {formatTime(message.timestamp)}
                      </div>
                    </div>
                    <div className={message.sender === 'user' ? 'text-black font-medium' : 'text-text-primary'}>
                      {message.sender === 'user' ? (
                        <span className="text-black">{message.content}</span>
                      ) : (
                        <div className="space-y-4">
                          {/* Display the AI's formatted response content first */}
                          <div className="text-text-primary leading-relaxed">
                            {message.content}
                          </div>
                          
                          {/* Then show the method call info and detailed results */}
                          {message.queryResult && <MethodCallComponent queryResult={message.queryResult} />}
                          {message.queryResult && renderQueryResult(message.queryResult)}
                          
                          {/* Show raw results only if they contain log entries or specific data */}
                          {message.queryResult?.results && message.queryResult.results.length > 0 && (
                            <div>
                              {message.queryResult.results[0]?.timestamp && 
                               message.queryResult.results[0]?.container && 
                               message.queryResult.results[0]?.message ? (
                                <TerminalLogDisplay logs={message.queryResult.results} />
                              ) : (
                                <div className="bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg p-4">
                                  <div className="flex items-center space-x-2 mb-4">
                                    <Terminal className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                                    <h4 className="font-semibold text-gray-900 dark:text-gray-100">
                                      Query Results ({message.queryResult.results.length})
                                    </h4>
                                  </div>
                                  <div className="max-h-96 overflow-y-auto space-y-2">
                                    {message.queryResult.results.slice(0, 10).map((result, index) => (
                                      <div key={index} className="bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-3">
                                        <pre className="text-xs font-mono text-gray-700 dark:text-gray-300 overflow-x-auto whitespace-pre-wrap">
                                          {JSON.stringify(result, null, 2)}
                                        </pre>
                                      </div>
                                    ))}
                                    {message.queryResult.results.length > 10 && (
                                      <div className="text-center py-2">
                                        <span className="text-sm text-gray-500 bg-gray-100 dark:bg-gray-700 px-3 py-1 rounded-full">
                                          ... and {message.queryResult.results.length - 10} more entries
                                        </span>
                                      </div>
                                    )}
                                  </div>
                                </div>
                              )}
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                    {message.type === 'ai' && (
                      <div className="flex items-center space-x-2 mt-4 pt-3 border-t border-gray-700">
                        <button className="flex items-center space-x-1 text-xs text-text-muted hover:text-neon-purple-500 transition-colors">
                          <Copy className="w-3 h-3" />
                          <span>Copy</span>
                        </button>
                        <button className="flex items-center space-x-1 text-xs text-text-muted hover:text-neon-purple-500 transition-colors">
                          <ExternalLink className="w-3 h-3" />
                          <span>Export</span>
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ))
        )}

        {/* Loading indicator */}
        {isLoading && (
          <div className="w-full">
            <div className="bg-dark-surface rounded-lg p-6 border border-gray-700">
              <div className="flex items-center justify-center space-x-3">
                <div className="flex space-x-1">
                  <div className="w-3 h-3 bg-neon-purple-500 rounded-full animate-bounce"></div>
                  <div className="w-3 h-3 bg-neon-purple-500 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                  <div className="w-3 h-3 bg-neon-purple-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                </div>
                <span className="text-text-muted">Processing your query...</span>
              </div>
            </div>
          </div>
        )}
        
        {/* Scroll anchor - this div will be scrolled into view */}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
       <div className="bg-dark-surface border-t border-gray-800 p-4">
         <div className="flex items-center space-x-3">
           <div className="flex-1 relative">
             <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 w-5 h-5 text-text-muted" />
             <input
               type="text"
               value={inputValue}
               onChange={(e) => setInputValue(e.target.value)}
               onKeyPress={handleKeyPress}
               placeholder="Ask about logs, metrics, anomalies, or system health..."
               className="w-full pl-12 pr-4 py-4 bg-dark-card border border-gray-700 rounded-xl text-text-primary placeholder-text-muted focus:outline-none focus:border-neon-purple-500 focus:ring-2 focus:ring-neon-purple-500/20 transition-all duration-200"
             />
           </div>
           <button
             onClick={handleSendMessage}
             disabled={!inputValue.trim()}
             className="px-6 py-4 bg-gradient-neon text-white rounded-xl hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 flex items-center space-x-2 font-medium shadow-lg"
           >
             <Send className="w-5 h-5" />
             <span>Analyze</span>
           </button>
         </div>
         
         {/* Quick Suggestions - Always show when there are messages, improved formatting */}
         {messages.length > 0 && (
           <div className="mt-4 p-4 bg-dark-card border border-gray-700 rounded-xl">
             <h4 className="text-sm font-medium text-text-primary mb-3 flex items-center">
               <Lightbulb className="w-4 h-4 mr-2 text-neon-purple-500" />
               Quick Actions
             </h4>
             <div className="grid grid-cols-3 gap-3">
               {allSuggestedQueries.map((query, queryIndex) => (
                 <button
                   key={queryIndex}
                   onClick={() => handleSuggestedQuery(query)}
                   className="group p-3 bg-dark-surface hover:bg-neon-purple-500/10 border border-gray-700 hover:border-neon-purple-500 rounded-lg transition-all duration-200 text-left"
                 >
                   <div className="flex items-center space-x-2">
                     <div className="text-lg">{query.split(' ')[0]}</div>
                     <div className="flex-1 min-w-0">
                       <div className="text-sm text-text-primary group-hover:text-neon-purple-500 transition-colors truncate">
                         {query.substring(2)}
                       </div>
                     </div>
                   </div>
                 </button>
               ))}
             </div>
           </div>
         )}
         
         {/* Quick Suggestions when typing - use flattened array */}
         {inputValue.length > 0 && (
           <div className="mt-3 flex flex-wrap gap-2">
             {allSuggestedQueries.slice(0, 4).map((query, index) => (
               <button
                 key={index}
                 onClick={() => handleSuggestedQuery(query)}
                 className="px-3 py-1 text-xs bg-dark-card hover:bg-neon-purple-500/20 border border-gray-700 hover:border-neon-purple-500 rounded-lg text-text-muted hover:text-neon-purple-500 transition-all duration-200"
               >
                 {query.substring(2)}
               </button>
             ))}
           </div>
         )}
       </div>
    </div>
  );
};

export default AskAI;