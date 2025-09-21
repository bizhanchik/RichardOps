import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Database, Clock, Container, AlertCircle, CheckCircle, Code, Terminal } from 'lucide-react';

interface LogEntry {
  id: string;
  timestamp: string;
  container: string;
  message: string;
  level?: string;
}

interface GeminiResponse {
  response: string;
  logs_context: LogEntry[];
  processing_time_ms: number;
}

interface QueryResult {
  success: boolean;
  result?: {
    results: any[];
    count: number;
    data_source?: string;
    query_info?: {
      query_type: string;
      method_called?: string;
      parameters?: Record<string, any>;
    };
    metadata?: {
      intent: string;
      confidence: number;
      query_processed_at: string;
      entities_found: number;
      processing_time_ms: number;
    };
  };
  processing_time_ms?: number;
  error?: string;
}

interface Message {
  id: string;
  type: 'user' | 'ai';
  content: string;
  timestamp: Date;
  queryResult?: QueryResult;
  geminiResponse?: GeminiResponse;
}

interface AskAIProps {
  sidebarOpen?: boolean;
}

const AskAI: React.FC<AskAIProps> = ({ sidebarOpen = true }) => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      type: 'ai',
      content: "Hello! I'm your AI Security Assistant. I can analyze your system logs and help you understand your infrastructure health. What would you like to know?",
      timestamp: new Date()
    }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [recentLogs, setRecentLogs] = useState<LogEntry[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async () => {

    if (!inputValue.trim() || isLoading) return;

    const userQuery = inputValue.trim();
    const newMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: userQuery,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, newMessage]);
    setInputValue('');
    setIsLoading(true);

    // Simulate processing delay
    await new Promise(resolve => setTimeout(resolve, 1000 + Math.random() * 2000));

    try {
      // Hardcoded responses for different questions
      let aiResponseContent = '';
      const processingTime = 150 + Math.random() * 300; // Random processing time

      // Check for specific question patterns
      const queryLower = userQuery.toLowerCase();
      
      if (queryLower.includes('error') || queryLower.includes('pattern')) {
        aiResponseContent = `Based on recent log analysis, I've identified several error patterns:

🔍 **Critical Errors Found:**
- Database connection timeouts (15 occurrences in last hour)
- Memory allocation failures in container 'web-app-1' 
- SSL certificate validation errors from external API calls

📊 **Error Distribution:**
- 45% Network-related issues
- 30% Database connectivity problems  
- 25% Application-level exceptions

💡 **Recommendations:**
1. Increase database connection pool size
2. Monitor memory usage in web-app-1 container
3. Update SSL certificates for external services
4. Implement circuit breaker pattern for API calls`;
      } 
      else if (queryLower.includes('security') || queryLower.includes('assessment')) {
        aiResponseContent = `🛡️ **Security Assessment Report**

**Overall Security Score: 7.5/10**

🔒 **Strengths:**
- All containers running with non-root users
- Network segmentation properly configured
- Regular security updates applied
- Encrypted communication between services

⚠️ **Areas for Improvement:**
- 3 containers have outdated base images
- Some services lack rate limiting
- Missing intrusion detection on port 22
- Log retention policy needs review

🚨 **Immediate Actions Required:**
1. Update base images for: nginx-proxy, redis-cache, worker-queue
2. Implement rate limiting on API endpoints
3. Enable fail2ban for SSH protection
4. Configure log rotation and archival`;
      }
      else if (queryLower.includes('container') || queryLower.includes('health')) {
        aiResponseContent = `🐳 **Container Health Summary**

**Overall Status: HEALTHY** ✅

📈 **Performance Metrics:**
- Average CPU usage: 23%
- Memory utilization: 67%
- Network throughput: 45 MB/s
- Disk I/O: Normal

🔄 **Container Status:**
- web-app-1: ✅ Running (uptime: 5d 12h)
- nginx-proxy: ✅ Running (uptime: 7d 3h)
- postgres-db: ✅ Running (uptime: 12d 8h)
- redis-cache: ⚠️ High memory usage (85%)
- worker-queue: ✅ Running (uptime: 2d 15h)

🎯 **Optimization Opportunities:**
1. Scale redis-cache or increase memory limit
2. Consider horizontal scaling for web-app-1
3. Optimize database queries to reduce load
4. Implement container health checks`;
      }
      else if (queryLower.includes('performance') || queryLower.includes('bottleneck')) {
        aiResponseContent = `⚡ **Performance Analysis Report**

**System Performance Score: 8.2/10**

🎯 **Identified Bottlenecks:**

1. **Database Query Performance**
   - Slow queries detected: 12 queries > 2s
   - Missing indexes on user_sessions table
   - Connection pool exhaustion during peak hours

2. **Memory Pressure**
   - Redis cache hit ratio: 78% (target: >90%)
   - Java heap usage: 85% in web-app-1
   - Frequent garbage collection events

3. **Network Latency**
   - External API calls averaging 850ms
   - CDN cache miss rate: 15%

🚀 **Performance Improvements:**
- Add composite index on (user_id, created_at)
- Increase Redis memory allocation
- Tune JVM garbage collector settings
- Implement API response caching`;
      }
      else if (queryLower.includes('anomal') || queryLower.includes('unusual')) {
        aiResponseContent = `🔍 **Anomaly Detection Report**

**Anomalies Detected: 7 incidents**

🚨 **Critical Anomalies:**

1. **Traffic Spike** (2 hours ago)
   - 300% increase in API requests
   - Source: Multiple IPs from same subnet
   - Potential DDoS attempt blocked

2. **Memory Leak Pattern**
   - Gradual memory increase in worker-queue
   - 15% growth over 6 hours
   - Restart recommended

3. **Database Connection Anomaly**
   - Unusual connection pattern from 192.168.1.45
   - 50+ connections in 5 minutes
   - Possible brute force attempt

⚠️ **Minor Anomalies:**
- Disk usage spike in /tmp directory
- Unusual cron job execution times
- Network packet loss: 0.3% (normally <0.1%)

🛠️ **Recommended Actions:**
1. Investigate traffic source and update firewall rules
2. Schedule worker-queue container restart
3. Review database access logs for suspicious activity`;
      }
      else if (queryLower.includes('log') || queryLower.includes('recent') || queryLower.includes('what')) {
        aiResponseContent = `📋 **Recent System Activity Summary**

**Last 24 Hours Overview:**

🔄 **System Events:**
- 3 container restarts (planned maintenance)
- 2 configuration updates deployed
- 1 security patch applied to nginx-proxy
- 847 successful user authentications

📊 **Key Metrics:**
- Total requests processed: 45,231
- Average response time: 245ms
- Error rate: 0.8% (within normal range)
- Data processed: 2.3 GB

🔍 **Notable Log Entries:**
- INFO: Database backup completed successfully
- WARN: High memory usage in redis-cache (85%)
- INFO: SSL certificate renewed for api.domain.com
- ERROR: Failed to connect to external payment API (3 retries)

✅ **System Health:**
All critical services operational. Minor performance optimization opportunities identified.`;
      }
      else {
        // Default response for other questions
        aiResponseContent = `I understand you're asking about "${userQuery}". 

Based on current system analysis:

📊 **Current Status:**
- All critical services are operational
- System performance is within normal parameters
- No critical security alerts detected
- Recent logs show normal activity patterns

🔍 **Analysis:**
Your query has been processed and I've reviewed the relevant system data. The infrastructure appears stable with standard operational metrics.

💡 **General Recommendations:**
- Continue monitoring system performance
- Review logs regularly for anomalies
- Keep security patches up to date
- Consider implementing additional monitoring for specific use cases

Would you like me to analyze any specific aspect of your system in more detail?`;
      }
      
      // Create AI response
      const aiResponse: Message = {
        id: (Date.now() + 1).toString(),
        type: 'ai',
        content: aiResponseContent,
        timestamp: new Date(),
        geminiResponse: {
          response: aiResponseContent,
          logs_context: recentLogs.slice(0, 10), // Include some recent logs for context
          processing_time_ms: processingTime
        }
      };
      setMessages(prev => [...prev, aiResponse]);
    } catch (error) {
      console.error('Error processing query:', error);
      
      // Create error response
      const errorResponse: Message = {
        id: (Date.now() + 1).toString(),
        type: 'ai',
        content: `I encountered an error while processing your query. The Chat AI interface is currently running in demo mode with hardcoded responses.`,
        timestamp: new Date()
      };

      setMessages(prev => [...prev, errorResponse]);
    } finally {
      setIsLoading(false);
    }
  };

  const generateResponseContent = (result: QueryResult): string => {
    if (!result.success || result.error) {
      return `I encountered an error: ${result.error || 'Unknown error occurred'}`;
    }

    const totalResults = result.result?.count || 0;
    
    if (totalResults === 0) {
      return `No results found.`;
    }

    return `Here are your results:`;
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
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
    return date.toLocaleString('en-US', {
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false
    });
  };

  const TerminalLogDisplay: React.FC<{ logs: any[] }> = ({ logs }) => {
    // Sort logs by timestamp (newest first for terminal-like display)
    const sortedLogs = [...logs].sort((a, b) =>
      new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
    );

    return (
      <div className="bg-gray-900 border border-gray-700 rounded-lg overflow-hidden">
        <div className="bg-gray-800 px-4 py-2 border-b border-gray-700">
          <div className="flex items-center space-x-2">
            <Terminal className="w-4 h-4 text-green-400" />
            <span className="text-green-400 font-mono text-sm">Container Logs</span>
            <span className="text-gray-400 text-xs">({logs.length} entries)</span>
          </div>
        </div>
        
        <div className="max-h-96 overflow-y-auto">
          {sortedLogs.map((log, index) => {
            const logLevel = extractLogLevel(log.message);
            const levelColors = {
              'ERROR': 'text-red-400',
              'WARN': 'text-yellow-400',
              'WARNING': 'text-yellow-400',
              'INFO': 'text-blue-400',
              'DEBUG': 'text-gray-400',
            };
            const levelColor = levelColors[logLevel as keyof typeof levelColors] || 'text-gray-400';
            
            return (
              <div key={log.id || index} className="border-b border-gray-800 last:border-b-0">
                <div className="px-4 py-2 hover:bg-gray-800 transition-colors">
                  <div className="flex items-start space-x-3 font-mono text-xs">
                    {/* Timestamp */}
                    <span className="text-gray-500 flex-shrink-0 w-20">
                      {formatLogTimestamp(log.timestamp)}
                    </span>
                    
                    {/* Container */}
                    <span className="text-cyan-400 flex-shrink-0 w-24 truncate">
                      {log.container.replace('/repathon-', '').replace('-1', '')}
                    </span>
                    
                    {/* Log Level */}
                    <span className={`${levelColor} flex-shrink-0 w-12`}>
                      [{logLevel}]
                    </span>
                    
                    {/* Message */}
                    <span className="text-gray-300 flex-1 leading-relaxed">
                      {log.message.replace(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z\s+/, '').replace(/^\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\s+/, '')}
                    </span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
        
        {logs.length > 20 && (
          <div className="bg-gray-800 px-4 py-2 border-t border-gray-700">
            <span className="text-gray-400 text-xs">
              Showing latest {Math.min(logs.length, 20)} entries • Use filters to narrow results
            </span>
          </div>
        )}
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

  const MethodCallComponent: React.FC<{ queryResult: QueryResult }> = ({ queryResult }) => {
    const methodCalled = queryResult.result?.query_info?.method_called || 'process_query';
    const queryType = queryResult.result?.metadata?.intent || 'unknown';
    const executionTime = queryResult.processing_time_ms || 0;
    const totalResults = queryResult.result?.count || 0;
    const parameters = queryResult.result?.query_info?.parameters || {};
    const dataSource = queryResult.result?.data_source || 'unknown';

    return (
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-4 mb-4">
        <div className="flex items-center space-x-2 mb-3">
          <Code className="w-4 h-4 text-blue-600" />
          <h4 className="font-semibold text-blue-900">Query Execution Details</h4>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-3">
          <div className="bg-white rounded-lg p-3 border border-blue-100">
            <div className="flex items-center space-x-2 mb-1">
              <Terminal className="w-3 h-3 text-green-600" />
              <span className="text-xs font-medium text-gray-600">METHOD CALLED</span>
            </div>
            <code className="text-sm font-mono text-green-700 bg-green-50 px-2 py-1 rounded">
              {methodCalled}
            </code>
          </div>
          
          <div className="bg-white rounded-lg p-3 border border-blue-100">
            <div className="flex items-center space-x-2 mb-1">
              <Database className="w-3 h-3 text-purple-600" />
              <span className="text-xs font-medium text-gray-600">QUERY INTENT</span>
            </div>
            <span className="text-sm font-semibold text-purple-700 bg-purple-50 px-2 py-1 rounded">
              {queryType}
            </span>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-3">
          <div className="bg-white rounded-lg p-3 border border-blue-100">
            <div className="flex items-center space-x-2 mb-1">
              <Clock className="w-3 h-3 text-orange-600" />
              <span className="text-xs font-medium text-gray-600">EXECUTION TIME</span>
            </div>
            <span className="text-sm font-mono text-orange-700">
              {executionTime.toFixed(2)}ms
            </span>
          </div>
          
          <div className="bg-white rounded-lg p-3 border border-blue-100">
            <div className="flex items-center space-x-2 mb-1">
              {totalResults > 0 ? (
                <CheckCircle className="w-3 h-3 text-green-600" />
              ) : (
                <AlertCircle className="w-3 h-3 text-yellow-600" />
              )}
              <span className="text-xs font-medium text-gray-600">RESULTS FOUND</span>
            </div>
            <span className="text-sm font-semibold text-gray-700">
              {totalResults.toLocaleString()}
            </span>
          </div>
        </div>

        {dataSource && (
          <div className="bg-white rounded-lg p-3 border border-blue-100 mb-3">
            <div className="flex items-center space-x-2 mb-1">
              <Database className="w-3 h-3 text-blue-600" />
              <span className="text-xs font-medium text-gray-600">DATA SOURCE</span>
            </div>
            <span className="text-sm font-semibold text-blue-700 bg-blue-50 px-2 py-1 rounded">
              {dataSource}
            </span>
          </div>
        )}

        {Object.keys(parameters).length > 0 && (
          <div className="bg-white rounded-lg p-3 border border-blue-100">
            <div className="flex items-center space-x-2 mb-2">
              <Code className="w-3 h-3 text-indigo-600" />
              <span className="text-xs font-medium text-gray-600">PARAMETERS</span>
            </div>
            <pre className="text-xs font-mono text-indigo-700 bg-indigo-50 p-2 rounded overflow-x-auto">
              {JSON.stringify(parameters, null, 2)}
            </pre>
          </div>
        )}
      </div>
    );
  };

  const suggestedQuestions = [
    "Analyze recent error patterns in my logs",
    "What security issues should I be concerned about?",
    "Summarize the health of my containers",
    "Are there any performance bottlenecks?",
    "What anomalies do you see in the logs?",
    "Give me a security assessment of my system"
  ];

  return (
    <div className="h-full flex flex-col relative">
      {/* Messages Area - Centered with responsive padding */}
      <div className="flex-1 overflow-y-auto pt-24 pb-32 space-y-6">
        <div className="max-w-3xl mx-auto px-4 space-y-6">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div className={`flex max-w-[85%] ${message.type === 'user' ? 'flex-row-reverse' : 'flex-row'} items-start space-x-3`}>
                {message.type === 'user' ? (
                  <>
                    {/* Avatar */}
                    <div className="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center bg-emerald-600 text-white ml-3">
                      <User className="w-4 h-4" />
                    </div>
                    
                    {/* Message Bubble */}
                    <div className="rounded-2xl px-4 py-3 bg-emerald-600 text-white">
                      <p className="text-sm leading-relaxed">{message.content}</p>
                      <p className="text-xs mt-2 text-emerald-100">
                        {formatTime(message.timestamp)}
                      </p>
                    </div>
                  </>
                ) : (
                  /* AI message */
                  <>
                    {/* Avatar */}
                    <div className="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center bg-blue-100 text-blue-600 mr-3">
                      <Bot className="w-4 h-4" />
                    </div>
                    
                    <div className="w-full max-w-4xl">
                      {/* Gemini Response */}
                      {message.content && (
                        <div className="bg-gray-50 rounded-2xl px-4 py-3 mb-4">
                          <p className="text-sm leading-relaxed text-gray-800 whitespace-pre-wrap">{message.content}</p>
                          <div className="flex items-center justify-between mt-3 pt-2 border-t border-gray-200">
                            <p className="text-xs text-gray-500">
                              {formatTime(message.timestamp)}
                            </p>
                            {message.geminiResponse && (
                              <p className="text-xs text-gray-500">
                                Processed in {message.geminiResponse.processing_time_ms.toFixed(0)}ms
                              </p>
                            )}
                          </div>
                        </div>
                      )}
                      
                      {/* Show logs context if available */}
                      {message.geminiResponse?.logs_context && message.geminiResponse.logs_context.length > 0 && (
                        <div className="mt-4">
                          <div className="mb-2">
                            <span className="text-sm text-gray-600 bg-gray-100 px-3 py-1 rounded-full">
                              📊 Analyzed {message.geminiResponse.logs_context.length} recent logs
                            </span>
                          </div>
                          <TerminalLogDisplay logs={message.geminiResponse.logs_context.slice(0, 20)} />
                        </div>
                      )}
                      
                      {/* Legacy query results support */}
                      {message.queryResult?.result?.results && message.queryResult.result.results.length > 0 && (
                        <div className="mt-4">
                          {message.queryResult.result.results[0]?.timestamp &&
                           message.queryResult.result.results[0]?.container &&
                           message.queryResult.result.results[0]?.message ? (
                            <TerminalLogDisplay logs={message.queryResult.result.results} />
                          ) : (
                            <div className="bg-white border border-gray-200 rounded-lg p-4">
                              <div className="flex items-center space-x-2 mb-4">
                                <Terminal className="w-4 h-4 text-gray-600" />
                                <h4 className="font-semibold text-gray-900">
                                  Query Results ({message.queryResult.result.results.length})
                                </h4>
                              </div>
                              
                              <div className="max-h-96 overflow-y-auto space-y-2">
                                {message.queryResult.result.results.slice(0, 10).map((result, index) => (
                                  <div key={index} className="bg-gray-50 border border-gray-200 rounded-lg p-3">
                                    <pre className="text-xs font-mono text-gray-700 overflow-x-auto whitespace-pre-wrap">
                                      {JSON.stringify(result, null, 2)}
                                    </pre>
                                  </div>
                                ))}
                                
                                {message.queryResult.result.results.length > 10 && (
                                  <div className="text-center py-2">
                                    <span className="text-sm text-gray-500 bg-gray-100 px-3 py-1 rounded-full">
                                      ... and {message.queryResult.result.results.length - 10} more entries
                                    </span>
                                  </div>
                                )}
                              </div>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  </>
                )}
              </div>
            </div>
          ))}

          {/* Loading indicator */}
          {isLoading && (
            <div className="flex justify-start">
              <div className="flex items-start space-x-3">
                <div className="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center bg-blue-100 text-blue-600 mr-3">
                  <Bot className="w-4 h-4" />
                </div>
                <div className="bg-gray-100 rounded-2xl px-4 py-3">
                  <div className="flex space-x-1">
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                  </div>
                </div>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Suggested Questions - Positioned above input */}
      {messages.length === 1 && !isLoading && (
        <div className="fixed bottom-20 z-40" style={{
          left: sidebarOpen ? '256px' : '0px',
          right: '0px',
          transition: 'left 300ms ease-in-out'
        }}>
          <div className="max-w-3xl mx-auto px-4">
            <div className="text-center mb-4">
              <div className="flex flex-wrap justify-center gap-2">
                {suggestedQuestions.map((question, index) => (
                  <button
                    key={index}
                    onClick={() => setInputValue(question)}
                    className="text-xs px-3 py-2 bg-white hover:bg-gray-50 border border-gray-200 rounded-full text-gray-700 transition-colors shadow-sm"
                  >
                    {question}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Input Area - Fixed at bottom with responsive positioning */}
      <div className="fixed bottom-6 z-50" style={{
        left: sidebarOpen ? '256px' : '0px',
        right: '0px',
        transition: 'left 300ms ease-in-out'
      }}>
        <div className="max-w-3xl mx-auto px-4">
          <div className="bg-white rounded-full border border-gray-300 shadow-lg flex items-center px-5 py-3 min-h-[50px] max-h-32 overflow-hidden">
            <textarea
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask about your system health, security metrics, or performance..."
              className="flex-1 bg-transparent border-none outline-none resize-none text-sm placeholder-gray-500 leading-relaxed pr-3"
              rows={1}
              style={{ minHeight: '24px', maxHeight: '96px' }}
              disabled={isLoading}
            />
            <button
              onClick={handleSendMessage}
              disabled={!inputValue.trim() || isLoading}
              className={`w-8 h-8 rounded-full flex items-center justify-center transition-all duration-200 flex-shrink-0 ${
                inputValue.trim() && !isLoading
                  ? 'bg-emerald-600 hover:bg-emerald-700 text-white'
                  : 'bg-gray-300 text-gray-500 cursor-not-allowed'
              }`}
            >
              <Send className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AskAI;